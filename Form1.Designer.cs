namespace EcoBrowser
{
    partial class Form1
    {
        private System.ComponentModel.IContainer components = null;

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null)) components.Dispose();
            base.Dispose(disposing);
        }

        private void InitializeComponent()
        {
            tabControl1 = new TabControl();
            tabPage1 = new TabPage();
            webView1 = new Microsoft.Web.WebView2.WinForms.WebView2();
            toolPanel = new Panel();
            leftPanel = new FlowLayoutPanel();
            btnBack = new Button();
            btnForward = new Button();
            btnRefresh = new Button();
            btnHome = new Button();
            rightPanel = new FlowLayoutPanel();
            btnAddTab = new Button();
            btnHistory = new Button();
            btnDownloads = new Button();
            btnDarkMode = new Button(); // Integrated directly into designer layout
            addressBarPanel = new Panel();
            lblSecure = new Label();
            txtUrl = new TextBox();

            tabControl1.SuspendLayout();
            tabPage1.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)webView1).BeginInit();
            toolPanel.SuspendLayout();
            leftPanel.SuspendLayout();
            rightPanel.SuspendLayout();
            addressBarPanel.SuspendLayout();
            SuspendLayout();

            // TabControl
            tabControl1.Controls.Add(tabPage1);
            tabControl1.Dock = DockStyle.Fill;
            tabControl1.ItemSize = new Size(180, 34);
            tabControl1.Location = new Point(0, 0);
            tabControl1.Name = "tabControl1";
            tabControl1.Size = new Size(1008, 681);
            tabControl1.SizeMode = TabSizeMode.Fixed;

            // TabPage
            tabPage1.Controls.Add(webView1);
            tabPage1.Controls.Add(toolPanel);
            tabPage1.Location = new Point(4, 38);
            tabPage1.Name = "tabPage1";
            tabPage1.Size = new Size(1000, 639);
            tabPage1.Text = "EcoBrowser";
            tabPage1.UseVisualStyleBackColor = true;

            // ToolPanel Container
            toolPanel.Name = "toolPanel";
            toolPanel.BackColor = Color.White;
            toolPanel.Dock = DockStyle.Top;
            toolPanel.Height = 50;
            toolPanel.Padding = new Padding(6, 7, 6, 7);
            toolPanel.Controls.Add(addressBarPanel);
            toolPanel.Controls.Add(rightPanel);
            toolPanel.Controls.Add(leftPanel);

            // Left Navigation Panel
            leftPanel.Name = "leftPanel";
            leftPanel.Dock = DockStyle.Left;
            leftPanel.AutoSize = true;
            leftPanel.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            leftPanel.WrapContents = false;
            leftPanel.Controls.AddRange(new Control[] { btnBack, btnForward, btnRefresh, btnHome });

            // Right Action Panel (Including DarkMode Button Managed via Designer)
            rightPanel.Name = "rightPanel";
            rightPanel.Dock = DockStyle.Right;
            rightPanel.AutoSize = true;
            rightPanel.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            rightPanel.WrapContents = false;
            rightPanel.Controls.AddRange(new Control[] { btnAddTab, btnHistory, btnDownloads, btnDarkMode });

            var buttons = new[] { btnBack, btnForward, btnRefresh, btnHome, btnAddTab, btnHistory, btnDownloads, btnDarkMode };
            var names = new[] { "btnBack", "btnForward", "btnRefresh", "btnHome", "btnAddTab", "btnHistory", "btnDownloads", "btnDarkMode" };
            var symbols = new[] { "<", ">", "↻", "⌂", "+", "🕐", "⬇", "🌙" };

            for (int i = 0; i < buttons.Length; i++)
            {
                buttons[i].Name = names[i];
                buttons[i].Text = symbols[i];
                buttons[i].Size = new Size(32, 32);
                buttons[i].FlatStyle = FlatStyle.Flat;
                buttons[i].FlatAppearance.BorderSize = 0;
                buttons[i].Font = new Font("Segoe UI Symbol", 11F, FontStyle.Bold);
                buttons[i].ForeColor = Color.FromArgb(60, 64, 67);
                buttons[i].BackColor = Color.White;
                buttons[i].Margin = new Padding(2, 0, 2, 0);
                buttons[i].Cursor = Cursors.Hand;
            }

            // AddressBar Panel
            addressBarPanel.Name = "addressBarPanel";
            addressBarPanel.Dock = DockStyle.Fill;
            addressBarPanel.BackColor = Color.FromArgb(241, 243, 244);
            addressBarPanel.Padding = new Padding(8, 6, 8, 6);
            addressBarPanel.Controls.Add(txtUrl);
            addressBarPanel.Controls.Add(lblSecure);

            lblSecure.Name = "lblSecure";
            lblSecure.Dock = DockStyle.Left;
            lblSecure.Width = 24;
            lblSecure.TextAlign = ContentAlignment.MiddleCenter;
            lblSecure.Font = new Font("Segoe UI Symbol", 9F);
            lblSecure.ForeColor = Color.FromArgb(95, 99, 104);

            txtUrl.Name = "txtUrl";
            txtUrl.Dock = DockStyle.Fill;
            txtUrl.BackColor = Color.FromArgb(241, 243, 244);
            txtUrl.BorderStyle = BorderStyle.None;
            txtUrl.Font = new Font("Segoe UI", 10F);

            // WebView
            webView1.Name = "webView1";
            webView1.Dock = DockStyle.Fill;

            // Form
            ClientSize = new Size(1008, 681);
            Controls.Add(tabControl1);
            Name = "Form1";
            StartPosition = FormStartPosition.CenterScreen;
            Text = "EcoBrowser";

            leftPanel.ResumeLayout(false);
            rightPanel.ResumeLayout(false);
            tabControl1.ResumeLayout(false);
            tabPage1.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)webView1).EndInit();
            toolPanel.ResumeLayout(false);
            toolPanel.PerformLayout();
            addressBarPanel.ResumeLayout(false);
            addressBarPanel.PerformLayout();
            ResumeLayout(false);
        }

        private TabControl tabControl1;
        private TabPage tabPage1;
        private Panel toolPanel, addressBarPanel;
        private FlowLayoutPanel leftPanel, rightPanel;
        private Button btnBack, btnForward, btnRefresh, btnHome, btnAddTab, btnHistory, btnDownloads, btnDarkMode;
        private Label lblSecure;
        private TextBox txtUrl;
        private Microsoft.Web.WebView2.WinForms.WebView2 webView1;
    }
}