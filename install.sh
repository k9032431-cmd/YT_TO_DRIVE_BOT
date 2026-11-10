#!/usr/bin/env bash
# =====================================================================
#  YT -> Google Drive bot: serwere bir komanda bilen gurnamak
#  Ulanylyşy (Ubuntu/Debian serwerde, root hökmünde):
#    curl -fsSL https://raw.githubusercontent.com/k9032431-cmd/YT_TO_DRIVE_BOT/HEAD/install.sh | sudo bash
# =====================================================================
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/k9032431-cmd/YT_TO_DRIVE_BOT.git}"
APP_DIR="/opt/ytbot"
APP_USER="ytbot"

if [ "$(id -u)" -ne 0 ]; then
  echo "Bu skripti root bilen işlediň:  sudo bash install.sh"; exit 1
fi

echo ">>> 1/5  Gerekli programmalar gurnalýar (git, python, ffmpeg)..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git python3 python3-venv python3-pip ffmpeg nano ca-certificates >/dev/null

echo ">>> 2/5  Kod GitHub-dan alynýar..."
if [ -d "$APP_DIR/.git" ]; then
  echo "    Eýýäm gurlupdyr — täzelenýär."
else
  git clone "$REPO_URL" "$APP_DIR"
fi

echo ">>> 3/5  Bot üçin aýratyn ulanyjy döredilýär..."
id "$APP_USER" &>/dev/null || useradd --system --home-dir "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

echo ">>> 4/5  Python kitaphanalary gurnalýar..."
runuser -u "$APP_USER" -- git -C "$APP_DIR" pull --ff-only || true
runuser -u "$APP_USER" -- python3 -m venv "$APP_DIR/venv"
runuser -u "$APP_USER" -- "$APP_DIR/venv/bin/pip" install -q --upgrade pip
runuser -u "$APP_USER" -- "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
  chmod 600 "$APP_DIR/.env"
fi

# --- Telegram tokenini soramak (telefondan hem aňsat bolar ýaly) ---
if grep -q "sizin-tokeniniz" "$APP_DIR/.env"; then
  TOKEN="${BOT_TOKEN:-}"
  while [ -z "$TOKEN" ]; do
    echo
    echo "👉 @BotFather-den alan TOKENIŇIZI şu ýere goýuň we Enter basyň:"
    read -r TOKEN < /dev/tty || true
    TOKEN="$(echo "$TOKEN" | tr -d '[:space:]')"
    if ! echo "$TOKEN" | grep -Eq '^[0-9]+:[A-Za-z0-9_-]{30,}$'; then
      echo "❌ Bu token däl ýaly (mysal: 123456789:AAH...). Täzeden synanyşyň."; TOKEN=""
    fi
  done
  sed -i "s|^TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$TOKEN|" "$APP_DIR/.env"
fi

echo ">>> 5/5  Awtomatik işleýän hyzmat (systemd) we 'ytbot' komandasy goşulýar..."
cat > /etc/systemd/system/ytbot.service <<UNIT
[Unit]
Description=YouTube -> Google Drive Telegram bot
After=network-online.target
Wants=network-online.target

[Service]
User=$APP_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
install -m 755 "$APP_DIR/ytbot" /usr/local/bin/ytbot
systemctl daemon-reload
systemctl enable ytbot >/dev/null 2>&1
systemctl restart ytbot

cat <<'MSG'

=====================================================================
 ✅ GURNALDY! Bot işleýär.

 Indi Telegrama geçiň, botuňyzy açyň we  /start  ýazyň.
 Galan ähli zady bot özi düşündirer. Serwere gaýdyp girmek gerek däl.

 Täzelemek: Telegramda botuňyza  /update  ýazyň.
=====================================================================
MSG
