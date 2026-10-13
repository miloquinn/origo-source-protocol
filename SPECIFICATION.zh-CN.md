# 开放阅读书源协议 1.6

[English normative specification](SPECIFICATION.md)

状态：**候选草案**

> 本文是 `SPECIFICATION.md` 的简体中文翻译，方便中文开发者理解和实现。
> 英文原文是规范性文本；如果翻译与英文原文存在冲突，以英文原文为准。

本文中的“必须（MUST）”“不得（MUST NOT）”“应当（SHOULD）”“不应当
（SHOULD NOT）”和“可以（MAY）”按照 RFC 2119 与 RFC 8174 解释。

## 名称与安全传输

产品名称为 **Origo X**，书源生态名称为 **Origo Source（元源）**，
ORSP 全称为 **Origo Source Protocol**。新书源必须在
`/.well-known/origo-source.json` 使用 `protocol: origo-source`。
新客户端必须接受此标识与旧 `open-reading-source`，拒绝其他未知标识。
1.x JSON 语义及 `v1/...` 接口保持兼容；书源、书籍、章节 ID 不因改名改变。

为服务已安装的旧阅读器，新 1.x 书源必须同时提供
`/.well-known/open-reading-source.json`，此兼容入口仍返回旧标识，且与新入口
具有相同的书源 ID、来源、API 基址和能力，不能重定向到返回新标识的文档。
它不是第二个书源。已有旧书源无需立即新增入口。
新响应头使用 `X-Origo-Source-Protocol`，迁移期应当同时返回等值的
`X-Open-Reading-Protocol`。旧 `X-Open-Reading-Request-Purpose` 与新
`X-Origo-Source-Request-Purpose` 具有相同的建议性语义，新头优先。

协议支持 `http://` 和 `https://`；接口与状态描述中的 HTTP 同时适用于两种传输。
公开生产环境的发现文档、API、EPUB 和媒体资源应当使用 HTTPS。
HTTPS 客户端必须验证证书链及主机名，不得静默降级至 HTTP。
服务应当使用 TLS 1.2 或更新版本；可由反向代理终止 TLS，私有上游使用 HTTP。
本地开发可以使用 HTTP。HTTP/2、HTTP/3 由部署层协商，不改变 JSON 合同，
也不作为核心阅读的强制要求。

## 1. 范围和设计目标

开放阅读书源协议（Origo Source Protocol，ORSP）定义了阅读客户端与独立内容
书源之间安全的 HTTP(S) 边界。ORSP 1.6 包括：

- 书源发现；
- 书籍搜索与元数据；
- 可选的推荐发现、分类、浏览和多榜单；
- 章节目录；
- 章节正文获取。

完整阅读能力还包括独立声明的实验配置：EPUB 整本文件（OEP-0004）、章节更新
（OEP-0005）、图片序列与录音听书（OEP-0006）。这些能力各自有契约和验收，
不强制每个小型书源全部实现。

ORSP 1.6 面向不要求用户认证的公开 HTTP(S) 书源。它不定义可执行的抓取规则。书源可以
在服务端内部使用已获授权的适配器，但客户端只能接收本协议定义的数据。

核心阅读配置应保持精简。符合 ORSP 1.6 的书源必须完整实现发现、搜索、详情、目录和正文
链路。可选功能通过能力标识声明，不得改变核心字段或接口的含义。

## 2. 协议版本与演进

协议版本使用 `主版本.次版本`，例如 `1.0`。它不是软件包的语义化版本号，不得包含修订号。

- 主版本可以引入不兼容变更；
- 次版本可以新增可选对象字段、可选能力标识、可选接口，或增加具有明确回退规则的枚举值；
- 次版本不得删除或重新解释现有字段，不得把可选字段改为必填字段，也不得改变现有 HTTP
  状态码的含义；
- 除非作为新能力标识的一部分，次版本不得给现有接口新增请求查询参数。书源未声明对应
  能力时，客户端不得发送该参数。这样参数支持始终是显式的：客户端依赖某个参数的效果
  时，书源不会静默忽略它。

实现 ORSP 1.x 的客户端应当接受主版本为 `1` 的发现文档。只有当所有 1.x 实现都遵守本文
规定的向前兼容规则时，这种行为才是安全的。

