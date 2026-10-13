# ORSP 1.6 完整阅读能力与书源升级指南

这是 **1.6 候选版本**，核心接口保持 ORSP 1.x 兼容。章节更新、EPUB、图片序列和
录音采用可选实验配置；多榜单是可选标准能力。不要仅修改版本号就声称实现了这些功能。
此仓库维护协议和参考实现；元创生产平台在独立的 `origo-creator` 仓库中。

## 能力与接口

所有 `v1/...` 路径都相对发现文档的 `apiBaseUrl` 解析。保留源、书籍、章节的稳定 ID，
不要把域名、分页位置或临时下载地址作为内容身份。

| 能力 | 声明 | 接口或正文形式 | 验收重点 |
| --- | --- | --- | --- |
| 文字、图文文章 | 核心 `content` | `text/plain`、`text/markdown`、`text/html` | MD 图片、相对 URL、HTML 安全处理 |
| 新章节与正文修订 | `top.xxread:chapter-updates` | `v1/books/{bookId}/updates`，原目录附加版本字段 | 新增、改文、删章、重排、跨页快照一致 |
| EPUB 整本阅读 | `top.xxread:publications` | `v1/books/{bookId}/publications` | 原始 EPUB 文件、字节数、SHA-256、不可变文件身份 |
| 图片序列 | `top.xxread:image-sequence` | 原正文接口，`image/sequence` + `images` | 图片顺序、实际文件、懒加载、资源限制 |
| 录音听书 | `top.xxread:remote-audio` | 原正文接口，`audio/uri` + `audio` | 音频格式、分段/Range、过期地址刷新、秒级进度 |
| 多榜单 | `rankings` | `v1/rankings`、`v1/rankings/{rankingId}` | 至少两个榜单、绝对排名、分页快照 |

`browse?sort=popular` 保持原语义；多榜单不挤占这个接口。客户端 TTS 是阅读器自己的
能力，录音听书不等同于 TTS。文章背景配乐仍是未来独立能力，不能冒充一章音频。

## 发现文档与媒体字段

`contentTypes` 可选；缺省表示旧源未声明。它列出章节形式，不把 `application/epub+zip`
混进来。声明图片或音频能力时，必须同时列出相应正文类型；反方向也成立。

```json
{
  "protocol": "open-reading-source",
  "protocolVersion": "1.6",
  "id": "org.example.original-reading",
  "name": "Original reading",
  "apiBaseUrl": "https://books.example.org/api/",
  "capabilities": ["search", "detail", "catalog", "content", "rankings",
    "top.xxread:chapter-updates", "top.xxread:publications",
    "top.xxread:image-sequence", "top.xxread:remote-audio"],
  "contentTypes": ["text/plain", "text/markdown", "text/html", "image/sequence", "audio/uri"]
}
```

图片章节保留 `bookId`、`chapterId`、`title`，`content` 为空，`images` 非空，不能混入
`audio`。音频章节使用同样的身份字段和空正文，提供 `audio.url`，不能混入 `images`。
书籍可提供 `mediaKind`；为了兼容现有开元解析器，同时提供 `type`：文字 8、图片 64、
音频 32。新客户端遇到陌生形式应明确提示不支持，不能猜成文字。

媒体地址必须是绝对 HTTP(S) URL，不带用户名/密码。`headers` 只允许公开的 `Referer`、
`Origin`、`Accept` 提示，禁止把上游 Cookie、用户令牌交给读者。可选 `expiresAt`
告诉客户端何时刷新原章节；过期或媒体返回 401/403/404/410 后，最多刷新一次，
地址变化才重试。不要循环请求，也不要换成用户登录凭据。HLS 的声明与传输见 OEP-0006；
当前参考实现验收的是 WAV 文件与 Range，不能据此声称真机 HLS 已验收。

## 更新与缓存

