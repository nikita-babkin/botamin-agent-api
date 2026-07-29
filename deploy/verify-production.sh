#!/bin/sh
set -eu

PROJECT_DIR="${PROJECT_DIR:-/opt/botamin-api}"
BASE_URL="${BASE_URL:-https://botamin-151-243-3-142.nip.io}"

cd "$PROJECT_DIR"

API_KEY=$(sed -n 's/^BOTAMIN_API_KEY=//p' .env)
if [ -z "$API_KEY" ]; then
    echo "BOTAMIN_API_KEY is missing" >&2
    exit 1
fi

no_key_status=$(curl -sS -o /tmp/botamin-no-key.json -w '%{http_code}' \
    -X POST "$BASE_URL/available-slots" \
    -H 'Content-Type: application/json' \
    -d '{"date_mode":"nearest","period":"any"}')

slots_status=$(curl -sS -o /tmp/botamin-slots.json -w '%{http_code}' \
    -X POST "$BASE_URL/available-slots" \
    -H 'Content-Type: application/json' \
    -H "X-API-Key: $API_KEY" \
    -d '{"date_mode":"nearest","period":"any"}')

invalid_email_status=$(curl -sS -o /tmp/botamin-invalid-email.json -w '%{http_code}' \
    -X POST "$BASE_URL/book-meeting" \
    -H 'Content-Type: application/json' \
    -H "X-API-Key: $API_KEY" \
    -d '{"slot_datetime":"2030-01-10T11:00:00+03:00","contact":"@test_user","work_email":"not-an-email","company_activity":"Test"}')

test "$no_key_status" = 401
test "$slots_status" = 200
test "$invalid_email_status" = 422

python3 - /tmp/botamin-slots.json <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as file:
    body = json.load(file)

assert body["success"] is True
assert len(body["slots"]) == 2
print(json.dumps(body, ensure_ascii=False))
PY

printf 'NO_KEY=%s SLOTS=%s INVALID_EMAIL=%s\n' \
    "$no_key_status" "$slots_status" "$invalid_email_status"
