# Administrator login lifetime

Administrator sessions created after this release expire exactly24 hours after
login. Reading a session does not extend its administrator expiry. Ordinary
members retain the existing12-hour sliding policy.

Session creation reads role and active status from the server account row.
Browser-supplied roles or local-storage expiry cannot grant administrator access.
Each token lookup rechecks the account's current role/status. Demotion removes
administrator privileges immediately and caps remaining ordinary-member lifetime
at12 hours. Disabled/deleted accounts and expired tokens cannot authenticate.
Existing explicit logout and administrative password-reset revocation remain.

The browser persistence bridge now saves the validated server expiration rather
than `Date.now()+TTL`. Cookie Max-Age uses only the remaining server lifetime;
reopening the browser cannot restart the24-hour administrator period. The formal
shell already accepts a supplied expiration and keeps its unchanged12-hour
fallback for ordinary/legacy messages. No shell deployment or schema migration
is required. Neither browser storage nor a valid-looking token bypasses server
validation.

Existing sessions retain their recorded expiration. The new administrator
duration starts on the next successful login; no existing/revoked/expired token
is silently granted a fresh24 hours. Clearing browser storage, explicit logout,
account disablement, backend revocation or a failed server validation can still
require login before the nominal time limit.

Verification uses isolated member/cost/report/BOM databases, simulated time at
12h+,23h59m59s and24h, repeat session reads, ordinary-member renewal, role
demotion, disablement, administrative password reset, explicit logout, member
listing/access, active cost history and remote snapshot restoration. No runtime
database, account, customer assignment or price list is replaced by this change.
