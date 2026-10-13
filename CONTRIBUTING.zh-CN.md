# 参与贡献

[English](CONTRIBUTING.md)

感谢你帮助改进开放阅读书源协议。

提出协议变更前，请先阅读 [GOVERNANCE.zh-CN.md](GOVERNANCE.zh-CN.md)。ORSP 优先保证不同
团队独立开发的阅读器和书源能够互操作，因此“功能有用”并不代表它一定适合进入核心协议。

## 实现反馈

实现经验非常重要。反馈时请说明：

1. 你实现的是书源、阅读器、适配器、目录还是测试工具；
2. 使用的语言和框架；
3. 测试的协议版本与能力；
4. 哪些行为存在歧义或在不同实现之间表现不同；
5. 在可能时提供最小请求和响应示例。

## 提出协议变更

请创建协议 Issue，并说明：

1. 阅读器或书源开发者面临的问题；
2. 当前协议或命名空间扩展为什么无法解决；
3. 建议的请求、响应和能力结构；
4. 向后兼容和向前兼容影响；
5. 安全、隐私、无障碍和版权影响；
6. 迁移和废弃方式；
7. 实现与测试证据。

协议变更必须在同一个 PR 中同步更新规范、OpenAPI、相关 JSON Schema、示例和一致性测试。

## 兼容性规则

- 次版本只能增加可选字段和可选行为；
- 同一主版本内不得改变已有字段和接口的含义；
- 实现必须忽略任意嵌套层级的未知 JSON 对象字段；
- 实现必须忽略未知的可选能力标识；
- 扩展能力使用 `反向域名:名称`，不得使用保留的 `orsp` 命名空间；
- 缺失和 `null` 不同，除非明确声明，否则 `null` 不合法；
- 不兼容变更需要新的主版本和迁移文档。

## 本地检查

参考验证工具链为 Dart 3.12.2 和 Python 3.12；CI 固定这些版本，避免不同机器的
格式化规则变化导致同一提交出现不同验收结果。

```bash
dart format --output=none --set-exit-if-changed \
  examples/dart_server.dart tool/conformance_test.dart
dart analyze examples/dart_server.dart tool/conformance_test.dart
dart run tool/conformance_test.dart
python -m pip install jsonschema pyyaml openapi-spec-validator
python scripts/validate_contracts.py
python scripts/validate_creator_extensions.py
python scripts/validate_chapter_updates.py
python scripts/validate_reading_profiles.py
python scripts/test_probe_source.py
dart run tool/discovery_conformance_test.dart
python scripts/registry_tool.py validate
python scripts/registry_tool.py build --check
python scripts/test_registry_tool.py
```

CI 会运行相同检查。仅确认 JSON 或 YAML 语法正确不能证明协议兼容。

本仓库不接受书源收录投稿。Registry Schema 与工具仅作为独立社区可复用的参考实现维护，
详见 [registry/README.zh-CN.md](registry/README.zh-CN.md)。

提交贡献即表示你同意使用本仓库的 MIT 许可证授权该贡献。
