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
def render_task_detail(t, cl, d, key_prefix):
    with st.container(border=True):
        st.markdown(f"**\u0417\u0430\u0434\u0430\u0447\u0430 \u2116{t.get('task_number', '')}**")
        st.markdown(format_created_date(t), unsafe_allow_html=True)
        st.markdown(f"**\u0422\u0435\u043c\u0430:** {t.get('text', '')}")
        st.markdown(f"**\u0422\u0438\u043f:** {t.get('type', '\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f')}")
        st.markdown(f"**\u0421\u0440\u043e\u043a:** {format_date(t.get('deadline', ''))}")
        st.markdown(f"**\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:** {t.get('manager', '\u2014')}")
        if t.get('in_work') and not t.get('done'):
            st.markdown('<span class="in-work-badge">\u0412 \u0440\u0430\u0431\u043e\u0442\u0435</span>', unsafe_allow_html=True)
        if t.get('delegated_to') and t.get('delegated_to') != t.get('manager'):
            st.markdown(f'<span class="delegated-badge">\u0414\u0435\u043b\u0435\u0433\u0438\u0440\u043e\u0432\u0430\u043d\u043e: {t["delegated_to"]}</span>', unsafe_allow_html=True)
        if t.get('products'): st.markdown(f"**\u0422\u043e\u0432\u0430\u0440\u044b:** {t['products']}")
        if t.get('ship_addr'): st.markdown(f"**\u0410\u0434\u0440\u0435\u0441:** {t['ship_addr']}")
        if t.get('receiver'): st.markdown(f"**\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:** {t['receiver']} ({t.get('receiver_phone', '')})")
        if t.get('ship_pay'): st.markdown(f"**\u041e\u043f\u043b\u0430\u0442\u0430:** {t['ship_pay']}")
        if t.get('tk_num'):
            st.markdown(f"**\u0422\u0440\u0435\u043a:**")
            render_track_inline(t['tk_num'], key_prefix)
        if t.get('order_amount', 0) > 0: st.markdown(f"**\u0421\u0443\u043c\u043c\u0430:** {t['order_amount']:,.0f} \u0440\u0443\u0431.".replace(",", " "))
        if t.get('ready_to_ship'): st.markdown('<span class="ready-badge">\u0413\u043e\u0442\u043e\u0432\u043e \u043a \u043e\u0442\u043f\u0440\u0430\u0432\u043a\u0435</span>', unsafe_allow_html=True)
        if t.get('task_comment'): st.markdown(f"**\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438:** {t['task_comment']}")
        if t.get("task_files"):
            st.markdown("**\u0424\u0430\u0439\u043b\u044b \u0437\u0430\u0434\u0430\u0447\u0438:**")
            render_file_thumbs(t["task_files"], f"{key_prefix}_files")
        st.markdown("**\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0444\u0430\u0439\u043b\u044b \u0432 \u0437\u0430\u0434\u0430\u0447\u0443:**")
        ntf_existing = st.file_uploader("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0444\u0430\u0439\u043b\u044b:", key=f"task_upload_{key_prefix}", accept_multiple_files=True, label_visibility="collapsed")
        if st.button("\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c", key=f"task_upload_btn_{key_prefix}", use_container_width=True):
            if ntf_existing:
                fi_list = save_uploaded_files(ntf_existing, (d["client_id"] if d else cl["id"]), "task_file")
                if fi_list:
                    t.setdefault("task_files", []).extend(normalize_file_list(fi_list))
                    t["last_modified"] = now_str()
                    cl["last_modified"] = now_str()
                    if d: d["last_modified"] = now_str()
                    commit_and_rerun(st.session_state.crm_store, "\u0424\u0430\u0439\u043b\u044b \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u044b")
            else: st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0444\u0430\u0439\u043b(\u044b)")
        st.markdown("---")
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
        tk_done = t.get("done", False)
        if not tk_done:
            render_print_button(t, cl, t.get('type', '\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f'), format_date(t.get('deadline', '')), f"{key_prefix}_print")
            if t.get("task_files"):
                render_print_file_button(t["task_files"], f"{key_prefix}_pfile")
            st.markdown("---")
            show_edit_task = st.session_state.get(f"show_edit_task_{key_prefix}", False)
            if st.button("\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443" if not show_edit_task else "\u0421\u043a\u0440\u044b\u0442\u044c", key=f"btn_edit_task_{key_prefix}", use_container_width=True):
                st.session_state[f"show_edit_task_{key_prefix}"] = not show_edit_task
                st.rerun()
            if show_edit_task:
                render_task_edit_form(t, cl, d, key_prefix)
            st.markdown("---")
            tc1, tc2 = st.columns(2)
            with tc1:
                if not t.get('in_work'):
                    if st.button("\u0412\u0437\u044f\u0442\u044c \u0432 \u0440\u0430\u0431\u043e\u0442\u0443", key=f"btn_inwork_{key_prefix}", type="primary", use_container_width=True):
                        t["in_work"] = True
                        t["in_work_by"] = st.session_state.user_name
                        t["last_modified"] = now_str()
                        commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0432\u0437\u044f\u0442\u0430 \u0432 \u0440\u0430\u0431\u043e\u0442\u0443")
                else:
                    if st.button("\u0421\u043d\u044f\u0442\u044c \u0441 \u0440\u0430\u0431\u043e\u0442\u044b", key=f"btn_unwork_{key_prefix}", use_container_width=True):
                        t["in_work"] = False
                        t.pop("in_work_by", None)
                        t["last_modified"] = now_str()
                        commit_and_rerun(st.session_state.crm_store)
            with tc2:
                if st.button("\u0414\u0435\u043b\u0435\u0433\u0438\u0440\u043e\u0432\u0430\u0442\u044c", key=f"btn_delegate_{key_prefix}", use_container_width=True):
                    st.session_state[f"show_delegate_{key_prefix}"] = not st.session_state.get(f"show_delegate_{key_prefix}", False)
                    st.rerun()
            if st.session_state.get(f"show_delegate_{key_prefix}", False):
                with st.container(border=True):
                    dlg_to = st.selectbox("\u0414\u0435\u043b\u0435\u0433\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043d\u0430:", [""] + get_managers_list(), index=0, key=f"dlg_to_{key_prefix}", placeholder=MGR_PLACEHOLDER)
                    if st.button("\u041f\u0435\u0440\u0435\u043d\u0430\u0437\u043d\u0430\u0447\u0438\u0442\u044c", key=f"dlg_go_{key_prefix}", type="primary", use_container_width=True):
                        if dlg_to:
                            t["delegated_to"] = dlg_to
                            t["manager"] = dlg_to
                            t["last_modified"] = now_str()
                            cl["last_modified"] = now_str()
                            if d: d["last_modified"] = now_str()
                            st.session_state[f"show_delegate_{key_prefix}"] = False
                            commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0434\u0435\u043b\u0435\u0433\u0438\u0440\u043e\u0432\u0430\u043d\u0430")
                        else: st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0430")
            st.markdown("---")
            show_key = f"show_complete_{key_prefix}"
            if st.button("\u0412\u044b\u043f\u043e\u043b\u043d\u0438\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443", key=f"btn_complete_{key_prefix}", type="primary", use_container_width=True):
                st.session_state[show_key] = not st.session_state.get(show_key, False)
                st.rerun()
            if st.session_state.get(show_key, False):
                rt = st.text_input("\u041e\u0442\u0447\u0451\u0442 (\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e):", key=f"rt_{key_prefix}")
                uf = st.file_uploader("\u0424\u0430\u0439\u043b\u044b/\u0444\u043e\u0442\u043e \u043e\u0442\u0447\u0451\u0442\u0430:", key=f"uf_{key_prefix}", accept_multiple_files=True)
                if st.button("\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c", key=f"go_{key_prefix}", use_container_width=True, type="primary"):
                    if rt.strip():
                        t["done"] = True
                        t["completion_report"] = rt.strip()
                        t["last_modified"] = now_str()
                        fi_list = save_uploaded_files(uf, (d["client_id"] if d else cl["id"]), "task_report")
                        if fi_list: t["completion_files"] = normalize_file_list(fi_list)
                        cl["last_modified"] = now_str()
                        if d: d["last_modified"] = now_str()
                        st.session_state[show_key] = False
                        commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u0430")
                    else: st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043e\u0442\u0447\u0451\u0442")
            st.markdown("---")
            ndd = st.date_input("\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0441\u0440\u043e\u043a:", value=parse_deadline(t.get("deadline", "")), format="DD/MM/YYYY", key=f"dl_{key_prefix}")
            if st.button("\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u0441\u0440\u043e\u043a", key=f"dl_btn_{key_prefix}"):
                t["deadline"] = ndd.isoformat()
                t["last_modified"] = now_str()
                cl["last_modified"] = now_str()
                if d: d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "\u0421\u0440\u043e\u043a \u043e\u0431\u043d\u043e\u0432\u043b\u0451\u043d")
        else:
            if t.get("completion_report"): st.caption(f"\u041e\u0442\u0447\u0451\u0442: {t['completion_report']}")
            if t.get("completion_files"):
                st.markdown("**\u0424\u0430\u0439\u043b\u044b \u043e\u0442\u0447\u0451\u0442\u0430:**")
                render_file_thumbs(t["completion_files"], f"{key_prefix}_cfiles")

def render_task_row(t, cl, d, task_key, key_prefix):
    is_tk_exp = st.session_state.expanded_task_key == task_key
    tk_done = t.get("done", False)
    tk_overdue = is_task_overdue(t)
    if tk_done: tk_bg, tk_bc = "#F5F6F8", "#C9CFD7"
    elif tk_overdue: tk_bg, tk_bc = "#FFEBEE", "#C62828"
    else: tk_bg, tk_bc = "#E8F5E9", "#4CAF50"
    tk_label = f"\u0417\u0430\u0434\u0430\u0447\u0430 \u2116{t.get('task_number', '')} \u2014 {t.get('text', '')} | {format_date(t.get('deadline', ''))}"
    if t.get('in_work') and not tk_done: tk_label += ' | \u0412 \u0440\u0430\u0431\u043e\u0442\u0435'
    if t.get('ready_to_ship') and not tk_done: tk_label += ' | \u0413\u043e\u0442\u043e\u0432\u043e \u043a \u043e\u0442\u043f\u0440\u0430\u0432\u043a\u0435'
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
        if t.get("file_path"): t["task_files"].append({"file_path": t["file_path"], "file_name": t.get("file_name", "\u0444\u0430\u0439\u043b"), "file_hash": ""})
    if "completion_files" not in t:
        t["completion_files"] = []
        if t.get("completion_file_path"): t["completion_files"].append({"file_path": t["completion_file_path"], "file_name": t.get("completion_file_name", "\u0444\u0430\u0439\u043b"), "file_hash": ""})
    if "task_comments" not in t: t["task_comments"] = []
    if "in_work" not in t: t["in_work"] = False
    if "ready_to_ship" not in t: t["ready_to_ship"] = False
    if "delegated_to" not in t: t["delegated_to"] = None
    if "created_at" not in t: t["created_at"] = t.get("last_modified", "")
    if "flagged" not in t: t["flagged"] = False
    if "type" not in t: t["type"] = "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f"
    if "products" not in t: t["products"] = ""
    if "ship_addr" not in t: t["ship_addr"] = ""
    if "receiver" not in t: t["receiver"] = ""
    if "receiver_phone" not in t: t["receiver_phone"] = ""
    if "ship_pay" not in t: t["ship_pay"] = ""
    if "tk_num" not in t: t["tk_num"] = ""
    if t.get("type") == "\u041e\u0442\u043f\u0440\u0430\u0432\u043a\u0430": t["type"] = "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437"

