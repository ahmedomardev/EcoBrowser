using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;
using Microsoft.Win32;
using System.Diagnostics;
using System.Drawing.Drawing2D;

namespace EcoBrowser
{
    public partial class Form1 : Form
    {
        private const string AppName = "EcoBrowser";
        private const string HomeUrl = "https://www.google.com";
        private const string SymbolFont = "Segoe UI Symbol";
        private const int ButtonSize = 32, ButtonRadius = 6, AddressRadius = 16;
        private string? _initialUrl = null;
        private bool _isDarkMode = false;

        // Modern neutral dark/light color scheme (No bright blue)
        private Color LightBg = Color.FromArgb(248, 249, 250);
        private Color LightText = Color.FromArgb(32, 33, 36);
        private Color DarkBg = Color.FromArgb(18, 18, 18);
        private Color DarkText = Color.FromArgb(240, 240, 240);
        private Color NeutralActiveColor = Color.FromArgb(50, 50, 50); // Replaced Accent Blue with dark charcoal

        private static readonly string[] AdBlockDomains = new[]
        {
            "doubleclick.net", "googleads", "googlesyndication", "googletagmanager.com",
            "googletagservices.com", "adservice.google", "google-analytics.com", "amazon-adsystem.com",
            "adnxs.com", "adsrvr.org", "adform.net", "criteo.com", "criteo.net", "taboola.com",
            "outbrain.com", "facebook.com/tr", "connect.facebook.net", "hotjar.com", "scorecardresearch.com",
            "quantserve.com", "moatads.com", "pubmatic.com", "rubiconproject.com", "openx.net",
            "casalemedia.com", "bidswitch.net", "adroll.com", "media.net", "yieldmo.com",
            "smartadserver.com", "advertising.com", "serving-sys.com", "adtechus.com", "mathtag.com",
            "bluekai.com", "krxd.net", "demdex.net", "rlcdn.com", "exelator.com", "rfihub.com",
            "3lift.com", "gumgum.com", "sharethrough.com", "spotxchange.com", "teads.tv",
            "adsafeprotected.com", "chartbeat.com", "newrelic.com", "segment.io", "segment.com",
            "mixpanel.com", "amplitude.com"
        };

        public Form1()
        {
            InitializeComponent();
            this.Text = AppName;

            SetAppIcon();
            RegisterAsBrowser();

            string[] args = Environment.GetCommandLineArgs();
            if (args.Length > 1)
            {
                string possibleUrl = args[1];
                if (Uri.IsWellFormedUriString(possibleUrl, UriKind.Absolute))
                {
                    _initialUrl = possibleUrl;
                }
            }

            this.Load += Form1_Load;
        }

