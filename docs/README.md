# 项目文档 · Docs

- [项目词汇表](../CONTEXT.md)
- [架构决定](adr/)
- [证据索引](evidence/INDEX.md)

通用方案放在本目录；绑定某一套真实环境的内容放在 `examples/<setup>/`。部署验证范围以对应票据证据为准。

## 通用方案

- [四个部件 · The four pieces](primitives.md)：信箱、叫醒、权限、全程留痕，各自的可选做法与规矩。
- [添加新 Bot · Adding a new bot](adding-a-new-bot.md)：新平台的能力问答与验收清单。
- [实战经验](lessons-learned.zh-CN.md) · [Lessons learned](lessons-learned.md)：分工、推送、叫醒上限、换钥匙、巡检、留痕搬家。
- [给 agent 的接入手册 · AGENTS.md](../AGENTS.md)

- [Fast-access protocol v1](fast-access-protocol.md)：紧凑读取、可靠续传和只读摘要缓存；[可运行示例](../examples/fast-access-client/README.md) 使用假数据，未宣称生产联调通过。

## 实际例子：Mac + Multica + Grok Bot

- [概览](../examples/kun-mac-multica-grok/README.md)
- [架构说明](../examples/kun-mac-multica-grok/architecture.md)：角色、通路与既有设计原则。
- [Multica 接入](../examples/kun-mac-multica-grok/multica-integration.md)：Bot 身份、写入归因、CLI 与叫醒规则。
- [Grok Bot 接入](../examples/kun-mac-multica-grok/grok.md)：Tailscale、SSH、守护与已知问题。
- [Bot 长期指令](../examples/kun-mac-multica-grok/standing-instructions.md)
- [Webhook 示例](../examples/kun-mac-multica-grok/webhook/README.md) / [执行信箱示例](../examples/kun-mac-multica-grok/mailbox/README.md)
- [SSH 配置示例](../examples/kun-mac-multica-grok/ssh/ssh_config.example) / [守护脚本示例](../examples/kun-mac-multica-grok/ssh/ensure-remote.sh)

## 研究

- [对标 4 个高传播仓库](../research/benchmark.md)
- [Yobiru 研究（中文）](../research/yobiru.zh-CN.md) / [English](../research/yobiru.md)
- [贡献约定](../CONTRIBUTING.md)
