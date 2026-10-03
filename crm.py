import streamlit as st
import streamlit.components.v1 as components
import json, os, re, urllib.parse, requests, hashlib, base64, csv, io, secrets, threading, uuid
import extra_streamlit_components as stx
from datetime import datetime
from collections import defaultdict

def _safe_id(v):
    """Safely convert value to int, returning 0 for non-numeric values."""
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0



st.set_page_config(page_title="Айплинт CRM", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F5F6F8; color: #2C3E50; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif; }
    section[data-testid="stSidebar"] { background-color: #EEF0F3; border-right: 1px solid #DCE0E5; }
    .stExpander { border-radius: 14px; overflow: hidden; background-color: #FFFFFF; margin-bottom: 0.3rem !important; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
    .stExpander > details { border-radius: 14px; }
    .stExpander > details > summary { font-weight: 600; font-size: 1rem; color: #2C3E50; padding: 0.75rem 1.25rem; list-style: none; border-radius: 14px; cursor: pointer; }
    .stExpander > details > summary:hover { background-color: #F5F6F8; }
    h1, h2, h3, h4 { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif; font-weight: 700; color: #2C3E50 !important; letter-spacing: -0.02em; }
    h1 { font-size: 1.75rem; margin-bottom: 0.5rem; }
    h2 { font-size: 1.4rem; margin-top: 1rem; }
    h3 { font-size: 1.1rem; }
    hr { border: 0; height: 1px; background: #E8EBEF; margin: 1rem 0; }
    button[kind="primary"], .stButton > button[kind="primary"] { background-color: #bc1661; color: #FFFFFF; border-radius: 10px; font-weight: 600; font-size: 0.95rem; padding: 0.55rem 1.1rem; border: none; box-shadow: 0 2px 6px rgba(188,22,97,0.2); transition: all 0.15s ease; }
    button[kind="primary"]:hover { background-color: #9a1452; box-shadow: 0 3px 10px rgba(188,22,97,0.25); }
    button[kind="secondary"], .stButton > button[kind="secondary"] { background-color: transparent; color: #bc1661; border: 1px solid #C9CFD7; border-radius: 10px; font-weight: 500; font-size: 0.95rem; padding: 0.55rem 1.1rem; transition: all 0.15s ease; }
    .stButton > button { border-radius: 10px; font-weight: 500; transition: all 0.15s ease; margin-top: 0.1rem !important; margin-bottom: 0.1rem !important; }
    .stTextInput > div > input, .stTextArea > div > textarea, .stNumberInput > div > div > input { background-color: #FFFFFF !important; border-radius: 10px !important; border: 1.5px solid #DCE0E5 !important; padding: 0.55rem 0.8rem !important; color: #2C3E50 !important; font-size: 1rem; }
    .stTextInput > div > input:focus, .stTextArea > div > textarea:focus, .stNumberInput > div > div > input:focus, .stSelectbox > div > div:focus-within { outline: none; border-color: #DCE0E5 !important; box-shadow: none !important; }
    .stSelectbox > div > div { background-color: #FFFFFF; border-radius: 10px; border: 1.5px solid #DCE0E5; padding: 0.35rem 0.75rem; }
    [data-testid="stMetric"] { background-color: #FFFFFF; border-radius: 14px; padding: 1rem 1.25rem; border: 1px solid #E8EBEF; box-shadow: 0 2px 6px rgba(0,0,0,0.02); }
    [data-testid="stMetric"] label { font-size: 0.78rem; color: #7F8C9A; text-transform: uppercase; letter-spacing: 0.03em; font-weight: 600; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 1.5rem; font-weight: 700; color: #2C3E50; }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #C9CFD7; border-radius: 4px; }
    .stMarkdown p, .stMarkdown li { color: #3C4A5A; line-height: 1.6; }
    .stMarkdown strong { color: #2C3E50; font-weight: 600; }
    .stMarkdown { margin-top: 0.15rem !important; margin-bottom: 0.15rem !important; }
    code { background-color: #EEF0F3; color: #5A6B7D; border-radius: 6px; padding: 0.1rem 0.35rem; font-size: 0.9em; }
    .stHorizontalBlock .stButton button { border-radius: 12px; font-size: 0.95rem; font-weight: 600; padding: 0.65rem 1rem; }
    .stHorizontalBlock { gap: 0.4rem !important; }
    [data-testid="stFileUploader"] { border-radius: 14px; border: 2px dashed #C9CFD7; background-color: #FAFBFC; padding: 0.75rem; }
    .greeting-block { margin-bottom: 1.5rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.35rem !important; }
    .stContainer { margin-top: 0.1rem !important; margin-bottom: 0.1rem !important; }
    .phone-action-group { display: flex; align-items: center; gap: 6px; white-space: nowrap; min-height: 32px; }
    .phone-btn { background: #EEF0F3 !important; border: 1px solid #DCE0E5 !important; border-radius: 8px !important; padding: 6px 10px !important; font-size: 0.85rem !important; color: #5A6B7D !important; cursor: pointer !important; min-width: 44px !important; min-height: 32px !important; display: inline-flex; align-items: center; justify-content: center; text-decoration: none; }
    .phone-btn:hover { background: #DCE0E5 !important; }
    .payment-status-badge { padding: 4px 10px; border-radius: 99px; font-size: 0.82rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; display: inline-block; }
    .payment-status-paid { background-color: #E8F5E9; color: #2E7D32; border: 1px solid #C8E6C9; }
    .payment-status-unpaid { background-color: #FFEBEE; color: #C62828; border: 1px solid #FFCDD2; }
    .stHtml { display: none !important; }
    .custom-print-btn { width: 100%; padding: 10px; background: #bc1661; color: white; border: none; border-radius: 10px; cursor: pointer; font-size: 14px; font-weight: 600; transition: background 0.15s; }
    .custom-print-btn:hover { background: #9a1452; }
    .chat-msg { padding: 8px 12px; border-radius: 10px; margin-bottom: 6px; max-width: 80%; }
    .chat-msg-me { background-color: #bc1661; color: white; margin-left: auto; }
    .chat-msg-other { background-color: #EEF0F3; color: #2C3E50; }
    .qa-card { background: #FFFFFF; border: 1px solid #E8EBEF; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
    #crm-lightbox { position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:999999; display:none; align-items:center; justify-content:center; cursor:pointer; }
    #crm-lightbox img { max-width:90%; max-height:90%; border-radius:8px; }
    .thumb-item { position:relative; width:110px; margin: 0 auto; text-align:center; }
    .thumb-item img { width:110px; height:110px; object-fit:cover; border-radius:8px; cursor:default; border:1px solid #DCE0E5; display:block; margin:0 auto; }
    .thumb-item img:hover { border-color:#DCE0E5; }
    .thumb-name { font-size:0.7rem; color:#7F8C9A; max-width:110px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; margin-bottom:6px; text-align:center; }
    .created-date { font-size: 0.72rem; color: #95A5B7; font-style: italic; margin-bottom: 0.8rem !important; }
    .ready-badge { display: inline-block; background: #2E7D32; color: white; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 99px; margin-left: 6px; text-transform: uppercase; letter-spacing: 0.04em; }
    .in-work-badge { display: inline-block; background: #bc1661; color: white; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 99px; margin-left: 6px; text-transform: uppercase; letter-spacing: 0.04em; }
    .delegated-badge { display: inline-block; background: #E65100; color: white; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 99px; margin-left: 6px; text-transform: uppercase; letter-spacing: 0.04em; }
    .track-copy-btn { background: #EEF0F3 !important; border: 1px solid #DCE0E5 !important; border-radius: 6px !important; padding: 2px 8px !important; font-size: 0.8rem !important; color: #5A6B7D !important; cursor: pointer !important; display: inline-flex !important; align-items: center !important; }
    .track-copy-btn:hover { background: #DCE0E5 !important; }
    .stTextArea > div > textarea { resize: vertical; }
    .copy-btn-crm { background: #EEF0F3; border: 1px solid #DCE0E5; border-radius: 8px; padding: 6px 12px; font-size: 0.85rem; color: #5A6B7D; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; transition: background 0.15s; }
    .copy-btn-crm:hover { background: #DCE0E5; }
    .center-btn-wrap { max-width: 280px; margin: 0 auto; }
    .section-title { text-align: center; font-size: 1rem; font-weight: 700; color: #2C3E50; margin: 0.3rem 0; }

    .rework-badge { display: inline-block; background: #D32F2F; color: white; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 99px; margin-left: 6px; text-transform: uppercase; letter-spacing: 0.04em; }
    [data-testid="stMultiInput"] > div > div > p { display: none !important; }
    [data-testid="stMultiInput"] > div > div { background-color: #FFFFFF !important; border-radius: 10px !important; border: 1.5px solid #DCE0E5 !important; }
    .stMarkdown p, .stMarkdown li { font-size: 0.9rem; }
    .stButton > button { font-size: 0.85rem !important; }
    .stHorizontalBlock .stButton button { font-size: 0.85rem !important; }
    h3 { font-size: 1rem !important; }
    .arch-search-input > div > input { background-color: #FFFFFF !important; border: 1.5px solid #DCE0E5 !important; border-radius: 10px !important; }

    /* Sticky search bar for deals tab — JS-driven, no parent overflow changes */
    .st-key-deals_sticky_header { transition: none; }
    .deals-sticky-fixed { position: fixed !important; top: 0 !important; left: 0 !important; right: 0 !important; z-index: 9999 !important; background-color: #F5F6F8 !important; padding: 8px 1rem !important; box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important; }
    .deals-sticky-placeholder { height: 0; }
    /* Scroll-to-top button */
    #crm-scroll-top { position: fixed; bottom: 24px; right: 24px; width: 44px; height: 44px; border-radius: 50%; background: #bc1661; color: white; border: none; font-size: 20px; cursor: pointer; z-index: 999998; display: none; box-shadow: 0 2px 8px rgba(188,22,97,0.3); transition: opacity 0.2s; }
    #crm-scroll-top:hover { background: #9a1452; }
    /* Compact task detail */
    .task-detail-compact .stMarkdown { margin-top: 0.05rem !important; margin-bottom: 0.05rem !important; line-height: 1.3 !important; }
    .task-detail-compact .stMarkdown p { line-height: 1.3 !important; margin-bottom: 0.1rem !important; }
    .task-detail-compact .stButton > button { padding: 0.3rem 0.7rem !important; font-size: 0.85rem !important; min-height: 30px !important; margin-top: 0.05rem !important; margin-bottom: 0.05rem !important; }
    .task-detail-compact .stTextInput > div > input, .task-detail-compact .stTextArea > div > textarea, .task-detail-compact .stSelectbox > div > div { padding: 0.35rem 0.6rem !important; font-size: 0.9rem !important; }
    .task-detail-compact .stHorizontalBlock { gap: 0.2rem !important; }
    .task-detail-compact hr { margin: 0.3rem 0 !important; }
    .task-detail-compact .stFileUploader { padding: 0.4rem !important; }
    .task-detail-compact .stContainer { margin-top: 0.05rem !important; margin-bottom: 0.05rem !important; }
    .task-detail-compact [data-testid="stMetric"] { padding: 0.4rem 0.6rem !important; }

    /* Bell button compact */
    .crm-bell-btn button { min-width: 48px !important; font-size: 1rem !important; padding: 0.4rem 0.6rem !important; }

</style>
""", unsafe_allow_html=True)

st.components.v1.html("""
<script>
(function() {
    var w = window;
    try { if (window.parent && window.parent !== window) w = window.parent; } catch(e) {}
    w.crmOpenLightbox = function(src) {
        var doc = w.document;
        var o = doc.getElementById('crm-lightbox');
        if (!o) {
            o = doc.createElement('div');
            o.id = 'crm-lightbox';
            o.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:999999;display:none;align-items:center;justify-content:center;cursor:pointer;';
            var i = doc.createElement('img');
            i.style.cssText = 'max-width:90%;max-height:90%;border-radius:8px;';
            o.appendChild(i);
            o.onclick = function() { this.style.display = 'none'; };
            doc.body.appendChild(o);
        }
        o.querySelector('img').src = src;
        o.style.display = 'flex';
    };
    w.crmCopy = function(text, btnId) {
        var btn = document.getElementById(btnId);
        if (!btn && w.document) btn = w.document.getElementById(btnId);
        if (!btn) return;
        var oldText = btn.textContent;
        function success() { btn.textContent = '\\u2713 Скопировано'; setTimeout(function() { btn.textContent = oldText; }, 1500); }
        function fail() { btn.textContent = 'Ошибка'; setTimeout(function() { btn.textContent = oldText; }, 1500); }
        try {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text).then(success).catch(function() {
                    var ta = document.createElement('textarea');
                    ta.value = text; ta.style.position='fixed'; ta.style.left='-9999px';
                    document.body.appendChild(ta); ta.select();
                    try { document.execCommand('copy'); success(); } catch(e) { fail(); }
                    document.body.removeChild(ta);
                });
            } else {
                var ta = document.createElement('textarea');
                ta.value = text; ta.style.position='fixed'; ta.style.left='-9999px';
                document.body.appendChild(ta); ta.select();
                try { document.execCommand('copy'); success(); } catch(e) { fail(); }
                document.body.removeChild(ta);
            }
        } catch(e) { fail(); }
    };
})();

    // Scroll-to-top button
    w.crmInitScrollTop = function() {
        var doc = w.document;
        var btn = doc.getElementById('crm-scroll-top');
        if (!btn) {
            btn = doc.createElement('button');
            btn.id = 'crm-scroll-top';
            btn.innerHTML = '\u2191';
            btn.style.cssText = 'position:fixed;bottom:24px;right:24px;width:44px;height:44px;border-radius:50%;background:#bc1661;color:white;border:none;font-size:20px;cursor:pointer;z-index:999998;display:none;box-shadow:0 2px 8px rgba(188,22,97,0.3);transition:opacity 0.2s;';
            btn.onclick = function() { w.scrollTo({top:0, behavior:'smooth'}); };
            btn.addEventListener('mouseenter', function() { this.style.background = '#9a1452'; });
            btn.addEventListener('mouseleave', function() { this.style.background = '#bc1661'; });
            doc.body.appendChild(btn);
            w.addEventListener('scroll', function() {
                if (w.scrollY > 300) { btn.style.display = 'block'; }
                else { btn.style.display = 'none'; }
            });
        }
    };
    setTimeout(w.crmInitScrollTop, 500);

</script>
""", height=0)

FILE_NAME = "web_crm_database_v2.json"
YANDEX_API_URL = "https://cloud-api.yandex.net/v1/disk/resources"
MAX_URL = "https://max.ru"
MAX_NUMBER = "+79003293300"
CATEGORIES = ["Не определён", "Дизайнер", "Строитель", "Дилер", "Покупатель"]
TASK_TYPES = ["Связаться", "Отправить заказ", "Отправить образцы"]
SHIP_PAY_OPTIONS = ["", "Включено в счёт", "Клиентом при получении"]

raw_token = st.secrets.get("YANDEX_DISK_TOKEN", "")
if isinstance(raw_token, str):
    YANDEX_TOKEN = raw_token.strip().strip('"').strip("'")
else:
    YANDEX_TOKEN = ""

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_sort_key(entity):
    return entity.get("last_modified", "1970-01-01 00:00:00")

def generate_task_number(prefix):
    year = datetime.now().strftime("%y")
    max_num = 0
    for c in st.session_state.crm_store.get("clients", []):
        for t in c.get("tasks", []):
            tn = t.get("task_number", "")
            if tn.startswith(f"{prefix}{year}-"):
                try: max_num = max(max_num, int(tn.split("-")[1]))
                except: pass
    return f"{prefix}{year}-{max_num + 1}"

def generate_deal_number():
    year = datetime.now().strftime("%y")
    max_num = 0
    for d in st.session_state.crm_store.get("deals", []):
        dn = d.get("deal_number", "")
        if dn.startswith(f"Сделка №{year}-"):
            try: max_num = max(max_num, int(dn.split("-")[1]))
            except: pass
    return f"Сделка №{year}-{max_num + 1}"

def assign_task_numbers(data):
    year = datetime.now().strftime("%y")
    zk_max, zs_max = 0, 0
    for c in data.get("clients", []):
        for t in c.get("tasks", []):
            tn = t.get("task_number", "")
            if tn.startswith(f"ЗК{year}-"):
                try: zk_max = max(zk_max, int(tn.split("-")[1]))
                except: pass
            elif tn.startswith(f"ЗС{year}-"):
                try: zs_max = max(zs_max, int(tn.split("-")[1]))
                except: pass
    for c in data.get("clients", []):
        for t in c.get("tasks", []):
            if not t.get("task_number"):
                if t.get("deal_id"):
                    zs_max += 1
                    t["task_number"] = f"ЗС{year}-{zs_max}"
                else:
                    zk_max += 1
                    t["task_number"] = f"ЗК{year}-{zk_max}"

def assign_deal_numbers(data):
    year = datetime.now().strftime("%y")
    max_num = 0
    for d in data.get("deals", []):
        dn = d.get("deal_number", "")
        if dn.startswith(f"Сделка №{year}-"):
            try: max_num = max(max_num, int(dn.split("-")[1]))
            except: pass
    for d in data.get("deals", []):
        if not d.get("deal_number"):
            max_num += 1
            d["deal_number"] = f"Сделка №{year}-{max_num}"
        if d.get("title", "").startswith("Заказ"):
            d["title"] = d.get("deal_number", d["title"])

def inject_payment_container_css(deal_id, status):
    border_color = "#2E7D32" if status == "Оплачено" else "#C62828"
    bg_color = "#E8F5E9" if status == "Оплачено" else "#FFEBEE"
    st.markdown(f"<style>.st-key-ps_wrap_{deal_id} {{ border: 2px solid {border_color} !important; border-radius: 10px !important; background-color: {bg_color} !important; padding: 8px 12px !important; }}</style>", unsafe_allow_html=True)

def hash_password(pwd, salt=None):
    if salt is None: salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + pwd.strip()).encode()).hexdigest()
    return f"{salt}:{h}"

def is_hashed(s):
    if not s: return False
    if ":" in s:
        parts = s.split(":")
        return len(parts) == 2 and len(parts[0]) == 32 and len(parts[1]) == 64 and all(c in "0123456789abcdef" for c in parts[0] + parts[1])
    return len(s) == 64 and all(c in "0123456789abcdef" for c in s)

def verify_password(pwd, stored):
    if not stored: return False
    if ":" in stored:
        parts = stored.split(":")
        if len(parts) == 2 and len(parts[0]) == 32:
            salt, h = parts
            return hashlib.sha256((salt + pwd.strip()).encode()).hexdigest() == h
    if len(stored) == 64 and all(c in "0123456789abcdef" for c in stored):
        return hashlib.sha256(pwd.strip().encode()).hexdigest() == stored
    return pwd.strip() == stored

def yandex_headers():
    return {"Authorization": f"OAuth {YANDEX_TOKEN}", "Accept": "application/json"}

def check_cloud_status():
    if not YANDEX_TOKEN: return False
    try:
        return requests.get(YANDEX_API_URL, headers=yandex_headers(), timeout=5).status_code == 200
    except: return False

def init_yandex_folders():
    if not YANDEX_TOKEN: return
    for folder in ["CRM_NE_TROGAT", "CRM_NE_TROGAT/uploads"]:
        try: requests.put(YANDEX_API_URL, params={"path": f"disk:/{folder}"}, headers=yandex_headers(), timeout=10)
        except: pass

def download_db_from_yandex():
    if not YANDEX_TOKEN: return
    try:
        res = requests.get(f"{YANDEX_API_URL}/download", params={"path": f"disk:/CRM_NE_TROGAT/{FILE_NAME}"}, headers=yandex_headers(), timeout=10)
        if res.status_code == 200:
            dl = requests.get(res.json().get("href"), timeout=30)
            if dl.status_code == 200:
                with open(FILE_NAME, "w", encoding="utf-8") as f: f.write(dl.text)
                return
    except: pass
    if not os.path.exists(FILE_NAME):
        db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}], "_migrated": "v2", "internal_tasks": [], "chat_messages": [], "qa_entries": [], "suppliers": [], "notifications": []}
        with open(FILE_NAME, "w", encoding="utf-8") as f: json.dump(db, f, ensure_ascii=False, indent=2)

def upload_db_to_yandex_async():
    if not YANDEX_TOKEN or not os.path.exists(FILE_NAME): return
    def _u():
        try:
            res = requests.get(f"{YANDEX_API_URL}/upload", params={"path": f"disk:/CRM_NE_TROGAT/{FILE_NAME}", "overwrite": "true"}, headers=yandex_headers(), timeout=10)
            if res.status_code == 200:
                with open(FILE_NAME, "rb") as f: requests.put(res.json().get("href"), data=f, timeout=30)
        except: pass
    threading.Thread(target=_u, daemon=True).start()

def upload_file_to_yandex(file_bytes, remote_name):
    if not YANDEX_TOKEN: return False
    try:
        res = requests.get(f"{YANDEX_API_URL}/upload", params={"path": f"disk:/CRM_NE_TROGAT/uploads/{remote_name}", "overwrite": "true"}, headers=yandex_headers(), timeout=10)
        if res.status_code == 200: return requests.put(res.json().get("href"), data=file_bytes, timeout=30).status_code in (200, 201)
    except: pass
    return False

@st.cache_data(ttl=300, show_spinner=False)
def download_file_from_yandex(remote_path):
    if not YANDEX_TOKEN: return None
    try:
        res = requests.get(f"{YANDEX_API_URL}/download", params={"path": f"disk:/{remote_path}"}, headers=yandex_headers(), timeout=10)
        if res.status_code == 200:
            fr = requests.get(res.json().get("href"), timeout=30)
            if fr.status_code == 200: return fr.content
    except: pass
    return None

def format_phone(p_str):
    if not p_str: return ""
    d = re.sub(r"\D", "", p_str)
    if len(d) == 11 and d[0] in ("7", "8"): d = d[1:]
    if len(d) == 10: return f"+7 {d[0:3]} {d[3:6]}-{d[6:8]}-{d[8:10]}"
    return p_str.strip()

def save_uploaded_file(u_file, c_id, prefix=""):
    if u_file is None: return None
    b = u_file.getvalue()
    file_hash = hashlib.sha256(b).hexdigest()
    for c in st.session_state.crm_store.get("clients", []):
        for f in c.get("client_files", []):
            if f.get("file_hash") == file_hash and file_hash:
                return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
        for t in c.get("tasks", []):
            for f in t.get("task_files", []):
                if f.get("file_hash") == file_hash and file_hash:
                    return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
            for f in t.get("completion_files", []):
                if f.get("file_hash") == file_hash and file_hash:
                    return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
    for d in st.session_state.crm_store.get("deals", []):
        for f in d.get("deal_files", []):
            if f.get("file_hash") == file_hash and file_hash:
                return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
        for f in d.get("close_files", []):
            if f.get("file_hash") == file_hash and file_hash:
                return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
    name = f"{c_id}_{prefix}_{int(datetime.now().timestamp())}_{u_file.name}"
    if YANDEX_TOKEN:
        rp = f"CRM_NE_TROGAT/uploads/{name}"
        if upload_file_to_yandex(b, name):
            return {"path": rp, "name": u_file.name, "file_hash": file_hash}
        st.warning("Не удалось загрузить на Диск, файл сохранён локально")
    os.makedirs("uploads", exist_ok=True)
    lp = f"uploads/{name}"
    with open(lp, "wb") as f: f.write(b)
    return {"path": lp, "name": u_file.name, "file_hash": file_hash}

def save_uploaded_files(files, c_id, prefix=""):
    if files is None: return []
    if not isinstance(files, list): files = [files]
    return [fi for fi in (save_uploaded_file(f, c_id, prefix) for f in files) if fi]

def normalize_file_list(fi_list):
    return [{"file_path": fi["path"], "file_name": fi["name"], "file_hash": fi.get("file_hash", "")} for fi in fi_list]

def normalize_remote_path(fp):
    if not fp: return None
    if fp.startswith("CRM_NE_TROGAT"): return fp
    elif fp.startswith("uploads/"): return f"CRM_NE_TROGAT/{fp}"
    else: return f"CRM_NE_TROGAT/uploads/{os.path.basename(fp)}"

@st.cache_data
def get_logo_base64():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f: return base64.b64encode(f.read()).decode()
    return None

def export_clients_csv():
    o = io.StringIO()
    w = csv.writer(o, delimiter=";")
    w.writerow(["ID", "ФИО", "Телефон", "Email", "Адрес", "Категория", "Скидка %", "Ответственный"])
    for c in st.session_state.crm_store["clients"]:
        w.writerow([c["id"], c["name"], c["phone"], c.get("email", ""), c.get("address", ""), c.get("category", ""), c.get("discount", 0), c.get("manager", "")])
    return ("﻿" + o.getvalue()).encode("utf-8")

def get_client_by_id(c_id):
    for c in st.session_state.crm_store["clients"]:
        if c["id"] == c_id: return c
    return None

def get_deal_by_id(d_id):
    for d in st.session_state.crm_store.get("deals", []):
        if d["id"] == d_id: return d
    return None

def parse_deadline(ds):
    if not ds: return datetime.now().date()
    try: return datetime.strptime(ds, "%Y-%m-%d").date()
    except:
        try: return datetime.strptime(ds, "%Y-%m-%d %H:%M").date()
        except: return datetime.now().date()

def is_task_overdue(task):
    if task.get("done"): return False
    dl = task.get("deadline", "")
    if not dl: return False
    now = datetime.now()
    try:
        if len(dl) == 10: deadline = datetime.strptime(dl, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        elif len(dl) >= 16: deadline = datetime.strptime(dl[:16], "%Y-%m-%d %H:%M")
        else: return False
    except: return False
    return deadline < now

def get_task_sort_date(task):
    dl = task.get("deadline", "")
    try: return datetime.strptime(dl, "%Y-%m-%d").date()
    except:
        try: return datetime.strptime(dl, "%Y-%m-%d %H:%M").date()
        except: return datetime.max.date()

def format_date(ds):
    if not ds: return ""
    try: return datetime.strptime(ds, "%Y-%m-%d").strftime("%d.%m.%Y")
    except:
        try: return datetime.strptime(ds, "%Y-%m-%d %H:%M").strftime("%d.%m.%Y")
        except: return ds

def format_created_date(entity):
    cd = entity.get("created_at") or entity.get("last_modified", "")
    if not cd or cd == "1970-01-01 00:00:00": return ""
    try:
        dt = datetime.strptime(cd[:19], "%Y-%m-%d %H:%M:%S")
        return f'<div class="created-date">Создано: {dt.strftime("%d.%m.%Y %H:%M")}</div>'
    except:
        try:
            dt = datetime.strptime(cd[:10], "%Y-%m-%d")
            return f'<div class="created-date">Создано: {dt.strftime("%d.%m.%Y")}</div>'
        except: return ""

def get_managers_list():
    return [u.get("name", u["login"]) for u in st.session_state.crm_store.get("users", []) if u.get("role") != "admin"]

def render_copy_button(text, btn_id, label="\U0001F4CB Копировать"):
    safe_text = text.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
    st.markdown(f'<button class="copy-btn-crm" id="{btn_id}" onclick="window.crmCopy(\'{safe_text}\',\'{btn_id}\')">{label}</button>', unsafe_allow_html=True)

def render_scroll_restore(key):
    st.components.v1.html(f"""<script>(function(){{var k='crm_scroll_'+window.location.pathname;try{{var s=window.parent.sessionStorage.getItem(k);if(s){{window.parent.scrollTo(0,parseInt(s));window.parent.sessionStorage.removeItem(k);}}}}catch(e){{}}}})();</script>""", height=0)

def save_scroll_and_rerun(key=None):
    st.components.v1.html("""<script>(function(){try{window.parent.sessionStorage.setItem('crm_scroll_'+window.parent.location.pathname,window.parent.scrollY);}catch(e){}})();</script>""", height=0)
    st.rerun()

def render_phone_inline(phone, uid):
    cph = re.sub(r"\D", "", phone)
    if cph.startswith("8") and len(cph) == 11: cph = "7" + cph[1:]
    elif not cph: cph = "79990000000"
    btn_id = f"ph_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f'<div class="phone-action-group" style="padding:4px 0;"><span style="font-size:1rem;font-weight:600;color:#2C3E50;">{phone}</span><button onclick="window.crmCopy(\'{phone}\',\'{btn_id}\')" class="phone-btn" id="{btn_id}" title="Скопировать">\U0001F4CB</button><a href="tel:+{cph}" class="phone-btn" title="Позвонить">\U0001F4DE</a></div>', unsafe_allow_html=True)

def render_extra_phone_inline(phone, name, role, uid):
    cph = re.sub(r"\D", "", phone)
    if cph.startswith("8") and len(cph) == 11: cph = "7" + cph[1:]
    elif not cph: cph = "79990000000"
    info = f"{phone} — {name} ({role})" if name else phone
    btn_id = f"ep_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f'<div class="phone-action-group" style="padding:4px 0;flex-wrap:wrap;gap:8px;white-space:normal;"><span style="font-size:0.9rem;color:#3C4A5A;flex:1 1 auto;min-width:0;word-break:break-word;">{info}</span><button onclick="window.crmCopy(\'{phone}\',\'{btn_id}\')" class="phone-btn" id="{btn_id}" title="Скопировать">\U0001F4CB</button><a href="tel:+{cph}" class="phone-btn" title="Позвонить">\U0001F4DE</a></div>', unsafe_allow_html=True)

def render_track_inline(track_num, uid):
    btn_id = f"trk_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f'<div style="display:flex;align-items:center;gap:8px;"><code>{track_num}</code><button onclick="window.crmCopy(\'{track_num}\',\'{btn_id}\')" class="track-copy-btn" id="{btn_id}" title="Копировать">⎘</button></div>', unsafe_allow_html=True)

def get_file_bytes(fp):
    if fp and not fp.startswith("CRM_NE_TROGAT") and os.path.exists(fp):
        try:
            with open(fp, "rb") as f: return f.read()
        except: return None
    rp = normalize_remote_path(fp)
    return download_file_from_yandex(rp) if rp else None

def render_file_thumbs(files, prefix, allow_delete=False):
    if not files:
        st.caption("Файлов нет")
        return
    # CSS to match download button and description height with primary action buttons
    st.markdown("""<style>
    .stDownloadButton > button {
        min-height: 38px !important;
        padding: 0.55rem 1.1rem !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
    }
    </style>""", unsafe_allow_html=True)
    all_files = files
    ncols = 4
    cols = st.columns(ncols)
    for i, ff in enumerate(all_files):
        with cols[i % ncols]:
            fp = ff.get("file_path", ff.get("path"))
            fn = ff.get("file_name", ff.get("name", "файл"))
            fb = get_file_bytes(fp)
            if fb:
                ext = os.path.splitext(fn)[1].lower()
                # Show thumbnail for images
                if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                    b64 = base64.b64encode(fb).decode()
                    mt = f"image/{{'jpeg' if ext == '.jpg' else ext[1:]}}"
                    st.markdown(f'<div class="thumb-item"><img src="data:{mt};base64,{b64}" title="{fn}" /><div class="thumb-name">{fn}</div></div>', unsafe_allow_html=True)
                else:
                    # Non-image file: show icon + name
                    icon = "\U0001F4C4" if ext == ".pdf" else "\U0001F4C1"
                    st.markdown(f'<div class="thumb-item"><div style="width:110px;height:110px;display:flex;align-items:center;justify-content:center;border:1px solid #DCE0E5;border-radius:8px;font-size:2rem;color:#5A6B7D;margin:0 auto;">{icon}</div><div class="thumb-name">{fn}</div></div>', unsafe_allow_html=True)

                # Description field (editable) - multiline, auto height
                desc_key = f"fdesc_{prefix}_{i}"
                cur_desc = ff.get("description", "")
                _desc_lines = max(1, (len(cur_desc) // 40) + (1 if len(cur_desc) % 40 else 0)) if cur_desc else 1
                _desc_height = 38 + (_desc_lines - 1) * 22
                st.markdown(f"<style>.st-key-{desc_key} .stTextArea > div > textarea {{ min-height: 38px !important; height: {_desc_height}px !important; padding: 0.45rem 0.8rem !important; font-size: 0.9rem !important; border-radius: 10px !important; resize: none !important; }} .st-key-{desc_key} .stTextArea > div > textarea::placeholder {{ font-size: 0.75rem !important; }}</style>", unsafe_allow_html=True)
                new_desc = st.text_area("Описание:", value=cur_desc, key=desc_key, max_chars=200, label_visibility="collapsed", placeholder="Описание файла...", height=_desc_height)
                if new_desc != cur_desc:
                    ff["description"] = new_desc
                    if hasattr(st.session_state, 'crm_store'):
                        save_data(st.session_state.crm_store)
                # Download button
                dl_key = f"dl_{prefix}_{i}"
                st.download_button(label="\u2B07\uFE0F Скачать", data=fb, file_name=fn, key=dl_key, use_container_width=True)
                # Delete button for admin
                if allow_delete and st.session_state.user_role == "admin":
                    del_key = f"del_{prefix}_{i}"
                    st.markdown(f"<style>.st-key-{del_key} button {{ padding:2px 6px!important;font-size:0.75rem!important;min-height:24px!important; }}</style>", unsafe_allow_html=True)
                    if st.button("\U0001F5D1", key=del_key, help="Удалить"):
                        files.pop(i)
                        commit_and_rerun(st.session_state.crm_store, "Файл удалён")



def build_print_html(task, cl, tp, fd):
    def esc(s): return str(s if s else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    products_html = esc(task.get('products', '')).replace('\n', '<br>')
    oav = task.get('order_amount', 0)
    cost_html = f"<div style='margin-top:6px;font-size:16px;font-weight:bold;'>Сумма: {oav:,.0f} руб.</div>".replace(",", " ") if oav and oav > 0 else ""
    file_reminder = "<div style='color:#D65757;font-weight:bold;margin:14px 0;border:2px solid #D65757;padding:8px;border-radius:8px;'>&#9888; Не забудь распечатать вложенные файлы!</div>" if task.get("task_files") else ""
    lb = get_logo_base64()
    logo_html = f"<img src='data:image/png;base64,{lb}' width='180' style='float:left;margin-right:20px;'/>" if lb else "<div style='font-size:24px;font-weight:bold;float:left;margin-right:20px;'>АЙПЛИНТ</div>"
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><title>Бланк задачи</title><style>body {{ font-family: Arial, sans-serif; margin: 40px; color: #222; }} .header {{ text-align: center; border-bottom: 2px solid #333; padding: 10px; }} .row {{ margin: 8px 0; }} hr {{ border: none; border-top: 1px solid #ccc; margin: 14px 0; }} .sig {{ margin-top: 30px; }} .sig p {{ margin: 12px 0; }}</style></head><body><div>{logo_html}</div><div class="header"><h2>БЛАНК ЗАДАЧИ</h2><p>{datetime.now().strftime('%d.%m.%Y')}</p></div><div class="row"><b>Задача:</b> №{esc(task.get('task_number', ''))}</div><div class="row"><b>Клиент:</b> {esc(cl['name'])} ({esc(cl['phone'])})</div><div class="row"><b>Тип:</b> {esc(tp)}</div><div class="row"><b>Тема:</b> {esc(task.get('text', ''))}</div><div class="row"><b>Срок:</b> {esc(fd)}</div><div class="row"><b>Ответственный:</b> {esc(task.get('manager', ''))}</div><hr><div class="row"><b>Товары:</b><br>{products_html}</div><div class="row"><b>Адрес:</b> {esc(task.get('ship_addr', ''))}</div><div class="row"><b>Получатель:</b> {esc(task.get('receiver', ''))} ({esc(task.get('receiver_phone', ''))})</div><div class="row"><b>Оплата:</b> {esc(task.get('ship_pay', ''))}</div><div class="row"><b>Трек:</b> {esc(task.get('tk_num', ''))}</div>{cost_html}{file_reminder}<div class="sig"><p>Отпустил: _____________</p><p>Получил: _____________</p></div></body></html>"""

def render_print_button(task, cl, tp, fd, key_suffix):
    html_content = build_print_html(task, cl, tp, fd)
    html_json = json.dumps(html_content).replace('<', '\\u003c')
    safe_key = key_suffix.replace('-', '_').replace('.', '_')
    btn_id = f"print_btn_{safe_key}"
    st.markdown(f'<button class="custom-print-btn" id="{btn_id}" style="width:auto;padding:4px 12px;font-size:0.85rem;">\U0001F5A8\uFE0F</button>', unsafe_allow_html=True)
    st.components.v1.html(f"""<script>(function() {{ var btn = window.parent.document.getElementById('{btn_id}'); if (!btn) return; var html = {html_json}; btn.addEventListener('click', function() {{ var w = window.open('', '_blank'); if (!w) {{ alert('Разрешите всплывающие окна'); return; }} w.document.open(); w.document.write(html); w.document.close(); w.focus(); setTimeout(function() {{ try {{ w.print(); }} catch(e) {{}} }}, 500); w.onafterprint = function() {{ setTimeout(function() {{ w.close(); }}, 300); }}; }}); }})();</script>""", height=0)

def render_print_file_button(files, key_suffix):
    if not files: return
    printable = [f for f in files if os.path.splitext(f.get("file_name", f.get("name", "")))[1].lower() in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf"]]
    for i, ff in enumerate(printable):
        fp = ff.get("file_path", ff.get("path"))
        fn = ff.get("file_name", ff.get("name", "файл"))
        fb = get_file_bytes(fp)
        if fb:
            ext = os.path.splitext(fn)[1].lower()
            btn_id = f"printfile_{key_suffix}_{i}"
            b64 = base64.b64encode(fb).decode()
            if ext == ".pdf":
                st.markdown(f'<button class="custom-print-btn" id="{btn_id}" style="background:#5A6B7D;margin-top:4px;">\U0001F5A8️ {fn}</button>', unsafe_allow_html=True)
                st.components.v1.html(f"""<script>(function(){{var b=window.parent.document.getElementById('{btn_id}');if(!b)return;b.addEventListener('click',function(){{var w=window.open('','_blank');if(!w)return;w.document.open();w.document.write('<html><head><title>{fn}</title></head><body style="margin:0"><iframe src="data:application/pdf;base64,{b64}" style="width:100vw;height:100vh;border:0" onload="setTimeout(function(){{try{{window.print()}}catch(e){{}}}},300)"></iframe></body></html>');w.document.close();}});}})();</script>""", height=0)
            else:
                mt = f"image/{'jpeg' if ext == '.jpg' else ext[1:]}"
                st.markdown(f'<button class="custom-print-btn" id="{btn_id}" style="background:#5A6B7D;margin-top:4px;">\U0001F5A8️ {fn}</button>', unsafe_allow_html=True)
                st.components.v1.html(f"""<script>(function(){{var b=window.parent.document.getElementById('{btn_id}');if(!b)return;b.addEventListener('click',function(){{var w=window.open('','_blank');if(!w)return;w.document.open();w.document.write('<html><head><title>{fn}</title></head><body style="margin:0;text-align:center"><img src="data:{mt};base64,{b64}" style="max-width:100%;max-height:100%" onload="setTimeout(function(){{try{{window.print()}}catch(e){{}}}},300)"/></body></html>');w.document.close();}});}})();</script>""", height=0)

def render_entity_chat(entity, entity_type, entity_id):
    chat_key = f"{entity_type}_chat"
    if chat_key not in entity: entity[chat_key] = []
    chat = entity[chat_key]
    st.markdown("**Чат:**")
    chat_container = st.container(height=200)
    with chat_container:
        for msg in chat[-50:]:
            is_me = msg.get("user") == st.session_state.get("user_name", "")
            cls = "chat-msg-me" if is_me else "chat-msg-other"
            st.markdown(f'<div class="chat-msg {cls}"><div style="font-size:0.75rem;opacity:0.7;margin-bottom:2px;">{msg.get("user","")} — {msg.get("time","")}</div>{msg.get("text","")}</div>', unsafe_allow_html=True)
        if not chat: st.caption("Сообщений нет")
    clr_key = f"clr_{entity_type}_{entity_id}"
    if st.session_state.get(clr_key):
        st.session_state[f"{entity_type}_msg_{entity_id}"] = ""
        st.session_state[clr_key] = False
    msg_text = st.text_input("Сообщение:", key=f"{entity_type}_msg_{entity_id}", placeholder="Введите сообщение...", label_visibility="collapsed")
    if st.button("Отправить", key=f"{entity_type}_send_{entity_id}", use_container_width=True):
        if msg_text.strip():
            chat.append({"user": st.session_state.get("user_name", ""), "text": msg_text.strip(), "time": datetime.now().strftime("%d.%m.%Y %H:%M")})
            st.session_state[clr_key] = True
            entity["last_modified"] = now_str()
            commit_and_rerun(st.session_state.crm_store)
        else: st.warning("Введите текст")

def render_task_detail(t, cl, d, key_prefix):
    with st.container(border=True, key=f"task_detail_{key_prefix}"):
        st.markdown(f'<style>.st-key-task_detail_{key_prefix} {{ padding: 0.5rem !important; }} .st-key-task_detail_{key_prefix} .stVerticalBlock {{ gap: 0.15rem !important; }}</style>', unsafe_allow_html=True)
        # CSS to align print and edit buttons
        st.markdown(f"""<style>
        .st-key-task_detail_{key_prefix} .stHorizontalBlock .stButton button,
        .st-key-task_detail_{key_prefix} .stHorizontalBlock .stMarkdown button {{
            min-height: 32px !important;
            padding: 4px 10px !important;
            font-size: 0.85rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        .st-key-task_detail_{key_prefix} .stHorizontalBlock .stMarkdown {{
            margin-top: 0 !important;
            display: flex !important;
            align-items: center !important;
        }}
        /* Remove top gap in right column */
        .st-key-task_detail_{key_prefix} > div > div:nth-child(2) > div > div:first-child {{
            margin-top: 0 !important;
            padding-top: 0 !important;
        }}
        .st-key-task_detail_{key_prefix} > div > div:nth-child(2) {{
            margin-top: 0 !important;
            padding-top: 0 !important;
        }}
        </style>""", unsafe_allow_html=True)
        # Two columns: left = everything, right = comments + files
        left_col, right_col = st.columns(2)
        with left_col:
            _task_header = f"\u0417\u0430\u0434\u0430\u0447\u0430 \u043f\u043e \u0441\u0434\u0435\u043b\u043a\u0435 \u2116{t.get('task_number', '')}" if d else f"\u0417\u0430\u0434\u0430\u0447\u0430 \u2116{t.get('task_number', '')}"
            _tp = t.get('type', '\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f')
            _fd = format_date(t.get('deadline', ''))
            if d:
                _deal_num = d.get('deal_number', d.get('title', ''))
                _deal_id = d.get('id')
                _deal_link_key = f"deal_link_{key_prefix}"
                _hdr_inner, _print_inner = st.columns([14, 1])
                with _hdr_inner:
                    st.subheader(_task_header)
                    if st.button(f"{_deal_num}", key=_deal_link_key, help="\u041f\u0435\u0440\u0435\u0439\u0442\u0438 \u043a \u0441\u0434\u0435\u043b\u043a\u0435", type="secondary"):
                        st.session_state.active_tab = "Сделки"
                        st.session_state["deal_tab_expanded"] = _deal_id
                        st.session_state.pop("dialog_task_key", None)
                        st.rerun()
                with _print_inner:
                    render_print_button(t, cl, _tp, _fd, f"td_{key_prefix}")
            else:
                _hdr_inner, _print_inner = st.columns([14, 1])
                with _hdr_inner:
                    st.subheader(_task_header)
                with _print_inner:
                    render_print_button(t, cl, _tp, _fd, f"td_{key_prefix}")
            st.markdown(format_created_date(t), unsafe_allow_html=True)
            show_edit_task = st.session_state.get(f"show_edit_task_{key_prefix}", False)
            if show_edit_task:
                # Inline editing mode
                et_topic = st.text_input("\u0422\u0435\u043c\u0430:", value=t.get("text", ""), key=f"edit_topic_{key_prefix}")
                et_type = st.selectbox("\u0422\u0438\u043f:", TASK_TYPES, index=TASK_TYPES.index(t.get("type", "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f")) if t.get("type", "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f") in TASK_TYPES else 0, key=f"edit_type_{key_prefix}")
                et_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", get_managers_list(), index=0 if t.get("manager", "") not in get_managers_list() else (get_managers_list()).index(t.get("manager", "")), key=f"edit_mgr_{key_prefix}", placeholder=MGR_PLACEHOLDER)
                et_comment = st.text_area("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438:", value=t.get("task_comment", ""), key=f"edit_comment_{key_prefix}")
                if et_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b"):
                    et_products = st.text_area("\u0422\u043e\u0432\u0430\u0440\u044b:", value=t.get("products", ""), key=f"edit_prod_{key_prefix}")
                    et_addr = st.text_area("\u0410\u0434\u0440\u0435\u0441 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438:", value=t.get("ship_addr", ""), key=f"edit_addr_{key_prefix}")
                    et_recv = st.text_input("\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:", value=t.get("receiver", ""), key=f"edit_recv_{key_prefix}")
                    et_rphone = st.text_input("\u0422\u0435\u043b\u0435\u0444\u043e\u043d \u043f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044f:", value=t.get("receiver_phone", ""), key=f"edit_rphone_{key_prefix}")
                    et_pay = st.selectbox("\u041e\u043f\u043b\u0430\u0442\u0430:", SHIP_PAY_OPTIONS, index=SHIP_PAY_OPTIONS.index(t.get("ship_pay", "")) if t.get("ship_pay", "") in SHIP_PAY_OPTIONS else 0, key=f"edit_pay_{key_prefix}", placeholder="\u0423\u043a\u0430\u0436\u0438 \u043f\u043b\u0430\u0442\u0435\u043b\u044c\u0449\u0438\u043a\u0430")
                    et_amount = st.text_input("\u0421\u0443\u043c\u043c\u0430 \u0437\u0430\u043a\u0430\u0437\u0430 (\u0440\u0443\u0431.):", value=str(t.get("order_amount", 0)) if t.get("order_amount", 0) > 0 else "", key=f"edit_amount_{key_prefix}", placeholder="\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u0443\u043c\u043c\u0443")
                    et_tk = st.text_input("\u0422\u0440\u0435\u043a:", value=t.get("tk_num", ""), key=f"edit_tk_{key_prefix}")
                else:
                    et_products = t.get("products", "")
                    et_addr = t.get("ship_addr", "")
                    et_recv = t.get("receiver", "")
                    et_rphone = t.get("receiver_phone", "")
                    et_pay = t.get("ship_pay", "")
                    et_amount = str(t.get("order_amount", 0)) if t.get("order_amount", 0) > 0 else ""
                    et_tk = t.get("tk_num", "")
                _save_col, _cancel_col = st.columns(2)
                with _save_col:
                    if st.button("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", key=f"edit_save_{key_prefix}", use_container_width=True, type="primary"):
                        if not et_mgr:
                            st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0433\u043e")
                        else:
                            t["text"] = et_topic
                            t["type"] = et_type
                            t["manager"] = et_mgr
                            t["task_comment"] = et_comment
                            t["products"] = et_products
                            t["ship_addr"] = et_addr
                            t["receiver"] = et_recv
                            t["receiver_phone"] = et_rphone
                            t["ship_pay"] = et_pay
                            t["order_amount"] = int(et_amount) if et_amount and et_amount.strip().isdigit() else 0
                            t["tk_num"] = et_tk
                            t["last_modified"] = now_str()
                            cl["last_modified"] = now_str()
                            if d: d["last_modified"] = now_str()
                            st.session_state[f"show_edit_task_{key_prefix}"] = False
                            commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0430")
                with _cancel_col:
                    if st.button("\u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c", key=f"edit_cancel_{key_prefix}", use_container_width=True):
                        st.session_state[f"show_edit_task_{key_prefix}"] = False
                        st.rerun()
            else:
                # Display mode
                st.markdown(f"**\u0422\u0435\u043c\u0430:** {t.get('text', '')}")
                st.markdown(f"**\u0422\u0438\u043f:** {t.get('type', '\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f')}")
                # Deadline: clickable date, no pencil button
                show_edit_dl = st.session_state.get(f"show_edit_dl_{key_prefix}", False)
                if show_edit_dl:
                    ndd = st.date_input("\u0421\u0440\u043e\u043a:", value=parse_deadline(t.get("deadline", "")), format="DD.MM.YYYY", key=f"dl_inline_{key_prefix}")
                    dl_btn_col1, dl_btn_col2 = st.columns(2)
                    with dl_btn_col1:
                        if st.button("\u041e\u043a", key=f"dl_ok_{key_prefix}", use_container_width=True, type="primary"):
                            t["deadline"] = ndd.isoformat()
                            t["last_modified"] = now_str()
                            cl["last_modified"] = now_str()
                            if d: d["last_modified"] = now_str()
                            st.session_state[f"show_edit_dl_{key_prefix}"] = False
                            commit_and_rerun(st.session_state.crm_store, "\u0421\u0440\u043e\u043a \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d")
                    with dl_btn_col2:
                        if st.button("\u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c", key=f"dl_cancel_{key_prefix}", use_container_width=True):
                            st.session_state[f"show_edit_dl_{key_prefix}"] = False
                            st.rerun()
                else:
                    dl_btn_key = f"btn_dl_click_{key_prefix}"
                    st.markdown(f"<style>.st-key-{dl_btn_key} button {{ background:none!important;border:none!important;color:#2C3E50!important;font-weight:600!important;font-size:1rem!important;padding:0!important;text-align:left!important; }}</style>", unsafe_allow_html=True)
                    if st.button(f"\u0421\u0440\u043e\u043a: {format_date(t.get('deadline', ''))}", key=dl_btn_key, help="\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u0447\u0442\u043e\u0431\u044b \u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0441\u0440\u043e\u043a"):
                        st.session_state[f"show_edit_dl_{key_prefix}"] = True
                        st.rerun()
                # Editable responsible person (replaces delegate button)
                st.markdown("**\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:**")
                mgr_options = get_managers_list()
                current_mgr = t.get("manager", "")
                current_idx = mgr_options.index(current_mgr) if current_mgr in mgr_options else 0
                new_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", mgr_options, index=current_idx, key=f"task_mgr_inline_{key_prefix}", placeholder=MGR_PLACEHOLDER, label_visibility="collapsed")
                if new_mgr != current_mgr and new_mgr:
                    t["manager"] = new_mgr
                    t["delegated_to"] = new_mgr
                    t["last_modified"] = now_str()
                    cl["last_modified"] = now_str()
                    if d: d["last_modified"] = now_str()
                    commit_and_rerun(st.session_state.crm_store, "\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d")
                if t.get('in_work') and not t.get('done'):
                    st.markdown('<span class="in-work-badge">\u0412 \u0440\u0430\u0431\u043e\u0442\u0435</span>', unsafe_allow_html=True)
                st.markdown("---")
                if t.get('products'): st.markdown(f"**\u0422\u043e\u0432\u0430\u0440\u044b:** {t['products']}")
                if t.get('ship_addr'): st.markdown(f"**\u0410\u0434\u0440\u0435\u0441:** {t['ship_addr']}")
                if t.get('receiver'): st.markdown(f"**\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:** {t['receiver']} ({t.get('receiver_phone', '')})")
                if t.get('ship_pay'): st.markdown(f"**\u041e\u043f\u043b\u0430\u0442\u0430:** {t['ship_pay']}")
                if t.get('tk_num'):
                    st.markdown(f"**\u0422\u0440\u0435\u043a:** `{t['tk_num']}`")
                if t.get('order_amount', 0) > 0: st.markdown(f"**\u0421\u0443\u043c\u043c\u0430:** {t['order_amount']:,.0f} \u0440\u0443\u0431.".replace(",", " "))
                if t.get('ready_to_ship'): st.markdown('<span class="ready-badge">\u0413\u043e\u0442\u043e\u0432\u043e \u043a \u043e\u0442\u043f\u0440\u0430\u0432\u043a\u0435</span>', unsafe_allow_html=True)
                if t.get('task_comment'): st.markdown(f"**\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438:** {t['task_comment']}")
                # Edit pencil button — same compact size, left-aligned, above action buttons
                pencil_key = f"btn_pencil_edit_{key_prefix}"
                st.markdown(f"<style>.st-key-{pencil_key} button {{ padding: 2px 8px !important; font-size: 0.85rem !important; min-height: 32px !important; }}</style>", unsafe_allow_html=True)
                if st.button("\u270e", key=pencil_key, help="\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c"):
                    st.session_state[f"show_edit_task_{key_prefix}"] = True
                    st.rerun()
                # Action buttons in left column (below task info)
                st.markdown("---")
                tk_done = t.get("done", False)
                if not tk_done:
                    if not t.get("in_work") and not t.get("needs_rework"):
                        if st.button("Взять в работу", key=f"btn_take_work_{key_prefix}", type="primary", use_container_width=True):
                            t["in_work"] = True
                            t["last_modified"] = now_str()
                            cl["last_modified"] = now_str()
                            if d: d["last_modified"] = now_str()
                            commit_and_rerun(st.session_state.crm_store, "Задача взята в работу")
                    show_key = f"show_complete_{key_prefix}"
                    if st.button("\u0412\u044b\u043f\u043e\u043b\u043d\u0438\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443", key=f"btn_complete_{key_prefix}", type="primary", use_container_width=True):
                        st.session_state[show_key] = not st.session_state.get(show_key, False)
                    if st.session_state.get(show_key, False):
                        rt = st.text_area("\u041e\u0442\u0447\u0435\u0442 (\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e):", key=f"rt_{key_prefix}", height=100)
                        uf_ver = st.session_state.get(f"uf_ver_{key_prefix}", 0)
                        uf = st.file_uploader("\u0424\u0430\u0439\u043b\u044b/\u0444\u043e\u0442\u043e \u043e\u0442\u0447\u0435\u0442\u0430:", key=f"uf_{key_prefix}_{uf_ver}", accept_multiple_files=True)
                        create_new_task = st.checkbox("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u043d\u043e\u0432\u0443\u044e \u0437\u0430\u0434\u0430\u0447\u0443 \u043f\u043e \u0441\u0434\u0435\u043b\u043a\u0435", key=f"cnt_{key_prefix}")
                        if create_new_task:
                            with st.container(border=True):
                                nt_topic2 = st.text_input("\u0422\u0435\u043c\u0430:", key=f"cnt_topic_{key_prefix}")
                                nt_mgr2 = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", get_managers_list(), index=0, key=f"cnt_mgr_{key_prefix}", placeholder=MGR_PLACEHOLDER)
                                nt_dl2 = st.date_input("\u0421\u0440\u043e\u043a:", format="DD.MM.YYYY", key=f"cnt_dl_{key_prefix}")
                                nt_comment2 = st.text_input("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:", key=f"cnt_comment_{key_prefix}")
                                nt_files2 = st.file_uploader("\u0424\u0430\u0439\u043b\u044b:", key=f"cnt_files_{key_prefix}", accept_multiple_files=True)
                        pc1, pc2 = st.columns(2)
                        with pc1:
                            if st.button("\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c", key=f"go_{key_prefix}", use_container_width=True, type="primary"):
                                if rt.strip():
                                    t["done"] = True
                                    t["completion_report"] = rt.strip()
                                    t["last_modified"] = now_str()
                                    add_notification(t.get("created_by", ""), f"\u0417\u0430\u0434\u0430\u0447\u0430 \u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0435: {t.get('task_number','')} \u2014 {cl.get('name','')} | \u0412\u044b\u043f\u043e\u043b\u043d\u0438\u043b: {st.session_state.get('user_name','')}", f"\u2705 \u0417\u0430\u0434\u0430\u0447\u0430 \u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0435: {t.get('task_number','')} \u2014 {cl.get('name','')} | \u0412\u044b\u043f\u043e\u043b\u043d\u0438\u043b: {st.session_state.get('user_name','')}")
                                    fi_list = save_uploaded_files(uf, (d["client_id"] if d else cl["id"]), "task_report")
                                    if fi_list: t["completion_files"] = normalize_file_list(fi_list)
                                    cl["last_modified"] = now_str()
                                    if d: d["last_modified"] = now_str()
                                    st.session_state[show_key] = False
                                    # Create new task if checkbox was checked
                                    if create_new_task and nt_topic2.strip():
                                        ntfi_list2 = save_uploaded_files(nt_files2, (d["client_id"] if d else cl["id"]), "task_file") if nt_files2 else []
                                        prefix2 = "\u0417\u0421" if d else "\u0417\u041a"
                                        tn2 = generate_task_number(prefix2)
                                        new_task = {
                                            "text": nt_topic2.strip(), "deadline": nt_dl2.isoformat(), "done": False, "type": "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f",
                                            "task_files": normalize_file_list(ntfi_list2), "manager": nt_mgr2,
                                            "completion_report": "", "completion_files": [],
                                            "deal_id": (d["id"] if d else None), "task_comment": nt_comment2.strip(),
                                            "order_amount": 0, "last_modified": now_str(),
                                            "task_number": tn2, "created_at": now_str(), "created_by": st.session_state.get("user_login", ""),
                                            "in_work": False, "ready_to_ship": False, "delegated_to": None, "needs_rework": False, "reviewed": False,
                                            "task_comments": [], "flagged": False,
                                            "products": "", "ship_addr": "", "receiver": "", "receiver_phone": "", "ship_pay": "", "tk_num": ""
                                        }
                                        cl.setdefault("tasks", []).append(new_task)
                                        add_notification(nt_mgr2, f"\u041d\u043e\u0432\u0430\u044f \u0437\u0430\u0434\u0430\u0447\u0430: {nt_topic2.strip()} | \u041a\u043b\u0438\u0435\u043d\u0442: {cl.get('name','')} | \u0421\u0440\u043e\u043a: {nt_dl2.isoformat()}", f"\U0001F4DD \u041d\u043e\u0432\u0430\u044f \u0437\u0430\u0434\u0430\u0447\u0430: {nt_topic2.strip()} | \u041a\u043b\u0438\u0435\u043d\u0442: {cl.get('name','')} | \u0421\u0440\u043e\u043a: {nt_dl2.isoformat()}")
                                    st.session_state[f"uf_ver_{key_prefix}"] = uf_ver + 1
                                    commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u0430")
                                else: st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043e\u0442\u0447\u0435\u0442")
                        with pc2:
                            if st.button("\u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c", key=f"cancel_complete_{key_prefix}", use_container_width=True):
                                st.session_state[show_key] = False
                else:
                    if t.get("needs_rework"):
                        st.markdown('<span class="reworkbadge" style="display:inline-block;background:#D32F2F;color:white;font-size:0.7rem;font-weight:700;padding:2px 8px;border-radius:99px;text-transform:uppercase;">\u041d\u0430 \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0435</span>', unsafe_allow_html=True)
                    if t.get("completion_report"): st.caption(f"\u041e\u0442\u0447\u0435\u0442: {t['completion_report']}")
                    if t.get("rework_comment"): st.warning(f"\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439 \u043a \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0435: {t['rework_comment']}")
                    if t.get("completion_files"):
                        st.markdown("**\u0424\u0430\u0439\u043b\u044b \u043e\u0442\u0447\u0435\u0442\u0430:**")
                        render_file_thumbs(t["completion_files"], f"{key_prefix}_cfiles")
                    if not t.get("reviewed", False):
                        is_author = (st.session_state.user_role == "admin") or (t.get("created_by", "") == st.session_state.get("user_login", ""))
                        if is_author:
                            st.markdown("---")
                            rc1, rc2 = st.columns(2)
                            with rc1:
                                if st.button("\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u0430", key=f"btn_review_{key_prefix}", type="primary", use_container_width=True):
                                    t["reviewed"] = True
                                    t["needs_rework"] = False
                                    t["rework_comment"] = ""
                                    t["last_modified"] = now_str()
                                    cl["last_modified"] = now_str()
                                    if d: d["last_modified"] = now_str()
                                    commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u0435\u043d\u0430 \u0438 \u0432 \u0430\u0440\u0445\u0438\u0432\u0435")
                            with rc2:
                                if st.button("\u0412\u0435\u0440\u043d\u0443\u0442\u044c \u0432 \u0440\u0430\u0431\u043e\u0442\u0443", key=f"btn_rework_{key_prefix}", use_container_width=True):
                                    st.session_state[f"show_rework_{key_prefix}"] = True
                                    st.rerun()
                            if st.session_state.get(f"show_rework_{key_prefix}", False):
                                rework_comment = st.text_area("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439 \u043a \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0435 (\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e):", key=f"rework_comment_{key_prefix}", height=100, placeholder="\u041e\u043f\u0438\u0448\u0438\u0442\u0435, \u0447\u0442\u043e \u043d\u0443\u0436\u043d\u043e \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u0430\u0442\u044c")
                                rw1, rw2 = st.columns(2)
                                with rw1:
                                    if st.button("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043d\u0430 \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0443", key=f"btn_rework_send_{key_prefix}", type="primary", use_container_width=True):
                                        if not rework_comment.strip():
                                            st.warning("\u041d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439 \u2014 \u0431\u0435\u0437 \u043d\u0435\u0433\u043e \u043d\u0435\u043b\u044c\u0437\u044f \u043e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443 \u043d\u0430 \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0443")
                                        else:
                                            t["done"] = False
                                            t["in_work"] = False
                                            t["needs_rework"] = True
                                            t["rework_comment"] = rework_comment.strip()
                                            t.setdefault("task_comments", []).append({"author": st.session_state.get("user_login", ""), "text": rework_comment.strip(), "date": now_str()})
                                            t["last_modified"] = now_str()
                                            cl["last_modified"] = now_str()
                                            if d: d["last_modified"] = now_str()
                                            st.session_state[f"show_rework_{key_prefix}"] = False
                                            add_notification(t.get("manager", ""), f"\u0417\u0430\u0434\u0430\u0447\u0430 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0435\u043d\u0430 \u043d\u0430 \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0443: {t.get('task_number','')} \u2014 {cl.get('name','')} | \u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439: {rework_comment.strip()}", f"\u26a0\ufe0f \u0417\u0430\u0434\u0430\u0447\u0430 \u043d\u0430 \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0443: {t.get('task_number','')} \u2014 {cl.get('name','')} | \u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439: {rework_comment.strip()}")
                                            commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0435\u043d\u0430 \u043d\u0430 \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0443")
                                with rw2:
                                    if st.button("\u041e\u0442\u043c\u0435\u043d\u0430", key=f"btn_rework_cancel_{key_prefix}", use_container_width=True):
                                        st.session_state[f"show_rework_{key_prefix}"] = False
                                        st.rerun()
                        else:
                            st.info("\u041e\u0436\u0438\u0434\u0430\u0435\u0442 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0438 \u0430\u0432\u0442\u043e\u0440\u043e\u043c")
                    else:
                        st.success("\u0417\u0430\u0434\u0430\u0447\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u0435\u043d\u0430")
        with right_col:
            # Comments block (now above files) — no gap at top
            if t.get("task_comments"):
                st.markdown("**\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438 \u0437\u0430\u0434\u0430\u0447\u0438:**")
                for tc in t["task_comments"]:
                    st.markdown(f"- *{tc.get('time', '')}* ({tc.get('user', '')}): {tc.get('text', '')}")
            tc_clr_key = f"clr_tc_{key_prefix}"
            if st.session_state.get(tc_clr_key):
                st.session_state[f"tc_input_{key_prefix}"] = ""
                st.session_state[tc_clr_key] = False
            ntc = st.text_input("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:", key=f"tc_input_{key_prefix}", placeholder="\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439...")
            if st.button("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c", key=f"tc_btn_{key_prefix}", use_container_width=True):
                if ntc.strip():
                    t.setdefault("task_comments", []).append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": ntc.strip(), "user": st.session_state.get("user_name", "")})
                    t["last_modified"] = now_str()
                    st.session_state[tc_clr_key] = True
                    commit_and_rerun(st.session_state.crm_store, "\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d")
                else: st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0442\u0435\u043a\u0441\u0442")
            st.markdown("---")
            # Files block (now below comments)
            if t.get("task_files"):
                st.markdown("**\u0424\u0430\u0439\u043b\u044b \u0437\u0430\u0434\u0430\u0447\u0438:**")
                render_file_thumbs(t["task_files"], f"{key_prefix}_files")
            st.markdown("**\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0444\u0430\u0439\u043b\u044b \u0432 \u0437\u0430\u0434\u0430\u0447\u0443:**")
            _tu_ver = st.session_state.get(f"task_upload_ver_{key_prefix}", 0)
            ntf_existing = st.file_uploader("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0444\u0430\u0439\u043b\u044b:", key=f"task_upload_{key_prefix}_{_tu_ver}", accept_multiple_files=True, label_visibility="collapsed")
            if st.button("\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c", key=f"task_upload_btn_{key_prefix}", use_container_width=True):
                if ntf_existing:
                    with st.spinner("\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0444\u0430\u0439\u043b\u043e\u0432..."):
                        fi_list = save_uploaded_files(ntf_existing, (d["client_id"] if d else cl["id"]), "task_file")
                    if fi_list:
                        t.setdefault("task_files", []).extend(normalize_file_list(fi_list))
                        t["last_modified"] = now_str()
                        cl["last_modified"] = now_str()
                        if d: d["last_modified"] = now_str()
                        st.session_state[f"task_upload_ver_{key_prefix}"] = _tu_ver + 1
                        commit_and_rerun(st.session_state.crm_store, "\u0424\u0430\u0439\u043b\u044b \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u044b")
                else: st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0444\u0430\u0439\u043b(\u044b)")

def render_task_row(t, cl, d, task_key, key_prefix):
    is_tk_exp = st.session_state.expanded_task_key == task_key
    tk_done = t.get("done", False)
    tk_overdue = is_task_overdue(t)
    tk_rework = t.get("needs_rework", False)
    if tk_done and not t.get("reviewed", False): tk_bg, tk_bc = "#FFF8E1", "#FF8F00"
    elif tk_done: tk_bg, tk_bc = "#F5F6F8", "#C9CFD7"
    elif tk_rework: tk_bg, tk_bc = "#FFEBEE", "#D32F2F"
    elif tk_overdue: tk_bg, tk_bc = "#FFEBEE", "#C62828"
    elif t.get("in_work"): tk_bg, tk_bc = "#E8F5E9", "#4CAF50"
    else: tk_bg, tk_bc = "#E3F2FD", "#2196F3"
    tk_label = f"Задача №{t.get('task_number', '')} — {t.get('text', '')} | {format_date(t.get('deadline', ''))}"
    if tk_rework and not tk_done: tk_label += ' | На доработке'
    if t.get('in_work') and not tk_done and not tk_rework: tk_label += ' | В работе'
    if t.get('ready_to_ship') and not tk_done: tk_label += ' | Готово к отправке'
    if tk_done and not t.get("reviewed", False): tk_label += ' | На проверке'
    tk_selected = is_tk_exp
    tk_border = "#2196F3" if tk_selected else tk_bc
    tk_shadow = "box-shadow: 0 0 0 2px rgba(33,150,243,0.3);" if tk_selected else ""
    st.markdown(f"<style>.st-key-tk_btn_wrap_{task_key} button {{ background-color: {tk_bg} !important; color: #2C3E50 !important; border: 2px solid {tk_border} !important; border-radius: 10px !important; {tk_shadow} }}</style>", unsafe_allow_html=True)
    with st.container(key=f"tk_btn_wrap_{task_key}"):
        if st.button(tk_label, key=f"tk_card_{task_key}", use_container_width=True, type="primary" if is_tk_exp else "secondary"):
            if is_tk_exp:
                st.session_state.expanded_task_key = None
                save_scroll_and_rerun()
            else:
                st.session_state.expanded_task_key = task_key
                st.rerun()
        if not is_tk_exp:
            render_scroll_restore(f"tk_{task_key}")
    if is_tk_exp: render_task_detail(t, cl, d, key_prefix)

def get_entity_border(tasks_list):
    has_overdue = any(not t.get("done") and is_task_overdue(t) for t in tasks_list)
    has_active = any(not t.get("done") for t in tasks_list)
    if has_overdue: return "#FFEBEE", "#C62828"
    elif has_active: return "#E8F5E9", "#4CAF50"
    else: return "#FFFFFF", "#DCE0E5"

def indented(margin=0.03):
    if margin <= 0:
        return st.container()
    cols = st.columns([margin, 1 - margin], gap="small")
    return cols[1]

def render_separator():
    st.markdown('<hr style="border:0;height:1px;background:#DCE0E5;margin:0.8rem 0;">', unsafe_allow_html=True)

def render_centered_title(title):
    st.markdown(f'<p class="section-title">{title}</p>', unsafe_allow_html=True)

def render_centered_button(label, key=None, btn_type="primary"):
    lbl_hash = hashlib.md5(label.encode()).hexdigest()[:6]
    btn_key = f"cb_{lbl_hash}_{key}" if key else f"cb_{lbl_hash}"
    cl1, cl2, cl3 = st.columns([1, 2, 1], gap="small")
    with cl2:
        if st.button(label, key=btn_key, type=btn_type, use_container_width=True):
            return True
    return False

def migrate_task_files(t):
    if "task_files" not in t:
        t["task_files"] = []
        if t.get("file_path"): t["task_files"].append({"file_path": t["file_path"], "file_name": t.get("file_name", "файл"), "file_hash": ""})
    if "completion_files" not in t:
        t["completion_files"] = []
        if t.get("completion_file_path"): t["completion_files"].append({"file_path": t["completion_file_path"], "file_name": t.get("completion_file_name", "файл"), "file_hash": ""})
    if "task_comments" not in t: t["task_comments"] = []
    if "in_work" not in t: t["in_work"] = False
    if "needs_rework" not in t: t["needs_rework"] = False
    if "reviewed" not in t: t["reviewed"] = False
    if "rework_comment" not in t: t["rework_comment"] = ""
    if "created_by" not in t: t["created_by"] = ""
    if "ready_to_ship" not in t: t["ready_to_ship"] = False
    if "delegated_to" not in t: t["delegated_to"] = None
    if "created_at" not in t: t["created_at"] = t.get("last_modified", "")
    if "flagged" not in t: t["flagged"] = False
    if "needs_rework" not in t: t["needs_rework"] = False
    if "reviewed" not in t: t["reviewed"] = False
    if "type" not in t: t["type"] = "Связаться"
    if "products" not in t: t["products"] = ""
    if "ship_addr" not in t: t["ship_addr"] = ""
    if "receiver" not in t: t["receiver"] = ""
    if "receiver_phone" not in t: t["receiver_phone"] = ""
    if "ship_pay" not in t: t["ship_pay"] = ""
    if "tk_num" not in t: t["tk_num"] = ""
    if t.get("type") == "Отправка": t["type"] = "Отправить заказ"

def migrate_data(data):
    du = [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}]
    if "users" not in data: data["users"] = du
    if "notifications" not in data: data["notifications"] = []
    for u in data["users"]:
        if not is_hashed(u.get("password", "")): u["password"] = hash_password(u["password"])
        if "telegram_chat_id" not in u: u["telegram_chat_id"] = ""
    for c in data.get("clients", []):
        client_deals = [d for d in data.get("deals", []) if d.get("client_id") == c["id"]]
        first_deal_id = client_deals[0]["id"] if client_deals else None
        for k, v in [("email",""),("address",""),("base_comment",""),("category","Не определён"),("discount",0),("extra_phones",[]),("extra_emails",[]),("extra_addresses",[]),("client_files",[]),("client_comments",[]),("manager",""),("comments",[]),("tasks",[]),("last_modified","1970-01-01 00:00:00"),("client_chat",[]),("created_at","")]:
            if k not in c or c[k] == "-": c[k] = v
        for ea in c.get("extra_addresses", []):
            if isinstance(ea, str):
                idx = c["extra_addresses"].index(ea)
                c["extra_addresses"][idx] = {"address": ea, "resp_name": "", "resp_role": "", "resp_phone": "", "resp_email": ""}
        for t in c.get("tasks", []):
            if "manager" not in t: t["manager"] = c.get("manager", "")
            if "deadline" in t and " " in str(t["deadline"]): t["deadline"] = str(t["deadline"]).split(" ")[0]
            if "completion_report" not in t: t["completion_report"] = ""
            if "deal_id" not in t: t["deal_id"] = first_deal_id
            if "last_modified" not in t: t["last_modified"] = "1970-01-01 00:00:00"
            if "task_number" not in t: t["task_number"] = ""
            if "created_at" not in t: t["created_at"] = ""
            migrate_task_files(t)
    for d in data.get("deals", []):
        if "deal_title" not in d: d["deal_title"] = ""
        if "deal_comments" not in d: d["deal_comments"] = []
        if "deal_files" not in d: d["deal_files"] = []
        if "payment_status" not in d: d["payment_status"] = "Не оплачено"
        if "manager" not in d: d["manager"] = ""
        if "close_files" not in d:
            d["close_files"] = []
            if d.get("close_file_path"): d["close_files"].append({"file_path": d["close_file_path"], "file_name": d.get("close_file_name", "файл"), "file_hash": ""})
        if "last_modified" not in d: d["last_modified"] = "1970-01-01 00:00:00"
        if "deal_chat" not in d: d["deal_chat"] = []
        if "deal_number" not in d: d["deal_number"] = ""
        if "created_at" not in d: d["created_at"] = ""
        if d.get("status") == "New": d["status"] = "Новый"
        if d.get("status") == "На согласовании": d["status"] = "В работе"
        if d.get("title", "").startswith("Заказ"): d["title"] = d.get("deal_number", d["title"])
    assign_task_numbers(data)
    assign_deal_numbers(data)
    if "internal_tasks" not in data: data["internal_tasks"] = []
    if "chat_messages" not in data: data["chat_messages"] = []
    if "qa_entries" not in data: data["qa_entries"] = []
    if "suppliers" not in data: data["suppliers"] = []
    data["_migrated"] = "v2"
    return data

def load_data():
    download_db_from_yandex()
    db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}], "_migrated": "v2", "internal_tasks": [], "chat_messages": [], "qa_entries": [], "suppliers": [], "notifications": []}
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("_migrated") != "v2":
                data = migrate_data(data)
                with open(FILE_NAME, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                upload_db_to_yandex_async()
            else:
                for c in data.get("clients", []):
                    client_deals = [d for d in data.get("deals", []) if d.get("client_id") == c["id"]]
                    first_deal_id = client_deals[0]["id"] if client_deals else None
                    if "last_modified" not in c: c["last_modified"] = "1970-01-01 00:00:00"
                    if "client_chat" not in c: c["client_chat"] = []
                    if "created_at" not in c: c["created_at"] = c.get("last_modified", "")
                    for t in c.get("tasks", []):
                        if "completion_report" not in t: t["completion_report"] = ""
                        if "deal_id" not in t: t["deal_id"] = first_deal_id
                        if "last_modified" not in t: t["last_modified"] = "1970-01-01 00:00:00"
                        if "task_number" not in t: t["task_number"] = ""
                        if "created_at" not in t: t["created_at"] = t.get("last_modified", "")
                        if "in_work" not in t: t["in_work"] = False
                        if "needs_rework" not in t: t["needs_rework"] = False
                        if "reviewed" not in t: t["reviewed"] = False
                        if "created_by" not in t: t["created_by"] = ""
                        if "ready_to_ship" not in t: t["ready_to_ship"] = False
                        if "delegated_to" not in t: t["delegated_to"] = None
                        if "task_comments" not in t: t["task_comments"] = []
                        if "flagged" not in t: t["flagged"] = False
                        if "type" not in t: t["type"] = "Связаться"
                        if "products" not in t: t["products"] = ""
                        if "ship_addr" not in t: t["ship_addr"] = ""
                        if "receiver" not in t: t["receiver"] = ""
                        if "receiver_phone" not in t: t["receiver_phone"] = ""
                        if "ship_pay" not in t: t["ship_pay"] = ""
                        if "tk_num" not in t: t["tk_num"] = ""
                        if t.get("type") == "Отправка": t["type"] = "Отправить заказ"
                        migrate_task_files(t)
                for d in data.get("deals", []):
                    if "deal_title" not in d: d["deal_title"] = ""
                    if "deal_files" not in d: d["deal_files"] = []
                    if "payment_status" not in d: d["payment_status"] = "Не оплачено"
                    if "manager" not in d: d["manager"] = ""
                    if "close_files" not in d:
                        d["close_files"] = []
                        if d.get("close_file_path"): d["close_files"].append({"file_path": d["close_file_path"], "file_name": d.get("close_file_name", "файл"), "file_hash": ""})
                    if "last_modified" not in d: d["last_modified"] = "1970-01-01 00:00:00"
                    if "deal_chat" not in d: d["deal_chat"] = []
                    if "deal_number" not in d: d["deal_number"] = ""
                    if "created_at" not in d: d["created_at"] = d.get("last_modified", "")
                    if d.get("status") == "На согласовании": d["status"] = "В работе"
                    if d.get("title", "").startswith("Заказ"): d["title"] = d.get("deal_number", d["title"])
                assign_task_numbers(data)
                assign_deal_numbers(data)
                if "internal_tasks" not in data: data["internal_tasks"] = []
                if "chat_messages" not in data: data["chat_messages"] = []
                if "qa_entries" not in data: data["qa_entries"] = []
                if "suppliers" not in data: data["suppliers"] = []
            return data
        except Exception:
            return db
    return db

def save_data(data):
    try:
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        upload_db_to_yandex_async()
    except Exception as e:
        st.sidebar.error(f"Ошибка сохранения: {e}")

def commit_and_rerun(data=None, toast_msg=None):
    if data is not None:
        save_data(data)
    if toast_msg:
        st.toast(toast_msg, icon="✅")
    st.rerun()

# ====== УВЕДОМЛЕНИЯ ======
TELEGRAM_BOT_TOKEN = "8997365571:AAHgrPDcL-Oi8Ew5L81Dm4w7xQPF3uUkpcc"

def get_user_by_login(login):
    for u in st.session_state.crm_store.get("users", []):
        if u.get("login") == login:
            return u
    return None

def resolve_login(name_or_login):
    """Преобразует имя сотрудника в логин (для уведомлений)."""
    if not name_or_login:
        return ""
    # Сначала пробуем как логин
    u = get_user_by_login(name_or_login)
    if u:
        return u["login"]
    # Потом ищем по имени
    for u in st.session_state.crm_store.get("users", []):
        if u.get("name") == name_or_login:
            return u["login"]
    return name_or_login

def send_telegram(chat_id, text):
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=5
        )
    except:
        pass

def add_notification(to_login, text, tg_text=None):
    """Создаёт уведомление: внутреннее (колокольчик) + Telegram"""
    to_login = resolve_login(to_login)
    store = st.session_state.crm_store
    if "notifications" not in store:
        store["notifications"] = []
    notif = {
        "id": len(store["notifications"]) + 1,
        "to": to_login,
        "text": text,
        "date": now_str(),
        "read": False
    }
    store["notifications"].append(notif)
    # Telegram
    u = get_user_by_login(to_login)
    if u and u.get("telegram_chat_id"):
        send_telegram(u["telegram_chat_id"], tg_text or text)

def get_unread_count():
    me = st.session_state.get("user_login", "")
    notifs = st.session_state.crm_store.get("notifications", [])
    return sum(1 for n in notifs if n.get("to") == me and not n.get("read", False))

def get_my_notifications():
    me = st.session_state.get("user_login", "")
    notifs = st.session_state.crm_store.get("notifications", [])
    mine = [n for n in notifs if n.get("to") == me]
    mine.sort(key=lambda n: n.get("date", ""), reverse=True)
    return mine[:30]

def mark_all_notifications_read():
    me = st.session_state.get("user_login", "")
    for n in st.session_state.crm_store.get("notifications", []):
        if n.get("to") == me:
            n["read"] = True
    save_data(st.session_state.crm_store)

def render_notifications_bell():
    """Колокольчик с уведомлениями — компактная кнопка"""
    unread = get_unread_count()
    bell_key = "crm_bell_toggle"
    if unread > 0:
        bell_label = f"🔔 {unread}"
    else:
        bell_label = "🔔"
    bc_col, _spacer = st.columns([1, 20])
    with bc_col:
        with st.container(key="crm_bell_wrap"):
            if st.button(bell_label, key="btn_bell", help=f"Уведомления ({unread} непрочитанных)"):
                st.session_state[bell_key] = not st.session_state.get(bell_key, False)
                st.rerun()

def render_notifications_panel():
    """Панель уведомлений на всю ширину"""
    bell_key = "crm_bell_toggle"
    if not st.session_state.get(bell_key, False):
        return
    notifs = get_my_notifications()
    unread = get_unread_count()
    with st.container(border=True):
        hc, bc = st.columns([10, 2])
        with hc:
            st.markdown("### 🔔 Уведомления")
        with bc:
            if unread > 0:
                if st.button("Прочитать все", key="btn_read_all", use_container_width=True):
                    mark_all_notifications_read()
                    st.rerun()
        if not notifs:
            st.caption("Нет уведомлений")
        else:
            for n in notifs:
                bg = "#E3F2FD" if not n.get("read", False) else "#F5F6F8"
                border = "1px solid #BBDEFB" if not n.get("read", False) else "1px solid #E8EBEF"
                st.markdown(
                    f'<div style="background:{bg};border:{border};border-radius:10px;padding:10px 14px;margin-bottom:8px;">'
                    f'<span style="font-size:0.75rem;color:#95A5B7;">{n.get("date","")}</span><br>'
                    f'<span style="font-size:0.95rem;color:#2C3E50;">{n.get("text","")}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )


@st.dialog("Завершить сделку", width="medium")
def close_deal_dialog(deal_id):
    deal = None
    for d in st.session_state.crm_store["deals"]:
        if d["id"] == deal_id:
            deal = d
            break
    if not deal:
        st.error("Сделка не найдена")
        return
    client = get_client_by_id(deal["client_id"])
    incomplete = [t for t in (client.get("tasks", []) if client else []) if not t.get("done") and t.get("deal_id") == deal_id]
    if incomplete:
        st.warning(f"Нельзя завершить сделку: {len(incomplete)} невыполненных задач(и).")
        for t in incomplete:
            st.markdown(f"- №{t.get('task_number', '')} — {format_date(t.get('deadline', ''))} — {t.get('text', '')}")
        if st.button("Понятно", use_container_width=True):
            st.rerun()
        return
    st.markdown("Заполните отчёт о выполнении сделки:")
    report = st.text_area("Отчёт (обязательно):", key=f"close_deal_report_{deal_id}", height=80)
    close_files = st.file_uploader("Файлы закрытия:", key=f"close_deal_file_{deal_id}", accept_multiple_files=True)
    if st.button("Завершить сделку", type="primary", use_container_width=True):
        if report.strip():
            for d in st.session_state.crm_store["deals"]:
                if d["id"] == deal_id:
                    d['status'] = "Сделка закрыта"
                    d['closed_date'] = datetime.now().strftime("%Y-%m-%d")
                    d['close_report'] = report.strip()
                    d['close_files'] = normalize_file_list(save_uploaded_files(close_files, d["client_id"], "deal_close")) if close_files else []
                    d["last_modified"] = now_str()
                    break
            save_data(st.session_state.crm_store)
            st.toast("Сделка завершена", icon="✅")
            st.rerun()
        else:
            st.error("Заполните отчёт")

if "crm_store" not in st.session_state:
    with st.spinner("Загрузка данных..."):
        st.session_state.crm_store = load_data()
if "f_ph" not in st.session_state: st.session_state.f_ph = []
if "f_em" not in st.session_state: st.session_state.f_em = []
if "f_ad" not in st.session_state: st.session_state.f_ad = []
if "last_id" not in st.session_state: st.session_state.last_id = None
if "active_tab" not in st.session_state: st.session_state.active_tab = "Задачи"
if "client_form_version" not in st.session_state: st.session_state.client_form_version = 0
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "user_role" not in st.session_state: st.session_state.user_role = None
if "user_login" not in st.session_state: st.session_state.user_login = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "cloud_ok" not in st.session_state: st.session_state.cloud_ok = check_cloud_status()
if "open_deal_id" not in st.session_state: st.session_state.open_deal_id = None
if "yandex_folders_ready" not in st.session_state:
    init_yandex_folders()
    st.session_state.yandex_folders_ready = True
if "deal_file_uploader_ver" not in st.session_state: st.session_state.deal_file_uploader_ver = {}
if "expanded_client_id" not in st.session_state: st.session_state.expanded_client_id = None
if "expanded_deal_id" not in st.session_state: st.session_state.expanded_deal_id = None
if "expanded_task_key" not in st.session_state: st.session_state.expanded_task_key = None
if "dialog_task_key" not in st.session_state: st.session_state.dialog_task_key = None
if "expanded_tree_id" not in st.session_state: st.session_state.expanded_tree_id = None
if "auto_expand_deal_id" not in st.session_state: st.session_state.auto_expand_deal_id = None
if "scroll_to_deal" not in st.session_state: st.session_state.scroll_to_deal = None

cookie_manager = stx.CookieManager()
cookies = cookie_manager.get_all()

if not st.session_state.get("authenticated") and not st.query_params.get("auth_token"):
    stored_token = cookies.get("auth_token")
    if stored_token:
        st.query_params["auth_token"] = stored_token
        st.rerun()

_auth_token = st.query_params.get("auth_token")
if _auth_token and not st.session_state.authenticated:
    for u in st.session_state.crm_store.get("users", []):
        if u.get("auth_token") == _auth_token:
            st.session_state.authenticated = True
            st.session_state.user_role = u["role"]
            st.session_state.user_login = u["login"]
            st.session_state.user_name = u.get("name", u["login"])
            break
    if not st.session_state.authenticated:
        if "auth_token" in st.query_params:
            del st.query_params["auth_token"]
        cookie_manager.delete("auth_token")

MGR_PLACEHOLDER = "Выбери ответственного"

st.markdown("""<style>.stTextInput > div > div > p, .stNumberInput > div > div > p, .stTextArea > div > div > p { display: none !important; }</style>""", unsafe_allow_html=True)

def check_login(username, password):
    for u in st.session_state.crm_store.get("users", []):
        if u["login"] == username.strip() and verify_password(password, u["password"]):
            st.session_state.authenticated = True
            st.session_state.user_role = u["role"]
            st.session_state.user_login = u["login"]
            st.session_state.user_name = u.get("name", u["login"])
            return True
    return False

if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center; margin-top: 3rem;'>Айплинт CRM</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #7F8C9A; margin-bottom: 2rem;'>Авторизуйтесь для входа в систему</p>", unsafe_allow_html=True)
    lc, mc, rc = st.columns([1, 2, 1])
    with mc:
        with st.container(border=True):
            iu = st.text_input("Логин:", placeholder="Введите логин")
            ip = st.text_input("Пароль:", type="password", placeholder="Введите пароль")
            if st.button("Войти", use_container_width=True, type="primary"):
                if check_login(iu, ip):
                    _token = secrets.token_hex(16)
                    for u in st.session_state.crm_store["users"]:
                        if u["login"] == iu.strip():
                            u["auth_token"] = _token
                            break
                    save_data(st.session_state.crm_store)
                    st.query_params["auth_token"] = _token
                    cookie_manager.set("auth_token", _token, expires_at=datetime(2027, 12, 31))
                    st.toast("Успешный вход", icon="\U0001F513")
                    st.rerun()
                else:
                    st.error("Неверный логин или пароль.")
    st.stop()

st.markdown(f"""<div class="greeting-block"><h1 style='text-align: center; margin-bottom: 0.1rem;'>Айплинт CRM</h1><p style='text-align: center; color: #7F8C9A; font-size: 0.95rem; margin-top: 0; margin-bottom: 0;'>Продуктивного тебе дня, {st.session_state.user_name} \U0001F60A</p></div>""", unsafe_allow_html=True)

with st.sidebar:
    if st.session_state.cloud_ok: st.success("Облако активно")
    else: st.warning("Облако недоступно (работа локально)")
    st.markdown("---")
    st.markdown(f"**{st.session_state.user_name}**")
    st.markdown(f"Роль: `{st.session_state.user_role}`")
    with st.expander("Сменить пароль"):
        cul = st.session_state.user_login
        np = st.text_input("Новый пароль:", type="password", key="self_new_pwd")
        cp = st.text_input("Повторите пароль:", type="password", key="self_conf_pwd")
        if st.button("Обновить", key="btn_save_self_pwd", use_container_width=True):
            if np and np == cp:
                _new_token = secrets.token_hex(16)
                for u in st.session_state.crm_store["users"]:
                    if u["login"] == cul:
                        u["password"] = hash_password(np)
                        u["auth_token"] = _new_token
                save_data(st.session_state.crm_store)
                st.query_params["auth_token"] = _new_token
                cookie_manager.set("auth_token", _new_token, expires_at=datetime(2027, 12, 31))
                st.toast("Пароль изменён", icon="✅")
                st.rerun()
            else: st.error("Пароли не совпадают")
    if st.session_state.user_role == "admin":
        with st.expander("Экспорт базы"):
            st.download_button("Скачать CSV", data=export_clients_csv(), file_name="clients_export.csv", mime="text/csv", use_container_width=True)
        with st.expander("Управление сотрудниками"):
            st.markdown("### Создать сотрудника")
            nul = st.text_input("Логин:", key="adm_nu_l")
            nup = st.text_input("Пароль:", key="adm_nu_p")
            nun = st.text_input("Имя / Должность:", key="adm_nu_n")
            nur = st.selectbox("Роль:", ["manager", "admin"], key="adm_nu_r")
            if st.button("Создать", use_container_width=True, type="primary"):
                if nul and nup and nun:
                    if not any(u["login"] == nul.strip() for u in st.session_state.crm_store.get("users", [])):
                        st.session_state.crm_store.setdefault("users", []).append({"login": nul.strip(), "password": hash_password(nup), "role": nur, "name": nun.strip()})
                        commit_and_rerun(st.session_state.crm_store, "Сотрудник создан")
                    else: st.error("Логин уже занят")
                else: st.error("Заполните все поля")
            st.markdown("---")
            for u in st.session_state.crm_store.get("users", []):
                ucl, ucr = st.columns([3, 1])
                with ucl: st.markdown(f"**{u.get('name', u['login'])}** ({u['role']})")
                with ucr:
                    if u["login"] != st.session_state.user_login:
                        if st.button("X", key=f"del_u_{u['login']}", help="Удалить"):
                            st.session_state.crm_store["users"] = [x for x in st.session_state.crm_store["users"] if x["login"] != u["login"]]
                            commit_and_rerun(st.session_state.crm_store, "Сотрудник удалён")
    with st.expander("Telegram уведомления"):
        st.markdown("Введите Chat ID для push-уведомлений в Telegram")
        st.caption("Узнать Chat ID: @userinfobot в Telegram")
        tg_id = st.text_input("Chat ID:", value=str(get_user_by_login(st.session_state.user_login).get("telegram_chat_id", "")) if get_user_by_login(st.session_state.user_login) else "", key="tg_chat_id_input")
        if st.button("Сохранить", key="btn_save_tg", use_container_width=True, type="primary"):
            u = get_user_by_login(st.session_state.user_login)
            if u:
                u["telegram_chat_id"] = tg_id.strip()
                save_data(st.session_state.crm_store)
                st.toast("Chat ID сохранён", icon="✅")
                st.rerun()
    st.markdown("---")
    if st.button("Выйти", use_container_width=True):
        _tok = st.query_params.get("auth_token")
        if _tok:
            for u in st.session_state.crm_store.get("users", []):
                if u.get("auth_token") == _tok:
                    u.pop("auth_token", None)
            save_data(st.session_state.crm_store)
            if "auth_token" in st.query_params:
                del st.query_params["auth_token"]
        cookie_manager.delete("auth_token")
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_login = None
        st.session_state.user_name = None
        st.rerun()

render_notifications_bell()
nc1, nc2, nc3, nc4, nc5 = st.columns(5)
with nc1:
    if st.button("Клиенты", use_container_width=True, type="primary" if st.session_state.active_tab == "Клиенты" else "secondary"):
        st.session_state.active_tab = "Клиенты"
        st.session_state.expanded_task_key = None
        st.session_state.pop("dialog_task_key", None)
        st.rerun()
with nc2:
    if st.button("Сделки", use_container_width=True, type="primary" if st.session_state.active_tab == "Сделки" else "secondary"):
        st.session_state.active_tab = "Сделки"
        st.session_state.expanded_task_key = None
        st.session_state.pop("dialog_task_key", None)
        st.rerun()
with nc3:
    if st.button("Задачи", use_container_width=True, type="primary" if st.session_state.active_tab == "Задачи" else "secondary"):
        st.session_state.active_tab = "Задачи"
        st.session_state.expanded_task_key = None
        st.session_state.pop("dialog_task_key", None)
        st.rerun()
with nc4:
    if st.button("Внутренние задачи", use_container_width=True, type="primary" if st.session_state.active_tab == "Внутренние задачи" else "secondary"):
        st.session_state.active_tab = "Внутренние задачи"
        st.session_state.expanded_task_key = None
        st.session_state.pop("dialog_task_key", None)
        st.rerun()
with nc5:
    if st.button("Поставщики", use_container_width=True, type="primary" if st.session_state.active_tab == "Поставщики" else "secondary"):
        st.session_state.active_tab = "Поставщики"
        st.session_state.expanded_task_key = None
        st.session_state.pop("dialog_task_key", None)
        st.rerun()
st.markdown("---")

# Toast при загрузке если есть непрочитанные
_unread_count = get_unread_count()
if _unread_count > 0 and not st.session_state.get("crm_toast_shown", False):
    st.toast(f"У вас {_unread_count} новых уведомлений", icon="\U0001F514")
    st.session_state["crm_toast_shown"] = True

render_notifications_panel()

cu = st.session_state.user_name

def render_task_form(deal_id, cl_id, key_suffix, default_type="Связаться"):
    ntype = st.selectbox("Тип задачи:", TASK_TYPES, index=TASK_TYPES.index(default_type) if default_type in TASK_TYPES else 0, key=f"nt_type_{key_suffix}")
    ntopic = st.text_input("Тема задачи:", key=f"nt_topic_{key_suffix}")
    ntm = st.selectbox("Ответственный:", get_managers_list(), index=0, key=f"nt_mgr_{key_suffix}", placeholder=MGR_PLACEHOLDER)
    ntd = st.date_input("Срок:", format="DD.MM.YYYY", key=f"nt_d_{key_suffix}")
    if ntype in ("Отправить заказ", "Отправить образцы"):
        nproducts = st.text_area("Товары:", key=f"nt_prod_{key_suffix}")
        nship_addr = st.text_area("Адрес доставки:", key=f"nt_addr_{key_suffix}")
        nreceiver = st.text_input("Получатель:", key=f"nt_recv_{key_suffix}")
        nreceiver_phone = st.text_input("Телефон получателя:", key=f"nt_rphone_{key_suffix}")
        nship_pay = st.selectbox("Оплата:", SHIP_PAY_OPTIONS, index=0, key=f"nt_pay_{key_suffix}", placeholder="Укажи плательщика")
        norder_amount = st.text_input("Сумма заказа (руб.):", value="", key=f"nt_amount_{key_suffix}", placeholder="Введите сумму")
        ntk_num = st.text_input("Трек:", key=f"nt_tk_{key_suffix}", placeholder="Введите трек-номер")
        ncomment = st.text_area("Комментарии:", key=f"nt_c_{key_suffix}")
        ntf = st.file_uploader("Файлы задачи:", key=f"nt_file_{key_suffix}", accept_multiple_files=True)
    else:
        nproducts = ""
        nship_addr = ""
        nreceiver = ""
        nreceiver_phone = ""
        nship_pay = ""
        norder_amount = ""
        ntk_num = ""
        ncomment = st.text_area("Комментарии:", key=f"nt_c_{key_suffix}")
        ntf = st.file_uploader("Файлы задачи:", key=f"nt_file_{key_suffix}", accept_multiple_files=True)
    if st.button("Создать", key=f"nt_go_{key_suffix}", use_container_width=True, type="primary"):
        if not ntopic.strip():
            st.warning("Введите тему задачи")
        elif not ntm:
            st.warning("Выберите ответственного")
        else:
            tfi_list = save_uploaded_files(ntf, cl_id, "task_file") if ntf else []
            prefix = "ЗС" if deal_id else "ЗК"
            tn = generate_task_number(prefix)
            te = {
                "text": ntopic.strip(), "deadline": ntd.isoformat(), "done": False, "type": ntype,
                "task_files": normalize_file_list(tfi_list), "manager": ntm,
                "completion_report": "", "completion_files": [],
                "deal_id": deal_id, "task_comment": ncomment.strip(),
                "order_amount": int(norder_amount) if norder_amount and norder_amount.strip().isdigit() else 0, "last_modified": now_str(),
                "task_number": tn, "created_at": now_str(), "created_by": st.session_state.get("user_login", ""),
                "in_work": False, "ready_to_ship": False, "delegated_to": None, "needs_rework": False, "reviewed": False,
                "task_comments": [], "flagged": False,
                "products": nproducts, "ship_addr": nship_addr,
                "receiver": nreceiver, "receiver_phone": nreceiver_phone,
                "ship_pay": nship_pay, "tk_num": ntk_num.strip()
            }
            cl = get_client_by_id(cl_id)
            if cl:
                cl.setdefault("tasks", []).append(te)
                cl["last_modified"] = now_str()
                if deal_id:
                    d = get_deal_by_id(deal_id)
                    if d: d["last_modified"] = now_str()
                add_notification(ntm, f"Новая задача: {ntopic.strip()} | Клиент: {cl.get('name','')} | Срок: {ntd.isoformat()}", f"📝 Новая задача: {ntopic.strip()} | Клиент: {cl.get('name','')} | Срок: {ntd.isoformat()}")
                return True
        return False
    return False

def render_deal_card_expanded(d, cl):
    with st.container(border=True):
        st.markdown(f"**{d.get('deal_number', d.get('title', ''))}**")
        st.markdown(format_created_date(d), unsafe_allow_html=True)
        st.markdown(f"**Бюджет:** {d.get('budget', 0):,.0f} руб.".replace(",", " "))
        ps = d.get("payment_status", "Не оплачено")
        inject_payment_container_css(d["id"], ps)
        with st.container(key=f"ps_wrap_{d['id']}"):
            new_ps = st.selectbox("Статус оплаты:", ["Не оплачено", "Оплачено"], index=0 if ps == "Не оплачено" else 1, key=f"ps_{d['id']}")
        if new_ps != ps:
            d["payment_status"] = new_ps
            d["last_modified"] = now_str()
            commit_and_rerun(st.session_state.crm_store, "Статус оплаты обновлён")
        if d.get("manager"): st.markdown(f"**Ответственный:** {d.get('manager')}")
        st.markdown("---")
        dl_files_col, dl_upload_col = st.columns(2)
        with dl_files_col:
            st.markdown("**Файлы сделки:**")
            render_file_thumbs(d.get("deal_files", []), f"deal_file_{d['id']}", allow_delete=True)
        with dl_upload_col:
            st.markdown("**Загрузить файлы:**")
            df_ver = st.session_state.deal_file_uploader_ver.get(d["id"], 0)
            udf = st.file_uploader("Выберите файлы:", key=f"df_up_{d['id']}_{df_ver}", accept_multiple_files=True, label_visibility="collapsed")
            if st.button("Загрузить", key=f"df_btn_{d['id']}", use_container_width=True):
                if udf:
                    with st.spinner("Загрузка файлов..."):
                        fi_list = save_uploaded_files(udf, d["client_id"], "deal_file")
                    if fi_list:
                        d.setdefault("deal_files", []).extend(normalize_file_list(fi_list))
                        d["last_modified"] = now_str()
                        st.session_state.deal_file_uploader_ver[d["id"]] = df_ver + 1
                        save_data(st.session_state.crm_store)
                        st.toast("Файлы загружены", icon="\U0001F4C1")
                        st.rerun()
                else: st.warning("Выберите файл(ы)")
        st.markdown("---")
        if d.get("deal_comments"):
            st.markdown("**Комментарии:**")
            for cm in d["deal_comments"]:
                st.markdown(f"- *{cm.get('time', '')}*: {cm.get('text', '')}")
        dc_clr_key = f"clr_dc_{d['id']}"
        if st.session_state.get(dc_clr_key):
            st.session_state[f"dc_input_{d['id']}"] = ""
            st.session_state[dc_clr_key] = False
        nc = st.text_input("Добавить комментарий:", key=f"dc_input_{d['id']}")
        if st.button("Добавить", key=f"dc_btn_{d['id']}", use_container_width=True):
            if nc.strip():
                d.setdefault("deal_comments", []).append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": nc.strip()})
                d["last_modified"] = now_str()
                st.session_state[dc_clr_key] = True
                commit_and_rerun(st.session_state.crm_store, "Комментарий добавлен")
            else: st.warning("Введите текст")
        st.markdown("---")
        render_entity_chat(d, "deal", d["id"])
        st.markdown("---")
        show_edit_deal = st.session_state.get(f"show_edit_deal_{d['id']}", False)
        if st.button("Редактировать сделку" if not show_edit_deal else "Скрыть", key=f"edit_deal_toggle_{d['id']}", use_container_width=True):
            st.session_state[f"show_edit_deal_{d['id']}"] = not show_edit_deal
            st.rerun()
        if show_edit_deal:
            with st.container(border=True):
                et = st.text_input("Название сделки:", value=d.get("deal_title", ""), key=f"et_{d['id']}")
                eb = st.text_input("Бюджет (руб.):", value=str(d.get("budget", 0)) if d.get("budget", 0) > 0 else "", key=f"eb_{d['id']}", placeholder="Введите сумму")
                em = st.selectbox("Ответственный:", get_managers_list(), index=0 if d.get('manager', '') not in get_managers_list() else (get_managers_list()).index(d.get('manager', '')), key=f"em_{d['id']}", placeholder=MGR_PLACEHOLDER)
                if st.button("Сохранить", key=f"es_{d['id']}", use_container_width=True, type="primary"):
                    if not em:
                        st.warning("Выберите ответственного")
                    else:
                        d["deal_title"] = et
                        d["budget"] = int(eb) if eb and eb.strip().isdigit() else 0
                        d["manager"] = em
                        d["last_modified"] = now_str()
                        st.session_state[f"show_edit_deal_{d['id']}"] = False
                        commit_and_rerun(st.session_state.crm_store, "Сделка обновлена")
        st.markdown("---")
        current_status = d.get("status", "Новый")
        if current_status == "Новый":
            if st.button("Взять в работу", key=f"deal_next_{d['id']}", use_container_width=True, type="primary"):
                d["status"] = "В работе"
                if not d.get("manager"): d["manager"] = cu
                d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Сделка взята в работу")
        elif current_status == "В работе":
            if st.button("Закрыть сделку", key=f"deal_close_{d['id']}", use_container_width=True, type="primary"):
                close_deal_dialog(d["id"])
        elif current_status == "Сделка закрыта":
            if st.button("Вернуть в работу", key=f"deal_reopen_{d['id']}", use_container_width=True):
                d["status"] = "В работе"
                d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Сделка возвращена")
            if st.button("В архив", key=f"deal_archive_{d['id']}", use_container_width=True, type="primary"):
                d["status"] = "Архив"
                d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Сделка в архиве")
        elif current_status == "Архив":
            if st.button("Вернуть в работу", key=f"arch_reopen_{d['id']}", use_container_width=True):
                d["status"] = "В работе"
                d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Сделка возвращена")
            if st.button("В закрытые", key=f"arch_toclosed_{d['id']}", use_container_width=True, type="primary"):
                d["status"] = "Сделка закрыта"
                d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Сделка в закрытых")
        if st.session_state.user_role == "admin":
            st.markdown("---")
            if st.button("Удалить сделку", key=f"deal_del_{d['id']}", use_container_width=True):
                st.session_state.crm_store["deals"] = [x for x in st.session_state.crm_store["deals"] if x["id"] != d["id"]]
                st.session_state.expanded_deal_id = None
                commit_and_rerun(st.session_state.crm_store, "Сделка удалена")

def render_deal_in_tree(d, cl):
    is_dl_exp = st.session_state.expanded_deal_id == d["id"] or st.session_state.auto_expand_deal_id == d["id"]
    dl_tasks = [t for t in cl.get("tasks", []) if t.get("deal_id") == d["id"]]
    dl_bg, dl_bc = get_entity_border(dl_tasks)
    dl_label = f"{d.get('deal_number', d.get('title', ''))} ({d['status']}) — {d.get('budget', 0):,.0f} руб. | Задач: {len(dl_tasks)}"
    if d.get("deal_title"):
        dl_label = f"{d.get('deal_number', d.get('title', ''))} — {d['deal_title']} ({d['status']}) — {d.get('budget', 0):,.0f} руб. | Задач: {len(dl_tasks)}"
    dl_selected = is_dl_exp
    dl_border = "#2196F3" if dl_selected else dl_bc
    dl_shadow = "box-shadow: 0 0 0 2px rgba(33,150,243,0.3);" if dl_selected else ""

    with indented(0.03):
        st.markdown(f"<style>.st-key-dl_btn_wrap_{d['id']} button {{ background-color: {dl_bg} !important; color: #2C3E50 !important; border: 2px solid {dl_border} !important; border-radius: 10px !important; {dl_shadow} }}</style>", unsafe_allow_html=True)
        anchor_id = f"deal_anchor_{d['id']}"
        with st.container(key=f"dl_btn_wrap_{d['id']}"):
            if st.button(dl_label, key=f"dl_card_{d['id']}", use_container_width=True, type="primary" if is_dl_exp else "secondary"):
                if is_dl_exp:
                    st.session_state.expanded_deal_id = None
                    save_scroll_and_rerun()
                else:
                    st.session_state.expanded_deal_id = d["id"]
                    st.session_state.expanded_task_key = None
                    st.rerun()
            if not is_dl_exp:
                render_scroll_restore(f"dl_{d['id']}")
        if st.session_state.auto_expand_deal_id == d["id"]:
            st.session_state.auto_expand_deal_id = None
            st.session_state.expanded_deal_id = d["id"]
            st.session_state.scroll_to_deal = anchor_id
        if st.session_state.scroll_to_deal == anchor_id:
            st.markdown(f'<div id="{anchor_id}"></div>', unsafe_allow_html=True)
            st.components.v1.html(f"""<script>setTimeout(function(){{var el=window.parent.document.getElementById('{anchor_id}');if(el)el.scrollIntoView({{behavior:'smooth',block:'center'}});}},300);</script>""", height=0)
            st.session_state.scroll_to_deal = None
        if st.session_state.expanded_deal_id == d["id"]:
            render_deal_card_expanded(d, cl)

        render_centered_title(f"Задачи по сделке ({len(dl_tasks)})")
        with indented(0.03):
            if dl_tasks:
                dl_tasks.sort(key=lambda t: get_sort_key(t), reverse=True)
                for ti, t in enumerate(dl_tasks):
                    task_key = f"dl_{d['id']}_{ti}"
                    render_task_row(t, cl, d, task_key, f"dl_{d['id']}_{ti}")
            show_ct_key = f"show_ct_{d['id']}"
            if render_centered_button("Создать задачу по сделке", key=f"btn_ct_dl_{d['id']}"):
                st.session_state[show_ct_key] = not st.session_state.get(show_ct_key, False)
                st.rerun()
        if st.session_state.get(show_ct_key, False):
            with st.container(border=True):
                if render_task_form(d["id"], d["client_id"], f"deal_{d['id']}"):
                    st.session_state[show_ct_key] = False
                    commit_and_rerun(st.session_state.crm_store, "Задача создана")


def render_deal_standalone(d, cl, cu):
    """Свёрнутая карточка сделки для вкладки «Сделки»."""
    deal_id = d["id"]
    exp_key = "deal_tab_expanded"
    is_exp = st.session_state.get(exp_key) == deal_id
    dl_tasks = [t for t in (cl.get("tasks", []) if cl else []) if t.get("deal_id") == deal_id]
    client_name = cl.get("name", "—") if cl else "—"
    num = d.get("deal_number", d.get("title", ""))
    parts = [str(num), client_name]
    if d.get("deal_title"):
        parts.append(d["deal_title"])
    parts.append(f"{d.get('budget', 0):,.0f} руб.".replace(",", " "))
    parts.append(f"Ответственный: {d.get('manager', '—')}")
    parts.append(f"Задач: {len(dl_tasks)}")
    label = " | ".join(parts)
    # Border colors based on task status (like in clients)
    dl_bg, dl_bc = get_entity_border(dl_tasks)
    bc = "#2196F3" if is_exp else dl_bc
    st.markdown(f"<style>.st-key-dls_wrap_{deal_id} button {{ background-color: {dl_bg} !important; color: #2C3E50 !important; border: 2px solid {bc} !important; border-radius: 10px !important; white-space: normal !important; height: auto !important; text-align: left !important; }}</style>", unsafe_allow_html=True)
    with st.container(key=f"dls_wrap_{deal_id}"):
        if st.button(label, key=f"dls_btn_{deal_id}", use_container_width=True, type="primary" if is_exp else "secondary"):
            st.session_state[exp_key] = None if is_exp else deal_id
            st.rerun()
    if is_exp:
        render_deal_card_tab(d, cl, cu)


def render_deal_card_tab(d, cl, cu):
    """Раскрытая карточка сделки во вкладке «Сделки»."""
    deal_id = d["id"]
    with st.container(border=True):
        num = d.get("deal_number", d.get("title", ""))
        head = f"**{num}**"
        if d.get("deal_title"):
            head += f" — {d['deal_title']}"
        st.markdown(head)
        st.markdown(f"**Клиент:** {cl.get('name', '—') if cl else '—'}")
        st.markdown(format_created_date(d), unsafe_allow_html=True)
        st.markdown(f"**Бюджет:** {d.get('budget', 0):,.0f} руб.".replace(",", " "))
        ps = d.get("payment_status", "Не оплачено")
        inject_payment_container_css(deal_id, ps)
        with st.container(key=f"ps_wrap_{deal_id}"):
            new_ps = st.selectbox("Статус оплаты:", ["Не оплачено", "Оплачено"], index=0 if ps == "Не оплачено" else 1, key=f"dls_ps_{deal_id}")
        if new_ps != ps:
            d["payment_status"] = new_ps
            d["last_modified"] = now_str()
            commit_and_rerun(st.session_state.crm_store, "Статус оплаты обновлён")
        if d.get("manager"):
            st.markdown(f"**Ответственный:** {d.get('manager')}")
        st.markdown("---")
        dl_files_col, dl_upload_col = st.columns(2)
        with dl_files_col:
            st.markdown("**Файлы сделки:**")
            render_file_thumbs(d.get("deal_files", []), f"dls_file_{deal_id}", allow_delete=True)
        with dl_upload_col:
            st.markdown("**Загрузить файлы:**")
            df_ver = st.session_state.deal_file_uploader_ver.get(f"tab_{deal_id}", 0)
            udf = st.file_uploader("Выберите файлы:", key=f"dls_up_{deal_id}_{df_ver}", accept_multiple_files=True, label_visibility="collapsed")
            if st.button("Загрузить", key=f"dls_upbtn_{deal_id}", use_container_width=True):
                if udf:
                    with st.spinner("Загрузка файлов..."):
                        fi_list = save_uploaded_files(udf, d["client_id"], "deal_file")
                    if fi_list:
                        d.setdefault("deal_files", []).extend(normalize_file_list(fi_list))
                        d["last_modified"] = now_str()
                        st.session_state.deal_file_uploader_ver[f"tab_{deal_id}"] = df_ver + 1
                        save_data(st.session_state.crm_store)
                        st.toast("Файлы загружены", icon="\U0001F4C1")
                        st.rerun()
                else:
                    st.warning("Выберите файл(ы)")
        st.markdown("---")
        if d.get("deal_comments"):
            st.markdown("**Комментарии:**")
            for cm in d["deal_comments"]:
                st.markdown(f"- *{cm.get('time', '')}*: {cm.get('text', '')}")
        dc_clr_key = f"dls_clr_dc_{deal_id}"
        if st.session_state.get(dc_clr_key):
            st.session_state[f"dls_dc_input_{deal_id}"] = ""
            st.session_state[dc_clr_key] = False
        nc = st.text_input("Добавить комментарий:", key=f"dls_dc_input_{deal_id}")
        if st.button("Добавить", key=f"dls_dc_btn_{deal_id}", use_container_width=True):
            if nc.strip():
                d.setdefault("deal_comments", []).append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": nc.strip()})
                d["last_modified"] = now_str()
                st.session_state[dc_clr_key] = True
                commit_and_rerun(st.session_state.crm_store, "Комментарий добавлен")
            else:
                st.warning("Введите текст")
        st.markdown("---")
        render_entity_chat(d, "deal", deal_id)
        st.markdown("---")
        dl_tasks = [t for t in (cl.get("tasks", []) if cl else []) if t.get("deal_id") == deal_id]
        render_centered_title(f"Задачи по сделке ({len(dl_tasks)})")
        show_ct_key = f"dls_show_ct_{deal_id}"
        if render_centered_button("Создать задачу по сделке", key=f"dls_btn_ct_{deal_id}"):
            st.session_state[show_ct_key] = not st.session_state.get(show_ct_key, False)
            st.rerun()
        if st.session_state.get(show_ct_key, False):
            with st.container(border=True):
                if render_task_form(deal_id, d["client_id"], f"dls_deal_{deal_id}"):
                    st.session_state[show_ct_key] = False
                    commit_and_rerun(st.session_state.crm_store, "Задача создана")
        st.markdown("---")
        show_edit_deal = st.session_state.get(f"dls_show_edit_{deal_id}", False)
        if st.button("Редактировать сделку" if not show_edit_deal else "Скрыть", key=f"dls_edit_toggle_{deal_id}", use_container_width=True):
            st.session_state[f"dls_show_edit_{deal_id}"] = not show_edit_deal
            st.rerun()
        if show_edit_deal:
            with st.container(border=True):
                et = st.text_input("Название сделки:", value=d.get("deal_title", ""), key=f"dls_et_{deal_id}")
                eb = st.text_input("Бюджет (руб.):", value=str(d.get("budget", 0)) if d.get("budget", 0) > 0 else "", key=f"dls_eb_{deal_id}", placeholder="Введите сумму")
                em = st.selectbox("Ответственный:", get_managers_list(), index=0 if d.get('manager', '') not in get_managers_list() else (get_managers_list()).index(d.get('manager', '')), key=f"dls_em_{deal_id}", placeholder=MGR_PLACEHOLDER)
                if st.button("Сохранить", key=f"dls_es_{deal_id}", use_container_width=True, type="primary"):
                    if not em:
                        st.warning("Выберите ответственного")
                    else:
                        d["deal_title"] = et
                        d["budget"] = int(eb) if eb and eb.strip().isdigit() else 0
                        d["manager"] = em
                        d["last_modified"] = now_str()
                        st.session_state[f"dls_show_edit_{deal_id}"] = False
                        commit_and_rerun(st.session_state.crm_store, "Сделка обновлена")
        st.markdown("---")
        action_key = f"dls_action_{deal_id}"
        action = st.session_state.get(action_key)
        current_status = d.get("status", "Новый")
        if current_status == "Новый":
            if st.button("Взять в работу", key=f"dls_take_{deal_id}", use_container_width=True, type="primary"):
                d["status"] = "В работе"
                if not d.get("manager"):
                    d["manager"] = cu
                d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Сделка взята в работу")
        elif current_status == "В работе":
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("Успешно завершена", key=f"dls_close_{deal_id}", use_container_width=True, type="primary"):
                    st.session_state[action_key] = "close"
                    st.rerun()
            with cc2:
                if st.button("В архив", key=f"dls_arch_{deal_id}", use_container_width=True):
                    st.session_state[action_key] = "archive"
                    st.rerun()
        elif current_status in ("Сделка закрыта", "Архив"):
            if st.button("Вернуть в работу", key=f"dls_reopen_{deal_id}", use_container_width=True):
                d["status"] = "В работе"
                d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Сделка возвращена")
        if action in ("close", "archive"):
            is_close = (action == "close")
            btn_label = "Успешно завершена" if is_close else "В архив"
            ex_files = d.get("close_files", []) if is_close else d.get("archive_files", [])
            with st.container(border=True):
                st.markdown(f"**{btn_label}: отчёт по сделке**")
                rep = st.text_area("Отчёт по сделке (обязательно):", key=f"dls_rep_{deal_id}_{action}", height=100)
                if ex_files:
                    st.markdown("**Ранее загруженный файл:**")
                    render_file_thumbs(ex_files, f"dls_ex_{deal_id}_{action}")
                up = st.file_uploader("Добавить файл:", key=f"dls_upf_{deal_id}_{action}", accept_multiple_files=True)
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("Подтвердить", key=f"dls_conf_{deal_id}_{action}", use_container_width=True, type="primary"):
                        if not rep.strip():
                            st.error("Заполните отчёт по сделке")
                        else:
                            new_files = normalize_file_list(save_uploaded_files(up, d["client_id"], "deal_close" if is_close else "deal_archive")) if up else []
                            merged = list(ex_files)
                            seen = {f.get("file_hash") for f in merged if isinstance(f, dict)}
                            for f in new_files:
                                if f.get("file_hash") not in seen:
                                    merged.append(f)
                                    seen.add(f.get("file_hash"))
                            if is_close:
                                d["status"] = "Сделка закрыта"
                                d["closed_date"] = datetime.now().strftime("%Y-%m-%d")
                                d["close_report"] = rep.strip()
                                d["close_files"] = merged
                            else:
                                d["status"] = "Архив"
                                d["archive_report"] = rep.strip()
                                d["archive_files"] = merged
                            d["last_modified"] = now_str()
                            st.session_state[action_key] = None
                            commit_and_rerun(st.session_state.crm_store, "Сделка обновлена")
                with bc2:
                    if st.button("Отмена", key=f"dls_cancel_{deal_id}_{action}", use_container_width=True):
                        st.session_state[action_key] = None
                        st.rerun()
        if current_status == "Сделка закрыта" and d.get("close_report"):
            st.markdown("---")
            st.markdown(f"**Отчёт:** {d.get('close_report')}")
            if d.get("close_files"):
                render_file_thumbs(d["close_files"], f"dls_cf_{deal_id}")
        if current_status == "Архив" and d.get("archive_report"):
            st.markdown("---")
            st.markdown(f"**Отчёт:** {d.get('archive_report')}")
            if d.get("archive_files"):
                render_file_thumbs(d["archive_files"], f"dls_af_{deal_id}")
        if st.session_state.user_role == "admin":
            st.markdown("---")
            if st.button("Удалить сделку", key=f"dls_del_{deal_id}", use_container_width=True):
                st.session_state.crm_store["deals"] = [x for x in st.session_state.crm_store["deals"] if x["id"] != deal_id]
                st.session_state["deal_tab_expanded"] = None
                commit_and_rerun(st.session_state.crm_store, "Сделка удалена")


def render_client_card_expanded(cl):
    with st.container(border=True):
        st.markdown(format_created_date(cl), unsafe_allow_html=True)
        info_col, comm_col = st.columns(2)
        with info_col:
            st.markdown("**Информация о клиенте:**")
            render_phone_inline(cl['phone'], cl['id'])
            st.markdown(f"{cl.get('email','')} | {cl.get('address','')}")
            st.markdown(f"Скидка: **{cl.get('discount',0)}%** | Ответственный: **{cl.get('manager','—')}**")
            cph = re.sub(r"\D", "", cl['phone'])
            if cph.startswith("8") and len(cph) == 11: cph = "7" + cph[1:]
            elif not cph: cph = "79990000000"
            mc1, mc2, mc3 = st.columns(3)
            mc1.link_button("WhatsApp", f"https://wa.me/{cph}", use_container_width=True)
            mc2.link_button("Telegram", f"https://t.me/+{cph}", use_container_width=True)
            mc3.link_button("MAX", MAX_URL, use_container_width=True, help=f"Номер в MAX: {MAX_NUMBER}")
            if cl.get("extra_phones"):
                st.markdown("**Доп. телефоны:**")
                for pi, p in enumerate(cl["extra_phones"]):
                    render_extra_phone_inline(p['phone'], p['name'], p['role'], f"{cl['id']}_extra_{pi}")
            if cl.get("extra_addresses"):
                st.markdown("**Доп. адреса:**")
                for ea in cl["extra_addresses"]:
                    if isinstance(ea, dict):
                        st.markdown(f"- **{ea.get('address', '')}** {ea.get('resp_name', '')} {ea.get('resp_phone', '')}")
        with comm_col:
            st.markdown("**Комментарии:**")
            for cc in cl.get("client_comments", []):
                st.markdown(f"- *{cc.get('time', '')}*: {cc.get('text', '')}")
            if not cl.get("client_comments"): st.caption("Пока нет комментариев")
            cc_clr_key = f"clr_cc_{cl['id']}"
            if st.session_state.get(cc_clr_key):
                st.session_state[f"new_cc_input_{cl['id']}"] = ""
                st.session_state[cc_clr_key] = False
            nci = st.text_input("Добавить комментарий:", key=f"new_cc_input_{cl['id']}", placeholder="Введите комментарий...")
            if st.button("Добавить комментарий", key=f"cc_btn_{cl['id']}", use_container_width=True):
                if nci.strip():
                    cl.setdefault("client_comments", []).append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": nci.strip()})
                    cl["last_modified"] = now_str()
                    st.session_state[cc_clr_key] = True
                    commit_and_rerun(st.session_state.crm_store, "Комментарий добавлен")
                else: st.warning("Введите текст")
        st.markdown("---")
        files_col, upload_col = st.columns(2)
        with files_col:
            st.markdown("**Файлы:**")
            render_file_thumbs(cl.get("client_files", []), f"cli_{cl['id']}", allow_delete=True)
        with upload_col:
            st.markdown("**Загрузить файлы:**")
            ucf = st.file_uploader("Выберите файлы:", key=f"cf_up_{cl['id']}", accept_multiple_files=True, label_visibility="collapsed")
            if st.button("Сохранить файлы", key=f"cf_btn_{cl['id']}", use_container_width=True):
                if ucf:
                    with st.spinner("Загрузка файлов..."):
                        fi_list = save_uploaded_files(ucf, cl["id"], "profile")
                    if fi_list:
                        cl.setdefault("client_files", []).extend(normalize_file_list(fi_list))
                        cl["last_modified"] = now_str()
                        save_data(st.session_state.crm_store)
                        st.toast("Файлы сохранены", icon="\U0001F4C1")
                        st.rerun()
                else: st.warning("Выберите файл(ы)")
        st.markdown("---")
        render_entity_chat(cl, "client", cl["id"])
        st.markdown("---")
        show_edit = st.session_state.get(f"show_edit_{cl['id']}", False)
        if st.button("Редактировать данные" if not show_edit else "Скрыть редактор", key=f"edit_toggle_{cl['id']}", use_container_width=True):
            st.session_state[f"show_edit_{cl['id']}"] = not show_edit
            st.rerun()
        if show_edit:
            with st.container(border=True):
                en = st.text_input("ФИО", value=cl['name'], key=f"en_{cl['id']}")
                ep = st.text_input("Телефон", value=cl['phone'], key=f"ep_{cl['id']}")
                ee = st.text_input("Email", value=cl.get('email', ''), key=f"ee_{cl['id']}")
                ea_val = st.text_input("Адрес", value=cl.get('address', ''), key=f"ea_{cl['id']}")
                ed = st.number_input("Скидка (%)", min_value=0, max_value=100, value=int(cl.get('discount', 0)), key=f"ed_{cl['id']}")
                ec_idx = CATEGORIES.index(cl.get('category', 'Не определён')) if cl.get('category', 'Не определён') in CATEGORIES else 0
                ec = st.selectbox("Категория", CATEGORIES, index=ec_idx, key=f"ec_{cl['id']}")
                em = st.selectbox("Ответственный:", get_managers_list(), index=0 if cl.get('manager', '') not in get_managers_list() else (get_managers_list()).index(cl.get('manager', '')), key=f"em_{cl['id']}", placeholder=MGR_PLACEHOLDER)
                if st.button("Сохранить", key=f"es_{cl['id']}", use_container_width=True, type="primary"):
                    cl['name'], cl['phone'], cl['email'], cl['address'], cl['discount'], cl['category'], cl['manager'] = en, format_phone(ep), ee, ea_val, int(ed), ec, em
                    cl["last_modified"] = now_str()
                    st.session_state[f"show_edit_{cl['id']}"] = False
                    commit_and_rerun(st.session_state.crm_store, "Данные клиента сохранены")
                if st.session_state.user_role == "admin":
                    st.markdown("---")
                    cdl = st.checkbox("Подтверждаю удаление клиента", key=f"cdl_{cl['id']}")
                    if cdl and st.button("Удалить клиента", key=f"del_cli_{cl['id']}", use_container_width=True, type="primary"):
                        st.session_state.crm_store["deals"] = [d for d in st.session_state.crm_store["deals"] if d["client_id"] != cl["id"]]
                        st.session_state.crm_store["clients"] = [c for c in st.session_state.crm_store["clients"] if c["id"] != cl["id"]]
                        st.session_state.expanded_client_id = None
                        commit_and_rerun(st.session_state.crm_store, "Клиент удалён")

def render_client_in_tree(cl):
    is_cl_exp = st.session_state.expanded_client_id == cl["id"]
    is_cl_deals_exp = st.session_state.expanded_tree_id == cl["id"]
    cl_tasks_all = cl.get("tasks", [])
    cl_deals = [d for d in st.session_state.crm_store["deals"] if d["client_id"] == cl["id"]]
    all_tasks_for_border = cl_tasks_all + [t for d in cl_deals for t in cl.get("tasks", []) if t.get("deal_id") == d["id"]]
    cl_bg, cl_bc = get_entity_border(all_tasks_for_border)
    cl_label = f"{cl['name']} — {cl['phone']} [{cl.get('category', 'Не определён')}] | Сделок: {len(cl_deals)} | Задач: {len(cl_tasks_all)}"
    cl_selected = is_cl_exp or is_cl_deals_exp
    cl_border = "#2196F3" if cl_selected else cl_bc
    cl_shadow = "box-shadow: 0 0 0 2px rgba(33,150,243,0.3);" if cl_selected else ""
    st.markdown(f"<style>.st-key-cl_btn_wrap_{cl['id']} button {{ background-color: {cl_bg} !important; color: #2C3E50 !important; border: 2px solid {cl_border} !important; border-radius: 10px !important; {cl_shadow} }}</style>", unsafe_allow_html=True)

    ac, bc = st.columns([1, 30])
    with ac:
        with st.container(key=f"arr_cl_{cl['id']}"):
            if st.button("▾" if is_cl_deals_exp else "▸", key=f"cl_arrow_{cl['id']}", use_container_width=True):
                if is_cl_deals_exp:
                    st.session_state.expanded_tree_id = None
                    save_scroll_and_rerun()
                else:
                    st.session_state.expanded_tree_id = cl["id"]
                    st.rerun()
            if not is_cl_deals_exp:
                render_scroll_restore(f"arr_{cl['id']}")
    with bc:
        with st.container(key=f"cl_btn_wrap_{cl['id']}"):
            if st.button(cl_label, key=f"cl_card_{cl['id']}", use_container_width=True, type="primary" if is_cl_exp else "secondary"):
                if is_cl_exp:
                    st.session_state.expanded_client_id = None
                    save_scroll_and_rerun()
                else:
                    st.session_state.expanded_client_id = cl["id"]
                    st.session_state.expanded_deal_id = None
                    st.session_state.expanded_task_key = None
                    st.rerun()
            if not is_cl_exp:
                render_scroll_restore(f"cl_{cl['id']}")

    if is_cl_exp:
        render_client_card_expanded(cl)

    if is_cl_deals_exp:
        client_only_tasks = [t for t in cl_tasks_all if not t.get("deal_id")]
        with indented(0.06):
            render_centered_title(f"Задачи по клиенту ({len(client_only_tasks)})")
            if client_only_tasks:
                client_only_tasks.sort(key=lambda t: get_sort_key(t), reverse=True)
                for ti, t in enumerate(client_only_tasks):
                    task_key = f"cl_{cl['id']}_{ti}"
                    render_task_row(t, cl, None, task_key, f"cl_{cl['id']}_{ti}")
            show_ct_key = f"show_ct_cl_{cl['id']}"
            if render_centered_button("Создать задачу по клиенту", key=f"btn_ct_cl_{cl['id']}"):
                st.session_state[show_ct_key] = not st.session_state.get(show_ct_key, False)
                st.rerun()
        if st.session_state.get(show_ct_key, False):
            with st.container(border=True):
                if render_task_form(None, cl["id"], f"cl_{cl['id']}"):
                    st.session_state[show_ct_key] = False
                    commit_and_rerun(st.session_state.crm_store, "Задача создана")

        render_separator()

        render_centered_title(f"Сделки по клиенту ({len(cl_deals)})")
        if cl_deals:
            cl_deals.sort(key=lambda d: get_sort_key(d), reverse=True)
            for d in cl_deals:
                render_deal_in_tree(d, cl)
        else:
            with indented(0.03):
                st.caption("Сделок нет")

        render_separator()

        show_cd_key = f"show_cd_cl_{cl['id']}"
        if render_centered_button("Создать новую сделку", key=f"btn_cd_cl_{cl['id']}"):
            st.session_state[show_cd_key] = not st.session_state.get(show_cd_key, False)
            st.rerun()
        if st.session_state.get(show_cd_key, False):
            with st.container(border=True):
                cd_title = st.text_input("Название сделки:", key=f"cd_title_{cl['id']}")
                cd_budget = st.text_input("Бюджет (руб.):", value="", key=f"cd_budget_{cl['id']}", placeholder="Введите сумму")
                cd_mgr = st.selectbox("Ответственный:", get_managers_list(), index=0, key=f"cd_mgr_{cl['id']}", placeholder=MGR_PLACEHOLDER)
                if st.button("Создать", key=f"cd_go_{cl['id']}", use_container_width=True, type="primary"):
                    if not cd_mgr:
                        st.warning("Выберите ответственного")
                    else:
                        deals = st.session_state.crm_store.get("deals", [])
                        did = (max([dd["id"] for dd in deals]) if deals else 0) + 1
                        dn = generate_deal_number()
                        new_deal = {"id": did, "client_id": cl["id"], "title": dn, "deal_number": dn, "deal_title": cd_title.strip(), "budget": int(cd_budget) if cd_budget and cd_budget.strip().isdigit() else 0, "status": "Новый", "manager": cd_mgr, "deal_comments": [], "deal_files": [], "payment_status": "Не оплачено", "close_files": [], "last_modified": now_str(), "created_at": now_str(), "deal_chat": []}
                        st.session_state.crm_store.setdefault("deals", []).append(new_deal)
                        cl["last_modified"] = now_str()
                        st.session_state[show_cd_key] = False
                        st.session_state.auto_expand_deal_id = did
                        commit_and_rerun(st.session_state.crm_store, "Сделка создана")

def render_client_form(fv):
    with st.expander("Добавить клиента", expanded=False, key=f"add_client_form_{fv}"):
        acl, acr = st.columns(2)
        with acl:
            cn = st.text_input("ФИО / Компания", key=f"cn_{fv}")
            cp = st.text_input("Основной телефон", key=f"cp_{fv}")
            ce = st.text_input("Основной Email", key=f"ce_{fv}")
            cd = st.number_input("Скидка (%)", min_value=0, max_value=100, step=1, value=None, key=f"cd_{fv}")
            cm = st.selectbox("Ответственный:", get_managers_list(), index=0, key=f"cm_{fv}", placeholder=MGR_PLACEHOLDER)
        with acr:
            ca = st.text_input("Основной адрес", key=f"ca_{fv}")
            cc = st.selectbox("Категория", [""] + CATEGORIES, index=0, key=f"cc_{fv}", placeholder="Выбери категорию")
            with st.container(border=True):
                st.markdown("**Комментарии:**")
                cc_form_clr = f"clr_cc_form_{fv}"
                if st.session_state.get(cc_form_clr):
                    st.session_state[f"new_cc_form_{fv}"] = ""
                    st.session_state[cc_form_clr] = False
                ncc = st.text_input("Добавить комментарий:", key=f"new_cc_form_{fv}", placeholder="Введите комментарий...")
                if st.button("Добавить комментарий", key=f"cc_form_btn_{fv}", use_container_width=True):
                    if ncc.strip():
                        st.session_state.setdefault("pending_client_comments", []).append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": ncc.strip()})
                        st.session_state[cc_form_clr] = True
                        st.rerun()
                    else: st.warning("Введите текст")
                if st.session_state.get("pending_client_comments"):
                    for pc in st.session_state["pending_client_comments"]:
                        st.markdown(f"- *{pc['time']}*: {pc['text']}")
        st.markdown("---")
        ac_ph, ac_em, ac_ad = st.columns(3)
        with ac_ph:
            st.markdown("**Доп. телефоны**")
            for i, ph in enumerate(st.session_state.f_ph):
                st.session_state.f_ph[i]["phone"] = st.text_input(f"Телефон #{i+1}", value=ph["phone"], key=f"f_ph_{fv}_{i}")
                st.session_state.f_ph[i]["name"] = st.text_input(f"ФИО #{i+1}", value=ph["name"], key=f"f_nm_{fv}_{i}")
                st.session_state.f_ph[i]["role"] = st.text_input(f"Должность #{i+1}", value=ph["role"], key=f"f_rl_{fv}_{i}")
            if st.button("Добавить телефон", key=f"add_ph_btn_{fv}"):
                st.session_state.f_ph.append({"phone": "", "name": "", "role": ""})
                st.rerun()
        with ac_em:
            st.markdown("**Доп. Email**")
            for i, em in enumerate(st.session_state.f_em):
                st.session_state.f_em[i] = st.text_input(f"Email #{i+1}", value=em, key=f"f_em_{fv}_{i}")
            if st.button("Добавить Email", key=f"add_em_btn_{fv}"):
                st.session_state.f_em.append("")
                st.rerun()
        with ac_ad:
            st.markdown("**Доп. адреса**")
            for i, ad in enumerate(st.session_state.f_ad):
                st.session_state.f_ad[i]["address"] = st.text_input(f"Адрес #{i+1}", value=ad.get("address", ""), key=f"f_ad_addr_{fv}_{i}")
                st.session_state.f_ad[i]["resp_name"] = st.text_input(f"Ответственный #{i+1}", value=ad.get("resp_name", ""), key=f"f_ad_rn_{fv}_{i}")
                st.session_state.f_ad[i]["resp_role"] = st.text_input(f"Должность #{i+1}", value=ad.get("resp_role", ""), key=f"f_ad_rr_{fv}_{i}")
                st.session_state.f_ad[i]["resp_phone"] = st.text_input(f"Телефон #{i+1}", value=ad.get("resp_phone", ""), key=f"f_ad_rp_{fv}_{i}")
                st.session_state.f_ad[i]["resp_email"] = st.text_input(f"Email #{i+1}", value=ad.get("resp_email", ""), key=f"f_ad_re_{fv}_{i}")
            if st.button("Добавить адрес", key=f"add_ad_btn_{fv}"):
                st.session_state.f_ad.append({"address": "", "resp_name": "", "resp_role": "", "resp_phone": "", "resp_email": ""})
                st.rerun()
        st.markdown("---")
        cf = st.file_uploader("Прикрепить файлы:", key=f"cf_{fv}", accept_multiple_files=True)
        if st.button("Внести клиента в базу", use_container_width=True, type="primary", key=f"add_client_btn_{fv}"):
            if cn and cp:
                if not cm: st.error("Выберите ответственного")
                elif not cc: st.error("Выберите категорию")
                else:
                    clients = st.session_state.crm_store["clients"]
                    nid = (max([c['id'] for c in clients]) if clients else 0) + 1
                    nc = {"id": nid, "name": cn, "phone": format_phone(cp), "email": ce, "address": ca, "category": cc, "discount": int(cd) if cd is not None else 0, "base_comment": "", "manager": cm, "extra_phones": [{"phone": format_phone(p["phone"]), "name": p["name"], "role": p["role"]} for p in st.session_state.f_ph if p["phone"].strip()], "extra_emails": [e for e in st.session_state.f_em if e.strip()], "extra_addresses": [{"address": a["address"], "resp_name": a["resp_name"], "resp_role": a["resp_role"], "resp_phone": a["resp_phone"], "resp_email": a["resp_email"]} for a in st.session_state.f_ad if a["address"].strip()], "client_files": [], "client_comments": [], "comments": [], "tasks": [], "last_modified": now_str(), "created_at": now_str(), "client_chat": []}
                    if cf:
                        fi_list = save_uploaded_files(cf, nid, "profile")
                        if fi_list: nc["client_files"].extend(normalize_file_list(fi_list))
                    if st.session_state.get("pending_client_comments"):
                        nc["client_comments"] = list(st.session_state["pending_client_comments"])
                        st.session_state["pending_client_comments"] = []
                    st.session_state.crm_store["clients"].append(nc)
                    save_data(st.session_state.crm_store)
                    st.session_state.f_ph, st.session_state.f_em, st.session_state.f_ad = [], [], []
                    st.session_state.last_id = nid
                    st.session_state.client_form_version += 1
                    st.session_state.expanded_client_id = nid
                    st.toast(f"Клиент {cn} добавлен", icon="✅")
                    st.rerun()
            else: st.error("Заполните ФИО и телефон")
@st.dialog("Подробности задачи", width="large")
@st.fragment
def task_detail_dialog(task, cl, d, key_prefix):
    render_task_detail(task, cl, d, key_prefix)
if st.session_state.active_tab == "Клиенты":
    fv = st.session_state.client_form_version
    render_client_form(fv)
    st.markdown("### Поиск")
    sq = st.text_input("По имени, компании или телефону:", key="search_input_key", placeholder="Введите текст...").strip().lower()
    cat_options = ["Все"] + CATEGORIES
    ctf = st.selectbox("Категория:", cat_options, index=0, key="cat_filter")
    all_clients = st.session_state.crm_store["clients"]
    fcl = []
    sd = re.sub(r"\D", "", sq)
    if sd and sd[0] in ("7", "8") and len(sd) > 1: sd = sd[1:]
    for cl in all_clients:
        if ctf != "Все" and cl.get("category", "Не определён") != ctf: continue
        if sq:
            ct = f"{cl['name']} {cl.get('email','')} {cl.get('address','')} {cl.get('base_comment','')}".lower()
            mb = sq in ct
            acd = re.sub(r"\D", "", cl['phone'])
            for p in cl.get("extra_phones", []):
                acd += " " + re.sub(r"\D", "", p["phone"])
                ct += " " + p["name"].lower()
            mp = sd and (sd in acd)
            if not (mb or mp or sq in ct): continue
        fcl.append(cl)
    if all_clients:
        fcl.sort(key=lambda c: get_sort_key(c), reverse=True)
        for cl in fcl:
            active_ids = set()
            if st.session_state.expanded_client_id is not None:
                active_ids.add(st.session_state.expanded_client_id)
            if st.session_state.expanded_tree_id is not None:
                active_ids.add(st.session_state.expanded_tree_id)
            if active_ids and cl["id"] not in active_ids:
                continue
            render_client_in_tree(cl)
    else:
        st.info("База клиентов пуста. Создайте первого клиента.")

elif st.session_state.active_tab == "Сделки":
    all_deals = st.session_state.crm_store.get("deals", [])
    cid_map = {c["id"]: c for c in st.session_state.crm_store.get("clients", [])}
    # Compute sums
    work_sum = sum(d.get("budget", 0) for d in all_deals if d.get("status", "Новый") == "В работе")
    closed_sum = sum(d.get("budget", 0) for d in all_deals if d.get("status", "") == "Сделка закрыта")
    # Sum metrics (no heading)
    m1, m2 = st.columns(2)
    with m1:
        st.metric("Сумма сделок в работе", f"{work_sum:,.0f} руб.".replace(",", " "))
    with m2:
        st.metric("Сумма завершённых сделок", f"{closed_sum:,.0f} руб.".replace(",", " "))
    # Collapsed sections for closed and archive at top
    with st.expander(f"Успешно завершены ({sum(1 for d in all_deals if d.get('status') == 'Сделка закрыта')})", expanded=False):
        closed_search = st.text_input("Поиск среди завершённых:", key="deal_closed_search", placeholder="Введите текст...").strip().lower()
        closed_deals = [d for d in all_deals if d.get("status") == "Сделка закрыта"]
        if closed_search:
            closed_deals = [d for d in closed_deals if closed_search in f"{d.get('deal_number', '')} {d.get('deal_title', '')} {d.get('title', '')} {(cid_map.get(d.get('client_id'), {}) or {}).get('name', '')}".lower()]
        closed_deals.sort(key=lambda d: d.get("last_modified", ""), reverse=True)
        if closed_deals:
            for d in closed_deals:
                render_deal_standalone(d, cid_map.get(d.get("client_id")), cu)
        else:
            st.caption("Завершённых сделок нет.")
    with st.expander(f"Архив ({sum(1 for d in all_deals if d.get('status') == 'Архив')})", expanded=False):
        arch_search = st.text_input("Поиск среди архива:", key="deal_arch_search", placeholder="Введите текст...").strip().lower()
        arch_deals = [d for d in all_deals if d.get("status") == "Архив"]
        if arch_search:
            arch_deals = [d for d in arch_deals if arch_search in f"{d.get('deal_number', '')} {d.get('deal_title', '')} {d.get('title', '')} {(cid_map.get(d.get('client_id'), {}) or {}).get('name', '')}".lower()]
        arch_deals.sort(key=lambda d: d.get("last_modified", ""), reverse=True)
        if arch_deals:
            for d in arch_deals:
                render_deal_standalone(d, cid_map.get(d.get("client_id")), cu)
        else:
            st.caption("Архив пуст.")
    # Sticky search + manager filter — JS-driven fixed position
    with st.container(key="deals_sticky_header"):
        fc1, fc2 = st.columns([2, 1])
        with fc1:
            deal_search = st.text_input("Поиск по номеру, названию или клиенту:", key="deal_tab_search", placeholder="Введите текст...").strip().lower()
        with fc2:
            mgr_filter = st.selectbox("Ответственный:", ["Все"] + get_managers_list(), index=0, key="deal_tab_mgr")
    st.components.v1.html('''<script>
(function(){
  var w=window;
  try{if(window.parent&&window.parent!==window)w=window.parent;}catch(e){}
  var sel='.st-key-deals_sticky_header';
  function init(){
    var el=w.document.querySelector(sel);
    if(!el){setTimeout(init,200);return;}
    var ph=w.document.createElement('div');
    ph.className='deals-sticky-placeholder';
    el.parentNode.insertBefore(ph,el);
    var fixed=false;
    var origTop=0;
    function measure(){
      var r=el.getBoundingClientRect();
      origTop=r.top+w.scrollY;
    }
    function onScroll(){
      if(fixed){
        if(w.scrollY<origTop-1){
          el.classList.remove('deals-sticky-fixed');
          ph.style.height='0px';
          fixed=false;
        }
      } else {
        var r=el.getBoundingClientRect();
        if(r.top<0){
          measure();
          el.classList.add('deals-sticky-fixed');
          ph.style.height=r.height+'px';
          fixed=true;
        }
      }
    }
    w.addEventListener('scroll',onScroll,{passive:true});
    setTimeout(measure,500);
    setTimeout(onScroll,600);
  }
  init();
})();
</script>''', height=0)
    # Filter deals for "Новые" and "В работе" columns only
    fdeals = []
    for d in all_deals:
        s = d.get("status", "Новый")
        if s not in ("Новый", "В работе"):
            continue
        cl = cid_map.get(d.get("client_id"))
        if mgr_filter != "Все" and d.get("manager", "") != mgr_filter:
            continue
        if deal_search:
            hay = f"{d.get('deal_number', '')} {d.get('deal_title', '')} {d.get('title', '')} {(cl.get('name', '') if cl else '')}".lower()
            if deal_search not in hay:
                continue
        fdeals.append(d)
    fdeals.sort(key=lambda d: d.get("last_modified", ""), reverse=True)
    new_deals = [d for d in fdeals if d.get("status", "Новый") == "Новый"]
    work_deals = [d for d in fdeals if d.get("status", "") == "В работе"]
    col_new, col_work = st.columns(2)
    with col_new:
        with st.container(border=True):
            st.subheader(f"Новые ({len(new_deals)})")
            if new_deals:
                for d in new_deals:
                    render_deal_standalone(d, cid_map.get(d.get("client_id")), cu)
            else:
                st.caption("Новых сделок нет.")
    with col_work:
        with st.container(border=True):
            st.subheader(f"В работе ({len(work_deals)})")
            if work_deals:
                for d in work_deals:
                    render_deal_standalone(d, cid_map.get(d.get("client_id")), cu)
            else:
                st.caption("Сделок в работе нет.")

elif st.session_state.active_tab == "Задачи":
    now_time = datetime.now()
    all_deals = st.session_state.crm_store["deals"]
    active_deals = [d for d in all_deals if d["status"] in ("Новый", "В работе")]
    active_sum = sum(d.get("budget", 0) for d in active_deals)
    overdue_count = sum(1 for c in st.session_state.crm_store.get("clients", []) for t in c.get("tasks", []) if is_task_overdue(t))
    total_clients = len(st.session_state.crm_store["clients"])
    d1, d2, d3 = st.columns(3)
    d1.metric("Активные сделки", len(active_deals), f"{active_sum:,.0f} руб.".replace(",", " "))
    d2.metric("Просрочено", overdue_count)
    d3.metric("Клиентов", total_clients)
    st.markdown("---")
    plan_sub1, plan_sub2 = st.tabs(["Активные", "Архив"])
    with plan_sub1:
        col_mf, col_sq = st.columns([1, 2])
        with col_mf:
            mf = st.selectbox("Ответственный", ["Мои задачи", "Все"] + get_managers_list(), index=0, key="task_filter_mgr")
        with col_sq:
            task_search = st.text_input("Поиск по задачам:", key="task_search_input", placeholder="Искать по тексту, клиенту, номеру...").strip().lower()
        di = {d["id"]: d for d in st.session_state.crm_store.get("deals", [])}
        aat = []
        new_tasks = []
        review_tasks = []
        for cl in st.session_state.crm_store.get("clients", []):
            for ti, tk in enumerate(cl.get("tasks", [])):
                tm = tk.get("manager", "")
                dtm = tk.get("delegated_to", "")
                if mf == "Мои задачи":
                    if tm and tm != cu and dtm != cu: continue
                elif mf != "Все":
                    if tm != mf and dtm != mf: continue
                if task_search:
                    search_text = f"{tk.get('text', '')} {tk.get('task_number', '')} {cl.get('name', '')} {cl.get('phone', '')} {tk.get('products', '')} {tk.get('ship_addr', '')} {tk.get('receiver', '')}".lower()
                    if task_search not in search_text: continue
                task_deal = di.get(tk.get("deal_id"))
                mdt = task_deal.get("deal_number", task_deal["title"]) if task_deal else ""
                entry = {"client_id": cl["id"], "client_name": cl["name"], "client_phone": cl["phone"], "deal_title": mdt, "sort_date": get_task_sort_date(tk), "deadline_str": tk.get("deadline", ""), "type": tk.get("type", "Связаться"), "text": tk.get("text", ""), "task_obj": tk, "task_idx": ti, "client_obj": cl}
                if tk.get("done", False) and not tk.get("reviewed", False):
                    is_author = (st.session_state.user_role == "admin") or (tk.get("created_by", "") == st.session_state.get("user_login", ""))
                    if is_author:
                        review_tasks.append(entry)
                elif not tk.get("done", False):
                    if not tk.get("in_work", False):
                        new_tasks.append(entry)
                    else:
                        aat.append(entry)
        aat.sort(key=lambda x: x["sort_date"])
        new_tasks.sort(key=lambda x: x["sort_date"])
        review_tasks.sort(key=lambda x: x["sort_date"])
        tt_list = [t for t in aat if t["sort_date"] <= now_time.date()]
        ft_list = [t for t in aat if t["sort_date"] > now_time.date()]
        def render_task_block(t, sk):
            task = t["task_obj"]
            cl = t["client_obj"]
            tp = task.get("type", "Связаться")
            io_ = is_task_overdue(task)
            fd = format_date(t["deadline_str"])
            task_key = f"tb_{sk}_{t['client_id']}_{t['task_idx']}"
            if task.get("needs_rework"): tk_bg, tk_bc = "#FFEBEE", "#D32F2F"
            elif io_: tk_bg, tk_bc = "#FFEBEE", "#C62828"
            elif task.get("in_work"): tk_bg, tk_bc = "#E8F5E9", "#4CAF50"
            else: tk_bg, tk_bc = "#E3F2FD", "#2196F3"
            exp_label = f"Задача №{task.get('task_number', '')} {fd} — {t['client_name']} — {t['text']}"
            if task.get('needs_rework'): exp_label += ' | На доработке'
            elif task.get('in_work'): exp_label += ' | В работе'
            if task.get('ready_to_ship'): exp_label += ' | Готово к отправке'
            st.markdown(f"<style>.st-key-tb_wrap_{task_key} button {{ background-color: {tk_bg} !important; color: #2C3E50 !important; border: 2px solid {tk_bc} !important; border-radius: 10px !important; }}</style>", unsafe_allow_html=True)
            with st.container(key=f"tb_wrap_{task_key}"):
                if st.button(exp_label, key=f"tb_btn_{task_key}", use_container_width=True):
                    st.session_state["dialog_task_key"] = task_key
                    st.rerun()
                render_scroll_restore(f"tb_{task_key}")
        col_new, col_today, col_future, col_review = st.columns(4)
        with col_new:
            with st.container(border=True):
                st.subheader(f"Новые ({len(new_tasks)})")
                if new_tasks:
                    for t in new_tasks: render_task_block(t, "new")
                else: st.caption("Новых задач нет.")
        with col_today:
            with st.container(border=True):
                st.subheader(f"На сегодня ({len(tt_list)})")
                if tt_list:
                    for t in tt_list: render_task_block(t, "today")
                else: st.success("Все задачи на сегодня закрыты.")
        with col_future:
            with st.container(border=True):
                st.subheader(f"Предстоящие ({len(ft_list)})")
                if ft_list:
                    for t in ft_list: render_task_block(t, "future")
                else: st.caption("План на будущие дни пуст.")
        with col_review:
            with st.container(border=True):
                st.subheader(f"На проверке ({len(review_tasks)})")
                if review_tasks:
                    for t in review_tasks: render_task_block(t, "review")
                else: st.caption("Задач на проверке нет.")
    with plan_sub2:
        archived_tasks = []
        for cl in st.session_state.crm_store.get("clients", []):
            for ti, tk in enumerate(cl.get("tasks", [])):
                if tk.get("done", False):
                    archived_tasks.append({"client_name": cl["name"], "task_obj": tk, "client_obj": cl, "task_idx": ti})
        archived_tasks.sort(key=lambda x: x["task_obj"].get("last_modified", ""), reverse=True)
        if archived_tasks:
            for at in archived_tasks[:50]:
                task = at["task_obj"]
                cl = at["client_obj"]
                task_key = f"arch_{at['task_idx']}_{cl['id']}"
                exp_label = f"✅ Задача №{task.get('task_number', '')} — {at['client_name']} — {task.get('text', '')} | {format_date(task.get('deadline', ''))}"
                with st.container(key=f"arch_wrap_{task_key}"):
                    if st.button(exp_label, key=f"arch_btn_{task_key}", use_container_width=True):
                        st.session_state["dialog_task_key"] = task_key
                        st.rerun()
        else:
            st.caption("Архив пуст.")
    # Show task detail dialog if requested
    _dialog_key = st.session_state.get("dialog_task_key")
    if _dialog_key:
        _found = False
        for _cl in st.session_state.crm_store.get("clients", []):
            if _found: break
            for _ti, _tk in enumerate(_cl.get("tasks", [])):
                _tk_keys = [f"tb_new_{_cl['id']}_{_ti}", f"tb_today_{_cl['id']}_{_ti}", f"tb_future_{_cl['id']}_{_ti}", f"tb_review_{_cl['id']}_{_ti}", f"arch_{_ti}_{_cl['id']}"]
                if _dialog_key in _tk_keys:
                    _deal = None
                    for _d in st.session_state.crm_store.get("deals", []):
                        if _d["id"] == _tk.get("deal_id"):
                            _deal = _d
                            break
                    task_detail_dialog(_tk, _cl, _deal, _dialog_key)
                    _found = True
                    break

elif st.session_state.active_tab == "Внутренние задачи":
    st.markdown("### Внутренние задачи")
    internal_tasks = st.session_state.crm_store.setdefault("internal_tasks", [])

    show_it_key = "show_it_form"
    if render_centered_button("Создать внутреннюю задачу", key="btn_new_it"):
        st.session_state[show_it_key] = not st.session_state.get(show_it_key, False)
        st.rerun()
    if st.session_state.get(show_it_key, False):
        with st.container(border=True):
            it_topic = st.text_input("Тема задачи:", key="it_topic")
            it_mgr = st.selectbox("Ответственный:", get_managers_list(), index=0, key="it_mgr", placeholder=MGR_PLACEHOLDER)
            it_dl = st.date_input("Срок:", format="DD.MM.YYYY", key="it_dl")
            it_comment = st.text_area("Комментарии:", key="it_comment")
            if st.button("Создать", key="it_go", use_container_width=True, type="primary"):
                if not it_topic.strip():
                    st.warning("Введите тему задачи")
                elif not it_mgr:
                    st.warning("Выберите ответственного")
                else:
                    new_it = {
                        "id": (max([_safe_id(t.get("id", 0)) for t in internal_tasks], default=0)) + 1,
                        "text": it_topic.strip(),
                        "deadline": it_dl.isoformat(),
                        "done": False,
                        "manager": it_mgr,
                        "comment": it_comment.strip(),
                        "created_at": now_str(),
                        "last_modified": now_str(),
                        "completed_report": ""
                    }
                    internal_tasks.append(new_it)
                    add_notification(it_mgr, f"Новая внутренняя задача: {it_topic.strip()} | Срок: {it_dl.isoformat()}", f"\U0001F4DD Новая внутренняя задача: {it_topic.strip()} | Срок: {it_dl.isoformat()}")
                    st.session_state[show_it_key] = False
                    commit_and_rerun(st.session_state.crm_store, "Внутренняя задача создана")

    st.markdown("---")
    it_filter = st.radio("Фильтр:", ["Активные", "Выполненные", "Все"], index=0, key="it_filter", horizontal=True)

    filtered_it = []
    for it in internal_tasks:
        if it_filter == "Активные" and it.get("done"): continue
        if it_filter == "Выполненные" and not it.get("done"): continue
        filtered_it.append(it)
    filtered_it.sort(key=lambda t: t.get("deadline", ""), reverse=False)

    if filtered_it:
        for it in filtered_it:
            it_key = f"it_{it['id']}"
            it_exp = st.session_state.expanded_task_key == it_key
            it_done = it.get("done", False)
            it_overdue = False
            if not it_done and it.get("deadline"):
                try:
                    dl = datetime.strptime(it["deadline"][:10], "%Y-%m-%d").replace(hour=23, minute=59)
                    if dl < datetime.now(): it_overdue = True
                except: pass
            if it_done: it_bg, it_bc = "#F5F6F8", "#C9CFD7"
            elif it_overdue: it_bg, it_bc = "#FFEBEE", "#C62828"
            else: it_bg, it_bc = "#E8F5E9", "#4CAF50"
            it_label = f"{'✅' if it_done else '⏳'} Задача №{it['id']} — {it.get('text', '')} | {format_date(it.get('deadline', ''))} | {it.get('manager', '—')}"
            it_selected = it_exp
            it_border = "#2196F3" if it_selected else it_bc
            it_shadow = "box-shadow: 0 0 0 2px rgba(33,150,243,0.3);" if it_selected else ""
            st.markdown(f"<style>.st-key-it_wrap_{it['id']} button {{ background-color: {it_bg} !important; color: #2C3E50 !important; border: 2px solid {it_border} !important; border-radius: 10px !important; {it_shadow} }}</style>", unsafe_allow_html=True)
            with st.container(key=f"it_wrap_{it['id']}"):
                if st.button(it_label, key=f"it_card_{it['id']}", use_container_width=True, type="primary" if it_exp else "secondary"):
                    if it_exp:
                        st.session_state.expanded_task_key = None
                        save_scroll_and_rerun()
                    else:
                        st.session_state.expanded_task_key = it_key
                        st.rerun()
                if not it_exp:
                    render_scroll_restore(f"it_{it['id']}")
            if it_exp:
                with st.container(border=True):
                    st.markdown(f"**Задача №{it['id']}**")
                    st.markdown(f"**Тема:** {it.get('text', '')}")
                    st.markdown(f"**Срок:** {format_date(it.get('deadline', ''))}")
                    st.markdown(f"**Ответственный:** {it.get('manager', '—')}")
                    if it.get("comment"): st.markdown(f"**Комментарий:** {it['comment']}")
                    if it.get("completed_report"): st.markdown(f"**Отчёт:** {it['completed_report']}")
                    st.markdown("---")
                    if not it_done:
                        show_it_complete = f"show_it_complete_{it['id']}"
                        if st.button("Выполнить", key=f"it_complete_btn_{it['id']}", type="primary", use_container_width=True):
                            st.session_state[show_it_complete] = not st.session_state.get(show_it_complete, False)
                            st.rerun()
                        if st.session_state.get(show_it_complete, False):
                            it_report = st.text_area("Отчёт:", key=f"it_report_{it['id']}", height=80)
                            if st.button("Подтвердить", key=f"it_complete_go_{it['id']}", type="primary", use_container_width=True):
                                if it_report.strip():
                                    it["done"] = True
                                    it["completed_report"] = it_report.strip()
                                    it["last_modified"] = now_str()
                                    st.session_state[show_it_complete] = False
                                    commit_and_rerun(st.session_state.crm_store, "Задача выполнена")
                                else:
                                    st.warning("Введите отчёт")
                        st.markdown("---")
                        show_it_edit = f"show_it_edit_{it['id']}"
                        if st.button("Редактировать", key=f"it_edit_btn_{it['id']}", use_container_width=True):
                            st.session_state[show_it_edit] = not st.session_state.get(show_it_edit, False)
                            st.rerun()
                        if st.session_state.get(show_it_edit, False):
                            with st.container(border=True):
                                eit_topic = st.text_input("Тема:", value=it.get("text", ""), key=f"eit_topic_{it['id']}")
                                eit_mgr = st.selectbox("Ответственный:", get_managers_list(), index=0 if it.get("manager", "") not in get_managers_list() else (get_managers_list()).index(it.get("manager", "")), key=f"eit_mgr_{it['id']}", placeholder=MGR_PLACEHOLDER)
                                eit_dl = st.date_input("Срок:", value=parse_deadline(it.get("deadline", "")), format="DD.MM.YYYY", key=f"eit_dl_{it['id']}")
                                eit_comment = st.text_area("Комментарий:", value=it.get("comment", ""), key=f"eit_comment_{it['id']}")
                                if st.button("Сохранить", key=f"eit_save_{it['id']}", type="primary", use_container_width=True):
                                    if not eit_mgr:
                                        st.warning("Выберите ответственного")
                                    else:
                                        it["text"] = eit_topic
                                        it["manager"] = eit_mgr
                                        it["deadline"] = eit_dl.isoformat()
                                        it["comment"] = eit_comment
                                        it["last_modified"] = now_str()
                                        st.session_state[show_it_edit] = False
                                        commit_and_rerun(st.session_state.crm_store, "Задача обновлена")
                    if st.session_state.user_role == "admin":
                        st.markdown("---")
                        if st.button("Удалить задачу", key=f"it_del_{it['id']}", use_container_width=True):
                            st.session_state.crm_store["internal_tasks"] = [x for x in internal_tasks if x["id"] != it["id"]]
                            st.session_state.expanded_task_key = None
                            commit_and_rerun(st.session_state.crm_store, "Задача удалена")
    else:
        st.info("Внутренних задач нет.")

elif st.session_state.active_tab == "Поставщики":
    st.markdown("### Поставщики")
    suppliers = st.session_state.crm_store.setdefault("suppliers", [])

    show_sup_key = "show_sup_form"
    if render_centered_button("Добавить поставщика", key="btn_new_sup"):
        st.session_state[show_sup_key] = not st.session_state.get(show_sup_key, False)
        st.rerun()
    if st.session_state.get(show_sup_key, False):
        with st.container(border=True):
            sup_name = st.text_input("Название / Имя:", key="sup_name")
            sup_phone = st.text_input("Телефон:", key="sup_phone")
            sup_email = st.text_input("Email:", key="sup_email")
            sup_address = st.text_input("Адрес:", key="sup_address")
            sup_category = st.text_input("Категория товаров:", key="sup_category", placeholder="Что поставляет")
            sup_comment = st.text_area("Комментарии:", key="sup_comment")
            if st.button("Сохранить", key="sup_go", use_container_width=True, type="primary"):
                if not sup_name.strip():
                    st.warning("Введите название")
                else:
                    new_sup = {
                        "id": (max([s.get("id", 0) for s in suppliers], default=0)) + 1,
                        "name": sup_name.strip(),
                        "phone": format_phone(sup_phone) if sup_phone else "",
                        "email": sup_email.strip(),
                        "address": sup_address.strip(),
                        "category": sup_category.strip(),
                        "comment": sup_comment.strip(),
                        "created_at": now_str(),
                        "last_modified": now_str()
                    }
                    suppliers.append(new_sup)
                    st.session_state[show_sup_key] = False
                    commit_and_rerun(st.session_state.crm_store, "Поставщик добавлен")

    st.markdown("---")
    sup_search = st.text_input("Поиск поставщика:", key="sup_search", placeholder="По названию, телефону, категории...").strip().lower()

    filtered_sup = []
    for s in suppliers:
        if sup_search:
            st_text = f"{s.get('name', '')} {s.get('phone', '')} {s.get('email', '')} {s.get('category', '')} {s.get('comment', '')}".lower()
            if sup_search not in st_text: continue
        filtered_sup.append(s)
    filtered_sup.sort(key=lambda s: s.get("name", "").lower())

    if filtered_sup:
        for s in filtered_sup:
            sup_key = f"sup_{s['id']}"
            sup_exp = st.session_state.expanded_task_key == sup_key
            sup_label = f"{s.get('name', 'Без названия')} — {s.get('phone', '—')} | {s.get('category', '—')}"
            sup_selected = sup_exp
            sup_border = "#2196F3" if sup_selected else "#DCE0E5"
            sup_shadow = "box-shadow: 0 0 0 2px rgba(33,150,243,0.3);" if sup_selected else ""
            st.markdown(f"<style>.st-key-sup_wrap_{s['id']} button {{ background-color: #FFFFFF !important; color: #2C3E50 !important; border: 2px solid {sup_border} !important; border-radius: 10px !important; {sup_shadow} }}</style>", unsafe_allow_html=True)
            with st.container(key=f"sup_wrap_{s['id']}"):
                if st.button(sup_label, key=f"sup_card_{s['id']}", use_container_width=True, type="primary" if sup_exp else "secondary"):
                    if sup_exp:
                        st.session_state.expanded_task_key = None
                        save_scroll_and_rerun()
                    else:
                        st.session_state.expanded_task_key = sup_key
                        st.rerun()
                if not sup_exp:
                    render_scroll_restore(f"sup_{s['id']}")
            if sup_exp:
                with st.container(border=True):
                    st.markdown(f"**{s.get('name', '')}**")
                    st.markdown(format_created_date(s), unsafe_allow_html=True)
                    if s.get("phone"):
                        render_phone_inline(s["phone"], f"sup_{s['id']}")
                    info_c, comm_c = st.columns(2)
                    with info_c:
                        st.markdown(f"**Email:** {s.get('email', '—')}")
                        st.markdown(f"**Адрес:** {s.get('address', '—')}")
                        st.markdown(f"**Категория:** {s.get('category', '—')}")
                    with comm_c:
                        if s.get("comment"):
                            st.markdown(f"**Комментарий:** {s['comment']}")
                        else:
                            st.caption("Комментариев нет")
                    st.markdown("---")
                    show_sup_edit = f"show_sup_edit_{s['id']}"
                    if st.button("Редактировать" if not st.session_state.get(show_sup_edit, False) else "Скрыть", key=f"sup_edit_toggle_{s['id']}", use_container_width=True):
                        st.session_state[show_sup_edit] = not st.session_state.get(show_sup_edit, False)
                        st.rerun()
                    if st.session_state.get(show_sup_edit, False):
                        with st.container(border=True):
                            esn = st.text_input("Название:", value=s.get("name", ""), key=f"esn_{s['id']}")
                            esp = st.text_input("Телефон:", value=s.get("phone", ""), key=f"esp_{s['id']}")
                            ese = st.text_input("Email:", value=s.get("email", ""), key=f"ese_{s['id']}")
                            esa = st.text_input("Адрес:", value=s.get("address", ""), key=f"esa_{s['id']}")
                            esc = st.text_input("Категория:", value=s.get("category", ""), key=f"esc_{s['id']}")
                            escom = st.text_area("Комментарий:", value=s.get("comment", ""), key=f"escom_{s['id']}")
                            if st.button("Сохранить", key=f"es_save_{s['id']}", type="primary", use_container_width=True):
                                s["name"] = esn.strip()
                                s["phone"] = format_phone(esp) if esp else ""
                                s["email"] = ese.strip()
                                s["address"] = esa.strip()
                                s["category"] = esc.strip()
                                s["comment"] = escom.strip()
                                s["last_modified"] = now_str()
                                st.session_state[show_sup_edit] = False
                                commit_and_rerun(st.session_state.crm_store, "Поставщик обновлён")
                    if st.session_state.user_role == "admin":
                        st.markdown("---")
                        if st.button("Удалить поставщика", key=f"sup_del_{s['id']}", use_container_width=True):
                            st.session_state.crm_store["suppliers"] = [x for x in suppliers if x["id"] != s["id"]]
                            st.session_state.expanded_task_key = None
                            commit_and_rerun(st.session_state.crm_store, "Поставщик удалён")
    else:
        st.info("Поставщиков нет. Добавьте первого.")
