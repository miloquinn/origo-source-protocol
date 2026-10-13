# ORSP 1.6 Schema 索引

ORSP 全称为 Origo Source Protocol，属于 Origo X 元源生态。
发现 `protocol` 首选 `origo-source`，Schema 同时接受旧 `open-reading-source` 以兼容已有 1.x 书源；其他标识无效。
发现、API 与资源 URL 均支持 HTTP 和 HTTPS，公开服务推荐 HTTPS。稳定 ID 与数据字段语义不因改名改变。

本文索引机器契约，不复制字段定义。变更字段时修改规范与对应 Schema，同步生成 OpenAPI，
运行验证脚本。候选能力及接入状态见[完整阅读指南](source-upgrade-guide.zh-CN.md)。

| 数据 | 单一字段契约 | 实现与校验 |
| --- | --- | --- |
| 发现文档、能力、contentTypes | `schemas/discovery.schema.json` | `scripts/validate_contracts.py` |
| 书籍、文字正文、目录、榜单 | `openapi.yaml` | Dart 核心套件、`scripts/validate_reading_profiles.py` |
| 图片、音频与公开请求提示 | `schemas/media-reading.schema.json` | `scripts/build_media_openapi.py` 生成核心 OpenAPI 的媒体组件 |
| 更新状态、目录快照、逐章版本 | `schemas/chapter-updates.schema.json` | `scripts/build_chapter_updates_openapi.py` → `chapter-updates.openapi.yaml` |
| EPUB、评论与段评草案 | `schemas/creator-extensions.schema.json` | `scripts/build_creator_openapi.py` → `extensions.openapi.yaml` |

源 ID 全局稳定，书籍和章节 ID 是源内身份；客户端使用 `(sourceId, bookId, chapterId)`。
核心 opaque ID 为 1–200 字符的 ASCII 安全令牌，不是 URL、章节页码或数据库的跨源主键。
未知 JSON 字段与可选能力允许忽略；未知正文类型需要明确拒绝。

`catalogVersion` 是整本目录快照令牌，逐章 `contentVersion` 是正文修订版本。
EPUB `sha256` 是文件完整性校验；媒体修订指纹不能充当文件校验。可选字段无值时省略，
不能用 null 代替。规范冲突以对应 OEP 与机器契约修复为准，不另造同名字段。
