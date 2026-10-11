# 项目地图

本文件只记录仓库特有且长期稳定的事实。

virtual-bot-connect 整理云端 Bot 与 Multica 智能体互通的连接方案，供他人复用。仓库以文档、研究笔记和脱敏示例交付；桥接脚本与 Multica 服务端改动尚未在这里发布。示例字段仅作示意，不能作为当前服务端协议的依据。

- 领域词汇表：[CONTEXT.md](CONTEXT.md)
- 文档索引：[docs/README.md](docs/README.md)
- 架构决定：[docs/adr/](docs/adr/)
- 证据索引：[docs/evidence/INDEX.md](docs/evidence/INDEX.md)
- 面向使用者的概览：[README.md](README.md) / [中文说明](README.zh-CN.md)

## 工作边界

项目工作单住 Multica。票、聊天、状态和文件以 Multica 为账本；云端 Bot 是客户端。连接角色、通路和既有设计原则以 [architecture.md](docs/architecture.md) 为入口。

这是公开分享的仓库。提交内容仅使用脱敏值或占位符；token、密钥、密码、真实 webhook 地址、Tailscale 节点名/IP、邮箱和内部主机信息留在仓库外。贡献与扫描要求见 [CONTRIBUTING.md](CONTRIBUTING.md)，推送前须扫描完整 Git 历史。

新增平台接入说明时从 [添加新 Bot](docs/adding-a-new-bot.md) 开始；记录实际验证范围。研究结论从 [Yobiru 对照笔记](research/yobiru.zh-CN.md) 读取，部署事实从对应票据证据读取。
