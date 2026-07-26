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
    if (!condition) {
      throw StateError('Rankings conformance check failed: $message');
    }
  }

  try {
    final discovery = await _json(
      client,
      baseUri.resolve('.well-known/open-reading-source.json'),
    );
    final capabilities = (discovery['capabilities'] as List)
        .cast<String>()
        .toSet();
    check(
      capabilities.contains('rankings'),
      'rankings capability is advertised',
    );

    final apiBase = Uri.parse(discovery['apiBaseUrl'] as String);
    final collection = await _json(client, apiBase.resolve('v1/rankings'));
    final definitions = collection['items'];
    check(
      definitions is List && definitions.length >= 2,
      'multiple ranking definitions are exposed',
    );
    check(
      definitions is List &&
          definitions.any(
            (item) =>
                item is Map &&
                item['id'] == 'weekly-popular' &&
                item['period'] == 'weekly',
          ),
      'ranking definitions expose stable IDs and standard periods',
    );
    check(
      definitions is List &&
          definitions.any(
            (item) =>
                item is Map &&
                item['id'] == 'monthly-new' &&
                item['categoryId'] == 'original',
          ),
      'rankings may reference source categories',
    );

    final firstPage = await _json(
      client,
      apiBase.resolve('v1/rankings/weekly-popular?page=1&pageSize=1'),
    );
    final firstItems = firstPage['items'] as List;
    final firstEntry = firstItems.single as Map;
    check(firstEntry['rank'] == 1, 'first page uses absolute rank one');
    check(
      firstEntry['previousRank'] == 2,
      'entries may expose a previous comparable rank',
    );
    check(
      (firstEntry['book'] as Map)['id'] == 'protocol-garden',
      'ranking entries wrap the shared book model',
    );
    check(firstPage['hasMore'] == true, 'first page reports more entries');
    check(
      firstPage['snapshotId'] is String,
      'ranking page identifies its ordered snapshot',
    );

    final secondPage = await _json(
      client,
      apiBase.resolve('v1/rankings/weekly-popular?page=2&pageSize=1'),
    );
    final secondEntry = (secondPage['items'] as List).single as Map;
    check(secondEntry['rank'] == 2, 'second page preserves absolute rank');
    check(
      secondPage['snapshotId'] == firstPage['snapshotId'],
      'pages share one snapshot identifier',
    );
    check(secondPage['hasMore'] == false, 'last ranking page is identified');

    final invalidPage = await _request(
      client,
      apiBase.resolve('v1/rankings/weekly-popular?page=0'),
    );
    check(
      invalidPage.statusCode == HttpStatus.badRequest,
      'invalid ranking pagination returns 400',
    );

    final missing = await _request(
      client,
      apiBase.resolve('v1/rankings/does-not-exist'),
    );
    check(
      missing.statusCode == HttpStatus.notFound,
      'unknown ranking returns 404',
    );
    final error = jsonDecode(await utf8.decoder.bind(missing).join()) as Map;
    check(
      (error['error'] as Map)['code'] == 'RANKING_NOT_FOUND',
      'unknown ranking uses the standard error code',
    );

    stdout.writeln('ORSP Rankings Profile checks passed: $checks');
  } finally {
    client.close(force: true);
    await server.close();
  }
}

Future<HttpClientResponse> _request(HttpClient client, Uri uri) async {
  final request = await client.getUrl(uri);
  request.headers.set('X-Open-Reading-Protocol', '1.5');
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
