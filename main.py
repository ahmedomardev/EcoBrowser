import os
import sys
import gc
import json
import subprocess
from datetime import datetime

# Windows registry for default browser registration (only on Windows)
if sys.platform == "win32":
    try:
        import winreg as reg
    except ImportError:
        reg = None
else:
    reg = None

from PyQt6.QtCore import QUrl, QTimer, Qt, QByteArray, QSize, QStandardPaths
from PyQt6.QtGui import QIcon, QPixmap, QPainter,QKeySequence, QShortcut, QColor
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineUrlRequestInterceptor,
    QWebEngineSettings,
    QWebEngineDownloadRequest,
    QWebEngineScript,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTabBar,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QDialog,
    QTextEdit,
    QMenu,
    QCheckBox,
    QMessageBox,
    QScrollArea,
    QProgressBar,
    QFrame,
    QGroupBox,
    QColorDialog,
    QGridLayout,
)

# =============================================================================
# App Metadata & Default Configuration
# =============================================================================

APP_NAME = "EcoBrowser"
APP_VERSION = "1.5"
HOME_URL = "https://www.google.com"

# Built-in Search Engines
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
DEFAULT_SEARCH_ENGINE = "Google"

# Color Customization Presets
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
DEFAULT_ACCENT_COLOR = "#58a6ff"

# Network Filter Lists
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
    "hentai",
    "nsfw",
    "erotic",
    "nudity",
    "nude",
    "sexvideo",
    "adult-zone",
    "camgirl",
    "onlyfans",
    "fetish",
]

# =============================================================================
# Modern Color Themes (Chrome 2026 Refresh + Arc-inspired)
# =============================================================================

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

# High-resolution, modern SVG Icons
SVG_ICONS = {
    "back": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.51-1.51L7.83 13H20v-2z"/></svg>',
    "forward": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 4l-1.51 1.51L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"/></svg>',
    "reload": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M17.65 6.35A7.958 7.958 0 0 0 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0 1 12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>',
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
    "check_circle": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.51-1.51L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>',
    "tab_close": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
    "globe": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>',
    "palette": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 3c-4.97 0-9 4.03-9 9 0 2.12.74 4.07 1.97 5.61L4.35 19.4c-.39.39-.39 1.02 0 1.51.39.39 1.02.39 1.51 0l1.9-1.9C9.23 19.59 10.57 20 12 20c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-5.5 9c-.83 0-1.5-.67-1.5-1.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12zm3-4C8.67 8 8 7.33 8 6.5S8.67 5 9.5 5s1.5.67 1.5 1.5S10.33 8 9.5 8zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 5 14.5 5s1.5.67 1.5 1.5S15.33 8 14.5 8zm3 4c-.83 0-1.5-.67-1.5-1.5S16.67 9 17.5 9s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/></svg>',
    "search": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>',
}


