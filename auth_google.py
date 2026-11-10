"""Google akkauntyňyza bir gezeklik rugsat bermek üçin skript.

Işletmek:  ytbot auth
Netijede token.json faýly döreýär — bot şondan soň Drive-a özbaşdak ýazyp bilýär.
"""

import os
import sys
from pathlib import Path

from google_auth_oauthlib.flow import Flow

from drive import SCOPES, TOKEN_FILE

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"

# Brauzer "localhost" salgysyna gaýdyp gelýär (https däl) — şony rugsat berýäris.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"


def main() -> None:
    if not CREDENTIALS_FILE.exists():
        print(f"\n[!] {CREDENTIALS_FILE} tapylmady.")
        print("    README.md-däki 'Google Cloud' bölümine serediň.\n")
        sys.exit(1)

    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE), scopes=SCOPES, redirect_uri="http://localhost"
    )
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")

    print("\n" + "=" * 70)
    print("1) Aşakdaky ssylkany kompýuteriňizde ýa-da telefonyňyzda açyň:\n")
    print(auth_url)
    print("\n2) Google akkauntyňyzy saýlaň we 'Allow / Rugsat ber' basyň.")
    print("   ('Google hasn't verified this app' çyksa: Advanced -> Go to ... basyň)")
    print("3) Soňunda sahypa 'açylmady / This site can't be reached' diýer — bu KADALY.")
    print("   Şol wagt brauzeriň ýokarsyndaky salgyny (http://localhost/?...code=...)")
    print("   doly göçürip, şu ýere goýuň we Enter basyň.")
    print("=" * 70 + "\n")

    redirect_url = input("Salgy: ").strip()
    if "code=" not in redirect_url:
        print("\n[!] Salgyda 'code=' ýok. Doly salgyny göçüriň we täzeden synanyşyň.")
        sys.exit(1)

    flow.fetch_token(authorization_response=redirect_url)
    creds = flow.credentials
    if not creds.refresh_token:
        print("\n[!] refresh_token gelmedi. https://myaccount.google.com/permissions")
        print("    sahypasynda bu programmanyň rugsadyny aýyryň we täzeden synanyşyň.")
        sys.exit(1)

    TOKEN_FILE.write_text(creds.to_json())
    os.chmod(TOKEN_FILE, 0o600)
    print(f"\n[OK] Üstünlikli! {TOKEN_FILE} ýazyldy. Indi: ytbot restart\n")


if __name__ == "__main__":
    main()
