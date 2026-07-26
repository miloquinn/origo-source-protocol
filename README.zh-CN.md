# Open Reading Source Protocol

[English](README.md) · **简体中文** · [繁體中文](README.zh-TW.md) ·
[日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) ·
[协议规范](SPECIFICATION.zh-CN.md) · [OpenAPI](openapi.yaml) ·
[治理机制](GOVERNANCE.zh-CN.md) · [生态架构](ECOSYSTEM.zh-CN.md) ·
[书源与权利政策](SOURCE_POLICY.zh-CN.md)

Open Reading Source Protocol（ORSP，开放阅读书源协议）是一套用于连接阅读应用与
独立内容服务的开放 HTTP 协议。它让不同书源以统一方式提供搜索、书籍详情、章节目录
和正文内容。

阅读器只需要实现一次 ORSP，就可以连接所有符合协议的书源。书源开发者可以：

- 为原创作品、公共领域作品或已获授权内容直接搭建 ORSP 服务；
- 在自己有权使用的现有内容服务前增加一个 ORSP 适配层；
- 使用任意语言和框架实现服务，只要 HTTP 请求与响应符合协议即可。

客户端不需要为每个网站内置不同的抓取脚本、Cookie 或可执行规则。书源服务也不需要
公开内部实现，只需要公开标准接口。

## 为什么建立统一书源协议

传统书源通常使用各自的字段、接口或脚本规则，阅读器必须逐个适配，而且规则容易随着
页面变化失效。ORSP 把阅读器和内容服务之间的边界固定为一个可验证的 HTTP 协议：

- 阅读器开发者只维护一套接入逻辑；
- 书源开发者可以独立部署、升级和选择技术栈；
- 用户可以通过一个服务地址添加书源；
- 社区可以共同维护规范、Schema、测试工具和兼容性约定。

## 协议概览

每个书源必须发布一个发现文档：

```text
GET /.well-known/open-reading-source.json
```

发现文档用于声明书源身份、协议版本、API 地址、支持语言和能力：

```json
{
  "protocol": "open-reading-source",
  "protocolVersion": "1.5",
  "id": "org.example.public-books",
  "name": "示例公共图书源",
  "description": "由 Example.org 维护的公共领域图书",
  "apiBaseUrl": "https://books.example.org/api/",
  "operatorName": "示例公共图书基金会",
  "contactUrl": "https://books.example.org/rights",
  "contentLicense": "Public Domain",
  "rightsStatement": "本书源提供经运营者确认的公共领域图书。",
  "languages": ["zh-CN"],
  "maxCatalogPageSize": 200,
  "capabilities": [
    "search", "discover", "categories", "browse", "rankings",
    "detail", "catalog", "content"
  ]
}
```

协议 1.5 保留四类核心接口：

```text
GET {apiBaseUrl}v1/search?q={query}&page=1&pageSize=20
GET {apiBaseUrl}v1/books/{bookId}
GET {apiBaseUrl}v1/books/{bookId}/chapters?page=1&pageSize=100
GET {apiBaseUrl}v1/books/{bookId}/chapters/{chapterId}
```

书源还可以声明发现与多榜单等可选标准能力：

```text
GET {apiBaseUrl}v1/discover
GET {apiBaseUrl}v1/categories
GET {apiBaseUrl}v1/browse?category={categoryId}&sort=latest&page=1&pageSize=20
GET {apiBaseUrl}v1/rankings
GET {apiBaseUrl}v1/rankings/{rankingId}?page=1&pageSize=20
```

这些相对路径必须基于发现文档中的 `apiBaseUrl` 解析。ORSP 1.5 Core Reading 书源必须
实现全部四项核心能力；发现、分类、浏览和多榜单按能力声明启用，旧的 1.x 书源无需修改
也可以继续搜索和阅读。榜单排名只在对应的书源、榜单 ID 和快照 ID 内有效。完整字段与
错误处理要求请阅读
[协议规范](SPECIFICATION.zh-CN.md)，接口模型可查看 [OpenAPI 3.1 文档](openapi.yaml)。

客户端可以把多个书源聚合为默认“全部书源”发现页，并提供单书源筛选。聚合界面必须
保留来源归属和书源作用域内的 ID，保持各书源内部排序，并在最新或热门列表中采用来源
均衡的合并方式。

## 快速运行测试书源

仓库内置一个零第三方依赖的 Dart 参考服务。示例书籍和正文均为原创测试内容，不依赖
外部网站：

