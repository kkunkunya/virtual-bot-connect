#!/usr/bin/env bash
# Sketch of the watchdog that runs on the bot computer (from its routine, and after a resume).
# Adapt names and paths; this is illustrative, not a drop-in script.
set -euo pipefail

STATE_DIR=/workspace/remote
PINNED_HOSTS="$STATE_DIR/hosts.pinned"   # lines like "<real-ip> <control-plane-host>"
OFFLINE_GRACE=15                         # seconds

# 1. Re-apply pinned host entries lost on reset (a fake-IP DNS proxy stalls Tailscale's long-poll).
if [ -f "$PINNED_HOSTS" ]; then
  while read -r line; do
    [ -z "$line" ] && continue
    grep -qxF "$line" /etc/hosts || echo "$line" | sudo tee -a /etc/hosts >/dev/null
  done < "$PINNED_HOSTS"
fi

# 2. Make sure tailscaled is running and the node is online; restart if offline too long.
online() { tailscale status --json 2>/dev/null | grep -q '"Online": *true'; }
if ! pgrep -x tailscaled >/dev/null; then
  sudo tailscaled --state="$STATE_DIR/tailscaled.state" >/dev/null 2>&1 &
  sleep 3
fi
waited=0
until online; do
  sleep 1; waited=$((waited + 1))
  if [ "$waited" -ge "$OFFLINE_GRACE" ]; then
    sudo pkill -x tailscaled || true
    sudo tailscaled --state="$STATE_DIR/tailscaled.state" >/dev/null 2>&1 &
    sleep 3
    sudo tailscale up --hostname="<bot-host>" --ssh=false
    break
  fi
done

# 3. Keep sshd (key-only, high port) up.
pgrep -f "sshd.*<ssh-port>" >/dev/null || sudo /usr/sbin/sshd -p "<ssh-port>"