        private void RegisterAsBrowser()
        {
            try
            {
                string exePath = Process.GetCurrentProcess().MainModule?.FileName ?? "";
                if (string.IsNullOrEmpty(exePath)) return;
                string progId = "EcoBrowser.HTML";

                using (var key = Registry.CurrentUser.CreateSubKey($@"Software\Classes\{progId}"))
                {
                    key.SetValue("", "EcoBrowser HTML Document");
                    using (var iconKey = key.CreateSubKey("DefaultIcon"))
                        iconKey.SetValue("", $"\"{exePath}\",0");
                    using (var commandKey = key.CreateSubKey(@"shell\open\command"))
                        commandKey.SetValue("", $"\"{exePath}\" \"%1\"");
                }

                using (var appKey = Registry.CurrentUser.CreateSubKey($@"Software\{AppName}\Capabilities"))
                {
                    appKey.SetValue("ApplicationDescription", "EcoBrowser Fast Lightweight Browser");
                    appKey.SetValue("ApplicationName", AppName);
                    using (var urlKey = appKey.CreateSubKey("URLAssociations"))
                    {
                        urlKey.SetValue("http", progId);
                        urlKey.SetValue("https", progId);
                    }
                    using (var mimeKey = appKey.CreateSubKey("FileAssociations"))
                    {
                        mimeKey.SetValue(".htm", progId);
                        mimeKey.SetValue(".html", progId);
                    }
                }

                using (var regApps = Registry.CurrentUser.CreateSubKey(@"Software\RegisteredApplications"))
                {
                    regApps.SetValue(AppName, $@"Software\{AppName}\Capabilities");
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine("Registry registration failed: " + ex.Message);
            }
        }

        private void SetAppIcon()
        {
            try
            {
                string iconPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "icon.png");
                if (File.Exists(iconPath))
                {
                    using var bitmap = new Bitmap(iconPath);
                    this.Icon = Icon.FromHandle(bitmap.GetHicon());
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Could not load icon: {ex.Message}");
            }
        }

        private async void Form1_Load(object? sender, EventArgs e)
        {
            this.BackColor = LightBg;
            this.ForeColor = LightText;

            // Tab configuration hooks
            tabControl1.DrawMode = TabDrawMode.OwnerDrawFixed;
            tabControl1.SizeMode = TabSizeMode.Fixed;
            tabControl1.ItemSize = new Size(180, 34);
            tabControl1.Padding = new Point(12, 4);

            tabControl1.DrawItem += TabControl1_DrawItem;
            tabControl1.MouseDown += TabControl1_MouseDown;
            tabControl1.SelectedIndexChanged += (s, ev) => SyncAddressBar(GetCurrentWebView());

            tabPage1.Text = AppName;

            RoundControl(addressBarPanel, AddressRadius);

            // Setup buttons initialized safely via designer setup
            SetupButton(btnBack, BtnBack_Click);
            SetupButton(btnForward, BtnForward_Click);
            SetupButton(btnRefresh, BtnRefresh_Click);
            SetupButton(btnHome, BtnHome_Click);
            SetupButton(btnAddTab, BtnAddTab_Click);
            SetupButton(btnHistory, BtnHistory_Click);
            SetupButton(btnDownloads, BtnDownloads_Click);
            SetupButton(btnDarkMode, BtnDarkMode_Click);

            txtUrl.KeyDown += TxtUrl_KeyDown;

            string targetUrl = !string.IsNullOrEmpty(_initialUrl) ? _initialUrl : HomeUrl;
            await InitializeWebViewAsync(webView1, targetUrl);
        }

        private void SetupButton(Button btn, EventHandler onClick)
        {
            RoundControl(btn, ButtonRadius);
            btn.Click += onClick;
            AddHoverEffect(btn);
        }

        private void BtnDarkMode_Click(object? sender, EventArgs e)
        {
            _isDarkMode = !_isDarkMode;
            ApplyTheme(_isDarkMode);
            UpdateDarkModeButtonOnAllTabs();
        }

        private void AddDarkModeButtonToPanel(FlowLayoutPanel panel)
        {
            var btnDarkMode = new Button
            {
                Name = "btnDarkMode",
                Text = _isDarkMode ? "☀️" : "🌙",
                Font = new Font(SymbolFont, 11F, FontStyle.Bold),
                Size = new Size(ButtonSize, ButtonSize),
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.White,
                ForeColor = Color.FromArgb(60, 64, 67),
                Margin = new Padding(2, 0, 2, 0),
                Cursor = Cursors.Hand
            };
            btnDarkMode.FlatAppearance.BorderSize = 0;
            RoundControl(btnDarkMode, ButtonRadius);
            btnDarkMode.Click += BtnDarkMode_Click;
            AddHoverEffect(btnDarkMode);
            panel.Controls.Add(btnDarkMode);
        }

        private void UpdateDarkModeButtonOnAllTabs()
        {
            string buttonText = _isDarkMode ? "☀️" : "🌙";
            foreach (TabPage tab in tabControl1.TabPages)
            {
                var rightPanel = tab.Controls.Find("rightPanel", true).FirstOrDefault() as FlowLayoutPanel;
                if (rightPanel != null)
                {
                    var darkModeBtn = rightPanel.Controls.Find("btnDarkMode", true).FirstOrDefault() as Button;
                    if (darkModeBtn != null) darkModeBtn.Text = buttonText;
                }
            }
        }

        private void ApplyTheme(bool isDark)
        {
            Color bgColor = isDark ? DarkBg : LightBg;
            Color textColor = isDark ? DarkText : LightText;
            Color panelColor = isDark ? Color.FromArgb(28, 28, 28) : Color.White;
            Color inputBgColor = isDark ? Color.FromArgb(40, 40, 40) : Color.FromArgb(241, 243, 244);

            this.BackColor = bgColor;
            this.ForeColor = textColor;
            UpdateControlTheme(this, bgColor, textColor, panelColor, inputBgColor);
            tabControl1.Invalidate();

            if (isDark) InjectDarkModeCSS();
            else InjectLightModeCSS();
        }

        private void UpdateControlTheme(Control parent, Color bgColor, Color textColor, Color panelColor, Color inputBgColor)
        {
            foreach (Control ctrl in parent.Controls)
            {
                if (ctrl is Panel) ctrl.BackColor = panelColor;
                else if (ctrl is TextBox) { ctrl.BackColor = inputBgColor; ctrl.ForeColor = textColor; }
                else if (ctrl is Button btn) { btn.BackColor = panelColor; btn.ForeColor = textColor; }
                else if (ctrl is Label lbl) { lbl.ForeColor = textColor; }
                else if (ctrl is TabControl) { ctrl.BackColor = bgColor; ctrl.ForeColor = textColor; }

                if (ctrl.HasChildren) UpdateControlTheme(ctrl, bgColor, textColor, panelColor, inputBgColor);
            }
        }

        private void InjectDarkModeCSS()
        {
            string darkCSS = @"
                document.body.style.backgroundColor = '#121212';
                document.body.style.color = '#e0e0e0';
            ";
            GetCurrentWebView()?.ExecuteScriptAsync(darkCSS);
        }

        private void InjectLightModeCSS()
        {
            GetCurrentWebView()?.ExecuteScriptAsync("location.reload();");
        }

        private void AddHoverEffect(Button btn) => btn.MouseEnter += (s, e) => btn.BackColor = Color.FromArgb(230, 233, 237);

        private void RoundControl(Control c, int radius)
        {
            void Apply()
            {
                if (c.Width <= 0 || c.Height <= 0) return;
                using var path = RoundedRect(new Rectangle(0, 0, c.Width, c.Height), radius);
                c.Region = new Region(path);
            }
            c.Resize += (s, e) => Apply();
            Apply();
        }

        private GraphicsPath RoundedRect(Rectangle rect, int radius)
        {
            var path = new GraphicsPath();
            int r = radius * 2;
            path.AddArc(rect.X, rect.Y, r, r, 180, 90);
            path.AddArc(rect.Right - r, rect.Y, r, r, 270, 90);
            path.AddArc(rect.Right - r, rect.Bottom - r, r, r, 0, 90);
            path.AddArc(rect.X, rect.Bottom - r, r, r, 90, 90);
            path.CloseFigure();
            return path;
        }

        private async Task InitializeWebViewAsync(WebView2? wv, string url = "https://www.google.com")
        {
            if (wv == null) return;
            try
            {
                var options = new CoreWebView2EnvironmentOptions();
                var env = await CoreWebView2Environment.CreateAsync(null, null, options);
                await wv.EnsureCoreWebView2Async(env);

                wv.CoreWebView2.NavigationStarting += (s, e) =>
                {
                    var uri = new Uri(e.Uri);
                    if (AdBlockDomains.Any(domain => uri.Host.Contains(domain)))
                    {
                        e.Cancel = true;
                    }
                };

                wv.CoreWebView2.NavigationCompleted += (s, e) =>
                {
                    SyncAddressBar(wv);
                    LogToHistory(wv.Source?.ToString());
                    UpdateTabTitle(wv);
                };

                wv.CoreWebView2.Navigate(url);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to initialize WebView: {ex.Message}", AppName, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void SyncAddressBar(WebView2? wv)
        {
            var txt = GetCurrentAddressBar();
            var lbl = GetCurrentSecureLabel();
            if (txt == null || wv?.CoreWebView2 == null) return;

            txt.Text = wv.Source?.ToString() ?? "";
            if (lbl != null) lbl.Text = wv.Source?.Scheme == "https" ? "🔒" : "🔓";
        }

        private void UpdateTabTitle(WebView2? wv)
        {
            if (wv == null) return;
            try
            {
                wv.ExecuteScriptAsync("document.title").ContinueWith(task =>
                {
                    if (task.IsCompleted && !task.IsFaulted)
                    {
                        string title = task.Result?.Trim('"') ?? "";
                        foreach (TabPage tab in tabControl1.TabPages)
                        {
                            if (tab.Controls.OfType<WebView2>().FirstOrDefault() == wv)
                            {
                                if (title.Length > 25) title = title.Substring(0, 22) + "...";
                                this.Invoke(() => tab.Text = title);
                                break;
                            }
                        }
                    }
                });
            }
            catch { }
        }

        private Label? GetCurrentSecureLabel() => tabControl1.SelectedTab?.Controls.Find("lblSecure", true).FirstOrDefault() as Label;
        private WebView2? GetCurrentWebView() => tabControl1.SelectedTab?.Controls.OfType<WebView2>().FirstOrDefault();
        private TextBox? GetCurrentAddressBar() => tabControl1.SelectedTab?.Controls.Find("txtUrl", true).FirstOrDefault() as TextBox;

        // Custom modern non-blue tab rendering
        private void TabControl1_DrawItem(object? sender, DrawItemEventArgs e)
        {
            if (e.Index < 0 || e.Index >= tabControl1.TabPages.Count) return;

            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            Rectangle tabRect = tabControl1.GetTabRect(e.Index);
            bool isSelected = tabControl1.SelectedIndex == e.Index;

            Color stripBgColor = _isDarkMode ? Color.FromArgb(24, 24, 24) : Color.FromArgb(238, 239, 241);
            using (var stripBg = new SolidBrush(stripBgColor))
                g.FillRectangle(stripBg, tabRect);

            Rectangle tabBoxRect = new Rectangle(tabRect.X + 2, tabRect.Y + 4, tabRect.Width - 4, tabRect.Height - 4);

            Color fillColor = _isDarkMode ?
                (isSelected ? Color.FromArgb(45, 45, 45) : Color.FromArgb(28, 28, 28)) :
                (isSelected ? Color.White : Color.FromArgb(220, 222, 225));

            Color textColor = _isDarkMode ?
                (isSelected ? Color.White : Color.FromArgb(160, 160, 160)) :
                (isSelected ? Color.FromArgb(20, 20, 20) : Color.FromArgb(90, 90, 90));

            using (var path = RoundedRect(tabBoxRect, 6))
            {
                using (var brush = new SolidBrush(fillColor))
                    g.FillPath(brush, path);

                if (isSelected)
                {
                    using (var pen = new Pen(_isDarkMode ? Color.FromArgb(90, 90, 90) : Color.FromArgb(190, 195, 200), 1.2f))
                        g.DrawPath(pen, path);
                }
            }

            Rectangle textRect = new Rectangle(tabBoxRect.X + 8, tabBoxRect.Y, tabBoxRect.Width - 26, tabBoxRect.Height);
            using (Font tabFont = new Font("Segoe UI", 9F, isSelected ? FontStyle.Bold : FontStyle.Regular))
                TextRenderer.DrawText(g, tabControl1.TabPages[e.Index].Text, tabFont, textRect, textColor, TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.EndEllipsis);

            Rectangle closeRect = new Rectangle(tabBoxRect.Right - 18, tabBoxRect.Y + (tabBoxRect.Height - 14) / 2, 14, 14);
            using (Font closeFont = new Font("Segoe UI", 8F, FontStyle.Bold))
                TextRenderer.DrawText(g, "×", closeFont, closeRect, textColor, TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter);
        }

        private void TabControl1_MouseDown(object? sender, MouseEventArgs e)
        {
            int tabIndexToClose = -1;
            for (int i = 0; i < tabControl1.TabPages.Count; i++)
            {
                Rectangle tabRect = tabControl1.GetTabRect(i);
                Rectangle closeRect = new Rectangle(tabRect.Right - 22, tabRect.Y + 8, 14, 14);
                if (closeRect.Contains(e.Location))
                {
                    tabIndexToClose = i;
                    break;
                }
            }

            if (tabIndexToClose >= 0)
            {
                if (tabControl1.TabCount <= 1) return;
                TabPage tabToClose = tabControl1.TabPages[tabIndexToClose];
                tabToClose.Controls.OfType<WebView2>().FirstOrDefault()?.Dispose();
                tabControl1.TabPages.Remove(tabToClose);
                tabToClose.Dispose();
            }
        }

        private async void BtnAddTab_Click(object? sender, EventArgs e)
        {
            var newTab = CreateTabPage();
            tabControl1.TabPages.Add(newTab);
            tabControl1.SelectedTab = newTab;
            await Task.Yield();
            await InitializeWebViewAsync(newTab.Controls.OfType<WebView2>().First());
        }

        private TabPage CreateTabPage()
        {
            var tabPage = new TabPage(AppName) { BackColor = Color.White, Padding = new Padding(0) };
            var toolPanel = new Panel { Dock = DockStyle.Top, Height = 50, BackColor = Color.White, Padding = new Padding(6, 7, 6, 7) };
            var font = new Font(SymbolFont, 11F, FontStyle.Bold);

            var leftCtrls = CreateButtonPanel(DockStyle.Left, new (string, EventHandler)[] { ("<", BtnBack_Click), (">", BtnForward_Click), ("↻", BtnRefresh_Click), ("⌂", BtnHome_Click) }, font);
            var rightCtrls = CreateButtonPanel(DockStyle.Right, new (string, EventHandler)[] { ("+", BtnAddTab_Click), ("🕐", BtnHistory_Click), ("⬇", BtnDownloads_Click) }, font);

            AddDarkModeButtonToPanel(rightCtrls);
            var addressPanel = CreateAddressPanel();

            toolPanel.Controls.Add(addressPanel);
            toolPanel.Controls.Add(rightCtrls);
            toolPanel.Controls.Add(leftCtrls);

            var webView = new WebView2 { Name = "webView1", Dock = DockStyle.Fill, DefaultBackgroundColor = Color.White };
            tabPage.Controls.Add(webView);
            tabPage.Controls.Add(toolPanel);

            RoundControl(addressPanel, AddressRadius);
            return tabPage;
        }

        private FlowLayoutPanel CreateButtonPanel(DockStyle dock, (string text, EventHandler onClick)[] buttons, Font font)
        {
            var panel = new FlowLayoutPanel { Dock = dock, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink, WrapContents = false };
            foreach (var (text, onClick) in buttons)
            {
                var btn = new Button { Text = text, Font = font, Size = new Size(ButtonSize, ButtonSize), FlatStyle = FlatStyle.Flat, BackColor = Color.White, ForeColor = Color.FromArgb(60, 64, 67), Margin = new Padding(2, 0, 2, 0) };
                btn.FlatAppearance.BorderSize = 0;
                SetupButton(btn, onClick);
                panel.Controls.Add(btn);
            }
            return panel;
        }

        private Panel CreateAddressPanel()
        {
            var panel = new Panel { Name = "addressBarPanel", BackColor = Color.FromArgb(241, 243, 244), Dock = DockStyle.Fill, Padding = new Padding(8, 6, 8, 6) };
            var txtUrl = new TextBox { Name = "txtUrl", BorderStyle = BorderStyle.None, BackColor = Color.FromArgb(241, 243, 244), Font = new Font("Segoe UI", 10F), Dock = DockStyle.Fill };
            var lblSecure = new Label { Name = "lblSecure", Font = new Font(SymbolFont, 9F), ForeColor = Color.FromArgb(95, 99, 104), Dock = DockStyle.Left, Width = 24, TextAlign = ContentAlignment.MiddleCenter };

            txtUrl.KeyDown += TxtUrl_KeyDown;
            panel.Controls.Add(txtUrl);
            panel.Controls.Add(lblSecure);
            return panel;
        }

        private void TxtUrl_KeyDown(object? sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter) { NavigateToUrl(); e.SuppressKeyPress = true; }
        }

        private void NavigateToUrl()
        {
            var wv = GetCurrentWebView();
            var txt = GetCurrentAddressBar();
            if (wv?.CoreWebView2 == null || string.IsNullOrWhiteSpace(txt?.Text)) return;

            string input = txt.Text.Trim();
            bool looksLikeUrl = input.Contains('.') && !input.Contains(' ');
            string url = input.StartsWith("http://") || input.StartsWith("https://") ? input :
                         looksLikeUrl ? "https://" + input : "https://www.google.com/search?q=" + Uri.EscapeDataString(input);
            wv.CoreWebView2.Navigate(url);
        }

        private void BtnBack_Click(object? sender, EventArgs e) => GetCurrentWebView()?.GoBack();
        private void BtnForward_Click(object? sender, EventArgs e) => GetContentWebViewForward();
        private void BtnRefresh_Click(object? sender, EventArgs e) => GetCurrentWebView()?.Reload();
        private void BtnHome_Click(object? sender, EventArgs e) => GetCurrentWebView()?.CoreWebView2?.Navigate(HomeUrl);
        private void GetContentWebViewForward() => GetCurrentWebView()?.GoForward();

        private void LogToHistory(string? url)
        {
            if (string.IsNullOrWhiteSpace(url) || url.StartsWith("data:") || url == "about:blank") return;
            try
            {
                string path = HistoryFilePath();
                Directory.CreateDirectory(Path.GetDirectoryName(path)!);
                File.AppendAllText(path, $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} - {url}\n");
            }
            catch { }
        }

        private string HistoryFilePath() =>
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "EcoBrowser", "history.txt");

        private void BtnHistory_Click(object? sender, EventArgs e)
        {
            string path = HistoryFilePath();
            if (!File.Exists(path))
            {
                Directory.CreateDirectory(Path.GetDirectoryName(path)!);
                File.WriteAllText(path, "");
            }
            try { Process.Start(new ProcessStartInfo(path) { UseShellExecute = true }); }
            catch { MessageBox.Show("Could not open history file.", AppName, MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }

        private void BtnDownloads_Click(object? sender, EventArgs e) => GetCurrentWebView()?.CoreWebView2?.OpenDefaultDownloadDialog();
    }
}