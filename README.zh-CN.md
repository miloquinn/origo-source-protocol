# Open Reading Source Protocol

[English](README.md) · **简体中文** · [繁體中文](README.zh-TW.md) ·
[日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) ·
[协议规范](SPECIFICATION.md) · [OpenAPI](openapi.yaml)

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
  "protocolVersion": "1.0",
  "id": "org.example.public-books",
  "name": "示例公共图书源",
  "description": "由 Example.org 维护的公共领域图书",
  "apiBaseUrl": "https://books.example.org/api/",
  "languages": ["zh-CN"],
  "capabilities": ["search", "detail", "catalog", "content"]
}
```

协议 1.0 定义四类核心接口：

```text
GET /v1/search?q={query}&page=1&pageSize=20
GET /v1/books/{bookId}
GET /v1/books/{bookId}/chapters
GET /v1/books/{bookId}/chapters/{chapterId}
```

对应能力分别是搜索、书籍详情、章节目录和章节正文。完整字段与错误处理要求请阅读
[协议规范](SPECIFICATION.md)，接口模型可查看 [OpenAPI 3.1 文档](openapi.yaml)。

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
curl "http://127.0.0.1:8787/v1/search?q=星&page=1&pageSize=20"
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
openapi.yaml                    OpenAPI 3.1 接口定义
schemas/discovery.schema.json   发现文档 JSON Schema
examples/dart_server.dart       可运行的 Dart 参考书源
examples/open-reading-source.json 发现文档示例
```

## 当前状态与兼容性

协议版本 `1.0` 目前是早期公开草案。发现、搜索、详情、目录和正文链路已经完成真实 HTTP
验证，但在宣布稳定版本之前，仍欢迎书源开发者对认证、更新同步、分页、内容格式和错误
处理提出建议。

同一主版本内应保持向后兼容。新增可选字段通常可以继续使用 1.x；修改必填字段、接口
含义或响应语义则需要新的主版本。

## 合法与负责任地使用

ORSP 面向原创内容、公共领域内容以及已获得合法授权的内容。请勿使用本协议绕过访问
控制、规避付费或认证机制、违反内容服务条款，或传播无权分发的作品。

协议本身不授予任何内容版权或访问权限。书源运营者负责确认内容授权，客户端开发者也
应提供清晰的来源信息与移除机制。

## 参与贡献

欢迎提交问题、兼容性反馈、协议改进建议、其他语言的参考实现和文档翻译。协议变更应
同时说明兼容性、安全、隐私和版权影响，并更新相关规范、Schema 或示例。

详细流程参见 [CONTRIBUTING.md](CONTRIBUTING.md)。本仓库采用 [MIT](LICENSE) 许可。
