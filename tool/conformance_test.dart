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
    if (!condition) throw StateError('Conformance check failed: $message');
  }

  try {
    final discovery = await request(
      client,
      baseUri.resolve('.well-known/origo-source.json'),
    );
    check(discovery.status == 200, 'discovery returns 200');
    check(
      discovery.headers
              .value(HttpHeaders.contentTypeHeader)
              ?.startsWith('application/json') ??
          false,
      'discovery uses application/json',
    );
    check(
      discovery.headers.value('x-open-reading-protocol') == '1.6',
      'source advertises its protocol version header',
    );
    final discoveryJson = discovery.json as Map<String, dynamic>;
    check(
      discovery.headers.value('x-origo-source-protocol') == '1.6',
      'source advertises canonical protocol header',
    );
    final legacyDiscovery = await request(
      client,
      baseUri.resolve('.well-known/open-reading-source.json'),
    );
    final legacyJson = legacyDiscovery.json as Map<String, dynamic>;
    check(
      legacyJson['protocol'] == 'open-reading-source',
      'legacy discovery identity',
    );
    check(
      legacyJson['id'] == discoveryJson['id'] &&
          legacyJson['apiBaseUrl'] == discoveryJson['apiBaseUrl'],
      'aliases retain source and API identity',
    );
    check(discoveryJson['protocol'] == 'origo-source', 'protocol token');
    check(discoveryJson['protocolVersion'] == '1.6', 'protocol version');
    final capabilities = (discoveryJson['capabilities'] as List).toSet();
    check(
      capabilities.containsAll([
        'search',
        'discover',
        'categories',
        'browse',
        'rankings',
        'detail',
        'catalog',
        'content',
      ]),
      'core and discovery capabilities are advertised',
    );
    final apiBase = Uri.parse(discoveryJson['apiBaseUrl'] as String);
    check(apiBase.path.endsWith('/'), 'apiBaseUrl ends in a slash');
    final supportedVersions = discoveryJson['supportedVersions'] as List;
    check(
      supportedVersions.contains(discoveryJson['protocolVersion']),
      'supportedVersions includes protocolVersion',
    );
    final maxCatalogPageSize = discoveryJson['maxCatalogPageSize'] as int;
    check(
      maxCatalogPageSize >= 1 && maxCatalogPageSize <= 1000,
      'maxCatalogPageSize is within the allowed range',
    );
    check(
      (discoveryJson['operatorName'] as String).isNotEmpty,
      'operatorName is present and non-empty',
    );
    check(
      Uri.parse(
        discoveryJson['contactUrl'] as String,
      ).scheme.startsWith('http'),
      'contactUrl is an absolute HTTP(S) URL',
    );
    check(
      (discoveryJson['contentLicense'] as String).isNotEmpty,
      'contentLicense is present and non-empty',
    );
    check(
      (discoveryJson['rightsStatement'] as String).isNotEmpty,
      'rightsStatement is present and non-empty',
    );

    final discover = await request(client, apiBase.resolve('v1/discover'));
    check(discover.status == 200, 'discover returns 200');
    final discoverSections = (discover.json as Map)['sections'] as List;
    check(discoverSections.length == 2, 'discover returns curated sections');
    check(
      (discoverSections.first as Map)['id'] == 'featured',
      'discover section IDs are stable',
    );

    final categories = await request(client, apiBase.resolve('v1/categories'));
    check(categories.status == 200, 'categories returns 200');
    final categoryItems = (categories.json as Map)['items'] as List;
    check(categoryItems.length == 2, 'categories returns source categories');
    check(
      categoryItems.any((item) => (item as Map)['id'] == 'protocol'),
      'category IDs are browseable',
    );

    final latest = await request(
      client,
      apiBase.resolve('v1/browse?sort=latest&page=1&pageSize=20'),
      headers: {'X-Origo-Source-Protocol': '1.6'},
    );
    check(latest.status == 200, 'latest browse returns 200');
    final latestItems = (latest.json as Map)['items'] as List;
    check(
      (latestItems.first as Map)['id'] == 'river-of-pages',
      'latest browse ordering is deterministic',
    );

    final categoryBrowse = await request(
      client,
      apiBase.resolve('v1/browse?category=protocol&sort=popular'),
    );
    final categoryBrowseItems = (categoryBrowse.json as Map)['items'] as List;
    check(categoryBrowse.status == 200, 'category browse returns 200');
    check(categoryBrowseItems.length == 1, 'category browse filters books');
    check(
      (categoryBrowseItems.single as Map)['id'] == 'protocol-garden',
      'category browse uses category IDs unchanged',
    );

    final rankingCollection = await request(
      client,
      apiBase.resolve('v1/rankings'),
    );
    check(rankingCollection.status == 200, 'rankings returns 200');
    final rankingDefinitions = (rankingCollection.json as Map)['items'] as List;
    check(rankingDefinitions.length >= 2, 'multiple rankings are exposed');
    check(
      rankingDefinitions.any(
        (item) =>
            (item as Map)['id'] == 'weekly-popular' &&
            item['period'] == 'weekly',
      ),
      'ranking definitions expose stable IDs and standard periods',
    );
    check(
      rankingDefinitions.any(
        (item) =>
            (item as Map)['id'] == 'monthly-new' &&
            item['categoryId'] == 'original',
      ),
      'rankings may reference source categories',
    );

    final rankingPage1 = await request(
      client,
      apiBase.resolve('v1/rankings/weekly-popular?page=1&pageSize=1'),
    );
    check(rankingPage1.status == 200, 'ranking page returns 200');
    final rankingJson1 = rankingPage1.json as Map<String, dynamic>;
    final rankingItems1 = rankingJson1['items'] as List;
    check(rankingItems1.length == 1, 'ranking page size honored');
    check(
      (rankingItems1.single as Map)['rank'] == 1,
      'ranking uses absolute one-based ranks',
    );
    check(
      (rankingItems1.single as Map)['previousRank'] == 2,
      'ranking may expose a previous comparable rank',
    );
    check(
      ((rankingItems1.single as Map)['book'] as Map)['id'] == 'protocol-garden',
      'ranking entries wrap the shared book model',
    );
    check(rankingJson1['hasMore'] == true, 'ranking page reports hasMore');
    check(
      rankingJson1['snapshotId'] is String,
      'ranking page identifies its ordered snapshot',
    );

    final rankingPage2 = await request(
      client,
      apiBase.resolve('v1/rankings/weekly-popular?page=2&pageSize=1'),
    );
    final rankingJson2 = rankingPage2.json as Map<String, dynamic>;
    final rankingItems2 = rankingJson2['items'] as List;
    check(rankingPage2.status == 200, 'second ranking page returns 200');
    check(
      (rankingItems2.single as Map)['rank'] == 2,
      'ranking page preserves absolute rank positions',
    );
    check(
      rankingJson2['snapshotId'] == rankingJson1['snapshotId'],
      'ranking pages share one snapshot identifier',
    );
    check(rankingJson2['hasMore'] == false, 'last ranking page');

    final searchPage1 = await request(
      client,
      apiBase.resolve('v1/search?q=Origo%20X&page=1&pageSize=1&future=x'),
      headers: {'X-Origo-Source-Protocol': '1.6'},
    );
    check(searchPage1.status == 200, 'search returns 200');
    final searchJson1 = searchPage1.json as Map<String, dynamic>;
    check(
      (searchJson1['items'] as List).length == 1,
      'search page size honored',
    );
    check(searchJson1['pageSize'] == 1, 'search reports requested capacity');
    check(searchJson1['total'] == 2, 'search total is correct');
    check(searchJson1['hasMore'] == true, 'search hasMore is correct');

    final searchPage2 = await request(
      client,
      apiBase.resolve('v1/search?q=Origo%20X&page=2&pageSize=1'),
    );
    final searchJson2 = searchPage2.json as Map<String, dynamic>;
    check((searchJson2['items'] as List).length == 1, 'second search page');
    check(searchJson2['hasMore'] == false, 'last search page');

    final detail = await request(
      client,
      apiBase.resolve('v1/books/protocol-garden'),
    );
    check(detail.status == 200, 'detail returns 200');
    check((detail.json as Map)['id'] == 'protocol-garden', 'detail ID');
    final etag = detail.headers.value(HttpHeaders.etagHeader);
    check(etag != null && etag.isNotEmpty, 'detail provides ETag');

    final notModified = await request(
      client,
      apiBase.resolve('v1/books/protocol-garden'),
      headers: {HttpHeaders.ifNoneMatchHeader: etag!},
    );
    check(notModified.status == 304, 'If-None-Match returns 304');
    check(notModified.body.isEmpty, '304 has no body');

    final catalog1 = await request(
      client,
      apiBase.resolve('v1/books/protocol-garden/chapters?page=1&pageSize=1'),
    );
    final catalogJson1 = catalog1.json as Map<String, dynamic>;
    check(catalog1.status == 200, 'catalog returns 200');
    check((catalogJson1['items'] as List).length == 1, 'catalog pagination');
    check(catalogJson1['total'] == 2, 'catalog total');
    check(catalogJson1['hasMore'] == true, 'catalog hasMore');

    final catalog2 = await request(
      client,
      apiBase.resolve('v1/books/protocol-garden/chapters?page=2&pageSize=1'),
    );
    final catalogItems2 = (catalog2.json as Map)['items'] as List;
    check(catalogItems2.single['id'] == 'common-language', 'catalog order');

    final catalogLarge = await request(
      client,
      apiBase.resolve(
        'v1/books/protocol-garden/chapters?pageSize=$maxCatalogPageSize',
      ),
    );
    check(
      catalogLarge.status == 200,
      'catalog accepts the declared maxCatalogPageSize',
    );
    check(
      (catalogLarge.json as Map)['pageSize'] == maxCatalogPageSize,
      'catalog reports the requested capacity',
    );

    final catalogTooLarge = await request(
      client,
      apiBase.resolve(
        'v1/books/protocol-garden/chapters?pageSize=${maxCatalogPageSize + 1}',
      ),
    );
    checkError(catalogTooLarge, 400, 'INVALID_PARAMETER', check);

    final content = await request(
      client,
      apiBase.resolve('v1/books/protocol-garden/chapters/seed'),
    );
    final contentJson = content.json as Map<String, dynamic>;
    check(content.status == 200, 'content returns 200');
    check(contentJson['bookId'] == 'protocol-garden', 'content book ID');
    check(contentJson['chapterId'] == 'seed', 'content chapter ID');
    check(contentJson['contentType'] == 'text/plain', 'content type');
    check(Uri.parse(contentJson['baseUrl'] as String).isAbsolute, 'base URL');

    final missingQuery = await request(client, apiBase.resolve('v1/search'));
    checkError(missingQuery, 400, 'INVALID_PARAMETER', check);

    final invalidPage = await request(
      client,
      apiBase.resolve('v1/search?q=test&page=0'),
    );
    checkError(invalidPage, 400, 'INVALID_PARAMETER', check);

    final invalidSort = await request(
      client,
      apiBase.resolve('v1/browse?sort=random'),
    );
    checkError(invalidSort, 400, 'INVALID_PARAMETER', check);

    final invalidRankingPage = await request(
      client,
      apiBase.resolve('v1/rankings/weekly-popular?page=0'),
    );
    checkError(invalidRankingPage, 400, 'INVALID_PARAMETER', check);

    final missingRanking = await request(
      client,
      apiBase.resolve('v1/rankings/does-not-exist'),
    );
    checkError(missingRanking, 404, 'RANKING_NOT_FOUND', check);

    final missingBook = await request(
      client,
      apiBase.resolve('v1/books/does-not-exist'),
    );
    checkError(missingBook, 404, 'BOOK_NOT_FOUND', check);

    final wrongMethod = await request(
      client,
      apiBase.resolve('v1/search?q=test'),
      method: 'POST',
    );
    checkError(wrongMethod, 405, 'METHOD_NOT_ALLOWED', check);
    check(
      wrongMethod.headers.value(HttpHeaders.allowHeader) == 'GET, OPTIONS',
      '405 includes Allow',
    );

    stdout.writeln('ORSP conformance checks passed: $checks');
  } finally {
    client.close(force: true);
    await server.close();
  }
}

void checkError(
  TestResponse response,
  int status,
  String code,
  void Function(bool, String) check,
) {
  check(response.status == status, '$code returns $status');
  final body = response.json as Map<String, dynamic>;
  final error = body['error'] as Map<String, dynamic>;
  check(error['code'] == code, '$code uses the standard error envelope');
  check(error['message'] is String, '$code includes a message');
}

Future<TestResponse> request(
  HttpClient client,
  Uri uri, {
  String method = 'GET',
  Map<String, String> headers = const {},
}) async {
  final request = await client.openUrl(method, uri);
  headers.forEach(request.headers.set);
  final response = await request.close();
  final body = await utf8.decoder.bind(response).join();
  return TestResponse(response.statusCode, response.headers, body);
}

class TestResponse {
  final int status;
  final HttpHeaders headers;
  final String body;

  const TestResponse(this.status, this.headers, this.body);

  Object? get json => body.isEmpty ? null : jsonDecode(body);
}
