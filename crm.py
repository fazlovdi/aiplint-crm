import streamlit as st
import streamlit.components.v1 as components
import json, os, re, urllib.parse, requests, hashlib, base64, csv, io, secrets, threading, uuid
from datetime import datetime
from collections import defaultdict

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
    .thumb-item { position:relative; width:110px; }
    .thumb-item img { width:110px; height:110px; object-fit:cover; border-radius:8px; cursor:pointer; border:1px solid #DCE0E5; }
    .thumb-item img:hover { border-color:#bc1661; }
    .thumb-name { font-size:0.7rem; color:#7F8C9A; max-width:110px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .created-date { font-size: 0.72rem; color: #95A5B7; font-style: italic; }
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
        function success() { btn.textContent = '\\u2713 \u0421\u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u043d\u043e'; setTimeout(function() { btn.textContent = oldText; }, 1500); }
        function fail() { btn.textContent = '\u041e\u0448\u0438\u0431\u043a\u0430'; setTimeout(function() { btn.textContent = oldText; }, 1500); }
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
</script>
""", height=0)

FILE_NAME = "web_crm_database_v2.json"
YANDEX_API_URL = "https://cloud-api.yandex.net/v1/disk/resources"
MAX_URL = "https://max.ru"
MAX_NUMBER = "+79003293300"
CATEGORIES = ["\u041d\u0435 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0451\u043d", "\u0414\u0438\u0437\u0430\u0439\u043d\u0435\u0440", "\u0421\u0442\u0440\u043e\u0438\u0442\u0435\u043b\u044c", "\u0414\u0438\u043b\u0435\u0440", "\u041f\u043e\u043a\u0443\u043f\u0430\u0442\u0435\u043b\u044c"]
TASK_TYPES = ["\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b"]
SHIP_PAY_OPTIONS = ["", "\u0412\u043a\u043b\u044e\u0447\u0435\u043d\u043e \u0432 \u0441\u0447\u0451\u0442", "\u041a\u043b\u0438\u0435\u043d\u0442\u043e\u043c \u043f\u0440\u0438 \u043f\u043e\u043b\u0443\u0447\u0435\u043d\u0438\u0438"]

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
        if dn.startswith(f"\u0421\u0434\u0435\u043b\u043a\u0430 \u2116{year}-"):
            try: max_num = max(max_num, int(dn.split("-")[1]))
            except: pass
    return f"\u0421\u0434\u0435\u043b\u043a\u0430 \u2116{year}-{max_num + 1}"

def assign_task_numbers(data):
    year = datetime.now().strftime("%y")
    zk_max, zs_max = 0, 0
    for c in data.get("clients", []):
        for t in c.get("tasks", []):
            tn = t.get("task_number", "")
            if tn.startswith(f"\u0417\u041a{year}-"):
                try: zk_max = max(zk_max, int(tn.split("-")[1]))
                except: pass
            elif tn.startswith(f"\u0417\u0421{year}-"):
                try: zs_max = max(zs_max, int(tn.split("-")[1]))
                except: pass
    for c in data.get("clients", []):
        for t in c.get("tasks", []):
            if not t.get("task_number"):
                if t.get("deal_id"):
                    zs_max += 1
                    t["task_number"] = f"\u0417\u0421{year}-{zs_max}"
                else:
                    zk_max += 1
                    t["task_number"] = f"\u0417\u041a{year}-{zk_max}"

def assign_deal_numbers(data):
    year = datetime.now().strftime("%y")
    max_num = 0
    for d in data.get("deals", []):
        dn = d.get("deal_number", "")
        if dn.startswith(f"\u0421\u0434\u0435\u043b\u043a\u0430 \u2116{year}-"):
            try: max_num = max(max_num, int(dn.split("-")[1]))
            except: pass
    for d in data.get("deals", []):
        if not d.get("deal_number"):
            max_num += 1
            d["deal_number"] = f"\u0421\u0434\u0435\u043b\u043a\u0430 \u2116{year}-{max_num}"
        if d.get("title", "").startswith("\u0417\u0430\u043a\u0430\u0437"):
            d["title"] = d.get("deal_number", d["title"])

def inject_payment_container_css(deal_id, status):
    border_color = "#2E7D32" if status == "\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043e" else "#C62828"
    bg_color = "#E8F5E9" if status == "\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043e" else "#FFEBEE"
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
        db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "\u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440"}], "_migrated": "v2", "internal_tasks": [], "chat_messages": [], "qa_entries": [], "suppliers": []}
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
        st.warning("\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0437\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u043d\u0430 \u0414\u0438\u0441\u043a, \u0444\u0430\u0439\u043b \u0441\u043e\u0445\u0440\u0430\u043d\u0451\u043d \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e")
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
    w.writerow(["ID", "\u0424\u0418\u041e", "\u0422\u0435\u043b\u0435\u0444\u043e\u043d", "Email", "\u0410\u0434\u0440\u0435\u0441", "\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f", "\u0421\u043a\u0438\u0434\u043a\u0430 %", "\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439"])
    for c in st.session_state.crm_store["clients"]:
        w.writerow([c["id"], c["name"], c["phone"], c.get("email", ""), c.get("address", ""), c.get("category", ""), c.get("discount", 0), c.get("manager", "")])
    return ("\uFEFF" + o.getvalue()).encode("utf-8")

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
    try: return datetime.strptime(ds, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        try: return datetime.strptime(ds, "%Y-%m-%d %H:%M").strftime("%d/%m/%Y")
        except: return ds

def format_created_date(entity):
    cd = entity.get("created_at") or entity.get("last_modified", "")
    if not cd or cd == "1970-01-01 00:00:00": return ""
    try:
        dt = datetime.strptime(cd[:19], "%Y-%m-%d %H:%M:%S")
        return f'<div class="created-date">\u0421\u043e\u0437\u0434\u0430\u043d\u043e: {dt.strftime("%d.%m.%Y %H:%M")}</div>'
    except:
        try:
            dt = datetime.strptime(cd[:10], "%Y-%m-%d")
            return f'<div class="created-date">\u0421\u043e\u0437\u0434\u0430\u043d\u043e: {dt.strftime("%d.%m.%Y")}</div>'
        except: return ""

def get_managers_list():
    return [u.get("name", u["login"]) for u in st.session_state.crm_store.get("users", []) if u.get("role") != "admin"]

def render_copy_button(text, btn_id, label="\U0001F4CB \u041a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c"):
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
    st.markdown(f'<div class="phone-action-group" style="padding:4px 0;"><span style="font-size:1rem;font-weight:600;color:#2C3E50;">{phone}</span><button onclick="window.crmCopy(\'{phone}\',\'{btn_id}\')" class="phone-btn" id="{btn_id}" title="\u0421\u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c">\U0001F4CB</button><a href="tel:+{cph}" class="phone-btn" title="\u041f\u043e\u0437\u0432\u043e\u043d\u0438\u0442\u044c">\U0001F4DE</a></div>', unsafe_allow_html=True)

def render_extra_phone_inline(phone, name, role, uid):
    cph = re.sub(r"\D", "", phone)
    if cph.startswith("8") and len(cph) == 11: cph = "7" + cph[1:]
    elif not cph: cph = "79990000000"
    info = f"{phone} \u2014 {name} ({role})" if name else phone
    btn_id = f"ep_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f'<div class="phone-action-group" style="padding:4px 0;flex-wrap:wrap;gap:8px;white-space:normal;"><span style="font-size:0.9rem;color:#3C4A5A;flex:1 1 auto;min-width:0;word-break:break-word;">{info}</span><button onclick="window.crmCopy(\'{phone}\',\'{btn_id}\')" class="phone-btn" id="{btn_id}" title="\u0421\u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c">\U0001F4CB</button><a href="tel:+{cph}" class="phone-btn" title="\u041f\u043e\u0437\u0432\u043e\u043d\u0438\u0442\u044c">\U0001F4DE</a></div>', unsafe_allow_html=True)

def render_track_inline(track_num, uid):
    btn_id = f"trk_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f'<div style="display:flex;align-items:center;gap:8px;"><code>{track_num}</code><button onclick="window.crmCopy(\'{track_num}\',\'{btn_id}\')" class="track-copy-btn" id="{btn_id}" title="\u041a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c">\u2398</button></div>', unsafe_allow_html=True)

def get_file_bytes(fp):
    if fp and not fp.startswith("CRM_NE_TROGAT") and os.path.exists(fp):
        try:
            with open(fp, "rb") as f: return f.read()
        except: return None
    rp = normalize_remote_path(fp)
    return download_file_from_yandex(rp) if rp else None

def render_file_thumbs(files, prefix, allow_delete=False):
    if not files:
        st.caption("\u0424\u0430\u0439\u043b\u043e\u0432 \u043d\u0435\u0442")
        return
    img_files, other_files = [], []
    for ff in files:
        fn = ff.get("file_name", ff.get("name", "\u0444\u0430\u0439\u043b"))
        ext = os.path.splitext(fn)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]: img_files.append(ff)
        else: other_files.append(ff)
    if img_files:
        ncols = min(len(img_files), 4)
        cols = st.columns(ncols)
        for i, ff in enumerate(img_files):
            with cols[i % ncols]:
                fp = ff.get("file_path", ff.get("path"))
                fn = ff.get("file_name", ff.get("name", "\u0444\u0430\u0439\u043b"))
                fb = get_file_bytes(fp)
                if fb:
                    ext = os.path.splitext(fn)[1].lower()
                    b64 = base64.b64encode(fb).decode()
                    mt = f"image/{'jpeg' if ext == '.jpg' else ext[1:]}"
                    st.markdown(f'<div class="thumb-item"><img src="data:{mt};base64,{b64}" title="{fn}" onclick="window.crmOpenLightbox && window.crmOpenLightbox(this.src)" /><div class="thumb-name">{fn}</div></div>', unsafe_allow_html=True)
                    st.download_button("\U00002B07", data=fb, file_name=fn, key=f"dl_{prefix}_{i}")
                    if allow_delete and st.session_state.user_role == "admin":
                        if st.button("\U0001F5D1", key=f"del_{prefix}_{i}", help="\u0423\u0434\u0430\u043b\u0438\u0442\u044c"):
                            files.pop(i)
                            commit_and_rerun(st.session_state.crm_store, "\u0424\u0430\u0439\u043b \u0443\u0434\u0430\u043b\u0451\u043d")
    for i, ff in enumerate(other_files):
        fp = ff.get("file_path", ff.get("path"))
        fn = ff.get("file_name", ff.get("name", "\u0444\u0430\u0439\u043b"))
        fb = get_file_bytes(fp)
        if fb:
            ext = os.path.splitext(fn)[1].lower()
            if ext == ".pdf":
                b64 = base64.b64encode(fb).decode()
                pdf_btn_id = f"pdf_view_{prefix}_{i}"
                st.markdown(f'<button class="custom-print-btn" id="{pdf_btn_id}" style="background:#5A6B7D;margin-bottom:4px;">\U0001F4C4 {fn}</button>', unsafe_allow_html=True)
                st.components.v1.html(f"""<script>(function(){{var b=window.parent.document.getElementById('{pdf_btn_id}');if(!b)return;var b64="{b64}";b.addEventListener('click',function(){{var w=window.open('','_blank');if(!w)return;var html='<html><head><title>{fn}</title></head><body style="margin:0"><iframe src="data:application/pdf;base64,'+b64+'" style="width:100vw;height:100vh;border:0"></iframe></body></html>';w.document.open();w.document.write(html);w.document.close();}});}})();</script>""", height=0)
                st.download_button(f"\U00002B07 {fn}", data=fb, file_name=fn, mime="application/pdf", key=f"dl_{prefix}_o_{i}")
            else:
                st.download_button(f"\U0001F4C4 {fn}", data=fb, file_name=fn, key=f"dl_{prefix}_o_{i}")
            if allow_delete and st.session_state.user_role == "admin":
                if st.button("\U0001F5D1 \u0423\u0434\u0430\u043b\u0438\u0442\u044c", key=f"del_{prefix}_o_{i}"):
                    files.pop(len(img_files) + i)
                    commit_and_rerun(st.session_state.crm_store, "\u0424\u0430\u0439\u043b \u0443\u0434\u0430\u043b\u0451\u043d")

def build_print_html(task, cl, tp, fd):
    def esc(s): return str(s if s else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    products_html = esc(task.get('products', '')).replace('\n', '<br>')
    oav = task.get('order_amount', 0)
    cost_html = f"<div style='margin-top:6px;font-size:16px;font-weight:bold;'>\u0421\u0443\u043c\u043c\u0430: {oav:,.0f} \u0440\u0443\u0431.</div>".replace(",", " ") if oav and oav > 0 else ""
    file_reminder = "<div style='color:#D65757;font-weight:bold;margin:14px 0;border:2px solid #D65757;padding:8px;border-radius:8px;'>&#9888; \u041d\u0435 \u0437\u0430\u0431\u0443\u0434\u044c \u0440\u0430\u0441\u043f\u0435\u0447\u0430\u0442\u0430\u0442\u044c \u0432\u043b\u043e\u0436\u0435\u043d\u043d\u044b\u0435 \u0444\u0430\u0439\u043b\u044b!</div>" if task.get("task_files") else ""
    lb = get_logo_base64()
    logo_html = f"<img src='data:image/png;base64,{lb}' width='180' style='float:left;margin-right:20px;'/>" if lb else "<div style='font-size:24px;font-weight:bold;float:left;margin-right:20px;'>\u0410\u0419\u041f\u041b\u0418\u041d\u0422</div>"
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><title>\u0411\u043b\u0430\u043d\u043a \u0437\u0430\u0434\u0430\u0447\u0438</title><style>body {{ font-family: Arial, sans-serif; margin: 40px; color: #222; }} .header {{ text-align: center; border-bottom: 2px solid #333; padding: 10px; }} .row {{ margin: 8px 0; }} hr {{ border: none; border-top: 1px solid #ccc; margin: 14px 0; }} .sig {{ margin-top: 30px; }} .sig p {{ margin: 12px 0; }}</style></head><body><div>{logo_html}</div><div class="header"><h2>\u0411\u041b\u0410\u041d\u041a \u0417\u0410\u0414\u0410\u0427\u0418</h2><p>{datetime.now().strftime('%d/%m/%Y')}</p></div><div class="row"><b>\u0417\u0430\u0434\u0430\u0447\u0430:</b> \u2116{esc(task.get('task_number', ''))}</div><div class="row"><b>\u041a\u043b\u0438\u0435\u043d\u0442:</b> {esc(cl['name'])} ({esc(cl['phone'])})</div><div class="row"><b>\u0422\u0438\u043f:</b> {esc(tp)}</div><div class="row"><b>\u0422\u0435\u043c\u0430:</b> {esc(task.get('text', ''))}</div><div class="row"><b>\u0421\u0440\u043e\u043a:</b> {esc(fd)}</div><div class="row"><b>\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:</b> {esc(task.get('manager', ''))}</div><hr><div class="row"><b>\u0422\u043e\u0432\u0430\u0440\u044b:</b><br>{products_html}</div><div class="row"><b>\u0410\u0434\u0440\u0435\u0441:</b> {esc(task.get('ship_addr', ''))}</div><div class="row"><b>\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:</b> {esc(task.get('receiver', ''))} ({esc(task.get('receiver_phone', ''))})</div><div class="row"><b>\u041e\u043f\u043b\u0430\u0442\u0430:</b> {esc(task.get('ship_pay', ''))}</div><div class="row"><b>\u0422\u0440\u0435\u043a:</b> {esc(task.get('tk_num', ''))}</div>{cost_html}{file_reminder}<div class="sig"><p>\u041e\u0442\u043f\u0443\u0441\u0442\u0438\u043b: _____________</p><p>\u041f\u043e\u043b\u0443\u0447\u0438\u043b: _____________</p></div></body></html>"""

def render_print_button(task, cl, tp, fd, key_suffix):
    html_content = build_print_html(task, cl, tp, fd)
    html_json = json.dumps(html_content).replace('<', '\\u003c')
    safe_key = key_suffix.replace('-', '_').replace('.', '_')
    btn_id = f"print_btn_{safe_key}"
    st.markdown(f'<button class="custom-print-btn" id="{btn_id}">\u0420\u0430\u0441\u043f\u0435\u0447\u0430\u0442\u0430\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443</button>', unsafe_allow_html=True)
    st.components.v1.html(f"""<script>(function() {{ var btn = window.parent.document.getElementById('{btn_id}'); if (!btn) return; var html = {html_json}; btn.addEventListener('click', function() {{ var w = window.open('', '_blank'); if (!w) {{ alert('\u0420\u0430\u0437\u0440\u0435\u0448\u0438\u0442\u0435 \u0432\u0441\u043f\u043b\u044b\u0432\u0430\u044e\u0449\u0438\u0435 \u043e\u043a\u043d\u0430'); return; }} w.document.open(); w.document.write(html); w.document.close(); w.focus(); setTimeout(function() {{ try {{ w.print(); }} catch(e) {{}} }}, 500); w.onafterprint = function() {{ setTimeout(function() {{ w.close(); }}, 300); }}; }}); }})();</script>""", height=0)

def render_print_file_button(files, key_suffix):
    if not files: return
    printable = [f for f in files if os.path.splitext(f.get("file_name", f.get("name", "")))[1].lower() in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf"]]
    for i, ff in enumerate(printable):
        fp = ff.get("file_path", ff.get("path"))
        fn = ff.get("file_name", ff.get("name", "\u0444\u0430\u0439\u043b"))
        fb = get_file_bytes(fp)
        if fb:
            ext = os.path.splitext(fn)[1].lower()
            btn_id = f"printfile_{key_suffix}_{i}"
            b64 = base64.b64encode(fb).decode()
            if ext == ".pdf":
                st.markdown(f'<button class="custom-print-btn" id="{btn_id}" style="background:#5A6B7D;margin-top:4px;">\U0001F5A8\uFE0F {fn}</button>', unsafe_allow_html=True)
                st.components.v1.html(f"""<script>(function(){{var b=window.parent.document.getElementById('{btn_id}');if(!b)return;b.addEventListener('click',function(){{var w=window.open('','_blank');if(!w)return;w.document.open();w.document.write('<html><head><title>{fn}</title></head><body style="margin:0"><iframe src="data:application/pdf;base64,{b64}" style="width:100vw;height:100vh;border:0" onload="setTimeout(function(){{try{{window.print()}}catch(e){{}}}},300)"></iframe></body></html>');w.document.close();}});}})();</script>""", height=0)
            else:
                mt = f"image/{'jpeg' if ext == '.jpg' else ext[1:]}"
                st.markdown(f'<button class="custom-print-btn" id="{btn_id}" style="background:#5A6B7D;margin-top:4px;">\U0001F5A8\uFE0F {fn}</button>', unsafe_allow_html=True)
                st.components.v1.html(f"""<script>(function(){{var b=window.parent.document.getElementById('{btn_id}');if(!b)return;b.addEventListener('click',function(){{var w=window.open('','_blank');if(!w)return;w.document.open();w.document.write('<html><head><title>{fn}</title></head><body style="margin:0;text-align:center"><img src="data:{mt};base64,{b64}" style="max-width:100%;max-height:100%" onload="setTimeout(function(){{try{{window.print()}}catch(e){{}}}},300)"/></body></html>');w.document.close();}});}})();</script>""", height=0)

def render_entity_chat(entity, entity_type, entity_id):
    chat_key = f"{entity_type}_chat"
    if chat_key not in entity: entity[chat_key] = []
    chat = entity[chat_key]
    st.markdown("**\u0427\u0430\u0442:**")
    chat_container = st.container(height=200)
    with chat_container:
        for msg in chat[-50:]:
            is_me = msg.get("user") == st.session_state.get("user_name", "")
            cls = "chat-msg-me" if is_me else "chat-msg-other"
            st.markdown(f'<div class="chat-msg {cls}"><div style="font-size:0.75rem;opacity:0.7;margin-bottom:2px;">{msg.get("user","")} \u2014 {msg.get("time","")}</div>{msg.get("text","")}</div>', unsafe_allow_html=True)
        if not chat: st.caption("\u0421\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0439 \u043d\u0435\u0442")
    clr_key = f"clr_{entity_type}_{entity_id}"
    if st.session_state.get(clr_key):
        st.session_state[f"{entity_type}_msg_{entity_id}"] = ""
        st.session_state[clr_key] = False
    msg_text = st.text_input("\u0421\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435:", key=f"{entity_type}_msg_{entity_id}", placeholder="\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435...", label_visibility="collapsed")
    if st.button("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c", key=f"{entity_type}_send_{entity_id}", use_container_width=True):
        if msg_text.strip():
            chat.append({"user": st.session_state.get("user_name", ""), "text": msg_text.strip(), "time": datetime.now().strftime("%d.%m.%Y %H:%M")})
            st.session_state[clr_key] = True
            entity["last_modified"] = now_str()
            commit_and_rerun(st.session_state.crm_store)
        else: st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0442\u0435\u043a\u0441\u0442")

def render_task_edit_form(t, cl, d, key_prefix):
    with st.container(border=True):
        et_topic = st.text_input("\u0422\u0435\u043c\u0430:", value=t.get("text", ""), key=f"edit_topic_{key_prefix}")
        et_type = st.selectbox("\u0422\u0438\u043f:", TASK_TYPES, index=TASK_TYPES.index(t.get("type", "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f")) if t.get("type", "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f") in TASK_TYPES else 0, key=f"edit_type_{key_prefix}")
        et_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", [""] + get_managers_list(), index=0 if t.get("manager", "") not in get_managers_list() else ([""] + get_managers_list()).index(t.get("manager", "")), key=f"edit_mgr_{key_prefix}", placeholder=MGR_PLACEHOLDER)
        et_dl = st.date_input("\u0421\u0440\u043e\u043a:", value=parse_deadline(t.get("deadline", "")), format="DD/MM/YYYY", key=f"edit_dl_{key_prefix}")
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
        if st.button("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", key=f"edit_save_{key_prefix}", use_container_width=True, type="primary"):
            if not et_mgr:
                st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0433\u043e")
            else:
                t["text"] = et_topic
                t["type"] = et_type
                t["manager"] = et_mgr
                t["deadline"] = et_dl.isoformat()
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
MGR_PLACEHOLDER = "\u0412\u044b\u0431\u0435\u0440\u0438 \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0433\u043e"

def commit_and_rerun(store, toast_msg=None):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)
    upload_db_to_yandex_async()
    if toast_msg:
        st.toast(toast_msg)
    st.rerun()

def indented(margin=0.03):
    if margin <= 0:
        return st.container()
    half = margin / 2
    cols = st.columns([half, 1 - margin, half], gap="small")
    return cols[1]

def render_centered_button(label, key, use_container_width=True, type="secondary"):
    with st.container():
        st.markdown('<div class="center-btn-wrap">', unsafe_allow_html=True)
        clicked = st.button(label, key=key, use_container_width=use_container_width, type=type)
        st.markdown('</div>', unsafe_allow_html=True)
    return clicked

def render_centered_title(text):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)

def render_separator():
    st.markdown('<hr style="border:0;height:1px;background:#DCE0E5;margin:0.6rem 0;">', unsafe_allow_html=True)

def render_task_form(deal_id, client_id, key_prefix):
    all_managers = get_managers_list()
    tf_topic = st.text_input("\u0422\u0435\u043c\u0430:", key=f"tf_topic_{key_prefix}")
    tf_type = st.selectbox("\u0422\u0438\u043f:", TASK_TYPES, key=f"tf_type_{key_prefix}")
    tf_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", [""] + all_managers, index=0, key=f"tf_mgr_{key_prefix}", placeholder=MGR_PLACEHOLDER)
    tf_dl = st.date_input("\u0421\u0440\u043e\u043a:", format="DD/MM/YYYY", key=f"tf_dl_{key_prefix}")
    tf_comment = st.text_area("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438:", key=f"tf_comment_{key_prefix}")
    tf_products, tf_addr, tf_recv, tf_rphone, tf_pay, tf_amount, tf_tk = "", "", "", "", "", "", ""
    if tf_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b"):
        tf_products = st.text_area("\u0422\u043e\u0432\u0430\u0440\u044b:", key=f"tf_prod_{key_prefix}")
        tf_addr = st.text_area("\u0410\u0434\u0440\u0435\u0441 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438:", key=f"tf_addr_{key_prefix}")
        tf_recv = st.text_input("\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:", key=f"tf_recv_{key_prefix}")
        tf_rphone = st.text_input("\u0422\u0435\u043b\u0435\u0444\u043e\u043d \u043f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044f:", key=f"tf_rphone_{key_prefix}")
        tf_pay = st.selectbox("\u041e\u043f\u043b\u0430\u0442\u0430:", SHIP_PAY_OPTIONS, key=f"tf_pay_{key_prefix}", placeholder="\u0423\u043a\u0430\u0436\u0438 \u043f\u043b\u0430\u0442\u0435\u043b\u044c\u0449\u0438\u043a\u0430")
        tf_amount = st.text_input("\u0421\u0443\u043c\u043c\u0430 \u0437\u0430\u043a\u0430\u0437\u0430 (\u0440\u0443\u0431.):", key=f"tf_amount_{key_prefix}", placeholder="\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u0443\u043c\u043c\u0443")
        tf_tk = st.text_input("\u0422\u0440\u0435\u043a:", key=f"tf_tk_{key_prefix}")
    tf_files = st.file_uploader("\u0424\u0430\u0439\u043b\u044b:", key=f"tf_files_{key_prefix}", accept_multiple_files=True)
    if st.button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443", key=f"tf_go_{key_prefix}", use_container_width=True, type="primary"):
        if not tf_topic.strip():
            st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0442\u0435\u043c\u0443")
            return False
        if not tf_mgr:
            st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0433\u043e")
            return False
        cl = get_client_by_id(client_id)
        if not cl: return False
        prefix = "\u0417\u0421" if deal_id else "\u0417\u041a"
        tn = generate_task_number(prefix)
        new_task = {
            "id": str(uuid.uuid4())[:8],
            "task_number": tn,
            "deal_id": deal_id,
            "text": tf_topic.strip(),
            "type": tf_type,
            "manager": tf_mgr,
            "deadline": tf_dl.isoformat(),
            "task_comment": tf_comment.strip(),
            "products": tf_products,
            "ship_addr": tf_addr,
            "receiver": tf_recv,
            "receiver_phone": format_phone(tf_rphone) if tf_rphone else "",
            "ship_pay": tf_pay,
            "order_amount": int(tf_amount) if tf_amount and tf_amount.strip().isdigit() else 0,
            "tk_num": tf_tk,
            "done": False,
            "in_work": False,
            "ready_to_ship": False,
            "delegated_to": "",
            "created_at": now_str(),
            "last_modified": now_str(),
            "task_files": normalize_file_list(save_uploaded_files(tf_files, client_id, "task")) if tf_files else [],
            "completion_files": [],
            "task_chat": []
        }
        cl.setdefault("tasks", []).append(new_task)
        cl["last_modified"] = now_str()
        if deal_id:
            d = get_deal_by_id(deal_id)
            if d: d["last_modified"] = now_str()
        commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0441\u043e\u0437\u0434\u0430\u043d\u0430")
        return True
    return False

def render_task_detail(task, cl, deal, key_prefix):
    tp = task.get("type", "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f")
    fd = format_date(task.get("deadline", ""))
    io_ = is_task_overdue(task)
    st.markdown(f"**\u0417\u0430\u0434\u0430\u0447\u0430 \u2116{task.get('task_number', '')}**")
    st.markdown(format_created_date(task), unsafe_allow_html=True)
    st.markdown(f"**\u0422\u0438\u043f:** {tp}")
    st.markdown(f"**\u0422\u0435\u043c\u0430:** {task.get('text', '')}")
    st.markdown(f"**\u0421\u0440\u043e\u043a:** {fd}")
    if io_ and not task.get("done"): st.markdown("**\u041f\u0420\u041e\u0421\u0420\u041e\u0427\u0415\u041d\u041e**")
    st.markdown(f"**\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:** {task.get('manager', '')}")
    if task.get("delegated_to"): st.markdown(f"**\u0414\u0435\u043b\u0435\u0433\u0438\u0440\u043e\u0432\u0430\u043d\u043e:** {task['delegated_to']}")
    if task.get("task_comment"): st.markdown(f"**\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:** {task['task_comment']}")
    if tp in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b"):
        if task.get("products"): st.markdown(f"**\u0422\u043e\u0432\u0430\u0440\u044b:** {task['products']}")
        if task.get("ship_addr"): st.markdown(f"**\u0410\u0434\u0440\u0435\u0441:** {task['ship_addr']}")
        if task.get("receiver"): st.markdown(f"**\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:** {task['receiver']}")
        if task.get("receiver_phone"): render_phone_inline(task["receiver_phone"], f"rph_{key_prefix}")
        if task.get("ship_pay"): st.markdown(f"**\u041e\u043f\u043b\u0430\u0442\u0430:** {task['ship_pay']}")
        if task.get("order_amount", 0) > 0: st.markdown(f"**\u0421\u0443\u043c\u043c\u0430:** {task['order_amount']:,.0f} \u0440\u0443\u0431.".replace(",", " "))
        if task.get("tk_num"): render_track_inline(task["tk_num"], f"tk_{key_prefix}")
    if task.get("task_files"):
        st.markdown("**\u0424\u0430\u0439\u043b\u044b \u0437\u0430\u0434\u0430\u0447\u0438:**")
        render_file_thumbs(task["task_files"], f"tf_{key_prefix}", allow_delete=True)
        render_print_file_button(task["task_files"], f"tf_{key_prefix}")
    render_print_button(task, cl, tp, fd, key_prefix)
    if task.get("done"):
        st.success(f"\u0412\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u0430: {task.get('done_at', '')}")
        if task.get("completion_report"): st.markdown(f"**\u041e\u0442\u0447\u0451\u0442:** {task['completion_report']}")
        if task.get("completion_files"):
            st.markdown("**\u0424\u0430\u0439\u043b\u044b \u043e\u0442\u0447\u0451\u0442\u0430:**")
            render_file_thumbs(task["completion_files"], f"cf_{key_prefix}", allow_delete=True)
        if st.button("\u0412\u0435\u0440\u043d\u0443\u0442\u044c \u0432 \u0440\u0430\u0431\u043e\u0442\u0443", key=f"reopen_{key_prefix}", use_container_width=True):
            task["done"] = False
            task.pop("done_at", None)
            task.pop("completion_report", None)
            task.pop("completion_files", None)
            task["last_modified"] = now_str()
            commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0435\u043d\u0430")
    else:
        btn1, btn2, btn3, btn4 = st.columns(4)
        with btn1:
            if st.button("\u0412\u044b\u043f\u043e\u043b\u043d\u0438\u0442\u044c", key=f"done_{key_prefix}", type="primary", use_container_width=True):
                show_complete = f"show_complete_{key_prefix}"
                st.session_state[show_complete] = not st.session_state.get(show_complete, False)
                st.rerun()
        with btn2:
            if st.button("\u0412 \u0440\u0430\u0431\u043e\u0442\u0443" if not task.get("in_work") else "\u0421\u043d\u044f\u0442\u044c \u0432 \u0440\u0430\u0431\u043e\u0442\u0443", key=f"inwork_{key_prefix}", use_container_width=True):
                task["in_work"] = not task.get("in_work", False)
                task["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store)
        with btn3:
            if st.button("\u0413\u043e\u0442\u043e\u0432\u043e \u043a \u043e\u0442\u043f\u0440\u0430\u0432\u043a\u0435" if not task.get("ready_to_ship") else "\u0421\u043d\u044f\u0442\u044c \u0433\u043e\u0442\u043e\u0432\u043d\u043e\u0441\u0442\u044c", key=f"rts_{key_prefix}", use_container_width=True):
                task["ready_to_ship"] = not task.get("ready_to_ship", False)
                task["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store)
        with btn4:
            show_dlg = f"show_dlg_{key_prefix}"
            if st.button("\u0414\u0435\u043b\u0435\u0433\u0438\u0440\u043e\u0432\u0430\u0442\u044c", key=f"dlg_{key_prefix}", use_container_width=True):
                st.session_state[show_dlg] = not st.session_state.get(show_dlg, False)
                st.rerun()
        if st.session_state.get(f"show_complete_{key_prefix}", False):
            with st.container(border=True):
                cr = st.text_input("\u041e\u0442\u0447\u0451\u0442 (\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e):", key=f"cr_{key_prefix}")
                cfiles = st.file_uploader("\u0424\u0430\u0439\u043b\u044b \u043e\u0442\u0447\u0451\u0442\u0430:", key=f"cfiles_{key_prefix}", accept_multiple_files=True)
                cn = st.checkbox("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u043d\u043e\u0432\u0443\u044e \u0437\u0430\u0434\u0430\u0447\u0443", key=f"cn_{key_prefix}")
                nn_title, nn_to, nn_dl, nn_desc, nn_pri = None, None, None, None, None
                if cn:
                    nn_title = st.text_input("\u0422\u0435\u043c\u0430 \u043d\u043e\u0432\u043e\u0439 \u0437\u0430\u0434\u0430\u0447\u0438:", key=f"nn_title_{key_prefix}")
                    nn_to = st.selectbox("\u041a\u043e\u043c\u0443:", [""] + get_managers_list(), index=0, key=f"nn_to_{key_prefix}", placeholder=MGR_PLACEHOLDER)
                    nn_dl = st.date_input("\u0421\u0440\u043e\u043a:", format="DD/MM/YYYY", key=f"nn_dl_{key_prefix}")
                    nn_desc = st.text_area("\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435:", key=f"nn_desc_{key_prefix}")
                if st.button("\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c", key=f"confirm_{key_prefix}", use_container_width=True, type="primary"):
                    if not cr.strip():
                        st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043e\u0442\u0447\u0451\u0442")
                    elif cn and (not nn_title or not nn_title.strip()):
                        st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0442\u0435\u043c\u0443 \u043d\u043e\u0432\u043e\u0439 \u0437\u0430\u0434\u0430\u0447\u0438")
                    elif cn and not nn_to:
                        st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0438\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044f")
                    else:
                        task["done"] = True
                        task["done_at"] = now_str()
                        task["completion_report"] = cr.strip()
                        task["last_modified"] = now_str()
                        if cfiles:
                            task["completion_files"] = normalize_file_list(save_uploaded_files(cfiles, cl["id"], "completion"))
                        if cn and nn_title:
                            new_t = {
                                "id": str(uuid.uuid4())[:8],
                                "task_number": generate_task_number("\u0417\u041a" if not task.get("deal_id") else "\u0417\u0421"),
                                "deal_id": task.get("deal_id"),
                                "text": nn_title.strip(),
                                "type": "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f",
                                "manager": nn_to,
                                "deadline": nn_dl.isoformat(),
                                "task_comment": nn_desc.strip() if nn_desc else "",
                                "products": "", "ship_addr": "", "receiver": "", "receiver_phone": "",
                                "ship_pay": "", "order_amount": 0, "tk_num": "",
                                "done": False, "in_work": False, "ready_to_ship": False,
                                "delegated_to": "", "created_at": now_str(), "last_modified": now_str(),
                                "task_files": [], "completion_files": [], "task_chat": []
                            }
                            cl.setdefault("tasks", []).append(new_t)
                        st.session_state[f"show_complete_{key_prefix}"] = False
                        commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u0430")
        if st.session_state.get(f"show_dlg_{key_prefix}", False):
            with st.container(border=True):
                dlg_to = st.selectbox("\u0414\u0435\u043b\u0435\u0433\u0438\u0440\u043e\u0432\u0430\u0442\u044c:", [""] + get_managers_list(), index=0, key=f"dlg_to_{key_prefix}", placeholder=MGR_PLACEHOLDER)
                if st.button("\u041f\u0435\u0440\u0435\u0434\u0430\u0442\u044c", key=f"dlg_go_{key_prefix}", use_container_width=True, type="primary"):
                    if dlg_to:
                        task["delegated_to"] = dlg_to
                        task["last_modified"] = now_str()
                        st.session_state[f"show_dlg_{key_prefix}"] = False
                        commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0434\u0435\u043b\u0435\u0433\u0438\u0440\u043e\u0432\u0430\u043d\u0430")
                    else:
                        st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0430")
    st.markdown("---")
    show_edit = st.session_state.get(f"show_edit_task_{key_prefix}", False)
    if st.button("\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c" if not show_edit else "\u0421\u043a\u0440\u044b\u0442\u044c", key=f"edit_toggle_{key_prefix}", use_container_width=True):
        st.session_state[f"show_edit_task_{key_prefix}"] = not show_edit
        st.rerun()
    if show_edit:
        render_task_edit_form(task, cl, deal, key_prefix)
    render_entity_chat(task, "task", key_prefix)
    if task.get("manager") == st.session_state.get("user_name", "") or st.session_state.user_role == "admin":
        st.markdown("---")
        if st.button("\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443", key=f"del_task_{key_prefix}", use_container_width=True):
            cl["tasks"] = [x for x in cl.get("tasks", []) if x["id"] != task["id"]]
            cl["last_modified"] = now_str()
            st.session_state.expanded_task_key = None
            commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0443\u0434\u0430\u043b\u0435\u043d\u0430")

def render_task_row(task, cl, deal, task_key, key_prefix):
    is_exp = st.session_state.expanded_task_key == task_key
    io_ = is_task_overdue(task)
    fd = format_date(task.get("deadline", ""))
    tp = task.get("type", "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f")
    label = f"\u0417\u0430\u0434\u0430\u0447\u0430 \u2116{task.get('task_number', '')} {fd} \u2014 {task.get('text', '')}"
    if task.get("in_work"): label += ' | \u0412 \u0440\u0430\u0431\u043e\u0442\u0435'
    if task.get("ready_to_ship"): label += ' | \u0413\u043e\u0442\u043e\u0432\u043e \u043a \u043e\u0442\u043f\u0440\u0430\u0432\u043a\u0435'
    if task.get("done"): label = f"\u2705 {label}"
    if io_ and not task.get("done"): label += " | \u041f\u0420\u041e\u0421\u0420\u041e\u0427\u0415\u041d\u041e"
    if io_: bg, bc = "#FFEBEE", "#C62828"
    elif task.get("in_work"): bg, bc = "#E8F5E9", "#4CAF50"
    elif task.get("done"): bg, bc = "#F5F6F8", "#C9CFD7"
    else: bg, bc = "#FFFFFF", "#DCE0E5"
    border = "#2196F3" if is_exp else bc
    shadow = "box-shadow: 0 0 0 2px rgba(33,150,243,0.3);" if is_exp else ""
    st.markdown(f"<style>.st-key-tr_wrap_{task_key} button {{ background-color: {bg} !important; color: #2C3E50 !important; border: 2px solid {border} !important; border-radius: 10px !important; {shadow} }}</style>", unsafe_allow_html=True)
    with st.container(key=f"tr_wrap_{task_key}"):
        if st.button(label, key=f"tr_btn_{task_key}", use_container_width=True, type="primary" if is_exp else "secondary"):
            if is_exp:
                st.session_state.expanded_task_key = None
                save_scroll_and_rerun()
            else:
                st.session_state.expanded_task_key = task_key
                st.rerun()
        if not is_exp:
            render_scroll_restore(task_key)
    if is_exp:
        render_task_detail(task, cl, deal, key_prefix)

def render_deal_in_tree(d, cl):
    deal_key = f"deal_{d['id']}"
    is_exp = st.session_state.expanded_deal_id == d["id"] or st.session_state.get("auto_expand_deal_id") == d["id"]
    if st.session_state.get("auto_expand_deal_id") == d["id"]:
        st.session_state.expanded_deal_id = d["id"]
        st.session_state.auto_expand_deal_id = None
    ps = d.get("payment_status", "\u041d\u0435 \u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043e")
    ps_cls = "payment-status-paid" if ps == "\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043e" else "payment-status-unpaid"
    label = f"{d.get('deal_number', '')} \u2014 {d.get('deal_title', '') or d.get('title', '')} | {d.get('status', '')} | {d.get('budget', 0):,.0f} \u0440\u0443\u0431.".replace(",", " ")
    border = "#2196F3" if is_exp else "#DCE0E5"
    shadow = "box-shadow: 0 0 0 2px rgba(33,150,243,0.3);" if is_exp else ""
    st.markdown(f"<style>.st-key-dl_wrap_{d['id']} button {{ background-color: #FFFFFF !important; color: #2C3E50 !important; border: 2px solid {border} !important; border-radius: 10px !important; {shadow} }}</style>", unsafe_allow_html=True)
    with indented(0.03):
        with st.container(key=f"dl_wrap_{d['id']}"):
            if st.button(label, key=f"dl_btn_{d['id']}", use_container_width=True, type="primary" if is_exp else "secondary"):
                if is_exp:
                    st.session_state.expanded_deal_id = None
                    save_scroll_and_rerun()
                else:
                    st.session_state.expanded_deal_id = d["id"]
                    st.rerun()
            if not is_exp:
                render_scroll_restore(f"dl_{d['id']}")
        if is_exp:
            with indented(0.03):
                with st.container(border=True):
                    st.markdown(f"**{d.get('deal_number', '')}**")
                    st.markdown(format_created_date(d), unsafe_allow_html=True)
                    st.markdown(f"**\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435:** {d.get('deal_title', '') or d.get('title', '')}")
                    st.markdown(f"**\u0421\u0442\u0430\u0442\u0443\u0441:** {d.get('status', '')}")
                    st.markdown(f"**\u0411\u044e\u0434\u0436\u0435\u0442:** {d.get('budget', 0):,.0f} \u0440\u0443\u0431.".replace(",", " "))
                    st.markdown(f"**\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:** {d.get('manager', '')}")
                    st.markdown(f'**\u041e\u043f\u043b\u0430\u0442\u0430:** <span class="payment-status-badge {ps_cls}">{ps}</span>', unsafe_allow_html=True)
                    inject_payment_container_css(d["id"], ps)
                    dls, dle = st.columns(2)
                    with dls:
                        new_ps = st.selectbox("\u0421\u0442\u0430\u0442\u0443\u0441 \u043e\u043f\u043b\u0430\u0442\u044b:", ["\u041d\u0435 \u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043e", "\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043e"], index=0 if ps != "\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043e" else 1, key=f"ps_{d['id']}")
                    with dle:
                        new_st = st.selectbox("\u0421\u0442\u0430\u0442\u0443\u0441 \u0441\u0434\u0435\u043b\u043a\u0438:", ["\u041d\u043e\u0432\u044b\u0439", "\u0412 \u0440\u0430\u0431\u043e\u0442\u0435", "\u0417\u0430\u043a\u0440\u044b\u0442\u0430"], index=["\u041d\u043e\u0432\u044b\u0439", "\u0412 \u0440\u0430\u0431\u043e\u0442\u0435", "\u0417\u0430\u043a\u0440\u044b\u0442\u0430"].index(d.get("status", "\u041d\u043e\u0432\u044b\u0439")), key=f"st_{d['id']}")
                    new_budget = st.text_input("\u0411\u044e\u0434\u0436\u0435\u0442:", value=str(d.get("budget", 0)), key=f"bg_{d['id']}")
                    new_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", [""] + get_managers_list(), index=0 if d.get("manager", "") not in get_managers_list() else ([""] + get_managers_list()).index(d.get("manager", "")), key=f"dm_{d['id']}", placeholder=MGR_PLACEHOLDER)
                    if st.button("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f", key=f"save_deal_{d['id']}", use_container_width=True, type="primary"):
                        d["payment_status"] = new_ps
                        d["status"] = new_st
                        d["budget"] = int(new_budget) if new_budget and new_budget.strip().isdigit() else 0
                        d["manager"] = new_mgr
                        d["last_modified"] = now_str()
                        cl["last_modified"] = now_str()
                        commit_and_rerun(st.session_state.crm_store, "\u0421\u0434\u0435\u043b\u043a\u0430 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0430")
                    if d.get("deal_files"):
                        st.markdown("**\u0424\u0430\u0439\u043b\u044b \u0441\u0434\u0435\u043b\u043a\u0438:**")
                        render_file_thumbs(d["deal_files"], f"df_{d['id']}", allow_delete=True)
                    df_upl = st.file_uploader("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0444\u0430\u0439\u043b\u044b:", key=f"df_upl_{d['id']}", accept_multiple_files=True)
                    if df_upl and st.button("\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c", key=f"df_go_{d['id']}"):
                        d.setdefault("deal_files", []).extend(normalize_file_list(save_uploaded_files(df_upl, cl["id"], "deal")))
                        d["last_modified"] = now_str()
                        commit_and_rerun(st.session_state.crm_store, "\u0424\u0430\u0439\u043b\u044b \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u044b")
                    render_entity_chat(d, "deal", d["id"])
                    deal_tasks = [t for t in cl.get("tasks", []) if t.get("deal_id") == d["id"]]
                    st.markdown("---")
                    render_centered_title(f"\u0417\u0430\u0434\u0430\u0447\u0438 \u043f\u043e \u0441\u0434\u0435\u043b\u043a\u0435 ({len(deal_tasks)})")
                    if deal_tasks:
                        deal_tasks.sort(key=lambda t: get_sort_key(t), reverse=True)
                        for ti, t in enumerate(deal_tasks):
                            tk = f"dt_{d['id']}_{ti}"
                            render_task_row(t, cl, d, tk, f"dt_{d['id']}_{ti}")
                            if ti < len(deal_tasks) - 1:
                                render_separator()
                    else:
                        with indented(0.03):
                            st.caption("\u0417\u0430\u0434\u0430\u0447 \u043f\u043e \u0441\u0434\u0435\u043b\u043a\u0435 \u043d\u0435\u0442")
                    show_dt_key = f"show_dt_{d['id']}"
                    if render_centered_button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443 \u043f\u043e \u0441\u0434\u0435\u043b\u043a\u0435", key=f"btn_dt_{d['id']}"):
                        st.session_state[show_dt_key] = not st.session_state.get(show_dt_key, False)
                        st.rerun()
                    if st.session_state.get(show_dt_key, False):
                        with st.container(border=True):
                            if render_task_form(d["id"], cl["id"], f"dt_{d['id']}"):
                                st.session_state[show_dt_key] = False
                    if st.session_state.user_role == "admin":
                        st.markdown("---")
                        if st.button("\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0441\u0434\u0435\u043b\u043a\u0443", key=f"del_deal_{d['id']}", use_container_width=True):
                            st.session_state.crm_store["deals"] = [x for x in st.session_state.crm_store.get("deals", []) if x["id"] != d["id"]]
                            cl["tasks"] = [t for t in cl.get("tasks", []) if t.get("deal_id") != d["id"]]
                            cl["last_modified"] = now_str()
                            st.session_state.expanded_deal_id = None
                            commit_and_rerun(st.session_state.crm_store, "\u0421\u0434\u0435\u043b\u043a\u0430 \u0443\u0434\u0430\u043b\u0435\u043d\u0430")

def render_client_form(version):
    with st.container(border=True):
        cn = st.text_input("\u0424\u0418\u041e:", key=f"cn_{version}")
        cph = st.text_input("\u0422\u0435\u043b\u0435\u0444\u043e\u043d:", key=f"cph_{version}")
        ce = st.text_input("Email:", key=f"ce_{version}")
        ca = st.text_input("\u0410\u0434\u0440\u0435\u0441:", key=f"ca_{version}")
        cc = st.selectbox("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:", CATEGORIES, key=f"cc_{version}")
        cm = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", [""] + get_managers_list(), index=0, key=f"cm_{version}", placeholder=MGR_PLACEHOLDER)
        cd = st.text_input("\u0421\u043a\u0438\u0434\u043a\u0430 %:", value="0", key=f"cd_{version}")
        cnote = st.text_area("\u0411\u0430\u0437\u043e\u0432\u044b\u0439 \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:", key=f"cnote_{version}")
        cfiles = st.file_uploader("\u0424\u0430\u0439\u043b\u044b:", key=f"cfiles_{version}", accept_multiple_files=True)
        if st.button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u043a\u043b\u0438\u0435\u043d\u0442\u0430", key=f"client_go_{version}", use_container_width=True, type="primary"):
            if not cn.strip():
                st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0424\u0418\u041e")
            elif not cph.strip():
                st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0442\u0435\u043b\u0435\u0444\u043e\u043d")
            else:
                cid = (max([c["id"] for c in st.session_state.crm_store.get("clients", [])], default=0)) + 1
                new_cl = {
                    "id": cid, "name": cn.strip(), "phone": format_phone(cph), "email": ce.strip(),
                    "address": ca.strip(), "category": cc, "manager": cm,
                    "discount": int(cd) if cd and cd.strip().isdigit() else 0,
                    "base_comment": cnote.strip(), "tasks": [], "client_files": normalize_file_list(save_uploaded_files(cfiles, cid, "client")) if cfiles else [],
                    "extra_phones": [], "client_chat": [],
                    "created_at": now_str(), "last_modified": now_str()
                }
                st.session_state.crm_store.setdefault("clients", []).append(new_cl)
                st.session_state.client_form_version += 1
                st.session_state.expanded_client_id = cid
                st.session_state.expanded_tree_id = cid
                commit_and_rerun(st.session_state.crm_store, "\u041a\u043b\u0438\u0435\u043d\u0442 \u0441\u043e\u0437\u0434\u0430\u043d")

def render_client_in_tree(cl):
    cl_key = f"cl_{cl['id']}"
    is_exp = st.session_state.expanded_client_id == cl["id"] or st.session_state.expanded_tree_id == cl["id"]
    if is_exp:
        st.session_state.expanded_client_id = cl["id"]
    cl_tasks_all = cl.get("tasks", [])
    cl_deals = [d for d in st.session_state.crm_store.get("deals", []) if d.get("client_id") == cl["id"]]
    label = f"{cl['name']} \u2014 {cl.get('phone', '')} | {cl.get('category', '')} | \u0421\u0434\u0435\u043b\u043e\u043a: {len(cl_deals)} | \u0417\u0430\u0434\u0430\u0447: {len(cl_tasks_all)}"
    border = "#2196F3" if is_exp else "#DCE0E5"
    shadow = "box-shadow: 0 0 0 2px rgba(33,150,243,0.3);" if is_exp else ""
    st.markdown(f"<style>.st-key-cl_wrap_{cl['id']} button {{ background-color: #FFFFFF !important; color: #2C3E50 !important; border: 2px solid {border} !important; border-radius: 10px !important; {shadow} }}</style>", unsafe_allow_html=True)
    with st.container(key=f"cl_wrap_{cl['id']}"):
        if st.button(label, key=f"cl_btn_{cl['id']}", use_container_width=True, type="primary" if is_exp else "secondary"):
            if is_exp:
                st.session_state.expanded_client_id = None
                st.session_state.expanded_tree_id = None
                save_scroll_and_rerun()
            else:
                st.session_state.expanded_client_id = cl["id"]
                st.session_state.expanded_tree_id = cl["id"]
                st.rerun()
        if not is_exp:
            render_scroll_restore(cl_key)
    if is_exp:
        with st.container(border=True):
            st.markdown(f"**{cl['name']}**")
            st.markdown(format_created_date(cl), unsafe_allow_html=True)
            render_phone_inline(cl.get("phone", ""), f"cl_{cl['id']}")
            if cl.get("email"): st.markdown(f"**Email:** {cl['email']}")
            if cl.get("address"): st.markdown(f"**\u0410\u0434\u0440\u0435\u0441:** {cl['address']}")
            st.markdown(f"**\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:** {cl.get('category', '')}")
            st.markdown(f"**\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:** {cl.get('manager', '')}")
            st.markdown(f"**\u0421\u043a\u0438\u0434\u043a\u0430:** {cl.get('discount', 0)}%")
            if cl.get("base_comment"): st.markdown(f"**\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:** {cl['base_comment']}")
            for ep in cl.get("extra_phones", []):
                render_extra_phone_inline(ep.get("phone", ""), ep.get("name", ""), ep.get("role", ""), f"ep_{cl['id']}_{ep.get('phone','')}")
            if cl.get("client_files"):
                st.markdown("**\u0424\u0430\u0439\u043b\u044b:**")
                render_file_thumbs(cl["client_files"], f"clf_{cl['id']}", allow_delete=True)
            cf_upl = st.file_uploader("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0444\u0430\u0439\u043b\u044b:", key=f"clf_upl_{cl['id']}", accept_multiple_files=True)
            if cf_upl and st.button("\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c", key=f"clf_go_{cl['id']}"):
                cl.setdefault("client_files", []).extend(normalize_file_list(save_uploaded_files(cf_upl, cl["id"], "client")))
                cl["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "\u0424\u0430\u0439\u043b\u044b \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u044b")
            show_ep = f"show_ep_{cl['id']}"
            if st.button("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0434\u043e\u043f. \u0442\u0435\u043b\u0435\u0444\u043e\u043d", key=f"ep_btn_{cl['id']}"):
                st.session_state[show_ep] = not st.session_state.get(show_ep, False)
                st.rerun()
            if st.session_state.get(show_ep, False):
                with st.container(border=True):
                    epn = st.text_input("\u0418\u043c\u044f:", key=f"epn_{cl['id']}")
                    epp = st.text_input("\u0422\u0435\u043b\u0435\u0444\u043e\u043d:", key=f"epp_{cl['id']}")
                    epr = st.text_input("\u0420\u043e\u043b\u044c:", key=f"epr_{cl['id']}")
                    if st.button("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c", key=f"ep_go_{cl['id']}", type="primary", use_container_width=True):
                        if epp.strip():
                            cl.setdefault("extra_phones", []).append({"name": epn.strip(), "phone": format_phone(epp), "role": epr.strip()})
                            cl["last_modified"] = now_str()
                            st.session_state[show_ep] = False
                            commit_and_rerun(st.session_state.crm_store, "\u0422\u0435\u043b\u0435\u0444\u043e\u043d \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d")
            show_ce = f"show_ce_{cl['id']}"
            if st.button("\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043a\u043b\u0438\u0435\u043d\u0442\u0430", key=f"ce_btn_{cl['id']}"):
                st.session_state[show_ce] = not st.session_state.get(show_ce, False)
                st.rerun()
            if st.session_state.get(show_ce, False):
                with st.container(border=True):
                    en = st.text_input("\u0424\u0418\u041e:", value=cl["name"], key=f"en_{cl['id']}")
                    ep = st.text_input("\u0422\u0435\u043b\u0435\u0444\u043e\u043d:", value=cl.get("phone", ""), key=f"ep_{cl['id']}")
                    ee = st.text_input("Email:", value=cl.get("email", ""), key=f"ee_{cl['id']}")
                    ea = st.text_input("\u0410\u0434\u0440\u0435\u0441:", value=cl.get("address", ""), key=f"ea_{cl['id']}")
                    ec = st.selectbox("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:", CATEGORIES, index=CATEGORIES.index(cl.get("category", CATEGORIES[0])), key=f"ec_{cl['id']}")
                    em = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", [""] + get_managers_list(), index=0 if cl.get("manager", "") not in get_managers_list() else ([""] + get_managers_list()).index(cl.get("manager", "")), key=f"em_{cl['id']}", placeholder=MGR_PLACEHOLDER)
                    ed = st.text_input("\u0421\u043a\u0438\u0434\u043a\u0430 %:", value=str(cl.get("discount", 0)), key=f"ed_{cl['id']}")
                    enote = st.text_area("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:", value=cl.get("base_comment", ""), key=f"enote_{cl['id']}")
                    if st.button("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", key=f"ce_go_{cl['id']}", type="primary", use_container_width=True):
                        cl["name"] = en.strip()
                        cl["phone"] = format_phone(ep) if ep else ""
                        cl["email"] = ee.strip()
                        cl["address"] = ea.strip()
                        cl["category"] = ec
                        cl["manager"] = em
                        cl["discount"] = int(ed) if ed and ed.strip().isdigit() else 0
                        cl["base_comment"] = enote.strip()
                        cl["last_modified"] = now_str()
                        st.session_state[show_ce] = False
                        commit_and_rerun(st.session_state.crm_store, "\u041a\u043b\u0438\u0435\u043d\u0442 \u043e\u0431\u043d\u043e\u0432\u043b\u0451\u043d")
            render_entity_chat(cl, "client", cl["id"])
            if st.session_state.user_role == "admin":
                st.markdown("---")
                if st.button("\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043a\u043b\u0438\u0435\u043d\u0442\u0430", key=f"del_cl_{cl['id']}", use_container_width=True):
                    st.session_state.crm_store["clients"] = [x for x in st.session_state.crm_store.get("clients", []) if x["id"] != cl["id"]]
                    st.session_state.crm_store["deals"] = [d for d in st.session_state.crm_store.get("deals", []) if d.get("client_id") != cl["id"]]
                    st.session_state.expanded_client_id = None
                    st.session_state.expanded_tree_id = None
                    commit_and_rerun(st.session_state.crm_store, "\u041a\u043b\u0438\u0435\u043d\u0442 \u0443\u0434\u0430\u043b\u0451\u043d")

        is_cl_deals_exp = True
        if is_cl_deals_exp:
            client_only_tasks = [t for t in cl_tasks_all if not t.get("deal_id")]
            with indented(0.06):
                render_centered_title(f"\u0417\u0430\u0434\u0430\u0447\u0438 \u043f\u043e \u043a\u043b\u0438\u0435\u043d\u0442\u0443 ({len(client_only_tasks)})")
                if client_only_tasks:
                    client_only_tasks.sort(key=lambda t: get_sort_key(t), reverse=True)
                    for ti, t in enumerate(client_only_tasks):
                        task_key = f"cl_{cl['id']}_{ti}"
                        render_task_row(t, cl, None, task_key, f"cl_{cl['id']}_{ti}")
                show_ct_key = f"show_ct_cl_{cl['id']}"
                if render_centered_button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443 \u043f\u043e \u043a\u043b\u0438\u0435\u043d\u0442\u0443", key=f"btn_ct_cl_{cl['id']}"):
                    st.session_state[show_ct_key] = not st.session_state.get(show_ct_key, False)
                    st.rerun()
            if st.session_state.get(show_ct_key, False):
                with st.container(border=True):
                    if render_task_form(None, cl["id"], f"cl_{cl['id']}"):
                        st.session_state[show_ct_key] = False
                        commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0441\u043e\u0437\u0434\u0430\u043d\u0430")

            render_separator()

            render_centered_title(f"\u0421\u0434\u0435\u043b\u043a\u0438 \u043f\u043e \u043a\u043b\u0438\u0435\u043d\u0442\u0443 ({len(cl_deals)})")
            if cl_deals:
                cl_deals.sort(key=lambda d: get_sort_key(d), reverse=True)
                for di, d in enumerate(cl_deals):
                    render_deal_in_tree(d, cl)
                    if di < len(cl_deals) - 1:
                        render_separator()
            else:
                with indented(0.03):
                    st.caption("\u0421\u0434\u0435\u043b\u043e\u043a \u043d\u0435\u0442")

            render_separator()

            show_cd_key = f"show_cd_cl_{cl['id']}"
            if render_centered_button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u043d\u043e\u0432\u0443\u044e \u0441\u0434\u0435\u043b\u043a\u0443", key=f"btn_cd_cl_{cl['id']}"):
                st.session_state[show_cd_key] = not st.session_state.get(show_cd_key, False)
                st.rerun()
            if st.session_state.get(show_cd_key, False):
                with st.container(border=True):
                    cd_title = st.text_input("\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0441\u0434\u0435\u043b\u043a\u0438:", key=f"cd_title_{cl['id']}")
                    cd_budget = st.text_input("\u0411\u044e\u0434\u0436\u0435\u0442 (\u0440\u0443\u0431.):", value="", key=f"cd_budget_{cl['id']}", placeholder="\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u0443\u043c\u043c\u0443")
                    cd_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", [""] + get_managers_list(), index=0, key=f"cd_mgr_{cl['id']}", placeholder=MGR_PLACEHOLDER)
                    if st.button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c", key=f"cd_go_{cl['id']}", use_container_width=True, type="primary"):
                        if not cd_mgr:
                            st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0433\u043e")
                        else:
                            deals = st.session_state.crm_store.get("deals", [])
                            did = (max([dd["id"] for dd in deals]) if deals else 0) + 1
                            dn = generate_deal_number()
                            new_deal = {"id": did, "client_id": cl["id"], "title": dn, "deal_number": dn, "deal_title": cd_title.strip(), "budget": int(cd_budget) if cd_budget and cd_budget.strip().isdigit() else 0, "status": "\u041d\u043e\u0432\u044b\u0439", "manager": cd_mgr, "deal_comments": [], "deal_files": [], "payment_status": "\u041d\u0435 \u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043e", "close_files": [], "last_modified": now_str(), "created_at": now_str(), "deal_chat": []}
                            st.session_state.crm_store.setdefault("deals", []).append(new_deal)
                            cl["last_modified"] = now_str()
                            st.session_state[show_cd_key] = False
                            st.session_state.auto_expand_deal_id = did
                            commit_and_rerun(st.session_state.crm_store, "\u0421\u0434\u0435\u043b\u043a\u0430 \u0441\u043e\u0437\u0434\u0430\u043d\u0430")

# --- Инициализация БД и сессии ---
if "crm_store" not in st.session_state:
    init_yandex_folders()
    download_db_from_yandex()
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            st.session_state.crm_store = json.load(f)
    else:
        st.session_state.crm_store = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "\u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440"}], "_migrated": "v2", "internal_tasks": [], "chat_messages": [], "qa_entries": [], "suppliers": []}
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            json.dump(st.session_state.crm_store, f, ensure_ascii=False, indent=2)
    assign_task_numbers(st.session_state.crm_store)
    assign_deal_numbers(st.session_state.crm_store)

if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "\u041a\u043b\u0438\u0435\u043d\u0442\u044b \u0438 \u0441\u0434\u0435\u043b\u043a\u0438"
if "expanded_client_id" not in st.session_state:
    st.session_state.expanded_client_id = None
if "expanded_tree_id" not in st.session_state:
    st.session_state.expanded_tree_id = None
if "expanded_deal_id" not in st.session_state:
    st.session_state.expanded_deal_id = None
if "expanded_task_key" not in st.session_state:
    st.session_state.expanded_task_key = None
if "auto_expand_deal_id" not in st.session_state:
    st.session_state.auto_expand_deal_id = None
if "client_form_version" not in st.session_state:
    st.session_state.client_form_version = 0

cu = st.session_state.user_name

# --- Логин ---
if not st.session_state.current_user:
    st.markdown('<div class="greeting-block">', unsafe_allow_html=True)
    st.markdown("### \u0410\u0439\u043f\u043b\u0438\u043d\u0442 CRM")
    st.markdown('</div>', unsafe_allow_html=True)
    with st.container(border=True):
        login = st.text_input("\u041b\u043e\u0433\u0438\u043d:", key="login_input")
        pwd = st.text_input("\u041f\u0430\u0440\u043e\u043b\u044c:", type="password", key="pwd_input")
        if st.button("\u0412\u043e\u0439\u0442\u0438", key="login_btn", type="primary", use_container_width=True):
            for u in st.session_state.crm_store.get("users", []):
                if u["login"] == login.strip() and verify_password(pwd, u.get("password", "")):
                    st.session_state.current_user = u
                    st.session_state.user_role = u.get("role", "manager")
                    st.session_state.user_name = u.get("name", u["login"])
                    cu = st.session_state.user_name
                    st.rerun()
            st.error("\u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u043b\u043e\u0433\u0438\u043d \u0438\u043b\u0438 \u043f\u0430\u0440\u043e\u043b\u044c")
    st.stop()

# --- Сайдбар ---
with st.sidebar:
    st.markdown(f"**{st.session_state.user_name}**")
    st.caption(f"\u0420\u043e\u043b\u044c: {st.session_state.user_role}")
    if st.session_state.user_role == "admin":
        with st.expander("\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f\u043c\u0438"):
            users = st.session_state.crm_store.get("users", [])
            for u in users:
                st.markdown(f"**{u['login']}** ({u.get('role', '')}) \u2014 {u.get('name', '')}")
            with st.container(border=True):
                nu_login = st.text_input("\u041b\u043e\u0433\u0438\u043d:", key="nu_login")
                nu_name = st.text_input("\u0418\u043c\u044f:", key="nu_name")
                nu_pwd = st.text_input("\u041f\u0430\u0440\u043e\u043b\u044c:", key="nu_pwd")
                nu_role = st.selectbox("\u0420\u043e\u043b\u044c:", ["manager", "admin"], key="nu_role")
                if st.button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c", key="nu_go", use_container_width=True, type="primary"):
                    if nu_login.strip() and nu_pwd.strip():
                        if any(u["login"] == nu_login.strip() for u in users):
                            st.warning("\u041b\u043e\u0433\u0438\u043d \u0437\u0430\u043d\u044f\u0442")
                        else:
                            st.session_state.crm_store.setdefault("users", []).append({"login": nu_login.strip(), "password": hash_password(nu_pwd), "role": nu_role, "name": nu_name.strip() or nu_login.strip()})
                            commit_and_rerun(st.session_state.crm_store, "\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c \u0441\u043e\u0437\u0434\u0430\u043d")
    if st.button("\u0412\u044b\u0439\u0442\u0438", key="logout_btn", use_container_width=True):
        st.session_state.current_user = None
        st.session_state.user_role = None
        st.session_state.user_name = ""
        st.rerun()
    st.markdown("---")
    tabs_list = ["\u041a\u043b\u0438\u0435\u043d\u0442\u044b \u0438 \u0441\u0434\u0435\u043b\u043a\u0438", "\u041f\u043b\u0430\u043d\u0438\u0440\u043e\u0432\u0449\u0438\u043a", "\u0412\u043d\u0443\u0442\u0440\u0435\u043d\u043d\u0438\u0435 \u0437\u0430\u0434\u0430\u0447\u0438", "\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0438"]
    st.session_state.active_tab = st.radio("\u0412\u043a\u043b\u0430\u0434\u043a\u0430:", tabs_list, key="tab_radio", horizontal=False)
    st.markdown("---")
    cloud_ok = check_cloud_status()
    if cloud_ok:
        st.caption("\u2705 \u041e\u0431\u043b\u0430\u043a\u043e \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u043e")
    else:
        st.caption("\u26a0\ufe0f \u041e\u0431\u043b\u0430\u043a\u043e \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e")
    csv_data = export_clients_csv()
    st.download_button("\u042d\u043a\u0441\u043f\u043e\u0440\u0442 CSV", data=csv_data, file_name="clients.csv", mime="text/csv", key="csv_export")
# --- Вкладка: Клиенты и сделки ---
if st.session_state.active_tab == "\u041a\u043b\u0438\u0435\u043d\u0442\u044b \u0438 \u0441\u0434\u0435\u043b\u043a\u0438":
    st.markdown('<div class="greeting-block">', unsafe_allow_html=True)
    st.markdown("### \u0410\u0439\u043f\u043b\u0438\u043d\u0442 CRM \u2014 \u041a\u043b\u0438\u0435\u043d\u0442\u044b \u0438 \u0441\u0434\u0435\u043b\u043a\u0438")
    st.markdown('</div>', unsafe_allow_html=True)
    col_s, col_a, col_n = st.columns([4, 2, 1])
    with col_s:
        search = st.text_input("\u041f\u043e\u0438\u0441\u043a:", key="cl_search", placeholder="\u0418\u043c\u044f, \u0442\u0435\u043b\u0435\u0444\u043e\u043d, \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f...", label_visibility="collapsed")
    with col_a:
        all_mgrs = get_managers_list()
        mgr_filter = st.selectbox(["\u0412\u0441\u0435"] + all_mgrs, key="cl_mgr_filter", label_visibility="collapsed")
    with col_n:
        show_new = st.session_state.get("show_new_client", False)
        if st.button("\u041d\u043e\u0432\u044b\u0439" if not show_new else "\u0421\u043a\u0440\u044b\u0442\u044c", key="new_cl_btn", type="primary" if not show_new else "secondary", use_container_width=True):
            st.session_state.show_new_client = not show_new
            st.rerun()
    if show_new:
        render_client_form(st.session_state.client_form_version)
    clients = st.session_state.crm_store.get("clients", [])
    if search.strip():
        s = search.strip().lower()
        clients = [c for c in clients if s in c.get("name", "").lower() or s in c.get("phone", "").lower() or s in c.get("category", "").lower() or s in c.get("email", "").lower()]
    if mgr_filter and mgr_filter != "\u0412\u0441\u0435":
        clients = [c for c in clients if c.get("manager", "") == mgr_filter]
    if clients:
        clients.sort(key=lambda c: get_sort_key(c), reverse=True)
        for cl in clients:
            render_client_in_tree(cl)
    else:
        st.info("\u041a\u043b\u0438\u0435\u043d\u0442\u043e\u0432 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e")

# --- Вкладка: Планировщик ---
elif st.session_state.active_tab == "\u041f\u043b\u0430\u043d\u0438\u0440\u043e\u0432\u0449\u0438\u043a":
    st.markdown('<div class="greeting-block">', unsafe_allow_html=True)
    st.markdown("### \u041f\u043b\u0430\u043d\u0438\u0440\u043e\u0432\u0449\u0438\u043a")
    st.markdown('</div>', unsafe_allow_html=True)
    all_tasks = []
    for cl in st.session_state.crm_store.get("clients", []):
        for t in cl.get("tasks", []):
            all_tasks.append((t, cl))
    all_tasks.sort(key=lambda x: get_task_sort_date(x[0]))
    overdue_tasks = [x for x in all_tasks if is_task_overdue(x[0])]
    today_tasks = [x for x in all_tasks if not x[0].get("done") and not is_task_overdue(x[0])]
    done_tasks = [x for x in all_tasks if x[0].get("done")]
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("\u041f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e", len(overdue_tasks))
    with m2:
        st.metric("\u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0435", len(today_tasks))
    with m3:
        st.metric("\u0412\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043e", len(done_tasks))
    if overdue_tasks:
        st.markdown("**\u041f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u044b\u0435 \u0437\u0430\u0434\u0430\u0447\u0438:**")
        for t, cl in overdue_tasks:
            tp = t.get("type", "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f")
            fd = format_date(t.get("deadline", ""))
            btn_label = f"\u26a0\ufe0f \u0417\u0430\u0434\u0430\u0447\u0430 \u2116{t.get('task_number', '')} \u2014 {cl['name']} | {tp} | {t.get('text', '')} | \u0421\u0440\u043e\u043a: {fd}"
            st.markdown(f'<div style="background:#FFEBEE;border:1px solid #C62828;border-radius:8px;padding:8px 12px;margin-bottom:6px;">{btn_label}</div>', unsafe_allow_html=True)
    if today_tasks:
        st.markdown("**\u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0435 \u0437\u0430\u0434\u0430\u0447\u0438:**")
        for t, cl in today_tasks:
            tp = t.get("type", "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f")
            fd = format_date(t.get("deadline", ""))
            badge = ""
            if t.get("in_work"): badge += ' <span class="in-work-badge">\u0412 \u0440\u0430\u0431\u043e\u0442\u0435</span>'
            if t.get("ready_to_ship"): badge += ' <span class="ready-badge">\u0413\u043e\u0442\u043e\u0432\u043e</span>'
            if t.get("delegated_to"): badge += f' <span class="delegated-badge">\u0414\u0435\u043b\u0435\u0433\u0438\u0440\u043e\u0432\u0430\u043d\u043e: {t["delegated_to"]}</span>'
            st.markdown(f'<div style="background:#FFFFFF;border:1px solid #DCE0E5;border-radius:8px;padding:8px 12px;margin-bottom:6px;"><b>\u0417\u0430\u0434\u0430\u0447\u0430 \u2116{t.get("task_number", "")}</b> \u2014 {cl["name"]} | {tp} | {t.get("text", "")} | \u0421\u0440\u043e\u043a: {fd}{badge}</div>', unsafe_allow_html=True)
    if done_tasks:
        with st.expander(f"\u0412\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043d\u044b\u0435 \u0437\u0430\u0434\u0430\u0447\u0438 ({len(done_tasks)})", expanded=False):
            for t, cl in done_tasks:
                tp = t.get("type", "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f")
                fd = format_date(t.get("deadline", ""))
                st.markdown(f'<div style="background:#F5F6F8;border:1px solid #C9CFD7;border-radius:8px;padding:8px 12px;margin-bottom:6px;"><b>\u2705 \u0417\u0430\u0434\u0430\u0447\u0430 \u2116{t.get("task_number", "")}</b> \u2014 {cl["name"]} | {tp} | {t.get("text", "")} | \u0412\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043e: {t.get("done_at", "")}</div>', unsafe_allow_html=True)

# --- Вкладка: Внутренние задачи ---
elif st.session_state.active_tab == "\u0412\u043d\u0443\u0442\u0440\u0435\u043d\u043d\u0438\u0435 \u0437\u0430\u0434\u0430\u0447\u0438":
    sub1, sub2, sub3 = st.tabs(["\u0417\u0430\u0434\u0430\u0447\u0438 \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0430\u043c", "\u0427\u0430\u0442", "\u0428\u043f\u0430\u0440\u0433\u0430\u043b\u043a\u0430"])
    with sub1:
        all_users = [u.get("name", u["login"]) for u in st.session_state.crm_store.get("users", []) if u.get("role") != "admin"]
        col_a, col_b = st.columns([3, 1])
        with col_a: itf = st.selectbox("\u0424\u0438\u043b\u044c\u0442\u0440:", ["\u041c\u043d\u0435", "\u041e\u0442 \u043c\u0435\u043d\u044f", "\u0412\u0441\u0435"], key="itf_filter")
        with col_b:
            st.write("")
            if st.button("\u041d\u043e\u0432\u0430\u044f \u0437\u0430\u0434\u0430\u0447\u0430", use_container_width=True, type="primary"):
                st.session_state.show_new_itask = not st.session_state.get("show_new_itask", False)
                st.rerun()
        if st.session_state.get("show_new_itask", False):
            with st.container(border=True):
                it_title = st.text_input("\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a:", key="it_title")
                it_desc = st.text_area("\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435:", key="it_desc")
                it_to = st.selectbox("\u041a\u043e\u043c\u0443:", [""] + all_users, index=0, key="it_to", placeholder="\u0412\u044b\u0431\u0435\u0440\u0438 \u0438\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044f")
                it_dl = st.date_input("\u0421\u0440\u043e\u043a:", format="DD/MM/YYYY", key="it_dl")
                it_pri = st.selectbox("\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442:", ["\u041e\u0431\u044b\u0447\u043d\u044b\u0439", "\u0421\u0440\u043e\u0447\u043d\u044b\u0439"], key="it_pri")
                if st.button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443", key="it_create", use_container_width=True, type="primary"):
                    if it_title.strip() and it_to:
                        st.session_state.crm_store.setdefault("internal_tasks", []).append({"id": str(uuid.uuid4())[:8], "title": it_title.strip(), "description": it_desc.strip(), "assigned_to": it_to, "created_by": cu, "deadline": it_dl.isoformat(), "priority": it_pri, "done": False, "created_at": now_str()})
                        st.session_state.show_new_itask = False
                        commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0441\u043e\u0437\u0434\u0430\u043d\u0430")
                    else:
                        if not it_title.strip(): st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a")
                        if not it_to: st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0438\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044f")
        itasks = st.session_state.crm_store.get("internal_tasks", [])
        filtered_it = []
        for t in itasks:
            if itf == "\u041c\u043d\u0435":
                if t.get("assigned_to") == cu: filtered_it.append(t)
            elif itf == "\u041e\u0442 \u043c\u0435\u043d\u044f":
                if t.get("created_by") == cu: filtered_it.append(t)
            else: filtered_it.append(t)
        filtered_it.sort(key=lambda x: (x.get("done", False), x.get("deadline", "")))
        for t in filtered_it:
            pri_color = "#C62828" if t.get("priority") == "\u0421\u0440\u043e\u0447\u043d\u044b\u0439" else "#2C3E50"
            itask_key = f"itask_{t['id']}"
            is_it_exp = st.session_state.expanded_task_key == itask_key
            it_overdue = False
            try:
                it_dl_date = datetime.strptime(t.get("deadline", ""), "%Y-%m-%d").date()
                it_overdue = it_dl_date < datetime.now().date() and not t.get("done")
            except: pass
            if t.get("done"): it_bg, it_bc = "#F5F6F8", "#C9CFD7"
            elif it_overdue: it_bg, it_bc = "#FFEBEE", "#C62828"
            else: it_bg, it_bc = "#FFFFFF", "#DCE0E5"
            it_label = f"{t['title']} \u2014 {t.get('assigned_to', '')} | {format_date(t.get('deadline', ''))}"
            if it_overdue and not t.get("done"): it_label += " | \u041f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e"
            st.markdown(f"<style>.st-key-itask_wrap_{t['id']} button {{ background-color: {it_bg} !important; color: #2C3E50 !important; border: 2px solid {it_bc} !important; border-radius: 10px !important; }}</style>", unsafe_allow_html=True)
            with st.container(key=f"itask_wrap_{t['id']}"):
                if st.button(it_label, key=f"itask_btn_{t['id']}", use_container_width=True, type="primary" if is_it_exp else "secondary"):
                    st.session_state.expanded_task_key = None if is_it_exp else itask_key
                    st.rerun()
            if is_it_exp:
                with st.container(border=True):
                    st.markdown(f"**\u041e\u0442:** {t.get('created_by', '')} \u2192 **\u041a\u043e\u043c\u0443:** {t.get('assigned_to', '')}")
                    st.markdown(format_created_date(t), unsafe_allow_html=True)
                    st.markdown(f"**\u0421\u0440\u043e\u043a:** {format_date(t.get('deadline', ''))} | **\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442:** <span style='color:{pri_color};font-weight:600'>{t.get('priority', '')}</span>", unsafe_allow_html=True)
                    if t.get("description"): st.markdown(f"**\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435:** {t['description']}")
                    st.markdown(f"**\u0421\u043e\u0437\u0434\u0430\u043d\u043e:** {t.get('created_at', '')}")
                    show_it_edit = st.session_state.get(f"show_it_edit_{t['id']}", False)
                    if st.button("\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c" if not show_it_edit else "\u0421\u043a\u0440\u044b\u0442\u044c", key=f"it_edit_{t['id']}", use_container_width=True):
                        st.session_state[f"show_it_edit_{t['id']}"] = not show_it_edit
                        st.rerun()
                    if show_it_edit:
                        with st.container(border=True):
                            et_title = st.text_input("\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a:", value=t.get("title", ""), key=f"it_et_{t['id']}")
                            et_desc = st.text_area("\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435:", value=t.get("description", ""), key=f"it_ed_{t['id']}")
                            et_to = st.selectbox("\u041a\u043e\u043c\u0443:", [""] + all_users, index=0 if t.get("assigned_to", "") not in all_users else ([""] + all_users).index(t.get("assigned_to", "")), key=f"it_eto_{t['id']}", placeholder="\u0412\u044b\u0431\u0435\u0440\u0438 \u0438\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044f")
                            et_dl = st.date_input("\u0421\u0440\u043e\u043a:", value=parse_deadline(t.get("deadline", "")), format="DD/MM/YYYY", key=f"it_edl_{t['id']}")
                            et_pri = st.selectbox("\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442:", ["\u041e\u0431\u044b\u0447\u043d\u044b\u0439", "\u0421\u0440\u043e\u0447\u043d\u044b\u0439"], index=0 if t.get("priority", "") == "\u041e\u0431\u044b\u0447\u043d\u044b\u0439" else 1, key=f"it_epri_{t['id']}")
                            if st.button("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", key=f"it_esave_{t['id']}", use_container_width=True, type="primary"):
                                if et_to:
                                    t["title"] = et_title
                                    t["description"] = et_desc
                                    t["assigned_to"] = et_to
                                    t["deadline"] = et_dl.isoformat()
                                    t["priority"] = et_pri
                                    st.session_state[f"show_it_edit_{t['id']}"] = False
                                    commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0430")
                                else: st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0438\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044f")
                    st.markdown("---")
                    if not t.get("done"):
                        show_it_complete = f"show_it_complete_{t['id']}"
                        if st.button("\u0412\u044b\u043f\u043e\u043b\u043d\u0438\u0442\u044c", key=f"it_done_{t['id']}", use_container_width=True, type="primary"):
                            st.session_state[show_it_complete] = not st.session_state.get(show_it_complete, False)
                            st.rerun()
                        if st.session_state.get(show_it_complete, False):
                            it_rt = st.text_input("\u041e\u0442\u0447\u0451\u0442 (\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e):", key=f"it_rt_{t['id']}")
                            it_uf = st.file_uploader("\u0424\u0430\u0439\u043b\u044b \u043e\u0442\u0447\u0451\u0442\u0430:", key=f"it_uf_{t['id']}", accept_multiple_files=True)
                            it_cn = st.checkbox("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u043d\u043e\u0432\u0443\u044e \u0437\u0430\u0434\u0430\u0447\u0443", key=f"it_cn_{t['id']}")
                            it_ne, it_ntd, it_ntitle, it_nto = {}, None, None, None
                            if it_cn:
                                it_ntitle = st.text_input("\u0422\u0435\u043c\u0430 \u043d\u043e\u0432\u043e\u0439 \u0437\u0430\u0434\u0430\u0447\u0438:", key=f"it_nt_title_{t['id']}")
                                it_nto = st.selectbox("\u041a\u043e\u043c\u0443:", [""] + all_users, index=0, key=f"it_nt_to_{t['id']}", placeholder="\u0412\u044b\u0431\u0435\u0440\u0438 \u0438\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044f")
                                it_ntd = st.date_input("\u0421\u0440\u043e\u043a:", format="DD/MM/YYYY", key=f"it_nt_dl_{t['id']}")
                                it_ne["description"] = st.text_area("\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435:", key=f"it_nt_desc_{t['id']}")
                                it_ne["priority"] = st.selectbox("\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442:", ["\u041e\u0431\u044b\u0447\u043d\u044b\u0439", "\u0421\u0440\u043e\u0447\u043d\u044b\u0439"], key=f"it_nt_pri_{t['id']}")
                            if st.button("\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c", key=f"it_confirm_{t['id']}", use_container_width=True, type="primary"):
                                if not it_rt.strip(): st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043e\u0442\u0447\u0451\u0442")
                                elif it_cn and (not it_ntitle or not it_ntitle.strip()): st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0442\u0435\u043c\u0443 \u043d\u043e\u0432\u043e\u0439 \u0437\u0430\u0434\u0430\u0447\u0438")
                                elif it_cn and not it_nto: st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0438\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044f \u0434\u043b\u044f \u043d\u043e\u0432\u043e\u0439 \u0437\u0430\u0434\u0430\u0447\u0438")
                                else:
                                    t["done"] = True
                                    t["done_at"] = now_str()
                                    t["completion_report"] = it_rt.strip()
                                    if it_uf:
                                        fi_list = save_uploaded_files(it_uf, 0, "itask_report")
                                        t["completion_files"] = normalize_file_list(fi_list)
                                    if it_cn and it_ntitle:
                                        new_it = {"id": str(uuid.uuid4())[:8], "title": it_ntitle.strip(), "description": it_ne.get("description", ""), "assigned_to": it_nto, "created_by": cu, "deadline": it_ntd.isoformat(), "priority": it_ne.get("priority", "\u041e\u0431\u044b\u0447\u043d\u044b\u0439"), "done": False, "created_at": now_str()}
                                        st.session_state.crm_store.setdefault("internal_tasks", []).append(new_it)
                                    st.session_state[show_it_complete] = False
                                    commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u0430")
                    else:
                        st.caption(f"\u0412\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u0430: {t.get('done_at', '')}")
                        if t.get("completion_report"): st.caption(f"\u041e\u0442\u0447\u0451\u0442: {t['completion_report']}")
                        if t.get("completion_files"):
                            st.markdown("**\u0424\u0430\u0439\u043b\u044b \u043e\u0442\u0447\u0451\u0442\u0430:**")
                            render_file_thumbs(t["completion_files"], f"itask_cf_{t['id']}")
                        if st.button("\u0412\u0435\u0440\u043d\u0443\u0442\u044c \u0432 \u0440\u0430\u0431\u043e\u0442\u0443", key=f"it_reopen_{t['id']}", use_container_width=True):
                            t["done"] = False
                            t.pop("done_at", None)
                            t.pop("completion_report", None)
                            t.pop("completion_files", None)
                            commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0435\u043d\u0430")
                    if t.get("created_by") == cu or st.session_state.user_role == "admin":
                        st.markdown("---")
                        if st.button("\u0423\u0434\u0430\u043b\u0438\u0442\u044c", key=f"it_del_{t['id']}", use_container_width=True):
                            st.session_state.crm_store["internal_tasks"] = [x for x in itasks if x["id"] != t["id"]]
                            commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0443\u0434\u0430\u043b\u0435\u043d\u0430")
        if not filtered_it: st.caption("\u041d\u0435\u0442 \u0437\u0430\u0434\u0430\u0447")
    with sub2:
        chat = st.session_state.crm_store.get("chat_messages", [])
        chat_container = st.container(height=400)
        with chat_container:
            for msg in chat[-100:]:
                is_me = msg.get("user") == cu
                cls = "chat-msg-me" if is_me else "chat-msg-other"
                st.markdown(f'<div class="chat-msg {cls}"><div style="font-size:0.75rem;opacity:0.7;margin-bottom:2px;">{msg.get("user","")} \u2014 {msg.get("time","")}</div>{msg.get("text","")}</div>', unsafe_allow_html=True)
            if not chat: st.caption("\u0421\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0439 \u043f\u043e\u043a\u0430 \u043d\u0435\u0442")
        chat_clr = st.session_state.get("chat_clr")
        if chat_clr:
            st.session_state["chat_input"] = ""
            st.session_state["chat_clr"] = False
        msg_text = st.text_input("\u0421\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435:", key="chat_input", placeholder="\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435...")
        if st.button("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c", key="chat_send", use_container_width=True, type="primary"):
            if msg_text.strip():
                st.session_state.crm_store.setdefault("chat_messages", []).append({"id": str(uuid.uuid4())[:8], "user": cu, "text": msg_text.strip(), "time": datetime.now().strftime("%d.%m.%Y %H:%M")})
                st.session_state["chat_clr"] = True
                commit_and_rerun(st.session_state.crm_store)
            else: st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0442\u0435\u043a\u0441\u0442")
    with sub3:
        qa_entries = st.session_state.crm_store.get("qa_entries", [])
        qa_search = st.text_input("\u041f\u043e\u0438\u0441\u043a \u043f\u043e \u0448\u043f\u0430\u0440\u0433\u0430\u043b\u043a\u0435:", key="qa_search", placeholder="\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0432\u043e\u043f\u0440\u043e\u0441 \u0438\u043b\u0438 \u043a\u043b\u044e\u0447\u0435\u0432\u043e\u0435 \u0441\u043b\u043e\u0432\u043e...").strip().lower()
        with st.expander("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043f\u0438\u0441\u044c", expanded=False):
            qa_q = st.text_input("\u0412\u043e\u043f\u0440\u043e\u0441:", key="qa_q")
            qa_a = st.text_area("\u041e\u0442\u0432\u0435\u0442:", key="qa_a")
            qa_cat = st.text_input("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:", key="qa_cat", placeholder="\u041d\u0430\u043f\u0440: \u0414\u043e\u0441\u0442\u0430\u0432\u043a\u0430, \u041e\u043f\u043b\u0430\u0442\u0430, \u041f\u0440\u043e\u0434\u0443\u043a\u0446\u0438\u044f...")
            if st.button("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c", key="qa_add", use_container_width=True, type="primary"):
                if qa_q.strip() and qa_a.strip():
                    st.session_state.crm_store.setdefault("qa_entries", []).append({"id": str(uuid.uuid4())[:8], "question": qa_q.strip(), "answer": qa_a.strip(), "category": qa_cat.strip() or "\u041e\u0431\u0449\u0435\u0435", "created_by": cu, "created_at": datetime.now().strftime("%Y-%m-%d")})
                    commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u043f\u0438\u0441\u044c \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u0430")
                else: st.warning("\u0417\u0430\u043f\u043e\u043b\u043d\u0438\u0442\u0435 \u0432\u043e\u043f\u0440\u043e\u0441 \u0438 \u043e\u0442\u0432\u0435\u0442")
        filtered_qa = []
        for qa in qa_entries:
            if qa_search:
                ct = f"{qa.get('question', '')} {qa.get('answer', '')} {qa.get('category', '')}".lower()
                if qa_search not in ct: continue
            filtered_qa.append(qa)
        qa_cats = sorted(set(qa.get("category", "\u041e\u0431\u0449\u0435\u0435") for qa in filtered_qa))
        for cat in qa_cats:
            st.markdown(f"**{cat}**")
            for qa in [q for q in filtered_qa if q.get("category", "\u041e\u0431\u0449\u0435\u0435") == cat]:
                with st.container(border=True):
                    st.markdown(f"<div class='qa-card'><b>Q: {qa.get('question', '')}</b><br><br>{qa.get('answer', '')}</div>", unsafe_allow_html=True)
                    qa_copy_btn_id = f"qa_copy_{qa['id']}"
                    render_copy_button(qa.get('answer', ''), qa_copy_btn_id, "\U0001F4CB \u041a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c")
                    show_qa_edit = st.session_state.get(f"show_qa_edit_{qa['id']}", False)
                    if st.button("\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c" if not show_qa_edit else "\u0421\u043a\u0440\u044b\u0442\u044c", key=f"qa_edit_{qa['id']}"):
                        st.session_state[f"show_qa_edit_{qa['id']}"] = not show_qa_edit
                        st.rerun()
                    if show_qa_edit:
                        with st.container(border=True):
                            eq_q = st.text_input("\u0412\u043e\u043f\u0440\u043e\u0441:", value=qa.get("question", ""), key=f"qa_eq_{qa['id']}")
                            eq_a = st.text_area("\u041e\u0442\u0432\u0435\u0442:", value=qa.get("answer", ""), key=f"qa_ea_{qa['id']}")
                            eq_cat = st.text_input("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:", value=qa.get("category", ""), key=f"qa_ec_{qa['id']}")
                            if st.button("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", key=f"qa_es_{qa['id']}", use_container_width=True, type="primary"):
                                qa["question"] = eq_q.strip()
                                qa["answer"] = eq_a.strip()
                                qa["category"] = eq_cat.strip() or "\u041e\u0431\u0449\u0435\u0435"
                                st.session_state[f"show_qa_edit_{qa['id']}"] = False
                                commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u043f\u0438\u0441\u044c \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0430")
                    if st.button("\u0423\u0434\u0430\u043b\u0438\u0442\u044c", key=f"qa_del_{qa['id']}", use_container_width=True):
                        st.session_state.crm_store["qa_entries"] = [x for x in qa_entries if x["id"] != qa["id"]]
                        commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u043f\u0438\u0441\u044c \u0443\u0434\u0430\u043b\u0435\u043d\u0430")
        if not filtered_qa: st.caption("\u0417\u0430\u043f\u0438\u0441\u0435\u0439 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e")

# --- Вкладка: Поставщики ---
elif st.session_state.active_tab == "\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0438":
    st.markdown("### \u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0438")
    suppliers = st.session_state.crm_store.get("suppliers", [])
    with st.expander("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0430", expanded=False):
        sl, sr = st.columns(2)
        with sl:
            sn = st.text_input("\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435:", key="sup_name")
            sp = st.text_input("\u041a\u043e\u043d\u0442\u0430\u043a\u0442\u043d\u043e\u0435 \u043b\u0438\u0446\u043e:", key="sup_person")
            sph = st.text_input("\u0422\u0435\u043b\u0435\u0444\u043e\u043d:", key="sup_phone")
        with sr:
            se = st.text_input("Email:", key="sup_email")
            sa = st.text_input("\u0410\u0434\u0440\u0435\u0441:", key="sup_address")
            sc = st.text_input("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u0442\u043e\u0432\u0430\u0440\u0430:", key="sup_category")
        snote = st.text_area("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:", key="sup_note")
        if st.button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c", key="sup_add_btn", use_container_width=True, type="primary"):
            if sn.strip():
                sid = (max([s.get("id", 0) for s in suppliers]) if suppliers else 0) + 1
                st.session_state.crm_store.setdefault("suppliers", []).append({"id": sid, "name": sn.strip(), "person": sp.strip(), "phone": format_phone(sph), "email": se.strip(), "address": sa.strip(), "category": sc.strip(), "note": snote.strip(), "created_at": now_str(), "last_modified": now_str()})
                commit_and_rerun(st.session_state.crm_store, "\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d")
            else: st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435")
    if suppliers:
        for s in sorted(suppliers, key=lambda x: x.get("last_modified", ""), reverse=True):
            with st.expander(f"{s['name']} \u2014 {s.get('phone', '')} | {s.get('category', '')}"):
                st.markdown(format_created_date(s), unsafe_allow_html=True)
                cl1, cl2 = st.columns(2)
                with cl1:
                    st.markdown(f"**\u041a\u043e\u043d\u0442\u0430\u043a\u0442:** {s.get('person', '\u2014')}")
                    st.markdown(f"**\u0422\u0435\u043b\u0435\u0444\u043e\u043d:** {s.get('phone', '\u2014')}")
                    st.markdown(f"**Email:** {s.get('email', '\u2014')}")
                with cl2:
                    st.markdown(f"**\u0410\u0434\u0440\u0435\u0441:** {s.get('address', '\u2014')}")
                    st.markdown(f"**\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:** {s.get('category', '\u2014')}")
                    if s.get("note"): st.markdown(f"**\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:** {s['note']}")
                show_sup_edit = st.session_state.get(f"show_sup_edit_{s['id']}", False)
                if st.button("\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c" if not show_sup_edit else "\u0421\u043a\u0440\u044b\u0442\u044c", key=f"sup_edit_{s['id']}", use_container_width=True):
                    st.session_state[f"show_sup_edit_{s['id']}"] = not show_sup_edit
                    st.rerun()
                if show_sup_edit:
                    with st.container(border=True):
                        en = st.text_input("\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435:", value=s["name"], key=f"sup_en_{s['id']}")
                        ep = st.text_input("\u041a\u043e\u043d\u0442\u0430\u043a\u0442:", value=s.get("person", ""), key=f"sup_ep_{s['id']}")
                        eph = st.text_input("\u0422\u0435\u043b\u0435\u0444\u043e\u043d:", value=s.get("phone", ""), key=f"sup_eph_{s['id']}")
                        ee = st.text_input("Email:", value=s.get("email", ""), key=f"sup_ee_{s['id']}")
                        ea = st.text_input("\u0410\u0434\u0440\u0435\u0441:", value=s.get("address", ""), key=f"sup_ea_{s['id']}")
                        ec = st.text_input("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:", value=s.get("category", ""), key=f"sup_ec_{s['id']}")
                        enote = st.text_area("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:", value=s.get("note", ""), key=f"sup_enote_{s['id']}")
                        if st.button("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", key=f"sup_save_{s['id']}", use_container_width=True, type="primary"):
                            s["name"], s["person"], s["phone"], s["email"], s["address"], s["category"], s["note"] = en, ep, format_phone(eph), ee, ea, ec, enote
                            s["last_modified"] = now_str()
                            st.session_state[f"show_sup_edit_{s['id']}"] = False
                            commit_and_rerun(st.session_state.crm_store, "\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a \u043e\u0431\u043d\u043e\u0432\u043b\u0451\u043d")
                if st.session_state.user_role == "admin":
                    st.markdown("---")
                    if st.button("\u0423\u0434\u0430\u043b\u0438\u0442\u044c", key=f"sup_del_{s['id']}", use_container_width=True):
                        st.session_state.crm_store["suppliers"] = [x for x in suppliers if x["id"] != s["id"]]
                        commit_and_rerun(st.session_state.crm_store, "\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a \u0443\u0434\u0430\u043b\u0451\u043d")
    else:
        st.info("\u0411\u0430\u0437\u0430 \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u043e\u0432 \u043f\u0443\u0441\u0442\u0430. \u0414\u043e\u0431\u0430\u0432\u044c\u0442\u0435 \u043f\u0435\u0440\u0432\u043e\u0433\u043e \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0430.")