def migrate_data(data):
    du = [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "\u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440"}]
    if "users" not in data: data["users"] = du
    for u in data["users"]:
        if not is_hashed(u.get("password", "")): u["password"] = hash_password(u["password"])
    for c in data.get("clients", []):
        client_deals = [d for d in data.get("deals", []) if d.get("client_id") == c["id"]]
        first_deal_id = client_deals[0]["id"] if client_deals else None
        for k, v in [("email",""),("address",""),("base_comment",""),("category","\u041d\u0435 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0451\u043d"),("discount",0),("extra_phones",[]),("extra_emails",[]),("extra_addresses",[]),("client_files",[]),("client_comments",[]),("manager",""),("comments",[]),("tasks",[]),("last_modified","1970-01-01 00:00:00"),("client_chat",[]),("created_at","")]:
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
        if "payment_status" not in d: d["payment_status"] = "\u041d\u0435 \u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043e"
        if "manager" not in d: d["manager"] = ""
        if "close_files" not in d:
            d["close_files"] = []
            if d.get("close_file_path"): d["close_files"].append({"file_path": d["close_file_path"], "file_name": d.get("close_file_name", "\u0444\u0430\u0439\u043b"), "file_hash": ""})
        if "last_modified" not in d: d["last_modified"] = "1970-01-01 00:00:00"
        if "deal_chat" not in d: d["deal_chat"] = []
        if "deal_number" not in d: d["deal_number"] = ""
        if "created_at" not in d: d["created_at"] = ""
        if d.get("status") == "New": d["status"] = "\u041d\u043e\u0432\u044b\u0439"
        if d.get("status") == "\u041d\u0430 \u0441\u043e\u0433\u043b\u0430\u0441\u043e\u0432\u0430\u043d\u0438\u0438": d["status"] = "\u0412 \u0440\u0430\u0431\u043e\u0442\u0435"
        if d.get("title", "").startswith("\u0417\u0430\u043a\u0430\u0437"): d["title"] = d.get("deal_number", d["title"])
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
    db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "\u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440"}], "_migrated": "v2", "internal_tasks": [], "chat_messages": [], "qa_entries": [], "suppliers": []}
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
                        if "ready_to_ship" not in t: t["ready_to_ship"] = False
                        if "delegated_to" not in t: t["delegated_to"] = None
                        if "task_comments" not in t: t["task_comments"] = []
                        if "flagged" not in t: t["flagged"] = False
                        if "type" not in t: t["type"] = "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f"
                        if "products" not in t: t["products"] = ""
                        if "ship_addr" not in t: t["ship_addr"] = ""
                        if "receiver" not in t: t["receiver"] = ""
                        if "receiver_phone" not in t: t["receiver_phone"] = ""
                        if "ship_pay" not in t: t["ship_pay"] = ""
                        if "tk_num" not in t: t["tk_num"] = ""
                        if t.get("type") == "\u041e\u0442\u043f\u0440\u0430\u0432\u043a\u0430": t["type"] = "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437"
                        migrate_task_files(t)
                for d in data.get("deals", []):
                    if "deal_title" not in d: d["deal_title"] = ""
                    if "deal_files" not in d: d["deal_files"] = []
                    if "payment_status" not in d: d["payment_status"] = "\u041d\u0435 \u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043e"
                    if "manager" not in d: d["manager"] = ""
                    if "close_files" not in d:
                        d["close_files"] = []
                        if d.get("close_file_path"): d["close_files"].append({"file_path": d["close_file_path"], "file_name": d.get("close_file_name", "\u0444\u0430\u0439\u043b"), "file_hash": ""})
                    if "last_modified" not in d: d["last_modified"] = "1970-01-01 00:00:00"
                    if "deal_chat" not in d: d["deal_chat"] = []
                    if "deal_number" not in d: d["deal_number"] = ""
                    if "created_at" not in d: d["created_at"] = d.get("last_modified", "")
                    if d.get("status") == "\u041d\u0430 \u0441\u043e\u0433\u043b\u0430\u0441\u043e\u0432\u0430\u043d\u0438\u0438": d["status"] = "\u0412 \u0440\u0430\u0431\u043e\u0442\u0435"
                    if d.get("title", "").startswith("\u0417\u0430\u043a\u0430\u0437"): d["title"] = d.get("deal_number", d["title"])
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
        st.sidebar.error(f"\u041e\u0448\u0438\u0431\u043a\u0430 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u044f: {e}")

def commit_and_rerun(data=None, toast_msg=None):
    if data is not None:
        save_data(data)
    if toast_msg:
        st.toast(toast_msg, icon="\u2705")
    st.rerun()

@st.dialog("\u0417\u0430\u0432\u0435\u0440\u0448\u0438\u0442\u044c \u0441\u0434\u0435\u043b\u043a\u0443", width="medium")
def close_deal_dialog(deal_id):
    deal = None
    for d in st.session_state.crm_store["deals"]:
        if d["id"] == deal_id:
            deal = d
            break
    if not deal:
        st.error("\u0421\u0434\u0435\u043b\u043a\u0430 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430")
        return
    client = get_client_by_id(deal["client_id"])
    incomplete = [t for t in (client.get("tasks", []) if client else []) if not t.get("done") and t.get("deal_id") == deal_id]
    if incomplete:
        st.warning(f"\u041d\u0435\u043b\u044c\u0437\u044f \u0437\u0430\u0432\u0435\u0440\u0448\u0438\u0442\u044c \u0441\u0434\u0435\u043b\u043a\u0443: {len(incomplete)} \u043d\u0435\u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043d\u044b\u0445 \u0437\u0430\u0434\u0430\u0447(\u0438).")
        for t in incomplete:
            st.markdown(f"- \u2116{t.get('task_number', '')} \u2014 {format_date(t.get('deadline', ''))} \u2014 {t.get('text', '')}")
        if st.button("\u041f\u043e\u043d\u044f\u0442\u043d\u043e", use_container_width=True):
            st.rerun()
        return
    st.markdown("\u0417\u0430\u043f\u043e\u043b\u043d\u0438\u0442\u0435 \u043e\u0442\u0447\u0451\u0442 \u043e \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0438 \u0441\u0434\u0435\u043b\u043a\u0438:")
    report = st.text_area("\u041e\u0442\u0447\u0451\u0442 (\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e):", key=f"close_deal_report_{deal_id}", height=80)
    close_files = st.file_uploader("\u0424\u0430\u0439\u043b\u044b \u0437\u0430\u043a\u0440\u044b\u0442\u0438\u044f:", key=f"close_deal_file_{deal_id}", accept_multiple_files=True)
    if st.button("\u0417\u0430\u0432\u0435\u0440\u0448\u0438\u0442\u044c \u0441\u0434\u0435\u043b\u043a\u0443", type="primary", use_container_width=True):
        if report.strip():
            for d in st.session_state.crm_store["deals"]:
                if d["id"] == deal_id:
                    d['status'] = "\u0421\u0434\u0435\u043b\u043a\u0430 \u0437\u0430\u043a\u0440\u044b\u0442\u0430"
                    d['closed_date'] = datetime.now().strftime("%Y-%m-%d")
                    d['close_report'] = report.strip()
                    d['close_files'] = normalize_file_list(save_uploaded_files(close_files, d["client_id"], "deal_close")) if close_files else []
                    d["last_modified"] = now_str()
                    break
            save_data(st.session_state.crm_store)
            st.toast("\u0421\u0434\u0435\u043b\u043a\u0430 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0430", icon="\u2705")
            st.rerun()
        else:
            st.error("\u0417\u0430\u043f\u043e\u043b\u043d\u0438\u0442\u0435 \u043e\u0442\u0447\u0451\u0442")

if "crm_store" not in st.session_state:
    with st.spinner("\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0434\u0430\u043d\u043d\u044b\u0445..."):
        st.session_state.crm_store = load_data()
if "f_ph" not in st.session_state: st.session_state.f_ph = []
if "f_em" not in st.session_state: st.session_state.f_em = []
if "f_ad" not in st.session_state: st.session_state.f_ad = []
if "last_id" not in st.session_state: st.session_state.last_id = None
if "active_tab" not in st.session_state: st.session_state.active_tab = "\u041f\u043b\u0430\u043d\u0438\u0440\u043e\u0432\u0449\u0438\u043a"
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
if "expanded_tree_id" not in st.session_state: st.session_state.expanded_tree_id = None
if "auto_expand_deal_id" not in st.session_state: st.session_state.auto_expand_deal_id = None
if "scroll_to_deal" not in st.session_state: st.session_state.scroll_to_deal = None

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

MGR_PLACEHOLDER = "\u0412\u044b\u0431\u0435\u0440\u0438 \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0433\u043e"

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
    st.markdown("<h2 style='text-align: center; margin-top: 3rem;'>\u0410\u0439\u043f\u043b\u0438\u043d\u0442 CRM</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #7F8C9A; margin-bottom: 2rem;'>\u0410\u0432\u0442\u043e\u0440\u0438\u0437\u0443\u0439\u0442\u0435\u0441\u044c \u0434\u043b\u044f \u0432\u0445\u043e\u0434\u0430 \u0432 \u0441\u0438\u0441\u0442\u0435\u043c\u0443</p>", unsafe_allow_html=True)
    lc, mc, rc = st.columns([1, 2, 1])
    with mc:
        with st.container(border=True):
            iu = st.text_input("\u041b\u043e\u0433\u0438\u043d:", placeholder="\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043b\u043e\u0433\u0438\u043d")
            ip = st.text_input("\u041f\u0430\u0440\u043e\u043b\u044c:", type="password", placeholder="\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043f\u0430\u0440\u043e\u043b\u044c")
            if st.button("\u0412\u043e\u0439\u0442\u0438", use_container_width=True, type="primary"):
                if check_login(iu, ip):
                    _token = secrets.token_hex(16)
                    for u in st.session_state.crm_store["users"]:
                        if u["login"] == iu.strip():
                            u["auth_token"] = _token
                            break
                    save_data(st.session_state.crm_store)
                    st.query_params["auth_token"] = _token
                    st.toast("\u0423\u0441\u043f\u0435\u0448\u043d\u044b\u0439 \u0432\u0445\u043e\u0434", icon="\U0001F513")
                    st.rerun()
                else:
                    st.error("\u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u043b\u043e\u0433\u0438\u043d \u0438\u043b\u0438 \u043f\u0430\u0440\u043e\u043b\u044c.")
    st.stop()

st.markdown(f"""<div class="greeting-block"><h1 style='text-align: center; margin-bottom: 0.1rem;'>\u0410\u0439\u043f\u043b\u0438\u043d\u0442 CRM</h1><p style='text-align: center; color: #7F8C9A; font-size: 0.95rem; margin-top: 0; margin-bottom: 0;'>\u041f\u0440\u043e\u0434\u0443\u043a\u0442\u0438\u0432\u043d\u043e\u0433\u043e \u0442\u0435\u0431\u0435 \u0434\u043d\u044f, {st.session_state.user_name} \U0001F60A</p></div>""", unsafe_allow_html=True)

