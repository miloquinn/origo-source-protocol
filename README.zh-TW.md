# Open Reading Source Protocol

[English](README.md) · [简体中文](README.zh-CN.md) · **繁體中文** ·
[日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) ·
[協議規範](SPECIFICATION.md) · [OpenAPI](openapi.yaml)

Open Reading Source Protocol（ORSP，開放閱讀書源協議）是一套連接閱讀應用程式與
獨立內容服務的開放 HTTP 協議。它以統一方式提供搜尋、書籍詳情、章節目錄與正文內容。

閱讀器只需實作一次 ORSP，即可連接所有相容書源。書源開發者可以為原創、公共領域或
已授權內容直接架設服務，也可以在自己有權使用的既有服務前建立 ORSP 轉接層。實作可
使用任何程式語言或框架。

## 為什麼需要統一協議

- 閱讀器開發者只需維護一套接入邏輯；
- 書源開發者能獨立部署、升級並選擇技術棧；
- 使用者可透過一個服務網址新增書源；
- 社群可以共同維護規範、Schema、測試工具與相容性約定。

客戶端不需要內建各網站的擷取腳本、Cookie 或可執行規則。

## 協議概覽

每個書源必須提供發現文件：

```text
GET /.well-known/open-reading-source.json
```

並實作四個核心端點：

```text
GET {apiBaseUrl}v1/search?q={query}&page=1&pageSize=20
GET {apiBaseUrl}v1/books/{bookId}
GET {apiBaseUrl}v1/books/{bookId}/chapters?page=1&pageSize=100
GET {apiBaseUrl}v1/books/{bookId}/chapters/{chapterId}
```

協議 1.1 亦提供可選的探索、分類與瀏覽端點：

```text
GET {apiBaseUrl}v1/discover
GET {apiBaseUrl}v1/categories
GET {apiBaseUrl}v1/browse?category={categoryId}&sort=latest&page=1&pageSize=20
```

完整欄位及錯誤處理請參閱[協議規範](SPECIFICATION.md)與
[OpenAPI 3.1 文件](openapi.yaml)。

## 執行測試書源

本倉庫提供零第三方相依套件的 Dart 參考服務，內容均為原創測試文字：

```bash
dart run examples/dart_server.dart
```

電腦端使用 `http://127.0.0.1:8787`；Android 模擬器使用
`http://10.0.2.2:8787`。真機測試可使用執行服務電腦的區域網路 IP。

## 開發自己的書源

1. 建立發現文件並宣告書源 ID、版本、API 網址與能力；
2. 實作搜尋、詳情、目錄與正文端點；
3. 為書籍與章節使用穩定且不透明的 ID；
4. 使用 UTF-8 JSON 與正確的 HTTP 狀態碼；
5. 依照 [JSON Schema](schemas/discovery.schema.json) 和
   [OpenAPI](openapi.yaml) 驗證輸出；
6. 以真實 HTTP 請求完成相容性測試。

## 狀態與使用邊界

協議 `1.1` 目前是候選草案。核心讀取流程已完成驗證，但在穩定版本發布前仍歡迎
對認證、同步、分頁及內容格式提出建議。

ORSP 僅適用於原創、公共領域或合法授權內容。請勿用於繞過存取控制、違反服務條款或
散布未授權作品。協議本身不授予任何內容版權或存取權限。

貢獻方式請參閱 [CONTRIBUTING.md](CONTRIBUTING.md)。本倉庫採用 [MIT](LICENSE) 授權。
