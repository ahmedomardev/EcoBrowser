# EcoBrowser

EcoBrowser is a desktop web browser built with Python, PyQt6, and Qt WebEngine (Chromium). It focuses on everyday usability with privacy tools, content filtering, and a built-in password manager.

**Version:** 1.9

## What's New in 1.9

- **Cleaner 3-dot menu:** Removed old Search Engine selector from the menu - engine switching is now handled directly in the New Tab page dropdown (less clutter)
- **12-hour clock:** New Tab time now shows `2:05 PM` format with AM/PM instead of 24h, updates every second
- **Fixed favicon CORS:** Quicklinks no longer spam `blocked by CORS policy` - switched from Google S2 (`google.com/s2/favicons`) to DuckDuckGo icon service (`icons.duckduckgo.com/ip3/`) which sends proper CORS headers
- **Adult content blocker fixed & enhanced:** Fixed crash `name 'is_adult_host' is not defined` / `is_adult_keyword` / `time` / `EcoBrowser`. Now blocks 3 ways:
  1. Adult domains (pornhub, xvideos, xnxx, etc.)
  2. URL keywords (porn, xxx, hentai, onlyfans, etc. - 50+ terms)
  3. **Page text content** - new `ADULT_PAGE_BLOCKER_JS` scans page text and replaces page with SafeShield block screen if explicit words are found
- **Stability:** Robust `sip` handling for PyQt6, `cryptography` import silenced with `type: ignore`, fixed `EcoBrowser` -> `EcoBrowserWindow` alias

## Features

- **Tabbed browsing:** Open and manage multiple pages with titles, site icons, and close controls
- **Search and address bar:** Use Google, DuckDuckGo, Bing, Ecosia, Brave Search, or Yahoo from the same field. Engine is selected from New Tab page dropdown
- **New Tab page:** 12hr clock with AM/PM, date, search box, quicklinks with auto favicons (CORS-fixed), wallpaper customizer with presets and upload
- **Bookmarks and history:** Save pages to the bookmarks bar and review your browsing history
- **Downloads:** Track active downloads and manage saved files
- **Privacy and content filters:** 
  - Block ad, tracker, and adult-content domains via `QWebEngineUrlRequestInterceptor`
  - SafeShield: Blocks navigation to adult domains + any URL containing adult keywords + any page containing explicit keywords in its text
  - Allowlist support (`wikipedia.org`, `youtube.com`, etc. bypass text scan)
- **Media safeguards:** HaramBlur - heuristic blur for explicit images/videos (32px), AI-generated media watermark `[✦ AI GENERATED]`, YouTube porn-bot avatar shield
- **Appearance:** Dark and light mode with custom accent colors (Classic Blue, Arc Violet, Cyber Emerald, etc.)
- **Secure DNS:** DNS over HTTPS support with configurable resolvers including Cloudflare Family (`family.cloudflare-dns.com`)
- **Browser-only proxy:** Route only EcoBrowser traffic through SOCKS5 or HTTP proxy (DPAPI encrypted on Windows)
- **Password Manager:** Detect login forms, save credentials securely, and autofill on return
- **Cookie controls:** Clear browser cookies anytime
- **Windows integration:** Handles http/https links and HTML files, registers as default browser (protected flag)

## Password Manager

EcoBrowser includes a local password manager that works directly in the browser.

### What it does

It automatically detects login forms that contain `input[type="password"]` and `input[type="email"]` or username fields. When you log in, it offers to save the credentials. Next time you visit that site, it fills them in for you.

### Detection

The browser runs a lightweight detector on every page that looks for:

- Email fields: `input[type="email"]`, `input[autocomplete="email"]`, `input[autocomplete="username"]`, `input[name*="email"]`, `input[id*="email"]`, `input[name*="user"]`, `input[name*="login"]`
- Password fields: `input[type="password"]`

It works with modern frameworks like React, Vue, and sites that load forms dynamically using MutationObserver. It listens for form submits, login button clicks, Enter in the password field, and focus changes.

### Saving and Autofill

1. Enter your email/username and password on any login page
2. Click Login or Sign In
3. EcoBrowser asks if you want to save the password for that site
4. On your next visit, the fields are filled automatically with a small badge showing it was autofilled

The detection triggers proper input events so React and similar sites accept the autofilled values.

### Security and Storage

- All passwords are stored locally only, never sent to a server
- Files are stored in the EcoBrowser app data folder: `passwords.json` and `.pm_key`
  - Windows: `%APPDATA%\EcoBrowser\`
  - Other systems: `~/EcoBrowser/` or `~/.config/EcoBrowser/`
- If the `cryptography` package is installed, passwords use Fernet AES encryption
- Without it, it falls back to local key obfuscation with Base64
- No plain text passwords are ever written to disk

Enable strong encryption:

```bash
pip install cryptography
```

### Manager UI

- **Toolbar button:** Key icon that turns blue when the current site has a saved login
- **Menu:** EcoBrowser Menu → Password Manager
- Inside the manager you can search by site or email, show or hide passwords, copy email or password, delete entries, clear all, and export to JSON

Keep `passwords.json` and `.pm_key` private. If you delete the key file, saved passwords cannot be decrypted.

## Keyboard Shortcuts

| Shortcut       | Action             |
| -------------- | ------------------ |
| `Ctrl+T`       | Open a new tab     |
| `Ctrl+J`       | Open Downloads     |
| `Ctrl+H`       | Open History       |
| `Ctrl+Shift+R` | Toggle Reader Mode |

## Search Engines

Google, DuckDuckGo, Bing, Ecosia, Brave Search, and Yahoo are built in. In 1.9 you change the active engine from the New Tab page dropdown (click the G/B/D icon), not from the 3-dot menu.

## Installation

### Download from Uptodown

Get the latest Windows build here:

**https://ecobrowser.en.uptodown.com/windows**

### Run from source

Install the required packages:

```bash
python -m pip install PyQt6 PyQt6-WebEngine
# Recommended for password encryption:
python -m pip install cryptography
```

Then start the browser:

```bash
python main.py
```

If you get Pylance warnings about `sip` or `cryptography.fernet` - they are silenced in 1.9 with `type: ignore` and robust fallbacks.

## Local Data

EcoBrowser keeps everything locally in its app data folder:

- `settings.json` for preferences
- JSON files for bookmarks, history, and downloads
- `passwords.json` and `.pm_key` for the password manager
- Proxy credentials are encrypted with Windows DPAPI on Windows

## Technology

- **Language:** Python
- **UI:** PyQt6
- **Engine:** Qt WebEngine / Chromium
- **Graphics:** SVG icons
- **Storage:** Local JSON
- **Password encryption:** Fernet AES when available, otherwise local obfuscation
- **Content blocking:** `ContentBlocker` interceptor + `AI_SAFEGUARD_SCRIPT` + `ADULT_PAGE_BLOCKER_JS` (new in 1.9)

## Download

- **Uptodown (Windows):** [EcoBrowser for Windows - Download from Uptodown](https://ecobrowser.en.uptodown.com/windows)

## Project

- **Repository:** [ahmedomardev/EcoBrowser](https://github.com/ahmedomardev/EcoBrowser)
- **Uptodown Page:** [ecobrowser.en.uptodown.com](https://ecobrowser.en.uptodown.com/windows)
- **Version:** 1.9
