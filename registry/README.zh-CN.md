# ORSP Registry 参考格式

[English](README.md)

本目录是联邦式 ORSP Registry 的非官方参考实现。Open Reading 项目不运营活动书源目录、
不接受书源收录投稿，也不会把 `registry/generated/registry.json` 分发给官方 App。

独立社区如果愿意自行承担审核、权利投诉、安全和下架治理责任，可以复用或 Fork 这里的
Schema 与工具。由第三方运营的 Registry 是独立服务，不受本项目背书或控制。

## 参考目录结构

```text
registry/sources/<source-id>.json
registry/generated/registry.json
```

文件名必须与条目中的 `id` 一致。生成文件来自 `registry/sources/` 下的条目；本仓库会
刻意保持该目录为空。

参考字段包括 `discoveryUrl`、`maintainers`、`description`、`languages`、
`contentTypes`、`testQuery` 和可选的 `reportingUrl`。通过协议测试不证明内容合法、优质、
已获授权或运营者可信。

## 参考检查工具

```bash
python scripts/registry_tool.py validate
python scripts/registry_tool.py build --check
python scripts/registry_tool.py check-source path/to/source-entry.json
```

这些工具只检查格式和网络安全边界，不认证内容权利。独立 Registry 运营者应采用至少与
[POLICY.zh-CN.md](POLICY.zh-CN.md) 同等严格的审核与下架政策，并提供自己的公开举报渠道。

官方项目的书源分发边界见 [SOURCE_POLICY.zh-CN.md](../SOURCE_POLICY.zh-CN.md)。