```bash
dart run examples/dart_server.dart
```

启动后可访问：

- 电脑或 iOS 模拟器：`http://127.0.0.1:8787`
- Android 模拟器：`http://10.0.2.2:8787`
- 局域网真机：使用运行服务电脑的局域网 IP，例如 `http://192.168.1.10:8787`

可以先验证发现接口：

```bash
curl http://127.0.0.1:8787/.well-known/open-reading-source.json
curl "http://127.0.0.1:8787/api/v1/search?q=协议&page=1&pageSize=20"
```

## 开发自己的书源

一个最小可用的 ORSP 书源可以按以下顺序实现：

1. 提供 `/.well-known/open-reading-source.json` 发现文档；
2. 实现搜索、详情、目录和正文四个接口；
3. 使用稳定、不随标题变化的书籍 ID 和章节 ID；
4. 使用 UTF-8 JSON，并为错误返回合适的 HTTP 状态码；
5. 根据 [JSON Schema](schemas/discovery.schema.json) 和
   [OpenAPI](openapi.yaml) 校验输出；
6. 用阅读器或参考客户端完成一次真实 HTTP 接入测试。

生产环境建议使用 HTTPS，并设置缓存、速率限制、响应大小限制和合适的 CORS 策略。
HTML 正文应被视为不可信输入，客户端在渲染前应进行清理。

## 仓库结构

```text
SPECIFICATION.md                规范性协议说明
OEP-0001-discovery.md           历史 ORSP 1.1 发现能力提案与兼容性分析
OEP-0003-registry-diagnostics.md Registry 诊断与配置检查候选提案
OEP-0004-rankings.md            ORSP 1.5 多榜单能力提案与兼容性分析
SPECIFICATION.zh-CN.md          简体中文协议翻译
openapi.yaml                    OpenAPI 3.1 接口定义
schemas/discovery.schema.json   发现文档 JSON Schema
examples/dart_server.dart       可运行的 Dart 参考书源
examples/open-reading-source.json 发现文档示例
tool/conformance_test.dart      端到端核心一致性测试
tool/discovery_conformance_test.dart Discovery Profile 一致性测试
tool/rankings_conformance_test.dart Rankings Profile 一致性测试
GOVERNANCE.zh-CN.md             协议变更与发布治理
ECOSYSTEM.zh-CN.md              适配器与联邦书源目录架构
registry/                       非官方 Registry 参考格式与工具
```

## 当前状态与兼容性

协议版本 `1.5` 目前是候选草案。兼容性规则、机器可读契约、参考书源和核心一致性测试
会同步演进。在宣布稳定版本之前，欢迎独立阅读器和书源实现参与互操作验证。

可以运行官方核心测试：

```bash
dart run tool/conformance_test.dart
dart run tool/discovery_conformance_test.dart
dart run tool/rankings_conformance_test.dart
```

同一主版本内应保持向后兼容。新增可选字段通常可以继续使用 1.x；修改必填字段、接口
含义或响应语义则需要新的主版本。

传统书源格式应通过服务端适配器转换成 ORSP，而不是把抓取脚本下发给阅读器。社区可以
运营多个联邦式书源目录，目录负责发现、健康状态和信任信息，但不能重新定义通信协议。
详细边界参见 [ECOSYSTEM.zh-CN.md](ECOSYSTEM.zh-CN.md)。

本项目不运营官方书源目录，也不接受书源收录投稿。`registry/` 仅保留为独立社区可自行采用
的参考格式和工具；Open Reading 官方 App 不读取其中生成的索引。详细边界见
[书源与权利政策](SOURCE_POLICY.zh-CN.md)。

## 合法与负责任地使用

ORSP 面向原创内容、公共领域内容以及已获得合法授权的内容。请勿使用本协议绕过访问
控制、规避付费或认证机制、违反内容服务条款，或传播无权分发的作品。

协议本身不授予任何内容版权或访问权限。书源运营者负责确认内容授权，客户端开发者也
应提供清晰的来源信息与移除机制。

协议兼容不构成内容合法性认证。Open Reading 官方项目不提供书源地址，用户添加的每个
书源均由其独立选择。

## 参与贡献

欢迎提交问题、兼容性反馈、协议改进建议、其他语言的参考实现和文档翻译。协议变更应
同时说明兼容性、安全、隐私和版权影响，并更新相关规范、Schema 或示例。

详细流程参见 [CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md)。本仓库采用 [MIT](LICENSE) 许可。
