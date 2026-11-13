"""Telegram bot: YouTube ssylkasyny alýar -> wideony ýükleýär -> Google Drive-a goýýar
-> Drive ssylkasyny yzyna iberýär.

Ähli sazlamalar Telegramyň içinden edilýär (telefondan amatly bolar ýaly):
  /start          — ilkinji ýazan adam botuň eýesi bolýar
  credentials.json faýlyny iberseň — Google Drive birikdirilýär
  /update         — GitHub-dan täze kody alyp boty täzeleýär
"""

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yt_dlp
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import drive

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
FOLDER_NAME = os.getenv("DRIVE_FOLDER_NAME", "YouTube Bot")
MAKE_PUBLIC = os.getenv("MAKE_PUBLIC", "true").lower() in ("1", "true", "yes", "hawa")
MAX_HEIGHT = int(os.getenv("MAX_HEIGHT", "1080"))
COOKIES_FILE = BASE_DIR / os.getenv("COOKIES_FILE", "cookies.txt")
USERS_FILE = BASE_DIR / "users.txt"   # 1-nji setir = eýesi, galanlary = rugsatly adamlar

YOUTUBE_RE = re.compile(
    r"(https?://)?(www\.|m\.|music\.)?(youtube\.com|youtu\.be)/\S+", re.IGNORECASE
)

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("ytbot")

# Serweriň diski dolmaz ýaly bir wagtda diňe 1 wideo işlenýär (beýlekiler nobata durýar).
work_lock = asyncio.Semaphore(1)
# Google rugsady garaşylýan ulanyjylar: user_id -> flow
pending_auth: dict = {}


# ---------------- Ulanyjylar ----------------

def load_users() -> list[int]:
    users: list[int] = []
    if USERS_FILE.exists():
        users = [int(x) for x in USERS_FILE.read_text().split() if x.strip().isdigit()]
    for x in os.getenv("ALLOWED_USERS", "").replace(" ", "").split(","):
        if x.isdigit() and int(x) not in users:
            users.append(int(x))
    return users


def save_users(users: list[int]) -> None:
    USERS_FILE.write_text("\n".join(str(u) for u in users) + "\n")


def owner_id() -> int | None:
    users = load_users()
    return users[0] if users else None


def is_allowed(update: Update) -> bool:
    return update.effective_user is not None and update.effective_user.id in load_users()


def is_owner(update: Update) -> bool:
    return update.effective_user is not None and update.effective_user.id == owner_id()


# ---------------- Wideo ýüklemek ----------------

