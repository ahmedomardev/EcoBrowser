# EcoBrowser

**EcoBrowser** (`ahmedomardev/EcoBrowser`) is a fast, modern web browser built using Python and `PyQt6-WebEngine`. It features a clean, responsive interface, native Windows integration, privacy/content filtering, customizable themes, and an optimized architecture designed for everyday browsing.

## Features

- **Lightweight Web Engine:** Uses `PyQt6-WebEngine` for modern website rendering and compatibility.
- **Optimized RAM Usage:** Lightweight architecture designed for a responsive browsing experience.
- **Modern Tabbed Interface:** Multi-tab browsing with improved tab styling, dynamic titles, website icons, close controls, and `Ctrl+T` new-tab support.
- **Modern SVG UI:** High-resolution SVG icons are used throughout the browser for a cleaner, scalable interface.
- **Multiple Search Engines:** Built-in support for **Google, DuckDuckGo, Bing, Ecosia, Brave Search, and Yahoo**, with selectable default search engine.
- **Smart Address Bar:** Automatically distinguishes URLs from search queries and supports `http://`, `https://`, `eco://`, and `about:` addresses.
- **Windows Default Browser Integration:** Registers EcoBrowser with Windows so it can appear as a browser capable of handling `http`/`https` links and HTML files.
- **External URL / Command-Line Handling:** Accepts URL arguments when launched by external applications.
- **Security Indicator:** Displays HTTPS lock/unlock status directly in the address bar.
- **Browsing History:** Automatically records visited web locations and provides a dedicated History window with a clear-history option (`Ctrl+H`).
- **Bookmarks:** Save pages with the address-bar bookmark button and access them from a dynamic bookmarks bar.
- **Downloads Manager:** Supports file downloads with a save-location dialog, live progress tracking, download history, a quick downloads popup, and a full downloads manager (`Ctrl+J`).
- **Ad & Tracker Blocking:** Intercepts requests to common advertising, analytics, and tracking domains.
- **Adult/Explicit Content Protection:** Blocks configured adult domains and URL keywords at the network/navigation level.
- **NSFW Media Blurring:** Detects explicit image/video content using client-side heuristics, blurs it automatically, and provides click-to-reveal controls.
- **Automatic Video Muting:** Explicit video content can be automatically muted and paused until revealed.
- **AI-Generated Media Detection:** Detects common AI-generation signatures and places an **AI GENERATED** watermark over detected media.
- **AI Slop / Brainrot Filter:** Detects configured synthetic-content indicators such as mutant anatomy, repetitive AI spam, and other AI-slop patterns, with optional automatic blurring and click-to-reveal.
- **Blockers & Filters Manager:** Central interface for enabling/disabling ad blocking, explicit-content protection, AI-generated media marking, AI-slop detection, and AI-slop blurring.
- **Dark Mode:** Global dark mode with matching browser UI and Chromium web-engine dark-mode support.
- **Custom Accent Colors:** Choose from built-in accent presets or select a custom color for active tabs, highlights, and download progress indicators.
- **Persistent Settings:** Browser preferences such as the selected search engine and custom accent color are stored locally.
- **Cookie Management:** Clear browser cookies directly from the main menu.
- **Resource Cleanup:** Uses explicit web-view cleanup and garbage collection when tabs are closed to help reduce unnecessary memory retention.

---

## What's New — v1.5

### Modernized Interface

- Reworked the browser UI with a cleaner, more modern visual style.
- Replaced text-style toolbar icons with scalable **SVG icons**.
- Improved the tab design with dynamic website icons, shortened tab titles, and dedicated close controls.
- Added a refreshed light/dark theme system inspired by modern browser interfaces.

### RAM & Performance Improvements

- Optimized browser architecture and tab cleanup to reduce unnecessary memory retention.
- Current project testing targets approximately **550 MB RAM usage**, compared with roughly **650 MB** in the previous build, depending on workload and open pages.

