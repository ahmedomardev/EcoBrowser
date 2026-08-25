import os
import json
import subprocess
import platform
import wx
import wx.html2

# ---------------------------------------------------------
# 1. State & Data Management (No Classes)
# ---------------------------------------------------------
state = {
    "tabs": [],
    "active_index": -1,
    "history_file": os.path.abspath(os.path.join(os.path.dirname(__file__), "history.json")),
    "downloads_file": os.path.abspath(os.path.join(os.path.dirname(__file__), "downloads.json"))
}

def get_json_data(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(title, url):
    if not url or url == "about:blank":
        return
    history = get_json_data(state["history_file"])
    if history and history[-1].get("url") == url:
        return
    history.append({"title": title or url, "url": url})
    try:
        with open(state["history_file"], "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass

def open_file_externally(filepath):
    """Opens a JSON or log file directly using the OS default application."""
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
            
    if platform.system() == "Windows":
        os.startfile(filepath)
    elif platform.system() == "Darwin":
        subprocess.run(["open", filepath])
    else:
        subprocess.run(["xdg-open", filepath])

# ---------------------------------------------------------
# 2. Modern Flat Rectangular Custom Widgets (No Curves)
# ---------------------------------------------------------
def create_flat_button(parent, label_text, size=(36, 32), on_click=None):
    panel = wx.Panel(parent, size=size)
    panel.SetBackgroundStyle(wx.BG_STYLE_PAINT)

    btn_state = {"hover": False}

    def on_paint(event):
        dc = wx.AutoBufferedPaintDC(panel)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return
        w, h = panel.GetClientSize()

        bg_col = wx.Colour(60, 62, 68) if btn_state["hover"] else wx.Colour(43, 43, 43)
        gc.SetBrush(wx.Brush(bg_col))
        gc.SetPen(wx.NullPen)
        gc.DrawRectangle(0, 0, w, h)

        gc.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Segoe UI"), wx.Colour(230, 230, 230))
        tw, th = gc.GetTextExtent(label_text)
        gc.DrawText(label_text, (w - tw) / 2, (h - th) / 2)

    def on_enter(e):
        btn_state["hover"] = True
        panel.Refresh()

    def on_leave(e):
        btn_state["hover"] = False
        panel.Refresh()

    def on_down(e):
        if on_click:
            on_click(panel)

    panel.Bind(wx.EVT_PAINT, on_paint)
    panel.Bind(wx.EVT_ENTER_WINDOW, on_enter)
    panel.Bind(wx.EVT_LEAVE_WINDOW, on_leave)
    panel.Bind(wx.EVT_LEFT_DOWN, on_down)

    return panel

# ---------------------------------------------------------
# 3. Main Application Setup
# ---------------------------------------------------------
app = wx.App()

CLR_BG_DARK = wx.Colour(27, 26, 25)
CLR_TOOLBAR = wx.Colour(43, 43, 43)
CLR_URL_BAR = wx.Colour(30, 30, 30)

frame = wx.Frame(None, title="EcoBrowser", size=(1280, 800))
frame.SetBackgroundColour(CLR_BG_DARK)

main_sizer = wx.BoxSizer(wx.VERTICAL)

# --- TOP TAB STRIP ---
tab_bar_panel = wx.Panel(frame)
tab_bar_panel.SetBackgroundColour(CLR_BG_DARK)
tab_sizer = wx.BoxSizer(wx.HORIZONTAL)
tab_bar_panel.SetSizer(tab_sizer)

# --- NAVIGATION TOOLBAR ---
nav_panel = wx.Panel(frame)
nav_panel.SetBackgroundColour(CLR_TOOLBAR)
nav_sizer = wx.BoxSizer(wx.HORIZONTAL)

btn_back = create_flat_button(nav_panel, "◀", (36, 32), lambda p: on_back_click())
btn_fwd = create_flat_button(nav_panel, "▶", (36, 32), lambda p: on_fwd_click())
btn_reload = create_flat_button(nav_panel, "↻", (36, 32), lambda p: on_reload_click())

# Sharp Flat Address Bar Container
url_container = wx.Panel(nav_panel)
url_container.SetBackgroundStyle(wx.BG_STYLE_PAINT)

def on_paint_url_bg(event):
    dc = wx.AutoBufferedPaintDC(url_container)
    gc = wx.GraphicsContext.Create(dc)
    if not gc:
        return
    w, h = url_container.GetClientSize()
    gc.SetBrush(wx.Brush(CLR_URL_BAR))
    gc.SetPen(wx.NullPen)
    gc.DrawRectangle(0, 0, w, h)

url_container.Bind(wx.EVT_PAINT, on_paint_url_bg)

url_container_sizer = wx.BoxSizer(wx.HORIZONTAL)
lock_icon = wx.StaticText(url_container, label="🔒")
lock_icon.SetForegroundColour(wx.Colour(160, 160, 160))
lock_icon.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Segoe UI Emoji"))

url_bar = wx.TextCtrl(url_container, style=wx.TE_PROCESS_ENTER | wx.BORDER_NONE)
url_bar.SetBackgroundColour(CLR_URL_BAR)
url_bar.SetForegroundColour(wx.Colour(240, 240, 240))
url_bar.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Segoe UI"))

url_container_sizer.Add(lock_icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
url_container_sizer.Add(url_bar, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
url_container.SetSizer(url_container_sizer)

# Dropdown Menu Logic for Options Button
def show_dropdown_menu(panel_ref):
    menu = wx.Menu()
    
    item_history = menu.Append(wx.ID_ANY, "View History")
    item_downloads = menu.Append(wx.ID_ANY, "View Downloads")
    
    def on_menu_selection(event):
        id_clicked = event.GetId()
        if id_clicked == item_history.GetId():
            open_file_externally(state["history_file"])
        elif id_clicked == item_downloads.GetId():
            open_file_externally(state["downloads_file"])

    frame.Bind(wx.EVT_MENU, on_menu_selection, id=item_history.GetId(), id2=item_downloads.GetId())
    
    panel_ref.PopupMenu(menu, (0, panel_ref.GetClientSize().GetHeight()))
    menu.Destroy()

btn_menu = create_flat_button(nav_panel, "Options ▾", (85, 32), show_dropdown_menu)

nav_sizer.Add(btn_back, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 6)
nav_sizer.Add(btn_fwd, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 2)
nav_sizer.Add(btn_reload, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 2)
nav_sizer.Add(url_container, 1, wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT, 6)
nav_sizer.Add(btn_menu, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
nav_panel.SetSizer(nav_sizer)

# --- WEB CONTENT HOLDER ---
web_container = wx.Panel(frame)
web_sizer = wx.BoxSizer(wx.VERTICAL)
web_container.SetSizer(web_sizer)

# Main Assembly
main_sizer.Add(tab_bar_panel, 0, wx.EXPAND)
main_sizer.Add(nav_panel, 0, wx.EXPAND)
main_sizer.Add(web_container, 1, wx.EXPAND)
frame.SetSizer(main_sizer)

# ---------------------------------------------------------
# 4. Core Application Logic
# ---------------------------------------------------------
def render_tab_strip():
    tab_sizer.Clear(True)

    for i, tab in enumerate(state["tabs"]):
        is_active = (i == state["active_index"])

        t_panel = wx.Panel(tab_bar_panel, size=(180, 32))
        t_panel.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        def make_tab_paint(p_ref, is_act):
            def on_paint_tab(event):
                dc = wx.AutoBufferedPaintDC(p_ref)
                gc = wx.GraphicsContext.Create(dc)
                if not gc:
                    return
                w, h = p_ref.GetClientSize()
                bg = CLR_TOOLBAR if is_act else CLR_BG_DARK
                gc.SetBrush(wx.Brush(bg))
                gc.SetPen(wx.NullPen)
                gc.DrawRectangle(0, 0, w, h)
            return on_paint_tab

        t_panel.Bind(wx.EVT_PAINT, make_tab_paint(t_panel, is_active))
        t_sizer = wx.BoxSizer(wx.HORIZONTAL)

        title_txt = tab["title"][:15] if tab["title"] else "EcoBrowser Tab"
        lbl_title = wx.StaticText(t_panel, label=title_txt)
        lbl_title.SetForegroundColour(wx.Colour(240, 240, 240) if is_active else wx.Colour(160, 160, 160))
        lbl_title.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Segoe UI"))

        lbl_close = wx.StaticText(t_panel, label="✕")
        lbl_close.SetForegroundColour(wx.Colour(160, 160, 160))
        lbl_close.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Segoe UI"))

        t_sizer.Add(lbl_title, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        t_sizer.Add(lbl_close, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        t_panel.SetSizer(t_sizer)

        def make_select_handler(idx):
            return lambda e: switch_to_tab(idx)

        def make_close_handler(idx):
            def handler(e):
                e.StopPropagation()
                close_tab(idx)
            return handler

        for w in (t_panel, lbl_title):
            w.Bind(wx.EVT_LEFT_DOWN, make_select_handler(i))

        lbl_close.Bind(wx.EVT_LEFT_DOWN, make_close_handler(i))
        tab_sizer.Add(t_panel, 0, wx.TOP | wx.LEFT, 4)

    btn_add_tab = create_flat_button(tab_bar_panel, "+", (30, 30), lambda p: create_new_tab())
    tab_sizer.Add(btn_add_tab, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)
    tab_bar_panel.Layout()

def switch_to_tab(index):
    if index < 0 or index >= len(state["tabs"]):
        return
    state["active_index"] = index

    for i, item in enumerate(state["tabs"]):
        if i == index:
            item["wv"].Show()
            url_bar.SetValue(item["wv"].GetCurrentURL())
        else:
            item["wv"].Hide()

    web_sizer.Clear()
    web_sizer.Add(state["tabs"][index]["wv"], 1, wx.EXPAND)
    web_container.Layout()
    render_tab_strip()

def close_tab(index):
    if len(state["tabs"]) <= 1:
        return
    item = state["tabs"].pop(index)
    item["wv"].Destroy()
    new_index = max(0, index - 1)
    switch_to_tab(new_index)

def create_new_tab(url="https://www.google.com"):
    try:
        wv = wx.html2.WebView.New(web_container, backend=wx.html2.WebViewBackendEdge)
    except Exception:
        wv = wx.html2.WebView.New(web_container)

    tab_data = {"wv": wv, "title": "EcoBrowser", "url": url}
    state["tabs"].append(tab_data)
    idx = len(state["tabs"]) - 1

    def on_url_navigated(event):
        u = event.GetURL()
        if state["active_index"] == idx:
            url_bar.SetValue(u)
        tab_data["url"] = u
        save_history(wv.GetCurrentTitle() or u, u)

    def on_title_changed(event):
        tab_data["title"] = event.GetString()
        render_tab_strip()

    wv.Bind(wx.html2.EVT_WEBVIEW_NAVIGATED, on_url_navigated)
    wv.Bind(wx.html2.EVT_WEBVIEW_TITLE_CHANGED, on_title_changed)

    wv.LoadURL(url)
    switch_to_tab(idx)

def on_navigate(event):
    target = url_bar.GetValue().strip()
    if not target.startswith("http://") and not target.startswith("https://"):
        if "." in target and " " not in target:
            target = "https://" + target
        else:
            target = f"https://www.google.com/search?q={target.replace(' ', '+')}"

    if 0 <= state["active_index"] < len(state["tabs"]):
        state["tabs"][state["active_index"]]["wv"].LoadURL(target)

def on_back_click():
    if 0 <= state["active_index"] < len(state["tabs"]):
        wv = state["tabs"][state["active_index"]]["wv"]
        if wv.CanGoBack():
            wv.GoBack()

def on_fwd_click():
    if 0 <= state["active_index"] < len(state["tabs"]):
        wv = state["tabs"][state["active_index"]]["wv"]
        if wv.CanGoForward():
            wv.GoForward()

def on_reload_click():
    if 0 <= state["active_index"] < len(state["tabs"]):
        state["tabs"][state["active_index"]]["wv"].Reload()

# Event Bindings
url_bar.Bind(wx.EVT_TEXT_ENTER, on_navigate)

# Start EcoBrowser
create_new_tab("https://www.google.com")
frame.Center()
frame.Show()
app.MainLoop()