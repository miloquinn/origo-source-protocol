import 'dart:async';
import 'dart:convert';
import 'dart:io';

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

  Future<void> close() async => _server?.close(force: true);

  Future<void> _serve(HttpServer server) async {
    await for (final request in server) {
      try {
        _handle(request);
      } catch (error) {
        _send(request.response, 500, {
          'error': {'code': 'INTERNAL_ERROR', 'message': '$error'},
        });
      }
    }
  }

  void _handle(HttpRequest request) {
    _cors(request.response);
    if (request.method == 'OPTIONS') {
      request.response.close();
      return;
    }
    if (request.method != 'GET') {
      _error(request.response, 405, 'METHOD_NOT_ALLOWED');
      return;
    }

    final path = request.uri.path;
    final segments = request.uri.pathSegments;
    if (path == '/.well-known/open-reading-source.json') {
      _send(request.response, 200, {
        'protocol': 'open-reading-source',
        'protocolVersion': '1.0',
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
      final book = books[bookId];
      if (book == null) {
        _error(request.response, 404, 'BOOK_NOT_FOUND');
        return;
      }
      if (segments.length == 4) {
        _send(request.response, 200, book.metadata);
        return;
      }
      if (segments.length == 5 && segments[4] == 'chapters') {
        _send(request.response, 200, {
          'items': book.chapters.map((chapter) => chapter.metadata).toList(),
        });
        return;
      }
      if (segments.length == 6 && segments[4] == 'chapters') {
        final chapter = book.chapters
            .where((item) => item.id == segments[5])
            .firstOrNull;
        if (chapter == null) {
          _error(request.response, 404, 'CHAPTER_NOT_FOUND');
          return;
        }
        _send(request.response, 200, {
          'bookId': bookId,
          'chapterId': chapter.id,
          'title': chapter.title,
          'contentType': 'text/plain',
          'content': chapter.content,
        });
        return;
      }
    }
    _error(request.response, 404, 'ROUTE_NOT_FOUND');
  }

  void _search(HttpRequest request) {
    final query = (request.uri.queryParameters['q'] ?? '').toLowerCase();
    final matches = books.values
        .where(
          (book) => '${book.metadata['title']} ${book.metadata['author']}'
              .toLowerCase()
              .contains(query),
        )
        .map((book) => book.metadata)
        .toList();
    _send(request.response, 200, {
      'items': matches,
      'page': 1,
      'pageSize': matches.length,
      'total': matches.length,
      'hasMore': false,
    });
  }

  void _error(HttpResponse response, int status, String code) {
    _send(response, status, {
      'error': {'code': code, 'message': code.replaceAll('_', ' ')},
    });
  }

  void _send(HttpResponse response, int status, Object body) {
    response
      ..statusCode = status
      ..headers.contentType = ContentType.json
      ..write(jsonEncode(body))
      ..close();
  }

  void _cors(HttpResponse response) {
    response.headers
      ..set('Access-Control-Allow-Origin', '*')
      ..set('Access-Control-Allow-Methods', 'GET, OPTIONS')
      ..set(
        'Access-Control-Allow-Headers',
        'Content-Type, X-Open-Reading-Protocol',
      );
  }
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
