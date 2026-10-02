# EcoBrowser

EcoBrowser is a desktop web browser built with Python, PyQt6, and Qt WebEngine
(Chromium). It combines everyday browsing tools with configurable content
filters, secure DNS, and browser-only proxy routing.

## Features

- **Tabbed browsing:** Open and manage multiple pages, with page titles, site
  icons, and close controls.
- **Search and address bar:** Choose Google, DuckDuckGo, Bing, Ecosia, Brave
  Search, or Yahoo. Enter a URL or a search query in the same field.
- **Bookmarks and history:** Save pages to the bookmarks bar, review browsing
  history, and clear history from the History window.
- **Downloads:** Track active downloads, review recent downloads, and manage
  saved files from the Downloads window.
- **Privacy and content filters:** Block requests to configured ad, tracker,
  and adult-content domains.
- **Media safeguards:** Apply heuristic filters to images and videos, including
  explicit-media blur, AI-generated media labels, and AI-slop indicators.
  These detections are best-effort and may produce incorrect results.
- **Appearance options:** Use dark or light mode and choose a built-in or custom
  accent color.
- **HTTPS indicator:** Show the connection scheme in the address bar.
- **Windows integration:** Register EcoBrowser as a handler for web links and
  HTML files, and accept URLs opened by other applications.
- **Cookie controls:** Clear browser cookies from the main menu.

## What's New in v1.6

### Secure DNS

- Configure DNS over HTTPS from the Network settings window.
- **Cloudflare Family** is the default resolver.
- Select another built-in resolver or enter a custom HTTPS resolver URL.
- When secure DNS is enabled, EcoBrowser does not silently fall back to
  unencrypted DNS if the resolver cannot be reached.

### Browser-only proxy settings

- Route EcoBrowser traffic through a user-provided **SOCKS5** or **HTTP**
  proxy. This changes only EcoBrowser's traffic; it is not a device-wide VPN.
- Configure the proxy type, host, and port in Network settings.
- HTTP proxies can use a username and password. On Windows, saved credentials
  are encrypted with Windows DPAPI and tied to the current Windows account.
- Chromium does not support username/password authentication for SOCKS5
  proxies. Use an authenticated HTTP proxy if your provider requires a login.
- Use a trusted proxy endpoint. Some HTTP proxy authentication methods can
  expose credentials between your computer and the proxy.
- Restart EcoBrowser after saving network settings.

## Keyboard Shortcuts

| Shortcut | Action         |
| -------- | -------------- |
| `Ctrl+T` | Open a new tab |
| `Ctrl+J` | Open Downloads |
| `Ctrl+H` | Open History   |

## Search Engines

The built-in search engines are Google, DuckDuckGo, Bing, Ecosia, Brave Search,
and Yahoo. Select the active engine from **EcoBrowser Menu → Search Engine**.

## Installation

### Windows installer

Download the latest available installer from
[EcoBrowser GitHub Releases](https://github.com/ahmedomardev/EcoBrowser/releases).

### Run from source

Install Python and the required Qt packages:

```bash
python -m pip install PyQt6 PyQt6-WebEngine
```

Then start the browser from the project directory:

```bash
python ecobrowser.py
```

## Local Data and Credentials

EcoBrowser stores settings and browser data locally in its application data
folder. Proxy usernames and passwords are encrypted with Windows DPAPI rather
than written as plain text. They can only be decrypted by the same Windows
account on that computer; re-enter them if you move the settings to another
account or device.

Saving authenticated proxy credentials is currently supported on Windows.

## Technology

- **Language:** Python
- **Desktop UI:** PyQt6
- **Browser engine:** Qt WebEngine / Chromium
- **Windows integration and credential protection:** Windows Registry and
  Windows DPAPI
- **UI graphics:** SVG icons
- **Local storage:** JSON settings and browser data

## Project

- **Repository:** [ahmedomardev/EcoBrowser](https://github.com/ahmedomardev/EcoBrowser)
