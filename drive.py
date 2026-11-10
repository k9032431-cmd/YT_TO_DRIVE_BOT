"""Google Drive bilen işleýän bölek: rugsat almak, faýl ýüklemek, ssylka gaýtarmak."""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = Path(__file__).resolve().parent
TOKEN_FILE = BASE_DIR / "token.json"
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
FOLDER_ID_FILE = BASE_DIR / "folder_id.txt"

# "drive.file" — bot diňe özi döreden faýllary görýär/üýtgedýär.
# Siziň Drive-daky beýleki faýllaryňyza eli ýetmeýär.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Google rugsatdan soň brauzeri "http://localhost" salgysyna gaýtarýar (https däl).
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"


# ---------- Rugsat (OAuth) ----------

def start_auth() -> tuple[Flow, str]:
    """Rugsat prosesini başlaýar. (flow, açmaly ssylka) gaýtarýar."""
    if not CREDENTIALS_FILE.exists():
        raise RuntimeError("credentials.json ýok.")
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE), scopes=SCOPES, redirect_uri="http://localhost"
    )
    url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    return flow, url


def finish_auth(flow: Flow, redirect_url: str) -> None:
    """Ulanyjy göçüren 'http://localhost/?...code=...' salgysyndan token alýar."""
    redirect_url = redirect_url.strip()
    if not redirect_url.startswith("http"):
        redirect_url = "http://" + redirect_url
    flow.fetch_token(authorization_response=redirect_url)
    creds = flow.credentials
    if not creds.refresh_token:
        raise RuntimeError(
            "refresh_token gelmedi. https://myaccount.google.com/permissions "
            "sahypasynda bu programmanyň rugsadyny aýyryň we täzeden synanyşyň."
        )
    TOKEN_FILE.write_text(creds.to_json())
    os.chmod(TOKEN_FILE, 0o600)


def is_connected() -> bool:
    return TOKEN_FILE.exists()


def _credentials() -> Credentials:
    if not TOKEN_FILE.exists():
        raise RuntimeError("Google Drive birikdirilmedik. Bota credentials.json iberiň.")
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())
        else:
            raise RuntimeError("Google rugsady köne. Bota /auth ýazyň.")
    return creds


# ---------- Ýüklemek ----------

def _service():
    return build("drive", "v3", credentials=_credentials(), cache_discovery=False)


def _get_folder_id(service, folder_name: str) -> str:
    """Papkany tapýar, ýok bolsa döredýär. ID-ni faýlda ýatda saklaýar."""
    if FOLDER_ID_FILE.exists():
        name, _, folder_id = FOLDER_ID_FILE.read_text().strip().partition("|")
        if name == folder_name and folder_id:
            try:
                f = service.files().get(fileId=folder_id, fields="id, trashed").execute()
                if not f.get("trashed"):
                    return folder_id
            except Exception:
                pass  # papka pozulan bolsa — täzesini döredýäris

    folder = service.files().create(
        body={"name": folder_name, "mimeType": "application/vnd.google-apps.folder"},
        fields="id",
    ).execute()
    FOLDER_ID_FILE.write_text(f"{folder_name}|{folder['id']}")
    return folder["id"]


def upload_file(path: str, folder_name: str, make_public: bool) -> str:
    """Faýly Drive-a ýükleýär we görmek üçin ssylkany gaýtarýar."""
    service = _service()
    folder_id = _get_folder_id(service, folder_name)

    media = MediaFileUpload(
        path, mimetype="video/mp4", resumable=True, chunksize=16 * 1024 * 1024
    )
    request = service.files().create(
        body={"name": os.path.basename(path), "parents": [folder_id]},
        media_body=media,
        fields="id, webViewLink",
    )
    response = None
    while response is None:
        _, response = request.next_chunk()

    if make_public:
        service.permissions().create(
            fileId=response["id"], body={"type": "anyone", "role": "reader"}
        ).execute()

    return response["webViewLink"]
