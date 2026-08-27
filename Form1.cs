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

            // Load app icon
            SetAppIcon();

            // Register in Windows Registry so it can be set as default browser
            RegisterAsBrowser();

            // Catch external link passed via command line (when opening links from Discord, Word, etc.)
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

                // Register ProgID & Protocols in Registry (HKCU)
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
                string localIconPath = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "icon.png");
                string absoluteIconPath = @"D:\Projects\C#\EcoBrowser\icon.png";

                string targetPath = File.Exists(localIconPath) ? localIconPath : absoluteIconPath;

                if (File.Exists(targetPath))
                {
                    using var bitmap = new Bitmap(targetPath);
                    this.Icon = Icon.FromHandle(bitmap.GetHicon());
                }
            }
            catch { }
        }

        private async void Form1_Load(object? sender, EventArgs e)
        {
            tabControl1.DrawMode = TabDrawMode.OwnerDrawFixed;
            tabControl1.SizeMode = TabSizeMode.Fixed;
            tabControl1.ItemSize = new Size(180, 32);
            tabControl1.Padding = new Point(12, 4);

            tabControl1.DrawItem += TabControl1_DrawItem;
            tabControl1.MouseDown += TabControl1_MouseDown;
            tabControl1.SelectedIndexChanged += (s, ev) => SyncAddressBar(GetCurrentWebView());

            tabPage1.Text = AppName;
            RoundControl(addressBarPanel, AddressRadius);

            SetupButton(btnBack, BtnBack_Click);
            SetupButton(btnForward, BtnForward_Click);
            SetupButton(btnRefresh, BtnRefresh_Click);
            SetupButton(btnHome, BtnHome_Click);
            SetupButton(btnAddTab, BtnAddTab_Click);
            SetupButton(btnHistory, BtnHistory_Click);
            SetupButton(btnDownloads, BtnDownloads_Click);

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

        private void AddHoverEffect(Button btn) => btn.MouseEnter += (s, e) => btn.BackColor = Color.FromArgb(230, 233, 237);

        private void ResetButtonColor(Button btn) => btn.BackColor = Color.White;

        private void RoundControl(Control c, int radius)
        {
            void Apply()
            {
                if (c.Width <= 0 || c.Height <= 0) return;
                using var path = RoundedRect(new Rectangle(0, 0, c.Width, c.Height), radius);
                c.Region = new Region(path);
            }
            c.Resize += (s, e) => Apply();
            c.MouseLeave += (s, e) => ResetButtonColor(c as Button ?? new Button());
            Apply();
        }

        private GraphicsPath RoundedRect(Rectangle rect, int radius)
        {
            int d = radius * 2;
            var path = new GraphicsPath();
            path.AddArc(rect.X, rect.Y, d, d, 180, 90);
            path.AddArc(rect.Right - d, rect.Y, d, d, 270, 90);
            path.AddArc(rect.Right - d, rect.Bottom - d, d, d, 0, 90);
            path.AddArc(rect.X, rect.Bottom - d, d, d, 90, 90);
            path.CloseFigure();
            return path;
        }

        private async Task InitializeWebViewAsync(WebView2 webView, string startUrl = HomeUrl)
        {
            try
            {
                while (!webView.IsHandleCreated) await Task.Delay(50);
                await webView.EnsureCoreWebView2Async();

                webView.CoreWebView2.AddWebResourceRequestedFilter("*", CoreWebView2WebResourceContext.All);
                webView.CoreWebView2.WebResourceRequested += (s, args) =>
                {
                    if (AdBlockDomains.Any(domain => args.Request.Uri.ToLower().Contains(domain)))
                        args.Response = webView.CoreWebView2.Environment.CreateWebResourceResponse(null, 403, "Blocked", "");
                };

                webView.CoreWebView2.DocumentTitleChanged += (s, e) => UpdateTabTitle(webView);
                webView.CoreWebView2.NavigationCompleted += (s, args) => { SyncAddressBar(webView); LogToHistory(webView.Source?.ToString()); };
                webView.CoreWebView2.Navigate(startUrl);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"WebView Error: {ex.Message}", AppName, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void UpdateTabTitle(WebView2 webView)
        {
            if (FindParentTabPage(webView) is TabPage tab && webView.CoreWebView2 != null)
            {
                tab.Text = string.IsNullOrWhiteSpace(webView.CoreWebView2.DocumentTitle) ? AppName : webView.CoreWebView2.DocumentTitle;
                tabControl1.Invalidate();
            }
        }

        private TabPage? FindParentTabPage(Control? c)
        {
            while (c != null && c is not TabPage) c = c.Parent;
            return c as TabPage;
        }

        private void SyncAddressBar(WebView2? webView)
        {
            if (webView?.CoreWebView2 == null || GetCurrentWebView() != webView) return;
            var txt = GetCurrentAddressBar();
            if (txt != null)
            {
                string src = webView.Source?.ToString() ?? "";
                txt.Text = src.StartsWith("data:") || src == "about:blank" ? "" : src;
            }
        }

        private WebView2? GetCurrentWebView() => tabControl1.SelectedTab?.Controls.OfType<WebView2>().FirstOrDefault();
        private TextBox? GetCurrentAddressBar() => tabControl1.SelectedTab?.Controls.Find("txtUrl", true).FirstOrDefault() as TextBox;

        private void TabControl1_DrawItem(object? sender, DrawItemEventArgs e)
        {
            if (e.Index < 0 || e.Index >= tabControl1.TabPages.Count) return;

            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            Rectangle tabRect = tabControl1.GetTabRect(e.Index);
            bool isSelected = tabControl1.SelectedIndex == e.Index;

            using (var stripBg = new SolidBrush(Color.FromArgb(225, 228, 232)))
                g.FillRectangle(stripBg, tabRect);

            Rectangle tabBoxRect = new Rectangle(tabRect.X + 2, tabRect.Y + 3, tabRect.Width - 4, tabRect.Height - 3);
            Color fillColor = isSelected ? Color.White : Color.FromArgb(225, 228, 232);
            Color textColor = isSelected ? Color.Black : Color.FromArgb(90, 95, 100);

            using (var path = RoundedRect(tabBoxRect, 6))
            using (var brush = new SolidBrush(fillColor))
                g.FillPath(brush, path);

            Rectangle textRect = new Rectangle(tabBoxRect.X + 8, tabBoxRect.Y, tabBoxRect.Width - 26, tabBoxRect.Height);
            using (Font tabFont = new Font("Segoe UI", 9F, isSelected ? FontStyle.Bold : FontStyle.Regular))
                TextRenderer.DrawText(g, tabControl1.TabPages[e.Index].Text, tabFont, textRect, textColor, TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.EndEllipsis);

            Rectangle closeRect = new Rectangle(tabBoxRect.Right - 18, tabBoxRect.Y + (tabBoxRect.Height - 14) / 2, 14, 14);
            using (Font closeFont = new Font("Segoe UI", 8F))
                TextRenderer.DrawText(g, "x", closeFont, closeRect, Color.FromArgb(120, 120, 120), TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter);
        }

        private void TabControl1_MouseDown(object? sender, MouseEventArgs e)
        {
            for (int i = 0; i < tabControl1.TabPages.Count; i++)
            {
                Rectangle tabRect = tabControl1.GetTabRect(i);
                Rectangle closeRect = new Rectangle(tabRect.Right - 22, tabRect.Y + 8, 14, 14);

                if (closeRect.Contains(e.Location))
                {
                    if (tabControl1.TabCount > 1)
                    {
                        tabControl1.TabPages[i].Dispose();
                        tabControl1.TabPages.RemoveAt(i);
                    }
                    else
                        MessageBox.Show("Cannot close the last tab.", AppName, MessageBoxButtons.OK, MessageBoxIcon.Information);
                    break;
                }
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

            var leftCtrls = CreateButtonPanel(DockStyle.Left,
                new (string, EventHandler)[] { ("<", BtnBack_Click), (">", BtnForward_Click), ("↻", BtnRefresh_Click), ("⌂", BtnHome_Click) },
                font);

            var rightCtrls = CreateButtonPanel(DockStyle.Right,
                new (string, EventHandler)[] { ("+", BtnAddTab_Click), ("🕐", BtnHistory_Click), ("⬇", BtnDownloads_Click) },
                font);

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
                btn.Click += onClick;
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
            if (wv?.CoreWebView2 == null || txt?.Text == null || string.IsNullOrWhiteSpace(txt.Text)) return;

            string input = txt.Text.Trim();
            bool looksLikeUrl = input.Contains('.') && !input.Contains(' ');
            string url = input.StartsWith("http://") || input.StartsWith("https://") ? input :
                         looksLikeUrl ? "https://" + input : "https://www.google.com/search?q=" + Uri.EscapeDataString(input);
            wv.CoreWebView2.Navigate(url);
        }

        private void BtnBack_Click(object? sender, EventArgs e) => GetCurrentWebView()?.GoBack();
        private void BtnForward_Click(object? sender, EventArgs e) => GetCurrentWebView()?.GoForward();
        private void BtnRefresh_Click(object? sender, EventArgs e) => GetCurrentWebView()?.Reload();
        private void BtnHome_Click(object? sender, EventArgs e) => GetCurrentWebView()?.CoreWebView2?.Navigate(HomeUrl);

        private void LogToHistory(string? url)
        {
            if (string.IsNullOrWhiteSpace(url) || url.StartsWith("data:") || url == "about:blank") return;
            try
            {
                string path = HistoryFilePath();
                Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path)!);
                File.AppendAllText(path, $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} - {url}\n");
            }
            catch { }
        }

        private string HistoryFilePath() =>
            System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "EcoBrowser", "history.txt");

        private void BtnHistory_Click(object? sender, EventArgs e)
        {
            string path = HistoryFilePath();
            if (!File.Exists(path))
            {
                Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path)!);
                File.WriteAllText(path, "");
            }
            try { System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(path) { UseShellExecute = true }); }
            catch { MessageBox.Show("Could not open history file.", AppName, MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }

        private void BtnDownloads_Click(object? sender, EventArgs e)
        {
            GetCurrentWebView()?.CoreWebView2?.OpenDefaultDownloadDialog();
        }
    }
}