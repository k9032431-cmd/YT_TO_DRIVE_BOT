# 🎬 YouTube → Google Drive Telegram boty

Bota YouTube ssylkasyny iberýärsiňiz → bot wideony ýükleýär → **siziň** Google Drive-yňyza goýýar → size Drive ssylkasyny iberýär.

---

## 📖 1-nji bölüm: Bu zatlar nähili işleýär? (programmirlemesiz düşündiriş)

### Telegram boty näme?
Telegram boty — bu adam däl-de, **programma** tarapyndan dolandyrylýan Telegram akkaunty.
Siz bota hat ýazanyňyzda, Telegram şol haty **siziň programmaňyza** berýär, programma bolsa jogap ýazýar.

Programma bilen Telegramyň arasyndaky "açar" — bu **token** (`123456:AAAbbb...` ýaly uzyn söz).
Ony **@BotFather** atly resmi Telegram botundan alýarsyňyz. Token kimde bolsa, bot şonuň elinde — **hiç kime görkezmäň!**

### Näme üçin serwer gerek?
Programma hemişe bir ýerde **işläp durmaly** — bot hatyňyzy garaşýar. Eger kompýuteriňizde işletseňiz, kompýuter öçende bot hem öçer.
Şonuň üçin **serwer** (VPS) ulanýarys — bu internetde 24/7 açyk duran kiçijik kompýuter. Aýda ~3–6 $ (Hetzner, DigitalOcean, Contabo, Vultr we ş.m.) ýa-da mugt (Oracle Cloud Free Tier).

Ähli zat şeýle işleýär:

```
 Siz (Telegram)          Telegram serwerleri          Siziň serweriňiz (VPS)             Google Drive
 ─────────────           ───────────────────          ──────────────────────            ────────────
  YouTube ssylka  ───►   haty saklaýar   ◄── "täze hat barmy?" ── bot.py
                                          ───  ssylka  ───►      │
                                                                 ├─ yt-dlp: YouTube-dan wideony ýükleýär
                                                                 ├─ drive.py: wideony Drive-a iberýär ──►  📁 "YouTube Bot"
                                                                 │                          ◄── ssylka ──
  Drive ssylkasy  ◄───────────────────────────────────────────── jogap iberýär
```

Bot Telegrama yzygiderli "maňa täze hat barmy?" diýip soraýar (*polling*). Şonuň üçin serwere hiç hili domen, IP sazlamasy gerek däl.

### Google Drive nähili baglanyşýar?
Bot siziň Drive-yňyza faýl goýmak üçin **rugsat** almaly. Bu şeýle bolýar:
1. **Google Cloud**-da kiçijik "programma" döredýärsiňiz (mugt) → `credentials.json` faýly berilýär. Bu "men şu programma" diýen şahadatnama.
2. `ytbot auth` komandasy size ssylka berýär → ony açyp, öz Google akkauntyňyz bilen **"Rugsat ber"** basýarsyňyz.
3. Google `token.json` berýär — bu "bu programma şu akkaunta faýl goýup biler" diýen açar. Bot ony saklaýar we her gezek ulanýar.

🔒 Bot diňe **özi goýan faýllaryny** görýär (`drive.file` rugsady). Siziň Drive-daky beýleki faýllaryňyza eli ýetmeýär.

### GitHub näme üçin?
Kod GitHub-da saklanýar. Serwer kody şu ýerden alýar. Täze funksiýa goşanymyzda (GitHub-da kod üýtgände), serwerde diňe:
```bash
ytbot update
```
ýazýarsyňyz — serwer täze kody alýar, gerekli zatlary gurnaýar we boty täzeden işledýär.

### Faýllar näme edýär?
| Faýl | Näme edýär |
|---|---|
| `bot.py` | Botuň esasy bölegi: hatlary alýar, wideony ýükleýär, jogap berýär |
| `drive.py` | Google Drive-a faýl ýüklemek |
| `auth_google.py` | Google akkauntyna bir gezeklik rugsat almak |
| `install.sh` | Serwere hemme zady bir komanda bilen gurnaýar |
| `ytbot` | Boty dolandyrmak komandasy (`ytbot update`, `ytbot logs` ...) |
| `.env.example` | Sazlamalaryň nusgasy (token, ID we ş.m.) |
| `requirements.txt` | Python kitaphanalarynyň sanawy |

---

## 🚀 2-nji bölüm: Gurnamak (ädimme-ädim)

### 1-nji ädim — Telegram bot döretmek (2 minut)
1. Telegramda **@BotFather** tapyň → `/newbot` ýazyň.
2. Bota at beriň (meselem `Meniň YT botum`), soň ulanyjy adyny beriň (`_bot` bilen gutarmaly, meselem `menin_yt_drive_bot`).
3. BotFather size **token** berer — bir ýere ýazyp goýuň.

### 2-nji ädim — Google Cloud-da rugsat faýlyny almak (10 minut)
1. https://console.cloud.google.com açyň, Google akkauntyňyz bilen giriň (wideolar şu akkauntyň Drive-yna gider).
2. Ýokarda **Select a project → New Project** → at beriň (`ytbot`) → **Create**.
3. Gözleg setirinde **"Google Drive API"** ýazyň → açyň → **Enable**.
4. Çep menýu: **APIs & Services → OAuth consent screen** (ýa-da **Google Auth Platform**):
   - **Get started** → App name: `ytbot`, email: öz emailiňiz → Audience: **External** → dowam ediň → **Create**.
   - **Audience** bölüminde **"Publish app"** basyň (statusy *In production* bolmaly).
     ⚠️ Muny etmeseňiz, rugsat **7 günden soň** öçýär we bot işlemesini bes eder!
