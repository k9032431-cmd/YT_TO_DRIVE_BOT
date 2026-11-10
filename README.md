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
2. Şol faýly bota iberýärsiňiz → bot size ssylka berýär → ony açyp, öz Google akkauntyňyz bilen **"Rugsat ber"** basýarsyňyz.
3. Google `token.json` berýär — bu "bu programma şu akkaunta faýl goýup biler" diýen açar. Bot ony saklaýar we her gezek ulanýar.

🔒 Bot diňe **özi goýan faýllaryny** görýär (`drive.file` rugsady). Siziň Drive-daky beýleki faýllaryňyza eli ýetmeýär.

### GitHub näme üçin?
Kod GitHub-da saklanýar. Serwer kody şu ýerden alýar. Täze funksiýa goşanymyzda (GitHub-da kod üýtgände), Telegramda bota diňe:
```
/update
```
ýazýarsyňyz — bot täze kody alýar, gerekli zatlary gurnaýar we özüni täzeden işledýär.

### Faýllar näme edýär?
| Faýl | Näme edýär |
|---|---|
| `bot.py` | Botuň esasy bölegi: hatlary alýar, wideony ýükleýär, jogap berýär |
| `drive.py` | Google Drive-a faýl ýüklemek |
| `auth_google.py` | (Ätiýaçlyk) Google rugsadyny serwerden almak |
| `install.sh` | Serwere hemme zady bir komanda bilen gurnaýar |
| `ytbot` | Serwerde boty dolandyrmak komandasy (`ytbot logs` ...) — adatça gerek däl |
| `.env.example` | Sazlamalaryň nusgasy (token, ID we ş.m.) |
| `requirements.txt` | Python kitaphanalarynyň sanawy |

---

## 📱 2-nji bölüm: TELEFONDAN gurnamak (ädimme-ädim)

Size diňe **telefon** gerek. Jemi takmynan 30 minut.

### 1-nji ädim — Telegram bot döretmek (2 minut)
1. Telegramda **@BotFather** gözläň we açyň → **Start** basyň.
2. `/newbot` ýazyp iberiň.
3. Bota at ýazyň (meselem: `Meniň YT botum`).
4. Ulanyjy adyny ýazyň — ahyry `bot` bilen gutarmaly (meselem: `menin_yt_drive_bot`).
5. BotFather uzyn **token** iberer (`7123456789:AAH...` ýaly). Üstüne basyp saklaň → ol göçürilýär. Muny soň ulanarys.

### 2-nji ädim — Serwer almak (10 minut)
Serwer — botuň 24 sagat işlejek ýeri. Islendik **VPS** bolýar (aýda ~3–6 $), meselem: Hetzner, DigitalOcean, Vultr, Contabo.
Sahypada hasap açanyňyzda şulary saýlaň:
- Operasion ulgam: **Ubuntu 24.04** (ýa-da 22.04)
- Iň arzan meýilnama ýeterlik (1 GB RAM)
- Giriş usuly: **Password** (parol) — öňden bir parol oýlap tapyň we ýazyp goýuň

Serwer döränden soň size **IP salgy** görkeziler (meselem `95.217.12.34`). Ony ýazyp goýuň.

### 3-nji ädim — Serwere telefondan birikmek
1. App Store / Play Market-den **Termius** programmasyny ýükläň (mugt).
2. Açyň → **+** → **New Host**:
   - Address / Hostname: serweriň **IP** salgysy
   - Username: `root`
   - Password: serweriň paroly
3. **Save** → hostuň üstüne basyň → (sorasa **Continue / Accept** basyň).
4. Gara ekran açylar we ahyrynda `root@...:~#` ýazylar. Bu — serweriňiz! 🎉

### 4-nji ädim — Boty gurnamak (1 komanda)
Aşakdaky setiri **doly** göçüriň, Termiusdaky gara ekrana basyp saklaň → **Paste** → telefonyň klawiaturasynda **Enter**:
```bash
curl -fsSL https://raw.githubusercontent.com/k9032431-cmd/YT_TO_DRIVE_BOT/HEAD/install.sh | sudo bash
```
Birnäçe minut ýazgylar akar. Soňra:
> 👉 @BotFather-den alan TOKENIŇIZI şu ýere goýuň we Enter basyň:

diýip sorar → 1-nji ädimde göçüren tokeniňizi **Paste** ediň → **Enter**.

Ahyrynda **✅ GURNALDY!** ýazylar. Termiusy ýapyp bilersiňiz — mundan beýläk hemme zat Telegramda.

### 5-nji ädim — Bota /start ýazmak
Telegramda öz botuňyzy açyň → **Start** basyň.
Bot: *"Siz indi bu botuň EÝESI"* diýer. (Ilkinji ýazan adam eýesi bolýar — şonuň üçin bu ädimi gijikdirmän ediň.)

### 6-njy ädim — Google Drive-y birikdirmek (10–15 minut)
Telefonyňyzda **Chrome** açyň. Google Cloud sahypasy telefonda kyn görünse, Chrome menýusy (⋮) → **Desktop site / Kompýuter wersiýasy** belläň.

1. https://console.cloud.google.com açyň, wideolar gitmeli **Google akkauntyňyz** bilen giriň. Şertleri kabul ediň.
2. Ýokarda **Select a project** → **New Project** → at: `ytbot` → **Create**. Döränden soň şol proýekti saýlaň.
3. Ýokardaky gözleg setirine **Google Drive API** ýazyň → açyň → **Enable**.
4. Gözleg setirine **OAuth consent screen** ýazyň → açyň → **Get started**:
   - App name: `ytbot`, User support email: öz emailiňiz → **Next**
   - Audience: **External** → **Next**
   - Contact email: öz emailiňiz → **Next** → razylygy belläň → **Create**
