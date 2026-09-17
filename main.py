import os
import sys
import gc
import json
import subprocess
import winreg as reg
from datetime import datetime

from PyQt6.QtCore import QUrl, QTimer, Qt, QByteArray, QSize, QStandardPaths
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QKeySequence, QShortcut
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineUrlRequestInterceptor,
    QWebEngineSettings,
    QWebEngineDownloadRequest,
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
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QScrollArea,
    QProgressBar,
    QFrame,
)

# =============================================================================
# Constants & Filter Lists
# =============================================================================

APP_NAME = "EcoBrowser"
HOME_URL = "https://www.google.com"

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
]

# =============================================================================
# Chrome Refresh Color Palettes
# =============================================================================

LIGHT_THEME = {
    "window_bg": "#dee1e6",
    "tabstrip_bg": "#dee1e6",
    "toolbar_bg": "#ffffff",
    "tab_active_bg": "#ffffff",
    "tab_inactive_hover": "rgba(255, 255, 255, 0.65)",
    "omnibox_bg": "#f1f3f4",
    "omnibox_hover_bg": "#e8eaed",
    "text_primary": "#202124",
    "text_secondary": "#5f6368",
    "icon_color": "#5f6368",
    "hover_bg": "rgba(0, 0, 0, 0.08)",
    "pressed_bg": "rgba(0, 0, 0, 0.14)",
    "divider": "#dadce0",
    "tab_divider": "rgba(60, 64, 67, 0.22)",
    "menu_bg": "#ffffff",
    "close_icon_color": "#5f6368",
    "close_btn_hover": "rgba(0, 0, 0, 0.12)",
    "star_active": "#1a73e8",
    "accent_blue": "#1a73e8",
    "progress_bg": "#e8eaed",
    "progress_fill": "#1a73e8",
}

DARK_THEME = {
    "window_bg": "#1e1f22",
    "tabstrip_bg": "#1e1f22",
    "toolbar_bg": "#2b2d30",
    "tab_active_bg": "#2b2d30",
    "tab_inactive_hover": "rgba(255, 255, 255, 0.08)",
    "omnibox_bg": "#1e1f22",
    "omnibox_hover_bg": "#28292c",
    "text_primary": "#f1f3f4",
    "text_secondary": "#9aa0a6",
    "icon_color": "#c4c7c5",
    "hover_bg": "rgba(255, 255, 255, 0.10)",
    "pressed_bg": "rgba(255, 255, 255, 0.16)",
    "divider": "#3c4043",
    "tab_divider": "rgba(255, 255, 255, 0.14)",
    "menu_bg": "#292a2d",
    "close_icon_color": "#c4c7c5",
    "close_btn_hover": "rgba(255, 255, 255, 0.15)",
    "star_active": "#8ab4f8",
    "accent_blue": "#8ab4f8",
    "progress_bg": "#3c4043",
    "progress_fill": "#8ab4f8",
}

SVG_ICONS = {
    "back": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>',
    "forward": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"/></svg>',
    "reload": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M17.65 6.35A7.958 7.958 0 0 0 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0 1 12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>',
    "stop": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
    "new_tab": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>',
    "lock": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg>',
    "unlock": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 17c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm6-9h-1V6c0-2.76-2.24-5-5-5-2.28 0-4.27 1.54-4.84 3.75l1.94.52C8.45 3.93 9.94 3 11.6 3c1.88 0 3.4 1.52 3.4 3.4V8H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm0 12H6V10h12v10z"/></svg>',
    "star_outline": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M22 9.24l-7.19-.62L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.63-7.03L22 9.24zM12 15.4l-3.76 2.27 1-4.28-3.32-2.88 4.38-.38L12 6.1l1.71 4.04 4.38.38-3.32 2.88 1 4.28M12 15.4z"/></svg>',
    "star_filled": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>',
    "menu": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="5" r="2" fill="{color}"/><circle cx="12" cy="12" r="2" fill="{color}"/><circle cx="12" cy="19" r="2" fill="{color}"/></svg>',
    "extensions": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M20.5 11H19V7c0-1.1-.9-2-2-2h-4V3.5C13 2.12 11.88 1 10.5 1S8 2.12 8 3.5V5H4c-1.1 0-1.99.9-1.99 2v3.8H3.5c1.49 0 2.7 1.21 2.7 2.7s-1.21 2.7-2.7 2.7H2V20c0 1.1.9 2 2 2h3.8v-1.5c0-1.49 1.21-2.7 2.7-2.7s2.7 1.21 2.7 2.7V22H17c1.1 0 2-.9 2-2v-4h1.5c1.38 0 2.5-1.12 2.5-2.5s-1.12-2.5-2.5-2.5z"/></svg>',
    "shield": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg>',
    "globe": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>',
    "download": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>',
    "folder": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>',
    "file": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>',
    "check_circle": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>',
    "tab_close": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
}


def render_svg_icon(svg_template, color, size=20):
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
# Windows Default Browser Registration Helper
# =============================================================================


