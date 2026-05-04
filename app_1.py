"""
My Industry AI Solutions - Streamlit SaaS Web App
تحويل تطبيق Flutter إلى تطبيق ويب باستخدام Streamlit
"""

import streamlit as st
import sqlite3
import hashlib
import os
import uuid
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="My Industry AI Solutions",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── THEME / STYLES ────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;500;600;700&display=swap');
  
  html, body, [class*="css"] { font-family: 'Rajdhani', sans-serif; }
  
  .main { background-color: #0A0E1A; }
  
  /* Header brand */
  .brand-header {
    font-family: 'Orbitron', sans-serif;
    font-size: 22px; font-weight: 900; letter-spacing: 4px;
    color: #4FC3F7; text-align: center; padding: 10px 0;
  }
  .brand-sub {
    font-family: 'Rajdhani', sans-serif;
    font-size: 13px; color: #78909C; text-align: center; letter-spacing: 2px;
  }
  
  /* Metric cards */
  .metric-card {
    background: #151B2B; border: 1px solid #1E2A3A;
    border-radius: 12px; padding: 20px; margin: 6px 0;
  }
  .metric-value {
    font-family: 'Orbitron', sans-serif; font-size: 22px;
    font-weight: 700; color: #E0E6F0;
  }
  .metric-label {
    font-size: 11px; color: #546E7A; letter-spacing: 2px;
    text-transform: uppercase; margin-top: 4px;
  }
  
  /* Section labels */
  .section-label {
    font-family: 'Rajdhani', sans-serif; font-size: 12px;
    font-weight: 700; color: #78909C; letter-spacing: 3px;
    text-transform: uppercase; border-bottom: 1px solid #1E2A3A;
    padding-bottom: 6px; margin: 18px 0 12px 0;
  }
  
  /* Status badges */
  .badge-green  { background:#00875A22; color:#00D68F; padding:3px 10px; border-radius:10px; font-size:11px; letter-spacing:1px; }
  .badge-red    { background:#C0392B22; color:#FF6B6B; padding:3px 10px; border-radius:10px; font-size:11px; letter-spacing:1px; }
  .badge-yellow { background:#CC990022; color:#FFD600; padding:3px 10px; border-radius:10px; font-size:11px; letter-spacing:1px; }
  .badge-blue   { background:#2196F322; color:#4FC3F7; padding:3px 10px; border-radius:10px; font-size:11px; letter-spacing:1px; }
  
  /* Trial warning */
  .trial-box {
    background: #FF8F0015; border: 1px solid #FF8F0050;
    border-radius: 10px; padding: 14px 18px; margin-bottom: 16px;
    font-family: 'Rajdhani', sans-serif; font-size: 14px; color: #FF8F00;
  }
  
  /* Streamlit overrides */
  .stButton>button {
    font-family: 'Rajdhani', sans-serif; font-weight: 700;
    letter-spacing: 1px; border-radius: 8px;
  }
  .stTextInput>div>div>input { font-family: 'Rajdhani', sans-serif; }
  .stSelectbox>div>div { font-family: 'Rajdhani', sans-serif; }
  
  div[data-testid="stSidebarContent"] {
    background-color: #0D1117;
  }
  
  /* Hide default streamlit branding */
  #MainMenu {visibility: hidden;}
  footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE LAYER  (sqlite3 — متوافق مع الاستضافة السحابية)
# ═══════════════════════════════════════════════════════════════════════════════

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "industry_ai.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """إنشاء الجداول وإدراج بيانات تجريبية إذا لم تكن موجودة."""
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS companies (
        id TEXT PRIMARY KEY, name TEXT NOT NULL,
        industry TEXT, address TEXT, phone TEXT, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
        username TEXT NOT NULL, password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'worker',
        is_active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL,
        UNIQUE(company_id, username)
    );
    CREATE TABLE IF NOT EXISTS stock_items (
        id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
        name TEXT NOT NULL, category TEXT NOT NULL,
        type TEXT NOT NULL DEFAULT 'material',
        quantity REAL NOT NULL DEFAULT 0, unit TEXT NOT NULL DEFAULT 'pcs',
        unit_cost REAL NOT NULL DEFAULT 0, min_quantity REAL NOT NULL DEFAULT 0,
        location TEXT, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS machines (
        id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
        name TEXT NOT NULL, model TEXT,
        status TEXT NOT NULL DEFAULT 'idle',
        hourly_cost REAL NOT NULL DEFAULT 0,
        location TEXT, last_maintenance TEXT, notes TEXT
    );
    CREATE TABLE IF NOT EXISTS workers (
        id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
        full_name TEXT NOT NULL, position TEXT,
        daily_wage REAL NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'active',
        phone TEXT, joined_date TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS production_records (
        id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
        machine_id TEXT, worker_id TEXT,
        product_name TEXT NOT NULL,
        quantity REAL NOT NULL DEFAULT 0, unit TEXT NOT NULL DEFAULT 'pcs',
        production_cost REAL NOT NULL DEFAULT 0,
        recorded_at TEXT NOT NULL, shift TEXT NOT NULL DEFAULT 'day', notes TEXT
    );
    CREATE TABLE IF NOT EXISTS sales_records (
        id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
        product_name TEXT NOT NULL,
        quantity REAL NOT NULL DEFAULT 0, unit_price REAL NOT NULL DEFAULT 0,
        total_amount REAL NOT NULL DEFAULT 0,
        customer TEXT, sold_at TEXT NOT NULL, notes TEXT
    );
    CREATE TABLE IF NOT EXISTS daily_reports (
        id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
        report_date TEXT NOT NULL,
        total_sales REAL DEFAULT 0, total_production_cost REAL DEFAULT 0,
        worker_wages REAL DEFAULT 0, net_profit REAL DEFAULT 0,
        total_production_qty REAL DEFAULT 0,
        UNIQUE(company_id, report_date)
    );
    CREATE TABLE IF NOT EXISTS worker_tasks (
        id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
        worker_id TEXT NOT NULL, task_name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        assigned_date TEXT NOT NULL, due_date TEXT, notes TEXT
    );
    """)

    # ── Seed demo data ──────────────────────────────────────────────────────────
    existing = c.execute("SELECT id FROM companies WHERE id='COMP001'").fetchone()
    if not existing:
        now = datetime.now().isoformat()
        c.execute("INSERT INTO companies VALUES (?,?,?,?,?,?)",
                  ('COMP001', 'Demo Manufacturing Co.', 'Manufacturing', 'Industrial Zone', '+1234567890', now))

        def pw(p): return hashlib.sha256(p.encode()).hexdigest()
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
                  (str(uuid.uuid4()), 'COMP001', 'admin', pw('admin123'), 'Admin User', 'admin', 1, now))
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
                  (str(uuid.uuid4()), 'COMP001', 'worker1', pw('worker123'), 'Ahmed Worker', 'worker', 1, now))

        # Stock
        for item in [
            ('Steel Sheets', 'Raw Material', 'material', 150, 'kg', 5.5, 20),
            ('Aluminum Rods', 'Raw Material', 'material', 80, 'pcs', 12.0, 10),
            ('Finished Gears', 'Product', 'product', 45, 'pcs', 35.0, 5),
            ('Motor Parts', 'Component', 'material', 200, 'pcs', 8.0, 30),
        ]:
            c.execute("INSERT INTO stock_items VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (str(uuid.uuid4()), 'COMP001', item[0], item[1], item[2],
                       item[3], item[4], item[5], item[6], 'Warehouse A', now))

        # Machines
        for m in [
            ('CNC Lathe 001', 'Mazak QTN-200', 'running', 25.0),
            ('Press Machine 01', 'Amada TP-300', 'idle', 18.0),
            ('Welding Robot', 'KUKA KR-60', 'running', 30.0),
            ('Drill Press', 'Bosch DH-500', 'maintenance', 10.0),
        ]:
            c.execute("INSERT INTO machines VALUES (?,?,?,?,?,?,?,?,?)",
                      (str(uuid.uuid4()), 'COMP001', m[0], m[1], m[2], m[3],
                       'Floor A', date.today().isoformat(), ''))

        # Workers
        for w in [
            ('Mohammed Ali', 'Machine Operator', 85.0, 'active', '+9661111'),
            ('Sara Hassan', 'Quality Inspector', 90.0, 'active', '+9662222'),
            ('Omar Khalid', 'Technician', 95.0, 'active', '+9663333'),
            ('Fatima Nour', 'Supervisor', 120.0, 'on_leave', '+9664444'),
        ]:
            c.execute("INSERT INTO workers VALUES (?,?,?,?,?,?,?,?)",
                      (str(uuid.uuid4()), 'COMP001', w[0], w[1], w[2], w[3], w[4],
                       (date.today() - timedelta(days=90)).isoformat()))

        # Demo sales + production for last 7 days
        for i in range(7):
            d = (date.today() - timedelta(days=i)).isoformat()
            prod_id = str(uuid.uuid4())
            c.execute("INSERT INTO production_records VALUES (?,?,NULL,NULL,?,?,?,?,?,?,?)",
                      (prod_id, 'COMP001', 'Finished Gears',
                       float(15 + i * 3), 'pcs', float(200 + i * 20),
                       f"{d}T08:00:00", 'day', ''))
            sale_id = str(uuid.uuid4())
            amt = float(800 + i * 120)
            c.execute("INSERT INTO sales_records VALUES (?,?,?,?,?,?,?,?,?)",
                      (sale_id, 'COMP001', 'Finished Gears',
                       float(10 + i), 35.0, amt, 'Walk-in Customer', f"{d}T14:00:00", ''))

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# LICENSE GATE  (نظام ترخيص بـ SHA-256 — مثل LicenseGate.dart)
# ═══════════════════════════════════════════════════════════════════════════════

_VALID_HASH = hashlib.sha256(b'22459129071981_INDUSTRY_AI_LICENSE').hexdigest()
FREE_TRIALS  = 3


def validate_license_key(key: str) -> bool:
    cleaned = key.strip().replace(' ', '').replace('-', '')
    h = hashlib.sha256(f"{cleaned}_INDUSTRY_AI_LICENSE".encode()).hexdigest()
    return h == _VALID_HASH


def show_license_screen():
    st.markdown('<div class="brand-header">🏭 MY INDUSTRY AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">ENTERPRISE LICENSE ACTIVATION</div>', unsafe_allow_html=True)
    st.markdown("---")

    trials_left = FREE_TRIALS - st.session_state.get("trial_count", 0)

    if trials_left <= 0:
        st.error("🔒 لقد استنفدت جميع المحاولات المجانية. يرجى إدخال مفتاح ترخيص صالح للمتابعة.")
    else:
        st.markdown(
            f'<div class="trial-box">⚡ وضع التجربة المجانية — متبقي <b>{trials_left}</b> '
            f'محاولة من {FREE_TRIALS}</div>', unsafe_allow_html=True
        )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔑 تفعيل الترخيص")
        license_key = st.text_input("مفتاح الترخيص", placeholder="XXXX-XXXX-XXXX-XXXX",
                                     type="password", key="lic_input")

        if st.button("✅ تفعيل الترخيص", use_container_width=True, type="primary"):
            if validate_license_key(license_key):
                st.session_state["licensed"] = True
                st.session_state["license_hint"] = (
                    f"{license_key[:4]}****{license_key[-4:]}" if len(license_key) >= 8 else "****"
                )
                st.success("✅ تم تفعيل الترخيص بنجاح! مرحباً بك.")
                st.rerun()
            else:
                count = st.session_state.get("trial_count", 0) + 1
                st.session_state["trial_count"] = count
                remaining = FREE_TRIALS - count
                if remaining > 0:
                    st.error(f"❌ مفتاح الترخيص غير صحيح. متبقي {remaining} محاولة.")
                else:
                    st.error("❌ انتهت جميع المحاولات المجانية.")
                st.rerun()

        st.markdown("---")
        st.markdown("**🧪 للتجربة:** استخدم المفتاح `")

        if trials_left > 0:
            if st.button("🚀 تجربة مجانية (تخطي الترخيص)", use_container_width=True):
                count = st.session_state.get("trial_count", 0) + 1
                st.session_state["trial_count"] = count
                st.session_state["licensed"] = True
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH LAYER
# ═══════════════════════════════════════════════════════════════════════════════

def db_login(company_id: str, username: str, password: str):
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = get_conn()
    row = conn.execute(
        """SELECT u.*, c.name as company_name
           FROM users u JOIN companies c ON c.id = u.company_id
           WHERE u.company_id=? AND u.username=? AND u.password_hash=? AND u.is_active=1""",
        (company_id.upper(), username, pw_hash)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def show_login_screen():
    st.markdown('<div class="brand-header">🏭 SYSTEM LOGIN</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">My Industry AI Solutions</div>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("#### 🔐 بيانات الدخول")
            company_id = st.text_input("Company ID", value="COMP001",
                                        placeholder="e.g. COMP001")
            username = st.text_input("اسم المستخدم", value="admin",
                                      placeholder="username")
            password = st.text_input("كلمة المرور", type="password",
                                      placeholder="••••••••")
            submitted = st.form_submit_button("🔓 AUTHENTICATE", use_container_width=True,
                                               type="primary")

        if submitted:
            user = db_login(company_id, username, password)
            if user:
                st.session_state["user"] = user
                st.success(f"✅ مرحباً {user['full_name']}!")
                st.rerun()
            else:
                st.error("❌ بيانات الدخول غير صحيحة. تحقق من Company ID والمستخدم وكلمة المرور.")

        st.info("📋 **بيانات تجريبية:**  \n"
                "Company ID: `COMP001`  \n"
                "Admin: `admin` / `admin123`  \n"
                "Worker: `worker1` / `worker123`")


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def q(sql, params=(), one=False):
    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    result = [dict(r) for r in rows]
    return result[0] if (one and result) else result


def execute(sql, params=()):
    conn = get_conn()
    conn.execute(sql, params)
    conn.commit()
    conn.close()


def get_dashboard_summary(company_id):
    today = date.today().isoformat()
    summary = {}
    summary["today_sales"] = (q(
        "SELECT COALESCE(SUM(total_amount),0) as v FROM sales_records WHERE company_id=? AND sold_at LIKE ?",
        (company_id, f"{today}%"), one=True) or {}).get("v", 0)
    summary["today_production"] = (q(
        "SELECT COALESCE(SUM(quantity),0) as v FROM production_records WHERE company_id=? AND recorded_at LIKE ?",
        (company_id, f"{today}%"), one=True) or {}).get("v", 0)
    machines = q("SELECT status FROM machines WHERE company_id=?", (company_id,))
    summary["total_machines"] = len(machines)
    summary["running_machines"] = sum(1 for m in machines if m["status"] == "running")
    workers = q("SELECT status FROM workers WHERE company_id=?", (company_id,))
    summary["active_workers"] = sum(1 for w in workers if w["status"] == "active")
    stock = q("SELECT quantity, min_quantity FROM stock_items WHERE company_id=?", (company_id,))
    summary["stock_count"] = len(stock)
    summary["low_stock_count"] = sum(1 for s in stock if s["quantity"] <= s["min_quantity"])
    return summary


def generate_daily_report(company_id, report_date):
    sales = (q("SELECT COALESCE(SUM(total_amount),0) as v FROM sales_records WHERE company_id=? AND sold_at LIKE ?",
               (company_id, f"{report_date}%"), one=True) or {}).get("v", 0)
    prod_cost = (q("SELECT COALESCE(SUM(production_cost),0) as v FROM production_records WHERE company_id=? AND recorded_at LIKE ?",
                   (company_id, f"{report_date}%"), one=True) or {}).get("v", 0)
    active_workers = q("SELECT COUNT(*) as v FROM workers WHERE company_id=? AND status='active'",
                       (company_id,), one=True).get("v", 0)
    wages = active_workers * 85.0
    prod_qty = (q("SELECT COALESCE(SUM(quantity),0) as v FROM production_records WHERE company_id=? AND recorded_at LIKE ?",
                  (company_id, f"{report_date}%"), one=True) or {}).get("v", 0)
    net = sales - prod_cost - wages
    rid = str(uuid.uuid4())
    conn = get_conn()
    conn.execute("""INSERT OR REPLACE INTO daily_reports
        (id, company_id, report_date, total_sales, total_production_cost, worker_wages, net_profit, total_production_qty)
        VALUES (?,?,?,?,?,?,?,?)""",
        (rid, company_id, report_date, sales, prod_cost, wages, net, prod_qty))
    conn.commit(); conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# SCREENS
# ═══════════════════════════════════════════════════════════════════════════════

def screen_dashboard():
    user = st.session_state["user"]
    cid  = user["company_id"]
    today = date.today().isoformat()

    generate_daily_report(cid, today)
    s = get_dashboard_summary(cid)

    st.markdown(f"### 🏭 OPERATIONS COMMAND — {user['company_name']}")
    st.caption(f"📅 {datetime.now().strftime('%A, %B %d • %Y')}  |  🟢 ONLINE")

    # ── KPI Cards ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">📊 SYSTEM STATUS</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    def kpi(col, label, value, icon, color):
        col.markdown(f"""
        <div class="metric-card" style="border-color:{color}33;">
          <div style="font-size:28px">{icon}</div>
          <div class="metric-value" style="color:{color}">{value}</div>
          <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    kpi(c1, "TODAY SALES", f"${s['today_sales']:,.2f}", "💰", "#00D68F")
    kpi(c2, "PRODUCTION",  f"{s['today_production']:.0f} pcs", "⚙️", "#4FC3F7")
    kpi(c3, "MACHINES",    f"{s['running_machines']}/{s['total_machines']} RUNNING", "🔧", "#FF9800")
    kpi(c4, "WORKERS",     f"{s['active_workers']} ACTIVE", "👷", "#FFD600")

    # Stock alert
    if s["low_stock_count"] > 0:
        st.warning(f"⚠️ **تحذير المخزون:** {s['low_stock_count']} صنف وصل لأدنى مستوى من أصل {s['stock_count']} صنف.")
    else:
        st.success(f"✅ المخزون سليم — {s['stock_count']} صنف مراقب.")

    # ── Weekly Charts ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">📈 WEEKLY PERFORMANCE</div>', unsafe_allow_html=True)

    reports = q("""SELECT report_date, total_sales, total_production_cost, worker_wages, net_profit
                   FROM daily_reports WHERE company_id=? ORDER BY report_date DESC LIMIT 7""", (cid,))
    reports = list(reversed(reports))

    if reports:
        df = pd.DataFrame(reports)
        fig = go.Figure()
        fig.add_bar(x=df["report_date"], y=df["total_sales"],    name="Sales",  marker_color="#4FC3F7")
        fig.add_bar(x=df["report_date"], y=df["total_production_cost"]+df["worker_wages"],
                    name="Costs", marker_color="#FF9800")
        fig.update_layout(
            barmode="group", plot_bgcolor="#151B2B", paper_bgcolor="#151B2B",
            font_color="#E0E6F0", legend=dict(bgcolor="#151B2B"),
            margin=dict(l=0, r=0, t=20, b=0), height=280,
            xaxis=dict(gridcolor="#1E2A3A"), yaxis=dict(gridcolor="#1E2A3A")
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Machine Status Pie ─────────────────────────────────────────────────────
    st.markdown('<div class="section-label">🔩 MACHINE STATUS</div>', unsafe_allow_html=True)
    machines = q("SELECT status FROM machines WHERE company_id=?", (cid,))
    if machines:
        mcol1, mcol2 = st.columns([1, 2])
        status_count = {}
        for m in machines:
            status_count[m["status"]] = status_count.get(m["status"], 0) + 1
        colors = {"running": "#00D68F", "idle": "#FFD600", "maintenance": "#FF6B6B"}
        fig2 = go.Figure(go.Pie(
            labels=list(status_count.keys()),
            values=list(status_count.values()),
            hole=0.5,
            marker_colors=[colors.get(k, "#78909C") for k in status_count.keys()]
        ))
        fig2.update_layout(
            paper_bgcolor="#151B2B", font_color="#E0E6F0",
            margin=dict(l=0, r=0, t=0, b=0), height=220,
            showlegend=True, legend=dict(bgcolor="#151B2B")
        )
        with mcol1: st.plotly_chart(fig2, use_container_width=True)
        with mcol2:
            st.markdown("**حالة الآلات:**")
            for status, count in status_count.items():
                badge = "badge-green" if status == "running" else "badge-yellow" if status == "idle" else "badge-red"
                st.markdown(f'<span class="{badge}">{status.upper()}</span> — **{count}** آلة', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────

def screen_production():
    user = st.session_state["user"]
    cid  = user["company_id"]

    st.markdown("### ⚙️ PRODUCTION LOG")

    # Date filter
    sel_date = st.date_input("📅 تاريخ الإنتاج", value=date.today())
    date_str = sel_date.isoformat()

    records  = q("SELECT * FROM production_records WHERE company_id=? AND recorded_at LIKE ? ORDER BY recorded_at DESC",
                 (cid, f"{date_str}%"))
    machines = q("SELECT id, name FROM machines WHERE company_id=?", (cid,))
    workers  = q("SELECT id, full_name FROM workers WHERE company_id=? AND status='active'", (cid,))

    # Summary
    total_qty  = sum(r["quantity"] for r in records)
    total_cost = sum(r["production_cost"] for r in records)
    cc1, cc2 = st.columns(2)
    cc1.metric("إجمالي الإنتاج اليوم", f"{total_qty:.0f} قطعة")
    cc2.metric("إجمالي تكلفة الإنتاج", f"${total_cost:,.2f}")

    # Add form
    with st.expander("➕ إضافة سجل إنتاج جديد", expanded=False):
        with st.form("prod_form", clear_on_submit=True):
            pname    = st.text_input("اسم المنتج *", placeholder="Finished Gears")
            col1, col2 = st.columns(2)
            qty      = col1.number_input("الكمية *", min_value=0.0, step=1.0)
            cost     = col2.number_input("تكلفة الإنتاج ($)", min_value=0.0, step=1.0)
            col3, col4 = st.columns(2)
            unit     = col3.selectbox("الوحدة", ["pcs", "kg", "m", "L", "box"])
            shift    = col4.selectbox("الوردية", ["day", "night"])
            mach_opts = {m["name"]: m["id"] for m in machines}
            work_opts = {w["full_name"]: w["id"] for w in workers}
            machine  = st.selectbox("الآلة (اختياري)", ["— بدون —"] + list(mach_opts.keys()))
            worker   = st.selectbox("العامل (اختياري)", ["— بدون —"] + list(work_opts.keys()))
            notes    = st.text_area("ملاحظات", height=68)
            if st.form_submit_button("💾 حفظ", type="primary"):
                if not pname or qty <= 0:
                    st.error("يرجى ملء اسم المنتج والكمية.")
                else:
                    execute("""INSERT INTO production_records
                        (id,company_id,machine_id,worker_id,product_name,quantity,unit,production_cost,recorded_at,shift,notes)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                        (str(uuid.uuid4()), cid,
                         mach_opts.get(machine), work_opts.get(worker),
                         pname, qty, unit, cost,
                         f"{date_str}T{datetime.now().strftime('%H:%M:%S')}",
                         shift, notes))
                    st.success("✅ تم حفظ سجل الإنتاج.")
                    st.rerun()

    # Table
    st.markdown('<div class="section-label">📋 سجلات الإنتاج</div>', unsafe_allow_html=True)
    if records:
        df = pd.DataFrame(records)[["product_name", "quantity", "unit", "production_cost", "shift", "recorded_at", "notes"]]
        df.columns = ["المنتج", "الكمية", "الوحدة", "التكلفة $", "الوردية", "وقت التسجيل", "ملاحظات"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد سجلات إنتاج لهذا التاريخ.")


# ──────────────────────────────────────────────────────────────────────────────

def screen_stock():
    user = st.session_state["user"]
    cid  = user["company_id"]
    is_admin = user["role"] == "admin"

    st.markdown("### 📦 STOCK MANAGEMENT")

    search = st.text_input("🔍 بحث في المخزون", placeholder="اسم الصنف أو الفئة...")
    ftype  = st.radio("النوع", ["الكل", "material", "product"], horizontal=True)

    items = q("SELECT * FROM stock_items WHERE company_id=? ORDER BY name", (cid,))

    # Filter
    if search:
        items = [i for i in items if search.lower() in i["name"].lower() or search.lower() in i["category"].lower()]
    if ftype != "الكل":
        items = [i for i in items if i["type"] == ftype]

    # Alerts
    low = [i for i in items if i["quantity"] <= i["min_quantity"]]
    if low:
        st.error(f"⚠️ **أصناف منخفضة:** {', '.join(i['name'] for i in low)}")

    # Add / Edit form (admin only)
    if is_admin:
        with st.expander("➕ إضافة / تعديل صنف", expanded=False):
            with st.form("stock_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                name     = col1.text_input("اسم الصنف *")
                category = col2.text_input("الفئة *", placeholder="Raw Material")
                col3, col4 = st.columns(2)
                stype    = col3.selectbox("النوع", ["material", "product"])
                unit     = col4.selectbox("الوحدة", ["pcs", "kg", "m", "L", "box", "ton"])
                col5, col6, col7 = st.columns(3)
                qty      = col5.number_input("الكمية", min_value=0.0)
                cost     = col6.number_input("تكلفة الوحدة ($)", min_value=0.0)
                minq     = col7.number_input("الحد الأدنى", min_value=0.0)
                location = st.text_input("الموقع", placeholder="Warehouse A")
                if st.form_submit_button("💾 حفظ الصنف", type="primary"):
                    if not name or not category:
                        st.error("يرجى ملء الاسم والفئة.")
                    else:
                        execute("""INSERT INTO stock_items (id,company_id,name,category,type,quantity,unit,unit_cost,min_quantity,location,updated_at)
                                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                            (str(uuid.uuid4()), cid, name, category, stype, qty, unit, cost, minq, location, datetime.now().isoformat()))
                        st.success("✅ تمت إضافة الصنف.")
                        st.rerun()

    # Display
    st.markdown('<div class="section-label">📋 قائمة المخزون</div>', unsafe_allow_html=True)
    if items:
        df = pd.DataFrame(items)[["name", "category", "type", "quantity", "unit", "unit_cost", "min_quantity", "location"]]
        df.columns = ["الاسم", "الفئة", "النوع", "الكمية", "الوحدة", "التكلفة", "الحد الأدنى", "الموقع"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Chart
        df_chart = pd.DataFrame(items)
        fig = px.bar(df_chart, x="name", y="quantity", color="type",
                     color_discrete_map={"material": "#4FC3F7", "product": "#00D68F"},
                     template="plotly_dark")
        fig.update_layout(paper_bgcolor="#151B2B", plot_bgcolor="#151B2B",
                          margin=dict(l=0, r=0, t=20, b=0), height=250)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد أصناف.")


# ──────────────────────────────────────────────────────────────────────────────

def screen_sales():
    user = st.session_state["user"]
    cid  = user["company_id"]
    today = date.today().isoformat()

    st.markdown("### 💰 SALES TRACKING")

    # Today total
    today_total = sum(r["total_amount"] for r in
                      q("SELECT total_amount FROM sales_records WHERE company_id=? AND sold_at LIKE ?",
                        (cid, f"{today}%")))
    st.markdown(f"""
    <div class="metric-card" style="border-color:#00D68F33; background:linear-gradient(135deg,#00875A22,#00D68F11)">
      <div style="font-size:28px">💰</div>
      <div class="metric-value" style="color:#00D68F">${today_total:,.2f}</div>
      <div class="metric-label">TODAY'S SALES</div>
    </div>""", unsafe_allow_html=True)

    # Add form
    with st.expander("➕ إضافة عملية بيع جديدة", expanded=False):
        with st.form("sales_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            pname    = col1.text_input("اسم المنتج *")
            customer = col2.text_input("اسم العميل")
            col3, col4, col5 = st.columns(3)
            qty      = col3.number_input("الكمية *", min_value=0.0, step=1.0)
            uprice   = col4.number_input("سعر الوحدة ($) *", min_value=0.0, step=0.5)
            sale_date = col5.date_input("تاريخ البيع", value=date.today())
            notes    = st.text_area("ملاحظات", height=68)
            if st.form_submit_button("💾 حفظ", type="primary"):
                if not pname or qty <= 0 or uprice <= 0:
                    st.error("يرجى ملء البيانات الإلزامية.")
                else:
                    total = qty * uprice
                    execute("""INSERT INTO sales_records (id,company_id,product_name,quantity,unit_price,total_amount,customer,sold_at,notes)
                               VALUES (?,?,?,?,?,?,?,?,?)""",
                        (str(uuid.uuid4()), cid, pname, qty, uprice, total,
                         customer, f"{sale_date.isoformat()}T{datetime.now().strftime('%H:%M:%S')}", notes))
                    st.success(f"✅ تم تسجيل البيع — الإجمالي: ${total:,.2f}")
                    st.rerun()

    # Records
    st.markdown('<div class="section-label">📋 سجلات المبيعات</div>', unsafe_allow_html=True)
    records = q("SELECT * FROM sales_records WHERE company_id=? ORDER BY sold_at DESC LIMIT 100", (cid,))
    if records:
        df = pd.DataFrame(records)[["product_name", "quantity", "unit_price", "total_amount", "customer", "sold_at"]]
        df.columns = ["المنتج", "الكمية", "سعر الوحدة", "الإجمالي $", "العميل", "التاريخ"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Trend chart
        df_all = pd.DataFrame(records)
        df_all["date"] = df_all["sold_at"].str[:10]
        trend = df_all.groupby("date")["total_amount"].sum().reset_index()
        fig = px.line(trend, x="date", y="total_amount", markers=True,
                      template="plotly_dark", labels={"total_amount": "المبيعات $", "date": "التاريخ"})
        fig.update_traces(line_color="#00D68F", marker_color="#00D68F")
        fig.update_layout(paper_bgcolor="#151B2B", plot_bgcolor="#151B2B",
                          margin=dict(l=0, r=0, t=20, b=0), height=220)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد سجلات مبيعات.")


# ──────────────────────────────────────────────────────────────────────────────

def screen_workers():
    user = st.session_state["user"]
    cid  = user["company_id"]
    is_admin = user["role"] == "admin"

    st.markdown("### 👷 WORKFORCE MANAGEMENT")

    workers = q("SELECT * FROM workers WHERE company_id=? ORDER BY full_name", (cid,))
    active    = sum(1 for w in workers if w["status"] == "active")
    on_leave  = sum(1 for w in workers if w["status"] == "on_leave")
    inactive  = sum(1 for w in workers if w["status"] == "inactive")

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 نشطون", active)
    c2.metric("🟡 في إجازة", on_leave)
    c3.metric("🔴 غير نشطين", inactive)

    if is_admin:
        with st.expander("➕ إضافة / تعديل موظف", expanded=False):
            with st.form("worker_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                name     = col1.text_input("الاسم الكامل *")
                position = col2.text_input("المنصب", placeholder="Machine Operator")
                col3, col4 = st.columns(2)
                wage     = col3.number_input("الأجر اليومي ($)", min_value=0.0, step=5.0)
                status   = col4.selectbox("الحالة", ["active", "on_leave", "inactive"])
                phone    = st.text_input("رقم الهاتف")
                if st.form_submit_button("💾 حفظ", type="primary"):
                    if not name:
                        st.error("يرجى إدخال الاسم.")
                    else:
                        execute("""INSERT INTO workers (id,company_id,full_name,position,daily_wage,status,phone,joined_date)
                                   VALUES (?,?,?,?,?,?,?,?)""",
                            (str(uuid.uuid4()), cid, name, position, wage, status, phone, date.today().isoformat()))
                        st.success("✅ تمت إضافة الموظف.")
                        st.rerun()

    st.markdown('<div class="section-label">📋 قائمة الموظفين</div>', unsafe_allow_html=True)
    if workers:
        status_colors = {"active": "🟢", "on_leave": "🟡", "inactive": "🔴"}
        df = pd.DataFrame(workers)[["full_name", "position", "daily_wage", "status", "phone", "joined_date"]]
        df["status"] = df["status"].map(lambda s: f"{status_colors.get(s,'⚪')} {s}")
        df.columns = ["الاسم", "المنصب", "الأجر اليومي $", "الحالة", "الهاتف", "تاريخ الانضمام"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("لا يوجد موظفون.")


# ──────────────────────────────────────────────────────────────────────────────

def screen_machines():
    user = st.session_state["user"]
    cid  = user["company_id"]
    is_admin = user["role"] == "admin"

    st.markdown("### 🔧 MACHINES MANAGEMENT")

    machines = q("SELECT * FROM machines WHERE company_id=? ORDER BY name", (cid,))
    running     = sum(1 for m in machines if m["status"] == "running")
    idle        = sum(1 for m in machines if m["status"] == "idle")
    maintenance = sum(1 for m in machines if m["status"] == "maintenance")

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 تعمل", running)
    c2.metric("🟡 خاملة", idle)
    c3.metric("🔴 صيانة", maintenance)

    if is_admin:
        with st.expander("➕ إضافة / تعديل آلة", expanded=False):
            with st.form("machine_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                name    = col1.text_input("اسم الآلة *")
                model   = col2.text_input("الموديل")
                col3, col4 = st.columns(2)
                status  = col3.selectbox("الحالة", ["running", "idle", "maintenance"])
                hcost   = col4.number_input("التكلفة بالساعة ($)", min_value=0.0)
                col5, col6 = st.columns(2)
                location = col5.text_input("الموقع")
                last_maint = col6.date_input("آخر صيانة", value=date.today())
                notes   = st.text_area("ملاحظات", height=68)
                if st.form_submit_button("💾 حفظ", type="primary"):
                    if not name:
                        st.error("يرجى إدخال اسم الآلة.")
                    else:
                        execute("""INSERT INTO machines (id,company_id,name,model,status,hourly_cost,location,last_maintenance,notes)
                                   VALUES (?,?,?,?,?,?,?,?,?)""",
                            (str(uuid.uuid4()), cid, name, model, status, hcost,
                             location, last_maint.isoformat(), notes))
                        st.success("✅ تمت إضافة الآلة.")
                        st.rerun()

    # Update status inline
    if is_admin and machines:
        st.markdown('<div class="section-label">🔄 تحديث حالة الآلات</div>', unsafe_allow_html=True)
        for m in machines:
            col_name, col_status, col_btn = st.columns([3, 2, 1])
            col_name.write(f"**{m['name']}** — _{m['model']}_")
            new_status = col_status.selectbox("", ["running", "idle", "maintenance"],
                                               index=["running", "idle", "maintenance"].index(m["status"]),
                                               key=f"mstatus_{m['id']}", label_visibility="collapsed")
            if col_btn.button("✏️", key=f"mbtn_{m['id']}"):
                execute("UPDATE machines SET status=? WHERE id=?", (new_status, m["id"]))
                st.success(f"✅ تم تحديث حالة {m['name']}.")
                st.rerun()
    else:
        st.markdown('<div class="section-label">📋 قائمة الآلات</div>', unsafe_allow_html=True)
        if machines:
            icons = {"running": "🟢", "idle": "🟡", "maintenance": "🔴"}
            df = pd.DataFrame(machines)[["name", "model", "status", "hourly_cost", "location", "last_maintenance"]]
            df["status"] = df["status"].map(lambda s: f"{icons.get(s,'⚪')} {s}")
            df.columns = ["الاسم", "الموديل", "الحالة", "التكلفة/ساعة $", "الموقع", "آخر صيانة"]
            st.dataframe(df, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────

def screen_daily_reports():
    user = st.session_state["user"]
    cid  = user["company_id"]
    today = date.today().isoformat()

    generate_daily_report(cid, today)
    reports = q("""SELECT * FROM daily_reports WHERE company_id=?
                   ORDER BY report_date DESC LIMIT 30""", (cid,))

    st.markdown("### 📑 DAILY FINANCIAL REPORTS")

    tab1, tab2 = st.tabs(["📊 تقرير اليوم", "📅 السجل التاريخي"])

    with tab1:
        today_rep = next((r for r in reports if r["report_date"] == today), None)
        if today_rep:
            st.markdown(f"#### تقرير يوم {today_rep['report_date']}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💰 إجمالي المبيعات",      f"${today_rep['total_sales']:,.2f}")
            c2.metric("⚙️ تكلفة الإنتاج",        f"${today_rep['total_production_cost']:,.2f}")
            c3.metric("👷 أجور العمال",           f"${today_rep['worker_wages']:,.2f}")
            profit = today_rep["net_profit"]
            c4.metric("📈 صافي الربح",           f"${profit:,.2f}",
                      delta=f"{'▲' if profit >= 0 else '▼'}")

            # Cost breakdown pie
            labels = ["تكلفة الإنتاج", "أجور العمال", "صافي الربح"]
            vals   = [today_rep["total_production_cost"],
                      today_rep["worker_wages"],
                      max(today_rep["net_profit"], 0)]
            fig = go.Figure(go.Pie(
                labels=labels, values=vals, hole=0.4,
                marker_colors=["#FF9800", "#FFD600", "#00D68F"]
            ))
            fig.update_layout(paper_bgcolor="#151B2B", font_color="#E0E6F0",
                              margin=dict(l=0, r=0, t=10, b=0), height=260)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("لا توجد بيانات لهذا اليوم. سجّل مبيعات أو إنتاجاً أولاً.")

    with tab2:
        if reports:
            df = pd.DataFrame(reports)[["report_date", "total_sales", "total_production_cost",
                                        "worker_wages", "net_profit", "total_production_qty"]]
            df.columns = ["التاريخ", "المبيعات $", "تكلفة الإنتاج $", "أجور العمال $", "صافي الربح $", "كمية الإنتاج"]
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Profit trend
            df_chart = pd.DataFrame(reports)
            fig2 = go.Figure()
            fig2.add_scatter(x=df_chart["report_date"], y=df_chart["total_sales"],
                             name="مبيعات", line_color="#4FC3F7", mode="lines+markers")
            fig2.add_scatter(x=df_chart["report_date"], y=df_chart["net_profit"],
                             name="صافي الربح", line_color="#00D68F", mode="lines+markers")
            fig2.update_layout(
                template="plotly_dark", paper_bgcolor="#151B2B", plot_bgcolor="#151B2B",
                margin=dict(l=0, r=0, t=20, b=0), height=260,
                xaxis=dict(gridcolor="#1E2A3A"), yaxis=dict(gridcolor="#1E2A3A")
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("لا توجد تقارير سابقة.")


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    user = st.session_state["user"]
    with st.sidebar:
        st.markdown('<div class="brand-header" style="font-size:14px">🏭 MY INDUSTRY AI</div>',
                    unsafe_allow_html=True)
        st.caption(f"👤 {user['full_name']}  {'👑 Admin' if user['role']=='admin' else '🔧 Worker'}")
        st.caption(f"🏢 {user['company_name']}")
        st.markdown("---")

        pages = {
            "📊 لوحة التحكم":      "dashboard",
            "⚙️ الإنتاج":          "production",
            "📦 المخزون":          "stock",
            "💰 المبيعات":         "sales",
            "👷 الموظفون":         "workers",
            "🔧 الآلات":           "machines",
            "📑 التقارير اليومية": "daily_reports",
        }

        for label, key in pages.items():
            active = st.session_state.get("page") == key
            if st.button(label, use_container_width=True,
                         type="primary" if active else "secondary", key=f"nav_{key}"):
                st.session_state["page"] = key
                st.rerun()

        st.markdown("---")
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state["user"] = None
            st.rerun()

        hint = st.session_state.get("license_hint", "")
        if hint:
            st.caption(f"🔑 ترخيص: `{hint}`")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    # Init DB
    init_db()

    # Init session state
    for key, default in [
        ("licensed", False), ("trial_count", 0), ("license_hint", ""),
        ("user", None), ("page", "dashboard")
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ── Route 1: License Gate ──────────────────────────────────────────────────
    if not st.session_state["licensed"]:
        show_license_screen()
        return

    # ── Route 2: Login ─────────────────────────────────────────────────────────
    if not st.session_state["user"]:
        show_login_screen()
        return

    # ── Route 3: Main App ──────────────────────────────────────────────────────
    render_sidebar()

    page = st.session_state.get("page", "dashboard")
    screens = {
        "dashboard":    screen_dashboard,
        "production":   screen_production,
        "stock":        screen_stock,
        "sales":        screen_sales,
        "workers":      screen_workers,
        "machines":     screen_machines,
        "daily_reports": screen_daily_reports,
    }
    screens.get(page, screen_dashboard)()


if __name__ == "__main__":
    main()