with st.sidebar:
    if st.session_state.cloud_ok: st.success("\u041e\u0431\u043b\u0430\u043a\u043e \u0430\u043a\u0442\u0438\u0432\u043d\u043e")
    else: st.warning("\u041e\u0431\u043b\u0430\u043a\u043e \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e (\u0440\u0430\u0431\u043e\u0442\u0430 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e)")
    st.markdown("---")
    st.markdown(f"**{st.session_state.user_name}**")
    st.markdown(f"\u0420\u043e\u043b\u044c: `{st.session_state.user_role}`")
    with st.expander("\u0421\u043c\u0435\u043d\u0438\u0442\u044c \u043f\u0430\u0440\u043e\u043b\u044c"):
        cul = st.session_state.user_login
        np = st.text_input("\u041d\u043e\u0432\u044b\u0439 \u043f\u0430\u0440\u043e\u043b\u044c:", type="password", key="self_new_pwd")
        cp = st.text_input("\u041f\u043e\u0432\u0442\u043e\u0440\u0438\u0442\u0435 \u043f\u0430\u0440\u043e\u043b\u044c:", type="password", key="self_conf_pwd")
        if st.button("\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c", key="btn_save_self_pwd", use_container_width=True):
            if np and np == cp:
                _new_token = secrets.token_hex(16)
                for u in st.session_state.crm_store["users"]:
                    if u["login"] == cul:
                        u["password"] = hash_password(np)
                        u["auth_token"] = _new_token
                save_data(st.session_state.crm_store)
                st.query_params["auth_token"] = _new_token
                st.toast("\u041f\u0430\u0440\u043e\u043b\u044c \u0438\u0437\u043c\u0435\u043d\u0451\u043d", icon="\u2705")
                st.rerun()
            else: st.error("\u041f\u0430\u0440\u043e\u043b\u0438 \u043d\u0435 \u0441\u043e\u0432\u043f\u0430\u0434\u0430\u044e\u0442")
    if st.session_state.user_role == "admin":
        with st.expander("\u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u0431\u0430\u0437\u044b"):
            st.download_button("\u0421\u043a\u0430\u0447\u0430\u0442\u044c CSV", data=export_clients_csv(), file_name="clients_export.csv", mime="text/csv", use_container_width=True)
        with st.expander("\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0430\u043c\u0438"):
            st.markdown("### \u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0430")
            nul = st.text_input("\u041b\u043e\u0433\u0438\u043d:", key="adm_nu_l")
            nup = st.text_input("\u041f\u0430\u0440\u043e\u043b\u044c:", key="adm_nu_p")
            nun = st.text_input("\u0418\u043c\u044f / \u0414\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u044c:", key="adm_nu_n")
            nur = st.selectbox("\u0420\u043e\u043b\u044c:", ["manager", "admin"], key="adm_nu_r")
            if st.button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c", use_container_width=True, type="primary"):
                if nul and nup and nun:
                    if not any(u["login"] == nul.strip() for u in st.session_state.crm_store.get("users", [])):
                        st.session_state.crm_store.setdefault("users", []).append({"login": nul.strip(), "password": hash_password(nup), "role": nur, "name": nun.strip()})
                        commit_and_rerun(st.session_state.crm_store, "\u0421\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a \u0441\u043e\u0437\u0434\u0430\u043d")
                    else: st.error("\u041b\u043e\u0433\u0438\u043d \u0443\u0436\u0435 \u0437\u0430\u043d\u044f\u0442")
                else: st.error("\u0417\u0430\u043f\u043e\u043b\u043d\u0438\u0442\u0435 \u0432\u0441\u0435 \u043f\u043e\u043b\u044f")
            st.markdown("---")
            for u in st.session_state.crm_store.get("users", []):
                ucl, ucr = st.columns([3, 1])
                with ucl: st.markdown(f"**{u.get('name', u['login'])}** ({u['role']})")
                with ucr:
                    if u["login"] != st.session_state.user_login:
                        if st.button("X", key=f"del_u_{u['login']}", help="\u0423\u0434\u0430\u043b\u0438\u0442\u044c"):
                            st.session_state.crm_store["users"] = [x for x in st.session_state.crm_store["users"] if x["login"] != u["login"]]
                            commit_and_rerun(st.session_state.crm_store, "\u0421\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a \u0443\u0434\u0430\u043b\u0451\u043d")
    st.markdown("---")
    if st.button("\u0412\u044b\u0439\u0442\u0438", use_container_width=True):
        _tok = st.query_params.get("auth_token")
        if _tok:
            for u in st.session_state.crm_store.get("users", []):
                if u.get("auth_token") == _tok:
                    u.pop("auth_token", None)
            save_data(st.session_state.crm_store)
            if "auth_token" in st.query_params:
                del st.query_params["auth_token"]
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_login = None
        st.session_state.user_name = None
        st.rerun()

nc1, nc2, nc3, nc4 = st.columns(4)
with nc1:
    if st.button("\u041a\u043b\u0438\u0435\u043d\u0442\u044b \u0438 \u0441\u0434\u0435\u043b\u043a\u0438", use_container_width=True, type="primary" if st.session_state.active_tab == "\u041a\u043b\u0438\u0435\u043d\u0442\u044b \u0438 \u0441\u0434\u0435\u043b\u043a\u0438" else "secondary"):
        st.session_state.active_tab = "\u041a\u043b\u0438\u0435\u043d\u0442\u044b \u0438 \u0441\u0434\u0435\u043b\u043a\u0438"
        st.session_state.expanded_task_key = None
        st.rerun()
with nc2:
    if st.button("\u041f\u043b\u0430\u043d\u0438\u0440\u043e\u0432\u0449\u0438\u043a", use_container_width=True, type="primary" if st.session_state.active_tab == "\u041f\u043b\u0430\u043d\u0438\u0440\u043e\u0432\u0449\u0438\u043a" else "secondary"):
        st.session_state.active_tab = "\u041f\u043b\u0430\u043d\u0438\u0440\u043e\u0432\u0449\u0438\u043a"
        st.session_state.expanded_task_key = None
        st.rerun()
with nc3:
with nc3:
    if st.button("\u0412\u043d\u0443\u0442\u0440\u0435\u043d\u043d\u0438\u0435 \u0437\u0430\u0434\u0430\u0447\u0438", use_container_width=True, type="primary" if st.session_state.active_tab == "\u0412\u043d\u0443\u0442\u0440\u0435\u043d\u043d\u0438\u0435 \u0437\u0430\u0434\u0430\u0447\u0438" else "secondary"):
        st.session_state.active_tab = "\u0412\u043d\u0443\u0442\u0440\u0435\u043d\u043d\u0438\u0435 \u0437\u0430\u0434\u0430\u0447\u0438"
        st.session_state.expanded_task_key = None
        st.rerun()
with nc4:
    if st.button("\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0438", use_container_width=True, type="primary" if st.session_state.active_tab == "\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0438" else "secondary"):
        st.session_state.active_tab = "\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0438"
        st.session_state.expanded_task_key = None
        st.rerun()

st.markdown("---")

cu = st.session_state.user_name