### Comprehensive Downloads Experience

- Added a dedicated **downloads popup bubble** for quick access to active and recent downloads.
- Added a full **Downloads Manager** dialog.
- Added live download progress tracking.
- Download records are persisted locally.
- Completed downloads can be opened directly, with access to their containing folder where supported.
- Added a **Clear All** downloads action.

### Bookmarks

- Added a bookmark button directly beside the address bar.
- Added a dynamic bookmarks bar that appears when bookmarks are saved.
- Added bookmark deletion through the bookmark context menu.
- Bookmark data is stored locally between sessions.

### Multiple Search Engines

- Added selectable search engines:
  - Google
  - DuckDuckGo
  - Bing
  - Ecosia
  - Brave Search
  - Yahoo
- The selected search engine is saved for future sessions.

### AI & Content Safety Features

- Added an **AI-Generated Media Detector** that can label detected AI-generated images and videos.
- Added an **AI Slop & Brainrot Blocker** with heuristics for synthetic spam, mutant anatomy, distorted imagery, and common generative-content signatures.
- Added click-to-reveal AI-slop filtering.
- Added NSFW/explicit-media blurring with click-to-reveal controls.
- Added automatic muting/pausing for detected explicit videos.
- Added a dedicated **Blockers and filters** configuration window.

### Theme & Personalization

- Added multiple accent-color presets:
  - Classic Blue
  - Arc Violet
  - Cyber Emerald
  - Sunset Orange
  - Neon Rose
  - Electric Teal
  - Crimson Red
  - Gold Amber
- Added a custom color picker.
- Accent colors are applied to browser UI elements such as active tabs, highlights, and download progress.

### Windows Integration Improvements

- Added protected Windows Registry browser registration.
- EcoBrowser registers `http` and `https` URL associations and `.html`/`.htm` file associations.
- Registration state is stored locally to avoid unnecessary duplicate registry writes.
- The browser can receive URLs from external applications through command-line arguments.

### Navigation & Privacy Improvements

- Added HTTPS security indicators in the address bar.
- Added automatic browsing-history logging with a dedicated History dialog.
- Added cookie clearing from the main menu.
- Added navigation-level blocking for configured advertising/tracking and adult-content domains.

---

## Keyboard Shortcuts

| Shortcut | Action         |
| -------- | -------------- |
| `Ctrl+T` | Open a new tab |
| `Ctrl+J` | Open Downloads |
| `Ctrl+H` | Open History   |

---

## Built-in Search Engines

EcoBrowser currently includes:

| Search Engine | Search URL        |
| ------------- | ----------------- |
| Google        | Google Search     |
| DuckDuckGo    | DuckDuckGo Search |
| Bing          | Bing Search       |
| Ecosia        | Ecosia Search     |
| Brave         | Brave Search      |
| Yahoo         | Yahoo Search      |

The active search engine can be changed from **EcoBrowser Menu → Search Engine**.

---

## Installation & Distribution

You can download EcoBrowser through the following:

- **GitHub Releases:** Get the latest installer (`EcoBrowser_Setup.exe`) from the [GitHub Releases page](https://github.com/ahmedomardev/EcoBrowser/releases).
- **Uptodown:** Download **EcoBrowser for Windows** from [Uptodown](https://en.uptodown.com/windows).

> **NOTE:** It is recommended to download EcoBrowser from the GitHub repository because the newest versions are published there first. Uptodown may take about 2 days to review and publish a new version.

---

## Technology

- **Language:** Python
- **GUI:** PyQt6
- **Browser Engine:** PyQt6-WebEngine / Chromium
- **Platform Integration:** Windows Registry
- **UI Graphics:** SVG-based icons
- **Local Data:** JSON-based settings, bookmarks, and download records

---

## Project

**GitHub:** https://github.com/ahmedomardev/EcoBrowser

**Current source version:** `1.5`
