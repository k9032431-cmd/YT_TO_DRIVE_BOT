"""Telegram bot: YouTube ssylkasyny alýar -> wideony ýükleýär -> Google Drive-a goýýar
-> Drive ssylkasyny yzyna iberýär."""

import asyncio
import logging
import os
import re
import shutil
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
ALLOWED_USERS = {
    int(x) for x in os.getenv("ALLOWED_USERS", "").replace(" ", "").split(",") if x
}
FOLDER_NAME = os.getenv("DRIVE_FOLDER_NAME", "YouTube Bot")
MAKE_PUBLIC = os.getenv("MAKE_PUBLIC", "true").lower() in ("1", "true", "yes", "hawa")
MAX_HEIGHT = int(os.getenv("MAX_HEIGHT", "1080"))
COOKIES_FILE = BASE_DIR / os.getenv("COOKIES_FILE", "cookies.txt")

YOUTUBE_RE = re.compile(
    r"(https?://)?(www\.|m\.|music\.)?(youtube\.com|youtu\.be)/\S+", re.IGNORECASE
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("ytbot")

# Serweriň diski dolmaz ýaly, bir wagtda diňe 1 wideo işlenýär (beýlekiler nobata durýar).
work_lock = asyncio.Semaphore(1)


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
        "restrictfilenames": False,
    }
    if COOKIES_FILE.is_file():
        opts["cookiefile"] = str(COOKIES_FILE)

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)
    # birleşdirilenden soň giňeltme .mp4 bolup biler
    mp4 = os.path.splitext(path)[0] + ".mp4"
    return mp4 if os.path.exists(mp4) else path


def is_allowed(update: Update) -> bool:
    return update.effective_user is not None and update.effective_user.id in ALLOWED_USERS


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if not is_allowed(update):
        await update.message.reply_text(
            f"Salam! Siziň ID-ňiz: {uid}\n"
            "Bu bot ýapyk. Eýesi bu ID-ni .env faýlyndaky ALLOWED_USERS-e goşmaly."
        )
        return
    await update.message.reply_text(
        "Salam! 👋\nMaňa YouTube ssylkasyny iberiň — men wideony Google Drive-yňyza "
        "goýup, ssylkasyny size iberaýin.\n\n/id — ID-ňizi görkezýär"
    )


async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Siziň Telegram ID-ňiz: `{update.effective_user.id}`",
        parse_mode=ParseMode.MARKDOWN,
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await update.message.reply_text(
            f"⛔ Rugsat ýok. Siziň ID-ňiz: {update.effective_user.id}"
        )
        return

    match = YOUTUBE_RE.search(update.message.text or "")
    if not match:
        await update.message.reply_text("Bu YouTube ssylkasyna meňzänok 🤔")
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
            link = await asyncio.to_thread(
                drive.upload_file, path, FOLDER_NAME, MAKE_PUBLIC
            )

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
                hint = "\n\nYouTube serweri bloklady. README-däki 'cookies.txt' bölümine serediň."
            await status.edit_text(f"❌ Wideony ýükläp bolmady.{hint}\n\n{msg[:500]}")
        except Exception as e:  # noqa: BLE001
            log.exception("Error for %s", url)
            await status.edit_text(f"❌ Ýalňyşlyk: {e}"[:1000])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


def main() -> None:
    if not TOKEN or "sizin-tokeniniz" in TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN .env faýlynda ýok. 'ytbot config' bilen goşuň.")
    if not ALLOWED_USERS:
        log.warning("ALLOWED_USERS boş — bot hiç kime işlemez (diňe /id görkezer).")

    app = Application.builder().token(TOKEN).concurrent_updates(True).build()
    app.add_handler(CommandHandler(["start", "help"], cmd_start))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("Bot işe başlady.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
