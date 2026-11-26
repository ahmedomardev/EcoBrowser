import base64
import ctypes
import gc
import hashlib
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlsplit, urlunsplit

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--use-gl=angle --use-angle=d3d11 "
    "--enable-gpu-rasterization --ignore-gpu-blocklist --disable-webgpu "
    "--renderer-process-limit=4 "
    "--disable-features=TranslateUI,BackForwardCache,CompressionDictionaryTransport,SharedDictionary,WebGPU "
    '--js-flags="--max-old-space-size=512 --expose-gc"'
)

try:
    _cache_dir = pathlib.Path.home() / "AppData" / "Roaming" / "EcoBrowser" / "cache"
    if _cache_dir.exists():
        for _p in _cache_dir.rglob("*SharedDictionary*"):
            if _p.is_file():
                try:
                    _p.unlink()
                except OSError:
                    pass
except Exception:
    pass

if sys.platform == "win32":
    try:
        import winreg as reg
    except ImportError:
        reg = None
else:
    reg = None

from PyQt6.QtCore import (
    QByteArray,
    QObject,
    QSize,
    QStandardPaths,
    Qt,
    QTimer,
    QUrl,
    pyqtSignal,
)

try:
    from PyQt6 import sip as _sip  # type: ignore
except ImportError:
    _sip = None

from PyQt6.QtGui import QColor, QIcon, QKeySequence, QPainter, QPixmap, QShortcut
from PyQt6.QtNetwork import QNetworkProxy, QNetworkProxyFactory
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWebEngineCore import (
    QWebEngineDownloadRequest,
    QWebEngineGlobalSettings,
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineScript,
    QWebEngineSettings,
    QWebEngineUrlRequestInterceptor,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTabBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def is_view_deleted(view):
    try:
        return bool(_sip is not None and _sip.isdeleted(view))
    except Exception:
        return False


def _read_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _write_json(path, data, indent=4):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception:
        return False


APP_NAME = "EcoBrowser"
APP_VERSION = "2.5"
HOME_URL = "https://www.google.com"
DEFAULT_SEARCH_ENGINE = "Google"
DEFAULT_ACCENT_COLOR = "#58a6ff"
FERNET_KEY_FILENAME = ".pm_key"

SEARCH_ENGINES = {
    "Google": {
        "name": "Google",
        "query_url": "https://www.google.com/search?q=",
        "home_url": "https://www.google.com",
    },
    "DuckDuckGo": {
        "name": "DuckDuckGo",
        "query_url": "https://duckduckgo.com/?q=",
        "home_url": "https://duckduckgo.com",
    },
    "Bing": {
        "name": "Bing",
        "query_url": "https://www.bing.com/search?q=",
        "home_url": "https://www.bing.com",
    },
    "Ecosia": {
        "name": "Ecosia",
        "query_url": "https://www.ecosia.org/search?q=",
        "home_url": "https://www.ecosia.org",
    },
    "Brave": {
        "name": "Brave",
        "query_url": "https://search.brave.com/search?q=",
        "home_url": "https://search.brave.com",
    },
    "Yahoo": {
        "name": "Yahoo",
        "query_url": "https://search.yahoo.com/search?p=",
        "home_url": "https://search.yahoo.com",
    },
}

COLOR_PRESETS = [
    {"name": "Classic Blue", "color": "#0969da", "dark_color": "#58a6ff"},
    {"name": "Arc Violet", "color": "#8b5cf6", "dark_color": "#a78bfa"},
    {"name": "Cyber Emerald", "color": "#10b981", "dark_color": "#34d399"},
    {"name": "Sunset Orange", "color": "#f97316", "dark_color": "#fb923c"},
    {"name": "Neon Rose", "color": "#ec4899", "dark_color": "#f472b6"},
    {"name": "Electric Teal", "color": "#06b6d4", "dark_color": "#22d3ee"},
    {"name": "Crimson Red", "color": "#ef4444", "dark_color": "#f87171"},
    {"name": "Gold Amber", "color": "#eab308", "dark_color": "#facc15"},
]

READER_THEMES = {
    "auto": {
        "label": "Auto (Match Browser)",
        "light_bg": "#ffffff",
        "light_fg": "#1a1a1a",
        "dark_bg": "#121418",
        "dark_fg": "#e6edf3",
    },
    "light": {"label": "Light", "bg": "#ffffff", "fg": "#1a1a1a", "accent": "#0969da"},
    "sepia": {"label": "Sepia", "bg": "#f4ecd8", "fg": "#5b4636", "accent": "#8b5e34"},
    "dark": {"label": "Dark", "bg": "#1a1a1a", "fg": "#e0e0e0", "accent": "#58a6ff"},
    "paper": {"label": "Paper", "bg": "#fdfcf9", "fg": "#2d2d2d", "accent": "#1a7f37"},
    "midnight": {
        "label": "Midnight",
        "bg": "#0d1117",
        "fg": "#c9d1d9",
        "accent": "#f778ba",
    },
}

READER_FONTS = {
    "serif": {
        "label": "Serif (Literata)",
        "stack": "Georgia, 'Times New Roman', Literata, serif",
    },
    "sans": {
        "label": "Sans (System)",
        "stack": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    },
    "mono": {
        "label": "Mono (JetBrains)",
        "stack": "'JetBrains Mono', 'SF Mono', Consolas, monospace",
    },
    "dyslexic": {
        "label": "Dyslexic-Friendly",
        "stack": "'OpenDyslexic', 'Lexie Readable', Verdana, sans-serif",
    },
    "news": {
        "label": "News (Charter)",
        "stack": "Charter, 'Bitstream Charter', Georgia, serif",
    },
}

READER_WIDTHS = {
    "narrow": {"label": "Narrow", "px": 640},
    "medium": {"label": "Medium", "px": 740},
    "wide": {"label": "Wide", "px": 860},
    "xwide": {"label": "Extra Wide", "px": 1020},
}

DNS_PROVIDERS = {
    "cloudflare_family": {
        "label": "Cloudflare Family",
        "url": "https://family.cloudflare-dns.com/dns-query",
    },
    "cloudflare_standard": {
        "label": "Cloudflare Standard",
        "url": "https://cloudflare-dns.com/dns-query",
    },
    "custom": {"label": "Custom DNS-over-HTTPS", "url": ""},
}

DEFAULT_SETTINGS = {
    "dark_mode": True,
    "search_engine": DEFAULT_SEARCH_ENGINE,
    "custom_accent": DEFAULT_ACCENT_COLOR,
    "registry_registered": False,
    "dns_enabled": True,
    "dns_provider": "cloudflare_family",
    "custom_doh_url": "",
    "proxy_enabled": False,
    "proxy_type": "SOCKS5",
    "proxy_host": "",
    "proxy_port": 1080,
    "proxy_username": "",
    "proxy_password": "",
    "reader_font": "serif",
    "reader_font_size": 19,
    "reader_line_height": 1.8,
    "reader_width": "medium",
    "reader_theme": "auto",
    "reader_text_align": "start",
    "reader_hide_chrome": True,
    "userscripts_enabled": True,
    "password_manager_enabled": True,
    "password_autofill_enabled": True,
    "password_save_prompt": True,
    "toolbar_pinned": {
        "back": True,
        "forward": True,
        "reload": True,
        "home": True,
        "reader": True,
        "userscript": False,
        "downloads": True,
        "proxy": False,
        "blockers": False,
        "bookmarks": True,
        "passwords": False,
        "split": False,
        "vertical_tabs": False,
        "command": False,
        "customize": True,
        "gpu": False,
        "optimizations": False,
        "translate": False,
    },
    "ui_density": "comfortable",
    "ui_animations": True,
    "ui_blur": True,
    "ui_corner_radius": 12,
    "ui_tab_shape": "rounded",
    "ui_font_size": 9.5,
    "ui_show_home_button": True,
    "newtab_enabled": True,
    "newtab_background_type": "gradient",
    "newtab_background_color": "#121418",
    "newtab_background_image": "",
    "newtab_show_search": True,
    "newtab_show_quicklinks": True,
    "newtab_show_clock": True,
    "newtab_show_weather": False,
    "adblock_enabled": True,
    "adult_filter_enabled": True,
    "custom_ad_domains": [],
    "custom_adult_keywords": [],
    "adult_allowlist": [
        "wikipedia.org",
        "google.com",
        "bing.com",
        "duckduckgo.com",
        "youtube.com",
    ],
    "startup_behavior": "newtab",
    "startup_urls": [],
    "homepage_url": "eco://newtab",
    "download_dir": "",
    "download_ask_location": False,
    "default_zoom": 100,
    "hardware_acceleration": True,
    "ram_trim_enabled": True,
    "ram_trim_aggressive": False,
    "ram_trim_interval": 30,
    "disk_hibernation_enabled": False,
    "disk_hibernation_on_switch": False,
    "disk_hibernation_keep_tabs": 1,
    "disk_hibernation_timeout": 0,
    "disk_hibernation_low_ram": True,
    "disk_hibernation_excluded_domains": "",
    "gpu_preference": "high_performance",
    "custom_user_agent": "",
    "custom_css": "",
    "custom_js": "",
    "clear_cache_on_exit": False,
    "do_not_track": False,
    "custom_search_engines": [],
    "blocking_level": 2,
    "translation_enabled": True,
    "translation_target_lang": "en",
    "strip_tracking_params": True,
    "https_only_mode": False,
    "vertical_tabs": False,
    "restore_session": False,
    "download_virus_scan": True,
    "download_block_dangerous": True,
}

TRACKING_QUERY_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "utm_name",
    "fbclid",
    "gclid",
    "dclid",
    "gbraid",
    "wbraid",
    "yclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "_hsenc",
    "_hsmi",
    "hsctatracking",
    "mkt_tok",
    "ref_src",
    "ref_url",
    "spm",
    "si",
    "oly_anon_id",
    "oly_enc_id",
}


def strip_tracking_params(url_str):
    try:
        parsed = urlsplit(url_str)
        if not parsed.query:
            return url_str
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        filtered = [
            (k, v)
            for k, v in pairs
            if k.lower() not in TRACKING_QUERY_PARAMS
            and not k.lower().startswith("utm_")
        ]
        if len(filtered) == len(pairs):
            return url_str
        return urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                urlencode(filtered, doseq=True),
                parsed.fragment,
            )
        )
    except Exception:
        return url_str


AD_DOMAINS = [
    "doubleclick.net",
    "googleads",
    "googlesyndication",
    "googletagmanager.com",
    "googletagservices.com",
    "adservice.google",
    "google-analytics.com",
    "amazon-adsystem.com",
    "adnxs.com",
    "adsrvr.org",
    "adform.net",
    "criteo.com",
    "criteo.net",
    "taboola.com",
    "outbrain.com",
    "facebook.com/tr",
    "connect.facebook.net",
    "hotjar.com",
    "popads.net",
    "propellerads.com",
]

ADULT_DOMAINS = [
    "pornhub.com",
    "xvideos.com",
    "xnxx.com",
    "redtube.com",
    "youporn.com",
    "xhamster.com",
    "stripchat.com",
    "chaturbate.com",
    "onlyfans.com",
    "livejasmin.com",
    "bongacams.com",
    "cam4.com",
    "spankbang.com",
    "beeg.com",
    "tube8.com",
    "hentaihaven.org",
    "eporner.com",
    "brazzers.com",
    "rule34.xxx",
    "youjizz.com",
    "xvideos2.com",
    "txxx.com",
    "hqporner.com",
    "tnaflix.com",
    "porntrex.com",
]

ADULT_KEYWORDS = [
    "porn",
    "xxx",
    "pornography",
    "porno",
    "hentai",
    "nsfw",
    "erotic",
    "erotica",
    "nudity",
    "nude",
    "naked",
    "sexvideo",
    "sexvideos",
    "adult-zone",
    "camgirl",
    "camgirls",
    "onlyfans",
    "fansly",
    "fetish",
    "bondage",
    "bdsm",
    "blowjob",
    "handjob",
    "cumshot",
    "creampie",
    "orgy",
    "orgasm",
    "masturbate",
    "masturbation",
    "escort",
    "brothel",
    "sextape",
    "sexcam",
    "hardcore",
    "softcore",
    "incest",
    "bestiality",
    "pornhub",
    "xvideos",
    "xnxx",
    "redtube",
    "youporn",
    "xhamster",
    "chaturbate",
    "stripchat",
    "bongacams",
    "livejasmin",
    "brazzers",
    "playboy",
    "rule34",
]

LIGHT_THEME = {
    "window_bg": "#f0f2f5",
    "tabstrip_bg": "#e3e6ea",
    "toolbar_bg": "#ffffff",
    "tab_active_bg": "#ffffff",
    "tab_inactive_hover": "rgba(255, 255, 255, 0.70)",
    "omnibox_bg": "#f1f3f6",
    "omnibox_hover_bg": "#e6e9ee",
    "text_primary": "#1f2328",
    "text_secondary": "#5f6672",
    "icon_color": "#57606a",
    "hover_bg": "rgba(0, 0, 0, 0.06)",
    "pressed_bg": "rgba(0, 0, 0, 0.12)",
    "divider": "#d0d7de",
    "tab_divider": "rgba(0, 0, 0, 0.08)",
    "menu_bg": "#ffffff",
    "close_icon_color": "#57606a",
    "close_btn_hover": "rgba(0, 0, 0, 0.10)",
    "star_active": "#1a73e8",
    "accent_blue": "#0969da",
    "accent_emerald": "#1a7f37",
    "accent_warning": "#cf222e",
    "progress_bg": "#e6e9ee",
    "progress_fill": "#0969da",
}

DARK_THEME = {
    "window_bg": "#16181d",
    "tabstrip_bg": "#121418",
    "toolbar_bg": "#1e2229",
    "tab_active_bg": "#1e2229",
    "tab_inactive_hover": "rgba(255, 255, 255, 0.06)",
    "omnibox_bg": "#14171c",
    "omnibox_hover_bg": "#222731",
    "text_primary": "#f0f6fc",
    "text_secondary": "#8b949e",
    "icon_color": "#8b949e",
    "hover_bg": "rgba(255, 255, 255, 0.08)",
    "pressed_bg": "rgba(255, 255, 255, 0.14)",
    "divider": "#30363d",
    "tab_divider": "rgba(255, 255, 255, 0.10)",
    "menu_bg": "#1e2229",
    "close_icon_color": "#8b949e",
    "close_btn_hover": "rgba(255, 255, 255, 0.14)",
    "star_active": "#58a6ff",
    "accent_blue": "#58a6ff",
    "accent_emerald": "#3fb950",
    "accent_warning": "#f85149",
    "progress_bg": "#30363d",
    "progress_fill": "#58a6ff",
}

SVG_ICONS = {
    "back": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>',
    "forward": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"/></svg>',
    "reload": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M17.65 6.35A7.958 7.958 0 0 0 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0 1 12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>',
    "home": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>',
    "stop": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
    "new_tab": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>',
    "lock": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg>',
    "unlock": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 17c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm6-9h-1V6c0-2.76-2.24-5-5-5-2.28 0-4.27 1.54-4.84 3.75l1.94.52C8.45 3.93 9.94 3 11.6 3c1.88 0 3.4 1.52 3.4 3.4V8H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm0 12H6V10h12v10z"/></svg>',
    "star_outline": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M22 9.24l-7.19-.62L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.63-7.03L22 9.24zM12 15.4l-3.76 2.27 1-4.28-3.32-2.88 4.38-.38L12 6.1l1.71 4.04 4.38.38-3.32 2.88 1 4.28M12 15.4z"/></svg>',
    "star_filled": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>',
    "menu": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="5" r="2" fill="{color}"/><circle cx="12" cy="12" r="2" fill="{color}"/><circle cx="12" cy="19" r="2" fill="{color}"/></svg>',
    "sparkles": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M9 21.5L10.5 15l6.5-1.5L10.5 12 9 5.5 7.5 12 1 13.5l6.5 1.5L9 21.5zm10-7.5l1-4.5 4.5-1L20 7.5 19 3l-1 4.5-4.5 1 4.5 1 1 4.5z"/></svg>',
    "download": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>',
    "file": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>',
    "check_circle": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>',
    "tab_close": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
    "globe": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>',
    "palette": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 3c-4.97 0-9 4.03-9 9 0 2.12.74 4.07 1.97 5.61L4.35 19.4c-.39.39-.39 1.02 0 1.41.39.39 1.02.39 1.41 0l1.9-1.9C9.23 19.59 10.57 20 12 20c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-5.5 9c-.83 0-1.5-.67-1.5-1.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12zm3-4C8.67 8 8 7.33 8 6.5S8.67 5 9.5 5s1.5.67 1.5 1.5S10.33 8 9.5 8zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 5 14.5 5s1.5.67 1.5 1.5S15.33 8 14.5 8zm3 4c-.83 0-1.5-.67-1.5-1.5S16.67 9 17.5 9s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/></svg>',
    "key": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12.65 10C11.83 7.67 9.61 6 7 6c-3.31 0-6 2.69-6 6s2.69 6 6 6c2.61 0 4.83-1.67 5.65-4H17v4h4v-4h2v-4H12.65zM7 14c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/></svg>',
    "key_filled": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12.65 10C11.83 7.67 9.61 6 7 6c-3.31 0-6 2.69-6 6s2.69 6 6 6c2.61 0 4.83-1.67 5.65-4H17v4h4v-4h2v-4H12.65zM7 14c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/></svg>',
    "search": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>',
    "reader": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19 4H5c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H5V6h14v12zM7 8h10v2H7V8zm0 4h10v2H7v-2zm0 4h7v2H7v-2z"/></svg>',
    "reader_active": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zM7 10h2v7H7v-7zm4-3h2v10h-2V7zm4 6h2v4h-2v-4z"/></svg>',
    "code": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z"/></svg>',
    "script": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 14H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>',
    "text_size": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M2.5 4v3h5v12h3V7h5V4h-13zm19 5v3h-5v12h-3V9h-5V6.5h13z"/></svg>',
    "proxy": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 4c1.86 0 3.41 1.28 3.86 3H21v2c0 4.29-2.91 8.29-9 9.87-6.09-1.58-9-5.58-9-9.87v-2h5.14C8.59 6.28 10.14 5 12 5zm0 2a2 2 0 100 4 2 2 0 000-4z"/></svg>',
    "shield": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-1 14l-4-4 1.41-1.41L11 12.17l4.59-4.58L17 9l-6 6z"/></svg>',
    "pin": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M16 9V4L8 4v5l-4 4v2h5v5h2v-5h5v-2l-4-4z"/></svg>',
    "close_small": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
    "gpu": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M15 9H9v6h6V9zm-2 4h-2v-2h2v2zm8-2V9h-2V7c0-1.1-.9-2-2-2h-2V3h-2v2h-2V3H9v2H7c-1.1 0-2 .9-2 2v2H3v2h2v2H3v2h2v2c0 1.1.9 2 2 2h2v2h2v-2h2v2h2v-2h2c1.1 0 2-.9 2-2v-2h2v-2h-2v-2h2zm-4 6H7V7h10v10z"/></svg>',
    "monitor": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M20 18c1.1 0 1.99-.9 1.99-2L22 6c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2H0v2h24v-2h-4zM4 6h16v10H4V6z"/></svg>',
    "info": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>',
    "split": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M3 5v14h18V5H3zm8 12H5V7h6v10zm8 0h-6V7h6v10z"/></svg>',
    "sidebar": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M3 5v14h18V5H3zm6 12H5V7h4v10zm10 0h-8V7h8v10z"/></svg>',
    "command": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M18 14a3 3 0 0 0-3 3v1H9v-1a3 3 0 1 0-3 3 3 3 0 0 0 3-3v-1h6v1a3 3 0 1 0 3-3zm0 4a1 1 0 1 1 0-2 1 1 0 0 1 0 2zM6 18a1 1 0 1 1 0-2 1 1 0 0 1 0 2zm9-9H9V7a3 3 0 1 0-3 3h1v4H6a1 1 0 1 1 0-2h1V9H6a1 1 0 1 1 0-2 1 1 0 0 1 1 1v1h6V8a3 3 0 1 0 3 3h-1v3h1a1 1 0 1 1 0 2h-1v-4h1a1 1 0 1 1 0-2z"/></svg>',
    "camera": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9zm3 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/></svg>',
}


def is_valid_https_url(value):
    if not value or any(ch.isspace() for ch in value):
        return False
    try:
        p = urlsplit(value)
        return (
            p.scheme.lower() == "https"
            and bool(p.hostname)
            and p.username is None
            and p.password is None
            and (p.port is None or 1 <= p.port <= 65535)
        )
    except ValueError:
        return False


def render_svg_icon(svg_template, color, size=20):
    renderer = QSvgRenderer(
        QByteArray(svg_template.replace("{color}", color).encode("utf-8"))
    )
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def format_file_size(size_bytes):
    if not size_bytes or size_bytes <= 0:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024.0:
            return f"{int(size_bytes)} B" if unit == "B" else f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


ECO_GUARD_JS = r"""
(function(){if(window.__ecoGuard)return;window.__ecoGuard=1;
let lvl=window.__ecoGuardLevel;
if(lvl===undefined){try{lvl=parseInt(localStorage.getItem('eco_blocking_level')||'2');}catch(e){lvl=2;}window.__ecoGuardLevel=lvl;}
if(lvl===0)return;
let R=/\b(porn|xxx|pornography|hentai|nsfw|onlyfans|fansly|erotic|fetish|bdsm|bondage|blowjob|handjob|cumshot|creampie|orgy|masturbat|escort|brothel|sextape|sexcam|hardcore|softcore|incest|bestiality|pornhub|xvideos|xnxx|redtube|youporn|xhamster|chaturbate|stripchat|bongacams|livejasmin|brazzers|playboy|rule34)\b/i;
let C=".b{filter:blur(32px)!important}.u{filter:none!important}.v{filter:blur(24px)!important;opacity:.65!important}.w{filter:none!important}";
try{let s=document.createElement('style');s.textContent=C;(document.head||document.documentElement).appendChild(s);}catch(e){}
function n(e){if(window.__ecoGuardLevel===0||!e||e._c)return;e._c=1;try{if(R.test((e.alt||'')+' '+(e.title||''))){e._b=1;e.classList.add('b');}}catch(err){}}
function r(){if(window.__ecoGuardLevel!==0)try{document.querySelectorAll('img,video').forEach(n);}catch(e){}}
let o=new MutationObserver(muts=>{if(window.__ecoGuardLevel===0)return;for(let m of muts)for(let a of m.addedNodes)if(a.nodeType===1){if(a.matches&&a.matches('img,video'))n(a);else if(a.querySelectorAll)try{a.querySelectorAll('img,video').forEach(n);}catch(e){}}});
try{r();o.observe(document.body||document.documentElement,{childList:true,subtree:true});}catch(e){}
window.addEventListener('ecoGuardLevelChanged',e=>{window.__ecoGuardLevel=e.detail.level;if(e.detail.level===0)try{document.querySelectorAll('.b,.v').forEach(el=>{el.classList.remove('b','v');el.classList.add('u','w');el.style.filter='none';});}catch(err){}});
})();
"""

AI_SAFEGUARD_SCRIPT = ECO_GUARD_JS
ADULT_PAGE_BLOCKER_JS = ""
PASSWORD_DETECTOR_JS = ""

ECO_READER_JS = r"""
(function(){if(window.__ecoReaderInitialized)return;window.__ecoReaderInitialized=true;
const THEMES={light:{bg:'#ffffff',fg:'#1a1a1a',muted:'#6b7280',border:'#e5e7eb',accent:'#0969da',codeBg:'#f3f4f6'},sepia:{bg:'#f4ecd8',fg:'#5b4636',muted:'#8b7355',border:'#e8dcc6',accent:'#8b5e34',codeBg:'#efe3c8'},dark:{bg:'#1e2229',fg:'#e6edf3',muted:'#8b949e',border:'#30363d',accent:'#58a6ff',codeBg:'#161b22'},paper:{bg:'#fdfcf9',fg:'#2d2d2d',muted:'#6b6b6b',border:'#ece9e3',accent:'#1a7f37',codeBg:'#f6f3ee'},midnight:{bg:'#0d1117',fg:'#c9d1d9',muted:'#8b949e',border:'#21262d',accent:'#f778ba',codeBg:'#161b22'}};
const POS=/article|body|content|entry|hentry|main|page|post|text|blog|story/i,NEG=/comment|combx|disqus|foot|header|menu|nav|remark|rss|shoutbox|sidebar|sponsor|ad-break|agegate|pagination|pager|popup|tweet|twitter|social|advert|comic|share|login|form|signup|related|recommended|trending|promo/i;
const FONTS={serif:"Georgia,'Times New Roman',Literata,Charter,serif",sans:"-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif",mono:"'JetBrains Mono','SF Mono',Consolas,Menlo,monospace",dyslexic:"'OpenDyslexic','Lexie Readable',Verdana,sans-serif",news:"Charter,'Bitstream Charter',Georgia,serif"};
const WIDTHS={narrow:640,medium:740,wide:860,xwide:1020,full:1200};
window.__ecoReader={isActive:false,original:{scrollY:0,bodyOverflow:''},settings:{font:'serif',fontSize:19,lineHeight:1.8,width:'medium',theme:'auto',textAlign:'start',isDarkBrowser:false},
_injectBaseStyles(){if(document.getElementById('__ecoReader_base'))return;const s=document.createElement('style');s.id='__ecoReader_base';s.textContent=`#eco-reader-overlay{position:fixed!important;inset:0!important;z-index:2147483646!important;overflow-y:auto!important;overflow-x:hidden!important;-webkit-font-smoothing:antialiased!important}#eco-reader-overlay *{box-sizing:border-box!important}.eco-reader-toolbar{position:sticky!important;top:0!important;z-index:10!important;backdrop-filter:blur(16px)!important;border-bottom:1px solid var(--er-border)!important;display:flex!important;align-items:center!important;justify-content:space-between!important;padding:10px 18px 10px 56px!important;gap:12px!important}.eco-reader-toolbar-group{display:flex!important;align-items:center!important;gap:8px!important;flex-wrap:wrap!important}.eco-reader-btn{border:1px solid var(--er-border)!important;background:var(--er-bg)!important;color:var(--er-fg)!important;border-radius:9999px!important;padding:6px 12px!important;font-size:12.5px!important;cursor:pointer!important}.eco-reader-select{background:var(--er-bg)!important;color:var(--er-fg)!important;border:1px solid var(--er-border)!important;border-radius:8px!important;padding:6px 10px!important;font-size:12.5px!important}.eco-reader-mini-fab{position:fixed!important;top:10px!important;left:12px!important;z-index:2147483647!important;width:36px!important;height:36px!important;border-radius:9999px!important;border:1px solid var(--er-border)!important;background:var(--er-bg)!important;color:var(--er-fg)!important;cursor:pointer!important}.eco-reader-content-wrap{margin:0 auto!important;padding:32px 24px 80px!important}.eco-reader-article{line-height:var(--er-lh)!important;font-size:var(--er-fs)!important;font-family:var(--er-font)!important;color:var(--er-fg)!important;text-align:var(--er-align,start)!important}.eco-reader-article img{max-width:100%!important;height:auto!important;border-radius:12px!important;margin:1.5em 0!important}.eco-reader-article p{margin:0 0 1.2em!important}.eco-reader-article a{color:var(--er-accent)!important}.eco-reader-meta{color:var(--er-muted)!important;font-size:13px!important;margin-bottom:24px!important;display:flex!important;gap:12px!important;flex-wrap:wrap!important}.eco-reader-divider{height:1px!important;background:var(--er-border)!important;margin:24px 0!important;border:0!important}`;(document.head||document.documentElement).appendChild(s);},
_getThemeColors(){let k=this.settings.theme;if(k==='auto')k=this.settings.isDarkBrowser?'dark':'light';return THEMES[k]||THEMES.light;},
_applyTheme(){const c=this._getThemeColors(),ov=document.getElementById('eco-reader-overlay');if(!ov)return;ov.style.background=c.bg;ov.style.color=c.fg;for(const[k,v]of Object.entries({'--er-bg':c.bg,'--er-fg':c.fg,'--er-muted':c.muted,'--er-border':c.border,'--er-accent':c.accent,'--er-codeBg':c.codeBg,'--er-font':FONTS[this.settings.font]||FONTS.serif,'--er-fs':this.settings.fontSize+'px','--er-lh':this.settings.lineHeight,'--er-align':this.settings.textAlign==='justify'?'justify':'start'}))ov.style.setProperty(k,v);},
_getWidthPx(){return WIDTHS[this.settings.width]||740;},
isProbablyReaderable(){try{if((document.body?.innerText||'').length<600||document.querySelectorAll('p').length<3)return false;if(document.querySelector('article'))return true;let s=0;document.querySelectorAll('p').forEach(p=>{if(p.textContent.length>100)s++;});return s>=4;}catch(e){return false;}},
_extractArticle(){let cands=[];document.querySelectorAll('div,article,section,main').forEach(el=>{const t=el.innerText||'';if(t.length<200)return;const ci=(el.className||'')+' '+(el.id||'');if(NEG.test(ci)&&!/and|article|body|column|main/i.test(ci))return;let sc=Math.min(Math.floor(t.length/100),5)+(POS.test(ci)?3:0)-(NEG.test(ci)?3:0)+el.querySelectorAll('p').length*0.5;if(sc>1.5)cands.push({el,sc,len:t.length});});cands.sort((a,b)=>b.sc-a.sc||b.len-a.len);const top=cands[0]?.el||document.querySelector('article,main')||document.body;let title=document.querySelector('meta[property="og:title"]')?.content||document.title||'';const h1=document.querySelector('h1');if(h1&&h1.innerText.trim().length>10&&h1.innerText.trim().length<200)title=h1.innerText.trim();const by=document.querySelector('[rel="author"],.author,.byline')?.innerText?.trim().slice(0,120)||'';const tm=document.querySelector('time')?.innerText?.trim().slice(0,40)||'';const cl=top.cloneNode(true);cl.querySelectorAll('script,style,nav,aside,footer,header,form,button,input,textarea,select,noscript,iframe,.ad,[class*="ad-"],[class*="share"],[class*="social"],[class*="comment"],[class*="sidebar"],[class*="popup"]').forEach(n=>n.remove());const words=cl.innerText.split(/\s+/).length;return{title,byline:by,date:tm,html:cl.innerHTML,words,minutes:Math.max(1,Math.round(words/220))};},
_escape(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;},
enter(){if(this.isActive)return;this._injectBaseStyles();this.original.scrollY=window.scrollY;this.original.bodyOverflow=document.body.style.overflow;const a=this._extractArticle(),ov=document.createElement('div');ov.id='eco-reader-overlay';ov.innerHTML=`<button id="eco-reader-mini-exit" class="eco-reader-mini-fab">✕</button><div class="eco-reader-toolbar"><div class="eco-reader-toolbar-group"><button class="eco-reader-btn" id="eco-reader-close">✕ Exit Reader</button><span style="font-size:12px;color:var(--er-muted)">Reader • EcoBrowser</span></div><div class="eco-reader-toolbar-group"><select class="eco-reader-select" id="eco-reader-font"><option value="serif">Serif</option><option value="sans">Sans</option><option value="news">News</option><option value="mono">Mono</option><option value="dyslexic">Dyslexic</option></select><select class="eco-reader-select" id="eco-reader-theme"><option value="auto">Auto</option><option value="light">Light</option><option value="sepia">Sepia</option><option value="paper">Paper</option><option value="dark">Dark</option><option value="midnight">Midnight</option></select><select class="eco-reader-select" id="eco-reader-width"><option value="narrow">Narrow</option><option value="medium">Medium</option><option value="wide">Wide</option><option value="xwide">X-Wide</option></select><button class="eco-reader-btn" id="eco-reader-fs-dec">A-</button><button class="eco-reader-btn" id="eco-reader-fs-inc">A+</button></div></div><div class="eco-reader-content-wrap" style="max-width:${this._getWidthPx()}px"><article class="eco-reader-article"><h1>${this._escape(a.title)}</h1><div class="eco-reader-meta">${a.byline?`<span>By ${this._escape(a.byline)}</span>`:''}${a.date?`<span>• ${this._escape(a.date)}</span>`:''}<span>${a.minutes} min read • ${a.words.toLocaleString()} words</span></div><hr class="eco-reader-divider"/><div>${a.html}</div></article></div>`;document.body.appendChild(ov);document.body.style.overflow='hidden';ov.querySelector('#eco-reader-font').value=this.settings.font;ov.querySelector('#eco-reader-theme').value=this.settings.theme;ov.querySelector('#eco-reader-width').value=this.settings.width;ov.querySelector('#eco-reader-close').onclick=()=>this.exit();ov.querySelector('#eco-reader-mini-exit').onclick=()=>this.exit();ov.querySelector('#eco-reader-font').onchange=e=>{this.settings.font=e.target.value;this._applyTheme();};ov.querySelector('#eco-reader-theme').onchange=e=>{this.settings.theme=e.target.value;this._applyTheme();};ov.querySelector('#eco-reader-width').onchange=e=>{this.settings.width=e.target.value;ov.querySelector('.eco-reader-content-wrap').style.maxWidth=this._getWidthPx()+'px';};ov.querySelector('#eco-reader-fs-dec').onclick=()=>{this.settings.fontSize=Math.max(12,this.settings.fontSize-1);this._applyTheme();};ov.querySelector('#eco-reader-fs-inc').onclick=()=>{this.settings.fontSize=Math.min(36,this.settings.fontSize+1);this._applyTheme();};ov.addEventListener('keydown',e=>{if(e.key==='Escape')this.exit();});this._applyTheme();this.isActive=true;},
exit(){if(!this.isActive)return;document.getElementById('eco-reader-overlay')?.remove();document.body.style.overflow=this.original.bodyOverflow||'';window.scrollTo(0,this.original.scrollY||0);this.isActive=false;},
toggle(){this.isActive?this.exit():this.enter();},
updateSettings(s){Object.assign(this.settings,s);this._applyTheme();const w=document.querySelector('#eco-reader-overlay .eco-reader-content-wrap');if(w)w.style.maxWidth=this._getWidthPx()+'px';},
setBrowserDark(d){this.settings.isDarkBrowser=!!d;if(this.settings.theme==='auto'&&this.isActive)this._applyTheme();}};
window.__ecoReaderIsReadable=()=>window.__ecoReader.isProbablyReaderable();
window.__ecoReaderToggle=()=>window.__ecoReader.toggle();
window.__ecoReaderUpdate=j=>{try{window.__ecoReader.updateSettings(JSON.parse(j));}catch(e){}};
})();
"""
READER_MODE_JS = ECO_READER_JS