def register_as_browser():
    if sys.platform != "win32":
        return

    if getattr(sys, "frozen", False):
        app_path = f'"{sys.executable}"'
    else:
        app_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'

    app_name = "EcoBrowser"
    capabilities_path = r"Software\EcoBrowser\Capabilities"

    try:
        with reg.CreateKey(reg.HKEY_CURRENT_USER, capabilities_path) as key:
            reg.SetValueEx(key, "ApplicationName", 0, reg.REG_SZ, app_name)
            reg.SetValueEx(
                key,
                "ApplicationDescription",
                0,
                reg.REG_SZ,
                "A lightweight, private Python web browser.",
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

    except Exception:
        pass


# =============================================================================
# Warning page shown when a site is blocked
# =============================================================================


def build_blocked_page_html(blocked_domain):
    return f"""<!DOCTYPE html><html><head><style>
    body {{ background: #202124; color: #e8eaed; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }} 
    .warning-card {{ background: #292a2d; padding: 32px 40px; border-radius: 12px; border: 1px solid #3c4043; text-align: center; max-width: 420px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }} 
    .warning-title {{ color: #ea4335; font-size: 20px; margin-top: 0; margin-bottom: 12px; font-weight: 500; }} 
    .warning-text {{ color: #9aa0a6; font-size: 14px; margin-bottom: 24px; line-height: 1.5; }} 
    .warning-btn {{ background: #8ab4f8; color: #202124; text-decoration: none; padding: 10px 24px; border-radius: 20px; font-size: 13px; font-weight: 500; display: inline-block; }} 
    .warning-btn:hover {{ background: #aecbfa; }}
    </style></head><body><div class='warning-card'>
    <h1 class='warning-title'>Site Blocked</h1>
    <p class='warning-text'>Access to <b>{blocked_domain}</b> was blocked by EcoBrowser privacy and safety protections.</p>
    <a class='warning-btn' href='https://www.google.com'>Back to Safety</a>
    </div></body></html>"""


# =============================================================================
# Content Filtering Helpers
# =============================================================================


def url_matches_ad_domain(host):
    return any(ad_domain in host for ad_domain in AD_DOMAINS)


def url_matches_adult_content(host, full_url_lowercase):
    matches_known_domain = any(domain in host for domain in ADULT_DOMAINS)
    matches_keyword = any(keyword in full_url_lowercase for keyword in ADULT_KEYWORDS)
    return matches_known_domain or matches_keyword


class ContentBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        self.ad_block_enabled = True
        self.nude_block_enabled = True

    def interceptRequest(self, info):
        url = info.requestUrl()
        url_string = url.toString()

        is_http_or_https = url_string.startswith("http://") or url_string.startswith(
            "https://"
        )
        if not is_http_or_https:
            return

        host = url.host().lower()
        full_url_lowercase = url_string.lower()

        if self.ad_block_enabled and url_matches_ad_domain(host):
            info.block(True)
            return

        if self.nude_block_enabled and url_matches_adult_content(
            host, full_url_lowercase
        ):
            info.block(True)
            return


# =============================================================================
# Custom Bookmark Button with Right-Click Context Menu
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
        delete_action = menu.addAction("Delete")
        action = menu.exec(self.mapToGlobal(pos))
        if action == delete_action:
            self.browser_window.delete_bookmark_by_url(self.bookmark_url)


# =============================================================================
# Dialogs: History, Block Manager, Bookmarks
# =============================================================================


class HistoryDialog(QDialog):
    def __init__(self, history_file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("History")
        self.resize(600, 420)
        self.history_file_path = history_file_path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        self.text_view.setText(self._load_history_text(self.history_file_path))
        layout.addWidget(self.text_view)

        btn_layout = QHBoxLayout()
        self.btn_clear = QPushButton("Clear browsing data")
        self.btn_close = QPushButton("Close")

        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.btn_clear.clicked.connect(self.clear_history)
        self.btn_close.clicked.connect(self.accept)

    @staticmethod
    def _load_history_text(history_file_path):
        if not os.path.exists(history_file_path):
            return "No browsing history found."
        with open(history_file_path, "r", encoding="utf-8") as history_file:
            return history_file.read()

    def clear_history(self):
        try:
            if os.path.exists(self.history_file_path):
                os.remove(self.history_file_path)
            self.text_view.setText("No browsing history found.")
        except Exception:
            pass


class BlockManagerDialog(QDialog):
    def __init__(self, interceptor, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Extensions & Safety")
        self.resize(400, 220)
        self.interceptor = interceptor

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title_label = QLabel("Content Protection")
        title_font = title_label.font()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        self.ad_block_checkbox = QCheckBox("Block ads and trackers")
        self.ad_block_checkbox.setChecked(self.interceptor.ad_block_enabled)
        self.ad_block_checkbox.toggled.connect(self._on_ad_block_toggled)
        layout.addWidget(self.ad_block_checkbox)

        self.nude_block_checkbox = QCheckBox("Filter adult / explicit content")
        self.nude_block_checkbox.setChecked(self.interceptor.nude_block_enabled)
        self.nude_block_checkbox.toggled.connect(self._on_nude_block_toggled)
        layout.addWidget(self.nude_block_checkbox)

        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        close_btn = QPushButton("Done")
        close_btn.clicked.connect(self.accept)
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)

    def _on_ad_block_toggled(self, is_checked):
        self.interceptor.ad_block_enabled = is_checked

    def _on_nude_block_toggled(self, is_checked):
        self.interceptor.nude_block_enabled = is_checked


class BookmarksDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bookmark Manager")
        self.resize(520, 360)
        self.browser_window = parent

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.btn_open = QPushButton("Open")
        self.btn_delete = QPushButton("Delete")
        self.btn_clear_all = QPushButton("Clear All")
        self.btn_close = QPushButton("Close")

        btn_layout.addWidget(self.btn_open)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_clear_all)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.btn_open.clicked.connect(self.open_bookmark)
        self.btn_delete.clicked.connect(self.delete_bookmark)
        self.btn_clear_all.clicked.connect(self.clear_all_bookmarks)
        self.btn_close.clicked.connect(self.accept)
        self.list_widget.itemDoubleClicked.connect(self.open_bookmark)

        self.load_bookmarks_into_ui()

    def load_bookmarks_into_ui(self):
        self.list_widget.clear()
        bookmarks = self.browser_window.load_bookmarks()
        for bm in bookmarks:
            item = QListWidgetItem(f"{bm['title']} — {bm['url']}")
            item.setData(Qt.ItemDataRole.UserRole, bm["url"])
            self.list_widget.addItem(item)

    def open_bookmark(self):
        item = self.list_widget.currentItem()
        if item:
            url = item.data(Qt.ItemDataRole.UserRole)
            current_view = self.browser_window.get_current_view()
            if current_view:
                current_view.setUrl(QUrl(url))
            self.accept()

    def delete_bookmark(self):
        item = self.list_widget.currentItem()
        if item:
            url = item.data(Qt.ItemDataRole.UserRole)
            self.browser_window.delete_bookmark_by_url(url)
            self.load_bookmarks_into_ui()

    def clear_all_bookmarks(self):
        self.browser_window.save_bookmarks([])
        self.load_bookmarks_into_ui()
        self.browser_window.update_bookmarks_bar()


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

        # File Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(28, 28)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_icon(theme)
        layout.addWidget(self.icon_label)

        # Content Column
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(3)

        self.name_label = QLabel(entry.get("fileName", "Unknown"))
        self.name_label.setStyleSheet(
            f"font-weight: 600; font-size: 9pt; color: {theme['text_primary']};"
        )
        content_layout.addWidget(self.name_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("downloadProgressBar")
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        content_layout.addWidget(self.progress_bar)

        # Status row
        self.status_label = QLabel()
        self.status_label.setStyleSheet(
            f"font-size: 8pt; color: {theme['text_secondary']};"
        )
        content_layout.addWidget(self.status_label)

        # Action Buttons row
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

        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 4, 4)

        title = QLabel("Downloads")
        title_font = title.font()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        header_layout.addStretch()

        btn_all = QPushButton("Show all downloads")
        btn_all.setProperty("class", "downloadActionBtn")
        btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_all.clicked.connect(self._open_all_downloads)
        header_layout.addWidget(btn_all)

        btn_close = QPushButton()
        btn_close.setFixedSize(20, 20)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setToolTip("Close")
        theme = DARK_THEME if self.browser_window.is_dark_mode else LIGHT_THEME
        btn_close.setIcon(
            render_svg_icon(SVG_ICONS["tab_close"], theme["close_icon_color"], 10)
        )
        btn_close.setIconSize(QSize(10, 10))
        btn_close.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; border-radius: 10px; }}
            QPushButton:hover {{ background: {theme['hover_bg']}; }}
        """)
        btn_close.clicked.connect(self.hide)
        header_layout.addWidget(btn_close)

        card_layout.addLayout(header_layout)

        # Scroll Area for Downloads List
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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
        # Clear existing items
        self.card_widgets.clear()
        while self.items_layout.count() > 1:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Combine active downloads with saved history
        active_entries = [
            (d, entry) for d, entry in self.browser_window.active_downloads.items()
        ]
        history_entries = self.browser_window.load_downloads()

        active_paths = {entry["filePath"] for _, entry in active_entries}
        filtered_history = [
            (None, h) for h in history_entries if h.get("filePath") not in active_paths
        ]

        all_items = active_entries + filtered_history
        recent_items = all_items[:12]

        if not recent_items:
            empty_label = QLabel("No downloads")
            theme = DARK_THEME if self.browser_window.is_dark_mode else LIGHT_THEME
            empty_label.setStyleSheet(
                f"color: {theme['text_secondary']}; padding: 24px 0px; font-size: 9.5pt;"
            )
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.items_layout.insertWidget(0, empty_label)
            return

        for d_obj, entry in recent_items:
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

        # Header Search Bar
        header_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search downloads...")
        self.search_input.setFixedHeight(32)
        self.search_input.textChanged.connect(self.filter_downloads)
        header_layout.addWidget(self.search_input, 1)

        self.btn_clear_all = QPushButton("Clear all")
        self.btn_clear_all.clicked.connect(self.clear_all_downloads)
        header_layout.addWidget(self.btn_clear_all)

        layout.addLayout(header_layout)

        # Scroll Area for all items
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
            msg = "No matching downloads found" if query else "No downloads found"
            theme = DARK_THEME if self.browser_window.is_dark_mode else LIGHT_THEME
            lbl = QLabel(msg)
            lbl.setStyleSheet(
                f"color: {theme['text_secondary']}; padding: 30px; font-size: 10pt;"
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.items_layout.insertWidget(0, lbl)

    def filter_downloads(self):
        self.load_all_downloads()

    def clear_all_downloads(self):
        self.browser_window.save_downloads([])
        self.load_all_downloads()
        if self.browser_window.downloads_bubble:
            self.browser_window.downloads_bubble.refresh()


# =============================================================================
# Main Window: EcoBrowser
# =============================================================================


class EcoBrowserWindow(QMainWindow):
    def __init__(self, initial_url=None):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1120, 740)
        self.initial_url = initial_url
        self.is_loading = False

        self.active_downloads = {}
        self.downloads_bubble = None

        # Set application and window icon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            self.setWindowIcon(app_icon)
            QApplication.setWindowIcon(app_icon)

        self.is_dark_mode = self.load_theme_setting()

        self._setup_web_profile()
        self._setup_ui()
        self.apply_theme()

        # Keyboard shortcuts
        self.shortcut_downloads = QShortcut(QKeySequence("Ctrl+J"), self)
        self.shortcut_downloads.activated.connect(self.toggle_downloads_bubble)

        self.add_new_tab(self.initial_url or HOME_URL)

    def _setup_web_profile(self):
        app_data_path = get_app_data_folder()

        self.profile = QWebEngineProfile("EcoBrowserProfile", self)
        self.profile.setPersistentStoragePath(os.path.join(app_data_path, "storage"))
        self.profile.setCachePath(os.path.join(app_data_path, "cache"))

        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )

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

        # 1. Chrome Tab Strip (Tabs at top with adjacent '+' button)
        self.tab_strip_widget = self._build_tab_strip()
        main_layout.addWidget(self.tab_strip_widget)

        # 2. Chrome Navigation Toolbar
        self.toolbar_panel = self._build_toolbar()
        main_layout.addWidget(self.toolbar_panel)

        # 3. Chrome Bookmarks Bar (dynamically hidden if no bookmarks exist)
        self.bookmarks_bar_widget = self._build_bookmarks_bar()
        main_layout.addWidget(self.bookmarks_bar_widget)
        self.update_bookmarks_bar()

        # 4. Web View Container
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
        self.tab_bar.setTabsClosable(
            False
        )  # We use custom reliable QPushButton tab close buttons!
        self.tab_bar.setMovable(True)
        self.tab_bar.setDocumentMode(True)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.setElideMode(Qt.TextElideMode.ElideRight)
        self.tab_bar.setIconSize(QSize(16, 16))
        self.tab_bar.currentChanged.connect(self.switch_tab)

        tab_strip_layout.addWidget(self.tab_bar)

        # '+' New Tab Button directly adjacent to tabs
        self.new_tab_button = QPushButton()
        self.new_tab_button.setObjectName("newTabButton")
        self.new_tab_button.setFixedSize(28, 28)
        self.new_tab_button.setIconSize(QSize(14, 14))
        self.new_tab_button.setToolTip("New tab (Ctrl+T)")
        self.new_tab_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_tab_button.clicked.connect(lambda: self.add_new_tab(HOME_URL))
        tab_strip_layout.addWidget(self.new_tab_button)

        tab_strip_layout.addStretch()
        return tab_strip

    def _build_toolbar(self):
        toolbar_panel = QWidget()
        toolbar_panel.setObjectName("toolbarPanel")
        toolbar_panel.setFixedHeight(44)

        toolbar_layout = QHBoxLayout(toolbar_panel)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)
        toolbar_layout.setSpacing(6)

        # Left: Navigation buttons
        self.back_button = self._make_toolbar_button("Click to go back")
        self.forward_button = self._make_toolbar_button("Click to go forward")
        self.refresh_button = self._make_toolbar_button("Reload this page")

        self.back_button.clicked.connect(self.go_back)
        self.forward_button.clicked.connect(self.go_forward)
        self.refresh_button.clicked.connect(self.on_reload_clicked)

        toolbar_layout.addWidget(self.back_button)
        toolbar_layout.addWidget(self.forward_button)
        toolbar_layout.addWidget(self.refresh_button)

        # Center: Chrome Omnibox
        self.address_panel = QWidget()
        self.address_panel.setObjectName("addressPanel")
        self.address_panel.setFixedHeight(34)

        address_layout = QHBoxLayout(self.address_panel)
        address_layout.setContentsMargins(10, 0, 8, 0)
        address_layout.setSpacing(6)

        self.security_icon_btn = QPushButton()
        self.security_icon_btn.setObjectName("securityBtn")
        self.security_icon_btn.setFixedSize(20, 20)
        self.security_icon_btn.setIconSize(QSize(14, 14))
        self.security_icon_btn.setToolTip("View site information")

        self.url_input = QLineEdit()
        self.url_input.setObjectName("omniboxInput")
        self.url_input.setPlaceholderText("Search Google or type a URL")
        self.url_input.setFrame(False)
        self.url_input.returnPressed.connect(self.navigate_to_url)

        self.bookmark_button = QPushButton()
        self.bookmark_button.setObjectName("bookmarkStarBtn")
        self.bookmark_button.setFixedSize(28, 28)
        self.bookmark_button.setIconSize(QSize(16, 16))
        self.bookmark_button.setToolTip("Bookmark this tab")
        self.bookmark_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bookmark_button.clicked.connect(self.toggle_bookmark_current_page)

        address_layout.addWidget(self.security_icon_btn)
        address_layout.addWidget(self.url_input, 1)
        address_layout.addWidget(self.bookmark_button)

        toolbar_layout.addWidget(self.address_panel, 1)

        # Right: Downloads & 3-dots Menu (Extensions/Ad Blocker/Safety now live in the 3-dot menu)
        self.downloads_button = self._make_toolbar_button("Downloads (Ctrl+J)")
        self.downloads_button.clicked.connect(self.toggle_downloads_bubble)

        self.menu_button = self._make_toolbar_button("Customize and control EcoBrowser")
        self.menu_button.clicked.connect(self.show_main_menu)

        toolbar_layout.addWidget(self.downloads_button)
        toolbar_layout.addWidget(self.menu_button)

        self._build_main_menu()
        return toolbar_panel

    def _build_main_menu(self):
        self.menu = QMenu(self)

        self.menu.addAction("New tab\tCtrl+T", lambda: self.add_new_tab(HOME_URL))
        self.menu.addSeparator()

        self.menu.addAction("Downloads\tCtrl+J", self.open_downloads_dialog)
        self.menu.addAction("Bookmarks", self.open_bookmarks_dialog)
        self.menu.addAction("History\tCtrl+H", self.open_history_dialog)
        self.menu.addAction("Clear browsing data...", self.clear_cookies)
        self.menu.addSeparator()

        self.menu.addAction(
            "Extensions, Ad Blocker & Safety", self.open_block_manager_dialog
        )

        self.dark_mode_action = self.menu.addAction("Dark mode")
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)

        self.menu.addSeparator()
        self.menu.addAction("Exit", self.close)

    def show_main_menu(self):
        self.dark_mode_action.setChecked(self.is_dark_mode)
        pos = self.menu_button.mapToGlobal(self.menu_button.rect().bottomRight())
        self.menu.exec(pos)

    def _build_bookmarks_bar(self):
        bar_container = QWidget()
        bar_container.setObjectName("bookmarksBarPanel")
        bar_container.setFixedHeight(28)

        self.bookmarks_layout = QHBoxLayout(bar_container)
        self.bookmarks_layout.setContentsMargins(8, 2, 8, 2)
        self.bookmarks_layout.setSpacing(4)
        self.bookmarks_layout.addStretch()

        self.update_bookmarks_bar()
        return bar_container

    def _make_toolbar_button(self, tooltip=""):
        button = QPushButton()
        button.setProperty("class", "toolbarBtn")
        button.setFixedSize(30, 30)
        button.setIconSize(QSize(18, 18))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            button.setToolTip(tooltip)
        return button

    # =========================================================================
    # Theme & Icon Styling
    # =========================================================================

    def apply_theme(self):
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME

        self.setStyleSheet(self._build_stylesheet(theme))
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

        self.back_button.setIcon(render_svg_icon(SVG_ICONS["back"], icon_color, 18))
        self.forward_button.setIcon(
            render_svg_icon(SVG_ICONS["forward"], icon_color, 18)
        )

        reload_icon_name = "stop" if self.is_loading else "reload"
        self.refresh_button.setIcon(
            render_svg_icon(SVG_ICONS[reload_icon_name], icon_color, 18)
        )

        self.new_tab_button.setIcon(
            render_svg_icon(SVG_ICONS["new_tab"], icon_color, 14)
        )

        has_active_dl = any(
            d.state() == QWebEngineDownloadRequest.DownloadState.DownloadInProgress
            for d in getattr(self, "active_downloads", {}).keys()
        )
        dl_icon_color = theme["accent_blue"] if has_active_dl else theme["icon_color"]
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
        sec_color = theme["text_secondary"] if is_https else "#ea4335"
        self.security_icon_btn.setIcon(
            render_svg_icon(SVG_ICONS[sec_icon], sec_color, 14)
        )

        is_bm = False
        if current_view:
            url = current_view.url().toString()
            is_bm = any(b["url"] == url for b in self.load_bookmarks())
        self.sync_bookmark_star(is_bm)

    def sync_bookmark_star(self, is_bookmarked):
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        if is_bookmarked:
            self.bookmark_button.setIcon(
                render_svg_icon(SVG_ICONS["star_filled"], theme["star_active"], 16)
            )
        else:
            self.bookmark_button.setIcon(
                render_svg_icon(SVG_ICONS["star_outline"], theme["icon_color"], 16)
            )

    def toggle_dark_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        self.save_theme_setting(self.is_dark_mode)
        self.apply_theme()

    def clear_cookies(self):
        if hasattr(self, "profile") and self.profile:
            self.profile.cookieStore().deleteAllCookies()
            QMessageBox.information(
                self,
                "Cookies Cleared",
                "All browser cookies and site data cleared successfully.",
            )

    def settings_file_path(self):
        return os.path.join(get_app_data_folder(), "settings.json")

    def load_theme_setting(self):
        path = self.settings_file_path()
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("dark_mode", False)
        except Exception:
            return False

    def save_theme_setting(self, is_dark):
        path = self.settings_file_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"dark_mode": is_dark}, f, indent=4)
        except Exception:
            pass

    def _setup_tab_close_button(self, index):
        btn = QPushButton()
        btn.setFixedSize(20, 20)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("Close tab")
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        btn.setIcon(
            render_svg_icon(SVG_ICONS["tab_close"], theme["close_icon_color"], 10)
        )
        btn.setIconSize(QSize(10, 10))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 10px;
                margin-right: 4px;
            }}
            QPushButton:hover {{
                background: {theme['close_btn_hover']};
            }}
            QPushButton:pressed {{
                background: {theme['pressed_bg']};
            }}
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
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        border: none;
                        border-radius: 10px;
                        margin-right: 4px;
                    }}
                    QPushButton:hover {{
                        background: {theme['close_btn_hover']};
                    }}
                    QPushButton:pressed {{
                        background: {theme['pressed_bg']};
                    }}
                """)

    @staticmethod
    def _build_stylesheet(theme):
        return f"""
            QMainWindow {{
                background-color: {theme['window_bg']};
                font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            }}

            /* Top Chrome Tab Strip */
            QWidget#tabStripPanel {{
                background-color: {theme['tabstrip_bg']};
                border: none;
            }}

            QTabBar {{
                background-color: transparent;
                border: none;
                qproperty-drawBase: 0;
            }}

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
                font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            }}

            QTabBar::tab:!selected {{
                border-right: 1px solid {theme['tab_divider']};
            }}

            QTabBar::tab:hover:!selected {{
                background-color: {theme['tab_inactive_hover']};
                color: {theme['text_primary']};
                border-right: 1px solid transparent;
            }}

            QTabBar::tab:selected {{
                background-color: {theme['tab_active_bg']};
                color: {theme['text_primary']};
                font-weight: 600;
                border-top: 2px solid {theme['accent_blue']};
                border-right: none;
            }}

            /* '+' New Tab Button */
            QPushButton#newTabButton {{
                background-color: transparent;
                border: none;
                border-radius: 14px;
                margin-bottom: 2px;
            }}

            QPushButton#newTabButton:hover {{
                background-color: {theme['hover_bg']};
            }}

            QPushButton#newTabButton:pressed {{
                background-color: {theme['pressed_bg']};
            }}

            /* Main Toolbar */
            QWidget#toolbarPanel {{
                background-color: {theme['toolbar_bg']};
                border-bottom: 1px solid {theme['divider']};
            }}

            /* Circular Toolbar Action Buttons */
            QPushButton[class="toolbarBtn"] {{
                background-color: transparent;
                border: none;
                border-radius: 15px;
            }}

            QPushButton[class="toolbarBtn"]:hover {{
                background-color: {theme['hover_bg']};
            }}

            QPushButton[class="toolbarBtn"]:pressed {{
                background-color: {theme['pressed_bg']};
            }}

            QPushButton[class="toolbarBtn"]:disabled {{
                opacity: 0.35;
            }}

            /* Chrome Pill-Shaped Omnibox */
            QWidget#addressPanel {{
                background-color: {theme['omnibox_bg']};
                border-radius: 17px;
                border: 2px solid transparent;
            }}

            QWidget#addressPanel:hover {{
                background-color: {theme['omnibox_hover_bg']};
            }}

            QLineEdit#omniboxInput {{
                background-color: transparent;
                color: {theme['text_primary']};
                border: none;
                font-size: 9.5pt;
                selection-background-color: #1a73e8;
                selection-color: #ffffff;
                padding: 2px 4px;
            }}

            QPushButton#securityBtn {{
                background-color: transparent;
                border: none;
                border-radius: 10px;
            }}

            QPushButton#bookmarkStarBtn {{
                background-color: transparent;
                border: none;
                border-radius: 14px;
            }}

            QPushButton#bookmarkStarBtn:hover {{
                background-color: {theme['hover_bg']};
            }}

            /* Bookmarks Bar */
            QWidget#bookmarksBarPanel {{
                background-color: {theme['toolbar_bg']};
                border-bottom: 1px solid {theme['divider']};
            }}

            QWidget#bookmarksBarPanel QPushButton {{
                color: {theme['text_primary']};
                background-color: transparent;
                font-size: 8.5pt;
                padding: 3px 8px;
                border: none;
                border-radius: 6px;
            }}

            QWidget#bookmarksBarPanel QPushButton:hover {{
                background-color: {theme['hover_bg']};
            }}

            /* Downloads Bubble & Dialog */
            QFrame#downloadsBubbleCard {{
                background-color: {theme['menu_bg']};
                border: 1px solid {theme['divider']};
                border-radius: 12px;
            }}

            QFrame#downloadItemCard {{
                background-color: transparent;
                border-radius: 8px;
                padding: 4px 6px;
            }}

            QFrame#downloadItemCard:hover {{
                background-color: {theme['hover_bg']};
            }}

            QProgressBar#downloadProgressBar {{
                background-color: {theme['progress_bg']};
                border: none;
                border-radius: 2px;
                height: 4px;
                text-align: right;
            }}

            QProgressBar#downloadProgressBar::chunk {{
                background-color: {theme['progress_fill']};
                border-radius: 2px;
            }}

            QPushButton.downloadActionBtn {{
                background-color: transparent;
                color: {theme['accent_blue']};
                border: none;
                font-size: 8.5pt;
                font-weight: 500;
                padding: 3px 6px;
                border-radius: 4px;
            }}

            QPushButton.downloadActionBtn:hover {{
                background-color: {theme['hover_bg']};
            }}

            /* Chrome Style Dropdown Menu */
            QMenu {{
                background-color: {theme['menu_bg']};
                color: {theme['text_primary']};
                border: 1px solid {theme['divider']};
                padding: 6px 0px;
                border-radius: 8px;
            }}

            QMenu::item {{
                padding: 6px 24px 6px 20px;
                font-size: 9.5pt;
            }}

            QMenu::item:selected {{
                background-color: {theme['hover_bg']};
            }}

            QMenu::separator {{
                height: 1px;
                background-color: {theme['divider']};
                margin: 4px 0px;
            }}

            /* Dialogs */
            QDialog {{
                background-color: {theme['toolbar_bg']};
                color: {theme['text_primary']};
            }}

            QLabel {{
                color: {theme['text_primary']};
            }}

            QCheckBox {{
                color: {theme['text_primary']};
                font-size: 9.5pt;
                spacing: 8px;
            }}

            QListWidget {{
                background-color: {theme['omnibox_bg']};
                color: {theme['text_primary']};
                border: 1px solid {theme['divider']};
                border-radius: 6px;
                padding: 4px;
            }}

            QListWidget::item {{
                padding: 6px 8px;
                border-radius: 4px;
            }}

            QListWidget::item:selected {{
                background-color: {theme['hover_bg']};
                color: {theme['text_primary']};
            }}

            QTextEdit {{
                background-color: {theme['omnibox_bg']};
                color: {theme['text_primary']};
                border: 1px solid {theme['divider']};
                border-radius: 6px;
            }}

            QDialog QPushButton {{
                background-color: {theme['omnibox_bg']};
                color: {theme['text_primary']};
                border: 1px solid {theme['divider']};
                border-radius: 4px;
                padding: 5px 14px;
                font-size: 9pt;
            }}

            QDialog QPushButton:hover {{
                background-color: {theme['hover_bg']};
            }}
        """

    # =========================================================================
    # Tab & Navigation Handling
    # =========================================================================

    def get_current_view(self):
        return self.stack.currentWidget()

    def add_new_tab(self, url):
        web_view = QWebEngineView()
        page = QWebEnginePage(self.profile, web_view)
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
            lambda request, view=web_view: self.handle_navigation(request, view)
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

    def close_tab(self, index):
        if self.tab_bar.count() <= 1:
            return

        web_view = self.stack.widget(index)
        self.tab_bar.removeTab(index)
        self.stack.removeWidget(web_view)
        web_view.deleteLater()
        gc.collect()

        # Re-attach close buttons to match shifted indices
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
        if len(display_title) > 24:
            display_title = display_title[:22] + "..."

        for i in range(self.stack.count()):
            if self.stack.widget(i) == web_view:
                self.tab_bar.setTabText(i, display_title)
                break

    def sync_tab_icon(self, web_view, icon):
        for i in range(self.stack.count()):
            if self.stack.widget(i) == web_view:
                if not icon.isNull():
                    self.tab_bar.setTabIcon(i, icon)
                break

    def handle_load_started(self, web_view):
        if web_view == self.get_current_view():
            self.is_loading = True
            theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
            self.refresh_button.setIcon(
                render_svg_icon(SVG_ICONS["stop"], theme["icon_color"], 18)
            )
            self.refresh_button.setToolTip("Stop loading this page")

    def handle_load_finished(self, web_view, ok):
        if web_view == self.get_current_view():
            self.is_loading = False
            theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
            self.refresh_button.setIcon(
                render_svg_icon(SVG_ICONS["reload"], theme["icon_color"], 18)
            )
            self.refresh_button.setToolTip("Reload this page")
            self.back_button.setEnabled(web_view.history().canGoBack())
            self.forward_button.setEnabled(web_view.history().canGoForward())

    def on_reload_clicked(self):
        current_view = self.get_current_view()
        if not current_view:
            return
        if self.is_loading:
            current_view.stop()
        else:
            current_view.reload()

    def go_back(self):
        current_view = self.get_current_view()
        if current_view:
            current_view.back()

    def go_forward(self):
        current_view = self.get_current_view()
        if current_view:
            current_view.forward()

    def navigate_to_url(self):
        typed_text = self.url_input.text().strip()
        current_view = self.get_current_view()
        if not current_view or not typed_text:
            return

        destination = self._resolve_address_bar_text(typed_text)
        current_view.setUrl(QUrl(destination))

    @staticmethod
    def _resolve_address_bar_text(typed_text):
        already_a_url = typed_text.startswith("http://") or typed_text.startswith(
            "https://"
        )
        if already_a_url:
            return typed_text

        looks_like_a_domain = "." in typed_text and " " not in typed_text
        if looks_like_a_domain:
            return "https://" + typed_text

        return "https://www.google.com/search?q=" + typed_text

    def sync_address_bar(self, web_view):
        if not web_view or web_view != self.get_current_view():
            return

        current_url = web_view.url().toString()
        if current_url == "about:blank":
            self.url_input.setText("")
        else:
            self.url_input.setText(current_url)

        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        is_https = current_url.startswith("https://")
        sec_icon = "lock" if is_https else "unlock"
        sec_color = theme["text_secondary"] if is_https else "#ea4335"
        self.security_icon_btn.setIcon(
            render_svg_icon(SVG_ICONS[sec_icon], sec_color, 14)
        )

        bookmarks = self.load_bookmarks()
        is_bookmarked = any(bm["url"] == current_url for bm in bookmarks)
        self.sync_bookmark_star(is_bookmarked)

        self.back_button.setEnabled(web_view.history().canGoBack())
        self.forward_button.setEnabled(web_view.history().canGoForward())

        self.log_to_history(current_url)

    def handle_navigation(self, request, web_view):
        destination_url = request.url()
        destination_url_lowercase = destination_url.toString().lower()
        host = destination_url.host().lower()

        is_blocked_ad = self.interceptor.ad_block_enabled and url_matches_ad_domain(
            host
        )
        is_blocked_adult_content = (
            self.interceptor.nude_block_enabled
            and url_matches_adult_content(host, destination_url_lowercase)
        )

        if is_blocked_ad or is_blocked_adult_content:
            request.reject()
            self._show_blocked_page(web_view, destination_url, host)
        else:
            request.accept()

    @staticmethod
    def _show_blocked_page(web_view, destination_url, host):
        blocked_host_display_name = host or "this website"
        warning_html = build_blocked_page_html(blocked_host_display_name)
        QTimer.singleShot(0, lambda: web_view.setHtml(warning_html, destination_url))

    # =========================================================================
    # Bookmarks & History Management
    # =========================================================================

    def history_file_path(self):
        return os.path.join(get_app_data_folder(), "history.txt")

    def log_to_history(self, url):
        if not url or url.startswith("data:") or url == "about:blank":
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"{timestamp} - {url}\n"
        try:
            with open(self.history_file_path(), "a", encoding="utf-8") as history_file:
                history_file.write(log_line)
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
        current_view = self.get_current_view()
        if not current_view:
            return
        url = current_view.url().toString()
        title = current_view.title() or url
        if not url or url == "about:blank" or url.startswith("data:"):
            return

        bookmarks = self.load_bookmarks()
        existing = next((bm for bm in bookmarks if bm["url"] == url), None)
        if existing:
            bookmarks = [bm for bm in bookmarks if bm["url"] != url]
            self.save_bookmarks(bookmarks)
            self.update_bookmarks_bar()
            self.sync_bookmark_star(False)
        else:
            bookmarks.append({"title": title, "url": url})
            self.save_bookmarks(bookmarks)
            self.update_bookmarks_bar()
            self.sync_bookmark_star(True)

    def delete_bookmark_by_url(self, url):
        bookmarks = self.load_bookmarks()
        bookmarks = [bm for bm in bookmarks if bm["url"] != url]
        self.save_bookmarks(bookmarks)
        self.update_bookmarks_bar()
        current_view = self.get_current_view()
        if current_view and current_view.url().toString() == url:
            self.sync_bookmark_star(False)

    def open_bookmarks_dialog(self):
        dialog = BookmarksDialog(self)
        dialog.exec()

    def update_bookmarks_bar(self):
        while self.bookmarks_layout.count() > 1:
            item = self.bookmarks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        theme = DARK_THEME if getattr(self, "is_dark_mode", False) else LIGHT_THEME
        bm_icon = render_svg_icon(SVG_ICONS["globe"], theme["text_secondary"], 14)

        bookmarks = self.load_bookmarks()

        # Hide bookmarks bar completely when there are no bookmarks
        if not bookmarks:
            if hasattr(self, "bookmarks_bar_widget"):
                self.bookmarks_bar_widget.hide()
            return

        if hasattr(self, "bookmarks_bar_widget"):
            self.bookmarks_bar_widget.show()

        for bm in bookmarks:
            display_title = bm["title"]
            if len(display_title) > 22:
                display_title = display_title[:20] + "..."

            btn = BookmarkButton(display_title, bm["url"], bm_icon, self)
            btn.setToolTip(bm["url"])
            self.bookmarks_layout.insertWidget(self.bookmarks_layout.count() - 1, btn)

    def navigate_to_bookmark(self, url):
        current_view = self.get_current_view()
        if current_view:
            current_view.setUrl(QUrl(url))

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
        # Determine default save directory (user's Downloads folder)
        default_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        suggested = download.suggestedFileName() or "download"
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

        # Update downloads icon to indicate active download
        self.update_all_icons()

        # Auto-open the downloads bubble when a new download starts
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
            entry["receivedBytes"] = download.totalBytes()
            # Save to persistent history
            history = self.load_downloads()
            history.insert(0, entry)
            history = history[:200]  # Keep at most 200 entries
            self.save_downloads(history)
            del self.active_downloads[download]
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
            entry["state"] = "cancelled"
            del self.active_downloads[download]
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            entry["state"] = "interrupted"
            del self.active_downloads[download]

        # Refresh bubble and icon
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

        # Position the bubble under the downloads button
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
        # Clean shutdown to prevent WebEngine warnings on exit
        for i in range(self.stack.count()):
            widget = self.stack.widget(i)
            if isinstance(widget, QWebEngineView):
                widget.setPage(None)
                widget.deleteLater()
        event.accept()


# =============================================================================
# Helper Functions & Entry Point
# =============================================================================


def get_app_data_folder():
    app_data_root = os.getenv("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(app_data_root, "EcoBrowser")
    os.makedirs(folder, exist_ok=True)
    return folder


def get_initial_url_from_args(argv):
    has_url_argument = len(argv) > 1 and argv[1].startswith("http")
    return argv[1] if has_url_argument else None


if __name__ == "__main__":
    # Automatically register as browser in Windows registry on startup
    register_as_browser()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    window = EcoBrowserWindow(get_initial_url_from_args(sys.argv))
    window.show()
    sys.exit(app.exec())