新增章节、修改旧正文、删除或重排章节，都应改变对应的 `catalogVersion`。不能仅依赖
总章节数或最新章节标题。文字 `contentVersion` 使用精确正文 UTF-8 字节的 SHA-256；
媒体采用覆盖实际资源版本与顺序的修订指纹，不是空字符串的 SHA-256。

客户端先读取更新状态，再携带 `catalogVersion` 加载目录；发生 409 时重新读取状态，
丢弃旧快照下已经加载的分页。原接口查询参数只能发给声明了更新能力的源。304 表示同一
请求的表示未变化，不能比较不同页 ETag 来推导整本版本。媒体签名地址换新而内容未变，
可以保持逻辑修订版本。

EPUB 作为整本 publication 下载，已有文字章节留给原读取链路。文件变化要更换
publication ID；文件 SHA-256 与文本修订版本分别使用各自字段。

## 书源升级顺序

1. 先让旧核心链路严格合规，尤其是正文的 `title` 和请求/响应 ID 对齐。
2. 实现可靠目录更新，补齐逐章修订版本，再提供更新状态与快照冲突处理。
3. 添加可用 EPUB 文件和 publication 元数据，验证文件大小与哈希。
4. 添加图文、图片或录音作品；实现对应能力之后再声明能力和正文类型。
5. 添加多个榜单，验证跨页排名与 `snapshotId`，不要伪造多个相同列表。
6. 通过 Schema、HTTP 检查和目标阅读器联调，再更新发现文档版本。

已有 1.1/1.4/1.5 源无需一次实现全部能力。不要更换源 ID，不删除旧接口，不自动向
未知源发送新的查询参数。第三方运营者需要在自己的服务器部署实现，升级协议仓库不会
自动更新其他人的书源。

## 可运行验证

Python 参考实现与验证工具需要 Python 3.11 或更新版本。

```bash
python -m pip install jsonschema pyyaml openapi-spec-validator
python scripts/validate_contracts.py
python scripts/validate_creator_extensions.py
python scripts/validate_chapter_updates.py
python scripts/validate_reading_profiles.py
python scripts/test_probe_source.py
dart run tool/conformance_test.dart
dart run tool/discovery_conformance_test.dart

# 输出临时本地端口；样例只含原创文字、生成图片和测试音频。
python examples/reading_profiles_server.py

# 仅 GET，不保存正文，不访问未声明的可选接口。
python scripts/probe_source.py https://books.example.org/.well-known/open-reading-source.json
```

检查工具默认禁止私网，`--allow-loopback` 只用于本地示例。最多 20 次 HTTP 请求（含
重定向），单次 JSON 上限 1 MiB，发现文档上限 64 KiB，连接/读取超时 12 秒。
失败退出码为 1；无数据时明确报告未完成阅读采样。它只采样一书一章及一页榜单，
通过采样不等于全部能力已验收。

## 当前接入证据与边界

| 项目 | 本轮确认 | 尚未确认 |
| --- | --- | --- |
| 协议参考源 | 原创文字、MD 图片、图片序列、WAV、过期刷新、EPUB、更新快照、多榜单 HTTP | 生产负载与平台特定播放器 |
| 现有 Origo X | 1.6/1.1 发现解析、媒体数字类型、图片/音频章节解析、旧文字回退 | 新榜单 UI、更新状态接入、EPUB 整本自动导入、真机播放与安全请求策略 |
| 用户提供的 110.42.63.158 源 | 1.1；核心和发现接口可访问，正文为 HTML | 正文缺少必需 title；未声明新增能力 |
| 元创生产源 | 已部署 1.5、公开文字章节、EPUB 与章节更新接口 | 本轮未修改生产源，不声称新增媒体与榜单已部署 |

最新指南是本文件；[Schema 索引](Schema.md)、[API 索引](api.md) 指向机器契约的单一真相源。
第三方书源的本轮观测见 [2026-10-13 检查记录](source-audit-2026-10-13.md)。