if st.session_state.active_tab == "\u041f\u043b\u0430\u043d\u0438\u0440\u043e\u0432\u0449\u0438\u043a":
    render_centered_title("\u041f\u043b\u0430\u043d\u0438\u0440\u043e\u0432\u0449\u0438\u043a")
    render_centered_button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443", key="new_task", btn_type="primary")
    if st.session_state.get("show_new_task_form", False):
        with st.container(border=True):
            tc, dc = st.columns(2)
            with tc:
                nt_client = st.selectbox("\u041a\u043b\u0438\u0435\u043d\u0442:", [""] + [c["name"] for c in st.session_state.crm_store["clients"]], index=0, key="nt_client", placeholder="\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043a\u043b\u0438\u0435\u043d\u0442\u0430")
            with dc:
                deals_for_select = [d for d in st.session_state.crm_store.get("deals", []) if d.get("status") not in ["\u0421\u0434\u0435\u043b\u043a\u0430 \u0437\u0430\u043a\u0440\u044b\u0442\u0430"]]
                nt_deal = st.selectbox("\u0421\u0434\u0435\u043b\u043a\u0430:", [""] + [f"{d.get('deal_number', '')} \u2014 {d.get('title', '')}" for d in deals_for_select], index=0, key="nt_deal", placeholder="\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0441\u0434\u0435\u043b\u043a\u0443")
            nt_topic = st.text_input("\u0422\u0435\u043c\u0430 \u0437\u0430\u0434\u0430\u0447\u0438:", key="nt_topic")
            nt_type = st.selectbox("\u0422\u0438\u043f:", TASK_TYPES, index=0, key="nt_type")
            nt_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", [""] + get_managers_list(), index=0, key="nt_mgr", placeholder=MGR_PLACEHOLDER)
            nt_dl = st.date_input("\u0421\u0440\u043e\u043a:", format="DD/MM/YYYY", key="nt_dl")
            nt_comment = st.text_area("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438:", key="nt_comment")
            if nt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b"):
                nt_products = st.text_area("\u0422\u043e\u0432\u0430\u0440\u044b:", key="nt_products")
                nt_addr = st.text_area("\u0410\u0434\u0440\u0435\u0441 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438:", key="nt_addr")
                nt_recv = st.text_input("\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:", key="nt_recv")
                nt_rphone = st.text_input("\u0422\u0435\u043b\u0435\u0444\u043e\u043d \u043f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044f:", key="nt_rphone")
                nt_pay = st.selectbox("\u041e\u043f\u043b\u0430\u0442\u0430:", SHIP_PAY_OPTIONS, index=0, key="nt_pay", placeholder="\u0423\u043a\u0430\u0436\u0438 \u043f\u043b\u0430\u0442\u0435\u043b\u044c\u0449\u0438\u043a\u0430")
                nt_amount = st.text_input("\u0421\u0443\u043c\u043c\u0430 \u0437\u0430\u043a\u0430\u0437\u0430 (\u0440\u0443\u0431.):", key="nt_amount", placeholder="\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u0443\u043c\u043c\u0443")
                nt_tk = st.text_input("\u0422\u0440\u0435\u043a:", key="nt_tk")
            if st.button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443", key="create_task_btn", use_container_width=True, type="primary"):
                if not nt_client: st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043a\u043b\u0438\u0435\u043d\u0442\u0430")
                elif not nt_topic.strip(): st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0442\u0435\u043c\u0443 \u0437\u0430\u0434\u0430\u0447\u0438")
                elif not nt_mgr: st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0433\u043e")
                else:
                    cl = None
                    for c in st.session_state.crm_store["clients"]:
                        if c["name"] == nt_client: cl = c; break
                    if cl:
                        deal_id = None
                        if nt_deal:
                            for d in deals_for_select:
                                if f"{d.get('deal_number', '')} \u2014 {d.get('title', '')}" == nt_deal: deal_id = d["id"]; break
                        prefix = "\u0417\u0421" if deal_id else "\u0417\u041a"
                        new_task = {"id": str(uuid.uuid4())[:8], "text": nt_topic.strip(), "type": nt_type, "manager": nt_mgr, "deadline": nt_dl.isoformat(), "task_comment": nt_comment.strip(), "done": False, "created_at": now_str(), "last_modified": now_str(), "deal_id": deal_id, "task_number": generate_task_number(prefix), "task_files": [], "completion_files": [], "task_comments": [], "in_work": False, "ready_to_ship": False, "delegated_to": None, "flagged": False, "products": nt_products if nt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "ship_addr": nt_addr if nt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "receiver": nt_recv if nt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "receiver_phone": nt_rphone if nt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "ship_pay": nt_pay if nt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "tk_num": nt_tk if nt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "order_amount": int(nt_amount) if nt_amount and nt_amount.strip().isdigit() else 0}
                        cl.setdefault("tasks", []).append(new_task)
                        cl["last_modified"] = now_str()
                        if deal_id:
                            for d in st.session_state.crm_store.get("deals", []):
                                if d["id"] == deal_id: d["last_modified"] = now_str(); break
                        st.session_state.show_new_task_form = False
                        commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0441\u043e\u0437\u0434\u0430\u043d\u0430")
    all_tasks = []
    for c in st.session_state.crm_store["clients"]:
        for t in c.get("tasks", []):
            all_tasks.append((t, c, t.get("deal_id")))
    active_tasks = [(t, c, d_id) for t, c, d_id in all_tasks if not t.get("done")]
    done_tasks = [(t, c, d_id) for t, c, d_id in all_tasks if t.get("done")]
    active_tasks.sort(key=lambda x: (is_task_overdue(x[0]), get_task_sort_date(x[0])))
    done_tasks.sort(key=lambda x: get_task_sort_date(x[0]), reverse=True)
    filter_col, mgr_col = st.columns(2)
    with filter_col:
        pf = st.selectbox("\u0424\u0438\u043b\u044c\u0442\u0440:", ["\u0412\u0441\u0435", "\u041c\u043e\u0438", "\u041e\u0442 \u043c\u0435\u043d\u044f", "\u041f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043d\u044b\u0435", "\u0412 \u0440\u0430\u0431\u043e\u0442\u0435"], key="planner_filter")
    with mgr_col:
        all_mgrs = sorted(set(t.get("manager", "") for _, t in [(x[0], x[0]) for x in active_tasks] if t.get("manager")))
        mgr_filter = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", ["\u0412\u0441\u0435"] + all_mgrs, key="planner_mgr_filter")
    def apply_plan_filter(tasks_list):
        result = []
        for t, c, d_id in tasks_list:
            if pf == "\u041c\u043e\u0438" and t.get("manager") != cu: continue
            if pf == "\u041e\u0442 \u043c\u0435\u043d\u044f" and t.get("created_by", t.get("manager", "")) != cu: continue
            if pf == "\u041f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043d\u044b\u0435" and not is_task_overdue(t): continue
            if pf == "\u0412 \u0440\u0430\u0431\u043e\u0442\u0435" and not t.get("in_work"): continue
            if mgr_filter != "\u0412\u0441\u0435" and t.get("manager") != mgr_filter: continue
            result.append((t, c, d_id))
        return result
    filtered_active = apply_plan_filter(active_tasks)
    filtered_done = apply_plan_filter(done_tasks)
    if not st.session_state.get("show_new_task_form", False):
        render_centered_button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443", key="new_task2", btn_type="primary")
    if st.session_state.get("show_new_task_form", False):
        with st.container(border=True):
            tc, dc = st.columns(2)
            with tc:
                nt_client = st.selectbox("\u041a\u043b\u0438\u0435\u043d\u0442:", [""] + [c["name"] for c in st.session_state.crm_store["clients"]], index=0, key="nt_client2", placeholder="\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043a\u043b\u0438\u0435\u043d\u0442\u0430")
            with dc:
                deals_for_select = [d for d in st.session_state.crm_store.get("deals", []) if d.get("status") not in ["\u0421\u0434\u0435\u043b\u043a\u0430 \u0437\u0430\u043a\u0440\u044b\u0442\u0430"]]
                nt_deal = st.selectbox("\u0421\u0434\u0435\u043b\u043a\u0430:", [""] + [f"{d.get('deal_number', '')} \u2014 {d.get('title', '')}" for d in deals_for_select], index=0, key="nt_deal2", placeholder="\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0441\u0434\u0435\u043b\u043a\u0443")
            nt_topic = st.text_input("\u0422\u0435\u043c\u0430 \u0437\u0430\u0434\u0430\u0447\u0438:", key="nt_topic2")
            nt_type = st.selectbox("\u0422\u0438\u043f:", TASK_TYPES, index=0, key="nt_type2")
            nt_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", [""] + get_managers_list(), index=0, key="nt_mgr2", placeholder=MGR_PLACEHOLDER)
            nt_dl = st.date_input("\u0421\u0440\u043e\u043a:", format="DD/MM/YYYY", key="nt_dl2")
            nt_comment = st.text_area("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438:", key="nt_comment2")
            if nt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b"):
                nt_products = st.text_area("\u0422\u043e\u0432\u0430\u0440\u044b:", key="nt_products2")
                nt_addr = st.text_area("\u0410\u0434\u0440\u0435\u0441 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438:", key="nt_addr2")
                nt_recv = st.text_input("\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:", key="nt_recv2")
                nt_rphone = st.text_input("\u0422\u0435\u043b\u0435\u0444\u043e\u043d \u043f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044f:", key="nt_rphone2")
                nt_pay = st.selectbox("\u041e\u043f\u043b\u0430\u0442\u0430:", SHIP_PAY_OPTIONS, index=0, key="nt_pay2", placeholder="\u0423\u043a\u0430\u0436\u0438 \u043f\u043b\u0430\u0442\u0435\u043b\u044c\u0449\u0438\u043a\u0430")
                nt_amount = st.text_input("\u0421\u0443\u043c\u043c\u0430 \u0437\u0430\u043a\u0430\u0437\u0430 (\u0440\u0443\u0431.):", key="nt_amount2", placeholder="\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u0443\u043c\u043c\u0443")
                nt_tk = st.text_input("\u0422\u0440\u0435\u043a:", key="nt_tk2")
            if st.button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443", key="create_task_btn2", use_container_width=True, type="primary"):
                if not nt_client: st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043a\u043b\u0438\u0435\u043d\u0442\u0430")
                elif not nt_topic.strip(): st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0442\u0435\u043c\u0443 \u0437\u0430\u0434\u0430\u0447\u0438")
                elif not nt_mgr: st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0433\u043e")
                else:
                    cl = None
                    for c in st.session_state.crm_store["clients"]:
                        if c["name"] == nt_client: cl = c; break
                    if cl:
                        deal_id = None
                        if nt_deal:
                            for d in deals_for_select:
                                if f"{d.get('deal_number', '')} \u2014 {d.get('title', '')}" == nt_deal: deal_id = d["id"]; break
                        prefix = "\u0417\u0421" if deal_id else "\u0417\u041a"
                        new_task = {"id": str(uuid.uuid4())[:8], "text": nt_topic.strip(), "type": nt_type, "manager": nt_mgr, "deadline": nt_dl.isoformat(), "task_comment": nt_comment.strip(), "done": False, "created_at": now_str(), "last_modified": now_str(), "deal_id": deal_id, "task_number": generate_task_number(prefix), "task_files": [], "completion_files": [], "task_comments": [], "in_work": False, "ready_to_ship": False, "delegated_to": None, "flagged": False, "products": nt_products if nt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "ship_addr": nt_addr if nt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "receiver": nt_recv if nt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "receiver_phone": nt_rphone if nt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "ship_pay": nt_pay if nt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "tk_num": nt_tk if nt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "order_amount": int(nt_amount) if nt_amount and nt_amount.strip().isdigit() else 0}
                        cl.setdefault("tasks", []).append(new_task)
                        cl["last_modified"] = now_str()
                        if deal_id:
                            for d in st.session_state.crm_store.get("deals", []):
                                if d["id"] == deal_id: d["last_modified"] = now_str(); break
                        st.session_state.show_new_task_form = False
                        commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0441\u043e\u0437\u0434\u0430\u043d\u0430")
    if st.session_state.get("show_new_task_form", False) and not st.session_state.get("_task_form_shown"):
        st.session_state._task_form_shown = True
    render_centered_title("\u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0435 \u0437\u0430\u0434\u0430\u0447\u0438")
    for task, cl, d_id in filtered_active:
        task_key = f"plan_{task['id']}"
        key_prefix = f"plan_{task['id']}"
        render_task_row(task, cl, get_deal_by_id(d_id) if d_id else None, task_key, key_prefix)
    if filtered_done:
        with st.expander(f"\u0410\u0440\u0445\u0438\u0432 \u0437\u0430\u0434\u0430\u0447 ({len(filtered_done)})", expanded=False):
            for task, cl, d_id in filtered_done:
                task_key = f"done_{task['id']}"
                key_prefix = f"done_{task['id']}"
                render_task_row(task, cl, get_deal_by_id(d_id) if d_id else None, task_key, key_prefix)