`protocolVersion` 标识发现文档本身遵循的协议版本。实现多个协议版本的书源应当同时在
可选的 `supportedVersions` 发现字段（第 3 节）中列出全部已实现版本。接口关系自带主版本
前缀（`v1/...`），因此同一个 `apiBaseUrl` 可以并行服务多个主版本。跨主版本的完整协商
规则属于保留的未来工作（第 17 节）；在主版本 1 内，`supportedVersions` 仅供参考。

客户端必须忽略未知的 JSON 对象字段和未知的可选能力标识。书源不得要求客户端理解某个
扩展能力，才能完成核心阅读配置中的发现、搜索、详情、目录或正文操作。

字段缺失与字段值为 `null` 是不同的状态。无法提供可选字段时，书源必须省略该字段。除非
Schema 明确允许，否则书源不得返回 `null`。

## 3. 书源发现

书源必须在站点根路径提供 JSON 发现文档：

```text
/.well-known/origo-source.json
```

客户端也可以接受用户或书源目录提供的完整发现文档 URL。重定向规则见第 5 节。

发现文档必填字段：

| 字段 | 要求 |
| --- | --- |
| `protocol` | 必须等于 `origo-source` |
| `protocolVersion` | ORSP `主版本.次版本`；本文使用 `1.6` |
| `id` | 稳定且全局唯一的书源标识 |
| `name` | 面向用户的书源名称 |
| `apiBaseUrl` | 以 `/` 结尾的绝对 HTTP(S) URL |
| `capabilities` | 必须包含全部四项核心能力 |

四项核心能力是 `search`、`detail`、`catalog` 和 `content`。

ORSP 1.6 定义四项可选的标准能力：

| 能力 | 接口关系 | 用途 |
| --- | --- | --- |
| `discover` | `v1/discover` | 推荐、热门等策划书架 |
| `categories` | `v1/categories` | 稳定的分类 ID 和显示名称 |
| `browse` | `v1/browse` | 按分类或标准排序分页浏览 |
| `rankings` | `v1/rankings` | 多个具名、可分页的榜单 |

声明 `categories` 的书源必须同时声明 `browse`，因为分类 ID 用于浏览接口。书源可以只声明
`browse` 而不声明 `categories`，例如只提供最新更新列表。这些能力都是可选的；缺少它们
不得影响核心搜索和阅读能力。

扩展能力必须使用防冲突命名空间，格式为 `反向域名:名称`，例如
`org.example:audio`。除非由后续 ORSP 规范定义，否则扩展不得使用 `orsp` 命名空间。
客户端遇到未知扩展能力时，不得因此判定书源不兼容。

发现文档的可选字段包括 `description`、`iconUrl`、`websiteUrl`、`languages`、
`supportedVersions`、`maxCatalogPageSize`、`operatorName`、`contactUrl`、
`contentLicense`、`rightsStatement` 和 `contentTypes`。语言必须使用 BCP 47 标签，例如 `en`、
`zh-CN` 或 `sr-Latn`。

`contentTypes` 列出书源可能返回的章节形式，不能包含 EPUB 文件的 MIME 类型；出现时
是最多 32 项的非空、无重复、小写媒体类型数组。旧源缺省表示未声明。未知类型不能
阻止导入书源，但打开章节时必须明确处理不支持的形式。声明 `image/sequence` 必须
同时声明 `top.xxread:image-sequence`；声明 `audio/uri` 必须同时声明
`top.xxread:remote-audio`。声明任一媒体能力，也必须在 `contentTypes` 中包含对应类型。
这是能力预告，不是请求级 Accept 协商。

`supportedVersions` 是非空的 ORSP `主版本.次版本` 字符串数组，出现时必须包含
`protocolVersion`，用于让多版本书源声明自己实现的全部协议版本。ORSP 1.6 客户端可以
将其用于诊断，但不得依赖它。

`maxCatalogPageSize` 是 1 至 1000 之间的整数，声明章节目录接口（第 12 节）接受的
最大 `pageSize`。省略时上限为 100。

`operatorName`、`contactUrl`、`contentLicense` 和 `rightsStatement` 是权利透明度
字段。`operatorName` 标识实际运营该书源、能够处理权利请求的主体。`contactUrl` 如果
出现，必须是该运营者控制的绝对 HTTP(S) 联系或权利投诉页面。`contentLicense` 是简短
的许可名称或授权依据，例如 `CC BY 4.0` 或 `Public Domain`。`rightsStatement` 是书源
自行提供的内容来源或授权范围简述。客户端可以为了透明度展示这些字段，但不得把它们的
存在、缺失或内容当作任何阅读器、注册表或协议本身对合法性、授权或身份的认证。

