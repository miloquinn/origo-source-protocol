import 'dart:async';
import 'dart:convert';
import 'dart:io';

const protocolVersion = '1.0';
final _opaqueIdPattern = RegExp(r'^[A-Za-z0-9._~-]{1,200}$');

class ReferenceSourceServer {
  HttpServer? _server;

  Uri get baseUri {
    final server = _server;
    if (server == null) throw StateError('Server is not running.');
    return Uri(
      scheme: 'http',
      host: server.address.address,
      port: server.port,
      path: '/',
    );
  }

  Future<Uri> start({int port = 8787}) async {
    _server ??= await HttpServer.bind(InternetAddress.loopbackIPv4, port);
    unawaited(_serve(_server!));
    return baseUri;
  }

  Future<void> close() async {
    await _server?.close(force: true);
    _server = null;
  }

  Future<void> _serve(HttpServer server) async {
    await for (final request in server) {
      try {
        _handle(request);
      } catch (_) {
        _error(request, 500, 'INTERNAL_ERROR', retryable: true);
      }
    }
  }

  void _handle(HttpRequest request) {
    _cors(request.response);
    request.response.headers.set('X-Open-Reading-Protocol', protocolVersion);

    if (request.method == 'OPTIONS') {
      request.response.statusCode = HttpStatus.noContent;
      request.response.close();
      return;
    }
    if (request.method != 'GET') {
      request.response.headers.set(HttpHeaders.allowHeader, 'GET, OPTIONS');
      _error(request, 405, 'METHOD_NOT_ALLOWED');
      return;
    }

    final path = request.uri.path;
    final segments = request.uri.pathSegments;
    if (path == '/.well-known/open-reading-source.json') {
      _sendJson(request, 200, {
        'protocol': 'open-reading-source',
        'protocolVersion': protocolVersion,
        'id': 'dev.open-reading.reference-source',
        'name': 'ORSP Reference Source',
        'description': 'Original sample content for protocol development.',
        'apiBaseUrl': baseUri.resolve('api/').toString(),
        'languages': ['zh-CN', 'en'],
        'capabilities': ['search', 'detail', 'catalog', 'content'],
      });
      return;
    }
    if (path == '/api/v1/search') {
      _search(request);
      return;
    }
    if (segments.length >= 4 &&
        segments[0] == 'api' &&
        segments[1] == 'v1' &&
        segments[2] == 'books') {
      final bookId = segments[3];
      if (!_validId(bookId)) {
        _error(request, 400, 'INVALID_BOOK_ID');
        return;
      }
      final book = books[bookId];
      if (book == null) {
        _error(request, 404, 'BOOK_NOT_FOUND');
        return;
      }
      if (segments.length == 4) {
        _sendJson(request, 200, book.metadata);
        return;
      }
      if (segments.length == 5 && segments[4] == 'chapters') {
        _catalog(request, book);
        return;
      }
      if (segments.length == 6 && segments[4] == 'chapters') {
        final chapterId = segments[5];
        if (!_validId(chapterId)) {
          _error(request, 400, 'INVALID_CHAPTER_ID');
          return;
        }
        final chapter = book.chapters
            .where((item) => item.id == chapterId)
            .firstOrNull;
        if (chapter == null) {
          _error(request, 404, 'CHAPTER_NOT_FOUND');
          return;
        }
        _sendJson(request, 200, {
          'bookId': bookId,
          'chapterId': chapter.id,
          'title': chapter.title,
          'contentType': 'text/plain',
          'content': chapter.content,
          'baseUrl': baseUri.resolve('books/$bookId/').toString(),
        });
        return;
      }
    }
    _error(request, 404, 'ROUTE_NOT_FOUND');
  }

  void _search(HttpRequest request) {
    final rawQuery = request.uri.queryParameters['q'];
    if (rawQuery == null) {
      _error(request, 400, 'QUERY_REQUIRED');
      return;
    }
    final query = rawQuery.trim();
    if (query.isEmpty || query.runes.length > 200) {
      _error(request, 400, 'INVALID_QUERY');
      return;
    }
    final pagination = _pagination(request);
    if (pagination == null) return;

    final normalizedQuery = query.toLowerCase();
    final matches = books.values
        .where(
          (book) => '${book.metadata['title']} ${book.metadata['author']}'
              .toLowerCase()
              .contains(normalizedQuery),
        )
        .map((book) => book.metadata)
        .toList();
    final pageItems = _page(matches, pagination);
    _sendJson(request, 200, {
      'items': pageItems,
      'page': pagination.page,
      'pageSize': pagination.pageSize,
      'total': matches.length,
      'hasMore': pagination.end < matches.length,
    });
  }

  void _catalog(HttpRequest request, BookData book) {
    final pagination = _pagination(request, defaultPageSize: 100);
    if (pagination == null) return;
    final chapters = [...book.chapters]
      ..sort((a, b) {
        final byOrder = a.order.compareTo(b.order);
        return byOrder != 0 ? byOrder : a.id.compareTo(b.id);
      });
    _sendJson(request, 200, {
      'items': _page(
        chapters,
        pagination,
      ).map((chapter) => chapter.metadata).toList(),
      'page': pagination.page,
      'pageSize': pagination.pageSize,
      'total': chapters.length,
      'hasMore': pagination.end < chapters.length,
    });
  }