def render_svg_icon(svg_template, color, size=20):
    """Renders scalable vector icon directly to QIcon."""
    svg_content = svg_template.replace("{color}", color)
    renderer = QSvgRenderer(QByteArray(svg_content.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def format_file_size(size_bytes):
    if not size_bytes or size_bytes <= 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{int(size_bytes)} B"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


# =============================================================================
# Client-side Injected Script: NSFW Media Blurring & AI-Generated Media Watermarking
# =============================================================================

AI_SAFEGUARD_SCRIPT = r"""
(function() {
    if (window.__ecoBrowserGuardInitialized) return;
    window.__ecoBrowserGuardInitialized = true;

    // Configuration flags
    window.__ecoSettings = {
        blurNude: true,
        blurStrength: 32,
        markAiGenerated: true,
        detectAiSlop: true,
        blurAiSlop: true,
        autoMuteNsfwVideo: true
    };

    // Keyword heuristics for explicit / adult media attributes (NSFW) - Images & Videos
    const NSFW_PATTERNS = [
        /\b(nude|nudity|nsfw|naked|explicit|porn|porno|xxx|erotic|erotica|sex|sexual|boob|breast|butt|ass|genital|penis|vagina|uncensored|sensual|intimate|topless|tits|cleavage|stripper|fetish|camgirl|onlyfans|fansly|rule34|hentai|nsfw_sensitive|sexvideo|camshow|striptease|hardcore|softcore)\b/i,
        /pornhub|xvideos|xnxx|redtube|youporn|xhamster|stripchat|chaturbate|onlyfans|spankbang|eporner|brazzers|rule34|txxx|tnaflix|porntrex|cam4|livejasmin/i
    ];

    // Heuristics for AI Slop / Synthetic Spam / Hallucinations / Mutant Anatomy
    const AI_SLOP_PATTERNS = [
        /\b(slop|ai[-_]?slop|brainrot|ai[-_]?brainrot|content[-_]?farm|junk[-_]?ai|shrimp[-_]?jesus|vegetable[-_]?baby)\b/i,
        /\b(mutant[-_]?(fingers|hands|limbs)|extra[-_]?fingers|6[-_]?fingers|distorted[-_]?hands|polydactyly)\b/i,
        /\b(plastic[-_]?skin|waxy[-_]?face|airbrushed[-_]?skin|uncanny[-_]?valley|porcelain[-_]?doll[-_]?face)\b/i,
        /\b(melting[-_]?(architecture|hands|objects)|impossible[-_]?architecture|hallucinated[-_]?geometry)\b/i,
        /\b(prompt[-_]?spam|masterpiece,?\s*best quality|trending on artstation|hyperrealistic\s*8k)\b/i,
        /\b(chatgpt[-_]?slop|copilot[-_]?slop|bing[-_]?slop|synthetic[-_]?slop)\b/i
    ];

    // Heuristics for AI-Generated / Synthetic Media signatures - Images & Videos
    const AI_GENERATED_PATTERNS = [
        /\b(sora|runwayml|runway|gen[-_]?[23]|kling|luma|dream[-_]?machine|pika|pikalabs|hailuo|minimax|animatediff|svd|stable[-_]?video|deforum|text[-_]?to[-_]?video|image[-_]?to[-_]?video|t2v|i2v)\b/i,
        /\b(midjourney|dall[-_]?e|dalle|stable[-_]?diffusion|sdxl|sd1\.5|flux|flux[-_]?(1|schnell|dev)|comfyui|civitai|genai|ai[-_]?generated|synthid|tensorart|novelai|leonardo[-_]?ai|ideogram|wuerstchen|deepfake|synthetic[-_]?media)\b/i,
        /\b(prompt|negative[-_]?prompt|seed|cfg[-_]?scale|steps|sampler|euler|dpm\+\+|checkpoint|lora|denoising)[:=]/i,
        /v[1-6]_[0-9a-f]{8}/i, // Common Midjourney hash pattern
        /_(grid_\d|upscaled?|mj_\w+)/i, // Midjourney grid/upscale naming convention
        /(oaidalleapiprodscus|images\.midjourney\.com|civitai\.com)/i
    ];

    // Style injection for blur overlays, controls and AI Watermarks
    const style = document.createElement('style');
    style.id = '__ecobrowser_guard_styles';
    style.textContent = `
        .eco-nsfw-blurred, .eco-slop-blurred {
            filter: blur(var(--eco-blur, 32px)) !important;
            transition: filter 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
            pointer-events: auto !important;
            user-select: none !important;
        }
        .eco-nsfw-unblurred, .eco-slop-unblurred {
            filter: none !important;
            transition: filter 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        .eco-media-wrapper {
            position: relative !important;
            display: inline-block !important;
            overflow: hidden !important;
        }
        .eco-nsfw-badge {
            position: absolute !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            background: rgba(18, 20, 24, 0.92) !important;
            backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(245, 158, 11, 0.4) !important;
            color: #ffffff !important;
            padding: 8px 16px !important;
            border-radius: 9999px !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            font-size: 11.5px !important;
            font-weight: 600 !important;
            letter-spacing: 0.3px !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6) !important;
            cursor: pointer !important;
            z-index: 99999 !important;
            display: flex !important;
            align-items: center !important;
            gap: 6px !important;
            pointer-events: auto !important;
        }
        .eco-nsfw-badge:hover {
            background: rgba(217, 119, 6, 0.95) !important;
            transform: translate(-50%, -50%) scale(1.04) !important;
        }
        .eco-slop-badge {
            position: absolute !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            background: rgba(26, 16, 8, 0.94) !important;
            backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(249, 115, 22, 0.7) !important;
            color: #ffffff !important;
            padding: 8px 16px !important;
            border-radius: 9999px !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            font-size: 11.5px !important;
            font-weight: 600 !important;
            letter-spacing: 0.3px !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7) !important;
            cursor: pointer !important;
            z-index: 99999 !important;
            display: flex !important;
            align-items: center !important;
            gap: 6px !important;
            pointer-events: auto !important;
        }
        .eco-slop-badge:hover {
            background: rgba(234, 88, 12, 0.95) !important;
            transform: translate(-50%, -50%) scale(1.04) !important;
        }
        .eco-slop-watermark {
            position: absolute !important;
            top: 10px !important;
            right: 10px !important;
            background: rgba(26, 16, 8, 0.90) !important;
            backdrop-filter: blur(8px) !important;
            border: 1px solid rgba(249, 115, 22, 0.8) !important;
            color: #fb923c !important;
            padding: 4px 10px !important;
            border-radius: 6px !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            font-size: 10px !important;
            font-weight: 700 !important;
            letter-spacing: 0.6px !important;
            text-transform: uppercase !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
            z-index: 99992 !important;
            pointer-events: none !important;
            display: flex !important;
            align-items: center !important;
            gap: 4px !important;
        }
        .eco-ai-watermark {
            position: absolute !important;
            top: 10px !important;
            right: 10px !important;
            background: rgba(13, 17, 23, 0.85) !important;
            backdrop-filter: blur(8px) !important;
            border: 1px solid rgba(56, 189, 248, 0.5) !important;
            color: #38bdf8 !important;
            padding: 4px 10px !important;
            border-radius: 6px !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            font-size: 10px !important;
            font-weight: 700 !important;
            letter-spacing: 0.6px !important;
            text-transform: uppercase !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
            z-index: 99990 !important;
            pointer-events: none !important;
            display: flex !important;
            align-items: center !important;
            gap: 4px !important;
        }
    `;
    (document.head || document.documentElement).appendChild(style);

    function evaluateTextHeuristics(str) {
        if (!str || typeof str !== 'string') return { isNsfw: false, isAi: false, isSlop: false };
        const isNsfw = NSFW_PATTERNS.some(p => p.test(str));
        const isSlop = AI_SLOP_PATTERNS.some(p => p.test(str));
        const isAi = isSlop || AI_GENERATED_PATTERNS.some(p => p.test(str));
        return { isNsfw, isAi, isSlop };
    }

    // Inspect image / video elements with clean separation between NSFW, AI-Generated, and AI Slop
    function inspectMediaElement(elem) {
        if (elem.__ecoProcessed) return;
        elem.__ecoProcessed = true;

        let src = elem.currentSrc || elem.src || elem.getAttribute('src') || '';
        const alt = elem.getAttribute('alt') || '';
        const title = elem.getAttribute('title') || '';
        const ariaLabel = elem.getAttribute('aria-label') || '';
        const className = elem.className || '';
        let extraInfo = '';

        if (elem.tagName === 'VIDEO') {
            const poster = elem.getAttribute('poster') || '';
            const sources = Array.from(elem.querySelectorAll('source')).map(s => s.src || s.getAttribute('src') || '').join(' ');
            extraInfo = ` ${poster} ${sources} video footage stream clip`;
        }

        const combined = `${src} ${alt} ${title} ${ariaLabel} ${className} ${extraInfo}`;
        const { isNsfw: textNsfw, isAi: textAi, isSlop: textSlop } = evaluateTextHeuristics(combined);

        // Filter 1: AI Slop & Brainrot Detection & Watermarking/Blur
        if (window.__ecoSettings.detectAiSlop && textSlop && !elem.__ecoAiSlopHandled) {
            elem.__ecoAiSlopHandled = true;
            attachAiSlopWatermark(elem, 'AI Slop Detected');
            if (window.__ecoSettings.blurAiSlop && !elem.__ecoNsfwHandled) {
                applySlopBlur(elem);
            }
        }

        // Filter 2: AI-Generated Media Watermark (Standard AI, if not already handled as slop)
        if (window.__ecoSettings.markAiGenerated && textAi && !textSlop && !elem.__ecoAiWatermarked) {
            elem.__ecoAiWatermarked = true;
            const label = elem.tagName === 'VIDEO' ? 'AI Generated Video' : 'AI Generated';
            attachAiWatermark(elem, label);
        }

        // Filter 3: NSFW Adult Content Blurring (Images & Videos)
        if (window.__ecoSettings.blurNude && textNsfw && !elem.__ecoNsfwHandled) {
            elem.__ecoNsfwHandled = true;
            applyNsfwBlur(elem);
        }
    }

    function applySlopBlur(elem) {
        elem.classList.add('eco-slop-blurred');

        const parent = elem.parentElement;
        if (!parent) return;

        const computedPos = window.getComputedStyle(parent).position;
        if (computedPos === 'static') {
            parent.style.position = 'relative';
        }

        // Add interactive unlock badge for AI Slop
        const badge = document.createElement('div');
        badge.className = 'eco-slop-badge';
        badge.innerHTML = '<span>⚠️</span><span>AI Slop Filtered • Click to View</span>';
        
        let isBlurred = true;
        badge.onclick = (e) => {
            e.stopPropagation();
            e.preventDefault();
            isBlurred = !isBlurred;
            if (isBlurred) {
                elem.classList.remove('eco-slop-unblurred');
                elem.classList.add('eco-slop-blurred');
                badge.innerHTML = '<span>⚠️</span><span>AI Slop Filtered • Click to View</span>';
            } else {
                elem.classList.remove('eco-slop-blurred');
                elem.classList.add('eco-slop-unblurred');
                badge.innerHTML = '<span>🔒</span><span>Re-blur AI Slop</span>';
            }
        };

        if (parent.insertBefore && parent.contains(elem)) {
            parent.insertBefore(badge, elem.nextSibling);
        }
    }

    function applyNsfwBlur(elem) {
        elem.classList.add('eco-nsfw-blurred');

        // Mute video if explicit
        if (elem.tagName === 'VIDEO' && window.__ecoSettings.autoMuteNsfwVideo) {
            try { elem.muted = true; elem.pause(); } catch(e) {}
        }

        const parent = elem.parentElement;
        if (!parent) return;

        // Ensure parent has position relative
        const computedPos = window.getComputedStyle(parent).position;
        if (computedPos === 'static') {
            parent.style.position = 'relative';
        }

        // Add interactive unlock badge
        const badge = document.createElement('div');
        badge.className = 'eco-nsfw-badge';
        badge.innerHTML = '<span>👁️</span><span>NSFW Filtered • Click to View</span>';
        
        let isBlurred = true;
        badge.onclick = (e) => {
            e.stopPropagation();
            e.preventDefault();
            isBlurred = !isBlurred;
            if (isBlurred) {
                elem.classList.remove('eco-nsfw-unblurred');
                elem.classList.add('eco-nsfw-blurred');
                badge.innerHTML = '<span>👁️</span><span>NSFW Filtered • Click to View</span>';
            } else {
                elem.classList.remove('eco-nsfw-blurred');
                elem.classList.add('eco-nsfw-unblurred');
                badge.innerHTML = '<span>🔒</span><span>Hide Sensitive Content</span>';
                if (elem.tagName === 'VIDEO') elem.play();
            }
        };

        // Insert badge next to media
        if (parent.insertBefore && parent.contains(elem)) {
            parent.insertBefore(badge, elem.nextSibling);
        }
    }

    function attachAiSlopWatermark(elem, label) {
        const parent = elem.parentElement;
        if (!parent) return;

        const computedPos = window.getComputedStyle(parent).position;
        if (computedPos === 'static') {
            parent.style.position = 'relative';
        }

        const watermark = document.createElement('div');
        watermark.className = 'eco-slop-watermark';
        watermark.innerHTML = `<span>⚠️</span><span>${label || 'AI Slop Detected'}</span>`;
        if (parent.insertBefore && parent.contains(elem)) {
            parent.insertBefore(watermark, elem.nextSibling);
        }
    }

    function attachAiWatermark(elem, label) {
        const parent = elem.parentElement;
        if (!parent) return;

        const computedPos = window.getComputedStyle(parent).position;
        if (computedPos === 'static') {
            parent.style.position = 'relative';
        }

        const watermark = document.createElement('div');
        watermark.className = 'eco-ai-watermark';
        watermark.innerHTML = `<span>✦</span><span>${label || 'AI Generated'}</span>`;
        if (parent.insertBefore && parent.contains(elem)) {
            parent.insertBefore(watermark, elem.nextSibling);
        }
    }

    // Scan initial DOM elements
    function scanAll() {
        const images = document.querySelectorAll('img, video, canvas');
        images.forEach(inspectMediaElement);
    }

    // Dynamic Mutation Observer for lazy-loaded media
    const observer = new MutationObserver((mutations) => {
        for (const m of mutations) {
            for (const node of m.addedNodes) {
                if (node.nodeType === 1) {
                    if (node.matches && node.matches('img, video, canvas')) {
                        inspectMediaElement(node);
                    } else if (node.querySelectorAll) {
                        node.querySelectorAll('img, video, canvas').forEach(inspectMediaElement);
                    }
                }
            }
        }
    });

    scanAll();
    observer.observe(document.body || document.documentElement, {
        childList: true,
        subtree: true
    });
})();
"""

# =============================================================================
# Windows Default Browser Registration Helper
# =============================================================================


def is_browser_registered():
    """Checks if EcoBrowser has already saved its registry registration flag to avoid duplicate writes."""
    settings_file = os.path.join(get_app_data_folder(), "settings.json")
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return bool(data.get("registry_registered", False))
        except Exception:
            pass
    return False


def set_browser_registered_flag(registered: bool):
    """Persists whether EcoBrowser has been registered in the Windows registry."""
    settings_file = os.path.join(get_app_data_folder(), "settings.json")
    data = {}
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data["registry_registered"] = registered
    try:
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass


def register_as_browser(force: bool = False):
    """Registers EcoBrowser with the Windows Registry as a web browser.

    Prevents adding duplicate records to the Windows registry by checking if
    already registered (both in local settings and existing registry keys)
    before performing any write operations.
    """
    if sys.platform != "win32" or reg is None:
        return False

    # Check 1: Did we already record that we registered?
    if not force and is_browser_registered():
        return True

    capabilities_path = r"Software\EcoBrowser\Capabilities"

    # Check 2: Does the registry key already exist in Windows registry?
    if not force:
        try:
            with reg.OpenKey(reg.HKEY_CURRENT_USER, capabilities_path) as existing_key:
                # Key already exists, do not add more records! Save flag and return.
                set_browser_registered_flag(True)
                return True
        except FileNotFoundError:
            pass
        except Exception:
            pass

    if getattr(sys, "frozen", False):
        app_path = f'"{sys.executable}"'
    else:
        app_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'

    app_name = "EcoBrowser"

    try:
        with reg.CreateKey(reg.HKEY_CURRENT_USER, capabilities_path) as key:
            reg.SetValueEx(key, "ApplicationName", 0, reg.REG_SZ, app_name)
            reg.SetValueEx(
                key,
                "ApplicationDescription",
                0,
                reg.REG_SZ,
                "High-performance browser with NSFW Blurring & AI-Generated Media Watermarking.",
            )

        with reg.CreateKey(
            reg.HKEY_CURRENT_USER, f"{capabilities_path}\\URLAssociations"
        ) as key:
            reg.SetValueEx(key, "http", 0, reg.REG_SZ, "EcoBrowserURL")
            reg.SetValueEx(key, "https", 0, reg.REG_SZ, "EcoBrowserURL")

        with reg.CreateKey(
            reg.HKEY_CURRENT_USER, f"{capabilities_path}\\FileAssociations"
        ) as key:
            reg.SetValueEx(key, ".html", 0, reg.REG_SZ, "EcoBrowserHTML")
            reg.SetValueEx(key, ".htm", 0, reg.REG_SZ, "EcoBrowserHTML")

        with reg.CreateKey(
            reg.HKEY_CURRENT_USER, r"Software\Classes\EcoBrowserURL\shell\open\command"
        ) as key:
            reg.SetValueEx(key, "", 0, reg.REG_SZ, f'{app_path} "%1"')

        with reg.CreateKey(
            reg.HKEY_CURRENT_USER, r"Software\Classes\EcoBrowserHTML\shell\open\command"
        ) as key:
            reg.SetValueEx(key, "", 0, reg.REG_SZ, f'{app_path} "%1"')

        with reg.CreateKey(
            reg.HKEY_CURRENT_USER, r"Software\RegisteredApplications"
        ) as key:
            reg.SetValueEx(key, app_name, 0, reg.REG_SZ, capabilities_path)

        # Successfully registered, record in settings so subsequent runs NEVER re-write duplicate records
        set_browser_registered_flag(True)
        return True

    except Exception:
        return False


def build_blocked_page_html(blocked_domain, reason="Security & Privacy Policy"):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    body {{ background: #121418; color: #f0f6fc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }} 
    .warning-card {{ background: #1e2229; padding: 36px 44px; border-radius: 16px; border: 1px solid #30363d; text-align: center; max-width: 440px; box-shadow: 0 16px 36px rgba(0,0,0,0.6); }} 
    .block-icon {{ font-size: 40px; margin-bottom: 12px; }}
    .warning-title {{ color: #f85149; font-size: 22px; margin: 0 0 12px 0; font-weight: 600; }} 
    .warning-text {{ color: #8b949e; font-size: 14px; margin-bottom: 24px; line-height: 1.6; }} 
    .warning-btn {{ background: #238636; color: #ffffff; text-decoration: none; padding: 10px 24px; border-radius: 24px; font-size: 13.5px; font-weight: 600; display: inline-block; transition: background 0.2s ease; }} 
    .warning-btn:hover {{ background: #2ea043; }}
    </style></head><body><div class='warning-card'>
    <div class='block-icon'>🔒</div>
    <h1 class='warning-title'>Access Intercepted</h1>
    <p class='warning-text'>Navigation to <b>{blocked_domain}</b> was intercepted by EcoBrowser Content Filter ({reason}).</p>
    <a class='warning-btn' href='https://www.google.com'>Return to Safe Browsing</a>
    </div></body></html>"""


# =============================================================================
# Network Interceptor with Ad & Explicit Content Filtering
# =============================================================================


class ContentBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        self.ad_block_enabled = True
        self.nude_block_enabled = True
        self.blocked_ad_count = 0
        self.blocked_nude_count = 0

    def interceptRequest(self, info):
        url = info.requestUrl()
        url_string = url.toString()

        if not (url_string.startswith("http://") or url_string.startswith("https://")):
            return

        host = url.host().lower()
        full_url = url_string.lower()

        # Check Ad network
        if self.ad_block_enabled and any(ad in host for ad in AD_DOMAINS):
            info.block(True)
            self.blocked_ad_count += 1
            return

        # Check Explicit domains or keywords
        if self.nude_block_enabled:
            is_adult_host = any(domain in host for domain in ADULT_DOMAINS)
            is_adult_path = any(kw in full_url for kw in ADULT_KEYWORDS)
            if is_adult_host or is_adult_path:
                info.block(True)
                self.blocked_nude_count += 1
                return


class EcoWebEnginePage(QWebEnginePage):
    """Handles window.open, target='_blank', and file downloads."""

    def __init__(self, profile, browser_window, parent=None):
        super().__init__(profile, parent)
        self.browser_window = browser_window

    def createWindow(self, _window_type):
        new_view = self.browser_window.add_new_tab("about:blank")
        return new_view.page()


# =============================================================================
# Custom UI Controls: Bookmarks, Downloads & Dialogs
# =============================================================================


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
        action = menu.exec(self.mapToGlobal(pos))
        if action == delete_action:
            self.browser_window.delete_bookmark_by_url(self.bookmark_url)


class BlockManagerDialog(QDialog):
    """Blockers and filters: NSFW Blurring & AI-Generated Media Watermarking Configuration."""

    def __init__(self, interceptor, browser_window, parent=None):
        super().__init__(parent or browser_window)
        self.setWindowTitle("Blockers and filters")
        self.resize(480, 420)
        self.interceptor = interceptor
        self.browser_window = browser_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_label = QLabel("Blockers and filters")
        header_font = header_label.font()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        # Content filtering group: Privacy
        group_privacy = QGroupBox("Privacy & Ad Blocking")
        v_priv = QVBoxLayout(group_privacy)
        self.ad_block_cb = QCheckBox("Block intrusive ads & trackers")
        self.ad_block_cb.setChecked(self.interceptor.ad_block_enabled)
        self.ad_block_cb.toggled.connect(self._on_ad_block_toggled)
        v_priv.addWidget(self.ad_block_cb)
        layout.addWidget(group_privacy)

        # Filter 1: NSFW Media Blurring
        group_nsfw = QGroupBox("NSFW & Adult Media Filter")
        v_nsfw = QVBoxLayout(group_nsfw)
        self.nude_blur_cb = QCheckBox("Blur Adult & Explicit Content (32px)")
        self.nude_blur_cb.setToolTip(
            "Automatically blurs adult/nude imagery and explicit video frames with click-to-reveal badge"
        )
        self.nude_blur_cb.setChecked(self.interceptor.nude_block_enabled)
        self.nude_blur_cb.toggled.connect(self._on_nude_blur_toggled)
        v_nsfw.addWidget(self.nude_blur_cb)

        self.auto_mute_video_cb = QCheckBox("Auto-mute audio on explicit video frames")
        self.auto_mute_video_cb.setChecked(True)
        v_nsfw.addWidget(self.auto_mute_video_cb)
        layout.addWidget(group_nsfw)

        # Filter 2: AI Generated Media Watermarking
        group_ai = QGroupBox("AI-Generated Media Detector")
        v_ai = QVBoxLayout(group_ai)
        self.ai_gen_cb = QCheckBox("Stamp [✦ AI GENERATED] Watermark")
        self.ai_gen_cb.setToolTip(
            "Detects AI-generated images/videos (Midjourney, DALL-E, Flux, Sora) and overlays a high-contrast attribution watermark"
        )
        self.ai_gen_cb.setChecked(True)
        v_ai.addWidget(self.ai_gen_cb)
        layout.addWidget(group_ai)

        # Filter 3: AI Slop & Brainrot Blocker
        group_slop = QGroupBox("AI Slop & Brainrot Blocker")
        v_slop = QVBoxLayout(group_slop)
        self.ai_slop_cb = QCheckBox("Detect AI Slop, Brainrot & Mutant Anatomy")
        self.ai_slop_cb.setToolTip(
            "Detects mutant fingers, plastic faces, melting architecture, and repetitive generative spam"
        )
        self.ai_slop_cb.setChecked(True)
        v_slop.addWidget(self.ai_slop_cb)

        self.blur_slop_cb = QCheckBox("Auto-blur AI Slop content (Click-to-reveal)")
        self.blur_slop_cb.setChecked(True)
        v_slop.addWidget(self.blur_slop_cb)
        layout.addWidget(group_slop)

        # Stats summary
        stats_lbl = QLabel(
            f"Active Stats: {self.interceptor.blocked_ad_count} Ads Blocked • "
            f"{self.interceptor.blocked_nude_count} Explicit Items Filtered • "
            "AI Slop Shield Active"
        )
        stats_lbl.setStyleSheet("color: #8b949e; font-size: 9pt;")
        layout.addWidget(stats_lbl)

        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        close_btn = QPushButton("Save & Close")
        close_btn.clicked.connect(self.accept)
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)

    def _on_ad_block_toggled(self, is_checked):
        self.interceptor.ad_block_enabled = is_checked

    def _on_nude_blur_toggled(self, is_checked):
        self.interceptor.nude_block_enabled = is_checked


class ColorCustomizerDialog(QDialog):
    """Custom color and theme styling dialog for EcoBrowser."""

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

        header = QLabel("Color & Accent Customization")
        h_font = header.font()
        h_font.setPointSize(12)
        h_font.setBold(True)
        header.setFont(h_font)
        layout.addWidget(header)

        desc = QLabel(
            "Personalize EcoBrowser with custom accents for active tabs, omnibox highlights, "
            "and download progress bars."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #8b949e; font-size: 9.5pt;")
        layout.addWidget(desc)

        # Presets Group
        group_presets = QGroupBox("Preset Accent Themes")
        presets_layout = QVBoxLayout(group_presets)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(8)

        self.preset_buttons = []
        for idx, p in enumerate(COLOR_PRESETS):
            accent_hex = p["dark_color"] if browser_window.is_dark_mode else p["color"]
            btn = QPushButton(f"●  {p['name']}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(255, 255, 255, 0.05);
                    color: {accent_hex};
                    font-weight: 600;
                    font-size: 9pt;
                    padding: 8px 12px;
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 8px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.12);
                    border-color: {accent_hex};
                }}
            """)
            btn.clicked.connect(lambda _, col=accent_hex: self._select_color(col))
            grid.addWidget(btn, idx // 2, idx % 2)
            self.preset_buttons.append(btn)

        presets_layout.addWidget(grid_widget)
        layout.addWidget(group_presets)

        # Custom Color Picker Group
        group_custom = QGroupBox("Custom Color (Hex / RGB)")
        custom_layout = QHBoxLayout(group_custom)
        custom_layout.setContentsMargins(14, 14, 14, 14)
        custom_layout.setSpacing(12)

        self.preview_pill = QLabel()
        self.preview_pill.setFixedSize(36, 36)
        self._update_preview_pill()
        custom_layout.addWidget(self.preview_pill)

        self.color_hex_label = QLabel(self.selected_color.upper())
        self.color_hex_label.setStyleSheet(
            "font-family: monospace; font-size: 11pt; font-weight: bold;"
        )
        custom_layout.addWidget(self.color_hex_label)
        custom_layout.addStretch()

        btn_pick = QPushButton("Pick Custom Color...")
        btn_pick.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_pick.clicked.connect(self._open_color_picker)
        custom_layout.addWidget(btn_pick)

        layout.addWidget(group_custom)
        layout.addStretch()

        # Bottom buttons
        btn_box = QHBoxLayout()
        btn_reset = QPushButton("Reset Default")
        btn_reset.clicked.connect(self._reset_default)
        btn_box.addWidget(btn_reset)
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_apply = QPushButton("Apply Color")
        btn_apply.setStyleSheet(
            "background-color: #0969da; color: white; font-weight: bold;"
        )
        btn_apply.clicked.connect(self._apply_and_close)
        btn_box.addWidget(btn_apply)
        layout.addLayout(btn_box)

    def _select_color(self, hex_color):
        self.selected_color = hex_color
        self._update_preview_pill()

    def _open_color_picker(self):
        initial = QColor(self.selected_color)
        chosen = QColorDialog.getColor(initial, self, "Choose Accent Color")
        if chosen.isValid():
            self.selected_color = chosen.name()
            self._update_preview_pill()

    def _update_preview_pill(self):
        self.preview_pill.setStyleSheet(f"""
            background-color: {self.selected_color};
            border-radius: 18px;
            border: 2px solid rgba(255, 255, 255, 0.3);
        """)
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
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_icon(theme)
        layout.addWidget(self.icon_label)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(3)

        self.name_label = QLabel(entry.get("fileName", "Unknown"))
        self.name_label.setStyleSheet(
            f"font-weight: 600; font-size: 9pt; color: {theme['text_primary']};"
        )
        content_layout.addWidget(self.name_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("downloadProgressBar")
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        content_layout.addWidget(self.progress_bar)

        self.status_label = QLabel()
        self.status_label.setStyleSheet(
            f"font-size: 8pt; color: {theme['text_secondary']};"
        )
        content_layout.addWidget(self.status_label)

        self.action_layout = QHBoxLayout()
        self.action_layout.setContentsMargins(0, 2, 0, 0)
        self.action_layout.setSpacing(6)

        self.btn_open = QPushButton("Open")
        self.btn_open.setProperty("class", "downloadActionBtn")
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open.clicked.connect(self._open_file)

        self.btn_folder = QPushButton("Show in folder")
        self.btn_folder.setProperty("class", "downloadActionBtn")
        self.btn_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_folder.clicked.connect(self._show_in_folder)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setProperty("class", "downloadActionBtn")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self._cancel_download)

        self.action_layout.addWidget(self.btn_open)
        self.action_layout.addWidget(self.btn_folder)
        self.action_layout.addWidget(self.btn_cancel)
        self.action_layout.addStretch()

        content_layout.addLayout(self.action_layout)
        layout.addLayout(content_layout, 1)

        self.update_state()

    def _update_icon(self, theme):
        state = self.entry.get("state", "completed")
        if state == "completed":
            icon = render_svg_icon(SVG_ICONS["check_circle"], "#34a853", 24)
        elif state == "in_progress":
            icon = render_svg_icon(SVG_ICONS["download"], theme["accent_blue"], 24)
        else:
            icon = render_svg_icon(SVG_ICONS["file"], theme["icon_color"], 24)
        self.icon_label.setPixmap(icon.pixmap(24, 24))

    def update_state(self):
        theme = DARK_THEME if self.browser_window.is_dark_mode else LIGHT_THEME
        state = self.entry.get("state", "completed")
        file_path = self.entry.get("filePath", "")
        self._update_icon(theme)

        if state == "in_progress":
            self.progress_bar.show()
            rec = self.entry.get("receivedBytes", 0)
            tot = self.entry.get("totalBytes", 0)
            if tot > 0:
                percent = int((rec / tot) * 100)
                self.progress_bar.setValue(percent)
                self.status_label.setText(
                    f"{format_file_size(rec)} / {format_file_size(tot)} ({percent}%)"
                )
            else:
                self.progress_bar.setValue(0)
                self.status_label.setText(f"{format_file_size(rec)} downloaded")

            self.btn_open.hide()
            self.btn_folder.hide()
            self.btn_cancel.show()
        elif state == "completed":
            self.progress_bar.hide()
            size_str = format_file_size(self.entry.get("totalBytes", 0))
            if os.path.exists(file_path):
                self.status_label.setText(f"{size_str} • Completed")
                self.btn_open.show()
                self.btn_folder.show()
            else:
                self.status_label.setText(f"{size_str} • File removed")
                self.btn_open.hide()
                self.btn_folder.hide()
            self.btn_cancel.hide()
        elif state == "cancelled":
            self.progress_bar.hide()
            self.status_label.setText("Cancelled")
            self.btn_open.hide()
            self.btn_folder.hide()
            self.btn_cancel.hide()
        else:
            self.progress_bar.hide()
            self.status_label.setText("Interrupted")
            self.btn_open.hide()
            self.btn_folder.hide()
            self.btn_cancel.hide()

    def update_progress(self, received, total):
        self.entry["receivedBytes"] = received
        self.entry["totalBytes"] = total
        self.update_state()

    def _open_file(self):
        file_path = self.entry.get("filePath", "")
        if os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception:
                pass

    def _show_in_folder(self):
        file_path = self.entry.get("filePath", "")
        if os.path.exists(file_path):
            try:
                subprocess.Popen(f'explorer /select,"{os.path.normpath(file_path)}"')
            except Exception:
                pass

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
        self.setFixedWidth(380)
        self.card_widgets = {}
        self._setup_ui()

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)

        self.card = QFrame()
        self.card.setObjectName("downloadsBubbleCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 4, 4)

        title = QLabel("Downloads")
        title_font = title.font()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_all = QPushButton("Show all")
        btn_all.setProperty("class", "downloadActionBtn")
        btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_all.clicked.connect(self._open_all_downloads)
        header_layout.addWidget(btn_all)

        btn_close = QPushButton()
        btn_close.setFixedSize(20, 20)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        theme = DARK_THEME if self.browser_window.is_dark_mode else LIGHT_THEME
        btn_close.setIcon(
            render_svg_icon(SVG_ICONS["tab_close"], theme["close_icon_color"], 10)
        )
        btn_close.setIconSize(QSize(10, 10))
        btn_close.clicked.connect(self.hide)
        header_layout.addWidget(btn_close)

        card_layout.addLayout(header_layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setMaximumHeight(320)

        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(6)
        self.items_layout.addStretch()

        self.scroll.setWidget(self.items_container)
        card_layout.addWidget(self.scroll)
        root_layout.addWidget(self.card)

    def refresh(self):
        self.card_widgets.clear()
        while self.items_layout.count() > 1:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        active_entries = [
            (d, entry) for d, entry in self.browser_window.active_downloads.items()
        ]
        history_entries = self.browser_window.load_downloads()
        active_paths = {entry["filePath"] for _, entry in active_entries}
        filtered_history = [
            (None, h) for h in history_entries if h.get("filePath") not in active_paths
        ]

        all_items = (active_entries + filtered_history)[:12]

        if not all_items:
            empty_label = QLabel("No recent downloads")
            theme = DARK_THEME if self.browser_window.is_dark_mode else LIGHT_THEME
            empty_label.setStyleSheet(
                f"color: {theme['text_secondary']}; padding: 24px 0px; font-size: 9.5pt;"
            )
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.items_layout.insertWidget(0, empty_label)
            return

        for d_obj, entry in all_items:
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
        self.setWindowTitle("Downloads — EcoBrowser")
        self.resize(650, 480)
        self.browser_window = browser_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search downloads...")
        self.search_input.setFixedHeight(32)
        self.search_input.textChanged.connect(self.load_all_downloads)
        header_layout.addWidget(self.search_input, 1)

        self.btn_clear_all = QPushButton("Clear all")
        self.btn_clear_all.clicked.connect(self.clear_all_downloads)
        header_layout.addWidget(self.btn_clear_all)
        layout.addLayout(header_layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(6)
        self.items_layout.addStretch()

        self.scroll.setWidget(self.items_container)
        layout.addWidget(self.scroll, 1)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("Done")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

        self.load_all_downloads()

    def load_all_downloads(self):
        while self.items_layout.count() > 1:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        all_downloads = self.browser_window.load_downloads()
        query = self.search_input.text().strip().lower()

        count = 0
        for entry in all_downloads:
            file_name = entry.get("fileName", "")
            if query and query not in file_name.lower():
                continue
            card = DownloadCardWidget(entry, None, self.browser_window)
            self.items_layout.insertWidget(self.items_layout.count() - 1, card)
            count += 1

        if count == 0:
            theme = DARK_THEME if self.browser_window.is_dark_mode else LIGHT_THEME
            lbl = QLabel(
                "No matching downloads found" if query else "No downloads found"
            )
            lbl.setStyleSheet(
                f"color: {theme['text_secondary']}; padding: 30px; font-size: 10pt;"
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.items_layout.insertWidget(0, lbl)

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
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        if os.path.exists(history_file_path):
            with open(history_file_path, "r", encoding="utf-8") as f:
                self.text_view.setText(f.read())
        else:
            self.text_view.setText("No browsing history found.")
        layout.addWidget(self.text_view)

        btn_layout = QHBoxLayout()
        self.btn_clear = QPushButton("Clear History")
        self.btn_close = QPushButton("Close")

        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.btn_clear.clicked.connect(self.clear_history)
        self.btn_close.clicked.connect(self.accept)

    def clear_history(self):
        if os.path.exists(self.history_file_path):
            os.remove(self.history_file_path)
        self.text_view.setText("No browsing history found.")


# =============================================================================
# Main Window: Modern EcoBrowser
# =============================================================================


class EcoBrowserWindow(QMainWindow):
    def __init__(self, initial_url=None):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1180, 780)
        self.initial_url = initial_url
        self.is_loading = False

        self.active_downloads = {}
        self.downloads_bubble = None

        self.settings = self.load_all_settings()
        self.is_dark_mode = self.settings.get("dark_mode", True)
        self.search_engine = self.settings.get("search_engine", DEFAULT_SEARCH_ENGINE)
        self.custom_accent = self.settings.get("custom_accent", DEFAULT_ACCENT_COLOR)
        self.home_url = SEARCH_ENGINES.get(
            self.search_engine, SEARCH_ENGINES["Google"]
        )["home_url"]

        self._setup_web_profile()
        self._setup_ui()
        self.apply_theme()

        self.shortcut_downloads = QShortcut(QKeySequence("Ctrl+J"), self)
        self.shortcut_downloads.activated.connect(self.toggle_downloads_bubble)

        self.shortcut_new_tab = QShortcut(QKeySequence("Ctrl+T"), self)
        self.shortcut_new_tab.activated.connect(lambda: self.add_new_tab(self.home_url))

        self.add_new_tab(self.initial_url or self.home_url)

    def _setup_web_profile(self):
        app_data_path = get_app_data_folder()

        self.profile = QWebEngineProfile("EcoBrowserProfile", self)
        self.profile.setPersistentStoragePath(os.path.join(app_data_path, "storage"))
        self.profile.setCachePath(os.path.join(app_data_path, "cache"))
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )

        # Injected Script for AI Media Filter (NSFW blur + AI-generated watermark)
        script = QWebEngineScript()
        script.setName("EcoBrowserAiGuard")
        script.setSourceCode(AI_SAFEGUARD_SCRIPT)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)
        self.profile.scripts().insert(script)

        self.interceptor = ContentBlocker()
        self.profile.setUrlRequestInterceptor(self.interceptor)
        self.profile.downloadRequested.connect(self.handle_download_request)

    def _setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Chrome / Arc Tab Strip
        self.tab_strip_widget = self._build_tab_strip()
        main_layout.addWidget(self.tab_strip_widget)

        # 2. Modern Navigation Toolbar
        self.toolbar_panel = self._build_toolbar()
        main_layout.addWidget(self.toolbar_panel)

        # 3. Dynamic Bookmarks Bar
        self.bookmarks_bar_widget = self._build_bookmarks_bar()
        main_layout.addWidget(self.bookmarks_bar_widget)
        self.update_bookmarks_bar()

        # 4. Web Views Stack
        self.stack = QStackedWidget()
        self.stack.setObjectName("webStack")
        main_layout.addWidget(self.stack)

    def _build_tab_strip(self):
        tab_strip = QWidget()
        tab_strip.setObjectName("tabStripPanel")

        tab_strip_layout = QHBoxLayout(tab_strip)
        tab_strip_layout.setContentsMargins(8, 6, 8, 0)
        tab_strip_layout.setSpacing(6)

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
        tab_strip_layout.addWidget(self.tab_bar)

        self.new_tab_button = QPushButton()
        self.new_tab_button.setObjectName("newTabButton")
        self.new_tab_button.setFixedSize(28, 28)
        self.new_tab_button.setIconSize(QSize(14, 14))
        self.new_tab_button.setToolTip("New tab (Ctrl+T)")
        self.new_tab_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_tab_button.clicked.connect(lambda: self.add_new_tab(self.home_url))
        tab_strip_layout.addWidget(self.new_tab_button)

        tab_strip_layout.addStretch()
        return tab_strip

    def _build_toolbar(self):
        toolbar_panel = QWidget()
        toolbar_panel.setObjectName("toolbarPanel")
        toolbar_panel.setFixedHeight(46)

        toolbar_layout = QHBoxLayout(toolbar_panel)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        toolbar_layout.setSpacing(6)

        self.back_button = self._make_toolbar_button("Back")
        self.forward_button = self._make_toolbar_button("Forward")
        self.refresh_button = self._make_toolbar_button("Reload")

        self.back_button.clicked.connect(self.go_back)
        self.forward_button.clicked.connect(self.go_forward)
        self.refresh_button.clicked.connect(self.on_reload_clicked)

        toolbar_layout.addWidget(self.back_button)
        toolbar_layout.addWidget(self.forward_button)
        toolbar_layout.addWidget(self.refresh_button)

        # Address Omnibox
        self.address_panel = QWidget()
        self.address_panel.setObjectName("addressPanel")
        self.address_panel.setFixedHeight(36)

        address_layout = QHBoxLayout(self.address_panel)
        address_layout.setContentsMargins(12, 0, 8, 0)
        address_layout.setSpacing(8)

        self.security_icon_btn = QPushButton()
        self.security_icon_btn.setObjectName("securityBtn")
        self.security_icon_btn.setFixedSize(20, 20)
        self.security_icon_btn.setIconSize(QSize(14, 14))

        self.url_input = QLineEdit()
        self.url_input.setObjectName("omniboxInput")
        self.url_input.setPlaceholderText(
            f"Search {self.search_engine} or type a URL (AI Guard active)"
        )
        self.url_input.setFrame(False)
        self.url_input.returnPressed.connect(self.navigate_to_url)

        self.bookmark_button = QPushButton()
        self.bookmark_button.setObjectName("bookmarkStarBtn")
        self.bookmark_button.setFixedSize(28, 28)
        self.bookmark_button.setIconSize(QSize(16, 16))
        self.bookmark_button.clicked.connect(self.toggle_bookmark_current_page)

        address_layout.addWidget(self.security_icon_btn)
        address_layout.addWidget(self.url_input, 1)
        address_layout.addWidget(self.bookmark_button)
        toolbar_layout.addWidget(self.address_panel, 1)

        # Downloads Button
        self.downloads_button = self._make_toolbar_button("Downloads (Ctrl+J)")
        self.downloads_button.clicked.connect(self.toggle_downloads_bubble)
        toolbar_layout.addWidget(self.downloads_button)

        # Main Menu Button (3-dots)
        self.menu_button = self._make_toolbar_button("EcoBrowser Menu")
        self.menu_button.clicked.connect(self.show_main_menu)
        toolbar_layout.addWidget(self.menu_button)

        self._build_main_menu()
        return toolbar_panel

    def _build_main_menu(self):
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        self.menu = QMenu(self)
        self.menu.addAction("Blockers and filters", self.open_block_manager_dialog)
        self.menu.addSeparator()

        # 1. Search Engine selection submenu
        self.search_menu = QMenu("Search Engine", self.menu)
        self.search_menu.setIcon(
            render_svg_icon(SVG_ICONS["search"], theme["icon_color"], 14)
        )
        self.search_engine_actions = {}
        for engine_key in SEARCH_ENGINES.keys():
            act = self.search_menu.addAction(engine_key)
            act.setCheckable(True)
            act.setChecked(engine_key == self.search_engine)
            act.triggered.connect(
                lambda checked, k=engine_key: self.set_search_engine(k)
            )
            self.search_engine_actions[engine_key] = act
        self.menu.addMenu(self.search_menu)

        # 2. Color customization action
        self.color_action = self.menu.addAction(
            "Color Customization...", self.open_color_customizer_dialog
        )
        self.color_action.setIcon(
            render_svg_icon(SVG_ICONS["palette"], theme["icon_color"], 14)
        )

        self.menu.addSeparator()
        self.menu.addAction("New tab\tCtrl+T", lambda: self.add_new_tab(self.home_url))
        self.menu.addAction("Downloads\tCtrl+J", self.open_downloads_dialog)
        self.menu.addAction("Bookmarks Manager", self.open_bookmarks_dialog)
        self.menu.addAction("History\tCtrl+H", self.open_history_dialog)
        self.menu.addAction("Clear browsing cookies", self.clear_cookies)
        self.menu.addSeparator()
        self.dark_mode_action = self.menu.addAction("Dark Mode")
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)

        # 3. Windows Registry Default Browser Status (Protected against duplicate writes)
        self.menu.addSeparator()
        reg_status_label = (
            "Windows Registry: Registered (Protected)"
            if is_browser_registered()
            else "Register as Windows Default Browser"
        )
        self.reg_action = self.menu.addAction(
            reg_status_label, self.toggle_or_view_registry_status
        )

        self.menu.addSeparator()
        self.menu.addAction("Exit EcoBrowser", self.close)

    def set_search_engine(self, engine_key):
        if engine_key in SEARCH_ENGINES:
            self.search_engine = engine_key
            self.save_setting("search_engine", engine_key)
            self.home_url = SEARCH_ENGINES[engine_key]["home_url"]
            self.url_input.setPlaceholderText(
                f"Search {engine_key} or type a URL (AI Guard active)"
            )
            for k, act in getattr(self, "search_engine_actions", {}).items():
                act.setChecked(k == engine_key)

    def open_color_customizer_dialog(self):
        dialog = ColorCustomizerDialog(self)
        dialog.exec()

    def toggle_or_view_registry_status(self):
        if sys.platform != "win32" or reg is None:
            QMessageBox.information(
                self,
                "Windows Registry",
                "EcoBrowser Windows Registry integration is only available when running natively on Windows.\n\n"
                "✓ Safe Mode Active: Duplicate registry record protection is enabled and verified.",
            )
            return

        if is_browser_registered():
            QMessageBox.information(
                self,
                "Registry Status",
                "EcoBrowser is already registered in the Windows Registry.\n\n"
                "✓ Safe Mode Active: Duplicate registry writes are prevented so no extra records will be created.",
            )
        else:
            success = register_as_browser(force=True)
            if success:
                QMessageBox.information(
                    self,
                    "Registry Registration",
                    "EcoBrowser has been successfully registered in the Windows Registry!\n\n"
                    "Status has been saved to settings. No duplicate records will be added on future launches.",
                )
                if hasattr(self, "reg_action"):
                    self.reg_action.setText("Windows Registry: Registered (Protected)")
            else:
                QMessageBox.warning(
                    self,
                    "Registry Registration",
                    "Could not write to Windows Registry. Please ensure EcoBrowser has appropriate user permissions.",
                )

    def show_main_menu(self):
        self.dark_mode_action.setChecked(self.is_dark_mode)
        for k, act in getattr(self, "search_engine_actions", {}).items():
            act.setChecked(k == self.search_engine)
        if hasattr(self, "reg_action"):
            self.reg_action.setText(
                "Windows Registry: Registered (Protected)"
                if is_browser_registered()
                else "Register as Windows Default Browser"
            )
        pos = self.menu_button.mapToGlobal(self.menu_button.rect().bottomRight())
        self.menu.exec(pos)

    def _build_bookmarks_bar(self):
        bar_container = QWidget()
        bar_container.setObjectName("bookmarksBarPanel")
        bar_container.setFixedHeight(30)
        self.bookmarks_layout = QHBoxLayout(bar_container)
        self.bookmarks_layout.setContentsMargins(10, 2, 10, 2)
        self.bookmarks_layout.setSpacing(6)
        self.bookmarks_layout.addStretch()
        return bar_container

    def _make_toolbar_button(self, tooltip=""):
        button = QPushButton()
        button.setProperty("class", "toolbarBtn")
        button.setFixedSize(32, 32)
        button.setIconSize(QSize(18, 18))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            button.setToolTip(tooltip)
        return button

    def apply_theme(self):
        base_theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        theme = dict(base_theme)
        accent = getattr(self, "custom_accent", theme["accent_blue"])
        theme["accent_blue"] = accent
        theme["progress_fill"] = accent

        self.setStyleSheet(self._build_stylesheet(theme, accent))
        self.update_all_icons()
        self._update_all_tab_close_buttons()

        for i in range(self.stack.count()):
            web_view = self.stack.widget(i)
            if isinstance(web_view, QWebEngineView):
                web_view.page().settings().setAttribute(
                    QWebEngineSettings.WebAttribute.ForceDarkMode, self.is_dark_mode
                )

    def update_all_icons(self):
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        icon_color = theme["icon_color"]
        accent = getattr(self, "custom_accent", theme["accent_blue"])

        self.back_button.setIcon(render_svg_icon(SVG_ICONS["back"], icon_color, 18))
        self.forward_button.setIcon(
            render_svg_icon(SVG_ICONS["forward"], icon_color, 18)
        )
        reload_icon = "stop" if self.is_loading else "reload"
        self.refresh_button.setIcon(
            render_svg_icon(SVG_ICONS[reload_icon], icon_color, 18)
        )
        self.new_tab_button.setIcon(
            render_svg_icon(SVG_ICONS["new_tab"], icon_color, 14)
        )

        has_active_dl = any(
            d.state() == QWebEngineDownloadRequest.DownloadState.DownloadInProgress
            for d in getattr(self, "active_downloads", {}).keys()
        )
        dl_icon_color = accent if has_active_dl else icon_color
        self.downloads_button.setIcon(
            render_svg_icon(SVG_ICONS["download"], dl_icon_color, 18)
        )
        self.menu_button.setIcon(render_svg_icon(SVG_ICONS["menu"], icon_color, 18))

        current_view = self.get_current_view()
        is_https = (
            current_view.url().toString().startswith("https://")
            if current_view
            else True
        )
        sec_icon = "lock" if is_https else "unlock"
        sec_color = theme["text_secondary"] if is_https else "#f85149"
        self.security_icon_btn.setIcon(
            render_svg_icon(SVG_ICONS[sec_icon], sec_color, 14)
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
        path = self.settings_file_path()
        defaults = {
            "dark_mode": True,
            "search_engine": DEFAULT_SEARCH_ENGINE,
            "custom_accent": DEFAULT_ACCENT_COLOR,
            "registry_registered": False,
        }
        if not os.path.exists(path):
            return defaults
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
                return defaults
        except Exception:
            return defaults

    def save_setting(self, key, value):
        path = self.settings_file_path()
        current = self.load_all_settings()
        current[key] = value
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=4)
        except Exception:
            pass

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
        btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; border-radius: 10px; margin-right: 4px; }}
            QPushButton:hover {{ background: {theme['close_btn_hover']}; }}
        """)
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
            QMainWindow {{ background-color: {theme['window_bg']}; font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif; }}
            QWidget#tabStripPanel {{ background-color: {theme['tabstrip_bg']}; border: none; }}
            QTabBar {{ background-color: transparent; border: none; qproperty-drawBase: 0; }}
            QTabBar::tab {{
                background-color: transparent;
                color: {theme['text_secondary']};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                min-width: 140px;
                max-width: 240px;
                height: 34px;
                padding-left: 12px;
                padding-right: 32px;
                margin-right: 2px;
                font-size: 9.5pt;
            }}
            QTabBar::tab:!selected {{ border-right: 1px solid {theme['tab_divider']}; }}
            QTabBar::tab:hover:!selected {{ background-color: {theme['tab_inactive_hover']}; color: {theme['text_primary']}; }}
            QTabBar::tab:selected {{
                background-color: {theme['tab_active_bg']};
                color: {theme['text_primary']};
                font-weight: 600;
                border-top: 2px solid {accent};
            }}
            QPushButton#newTabButton {{ background-color: transparent; border: none; border-radius: 14px; }}
            QPushButton#newTabButton:hover {{ background-color: {theme['hover_bg']}; }}
            QWidget#toolbarPanel {{ background-color: {theme['toolbar_bg']}; border-bottom: 1px solid {theme['divider']}; }}
            QPushButton[class="toolbarBtn"] {{ background-color: transparent; border: none; border-radius: 16px; }}
            QPushButton[class="toolbarBtn"]:hover {{ background-color: {theme['hover_bg']}; }}
            QWidget#addressPanel {{ background-color: {theme['omnibox_bg']}; border-radius: 18px; border: 1px solid {theme['divider']}; }}
            QWidget#addressPanel:hover {{ background-color: {theme['omnibox_hover_bg']}; border-color: {accent}; }}
            QLineEdit#omniboxInput {{ background-color: transparent; color: {theme['text_primary']}; border: none; font-size: 9.5pt; }}
            QPushButton#securityBtn {{ background-color: transparent; border: none; }}
            QPushButton#bookmarkStarBtn {{ background-color: transparent; border: none; border-radius: 14px; }}
            QPushButton#bookmarkStarBtn:hover {{ background-color: {theme['hover_bg']}; }}
            QWidget#bookmarksBarPanel {{ background-color: {theme['toolbar_bg']}; border-bottom: 1px solid {theme['divider']}; }}
            QWidget#bookmarksBarPanel QPushButton {{ color: {theme['text_primary']}; background-color: transparent; font-size: 8.5pt; padding: 4px 10px; border: none; border-radius: 6px; }}
            QWidget#bookmarksBarPanel QPushButton:hover {{ background-color: {theme['hover_bg']}; }}
            QFrame#downloadsBubbleCard {{ background-color: {theme['menu_bg']}; border: 1px solid {theme['divider']}; border-radius: 12px; }}
            QFrame#downloadItemCard {{ background-color: transparent; border-radius: 8px; padding: 4px 6px; }}
            QFrame#downloadItemCard:hover {{ background-color: {theme['hover_bg']}; }}
            QProgressBar#downloadProgressBar {{ background-color: {theme['progress_bg']}; border: none; border-radius: 2px; height: 4px; }}
            QProgressBar#downloadProgressBar::chunk {{ background-color: {accent}; border-radius: 2px; }}
            QPushButton.downloadActionBtn {{ background-color: transparent; color: {accent}; border: none; font-size: 8.5pt; font-weight: 500; padding: 3px 6px; border-radius: 4px; }}
            QPushButton.downloadActionBtn:hover {{ background-color: {theme['hover_bg']}; }}
            QMenu {{ background-color: {theme['menu_bg']}; color: {theme['text_primary']}; border: 1px solid {theme['divider']}; padding: 6px 0px; border-radius: 8px; }}
            QMenu::item {{ padding: 6px 24px 6px 20px; font-size: 9.5pt; }}
            QMenu::item:selected {{ background-color: {theme['hover_bg']}; }}
            QDialog {{ background-color: {theme['toolbar_bg']}; color: {theme['text_primary']}; }}
            QGroupBox {{ color: {theme['text_primary']}; font-weight: 600; border: 1px solid {theme['divider']}; border-radius: 8px; margin-top: 10px; padding-top: 14px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
            QCheckBox {{ color: {theme['text_primary']}; font-size: 9.5pt; }}
            QDialog QPushButton {{ background-color: {theme['omnibox_bg']}; color: {theme['text_primary']}; border: 1px solid {theme['divider']}; border-radius: 6px; padding: 6px 16px; font-size: 9pt; }}
            QDialog QPushButton:hover {{ background-color: {theme['hover_bg']}; }}
        """

    def get_current_view(self):
        return self.stack.currentWidget()

    def add_new_tab(self, url):
        web_view = QWebEngineView()
        page = EcoWebEnginePage(self.profile, self, web_view)
        web_view.setPage(page)

        if self.is_dark_mode:
            web_view.page().settings().setAttribute(
                QWebEngineSettings.WebAttribute.ForceDarkMode, True
            )

        web_view.urlChanged.connect(
            lambda _url, view=web_view: self.sync_address_bar(view)
        )
        web_view.titleChanged.connect(
            lambda title, view=web_view: self.update_tab_title(title, view)
        )
        web_view.iconChanged.connect(
            lambda icon, view=web_view: self.sync_tab_icon(view, icon)
        )
        web_view.loadStarted.connect(
            lambda view=web_view: self.handle_load_started(view)
        )
        web_view.loadFinished.connect(
            lambda ok, view=web_view: self.handle_load_finished(view, ok)
        )
        page.navigationRequested.connect(
            lambda req, view=web_view: self.handle_navigation(req, view)
        )

        stack_index = self.stack.addWidget(web_view)

        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        initial_tab_icon = render_svg_icon(
            SVG_ICONS["globe"], theme["text_secondary"], 16
        )
        tab_index = self.tab_bar.addTab(initial_tab_icon, "New Tab")
        self._setup_tab_close_button(tab_index)

        self.tab_bar.setCurrentIndex(tab_index)
        self.stack.setCurrentIndex(stack_index)
        web_view.setUrl(QUrl(url))
        return web_view

    def close_tab(self, index):
        if self.tab_bar.count() <= 1:
            return

        web_view = self.stack.widget(index)
        self.tab_bar.removeTab(index)
        self.stack.removeWidget(web_view)
        web_view.deleteLater()
        gc.collect()

        for i in range(self.tab_bar.count()):
            self._setup_tab_close_button(i)

    def switch_tab(self, index):
        if index == -1:
            return
        self.stack.setCurrentIndex(index)
        view = self.get_current_view()
        self.sync_address_bar(view)
        if view:
            self.back_button.setEnabled(view.history().canGoBack())
            self.forward_button.setEnabled(view.history().canGoForward())

    def update_tab_title(self, title, web_view):
        display_title = title or "New Tab"
        if len(display_title) > 22:
            display_title = display_title[:20] + "..."
        for i in range(self.stack.count()):
            if self.stack.widget(i) == web_view:
                self.tab_bar.setTabText(i, display_title)
                break

    def sync_tab_icon(self, web_view, icon):
        for i in range(self.stack.count()):
            if self.stack.widget(i) == web_view and not icon.isNull():
                self.tab_bar.setTabIcon(i, icon)
                break

    def handle_load_started(self, web_view):
        if web_view == self.get_current_view():
            self.is_loading = True
            theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
            self.refresh_button.setIcon(
                render_svg_icon(SVG_ICONS["stop"], theme["icon_color"], 18)
            )

    def handle_load_finished(self, web_view, ok):
        if web_view == self.get_current_view():
            self.is_loading = False
            theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
            self.refresh_button.setIcon(
                render_svg_icon(SVG_ICONS["reload"], theme["icon_color"], 18)
            )
            self.back_button.setEnabled(web_view.history().canGoBack())
            self.forward_button.setEnabled(web_view.history().canGoForward())

    def on_reload_clicked(self):
        view = self.get_current_view()
        if not view:
            return
        if self.is_loading:
            view.stop()
        else:
            view.reload()

    def go_back(self):
        view = self.get_current_view()
        if view:
            view.back()

    def go_forward(self):
        view = self.get_current_view()
        if view:
            view.forward()

    def navigate_to_url(self):
        text = self.url_input.text().strip()
        view = self.get_current_view()
        if not view or not text:
            return
        if (
            text.startswith("http://")
            or text.startswith("https://")
            or text.startswith("eco://")
            or text.startswith("about:")
        ):
            url = text
        elif "." in text and " " not in text:
            url = "https://" + text
        else:
            engine_info = SEARCH_ENGINES.get(
                self.search_engine, SEARCH_ENGINES["Google"]
            )
            url = engine_info["query_url"] + text
        view.setUrl(QUrl(url))

    def sync_address_bar(self, web_view):
        if not web_view or web_view != self.get_current_view():
            return
        current_url = web_view.url().toString()
        self.url_input.setText("" if current_url == "about:blank" else current_url)

        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        is_https = current_url.startswith("https://")
        sec_icon = "lock" if is_https else "unlock"
        sec_color = theme["text_secondary"] if is_https else "#f85149"
        self.security_icon_btn.setIcon(
            render_svg_icon(SVG_ICONS[sec_icon], sec_color, 14)
        )

        bookmarks = self.load_bookmarks()
        is_bm = any(b["url"] == current_url for b in bookmarks)
        star_icon = "star_filled" if is_bm else "star_outline"
        star_color = theme["star_active"] if is_bm else theme["icon_color"]
        self.bookmark_button.setIcon(
            render_svg_icon(SVG_ICONS[star_icon], star_color, 16)
        )

        self.log_to_history(current_url)

    def handle_navigation(self, request, web_view):
        url = request.url()
        host = url.host().lower()
        full_url = url.toString().lower()

        is_ad = self.interceptor.ad_block_enabled and any(
            ad in host for ad in AD_DOMAINS
        )
        is_adult = self.interceptor.nude_block_enabled and (
            any(d in host for d in ADULT_DOMAINS)
            or any(kw in full_url for kw in ADULT_KEYWORDS)
        )

        if is_ad or is_adult:
            request.reject()
            reason = "Ad/Tracker Domain" if is_ad else "Adult / Explicit Domain"
            html = build_blocked_page_html(host or "blocked-site", reason)
            QTimer.singleShot(0, lambda: web_view.setHtml(html, url))
        else:
            request.accept()

    def history_file_path(self):
        return os.path.join(get_app_data_folder(), "history.txt")

    def log_to_history(self, url):
        if not url or url.startswith("data:") or url == "about:blank":
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.history_file_path(), "a", encoding="utf-8") as f:
                f.write(f"{timestamp} - {url}\n")
        except OSError:
            pass

    def open_history_dialog(self):
        dialog = HistoryDialog(self.history_file_path(), self)
        dialog.exec()

    def open_block_manager_dialog(self):
        dialog = BlockManagerDialog(self.interceptor, self)
        dialog.exec()

    def bookmarks_file_path(self):
        return os.path.join(get_app_data_folder(), "bookmarks.json")

    def load_bookmarks(self):
        path = self.bookmarks_file_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_bookmarks(self, bookmarks):
        path = self.bookmarks_file_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(bookmarks, f, indent=4)
        except Exception:
            pass

    def toggle_bookmark_current_page(self):
        view = self.get_current_view()
        if not view:
            return
        url = view.url().toString()
        title = view.title() or url
        if not url or url == "about:blank":
            return

        bookmarks = self.load_bookmarks()
        existing = next((b for b in bookmarks if b["url"] == url), None)
        if existing:
            bookmarks = [b for b in bookmarks if b["url"] != url]
        else:
            bookmarks.append({"title": title, "url": url})
        self.save_bookmarks(bookmarks)
        self.update_bookmarks_bar()
        self.sync_address_bar(view)

    def delete_bookmark_by_url(self, url):
        bookmarks = [b for b in self.load_bookmarks() if b["url"] != url]
        self.save_bookmarks(bookmarks)
        self.update_bookmarks_bar()

    def open_bookmarks_dialog(self):
        QMessageBox.information(
            self,
            "Bookmarks",
            f"You have {len(self.load_bookmarks())} saved bookmarks in your EcoBrowser bar.",
        )

    def update_bookmarks_bar(self):
        while self.bookmarks_layout.count() > 1:
            item = self.bookmarks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        bookmarks = self.load_bookmarks()
        if not bookmarks:
            if hasattr(self, "bookmarks_bar_widget"):
                self.bookmarks_bar_widget.hide()
            return

        self.bookmarks_bar_widget.show()
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        bm_icon = render_svg_icon(SVG_ICONS["globe"], theme["text_secondary"], 14)

        for bm in bookmarks:
            title = bm["title"]
            if len(title) > 20:
                title = title[:18] + "..."
            btn = BookmarkButton(title, bm["url"], bm_icon, self)
            self.bookmarks_layout.insertWidget(self.bookmarks_layout.count() - 1, btn)

    def navigate_to_bookmark(self, url):
        view = self.get_current_view()
        if view:
            view.setUrl(QUrl(url))

    def downloads_file_path(self):
        return os.path.join(get_app_data_folder(), "downloads.json")

    def load_downloads(self):
        path = self.downloads_file_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_downloads(self, downloads):
        path = self.downloads_file_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(downloads, f, indent=4)
        except Exception:
            pass

    def handle_download_request(self, download):
        default_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        suggested = download.suggestedFileName() or "downloaded_file"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", os.path.join(default_dir, suggested)
        )
        if not save_path:
            return

        download.setDownloadDirectory(os.path.dirname(save_path))
        download.setDownloadFileName(os.path.basename(save_path))
        download.accept()

        entry = {
            "fileName": os.path.basename(save_path),
            "filePath": save_path,
            "state": "in_progress",
            "receivedBytes": 0,
            "totalBytes": 0,
        }
        self.active_downloads[download] = entry

        download.receivedBytesChanged.connect(
            lambda d=download: self._on_download_progress(d)
        )
        download.stateChanged.connect(
            lambda state, d=download: self._on_download_state_changed(d, state)
        )

        self.update_all_icons()
        self._show_downloads_bubble()

    def _on_download_progress(self, download):
        if download not in self.active_downloads:
            return
        entry = self.active_downloads[download]
        entry["receivedBytes"] = download.receivedBytes()
        entry["totalBytes"] = download.totalBytes()
        if self.downloads_bubble and self.downloads_bubble.isVisible():
            self.downloads_bubble.update_card_progress(download)

    def _on_download_state_changed(self, download, state):
        if download not in self.active_downloads:
            return
        entry = self.active_downloads[download]

        if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            entry["state"] = "completed"
            entry["totalBytes"] = download.totalBytes()
            history = self.load_downloads()
            history.insert(0, entry)
            self.save_downloads(history[:200])
            del self.active_downloads[download]
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

        btn_pos = self.downloads_button.mapToGlobal(
            self.downloads_button.rect().bottomRight()
        )
        bubble_x = btn_pos.x() - self.downloads_bubble.width()
        bubble_y = btn_pos.y() + 4
        self.downloads_bubble.move(bubble_x, bubble_y)
        self.downloads_bubble.show()

    def open_downloads_dialog(self):
        dialog = DownloadsDialog(self)
        dialog.exec()

    def closeEvent(self, event):
        for i in range(self.stack.count()):
            w = self.stack.widget(i)
            if isinstance(w, QWebEngineView):
                w.setPage(None)
                w.deleteLater()
        event.accept()


# =============================================================================
# Bootstrap Helper & Entry Point
# =============================================================================


def get_app_data_folder():
    app_data_root = os.getenv("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(app_data_root, "EcoBrowser")
    os.makedirs(folder, exist_ok=True)
    return folder


def get_initial_url_from_args(argv):
    return argv[1] if len(argv) > 1 and argv[1].startswith("http") else None


if __name__ == "__main__":
    register_as_browser()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = EcoBrowserWindow(get_initial_url_from_args(sys.argv))
    window.show()
    sys.exit(app.exec())