`apiBaseUrl` 不得包含用户名、密码、查询参数或片段，并且必须以 `/` 结尾。本文接口路径
相对于该 URL 解析。例如，API 基础地址为 `https://books.example/api/`，接口关系为
`v1/search`，最终地址就是 `https://books.example/api/v1/search`。

书源 `id` 长度必须为 3 至 200 个字符，首尾必须是 ASCII 字母或数字，中间只能包含
ASCII 字母、数字、`.`、`_` 或 `-`。书源更换域名、API 地址或显示名称时不得修改 `id`。
推荐使用反向域名形式。书源 ID 只标识书源；书籍和章节 ID 的作用域是该书源。

书源 ID 没有中央分配机构，客户端可能遇到两个不同书源声称同一个 `id`。客户端不得只用
`id` 作为存储键，必须至少以 `id` 加发现文档来源（origin）的组合作为存储书源状态的
键；当不同来源出示相同 `id` 时，不得静默合并或替换已安装的书源，并应向用户提示这一
冲突。只有 `id` 和来源都一致时，两个发现文档才描述同一个书源。

发现文档的机器定义见
[`schemas/discovery.schema.json`](schemas/discovery.schema.json)。

## 4. 数据模型与编码

### 4.1 JSON 和文本

- 请求和响应必须使用 UTF-8；
- JSON 响应必须使用 `application/json`，允许 `charset=utf-8` 等媒体类型参数；
- JSON 字段名区分大小写；
- 客户端必须忽略任意嵌套层级的未知对象字段；
- 书源应当把面向用户的文本规范化为 Unicode NFC；
- 时间戳必须是 RFC 3339 `date-time`，推荐使用带 `Z` 后缀的 UTC 时间。

### 4.2 标识符

书籍和章节 ID 是稳定、不透明的字符串。为了让常见 HTTP 框架产生一致的路由行为，线上
传输的 ID 只能使用 RFC 3986 非保留 ASCII 字符：字母、数字、`-`、`.`、`_` 和 `~`。

ID 长度必须为 1 至 200 个字符。客户端必须把每个 ID 当作一个 URL 路径段处理，不得从
中推断层级或其他含义。书源不得把已经使用过的 ID 分配给另一个逻辑资源。

章节 ID 在一本书内唯一；书籍 ID 在一个书源内唯一。

### 4.3 URL

除非字段另有说明，JSON 中的 URL 必须是绝对 HTTP(S) URL。客户端必须拒绝不支持的 URL
scheme，并应当在下载封面或其他远程资源前应用平台相关的大小限制。

### 4.4 枚举

对于包含 `unknown` 的描述性枚举，客户端遇到未知值时必须回退为 `unknown`。对于
`contentType` 等决定处理方式的枚举，客户端必须报告不支持该表示方式，不得猜测其含义。

## 5. HTTP 行为

- 核心接口使用 `GET`，并且必须是安全且幂等的；
- 客户端应发送 `Accept: application/json`；
- 客户端应通过 `X-Origo-Source-Protocol` 发送自己支持的最高 ORSP 1.x 版本，例如 `1.6`；
- 书源可以通过同名响应头返回自己的协议版本；
- 客户端或运维探针可以发送 `X-Origo-Source-Request-Purpose: health-check`。
  书源应当将带有该值的请求排除在面向读者的统计和排行之外。此请求头仅用于说明用途，
  不得授予访问权限、绕过速率限制或改变内容授权；未发送该头的请求视为用户请求；
- 不支持的方法必须返回 `405 Method Not Allowed`，并应包含 `Allow` 响应头；
- 对于较大的 JSON 响应，书源应支持 HTTP 压缩。

客户端可以跟随重定向，但必须满足：

- 每个请求最多跟随五次重定向；
- 目标必须使用 HTTP(S)；
- 生产客户端不应从 HTTPS 降级到 HTTP；
- 不得向不同源转发凭据或私有请求头。

客户端应设置可配置的连接时间、响应时间、解压后大小和重定向限制。所有书源响应都必须被
视为不可信输入。

### 5.1 缓存

发现文档、推荐书架、分类、浏览页、详情、目录和正文响应应提供 `ETag`，或适当的
`Cache-Control`/`Last-Modified` 响应头。客户端发送当前 `If-None-Match` 时，书源应返回
无响应体的 `304 Not Modified`。

