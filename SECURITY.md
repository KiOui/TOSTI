# Security policy

TOSTI handles personal data for Radboud students, processes payments and refunds, and includes legally-loaded surfaces like Yivi-backed age verification for the beer fridge. If you find a security issue, we want to hear about it before anyone else does.

## Supported versions

Only the most recent version of TOSTI &mdash; whatever is currently deployed at <https://tosti.science.ru.nl> &mdash; is supported. We do not back-port fixes to older deployments.

The same applies to the [TOSTI-fridge-client](https://github.com/KiOui/TOSTI-fridge-client) firmware running on the Raspberry Pi inside each beer fridge: only the most recent release is supported.

## Reporting a vulnerability

**Do not open a public GitHub issue or pull request for security-sensitive bugs.** Email <www-tosti@science.ru.nl> instead.

Please include:

- A description of the issue and what an attacker could do with it.
- Steps to reproduce. A minimal proof-of-concept &mdash; a `curl` invocation, a script, a request payload &mdash; helps us confirm the issue quickly.
- The TOSTI version or commit you tested against (if you know it).
- Whether you've already shared the details with anyone else.

You should hear back from the website committee within **7 days** with an acknowledgement. We'll work with you to confirm the issue, agree on a fix timeline, and credit you in the release notes if you'd like.

If you do not get a response within 14 days, escalate by emailing <tartaruswebsite@science.ru.nl> and asking them to chase it up.

## What counts as a security issue

When in doubt, report it &mdash; we'd rather field a false alarm than miss something. As a rough guide, these are squarely in scope:

- **Authentication / authorisation bypasses** &mdash; anything that lets a user access another user's account, place orders or transactions on someone else's behalf, or read data without the right scope.
- **Age-verification bypass** for the beer fridge. This is the most legally-loaded surface in the project; treat anything that lets an underage user open a fridge as a high-severity issue.
- **OAuth / MCP issues** &mdash; flaws in the authorize / token / consent flow at `/oauth/authorize/`, `/oauth/token/`, `/oauth/register/`, or the MCP endpoints. Scope-confusion, PKCE bypass, token leakage, replayable codes, etc.
- **SAML / SURFconext integration** issues &mdash; signature bypass, assertion replay, IdP impersonation.
- **Privacy leaks** &mdash; endpoints that return PII (names, emails, age verifications, transaction history, song requests) to viewers who shouldn't see it.
- **Stored XSS / CSRF / SQL injection / SSRF** in any user-reachable surface.
- **Secret leakage** &mdash; credentials, tokens, or keys exposed in the repo, in logs, in Sentry events, or in client-side responses.
- **Supply chain** &mdash; vulnerabilities in our vendored frontend assets (Vue, Bootstrap, Swagger UI, etc.) or in dependencies that meaningfully affect TOSTI.

Generally out of scope (open a regular GitHub issue for these):

- Bugs in feature behaviour that don't have a security impact.
- Cosmetic issues, broken links, typos.
- Reports against domains we don't operate (e.g. `radboudnet.nl`, `surf.nl`).
- Findings from automated scanners without a working proof-of-concept &mdash; we appreciate the heads-up, but please verify the finding manually first.

## What we ask of reporters

- **Don't pivot.** Once you've demonstrated the issue exists, stop. Don't download other people's data, modify production state, or escalate to other surfaces.
- **Don't test in production unless you have to.** A local dev instance reproduces almost everything.
- **Coordinate disclosure.** Don't publish details &mdash; talks, blog posts, social media &mdash; until we've shipped a fix and agreed on a publication date with you.

## Maintainer contact

- Website committee &mdash; <www-tosti@science.ru.nl> (security)
- General &mdash; <tartaruswebsite@science.ru.nl>

Both addresses reach the same Tartarus website committee. The first is reserved for security-sensitive correspondence.
</content>
</invoke>