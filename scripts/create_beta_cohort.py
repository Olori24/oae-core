#!/usr/bin/env python3
"""Create the initial 20-developer OAE beta cohort.

Set OAE_API_URL to the running OAE API before executing this script.
API keys are printed once and should be stored securely; OAE stores only
salted PBKDF2 hashes of the keys.
"""

import json
import os
import sys
import urllib.error
import urllib.request

API_URL = os.environ.get("OAE_API_URL", "http://127.0.0.1:8000").rstrip("/")
COHORT_SIZE = 20


def create_tenant(name: str) -> dict[str, str]:
    payload = json.dumps({"name": name}).encode()
    request = urllib.request.Request(
        f"{API_URL}/v1/tenants",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def main() -> int:
    print(f"OAE developer beta cohort — {API_URL}")
    print(f"Creating {COHORT_SIZE} isolated tenants...\n")
    print("developer,tenant_id,api_key")

    for number in range(1, COHORT_SIZE + 1):
        name = f"Developer {number:02d}"
        try:
            result = create_tenant(name)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"ERROR,{name},{exc.code},{body}", file=sys.stderr)
            return 1
        except urllib.error.URLError as exc:
            print(f"ERROR,{name},connection,{exc.reason}", file=sys.stderr)
            return 1

        print(f"{name},{result['tenant_id']},{result['api_key']}")

    print("\nStore the API keys securely. They cannot be recovered later.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