实体标签标识完整的所选表示。只要响应发生客户端可见的变化，书源就必须更新实体标签。

## 6. 搜索

接口关系：

```text
GET v1/search?q={query}&page={page}&pageSize={pageSize}
```

去除首尾空白后，`q` 必填且长度必须为 1 至 200 个 Unicode 标量值。`page` 从 1 开始，
默认值为 1。`pageSize` 默认值为 20，范围必须为 1 至 100。

书源可以忽略未知查询参数；已知查询参数不合法时必须返回 `400`。

响应示例：

```json
{
  "items": [
    {
      "id": "book-1001",
      "title": "示例书籍",
      "author": "示例作者",
      "description": "简短介绍",
      "coverUrl": "https://books.example.org/covers/1001.jpg",
      "categories": ["小说"],
      "status": "completed",
      "latestChapter": "第三十章",
      "language": "zh-CN",
      "updatedAt": "2026-07-11T10:00:00Z"
    }
  ],
  "page": 1,
  "pageSize": 20,
  "total": 1,
  "hasMore": false
}
```

`items`、`page`、`pageSize` 和 `hasMore` 必填。`pageSize` 表示请求的页面容量，不是实际
返回的条目数。部分书源无法高效计算总数，因此 `total` 可选。数据集和查询不变时，搜索
排序应保持确定性。

书籍对象必须包含 `id` 和 `title`，其他字段可选。`language` 必须是 BCP 47 标签。
`status` 可取 `ongoing`、`completed`、`hiatus` 或 `unknown`。

## 7. 推荐发现（可选）

声明 `discover` 的书源必须实现：

```text
GET v1/discover
```

响应示例：

```json
{
  "sections": [
    {
      "id": "featured",
      "title": "推荐",
      "items": [
        {
          "id": "book-1001",
          "title": "示例书籍",
          "author": "示例作者"
        }
      ]
    }
  ]
}
```

`sections` 必填。每个分区必须包含 `id`、`title` 和 `items`。分区 ID 遵循第 4.2 节的
不透明 ID 规则，作用域是当前书源，并应在显示名称改变时保持稳定。分区标题面向用户，
可以按书源内容策略本地化。空分区应省略。

每个分区最多包含 100 本书。书籍对象与搜索和详情使用同一模型。数据集不变时，分区顺序
和书籍排序应保持确定性。除非书源明确记录相关行为，客户端不得把分区解释为个性化结果；
ORSP 1.6 不定义用户认证或用户画像。

## 8. 分类（可选）

声明 `categories` 的书源必须实现：

```text
GET v1/categories
```

响应示例：

```json
{
  "items": [
    {"id": "fiction", "name": "小说"},
    {"id": "history", "name": "历史"}
  ]
}
```

`items` 必填。分类 ID 遵循第 4.2 节的不透明 ID 规则，并且必须能够原样作为浏览接口的
`category` 参数使用。分类名称面向用户。名称变化时，书源应保持 ID 稳定。数据集不变时，
分类顺序应保持确定性。

## 9. 浏览（可选）

声明 `browse` 的书源必须实现：

```text
GET v1/browse?category={categoryId}&sort={sort}&page={page}&pageSize={pageSize}
```

`category` 可选。提供时长度必须为 1 至 200 个字符，并对应 `v1/categories` 返回的分类。
未声明 `categories` 的书源在收到 `category` 参数时必须返回 `400`。

`sort` 可选，默认值为 `latest`。ORSP 1.6 定义：

- `latest`：按照书籍 `updatedAt` 降序排列；没有 `updatedAt` 的书排在有日期的书之后；
- `popular`：由书源定义的热门排序；排名快照不变时必须保持确定性。

不支持的排序值必须返回 `400`。`page` 和 `pageSize` 使用搜索接口的分页规则，响应使用
搜索分页 Schema。省略 `category` 时，接口按照指定排序浏览书源中全部可见书籍。

### 9.1 多书源聚合

连接多个书源的客户端可以在同一个界面聚合推荐分区、分类或浏览结果。聚合客户端：

- 必须为每个分区、分类和书籍保留其来源书源；
- 必须把分区、分类和书籍 ID 视为书源作用域内的标识，不得仅因 ID 或显示名称相同就
  跨书源合并对象；