5. Çepdäki menýudan **Audience** → **Publish app** → **Confirm**.
   ⚠️ **Muny hökman ediň!** Etmeseňiz, rugsat 7 günden soň öçýär.
6. Çepdäki menýudan **Clients** → **+ Create client**:
   - Application type: **Desktop app**
   - Name: `ytbot` → **Create**
7. Açylan penjirede **Download JSON** basyň. Telefonyňyza `client_secret_....json` faýly ýüklenýär.
8. Telegramda botuňyzy açyň → **📎** → **Faýl** → ýüklenen `client_secret_....json` faýlyny saýlap iberiň.
9. Bot size **ssylka** we gysga düşündiriş iberer:
   - Ssylka basyň → akkauntyňyzy saýlaň
   - *"Google hasn't verified this app"* çyksa → **Advanced** → **Go to ytbot (unsafe)** (bu siziň öz programmaňyz, howpsuz)
   - **Continue** → **Continue / Allow**
   - Sahypa **"This site can't be reached / Sahypa açylmady"** diýer — bu **KADALY** ✅
   - Ýokardaky **salgy setirine** basyň → uzyn salgyny (`localhost/?state=...&code=...`) **doly** göçüriň
   - Telegrama gaýdyp, şol salgyny bota hat edip iberiň
10. Bot: **🎉 Google Drive birikdirildi!** diýer.

### 7-nji ädim — Ulanmak 🎬
YouTube-da islendik wideoda **Paýlaş (Share)** → **Telegram** → öz botuňyz. Ýa-da ssylkany göçürip bota iberiň.
Bot wideony Drive-yňyza goýup, ssylkasyny iberer. Wideolar Drive-da **YouTube Bot** papkasynda bolar.

---

## 🔧 3-nji bölüm: Telegramdaky komandalar

| Komanda | Näme edýär |
|---|---|
| (YouTube ssylka) | Wideony Drive-a goýýar |
| `/update` | **GitHub-dan täze kody alyp boty täzeleýär** (täze zat goşanymyzda) |
| `/status` | Bot we Drive ýagdaýy, serwerdäki boş ýer |
| `/auth` | Google Drive-y täzeden birikdirmek |
| `/adduser 12345` | Başga adama boty ulanmaga rugsat bermek (ol adam ID-ni `/id` bilen bilýär) |
| `/deluser 12345` | Rugsady aýyrmak |
| `/users` | Rugsatly adamlaryň sanawy |
| `/id` | Telegram ID-ňiz |

Bot serwer öçüp-ýansa hem **özbaşdak** işe başlaýar.

### (Goşmaça) Serwerdäki komandalar
Adatça gerek däl, ýöne Termius arkaly serwere girseňiz:

| Komanda | Näme edýär |
|---|---|
| `ytbot logs` | Bot näme edýär — göni görmek (çykmak: Ctrl+C) |
| `ytbot status` | Bot işleýärmi? |
| `ytbot restart` | Täzeden işletmek |
| `ytbot update` | Täzelemek (`/update` bilen birmeňzeş) |
| `ytbot config` | Sazlamalar: papka ady, hil (`MAX_HEIGHT`), açyk ssylka (`MAKE_PUBLIC`) |

---

## ❓ 4-nji bölüm: Problemalar

**"Sign in to confirm you're not a bot"** — YouTube käbir serwer IP-lerini bloklaýar. Çözgüt — `cookies.txt` faýlyny bota ibermek:
- **Android**: Play Market-den **Kiwi Browser** (ýa-da giňeltme goldaýan başga brauzer) guruň → oňa **"Get cookies.txt LOCALLY"** giňeltmesini goşuň → youtube.com açyp akkauntyňyza giriň → giňeltmäni basyň → **Export** → ýüklenen `.txt` faýlyny bota iberiň.
- **Kompýuter** tapyp bilseňiz: Chrome-a şol giňeltmäni goşuň, şol bir zady ediň, faýly Telegram arkaly bota iberiň.
- Ýa-da başga serwer berijisini synanyşyň (käbir IP-ler bloklanmaýar).

**Wideolar birden ýüklenmesini bes etdi** — YouTube köplenç üýtgeýär. Bota `/update` ýazyň (yt-dlp hem täzelenýär).

**"Google rugsady köne"** — bota `/auth` ýazyň. 7 günden soň gaýtalanýan bolsa, 6-njy ädimdäki **Publish app**-y unutduňyz.

**Bot jogap berenok** — Termius bilen serwere giriň → `ytbot logs` ýazyň → ýalňyşlygyň suratyny alyň.

**Kimdir biri meniň öňümden /start ýazdy** — Termius bilen serwere giriň → `rm /opt/ytbot/users.txt && ytbot restart` → derrew öz botuňyza `/start` ýazyň.

**Termiusda "Paste" çykmaýar** — gara ekrana uzak basyp saklaň; ýa-da klawiaturanyň ýokarsyndaky goşmaça düwmelerden peýdalanyň.

**Google Drive doldy** — mugt Drive 15 GB. Köne wideolary pozuň ýa-da `MAX_HEIGHT=720` goýuň.

---

## 🔐 Howpsuzlyk
- `.env`, `credentials.json`, `token.json`, `cookies.txt`, `users.txt` — **gizlin** faýllar. Olar GitHub-a hiç haçan goýulmaýar (`.gitignore`-da bar). Hiç kime ibermäň.
- Bot diňe size (eýesine) we siz `/adduser` bilen goşan adamlara işleýär — başgalar siziň Drive-yňyzy dolduryp bilmez.
