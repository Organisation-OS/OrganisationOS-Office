#!/bin/bash
set -euo pipefail
# Per-instance secret mounted by the native runtime lifecycle, never included in the image.
secret=/run/secrets/organisationos-office-jwt
if [[ ! -f "$secret" || -L "$secret" || "$(stat -c '%u:%a' "$secret")" != '0:400' ]]; then
  echo 'OrganisationOS Office: protected instance JWT secret is required.' >&2
  exit 78
fi
JWT_SECRET=$(cat "$secret")
if [[ ! "$JWT_SECRET" =~ ^[A-Za-z0-9_-]{64,128}$ ]]; then
  echo 'OrganisationOS Office: invalid instance JWT secret format.' >&2
  exit 78
fi
export JWT_SECRET
exec /app/ds/run-document-server.sh "$@"
