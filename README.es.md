# Open Reading Source Protocol

[English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) ·
[日本語](README.ja.md) · [한국어](README.ko.md) · **Español** ·
[Especificación](SPECIFICATION.md) · [OpenAPI](openapi.yaml)

Open Reading Source Protocol (ORSP) es un protocolo HTTP abierto que conecta
aplicaciones de lectura con servicios de contenido independientes. Ofrece una
interfaz común para búsquedas, metadatos de libros, capítulos y contenido.

Una aplicación solo necesita implementar ORSP una vez para conectarse a todas
las fuentes compatibles. Los desarrolladores pueden crear servicios para obras
originales, de dominio público o debidamente licenciadas, o añadir un adaptador
ORSP a un servicio que estén autorizados a utilizar.

## Resumen del protocolo

Cada fuente publica un documento de descubrimiento:

```text
GET /.well-known/open-reading-source.json
```

También implementa cuatro operaciones principales:

```text
GET {apiBaseUrl}v1/search?q={query}&page=1&pageSize=20
GET {apiBaseUrl}v1/books/{bookId}
GET {apiBaseUrl}v1/books/{bookId}/chapters?page=1&pageSize=100
GET {apiBaseUrl}v1/books/{bookId}/chapters/{chapterId}
```

La versión 1.3 también define operaciones opcionales de descubrimiento,
categorías y exploración:

```text
GET {apiBaseUrl}v1/discover
GET {apiBaseUrl}v1/categories
GET {apiBaseUrl}v1/browse?category={categoryId}&sort=latest&page=1&pageSize=20
```

Consulta la [especificación](SPECIFICATION.md) y la definición
[OpenAPI 3.1](openapi.yaml) para conocer todos los campos y errores.

## Ejecutar la fuente de referencia

El repositorio incluye un servidor Dart sin dependencias externas. Los libros
y textos de ejemplo son contenido original creado para pruebas.

```bash
dart run examples/dart_server.dart
```

Usa `http://127.0.0.1:8787` en un ordenador o `http://10.0.2.2:8787` en un
emulador de Android.

## Crear una fuente propia

1. Publica el documento de descubrimiento con el ID, versión, URL y capacidades.
2. Implementa búsqueda, detalles, catálogo de capítulos y contenido.
3. Usa identificadores estables y opacos para libros y capítulos.
4. Devuelve JSON UTF-8 y códigos de estado HTTP adecuados.
5. Valida las respuestas con el [JSON Schema](schemas/discovery.schema.json) y
   [OpenAPI](openapi.yaml).
6. Comprueba la compatibilidad mediante solicitudes HTTP reales.

## Estado y uso responsable

La versión `1.3` es un borrador candidato. El flujo básico de lectura ya
ha sido verificado, pero se aceptan propuestas sobre autenticación,
sincronización, paginación y formatos de contenido antes de declarar una
versión estable.

ORSP está destinado a contenido original, de dominio público o debidamente
licenciado. No debe utilizarse para eludir controles de acceso, infringir las
condiciones de un servicio ni distribuir obras sin autorización.

Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para colaborar. Licencia [MIT](LICENSE).
