# Open Reading Source Protocol

[English](README.md) · [简体中文](README.zh-CN.md) ·
[繁體中文](README.zh-TW.md) · **日本語** · [한국어](README.ko.md) ·
[Español](README.es.md) · [仕様](SPECIFICATION.md) · [OpenAPI](openapi.yaml)

Open Reading Source Protocol（ORSP）は、読書アプリと独立したコンテンツサービスを
接続するためのオープンな HTTP プロトコルです。検索、書籍情報、章一覧、本文取得を
共通のインターフェースで提供します。

リーダー側は ORSP を一度実装すれば、すべての互換ソースに接続できます。ソース開発者は、
オリジナル作品、パブリックドメイン、または正規に許諾されたコンテンツ向けのサービスを
構築できます。また、利用権限のある既存サービスに ORSP アダプターを追加することもできます。

## プロトコル概要

各ソースはディスカバリードキュメントを公開します。

```text
GET /.well-known/open-reading-source.json
```

さらに、4 つの基本エンドポイントを実装します。

```text
GET {apiBaseUrl}v1/search?q={query}&page=1&pageSize=20
GET {apiBaseUrl}v1/books/{bookId}
GET {apiBaseUrl}v1/books/{bookId}/chapters?page=1&pageSize=100
GET {apiBaseUrl}v1/books/{bookId}/chapters/{chapterId}
```

バージョン 1.6 では、任意のディスカバリー、カテゴリ、ブラウズ、複数ランキング API も定義します。

```text
GET {apiBaseUrl}v1/discover
GET {apiBaseUrl}v1/categories
GET {apiBaseUrl}v1/browse?category={categoryId}&sort=latest&page=1&pageSize=20
GET {apiBaseUrl}v1/rankings
GET {apiBaseUrl}v1/rankings/{rankingId}?page=1&pageSize=20
```

フィールドとエラー処理の詳細は、[仕様書](SPECIFICATION.md)および
[OpenAPI 3.1 定義](openapi.yaml)を参照してください。

## 参照ソースを実行する

リポジトリには、外部パッケージに依存しない Dart 製の参照サーバーが含まれています。
サンプル本文はすべてテスト用のオリジナルコンテンツです。

```bash
dart run examples/dart_server.dart
```

PC では `http://127.0.0.1:8787`、Android エミュレーターでは
`http://10.0.2.2:8787` を使用してください。

## 独自ソースの実装

1. ソース ID、バージョン、API URL、機能を宣言するディスカバリードキュメントを作成する。
2. 検索、詳細、章一覧、本文の各エンドポイントを実装する。
3. 書籍と章には安定した不透明 ID を使用する。
4. UTF-8 JSON と適切な HTTP ステータスコードを返す。
5. [JSON Schema](schemas/discovery.schema.json) と [OpenAPI](openapi.yaml) で検証する。
6. 実際の HTTP リクエストで互換性を確認する。

## ステータスと責任ある利用

バージョン `1.6` は候補ドラフトです。基本的な読書フローは検証済みですが、安定版の
公開前に、認証、同期、ページング、コンテンツ形式についてのフィードバックを歓迎します。

ORSP は、オリジナル、パブリックドメイン、または正規に許諾されたコンテンツを対象とします。
アクセス制御の回避、利用規約への違反、無許可コンテンツの配布には使用しないでください。

貢献方法は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。ライセンスは
[MIT](LICENSE) です。

[ORSP 1.6 reading profiles](OEP-0006-media-reading.md) · [Upgrade guide](docs/source-upgrade-guide.zh-CN.md) · [Reference validation](scripts/validate_reading_profiles.py)
