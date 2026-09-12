import os
import sys
import gc
import json
import winreg as reg
from datetime import datetime

from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineUrlRequestInterceptor,
    QWebEngineSettings,
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
)

# =============================================================================
# Constants & filter lists
# =============================================================================

APP_NAME = "EcoBrowser"
HOME_URL = "https://www.google.com"

# Compact toolbar button sizing to match Edge's sleek height.
TOOLBAR_BUTTON_SIZE = 26

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

DARK_THEME = {
    "background": "#121212",
    "text": "#f0f0f0",
    "panel": "#181818",
    "input_background": "#2b2b2b",
    "tab_background": "#181818",
    "tab_selected_background": "#121212",
    "hover_background": "#323238",
    "border": "#2f2f35",
    "tab_border": "#ffffff",
    "close_icon_color": "#ffffff",
}

LIGHT_THEME = {
    "background": "#f3f3f3",
    "text": "#1f1f1f",
    "panel": "#ffffff",
    "input_background": "#f0f2f5",
    "tab_background": "#e5e5e5",
    "tab_selected_background": "#ffffff",
    "hover_background": "#dedede",
    "border": "#dcdcdc",
    "tab_border": "#000000",
    "close_icon_color": "#000000",
}


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
    body {{ background: #121212; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }} 
    .warning-card {{ background: #1e1e1e; padding: 30px 40px; border-radius: 12px; border: 1px solid #333; text-align: center; max-width: 400px; box-shadow: 0 8px 24px rgba(0,0,0,0.4); }} 
    .warning-title {{ color: #ff5252; font-size: 20px; margin-top: 0; margin-bottom: 10px; }} 
    .warning-text {{ color: #aaaaaa; font-size: 13px; margin-bottom: 20px; line-height: 1.4; }} 
    .warning-btn {{ background: #333333; color: #ffffff; text-decoration: none; padding: 10px 20px; border-radius: 6px; font-size: 13px; font-weight: 600; display: inline-block; }} 
    .warning-btn:hover {{ background: #444444; }}
    </style></head><body><div class='warning-card'>
    <h1 class='warning-title'>18+ Content Blocked</h1>
    <p class='warning-text'>Access to <b>{blocked_domain}</b> has been blocked by EcoBrowser safety filters.</p>
    <a class='warning-btn' href='https://www.google.com'>Go Back Home</a>
    </div></body></html>"""


# =============================================================================
# Content filtering helpers
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
    def __init__(self, title, url, browser_window):
        super().__init__(title)
        self.bookmark_url = url
        self.browser_window = browser_window
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


# =============================================================================
# Dialogs: History, Block Manager, Bookmarks
# =============================================================================


class HistoryDialog(QDialog):
    def __init__(self, history_file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Browsing History")
        self.resize(600, 400)
        self.history_file_path = history_file_path

        layout = QVBoxLayout(self)
        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        self.text_view.setText(self._load_history_text(self.history_file_path))
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
        self.setWindowTitle("Ad Block and Nude Block Manager")
        self.resize(400, 220)
        self.interceptor = interceptor

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(QLabel("Configure your protection filters below:"))

        self.ad_block_checkbox = QCheckBox("Enable Ad Blocking")
        self.ad_block_checkbox.setChecked(self.interceptor.ad_block_enabled)
        self.ad_block_checkbox.toggled.connect(self._on_ad_block_toggled)
        layout.addWidget(self.ad_block_checkbox)

        self.nude_block_checkbox = QCheckBox("Enable Nude / Adult Content Blocking")
        self.nude_block_checkbox.setChecked(self.interceptor.nude_block_enabled)
        self.nude_block_checkbox.toggled.connect(self._on_nude_block_toggled)
        layout.addWidget(self.nude_block_checkbox)

        layout.addStretch()

    def _on_ad_block_toggled(self, is_checked):
        self.interceptor.ad_block_enabled = is_checked

    def _on_nude_block_toggled(self, is_checked):
        self.interceptor.nude_block_enabled = is_checked


class BookmarksDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Bookmarks")
        self.resize(500, 350)
        self.browser_window = parent

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.btn_open = QPushButton("Open")
        self.btn_delete = QPushButton("Delete")
        self.btn_clear_all = QPushButton("Clear All Bookmarks")
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


# =============================================================================
# Main window
# =============================================================================


class EcoBrowserWindow(QMainWindow):
    def __init__(self, initial_url=None):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1008, 681)
        self.initial_url = initial_url

        self.is_dark_mode = self.load_theme_setting()

        self._setup_web_profile()
        self._setup_ui()
        self.apply_theme()

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
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tab_bar = self._build_tab_bar()
        main_layout.addWidget(self.tab_bar)

        self.toolbar_panel = self._build_toolbar(main_layout)
        main_layout.addWidget(self.toolbar_panel)

        self.bookmarks_bar_widget = self._build_bookmarks_bar()
        main_layout.addWidget(self.bookmarks_bar_widget)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

    def _build_tab_bar(self):
        tab_bar = QTabBar()
        tab_bar.setTabsClosable(True)
        tab_bar.setMovable(True)
        tab_bar.setDocumentMode(True)
        tab_bar.setExpanding(False)
        tab_bar.tabCloseRequested.connect(self.close_tab)
        tab_bar.currentChanged.connect(self.switch_tab)
        return tab_bar

    def _build_toolbar(self, main_layout):
        toolbar_panel = QWidget()
        toolbar_panel.setObjectName("toolbarPanel")

        toolbar_layout = QHBoxLayout(toolbar_panel)
        toolbar_layout.setContentsMargins(6, 4, 6, 4)
        toolbar_layout.setSpacing(4)

        self._add_navigation_buttons(toolbar_layout)
        self._add_address_bar(toolbar_layout)
        self._add_tab_and_menu_buttons(toolbar_layout)

        return toolbar_panel

    def _build_bookmarks_bar(self):
        bar_container = QWidget()
        bar_container.setObjectName("bookmarksBarPanel")

        self.bookmarks_layout = QHBoxLayout(bar_container)
        self.bookmarks_layout.setContentsMargins(8, 2, 8, 2)
        self.bookmarks_layout.setSpacing(4)
        self.bookmarks_layout.addStretch()

        self.update_bookmarks_bar()
        return bar_container

    def _add_navigation_buttons(self, toolbar_layout):
        self.back_button = self._make_toolbar_button("◀")
        self.forward_button = self._make_toolbar_button("▶")
        self.refresh_button = self._make_toolbar_button("⟳")

        toolbar_layout.addWidget(self.back_button)
        toolbar_layout.addWidget(self.forward_button)
        toolbar_layout.addWidget(self.refresh_button)

        self.back_button.clicked.connect(self.go_back)
        self.forward_button.clicked.connect(self.go_forward)
        self.refresh_button.clicked.connect(self.reload_current_page)

    def _add_address_bar(self, toolbar_layout):
        self.address_panel = QWidget()
        self.address_panel.setObjectName("addressPanel")

        address_layout = QHBoxLayout(self.address_panel)
        address_layout.setContentsMargins(8, 0, 8, 0)
        address_layout.setSpacing(4)

        self.security_icon_label = QLabel("🔒︎")
        self.security_icon_label.setFixedWidth(18)
        address_layout.addWidget(self.security_icon_label)

        self.url_input = QLineEdit()
        self.url_input.setFrame(False)
        self.url_input.returnPressed.connect(self.navigate_to_url)
        address_layout.addWidget(self.url_input)

        toolbar_layout.addWidget(self.address_panel, 1)

    def _add_tab_and_menu_buttons(self, toolbar_layout):
        self.new_tab_button = self._make_toolbar_button("+")
        self.bookmark_button = self._make_toolbar_button("★")
        self.menu_button = self._make_toolbar_button("")

        toolbar_layout.addWidget(self.new_tab_button)
        toolbar_layout.addWidget(self.bookmark_button)
        toolbar_layout.addWidget(self.menu_button)

        self.new_tab_button.clicked.connect(lambda: self.add_new_tab(HOME_URL))
        self.bookmark_button.clicked.connect(self.add_current_page_to_bookmarks)

        self.menu = QMenu(self)

        self.block_manager_action = self.menu.addAction("Block Manager")
        self.block_manager_action.triggered.connect(self.open_block_manager_dialog)

        self.dark_mode_action = self.menu.addAction("Dark Mode")
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)

        self.action_manage_bookmarks = self.menu.addAction("Manage Bookmarks")
        self.action_manage_bookmarks.triggered.connect(self.open_bookmarks_dialog)

        # Added Clear Cookies Action
        self.clear_cookies_action = self.menu.addAction("Clear Cookies")
        self.clear_cookies_action.triggered.connect(self.clear_cookies)

        self.menu.addSeparator()

        self.history_action = self.menu.addAction("History")
        self.history_action.triggered.connect(self.open_history_dialog)

        self.menu.aboutToShow.connect(self.populate_main_menu)
        self.menu_button.setMenu(self.menu)

    @staticmethod
    def _make_toolbar_button(label):
        button = QPushButton(label)
        button.setFixedSize(TOOLBAR_BUTTON_SIZE, TOOLBAR_BUTTON_SIZE)
        return button

    def apply_theme(self):
        theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME

        close_icon_path = self._write_tab_close_icon(theme["close_icon_color"])
        self.setStyleSheet(self._build_stylesheet(theme, close_icon_path))

        for i in range(self.stack.count()):
            web_view = self.stack.widget(i)
            if isinstance(web_view, QWebEngineView):
                web_view.page().settings().setAttribute(
                    QWebEngineSettings.WebAttribute.ForceDarkMode, self.is_dark_mode
                )

    def toggle_dark_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        self.save_theme_setting(self.is_dark_mode)
        self.apply_theme()

    def clear_cookies(self):
        if hasattr(self, "profile") and self.profile:
            self.profile.cookieStore().deleteAllCookies()
            QMessageBox.information(
                self, "Cookies Cleared", "All browser cookies have been cleared successfully."
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

    @staticmethod
    def _write_tab_close_icon(close_icon_color):
        icon_folder = get_app_data_folder()
        icon_path = os.path.join(icon_folder, "close_icon.svg").replace("\\", "/")

        svg_markup = (
            "<svg xmlns='http://www.w3.org/2000/svg' width='8' height='8' "
            "viewBox='0 0 10 10'>"
            f"<path d='M1,1 L9,9 M9,1 L1,9' stroke='{close_icon_color}' "
            "stroke-width='1.5' stroke-linecap='round'/></svg>"
        )
        try:
            with open(icon_path, "w", encoding="utf-8") as icon_file:
                icon_file.write(svg_markup)
        except OSError:
            pass

        return icon_path

    @staticmethod
    def _build_stylesheet(theme, close_icon_path):
        return f"""
            QMainWindow {{ background-color: {theme['background']}; color: {theme['text']}; }}
            QWidget#toolbarPanel {{ background-color: {theme['panel']}; border-bottom: 1px solid {theme['border']}; padding: 0px; }}
            QWidget#bookmarksBarPanel {{ background-color: {theme['panel']}; border-bottom: 1px solid {theme['border']}; }}
            QPushButton {{ background-color: transparent; color: {theme['text']}; border: none; border-radius: 4px; font-weight: bold; font-size: 9.5pt; }}
            QPushButton:hover {{ background-color: {theme['hover_background']}; }}
            
            QWidget#bookmarksBarPanel QPushButton {{
                font-size: 8.5pt;
                font-weight: normal;
                padding: 2px 8px;
                border-radius: 3px;
            }}
            QWidget#bookmarksBarPanel QPushButton:hover {{
                background-color: {theme['hover_background']};
            }}

            QWidget#addressPanel {{ background-color: {theme['input_background']}; border-radius: 12px; border: 1px solid {theme['border']}; }}
            QLineEdit {{ background-color: transparent; color: {theme['text']}; border: none; font-size: 9.5pt; selection-background-color: #0078d4; selection-color: white; }}

            QTabBar {{ background-color: {theme['panel']}; padding: 2px 2px 0px 2px; }}
            QTabBar::tab {{
                background-color: {theme['tab_background']};
                color: {theme['text']};
                padding: 4px 12px;
                margin: 1px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                min-width: 120px;
                max-width: 200px;
                font-size: 9pt;
                height: 24px;
            }}
            QTabBar::tab:selected {{
                background-color: {theme['tab_selected_background']};
                font-weight: bold;
                border: 1px solid {theme['border']};
                border-bottom: none;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {theme['hover_background']};
            }}
            QTabBar::close-button {{
                image: url("{close_icon_path}");
                subcontrol-position: right;
                margin-right: 4px;
                padding: 2px;
            }}
            QTabBar::close-button:hover {{
                background-color: {theme['hover_background']};
                border-radius: 3px;
            }}
            QMenu {{ background-color: {theme['panel']}; color: {theme['text']}; border: 1px solid {theme['border']}; padding: 4px; }}
            QMenu::item {{ padding: 5px 16px; border-radius: 3px; font-size: 9.5pt; }}
            QMenu::item:selected {{ background-color: {theme['hover_background']}; }}
            QCheckBox {{ color: {theme['text']}; font-size: 10pt; spacing: 8px; }}
        """

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
        page.navigationRequested.connect(
            lambda request, view=web_view: self.handle_navigation(request, view)
        )

        stack_index = self.stack.addWidget(web_view)
        tab_index = self.tab_bar.addTab(APP_NAME)
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

    def switch_tab(self, index):
        if index == -1:
            return

        self.stack.setCurrentIndex(index)
        self.sync_address_bar(self.get_current_view())

    def update_tab_title(self, title, web_view):
        display_title = title or APP_NAME
        if len(display_title) > 20:
            display_title = display_title[:18] + "..."

        for i in range(self.stack.count()):
            if self.stack.widget(i) == web_view:
                self.tab_bar.setTabText(i, display_title)
                break

    def go_back(self):
        current_view = self.get_current_view()
        if current_view:
            current_view.back()

    def go_forward(self):
        current_view = self.get_current_view()
        if current_view:
            current_view.forward()

    def reload_current_page(self):
        current_view = self.get_current_view()
        if current_view:
            current_view.reload()

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
        self.url_input.setText(current_url)
        self.security_icon_label.setText(
            "🔒︎" if current_url.startswith("https://") else "ꗃ"
        )
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

    def add_current_page_to_bookmarks(self):
        current_view = self.get_current_view()
        if not current_view:
            return
        url = current_view.url().toString()
        title = current_view.title() or url
        if not url or url == "about:blank" or url.startswith("data:"):
            return

        bookmarks = self.load_bookmarks()
        if not any(bm["url"] == url for bm in bookmarks):
            bookmarks.append({"title": title, "url": url})
            self.save_bookmarks(bookmarks)
            self.update_bookmarks_bar()

    def delete_bookmark_by_url(self, url):
        bookmarks = self.load_bookmarks()
        bookmarks = [bm for bm in bookmarks if bm["url"] != url]
        self.save_bookmarks(bookmarks)
        self.update_bookmarks_bar()

    def open_bookmarks_dialog(self):
        dialog = BookmarksDialog(self)
        dialog.exec()

    def update_bookmarks_bar(self):
        while self.bookmarks_layout.count() > 1:
            item = self.bookmarks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        bookmarks = self.load_bookmarks()
        for bm in bookmarks:
            display_title = bm["title"]
            if len(display_title) > 22:
                display_title = display_title[:20] + "..."

            btn = BookmarkButton(display_title, bm["url"], self)
            btn.setToolTip(bm["url"])

            self.bookmarks_layout.insertWidget(self.bookmarks_layout.count() - 1, btn)

    def populate_main_menu(self):
        self.dark_mode_action.setChecked(self.is_dark_mode)

    def navigate_to_bookmark(self, url):
        current_view = self.get_current_view()
        if current_view:
            current_view.setUrl(QUrl(url))

    def handle_download_request(self, download):
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", download.suggestedFileName()
        )
        if save_path:
            download.setDownloadFileName(save_path)
            download.accept()


def get_app_data_folder():
    app_data_root = os.getenv("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(app_data_root, "EcoBrowser")
    os.makedirs(folder, exist_ok=True)
    return folder


def get_initial_url_from_args(argv):
    has_url_argument = len(argv) > 1 and argv[1].startswith("http")
    return argv[1] if has_url_argument else None


if __name__ == "__main__":
    # Automatically register as a browser in Windows registry on startup
    register_as_browser()

    app = QApplication(sys.argv)
    window = EcoBrowserWindow(get_initial_url_from_args(sys.argv))
    window.show()
    sys.exit(app.exec())