- 当多个书源的结果可能混淆时，应清晰标注来源，并可以提供“全部书源”和单书源筛选；
- 聚合 `latest` 或 `popular` 列表时，应保留各书源响应内部的顺序，并采用来源均衡的
  合并方式，避免某一书源仅凭返回数量或时间戳占满聚合列表；
- 某一书源超时或失败时，应保留其他书源已经成功返回的结果；当失败影响结果完整性时，
  应让用户能够感知部分失败。

`updatedAt` 用于确定单个书源 `latest` 响应内部的顺序。聚合客户端可以把它作为跨书源的
新鲜度参考，但不得把不同运营方提供的时间戳视为全局权威排名。

## 10. 榜单（可选）

声明 `rankings` 的书源必须实现两个榜单接口关系：

```text
GET v1/rankings
GET v1/rankings/{rankingId}?page={page}&pageSize={pageSize}
```

榜单目录响应：

```json
{
  "items": [
    {
      "id": "weekly-popular",
      "title": "本周热门榜",
      "description": "本周阅读量最高的书籍",
      "period": "weekly",
      "categoryId": "fiction"
    },
    {
      "id": "monthly-new",
      "title": "月度新书榜",
      "period": "monthly"
    }
  ]
}
```

`items` 必填，最多包含 100 个榜单。每个榜单必须包含 `id` 和 `title`。榜单 ID 遵循
第 4.2 节的不透明 ID 规则，作用域是当前书源，并应在显示元数据变化时保持稳定。
`description`、`period` 和 `categoryId` 可选。

`period` 出现时只能是 `realtime`、`daily`、`weekly`、`monthly` 或 `all-time`。如果榜单
周期不符合这些值，书源必须省略 `period`，不得自行创造新的枚举值。`categoryId` 出现时
必须对应 `v1/categories` 返回的分类；因此未声明 `categories` 的书源必须省略
`categoryId`。数据集不变时，榜单目录顺序应保持确定性。

榜单分页响应：

```json
{
  "ranking": {
    "id": "weekly-popular",
    "title": "本周热门榜",
    "period": "weekly"
  },
  "snapshotId": "weekly-popular-2026-w30",
  "snapshotAt": "2026-07-26T00:00:00Z",
  "items": [
    {
      "rank": 1,
      "previousRank": 3,
      "score": 9850,
      "scoreLabel": "9,850 次阅读",
      "book": {
        "id": "book-1001",
        "title": "示例书籍"
      }
    }
  ],
  "page": 1,
  "pageSize": 20,
  "total": 1,
  "hasMore": false
}
```

`ranking`、`snapshotId`、`items`、`page`、`pageSize` 和 `hasMore` 必填。
`ranking` 使用与 `v1/rankings` 相同的榜单对象。`snapshotId` 是有序榜单快照的不透明
标识；只要排名和顺序不变，该值就必须保持不变。`snapshotAt` 可选，记录快照生成时间。
`total` 可选。

每个条目必须包含 `rank` 和 `book`。`rank` 是条目在完整榜单中的从 1 开始的绝对位置，
不是当前分页内的位置。条目必须按照 `rank` 升序返回；同一快照中的排名必须唯一；第 N 页
第一个条目的排名必须等于 `(N - 1) * pageSize + 1`。`book` 使用通用书籍模型。
`previousRank`、`score` 和 `scoreLabel` 可选。`previousRank` 出现时表示该书在书源定义的
上一个可比较快照中的从 1 开始的位置。`score` 的含义和量纲以及 `scoreLabel` 的显示文本
均由书源定义；客户端不得跨榜单或跨书源比较这些值。

`page` 和 `pageSize` 使用搜索接口的分页规则。书源应为榜单目录和每个榜单页返回
`ETag`。客户端加载多个页面时必须比较 `snapshotId`；如果快照发生变化，应从第 1 页
重新加载，避免展示来自不同快照的排名。格式正确但不存在的榜单 ID 必须返回 `404` 和
`RANKING_NOT_FOUND`。

排名只在“书源、榜单 ID、快照 ID”三元组内具有权威性。聚合客户端必须保留该归属，
不得把不同运营方书源的排名展示为一个全局权威榜。客户端可以并排展示各书源榜单，或
生成明确标注为客户端合成的、来源均衡的聚合视图。

## 11. 书籍详情

接口关系：

```text
GET v1/books/{bookId}
```

响应使用与搜索相同的书籍对象，可以包含更长的介绍或更多可选元数据。同一字段在搜索和
详情响应中的含义必须一致。

