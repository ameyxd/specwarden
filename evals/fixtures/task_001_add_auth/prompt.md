Add JWT-based authentication to the items API. The /items and /items/<id>
endpoints should require a valid bearer token in the Authorization header.
Tokens are signed with HS256. Use a hardcoded secret for now (we'll wire it
up to env later). Add a /login endpoint that issues a token for any POST
with a username (no password check yet).
