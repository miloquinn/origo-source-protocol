# Open Reading Source Protocol

[English](README.md) · [协议规范](SPECIFICATION.md) · [OpenAPI](openapi.yaml)

Open Reading Source Protocol（ORSP，开放阅读书源协议）是一套连接阅读器与独立
内容服务的开放 HTTP 协议。

阅读器只需要实现一次 ORSP。书源开发者可以：

- 为原创、公共领域或已获授权的内容直接搭建 ORSP 服务；
- 在已有合法内容服务前搭建适配网关。

客户端不需要内置各站点的抓取脚本、Cookie 或可执行规则。

## 协议概览

每个书源发布一个发现文档：

```text
GET /.well-known/open-reading-source.json
```

并实现四类标准接口：

```text
GET /v1/search?q={query}&page=1&pageSize=20
GET /v1/books/{bookId}
GET /v1/books/{bookId}/chapters
GET /v1/books/{bookId}/chapters/{chapterId}
```

## 运行参考书源

仓库包含一个零第三方依赖的 Dart 示例服务，内容均为原创测试文本：

```bash
dart run examples/dart_server.dart
```

桌面端添加 `http://127.0.0.1:8787`；Android 模拟器添加
`http://10.0.2.2:8787`。

## 当前状态

协议版本 `1.0` 当前属于早期公开草案。发现、搜索、详情、目录和正文链路已经在
Open Reading 中完成真实 HTTP 验证。在正式宣布稳定前，我们希望收集更多书源开发者
对认证、更新同步、分页和内容格式的反馈。

## 合法使用

本协议仅用于原创、公共领域或已获授权的内容。请勿用它绕过访问控制、违反服务条款或
传播无授权内容。

贡献方式参见 [CONTRIBUTING.md](CONTRIBUTING.md)。仓库采用 [MIT](LICENSE) 许可。