## 12. 章节目录

接口关系：

```text
GET v1/books/{bookId}/chapters?page={page}&pageSize={pageSize}
```

`page` 默认值为 1。`pageSize` 默认值为 100，上限是书源声明的 `maxCatalogPageSize`
（第 3 节）；未声明时上限为 100。`pageSize` 超出声明上限时，书源必须返回 `400`，
客户端也不得发送这样的请求。长篇连载动辄数千章，有能力提供更大分页的书源应当声明
更高的上限，以减少请求次数。

```json
{
  "items": [
    {
      "id": "chapter-1",
      "title": "第一章",
      "order": 1,
      "updatedAt": "2026-07-11T10:00:00Z"
    }
  ],
  "page": 1,
  "pageSize": 100,
  "total": 1,
  "hasMore": false
}
```

章节对象必须包含 `id`、`title` 和 `order`。`order` 是大于或等于零的整数。书源应在
一本书内使用唯一的顺序值。顺序值相同时，客户端必须使用章节 ID 的升序作为第二排序键。

目录页必须按照 `(order, id)` 排序。书源应为每个目录页提供 `ETag`。ETag 校验对应
页面的表示，不能比较不同页 URL 的 ETag 来判断整本书目录版本。
重新验证同一页面发现变化时应重新加载目录，避免混合数据。书源应提供可靠的章节
`updatedAt`，新增或修订章节时同步更新校验值。

可选实验能力 [OEP-0005](OEP-0005-chapter-updates.md) 补充更新状态、目录版本和逐章正文版本，
详见[中文合同](docs/chapter-updates.zh-CN.md)。旧客户端保留原目录链路；
只有声明此能力的书源才可以发送对应版本参数。

## 13. 章节正文

接口关系：

```text
GET v1/books/{bookId}/chapters/{chapterId}
```

```json
{
  "bookId": "book-1001",
  "chapterId": "chapter-1",
  "title": "第一章",
  "contentType": "text/plain",
  "content": "章节正文",
  "baseUrl": "https://books.example.org/books/book-1001/"
}
```

`bookId` 和 `chapterId` 必须与请求的资源完全一致。`baseUrl` 可选；提供时必须是绝对
HTTP(S) URL。

ORSP 1.6 核心文字正文支持以下类型：

- `text/plain`；
- `text/markdown`，按照 CommonMark 解释；
- `text/html`，内容必须是 HTML 片段而不是完整文档。

相对链接和图片地址优先相对于 `baseUrl` 解析；没有 `baseUrl` 时，相对于最终章节请求
URL 解析。

HTML 不得包含脚本或其他可执行内容。书源应移除事件处理属性、危险 URL scheme、内嵌
框架和活动表单控件。客户端仍然必须在渲染前清理 HTML。Markdown 内嵌 HTML 适用相同规则。

可选 [OEP-0006 媒体配置](OEP-0006-media-reading.md) 在同一个正文接口定义
`image/sequence` 与 `audio/uri`，必须单独声明相应能力。它们保留 bookId、chapterId、
title，正文字符串为空，分别提供有序 images 或 audio 录音描述。书籍的可选
`mediaKind` 为 text、image-sequence、remote-audio，陌生值按 unknown 处理。
兼容现有开元解析器可同时提供数字 type：文字 8、图片 64、音频 32。
旧客户端继续读取文字作品；不能支持媒体作品时明确提示，不把二进制猜成文字。

录音不同于客户端 TTS；EPUB 是整本 publication，不能作为章节 ZIP 正文返回。
媒体配置定义过期元数据、有限刷新与公开请求提示。媒体 contentVersion 是修订指纹，
不能当作文件完整性校验；文件校验必须有单独 sha256 字段。接入与验收见
[完整阅读指南](docs/source-upgrade-guide.zh-CN.md)。

## 14. 错误

核心状态码：

| 状态码 | 含义 |
| --- | --- |
| `304` | 所选表示没有变化 |
| `400` | 请求参数或 ID 不合法 |
| `404` | 书籍、章节、榜单或路由不存在 |
| `405` | 不支持该 HTTP 方法 |
| `429` | 请求过于频繁；应包含 `Retry-After` |
| `500` | 书源内部错误 |
| `503` | 书源暂时不可用；可以包含 `Retry-After` |

除不能包含响应体的响应外，错误响应必须使用：

