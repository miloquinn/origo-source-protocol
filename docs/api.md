# ORSP 1.6 API 索引

协议保持 HTTP JSON 和现有 `apiBaseUrl`，版本放在发现文档与 `v1/` 关系中。
元创平台、Origo Account 和阅读客户端各自独立，不把发布后台、登录或积分接口加入书源核心。

| GET 关系 | 使用条件 | 权威合同 |
| --- | --- | --- |
| 原点 `/.well-known/open-reading-source.json` | 必须 | `schemas/discovery.schema.json` |
| `v1/search`、`v1/books/{bookId}` | 必须 | `openapi.yaml` |
| `v1/books/{bookId}/chapters`、`.../chapters/{chapterId}` | 必须；媒体需单独声明 | `openapi.yaml`、OEP-0006 |
| `v1/discover`、`v1/categories`、`v1/browse` | 各自声明能力；categories 依赖 browse | `openapi.yaml` |
| `v1/rankings`、`v1/rankings/{rankingId}` | rankings | `openapi.yaml`、OEP-0007 |
| `v1/books/{bookId}/updates` | top.xxread:chapter-updates | `chapter-updates.openapi.yaml`、OEP-0005 |
| `v1/books/{bookId}/publications` | top.xxread:publications | `extensions.openapi.yaml`、OEP-0004 |

整本 EPUB 和媒体使用返回的绝对 URL。EPUB 不塞进章节正文；录音不混进正文配乐。
榜单 rank 属于榜单快照关系，不放在共享 Book 上。章节更新保留原目录接口，带版本查询
只用于支持该扩展的源。评论写入与认证仍为独立草案，不能仅有接口文档就声明上线。

源开发者的操作、回退和验证流程见[完整阅读指南](source-upgrade-guide.zh-CN.md)。