ECO_AUTH_JS = r"""
(function(){if(window._gm)return;window._gm=window.__ecoUserscriptPolyfill=1;
window.GM=window.GM||{};window.GM_info={scriptHandler:'EcoBrowser'};
window.GM_addStyle=c=>{let s=document.createElement('style');s.textContent=c;(document.head||document.documentElement).appendChild(s);return s;};
window.GM_getValue=(k,d)=>{try{let v=localStorage.getItem('eco_gm_'+k);return v!==null?JSON.parse(v):d;}catch(e){return d;}};
window.GM_setValue=(k,v)=>{try{localStorage.setItem('eco_gm_'+k,JSON.stringify(v));}catch(e){}};
window.GM_deleteValue=k=>localStorage.removeItem('eco_gm_'+k);
window.GM_listValues=()=>{let a=[];for(let i=0;i<localStorage.length;i++){let k=localStorage.key(i);if(k&&k.startsWith('eco_gm_'))a.push(k.slice(7));}return a;};
window.GM_log=(...a)=>console.log('[GM]',...a);
window.GM_openInTab=u=>{window.open(u,'_blank');return{close:()=>{}};};
window.unsafeWindow=window;
})();
"""
USERSCRIPT_POLYFILL_JS = ECO_AUTH_JS

ECO_TRANSLATE_JS = r"""
(function(){if(window.__ecoTranslateLoaded)return;window.__ecoTranslateLoaded=1;
let C=".eco-t-bubble{position:fixed!important;bottom:20px!important;right:20px!important;z-index:2147483647!important;background:#1e2229!important;border:1px solid #30363d!important;border-radius:24px!important;padding:10px 18px!important;color:#f0f6fc!important;cursor:pointer!important}.eco-t-panel{position:fixed!important;bottom:70px!important;right:20px!important;z-index:2147483647!important;background:#1e2229!important;border:1px solid #30363d!important;border-radius:16px!important;padding:16px!important;min-width:300px!important;display:none!important;color:#f0f6fc!important}.eco-t-panel.show{display:block!important}.eco-t-select{width:100%!important;background:#121418!important;color:#f0f6fc!important;border:1px solid #30363d!important;border-radius:8px!important;padding:8px!important;margin-bottom:10px!important}.eco-t-btn{background:#238636!important;color:#fff!important;border:0!important;border-radius:20px!important;padding:10px 16px!important;cursor:pointer!important;width:100%!important;font-weight:600!important;margin-top:6px!important}.eco-t-status{font-size:11px!important;color:#8b949e!important;margin-top:8px!important;text-align:center!important}.eco-t-progress{width:100%!important;height:4px!important;background:#121418!important;border-radius:2px!important;margin-top:8px!important;display:none!important}.eco-t-progress-bar{height:100%!important;background:#238636!important;width:0%!important}";
try{let s=document.createElement('style');s.textContent=C;(document.head||document.documentElement).appendChild(s);}catch(e){}
let orig=new Map(),cache=[];
function getNodes(){let w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,{acceptNode(n){let t=(n.nodeValue||'').trim(),p=n.parentElement;if(!p||t.length<2||t.length>500||p.closest('script,style,noscript,iframe,svg,canvas,.eco-t-bubble,.eco-t-panel'))return NodeFilter.FILTER_REJECT;let st=getComputedStyle(p);return(st.display==='none'||st.visibility==='hidden')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT;}});let a=[],n;while(n=w.nextNode())a.push(n);cache=a;return a;}
window.__ecoCollectTexts=()=>getNodes().map(n=>n.nodeValue);
window.__ecoApplyTranslations=arr=>{let nodes=cache.length?cache:getNodes();if(!orig.size)nodes.forEach(n=>orig.set(n,n.nodeValue));for(let i=0;i<nodes.length&&i<arr.length;i++)if(arr[i]&&arr[i].trim())nodes[i].nodeValue=arr[i];let s=document.getElementById('eco-t-status');if(s)s.textContent=`Translated ${arr.length} pieces`;let p=document.getElementById('eco-t-progress');if(p)p.style.display='none';};
window.__ecoRestoreOriginal=()=>{orig.forEach((v,n)=>{if(n&&n.parentElement)n.nodeValue=v;});};
window.__ecoTranslate=lang=>console.log('ECO_TRANSLATE_REQUEST::'+lang+'::'+JSON.stringify(getNodes().map(n=>n.nodeValue).slice(0,300)));
try{if(!document.getElementById('eco-translate-bubble')){let b=document.createElement('div');b.id='eco-translate-bubble';b.className='eco-t-bubble';b.textContent='Translate';b.onclick=()=>document.getElementById('eco-translate-panel')?.classList.toggle('show');document.body.appendChild(b);let p=document.createElement('div');p.id='eco-translate-panel';p.className='eco-t-panel';p.innerHTML=`<div style="display:flex;justify-content:space-between;margin-bottom:12px"><b>Translate Page</b><button onclick="this.closest('.eco-t-panel').classList.remove('show')" style="background:none;border:0;color:#8b949e;cursor:pointer">✕</button></div><select class="eco-t-select" id="eco-t-lang"><option value="en">English</option><option value="es">Spanish</option><option value="fr">French</option><option value="de">German</option><option value="ar">Arabic</option><option value="hi">Hindi</option><option value="tr">Turkish</option><option value="ru">Russian</option><option value="zh">Chinese</option><option value="ja">Japanese</option><option value="pt">Portuguese</option><option value="it">Italian</option><option value="ko">Korean</option><option value="ur">Urdu</option></select><button class="eco-t-btn" id="eco-t-do">Translate Every Text</button><button class="eco-t-btn" id="eco-t-restore" style="background:#30363d!important">Restore Original</button><div class="eco-t-progress" id="eco-t-progress"><div class="eco-t-progress-bar" id="eco-t-progress-bar"></div></div><div class="eco-t-status" id="eco-t-status">Ready</div>`;document.body.appendChild(p);document.getElementById('eco-t-do').onclick=()=>window.__ecoTranslate(document.getElementById('eco-t-lang').value);document.getElementById('eco-t-restore').onclick=()=>window.__ecoRestoreOriginal();}}catch(e){}
})();
"""


def build_password_autofill_js(email, password):
    em, pw = json.dumps(email), json.dumps(password)
    return f"""
(function(){{
    window.__ecoSavedCredentials={{email:{em},password:{pw}}};
    function isVis(el){{try{{if(!el)return false;let s=getComputedStyle(el);if(s.display==='none'||s.visibility==='hidden'||s.opacity==='0')return false;let r=el.getBoundingClientRect();return !(r.width===0&&r.height===0&&document.activeElement!==el);}}catch(e){{return !!el;}}}}
    function setVal(el,val){{try{{el.focus();let d=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value');if(d&&d.set)d.set.call(el,val);else el.value=val;el.dispatchEvent(new InputEvent('input',{{bubbles:true,inputType:'insertText',data:val}}));el.dispatchEvent(new Event('change',{{bubbles:true}}));}}catch(e){{el.value=val;}}}}
    function findInput(sels,fb){{for(let s of sels){{try{{let el=document.querySelector(s);if(el&&isVis(el))return el;}}catch(e){{}}}}return fb?fb():null;}}
    function doFill(){{try{{
        let e=findInput(['#identifierId','input[name="identifier"]','input[type="email"]','input[autocomplete="email"]','input[autocomplete="username"]','input[name*="email" i]','input[name*="user" i]','input[id*="user" i]'],()=>[...document.querySelectorAll('input[type="text"],input:not([type])')].find(isVis));
        let p=findInput(['input[name="Passwd"]','#password','input[autocomplete="current-password"]','input[type="password"]'],()=>[...document.querySelectorAll('input[type="password"]')].find(isVis));
        let filled=false;
        if(e&&e.value!=={em}){{setVal(e,{em});filled=true;}}
        if(p&&!p.value){{setVal(p,{pw});filled=true;}}
        if(filled)console.log('ECO_PASS_FILLED::'+location.hostname);
        return filled;
    }}catch(err){{return false;}}}}
    window.__ecoPassTryFill=(e,p)=>{{window.__ecoSavedCredentials={{email:e,password:p}};doFill();}};
    [0,800,2000,4000,7000].forEach(ms=>setTimeout(doFill,ms));
    document.addEventListener('focusin',ev=>{{let t=ev.target;if(t&&(t.type==='password'||t.type==='email'||t.type==='text')&&window.__ecoSavedCredentials&&!t.value)doFill();}},true);
    try{{new MutationObserver(()=>{{if(window.__ecoSavedCredentials)doFill();}}).observe(document.documentElement,{{childList:true,subtree:true}});}}catch(e){{}}
}})();
"""


def apply_windows_gpu_preference(pref="high_performance"):
    if sys.platform != "win32" or reg is None:
        return False
    val = {"high_performance": 2, "power_saving": 1, "auto": 0}.get(
        str(pref).lower(), 2
    )
    try:
        key = reg.CreateKey(
            reg.HKEY_CURRENT_USER, r"Software\Microsoft\DirectX\UserGpuPreferences"
        )
        ok = False
        for exe in (
            sys.executable,
            "QtWebEngineProcess.exe",
            "python.exe",
            "pythonw.exe",
        ):
            if exe:
                try:
                    reg.SetValueEx(key, exe, 0, reg.REG_SZ, f"GpuPreference={val};")
                    ok = True
                except Exception:
                    pass
        reg.CloseKey(key)
        return ok
    except Exception:
        return False


def is_browser_registered():
    data = _read_json(os.path.join(get_app_data_folder(), "settings.json"), {})
    return (
        bool(data.get("registry_registered", False))
        if isinstance(data, dict)
        else False
    )


def set_browser_registered_flag(registered: bool):
    path = os.path.join(get_app_data_folder(), "settings.json")
    data = _read_json(path, {})
    if not isinstance(data, dict):
        data = {}
    data["registry_registered"] = registered
    _write_json(path, data)


def register_as_browser(force: bool = False):
    if sys.platform != "win32" or reg is None:
        return False
    if not force and is_browser_registered():
        return True
    cap = r"Software\EcoBrowser\Capabilities"
    if not force:
        try:
            with reg.OpenKey(reg.HKEY_CURRENT_USER, cap):
                set_browser_registered_flag(True)
                return True
        except Exception:
            pass
    app_path = (
        f'"{sys.executable}"'
        if getattr(sys, "frozen", False)
        else f'"{sys.executable}" "{os.path.abspath(__file__)}"'
    )
    try:
        with reg.CreateKey(reg.HKEY_CURRENT_USER, cap) as k:
            reg.SetValueEx(k, "ApplicationName", 0, reg.REG_SZ, "EcoBrowser")
            reg.SetValueEx(
                k,
                "ApplicationDescription",
                0,
                reg.REG_SZ,
                "Low-RAM browser with AdBlock & SafeShield.",
            )
        for sub, entries in (
            (
                f"{cap}\\URLAssociations",
                (("http", "EcoBrowserURL"), ("https", "EcoBrowserURL")),
            ),
            (
                f"{cap}\\FileAssociations",
                ((".html", "EcoBrowserHTML"), (".htm", "EcoBrowserHTML")),
            ),
            (
                r"Software\Classes\EcoBrowserURL\shell\open\command",
                (("", f'{app_path} "%1"'),),
            ),
            (
                r"Software\Classes\EcoBrowserHTML\shell\open\command",
                (("", f'{app_path} "%1"'),),
            ),
            (r"Software\RegisteredApplications", (("EcoBrowser", cap),)),
        ):
            with reg.CreateKey(reg.HKEY_CURRENT_USER, sub) as k:
                for name, val in entries:
                    reg.SetValueEx(k, name, 0, reg.REG_SZ, val)
        set_browser_registered_flag(True)
        return True
    except Exception:
        return False


def build_blocked_page_html(blocked_domain, reason="Security & Privacy Policy"):
    return (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
        f"body{{background:#121418;color:#f0f6fc;font-family:Segoe UI,sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}}"
        f".card{{background:#1e2229;padding:36px 44px;border-radius:16px;border:1px solid #30363d;text-align:center;max-width:440px}}"
        f"h1{{color:#f85149;font-size:22px;margin:0 0 12px}}p{{color:#8b949e;font-size:14px;margin-bottom:24px}}"
        f"a{{background:#238636;color:#fff;text-decoration:none;padding:10px 24px;border-radius:24px;font-weight:600;display:inline-block}}"
        f"</style></head><body><div class='card'><div>[Locked]</div><h1>Access Intercepted</h1>"
        f"<p>Navigation to <b>{blocked_domain}</b> was intercepted ({reason}).</p>"
        f"<a href='https://www.google.com'>Return to Safe Browsing</a></div></body></html>"
    )


class ContentBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        self.ad_block_enabled = True
        self.nude_block_enabled = True
        self.blocked_ad_count = 0
        self.blocked_nude_count = 0
        self.custom_ad_domains = []
        self.custom_adult_keywords = []
        self.allowlist = []

    def interceptRequest(self, info):
        try:
            if not self.ad_block_enabled and not self.nude_block_enabled:
                return
            url = info.requestUrl()
            url_str = url.toString()
            if not (url_str.startswith("http://") or url_str.startswith("https://")):
                return
            host = url.host().lower()
            if not host or "blocked.ecobrowser" in host:
                return
            if any(
                host == a.lower() or host.endswith("." + a.lower())
                for a in self.allowlist
            ):
                return
            if self.ad_block_enabled and any(
                ad.lower()
                and (
                    host == ad.lower()
                    or host.endswith("." + ad.lower())
                    or ad.lower() in host
                )
                for ad in AD_DOMAINS + self.custom_ad_domains
            ):
                info.block(True)
                self.blocked_ad_count += 1
                return
            if self.nude_block_enabled:
                if any(host == d or host.endswith("." + d) for d in ADULT_DOMAINS):
                    info.block(True)
                    self.blocked_nude_count += 1
                    return
                try:
                    is_main = info.resourceType() in (0, 1)
                except Exception:
                    is_main = True
                if is_main:
                    low = url_str.lower()
                    if "eco://newtab" not in low and any(
                        kw.lower() in low
                        for kw in ADULT_KEYWORDS + self.custom_adult_keywords
                        if kw
                    ):
                        info.block(True)
                        self.blocked_nude_count += 1
        except Exception as e:
            print(f"[Blocker] intercept error (safe): {e}")


class Userscript:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.name = self.filename
        self.namespace = ""
        self.version = "1.0"
        self.description = ""
        self.author = ""
        (
            self.matches,
            self.includes,
            self.excludes,
            self.exclude_matches,
            self.grants,
        ) = ([], [], [], [], [])
        self.run_at = "document-idle"
        self.enabled = True
        self.code = ""
        self.meta_block = ""
        self._parse()

    def _parse(self):
        try:
            with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
                self.code = f.read()
        except Exception:
            return
        m = re.search(
            r"//\s*==UserScript==.*?//\s*==/UserScript==", self.code, re.DOTALL
        )
        if not m:
            self.matches = ["*://*/*"]
            return
        self.meta_block = m.group(0)
        for line in self.meta_block.splitlines():
            line = line.strip()
            if line.startswith("//"):
                line = line[2:].strip()
            if not line.startswith("@"):
                continue
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            k, v = parts[0].lower().lstrip("@"), parts[1].strip()
            if k in ("name", "namespace", "version", "description", "author"):
                setattr(self, k, v)
            elif k == "match":
                self.matches.append(v)
            elif k == "include":
                self.includes.append(v)
            elif k == "exclude":
                self.excludes.append(v)
            elif k == "exclude-match":
                self.exclude_matches.append(v)
            elif k == "grant":
                self.grants.append(v)
            elif k == "run-at":
                self.run_at = v.lower()
        if not self.matches and not self.includes:
            self.matches = ["*://*/*"]

    def matches_url(self, url):
        if not url or url.startswith(("about:", "eco://", "data:")):
            return False
        if any(
            _userscript_url_matches(p, url)
            for p in self.excludes + self.exclude_matches
        ):
            return False
        rules = self.matches + self.includes
        return any(_userscript_url_matches(p, url) for p in rules)

    def get_injection_code(self):
        body = (
            self.code.replace(self.meta_block, "", 1) if self.meta_block else self.code
        )
        return (
            f"(function(){{try{{const __ecoScriptInfo={{name:{json.dumps(self.name)},"
            f"version:{json.dumps(self.version)},filename:{json.dumps(self.filename)}}};\n"
            f"{body}\n}}catch(e){{console.error('[EcoBrowser Userscript Error]',e);}}}})();"
        )


def _glob_to_regex(pattern):
    out = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            out.append(".*")
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                i += 1
        elif c in ".+^$()[]{}|\\":
            out.append("\\" + c)
        elif c == "?":
            out.append(".")
        else:
            out.append(c)
        i += 1
    return "".join(out)


def _userscript_url_matches(pattern, url):
    p = (pattern or "").strip()
    if not p:
        return False
    if p in ("<all_urls>", "*://*/*", "*"):
        return True
    try:
        if p.startswith("/") and p.endswith("/") and len(p) > 2:
            return bool(re.search(p[1:-1], url))
        if p.startswith("*://"):
            p = ".*://" + p[4:]
        return bool(re.search(_glob_to_regex(p), url, re.IGNORECASE))
    except Exception:
        return False


class UserscriptManager:
    def __init__(self, app_data_folder):
        self.folder = os.path.join(app_data_folder, "userscripts")
        os.makedirs(self.folder, exist_ok=True)
        self.state_file = os.path.join(app_data_folder, "userscripts_state.json")
        self.scripts = {}
        self.enabled_map = {}
        self._load_state()
        self.load_scripts()

    def _load_state(self):
        data = _read_json(self.state_file, {})
        self.enabled_map = data if isinstance(data, dict) else {}

    def _save_state(self):
        _write_json(self.state_file, self.enabled_map, indent=2)

    def load_scripts(self):
        self.scripts.clear()
        try:
            for fname in os.listdir(self.folder):
                fpath = os.path.join(self.folder, fname)
                if fname.lower().endswith(".user.js") and os.path.isfile(fpath):
                    us = Userscript(fpath)
                    us.enabled = bool(self.enabled_map.get(fname, us.enabled))
                    self.enabled_map[fname] = us.enabled
                    self.scripts[fname] = us
        except Exception as e:
            print(f"[UserscriptManager] load error: {e}")
        self._save_state()

    def get_all_scripts(self):
        return list(self.scripts.values())

    def get_matching_scripts(self, url):
        if not url:
            return []
        return sorted(
            (s for s in self.scripts.values() if s.enabled and s.matches_url(url)),
            key=lambda s: s.name.lower(),
        )

    def set_enabled(self, filename, enabled):
        if filename in self.scripts:
            self.scripts[filename].enabled = enabled
        self.enabled_map[filename] = enabled
        self._save_state()

    def _unique_dest(self, filename):
        dest = os.path.join(self.folder, filename)
        base, ext = os.path.splitext(dest)
        n = 1
        while os.path.exists(dest):
            dest = f"{base}_{n}{ext}"
            n += 1
        return dest

    def add_script_from_file(self, src_path):
        try:
            fname = os.path.basename(src_path)
            if not fname.lower().endswith(".js"):
                fname += ".user.js"
            dest = self._unique_dest(fname)
            shutil.copy2(src_path, dest)
            self.load_scripts()
            return os.path.basename(dest)
        except Exception:
            return None

    def add_script_from_code(self, code, filename="custom.user.js"):
        try:
            dest = self._unique_dest(filename)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(code)
            self.load_scripts()
            return os.path.basename(dest)
        except Exception:
            return None

    def delete_script(self, filename):
        try:
            fpath = os.path.join(self.folder, filename)
            if os.path.exists(fpath):
                os.remove(fpath)
            self.scripts.pop(filename, None)
            self.enabled_map.pop(filename, None)
            self._save_state()
            return True
        except Exception:
            return False

    def open_folder(self):
        try:
            if sys.platform == "win32":
                os.startfile(self.folder)
            else:
                subprocess.Popen(
                    ["open" if sys.platform == "darwin" else "xdg-open", self.folder]
                )
        except Exception:
            pass

    def build_injection_js(self, url):
        matching = self.get_matching_scripts(url)
        if not matching:
            return None
        parts = [USERSCRIPT_POLYFILL_JS]
        for s in matching:
            code = s.get_injection_code()
            if s.run_at == "document-start":
                parts.append(code)
            elif s.run_at == "document-body":
                parts.append(
                    f"if(document.body){{{code}}}else{{document.addEventListener('DOMContentLoaded',function(){{{code}}});}}"
                )
            else:
                parts.append(
                    f"(function(){{function r(){{{code}}}if(document.readyState!=='loading')setTimeout(r,1);else document.addEventListener('DOMContentLoaded',r);}})();"
                )
        return "\n".join(parts)


def _load_or_create_fernet_key(app_data_folder=None):
    try:
        from cryptography.fernet import Fernet  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "Fernet encryption requires 'cryptography'. Install: pip install cryptography"
        ) from e

    folder = app_data_folder or get_app_data_folder()
    os.makedirs(folder, exist_ok=True)
    key_path = os.path.join(folder, FERNET_KEY_FILENAME)

    if os.path.exists(key_path):
        with open(key_path, "r", encoding="utf-8") as kf:
            k = kf.read().strip()
        if k:
            try:
                Fernet(k.encode() if isinstance(k, str) else k)
                return k.encode() if isinstance(k, str) else k
            except Exception:
                pass

    new_key = Fernet.generate_key()
    try:
        with open(key_path, "w", encoding="utf-8") as kf:
            kf.write(new_key.decode())
        try:
            os.chmod(key_path, 0o600)
        except Exception:
            pass
        if sys.platform == "win32":
            try:
                ctypes.windll.kernel32.SetFileAttributesW(key_path, 2)
            except Exception:
                pass
    except Exception:
        pass
    return new_key


def _get_fernet(app_data_folder=None):
    from cryptography.fernet import Fernet  # type: ignore

    return Fernet(_load_or_create_fernet_key(app_data_folder))


def fernet_encrypt(plaintext, app_data_folder=None):
    if not plaintext:
        return ""
    return (
        _get_fernet(app_data_folder).encrypt(plaintext.encode("utf-8")).decode("utf-8")
    )


def _legacy_xor_decrypt(ciphertext, key):
    raw = base64.b64decode(ciphertext.encode())
    k = (key or "ecobrowser_default_key").encode()
    return bytes([b ^ k[i % len(k)] for i, b in enumerate(raw)]).decode()


def fernet_decrypt(token, app_data_folder=None, legacy_key=None):
    if not token:
        return ""
    try:
        return (
            _get_fernet(app_data_folder).decrypt(token.encode("utf-8")).decode("utf-8")
        )
    except Exception:
        pass
    try:
        key = legacy_key
        if key is None and app_data_folder:
            kp = os.path.join(app_data_folder, FERNET_KEY_FILENAME)
            if os.path.exists(kp):
                with open(kp, "r", encoding="utf-8") as kf:
                    key = kf.read().strip()
        return _legacy_xor_decrypt(token, key)
    except Exception:
        pass
    try:
        return base64.b64decode(token.encode()).decode()
    except Exception:
        return token


class PasswordManager:
    def __init__(self, app_data_folder):
        self.folder = app_data_folder
        self.file_path = os.path.join(app_data_folder, "passwords.json")
        self.key_path = os.path.join(app_data_folder, FERNET_KEY_FILENAME)
        self._key = _load_or_create_fernet_key(app_data_folder)
        self._fernet = _get_fernet(app_data_folder)
        self._has_fernet = True
        self._data = {}
        self._load()
        self._migrate_legacy_entries()

    def _encrypt(self, plaintext):
        return fernet_encrypt(plaintext, self.folder) if plaintext else ""

    def _decrypt(self, ciphertext):
        if not ciphertext:
            return ""
        lk = self._key.decode() if isinstance(self._key, bytes) else self._key
        return fernet_decrypt(ciphertext, self.folder, legacy_key=lk)

    def _is_fernet_token(self, value):
        return isinstance(value, str) and value.startswith("gAAAAA")

    def _migrate_legacy_entries(self):
        changed = False
        for entry in list(self._data.values()):
            stored = entry.get("password", "")
            if stored and not self._is_fernet_token(stored):
                try:
                    entry["password"] = self._encrypt(self._decrypt(stored))
                    changed = True
                except Exception:
                    pass
        if changed:
            self._save()

    def _load(self):
        data = _read_json(self.file_path, {})
        self._data = data if isinstance(data, dict) else {}

    def _save(self):
        _write_json(self.file_path, self._data, indent=2)

    def save_credential(self, host, email, password, origin="", href=""):
        host = (host or "").lower().strip()
        if not host or not password:
            return False
        existing = self._data.get(host, {})
        now_iso = datetime.now().isoformat()
        self._data[host] = {
            "host": host,
            "email": email,
            "username": email,
            "password": self._encrypt(password),
            "password_plain_len": len(password),
            "origin": origin or existing.get("origin", ""),
            "href": href or existing.get("href", ""),
            "updated": now_iso,
            "created": existing.get("created", now_iso),
        }
        self._save()
        return True

    def _build_cred(self, host, entry):
        try:
            return {
                "host": entry.get("host", host),
                "email": entry.get("email", ""),
                "username": entry.get("username", entry.get("email", "")),
                "password": self._decrypt(entry.get("password", "")),
                "origin": entry.get("origin", ""),
                "updated": entry.get("updated", ""),
            }
        except Exception:
            return None

    def get_credential(self, host):
        host = (host or "").lower().strip()
        if not host:
            return None
        if host in self._data:
            return self._build_cred(host, self._data[host])
        no_www = host[4:] if host.startswith("www.") else host
        if no_www in self._data:
            return self._build_cred(no_www, self._data[no_www])
        parts = host.split(".")
        base = ".".join(parts[-2:]) if len(parts) >= 2 else host
        if base in self._data:
            return self._build_cred(base, self._data[base])
        for saved_host in self._data:
            sp = saved_host.lower().split(".")
            if (".".join(sp[-2:]) if len(sp) >= 2 else saved_host.lower()) == base:
                return self._build_cred(saved_host, self._data[saved_host])
        return None

    def has_credential(self, host):
        return self.get_credential(host) is not None

    def get_all(self):
        out = []
        for host, entry in self._data.items():
            try:
                out.append(
                    {
                        "host": host,
                        "email": entry.get("email", ""),
                        "password": self._decrypt(entry.get("password", "")),
                        "origin": entry.get("origin", ""),
                        "updated": entry.get("updated", ""),
                        "created": entry.get("created", ""),
                    }
                )
            except Exception:
                pass
        return sorted(out, key=lambda x: x["host"])

    def delete(self, host):
        host = (host or "").lower().strip()
        if host in self._data:
            del self._data[host]
            self._save()
            return True
        return False

    def count(self):
        return len(self._data)


def _dialog_header(layout, title, subtitle=None, size=12):
    lbl = QLabel(title)
    f = lbl.font()
    f.setPointSize(size)
    f.setBold(True)
    lbl.setFont(f)
    layout.addWidget(lbl)
    if subtitle:
        sub = QLabel(subtitle)
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #8b949e; font-size: 9pt;")
        layout.addWidget(sub)
    return lbl


def _clear_layout_except_stretch(layout):
    while layout.count() > 1:
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()


