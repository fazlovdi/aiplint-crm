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
    #sticky-tab-label { position: fixed; top: 12px; right: 16px; z-index: 99999; background: rgba(245,246,248,0.92); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); border: 1px solid rgba(220,224,229,0.6); border-radius: 9px; padding: 6px 12px; font-size: 0.85rem; font-weight: 600; color: #2C3E50; box-shadow: 0 4px 12px rgba(0,0,0,0.06); display: none; pointer-events: none; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    #sticky-tab-label.visible { display: block !important; }
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
    .arrow-btn-col button { font-size: 1.6rem !important; font-weight: bold !important; padding: 0.05rem 0.25rem !important; min-height: 36px !important; color: #bc1661 !important; background-color: transparent !important; border: none !important; transition: all 0.15s ease !important; line-height: 1 !important; }
    .arrow-btn-col button:hover { color: #9a1452 !important; background-color: #FCE4EC !important; border-radius: 8px !important; }
    .created-date { font-size: 0.72rem; color: #95A5B7; font-style: italic; }
    .ready-badge { display: inline-block; background: #2E7D32; color: white; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 99px; margin-left: 6px; text-transform: uppercase; letter-spacing: 0.04em; }
    .in-work-badge { display: inline-block; background: #bc1661; color: white; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 99px; margin-left: 6px; text-transform: uppercase; letter-spacing: 0.04em; }
    .delegated-badge { display: inline-block; background: #E65100; color: white; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 99px; margin-left: 6px; text-transform: uppercase; letter-spacing: 0.04em; }
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
})();
</script>
""", height=0)

FILE_NAME = "web_crm_database_v2.json"
YANDEX_API_URL = "https://cloud-api.yandex.net/v1/disk/resources"
MAX_URL = "https://max.ru"
MAX_NUMBER = "+79003293300"
CATEGORIES = ["\u041d\u0435 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0451\u043d", "\u0414\u0438\u0437\u0430\u0439\u043d\u0435\u0440", "\u0421\u0442\u0440\u043e\u0438\u0442\u0435\u043b\u044c", "\u0414\u0438\u043b\u0435\u0440", "\u041f\u043e\u043a\u0443\u043f\u0430\u0442\u0435\u043b\u044c"]

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

def find_user_by_login(login):
    for u in st.session_state.crm_store.get("users", []):
        if u["login"] == login: return u
    return None

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

def render_phone_inline(phone, uid):
    cph = re.sub(r"\D", "", phone)
    if cph.startswith("8") and len(cph) == 11: cph = "7" + cph[1:]
    elif not cph: cph = "79990000000"
    btn_id = f"ph_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f'<div class="phone-action-group" style="padding:4px 0;"><span style="font-size:1rem;font-weight:600;color:#2C3E50;">{phone}</span><button onclick="navigator.clipboard.writeText(\'{phone}\').then(function(){{var b=document.getElementById(\'{btn_id}\');b.textContent=\'\u2713\';setTimeout(function(){{b.textContent=\'\U0001F4CB\';}},1500);}});" class="phone-btn" id="{btn_id}" title="\u0421\u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c">\U0001F4CB</button><a href="tel:+{cph}" class="phone-btn" title="\u041f\u043e\u0437\u0432\u043e\u043d\u0438\u0442\u044c">\U0001F4DE</a></div>', unsafe_allow_html=True)

def render_extra_phone_inline(phone, name, role, uid):
    cph = re.sub(r"\D", "", phone)
    if cph.startswith("8") and len(cph) == 11: cph = "7" + cph[1:]
    elif not cph: cph = "79990000000"
    info = f"{phone} \u2014 {name} ({role})" if name else phone
    btn_id = f"ep_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f'<div class="phone-action-group" style="padding:4px 0;flex-wrap:wrap;gap:8px;white-space:normal;"><span style="font-size:0.9rem;color:#3C4A5A;flex:1 1 auto;min-width:0;word-break:break-word;">{info}</span><button onclick="navigator.clipboard.writeText(\'{phone}\').then(function(){{var b=document.getElementById(\'{btn_id}\');b.textContent=\'\u2713\';setTimeout(function(){{b.textContent=\'\U0001F4CB\';}},1500);}});" class="phone-btn" id="{btn_id}" title="\u0421\u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c">\U0001F4CB</button><a href="tel:+{cph}" class="phone-btn" title="\u041f\u043e\u0437\u0432\u043e\u043d\u0438\u0442\u044c">\U0001F4DE</a></div>', unsafe_allow_html=True)

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
            if ext == ".pdf": st.download_button(f"\U0001F4C4 {fn}", data=fb, file_name=fn, mime="application/pdf", key=f"dl_{prefix}_o_{i}")
            else: st.download_button(f"\U0001F4C4 {fn}", data=fb, file_name=fn, key=f"dl_{prefix}_o_{i}")
            if allow_delete and st.session_state.user_role == "admin":
                if st.button("\U0001F5D1 \u0423\u0434\u0430\u043b\u0438\u0442\u044c", key=f"del_{prefix}_o_{i}"):
                    files.pop(len(img_files) + i)
                    commit_and_rerun(st.session_state.crm_store, "\u0424\u0430\u0439\u043b \u0443\u0434\u0430\u043b\u0451\u043d")

def render_deal_files_in_task(deal, task_key_prefix):
    if not deal or not deal.get("deal_files"): return
    st.markdown("**\u0424\u0430\u0439\u043b\u044b \u0441\u0434\u0435\u043b\u043a\u0438:**")
    render_file_thumbs(deal["deal_files"], f"{task_key_prefix}_dealfile")

def build_print_html(task, cl, tp, fd):
    def esc(s): return str(s if s else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    products_html = esc(task.get('products', '')).replace('\n', '<br>')
    oav = task.get('order_amount', 0)
    cost_html = f"<div style='margin-top:6px;font-size:16px;font-weight:bold;'>\u0421\u0443\u043c\u043c\u0430: {oav:,.0f} \u0440\u0443\u0431.</div>".replace(",", " ") if oav and oav > 0 else ""
    file_reminder = "<div style='color:#D65757;font-weight:bold;margin:14px 0;border:2px solid #D65757;padding:8px;border-radius:8px;'>&#9888; \u041d\u0435 \u0437\u0430\u0431\u0443\u0434\u044c \u0440\u0430\u0441\u043f\u0435\u0447\u0430\u0442\u0430\u0442\u044c \u0432\u043b\u043e\u0436\u0435\u043d\u043d\u044b\u0435 \u0444\u0430\u0439\u043b\u044b!</div>" if task.get("task_files") else ""
    lb = get_logo_base64()
    logo_html = f"<img src='data:image/png;base64,{lb}' width='180' style='float:left;margin-right:20px;'/>" if lb else "<div style='font-size:24px;font-weight:bold;float:left;margin-right:20px;'>\u0410\u0419\u041f\u041b\u0418\u041d\u0422</div>"
    task_type_label = {"\u041e\u0442\u043f\u0440\u0430\u0432\u043a\u0430": "\u041e\u0442\u043f\u0440\u0430\u0432\u043a\u0430 \u0437\u0430\u043a\u0430\u0437\u0430", "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f": "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b": "\u041e\u0442\u043f\u0440\u0430\u0432\u043a\u0430 \u043e\u0431\u0440\u0430\u0437\u0446\u043e\u0432"}.get(tp, tp)
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><title>\u0411\u043b\u0430\u043d\u043a \u0437\u0430\u0434\u0430\u0447\u0438</title><style>body {{ font-family: Arial, sans-serif; margin: 40px; color: #222; }} .header {{ text-align: center; border-bottom: 2px solid #333; padding: 10px; }} .row {{ margin: 8px 0; }} hr {{ border: none; border-top: 1px solid #ccc; margin: 14px 0; }} .sig {{ margin-top: 30px; }} .sig p {{ margin: 12px 0; }}</style></head><body><div>{logo_html}</div><div class="header"><h2>\u0411\u041b\u0410\u041d\u041a \u0417\u0410\u0414\u0410\u0427\u0418</h2><p>{datetime.now().strftime('%d/%m/%Y')}</p></div><div class="row"><b>\u0417\u0430\u0434\u0430\u0447\u0430:</b> \u2116{esc(task.get('task_number', ''))}</div><div class="row"><b>\u041a\u043b\u0438\u0435\u043d\u0442:</b> {esc(cl['name'])} ({esc(cl['phone'])})</div><div class="row"><b>\u0422\u0438\u043f:</b> {esc(task_type_label)}</div><div class="row"><b>\u0422\u0435\u043c\u0430:</b> {esc(task.get('text', ''))}</div><div class="row"><b>\u0421\u0440\u043e\u043a:</b> {esc(fd)}</div><div class="row"><b>\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:</b> {esc(task.get('manager', ''))}</div><hr><div class="row"><b>\u0422\u043e\u0432\u0430\u0440\u044b:</b><br>{products_html}</div><div class="row"><b>\u0410\u0434\u0440\u0435\u0441:</b> {esc(task.get('ship_addr', ''))}</div><div class="row"><b>\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:</b> {esc(task.get('receiver', ''))} ({esc(task.get('receiver_phone', ''))})</div><div class="row"><b>\u041e\u043f\u043b\u0430\u0442\u0430:</b> {esc(task.get('ship_pay', ''))}</div><div class="row"><b>\u0422\u0440\u0435\u043a:</b> {esc(task.get('tk_num', ''))}</div>{cost_html}{file_reminder}<div class="sig"><p>\u041e\u0442\u043f\u0443\u0441\u0442\u0438\u043b: _____________</p><p>\u041f\u043e\u043b\u0443\u0447\u0438\u043b: _____________</p></div></body></html>"""

def render_print_button(task, cl, tp, fd, key_suffix):
    html_content = build_print_html(task, cl, tp, fd)
    html_json = json.dumps(html_content).replace('<', '\\u003c')
    safe_key = key_suffix.replace('-', '_').replace('.', '_')
    btn_id = f"print_btn_{safe_key}"
    st.markdown(f'<button class="custom-print-btn" id="{btn_id}">\u0420\u0430\u0441\u043f\u0435\u0447\u0430\u0442\u0430\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443</button>', unsafe_allow_html=True)
    st.components.v1.html(f"""<script>(function() {{ var btn = window.parent.document.getElementById('{btn_id}'); if (!btn) return; var html = {html_json}; btn.addEventListener('click', function() {{ var w = window.open('', '_blank'); if (!w) {{ alert('\u0420\u0430\u0437\u0440\u0435\u0448\u0438\u0442\u0435 \u0432\u0441\u043f\u043b\u044b\u0432\u0430\u044e\u0449\u0438\u0435 \u043e\u043a\u043d\u0430'); return; }} w.document.open(); w.document.write(html); w.document.close(); w.focus(); setTimeout(function() {{ try {{ w.print(); }} catch(e) {{}} }}, 500); w.onafterprint = function() {{ setTimeout(function() {{ w.close(); }}, 300); }}; }}); }})();</script>""", height=0)

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
        if t.get('tk_num'): st.markdown(f"**\u0422\u0440\u0435\u043a:** `{t['tk_num']}`")
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
                st.markdown(f"- *{tc.get('time', '')}*: {tc.get('text', '')}")
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
            st.markdown("---")
            tc1, tc2, tc3 = st.columns(3)
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
            with tc3:
                if t.get('type') in ('\u041e\u0442\u043f\u0440\u0430\u0432\u043a\u0430', '\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b'):
                    ready_label = "\u0413\u043e\u0442\u043e\u0432\u043e \u2705" if t.get('ready_to_ship') else "\u041e\u0442\u043c\u0435\u0442\u0438\u0442\u044c \u0433\u043e\u0442\u043e\u0432\u043d\u043e\u0441\u0442\u044c"
                    if st.button(ready_label, key=f"btn_ready_{key_prefix}", use_container_width=True):
                        t["ready_to_ship"] = not t.get("ready_to_ship", False)
                        t["last_modified"] = now_str()
                        commit_and_rerun(st.session_state.crm_store, "\u0421\u0442\u0430\u0442\u0443\u0441 \u043e\u0442\u043f\u0440\u0430\u0432\u043a\u0438 \u043e\u0431\u043d\u043e\u0432\u043b\u0451\u043d")
            if st.session_state.get(f"show_delegate_{key_prefix}", False):
                with st.container(border=True):
                    dlg_to = st.selectbox("\u0414\u0435\u043b\u0435\u0433\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043d\u0430:", [""] + mgrs, index=0, key=f"dlg_to_{key_prefix}")
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
    if t.get('in_work') and not tk_done:
        tk_label += ' | \u0412 \u0440\u0430\u0431\u043e\u0442\u0435'
    if t.get('ready_to_ship') and not tk_done:
        tk_label += ' | \u0413\u043e\u0442\u043e\u0432\u043e \u043a \u043e\u0442\u043f\u0440\u0430\u0432\u043a\u0435'
    st.markdown(f"<style>.st-key-tk_btn_wrap_{task_key} button {{ background-color: {tk_bg} !important; color: #2C3E50 !important; border: 2px solid {tk_bc} !important; border-radius: 10px !important; }}</style>", unsafe_allow_html=True)
    with st.container(key=f"tk_btn_wrap_{task_key}"):
        if st.button(tk_label, key=f"tk_card_{task_key}", use_container_width=True, type="primary" if is_tk_exp else "secondary"):
            st.session_state.expanded_task_key = None if is_tk_exp else task_key
            st.rerun()
    if is_tk_exp: render_task_detail(t, cl, d, key_prefix)

def get_entity_border(tasks_list):
    has_overdue = any(not t.get("done") and is_task_overdue(t) for t in tasks_list)
    has_active = any(not t.get("done") for t in tasks_list)
    if has_overdue: return "#FFEBEE", "#C62828"
    elif has_active: return "#E8F5E9", "#4CAF50"
    else: return "#FFFFFF", "#DCE0E5"

def tree_col(level):
    indents = {1: 0.02, 2: 0.035, 3: 0.055}
    indent = indents.get(level, 0)
    if indent == 0: return st.container()
    cols = st.columns([indent, 1 - indent], gap="small")
    return cols[1]

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
# --- Инициализация session_state и загрузка БД ---

if "crm_store" not in st.session_state:
    st.session_state.crm_store = {}

if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "clients"  # clients, deals, tasks, chat

if "sidebar_expanded" not in st.session_state:
    st.session_state.sidebar_expanded = True

# Загрузка БД при старте
@st.cache_resource
def load_db():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    # Если файла нет — создаём дефолтную структуру
    return {
        "clients": [],
        "deals": [],
        "users": [
            {"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}
        ],
        "_migrated": "v2",
        "internal_tasks": [],
        "chat_messages": [],
        "qa_entries": [],
        "suppliers": []
    }

def refresh_db_from_file():
    db = load_db()
    st.session_state.crm_store = db
    assign_deal_numbers(st.session_state.crm_store)
    assign_task_numbers(st.session_state.crm_store)

refresh_db_from_file()

# --- Авторизация ---

def login_page():
    st.title("Вход в Айплинт CRM")
    with st.form("login_form"):
        login = st.text_input("Логин", value="admin")
        pwd = st.text_input("Пароль", type="password")
        submitted = st.form_submit_button("Войти", type="primary")
        if submitted:
            user = find_user_by_login(login)
            if user and verify_password(pwd, user["password"]):
                st.session_state.user_logged_in = True
                st.session_state.current_user = user
                st.rerun()
            else:
                st.error("Неверный логин или пароль")

def logout_button():
    if st.button("Выйти", key="logout_btn", type="secondary"):
        st.session_state.user_logged_in = False
        st.session_state.current_user = None
        st.rerun()

# --- Навигация и сайдбар ---

def render_sidebar():
    with st.sidebar:
        st.markdown("## Айплинт CRM")
        st.write(f"Пользователь: **{st.session_state.current_user['name']}**")
        logout_button()
        st.divider()
        
        nav_options = [
            ("👤 Клиенты", "clients"),
            ("💰 Сделки", "deals"),
            ("📝 Задачи", "tasks"),
            ("💬 Чат", "chat"),
            ("⚙️ Настройки", "settings")
        ]
        for label, mode in nav_options:
            if st.button(label, key=f"nav_{mode}", type="secondary", use_container_width=True):
                st.session_state.view_mode = mode
                st.rerun()
        
        st.divider()
        with st.expander("Помощь и контакты"):
            st.write("CRM для компании «Айплинт» — управление клиентами, сделками, задачами и коммуникациями.")
            st.write(f"Сайт: {MAX_URL}")
            st.write(f"Телефон: {MAX_NUMBER}")

# --- Вспомогательные UI-функции ---

def format_client_row(c):
    status_badge = ""
    if c.get("is_active", True):
        status_badge = '<span class="ready-badge">Активен</span>'
    else:
        status_badge = '<span class="in-work-badge">В работе</span>'
    
    manager = c.get("manager", "Не назначен")
    category = c.get("category", "Не определена")
    
    html = f"""
    <div style="display:flex; align-items:center; gap:12px; padding:10px; border-radius:12px; background:#FFFFFF; border:1px solid #E8EBEF;">
        <div style="font-size:1.1rem; font-weight:600;">{c["name"]}</div>
        {status_badge}
        <div style="margin-left:auto; font-size:0.85rem; color:#7F8C9A;">{category}</div>
        <div style="font-size:0.85rem; color:#5A6B7D;">Менеджер: {manager}</div>
    </div>
    """
    return html

def render_client_card(c):
    with st.expander(f"👤 {c['name']}", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.metric("Телефон", c.get("phone", "—"))
            st.metric("Email", c.get("email", "—"))
            st.metric("Адрес", c.get("address", "—"))
        with col2:
            st.metric("Скидка", f"{c.get('discount', 0)} %")
            st.metric("Категория", c.get("category", "—"))
        
        st.divider()
        st.subheader("Файлы клиента")
        files = c.get("client_files", [])
        if files:
            for f in files:
                fname = f.get("file_name", "Файл")
                fpath = f.get("file_path", "")
                if fpath:
                    # Кнопка просмотра/скачивания
                    if fpath.startswith("CRM_NE_TROGAT"):
                        # Для Яндекс Диска можно сделать ссылку на скачивание через API
                        st.button(f"📥 {fname}", key=f"dl_{fpath}")
                    else:
                        st.download_button(f"📥 {fname}", data=open(fpath, "rb").read(), file_name=fname, use_container_width=True)
        else:
            st.caption("Нет загруженных файлов")
        
        # Действия с клиентом
        ac_col1, ac_col2, ac_col3 = st.columns([1, 1, 1], gap="small")
        with ac_col1:
            if st.button("📝 Задача", key=f"task_{c['id']}"):
                # Логика создания задачи — вынести в отдельный обработчик
                pass
        with ac_col2:
            if st.button("💰 Сделка", key=f"deal_{c['id']}"):
                pass
        with ac_col3:
            if st.button("🗑 Удалить", type="secondary", key=f"del_{c['id']}"):
                confirm = st.checkbox("Подтверждаю удаление", key=f"conf_{c['id']}")
                if confirm:
                    st.session_state.crm_store["clients"] = [cl for cl in st.session_state.crm_store["clients"] if cl["id"] != c["id"]]
                    refresh_db_from_file()
                    st.success("Клиент удалён")
                    st.rerun()

# --- Основной роутер по view_mode ---

def main_router():
    if not st.session_state.user_logged_in:
        login_page()
        return
    
    render_sidebar()
    
    mode = st.session_state.view_mode
    
    if mode == "clients":
        st.header("👤 Управление клиентами")
        # Кнопка добавления клиента
        with st.expander("Добавить нового клиента", expanded=False):
            with st.form("add_client_form"):
                name = st.text_input("ФИО / Название компании")
                phone = st.text_input("Телефон")
                email = st.text_input("Email")
                address = st.text_area("Адрес")
                category = st.selectbox("Категория", CATEGORIES)
                discount = st.number_input("Скидка (%)", min_value=0, max_value=100, value=0)
                manager = st.text_input("Менеджер (ФИО)")
                submitted = st.form_submit_button("Сохранить", type="primary")
                if submitted:
                    new_id = str(uuid.uuid4())
                    new_client = {
                        "id": new_id,
                        "name": name,
                        "phone": format_phone(phone),
                        "email": email,
                        "address": address,
                        "category": category,
                        "discount": discount,
                        "manager": manager,
                        "client_files": [],
                        "tasks": [],
                        "is_active": True,
                        "created_at": now_str(),
                        "last_modified": now_str()
                    }
                    st.session_state.crm_store["clients"].append(new_client)
                    refresh_db_from_file()
                    st.success("Клиент добавлен")
                    st.rerun()
        
        # Список клиентов
        clients = st.session_state.crm_store.get("clients", [])
        for c in sorted(clients, key=get_sort_key, reverse=True):
            st.markdown(format_client_row(c), unsafe_allow_html=True)
            render_client_card(c)
        
        if not clients:
            st.info("Список клиентов пуст. Добавьте первого клиента выше.")
    
    elif mode == "deals":
        st.header("💰 Сделки")
        st.info("В разработке: интерфейс сделок и статусов оплаты")
        # Сюда позже добавим логику сделок с номерами, статусами и суммами
    
    elif mode == "tasks":
        st.header("📝 Задачи")
        st.info("В разработке: список задач, дедлайны, статусы выполнения")
    
    elif mode == "chat":
        st.header("💬 Внутренний чат")
        st.info("В разработке: обмен сообщениями между сотрудниками и история переписки")
    
    elif mode == "settings":
        st.header("⚙️ Настройки CRM")
        st.subheader("Интеграция с Яндекс.Диском")
        status = "✅ Подключено" if check_cloud_status() else "⚠️ Не подключено"
        st.metric("Статус облака", status)
        if st.button("Синхронизировать базу сейчас", type="primary"):
            upload_db_to_yandex_async()
            st.success("Синхронизация запущена в фоне")
        
        st.divider()
        st.subheader("Экспорт данных")
        csv_data = export_clients_csv()
        st.download_button("📥 Скачать список клиентов (CSV)", data=csv_data, file_name="ayplint_clients.csv", use_container_width=True)

# Запуск основного интерфейса
main_router()