elif st.session_state.active_tab == "\u041a\u043b\u0438\u0435\u043d\u0442\u044b \u0438 \u0441\u0434\u0435\u043b\u043a\u0438":
    render_centered_title("\u041a\u043b\u0438\u0435\u043d\u0442\u044b \u0438 \u0441\u0434\u0435\u043b\u043a\u0438")
    col_search, col_cat, col_mgr, col_btn = st.columns([3, 2, 2, 1])
    with col_search:
        search = st.text_input("\u041f\u043e\u0438\u0441\u043a:", key="client_search", placeholder="\u0418\u043c\u044f, \u0442\u0435\u043b\u0435\u0444\u043e\u043d, email...", label_visibility="collapsed")
    with col_cat:
        cat_filter = st.selectbox("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:", ["\u0412\u0441\u0435"] + CATEGORIES, key="cat_filter", label_visibility="collapsed")
    with col_mgr:
        mgr_list = ["\u0412\u0441\u0435"] + get_managers_list()
        mgr_f = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", mgr_list, key="mgr_filter", label_visibility="collapsed")
    with col_btn:
        if st.button("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c", key="add_client_btn", use_container_width=True, type="primary"):
            st.session_state.show_client_form = not st.session_state.get("show_client_form", False)
            st.session_state.client_form_version += 1
            st.rerun()
    if st.session_state.get("show_client_form", False):
        with st.container(border=True):
            st.markdown("### \u041d\u043e\u0432\u044b\u0439 \u043a\u043b\u0438\u0435\u043d\u0442")
            cl1, cl2 = st.columns(2)
            with cl1:
                n_name = st.text_input("\u0424\u0418\u041e:", key=f"new_name_{st.session_state.client_form_version}")
                n_phone = st.text_input("\u0422\u0435\u043b\u0435\u0444\u043e\u043d:", key=f"new_phone_{st.session_state.client_form_version}")
                n_email = st.text_input("Email:", key=f"new_email_{st.session_state.client_form_version}")
                n_addr = st.text_input("\u0410\u0434\u0440\u0435\u0441:", key=f"new_addr_{st.session_state.client_form_version}")
            with cl2:
                n_cat = st.selectbox("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:", CATEGORIES, key=f"new_cat_{st.session_state.client_form_version}")
                n_disc = st.number_input("\u0421\u043a\u0438\u0434\u043a\u0430 %:", min_value=0, max_value=100, value=0, step=1, key=f"new_disc_{st.session_state.client_form_version}")
                n_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", [""] + get_managers_list(), key=f"new_mgr_{st.session_state.client_form_version}", placeholder=MGR_PLACEHOLDER)
                n_comment = st.text_input("\u0411\u0430\u0437\u043e\u0432\u044b\u0439 \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:", key=f"new_comment_{st.session_state.client_form_version}")
            n_files = st.file_uploader("\u0424\u0430\u0439\u043b\u044b \u043a\u043b\u0438\u0435\u043d\u0442\u0430:", key=f"new_files_{st.session_state.client_form_version}", accept_multiple_files=True)
            if st.button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c", key="create_client_btn", use_container_width=True, type="primary"):
                if n_name.strip():
                    cid = str(uuid.uuid4())[:8]
                    new_client = {"id": cid, "name": n_name.strip(), "phone": format_phone(n_phone), "email": n_email.strip(), "address": n_addr.strip(), "category": n_cat, "discount": int(n_disc), "manager": n_mgr, "base_comment": n_comment.strip(), "extra_phones": [], "extra_emails": [], "extra_addresses": [], "client_files": normalize_file_list(save_uploaded_files(n_files, cid, "client_file")) if n_files else [], "client_comments": [], "comments": [], "tasks": [], "last_modified": now_str(), "created_at": now_str(), "client_chat": []}
                    st.session_state.crm_store["clients"].append(new_client)
                    st.session_state.show_client_form = False
                    commit_and_rerun(st.session_state.crm_store, "\u041a\u043b\u0438\u0435\u043d\u0442 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d")
                else: st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0438\u043c\u044f")
    clients = st.session_state.crm_store["clients"]
    filtered = []
    for c in clients:
        if search:
            s = search.lower()
            if s not in c["name"].lower() and s not in c.get("phone", "").lower() and s not in c.get("email", "").lower() and s not in c.get("address", "").lower(): continue
        if cat_filter != "\u0412\u0441\u0435" and c.get("category", "\u041d\u0435 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0451\u043d") != cat_filter: continue
        if mgr_f != "\u0412\u0441\u0435" and c.get("manager", "") != mgr_f: continue
        filtered.append(c)
    filtered.sort(key=get_sort_key, reverse=True)
    for c in filtered:
        client_id = c["id"]
        is_exp = st.session_state.expanded_client_id == client_id
        client_deals = [d for d in st.session_state.crm_store.get("deals", []) if d.get("client_id") == client_id]
        active_deals = [d for d in client_deals if d.get("status") != "\u0421\u0434\u0435\u043b\u043a\u0430 \u0437\u0430\u043a\u0440\u044b\u0442\u0430"]
        closed_deals = [d for d in client_deals if d.get("status") == "\u0421\u0434\u0435\u043b\u043a\u0430 \u0437\u0430\u043a\u0440\u044b\u0442\u0430"]
        bg, bc = get_entity_border(c.get("tasks", []))
        client_label = f"{c['name']} \u2014 {c.get('phone', '')}"
        if c.get("category") and c["category"] != "\u041d\u0435 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0451\u043d": client_label += f" | {c['category']}"
        if c.get("discount", 0) > 0: client_label += f" | -{c['discount']}%"
        if active_deals: client_label += f" | \u0421\u0434\u0435\u043b\u043e\u043a: {len(active_deals)}"
        if c.get("manager"): client_label += f" | {c['manager']}"
        st.markdown(f"<style>.st-key-cl_wrap_{client_id} button {{ background-color: {bg} !important; color: #2C3E50 !important; border: 2px solid {bc} !important; border-radius: 10px !important; }}</style>", unsafe_allow_html=True)
        with st.container(key=f"cl_wrap_{client_id}"):
            if st.button(client_label, key=f"cl_btn_{client_id}", use_container_width=True, type="primary" if is_exp else "secondary"):
                if is_exp:
                    st.session_state.expanded_client_id = None
                    save_scroll_and_rerun()
                else:
                    st.session_state.expanded_client_id = client_id
                    st.rerun()
            if not is_exp:
                render_scroll_restore(f"cl_{client_id}")
        if is_exp:
            with st.container(border=True):
                st.markdown(format_created_date(c), unsafe_allow_html=True)
                render_phone_inline(c.get("phone", ""), client_id)
                cl_info1, cl_info2, cl_info3 = st.columns(3)
                with cl_info1:
                    if c.get("email"): st.markdown(f"**Email:** {c['email']}")
                    if c.get("address"): st.markdown(f"**\u0410\u0434\u0440\u0435\u0441:** {c['address']}")
                with cl_info2:
                    st.markdown(f"**\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:** {c.get('category', '\u2014')}")
                    if c.get("discount", 0) > 0: st.markdown(f"**\u0421\u043a\u0438\u0434\u043a\u0430:** {c['discount']}%")
                with cl_info3:
                    st.markdown(f"**\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:** {c.get('manager', '\u2014')}")
                    if c.get("base_comment"): st.markdown(f"**\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:** {c['base_comment']}")
                if c.get("extra_phones"):
                    st.markdown("**\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u044b:**")
                    for i, ep in enumerate(c["extra_phones"]):
                        render_extra_phone_inline(ep.get("phone", ""), ep.get("name", ""), ep.get("role", ""), f"{client_id}_ep_{i}")
                if c.get("extra_emails"):
                    st.markdown("**\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 email:**")
                    for i, ee in enumerate(c["extra_emails"]):
                        st.markdown(f"- {ee}")
                if c.get("extra_addresses"):
                    st.markdown("**\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0430\u0434\u0440\u0435\u0441\u0430:**")
                    for i, ea in enumerate(c.get("extra_addresses", [])):
                        if isinstance(ea, dict):
                            st.markdown(f"- {ea.get('address', '')} ({ea.get('resp_name', '')} {ea.get('resp_role', '')})")
                        else:
                            st.markdown(f"- {ea}")
                if c.get("client_files"):
                    st.markdown("**\u0424\u0430\u0439\u043b\u044b \u043a\u043b\u0438\u0435\u043d\u0442\u0430:**")
                    render_file_thumbs(c["client_files"], f"cl_{client_id}", allow_delete=True)
                st.markdown("---")
                show_edit = st.session_state.get(f"show_edit_{client_id}", False)
                if st.button("\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c" if not show_edit else "\u0421\u043a\u0440\u044b\u0442\u044c", key=f"edit_btn_{client_id}", use_container_width=True):
                    st.session_state[f"show_edit_{client_id}"] = not show_edit
                    st.rerun()
                if show_edit:
                    with st.container(border=True):
                        el1, el2 = st.columns(2)
                        with el1:
                            e_name = st.text_input("\u0424\u0418\u041e:", value=c["name"], key=f"e_name_{client_id}")
                            e_phone = st.text_input("\u0422\u0435\u043b\u0435\u0444\u043e\u043d:", value=c.get("phone", ""), key=f"e_phone_{client_id}")
                            e_email = st.text_input("Email:", value=c.get("email", ""), key=f"e_email_{client_id}")
                            e_addr = st.text_input("\u0410\u0434\u0440\u0435\u0441:", value=c.get("address", ""), key=f"e_addr_{client_id}")
                        with el2:
                            e_cat = st.selectbox("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f:", CATEGORIES, index=CATEGORIES.index(c.get("category", "\u041d\u0435 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0451\u043d")) if c.get("category", "\u041d\u0435 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0451\u043d") in CATEGORIES else 0, key=f"e_cat_{client_id}")
                            e_disc = st.number_input("\u0421\u043a\u0438\u0434\u043a\u0430 %:", min_value=0, max_value=100, value=c.get("discount", 0), step=1, key=f"e_disc_{client_id}")
                            e_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", [""] + get_managers_list(), index=0 if c.get("manager", "") not in get_managers_list() else ([""] + get_managers_list()).index(c.get("manager", "")), key=f"e_mgr_{client_id}", placeholder=MGR_PLACEHOLDER)
                            e_comment = st.text_input("\u0411\u0430\u0437\u043e\u0432\u044b\u0439 \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:", value=c.get("base_comment", ""), key=f"e_comment_{client_id}")
                        st.markdown("**\u0414\u043e\u043f. \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u044b:**")
                        for i in range(len(c.get("extra_phones", []))):
                            ep_l, ep_r = st.columns([3, 1])
                            with ep_l:
                                c["extra_phones"][i]["phone"] = st.text_input(f"\u0422\u0435\u043b\u0435\u0444\u043e\u043d {i+1}:", value=c["extra_phones"][i].get("phone", ""), key=f"ep_{client_id}_{i}")
                                c["extra_phones"][i]["name"] = st.text_input(f"\u0418\u043c\u044f {i+1}:", value=c["extra_phones"][i].get("name", ""), key=f"epn_{client_id}_{i}")
                                c["extra_phones"][i]["role"] = st.text_input(f"\u0414\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u044c {i+1}:", value=c["extra_phones"][i].get("role", ""), key=f"epr_{client_id}_{i}")
                            with ep_r:
                                st.write("")
                                if st.button("X", key=f"del_ep_{client_id}_{i}"):
                                    c["extra_phones"].pop(i)
                                    st.rerun()
                        if st.button("+ \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0442\u0435\u043b\u0435\u0444\u043e\u043d", key=f"add_ep_{client_id}", use_container_width=True):
                            c.setdefault("extra_phones", []).append({"phone": "", "name": "", "role": ""})
                            st.rerun()
                        st.markdown("**\u0414\u043e\u043f. email:**")
                        for i in range(len(c.get("extra_emails", []))):
                            ee_l, ee_r = st.columns([3, 1])
                            with ee_l:
                                c["extra_emails"][i] = st.text_input(f"Email {i+1}:", value=c["extra_emails"][i], key=f"ee_{client_id}_{i}")
                            with ee_r:
                                st.write("")
                                if st.button("X", key=f"del_ee_{client_id}_{i}"):
                                    c["extra_emails"].pop(i)
                                    st.rerun()
                        if st.button("+ \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c email", key=f"add_ee_{client_id}", use_container_width=True):
                            c.setdefault("extra_emails", []).append("")
                            st.rerun()
                        st.markdown("**\u0414\u043e\u043f. \u0430\u0434\u0440\u0435\u0441\u0430:**")
                        for i in range(len(c.get("extra_addresses", []))):
                            ea = c["extra_addresses"][i] if isinstance(c["extra_addresses"][i], dict) else {"address": c["extra_addresses"][i], "resp_name": "", "resp_role": "", "resp_phone": "", "resp_email": ""}
                            ea_l, ea_r = st.columns([3, 1])
                            with ea_l:
                                ea["address"] = st.text_input(f"\u0410\u0434\u0440\u0435\u0441 {i+1}:", value=ea.get("address", ""), key=f"ea_{client_id}_{i}")
                                ea["resp_name"] = st.text_input(f"\u041e\u0442\u0432. \u043b\u0438\u0446\u043e {i+1}:", value=ea.get("resp_name", ""), key=f"ean_{client_id}_{i}")
                                ea["resp_role"] = st.text_input(f"\u0414\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u044c {i+1}:", value=ea.get("resp_role", ""), key=f"ear_{client_id}_{i}")
                            with ea_r:
                                st.write("")
                                if st.button("X", key=f"del_ea_{client_id}_{i}"):
                                    c["extra_addresses"].pop(i)
                                    st.rerun()
                            c["extra_addresses"][i] = ea
                        if st.button("+ \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0430\u0434\u0440\u0435\u0441", key=f"add_ea_{client_id}", use_container_width=True):
                            c.setdefault("extra_addresses", []).append({"address": "", "resp_name": "", "resp_role": "", "resp_phone": "", "resp_email": ""})
                            st.rerun()
                        ncf = st.file_uploader("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0444\u0430\u0439\u043b\u044b:", key=f"ncf_{client_id}", accept_multiple_files=True)
                        if st.button("\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c", key=f"upl_cl_{client_id}", use_container_width=True):
                            if ncf:
                                fi_list = save_uploaded_files(ncf, client_id, "client_file")
                                c.setdefault("client_files", []).extend(normalize_file_list(fi_list))
                                c["last_modified"] = now_str()
                                commit_and_rerun(st.session_state.crm_store, "\u0424\u0430\u0439\u043b\u044b \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u044b")
                            else: st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0444\u0430\u0439\u043b(\u044b)")
                        if st.button("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", key=f"save_cl_{client_id}", use_container_width=True, type="primary"):
                            c["name"] = e_name.strip()
                            c["phone"] = format_phone(e_phone)
                            c["email"] = e_email.strip()
                            c["address"] = e_addr.strip()
                            c["category"] = e_cat
                            c["discount"] = int(e_disc)
                            c["manager"] = e_mgr
                            c["base_comment"] = e_comment.strip()
                            c["last_modified"] = now_str()
                            st.session_state[f"show_edit_{client_id}"] = False
                            commit_and_rerun(st.session_state.crm_store, "\u041a\u043b\u0438\u0435\u043d\u0442 \u043e\u0431\u043d\u043e\u0432\u043b\u0451\u043d")
                st.markdown("---")
                render_entity_chat(c, "client", client_id)
                st.markdown("---")
                if active_deals:
                    st.markdown(f"#### \u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0435 \u0441\u0434\u0435\u043b\u043a\u0438 ({len(active_deals)})")
                    for d in sorted(active_deals, key=get_sort_key, reverse=True):
                        deal_id = d["id"]
                        is_d_exp = st.session_state.expanded_deal_id == deal_id
                        d_bg, d_bc = get_entity_border([t for t in c.get("tasks", []) if t.get("deal_id") == deal_id])
                        deal_label = f"{d.get('deal_number', '')} \u2014 {d.get('title', '')}"
                        if d.get("status"): deal_label += f" | {d['status']}"
                        if d.get("manager"): deal_label += f" | {d['manager']}"
                        st.markdown(f"<style>.st-key-dl_wrap_{deal_id} button {{ background-color: {d_bg} !important; color: #2C3E50 !important; border: 2px solid {d_bc} !important; border-radius: 10px !important; }}</style>", unsafe_allow_html=True)
                        with st.container(key=f"dl_wrap_{deal_id}"):
                            if st.button(deal_label, key=f"dl_btn_{deal_id}", use_container_width=True, type="primary" if is_d_exp else "secondary"):
                                if is_d_exp:
                                    st.session_state.expanded_deal_id = None
                                    save_scroll_and_rerun()
                                else:
                                    st.session_state.expanded_deal_id = deal_id
                                    st.rerun()
                            if not is_d_exp:
                                render_scroll_restore(f"dl_{deal_id}")
                        if is_d_exp:
                            with st.container(border=True):
                                st.markdown(format_created_date(d), unsafe_allow_html=True)
                                st.markdown(f"**\u0421\u0442\u0430\u0442\u0443\u0441:** {d.get('status', '\u041d\u043e\u0432\u044b\u0439')}")
                                st.markdown(f"**\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:** {d.get('manager', '\u2014')}")
                                if d.get("deal_title"): st.markdown(f"**\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a:** {d['deal_title']}")
                                if d.get("deal_comments"):
                                    st.markdown("**\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438 \u0441\u0434\u0435\u043b\u043a\u0438:**")
                                    for dc in d["deal_comments"]:
                                        st.markdown(f"- *{dc.get('time', '')}*: {dc.get('text', '')}")
                                st.markdown("---")
                                ps_wrap_key = f"ps_wrap_{deal_id}"
                                with st.container(key=ps_wrap_key):
                                    cur_ps = d.get("payment_status", "\u041d\u0435 \u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043e")
                                    inject_payment_container_css(deal_id, cur_ps)
                                    st.markdown(f"**\u0421\u0442\u0430\u0442\u0443\u0441 \u043e\u043f\u043b\u0430\u0442\u044b:**")
                                    new_ps = st.selectbox("\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043e/\u041d\u0435 \u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043e:", ["\u041d\u0435 \u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043e", "\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043e"], index=0 if cur_ps == "\u041d\u0435 \u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043e" else 1, key=f"ps_{deal_id}", label_visibility="collapsed")
                                    if new_ps != cur_ps:
                                        d["payment_status"] = new_ps
                                        d["last_modified"] = now_str()
                                        commit_and_rerun(st.session_state.crm_store, "\u0421\u0442\u0430\u0442\u0443\u0441 \u043e\u043f\u043b\u0430\u0442\u044b \u043e\u0431\u043d\u043e\u0432\u043b\u0451\u043d")
                                st.markdown("---")
                                show_deal_edit = st.session_state.get(f"show_deal_edit_{deal_id}", False)
                                if st.button("\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0441\u0434\u0435\u043b\u043a\u0443" if not show_deal_edit else "\u0421\u043a\u0440\u044b\u0442\u044c", key=f"de_btn_{deal_id}", use_container_width=True):
                                    st.session_state[f"show_deal_edit_{deal_id}"] = not show_deal_edit
                                    st.rerun()
                                if show_deal_edit:
                                    with st.container(border=True):
                                        e_status = st.selectbox("\u0421\u0442\u0430\u0442\u0443\u0441:", ["\u041d\u043e\u0432\u044b\u0439", "\u0412 \u0440\u0430\u0431\u043e\u0442\u0435", "\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435", "\u041e\u0442\u0433\u0440\u0443\u0436\u0435\u043d", "\u0414\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d", "\u0421\u0434\u0435\u043b\u043a\u0430 \u0437\u0430\u043a\u0440\u044b\u0442\u0430"], index=["\u041d\u043e\u0432\u044b\u0439", "\u0412 \u0440\u0430\u0431\u043e\u0442\u0435", "\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435", "\u041e\u0442\u0433\u0440\u0443\u0436\u0435\u043d", "\u0414\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d", "\u0421\u0434\u0435\u043b\u043a\u0430 \u0437\u0430\u043a\u0440\u044b\u0442\u0430"].index(d.get("status", "\u041d\u043e\u0432\u044b\u0439")) if d.get("status", "\u041d\u043e\u0432\u044b\u0439") in ["\u041d\u043e\u0432\u044b\u0439", "\u0412 \u0440\u0430\u0431\u043e\u0442\u0435", "\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435", "\u041e\u0442\u0433\u0440\u0443\u0436\u0435\u043d", "\u0414\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d", "\u0421\u0434\u0435\u043b\u043a\u0430 \u0437\u0430\u043a\u0440\u044b\u0442\u0430"] else 0, key=f"e_st_{deal_id}")
                                        e_title = st.text_input("\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a:", value=d.get("deal_title", ""), key=f"e_dt_{deal_id}")
                                        e_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", [""] + get_managers_list(), index=0 if d.get("manager", "") not in get_managers_list() else ([""] + get_managers_list()).index(d.get("manager", "")), key=f"e_dm_{deal_id}", placeholder=MGR_PLACEHOLDER)
                                        e_dc = st.text_area("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439 \u043a \u0441\u0434\u0435\u043b\u043a\u0435:", value="", key=f"e_dc_{deal_id}")
                                        if st.button("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", key=f"save_d_{deal_id}", use_container_width=True, type="primary"):
                                            d["status"] = e_status
                                            d["deal_title"] = e_title.strip()
                                            d["manager"] = e_mgr
                                            if e_dc.strip():
                                                d.setdefault("deal_comments", []).append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": e_dc.strip(), "user": cu})
                                            d["last_modified"] = now_str()
                                            st.session_state[f"show_deal_edit_{deal_id}"] = False
                                            commit_and_rerun(st.session_state.crm_store, "\u0421\u0434\u0435\u043b\u043a\u0430 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0430")
                                st.markdown("---")
                                st.markdown("**\u0424\u0430\u0439\u043b\u044b \u0441\u0434\u0435\u043b\u043a\u0438:**")
                                render_file_thumbs(d.get("deal_files", []), f"dl_{deal_id}", allow_delete=True)
                                df_ver = st.session_state.deal_file_uploader_ver.get(deal_id, 0)
                                df_key = f"df_{deal_id}_{df_ver}"
                                new_df = st.file_uploader("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0444\u0430\u0439\u043b\u044b:", key=df_key, accept_multiple_files=True)
                                if st.button("\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c", key=f"upl_df_{deal_id}", use_container_width=True):
                                    if new_df:
                                        fi_list = save_uploaded_files(new_df, d["client_id"], "deal_file")
                                        d.setdefault("deal_files", []).extend(normalize_file_list(fi_list))
                                        d["last_modified"] = now_str()
                                        st.session_state.deal_file_uploader_ver[deal_id] = df_ver + 1
                                        commit_and_rerun(st.session_state.crm_store, "\u0424\u0430\u0439\u043b\u044b \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u044b")
                                    else: st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0444\u0430\u0439\u043b(\u044b)")
                                st.markdown("---")
                                render_entity_chat(d, "deal", deal_id)
                                st.markdown("---")
                                deal_tasks = [t for t in c.get("tasks", []) if t.get("deal_id") == deal_id]
                                if deal_tasks:
                                    st.markdown(f"**\u0417\u0430\u0434\u0430\u0447\u0438 \u0441\u0434\u0435\u043b\u043a\u0438 ({len(deal_tasks)}):**")
                                    for t in sorted(deal_tasks, key=lambda x: (x.get("done", False), x.get("deadline", ""))):
                                        task_key = f"deal_{t['id']}"
                                        key_prefix = f"deal_{t['id']}"
                                        render_task_row(t, c, d, task_key, key_prefix)
                                add_task_col, _ = st.columns([1, 3])
                                with add_task_col:
                                    if st.button("+ \u0417\u0430\u0434\u0430\u0447\u0443 \u0432 \u0441\u0434\u0435\u043b\u043a\u0443", key=f"add_dt_{deal_id}", use_container_width=True):
                                        st.session_state[f"show_new_dt_{deal_id}"] = not st.session_state.get(f"show_new_dt_{deal_id}", False)
                                        st.rerun()
                                if st.session_state.get(f"show_new_dt_{deal_id}", False):
                                    with st.container(border=True):
                                        dt_topic = st.text_input("\u0422\u0435\u043c\u0430:", key=f"dt_t_{deal_id}")
                                        dt_type = st.selectbox("\u0422\u0438\u043f:", TASK_TYPES, index=0, key=f"dt_ty_{deal_id}")
                                        dt_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", [""] + get_managers_list(), index=0, key=f"dt_m_{deal_id}", placeholder=MGR_PLACEHOLDER)
                                        dt_dl = st.date_input("\u0421\u0440\u043e\u043a:", format="DD/MM/YYYY", key=f"dt_d_{deal_id}")
                                        dt_comment = st.text_area("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438:", key=f"dt_c_{deal_id}")
                                        if dt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b"):
                                            dt_products = st.text_area("\u0422\u043e\u0432\u0430\u0440\u044b:", key=f"dt_p_{deal_id}")
                                            dt_addr = st.text_area("\u0410\u0434\u0440\u0435\u0441:", key=f"dt_a_{deal_id}")
                                            dt_recv = st.text_input("\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:", key=f"dt_r_{deal_id}")
                                            dt_rphone = st.text_input("\u0422\u0435\u043b\u0435\u0444\u043e\u043d \u043f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044f:", key=f"dt_rp_{deal_id}")
                                            dt_pay = st.selectbox("\u041e\u043f\u043b\u0430\u0442\u0430:", SHIP_PAY_OPTIONS, index=0, key=f"dt_pay_{deal_id}", placeholder="\u0423\u043a\u0430\u0436\u0438 \u043f\u043b\u0430\u0442\u0435\u043b\u044c\u0449\u0438\u043a\u0430")
                                            dt_amount = st.text_input("\u0421\u0443\u043c\u043c\u0430 (\u0440\u0443\u0431.):", key=f"dt_am_{deal_id}", placeholder="\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u0443\u043c\u043c\u0443")
                                            dt_tk = st.text_input("\u0422\u0440\u0435\u043a:", key=f"dt_tk_{deal_id}")
                                        if st.button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c", key=f"go_dt_{deal_id}", use_container_width=True, type="primary"):
                                            if not dt_topic.strip(): st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0442\u0435\u043c\u0443")
                                            elif not dt_mgr: st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0433\u043e")
                                            else:
                                                new_t = {"id": str(uuid.uuid4())[:8], "text": dt_topic.strip(), "type": dt_type, "manager": dt_mgr, "deadline": dt_dl.isoformat(), "task_comment": dt_comment.strip(), "done": False, "created_at": now_str(), "last_modified": now_str(), "deal_id": deal_id, "task_number": generate_task_number("\u0417\u0421"), "task_files": [], "completion_files": [], "task_comments": [], "in_work": False, "ready_to_ship": False, "delegated_to": None, "flagged": False, "products": dt_products if dt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "ship_addr": dt_addr if dt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "receiver": dt_recv if dt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "receiver_phone": dt_rphone if dt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "ship_pay": dt_pay if dt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "tk_num": dt_tk if dt_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b") else "", "order_amount": int(dt_amount) if dt_amount and dt_amount.strip().isdigit() else 0}
                                                c.setdefault("tasks", []).append(new_t)
                                                c["last_modified"] = now_str()
                                                d["last_modified"] = now_str()
                                                st.session_state[f"show_new_dt_{deal_id}"] = False
                                                commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u0430 \u0432 \u0441\u0434\u0435\u043b\u043a\u0443")
                                st.markdown("---")
                                if d.get("status") != "\u0421\u0434\u0435\u043b\u043a\u0430 \u0437\u0430\u043a\u0440\u044b\u0442\u0430":
                                    if st.button("\u0417\u0430\u0432\u0435\u0440\u0448\u0438\u0442\u044c \u0441\u0434\u0435\u043b\u043a\u0443", key=f"close_d_{deal_id}", use_container_width=True, type="primary"):
                                        close_deal_dialog(deal_id)
                                else:
                                    st.markdown(f"**\u0414\u0430\u0442\u0430 \u0437\u0430\u043a\u0440\u044b\u0442\u0438\u044f:** {d.get('closed_date', '')}")
                                    if d.get("close_report"): st.caption(f"\u041e\u0442\u0447\u0451\u0442: {d['close_report']}")
                                    if d.get("close_files"):
                                        st.markdown("**\u0424\u0430\u0439\u043b\u044b \u0437\u0430\u043a\u0440\u044b\u0442\u0438\u044f:**")
                                        render_file_thumbs(d["close_files"], f"cl_d_{deal_id}")
                                st.markdown("---")
                                if st.session_state.user_role == "admin":
                                    if st.button("\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0441\u0434\u0435\u043b\u043a\u0443", key=f"del_d_{deal_id}", use_container_width=True):
                                        st.session_state.crm_store["deals"] = [x for x in st.session_state.crm_store.get("deals", []) if x["id"] != deal_id]
                                        c["tasks"] = [t for t in c.get("tasks", []) if t.get("deal_id") != deal_id]
                                        c["last_modified"] = now_str()
                                        commit_and_rerun(st.session_state.crm_store, "\u0421\u0434\u0435\u043b\u043a\u0430 \u0443\u0434\u0430\u043b\u0435\u043d\u0430")
                if closed_deals:
                    with st.expander(f"\u0417\u0430\u043a\u0440\u044b\u0442\u044b\u0435 \u0441\u0434\u0435\u043b\u043a\u0438 ({len(closed_deals)})", expanded=False):
                        for d in sorted(closed_deals, key=get_sort_key, reverse=True):
                            st.markdown(f"- {d.get('deal_number', '')} \u2014 {d.get('title', '')} | \u0417\u0430\u043a\u0440\u044b\u0442\u0430 {d.get('closed_date', '')}")
                st.markdown("---")
                if st.session_state.user_role == "admin":
                    add_deal_col, _ = st.columns([1, 3])
                    with add_deal_col:
                        if st.button("+ \u0421\u0434\u0435\u043b\u043a\u0443", key=f"add_d_{client_id}", use_container_width=True):
                            st.session_state[f"show_new_d_{client_id}"] = not st.session_state.get(f"show_new_d_{client_id}", False)
                            st.rerun()
                    if st.session_state.get(f"show_new_d_{client_id}", False):
                        with st.container(border=True):
                            nd_title = st.text_input("\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a \u0441\u0434\u0435\u043b\u043a\u0438:", key=f"nd_t_{client_id}")
                            nd_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", [""] + get_managers_list(), index=0, key=f"nd_m_{client_id}", placeholder=MGR_PLACEHOLDER)
                            nd_status = st.selectbox("\u0421\u0442\u0430\u0442\u0443\u0441:", ["\u041d\u043e\u0432\u044b\u0439", "\u0412 \u0440\u0430\u0431\u043e\u0442\u0435", "\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435", "\u041e\u0442\u0433\u0440\u0443\u0436\u0435\u043d", "\u0414\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d"], index=0, key=f"nd_s_{client_id}")
                            if st.button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c", key=f"go_nd_{client_id}", use_container_width=True, type="primary"):
                                if nd_title.strip():
                                    new_deal = {"id": str(uuid.uuid4())[:8], "client_id": client_id, "title": nd_title.strip(), "deal_title": nd_title.strip(), "status": nd_status, "manager": nd_mgr, "deal_number": generate_deal_number(), "deal_comments": [], "deal_files": [], "close_files": [], "payment_status": "\u041d\u0435 \u043e\u043f\u043b\u0430\u0447\u0435\u043d\u043e", "last_modified": now_str(), "created_at": now_str(), "deal_chat": []}
                                    st.session_state.crm_store.setdefault("deals", []).append(new_deal)
                                    st.session_state[f"show_new_d_{client_id}"] = False
                                    commit_and_rerun(st.session_state.crm_store, "\u0421\u0434\u0435\u043b\u043a\u0430 \u0441\u043e\u0437\u0434\u0430\u043d\u0430")
                                else: st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a")
                st.markdown("---")
                if st.session_state.user_role == "admin":
                    if st.button("\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043a\u043b\u0438\u0435\u043d\u0442\u0430", key=f"del_c_{client_id}", use_container_width=True):
                        st.session_state.crm_store["clients"] = [x for x in st.session_state.crm_store["clients"] if x["id"] != client_id]
                        st.session_state.crm_store["deals"] = [d for d in st.session_state.crm_store.get("deals", []) if d.get("client_id") != client_id]
                        commit_and_rerun(st.session_state.crm_store, "\u041a\u043b\u0438\u0435\u043d\u0442 \u0443\u0434\u0430\u043b\u0451\u043d")
    if not filtered: st.caption("\u041a\u043b\u0438\u0435\u043d\u0442\u043e\u0432 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e")
elif st.session_state.active_tab == "Внутренние задачи":
    sub1, sub2, sub3 = st.tabs(["Задачи сотрудникам", "Чат", "Шпаргалка"])
    with sub1:
        all_users = [u.get("name", u["login"]) for u in st.session_state.crm_store.get("users", []) if u.get("role") != "admin"]
        col_a, col_b = st.columns([3, 1])
        with col_a: itf = st.selectbox("Фильтр:", ["Мне", "От меня", "Все"], key="itf_filter")
        with col_b:
            st.write("")
            if st.button("Новая задача", use_container_width=True, type="primary"):
                st.session_state.show_new_itask = not st.session_state.get("show_new_itask", False)
                st.rerun()
        if st.session_state.get("show_new_itask", False):
            with st.container(border=True):
                it_title = st.text_input("Заголовок:", key="it_title")
                it_desc = st.text_area("Описание:", key="it_desc")
                it_to = st.selectbox("Кому:", [""] + all_users, index=0, key="it_to", placeholder="Выбери исполнителя")
                it_dl = st.date_input("Срок:", format="DD/MM/YYYY", key="it_dl")
                it_pri = st.selectbox("Приоритет:", ["Обычный", "Срочный"], key="it_pri")
                if st.button("Создать задачу", key="it_create", use_container_width=True, type="primary"):
                    if it_title.strip() and it_to:
                        st.session_state.crm_store.setdefault("internal_tasks", []).append({"id": str(uuid.uuid4())[:8], "title": it_title.strip(), "description": it_desc.strip(), "assigned_to": it_to, "created_by": cu, "deadline": it_dl.isoformat(), "priority": it_pri, "done": False, "created_at": now_str()})
                        st.session_state.show_new_itask = False
                        commit_and_rerun(st.session_state.crm_store, "Задача создана")
                    else:
                        if not it_title.strip(): st.warning("Введите заголовок")
                        if not it_to: st.warning("Выберите исполнителя")
        itasks = st.session_state.crm_store.get("internal_tasks", [])
        filtered_it = []
        for t in itasks:
            if itf == "Мне":
                if t.get("assigned_to") == cu: filtered_it.append(t)
            elif itf == "От меня":
                if t.get("created_by") == cu: filtered_it.append(t)
            else: filtered_it.append(t)
        filtered_it.sort(key=lambda x: (x.get("done", False), x.get("deadline", "")))
        for t in filtered_it:
            pri_color = "#C62828" if t.get("priority") == "Срочный" else "#2C3E50"
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
            it_label = f"{t['title']} — {t.get('assigned_to', '')} | {format_date(t.get('deadline', ''))}"
            if it_overdue and not t.get("done"): it_label += " | Просрочено"
            it_selected = is_it_exp
            it_border = "#2196F3" if it_selected else it_bc
            it_shadow = "box-shadow: 0 0 0 2px rgba(33,150,243,0.3);" if it_selected else ""
            st.markdown(f"<style>.st-key-itask_wrap_{t['id']} button {{ background-color: {it_bg} !important; color: #2C3E50 !important; border: 2px solid {it_border} !important; border-radius: 10px !important; {it_shadow} }}</style>", unsafe_allow_html=True)
            with st.container(key=f"itask_wrap_{t['id']}"):
                if st.button(it_label, key=f"itask_btn_{t['id']}", use_container_width=True, type="primary" if is_it_exp else "secondary"):
                    if is_it_exp:
                        save_scroll_and_rerun()
                    else:
                        st.session_state.expanded_task_key = itask_key
                        st.rerun()
                if not is_it_exp:
                    render_scroll_restore(f"it_{t['id']}")
            if is_it_exp:
                with st.container(border=True):
                    st.markdown(f"**От:** {t.get('created_by', '')} → **Кому:** {t.get('assigned_to', '')}")
                    st.markdown(format_created_date(t), unsafe_allow_html=True)
                    st.markdown(f"**Срок:** {format_date(t.get('deadline', ''))} | **Приоритет:** <span style='color:{pri_color};font-weight:600'>{t.get('priority', '')}</span>", unsafe_allow_html=True)
                    if t.get("description"): st.markdown(f"**Описание:** {t['description']}")
                    st.markdown(f"**Создано:** {t.get('created_at', '')}")
                    show_it_edit = st.session_state.get(f"show_it_edit_{t['id']}", False)
                    if st.button("Редактировать" if not show_it_edit else "Скрыть", key=f"it_edit_{t['id']}", use_container_width=True):
                        st.session_state[f"show_it_edit_{t['id']}"] = not show_it_edit
                        st.rerun()
                    if show_it_edit:
                        with st.container(border=True):
                            et_title = st.text_input("Заголовок:", value=t.get("title", ""), key=f"it_et_{t['id']}")
                            et_desc = st.text_area("Описание:", value=t.get("description", ""), key=f"it_ed_{t['id']}")
                            et_to = st.selectbox("Кому:", [""] + all_users, index=0 if t.get("assigned_to", "") not in all_users else ([""] + all_users).index(t.get("assigned_to", "")), key=f"it_eto_{t['id']}", placeholder="Выбери исполнителя")
                            et_dl = st.date_input("Срок:", value=parse_deadline(t.get("deadline", "")), format="DD/MM/YYYY", key=f"it_edl_{t['id']}")
                            et_pri = st.selectbox("Приоритет:", ["Обычный", "Срочный"], index=0 if t.get("priority", "") == "Обычный" else 1, key=f"it_epri_{t['id']}")
                            if st.button("Сохранить", key=f"it_esave_{t['id']}", use_container_width=True, type="primary"):
                                if et_to:
                                    t["title"] = et_title
                                    t["description"] = et_desc
                                    t["assigned_to"] = et_to
                                    t["deadline"] = et_dl.isoformat()
                                    t["priority"] = et_pri
                                    st.session_state[f"show_it_edit_{t['id']}"] = False
                                    commit_and_rerun(st.session_state.crm_store, "Задача обновлена")
                                else: st.warning("Выберите исполнителя")
                    st.markdown("---")
                    if not t.get("done"):
                        show_it_complete = f"show_it_complete_{t['id']}"
                        if st.button("Выполнить", key=f"it_done_{t['id']}", use_container_width=True, type="primary"):
                            st.session_state[show_it_complete] = not st.session_state.get(show_it_complete, False)
                            st.rerun()
                        if st.session_state.get(show_it_complete, False):
                            it_rt = st.text_input("Отчёт (обязательно):", key=f"it_rt_{t['id']}")
                            it_uf = st.file_uploader("Файлы отчёта:", key=f"it_uf_{t['id']}", accept_multiple_files=True)
                            it_cn = st.checkbox("Создать новую задачу", key=f"it_cn_{t['id']}")
                            it_ne, it_ntd, it_ntitle, it_nto = {}, None, None, None
                            if it_cn:
                                it_ntitle = st.text_input("Тема новой задачи:", key=f"it_nt_title_{t['id']}")
                                it_nto = st.selectbox("Кому:", [""] + all_users, index=0, key=f"it_nt_to_{t['id']}", placeholder="Выбери исполнителя")
                                it_ntd = st.date_input("Срок:", format="DD/MM/YYYY", key=f"it_nt_dl_{t['id']}")
                                it_ne["description"] = st.text_area("Описание:", key=f"it_nt_desc_{t['id']}")
                                it_ne["priority"] = st.selectbox("Приоритет:", ["Обычный", "Срочный"], key=f"it_nt_pri_{t['id']}")
                            if st.button("Подтвердить", key=f"it_confirm_{t['id']}", use_container_width=True, type="primary"):
                                if not it_rt.strip(): st.warning("Введите отчёт")
                                elif it_cn and (not it_ntitle or not it_ntitle.strip()): st.warning("Введите тему новой задачи")
                                elif it_cn and not it_nto: st.warning("Выберите исполнителя для новой задачи")
                                else:
                                    t["done"] = True
                                    t["done_at"] = now_str()
                                    t["completion_report"] = it_rt.strip()
                                    if it_uf:
                                        fi_list = save_uploaded_files(it_uf, 0, "itask_report")
                                        t["completion_files"] = normalize_file_list(fi_list)
                                    if it_cn and it_ntitle:
                                        new_it = {"id": str(uuid.uuid4())[:8], "title": it_ntitle.strip(), "description": it_ne.get("description", ""), "assigned_to": it_nto, "created_by": cu, "deadline": it_ntd.isoformat(), "priority": it_ne.get("priority", "Обычный"), "done": False, "created_at": now_str()}
                                        st.session_state.crm_store.setdefault("internal_tasks", []).append(new_it)
                                    st.session_state[show_it_complete] = False
                                    commit_and_rerun(st.session_state.crm_store, "Задача выполнена")
                    else:
                        st.caption(f"Выполнена: {t.get('done_at', '')}")
                        if t.get("completion_report"): st.caption(f"Отчёт: {t['completion_report']}")
                        if t.get("completion_files"):
                            st.markdown("**Файлы отчёта:**")
                            render_file_thumbs(t["completion_files"], f"itask_cf_{t['id']}")
                        if st.button("Вернуть в работу", key=f"it_reopen_{t['id']}", use_container_width=True):
                            t["done"] = False
                            t.pop("done_at", None)
                            t.pop("completion_report", None)
                            t.pop("completion_files", None)
                            commit_and_rerun(st.session_state.crm_store, "Задача возвращена")
                    if t.get("created_by") == cu or st.session_state.user_role == "admin":
                        st.markdown("---")
                        if st.button("Удалить", key=f"it_del_{t['id']}", use_container_width=True):
                            st.session_state.crm_store["internal_tasks"] = [x for x in itasks if x["id"] != t["id"]]
                            commit_and_rerun(st.session_state.crm_store, "Задача удалена")
        if not filtered_it: st.caption("Нет задач")
    with sub2:
        chat = st.session_state.crm_store.get("chat_messages", [])
        chat_container = st.container(height=400)
        with chat_container:
            for msg in chat[-100:]:
                is_me = msg.get("user") == cu
                cls = "chat-msg-me" if is_me else "chat-msg-other"
                st.markdown(f'<div class="chat-msg {cls}"><div style="font-size:0.75rem;opacity:0.7;margin-bottom:2px;">{msg.get("user","")} — {msg.get("time","")}</div>{msg.get("text","")}</div>', unsafe_allow_html=True)
            if not chat: st.caption("Сообщений пока нет")
        chat_clr = st.session_state.get("chat_clr")
        if chat_clr:
            st.session_state["chat_input"] = ""
            st.session_state["chat_clr"] = False
        msg_text = st.text_input("Сообщение:", key="chat_input", placeholder="Введите сообщение...")
        if st.button("Отправить", key="chat_send", use_container_width=True, type="primary"):
            if msg_text.strip():
                st.session_state.crm_store.setdefault("chat_messages", []).append({"id": str(uuid.uuid4())[:8], "user": cu, "text": msg_text.strip(), "time": datetime.now().strftime("%d.%m.%Y %H:%M")})
                st.session_state["chat_clr"] = True
                commit_and_rerun(st.session_state.crm_store)
            else: st.warning("Введите текст")
    with sub3:
        qa_entries = st.session_state.crm_store.get("qa_entries", [])
        qa_search = st.text_input("Поиск по шпаргалке:", key="qa_search", placeholder="Введите вопрос или ключевое слово...").strip().lower()
        with st.expander("Добавить запись", expanded=False):
            qa_q = st.text_input("Вопрос:", key="qa_q")
            qa_a = st.text_area("Ответ:", key="qa_a")
            qa_cat = st.text_input("Категория:", key="qa_cat", placeholder="Напр: Доставка, Оплата, Продукция...")
            if st.button("Добавить", key="qa_add", use_container_width=True, type="primary"):
                if qa_q.strip() and qa_a.strip():
                    st.session_state.crm_store.setdefault("qa_entries", []).append({"id": str(uuid.uuid4())[:8], "question": qa_q.strip(), "answer": qa_a.strip(), "category": qa_cat.strip() or "Общее", "created_by": cu, "created_at": datetime.now().strftime("%Y-%m-%d")})
                    commit_and_rerun(st.session_state.crm_store, "Запись добавлена")
                else: st.warning("Заполните вопрос и ответ")
        filtered_qa = []
        for qa in qa_entries:
            if qa_search:
                ct = f"{qa.get('question', '')} {qa.get('answer', '')} {qa.get('category', '')}".lower()
                if qa_search not in ct: continue
            filtered_qa.append(qa)
        qa_cats = sorted(set(qa.get("category", "Общее") for qa in filtered_qa))
        for cat in qa_cats:
            st.markdown(f"**{cat}**")
            for qa in [q for q in filtered_qa if q.get("category", "Общее") == cat]:
                with st.container(border=True):
                    st.markdown(f"<div class='qa-card'><b>Q: {qa.get('question', '')}</b><br><br>{qa.get('answer', '')}</div>", unsafe_allow_html=True)
                    qa_copy_btn_id = f"qa_copy_{qa['id']}"
                    render_copy_button(qa.get('answer', ''), qa_copy_btn_id, "📋 Копировать")
                    show_qa_edit = st.session_state.get(f"show_qa_edit_{qa['id']}", False)
                    if st.button("Редактировать" if not show_qa_edit else "Скрыть", key=f"qa_edit_{qa['id']}"):
                        st.session_state[f"show_qa_edit_{qa['id']}"] = not show_qa_edit
                        st.rerun()
                    if show_qa_edit:
                        with st.container(border=True):
                            eq_q = st.text_input("Вопрос:", value=qa.get("question", ""), key=f"qa_eq_{qa['id']}")
                            eq_a = st.text_area("Ответ:", value=qa.get("answer", ""), key=f"qa_ea_{qa['id']}")
                            eq_cat = st.text_input("Категория:", value=qa.get("category", ""), key=f"qa_ec_{qa['id']}")
                            if st.button("Сохранить", key=f"qa_es_{qa['id']}", use_container_width=True, type="primary"):
                                qa["question"] = eq_q.strip()
                                qa["answer"] = eq_a.strip()
                                qa["category"] = eq_cat.strip() or "Общее"
                                st.session_state[f"show_qa_edit_{qa['id']}"] = False
                                commit_and_rerun(st.session_state.crm_store, "Запись обновлена")
                    if st.button("Удалить", key=f"qa_del_{qa['id']}", use_container_width=True):
                        st.session_state.crm_store["qa_entries"] = [x for x in qa_entries if x["id"] != qa["id"]]
                        commit_and_rerun(st.session_state.crm_store, "Запись удалена")
        if not filtered_qa: st.caption("Записей не найдено")

elif st.session_state.active_tab == "Поставщики":
    st.markdown("### Поставщики")
    suppliers = st.session_state.crm_store.get("suppliers", [])
    with st.expander("Добавить поставщика", expanded=False):
        sl, sr = st.columns(2)
        with sl:
            sn = st.text_input("Название:", key="sup_name")
            sp = st.text_input("Контактное лицо:", key="sup_person")
            sph = st.text_input("Телефон:", key="sup_phone")
        with sr:
            se = st.text_input("Email:", key="sup_email")
            sa = st.text_input("Адрес:", key="sup_address")
            sc = st.text_input("Категория товара:", key="sup_category")
        snote = st.text_area("Комментарий:", key="sup_note")
        if st.button("Создать", key="sup_add_btn", use_container_width=True, type="primary"):
            if sn.strip():
                sid = (max([s.get("id", 0) for s in suppliers]) if suppliers else 0) + 1
                st.session_state.crm_store.setdefault("suppliers", []).append({"id": sid, "name": sn.strip(), "person": sp.strip(), "phone": format_phone(sph), "email": se.strip(), "address": sa.strip(), "category": sc.strip(), "note": snote.strip(), "created_at": now_str(), "last_modified": now_str()})
                commit_and_rerun(st.session_state.crm_store, "Поставщик добавлен")
            else: st.warning("Введите название")
    if suppliers:
        for s in sorted(suppliers, key=lambda x: x.get("last_modified", ""), reverse=True):
            with st.expander(f"{s['name']} — {s.get('phone', '')} | {s.get('category', '')}"):
                st.markdown(format_created_date(s), unsafe_allow_html=True)
                cl1, cl2 = st.columns(2)
                with cl1:
                    st.markdown(f"**Контакт:** {s.get('person', '—')}")
                    st.markdown(f"**Телефон:** {s.get('phone', '—')}")
                    st.markdown(f"**Email:** {s.get('email', '—')}")
                with cl2:
                    st.markdown(f"**Адрес:** {s.get('address', '—')}")
                    st.markdown(f"**Категория:** {s.get('category', '—')}")
                    if s.get("note"): st.markdown(f"**Комментарий:** {s['note']}")
                show_sup_edit = st.session_state.get(f"show_sup_edit_{s['id']}", False)
                if st.button("Редактировать" if not show_sup_edit else "Скрыть", key=f"sup_edit_{s['id']}", use_container_width=True):
                    st.session_state[f"show_sup_edit_{s['id']}"] = not show_sup_edit
                    st.rerun()
                if show_sup_edit:
                    with st.container(border=True):
                        en = st.text_input("Название:", value=s["name"], key=f"sup_en_{s['id']}")
                        ep = st.text_input("Контакт:", value=s.get("person", ""), key=f"sup_ep_{s['id']}")
                        eph = st.text_input("Телефон:", value=s.get("phone", ""), key=f"sup_eph_{s['id']}")
                        ee = st.text_input("Email:", value=s.get("email", ""), key=f"sup_ee_{s['id']}")
                        ea = st.text_input("Адрес:", value=s.get("address", ""), key=f"sup_ea_{s['id']}")
                        ec = st.text_input("Категория:", value=s.get("category", ""), key=f"sup_ec_{s['id']}")
                        enote = st.text_area("Комментарий:", value=s.get("note", ""), key=f"sup_enote_{s['id']}")
                        if st.button("Сохранить", key=f"sup_save_{s['id']}", use_container_width=True, type="primary"):
                            s["name"], s["person"], s["phone"], s["email"], s["address"], s["category"], s["note"] = en, ep, format_phone(eph), ee, ea, ec, enote
                            s["last_modified"] = now_str()
                            st.session_state[f"show_sup_edit_{s['id']}"] = False
                            commit_and_rerun(st.session_state.crm_store, "Поставщик обновлён")
                if st.session_state.user_role == "admin":
                    st.markdown("---")
                    if st.button("Удалить", key=f"sup_del_{s['id']}", use_container_width=True):
                        st.session_state.crm_store["suppliers"] = [x for x in suppliers if x["id"] != s["id"]]
                        commit_and_rerun(st.session_state.crm_store, "Поставщик удалён")
    else:
        st.info("База поставщиков пуста. Добавьте первого поставщика.")