  Pagination? _pagination(HttpRequest request, {int defaultPageSize = 20}) {
    final pageText = request.uri.queryParameters['page'];
    final pageSizeText = request.uri.queryParameters['pageSize'];
    final page = pageText == null ? 1 : int.tryParse(pageText);
    final pageSize = pageSizeText == null
        ? defaultPageSize
        : int.tryParse(pageSizeText);
    if (page == null || page < 1) {
      _error(request, 400, 'INVALID_PAGE');
      return null;
    }
    if (pageSize == null || pageSize < 1 || pageSize > 100) {
      _error(request, 400, 'INVALID_PAGE_SIZE');
      return null;
    }
    return Pagination(page, pageSize);
  }

  List<T> _page<T>(List<T> items, Pagination pagination) {
    if (pagination.start >= items.length) return const [];
    final end = pagination.end.clamp(0, items.length);
    return items.sublist(pagination.start, end);
  }

  bool _validId(String value) => _opaqueIdPattern.hasMatch(value);

  void _error(
    HttpRequest request,
    int status,
    String code, {
    bool retryable = false,
  }) {
    _sendJson(request, status, {
      'error': {
        'code': code,
        'message': code.replaceAll('_', ' '),
        'retryable': retryable,
      },
    }, cacheable: false);
  }

  void _sendJson(
    HttpRequest request,
    int status,
    Object body, {
    bool cacheable = true,
  }) {
    final encoded = jsonEncode(body);
    final response = request.response;
    if (cacheable) {
      final etag = _etag(encoded);
      response.headers
        ..set(HttpHeaders.etagHeader, etag)
        ..set(HttpHeaders.cacheControlHeader, 'public, max-age=60');
      if (request.headers.value(HttpHeaders.ifNoneMatchHeader) == etag) {
        response.statusCode = HttpStatus.notModified;
        response.close();
        return;
      }
    } else {
      response.headers.set(HttpHeaders.cacheControlHeader, 'no-store');
    }
    response
      ..statusCode = status
      ..headers.contentType = ContentType.json
      ..write(encoded)
      ..close();
  }

  String _etag(String value) {
    var hash = 0x811c9dc5;
    for (final byte in utf8.encode(value)) {
      hash ^= byte;
      hash = (hash * 0x01000193) & 0xffffffff;
    }
    return '"${hash.toRadixString(16).padLeft(8, '0')}"';
  }

  void _cors(HttpResponse response) {
    response.headers
      ..set('Access-Control-Allow-Origin', '*')
      ..set('Access-Control-Allow-Methods', 'GET, OPTIONS')
      ..set(
        'Access-Control-Allow-Headers',
        'Accept, Content-Type, If-None-Match, X-Open-Reading-Protocol',
      )
      ..set('Access-Control-Expose-Headers', 'ETag, X-Open-Reading-Protocol');
  }
}

class Pagination {
  final int page;
  final int pageSize;

  const Pagination(this.page, this.pageSize);

  int get start => (page - 1) * pageSize;
  int get end => start + pageSize;
}

class BookData {
  final Map<String, Object> metadata;
  final List<ChapterData> chapters;

  const BookData(this.metadata, this.chapters);
}

class ChapterData {
  final String id;
  final String title;
  final int order;
  final String content;

  const ChapterData(this.id, this.title, this.order, this.content);

  Map<String, Object> get metadata => {
    'id': id,
    'title': title,
    'order': order,
    'updatedAt': '2026-07-11T00:00:00Z',
  };
}

const books = <String, BookData>{
  'protocol-garden': BookData(
    {
      'id': 'protocol-garden',
      'title': '协议花园',
      'author': 'Open Reading',
      'description': 'An original micro-story used to test ORSP.',
      'categories': ['Original', 'Protocol'],
      'status': 'completed',
      'latestChapter': '共同的语言',
      'language': 'zh-CN',
      'updatedAt': '2026-07-11T00:00:00Z',
    },
    [
      ChapterData('seed', '一颗种子', 1, '清晨，阅读器收到了一颗没有名字的种子。它先问：你遵循什么协议？'),
      ChapterData(
        'common-language',
        '共同的语言',
        2,
        '当发现、搜索、目录和正文都有了共同语言，每位开发者都能种下自己的故事。',
      ),
    ],
  ),
  'river-of-pages': BookData(
    {
      'id': 'river-of-pages',
      'title': '书页之河',
      'author': 'Open Reading',
      'description': 'A second original sample used for pagination tests.',
      'categories': ['Original'],
      'status': 'ongoing',
      'latestChapter': '向远方',
      'language': 'zh-CN',
      'updatedAt': '2026-07-12T00:00:00Z',
    },
    [
      ChapterData('source', '源头', 1, '每一条繁华的河流，都从一个可以验证的小源头开始。'),
      ChapterData('distance', '向远方', 2, '当规则稳定、道路开放，故事便会流向更多读者。'),
    ],
  ),
};

Future<void> main(List<String> arguments) async {
  final portIndex = arguments.indexOf('--port');
  final port = portIndex >= 0 && portIndex + 1 < arguments.length
      ? int.tryParse(arguments[portIndex + 1]) ?? 8787
      : 8787;
  final server = ReferenceSourceServer();
  final uri = await server.start(port: port);
  stdout.writeln('ORSP reference source: $uri');
  stdout.writeln(
    'Discovery: ${uri.resolve('.well-known/open-reading-source.json')}',
  );
  stdout.writeln('Press Ctrl+C to stop.');
  final stopped = Completer<void>();
  ProcessSignal.sigint.watch().listen((_) {
    if (!stopped.isCompleted) stopped.complete();
  });
  await stopped.future;
  await server.close();
}

extension<T> on Iterable<T> {
  T? get firstOrNull {
    final iterator = this.iterator;
    return iterator.moveNext() ? iterator.current : null;
  }
}
