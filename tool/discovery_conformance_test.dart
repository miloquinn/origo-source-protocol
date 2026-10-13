import 'dart:convert';
import 'dart:io';

import '../examples/dart_server.dart';

Future<void> main() async {
  final server = ReferenceSourceServer();
  final baseUri = await server.start(port: 0);
  final client = HttpClient();
  var checks = 0;

  void check(bool condition, String message) {
    checks++;
    if (!condition)
      throw StateError('Discovery conformance check failed: $message');
  }

  try {
    final manifest = await _request(
      client,
      baseUri.resolve('.well-known/origo-source.json'),
    );
    check(
      manifest.statusCode == HttpStatus.ok,
      'discovery document returns 200',
    );
    final discovery =
        jsonDecode(await utf8.decoder.bind(manifest).join())
            as Map<String, dynamic>;
    final capabilities = (discovery['capabilities'] as List)
        .cast<String>()
        .toSet();
    check(
      capabilities.containsAll({'discover', 'categories', 'browse'}),
      'all Discovery Profile capabilities are advertised together',
    );

    final apiBase = Uri.parse(discovery['apiBaseUrl'] as String);
    final discover = await _json(client, apiBase.resolve('v1/discover'));
    final sections = discover['sections'];
    check(
      sections is List &&
          sections.any(
            (section) =>
                section is Map &&
                section['items'] is List &&
                (section['items'] as List).isNotEmpty,
          ),
      'discover returns a non-empty section',
    );

    final categories = await _json(client, apiBase.resolve('v1/categories'));
    final categoryItems = categories['items'];
    check(
      categoryItems is List && categoryItems.isNotEmpty,
      'categories returns an item',
    );
    final category = categoryItems.first as Map;
    final categoryId = category['id'];
    check(
      categoryId is String && categoryId.isNotEmpty,
      'category has a stable ID',
    );

    final browse = await _json(
      client,
      apiBase.resolve(
        'v1/browse?category=${Uri.encodeQueryComponent(categoryId as String)}&page=1&pageSize=1',
      ),
    );
    final books = browse['items'];
    check(books is List && books.isNotEmpty, 'category browse returns a book');
    check(
      browse['page'] == 1 && browse['pageSize'] == 1,
      'browse honors pagination',
    );

    final invalidSort = await _request(
      client,
      apiBase.resolve('v1/browse?sort=unsupported'),
    );
    check(
      invalidSort.statusCode == HttpStatus.badRequest,
      'invalid browse parameters return 400',
    );
    stdout.writeln('ORSP Discovery Profile checks passed: $checks');
  } finally {
    client.close(force: true);
    await server.close();
  }
}

Future<HttpClientResponse> _request(HttpClient client, Uri uri) async {
  final request = await client.getUrl(uri);
  request.headers.set('X-Origo-Source-Protocol', '1.4');
  return request.close();
}

Future<Map<String, dynamic>> _json(HttpClient client, Uri uri) async {
  final response = await _request(client, uri);
  if (response.statusCode != HttpStatus.ok) {
    throw StateError('${uri.path} returned ${response.statusCode}');
  }
  return jsonDecode(await utf8.decoder.bind(response).join())
      as Map<String, dynamic>;
}
