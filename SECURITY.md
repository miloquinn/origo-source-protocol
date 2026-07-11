# Security Policy

Please do not open public issues for vulnerabilities that could expose user
data, credentials, private source URLs, or content-provider infrastructure.

Report security problems privately through GitHub's security advisory feature
for this repository. Include reproduction steps, affected protocol version,
and the expected impact.

ORSP source operators should use HTTPS in production, validate all opaque IDs
and query parameters, sanitize HTML, set response-size limits, and avoid
returning cookies, tokens, internal URLs, or executable scripts.
