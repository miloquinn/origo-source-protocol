# 第三方书源检查记录：2026-10-13

检查入口：[用户提供的书源](http://110.42.63.158:8787/.well-known/open-reading-source.json)。
源标识 `cn.fanqie.orsp-adapter`，发现文档版本 1.1。这是一次读取采样，不表示掌握
运营者的代码或服务器，也不代表其所有作品均已验收。

通过 `scripts/probe_source.py` 实际发送 8 次 GET，发现、搜索、分类、发现推荐、浏览、
书籍详情、目录、正文均返回 200。已声明 search/discover/categories/browse/detail/catalog/content。
正文为 `text/html`，请求和返回的 bookId、chapterId 相符。

严格协议检查发现：正文没有必需的 `title`，因此尚未通过完整核心结构验收。
开元现有解析器可以从目录使用标题回退，这个兼容行为不取消书源开发者补齐字段的责任。
没有输出或保存小说正文，也没有进行写入、SSH 或部署操作。

目录目前返回 id/title/order，未提供逐章 updatedAt/contentVersion；后两者并非旧核心的
必需字段，不能因此判定 1.1 不兼容，但不能保证可靠发现旧正文修订。书源没有声明
章节更新状态、EPUB publication、图片序列、录音听书或多榜单能力，本轮没有调用这些
未声明接口，也没有把“未声明”写成“已实现”。

升级建议：先补正文 title，再按[完整阅读指南](source-upgrade-guide.zh-CN.md) 实现和测试
所需配置，最后更新发现文档。源身份与原接口保持不变。这个记录只代表当天的观测，
后续状态以重新运行工具为准。
