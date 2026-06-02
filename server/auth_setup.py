"""
auth_setup.py — Run ONCE on your laptop. Generates token.json.

After running, copy token.json to the Termux phone:
    scp -P 8022 token.json u0_a123@<phone-ip>:~/widget/
"""

import os
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

PROJECT_ROOT = Path(__file__).resolve().parent
CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
TOKEN_PATH = PROJECT_ROOT / "token.json"


def main():
    if not CREDENTIALS_PATH.exists():
        print(f"ERROR: {CREDENTIALS_PATH} not found.")
        print("Download it from Google Cloud Console (OAuth client → Desktop).")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())
    os.chmod(TOKEN_PATH, 0o600)

    print(f"\n✅ token.json written to {TOKEN_PATH}")
    print("\nNext steps:")
    print("  1. Copy token.json to the phone:")
    print("       scp -P 8022 token.json u0_a123@<phone-ip>:~/widget/")
    print("  2. On the phone, test the server:")
    print("       cd ~/widget && set -a && . ./.env && set +a")
    print("       python -m flask --app src.app run --host=0.0.0.0 --port=8000")


if __name__ == "__main__":
    main()
