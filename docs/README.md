# 项目文档

- [项目词汇表](../CONTEXT.md)
- [架构决定](adr/)
- [证据索引](evidence/INDEX.md)

可复跑的操作手册放在本目录，并从这里建立入口。当前内容为连接方案说明与脱敏示例；部署验证范围以对应票据证据为准。

## 连接方案

- [架构说明](architecture.md)：角色、通路与既有设计原则。
- [Multica 接入](multica-integration.md)：Bot 身份、写入归因、CLI 与叫醒规则。
- [Grok Bot 接入](grok.md)：Tailscale、SSH、守护与已知问题。
- [添加新 Bot](adding-a-new-bot.md)：新增平台的接入和验证清单。

## 示例与研究

- [Bot 长期指令](../examples/standing-instructions.md)
- [Webhook 示例](../examples/webhook/README.md)
- [执行信箱示例](../examples/mailbox/README.md)
- [SSH 配置示例](../examples/ssh/ssh_config.example) / [守护脚本示例](../examples/ssh/ensure-remote.sh)
- [Yobiru 研究（中文）](../research/yobiru.zh-CN.md) / [English](../research/yobiru.md)
- [贡献约定](../CONTRIBUTING.md)
