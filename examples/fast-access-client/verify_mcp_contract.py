#!/usr/bin/env python3
"""Compare the documented MCP argument table with real tools/list input schemas.

Only initialize, notifications/initialized and tools/list are sent. No tool is called.
Python 3.9+, standard library, POSIX (selectable subprocess pipes).
"""
import argparse
import json
from pathlib import Path
import re
import selectors
import subprocess
import sys
import time


def discover(command):
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, bufsize=0)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    pending = bytearray()

    def request(method, params, ident):
        message = {"jsonrpc": "2.0", "method": method, "params": params}
        if ident is not None:
            message["id"] = ident
        process.stdin.write((json.dumps(message) + "\n").encode())
        process.stdin.flush()
        if ident is None:
            return None
        deadline = time.monotonic() + 15
        while True:
            while b"\n" in pending:
                line, _, rest = pending.partition(b"\n")
                pending[:] = rest
                result = json.loads(line)
                if result.get("id") == ident:
                    if "error" in result:
                        raise ValueError("MCP discovery returned an error")
                    return result["result"]
            if not selector.select(max(0, deadline - time.monotonic())):
                raise ValueError("MCP discovery timed out")
            chunk = process.stdout.read(65536)
            if not chunk:
                raise ValueError("MCP process closed before discovery completed")
            pending.extend(chunk)
            if len(pending) > 2_000_000:
                raise ValueError("MCP discovery response exceeded local size limit")

    try:
        request("initialize", {"protocolVersion": "2025-11-25", "capabilities": {},
                                "clientInfo": {"name": "contract-check", "version": "1"}}, 1)
        request("notifications/initialized", {}, None)
        result, tools, ident = {}, [], 2
        while True:
            result = request("tools/list", {"cursor": result["nextCursor"]} if result.get("nextCursor") else {}, ident)
            tools.extend({"name": tool["name"], "inputSchema": tool["inputSchema"]}
                         for tool in result["tools"])
            if not result.get("nextCursor"):
                return {"tools": tools}
            ident += 1
            if ident > 20:
                raise ValueError("too many discovery pages")
    finally:
        selector.close()
        process.stdin.close()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        process.stdout.close()


def check(document, discovery):
    section = document.split("## MCP adapter tool surface", 1)[1].split("## Compatibility", 1)[0]
    if "| Tool | Required inputs | Optional inputs |" not in section:
        raise ValueError("documentation must distinguish exact required and optional argument names")
    rows = {}
    for line in section.splitlines():
        columns = [part.strip() for part in line.split("|")[1:-1]]
        if len(columns) != 4 or not re.fullmatch(r"`[a-z_]+`", columns[0]):
            continue
        name = columns[0].strip("`")
        if name in rows:
            raise ValueError("duplicate documented tool")
        rows[name] = (set(re.findall(r"`([a-z_]+)`", columns[1])),
                      set(re.findall(r"`([a-z_]+)`", columns[2])), columns[3])
    tools = {tool["name"]: tool["inputSchema"] for tool in discovery["tools"]}
    if set(rows) != set(tools):
        raise ValueError("documented tool names differ from discovery")
    failures = []
    for name, (required, optional, bounds) in rows.items():
        schema = tools[name]
        properties = schema.get("properties", {})
        if required & optional or required != set(schema.get("required", [])) or required | optional != set(properties):
            failures.append(name + ": required/optional fields differ")
        if schema.get("additionalProperties") is not False:
            failures.append(name + ": strict input schema expected")
        limit = re.search(r"limit=(\d+)\.\.(\d+)", bounds)
        if "limit" in properties:
            if not limit or [properties["limit"].get("minimum"), properties["limit"].get("maximum")] != [int(limit[1]), int(limit[2])]:
                failures.append(name + ": limit range differs")
        if "mode" in properties and properties["mode"].get("enum") != ["steer", "queue", "restart"]:
            failures.append(name + ": mode enum differs")
        if "offset" in properties and properties["offset"].get("minimum") != 0:
            failures.append(name + ": offset minimum differs")
        if "scope" in properties:
            scope = properties["scope"]
            if set(scope.get("properties", {})) != {"mode", "workspace_ids"} or scope.get("required") != ["mode"]:
                failures.append(name + ": nested scope fields differ")
    if failures:
        raise ValueError("; ".join(failures))
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc", type=Path, default=Path(__file__).resolve().parents[2] / "docs/fast-access-protocol.md")
    parser.add_argument("--schema", type=Path, help="Previously captured tools/list JSON (offline recheck only)")
    parser.add_argument("--save-schema", type=Path, help="Save discovered names/input schemas; review before sharing")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Executable and arguments after --, e.g. multica mcp serve")
    args = parser.parse_args()
    try:
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        if bool(command) == bool(args.schema):
            raise ValueError("choose either --schema or an MCP command")
        discovery = json.loads(args.schema.read_text()) if args.schema else discover(command)
        if args.save_schema:
            args.save_schema.write_text(json.dumps(discovery, indent=2) + "\n")
        count = check(args.doc.read_text(), discovery)
        print(f"PASS: {count} tools; required/optional fields, strictness and declared schema bounds match")
        print("No tools/call requests sent; no business API or write was invoked")
        return 0
    except (OSError, KeyError, ValueError, IndexError) as error:
        # Avoid logging arbitrary process output, environment, endpoint or credential values.
        print("FAIL: MCP contract check did not pass", file=sys.stderr)
        if isinstance(error, ValueError) and not isinstance(error, json.JSONDecodeError):
            print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
