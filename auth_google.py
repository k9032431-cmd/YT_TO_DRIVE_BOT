"""(Ätiýaçlyk) Google rugsadyny terminaldan almak.  Adatça gerek däl —
bota credentials.json iberseňiz, bot özi sorar. Işletmek: ytbot auth"""

import sys

import drive


def main() -> None:
    try:
        flow, url = drive.start_auth()
    except RuntimeError:
        print(f"\n[!] {drive.CREDENTIALS_FILE} tapylmady. README.md-ä serediň.\n")
        sys.exit(1)

    print("\n1) Şu ssylkany brauzerde açyň we 'Allow' basyň:\n")
    print(url)
    print("\n2) Soňunda 'This site can't be reached' çykar — bu kadaly.")
    print("   Salgy setirindäki http://localhost/?...code=... salgyny göçürip şu ýere goýuň.\n")
    try:
        drive.finish_auth(flow, input("Salgy: "))
    except Exception as e:  # noqa: BLE001
        print(f"\n[!] Ýalňyşlyk: {e}\n")
        sys.exit(1)
    print("\n[OK] Üstünlikli! Indi: ytbot restart\n")


if __name__ == "__main__":
    main()
