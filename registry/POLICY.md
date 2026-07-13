# Registry Review and Removal Policy

[简体中文](POLICY.zh-CN.md)

## Scope

The registry lists public ORSP sources that implement the complete Core Reading
profile. Listing is discretionary and does not certify content ownership,
security, permanence, or quality.

## Submission declarations

Submitters must state that:

- they operate the source or are authorized by its operator to submit it;
- the source distributes only original, public-domain, or licensed content;
- the provided test query is safe and stable enough for automated checks;
- maintainers will respond to security, availability, and rights reports;
- no secret, cookie, or private infrastructure detail is included.

## Review

Automated validation is evidence, not the final decision. Reviewers may request
ownership evidence, clearer licensing information, source-code links, a public
reporting channel, or changes needed to protect users and infrastructure.

Reviewers should explain rejection or deferral using concrete protocol, safety,
maintenance, or policy reasons. Competing readers and sources must be treated
under the same criteria.

Source IDs must be unique within this registry; automated validation rejects a
submission whose ID duplicates an accepted entry. A submission that reuses the
ID of a previously accepted source is treated as a maintainer transfer and
requires the evidence described below, not a fresh review.

## Maintainer transfer

An existing maintainer may add or transfer responsibility through a pull
request. If all maintainers are unreachable, a new operator must demonstrate
control of the discovery endpoint or source domain. The stable source ID should
remain unchanged only when the logical source continues.

## Operational states

- `verified`: current compatibility and policy checks pass.
- `degraded`: some checks fail but the core reading path remains usable.
- `offline`: repeated checks cannot reach or use the source.
- `unmaintained`: maintainers do not respond within the published review window.
- `suspended`: hidden or warned due to an active safety, abuse, or rights issue.
- `removed`: no longer distributed by the active registry.

Except for urgent risks, a source should not be removed after one failed check.
Repeated failures should first mark it degraded, then offline. Restoration uses
the same validation process as a new submission.

## Emergency suspension

Maintainers may immediately suspend a source for credential exposure, malicious
content, unsafe redirects, client exploitation, credible copyright complaints,
or deliberate evasion of registry checks. Public notes must avoid disclosing
secrets or details that increase user risk.

## Appeals

Source maintainers may open a new pull request or issue with corrected evidence.
An appeal should be reviewed by someone other than the person who made the
original discretionary decision when another reviewer is available.
