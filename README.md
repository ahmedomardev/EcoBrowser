# EcoBrowser

EcoBrowser is a desktop web browser built with Python, PyQt6, and Qt WebEngine (Chromium). It focuses on everyday usability with privacy tools, content filtering, and a built-in password manager.

## Features

- **Tabbed browsing:** Open and manage multiple pages with titles, site icons, and close controls
- **Search and address bar:** Use Google, DuckDuckGo, Bing, Ecosia, Brave Search, or Yahoo from the same field
- **Bookmarks and history:** Save pages to the bookmarks bar and review your browsing history
- **Downloads:** Track active downloads and manage saved files
- **Privacy and content filters:** Block ad, tracker, and adult-content domains
- **Media safeguards:** Heuristic filtering for explicit-media blur and AI-generated media labels
- **Appearance:** Dark and light mode with custom accent colors
- **Secure DNS:** DNS over HTTPS support with configurable resolvers including Cloudflare Family
- **Browser-only proxy:** Route only EcoBrowser traffic through SOCKS5 or HTTP proxy
- **Password Manager:** Detect login forms, save credentials securely, and autofill on return
- **Cookie controls:** Clear browser cookies anytime
- **Windows integration:** Handles http/https links and HTML files

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

Google, DuckDuckGo, Bing, Ecosia, Brave Search, and Yahoo are built in. You can change the active engine from EcoBrowser Menu → Search Engine.

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

## Download

- **Uptodown (Windows):** [EcoBrowser for Windows - Download from Uptodown](https://ecobrowser.en.uptodown.com/windows)

## Project

- **Repository:** [ahmedomardev/EcoBrowser](https://github.com/ahmedomardev/EcoBrowser)
- **Uptodown Page:** [ecobrowser.en.uptodown.com](https://ecobrowser.en.uptodown.com/windows)
- **Version:** 1.8

# EcoBrowser

EcoBrowser is a desktop web browser built with Python, PyQt6, and Qt WebEngine (Chromium). It focuses on everyday usability with privacy tools, content filtering, and a built-in password manager.

## Features

- **Tabbed browsing:** Open and manage multiple pages with titles, site icons, and close controls
- **Search and address bar:** Use Google, DuckDuckGo, Bing, Ecosia, Brave Search, or Yahoo from the same field
- **Bookmarks and history:** Save pages to the bookmarks bar and review your browsing history
- **Downloads:** Track active downloads and manage saved files
- **Privacy and content filters:** Block ad, tracker, and adult-content domains
- **Media safeguards:** Heuristic filtering for explicit-media blur and AI-generated media labels
- **Appearance:** Dark and light mode with custom accent colors
- **Secure DNS:** DNS over HTTPS support with configurable resolvers including Cloudflare Family
- **Browser-only proxy:** Route only EcoBrowser traffic through SOCKS5 or HTTP proxy
- **Password Manager:** Detect login forms, save credentials securely, and autofill on return
- **Cookie controls:** Clear browser cookies anytime
- **Windows integration:** Handles http/https links and HTML files

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

Google, DuckDuckGo, Bing, Ecosia, Brave Search, and Yahoo are built in. You can change the active engine from EcoBrowser Menu → Search Engine.

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

## Download

- **Uptodown (Windows):** [EcoBrowser for Windows - Download from Uptodown](https://ecobrowser.en.uptodown.com/windows)

## Project

- **Repository:** [ahmedomardev/EcoBrowser](https://github.com/ahmedomardev/EcoBrowser)
- **Uptodown Page:** [ecobrowser.en.uptodown.com](https://ecobrowser.en.uptodown.com/windows)
- **Version:** 1.8
