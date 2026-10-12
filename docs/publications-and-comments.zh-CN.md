# EPUB、评论与段评扩展合同

当前核心版本 **ORSP 1.5**；[OEP-0004](../OEP-0004-publications-and-comments.md)
是本扩展的英文合同。EPUB 为实验能力；评论、段评和写入为草案。
不得把未实现的能力写进发现文档，也不破坏现有搜索、详情、目录、正文接口。

## 当前元创接入

- 名称：元创；稳定书源 ID：`origo-yuanchuang`。
- 地址：`https://creator.xxread.top/.well-known/open-reading-source.json`。
- 基础 API：`https://creator.xxread.top/api/orsp/`。
- 开元阅读现有 ORSP 1.x 导入即可使用；公开 EPUB 可按文本章节阅读，也能下载完整原文件。
- 个人草稿不进入书源。此次不发布评论或段评写入服务。

## 可选能力

| 发现能力 | 端点关系 | 状态 |
| --- | --- | --- |
| `top.xxread:publications` | `GET v1/books/{bookId}/publications` | 元创已实现 |
| `top.xxread:comments` | `GET v1/books/{bookId}/comments` | 草案 |
| `top.xxread:paragraph-comments` | 评论筛选 `chapterId`、canonical anchor | 草案，依赖 comments |
| `top.xxread:comment-write` | `POST .../comments`、`DELETE .../comments/{id}` | 草案，依赖 comments |

EPUB 元数据包含不复用的出版文件 ID、HTTPS 下载地址、MIME、字节数与 SHA-256。
客户端完成大小限制和完整性校验后交给已有 EPUB 阅读器，保留原排版。
不能把 EPUB ZIP 当成章节 JSON，不能把纯文本投影冒充完整 EPUB 阅读体验。

## 评论与段评

普通评论绑定作品 UUID；段评另外绑定章节 ID、内容版本和文字选择器。
评论正文是纯文本，作者 ID 必须由服务端验证身份后取得，不能信任客户端提交。
公开作者仅包含 ID 与展示名，不包含邮箱、设备信息、令牌。

文字锚点采用 Unicode 码点 `[start,end)`，同时保存 exact/prefix/suffix 引文。
`contentVersion` 是 canonicalText 原文 UTF-8 的 SHA-256。
字号、设备、页码、DOM 序号和字体变化都不能改变锚点身份。
Markdown 的原文位置与渲染位置必须显式映射，不能混用；EPUB CFI 使用独立选择器，
绑定不可变 EPUB 文件 SHA-256 和包内资源，不能直接冒充文本偏移。
版本/引文不匹配返回 409；旧评论不能静默挂到新版的另一段上。

读评论与发评论分开声明。将来开放写入之前，需实现源专用令牌授权、幂等、限流、
举报审核、删除和隐私边界。开元/Origo 令牌不得转发给任意第三方书源。
分页使用限定到作品和筛选条件的游标；评论编辑/删除不修改正文锚点版本。

结构定义见 [Schema](../schemas/creator-extensions.schema.json)，端点见
[OpenAPI](../extensions.openapi.yaml)。保留旧接口，新增能力由客户端按发现声明启用；
以后只有无法兼容的语义变更才走新的主版本和明确迁移方案。