def download_video(url: str, folder: str) -> str:
    """Wideony ýükleýär we faýlyň ýoluny gaýtarýar."""
    opts = {
        "format": (
            f"bv*[height<={MAX_HEIGHT}][ext=mp4]+ba[ext=m4a]/"
            f"bv*[height<={MAX_HEIGHT}]+ba/b[height<={MAX_HEIGHT}]/b"
        ),
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(folder, "%(title).150B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    if COOKIES_FILE.is_file():
        opts["cookiefile"] = str(COOKIES_FILE)

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)
    mp4 = os.path.splitext(path)[0] + ".mp4"
    return mp4 if os.path.exists(mp4) else path


# ---------------- Komandalar ----------------

HELP_TEXT = (
    "Maňa YouTube ssylkasyny iberiň — wideony Google Drive-yňyza goýup, "
    "ssylkasyny size iberaýin. 🎬\n\n"
    "Komandalar:\n"
    "/status — ýagdaý\n"
    "/id — Telegram ID-ňiz\n"
)
OWNER_HELP = (
    "\nDiňe eýesi üçin:\n"
    "/auth — Google Drive-y (täzeden) birikdirmek\n"
    "/update — boty GitHub-dan täzelemek\n"
    "/adduser 12345 — başga adama rugsat bermek\n"
    "/deluser 12345 — rugsady aýyrmak\n"
    "/users — rugsatly adamlar\n"
    "credentials.json ýa-da cookies.txt faýlyny şu ýere iberip bilersiňiz."
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if owner_id() is None:
        save_users([uid])  # ilkinji adam — eýesi
        log.info("Owner set to %s", uid)
        await update.message.reply_text(
            "🎉 Salam! Siz indi bu botuň EÝESI.\n"
            "Başga hiç kim (siz rugsat bermeseňiz) boty ulanyp bilmez.\n\n"
            + setup_hint()
        )
        return
    if not is_allowed(update):
        await update.message.reply_text(
            f"⛔ Bu bot ýapyk. Siziň ID-ňiz: {uid}\n"
            f"Eýesinden /adduser {uid} ýazmagyny haýyş ediň."
        )
        return
    text = HELP_TEXT + (OWNER_HELP if is_owner(update) else "")
    if is_owner(update) and not drive.is_connected():
        text += "\n\n" + setup_hint()
    await update.message.reply_text(text)


def setup_hint() -> str:
    if drive.is_connected():
        return "✅ Google Drive birikdirilen. YouTube ssylkasyny iberiň!"
    return (
        "⚙️ Indiki ädim: Google Drive-y birikdirmek.\n"
        "Google Cloud-dan alan credentials.json faýlyny şu ýere FAÝL edip iberiň "
        "(📎 → Faýl).\nÝa-da Client ID we Client secret (GOCSPX-...) kodlaryny hat edip iberiň."
    )


async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Siziň Telegram ID-ňiz: `{update.effective_user.id}`", parse_mode=ParseMode.MARKDOWN
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    lines = [
        "🤖 Bot işleýär",
        f"☁️ Google Drive: {'✅ birikdirilen' if drive.is_connected() else '❌ birikdirilmedik'}",
        f"🍪 cookies.txt: {'bar' if COOKIES_FILE.is_file() else 'ýok'}",
        f"📁 Papka: {FOLDER_NAME}",
        f"🎞 Iň ýokary hil: {MAX_HEIGHT}p",
        f"🔓 Hemmä açyk ssylka: {'hawa' if MAKE_PUBLIC else 'ýok'}",
        f"🔧 yt-dlp: {yt_dlp.version.__version__}",
    ]
    total, used, free = shutil.disk_usage(BASE_DIR)
    lines.append(f"💾 Serwerde boş ýer: {free / 1024**3:.1f} GB")
    await update.message.reply_text("\n".join(lines))


async def cmd_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    if not drive.CREDENTIALS_FILE.exists():
        await update.message.reply_text(setup_hint())
        return
    await send_auth_link(update)


async def send_auth_link(update: Update) -> None:
    flow, url = drive.start_auth()
    pending_auth[update.effective_user.id] = flow
    await update.message.reply_text(
        "🔑 Google Drive-a rugsat bermek:\n\n"
        "1️⃣ Aşakdaky ssylka basyň.\n"
        "2️⃣ Google akkauntyňyzy saýlaň.\n"
        "3️⃣ 'Google hasn't verified this app' çyksa: Advanced → Go to ... (unsafe) basyň "
        "(bu siziň öz programmaňyz, howpsuz).\n"
        "4️⃣ Continue / Allow basyň.\n"
        "5️⃣ Soňunda sahypa 'açylmady / This site can't be reached' diýer — bu KADALY! ✅\n"
        "6️⃣ Şol sahypanyň ýokarsyndaky salgy setirine basyp, uzyn salgyny (localhost/?...code=...) "
        "DOLY göçüriň we şu ýere hat edip iberiň.\n\n"
        f"👉 {url}",
        disable_web_page_preview=True,
    )


async def cmd_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    users = load_users()
    await update.message.reply_text(
        "Rugsatly adamlar:\n" + "\n".join(
            f"{'👑' if i == 0 else '👤'} {u}" for i, u in enumerate(users)
        )
    )


async def cmd_adduser(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Ulanylyşy: /adduser 123456789\n(Adam ID-ni bota /id ýazyp biler)")
        return
    users = load_users()
    uid = int(context.args[0])
    if uid not in users:
        users.append(uid)
        save_users(users)
    await update.message.reply_text(f"✅ {uid} goşuldy.")


async def cmd_deluser(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Ulanylyşy: /deluser 123456789")
        return
    uid = int(context.args[0])
    users = load_users()
    if uid == users[0]:
        await update.message.reply_text("Eýesini aýryp bolmaýar.")
        return
    save_users([u for u in users if u != uid])
    await update.message.reply_text(f"🗑 {uid} aýryldy.")


def run_update() -> str:
    """GitHub-dan täze kody alýar we kitaphanalary täzeleýär."""
    py = sys.executable
    steps = [
        ["git", "pull", "--ff-only"],
        [py, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
        [py, "-m", "pip", "install", "-q", "-U", "yt-dlp"],
    ]
    out = []
    for cmd in steps:
        r = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=600)
        out.append((r.stdout + r.stderr).strip()[-600:])
        if r.returncode != 0:
            raise RuntimeError(f"{' '.join(cmd[:3])} şowsuz:\n" + out[-1])
    return out[0]


async def cmd_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    msg = await update.message.reply_text("🔄 Täzelenýär... (wideo işlenýän bolsa, gutarmagyna garaşýar)")
    async with work_lock:
        try:
            git_out = await asyncio.to_thread(run_update)
        except Exception as e:  # noqa: BLE001
            await msg.edit_text(f"❌ Täzeläp bolmady:\n{e}"[:3000])
            return
        await msg.edit_text(
            f"✅ Täzelendi! Bot 10 sekuntdan täzeden işe başlar.\n\n{git_out[:1500]}"
        )
        # Programma çykýar, systemd ony täze kod bilen awtomatik täzeden işledýär.
        context.application.stop_running()


# ---------------- Faýllar (credentials.json, cookies.txt) ----------------

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    doc = update.message.document
    name = (doc.file_name or "").lower()
    if doc.file_size and doc.file_size > 5 * 1024 * 1024:
        await update.message.reply_text("Faýl gaty uly.")
        return
    data = bytes(await (await doc.get_file()).download_as_bytearray())

    if name.endswith(".json"):
        try:
            info = json.loads(data)
        except ValueError:
            await update.message.reply_text("❌ Bu JSON faýl däl.")
            return
        if "installed" not in info:
            hint = ""
            if "web" in info:
                hint = "\nSiz 'Web application' saýlapsyňyz — 'Desktop app' saýlap täzeden dörediň."
            elif info.get("type") == "service_account":
                hint = "\nBu 'Service account' faýly — bize 'OAuth client ID → Desktop app' gerek."
            await update.message.reply_text("❌ Bu dogry credentials.json däl." + hint)
            return
        drive.CREDENTIALS_FILE.write_bytes(data)
        os.chmod(drive.CREDENTIALS_FILE, 0o600)
        await update.message.reply_text("✅ credentials.json kabul edildi!")
        await send_auth_link(update)
        return

    if name.endswith(".txt") and (b"youtube.com" in data or b"# Netscape" in data):
        COOKIES_FILE.write_bytes(data)
        os.chmod(COOKIES_FILE, 0o600)
        await update.message.reply_text("✅ cookies.txt saklandy. Indi wideony täzeden iberip görüň.")
        return

    await update.message.reply_text("Bu faýly tanamadym. credentials.json ýa-da cookies.txt iberiň.")


CLIENT_ID_RE = re.compile(r"[0-9]+-[a-z0-9]+\.apps\.googleusercontent\.com")
SECRET_RE = re.compile(r"GOCSPX-[A-Za-z0-9_\-]+")
partial_client: dict = {}   # user_id -> {"id": ..., "secret": ...}


async def handle_client_text(update: Update, text: str) -> None:
    """Client ID we secret-i hatdan alyp credentials.json döredýär."""
    uid = update.effective_user.id
    part = partial_client.setdefault(uid, {})
    if m := CLIENT_ID_RE.search(text):
        part["id"] = m.group(0)
        text = text.replace(m.group(0), " ")  # ýelmeşen bolsa secret-den aýyrmak üçin
    if m := SECRET_RE.search(text):
        part["secret"] = m.group(0)
    if "id" not in part:
        await update.message.reply_text("✅ Secret alyndy. Indi Client ID-ni hem iberiň (...apps.googleusercontent.com).")
        return
    if "secret" not in part:
        await update.message.reply_text("✅ Client ID alyndy. Indi Client secret-i hem iberiň (GOCSPX- bilen başlaýar).")
        return
    info = {"installed": {
        "client_id": part["id"],
        "client_secret": part["secret"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }}
    drive.CREDENTIALS_FILE.write_text(json.dumps(info))
    os.chmod(drive.CREDENTIALS_FILE, 0o600)
    partial_client.pop(uid, None)
    await update.message.reply_text("✅ Client ID we secret kabul edildi!")
    await send_auth_link(update)


# ---------------- Hatlar ----------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text or ""
    uid = update.effective_user.id

    if owner_id() is None:
        await cmd_start(update, context)
        return
    if not is_allowed(update):
        await update.message.reply_text(f"⛔ Rugsat ýok. Siziň ID-ňiz: {uid}")
        return

    # Google rugsadyndan soňky salgy
    if uid in pending_auth and "code=" in text:
        try:
            await asyncio.to_thread(drive.finish_auth, pending_auth[uid], text)
        except Exception as e:  # noqa: BLE001
            await update.message.reply_text(
                f"❌ Bolmady: {e}\n\nTäzeden synanyşmak üçin /auth ýazyň."[:1500]
            )
            return
        pending_auth.pop(uid, None)
        await update.message.reply_text(
            "🎉 Google Drive birikdirildi! Indi islendik YouTube ssylkasyny iberiň."
        )
        return

    # credentials.json faýly ýerine Client ID we Client secret hat edip iberilse
    if is_owner(update) and (CLIENT_ID_RE.search(text) or SECRET_RE.search(text)):
        await handle_client_text(update, text)
        return

    match = YOUTUBE_RE.search(text)
    if not match:
        await update.message.reply_text("Bu YouTube ssylkasyna meňzänok 🤔")
        return
    if not drive.is_connected():
        await update.message.reply_text(
            "Google Drive heniz birikdirilmedik. " + ("" if is_owner(update) else "Eýesine ýüz tutuň.")
        )
        return

    url = match.group(0)
    if not url.startswith("http"):
        url = "https://" + url

    status = await update.message.reply_text("⏳ Nobata goýuldy...")
    async with work_lock:
        tmpdir = tempfile.mkdtemp(prefix="ytbot_")
        try:
            await status.edit_text("⬇️ YouTube-dan ýüklenýär...")
            path = await asyncio.to_thread(download_video, url, tmpdir)
            size_mb = os.path.getsize(path) / 1024 / 1024

            await status.edit_text(f"☁️ Google Drive-a ýüklenýär... ({size_mb:.0f} MB)")
            link = await asyncio.to_thread(drive.upload_file, path, FOLDER_NAME, MAKE_PUBLIC)

            await status.edit_text(
                f"✅ Taýýar!\n\n🎬 {os.path.basename(path)}\n📦 {size_mb:.1f} MB\n\n🔗 {link}",
                disable_web_page_preview=True,
            )
            log.info("OK %s -> %s", url, link)
        except yt_dlp.utils.DownloadError as e:
            log.warning("Download error %s: %s", url, e)
            msg = str(e)
            hint = ""
            if "Sign in" in msg or "bot" in msg:
                hint = (
                    "\n\n🔒 YouTube serweri bloklady. Çözgüt: README-däki 'cookies.txt' "
                    "bölümine serediň we cookies.txt faýlyny şu ýere iberiň."
                )
            await status.edit_text(f"❌ Wideony ýükläp bolmady.{hint}\n\n{msg[:500]}")
        except Exception as e:  # noqa: BLE001
            log.exception("Error for %s", url)
            await status.edit_text(f"❌ Ýalňyşlyk: {e}"[:1000])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


def main() -> None:
    if not TOKEN or "sizin-tokeniniz" in TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN .env faýlynda ýok. 'ytbot config' bilen goşuň.")

    app = Application.builder().token(TOKEN).concurrent_updates(True).build()
    app.add_handler(CommandHandler(["start", "help"], cmd_start))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("auth", cmd_auth))
    app.add_handler(CommandHandler("update", cmd_update))
    app.add_handler(CommandHandler("users", cmd_users))
    app.add_handler(CommandHandler("adduser", cmd_adduser))
    app.add_handler(CommandHandler("deluser", cmd_deluser))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    # "/GOCSPX-..." ýaly "/" bilen başlanan kodlar hem kabul edilsin
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"GOCSPX-|apps\.googleusercontent\.com"), handle_message
    ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("Bot işe başlady.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
