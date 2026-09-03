# EcoBrowser

**EcoBrowser** is a fast, lightweight, and modern desktop web browser built with C# and Microsoft WebView2 (Chromium). It features built-in ad blocking, tab management, navigation controls, file logging, and native integration with Windows as a customizable default browser.

---

## Key Features

- **Chromium Performance**: Powered by Microsoft WebView2 engine for modern web standard compatibility and speed.
- **Tab Management**: Support for opening, switching, custom-rendering, and closing browser tabs dynamically.
- **Windows Default Browser Ready**: Built-in automated registry setup enabling Windows to recognize EcoBrowser in Default Apps (`http`/`https` associations).
- **Protocol & Command Line Handling**: Accepts URL arguments when launched from external applications (e.g., Discord, Word, Outlook).
- **Browsing History**: Automatically logs visited web locations to a local history log file.
- **Built-in Ad & Tracker Blocker:** Intercepts network navigation to block common ad networks and telemetry domains automatically.
- **Dark Mode Support:** Seamless global dark mode switching with auto-injected web CSS adjustments.
- **History & Downloads:** Integrated browsing history logger and direct access to the default Chromium download manager.

---

## File Structure Overview

- **`Form1.cs`**: Main application logic including tab controls, registry setup for default browser integration, ad-block filters, icon handling, and custom painting.
- **`Form1.Designer.cs`**: Automated code generation layout containing control definitions and component initialization.

---

## Setup & Running locally

### Prerequisites

- [.NET 6.0 SDK](https://dotnet.microsoft.com/download) or higher
- [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) (pre-installed on Windows 10/11)

### Downloading the Project

1. Clone the repository:

```bash
git clone <https://github.com/ahmedomardev/EcoBrowser>
cd EcoBrowser
```

### You can download the exe from the releases by using the setup.exe file or the ecobrowser.exe file

## Setting EcoBrowser as Default Browser

1. Launch **EcoBrowser** at least once to automatically create the necessary registry entries under `HKCU`.
2. Open Windows Settings (**Win + I**).
3. Navigate to **Apps** $\rightarrow$ **Default apps**.
4. Search for **EcoBrowser**.
5. Select **Set default**.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

# COMING TO UPTODOWN SOON!!