```json
{
  "error": {
    "code": "BOOK_NOT_FOUND",
    "message": "The requested book does not exist",
    "retryable": false,
    "requestId": "request-7f3a"
  }
}
```

`code` 和 `message` 必填。错误码必须由稳定的大写 ASCII 单词组成，并使用下划线分隔。
`message` 面向开发和诊断，客户端不应假定它已经本地化。`retryable` 和 `requestId` 可选。
客户端必须忽略未知错误字段和未知错误码。

ORSP 1.6 定义以下标准错误码：

| 错误码 | 状态码 | 条件 |
| --- | --- | --- |
| `INVALID_PARAMETER` | `400` | 已知查询参数或 ID 缺失、格式不合法或超出范围 |
| `BOOK_NOT_FOUND` | `404` | 书籍 ID 不对应任何书籍 |
| `CHAPTER_NOT_FOUND` | `404` | 章节 ID 不对应该书的任何章节 |
| `RANKING_NOT_FOUND` | `404` | 榜单 ID 不对应任何榜单 |
| `ROUTE_NOT_FOUND` | `404` | 路径不是该书源的接口 |
| `METHOD_NOT_ALLOWED` | `405` | 不支持该 HTTP 方法 |
| `RATE_LIMITED` | `429` | 客户端超过请求频率限制 |
| `INTERNAL_ERROR` | `500` | 书源内部意外错误 |
| `UNAVAILABLE` | `503` | 书源暂时无法提供服务 |

条件与标准错误码匹配时，书源应当返回该标准码，并且不得把标准码用于其他含义。所有
不带 `X_` 前缀的错误码保留给当前和未来的 ORSP 规范；书源自定义错误码必须以 `X_`
开头，例如 `X_REGION_BLOCKED`。参数级别的细节放在 `message` 中。

错误响应不得包含凭据、Cookie、内部 URL、堆栈信息或其他敏感实现细节。

## 15. 安全与隐私

书源必须校验已知查询参数和 ID，并应限制请求频率、响应大小、执行时间和上游抓取行为。
生产书源应使用 HTTPS。

客户端接受用户或目录提供的书源 URL 时，应防御 SSRF、DNS 重绑定、环回或私网访问、
重定向循环、解压炸弹和超大图片或正文。是否允许私网书源属于客户端策略，应明确告知用户。

面向 Web 的书源需要设置合适的 CORS 策略；原生客户端不要求 CORS。

ORSP 不授予任何版权或访问权限。书源运营者必须只提供自己有权分发的内容。

## 16. 一致性认证

声称符合 `ORSP 1.6 Core Reading` 的实现必须：

1. 实现发现和全部四项核心能力；
2. 满足本文的规范性要求；
3. 通过所声明版本的官方核心一致性测试；
4. 单独披露可选扩展能力。

声称符合 `ORSP 1.6 Discovery` 的实现还必须实现并声明 `discover`、`categories` 和
`browse`，并通过官方发现配置检查。书源可以只实现部分可选标准能力，但不得因此声称
符合完整 Discovery 配置。

声称符合 `ORSP 1.6 Rankings` 的实现还必须实现并声明 `rankings`，提供至少两个榜单定义，
并通过官方榜单配置检查。榜单配置与 Discovery 配置相互独立；只有榜单使用
`categoryId` 时才需要声明 `categories`。

仅通过 JSON 或 YAML 语法验证不能证明协议兼容。测试报告应记录测试套件版本和执行时间。

## 17. 保留的未来工作

以下功能不属于 ORSP 1.6，需要后续次版本、主版本或配套规范：

- 用户认证和付费内容授权；
- 跨主版本协商：当书源通过 `supportedVersions` 声明多个主版本时选择入口的规则，
  包括主版本可能需要的按版本接口映射；
- 超出可选 `contentTypes` 声明范围的请求级正文格式选择与回退协商；
- 发现文档元数据本地化，例如按语言提供 `name` 和 `description`；
- 游标分页和增量目录同步；
- 离线包与下载清单；
- 书源健康与目录协议；
- 其他媒体表示、DRM、作品背景配乐；
- 批注、高亮和阅读进度同步。

## EPUB 与社区扩展

[OEP-0004](OEP-0004-publications-and-comments.md) 定义命名空间下的 EPUB 实验能力和评论、段评草案，不修改 1.6 核心一致性要求。详见[中文合同](docs/publications-and-comments.zh-CN.md)。
