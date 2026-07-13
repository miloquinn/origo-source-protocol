# Security Policy

[简体中文](SECURITY.zh-CN.md)

Please do not open public issues for vulnerabilities that could expose user
data, credentials, private source URLs, or content-provider infrastructure.

Report security problems privately through GitHub's security advisory feature
for this repository. Include reproduction steps, affected protocol version,
expected impact, and whether the issue affects readers, sources, adapters, or
registries.

Source operators should use HTTPS in production, validate all IDs and known
query parameters, sanitize HTML, set response-size and execution-time limits,
and avoid returning cookies, tokens, internal URLs, stack traces, or executable
content.

Readers should treat discovery URLs and all source responses as untrusted. They
should defend against server-side request forgery, DNS rebinding, loopback and
private-network access unless explicitly allowed, redirect loops, TLS
downgrades, decompression bombs, oversized images, unsafe HTML, and dangerous
URL schemes.

Adapters should isolate source-specific credentials and parsing logic from the
public ORSP response. Registries should avoid publishing private source
locations or operational details that increase attack surface.
