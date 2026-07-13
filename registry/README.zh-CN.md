# ORSP 社区书源目录

[English](README.md)

本目录是公开 ORSP 书源的初始社区 Registry。它负责书源发现与社区治理，不会取代 ORSP
通信协议。

每个书源使用一个独立 JSON 文件提交：

```text
registry/sources/<source-id>.json
```

文件名必须与条目中的 `id` 完全一致。不要手工编辑
`registry/generated/registry.json`，该文件由已接受的条目自动生成。

## 提交书源

1. Fork 本仓库；
2. 把 `registry/examples/source-entry.json` 复制到
   `registry/sources/<你的书源ID>.json`；
3. 替换全部示例内容，并设置一个稳定的 `testQuery`。该查询必须至少返回一本包含章节的书；
4. 运行下文中的本地检查；
5. 使用 `.github/PULL_REQUEST_TEMPLATE/source-submission.md` 创建 Pull Request。

发现文档中的 `id` 必须与 Registry 条目和文件名一致。书源必须支持 ORSP Core Reading 的
全部四项核心能力。

## Registry 字段说明

- `discoveryUrl`：书源规范的 HTTPS 发现文档地址；
- `maintainers`：负责维护该书源条目的 GitHub 账号；
- `description`：面向目录用户的简介；运行时书源信息仍以发现文档为准；
- `languages`：运营者声明的内容语言；网络检查会与发现文档比较；
- `contentTypes`：运营者对内容分发依据的声明；
- `testQuery`：仅供兼容性和健康检查使用的稳定搜索词；
- `reportingUrl`：可选的滥用、版权或可用性问题举报页面。

通过协议测试只代表接口兼容，不代表内容一定合法、优质或运营者一定可信。这些属于不同的
社区判断。

## 本地检查

```bash
python scripts/registry_tool.py validate
python scripts/registry_tool.py build --check
python scripts/registry_tool.py check-source \
  registry/sources/<source-id>.json
```

前两个命令是安全的静态检查，会在每个 PR 中运行。对于新提交的 Manifest，独立工作流会
使用 PR 基础分支中已经审核的验证器；它不会执行投稿代码，也不会向验证器暴露仓库凭据。

网络检查会拒绝私网、环回、链路本地、组播和保留 IP，把 TLS 连接固定到已经校验的公网
地址，并在每次重定向后重新验证目标。

## 审核与发布

满足以下条件后，PR 才可以合并：

- Manifest 和文件名通过静态检查；
- Registry、Discovery 和文件名中的 ID 一致；
- Discovery 和 API 地址通过公网安全检查；
- 搜索、详情、目录和正文链路可以完成；
- 提交者完成内容授权与维护声明；
- 不存在尚未解决的安全、滥用或版权问题。

接受的条目按照书源 ID 排序写入 `registry/generated/registry.json`。阅读器可以订阅该文件，
但实际添加书源前仍必须从书源获取当前发现文档。

## 健康检查与下架

自动化健康报告与作者维护的 Manifest 分开保存。一次失败不会直接删除书源。

建议状态包括：

- `verified`：当前兼容性和政策检查通过；
- `degraded`：部分检查失败，但主要阅读链路仍可用；
- `offline`：连续多次无法访问或使用；
- `unmaintained`：维护者在规定时间内没有回应；
- `suspended`：因安全、滥用或权利问题暂停展示；
- `removed`：已从活动目录中移除。

出现可信的安全或法律风险时，维护者可以立即暂停书源。下架记录保存在
`registry/removed/`，在适合公开时说明原因。

审核、维护权转移、暂停和下架规则见 [POLICY.zh-CN.md](POLICY.zh-CN.md)。
