# EcoBrowser

**EcoBrowser** (`ahmedomardev/EcoBrowser`) is a fast, modern web browser built using Python and `PyQt6-WebEngine`. It features a clean, responsive interface, native Windows integration, and is engineered for optimal speed using a structured directory deployment model.

## Features

- **Chromium-Powered Engine:** Utilizes `PyQt6-WebEngine` for modern web rendering and compatibility.
- **Optimized RAM Usage:** Lightweight architecture engineered to use significantly less memory for an ultra-snappy experience.
- **Windows Default Browser Ready:** Built-in automated registry setup enabling Windows to recognize EcoBrowser in Default Apps (`http`/`https` associations).
- **Protocol & Command Line Handling:** Accepts URL arguments when launched from external applications (e.g., Discord, Word, Outlook).
- **Browsing History & Downloads:** Automatically logs visited web locations to a local history log file and provides direct access to the Chromium download manager.
- **Built-in Ad & Tracker Blocker:** Intercepts network navigation to block common ad networks and telemetry domains automatically.
- **Dark Mode Support:** Seamless global dark mode switching with auto-injected web CSS adjustments.

---

## What's New

- **Advanced Tab Management & Bookmarks:** Seamlessly manage tabs and easily save your favorite sites using built-in bookmarks.
- **Massive RAM Optimization:** Consumes a fraction of the memory compared to previous builds—dropping from ~1800MB (running 5 YouTube long-form videos and 1 Short) down to just ~650MB.
- **Built-in Adult Content Blocker:** Automatically blocks pornography sites for a safer browsing experience.
- **Persistent Preferences:** Automatically saves your favorite settings, such as dark/light mode states and ad blocker configurations.

---

## Installation & Distribution

You can download the latest professional installer (`EcoBrowser_Setup.exe`) directly from the [GitHub Releases page](https://github.com/ahmedomardev/EcoBrowser/releases).

The installer handles setting up the directory structure cleanly in `C:\EcoBrowser`, creates optional desktop shortcuts, and registers file associations automatically.