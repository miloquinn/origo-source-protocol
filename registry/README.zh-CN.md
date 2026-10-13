# ORSP Registry 参考格式

[English](README.md)

本目录是联邦式 ORSP Registry 的非官方参考实现。Origo X 项目不运营活动书源目录、
不接受书源收录投稿，也不会把 `registry/generated/registry.json` 分发给官方 App。

独立社区如果愿意自行承担审核、权利投诉、安全和下架治理责任，可以复用或 Fork 这里的
Schema 与工具。由第三方运营的 Registry 是独立服务，不受本项目背书或控制。

## 参考目录结构

```text
registry/sources/<source-id>.json
registry/status/<source-id>.json
registry/generated/registry.json
```

文件名必须与条目中的 `id` 一致。生成文件来自 `registry/sources/` 下的条目；本仓库会
刻意保持该目录为空。

参考字段包括 `discoveryUrl`、`maintainers`、`description`、`languages`、
`contentTypes`、`testQuery` 和可选的 `reportingUrl`。通过协议测试不证明内容合法、优质、
已获授权或运营者可信。

`registry/status/` 可以保存某书源最新的有界诊断记录，格式由
`schemas/source-status.schema.json` 校验。记录只包含 profile、时间、阶段结果和有界
延迟；不得包含读者 IP、正文、Cookie、凭据、内部 URL 或浏览器验证资料。状态文件属于
Registry 元数据，不能替代书源自己的发现文档。

## 参考检查工具

```bash
python scripts/registry_tool.py validate
python scripts/registry_tool.py build --check
python scripts/registry_tool.py check-source path/to/source-entry.json
python scripts/registry_tool.py check-source path/to/source-entry.json --profile discovery
```

这些工具只检查格式和网络安全边界，不认证内容权利。独立 Registry 运营者应采用至少与
[POLICY.zh-CN.md](POLICY.zh-CN.md) 同等严格的审核与下架政策，并提供自己的公开举报渠道。

官方项目的书源分发边界见 [SOURCE_POLICY.zh-CN.md](../SOURCE_POLICY.zh-CN.md)。

1.6 候选的核心诊断使用共享章节 Schema，可检查声明了对应能力的图片/录音 JSON 描述，
会严格报告缺少 title 等字段。诊断不下载媒体，不验证播放；完整媒体验收和允许 HTTP 的
读取采样分别见[完整阅读指南](../docs/source-upgrade-guide.zh-CN.md)。本目录网络策略仍为 HTTPS。