5. **Clients** (ýa-da **Credentials → Create credentials → OAuth client ID**):
   - Application type: **Desktop app** → **Create**.
   - **Download JSON** basyň. Bu faýl — siziň `credentials.json`-yňyz.

### 3-nji ädim — Serwer almak
Islendik VPS: **Ubuntu 22.04 ýa-da 24.04**, 1 GB RAM, 20+ GB disk ýeterlik.
Serwer berijisi size **IP salgy** we **parol** berer.

Serwere birikmek:
- **Windows**: `PowerShell` açyň → `ssh root@SERWERIŇ_IP` ýazyň → paroly ýazyň (ýazanyňyzda görünmeýär — bu kadaly).
- **Telefon**: *Termius* programmasy.

### 4-nji ädim — Boty gurnamak (1 komanda)
Serwere girenden soň şuny göçürip goýuň we Enter basyň:
```bash
curl -fsSL https://raw.githubusercontent.com/k9032431-cmd/YT_TO_DRIVE_BOT/HEAD/install.sh | sudo bash
```
> Eger repo **private** (ýapyk) bolsa, ilki repony public ediň, ýa-da GitHub tokeni bilen:
> `git clone https://TOKEN@github.com/k9032431-cmd/YT_TO_DRIVE_BOT.git /opt/ytbot && sudo bash /opt/ytbot/install.sh`

### 5-nji ädim — Sazlamak
```bash
ytbot config
```
Açylan faýlda `TELEGRAM_BOT_TOKEN=` setirine BotFather-iň beren tokenini ýazyň.
`ALLOWED_USERS=` — siziň Telegram ID-ňiz (bilmeýän bolsaňyz, häzirlikçe goýuň; boty işledeniňizden soň bota `/id` ýazyň we soň täzeden `ytbot config` bilen goşuň).
Saklamak: **Ctrl+O**, **Enter**, çykmak: **Ctrl+X**.

```bash
ytbot credentials
```
Kompýuteriňizde `credentials.json`-y Notepad bilen açyň, hemme ýazgyny göçüriň, serwerdäki açylan penjirä goýuň (sag düwme ýa-da Ctrl+Shift+V). Ctrl+O, Enter, Ctrl+X.

```bash
ytbot auth
```
Görkezilen ssylkany brauzerde açyň → akkauntyňyzy saýlaň →
*"Google hasn't verified this app"* çyksa: **Advanced → Go to ytbot (unsafe)** (bu siziň öz programmaňyz, howpsuz) → **Continue / Allow**.
Soňunda sahypa **"This site can't be reached"** diýer — bu kadaly! Brauzeriň salgy setirindäki uzyn salgyny (`http://localhost/?state=...&code=...`) **doly** göçürip, serwere goýuň we Enter basyň.

### 6-njy ädim — Barlamak
```bash
ytbot status    # "active (running)" ýazylan bolmaly
```
Telegramda botuňyza `/start` ýazyň, soň islendik YouTube ssylkasyny iberiň. 🎉

---

## 🔧 3-nji bölüm: Gündelik ulanyş

| Komanda | Näme edýär |
|---|---|
| `ytbot update` | **GitHub-dan täze kody alyp boty täzeleýär** |
| `ytbot logs` | Bot näme edýär — göni görmek (çykmak: Ctrl+C) |
| `ytbot status` | Bot işleýärmi? |
| `ytbot restart` | Täzeden işletmek |
| `ytbot config` | Sazlamalary üýtgetmek |
| `ytbot stop` / `ytbot start` | Duruzmak / işletmek |

Bot serwer täzeden ýüklense hem **özbaşdak** işe başlaýar.

### Sazlamalar (`ytbot config`)
| Sazlama | Düşündiriş |
|---|---|
| `ALLOWED_USERS` | Boty ulanyp biljek ID-ler, otur bilen: `111,222` |
| `DRIVE_FOLDER_NAME` | Drive-daky papkanyň ady |
| `MAKE_PUBLIC` | `true` — ssylkasy bolan her kim görüp biler; `false` — diňe siz |
| `MAX_HEIGHT` | Iň ýokary hil: `720`, `1080`, `2160` ... |

---

## ❓ 4-nji bölüm: Problemalar

**"Sign in to confirm you're not a bot"** — YouTube käbir serwer IP-lerini bloklaýar. Çözgüt:
1. Kompýuteriňizde Chrome/Firefox-a **"Get cookies.txt LOCALLY"** giňeltmesini guruň.
2. youtube.com açyň (akkauntyňyza giriň) → giňeltmäni basyň → **Export**.
3. Serwerde `ytbot cookies` → faýlyň mazmunyny goýuň → saklaň.

**Wideolar birden ýüklenmesini bes etdi** — YouTube köplenç üýtgeýär. `ytbot update` yt-dlp-ni hem täzeleýär, ilki şony synanyşyň.

**"token.json tapylmady" / "Google rugsady köne"** — `ytbot auth` täzeden işlediň. 7 günden soň gaýtalanýan bolsa, 2-nji ädimdäki **Publish app**-y unutduňyz.

**Bot jogap berenok** — `ytbot logs` ýazyň we ýalňyşlygy okaň.

**Google Drive doldy** — mugt Drive 15 GB. Köne wideolary pozuň ýa-da `MAX_HEIGHT=720` goýuň.

---

## 🔐 Howpsuzlyk
- `.env`, `credentials.json`, `token.json`, `cookies.txt` — **gizlin** faýllar. Olar GitHub-a hiç haçan goýulmaýar (`.gitignore`-da bar). Hiç kime ibermäň.
- Bot diňe `ALLOWED_USERS`-däki adamlara işleýär — başgalar siziň Drive-yňyzy dolduryp bilmez.
