# OEP-0006: Image sequences, remote audio and media refresh

Status: **Candidate experiment**

Target: ORSP **1.6 candidate**, preserving the ORSP 1.x core relations.

## Scope and negotiation

This profile adds the existing reader-compatible chapter representations
`image/sequence` and `audio/uri`. Text/plain, CommonMark and sanitized HTML
continue using the current content fields and `baseUrl` resolution rules.

| Capability | Representation | Book mediaKind | Compatibility type |
| --- | --- | --- | --- |
| Core content | text/plain, text/markdown, text/html | text | 8 |
| `top.xxread:image-sequence` | image/sequence | image-sequence | 64 |
| `top.xxread:remote-audio` | audio/uri | remote-audio | 32 |

Media capabilities are optional namespaced experiments. Discovery also declares
`contentTypes` containing each emitted representation. Unknown optional types
do not reject the source: a reader reports an unsupported representation only
when opening it, without guessing it is plain text. Sources providing media
SHOULD expose book `mediaKind` and MAY supply the legacy numeric `type` bridge
above for existing Origo X readers. Neither field changes book/chapter identity.
An unknown mediaKind maps to unknown; it MUST NOT silently enable audio/image
processing. Audio content is a recording; it is not client-generated TTS.

## Image sequence chapters

```json
{
  "bookId": "picture-book", "chapterId": "chapter-1", "title": "First pages",
  "contentType": "image/sequence", "content": "",
  "images": [
    {"url": "https://books.example/pages/1.png", "mimeType": "image/png",
     "width": 800, "height": 1200, "alt": "First page"},
    {"url": "https://books.example/pages/2.png", "mimeType": "image/png"}
  ]
}
```

The nonempty `images` array defines reading order. Each image requires an
absolute HTTP(S) `url`; optional mimeType, width, height, alt, headers and
expiresAt describe delivery. The chapter content string is empty; audio MUST
be absent. Readers preserve array order, bound decoded pixel size and bytes,
load lazily and release offscreen images. They MUST NOT execute an image as
HTML or infer an authenticated session from media metadata.

## Audio chapters

```json
{
  "bookId": "audio-book", "chapterId": "chapter-1", "title": "First recording",
  "contentType": "audio/uri", "content": "",
  "audio": {"url": "https://books.example/audio/1.mp3", "mimeType": "audio/mpeg",
            "durationSeconds": 180.5, "transport": "file"}
}
```

`audio` is required; images MUST be absent. Optional durationSeconds is a
finite positive number, at most 315360000 seconds. Optional transport is file or hls. HLS URLs identify
playlists, not raw audio files; playlist/segment redirects follow the same
network policy. Readers MAY reject codecs/transports unsupported by the target
platform and MUST avoid autoplay merely because a book detail was fetched.
Resume positions use source/book/chapter identity, media revision and seconds,
not text offsets or device page indexes. HTTP byte ranges support seekable file
delivery; HLS follows RFC 8216. Do not use this profile to distribute DRM keys.

## Media URLs and safe request hints

Optional `headers` supports only public Referer, Origin and Accept hints in
canonical spelling. It MUST NOT contain Authorization, Cookie, Host, proxy
credentials, OAuth tokens, or user/device identifiers. These are source data,
not instructions to copy the reader's session. Source-provided hints apply
only to that asset's original origin; readers do not forward them to a different
origin on redirect. Sources needing a secret upstream session proxy it server
side rather than publishing that session.

Optional expiresAt is RFC 3339 metadata. A reader opening an expired URL
revalidates the same chapter through the existing content endpoint. On media
401/403/404/410 it MAY refresh chapter metadata once and retry if the URL changed;
it MUST NOT loop indefinitely or retry with user credentials. Server 429 obeys
Retry-After. Signed delivery URL changes do not allocate new logical chapter IDs.

## Updates, EPUB and text/media boundaries

Sources implementing OEP-0005 with this profile include media representations
in their catalog snapshot. For media, contentVersion is a source-generated
64-character SHA-256 revision fingerprint covering ordered assets, actual
content revisions and media semantics, not SHA-256 of the empty content string.
Clients treat it as a comparison token and MUST NOT interpret it as a file
integrity hash. A file's integrity hash is explicitly provided separately.
Asset order, pixels/recording, title/order or format changes invalidate the
appropriate catalog/content representation. Pure delivery expiry refresh need
not change a logical content revision if media bytes and semantics are unchanged.

EPUB is a complete publication under OEP-0004, never a chapter ZIP payload.
Keep the old text chapter representation for existing readers and offer the
original publication for full layout. Book-level background music is not an
audio chapter: use explicit opt-in playback and a separate future capability.
Comments/paragraph anchors remain the distinct OEP-0004 draft contract.

## Implementation and acceptance

`schemas/media-reading.schema.json`, the core OpenAPI profile definitions,
`examples/reading_profiles_server.py`, and
`scripts/validate_reading_profiles.py` provide positive/negative fixtures and
real HTTP asset, range and expiry-refresh checks. Origo X's existing
BookSourceBook/ChapterContent parsers support the numeric bridge and these two
representations; profile tests use those parsers without claiming a new app
release or physical playback acceptance. The complete profile remains a
candidate experiment until independent implementations satisfy governance gates.

References: [CommonMark images](https://spec.commonmark.org/0.31.2/#images),
[HLS RFC 8216](https://www.rfc-editor.org/rfc/rfc8216.html),
[EPUB 3.3](https://www.w3.org/TR/epub-33/).