class PasswordManagerDialog(QDialog):
    def __init__(self, password_manager, parent=None):
        super().__init__(parent)
        self.password_manager = password_manager
        self.setWindowTitle("Password Manager — EcoBrowser")
        self.resize(720, 520)
        self._revealed = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        _dialog_header(
            layout,
            "Saved Passwords",
            "EcoBrowser detects login forms and saves credentials encrypted with Fernet.",
        )

        top = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by site or email...")
        self.search_input.setFixedHeight(32)
        self.search_input.textChanged.connect(self.refresh)
        top.addWidget(self.search_input, 1)

        for attr, label, cb in (
            ("btn_export", "Export", self.export_passwords),
            ("btn_clear_all", "Clear All", self.clear_all),
            ("btn_autofill", "Autofill Current Page", self._autofill_current),
        ):
            btn = QPushButton(label)
            btn.clicked.connect(cb)
            setattr(self, attr, btn)
            top.addWidget(btn)
        layout.addLayout(top)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.container_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.container_widget)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()
        self.scroll.setWidget(self.container_widget)
        layout.addWidget(self.scroll, 1)

        bottom = QHBoxLayout()
        bottom.addStretch()
        self.btn_close = QPushButton("Done")
        self.btn_close.clicked.connect(self.accept)
        bottom.addWidget(self.btn_close)
        layout.addLayout(bottom)
        self.refresh()

    def _autofill_current(self):
        parent = self.parent()
        if parent and hasattr(parent, "force_autofill_current_page"):
            parent.force_autofill_current_page()
            QMessageBox.information(self, "Autofill", "Tried to autofill current page.")
        else:
            QMessageBox.warning(self, "Autofill", "Could not find main window.")

    def refresh(self):
        _clear_layout_except_stretch(self.cards_layout)
        q = self.search_input.text().strip().lower()
        filtered = [
            c
            for c in self.password_manager.get_all()
            if not q or q in c["host"].lower() or q in c["email"].lower()
        ]
        if not filtered:
            lbl = QLabel("No matching passwords" if q else "No saved passwords")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #8b949e; padding: 30px;")
            self.cards_layout.insertWidget(0, lbl)
            return
        for cred in filtered:
            self.cards_layout.insertWidget(
                self.cards_layout.count() - 1, self._create_card(cred)
            )

    def _create_card(self, cred):
        host, email, password = cred["host"], cred["email"], cred["password"]
        updated = cred.get("updated", "")[:19].replace("T", " ")
        frame = QFrame()
        frame.setObjectName("passCard")
        frame.setStyleSheet(
            "QFrame#passCard{background:rgba(255,255,255,0.04);border:1px solid #30363d;border-radius:10px}QFrame#passCard:hover{border-color:#58a6ff}"
        )
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(14, 12, 14, 12)
        vbox.setSpacing(6)

        top = QHBoxLayout()
        top.addWidget(QLabel("[Key]"))
        hl = QLabel(f"<b>{host}</b>")
        hl.setTextFormat(Qt.TextFormat.RichText)
        top.addWidget(hl, 1)
        dl = QLabel(updated)
        dl.setStyleSheet("color: #8b949e; font-size: 8pt;")
        top.addWidget(dl)
        vbox.addLayout(top)

        ro_style = "background:rgba(0,0,0,0.2);border:1px solid #30363d;border-radius:6px;padding:4px 8px;"
        erow = QHBoxLayout()
        erow.addWidget(QLabel("Email:"))
        ev = QLineEdit(email)
        ev.setReadOnly(True)
        ev.setStyleSheet(ro_style)
        erow.addWidget(ev, 1)
        vbox.addLayout(erow)

        prow = QHBoxLayout()
        prow.addWidget(QLabel("Password:"))
        rev = self._revealed.get(host, False)
        pv = QLineEdit(password if rev else "•" * min(len(password), 16))
        pv.setReadOnly(True)
        pv.setEchoMode(
            QLineEdit.EchoMode.Normal if rev else QLineEdit.EchoMode.Password
        )
        pv.setStyleSheet(ro_style)
        prow.addWidget(pv, 1)
        bs = QPushButton("Hide" if rev else "Show")
        bs.setFixedWidth(60)
        bs.clicked.connect(lambda _, h=host: self.toggle_reveal(h))
        prow.addWidget(bs)
        vbox.addLayout(prow)

        act = QHBoxLayout()
        act.addStretch()
        for text, cb, style in (
            (
                "Copy Email",
                lambda _, e=email: QApplication.clipboard().setText(e),
                None,
            ),
            (
                "Copy Pass",
                lambda _, p=password: QApplication.clipboard().setText(p),
                None,
            ),
            ("Delete", lambda _, h=host: self.delete_entry(h), "color:#f85149;"),
        ):
            b = QPushButton(text)
            if style:
                b.setStyleSheet(style)
            b.clicked.connect(cb)
            act.addWidget(b)
        vbox.addLayout(act)
        return frame

    def toggle_reveal(self, host):
        self._revealed[host] = not self._revealed.get(host, False)
        self.refresh()

    def delete_entry(self, host):
        if (
            QMessageBox.question(
                self, "Delete Password", f"Delete saved password for {host}?"
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.password_manager.delete(host)
            self._revealed.pop(host, None)
            self.refresh()

    def clear_all(self):
        if (
            QMessageBox.warning(
                self,
                "Clear All Passwords",
                "Delete ALL saved passwords?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            for cred in self.password_manager.get_all():
                self.password_manager.delete(cred["host"])
            self._revealed.clear()
            self.refresh()

    def export_passwords(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Passwords",
            os.path.join(os.path.expanduser("~"), "ecobrowser_passwords_export.json"),
            "JSON Files (*.json)",
        )
        if path:
            data = self.password_manager.get_all()
            if _write_json(path, data, indent=2):
                QMessageBox.information(
                    self, "Exported", f"Exported {len(data)} passwords to {path}"
                )
            else:
                QMessageBox.critical(
                    self, "Export Failed", "Could not write export file."
                )


class EcoWebEnginePage(QWebEnginePage):
    def __init__(self, profile, browser_window, parent=None):
        super().__init__(profile, parent)
        self.browser_window = browser_window
        self._is_showing_blocked_page = False
        self._last_blocked_url = ""

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        if isinstance(message, str):
            if message.startswith("ECO_PASS_SAVE::"):
                try:
                    data = json.loads(message[len("ECO_PASS_SAVE::") :])
                    QTimer.singleShot(
                        0,
                        lambda d=data: self.browser_window.handle_password_save_request(
                            d
                        ),
                    )
                except Exception as e:
                    print(f"[PasswordManager] parse save error: {e}")
                return
            if message.startswith("ECO_PASS_FILLED::"):
                print(
                    f"[PasswordManager] Autofilled for {message[len('ECO_PASS_FILLED::'):].strip()}"
                )
                return
        try:
            super().javaScriptConsoleMessage(level, message, lineNumber, sourceID)
        except Exception:
            pass

    def createWindow(self, _window_type):
        v = self.browser_window.add_new_tab("about:blank")
        return v.page() if v is not None and hasattr(v, "page") else None

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        try:
            url_str = url.toString()
            if url_str.startswith(
                ("data:", "about:", "eco://", "qrc:", "file:", "blob:")
            ):
                return super().acceptNavigationRequest(url, nav_type, is_main_frame)
            if self._is_showing_blocked_page:
                if url_str == self._last_blocked_url:
                    return False
                self._is_showing_blocked_page = False
            if not url_str.startswith(("http://", "https://")):
                return super().acceptNavigationRequest(url, nav_type, is_main_frame)

            interceptor = getattr(self.browser_window, "interceptor", None)
            host = url.host().lower()
            lower = url_str.lower()
            allowlist = getattr(interceptor, "allowlist", []) if interceptor else []
            if any(
                host == a.lower().strip() or host.endswith("." + a.lower().strip())
                for a in allowlist
                if a.strip()
            ):
                return super().acceptNavigationRequest(url, nav_type, is_main_frame)

            level = (
                self.browser_window._get_blocking_level()
                if hasattr(self.browser_window, "_get_blocking_level")
                else 2
            )
            if level == 0:
                return super().acceptNavigationRequest(url, nav_type, is_main_frame)

            if (
                level >= 2
                and getattr(interceptor, "nude_block_enabled", True)
                and "blocked.ecobrowser" not in host
                and "eco://newtab" not in lower
            ):
                is_host = any(
                    host == d or host.endswith("." + d) or d in host
                    for d in ADULT_DOMAINS
                )
                custom_kw = (
                    getattr(interceptor, "custom_adult_keywords", [])
                    if interceptor
                    else []
                )
                matched_kw = next(
                    (
                        kw
                        for kw in ADULT_KEYWORDS + custom_kw
                        if kw and kw.lower() in lower
                    ),
                    "",
                )
                if is_host or matched_kw:
                    reason = "Adult Domain" if is_host else f"Keyword '{matched_kw}'"
                    html = build_blocked_page_html(
                        host or url_str[:80], f"SafeShield: {reason} Blocked"
                    )
                    self._last_blocked_url = url_str
                    QTimer.singleShot(
                        0, lambda h=html, u=url: self._safe_set_blocked_html(h, u)
                    )
                    return False

            if getattr(interceptor, "ad_block_enabled", True) and any(
                host == ad or host.endswith("." + ad) for ad in AD_DOMAINS
            ):
                return False

            if is_main_frame and getattr(self.browser_window, "settings", None):
                if (
                    self.browser_window.settings.get("https_only_mode", False)
                    and url_str.startswith("http://")
                    and host not in ("localhost", "127.0.0.1")
                ):
                    upgraded = "https://" + url_str[len("http://") :]
                    if self.browser_window.settings.get("strip_tracking_params", True):
                        upgraded = strip_tracking_params(upgraded)
                    QTimer.singleShot(
                        0,
                        lambda u=upgraded: (
                            self.setUrl(QUrl(u)) if not is_view_deleted(self) else None
                        ),
                    )
                    return False
                if self.browser_window.settings.get("strip_tracking_params", True):
                    cleaned = strip_tracking_params(url_str)
                    if cleaned != url_str:
                        QTimer.singleShot(
                            0,
                            lambda u=cleaned: (
                                self.setUrl(QUrl(u))
                                if not is_view_deleted(self)
                                else None
                            ),
                        )
                        return False

            return super().acceptNavigationRequest(url, nav_type, is_main_frame)
        except Exception:
            return super().acceptNavigationRequest(url, nav_type, is_main_frame)

    def _safe_set_blocked_html(self, html, base_url):
        try:
            if is_view_deleted(self) or (
                self._is_showing_blocked_page
                and base_url.toString() == self._last_blocked_url
            ):
                return
            self._is_showing_blocked_page = True
            self.setHtml(html, QUrl("https://blocked.ecobrowser/"))
            QTimer.singleShot(
                2000, lambda: setattr(self, "_is_showing_blocked_page", False)
            )
        except Exception:
            self._is_showing_blocked_page = False


class BookmarkButton(QPushButton):
    def __init__(self, title, url, icon, browser_window):
        super().__init__(title)
        self.bookmark_url = url
        self.browser_window = browser_window
        if icon and not icon.isNull():
            self.setIcon(icon)
            self.setIconSize(QSize(14, 14))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.clicked.connect(
            lambda: self.browser_window.navigate_to_bookmark(self.bookmark_url)
        )

    def show_context_menu(self, pos):
        menu = QMenu(self)
        delete_action = menu.addAction("Delete Bookmark")
        if menu.exec(self.mapToGlobal(pos)) == delete_action:
            self.browser_window.delete_bookmark_by_url(self.bookmark_url)


class CrashProofManager:
    def __init__(self, browser_window):
        self.browser_window = browser_window
        self.crash_count = {}
        self.last_crash_time = {}

    def handle_crash(self, view, status, code):
        try:
            if is_view_deleted(view):
                return
            vid, now = id(view), time.time()
            self.crash_count[vid] = self.crash_count.get(vid, 0) + 1
            prev = self.last_crash_time.get(vid, now)
            self.last_crash_time[vid] = now
            if self.crash_count[vid] >= 3 and now - prev < 30:
                self.show_crash_recovery_page(view)
                return
            QTimer.singleShot(1500, lambda v=view: self.safe_reload(v))
        except Exception as e:
            print(f"[CrashProof] handle error: {e}")

    def safe_reload(self, view):
        try:
            if not is_view_deleted(view) and any(
                self.browser_window.stack.widget(i) == view
                for i in range(self.browser_window.stack.count())
            ):
                view.reload()
        except Exception:
            pass

    def show_crash_recovery_page(self, view):
        try:
            if is_view_deleted(view):
                return
            view.setHtml(
                "<!DOCTYPE html><html><body style='background:#0e1116;color:#e6edf3;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0'>"
                "<div style='background:#1c212b;padding:40px;border-radius:16px;text-align:center'><h1 style='color:#f85149'>Tab Crashed</h1>"
                "<p>This tab crashed multiple times.</p><button onclick='location.reload()' style='background:#238636;color:#fff;border:0;padding:10px 20px;border-radius:8px;cursor:pointer;margin:6px'>Try Again</button>"
                "<button onclick=\"location.href='https://www.google.com'\" style='background:#30363d;color:#fff;border:0;padding:10px 20px;border-radius:8px;cursor:pointer'>Go to Google</button></div></body></html>",
                QUrl("https://crashed.ecobrowser/"),
            )
        except Exception:
            pass


def build_new_tab_page_html(settings, search_engine_name="Google"):
    bg_type = settings.get("newtab_background_type", "gradient")
    bg_image = settings.get("newtab_background_image", "")
    quicklinks = [
        {"title": ql.get("title", "Link")[:18], "url": ql.get("url", "#")}
        for ql in settings.get("newtab_quicklinks", [])[:16]
    ]
    accent = settings.get("custom_accent", "#58a6ff")
    giza_default_url = (
        "https://images.unsplash.com/photo-1503177119275-0aa32b3a9368?w=1920&q=80"
    )
    if bg_type == "image" and bg_image:
        initial_wp = f"file:///{bg_image.replace(chr(92), '/')}"
    else:
        initial_wp = giza_default_url
    bg_css = "background:linear-gradient(165deg,#1b1824 0%,#3d2a26 42%,#8b5a2b 78%,#1e1612 100%);"
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>New Tab</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}html,body{{height:100%;overflow:hidden}}
body{{{bg_css}color:#f0f6fc;font-family:Inter,Segoe UI,sans-serif;display:flex;flex-direction:column;position:relative}}
#wallpaper{{position:fixed;inset:0;background-size:cover;background-position:center;z-index:-2;opacity:1;background-image:url('{initial_wp}');transition:opacity .35s ease}}
.scrim{{position:fixed;inset:0;z-index:-1;background:radial-gradient(circle at 50% 42%,rgba(10,12,18,.34) 0%,rgba(10,12,18,.68) 100%)}}
.center{{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:22px;padding:24px;z-index:10}}
.time{{font-size:78px;font-weight:300;letter-spacing:-3px;text-shadow:0 4px 24px rgba(0,0,0,.55)}}
.date{{font-size:15px;opacity:.88;text-shadow:0 2px 10px rgba(0,0,0,.5)}}
.search-wrap{{width:100%;max-width:580px;position:relative}}
.search-box{{display:flex;align-items:center;padding:6px 8px 6px 14px;background:rgba(18,20,28,.62);backdrop-filter:blur(22px);border:1px solid rgba(255,255,255,.22);border-radius:30px;box-shadow:0 12px 32px rgba(0,0,0,.35)}}
.search-box:focus-within{{border-color:{accent};background:rgba(18,20,28,.78)}}
.search-box input{{flex:1;background:transparent;border:0;outline:0;color:#fff;font-size:15.5px;padding:10px 4px}}
.search-box input::placeholder{{color:rgba(255,255,255,.65)}}
.engine-icon{{width:34px;height:34px;border-radius:50%;background:#fff;color:#111;display:flex;align-items:center;justify-content:center;font-weight:700;margin-right:10px;cursor:pointer;flex-shrink:0}}
.engine-dropdown{{position:absolute;top:54px;left:0;background:rgba(22,25,34,.96);border:1px solid rgba(255,255,255,.14);border-radius:14px;padding:6px;display:none;flex-direction:column;gap:2px;z-index:30;min-width:150px;box-shadow:0 12px 28px rgba(0,0,0,.45)}}
.engine-dropdown.show{{display:flex}}.engine-option{{padding:8px 12px;border-radius:8px;cursor:pointer;font-size:13px}}.engine-option:hover{{background:rgba(255,255,255,.12)}}
.search-btn{{background:{accent};color:#fff;border:0;border-radius:22px;padding:10px 22px;font-weight:600;cursor:pointer;font-size:14px}}
.quicklinks{{display:grid;grid-template-columns:repeat(auto-fill,88px);gap:14px;max-width:600px;width:100%;justify-content:center;margin-top:4px}}
.ql{{display:flex;flex-direction:column;align-items:center;gap:8px;cursor:pointer;position:relative;padding:6px;border-radius:14px;transition:background .15s}}
.ql:hover{{background:rgba(255,255,255,.10)}}
.ql-icon{{width:54px;height:54px;border-radius:16px;background:rgba(18,20,28,.62);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;color:#fff;font-size:20px;overflow:hidden}}
.ql-icon img{{width:28px;height:28px;border-radius:6px}}.ql-title{{font-size:11.5px;color:rgba(255,255,255,.92);max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-shadow:0 1px 4px rgba(0,0,0,.6)}}
.ql-remove{{position:absolute;top:2px;right:6px;width:18px;height:18px;background:rgba(0,0,0,.78);border-radius:50%;display:none;align-items:center;justify-content:center;font-size:10px;color:#fff}}
.ql:hover .ql-remove{{display:flex}}
#wallpaperBtn{{position:fixed;bottom:20px;right:20px;background:rgba(18,20,28,.65);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.2);border-radius:22px;padding:9px 16px;color:#fff;cursor:pointer;z-index:50;font-size:13px}}
#wallpaperBtn:hover{{background:rgba(18,20,28,.85)}}
#wallpaperPanel{{position:fixed;bottom:68px;right:20px;width:330px;max-height:72vh;overflow-y:auto;background:rgba(18,20,28,.96);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,.14);border-radius:18px;padding:18px;z-index:60;display:none;flex-direction:column;gap:12px;box-shadow:0 16px 40px rgba(0,0,0,.5)}}
#wallpaperPanel.show{{display:flex}}.wp-presets{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}.wp-preset{{height:58px;border-radius:8px;background-size:cover;background-position:center;cursor:pointer;border:1px solid rgba(255,255,255,.15)}}
.wp-preset:hover{{border-color:{accent}}}
.wp-input{{width:100%;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);border-radius:8px;padding:8px 10px;color:#fff;font-size:13px;outline:0}}.wp-btn{{background:{accent};color:#fff;border:0;border-radius:8px;padding:8px 14px;cursor:pointer;font-size:13px;font-weight:600}}
.ql-modal-bg{{position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;align-items:center;justify-content:center;z-index:80}}
.ql-modal-bg.show{{display:flex}}
.ql-modal{{width:340px;background:#181b24;border:1px solid rgba(255,255,255,.14);border-radius:16px;padding:20px;display:flex;flex-direction:column;gap:12px;box-shadow:0 20px 50px rgba(0,0,0,.6)}}
</style></head><body><div id="wallpaper"></div><div class="scrim"></div><div class="center">
<div class="time" id="clock">--:--</div><div class="date" id="date"></div>
<div class="search-wrap"><div class="search-box"><div class="engine-icon" id="engineIcon" title="Switch search engine" onclick="event.stopPropagation();document.getElementById('engineDropdown').classList.toggle('show')">{search_engine_name[0]}</div>
<div class="engine-dropdown" id="engineDropdown">
<div class="engine-option" data-engine="Google" data-icon="G" data-url="https://www.google.com/search?q=">Google</div>
<div class="engine-option" data-engine="Bing" data-icon="B" data-url="https://www.bing.com/search?q=">Bing</div>
<div class="engine-option" data-engine="DuckDuckGo" data-icon="D" data-url="https://duckduckgo.com/?q=">DuckDuckGo</div>
<div class="engine-option" data-engine="Brave" data-icon="Br" data-url="https://search.brave.com/search?q=">Brave</div>
<div class="engine-option" data-engine="Yahoo" data-icon="Y" data-url="https://search.yahoo.com/search?p=">Yahoo</div>
<div class="engine-option" data-engine="Ecosia" data-icon="EC" data-url="https://www.ecosia.org/search?q=">Ecosia</div>
</div><input id="searchInput" type="text" placeholder="Search {search_engine_name} or enter web address..." autofocus autocomplete="off"><button class="search-btn" id="searchBtn">Search</button></div></div>
<div class="quicklinks" id="quicklinks"></div></div>
<button id="wallpaperBtn" onclick="event.stopPropagation();document.getElementById('wallpaperPanel').classList.toggle('show')">Wallpaper</button>
<div id="wallpaperPanel" onclick="event.stopPropagation()"><div style="display:flex;justify-content:space-between;align-items:center"><b>Customize Wallpaper</b><button onclick="document.getElementById('wallpaperPanel').classList.remove('show')" style="background:none;border:0;color:#fff;cursor:pointer;font-size:15px">✕</button></div>
<input type="file" id="wallpaperUpload" accept="image/*" class="wp-input"><div style="display:flex;gap:8px"><input id="wallpaperUrlInput" class="wp-input" placeholder="Paste image URL..."><button class="wp-btn" onclick="applyUrlWallpaper()">Apply</button></div>
<div class="wp-presets" id="wpPresets"></div><div style="display:flex;gap:8px"><button class="wp-btn" style="flex:1;background:rgba(255,255,255,.15)" onclick="resetWallpaper()">Giza Default</button><button class="wp-btn" style="flex:1;background:rgba(255,255,255,.15)" onclick="clearWallpaper()">Clear</button></div></div>
<div id="qlModalBg" class="ql-modal-bg" onclick="closeQlModal()"><div class="ql-modal" onclick="event.stopPropagation()">
<b>Add Shortcut</b>
<input id="qlTitleInput" class="wp-input" placeholder="Name (e.g. Wikipedia)">
<input id="qlUrlInput" class="wp-input" placeholder="Address (e.g. wikipedia.org)">
<div style="display:flex;gap:8px;justify-content:flex-end"><button class="wp-btn" style="background:rgba(255,255,255,.14)" onclick="closeQlModal()">Cancel</button><button class="wp-btn" onclick="saveQlModal()">Add</button></div>
</div></div>
<script>
const DEFAULT_GIZA='{giza_default_url}';
const starterLinks=[{{title:'Google',url:'https://www.google.com'}},{{title:'YouTube',url:'https://www.youtube.com'}},{{title:'Wikipedia',url:'https://www.wikipedia.org'}},{{title:'GitHub',url:'https://github.com'}}];
let currentEngine={{name:"{search_engine_name}",icon:"{search_engine_name[0]}",url:"{SEARCH_ENGINES.get(search_engine_name, SEARCH_ENGINES['Google'])['query_url']}"}},quicklinksData={json.dumps(quicklinks)};
function updateClock(){{const n=new Date();let h=n.getHours(),m=String(n.getMinutes()).padStart(2,'0'),ap=h>=12?'PM':'AM';h=h%12||12;clock.textContent=h+':'+m+' '+ap;date.textContent=n.toLocaleDateString([],{{weekday:'long',month:'long',day:'numeric'}});}}
updateClock();setInterval(updateClock,1000);
const presets=[DEFAULT_GIZA,'https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/All_Gizah_Pyramids.jpg/1920px-All_Gizah_Pyramids.jpg','https://images.unsplash.com/photo-1539650116574-8efeb43e2750?w=1920&q=80','https://images.unsplash.com/photo-1572252009286-268acec5ca0a?w=1920&q=80','https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=80','https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1920&q=80'];
presets.forEach(u=>{{let d=document.createElement('div');d.className='wp-preset';d.style.backgroundImage=`url('${{u}}')`;d.onclick=()=>setWallpaper(u);wpPresets.appendChild(d);}});
function setWallpaper(u){{wallpaper.style.backgroundImage=`url('${{u}}')`;wallpaper.style.opacity='1';try{{localStorage.setItem('eco_wallpaper',u);}}catch(e){{}}}}
function applyUrlWallpaper(){{let u=wallpaperUrlInput.value.trim();if(u)setWallpaper(u);}}
function resetWallpaper(){{setWallpaper(DEFAULT_GIZA);}}
function clearWallpaper(){{wallpaper.style.backgroundImage='none';wallpaper.style.opacity='0';try{{localStorage.removeItem('eco_wallpaper');}}catch(e){{}}}}
try{{let s=localStorage.getItem('eco_wallpaper');if(s)wallpaper.style.backgroundImage=`url('${{s}}')`;}}catch(e){{}}
wallpaperUpload.onchange=e=>{{let f=e.target.files[0];if(!f||f.size>8e6)return;let r=new FileReader();r.onload=ev=>setWallpaper(ev.target.result);r.readAsDataURL(f);}};
document.querySelectorAll('.engine-option').forEach(o=>o.onclick=()=>{{currentEngine={{name:o.dataset.engine,icon:o.dataset.icon,url:o.dataset.url}};engineIcon.textContent=currentEngine.icon;searchInput.placeholder='Search '+currentEngine.name+' or enter web address...';engineDropdown.classList.remove('show');}});
document.addEventListener('click',()=>{{engineDropdown.classList.remove('show');wallpaperPanel.classList.remove('show');}});
document.addEventListener('keydown',e=>{{if(e.key==='Escape'){{engineDropdown.classList.remove('show');wallpaperPanel.classList.remove('show');closeQlModal();}}}});
function doSearch(){{const q=searchInput.value.trim();if(!q)return;location.href=(q.startsWith('http')||(q.includes('.')&&!q.includes(' ')))?(q.startsWith('http')?q:'https://'+q):currentEngine.url+encodeURIComponent(q);}}
searchInput.onkeydown=e=>{{if(e.key==='Enter')doSearch();}};searchBtn.onclick=doSearch;
function getLinks(){{let saved=localStorage.getItem('eco_quicklinks');if(saved!==null)return JSON.parse(saved);return quicklinksData.length?quicklinksData:starterLinks;}}
function renderQuicklinks(){{quicklinks.innerHTML='';let links=getLinks();links.forEach((l,i)=>{{let el=document.createElement('div');el.className='ql';let dom='';try{{dom=new URL(l.url).hostname;}}catch(e){{}}el.innerHTML=`<div class="ql-remove" onclick="event.stopPropagation();removeQuicklink(${{i}})">✕</div><div class="ql-icon"><img src="https://icons.duckduckgo.com/ip3/${{dom}}.ico" onerror="this.style.display='none';this.nextSibling.style.display='flex'"><span style="display:none">${{(l.title||'?')[0].toUpperCase()}}</span></div><div class="ql-title">${{l.title}}</div>`;el.onclick=()=>location.href=l.url;quicklinks.appendChild(el);}});let add=document.createElement('div');add.className='ql';add.innerHTML='<div class="ql-icon">+</div><div class="ql-title">Add</div>';add.onclick=addQuicklink;quicklinks.appendChild(add);}}
function addQuicklink(){{qlTitleInput.value='';qlUrlInput.value='';qlModalBg.classList.add('show');setTimeout(()=>qlTitleInput.focus(),30);}}
function closeQlModal(){{qlModalBg.classList.remove('show');}}
function saveQlModal(){{let u=qlUrlInput.value.trim();if(!u)return;if(!u.startsWith('http'))u='https://'+u;let t=qlTitleInput.value.trim()||u.replace(/^https?:\\/\\/(www\\.)?/,'').split('/')[0];let links=getLinks().slice();links.push({{title:t.slice(0,18),url:u}});localStorage.setItem('eco_quicklinks',JSON.stringify(links));closeQlModal();renderQuicklinks();}}
qlUrlInput.onkeydown=e=>{{if(e.key==='Enter')saveQlModal();}};
function removeQuicklink(i){{let links=getLinks().slice();links.splice(i,1);localStorage.setItem('eco_quicklinks',JSON.stringify(links));renderQuicklinks();}}
renderQuicklinks();
</script></body></html>"""


_DANGEROUS_DOUBLE_EXT_RE = re.compile(
    r"\.(pdf|docx?|xlsx?|pptx?|txt|rtf|jpe?g|png|gif|webp|mp3|mp4|mov|zip|rar|7z)\.(exe|scr|pif|bat|cmd|com|vbs|vbe|js|jse|hta|wsf|wsh|ps1|msi|lnk)$",
    re.IGNORECASE,
)
_EXEC_EXTS = {
    ".exe",
    ".msi",
    ".msix",
    ".appx",
    ".bat",
    ".cmd",
    ".ps1",
    ".vbs",
    ".vbe",
    ".js",
    ".jse",
    ".hta",
    ".scr",
    ".pif",
    ".com",
    ".wsf",
    ".wsh",
    ".lnk",
    ".reg",
    ".dll",
    ".sys",
    ".jar",
    ".apk",
    ".dmg",
    ".pkg",
    ".deb",
    ".rpm",
}
_DOC_MEDIA_EXTS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".txt",
    ".csv",
    ".json",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".mp3",
    ".mp4",
    ".wav",
}
_SCRIPT_EXTS = {
    ".ps1",
    ".bat",
    ".cmd",
    ".vbs",
    ".vbe",
    ".js",
    ".jse",
    ".hta",
    ".wsf",
    ".sh",
    ".py",
}
_EICAR_BYTES = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
_DROPPER_PATTERNS = [
    re.compile(
        r"powershell[^\n]{0,80}(-enc|-encodedcommand|iex\b|invoke-expression|downloadstring)",
        re.I,
    ),
    re.compile(r"certutil[^\n]{0,80}(-urlcache|-decode)", re.I),
    re.compile(r"bitsadmin[^\n]{0,80}/transfer", re.I),
    re.compile(r"mshta\s+https?://", re.I),
    re.compile(r"regsvr32[^\n]{0,80}/i:https?://", re.I),
    re.compile(r"(curl|wget)\s+https?://[^\n]{0,120}\|\s*(sh|bash|python)", re.I),
    re.compile(r"wscript\.shell|shell\.application|adodb\.stream", re.I),
]


def _find_windows_defender_cli():
    if sys.platform != "win32":
        return None
    candidates = []
    prog_data = os.environ.get("ProgramData", r"C:\ProgramData")
    plat_dir = os.path.join(prog_data, "Microsoft", "Windows Defender", "Platform")
    if os.path.isdir(plat_dir):
        try:
            versions = sorted(os.listdir(plat_dir), reverse=True)
            for v in versions:
                p = os.path.join(plat_dir, v, "MpCmdRun.exe")
                if os.path.isfile(p):
                    candidates.append(p)
        except Exception:
            pass
    prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    candidates.append(os.path.join(prog_files, "Windows Defender", "MpCmdRun.exe"))
    return next((c for c in candidates if os.path.isfile(c)), None)


def scan_file_safety(file_path, source_url=""):
    details = []
    status = "safe"
    av_engine = "Heuristic + Signature Guard"
    sha256_hex = ""

    if not file_path or not os.path.isfile(file_path):
        return {
            "status": "caution",
            "summary": "File no longer exists on disk.",
            "details": ["Missing file"],
            "sha256": "",
            "av_engine": av_engine,
        }

    fname = os.path.basename(file_path)
    ext = os.path.splitext(fname)[1].lower()

    # 1. Compute SHA-256 and read header / preview chunk
    h = hashlib.sha256()
    header = b""
    sample = b""
    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                if not header:
                    header = chunk[:64]
                if len(sample) < 1024 * 1024:
                    sample += chunk[: (1024 * 1024 - len(sample))]
                h.update(chunk)
        sha256_hex = h.hexdigest()
    except Exception as e:
        return {
            "status": "caution",
            "summary": f"Could not read file: {e}",
            "details": [str(e)],
            "sha256": "",
            "av_engine": av_engine,
        }

    # 2. EICAR test virus signature
    if _EICAR_BYTES in sample:
        status = "dangerous"
        details.append("Matched EICAR standard antivirus test signature.")

    # 3. Double-extension spoofing (e.g. invoice.pdf.exe)
    if _DANGEROUS_DOUBLE_EXT_RE.search(fname):
        status = "dangerous"
        details.append(f"Double-extension spoofing detected in '{fname}'.")

    # 4. File magic-byte spoofing (executable disguised as document/media)
    if ext in _DOC_MEDIA_EXTS:
        if header.startswith(b"MZ"):
            status = "dangerous"
            details.append(
                f"Disguised Windows PE executable (MZ header) inside '{ext}' file."
            )
        elif header.startswith(b"\x7fELF"):
            status = "dangerous"
            details.append(f"Disguised ELF executable inside '{ext}' file.")
        elif header.startswith(b"L\x00\x00\x00\x01\x14\x02\x00"):
            status = "dangerous"
            details.append(
                f"Disguised Windows Shortcut (.lnk) payload inside '{ext}' file."
            )

    # 5. Script dropper / obfuscation heuristics
    if ext in _SCRIPT_EXTS and sample:
        text_sample = sample.decode("utf-8", errors="ignore")
        hits = sum(1 for pat in _DROPPER_PATTERNS if pat.search(text_sample))
        if hits > 0:
            status = "dangerous"
            details.append(
                f"Matched {hits} high-risk script downloader/dropper pattern(s)."
            )

    # 6. Archive payload inspection (.zip)
    if ext == ".zip":
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                names = zf.namelist()[:200]
                spoofed = [n for n in names if _DANGEROUS_DOUBLE_EXT_RE.search(n)]
                execs = [
                    n for n in names if os.path.splitext(n)[1].lower() in _EXEC_EXTS
                ]
                if spoofed:
                    status = "dangerous"
                    details.append(
                        f"Archive contains double-extension spoofed file: {spoofed[0]}"
                    )
                elif execs and status == "safe":
                    status = "caution"
                    details.append(
                        f"Archive contains executable file(s), e.g. {os.path.basename(execs[0])}."
                    )
        except Exception:
            pass

    # 7. Real OS Antivirus engine scan (Windows Defender or ClamAV)
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    defender_cli = _find_windows_defender_cli()
    if defender_cli:
        try:
            proc = subprocess.run(
                [
                    defender_cli,
                    "-Scan",
                    "-ScanType",
                    "3",
                    "-File",
                    file_path,
                    "-DisableRemediation",
                ],
                capture_output=True,
                text=True,
                timeout=20,
                creationflags=flags,
            )
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            if (
                proc.returncode == 2
                or "found" in out.lower()
                and "threat" in out.lower()
            ):
                status = "dangerous"
                av_engine = "Windows Defender"
                details.append("Windows Defender detected a threat in this file.")
            elif proc.returncode == 0:
                av_engine = "Windows Defender (Clean)"
        except Exception:
            pass
    else:
        clam = shutil.which("clamdscan") or shutil.which("clamscan")
        if clam:
            try:
                proc = subprocess.run(
                    [clam, "--no-summary", file_path],
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                if proc.returncode == 1 or "FOUND" in (proc.stdout or ""):
                    status = "dangerous"
                    av_engine = "ClamAV"
                    details.append(
                        f"ClamAV threat detected: {(proc.stdout or '').strip()[:160]}"
                    )
                elif proc.returncode == 0:
                    av_engine = "ClamAV (Clean)"
            except Exception:
                pass

    # 8. Executable/installer caution (if not already flagged dangerous)
    if status == "safe" and ext in _EXEC_EXTS:
        status = "caution"
        details.append(
            f"Executable or installer type ({ext}). Only run files from trusted sources."
        )

    if status == "dangerous":
        summary = f"THREAT DETECTED ({av_engine}): " + (
            details[0] if details else "Suspicious or malicious file."
        )
    elif status == "caution":
        summary = f"Caution ({av_engine}): " + (
            details[0] if details else "Verify file before opening."
        )
    else:
        short_hash = sha256_hex[:12] if sha256_hex else "verified"
        summary = f"Clean ({av_engine}) • SHA-256: {short_hash}..."
        details.append(
            "No known malware signatures, spoofed headers, or risky payloads found."
        )

    return {
        "status": status,
        "summary": summary,
        "details": details,
        "sha256": sha256_hex,
        "av_engine": av_engine,
    }


class DownloadSafetyWorker(QObject):
    finished = pyqtSignal(object, dict)

    def start_scan(self, entry, file_path, source_url=""):
        def _run():
            res = scan_file_safety(file_path, source_url=source_url)
            self.finished.emit(entry, res)

        threading.Thread(target=_run, daemon=True).start()


class BlockManagerDialog(QDialog):
    def __init__(self, interceptor, browser_window, parent=None):
        super().__init__(parent or browser_window)
        self.setWindowTitle("Blockers and filters")
        self.resize(480, 470)
        self.interceptor = interceptor
        self.browser_window = browser_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        _dialog_header(layout, "Blockers and filters")

        def add_group(title, checks):
            g = QGroupBox(title)
            v = QVBoxLayout(g)
            for attr, text, checked, cb in checks:
                c = QCheckBox(text)
                c.setChecked(checked)
                if cb:
                    c.toggled.connect(cb)
                setattr(self, attr, c)
                v.addWidget(c)
            layout.addWidget(g)

        add_group(
            "Privacy & Ad Blocking",
            [
                (
                    "ad_block_cb",
                    "Block intrusive ads & trackers",
                    interceptor.ad_block_enabled,
                    self._on_ad_block_toggled,
                )
            ],
        )
        add_group(
            "Download Safety & Virus Scanner",
            [
                (
                    "virus_scan_cb",
                    "Automatically scan downloaded files for viruses & threats",
                    bool(browser_window.settings.get("download_virus_scan", True)),
                    lambda chk: browser_window.save_setting("download_virus_scan", chk),
                ),
                (
                    "block_danger_cb",
                    "Warn before downloading risky executables or double extensions",
                    bool(browser_window.settings.get("download_block_dangerous", True)),
                    lambda chk: browser_window.save_setting(
                        "download_block_dangerous", chk
                    ),
                ),
            ],
        )
        add_group(
            "NSFW & Adult Media Filter",
            [
                (
                    "nude_blur_cb",
                    "Blur Adult & Explicit Content (32px)",
                    interceptor.nude_block_enabled,
                    self._on_nude_blur_toggled,
                ),
                (
                    "auto_mute_video_cb",
                    "Auto-mute audio on explicit video frames",
                    True,
                    None,
                ),
            ],
        )
        add_group(
            "AI-Generated Media Detector",
            [("ai_gen_cb", "Stamp [AI GENERATED] Watermark", True, None)],
        )
        add_group(
            "AI Slop & Brainrot Blocker",
            [
                ("ai_slop_cb", "Detect AI Slop & Mutant Anatomy", True, None),
                ("blur_slop_cb", "Auto-blur AI Slop content", True, None),
            ],
        )

        stats = QLabel(
            f"Active Stats: {interceptor.blocked_ad_count} Ads Blocked • {interceptor.blocked_nude_count} Explicit Filtered"
        )
        stats.setStyleSheet("color: #8b949e; font-size: 9pt;")
        layout.addWidget(stats)
        layout.addStretch()
        close_btn = QPushButton("Save & Close")
        close_btn.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(close_btn)
        layout.addLayout(row)

    def _on_ad_block_toggled(self, is_checked):
        self.interceptor.ad_block_enabled = is_checked

    def _on_nude_blur_toggled(self, is_checked):
        self.interceptor.nude_block_enabled = is_checked


class ColorCustomizerDialog(QDialog):
    def __init__(self, browser_window, parent=None):
        super().__init__(parent or browser_window)
        self.browser_window = browser_window
        self.setWindowTitle("Color & Theme Customization — EcoBrowser")
        self.resize(520, 500)
        self.selected_color = getattr(
            browser_window, "custom_accent", DEFAULT_ACCENT_COLOR
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        _dialog_header(
            layout,
            "Color & Accent Customization",
            "Personalize EcoBrowser accents for active tabs, omnibox highlights, and progress bars.",
        )

        group_presets = QGroupBox("Preset Accent Themes")
        grid = QGridLayout(group_presets)
        self.preset_buttons = []
        for idx, p in enumerate(COLOR_PRESETS):
            hx = p["dark_color"] if browser_window.is_dark_mode else p["color"]
            btn = QPushButton(f"●  {p['name']}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton{{background:rgba(255,255,255,0.05);color:{hx};font-weight:600;padding:8px 12px;border:1px solid rgba(255,255,255,0.12);border-radius:8px;text-align:left}}QPushButton:hover{{border-color:{hx}}}"
            )
            btn.clicked.connect(lambda _, col=hx: self._select_color(col))
            grid.addWidget(btn, idx // 2, idx % 2)
            self.preset_buttons.append(btn)
        layout.addWidget(group_presets)

        group_custom = QGroupBox("Custom Color (Hex / RGB)")
        cl = QHBoxLayout(group_custom)
        self.preview_pill = QLabel()
        self.preview_pill.setFixedSize(36, 36)
        self.color_hex_label = QLabel(self.selected_color.upper())
        self.color_hex_label.setStyleSheet(
            "font-family: monospace; font-size: 11pt; font-weight: bold;"
        )
        self._update_preview_pill()
        btn_pick = QPushButton("Pick Custom Color...")
        btn_pick.clicked.connect(self._open_color_picker)
        cl.addWidget(self.preview_pill)
        cl.addWidget(self.color_hex_label)
        cl.addStretch()
        cl.addWidget(btn_pick)
        layout.addWidget(group_custom)
        layout.addStretch()

        box = QHBoxLayout()
        for label, cb, style in (
            ("Reset Default", self._reset_default, None),
            (None, None, None),
            ("Cancel", self.reject, None),
            (
                "Apply Color",
                self._apply_and_close,
                "background-color:#0969da;color:white;font-weight:bold;",
            ),
        ):
            if label is None:
                box.addStretch()
            else:
                b = QPushButton(label)
                if style:
                    b.setStyleSheet(style)
                b.clicked.connect(cb)
                box.addWidget(b)
        layout.addLayout(box)

    def _select_color(self, hex_color):
        self.selected_color = hex_color
        self._update_preview_pill()

    def _open_color_picker(self):
        chosen = QColorDialog.getColor(
            QColor(self.selected_color), self, "Choose Accent Color"
        )
        if chosen.isValid():
            self.selected_color = chosen.name()
            self._update_preview_pill()

    def _update_preview_pill(self):
        self.preview_pill.setStyleSheet(
            f"background-color:{self.selected_color};border-radius:18px;border:2px solid rgba(255,255,255,0.3);"
        )
        if hasattr(self, "color_hex_label"):
            self.color_hex_label.setText(self.selected_color.upper())

    def _reset_default(self):
        self.selected_color = DEFAULT_ACCENT_COLOR
        self._update_preview_pill()

    def _apply_and_close(self):
        self.browser_window.custom_accent = self.selected_color
        self.browser_window.save_setting("custom_accent", self.selected_color)
        self.browser_window.apply_theme()
        self.accept()


class DownloadCardWidget(QFrame):
    def __init__(self, entry, download_obj, browser_window, parent=None):
        super().__init__(parent)
        self.setObjectName("downloadItemCard")
        self.entry = entry
        self.download_obj = download_obj
        self.browser_window = browser_window
        theme = DARK_THEME if browser_window.is_dark_mode else LIGHT_THEME

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(28, 28)
        layout.addWidget(self.icon_label)

        col = QVBoxLayout()
        col.setSpacing(3)
        name_row = QHBoxLayout()
        self.name_label = QLabel(entry.get("fileName", "Unknown"))
        self.name_label.setStyleSheet(
            f"font-weight:600;font-size:9pt;color:{theme['text_primary']};"
        )
        self.safety_badge = QLabel("")
        self.safety_badge.setStyleSheet(
            "font-size:7.5pt;font-weight:700;padding:1px 7px;border-radius:8px;"
        )
        name_row.addWidget(self.name_label, 1)
        name_row.addWidget(self.safety_badge)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("downloadProgressBar")
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.status_label = QLabel()
        self.status_label.setStyleSheet(
            f"font-size:8pt;color:{theme['text_secondary']};"
        )
        self.safety_label = QLabel()
        self.safety_label.setWordWrap(True)
        self.safety_label.setStyleSheet(
            f"font-size:7.8pt;color:{theme['text_secondary']};"
        )
        col.addLayout(name_row)
        col.addWidget(self.progress_bar)
        col.addWidget(self.status_label)
        col.addWidget(self.safety_label)

        self.action_layout = QHBoxLayout()
        for attr, txt, cb in (
            ("btn_open", "Open", self._open_file),
            ("btn_folder", "Show in folder", self._show_in_folder),
            ("btn_scan", "Scan", self._scan_file),
            ("btn_delete", "Delete Threat", self._delete_file),
            ("btn_cancel", "Cancel", self._cancel_download),
        ):
            b = QPushButton(txt)
            b.setProperty("class", "downloadActionBtn")
            b.clicked.connect(cb)
            setattr(self, attr, b)
            self.action_layout.addWidget(b)
        self.action_layout.addStretch()
        col.addLayout(self.action_layout)
        layout.addLayout(col, 1)
        self.update_state()

    def _update_icon(self, theme):
        st = self.entry.get("state", "completed")
        safety = self.entry.get("safetyStatus", "")
        if st == "completed" and safety == "dangerous":
            key, col = "shield", "#f85149"
        elif st == "completed" and safety == "caution":
            key, col = "shield", "#d29922"
        elif st == "completed":
            key, col = "check_circle", "#34a853"
        elif st == "in_progress":
            key, col = "download", theme["accent_blue"]
        else:
            key, col = "file", theme["icon_color"]
        self.icon_label.setPixmap(
            render_svg_icon(SVG_ICONS[key], col, 24).pixmap(24, 24)
        )

    def _update_safety_ui(self, exists):
        safety = self.entry.get("safetyStatus", "")
        summary = self.entry.get("safetySummary", "")
        if safety == "scanning":
            self.safety_badge.setText("SCANNING")
            self.safety_badge.setStyleSheet(
                "background:rgba(88,166,255,0.2);color:#58a6ff;font-size:7.5pt;font-weight:700;padding:1px 7px;border-radius:8px;"
            )
            self.safety_badge.show()
        elif safety == "safe":
            self.safety_badge.setText("SAFE")
            self.safety_badge.setStyleSheet(
                "background:rgba(52,168,83,0.2);color:#3fb950;font-size:7.5pt;font-weight:700;padding:1px 7px;border-radius:8px;"
            )
            self.safety_badge.show()
        elif safety == "caution":
            self.safety_badge.setText("CAUTION")
            self.safety_badge.setStyleSheet(
                "background:rgba(210,153,34,0.22);color:#d29922;font-size:7.5pt;font-weight:700;padding:1px 7px;border-radius:8px;"
            )
            self.safety_badge.show()
        elif safety == "dangerous":
            self.safety_badge.setText("THREAT")
            self.safety_badge.setStyleSheet(
                "background:rgba(248,81,73,0.22);color:#f85149;font-size:7.5pt;font-weight:700;padding:1px 7px;border-radius:8px;"
            )
            self.safety_badge.show()
        else:
            self.safety_badge.hide()
        self.safety_label.setText(summary)
        self.safety_label.setVisible(bool(summary))
        self.btn_scan.setVisible(exists and self.entry.get("state") == "completed")
        self.btn_delete.setVisible(exists and safety == "dangerous")
        self.btn_delete.setStyleSheet("color:#f85149;font-weight:700;")

    def update_state(self):
        theme = DARK_THEME if self.browser_window.is_dark_mode else LIGHT_THEME
        state, fpath = self.entry.get("state", "completed"), self.entry.get(
            "filePath", ""
        )
        self._update_icon(theme)
        self.progress_bar.setVisible(state == "in_progress")
        self.btn_cancel.setVisible(state == "in_progress")
        if state == "in_progress":
            rec, tot = self.entry.get("receivedBytes", 0), self.entry.get(
                "totalBytes", 0
            )
            pct = int((rec / tot) * 100) if tot > 0 else 0
            self.progress_bar.setValue(pct)
            self.status_label.setText(
                f"{format_file_size(rec)} / {format_file_size(tot)} ({pct}%)"
                if tot > 0
                else f"{format_file_size(rec)} downloaded"
            )
            self.btn_open.hide()
            self.btn_folder.hide()
            self.btn_scan.hide()
            self.btn_delete.hide()
            self._update_safety_ui(False)
        elif state == "completed":
            size_str = format_file_size(self.entry.get("totalBytes", 0))
            exists = os.path.exists(fpath)
            self.status_label.setText(
                f"{size_str} • {'Completed' if exists else 'File removed'}"
            )
            self.btn_open.setVisible(exists)
            self.btn_folder.setVisible(exists)
            self._update_safety_ui(exists)
        else:
            self.status_label.setText(
                "Cancelled" if state == "cancelled" else "Interrupted"
            )
            self.btn_open.hide()
            self.btn_folder.hide()
            self.btn_scan.hide()
            self.btn_delete.hide()
            self._update_safety_ui(False)

    def update_progress(self, received, total):
        self.entry["receivedBytes"] = received
        self.entry["totalBytes"] = total
        self.update_state()

    def _open_file(self):
        fp = self.entry.get("filePath", "")
        if not os.path.exists(fp):
            return
        if self.entry.get("safetyStatus") == "dangerous":
            res = QMessageBox.warning(
                self,
                "Dangerous File Blocked",
                f"EcoBrowser Safety Guard flagged this file:\n{self.entry.get('safetySummary', '')}\n\nOpen anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if res != QMessageBox.StandardButton.Yes:
                return
        try:
            if sys.platform == "win32":
                os.startfile(fp)
            else:
                subprocess.Popen(
                    ["open" if sys.platform == "darwin" else "xdg-open", fp]
                )
        except Exception:
            pass

    def _show_in_folder(self):
        fp = self.entry.get("filePath", "")
        if os.path.exists(fp):
            try:
                if sys.platform == "win32":
                    subprocess.Popen(f'explorer /select,"{os.path.normpath(fp)}"')
                else:
                    subprocess.Popen(
                        [
                            "open" if sys.platform == "darwin" else "xdg-open",
                            os.path.dirname(fp),
                        ]
                    )
            except Exception:
                pass

    def _scan_file(self):
        fp = self.entry.get("filePath", "")
        if not os.path.exists(fp):
            return
        res = scan_file_safety(fp)
        self.entry["safetyStatus"] = res["status"]
        self.entry["safetySummary"] = res["summary"]
        self.entry["sha256"] = res["sha256"]
        self.browser_window._update_download_entry_on_disk(self.entry)
        self.update_state()
        QMessageBox.information(
            self,
            "File Safety Report",
            f"File: {self.entry.get('fileName')}\nStatus: {res['status'].upper()}\nEngine: {res['av_engine']}\n"
            f"SHA-256: {res['sha256']}\n\nDetails:\n- " + "\n- ".join(res["details"]),
        )

    def _delete_file(self):
        fp = self.entry.get("filePath", "")
        if os.path.exists(fp):
            try:
                os.remove(fp)
            except Exception as e:
                QMessageBox.warning(self, "Delete Failed", str(e))
                return
        self.entry["safetySummary"] = "Threat file deleted from disk."
        self.browser_window._update_download_entry_on_disk(self.entry)
        self.update_state()

    def _cancel_download(self):
        if self.download_obj:
            try:
                self.download_obj.cancel()
            except Exception:
                pass
        self.entry["state"] = "cancelled"
        self.update_state()


class DownloadsBubblePopup(QWidget):
    def __init__(self, browser_window):
        super().__init__(
            browser_window, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.browser_window = browser_window
        self.setFixedWidth(400)
        self.card_widgets = {}
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        self.card = QFrame()
        self.card.setObjectName("downloadsBubbleCard")
        cl = QVBoxLayout(self.card)
        hl = QHBoxLayout()
        _dialog_header(hl, "Downloads", size=11)
        hl.addStretch()
        btn_all = QPushButton("Show all")
        btn_all.setProperty("class", "downloadActionBtn")
        btn_all.clicked.connect(self._open_all_downloads)
        hl.addWidget(btn_all)
        theme = DARK_THEME if self.browser_window.is_dark_mode else LIGHT_THEME
        btn_close = QPushButton()
        btn_close.setFixedSize(20, 20)
        btn_close.setIcon(
            render_svg_icon(SVG_ICONS["tab_close"], theme["close_icon_color"], 10)
        )
        btn_close.clicked.connect(self.hide)
        hl.addWidget(btn_close)
        cl.addLayout(hl)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setMaximumHeight(340)
        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setSpacing(6)
        self.items_layout.addStretch()
        self.scroll.setWidget(self.items_container)
        cl.addWidget(self.scroll)
        root.addWidget(self.card)

    def refresh(self):
        self.card_widgets.clear()
        _clear_layout_except_stretch(self.items_layout)
        active = [(d, e) for d, e in self.browser_window.active_downloads.items()]
        active_paths = {e["filePath"] for _, e in active}
        hist = [
            (None, h)
            for h in self.browser_window.load_downloads()
            if h.get("filePath") not in active_paths
        ]
        items = (active + hist)[:12]
        if not items:
            lbl = QLabel("No recent downloads")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #8b949e; padding: 24px 0;")
            self.items_layout.insertWidget(0, lbl)
            return
        for d_obj, entry in items:
            card = DownloadCardWidget(entry, d_obj, self.browser_window)
            if d_obj:
                self.card_widgets[d_obj] = card
            self.items_layout.insertWidget(self.items_layout.count() - 1, card)

    def update_card_progress(self, download):
        if download in self.card_widgets:
            self.card_widgets[download].update_progress(
                download.receivedBytes(), download.totalBytes()
            )

    def _open_all_downloads(self):
        self.hide()
        self.browser_window.open_downloads_dialog()


class DownloadsDialog(QDialog):
    def __init__(self, browser_window):
        super().__init__(browser_window)
        self.setWindowTitle("Downloads & Safety Scanner — EcoBrowser")
        self.resize(680, 500)
        self.browser_window = browser_window
        layout = QVBoxLayout(self)
        hl = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search downloads...")
        self.search_input.textChanged.connect(self.load_all_downloads)
        hl.addWidget(self.search_input, 1)
        self.btn_scan_any = QPushButton("Scan File for Viruses...")
        self.btn_scan_any.clicked.connect(self.scan_any_file)
        hl.addWidget(self.btn_scan_any)
        self.btn_clear_all = QPushButton("Clear all")
        self.btn_clear_all.clicked.connect(self.clear_all_downloads)
        hl.addWidget(self.btn_clear_all)
        layout.addLayout(hl)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.addStretch()
        self.scroll.setWidget(self.items_container)
        layout.addWidget(self.scroll, 1)
        btn = QPushButton("Done")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.load_all_downloads()

    def scan_any_file(self):
        self.browser_window.scan_local_file_dialog(parent=self)
        self.load_all_downloads()

    def load_all_downloads(self):
        _clear_layout_except_stretch(self.items_layout)
        q = self.search_input.text().strip().lower()
        entries = [
            e
            for e in self.browser_window.load_downloads()
            if not q or q in e.get("fileName", "").lower()
        ]
        if not entries:
            lbl = QLabel("No matching downloads found" if q else "No downloads found")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #8b949e; padding: 30px;")
            self.items_layout.insertWidget(0, lbl)
            return
        for e in entries:
            self.items_layout.insertWidget(
                self.items_layout.count() - 1,
                DownloadCardWidget(e, None, self.browser_window),
            )

    def clear_all_downloads(self):
        self.browser_window.save_downloads([])
        self.load_all_downloads()


class HistoryDialog(QDialog):
    def __init__(self, history_file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("History — EcoBrowser")
        self.resize(620, 440)
        self.history_file_path = history_file_path
        layout = QVBoxLayout(self)
        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        if os.path.exists(history_file_path):
            with open(history_file_path, "r", encoding="utf-8") as f:
                self.text_view.setText(f.read())
        else:
            self.text_view.setText("No browsing history found.")
        layout.addWidget(self.text_view)
        row = QHBoxLayout()
        self.btn_clear = QPushButton("Clear History")
        self.btn_close = QPushButton("Close")
        self.btn_clear.clicked.connect(self.clear_history)
        self.btn_close.clicked.connect(self.accept)
        row.addWidget(self.btn_clear)
        row.addStretch()
        row.addWidget(self.btn_close)
        layout.addLayout(row)

    def clear_history(self):
        if os.path.exists(self.history_file_path):
            os.remove(self.history_file_path)
        self.text_view.setText("No browsing history found.")


def _fill_combo(combo, items, current_val):
    for label, val in items:
        combo.addItem(label, val)
    idx = combo.findData(current_val)
    combo.setCurrentIndex(idx if idx >= 0 else 0)


class NetworkSettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Network, proxy and DNS — EcoBrowser")
        self.setMinimumWidth(480)
        self.values = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        intro = QLabel(
            "Configure secure DNS and a proxy for EcoBrowser (applies to this browser only)."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        dns_group = QGroupBox("Secure DNS (DNS over HTTPS)")
        dns_layout = QVBoxLayout(dns_group)
        self.dns_enabled_checkbox = QCheckBox("Use encrypted DNS")
        self.dns_enabled_checkbox.setChecked(settings.get("dns_enabled", True))
        dns_layout.addWidget(self.dns_enabled_checkbox)

        dns_form = QFormLayout()
        self.dns_provider_combo = QComboBox()
        _fill_combo(
            self.dns_provider_combo,
            [(p["label"], k) for k, p in DNS_PROVIDERS.items()],
            settings.get("dns_provider", "cloudflare_family"),
        )
        dns_form.addRow("Resolver", self.dns_provider_combo)
        self.custom_doh_label = QLabel("Custom HTTPS resolver URL")
        self.custom_doh_input = QLineEdit(settings.get("custom_doh_url", ""))
        self.custom_doh_input.setPlaceholderText("https://resolver.example/dns-query")
        dns_form.addRow(self.custom_doh_label, self.custom_doh_input)
        dns_layout.addLayout(dns_form)
        layout.addWidget(dns_group)

        proxy_group = QGroupBox("Proxy")
        proxy_layout = QVBoxLayout(proxy_group)
        self.proxy_enabled_checkbox = QCheckBox(
            "Route EcoBrowser traffic through my proxy"
        )
        self.proxy_enabled_checkbox.setChecked(settings.get("proxy_enabled", False))
        proxy_layout.addWidget(self.proxy_enabled_checkbox)

        proxy_form = QFormLayout()
        self.proxy_type_combo = QComboBox()
        _fill_combo(
            self.proxy_type_combo,
            [("SOCKS5", "SOCKS5"), ("HTTP", "HTTP")],
            settings.get("proxy_type", "SOCKS5"),
        )
        proxy_form.addRow("Proxy type", self.proxy_type_combo)
        self.proxy_host_input = QLineEdit(settings.get("proxy_host", ""))
        self.proxy_host_input.setPlaceholderText("Host name or IP address")
        proxy_form.addRow("Proxy host", self.proxy_host_input)
        self.proxy_port_input = QLineEdit(
            str(settings.get("proxy_port", DEFAULT_SETTINGS["proxy_port"]))
        )
        self.proxy_port_input.setPlaceholderText("1080")
        proxy_form.addRow("Port", self.proxy_port_input)
        self.proxy_username_input = QLineEdit(settings.get("proxy_username", ""))
        proxy_form.addRow("Username", self.proxy_username_input)
        self.proxy_password_input = QLineEdit(settings.get("proxy_password", ""))
        self.proxy_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        proxy_form.addRow("Password", self.proxy_password_input)
        proxy_layout.addLayout(proxy_form)
        layout.addWidget(proxy_group)

        for sig in (
            self.dns_enabled_checkbox.toggled,
            self.dns_provider_combo.currentIndexChanged,
            self.proxy_enabled_checkbox.toggled,
            self.proxy_type_combo.currentIndexChanged,
            self.proxy_username_input.textChanged,
            self.proxy_password_input.textChanged,
        ):
            sig.connect(self._update_control_states)
        self._update_control_states()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_control_states(self, *_):
        dns_on = self.dns_enabled_checkbox.isChecked()
        custom_dns = self.dns_provider_combo.currentData() == "custom"
        self.dns_provider_combo.setEnabled(dns_on)
        self.custom_doh_label.setVisible(dns_on and custom_dns)
        self.custom_doh_input.setVisible(dns_on and custom_dns)

        px_on = self.proxy_enabled_checkbox.isChecked()
        is_http = self.proxy_type_combo.currentData() == "HTTP"
        for w in (self.proxy_type_combo, self.proxy_host_input, self.proxy_port_input):
            w.setEnabled(px_on)
        auth_ok = is_http or bool(
            self.proxy_username_input.text() or self.proxy_password_input.text()
        )
        self.proxy_username_input.setEnabled(auth_ok)
        self.proxy_password_input.setEnabled(auth_ok)

    def _accept_settings(self):
        dns_on = self.dns_enabled_checkbox.isChecked()
        dns_prov = self.dns_provider_combo.currentData()
        custom_doh = self.custom_doh_input.text().strip()
        if dns_on and dns_prov == "custom" and not is_valid_https_url(custom_doh):
            QMessageBox.warning(
                self, "Invalid DNS URL", "Enter a valid HTTPS DNS-over-HTTPS URL."
            )
            return
        px_on = self.proxy_enabled_checkbox.isChecked()
        px_host = self.proxy_host_input.text().strip()
        port_txt = self.proxy_port_input.text().strip()
        px_type = self.proxy_type_combo.currentData()
        px_user, px_pass = (
            self.proxy_username_input.text(),
            self.proxy_password_input.text(),
        )
        if bool(px_user) != bool(px_pass):
            QMessageBox.warning(
                self,
                "Incomplete proxy credentials",
                "Enter both a proxy username and password, or leave both blank.",
            )
            return
        if (px_user or px_pass) and px_type != "HTTP":
            QMessageBox.warning(
                self,
                "SOCKS5 authentication unavailable",
                "Chromium does not support auth for SOCKS5 proxies.",
            )
            return
        if px_on and (
            not px_host
            or any(c.isspace() for c in px_host)
            or not port_txt.isdigit()
            or not 1 <= int(port_txt) <= 65535
        ):
            QMessageBox.warning(
                self,
                "Invalid proxy settings",
                "Enter a valid proxy host and port (1-65535).",
            )
            return
        self.values = {
            "dns_enabled": dns_on,
            "dns_provider": dns_prov,
            "custom_doh_url": custom_doh,
            "proxy_enabled": px_on,
            "proxy_type": px_type,
            "proxy_host": px_host,
            "proxy_username": px_user,
            "proxy_password": px_pass,
            "proxy_port": (
                int(port_txt) if port_txt.isdigit() else DEFAULT_SETTINGS["proxy_port"]
            ),
        }
        self.accept()


class OptimizationsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Optimizations - EcoBrowser")
        self.resize(620, 700)
        self.values = None
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setSpacing(16)

        vram_group = QGroupBox("VRAM / GPU Offload")
        vl = QVBoxLayout(vram_group)
        vl.addWidget(QLabel("Choose which GPU EcoBrowser uses for VRAM."))
        try:
            out = (
                subprocess.check_output(
                    [
                        "nvidia-smi",
                        "--query-gpu=index,name,pci.bus_id,memory.total,memory.used",
                        "--format=csv,noheader,nounits",
                    ],
                    stderr=subprocess.DEVNULL,
                    timeout=3,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
                .decode()
                .strip()
            )
            gpu_txt = "Detected NVIDIA:\n" + "\n".join(
                "• " + l.strip() for l in out.splitlines()
            )
        except Exception:
            gpu_txt = "No NVIDIA via nvidia-smi. Check via Check Current GPU (WebGL)."
        gpu_lbl = QLabel(gpu_txt)
        gpu_lbl.setWordWrap(True)
        gpu_lbl.setStyleSheet(
            "color:#8b949e;font-size:11px;background:#121418;padding:10px;border-radius:8px;"
        )
        vl.addWidget(gpu_lbl)
        self.gpu_combo = QComboBox()
        _fill_combo(
            self.gpu_combo,
            [
                ("Auto - Let Windows decide", "auto"),
                ("High performance - dGPU (Use VRAM, fastest)", "high_performance"),
                ("Power saving - iGPU (Save battery)", "power_saving"),
            ],
            settings.get("gpu_preference", "high_performance"),
        )
        vl.addWidget(self.gpu_combo)
        row = QHBoxLayout()
        for txt, cb in (
            ("Open Windows Graphics...", self._open_windows_graphics),
            ("Check Current GPU (WebGL)", self._check_gpu),
        ):
            b = QPushButton(txt)
            b.clicked.connect(cb)
            row.addWidget(b)
        vl.addLayout(row)
        cl.addWidget(vram_group)

        ssd_group = QGroupBox("SSD / Disk Hibernation")
        sl = QVBoxLayout(ssd_group)
        hdir = os.path.join(get_app_data_folder(), "hibernated_tabs")
        cnt = (
            len([f for f in os.listdir(hdir) if f.endswith(".json")])
            if os.path.exists(hdir)
            else 0
        )
        sl.addWidget(QLabel(f"Hibernated on SSD: {cnt} tabs ({hdir})"))
        self.disk_enabled = QCheckBox("Enable Disk Hibernation (RAM + VRAM -> SSD)")
        self.disk_enabled.setChecked(settings.get("disk_hibernation_enabled", False))
        self.disk_on_switch = QCheckBox("When leave tab, hibernate immediately")
        self.disk_on_switch.setChecked(
            settings.get("disk_hibernation_on_switch", False)
        )
        sl.addWidget(self.disk_enabled)
        sl.addWidget(self.disk_on_switch)

        sform = QFormLayout()
        self.keep_spin = QSpinBox()
        self.keep_spin.setRange(1, 5)
        self.keep_spin.setValue(int(settings.get("disk_hibernation_keep_tabs", 1)))
        sform.addRow("Keep in RAM:", self.keep_spin)
        self.disk_timeout_spin = QSpinBox()
        self.disk_timeout_spin.setRange(0, 120)
        self.disk_timeout_spin.setSuffix(" minutes (0 = disabled)")
        self.disk_timeout_spin.setValue(
            int(settings.get("disk_hibernation_timeout", 0))
        )
        sform.addRow("Hibernate after:", self.disk_timeout_spin)
        sl.addLayout(sform)

        sl.addWidget(QLabel("Excluded domains (never hibernate):"))
        self.excluded_edit = QTextEdit()
        self.excluded_edit.setMaximumHeight(65)
        ex = settings.get("disk_hibernation_excluded_domains", "")
        self.excluded_edit.setPlainText(
            ", ".join(ex) if isinstance(ex, list) else str(ex)
        )
        sl.addWidget(self.excluded_edit)
        self.low_ram_check = QCheckBox(
            "Ultra Low RAM: Disk cache 200MB on SSD, renderer limit 4"
        )
        self.low_ram_check.setChecked(settings.get("disk_hibernation_low_ram", True))
        sl.addWidget(self.low_ram_check)
        srow = QHBoxLayout()
        for txt, cb in (
            ("Clear SSD Files", self._clear_ssd),
            ("Open SSD Folder", self._open_ssd_folder),
        ):
            b = QPushButton(txt)
            b.clicked.connect(cb)
            srow.addWidget(b)
        sl.addLayout(srow)
        cl.addWidget(ssd_group)

        ram_group = QGroupBox("RAM Trimming (Tear-Free)")
        rl = QVBoxLayout(ram_group)
        rl.addWidget(
            QLabel(
                "Trims idle renderer working sets without disturbing the GPU compositor to avoid visual tearing."
            )
        )
        self.ram_trim_enabled = QCheckBox("Enable RAM Trimming (Recommended)")
        self.ram_trim_enabled.setChecked(settings.get("ram_trim_enabled", True))
        self.ram_aggressive = QCheckBox(
            "Aggressive Trim: Periodic GC + Trim on hibernation"
        )
        self.ram_aggressive.setChecked(settings.get("ram_trim_aggressive", False))
        rl.addWidget(self.ram_trim_enabled)
        rl.addWidget(self.ram_aggressive)
        rform = QFormLayout()
        self.ram_interval_spin = QSpinBox()
        self.ram_interval_spin.setRange(5, 120)
        self.ram_interval_spin.setSuffix(" seconds")
        self.ram_interval_spin.setValue(int(settings.get("ram_trim_interval", 30)))
        rform.addRow("Trim every:", self.ram_interval_spin)
        rl.addLayout(rform)
        trim_now_btn = QPushButton("Trim RAM Now")
        trim_now_btn.clicked.connect(self._trim_now)
        rl.addWidget(trim_now_btn)
        cl.addWidget(ram_group)
        cl.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

    def _open_windows_graphics(self):
        try:
            subprocess.Popen(
                ["explorer", "ms-settings:display-advancedgraphics"], shell=False
            )
        except Exception as e:
            QMessageBox.information(
                self,
                "Windows Graphics",
                f"Open Settings -> Display -> Graphics manually: {e}",
            )

    def _check_gpu(self):
        parent = self.parent()
        if parent and hasattr(parent, "open_gpu_info_page"):
            parent.open_gpu_info_page()
            self.accept()

    def _clear_ssd(self):
        hdir = os.path.join(get_app_data_folder(), "hibernated_tabs")
        cnt = 0
        if os.path.exists(hdir):
            for f in os.listdir(hdir):
                try:
                    os.remove(os.path.join(hdir, f))
                    cnt += 1
                except Exception:
                    pass
        QMessageBox.information(self, "Disk Hibernation", f"Cleared {cnt} SSD files.")

    def _open_ssd_folder(self):
        hdir = os.path.join(get_app_data_folder(), "hibernated_tabs")
        os.makedirs(hdir, exist_ok=True)
        try:
            subprocess.Popen(["explorer", hdir])
        except Exception:
            pass

    def _trim_now(self):
        parent = self.parent()
        if parent and hasattr(parent, "_trim_working_sets"):
            stats = parent._trim_working_sets(force_ui=True)
            if isinstance(stats, dict) and stats.get("before_mb", 0) > 0:
                saved = max(0, stats["before_mb"] - stats["after_mb"])
                QMessageBox.information(
                    self,
                    "RAM Trim Complete",
                    f"Trimmed {stats['trimmed']} process(es) safely (GPU compositor preserved).\n"
                    f"Working Set: {stats['before_mb']:.0f} MB -> {stats['after_mb']:.0f} MB (freed {saved:.0f} MB).",
                )
            else:
                QMessageBox.information(
                    self, "RAM Trim Complete", "Python GC & heap memory trim completed."
                )

    def accept(self):
        self.values = {
            "gpu_preference": self.gpu_combo.currentData(),
            "disk_hibernation_enabled": self.disk_enabled.isChecked(),
            "disk_hibernation_on_switch": self.disk_on_switch.isChecked(),
            "disk_hibernation_keep_tabs": int(self.keep_spin.value()),
            "disk_hibernation_timeout": int(self.disk_timeout_spin.value()),
            "disk_hibernation_excluded_domains": self.excluded_edit.toPlainText().strip(),
            "disk_hibernation_low_ram": self.low_ram_check.isChecked(),
            "hibernation_enabled": self.disk_enabled.isChecked(),
            "ram_trim_enabled": self.ram_trim_enabled.isChecked(),
            "ram_trim_aggressive": self.ram_aggressive.isChecked(),
            "ram_trim_interval": int(self.ram_interval_spin.value()),
        }
        super().accept()


HibernationSettingsDialog = OptimizationsDialog


class ReaderSettingsDialog(QDialog):
    def __init__(self, browser_window, parent=None):
        super().__init__(parent or browser_window)
        self.browser_window = browser_window
        self.settings = browser_window.settings
        self.setWindowTitle("Reader Mode Settings — EcoBrowser")
        self.resize(520, 580)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        _dialog_header(
            layout,
            "Reader Mode / Distraction-Free Reading",
            "Clean reading layout that strips ads and sidebars.",
        )

        form = QFormLayout()
        self.font_combo = QComboBox()
        _fill_combo(
            self.font_combo,
            [(v["label"], k) for k, v in READER_FONTS.items()],
            self.settings.get("reader_font", "serif"),
        )
        form.addRow("Font Family:", self.font_combo)

        self.font_size_combo = QComboBox()
        sizes = [(f"{s} px", s) for s in (14, 16, 18, 19, 20, 22, 24, 26, 28)]
        cur_sz = self.settings.get("reader_font_size", 19)
        if not any(v == cur_sz for _, v in sizes):
            sizes.append((f"{cur_sz} px (custom)", cur_sz))
        _fill_combo(self.font_size_combo, sizes, cur_sz)
        form.addRow("Font Size:", self.font_size_combo)

        self.line_height_combo = QComboBox()
        _fill_combo(
            self.line_height_combo,
            [(str(lh), lh) for lh in (1.4, 1.6, 1.8, 2.0, 2.2)],
            self.settings.get("reader_line_height", 1.8),
        )
        form.addRow("Line Height:", self.line_height_combo)

        self.width_combo = QComboBox()
        _fill_combo(
            self.width_combo,
            [(f"{v['label']} ({v['px']}px)", k) for k, v in READER_WIDTHS.items()],
            self.settings.get("reader_width", "medium"),
        )
        form.addRow("Page Width:", self.width_combo)

        self.theme_combo = QComboBox()
        _fill_combo(
            self.theme_combo,
            [(v["label"], k) for k, v in READER_THEMES.items()],
            self.settings.get("reader_theme", "auto"),
        )
        form.addRow("Paper Theme:", self.theme_combo)

        self.align_combo = QComboBox()
        _fill_combo(
            self.align_combo,
            [("Left / Start", "start"), ("Justified", "justify")],
            self.settings.get("reader_text_align", "start"),
        )
        form.addRow("Text Align:", self.align_combo)
        layout.addLayout(form)

        pg = QGroupBox("Preview")
        pl = QVBoxLayout(pg)
        self.preview_label = QLabel(
            "The quick brown fox jumps over the lazy dog.\n\nDistraction-free reading layout."
        )
        self.preview_label.setWordWrap(True)
        pl.addWidget(self.preview_label)
        layout.addWidget(pg)

        box = QHBoxLayout()
        box.addStretch()
        bc = QPushButton("Cancel")
        bc.clicked.connect(self.reject)
        ba = QPushButton("Save & Apply")
        ba.setStyleSheet(
            "background-color:#0969da;color:white;font-weight:bold;padding:6px 14px;border-radius:6px;"
        )
        ba.clicked.connect(self._save)
        box.addWidget(bc)
        box.addWidget(ba)
        layout.addLayout(box)

        for c in (
            self.font_combo,
            self.font_size_combo,
            self.width_combo,
            self.theme_combo,
        ):
            c.currentIndexChanged.connect(self._update_preview)
        self._update_preview()

    def _update_preview(self):
        font_info = READER_FONTS.get(
            self.font_combo.currentData(), READER_FONTS["serif"]
        )
        size = self.font_size_combo.currentData() or 19
        tk = self.theme_combo.currentData() or "light"
        th = READER_THEMES.get(tk, READER_THEMES["light"])
        bg = th.get("bg", "#ffffff") if tk != "auto" else "#ffffff"
        fg = th.get("fg", "#1a1a1a") if tk != "auto" else "#1a1a1a"
        self.preview_label.setStyleSheet(
            f"font-family:{font_info['stack']};font-size:{size}pt;background:{bg};color:{fg};padding:14px;border-radius:8px;border:1px solid #30363d;"
        )

    def _save(self):
        vals = {
            "reader_font": self.font_combo.currentData(),
            "reader_font_size": self.font_size_combo.currentData(),
            "reader_line_height": self.line_height_combo.currentData(),
            "reader_width": self.width_combo.currentData(),
            "reader_theme": self.theme_combo.currentData(),
            "reader_text_align": self.align_combo.currentData(),
        }
        if self.browser_window.save_setting_batch(vals):
            v = self.browser_window.get_current_view()
            if v:
                self.browser_window.apply_reader_settings_to_view(v)
        self.accept()


class UserscriptManagerDialog(QDialog):
    def __init__(self, browser_window, parent=None):
        super().__init__(parent or browser_window)
        self.browser_window = browser_window
        self.manager = browser_window.userscript_manager
        self.setWindowTitle("Userscript Manager — EcoBrowser (.user.js)")
        self.resize(720, 520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        hl = QHBoxLayout()
        _dialog_header(hl, "Custom Userscript & Extension Support", size=11)
        hl.addStretch()
        for txt, cb in (
            ("Open Folder", self.manager.open_folder),
            ("Refresh", self.refresh_list),
        ):
            b = QPushButton(txt)
            b.clicked.connect(cb)
            hl.addWidget(b)
        layout.addLayout(hl)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, 1)

        ctrl = QHBoxLayout()
        for txt, cb, style in (
            ("Install from File...", self._install_from_file, None),
            ("New Script...", self._new_script, None),
            (None, None, None),
            ("Edit", self._edit_selected, None),
            ("Enable/Disable", self._toggle_selected, None),
            ("Delete", self._delete_selected, "color:#f85149;"),
        ):
            if txt is None:
                ctrl.addStretch()
            else:
                b = QPushButton(txt)
                if style:
                    b.setStyleSheet(style)
                b.clicked.connect(cb)
                ctrl.addWidget(b)
        layout.addLayout(ctrl)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.refresh_list()

    def refresh_list(self):
        self.manager.load_scripts()
        self.list_widget.clear()
        scripts = self.manager.get_all_scripts()
        if not scripts:
            item = QListWidgetItem("No userscripts installed.")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.list_widget.addItem(item)
            return
        for s in scripts:
            st = "Enabled" if s.enabled else "Disabled"
            txt = f"[{st}] {s.name} v{s.version} — {s.filename}" + (
                f" — {s.description[:80]}" if s.description else ""
            )
            item = QListWidgetItem(txt)
            item.setData(Qt.ItemDataRole.UserRole, s.filename)
            self.list_widget.addItem(item)

    def _selected_filename(self):
        it = self.list_widget.currentItem()
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def _install_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Install Userscript",
            "",
            "Userscript Files (*.user.js *.js);;All Files (*)",
        )
        if path and self.manager.add_script_from_file(path):
            self.refresh_list()

    def _new_script(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Create New Userscript")
        dlg.resize(600, 500)
        v = QVBoxLayout(dlg)
        ed = QTextEdit(
            "// ==UserScript==\n// @name         My Script\n// @match        *://*/*\n// ==/UserScript==\n(function(){\n  'use strict';\n})();\n"
        )
        v.addWidget(ed, 1)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        v.addWidget(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            code = ed.toPlainText()
            m = re.search(r"@name\s+(.+)", code)
            fname = (
                f"{re.sub(r'[^a-zA-Z0-9_-]', '_', m.group(1).strip())[:30]}.user.js"
                if m
                else "custom.user.js"
            )
            if self.manager.add_script_from_code(code, fname):
                self.refresh_list()

    def _edit_selected(self):
        fname = self._selected_filename()
        if not fname:
            return
        fpath = os.path.join(self.manager.folder, fname)
        if not os.path.exists(fpath):
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Edit {fname}")
        dlg.resize(700, 600)
        v = QVBoxLayout(dlg)
        ed = QTextEdit()
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            ed.setPlainText(f.read())
        v.addWidget(ed, 1)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        v.addWidget(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(ed.toPlainText())
            self.manager.load_scripts()
            self.refresh_list()

    def _toggle_selected(self):
        fname = self._selected_filename()
        if fname and fname in self.manager.scripts:
            self.manager.set_enabled(fname, not self.manager.scripts[fname].enabled)
            self.refresh_list()

    def _delete_selected(self):
        fname = self._selected_filename()
        if (
            fname
            and QMessageBox.question(self, "Delete", f"Delete '{fname}'?")
            == QMessageBox.StandardButton.Yes
        ):
            self.manager.delete_script(fname)
            self.refresh_list()


class ToolbarCustomizerDialog(QDialog):
    def __init__(self, browser_window, parent=None):
        super().__init__(parent or browser_window)
        self.browser_window = browser_window
        self.settings = browser_window.settings
        self.setWindowTitle("Customize Toolbar — Pin / Unpin")
        self.resize(460, 520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        _dialog_header(
            layout,
            "Pin what you want in the top bar",
            "Choose which buttons appear in the toolbar.",
            size=11,
        )

        self.checkboxes = {}
        defaults = DEFAULT_SETTINGS["toolbar_pinned"]
        pinned = dict(self.settings.get("toolbar_pinned", defaults))
        items = [
            ("back", "Back", "Go back"),
            ("forward", "Forward", "Go forward"),
            ("reload", "Reload / Stop", "Reload or stop loading"),
            ("home", "Home", "Open home / start page"),
            ("reader", "Reader Mode", "Distraction-free reading"),
            ("bookmarks", "Bookmark Star", "Bookmark current page"),
            ("downloads", "Downloads", "Downloads bubble"),
            ("split", "Split View", "Side-by-side dual pane"),
            ("vertical_tabs", "Vertical Tabs", "Toggle vertical tab sidebar"),
            ("command", "Command Palette", "Quick tab & action switcher (Ctrl+K)"),
            ("translate", "Translate", "Translate Page button"),
            ("blockers", "Blockers & Filters", "Ad & NSFW blocker settings"),
            ("passwords", "Password Manager", "Saved logins & autofill"),
            ("userscript", "Userscripts (.user.js)", "Custom JS enhancements"),
            ("proxy", "Proxy & DNS", "Network settings"),
            ("customize", "Customize", "Appearance & New Tab"),
            ("gpu", "GPU / VRAM", "Opens Optimizations"),
            ("optimizations", "Optimizations", "VRAM + Hibernation + RAM Trim"),
        ]
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        il = QVBoxLayout(inner)
        for key, label, tip in items:
            cb = QCheckBox(f"{label} — {tip}")
            cb.setChecked(pinned.get(key, defaults.get(key, False)))
            self.checkboxes[key] = cb
            il.addWidget(cb)
        il.addStretch()
        scroll.setWidget(inner)
        layout.addWidget(scroll, 1)

        self.hide_chrome_cb = QCheckBox("Reader Mode hides Nav & Bookmark bar")
        self.hide_chrome_cb.setChecked(self.settings.get("reader_hide_chrome", True))
        layout.addWidget(self.hide_chrome_cb)

        box = QHBoxLayout()
        box.addStretch()
        for label, cb, style in (
            ("Reset Defaults", self._reset, None),
            ("Cancel", self.reject, None),
            (
                "Save",
                self._save,
                "background-color:#0969da;color:white;font-weight:bold;padding:6px 14px;border-radius:6px;",
            ),
        ):
            b = QPushButton(label)
            if style:
                b.setStyleSheet(style)
            b.clicked.connect(cb)
            box.addWidget(b)
        layout.addLayout(box)

    def _reset(self):
        defaults = DEFAULT_SETTINGS["toolbar_pinned"]
        for key, cb in self.checkboxes.items():
            cb.setChecked(defaults.get(key, False))
        self.hide_chrome_cb.setChecked(True)

    def _save(self):
        updates = {
            "toolbar_pinned": {k: cb.isChecked() for k, cb in self.checkboxes.items()},
            "reader_hide_chrome": self.hide_chrome_cb.isChecked(),
        }
        if self.browser_window.save_setting_batch(updates):
            self.browser_window.apply_toolbar_config()
        self.accept()


def _get_process_cmdline_win(pid):
    """Best-effort command line lookup for a child process without requiring psutil."""
    try:
        import psutil  # type: ignore

        return " ".join(psutil.Process(pid).cmdline()).lower()
    except Exception:
        pass
    if sys.platform != "win32":
        return ""
    try:
        from ctypes import wintypes

        class UNICODE_STRING(ctypes.Structure):
            _fields_ = [
                ("Length", wintypes.USHORT),
                ("MaximumLength", wintypes.USHORT),
                ("Buffer", ctypes.c_void_p),
            ]

        ntdll = ctypes.WinDLL("ntdll")
        k32 = ctypes.WinDLL("kernel32")
        k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.CloseHandle.argtypes = [wintypes.HANDLE]
        k32.CloseHandle.restype = wintypes.BOOL
        ntdll.NtQueryInformationProcess.argtypes = [
            wintypes.HANDLE,
            wintypes.ULONG,
            ctypes.c_void_p,
            wintypes.ULONG,
            ctypes.POINTER(wintypes.ULONG),
        ]
        ntdll.NtQueryInformationProcess.restype = ctypes.c_long

        h = k32.OpenProcess(
            0x1000, False, int(pid)
        )  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return ""
        try:
            buf_size = 8192
            buf = ctypes.create_string_buffer(buf_size)
            ret_len = wintypes.ULONG()
            status = ntdll.NtQueryInformationProcess(
                h, 60, buf, buf_size, ctypes.byref(ret_len)
            )
            if status == 0:
                us = UNICODE_STRING.from_buffer_copy(buf)
                if us.Buffer and us.Length:
                    return ctypes.wstring_at(us.Buffer, us.Length // 2).lower()
        finally:
            k32.CloseHandle(h)
    except Exception:
        pass
    return ""


def _win_process_working_set_bytes(h_proc):
    if sys.platform != "win32" or not h_proc:
        return 0
    try:
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        psapi = ctypes.WinDLL("psapi")
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
            wintypes.DWORD,
        ]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        if psapi.GetProcessMemoryInfo(h_proc, ctypes.byref(pmc), pmc.cb):
            return int(pmc.WorkingSetSize)
    except Exception:
        pass
    return 0


def _win_empty_working_set(h_proc):
    if sys.platform != "win32" or not h_proc:
        return False
    from ctypes import wintypes

    k32 = ctypes.WinDLL("kernel32")
    k32.SetProcessWorkingSetSizeEx.argtypes = [
        wintypes.HANDLE,
        ctypes.c_size_t,
        ctypes.c_size_t,
        wintypes.DWORD,
    ]
    k32.SetProcessWorkingSetSizeEx.restype = wintypes.BOOL
    try:
        fn = getattr(k32, "K32EmptyWorkingSet", None)
        if fn is None:
            fn = ctypes.WinDLL("psapi").EmptyWorkingSet
        fn.argtypes = [wintypes.HANDLE]
        fn.restype = wintypes.BOOL
        if fn(h_proc):
            return True
    except Exception:
        pass
    try:
        neg1 = ctypes.c_size_t(-1).value
        return bool(k32.SetProcessWorkingSetSizeEx(h_proc, neg1, neg1, 0))
    except Exception:
        return False


class CommandPaletteDialog(QDialog):
    def __init__(self, browser_window, parent=None):
        super().__init__(parent or browser_window)
        self.browser_window = browser_window
        self.setWindowTitle("Command Palette — EcoBrowser")
        self.resize(560, 420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Type a tab title, bookmark, or command (e.g. split, private, mute, zoom)..."
        )
        self.search_input.setFixedHeight(36)
        self.search_input.textChanged.connect(self._refresh)
        self.search_input.returnPressed.connect(self._run_selected)
        layout.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.list_widget.itemActivated.connect(lambda _: self._run_selected())
        layout.addWidget(self.list_widget, 1)

        self._entries = self._collect_entries()
        self._refresh()
        self.search_input.setFocus()

    def _collect_entries(self):
        bw = self.browser_window
        entries = []
        for i in range(bw.tab_bar.count()):
            title = bw.tab_bar.tabText(i) or f"Tab {i + 1}"
            entries.append(
                (f"[Tab] {title}", lambda idx=i: bw.tab_bar.setCurrentIndex(idx))
            )
        for bm in bw.load_bookmarks()[:30]:
            entries.append(
                (
                    f"[Bookmark] {bm.get('title', bm.get('url', ''))}",
                    lambda u=bm.get("url", ""): bw.add_new_tab(u),
                )
            )
        actions = [
            ("New Tab (Ctrl+T)", lambda: bw.add_new_tab(bw.home_url)),
            ("New Private / Incognito Window (Ctrl+Shift+N)", bw.open_private_window),
            ("Reopen Closed Tab (Ctrl+Shift+T)", bw.reopen_closed_tab),
            ("Toggle Split View Side-by-Side (Ctrl+\\)", bw.toggle_split_view),
            ("Swap Split View Panes", bw.swap_split_panes),
            ("Toggle Vertical Tabs Sidebar (Ctrl+Shift+V)", bw.toggle_vertical_tabs),
            ("Find in Page (Ctrl+F)", bw.toggle_find_bar),
            ("Picture-in-Picture Floating Video (Alt+P)", bw.toggle_picture_in_picture),
            ("Mute / Unmute Current Tab (Ctrl+M)", bw.toggle_mute_current_tab),
            (
                "Pin / Unpin Current Tab",
                lambda: bw.toggle_pin_tab(bw.tab_bar.currentIndex()),
            ),
            (
                "Duplicate Current Tab",
                lambda: bw.duplicate_tab(bw.tab_bar.currentIndex()),
            ),
            ("Capture Viewport Screenshot (Ctrl+Shift+S)", bw.capture_page_screenshot),
            ("Copy Clean URL (Strip Tracking Params)", bw.copy_clean_current_url),
            ("Toggle Reader Mode (Ctrl+Shift+R)", bw.toggle_reader_mode),
            ("Toggle Dark Mode", bw.toggle_dark_mode),
            ("Zoom In (Ctrl+=)", lambda: bw.adjust_zoom(0.1)),
            ("Zoom Out (Ctrl+-)", lambda: bw.adjust_zoom(-0.1)),
            ("Reset Zoom to 100% (Ctrl+0)", bw.reset_zoom),
            ("Toggle Fullscreen (F11)", bw.toggle_fullscreen),
            ("Restore Previous Session Tabs", bw.restore_previous_session),
            ("Open Blockers & SafeShield Filters", bw.open_block_manager_dialog),
            (
                "Open Optimizations (RAM Trim / Hibernation / GPU)",
                bw.open_optimizations_dialog,
            ),
            ("Open Password Manager", bw.open_password_manager_dialog),
            ("Open History (Ctrl+H)", bw.open_history_dialog),
        ]
        for label, fn in actions:
            entries.append((f"[Action] {label}", fn))
        return entries

    def _refresh(self):
        q = self.search_input.text().strip().lower()
        self.list_widget.clear()
        for label, fn in self._entries:
            if not q or all(tok in label.lower() for tok in q.split()):
                it = QListWidgetItem(label)
                it.setData(Qt.ItemDataRole.UserRole, fn)
                self.list_widget.addItem(it)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _run_selected(self):
        it = self.list_widget.currentItem()
        if not it:
            return
        fn = it.data(Qt.ItemDataRole.UserRole)
        self.accept()
        if callable(fn):
            QTimer.singleShot(0, fn)


class EcoBrowserWindow(QMainWindow):
    def __init__(self, initial_url=None, private_mode=False):
        super().__init__()
        self.private_mode = bool(private_mode)
        self.setWindowTitle(
            f"{APP_NAME} v{APP_VERSION}"
            + (" — Private Browsing" if self.private_mode else "")
        )
        self.resize(1180, 780)
        self.initial_url = initial_url
        self.is_loading = False
        self.active_downloads = {}
        self.downloads_bubble = None
        self.reader_state = {}
        self.readable_state = {}
        self.tab_last_active = {}
        self.closed_tabs = []
        self.pinned_tabs = set()
        self.muted_tabs = set()
        self.split_view = None
        self.settings = self.load_all_settings()
        self.vertical_tabs_enabled = (
            False
            if self.private_mode
            else bool(self.settings.get("vertical_tabs", False))
        )

        try:
            self.hibernation_dir = os.path.join(
                get_app_data_folder(), "hibernated_tabs"
            )
            os.makedirs(self.hibernation_dir, exist_ok=True)
        except Exception:
            self.hibernation_dir = ""
        self.hibernated_tabs = {}
        self._hibernating = set()

        try:
            self.password_manager = (
                None if self.private_mode else PasswordManager(get_app_data_folder())
            )
        except Exception as e:
            print(f"[PasswordManager] init failed: {e}")
            self.password_manager = None
        self._pending_password_save = None

        self.is_dark_mode = self.settings.get("dark_mode", True)
        self.search_engine = self.settings.get("search_engine", DEFAULT_SEARCH_ENGINE)
        self.custom_accent = (
            "#a78bfa"
            if self.private_mode
            else self.settings.get("custom_accent", DEFAULT_ACCENT_COLOR)
        )
        self.home_url = SEARCH_ENGINES.get(
            self.search_engine, SEARCH_ENGINES["Google"]
        )["home_url"]
        self.userscript_manager = UserscriptManager(get_app_data_folder())

        self._setup_web_profile()
        self._setup_ui()
        self.apply_theme()

        shortcuts = [
            ("Ctrl+J", self.toggle_downloads_bubble),
            ("Ctrl+T", lambda: self.add_new_tab(self.home_url)),
            ("Ctrl+W", self.close_current_tab),
            ("Ctrl+Shift+T", self.reopen_closed_tab),
            ("Ctrl+Shift+N", self.open_private_window),
            ("Ctrl+Shift+R", self.toggle_reader_mode),
            ("Ctrl+Shift+V", self.toggle_vertical_tabs),
            ("Ctrl+Shift+S", self.capture_page_screenshot),
            ("Ctrl+K", self.open_command_palette),
            ("Ctrl+F", self.toggle_find_bar),
            ("Ctrl+\\", self.toggle_split_view),
            ("Ctrl+M", self.toggle_mute_current_tab),
            ("Ctrl+=", lambda: self.adjust_zoom(0.1)),
            ("Ctrl++", lambda: self.adjust_zoom(0.1)),
            ("Ctrl+-", lambda: self.adjust_zoom(-0.1)),
            ("Ctrl+0", self.reset_zoom),
            ("F11", self.toggle_fullscreen),
            ("Ctrl+H", self.open_history_dialog),
            ("Escape", self._handle_escape_key),
        ]
        for seq, cb in shortcuts:
            QShortcut(QKeySequence(seq), self).activated.connect(cb)

        self.reader_check_timer = QTimer(self)
        self.reader_check_timer.timeout.connect(self._check_reader_js_state)
        self.reader_check_timer.start(700)

        restored = False
        if (
            not self.private_mode
            and not self.initial_url
            and (
                self.settings.get("startup_behavior") == "restore"
                or self.settings.get("restore_session", False)
            )
        ):
            restored = self.restore_previous_session(silent=True)
        if not restored:
            self.add_new_tab(self.initial_url or self.home_url)

        self.memory_timer = QTimer(self)
        self.memory_timer.timeout.connect(self._periodic_memory_cleanup)
        self.memory_timer.start(30000)

    def _check_reader_js_state(self):
        try:
            view = self.get_current_view()
            if not view:
                return
            vid = id(view)
            if not self.reader_state.get(vid, False):
                return

            def cb(is_active):
                if not is_active:
                    self.reader_state[vid] = False
                    self._refresh_reader_button_ui()
                    self._set_reader_chrome_hidden(False)

            view.page().runJavaScript(
                "window.__ecoReader ? window.__ecoReader.isActive : false", cb
            )
        except Exception:
            pass

    def _setup_web_profile(self):
        app_data_path = get_app_data_folder()
        self._ram_trim_timer = QTimer(self)

        def _discard_background_tabs(self_ref):
            try:
                if not self_ref.settings.get("disk_hibernation_enabled", False):
                    return
                timeout_min = int(self_ref.settings.get("disk_hibernation_timeout", 0))
                if timeout_min <= 0:
                    return
                now = time.time()
                current = (
                    self_ref.stack.currentWidget()
                    if hasattr(self_ref, "stack")
                    else None
                )
                for i in range(self_ref.stack.count()):
                    v = self_ref.stack.widget(i)
                    if (
                        v is None
                        or v is current
                        or is_view_deleted(v)
                        or getattr(v, "_is_hibernated_placeholder", False)
                        or id(v) in getattr(self_ref, "pinned_tabs", set())
                    ):
                        continue
                    if now - getattr(v, "_last_active", now) >= timeout_min * 60:
                        self_ref.hibernate_tab_to_disk(i)
            except Exception:
                pass

        def _iter_child_pids_win():
            if sys.platform != "win32":
                return []
            try:
                import psutil  # type: ignore

                return [p.pid for p in psutil.Process().children(recursive=True)]
            except Exception:
                pass
            pids = []
            try:
                from ctypes import wintypes

                class PROCESSENTRY32(ctypes.Structure):
                    _fields_ = [
                        ("dwSize", wintypes.DWORD),
                        ("cntUsage", wintypes.DWORD),
                        ("th32ProcessID", wintypes.DWORD),
                        ("th32DefaultHeapID", ctypes.c_size_t),
                        ("th32ModuleID", wintypes.DWORD),
                        ("cntThreads", wintypes.DWORD),
                        ("th32ParentProcessID", wintypes.DWORD),
                        ("pcPriClassBase", wintypes.LONG),
                        ("dwFlags", wintypes.DWORD),
                        ("szExeFile", ctypes.c_char * 260),
                    ]

                k32 = ctypes.WinDLL("kernel32")
                k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
                k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
                k32.Process32First.argtypes = [
                    wintypes.HANDLE,
                    ctypes.POINTER(PROCESSENTRY32),
                ]
                k32.Process32First.restype = wintypes.BOOL
                k32.Process32Next.argtypes = [
                    wintypes.HANDLE,
                    ctypes.POINTER(PROCESSENTRY32),
                ]
                k32.Process32Next.restype = wintypes.BOOL
                k32.CloseHandle.argtypes = [wintypes.HANDLE]

                snap = k32.CreateToolhelp32Snapshot(0x00000002, 0)
                if not snap or snap == wintypes.HANDLE(-1).value:
                    return []
                children_map = {}
                try:
                    entry = PROCESSENTRY32()
                    entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
                    if k32.Process32First(snap, ctypes.byref(entry)):
                        while True:
                            children_map.setdefault(
                                int(entry.th32ParentProcessID), []
                            ).append(int(entry.th32ProcessID))
                            if not k32.Process32Next(snap, ctypes.byref(entry)):
                                break
                finally:
                    k32.CloseHandle(snap)
                # Traverse full descendant tree (children + grandchildren)
                queue = list(children_map.get(os.getpid(), []))
                seen = {os.getpid()}
                while queue:
                    cid = queue.pop(0)
                    if cid in seen:
                        continue
                    seen.add(cid)
                    pids.append(cid)
                    queue.extend(children_map.get(cid, []))
            except Exception:
                pass
            return pids

        def _trim_working_sets(force_ui=False):
            # Tear-free RAM trim:
            # 1) Never trim GPU/compositor processes (--type=gpu-process) to avoid D3D11/ANGLE scanout tearing.
            # 2) Properly type all 64-bit Windows HANDLEs so EmptyWorkingSet / SetProcessWorkingSetSizeEx actually run.
            # 3) Trim background tab V8 heaps (window.gc) + Python GC + glibc malloc_trim on Linux.
            gc.collect()
            if force_ui or self.settings.get("ram_trim_aggressive", False):
                try:
                    cur = (
                        self.get_current_view()
                        if hasattr(self, "get_current_view")
                        else None
                    )
                    if hasattr(self, "stack"):
                        for i in range(self.stack.count()):
                            v = self.stack.widget(i)
                            if (
                                v is not None
                                and v is not cur
                                and isinstance(v, QWebEngineView)
                                and not is_view_deleted(v)
                            ):
                                v.page().runJavaScript(
                                    "if(window.gc)try{window.gc();}catch(e){}"
                                )
                except Exception:
                    pass

            if sys.platform != "win32":
                try:
                    libc = ctypes.CDLL("libc.so.6")
                    libc.malloc_trim(0)
                except Exception:
                    pass
                return {"trimmed": 1, "before_mb": 0.0, "after_mb": 0.0}

            trimmed = 0
            before_bytes = 0
            after_bytes = 0
            try:
                from ctypes import wintypes

                k32 = ctypes.WinDLL("kernel32")
                k32.GetCurrentProcess.restype = wintypes.HANDLE
                k32.OpenProcess.argtypes = [
                    wintypes.DWORD,
                    wintypes.BOOL,
                    wintypes.DWORD,
                ]
                k32.OpenProcess.restype = wintypes.HANDLE
                k32.CloseHandle.argtypes = [wintypes.HANDLE]
                k32.CloseHandle.restype = wintypes.BOOL

                me_h = k32.GetCurrentProcess()
                before_bytes += _win_process_working_set_bytes(me_h)
                if _win_empty_working_set(me_h):
                    trimmed += 1
                after_bytes += _win_process_working_set_bytes(me_h)

                for pid in _iter_child_pids_win():
                    cmd = _get_process_cmdline_win(pid)
                    if "--type=gpu-process" in cmd or "--type=crashpad-handler" in cmd:
                        continue
                    h = k32.OpenProcess(0x1100, False, int(pid)) or k32.OpenProcess(
                        0x0500, False, int(pid)
                    )
                    if h:
                        try:
                            before_bytes += _win_process_working_set_bytes(h)
                            if _win_empty_working_set(h):
                                trimmed += 1
                            after_bytes += _win_process_working_set_bytes(h)
                        finally:
                            k32.CloseHandle(h)
            except Exception as e:
                print(f"[RAM] trim error: {e}")
            return {
                "trimmed": trimmed,
                "before_mb": before_bytes / (1024 * 1024),
                "after_mb": after_bytes / (1024 * 1024),
            }

        def _log_ram():
            try:
                import psutil  # type: ignore

                me = psutil.Process(os.getpid())
                procs = [me, *me.children(recursive=True)]
                priv = sum(
                    getattr(p.memory_full_info(), "uss", p.memory_info().rss)
                    for p in procs
                )
                rss = sum(p.memory_info().rss for p in procs)
                print(
                    f"[RAM] Private {priv/1024/1024:.0f}MB | WorkingSet {rss/1024/1024:.0f}MB | Children: {len(procs)-1}"
                )
            except Exception:
                pass

        def _trim_ram():
            try:
                if not self.settings.get("ram_trim_enabled", True):
                    return
                _log_ram()
                _discard_background_tabs(self)
                _trim_working_sets(force_ui=False)
                if self.settings.get("ram_trim_aggressive", False):
                    self._trim_tick = getattr(self, "_trim_tick", 0) + 1
                    if self._trim_tick % 10 == 0:
                        gc.collect()
            except Exception as e:
                print(f"[RAM] trim error: {e}")

        self._ram_trim_timer.timeout.connect(_trim_ram)
        self._ram_trim_timer.start(
            max(5, int(self.settings.get("ram_trim_interval", 30))) * 1000
        )
        self._discard_background_tabs = _discard_background_tabs
        self._trim_working_sets = _trim_working_sets

        if self.private_mode:
            self.profile = QWebEngineProfile(self)
            try:
                self.profile.setHttpCacheType(
                    QWebEngineProfile.HttpCacheType.MemoryHttpCache
                )
                self.profile.setPersistentCookiesPolicy(
                    QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
                )
                self.profile.settings().setAttribute(
                    QWebEngineSettings.WebAttribute.PluginsEnabled, False
                )
            except Exception:
                pass
        else:
            self.profile = QWebEngineProfile("EcoBrowserProfile", self)
            self.profile.setPersistentStoragePath(
                os.path.join(app_data_path, "storage")
            )
            self.profile.setCachePath(os.path.join(app_data_path, "cache_v2"))
            self.profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
            )
            try:
                self.profile.setHttpCacheType(
                    QWebEngineProfile.HttpCacheType.DiskHttpCache
                )
                self.profile.setHttpCacheMaximumSize(200 * 1024 * 1024)
                self.profile.settings().setAttribute(
                    QWebEngineSettings.WebAttribute.PluginsEnabled, False
                )
            except Exception:
                pass

        for name, src, pt in (
            (
                "EcoBrowserCombinedGuard",
                ECO_GUARD_JS,
                QWebEngineScript.InjectionPoint.DocumentReady,
            ),
            (
                "EcoBrowserCombinedAuth",
                ECO_AUTH_JS,
                QWebEngineScript.InjectionPoint.DocumentCreation,
            ),
        ):
            try:
                sc = QWebEngineScript()
                sc.setName(name)
                sc.setSourceCode(src)
                sc.setInjectionPoint(pt)
                sc.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
                sc.setRunsOnSubFrames(True)
                self.profile.scripts().insert(sc)
            except Exception as e:
                print(f"[{name}] injection failed: {e}")

        self.interceptor = ContentBlocker()
        init_lvl = int(self.settings.get("blocking_level", 2))
        self.interceptor.ad_block_enabled = init_lvl >= 1
        self.interceptor.nude_block_enabled = init_lvl >= 2
        self.profile.setUrlRequestInterceptor(self.interceptor)
        self.profile.downloadRequested.connect(self.handle_download_request)
        self.crash_manager = CrashProofManager(self)

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        self.central_widget = central

        self.reader_mini_fab = QPushButton("✕", self.central_widget)
        self.reader_mini_fab.setObjectName("readerMiniFab")
        self.reader_mini_fab.setFixedSize(36, 36)
        self.reader_mini_fab.setToolTip("Exit Reader Mode (Esc)")
        self.reader_mini_fab.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reader_mini_fab.hide()
        self.reader_mini_fab.clicked.connect(self._handle_escape_reader)
        self.reader_mini_fab.raise_()

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.tab_strip_widget = self._build_tab_strip()
        self.toolbar_panel = self._build_toolbar()
        self.bookmarks_bar_widget = self._build_bookmarks_bar()
        self.find_bar_widget = self._build_find_bar()

        body = QWidget()
        body_row = QHBoxLayout(body)
        body_row.setContentsMargins(0, 0, 0, 0)
        body_row.setSpacing(0)

        self.vertical_tabs_panel = self._build_vertical_tabs_panel()
        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_splitter.setHandleWidth(4)
        self.stack = QStackedWidget()
        self.stack.setObjectName("webStack")
        self.content_splitter.addWidget(self.stack)

        body_row.addWidget(self.vertical_tabs_panel)
        body_row.addWidget(self.content_splitter, 1)

        for w in (
            self.tab_strip_widget,
            self.toolbar_panel,
            self.bookmarks_bar_widget,
            self.find_bar_widget,
        ):
            main_layout.addWidget(w)
        main_layout.addWidget(body, 1)

        self.tab_strip_widget.setVisible(not self.vertical_tabs_enabled)
        self.vertical_tabs_panel.setVisible(self.vertical_tabs_enabled)
        self.update_bookmarks_bar()

    def _build_vertical_tabs_panel(self):
        panel = QFrame()
        panel.setObjectName("verticalTabsPanel")
        panel.setFixedWidth(220)
        vl = QVBoxLayout(panel)
        vl.setContentsMargins(8, 8, 8, 8)
        vl.setSpacing(6)
        top = QHBoxLayout()
        lbl = QLabel("Tabs")
        lbl.setStyleSheet("font-weight:600;font-size:9.5pt;")
        btn_new = QPushButton("+ New Tab")
        btn_new.clicked.connect(lambda: self.add_new_tab(self.home_url))
        top.addWidget(lbl)
        top.addStretch()
        top.addWidget(btn_new)
        vl.addLayout(top)
        self.vertical_tabs_list = QListWidget()
        self.vertical_tabs_list.setObjectName("verticalTabsList")
        self.vertical_tabs_list.currentRowChanged.connect(
            lambda row: (
                self.tab_bar.setCurrentIndex(row)
                if 0 <= row < self.tab_bar.count()
                else None
            )
        )
        self.vertical_tabs_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.vertical_tabs_list.customContextMenuRequested.connect(
            self._show_vertical_tab_context_menu
        )
        vl.addWidget(self.vertical_tabs_list, 1)
        return panel

    def _build_find_bar(self):
        bar = QFrame()
        bar.setObjectName("findBarPanel")
        bar.setFixedHeight(40)
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(12, 4, 12, 4)
        hl.setSpacing(6)
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find in page...")
        self.find_input.setFixedWidth(260)
        self.find_input.textChanged.connect(lambda _: self._run_find(forward=True))
        self.find_input.returnPressed.connect(lambda: self._run_find(forward=True))
        self.find_case_cb = QCheckBox("Match case")
        self.find_case_cb.toggled.connect(lambda _: self._run_find(forward=True))
        self.find_status_label = QLabel("")
        self.find_status_label.setStyleSheet("font-size:8.5pt;color:#8b949e;")
        btn_prev = QPushButton("Prev")
        btn_prev.clicked.connect(lambda: self._run_find(forward=False))
        btn_next = QPushButton("Next")
        btn_next.clicked.connect(lambda: self._run_find(forward=True))
        btn_close = QPushButton("✕")
        btn_close.setFixedWidth(28)
        btn_close.clicked.connect(self.close_find_bar)
        for w in (
            self.find_input,
            self.find_case_cb,
            btn_prev,
            btn_next,
            self.find_status_label,
        ):
            hl.addWidget(w)
        hl.addStretch()
        hl.addWidget(btn_close)
        bar.hide()
        return bar

    def _build_tab_strip(self):
        strip = QWidget()
        strip.setObjectName("tabStripPanel")
        hl = QHBoxLayout(strip)
        hl.setContentsMargins(8, 6, 8, 0)
        hl.setSpacing(6)

        self.tab_bar = QTabBar()
        self.tab_bar.setObjectName("chromeTabBar")
        self.tab_bar.setTabsClosable(False)
        self.tab_bar.setMovable(True)
        self.tab_bar.setDocumentMode(True)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.setElideMode(Qt.TextElideMode.ElideRight)
        self.tab_bar.setIconSize(QSize(16, 16))
        self.tab_bar.currentChanged.connect(self.switch_tab)
        self.tab_bar.tabMoved.connect(self.on_tab_moved)
        self.tab_bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_bar.customContextMenuRequested.connect(self.show_tab_context_menu)
        hl.addWidget(self.tab_bar)

        self.new_tab_button = QPushButton()
        self.new_tab_button.setObjectName("newTabButton")
        self.new_tab_button.setFixedSize(28, 28)
        self.new_tab_button.setIconSize(QSize(14, 14))
        self.new_tab_button.setToolTip("New tab (Ctrl+T)")
        self.new_tab_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_tab_button.clicked.connect(lambda: self.add_new_tab(self.home_url))
        hl.addWidget(self.new_tab_button)
        hl.addStretch()
        return strip

    def _build_toolbar(self):
        panel = QWidget()
        panel.setObjectName("toolbarPanel")
        panel.setFixedHeight(46)
        tl = QHBoxLayout(panel)
        tl.setContentsMargins(10, 5, 10, 5)
        tl.setSpacing(6)

        for attr, tip, cb in (
            ("back_button", "Back", self.go_back),
            ("forward_button", "Forward", self.go_forward),
            ("refresh_button", "Reload", self.on_reload_clicked),
            ("home_button", "Home (Start Page)", self.navigate_home),
        ):
            b = self._make_toolbar_button(tip)
            b.clicked.connect(cb)
            setattr(self, attr, b)
            tl.addWidget(b)

        self.address_panel = QWidget()
        self.address_panel.setObjectName("addressPanel")
        self.address_panel.setFixedHeight(36)
        al = QHBoxLayout(self.address_panel)
        al.setContentsMargins(12, 0, 8, 0)
        al.setSpacing(8)
        self.security_icon_btn = QPushButton()
        self.security_icon_btn.setObjectName("securityBtn")
        self.security_icon_btn.setFixedSize(20, 20)
        self.security_icon_btn.setIconSize(QSize(14, 14))
        self.security_icon_btn.setToolTip("Site connection security")
        self.url_input = QLineEdit()
        self.url_input.setObjectName("omniboxInput")
        self.url_input.setPlaceholderText(
            f"Search {self.search_engine} or enter web address..."
        )
        self.url_input.setFrame(False)
        self.url_input.returnPressed.connect(self.navigate_to_url)
        self.bookmark_button = QPushButton()
        self.bookmark_button.setObjectName("bookmarkStarBtn")
        self.bookmark_button.setFixedSize(28, 28)
        self.bookmark_button.setIconSize(QSize(16, 16))
        self.bookmark_button.setToolTip("Bookmark this page")
        self.bookmark_button.clicked.connect(self.toggle_bookmark_current_page)
        self.zoom_badge_btn = QPushButton("100%")
        self.zoom_badge_btn.setToolTip("Reset page zoom (Ctrl+0)")
        self.zoom_badge_btn.setStyleSheet(
            "background:rgba(128,128,128,0.18);border:none;border-radius:10px;padding:2px 8px;font-size:8pt;"
        )
        self.zoom_badge_btn.clicked.connect(self.reset_zoom)
        self.zoom_badge_btn.hide()
        self.private_badge_label = QLabel("PRIVATE")
        self.private_badge_label.setStyleSheet(
            "background:#6d28d9;color:#fff;border-radius:8px;padding:2px 7px;font-size:7.5pt;font-weight:700;"
        )
        self.private_badge_label.setVisible(self.private_mode)
        al.addWidget(self.security_icon_btn)
        al.addWidget(self.private_badge_label)
        al.addWidget(self.url_input, 1)
        al.addWidget(self.zoom_badge_btn)
        al.addWidget(self.bookmark_button)
        tl.addWidget(self.address_panel, 1)

        right_buttons = [
            (
                "reader_button",
                "Reader Mode (Ctrl+Shift+R)",
                self.toggle_reader_mode,
                True,
            ),
            (
                "split_button",
                "Split View Side-by-Side (Ctrl+\\)",
                self.toggle_split_view,
                True,
            ),
            (
                "vertical_tabs_button",
                "Vertical Tabs Sidebar (Ctrl+Shift+V)",
                self.toggle_vertical_tabs,
                True,
            ),
            (
                "command_button",
                "Command Palette (Ctrl+K)",
                self.open_command_palette,
                False,
            ),
            (
                "gpu_button",
                "GPU / VRAM - Opens Optimizations",
                self.open_optimizations_dialog,
                False,
            ),
            (
                "optimizations_button",
                "Optimizations - VRAM + Hibernation + RAM Trim",
                self.open_optimizations_dialog,
                False,
            ),
            (
                "translate_button",
                "Translate Page",
                self.toggle_translation_bubble,
                False,
            ),
            (
                "userscript_button",
                "Userscripts (.user.js)",
                self.open_userscript_manager_dialog,
                False,
            ),
            (
                "proxy_button",
                "Proxy & DNS (Network)",
                self.open_network_settings_dialog,
                False,
            ),
            (
                "blockers_button",
                "Blockers and Filters",
                self.open_block_manager_dialog,
                False,
            ),
            (
                "passwords_button",
                "Password Manager (Saved logins)",
                self.open_password_manager_dialog,
                False,
            ),
            (
                "downloads_button",
                "Downloads (Ctrl+J)",
                self.toggle_downloads_bubble,
                False,
            ),
            ("menu_button", "Menu & More Tools", self.show_main_menu, False),
        ]
        for attr, tip, cb, checkable in right_buttons:
            b = self._make_toolbar_button(tip)
            if checkable:
                b.setCheckable(True)
            b.clicked.connect(cb)
            setattr(self, attr, b)
            tl.addWidget(b)
        self.vertical_tabs_button.setChecked(self.vertical_tabs_enabled)

        self._build_main_menu()
        QTimer.singleShot(0, self.apply_toolbar_config)
        return panel

    def _build_main_menu(self):
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        self.menu = QMenu(self)

        self.menu.addAction("New Tab\tCtrl+T", lambda: self.add_new_tab(self.home_url))
        self.menu.addAction(
            "New Private Window\tCtrl+Shift+N", self.open_private_window
        )
        self.menu.addAction("Reopen Closed Tab\tCtrl+Shift+T", self.reopen_closed_tab)
        self.menu.addAction("Home Page", self.navigate_home)
        self.menu.addSeparator()

        self.menu.addAction("Find in Page...\tCtrl+F", self.toggle_find_bar)
        self.menu.addAction("Command Palette...\tCtrl+K", self.open_command_palette)

        zoom_menu = self.menu.addMenu("Zoom & Screen")
        zoom_menu.addAction("Zoom In\tCtrl++", lambda: self.adjust_zoom(0.1))
        zoom_menu.addAction("Zoom Out\tCtrl+-", lambda: self.adjust_zoom(-0.1))
        zoom_menu.addAction("Reset Zoom (100%)\tCtrl+0", self.reset_zoom)
        zoom_menu.addSeparator()
        zoom_menu.addAction("Fullscreen\tF11", self.toggle_fullscreen)
        self.menu.addSeparator()

        view_menu = self.menu.addMenu("Tabs & Layout")
        view_menu.addAction(
            "Split View (Side-by-Side)\tCtrl+\\", self.toggle_split_view
        )
        self.vertical_tabs_action = view_menu.addAction(
            "Vertical Tabs Sidebar\tCtrl+Shift+V", self.toggle_vertical_tabs
        )
        self.vertical_tabs_action.setCheckable(True)
        view_menu.addSeparator()
        view_menu.addAction("Toggle Reader Mode\tCtrl+Shift+R", self.toggle_reader_mode)
        view_menu.addAction("Reader Mode Settings...", self.open_reader_settings_dialog)

        tools_menu = self.menu.addMenu("Page & Media Tools")
        tools_menu.addAction("Translate Page", self.toggle_translation_bubble)
        tools_menu.addAction(
            "Capture Screenshot\tCtrl+Shift+S", self.capture_page_screenshot
        )
        tools_menu.addAction(
            "Copy Clean URL (No Trackers)", self.copy_clean_current_url
        )
        tools_menu.addSeparator()
        tools_menu.addAction(
            "Userscript Manager (.user.js)...", self.open_userscript_manager_dialog
        )

        library_menu = self.menu.addMenu("Library & Session")
        library_menu.addAction("Bookmarks Manager", self.open_bookmarks_dialog)
        library_menu.addAction("Password Manager", self.open_password_manager_dialog)
        library_menu.addAction("Downloads\tCtrl+J", self.open_downloads_dialog)
        library_menu.addAction("Scan File for Viruses...", self.scan_local_file_dialog)
        library_menu.addAction("History\tCtrl+H", self.open_history_dialog)
        library_menu.addSeparator()
        self.restore_session_action = library_menu.addAction(
            "Continue Where I Left Off"
        )
        self.restore_session_action.setCheckable(True)
        self.restore_session_action.triggered.connect(
            lambda chk: self.save_setting("restore_session", chk)
        )
        library_menu.addAction(
            "Restore Previous Session Now", self.restore_previous_session
        )

        privacy_menu = self.menu.addMenu("Privacy, Blocker & Network")
        privacy_menu.addAction(
            "Blockers & Filters (Ad / NSFW)...", self.open_block_manager_dialog
        )
        privacy_menu.addAction("Scan File for Viruses...", self.scan_local_file_dialog)
        self.strip_trackers_action = privacy_menu.addAction("Strip Tracking URL Params")
        self.strip_trackers_action.setCheckable(True)
        self.strip_trackers_action.triggered.connect(
            lambda chk: self.save_setting("strip_tracking_params", chk)
        )
        self.https_only_action = privacy_menu.addAction("HTTPS-Only Mode")
        self.https_only_action.setCheckable(True)
        self.https_only_action.triggered.connect(
            lambda chk: self.save_setting("https_only_mode", chk)
        )
        privacy_menu.addSeparator()
        privacy_menu.addAction(
            "Network, Proxy & DNS...", self.open_network_settings_dialog
        )
        privacy_menu.addAction(
            "Performance & RAM Optimizations...", self.open_optimizations_dialog
        )
        privacy_menu.addAction("Clear Browsing Cookies", self.clear_cookies)

        appearance_menu = self.menu.addMenu("Appearance & Settings")
        self.dark_mode_action = appearance_menu.addAction("Dark Mode")
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)
        self.color_action = appearance_menu.addAction(
            "Color Customization...", self.open_color_customizer_dialog
        )
        self.color_action.setIcon(
            render_svg_icon(SVG_ICONS["palette"], theme["icon_color"], 14)
        )
        appearance_menu.addAction(
            "Customize Toolbar (Pin / Unpin)...", self.open_toolbar_customizer_dialog
        )
        search_menu = appearance_menu.addMenu("Search Engine")
        self.search_engine_actions = {}
        for eng_key in SEARCH_ENGINES:
            act = search_menu.addAction(
                eng_key, lambda chk=False, k=eng_key: self.set_search_engine(k)
            )
            act.setCheckable(True)
            act.setChecked(eng_key == self.search_engine)
            self.search_engine_actions[eng_key] = act
        appearance_menu.addSeparator()
        reg_lbl = (
            "Windows Registry: Registered (Protected)"
            if is_browser_registered()
            else "Register as Windows Default Browser"
        )
        self.reg_action = appearance_menu.addAction(
            reg_lbl, self.toggle_or_view_registry_status
        )

        self.menu.addSeparator()
        self.menu.addAction("Exit EcoBrowser", self.close)

    def set_search_engine(self, engine_key):
        if engine_key in SEARCH_ENGINES:
            self.search_engine = engine_key
            self.save_setting("search_engine", engine_key)
            self.home_url = SEARCH_ENGINES[engine_key]["home_url"]
            self.url_input.setPlaceholderText(
                f"Search {engine_key} or enter web address..."
            )
            for k, act in getattr(self, "search_engine_actions", {}).items():
                act.setChecked(k == engine_key)

    def open_color_customizer_dialog(self):
        ColorCustomizerDialog(self).exec()

    def get_new_tab_url(self):
        if self.settings.get("newtab_enabled", True) and (
            self.settings.get("homepage_url", "eco://newtab") == "eco://newtab"
            or self.home_url == "eco://newtab"
        ):
            return "eco://newtab"
        return self.home_url

    def open_network_settings_dialog(self):
        dlg = NetworkSettingsDialog(self.settings, self)
        if (
            dlg.exec() == QDialog.DialogCode.Accepted
            and dlg.values is not None
            and self.save_setting_batch(dlg.values)
        ):
            QMessageBox.information(
                self,
                "Network settings saved",
                "DNS and proxy settings saved. Restart EcoBrowser to apply.",
            )

    def toggle_or_view_registry_status(self):
        if sys.platform != "win32" or reg is None:
            QMessageBox.information(
                self,
                "Windows Registry",
                "Windows Registry integration is only available on Windows.",
            )
            return
        if is_browser_registered():
            QMessageBox.information(
                self,
                "Registry Status",
                "EcoBrowser is already registered in the Windows Registry.",
            )
        elif register_as_browser(force=True):
            QMessageBox.information(
                self,
                "Registry Registration",
                "EcoBrowser registered in Windows Registry.",
            )
            if hasattr(self, "reg_action"):
                self.reg_action.setText("Windows Registry: Registered (Protected)")
        else:
            QMessageBox.warning(
                self, "Registry Registration", "Could not write to Windows Registry."
            )

    def show_main_menu(self):
        self.dark_mode_action.setChecked(self.is_dark_mode)
        self.vertical_tabs_action.setChecked(self.vertical_tabs_enabled)
        self.strip_trackers_action.setChecked(
            bool(self.settings.get("strip_tracking_params", True))
        )
        self.https_only_action.setChecked(
            bool(self.settings.get("https_only_mode", False))
        )
        self.restore_session_action.setChecked(
            bool(self.settings.get("restore_session", False))
        )
        for k, act in getattr(self, "search_engine_actions", {}).items():
            act.setChecked(k == self.search_engine)
        if hasattr(self, "reg_action"):
            self.reg_action.setText(
                "Windows Registry: Registered (Protected)"
                if is_browser_registered()
                else "Register as Windows Default Browser"
            )
        self.menu.exec(
            self.menu_button.mapToGlobal(self.menu_button.rect().bottomRight())
        )

    def _build_bookmarks_bar(self):
        bar = QWidget()
        bar.setObjectName("bookmarksBarPanel")
        bar.setFixedHeight(30)
        self.bookmarks_layout = QHBoxLayout(bar)
        self.bookmarks_layout.setContentsMargins(10, 2, 10, 2)
        self.bookmarks_layout.setSpacing(6)
        self.bookmarks_layout.addStretch()
        return bar

    def _make_toolbar_button(self, tooltip=""):
        btn = QPushButton()
        btn.setProperty("class", "toolbarBtn")
        btn.setFixedSize(32, 32)
        btn.setIconSize(QSize(18, 18))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            btn.setToolTip(tooltip)
        return btn

    def apply_theme(self):
        theme = dict(DARK_THEME if self.is_dark_mode else LIGHT_THEME)
        accent = getattr(self, "custom_accent", theme["accent_blue"])
        theme["accent_blue"] = accent
        theme["progress_fill"] = accent
        self.setStyleSheet(self._build_stylesheet(theme, accent))
        self.update_all_icons()
        for i in range(self.stack.count()):
            v = self.stack.widget(i)
            if v:
                self._sync_reader_dark_state(v)
            if isinstance(v, QWebEngineView):
                v.page().settings().setAttribute(
                    QWebEngineSettings.WebAttribute.ForceDarkMode, self.is_dark_mode
                )
        self._refresh_reader_button_ui()
        if hasattr(self, "reader_mini_fab"):
            self.reader_mini_fab.setStyleSheet(
                f"QPushButton#readerMiniFab{{background:{theme['toolbar_bg']};color:{theme['text_primary']};border:1px solid {theme['divider']};border-radius:18px;font-weight:bold;font-size:14pt;}}"
                f"QPushButton#readerMiniFab:hover{{background:{accent};color:white;border-color:{accent};}}"
            )
        self._update_all_tab_close_buttons()

    def update_all_icons(self):
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        ic = theme["icon_color"]
        accent = getattr(self, "custom_accent", theme["accent_blue"])
        self.back_button.setIcon(render_svg_icon(SVG_ICONS["back"], ic, 18))
        self.forward_button.setIcon(render_svg_icon(SVG_ICONS["forward"], ic, 18))
        self.refresh_button.setIcon(
            render_svg_icon(SVG_ICONS["stop" if self.is_loading else "reload"], ic, 18)
        )
        if hasattr(self, "home_button"):
            self.home_button.setIcon(render_svg_icon(SVG_ICONS["home"], ic, 18))
        self.new_tab_button.setIcon(render_svg_icon(SVG_ICONS["new_tab"], ic, 14))
        has_dl = any(
            d.state() == QWebEngineDownloadRequest.DownloadState.DownloadInProgress
            for d in self.active_downloads
        )
        self.downloads_button.setIcon(
            render_svg_icon(SVG_ICONS["download"], accent if has_dl else ic, 18)
        )
        self.menu_button.setIcon(render_svg_icon(SVG_ICONS["menu"], ic, 18))

        cur = self.get_current_view()
        is_https = (
            cur.url().toString().startswith("https://")
            if cur and not getattr(cur, "_is_hibernated_placeholder", False)
            else True
        )
        self.security_icon_btn.setIcon(
            render_svg_icon(
                SVG_ICONS["lock" if is_https else "unlock"],
                theme["text_secondary"] if is_https else "#f85149",
                14,
            )
        )

        self._refresh_reader_button_ui()
        for attr, icon_name in (
            ("split_button", "split"),
            ("vertical_tabs_button", "sidebar"),
            ("command_button", "command"),
            ("userscript_button", "code"),
            ("proxy_button", "proxy"),
            ("blockers_button", "shield"),
            ("translate_button", "globe"),
            ("gpu_button", "gpu"),
            ("optimizations_button", "gpu"),
        ):
            btn = getattr(self, attr, None)
            if btn:
                btn.setIcon(render_svg_icon(SVG_ICONS[icon_name], ic, 18))
        if hasattr(self, "passwords_button"):
            host = cur.url().host().lower() if cur and hasattr(cur, "url") else ""
            saved = bool(
                self.password_manager and self.password_manager.has_credential(host)
            )
            self.passwords_button.setIcon(
                render_svg_icon(
                    SVG_ICONS["key_filled" if saved else "key"],
                    accent if saved else ic,
                    18,
                )
            )

    def toggle_dark_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        self.save_theme_setting(self.is_dark_mode)
        self.apply_theme()

    def clear_cookies(self):
        if hasattr(self, "profile") and self.profile:
            self.profile.cookieStore().deleteAllCookies()
            QMessageBox.information(
                self, "Cookies Cleared", "All browser cookies cleared successfully."
            )

    def settings_file_path(self):
        return os.path.join(get_app_data_folder(), "settings.json")

    def load_all_settings(self):
        return load_saved_settings()

    def save_setting(self, key, value):
        self.save_setting_batch({key: value})

    def save_settings_batch(self, updates):
        return self.save_setting_batch(updates)

    def save_settings(self):
        return self.save_setting_batch(self.settings)

    def save_setting_batch(self, updates):
        current = self.load_all_settings()
        current.update(updates)
        try:
            stored = prepare_settings_for_storage(current)
            with open(self.settings_file_path(), "w", encoding="utf-8") as f:
                json.dump(stored, f, indent=4)
        except Exception as error:
            QMessageBox.warning(
                self,
                "Could not save settings securely",
                f"EcoBrowser could not save these settings:\n{error}",
            )
            return False
        self.settings = current
        return True

    def load_theme_setting(self):
        return self.load_all_settings().get("dark_mode", True)

    def save_theme_setting(self, is_dark):
        self.save_setting("dark_mode", is_dark)

    def _setup_tab_close_button(self, index):
        btn = QPushButton()
        btn.setFixedSize(20, 20)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        btn.setIcon(
            render_svg_icon(SVG_ICONS["tab_close"], theme["close_icon_color"], 10)
        )
        btn.setIconSize(QSize(10, 10))
        btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;border-radius:10px;margin-right:4px;}}QPushButton:hover{{background:{theme['close_btn_hover']};}}"
        )
        btn.clicked.connect(lambda _, b=btn: self._on_close_button_clicked(b))
        self.tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, btn)

    def _on_close_button_clicked(self, button):
        for i in range(self.tab_bar.count()):
            if self.tab_bar.tabButton(i, QTabBar.ButtonPosition.RightSide) == button:
                self.close_tab(i)
                break

    def _update_all_tab_close_buttons(self):
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        for i in range(self.tab_bar.count()):
            btn = self.tab_bar.tabButton(i, QTabBar.ButtonPosition.RightSide)
            if isinstance(btn, QPushButton):
                btn.setIcon(
                    render_svg_icon(
                        SVG_ICONS["tab_close"], theme["close_icon_color"], 10
                    )
                )

    @staticmethod
    def _build_stylesheet(theme, custom_accent=None):
        accent = custom_accent or theme.get("accent_blue", "#0969da")
        return f"""
            QMainWindow{{background-color:{theme['window_bg']};font-family:"Segoe UI",-apple-system,sans-serif}}
            QWidget#tabStripPanel{{background-color:{theme['tabstrip_bg']};border:none}}
            QTabBar{{background:transparent;border:none;qproperty-drawBase:0}}
            QTabBar::tab{{background:transparent;color:{theme['text_secondary']};border-top-left-radius:10px;border-top-right-radius:10px;min-width:140px;max-width:240px;height:34px;padding:0 32px 0 12px;margin-right:2px;font-size:9.5pt}}
            QTabBar::tab:!selected{{border-right:1px solid {theme['tab_divider']}}}
            QTabBar::tab:hover:!selected{{background:{theme['tab_inactive_hover']};color:{theme['text_primary']}}}
            QTabBar::tab:selected{{background:{theme['tab_active_bg']};color:{theme['text_primary']};font-weight:600;border-top:2px solid {accent}}}
            QPushButton#newTabButton,QPushButton[class="toolbarBtn"],QPushButton#bookmarkStarBtn{{background:transparent;border:none;border-radius:14px}}
            QPushButton#newTabButton:hover,QPushButton[class="toolbarBtn"]:hover,QPushButton#bookmarkStarBtn:hover{{background:{theme['hover_bg']}}}
            QWidget#toolbarPanel,QWidget#bookmarksBarPanel{{background:{theme['toolbar_bg']};border-bottom:1px solid {theme['divider']}}}
            QWidget#addressPanel{{background:{theme['omnibox_bg']};border-radius:18px;border:1px solid {theme['divider']}}}
            QWidget#addressPanel:hover{{background:{theme['omnibox_hover_bg']};border-color:{accent}}}
            QLineEdit#omniboxInput,QPushButton#securityBtn{{background:transparent;color:{theme['text_primary']};border:none;font-size:9.5pt}}
            QWidget#bookmarksBarPanel QPushButton{{color:{theme['text_primary']};background:transparent;font-size:8.5pt;padding:4px 10px;border:none;border-radius:6px}}
            QWidget#bookmarksBarPanel QPushButton:hover{{background:{theme['hover_bg']}}}
            QFrame#downloadsBubbleCard{{background:{theme['menu_bg']};border:1px solid {theme['divider']};border-radius:12px}}
            QFrame#downloadItemCard{{background:transparent;border-radius:8px;padding:4px 6px}}
            QFrame#downloadItemCard:hover{{background:{theme['hover_bg']}}}
            QProgressBar#downloadProgressBar{{background:{theme['progress_bg']};border:none;border-radius:2px;height:4px}}
            QProgressBar#downloadProgressBar::chunk{{background:{accent};border-radius:2px}}
            QPushButton.downloadActionBtn{{background:transparent;color:{accent};border:none;font-size:8.5pt;font-weight:500;padding:3px 6px;border-radius:4px}}
            QMenu{{background:{theme['menu_bg']};color:{theme['text_primary']};border:1px solid {theme['divider']};padding:6px 0;border-radius:8px}}
            QMenu::item{{padding:6px 24px 6px 20px;font-size:9.5pt}}
            QMenu::item:selected{{background:{theme['hover_bg']}}}
            QDialog{{background:{theme['toolbar_bg']};color:{theme['text_primary']}}}
            QGroupBox{{color:{theme['text_primary']};font-weight:600;border:1px solid {theme['divider']};border-radius:8px;margin-top:10px;padding-top:14px}}
            QGroupBox::title{{subcontrol-origin:margin;left:10px;padding:0 4px}}
            QCheckBox{{color:{theme['text_primary']};font-size:9.5pt}}
            QDialog QPushButton{{background:{theme['omnibox_bg']};color:{theme['text_primary']};border:1px solid {theme['divider']};border-radius:6px;padding:6px 16px;font-size:9pt}}
            QDialog QPushButton:hover{{background:{theme['hover_bg']}}}
            QFrame#verticalTabsPanel{{background:{theme['tabstrip_bg']};border-right:1px solid {theme['divider']}}}
            QListWidget#verticalTabsList{{background:transparent;border:none;color:{theme['text_primary']};outline:none}}
            QListWidget#verticalTabsList::item{{padding:7px 8px;border-radius:8px;margin:2px 0}}
            QListWidget#verticalTabsList::item:selected{{background:{theme['tab_active_bg']};border-left:3px solid {accent};font-weight:600}}
            QListWidget#verticalTabsList::item:hover:!selected{{background:{theme['hover_bg']}}}
            QFrame#findBarPanel{{background:{theme['toolbar_bg']};border-bottom:1px solid {theme['divider']}}}
            QFrame#findBarPanel QLineEdit{{background:{theme['omnibox_bg']};color:{theme['text_primary']};border:1px solid {theme['divider']};border-radius:6px;padding:4px 8px}}
            QFrame#findBarPanel QPushButton{{background:{theme['omnibox_bg']};color:{theme['text_primary']};border:1px solid {theme['divider']};border-radius:6px;padding:4px 10px}}
        """

    def get_current_view(self):
        return self.stack.currentWidget()

    def _create_web_view(self):
        web_view = QWebEngineView()
        web_view.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        web_view._last_active = time.time()
        page = EcoWebEnginePage(self.profile, self, web_view)
        web_view.setPage(page)
        page.renderProcessTerminated.connect(
            lambda st, code, v=web_view: self.handle_render_crash(v, st, code)
        )
        if self.is_dark_mode:
            web_view.page().settings().setAttribute(
                QWebEngineSettings.WebAttribute.ForceDarkMode, True
            )
        web_view.urlChanged.connect(
            lambda _u, v=web_view: (
                self.sync_address_bar(v) if not is_view_deleted(v) else None
            )
        )
        web_view.titleChanged.connect(
            lambda t, v=web_view: (
                self.update_tab_title(t, v) if not is_view_deleted(v) else None
            )
        )
        web_view.iconChanged.connect(
            lambda ic, v=web_view: (
                self.sync_tab_icon(v, ic) if not is_view_deleted(v) else None
            )
        )
        web_view.loadStarted.connect(
            lambda v=web_view: (
                self.handle_load_started(v) if not is_view_deleted(v) else None
            )
        )
        return web_view

    def add_new_tab(self, url):
        try:
            cur = self.stack.currentIndex() if hasattr(self, "stack") else -1
            if cur != -1 and self.stack.count() >= 1:
                self.hibernate_tab_to_disk(cur)
            if not url or not isinstance(url, str) or len(url) > 2000:
                url = self.home_url

            web_view = self._create_web_view()
            web_view.loadFinished.connect(
                lambda ok, v=web_view: (
                    self.handle_load_finished(v, ok) if not is_view_deleted(v) else None
                )
            )
            stack_idx = self.stack.addWidget(web_view)

            theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
            tab_idx = self.tab_bar.addTab(
                render_svg_icon(SVG_ICONS["globe"], theme["text_secondary"], 16),
                "New Tab",
            )
            self._setup_tab_close_button(tab_idx)
            self.tab_bar.setCurrentIndex(tab_idx)
            self.stack.setCurrentIndex(stack_idx)

            if url == "eco://newtab" or (
                url == self.home_url
                and self.settings.get("newtab_enabled", True)
                and self.settings.get("homepage_url", "eco://newtab") == "eco://newtab"
            ):
                web_view.setHtml(
                    build_new_tab_page_html(self.settings, self.search_engine),
                    QUrl("eco://newtab"),
                )
            else:
                qurl = QUrl(url)
                web_view.setUrl(qurl if qurl.isValid() else QUrl(self.home_url))
            try:
                web_view.setZoomFactor(
                    max(
                        0.25,
                        min(3.0, float(self.settings.get("default_zoom", 100)) / 100.0),
                    )
                )
            except Exception:
                pass
            self._refresh_vertical_tabs()
            return web_view
        except Exception as e:
            print(f"[Tabs] add_new_tab error: {e}")
            return self.get_current_view()

    def handle_render_crash(self, web_view, terminationStatus, exitCode):
        if is_view_deleted(web_view):
            return
        if getattr(self, "crash_manager", None):
            self.crash_manager.handle_crash(web_view, terminationStatus, exitCode)
        else:
            QTimer.singleShot(1000, lambda v=web_view: self._safe_reload_after_crash(v))

    def _safe_reload_after_crash(self, web_view):
        if not is_view_deleted(web_view) and any(
            self.stack.widget(i) == web_view for i in range(self.stack.count())
        ):
            web_view.reload()

    def _periodic_memory_cleanup(self):
        gc.collect()
        if self.stack.count() > 15:
            try:
                self.profile.clearHttpCache()
            except Exception:
                pass

    def _update_tab_activity(self, view):
        if not view or is_view_deleted(view):
            return
        self.tab_last_active[id(view)] = time.time()
        if getattr(view, "_is_hibernated", False):
            self.wake_tab(view)

    def _check_hibernation(self):
        timeout = self.settings.get("hibernation_timeout", 15) * 60
        now, current = time.time(), self.get_current_view()
        cur_id = id(current) if current else None
        for i in range(self.stack.count()):
            v = self.stack.widget(i)
            if (
                v
                and not is_view_deleted(v)
                and id(v) != cur_id
                and not getattr(v, "_is_hibernated", False)
            ):
                if now - self.tab_last_active.get(id(v), now) > timeout:
                    self.hibernate_tab(v)

    def hibernate_tab(self, view):
        if (
            not view
            or is_view_deleted(view)
            or getattr(view, "_is_hibernated", False)
            or self.stack.count() <= 1
        ):
            return
        url = view.url().toString()
        if not url or url.startswith(("eco://", "about:")):
            return
        view._hibernated_url = url
        view._is_hibernated = True
        self.hibernated_tabs[id(view)] = url
        html = (
            f"<html><body style='background:#121418;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif'>"
            f"<div style='text-align:center'><h2>Tab Slept</h2><p>{view.title()[:40]}</p>"
            f"<p style='color:#8b949e;font-size:12px'>{url[:60]}</p><p style='color:#8b949e'>Click tab to wake</p></div></body></html>"
        )
        view.setHtml(html, QUrl("eco://hibernated"))
        self.update_tab_title("[Hibernated] " + (view.title() or "Sleeping"), view)

    def wake_tab(self, view):
        if not getattr(view, "_is_hibernated", False):
            return
        url = getattr(view, "_hibernated_url", None)
        if url:
            view._is_hibernated = False
            view.setUrl(QUrl(url))
            self.tab_last_active[id(view)] = time.time()

    PYTHON_ADULT_KEYWORDS = [
        "porn",
        "xxx",
        "hentai",
        "nsfw",
        "erotic",
        "nude",
        "naked",
        "sexvideo",
        "onlyfans",
        "fetish",
        "bdsm",
        "blowjob",
        "handjob",
        "cumshot",
        "orgy",
        "masturbate",
        "escort",
        "hardcore",
        "incest",
        "pornhub",
        "xvideos",
        "xnxx",
        "youporn",
        "xhamster",
        "chaturbate",
        "stripchat",
        "bongacams",
        "brazzers",
        "rule34",
        "pussy",
        "dick",
        "cock",
        "boobs",
        "anal",
    ]
    PYTHON_ADULT_ALLOW_HOSTS = [
        "wikipedia.org",
        "youtube.com",
        "github.com",
        "stackoverflow.com",
    ]

    def toggle_translation_bubble(self):
        view = self.get_current_view()
        if not view:
            return
        url = view.url().toString()
        if not url or url.startswith(("eco://", "about:", "data:")):
            QMessageBox.information(self, "Translate", "Cannot translate this page")
            return
        lang_names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "ar": "Arabic",
            "tr": "Turkish",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "pt": "Portuguese",
            "it": "Italian",
            "hi": "Hindi",
            "ur": "Urdu",
        }
        items = [f"{name} ({code})" for code, name in lang_names.items()]
        item, ok = QInputDialog.getItem(
            self, "Google Translate", "Translate page to:", items, 0, False
        )
        if ok and item:
            m = re.search(r"\((\w+)\)", item)
            tl = m.group(1) if m else "en"
            self.add_new_tab(
                f"https://translate.google.com/translate?sl=auto&tl={tl}&u={quote(url, safe='')}"
            )

    def translate_current_page(self, target_lang="en"):
        view = self.get_current_view()
        if not view:
            return
        url = view.url().toString()
        if not url or url.startswith(("eco://", "about:")):
            QMessageBox.information(
                self, "Translate", "Cannot translate internal pages"
            )
            return
        view.page().runJavaScript(ECO_TRANSLATE_JS)
        QTimer.singleShot(
            600,
            lambda v=view, l=target_lang: (
                v.page().runJavaScript(f"window.__ecoTranslate('{l}')")
                if not is_view_deleted(v)
                else None
            ),
        )

    def open_translation_dialog(self):
        langs = [
            "en - English",
            "es - Spanish",
            "fr - French",
            "de - German",
            "ar - Arabic",
            "hi - Hindi",
            "tr - Turkish",
            "ru - Russian",
            "zh - Chinese",
            "ja - Japanese",
            "pt - Portuguese",
            "it - Italian",
            "ko - Korean",
            "nl - Dutch",
            "pl - Polish",
            "ur - Urdu",
        ]
        lang, ok = QInputDialog.getItem(
            self, "Translate Page", "Select target language:", langs, 0, False
        )
        if ok and lang:
            self.translate_current_page(lang.split(" - ")[0])
            self.toggle_translation_bubble()

    def _get_blocking_level(self):
        try:
            return int(self.settings.get("blocking_level", 2))
        except Exception:
            return 2

    def _python_check_adult_block(self, view, plain_text, url, host):
        if (
            self._get_blocking_level() < 2
            or not view
            or is_view_deleted(view)
            or not plain_text
            or len(plain_text) < 100
        ):
            return
        if (
            host
            and any(
                host == a or host.endswith("." + a)
                for a in self.PYTHON_ADULT_ALLOW_HOSTS
            )
        ) or url.startswith(("eco://", "about:", "data:")):
            return
        sample = plain_text[:20000].lower()
        for kw in self.PYTHON_ADULT_KEYWORDS:
            found = (
                bool(re.search(r"\b" + re.escape(kw) + r"\b", sample, re.I))
                if len(kw) <= 3
                else (kw in sample)
            )
            if found:
                if getattr(view, "_python_blocked", False):
                    return
                view._python_blocked = True
                view.setHtml(
                    build_blocked_page_html(
                        host, f"SafeShield: Keyword '{kw}' Blocked"
                    ),
                    QUrl("eco://blocked"),
                )
                return

    def _python_adult_block_check(self, view):
        if (
            not view
            or is_view_deleted(view)
            or not self.settings.get("nude_block_enabled", True)
        ):
            return
        url, host = view.url().toString(), view.url().host().lower()
        if url and not url.startswith(("eco://", "about:")):
            view.page().toPlainText(
                lambda text: self._python_check_adult_block(view, text, url, host)
            )

    def _python_password_manager_check(self, view):
        if (
            not view
            or is_view_deleted(view)
            or not getattr(self, "password_manager", None)
            or not self.settings.get("password_manager_enabled", True)
        ):
            return
        self._try_autofill_passwords(view)
        js_detect = """(function(){if(window._ecoPassPython)return;window._ecoPassPython=1;
const getEm=()=>{try{return window._ecoSavedEmail||localStorage.getItem('eco_last_email');}catch(e){return null;}};
const setEm=v=>{try{if(v&&v.length>1){window._ecoSavedEmail=v;localStorage.setItem('eco_last_email',v);}}catch(e){}};
const vis=el=>{try{let s=getComputedStyle(el),r=el.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&(r.width>0||r.height>0||document.activeElement===el);}catch(e){return !!el;}};
const findU=()=>{for(let s of ['#identifierId','input[name="identifier"]','input[type="email"]','input[autocomplete="email"]','input[autocomplete="username"]','input[name*="email" i]','input[name*="user" i]']){let el=document.querySelector(s);if(el&&vis(el)&&el.value?.trim())return el;}return null;};
const findP=()=>{for(let s of ['input[name="Passwd"]','#password','input[autocomplete="current-password"]','input[type="password"]']){let el=document.querySelector(s);if(el&&vis(el))return el;}return document.querySelector('input[type="password"]');};
const save=()=>{let e=findU(),p=findP();if(e&&!p){setEm(e.value.trim());return;}let ev=(e?.value||'').trim()||getEm()||(document.querySelector('#profileIdentifier,[data-email]')?.textContent||'').trim(),pv=p?.value||'';if(ev&&ev.length>1&&pv.length>=3){console.log('ECO_PASS_SAVE::'+JSON.stringify({email:ev,password:pv,host:location.hostname}));try{window._ecoSavedEmail=null;localStorage.removeItem('eco_last_email');}catch(x){}}};
document.addEventListener('click',ev=>{if(ev.target.closest?.('button,input[type="submit"],div[role="button"]')){setTimeout(save,500);setTimeout(save,1200);}else if(findP()?.value?.length>=3)setTimeout(save,400);},true);
document.addEventListener('submit',()=>{setTimeout(save,300);setTimeout(save,1000);},true);
document.addEventListener('keydown',ev=>{if(ev.key==='Enter'){let e=findU(),p=findP();if(e&&!p)setEm(e.value.trim());if(p&&ev.target===p)setTimeout(save,300);}},true);
setInterval(()=>{let p=findP();if(p&&!p._ecoHooked){p._ecoHooked=1;p.addEventListener('change',save);p.addEventListener('blur',save);}let e=findU();if(e?.value?.trim())setEm(e.value.trim());},1500);
})();"""
        try:
            view.page().runJavaScript(js_detect)
        except Exception:
            pass

    def _python_translate_batch(self, texts, target_lang="en", source_lang="auto"):
        import urllib.parse
        import urllib.request

        uniq_map, uniq_list, idx_map = {}, [], []
        for t in texts:
            tt = t.strip()
            if not tt:
                idx_map.append(-1)
            else:
                if tt not in uniq_map:
                    uniq_map[tt] = len(uniq_list)
                    uniq_list.append(tt)
                idx_map.append(uniq_map[tt])
        if not uniq_list:
            return texts

        chunk_size = 20
        chunks = [
            uniq_list[i : i + chunk_size] for i in range(0, len(uniq_list), chunk_size)
        ]

        def _fetch_single(text):
            q = urllib.parse.urlencode(
                [
                    ("client", "gtx"),
                    ("sl", source_lang),
                    ("tl", target_lang),
                    ("dt", "t"),
                    ("q", text[:1000]),
                ]
            )
            req = urllib.request.Request(
                f"https://translate.googleapis.com/translate_a/single?{q}",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                d = json.loads(r.read().decode("utf-8"))
                return "".join(s[0] for s in d[0] if s and s[0]) or text

        def translate_chunk(chunk):
            try:
                params = [
                    ("client", "gtx"),
                    ("sl", source_lang),
                    ("tl", target_lang),
                    ("dt", "t"),
                ] + [("q", t[:1000]) for t in chunk]
                url = f"https://translate.googleapis.com/translate_a/single?{urllib.parse.urlencode(params, doseq=True)}"
                req = urllib.request.Request(
                    url, headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"}
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, list) and len(data) >= len(chunk):
                    out = []
                    for i, entry in enumerate(data[: len(chunk)]):
                        segs = (
                            entry[0]
                            if isinstance(entry, list)
                            and entry
                            and isinstance(entry[0], list)
                            and entry[0]
                            and isinstance(entry[0][0], list)
                            else entry
                        )
                        tr = (
                            "".join(
                                s[0] for s in segs if isinstance(s, list) and s and s[0]
                            )
                            if isinstance(segs, list)
                            else str(entry[0])
                        )
                        out.append(tr or chunk[i])
                    return out
                if isinstance(data, list) and data and isinstance(data[0], list):
                    first = (
                        "".join(seg[0] for seg in data[0] if seg and seg[0]) or chunk[0]
                    )
                    return [first] + [_fetch_single(t) for t in chunk[1:]]
            except Exception:
                pass
            return chunk

        translated = list(uniq_list)
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = {ex.submit(translate_chunk, c): idx for idx, c in enumerate(chunks)}
            for fut in as_completed(futs):
                idx = futs[fut]
                try:
                    for j, tr in enumerate(fut.result()):
                        if idx * chunk_size + j < len(translated):
                            translated[idx * chunk_size + j] = tr
                except Exception:
                    pass
        return ["" if i == -1 else translated[i] for i in idx_map]

    def _handle_python_translation_request(self, view, target_lang, texts):
        clean_texts = [t.strip()[:500] for t in (texts or [])[:400] if t and t.strip()]
        if not clean_texts:
            return

        def do_translate():
            try:
                js = f"(function(){{let arr={json.dumps(self._python_translate_batch(clean_texts, target_lang), ensure_ascii=False)};if(window.__ecoApplyTranslations)window.__ecoApplyTranslations(arr);}})()"
                QTimer.singleShot(
                    0,
                    lambda v=view, code=js: (
                        v.page().runJavaScript(code) if not is_view_deleted(v) else None
                    ),
                )
            except Exception as e:
                print(f"[FastTranslate] error: {e}")

        threading.Thread(target=do_translate, daemon=True).start()

    def on_tab_moved(self, from_idx, to_idx):
        if from_idx == to_idx:
            return
        w = self.stack.widget(from_idx)
        if w:
            self.stack.removeWidget(w)
            self.stack.insertWidget(to_idx, w)
            self.stack.setCurrentIndex(to_idx)
        self._update_all_tab_close_buttons()
        self._refresh_vertical_tabs()
        if self.get_current_view():
            self.sync_address_bar(self.get_current_view())

    def _build_tab_menu_for_index(self, idx):
        v = self.stack.widget(idx)
        vid = id(v) if v else None
        menu = QMenu(self)
        menu.addAction(
            "Unpin Tab" if vid in self.pinned_tabs else "Pin Tab",
            lambda: self.toggle_pin_tab(idx),
        )
        menu.addAction(
            "Unmute Tab" if vid in self.muted_tabs else "Mute Tab\tCtrl+M",
            lambda: self.toggle_mute_tab(idx),
        )
        menu.addAction("Duplicate Tab", lambda: self.duplicate_tab(idx))
        menu.addAction("Open in Split View", lambda: self.open_in_split_view(idx))
        menu.addAction("Copy Clean URL", lambda: self._copy_clean_url_for_view(v))
        menu.addSeparator()
        if self.closed_tabs:
            menu.addAction("Reopen Closed Tab\tCtrl+Shift+T", self.reopen_closed_tab)
        menu.addAction(
            "Snap Out into New Window", lambda: self.detach_tab_to_window(idx)
        )
        menu.addSeparator()
        if idx > 0:
            menu.addAction("Move Tab Left", lambda: self.move_tab_direction(idx, -1))
        if idx < self.tab_bar.count() - 1:
            menu.addAction("Move Tab Right", lambda: self.move_tab_direction(idx, 1))
        menu.addSeparator()
        close_act = menu.addAction("Close Tab", lambda: self.close_tab(idx))
        close_act.setEnabled(vid not in self.pinned_tabs)
        return menu

    def show_tab_context_menu(self, pos):
        idx = self.tab_bar.tabAt(pos)
        if idx >= 0:
            self._build_tab_menu_for_index(idx).exec(self.tab_bar.mapToGlobal(pos))

    def _show_vertical_tab_context_menu(self, pos):
        item = self.vertical_tabs_list.itemAt(pos)
        if item:
            idx = self.vertical_tabs_list.row(item)
            if 0 <= idx < self.tab_bar.count():
                self._build_tab_menu_for_index(idx).exec(
                    self.vertical_tabs_list.mapToGlobal(pos)
                )

    def move_tab_direction(self, index, direction):
        target = index + direction
        if 0 <= target < self.tab_bar.count():
            self.tab_bar.moveTab(index, target)

    def detach_tab_to_window(self, index):
        if 0 <= index < self.tab_bar.count():
            v = self.stack.widget(index)
            win = EcoBrowserWindow(
                initial_url=(
                    v.url().toString() if v and hasattr(v, "url") else self.home_url
                ),
                private_mode=self.private_mode,
            )
            win.show()
            self._detached_windows = getattr(self, "_detached_windows", []) + [win]
            if self.tab_bar.count() > 1:
                self.close_tab(index, force=True)

    def close_current_tab(self):
        idx = self.tab_bar.currentIndex()
        if idx >= 0:
            self.close_tab(idx)

    def close_tab(self, index, force=False):
        if self.tab_bar.count() <= 1:
            return
        try:
            wv = self.stack.widget(index)
            if not wv or is_view_deleted(wv):
                self.tab_bar.removeTab(index)
                self._refresh_vertical_tabs()
                return
            if not force and id(wv) in self.pinned_tabs:
                return
            if isinstance(wv, QWebEngineView):
                u = wv.url().toString()
                if u and u not in ("about:blank", ""):
                    self.closed_tabs.append({"url": u, "title": wv.title() or u})
                    self.closed_tabs = self.closed_tabs[-25:]
                wv.stop()
                for sig in (
                    wv.urlChanged,
                    wv.titleChanged,
                    wv.iconChanged,
                    wv.loadStarted,
                    wv.loadFinished,
                ):
                    try:
                        sig.disconnect()
                    except Exception:
                        pass
            self.pinned_tabs.discard(id(wv))
            self.muted_tabs.discard(id(wv))
            self.tab_bar.removeTab(index)
            self.stack.removeWidget(wv)
            if isinstance(wv, QWebEngineView):
                page = wv.page()
                if page:
                    wv.setPage(None)
                    page.deleteLater()
            wv.deleteLater()
            QTimer.singleShot(100, gc.collect)
        except Exception as e:
            print(f"[Tabs] close_tab error: {e}")
        for i in range(self.tab_bar.count()):
            self._setup_tab_close_button(i)
        self._refresh_vertical_tabs()

    def open_gpu_info_page(self):
        gpu_html = """<html><head><title>GPU Info - EcoBrowser</title><style>body{font-family:Segoe UI;background:#0d1117;color:#e6edf3;padding:30px}.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin:15px 0}</style></head><body><h1>EcoBrowser GPU Info</h1><div class="card" id="info">Detecting...</div><script>try{let c=document.createElement('canvas'),gl=c.getContext('webgl')||c.getContext('experimental-webgl'),info=document.getElementById('info');if(!gl)info.textContent='WebGL not available';else{let ext=gl.getExtension('WEBGL_debug_renderer_info');info.innerHTML='<h3>Renderer: '+(ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER))+'</h3><p>Vendor: '+(ext?gl.getParameter(ext.UNMASKED_VENDOR_WEBGL):gl.getParameter(gl.VENDOR))+'</p>';}}catch(e){document.getElementById('info').textContent=e;}</script></body></html>"""
        self.add_new_tab("about:blank").setHtml(gpu_html)

    def _get_hibernation_json_path(self, tab_index):
        return os.path.join(self.hibernation_dir, f"tab_{tab_index}.json")

    def _save_tab_state_to_disk(self, tab_index, url, title, scroll_x=0, scroll_y=0):
        path = self._get_hibernation_json_path(tab_index)
        data = {
            "url": url,
            "title": title,
            "scroll_x": scroll_x,
            "scroll_y": scroll_y,
            "saved_at": time.time(),
        }
        return path if _write_json(path, data, indent=None) else None

    def hibernate_tab_to_disk(self, tab_index):
        try:
            if not self.settings.get(
                "disk_hibernation_enabled",
                self.settings.get("hibernation_enabled", False),
            ):
                return False
            if (
                not (0 <= tab_index < self.stack.count())
                or tab_index in self._hibernating
                or tab_index in self.hibernated_tabs
            ):
                return False
            view = self.stack.widget(tab_index)
            if (
                not view
                or is_view_deleted(view)
                or getattr(view, "_is_hibernated_placeholder", False)
            ):
                return False
            url = view.url().toString() if hasattr(view, "url") else ""
            if not url or url in ("about:blank", "eco://newtab", ""):
                return False

            raw_ex = self.settings.get("disk_hibernation_excluded_domains", "") or ""
            excluded = (
                raw_ex
                if isinstance(raw_ex, list)
                else [
                    p.strip().lower()
                    for p in str(raw_ex).replace("\n", ",").split(",")
                    if p.strip()
                ]
            )
            host = (urlparse(url).hostname or url).lower()
            if any(
                host == ex or host.endswith("." + ex) or ex in host or ex in url.lower()
                for ex in excluded
            ):
                return False

            title_clean = (
                (self.tab_bar.tabText(tab_index) if hasattr(self, "tab_bar") else url)
                .replace("[Hibernated]", "")
                .strip()
            )
            self._hibernating.add(tab_index)

            def _on_scroll(scroll_json):
                try:
                    d = json.loads(scroll_json) if isinstance(scroll_json, str) else {}
                    sx, sy = int(d.get("x", 0)), int(d.get("y", 0))
                except Exception:
                    sx, sy = 0, 0
                try:
                    jpath = self._save_tab_state_to_disk(
                        tab_index, url, title_clean, sx, sy
                    )
                    self.hibernated_tabs[tab_index] = {
                        "url": url,
                        "title": title_clean,
                        "scroll_x": sx,
                        "scroll_y": sy,
                        "json_path": jpath,
                    }
                    try:
                        view.page().triggerAction(view.page().WebAction.Stop)
                        view.page().deleteLater()
                    except Exception:
                        pass
                    ph = QWidget()
                    ph._is_hibernated_placeholder = True
                    ph._hibernated_index = tab_index
                    pl = QVBoxLayout(ph)
                    pl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl = QLabel(
                        f"Hibernated - On SSD\n\n{title_clean}\n{url[:80]}\n\nClick tab to restore"
                    )
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl.setWordWrap(True)
                    lbl.setStyleSheet("color:#8b949e;font-size:12px;")
                    pl.addWidget(lbl)
                    self.stack.removeWidget(view)
                    view.deleteLater()
                    self.stack.insertWidget(tab_index, ph)
                    self.tab_bar.setTabText(
                        tab_index, "[Hibernated] " + title_clean[:20]
                    )
                    # Defer working-set trim slightly so the placeholder frame finishes painting tear-free
                    if hasattr(self, "_trim_working_sets"):
                        QTimer.singleShot(250, self._trim_working_sets)
                finally:
                    self._hibernating.discard(tab_index)

            try:
                view.page().runJavaScript(
                    "JSON.stringify({x: window.scrollX, y: window.scrollY})", _on_scroll
                )
            except Exception:
                _on_scroll("{}")
            return True
        except Exception:
            self._hibernating.discard(tab_index)
            return False

    def restore_tab_from_disk(self, tab_index):
        try:
            if tab_index not in self.hibernated_tabs:
                data = _read_json(self._get_hibernation_json_path(tab_index), None)
                if not isinstance(data, dict):
                    return False
                self.hibernated_tabs[tab_index] = data
            info = self.hibernated_tabs.pop(tab_index, None)
            if not info:
                return False
            url, title, sx, sy = (
                info.get("url", ""),
                info.get("title", "New Tab"),
                info.get("scroll_x", 0),
                info.get("scroll_y", 0),
            )
            ph = self.stack.widget(tab_index)
            if ph:
                self.stack.removeWidget(ph)
                ph.deleteLater()
            wv = self._create_web_view()
            wv.loadFinished.connect(
                lambda ok, v=wv, x=sx, y=sy: (
                    self.handle_load_finished(v, ok),
                    (
                        v.page().runJavaScript(f"window.scrollTo({x},{y});")
                        if ok and (x or y)
                        else None
                    ),
                )
            )
            self.stack.insertWidget(tab_index, wv)
            self.tab_bar.setTabText(tab_index, title[:22] if title else "New Tab")
            wv.load(QUrl(url))
            self.tab_last_active[id(wv)] = time.time()
            return True
        except Exception as e:
            print(f"[HIBERNATE-DISK] restore error: {e}")
            return False

    def switch_tab(self, index):
        if index == -1:
            return
        if index in self.hibernated_tabs:
            self.restore_tab_from_disk(index)
        prev = self.stack.currentIndex()
        if prev not in (-1, index) and self.stack.count() > 1:
            self.hibernate_tab_to_disk(prev)
        self.stack.setCurrentIndex(index)
        view = self.get_current_view()
        if view and not getattr(view, "_is_hibernated_placeholder", False):
            view._last_active = time.time()
            QTimer.singleShot(
                500,
                lambda v=view: (
                    self._try_autofill_passwords(v) if not is_view_deleted(v) else None
                ),
            )
            self.back_button.setEnabled(view.history().canGoBack())
            self.forward_button.setEnabled(view.history().canGoForward())
        self.sync_address_bar(view)
        self._refresh_reader_button_ui()
        self._sync_zoom_badge()
        self._refresh_vertical_tabs()

    def _format_tab_label(self, raw_title, view):
        prefix = ""
        if id(view) in getattr(self, "pinned_tabs", set()):
            prefix += "[Pin] "
        if id(view) in getattr(self, "muted_tabs", set()):
            prefix += "[Muted] "
        txt = raw_title or "New Tab"
        limit = max(10, 20 - len(prefix))
        return prefix + (txt[:limit] + "..." if len(txt) > limit + 2 else txt)

    def _refresh_vertical_tabs(self):
        if not hasattr(self, "vertical_tabs_list"):
            return
        self.vertical_tabs_list.blockSignals(True)
        self.vertical_tabs_list.clear()
        for i in range(self.tab_bar.count()):
            it = QListWidgetItem(
                self.tab_bar.tabIcon(i), self.tab_bar.tabText(i) or f"Tab {i + 1}"
            )
            self.vertical_tabs_list.addItem(it)
        cur = self.tab_bar.currentIndex()
        if 0 <= cur < self.vertical_tabs_list.count():
            self.vertical_tabs_list.setCurrentRow(cur)
        self.vertical_tabs_list.blockSignals(False)

    def update_tab_title(self, title, web_view):
        if is_view_deleted(web_view):
            return
        web_view._raw_title = title or "New Tab"
        txt = self._format_tab_label(web_view._raw_title, web_view)
        for i in range(self.stack.count()):
            if self.stack.widget(i) == web_view:
                self.tab_bar.setTabText(i, txt)
                break
        self._refresh_vertical_tabs()

    def sync_tab_icon(self, web_view, icon):
        if not is_view_deleted(web_view) and not icon.isNull():
            for i in range(self.stack.count()):
                if self.stack.widget(i) == web_view:
                    self.tab_bar.setTabIcon(i, icon)
                    break
            self._refresh_vertical_tabs()

    def handle_load_started(self, web_view):
        if not is_view_deleted(web_view) and web_view == self.get_current_view():
            self.is_loading = True
            theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
            self.refresh_button.setIcon(
                render_svg_icon(SVG_ICONS["stop"], theme["icon_color"], 18)
            )

    def handle_load_finished(self, web_view, ok):
        if is_view_deleted(web_view):
            return
        if web_view == self.get_current_view():
            self.is_loading = False
            theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
            self.refresh_button.setIcon(
                render_svg_icon(SVG_ICONS["reload"], theme["icon_color"], 18)
            )
            self.back_button.setEnabled(web_view.history().canGoBack())
            self.forward_button.setEnabled(web_view.history().canGoForward())
        if not ok:
            return
        if self.settings.get("userscripts_enabled", True):
            inj = self.userscript_manager.build_injection_js(web_view.url().toString())
            if inj:
                QTimer.singleShot(
                    300, lambda v=web_view, js=inj: self._inject_userscript(v, js)
                )
        self._python_adult_block_check(web_view)
        self._python_password_manager_check(web_view)
        self._try_autofill_passwords(web_view)
        QTimer.singleShot(1000, self.update_all_icons)
        self._update_reader_button_state(web_view)
        self._sync_reader_dark_state(web_view)

    def _inject_userscript(self, web_view, js_code):
        if web_view and js_code and not is_view_deleted(web_view):
            web_view.page().runJavaScript(js_code)

    def _update_reader_button_state(self, web_view):
        def cb(res):
            self.readable_state[id(web_view)] = bool(res)
            if web_view == self.get_current_view():
                self._refresh_reader_button_ui()

        web_view.page().runJavaScript(
            "typeof window.__ecoReaderIsReadable==='function'?window.__ecoReaderIsReadable():false",
            cb,
        )

    def _sync_reader_dark_state(self, web_view):
        if isinstance(web_view, QWebEngineView):
            web_view.page().runJavaScript(
                f"if(window.__ecoReader)window.__ecoReader.setBrowserDark({str(self.is_dark_mode).lower()});"
            )

    def _refresh_reader_button_ui(self):
        view = self.get_current_view()
        if not view:
            return
        vid = id(view)
        active = self.reader_state.get(vid, False)
        readable = self.readable_state.get(vid, False)
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        self.reader_button.setChecked(active)
        self.reader_button.setIcon(
            render_svg_icon(
                SVG_ICONS["reader_active" if (active or readable) else "reader"],
                theme["accent_blue"] if (active or readable) else theme["icon_color"],
                18,
            )
        )

    def _set_reader_chrome_hidden(self, hidden):
        if not self.settings.get("reader_hide_chrome", True):
            hidden = False
        self.toolbar_panel.setVisible(not hidden)
        self.bookmarks_bar_widget.setVisible(not hidden and bool(self.load_bookmarks()))
        if hidden:
            self.reader_mini_fab.move(12, 12)
            self.reader_mini_fab.show()
            self.reader_mini_fab.raise_()
        else:
            self.reader_mini_fab.hide()

    def toggle_reader_mode(self):
        view = self.get_current_view()
        if not view or not isinstance(view, QWebEngineView):
            return
        rs = json.dumps(
            {
                "font": self.settings.get("reader_font", "serif"),
                "fontSize": self.settings.get("reader_font_size", 19),
                "lineHeight": self.settings.get("reader_line_height", 1.8),
                "width": self.settings.get("reader_width", "medium"),
                "theme": self.settings.get("reader_theme", "auto"),
                "textAlign": self.settings.get("reader_text_align", "start"),
                "isDarkBrowser": self.is_dark_mode,
            }
        )

        def do_toggle():
            js = f"(function(){{if(window.__ecoReader){{window.__ecoReader.updateSettings({rs});window.__ecoReader.toggle();return window.__ecoReader.isActive;}}return false;}})()"

            def cb(is_active):
                vid = id(view)
                self.reader_state[vid] = (
                    is_active
                    if isinstance(is_active, bool)
                    else not self.reader_state.get(vid, False)
                )
                self._refresh_reader_button_ui()
                self._set_reader_chrome_hidden(self.reader_state[vid])

            view.page().runJavaScript(js, cb)

        view.page().runJavaScript(
            "!!window.__ecoReaderInitialized",
            lambda ok: (
                do_toggle()
                if ok
                else view.page().runJavaScript(ECO_READER_JS, lambda _: do_toggle())
            ),
        )

    def _handle_escape_reader(self):
        view = self.get_current_view()
        if view and self.reader_state.get(id(view), False):
            view.page().runJavaScript(
                "if(window.__ecoReader)window.__ecoReader.exit();"
            )
            self.reader_state[id(view)] = False
            self._refresh_reader_button_ui()
        self._set_reader_chrome_hidden(False)

    def apply_reader_settings_to_view(self, web_view):
        if isinstance(web_view, QWebEngineView):
            rs = json.dumps(
                {
                    "font": self.settings.get("reader_font", "serif"),
                    "fontSize": self.settings.get("reader_font_size", 19),
                    "lineHeight": self.settings.get("reader_line_height", 1.8),
                    "width": self.settings.get("reader_width", "medium"),
                    "theme": self.settings.get("reader_theme", "auto"),
                    "textAlign": self.settings.get("reader_text_align", "start"),
                    "isDarkBrowser": self.is_dark_mode,
                }
            )
            web_view.page().runJavaScript(
                f"if(window.__ecoReader)window.__ecoReader.updateSettings({rs});"
            )

    def open_reader_settings_dialog(self):
        ReaderSettingsDialog(self).exec()
        if self.get_current_view():
            self.apply_reader_settings_to_view(self.get_current_view())

    def open_hibernation_settings_dialog(self):
        self.open_optimizations_dialog()

    def open_optimizations_dialog(self):
        dlg = OptimizationsDialog(self.settings, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.values:
            self.settings.update(dlg.values)
            self.save_setting_batch(dlg.values)
            apply_windows_gpu_preference(
                dlg.values.get("gpu_preference", "high_performance")
            )
            if hasattr(self, "_ram_trim_timer"):
                if self.settings.get("ram_trim_enabled", True):
                    self._ram_trim_timer.start(
                        int(self.settings.get("ram_trim_interval", 30)) * 1000
                    )
                else:
                    self._ram_trim_timer.stop()
            QMessageBox.information(
                self,
                "Optimizations",
                "Optimizations saved! Restart for GPU change to take effect.",
            )

    def open_gpu_settings_dialog(self):
        return self.open_optimizations_dialog()

    def open_blocking_level_dialog(self):
        return self.open_optimizations_dialog()

    def open_userscript_manager_dialog(self):
        UserscriptManagerDialog(self).exec()

    def open_toolbar_customizer_dialog(self):
        ToolbarCustomizerDialog(self).exec()

    def apply_toolbar_config(self):
        defaults = DEFAULT_SETTINGS["toolbar_pinned"]
        pinned = self.settings.get("toolbar_pinned", defaults)
        for attr, key in (
            ("back_button", "back"),
            ("forward_button", "forward"),
            ("refresh_button", "reload"),
            ("home_button", "home"),
            ("reader_button", "reader"),
            ("split_button", "split"),
            ("vertical_tabs_button", "vertical_tabs"),
            ("command_button", "command"),
            ("userscript_button", "userscript"),
            ("downloads_button", "downloads"),
            ("proxy_button", "proxy"),
            ("blockers_button", "blockers"),
            ("bookmark_button", "bookmarks"),
            ("passwords_button", "passwords"),
            ("gpu_button", "gpu"),
            ("optimizations_button", "optimizations"),
            ("translate_button", "translate"),
        ):
            w = getattr(self, attr, None)
            if w:
                w.setVisible(bool(pinned.get(key, defaults.get(key, False))))
        self.update_all_icons()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "reader_mini_fab") and self.reader_mini_fab.isVisible():
            self.reader_mini_fab.move(12, 12)
            self.reader_mini_fab.raise_()

    def on_reload_clicked(self):
        v = self.get_current_view()
        if v and isinstance(v, QWebEngineView):
            v.stop() if self.is_loading else v.reload()

    def go_back(self):
        v = self.get_current_view()
        if v and isinstance(v, QWebEngineView):
            v.back()

    def go_forward(self):
        v = self.get_current_view()
        if v and isinstance(v, QWebEngineView):
            v.forward()

    def navigate_home(self):
        view = self.get_current_view()
        if not view or not isinstance(view, QWebEngineView):
            self.add_new_tab(self.get_new_tab_url())
            return
        target = self.get_new_tab_url()
        if target == "eco://newtab":
            view.setHtml(
                build_new_tab_page_html(self.settings, self.search_engine),
                QUrl("eco://newtab"),
            )
        else:
            view.setUrl(QUrl(target))

    def handle_new_tab_request(self, view):
        if self.settings.get("newtab_enabled", True):
            view.setHtml(
                build_new_tab_page_html(self.settings, self.search_engine),
                QUrl("eco://newtab"),
            )
            return True
        return False

    def navigate_to_url(self):
        text = self.url_input.text().strip()
        view = self.get_current_view()
        if not view or not text or not isinstance(view, QWebEngineView):
            return
        if text.lower() == "eco://newtab":
            view.setHtml(
                build_new_tab_page_html(self.settings, self.search_engine),
                QUrl("eco://newtab"),
            )
            return
        if text.startswith(("http://", "https://", "eco://", "about:")):
            url = text
        elif "." in text and " " not in text:
            url = "https://" + text
        else:
            url = (
                SEARCH_ENGINES.get(self.search_engine, SEARCH_ENGINES["Google"])[
                    "query_url"
                ]
                + text
            )
        view.setUrl(QUrl(url))

    def sync_address_bar(self, web_view):
        if (
            not web_view
            or is_view_deleted(web_view)
            or web_view != self.get_current_view()
            or not isinstance(web_view, QWebEngineView)
        ):
            return
        url = web_view.url().toString()
        self.url_input.setText("" if url == "about:blank" else url)
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        is_https = url.startswith("https://")
        self.security_icon_btn.setIcon(
            render_svg_icon(
                SVG_ICONS["lock" if is_https else "unlock"],
                theme["text_secondary"] if is_https else "#f85149",
                14,
            )
        )
        is_bm = any(b["url"] == url for b in self.load_bookmarks())
        self.bookmark_button.setIcon(
            render_svg_icon(
                SVG_ICONS["star_filled" if is_bm else "star_outline"],
                theme["star_active"] if is_bm else theme["icon_color"],
                16,
            )
        )
        self.log_to_history(url)

    def handle_navigation(self, request, web_view):
        url = request.url()
        host, full = url.host().lower(), url.toString().lower()
        if self._get_blocking_level() == 0:
            request.accept()
            return
        is_ad = self.interceptor.ad_block_enabled and any(
            ad in host for ad in AD_DOMAINS
        )
        is_adult = (
            self._get_blocking_level() >= 2
            and self.interceptor.nude_block_enabled
            and (
                any(d in host for d in ADULT_DOMAINS)
                or any(kw in full for kw in ADULT_KEYWORDS)
            )
        )
        if is_ad or is_adult:
            request.reject()
            html = build_blocked_page_html(
                host or "blocked-site",
                "Ad/Tracker Domain" if is_ad else "Adult / Explicit Domain",
            )
            QTimer.singleShot(0, lambda: web_view.setHtml(html, url))
        else:
            request.accept()

    def history_file_path(self):
        return os.path.join(get_app_data_folder(), "history.txt")

    def log_to_history(self, url):
        if getattr(self, "private_mode", False):
            return
        if url and not url.startswith("data:") and url != "about:blank":
            try:
                with open(self.history_file_path(), "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} - {url}\n")
            except OSError:
                pass

    def open_history_dialog(self):
        HistoryDialog(self.history_file_path(), self).exec()

    def open_block_manager_dialog(self):
        BlockManagerDialog(self.interceptor, self).exec()

    def bookmarks_file_path(self):
        return os.path.join(get_app_data_folder(), "bookmarks.json")

    def load_bookmarks(self):
        data = _read_json(self.bookmarks_file_path(), [])
        return data if isinstance(data, list) else []

    def save_bookmarks(self, bookmarks):
        _write_json(self.bookmarks_file_path(), bookmarks)

    def toggle_bookmark_current_page(self):
        view = self.get_current_view()
        if not view or not isinstance(view, QWebEngineView):
            return
        url, title = view.url().toString(), view.title() or view.url().toString()
        if not url or url == "about:blank":
            return
        bms = self.load_bookmarks()
        if any(b["url"] == url for b in bms):
            bms = [b for b in bms if b["url"] != url]
        else:
            bms.append({"title": title, "url": url})
        self.save_bookmarks(bms)
        self.update_bookmarks_bar()
        self.sync_address_bar(view)

    def delete_bookmark_by_url(self, url):
        self.save_bookmarks([b for b in self.load_bookmarks() if b["url"] != url])
        self.update_bookmarks_bar()

    def open_bookmarks_dialog(self):
        QMessageBox.information(
            self,
            "Bookmarks",
            f"You have {len(self.load_bookmarks())} saved bookmarks in your EcoBrowser bar.",
        )

    def update_bookmarks_bar(self):
        _clear_layout_except_stretch(self.bookmarks_layout)
        bms = self.load_bookmarks()
        if not bms:
            self.bookmarks_bar_widget.hide()
            return
        self.bookmarks_bar_widget.show()
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        ic = render_svg_icon(SVG_ICONS["globe"], theme["text_secondary"], 14)
        for bm in bms:
            t = bm["title"][:18] + "..." if len(bm["title"]) > 20 else bm["title"]
            self.bookmarks_layout.insertWidget(
                self.bookmarks_layout.count() - 1,
                BookmarkButton(t, bm["url"], ic, self),
            )

    def navigate_to_bookmark(self, url):
        v = self.get_current_view()
        if v and isinstance(v, QWebEngineView):
            v.setUrl(QUrl(url))

    def downloads_file_path(self):
        return os.path.join(get_app_data_folder(), "downloads.json")

    def load_downloads(self):
        data = _read_json(self.downloads_file_path(), [])
        return data if isinstance(data, list) else []

    def save_downloads(self, downloads):
        _write_json(self.downloads_file_path(), downloads)

    def _update_download_entry_on_disk(self, updated_entry):
        items = self.load_downloads()
        fp = updated_entry.get("filePath")
        for idx, it in enumerate(items):
            if it.get("filePath") == fp:
                items[idx] = updated_entry
                self.save_downloads(items)
                return
        self.save_downloads(([updated_entry] + items)[:200])

    def _get_safety_worker(self):
        if not hasattr(self, "_download_safety_worker"):
            self._download_safety_worker = DownloadSafetyWorker(self)
            self._download_safety_worker.finished.connect(
                self._on_download_scan_finished
            )
        return self._download_safety_worker

    def _on_download_scan_finished(self, entry, result):
        if not isinstance(entry, dict):
            return
        entry["safetyStatus"] = result.get("status", "safe")
        entry["safetySummary"] = result.get("summary", "")
        entry["safetyDetails"] = result.get("details", [])
        entry["sha256"] = result.get("sha256", "")
        self._update_download_entry_on_disk(entry)
        if self.downloads_bubble and self.downloads_bubble.isVisible():
            self.downloads_bubble.refresh()
        if entry["safetyStatus"] == "dangerous":
            ans = QMessageBox.warning(
                self,
                "Virus / Threat Detected in Download",
                f"EcoBrowser Safety Guard detected a threat in:\n{entry.get('fileName')}\n\n"
                f"{entry.get('safetySummary')}\n\nDelete this file immediately?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if ans == QMessageBox.StandardButton.Yes and os.path.exists(
                entry.get("filePath", "")
            ):
                try:
                    os.remove(entry["filePath"])
                    entry["safetySummary"] = "Threat removed from disk."
                    self._update_download_entry_on_disk(entry)
                    if self.downloads_bubble and self.downloads_bubble.isVisible():
                        self.downloads_bubble.refresh()
                except Exception:
                    pass

    def scan_local_file_dialog(self, parent=None):
        path, _ = QFileDialog.getOpenFileName(
            parent or self, "Select File to Scan for Viruses", "", "All Files (*)"
        )
        if not path:
            return
        res = scan_file_safety(path)
        QMessageBox.information(
            parent or self,
            "File Safety Scan Result",
            f"File: {os.path.basename(path)}\nStatus: {res['status'].upper()}\nEngine: {res['av_engine']}\n"
            f"SHA-256: {res['sha256']}\n\nDetails:\n- " + "\n- ".join(res["details"]),
        )

    def handle_download_request(self, download):
        default_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        suggested = download.suggestedFileName() or "downloaded_file"
        if self.settings.get("download_block_dangerous", True):
            ext = os.path.splitext(suggested)[1].lower()
            if _DANGEROUS_DOUBLE_EXT_RE.search(suggested):
                ans = QMessageBox.warning(
                    self,
                    "Suspicious Download Blocked",
                    f"'{suggested}' uses double-extension spoofing, commonly used by malware.\nDownload anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if ans != QMessageBox.StandardButton.Yes:
                    download.cancel()
                    return
            elif ext in _EXEC_EXTS:
                ans = QMessageBox.question(
                    self,
                    "Executable Download Safety Check",
                    f"'{suggested}' is an executable/installer ({ext}).\nDo you trust this source and want to download it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if ans != QMessageBox.StandardButton.Yes:
                    download.cancel()
                    return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", os.path.join(default_dir, suggested)
        )
        if not save_path:
            download.cancel()
            return
        download.setDownloadDirectory(os.path.dirname(save_path))
        download.setDownloadFileName(os.path.basename(save_path))
        download.accept()
        self.active_downloads[download] = {
            "fileName": os.path.basename(save_path),
            "filePath": save_path,
            "state": "in_progress",
            "receivedBytes": 0,
            "totalBytes": 0,
            "safetyStatus": (
                "scanning" if self.settings.get("download_virus_scan", True) else ""
            ),
            "safetySummary": (
                "Pending virus & safety check..."
                if self.settings.get("download_virus_scan", True)
                else ""
            ),
            "sourceUrl": download.url().toString(),
        }
        download.receivedBytesChanged.connect(
            lambda d=download: self._on_download_progress(d)
        )
        download.stateChanged.connect(
            lambda state, d=download: self._on_download_state_changed(d, state)
        )
        self.update_all_icons()
        self._show_downloads_bubble()

    def _on_download_progress(self, download):
        if download in self.active_downloads:
            e = self.active_downloads[download]
            e["receivedBytes"], e["totalBytes"] = (
                download.receivedBytes(),
                download.totalBytes(),
            )
            if self.downloads_bubble and self.downloads_bubble.isVisible():
                self.downloads_bubble.update_card_progress(download)

    def _on_download_state_changed(self, download, state):
        if download not in self.active_downloads:
            return
        entry = self.active_downloads[download]
        if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            entry["state"], entry["totalBytes"] = "completed", download.totalBytes()
            if self.settings.get("download_virus_scan", True):
                entry["safetyStatus"] = "scanning"
                entry["safetySummary"] = "Scanning file for viruses & threats..."
            self.save_downloads(([entry] + self.load_downloads())[:200])
            del self.active_downloads[download]
            if self.settings.get("download_virus_scan", True):
                self._get_safety_worker().start_scan(
                    entry, entry["filePath"], entry.get("sourceUrl", "")
                )
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
            entry["state"] = "cancelled"
            del self.active_downloads[download]
        self.update_all_icons()
        if self.downloads_bubble and self.downloads_bubble.isVisible():
            self.downloads_bubble.refresh()

    def toggle_downloads_bubble(self):
        if self.downloads_bubble and self.downloads_bubble.isVisible():
            self.downloads_bubble.hide()
        else:
            self._show_downloads_bubble()

    def _show_downloads_bubble(self):
        if self.downloads_bubble is None:
            self.downloads_bubble = DownloadsBubblePopup(self)
        self.downloads_bubble.refresh()
        pos = self.downloads_button.mapToGlobal(
            self.downloads_button.rect().bottomRight()
        )
        self.downloads_bubble.move(pos.x() - self.downloads_bubble.width(), pos.y() + 4)
        self.downloads_bubble.show()

    def _try_autofill_passwords(self, web_view):
        if (
            is_view_deleted(web_view)
            or not getattr(self, "password_manager", None)
            or not self.settings.get("password_manager_enabled", True)
            or not self.settings.get("password_autofill_enabled", True)
        ):
            return
        try:
            host = web_view.url().host()
            if not host or host in ("newtab", "about", "blank"):
                return
            cred = self.password_manager.get_credential(host)
            if not cred or not cred.get("email") or not cred.get("password"):
                return
            js = build_password_autofill_js(cred["email"], cred["password"])
            for ms in (700, 2000, 4000):
                QTimer.singleShot(
                    ms,
                    lambda v=web_view, j=js: (
                        self._inject_autofill(v, j) if not is_view_deleted(v) else None
                    ),
                )
        except Exception:
            pass

    def force_autofill_current_page(self):
        v = self.get_current_view()
        if v:
            self._try_autofill_passwords(v)
            QTimer.singleShot(
                1000,
                lambda: (
                    self._try_autofill_passwords(v) if not is_view_deleted(v) else None
                ),
            )

    def _inject_autofill(self, web_view, js_code):
        if (
            web_view
            and js_code
            and not is_view_deleted(web_view)
            and any(self.stack.widget(i) == web_view for i in range(self.stack.count()))
        ):
            page = web_view.page()
            if page and not is_view_deleted(page):
                page.runJavaScript(js_code)

    def handle_password_save_request(self, data):
        if not getattr(self, "password_manager", None) or not self.settings.get(
            "password_manager_enabled", True
        ):
            return
        host, email, password = (
            data.get("host", "").lower().strip(),
            data.get("email", "").strip(),
            data.get("password", ""),
        )
        origin, href = data.get("origin", ""), data.get("href", "")
        if not (host and email and password):
            return
        now_key, now = f"{host}|{email}|{len(password)}", time.time()
        if (
            getattr(self, "_last_save_key", None) == now_key
            and now - getattr(self, "_last_save_time", 0) < 3
        ):
            return
        self._last_save_key, self._last_save_time = now_key, now
        existing = self.password_manager.get_credential(host)
        if (
            existing
            and existing.get("email") == email
            and existing.get("password") == password
        ):
            return
        if self.settings.get("password_save_prompt", True):
            QTimer.singleShot(
                100,
                lambda: self._prompt_save_password(host, email, password, origin, href),
            )
        else:
            self.password_manager.save_credential(host, email, password, origin, href)

    def _prompt_save_password(self, host, email, password, origin, href):
        msg = QMessageBox(self)
        msg.setWindowTitle("Save Password?")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText(f"Save password for {host}?")
        msg.setInformativeText(
            f"Email/Username: {email}\nPassword: {'•' * min(len(password), 12)}\n\nEcoBrowser will autofill it next time."
        )
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.password_manager.save_credential(host, email, password, origin, href)

    def open_password_manager_dialog(self):
        if not getattr(self, "password_manager", None):
            self.password_manager = PasswordManager(get_app_data_folder())
        PasswordManagerDialog(self.password_manager, self).exec()

    def open_downloads_dialog(self):
        DownloadsDialog(self).exec()

    def open_private_window(self):
        win = EcoBrowserWindow(initial_url=self.home_url, private_mode=True)
        win.show()
        self._private_windows = getattr(self, "_private_windows", []) + [win]

    def open_command_palette(self):
        CommandPaletteDialog(self).exec()

    def reopen_closed_tab(self):
        if not self.closed_tabs:
            return
        entry = self.closed_tabs.pop()
        self.add_new_tab(entry.get("url") or self.home_url)

    def duplicate_tab(self, index):
        if 0 <= index < self.stack.count():
            v = self.stack.widget(index)
            url = (
                v.url().toString()
                if isinstance(v, QWebEngineView)
                else getattr(v, "_hibernated_url", self.home_url)
            )
            self.add_new_tab(url or self.home_url)

    def toggle_pin_tab(self, index):
        if not (0 <= index < self.stack.count()):
            return
        v = self.stack.widget(index)
        if not v:
            return
        vid = id(v)
        if vid in self.pinned_tabs:
            self.pinned_tabs.discard(vid)
        else:
            self.pinned_tabs.add(vid)
        self.update_tab_title(getattr(v, "_raw_title", self.tab_bar.tabText(index)), v)

    def toggle_mute_tab(self, index):
        if not (0 <= index < self.stack.count()):
            return
        v = self.stack.widget(index)
        if not isinstance(v, QWebEngineView):
            return
        vid = id(v)
        muted = vid not in self.muted_tabs
        if muted:
            self.muted_tabs.add(vid)
        else:
            self.muted_tabs.discard(vid)
        try:
            v.page().setAudioMuted(muted)
        except Exception:
            pass
        self.update_tab_title(getattr(v, "_raw_title", v.title()), v)

    def toggle_mute_current_tab(self):
        self.toggle_mute_tab(self.tab_bar.currentIndex())

    def toggle_vertical_tabs(self):
        self.vertical_tabs_enabled = not self.vertical_tabs_enabled
        self.tab_strip_widget.setVisible(not self.vertical_tabs_enabled)
        self.vertical_tabs_panel.setVisible(self.vertical_tabs_enabled)
        if hasattr(self, "vertical_tabs_button"):
            self.vertical_tabs_button.setChecked(self.vertical_tabs_enabled)
        if not self.private_mode:
            self.save_setting("vertical_tabs", self.vertical_tabs_enabled)
        self._refresh_vertical_tabs()

    def toggle_find_bar(self):
        if self.find_bar_widget.isVisible():
            self.close_find_bar()
            return
        self.find_bar_widget.show()
        self.find_input.setFocus()
        self.find_input.selectAll()

    def close_find_bar(self):
        self.find_bar_widget.hide()
        self.find_status_label.setText("")
        v = self.get_current_view()
        if isinstance(v, QWebEngineView):
            v.findText("")

    def _run_find(self, forward=True):
        v = self.get_current_view()
        if not isinstance(v, QWebEngineView):
            return
        query = self.find_input.text()
        if not query:
            v.findText("")
            self.find_status_label.setText("")
            return
        flags = QWebEnginePage.FindFlag(0)
        if not forward:
            flags |= QWebEnginePage.FindFlag.FindBackward
        if self.find_case_cb.isChecked():
            flags |= QWebEnginePage.FindFlag.FindCaseSensitively
        v.findText(
            query,
            flags,
            lambda found: self.find_status_label.setText(
                "Match found" if found else "No matches"
            ),
        )

    def toggle_split_view(self):
        if self.split_view is not None:
            self._close_split_view()
        else:
            self.open_in_split_view(self.tab_bar.currentIndex())

    def open_in_split_view(self, index):
        v = (
            self.stack.widget(index)
            if 0 <= index < self.stack.count()
            else self.get_current_view()
        )
        target_url = (
            v.url().toString()
            if isinstance(v, QWebEngineView) and v.url().toString()
            else self.home_url
        )
        if self.split_view is None:
            self.split_pane = QFrame()
            pl = QVBoxLayout(self.split_pane)
            pl.setContentsMargins(0, 0, 0, 0)
            pl.setSpacing(0)
            bar = QWidget()
            bl = QHBoxLayout(bar)
            bl.setContentsMargins(8, 4, 8, 4)
            self.split_url_input = QLineEdit(target_url)
            self.split_url_input.setPlaceholderText("Split view URL...")
            self.split_url_input.returnPressed.connect(
                lambda: self.split_view.setUrl(
                    QUrl(
                        self.split_url_input.text().strip()
                        if "://" in self.split_url_input.text()
                        else "https://" + self.split_url_input.text().strip()
                    )
                )
            )
            btn_swap = QPushButton("Swap")
            btn_swap.clicked.connect(self.swap_split_panes)
            btn_close = QPushButton("Close Split")
            btn_close.clicked.connect(self._close_split_view)
            bl.addWidget(self.split_url_input, 1)
            bl.addWidget(btn_swap)
            bl.addWidget(btn_close)
            self.split_view = self._create_web_view()
            self.split_view.urlChanged.connect(
                lambda u: (
                    self.split_url_input.setText(u.toString())
                    if hasattr(self, "split_url_input")
                    else None
                )
            )
            pl.addWidget(bar)
            pl.addWidget(self.split_view, 1)
            self.content_splitter.addWidget(self.split_pane)
            self.content_splitter.setSizes([1, 1])
        self.split_view.setUrl(QUrl(target_url))
        if hasattr(self, "split_button"):
            self.split_button.setChecked(True)

    def swap_split_panes(self):
        cur = self.get_current_view()
        if not isinstance(cur, QWebEngineView) or not isinstance(
            self.split_view, QWebEngineView
        ):
            return
        u1, u2 = cur.url(), self.split_view.url()
        cur.setUrl(u2)
        self.split_view.setUrl(u1)

    def _close_split_view(self):
        if self.split_view is not None:
            try:
                self.split_view.stop()
                p = self.split_view.page()
                self.split_view.setPage(None)
                if p and not is_view_deleted(p):
                    p.deleteLater()
                self.split_view.deleteLater()
            except Exception:
                pass
            self.split_view = None
        if hasattr(self, "split_pane") and self.split_pane is not None:
            self.split_pane.setParent(None)
            self.split_pane.deleteLater()
            self.split_pane = None
        if hasattr(self, "split_button"):
            self.split_button.setChecked(False)

    def adjust_zoom(self, delta):
        v = self.get_current_view()
        if isinstance(v, QWebEngineView):
            v.setZoomFactor(max(0.25, min(3.0, round(v.zoomFactor() + delta, 2))))
            self._sync_zoom_badge()

    def reset_zoom(self):
        v = self.get_current_view()
        if isinstance(v, QWebEngineView):
            v.setZoomFactor(1.0)
            self._sync_zoom_badge()

    def _sync_zoom_badge(self):
        if not hasattr(self, "zoom_badge_btn"):
            return
        v = self.get_current_view()
        if isinstance(v, QWebEngineView):
            pct = int(round(v.zoomFactor() * 100))
            self.zoom_badge_btn.setText(f"{pct}%")
            self.zoom_badge_btn.setVisible(pct != 100)
        else:
            self.zoom_badge_btn.hide()

    def capture_page_screenshot(self):
        v = self.get_current_view()
        if not isinstance(v, QWebEngineView):
            return
        default_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.PicturesLocation
        ) or QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        fname = f"ecobrowser_{datetime.now():%Y%m%d_%H%M%S}.png"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Page Screenshot",
            os.path.join(default_dir, fname),
            "PNG Image (*.png)",
        )
        if path:
            v.grab().save(path, "PNG")
            QMessageBox.information(
                self, "Screenshot Saved", f"Saved screenshot to:\n{path}"
            )

    def _copy_clean_url_for_view(self, view):
        if isinstance(view, QWebEngineView):
            cleaned = strip_tracking_params(view.url().toString())
            QApplication.clipboard().setText(cleaned)

    def copy_clean_current_url(self):
        v = self.get_current_view()
        if isinstance(v, QWebEngineView):
            self._copy_clean_url_for_view(v)
            QMessageBox.information(
                self, "Clean URL Copied", "Copied URL with tracking parameters removed."
            )

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _handle_escape_key(self):
        if hasattr(self, "find_bar_widget") and self.find_bar_widget.isVisible():
            self.close_find_bar()
            return
        v = self.get_current_view()
        if v and self.reader_state.get(id(v), False):
            self._handle_escape_reader()
            return
        if self.isFullScreen():
            self.showNormal()

    def _session_file_path(self):
        return os.path.join(get_app_data_folder(), "session.json")

    def save_current_session(self):
        if self.private_mode:
            return
        urls = []
        for i in range(self.stack.count()):
            w = self.stack.widget(i)
            u = (
                w.url().toString()
                if isinstance(w, QWebEngineView)
                else getattr(w, "_hibernated_url", "")
            )
            if u and not u.startswith(("about:blank", "data:")):
                urls.append(u)
        _write_json(
            self._session_file_path(),
            {"urls": urls[:30], "active": max(0, self.tab_bar.currentIndex())},
            indent=2,
        )

    def restore_previous_session(self, silent=False):
        data = _read_json(self._session_file_path(), None)
        urls = [
            u
            for u in (data.get("urls", []) if isinstance(data, dict) else [])
            if isinstance(u, str) and u.strip()
        ]
        if not urls:
            if not silent:
                QMessageBox.information(
                    self, "Session Restore", "No previous browsing session found."
                )
            return False
        for u in urls:
            self.add_new_tab(u)
        act = int(data.get("active", 0)) if isinstance(data, dict) else 0
        if 0 <= act < self.tab_bar.count():
            self.tab_bar.setCurrentIndex(act)
        return True

    def closeEvent(self, event):
        self.save_current_session()
        self._close_split_view()
        if not self.private_mode and self.settings.get("clear_cache_on_exit", False):
            try:
                self.profile.clearHttpCache()
            except Exception:
                pass
        for i in range(self.stack.count()):
            w = self.stack.widget(i)
            if isinstance(w, QWebEngineView) and not is_view_deleted(w):
                try:
                    w.stop()
                    page = w.page()
                    w.setPage(None)
                    if page and not is_view_deleted(page):
                        page.deleteLater()
                    w.deleteLater()
                except Exception:
                    pass
        event.accept()


def get_app_data_folder():
    folder = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "EcoBrowser")
    os.makedirs(folder, exist_ok=True)
    return folder


PROXY_CREDENTIALS_STORAGE_KEY = "proxy_credentials_fernet"
PROXY_CREDENTIALS_LEGACY_STORAGE_KEY = "proxy_credentials_dpapi"


def _dpapi_crypt(data, protect):
    if sys.platform != "win32":
        raise RuntimeError("DPAPI decryption is only supported on Windows.")
    from ctypes import wintypes

    class DataBlob(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
        ]

    in_buf = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    in_blob = DataBlob(len(data), ctypes.cast(in_buf, ctypes.POINTER(ctypes.c_ubyte)))
    out_blob, desc = DataBlob(), wintypes.LPWSTR()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    fn = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    fn.restype = wintypes.BOOL
    args = (
        ctypes.byref(in_blob),
        "EcoBrowser proxy credentials" if protect else ctypes.byref(desc),
        None,
        None,
        None,
        0x1,
        ctypes.byref(out_blob),
    )
    try:
        if not fn(*args):
            raise ctypes.WinError(ctypes.get_last_error())
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        if out_blob.pbData:
            kernel32.LocalFree(ctypes.cast(out_blob.pbData, ctypes.c_void_p))
        if desc:
            kernel32.LocalFree(ctypes.cast(desc, ctypes.c_void_p))


def protect_proxy_credentials(username, password):
    if not username and not password:
        return None
    return fernet_encrypt(
        json.dumps({"username": username, "password": password}, ensure_ascii=False)
    )


def unprotect_proxy_credentials(protected_value):
    if not protected_value:
        raise ValueError("Saved proxy credentials are empty.")
    try:
        data = json.loads(fernet_decrypt(str(protected_value)))
        if isinstance(data, dict):
            return {
                "proxy_username": str(data.get("username", "")),
                "proxy_password": str(data.get("password", "")),
            }
        raise ValueError("Invalid proxy credential format.")
    except (ValueError, json.JSONDecodeError):
        raise
    except Exception:
        pass
    try:
        data = json.loads(
            _dpapi_crypt(
                base64.b64decode(protected_value, validate=True), protect=False
            ).decode("utf-8")
        )
        return {
            "proxy_username": str(data.get("username", "")),
            "proxy_password": str(data.get("password", "")),
        }
    except Exception as e:
        raise ValueError("Saved proxy credentials could not be decrypted.") from e


def prepare_settings_for_storage(settings):
    stored = dict(settings)
    user = str(stored.pop("proxy_username", "") or "")
    pw = str(stored.pop("proxy_password", "") or "")
    for k in (
        "proxy_credentials_error",
        PROXY_CREDENTIALS_STORAGE_KEY,
        PROXY_CREDENTIALS_LEGACY_STORAGE_KEY,
    ):
        stored.pop(k, None)
    if bool(user) != bool(pw):
        raise ValueError("Both a proxy username and password must be configured.")
    prot = protect_proxy_credentials(user, pw)
    if prot:
        stored[PROXY_CREDENTIALS_STORAGE_KEY] = prot
    return stored


def load_saved_settings():
    settings = dict(DEFAULT_SETTINGS)
    saved = _read_json(os.path.join(get_app_data_folder(), "settings.json"), None)
    if isinstance(saved, dict):
        prot = saved.pop(PROXY_CREDENTIALS_STORAGE_KEY, None)
        leg = saved.pop(PROXY_CREDENTIALS_LEGACY_STORAGE_KEY, None)
        settings.update(saved)
        for cand in (prot, leg):
            if cand:
                try:
                    settings.update(unprotect_proxy_credentials(cand))
                    break
                except Exception:
                    continue
        else:
            if prot or leg:
                settings.update(
                    {
                        "proxy_username": "",
                        "proxy_password": "",
                        "proxy_credentials_error": True,
                    }
                )
    return settings


def get_dns_server_template(settings):
    if not settings.get("dns_enabled", True):
        return None
    pk = settings.get("dns_provider", "cloudflare_family")
    tpl = (
        settings.get("custom_doh_url", "")
        if pk == "custom"
        else DNS_PROVIDERS.get(pk, DNS_PROVIDERS["cloudflare_family"])["url"]
    )
    if not is_valid_https_url(tpl):
        raise ValueError("The configured DNS-over-HTTPS URL must be a valid HTTPS URL.")
    return tpl


def _take_chromium_switch(arguments, switch_name):
    kept, values, i = [], [], 0
    while i < len(arguments):
        arg = arguments[i]
        if arg == switch_name:
            if i + 1 < len(arguments):
                values.append(arguments[i + 1])
                i += 2
            else:
                i += 1
        elif arg.startswith(f"{switch_name}="):
            values.append(arg.split("=", 1)[1])
            i += 1
        else:
            kept.append(arg)
            i += 1
    return kept, values


def _merge_switch_items(values):
    return list(dict.fromkeys(item for v in values for item in v.split(",") if item))


def configure_chromium_doh_flags(server_template):
    args = shlex.split(os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", ""))
    sv = {}
    for sw in (
        "--enable-features",
        "--disable-features",
        "--force-fieldtrials",
        "--force-fieldtrial-params",
    ):
        args, sv[sw] = _take_chromium_switch(args, sw)

    is_doh = lambda f: f.split("<", 1)[0].split(":", 1)[0].lower() in {
        "dnsoverhttps",
        "dns-over-https",
    }
    en = [f for f in _merge_switch_items(sv["--enable-features"]) if not is_doh(f)]
    dis = [f for f in _merge_switch_items(sv["--disable-features"]) if not is_doh(f)]
    trials, tv = [], [item for v in sv["--force-fieldtrials"] for item in v.split("/")]
    for i in range(0, len(tv) - 1, 2):
        if tv[i] != "DoHTrial":
            trials.extend(tv[i : i + 2])
    params = [
        item
        for v in sv["--force-fieldtrial-params"]
        for item in v.split(",")
        if item and not item.startswith("DoHTrial.Group1:")
    ]

    if server_template:
        en.append("DnsOverHttps<DoHTrial")
        trials.extend(["DoHTrial", "Group1"])
        params.append(
            f"DoHTrial.Group1:Fallback/false/Templates/{quote(server_template, safe='')}"
        )
    else:
        dis.append("DnsOverHttps")

    for sw, vals in (
        ("--enable-features", en),
        ("--disable-features", dis),
        ("--force-fieldtrials", trials),
        ("--force-fieldtrial-params", params),
    ):
        if vals:
            args.append(
                f"{sw}={(',' if 'features' in sw or 'params' in sw else '/').join(vals)}"
            )
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join(
        f'"{a}"' if " " in a and not a.startswith('"') else a for a in args
    )


def apply_webengine_network_settings(settings, doh_flags_preconfigured=False):
    tpl = get_dns_server_template(settings)
    setter = getattr(QWebEngineGlobalSettings, "setDnsMode", None)
    if callable(setter):
        dm = QWebEngineGlobalSettings.DnsMode()
        dm.secureMode = (
            QWebEngineGlobalSettings.SecureDnsMode.SecureOnly
            if tpl
            else QWebEngineGlobalSettings.SecureDnsMode.SystemOnly
        )
        dm.serverTemplates = [tpl] if tpl else []
        if not setter(dm):
            raise RuntimeError("Qt WebEngine rejected the DNS-over-HTTPS settings.")
    elif not doh_flags_preconfigured:
        configure_chromium_doh_flags(tpl)

    if not settings.get("proxy_enabled", False):
        QNetworkProxyFactory.setUseSystemConfiguration(True)
        return
    host, port = str(settings.get("proxy_host", "")).strip(), int(
        settings.get("proxy_port", DEFAULT_SETTINGS["proxy_port"])
    )
    if not host or not 1 <= port <= 65535:
        raise ValueError("The configured browser proxy host or port is invalid.")
    ptype = (
        QNetworkProxy.ProxyType.HttpProxy
        if settings.get("proxy_type", "SOCKS5") == "HTTP"
        else QNetworkProxy.ProxyType.Socks5Proxy
    )
    proxy = QNetworkProxy(ptype, host, port)
    user, pw = str(settings.get("proxy_username", "")), str(
        settings.get("proxy_password", "")
    )
    if bool(user) != bool(pw):
        raise ValueError("Both a proxy username and password must be configured.")
    if user and settings.get("proxy_type", "SOCKS5") != "HTTP":
        raise ValueError(
            "Chromium does not support username/password authentication for SOCKS5 proxies."
        )
    if user:
        proxy.setUser(user)
        proxy.setPassword(pw)
    QNetworkProxyFactory.setUseSystemConfiguration(False)
    QNetworkProxy.setApplicationProxy(proxy)


def get_initial_url_from_args(argv):
    return argv[1] if len(argv) > 1 and argv[1].startswith("http") else None


if __name__ == "__main__":
    register_as_browser()
    startup_settings = load_saved_settings()
    doh_pre = not callable(getattr(QWebEngineGlobalSettings, "setDnsMode", None))
    startup_net_err = None
    if doh_pre:
        try:
            configure_chromium_doh_flags(get_dns_server_template(startup_settings))
        except ValueError as e:
            startup_net_err = e

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    if startup_settings.get("proxy_credentials_error"):
        QMessageBox.warning(
            None,
            "Proxy credentials unavailable",
            "EcoBrowser could not decrypt saved proxy credentials.",
        )
    if startup_net_err:
        QMessageBox.critical(
            None,
            "Network settings error",
            f"EcoBrowser could not apply DNS settings:\n{startup_net_err}",
        )
        sys.exit(1)
    try:
        apply_webengine_network_settings(
            startup_settings, doh_flags_preconfigured=doh_pre
        )
    except (RuntimeError, ValueError) as e:
        QMessageBox.critical(
            None,
            "Network settings error",
            f"EcoBrowser could not apply DNS or proxy settings:\n{e}",
        )
        sys.exit(1)
    window = EcoBrowserWindow(get_initial_url_from_args(sys.argv))
    window.show()
    sys.exit(app.exec())
