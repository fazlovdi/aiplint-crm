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
    .stExpander { border-radius: 14px; overflow: hidden; background-color: #FFFFFF; margin-bottom: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
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
    .stButton > button { border-radius: 10px; font-weight: 500; transition: all 0.15s ease; }
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
    code { background-color: #EEF0F3; color: #5A6B7D; border-radius: 6px; padding: 0.1rem 0.35rem; font-size: 0.9em; }
    .stHorizontalBlock .stButton button { border-radius: 12px; font-size: 0.95rem; font-weight: 600; padding: 0.65rem 1rem; }
    [data-testid="stFileUploader"] { border-radius: 14px; border: 2px dashed #C9CFD7; background-color: #FAFBFC; padding: 0.75rem; }
    .greeting-block { margin-bottom: 1.5rem !important; }
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
    .custom-img-print-btn { width: 100%; padding: 8px; background: #bc1661; color: white; border: none; border-radius: 10px; cursor: pointer; font-size: 14px; font-weight: 600; transition: background 0.15s; }
    .custom-img-print-btn:hover { background: #9a1452; }
    .chat-msg { padding: 8px 12px; border-radius: 10px; margin-bottom: 6px; max-width: 80%; }
    .chat-msg-me { background-color: #bc1661; color: white; margin-left: auto; }
    .chat-msg-other { background-color: #EEF0F3; color: #2C3E50; }
    .qa-card { background: #FFFFFF; border: 1px solid #E8EBEF; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
    #crm-lightbox { position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:999999; display:none; align-items:center; justify-content:center; cursor:pointer; }
    #crm-lightbox img { max-width:90%; max-height:90%; border-radius:8px; }
    .thumb-grid { display:flex; flex-wrap:wrap; gap:8px; }
    .thumb-item { position:relative; width:110px; }
    .thumb-item img { width:110px; height:110px; object-fit:cover; border-radius:8px; cursor:pointer; border:1px solid #DCE0E5; }
    .thumb-item img:hover { border-color:#bc1661; }
    .thumb-name { font-size:0.7rem; color:#7F8C9A; max-width:110px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .st-key-cl_btn_wrap button, .st-key-dl_btn_wrap button, .st-key-tk_btn_wrap button { border-left-width: 4px !important; border-left-style: solid !important; }
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

raw_token = st.secrets.get("YANDEX_DISK_TOKEN", "")
if isinstance(raw_token, str):
    YANDEX_TOKEN = raw_token.strip().strip('"').strip("'")
else:
    YANDEX_TOKEN = ""

def inject_border_css(key, color):
    if color:
        st.markdown(f"<style>.st-key-{key} > .stExpander > details {{ border: 2px solid {color} !important; border-radius: 14px !important; }}</style>", unsafe_allow_html=True)

def inject_payment_container_css(deal_id, status):
    border_color = "#2E7D32" if status == "Оплачено" else "#C62828"
    bg_color = "#E8F5E9" if status == "Оплачено" else "#FFEBEE"
    st.markdown(f"<style>.st-key-ps_wrap_{deal_id} {{ border: 2px solid {border_color} !important; border-radius: 10px !important; background-color: {bg_color} !important; padding: 8px 12px !important; }}</style>", unsafe_allow_html=True)

def hash_password(pwd, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + pwd.strip()).encode()).hexdigest()
    return f"{salt}:{h}"

def is_hashed(s):
    if not s:
        return False
    if ":" in s:
        parts = s.split(":")
        return len(parts) == 2 and len(parts[0]) == 32 and len(parts[1]) == 64 and all(c in "0123456789abcdef" for c in parts[0] + parts[1])
    return len(s) == 64 and all(c in "0123456789abcdef" for c in s)

def verify_password(pwd, stored):
    if not stored:
        return False
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
        if u["login"] == login:
            return u
    return None

def yandex_headers():
    return {"Authorization": f"OAuth {YANDEX_TOKEN}", "Accept": "application/json"}

def check_cloud_status():
    if not YANDEX_TOKEN:
        return False
    try:
        res = requests.get(YANDEX_API_URL, headers=yandex_headers(), timeout=5)
        return res.status_code == 200
    except Exception:
        return False

def init_yandex_folders():
    if not YANDEX_TOKEN:
        return
    for folder in ["CRM_NE_TROGAT", "CRM_NE_TROGAT/uploads"]:
        try:
            requests.put(YANDEX_API_URL, params={"path": f"disk:/{folder}"}, headers=yandex_headers(), timeout=10)
        except Exception:
            pass

def download_db_from_yandex():
    if not YANDEX_TOKEN:
        return
    try:
        res = requests.get(f"{YANDEX_API_URL}/download", params={"path": f"disk:/CRM_NE_TROGAT/{FILE_NAME}"}, headers=yandex_headers(), timeout=10)
        if res.status_code == 200:
            dl = requests.get(res.json().get("href"), timeout=30)
            if dl.status_code == 200:
                with open(FILE_NAME, "w", encoding="utf-8") as f:
                    f.write(dl.text)
                return
    except Exception:
        pass
    if not os.path.exists(FILE_NAME):
        db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}], "_migrated": "v2", "internal_tasks": [], "chat_messages": [], "qa_entries": []}
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

def upload_db_to_yandex_async():
    if not YANDEX_TOKEN or not os.path.exists(FILE_NAME):
        return
    def _u():
        try:
            res = requests.get(f"{YANDEX_API_URL}/upload", params={"path": f"disk:/CRM_NE_TROGAT/{FILE_NAME}", "overwrite": "true"}, headers=yandex_headers(), timeout=10)
            if res.status_code == 200:
                with open(FILE_NAME, "rb") as f:
                    requests.put(res.json().get("href"), data=f, timeout=30)
        except Exception:
            pass
    threading.Thread(target=_u, daemon=True).start()

def upload_file_to_yandex(file_bytes, remote_name):
    if not YANDEX_TOKEN:
        return False
    try:
        res = requests.get(f"{YANDEX_API_URL}/upload", params={"path": f"disk:/CRM_NE_TROGAT/uploads/{remote_name}", "overwrite": "true"}, headers=yandex_headers(), timeout=10)
        if res.status_code == 200:
            return requests.put(res.json().get("href"), data=file_bytes, timeout=30).status_code in (200, 201)
    except Exception:
        pass
    return False

@st.cache_data(ttl=300, show_spinner=False)
def download_file_from_yandex(remote_path):
    if not YANDEX_TOKEN:
        return None
    try:
        res = requests.get(f"{YANDEX_API_URL}/download", params={"path": f"disk:/{remote_path}"}, headers=yandex_headers(), timeout=10)
        if res.status_code == 200:
            fr = requests.get(res.json().get("href"), timeout=30)
            if fr.status_code == 200:
                return fr.content
    except Exception:
        pass
    return None

def format_phone(p_str):
    if not p_str:
        return ""
    d = re.sub(r"\D", "", p_str)
    if len(d) == 11 and d[0] in ("7", "8"):
        d = d[1:]
    if len(d) == 10:
        return f"+7 {d[0:3]} {d[3:6]}-{d[6:8]}-{d[8:10]}"
    return p_str.strip()

def save_uploaded_file(u_file, c_id, prefix=""):
    if u_file is None:
        return None
    name = f"{c_id}_{prefix}_{int(datetime.now().timestamp())}_{u_file.name}"
    b = u_file.getvalue()
    if YANDEX_TOKEN:
        rp = f"CRM_NE_TROGAT/uploads/{name}"
        if upload_file_to_yandex(b, name):
            return {"path": rp, "name": u_file.name}
        st.warning("Не удалось загрузить на Диск, файл сохранён локально")
    os.makedirs("uploads", exist_ok=True)
    lp = f"uploads/{name}"
    with open(lp, "wb") as f:
        f.write(b)
    return {"path": lp, "name": u_file.name}

def save_uploaded_files(files, c_id, prefix=""):
    if files is None:
        return []
    if not isinstance(files, list):
        files = [files]
    result = []
    for f in files:
        fi = save_uploaded_file(f, c_id, prefix)
        if fi:
            result.append(fi)
    return result

def normalize_remote_path(fp):
    if not fp:
        return None
    if fp.startswith("CRM_NE_TROGAT"):
        return fp
    elif fp.startswith("uploads/"):
        return f"CRM_NE_TROGAT/{fp}"
    else:
        return f"CRM_NE_TROGAT/uploads/{os.path.basename(fp)}"

@st.cache_data
def get_logo_base64():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def export_clients_csv():
    o = io.StringIO()
    w = csv.writer(o, delimiter=";")
    w.writerow(["ID", "ФИО", "Телефон", "Email", "Адрес", "Категория", "Скидка %", "Ответственный"])
    for c in st.session_state.crm_store["clients"]:
        w.writerow([c["id"], c["name"], c["phone"], c.get("email", ""), c.get("address", ""), c.get("category", ""), c.get("discount", 0), c.get("manager", "")])
    return ("\uFEFF" + o.getvalue()).encode("utf-8")

def get_client_by_id(c_id):
    for c in st.session_state.crm_store["clients"]:
        if c["id"] == c_id:
            return c
    return None

def get_deal_by_id(d_id):
    for d in st.session_state.crm_store.get("deals", []):
        if d["id"] == d_id:
            return d
    return None

def parse_deadline(ds):
    if not ds:
        return datetime.now().date()
    try:
        return datetime.strptime(ds, "%Y-%m-%d").date()
    except Exception:
        try:
            return datetime.strptime(ds, "%Y-%m-%d %H:%M").date()
        except Exception:
            return datetime.now().date()

def is_task_overdue(task):
    if task.get("done"):
        return False
    dl = task.get("deadline", "")
    if not dl:
        return False
    now = datetime.now()
    try:
        if len(dl) == 10:
            deadline = datetime.strptime(dl, "%Y-%m-%d")
            deadline = deadline.replace(hour=23, minute=59, second=59)
        elif len(dl) >= 16:
            deadline = datetime.strptime(dl[:16], "%Y-%m-%d %H:%M")
        else:
            return False
    except Exception:
        return False
    return deadline < now

def get_task_sort_date(task):
    dl = task.get("deadline", "")
    try:
        return datetime.strptime(dl, "%Y-%m-%d").date()
    except Exception:
        try:
            return datetime.strptime(dl, "%Y-%m-%d %H:%M").date()
        except Exception:
            return datetime.max.date()

def format_date(ds):
    if not ds:
        return ""
    try:
        return datetime.strptime(ds, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        try:
            return datetime.strptime(ds, "%Y-%m-%d %H:%M").strftime("%d/%m/%Y")
        except Exception:
            return ds

def get_managers_list():
    return [u.get("name", u["login"]) for u in st.session_state.crm_store.get("users", []) if u.get("role") != "admin"]

def auto_task_title(tt, cn, dt):
    if tt == "Отправить заказ":
        return f"Отправка по {dt}" if dt else f"Отправка: {cn}"
    return f"Связаться: {cn}"

def render_phone_inline(phone, uid):
    cph = re.sub(r"\D", "", phone)
    if cph.startswith("8") and len(cph) == 11:
        cph = "7" + cph[1:]
    elif not cph:
        cph = "79990000000"
    btn_id = f"ph_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f"""
    <div class="phone-action-group" style="padding:4px 0;">
        <span style="font-size:1rem;font-weight:600;color:#2C3E50;">{phone}</span>
        <button onclick="navigator.clipboard.writeText('{phone}').then(function(){{var b=document.getElementById('{btn_id}');b.textContent='\u2713';setTimeout(function(){{b.textContent='\U0001F4CB';}},1500);}});" class="phone-btn" id="{btn_id}" title="Скопировать">\U0001F4CB</button>
        <a href="tel:+{cph}" class="phone-btn" title="Позвонить">\U0001F4DE</a>
    </div>
    """, unsafe_allow_html=True)

def render_extra_phone_inline(phone, name, role, uid):
    cph = re.sub(r"\D", "", phone)
    if cph.startswith("8") and len(cph) == 11:
        cph = "7" + cph[1:]
    elif not cph:
        cph = "79990000000"
    info = f"{phone} \u2014 {name} ({role})" if name else phone
    btn_id = f"ep_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f"""
    <div class="phone-action-group" style="padding:4px 0;flex-wrap:wrap;gap:8px;white-space:normal;">
        <span style="font-size:0.9rem;color:#3C4A5A;flex:1 1 auto;min-width:0;word-break:break-word;">{info}</span>
        <button onclick="navigator.clipboard.writeText('{phone}').then(function(){{var b=document.getElementById('{btn_id}');b.textContent='\u2713';setTimeout(function(){{b.textContent='\U0001F4CB';}},1500);}});" class="phone-btn" id="{btn_id}" title="Скопировать">\U0001F4CB</button>
        <a href="tel:+{cph}" class="phone-btn" title="Позвонить">\U0001F4DE</a>
    </div>
    """, unsafe_allow_html=True)

def render_payment_status_badge(status):
    cls = "payment-status-paid" if status == "Оплачено" else "payment-status-unpaid"
    st.markdown(f'<span class="payment-status-badge {cls}">{status}</span>', unsafe_allow_html=True)

def render_file_thumbs(files, prefix, allow_delete=False, entity_id=None):
    if not files:
        st.caption("Файлов нет")
        return
    img_files = []
    other_files = []
    for ff in files:
        fn = ff.get("file_name", ff.get("name", "файл"))
        ext = os.path.splitext(fn)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
            img_files.append(ff)
        else:
            other_files.append(ff)
    if img_files:
        ncols = min(len(img_files), 4)
        cols = st.columns(ncols)
        for i, ff in enumerate(img_files):
            with cols[i % ncols]:
                fp = ff.get("file_path", ff.get("path"))
                fn = ff.get("file_name", ff.get("name", "файл"))
                if fp and not fp.startswith("CRM_NE_TROGAT") and os.path.exists(fp):
                    try:
                        with open(fp, "rb") as f:
                            fb = f.read()
                    except:
                        fb = None
                else:
                    rp = normalize_remote_path(fp)
                    fb = download_file_from_yandex(rp) if rp else None
                if fb:
                    ext = os.path.splitext(fn)[1].lower()
                    b64 = base64.b64encode(fb).decode()
                    mt = f"image/{'jpeg' if ext == '.jpg' else ext[1:]}"
                    st.markdown(f"""
                    <div class="thumb-item">
                        <img src="data:{mt};base64,{b64}" title="{fn}" onclick="window.crmOpenLightbox && window.crmOpenLightbox(this.src)" />
                        <div class="thumb-name">{fn}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.download_button("\U00002B07", data=fb, file_name=fn, key=f"dl_{prefix}_{i}")
                    if allow_delete and st.session_state.user_role == "admin":
                        if st.button("\U0001F5D1", key=f"del_{prefix}_{i}", help="Удалить"):
                            files.pop(i)
                            commit_and_rerun(st.session_state.crm_store, "Файл удалён")
    for i, ff in enumerate(other_files):
        fp = ff.get("file_path", ff.get("path"))
        fn = ff.get("file_name", ff.get("name", "файл"))
        if fp and not fp.startswith("CRM_NE_TROGAT") and os.path.exists(fp):
            try:
                with open(fp, "rb") as f:
                    fb = f.read()
            except:
                fb = None
        else:
            rp = normalize_remote_path(fp)
            fb = download_file_from_yandex(rp) if rp else None
        if fb:
            ext = os.path.splitext(fn)[1].lower()
            if ext == ".pdf":
                st.download_button(f"\U0001F4C4 {fn}", data=fb, file_name=fn, mime="application/pdf", key=f"dl_{prefix}_o_{i}")
            else:
                st.download_button(f"\U0001F4C4 {fn}", data=fb, file_name=fn, key=f"dl_{prefix}_o_{i}")
            if allow_delete and st.session_state.user_role == "admin":
                if st.button("\U0001F5D1 Удалить", key=f"del_{prefix}_o_{i}"):
                    files.pop(len(img_files) + i)
                    commit_and_rerun(st.session_state.crm_store, "Файл удалён")

def render_file_action_buttons(fp, fn, kp):
    if fp and not fp.startswith("CRM_NE_TROGAT") and os.path.exists(fp):
        try:
            with open(fp, "rb") as f:
                fb = f.read()
        except:
            fb = None
    else:
        rp = normalize_remote_path(fp)
        fb = download_file_from_yandex(rp) if rp else None
    if not fb:
        st.caption("Файл недоступен")
        return
    ext = os.path.splitext(fn)[1].lower()
    if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
        try:
            st.image(fb, caption=fn)
        except:
            pass
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("Скачать", data=fb, file_name=fn, key=f"dl_{kp}")
        with c2:
            b64 = base64.b64encode(fb).decode()
            mt = f"image/{'jpeg' if ext == '.jpg' else ext[1:]}"
            safe_kp = re.sub(r'[^a-zA-Z0-9_]', '_', kp)
            btn_id = f"img_print_btn_{safe_kp}"
            st.markdown(f'<button class="custom-img-print-btn" id="{btn_id}">Распечатать</button>', unsafe_allow_html=True)
            st.components.v1.html(f"""
            <script>
            (function() {{
                var btn = window.parent.document.getElementById('{btn_id}');
                if (!btn) return;
                var html = '<html><head><meta charset="utf-8"></head><body style="margin:0;text-align:center;"><img src="data:{mt};base64,{b64}" style="max-width:100%;" /></body></html>';
                btn.addEventListener('click', function() {{
                    var w = window.open('', '_blank');
                    if (!w) {{ alert('Разрешите всплывающие окна для печати'); return; }}
                    w.document.open(); w.document.write(html); w.document.close(); w.focus();
                    setTimeout(function() {{ try {{ w.print(); }} catch(e) {{}} }}, 500);
                    w.onafterprint = function() {{ setTimeout(function() {{ w.close(); }}, 300); }};
                }});
            }})();
            </script>
            """, height=0)
    elif ext == ".pdf":
        st.download_button("Открыть / Скачать PDF", data=fb, file_name=fn, mime="application/pdf", key=f"dl_{kp}")
    else:
        st.download_button("Скачать", data=fb, file_name=fn, key=f"dl_{kp}")

def build_print_html(task, cl, tp, fd):
    def esc(s):
        return str(s if s else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    products_html = esc(task.get('products', '')).replace('\n', '<br>')
    oav = task.get('order_amount', 0)
    cost_html = ""
    if oav and oav > 0:
        cost_html = f"<div style='margin-top:6px;font-size:16px;font-weight:bold;'>Сумма: {oav:,.0f} руб.</div>".replace(",", " ")
    file_reminder = ""
    if task.get("task_files"):
        file_reminder = "<div style='color:#D65757;font-weight:bold;margin:14px 0;border:2px solid #D65757;padding:8px;border-radius:8px;'>&#9888; Не забудь распечатать вложенные файлы!</div>"
    lb = get_logo_base64()
    logo_html = f"<img src='data:image/png;base64,{lb}' width='180' style='float:left;margin-right:20px;'/>" if lb else "<div style='font-size:24px;font-weight:bold;float:left;margin-right:20px;'>АЙПЛИНТ</div>"
    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>Бланк задачи</title>
<style>body {{ font-family: Arial, sans-serif; margin: 40px; color: #222; }} .clearfix::after {{ content: ""; display: table; clear: both; }} .header {{ text-align: center; border-bottom: 2px solid #333; padding: 10px; }} .row {{ margin: 8px 0; }} hr {{ border: none; border-top: 1px solid #ccc; margin: 14px 0; }} .sig {{ margin-top: 30px; }} .sig p {{ margin: 12px 0; }} @media print {{ body {{ margin: 15px; }} }}</style>
</head><body>
<div class="clearfix">{logo_html}</div>
<div class="header"><h2>БЛАНК ЗАДАЧИ</h2><p>{datetime.now().strftime('%d/%m/%Y')}</p></div>
<div class="row"><b>Клиент:</b> {esc(cl['name'])} ({esc(cl['phone'])})</div>
<div class="row"><b>Тип:</b> {esc(tp)}</div>
<div class="row"><b>Срок:</b> {esc(fd)}</div>
<div class="row"><b>Ответственный:</b> {esc(task.get('manager', ''))}</div>
<hr>
<div class="row"><b>Товары:</b><br>{products_html}</div>
<div class="row"><b>Адрес:</b> {esc(task.get('ship_addr', ''))}</div>
<div class="row"><b>Получатель:</b> {esc(task.get('receiver', ''))} ({esc(task.get('receiver_phone', ''))})</div>
<div class="row"><b>Оплата:</b> {esc(task.get('ship_pay', ''))}</div>
<div class="row"><b>Трек:</b> {esc(task.get('tk_num', ''))}</div>
{cost_html}
{file_reminder}
<div class="sig"><p>Отпустил: _____________</p><p>Получил: _____________</p></div>
</body></html>"""

def render_print_button(task, cl, tp, fd, key_suffix):
    html_content = build_print_html(task, cl, tp, fd)
    html_json = json.dumps(html_content).replace('<', '\\u003c')
    safe_key = key_suffix.replace('-', '_').replace('.', '_')
    btn_id = f"print_btn_{safe_key}"
    st.markdown(f'<button class="custom-print-btn" id="{btn_id}">Распечатать задачу</button>', unsafe_allow_html=True)
    st.components.v1.html(f"""
    <script>
    (function() {{
        var btn = window.parent.document.getElementById('{btn_id}');
        if (!btn) return;
        var html = {html_json};
        btn.addEventListener('click', function() {{
            var w = window.open('', '_blank');
            if (!w) {{ alert('Разрешите всплывающие окна для печати'); return; }}
            w.document.open(); w.document.write(html); w.document.close(); w.focus();
            setTimeout(function() {{ try {{ w.print(); }} catch(e) {{}} }}, 500);
            w.onafterprint = function() {{ setTimeout(function() {{ w.close(); }}, 300); }};
        }});
    }})();
    </script>
    """, height=0)

def render_deal_files_in_task(deal, task_key_prefix):
    if not deal:
        return
    deal_files = deal.get("deal_files", [])
    if not deal_files:
        return
    st.markdown("**Файлы сделки:**")
    for dfi, dff in enumerate(deal_files):
        st.markdown(f"\U0001F4C4 {dff.get('file_name', dff.get('name', 'файл'))}")
        render_file_action_buttons(dff.get("file_path", dff.get("path")), dff.get("file_name", dff.get("name", "файл")), f"{task_key_prefix}_dealfile_{dfi}")

def render_task_files_in_deal(client, deal_id, key_prefix):
    if not client:
        return
    task_files_list = []
    for t in client.get("tasks", []):
        if t.get("deal_id") == deal_id and t.get("task_files"):
            for tf in t["task_files"]:
                task_files_list.append((t, tf))
    if not task_files_list:
        return
    st.markdown("**Файлы из задач:**")
    for tfi, (task, tf) in enumerate(task_files_list):
        task_type = task.get("type", "Связаться")
        st.caption(f"\U0001F4C4 {tf.get('name', 'файл')} (из задачи: {task_type})")
        render_file_action_buttons(tf.get("path"), tf.get("name", "файл"), f"{key_prefix}_taskfile_{tfi}")

def migrate_task_files(t):
    if "task_files" not in t:
        t["task_files"] = []
        if t.get("file_path"):
            t["task_files"].append({"path": t["file_path"], "name": t.get("file_name", "файл")})
    if "completion_files" not in t:
        t["completion_files"] = []
        if t.get("completion_file_path"):
            t["completion_files"].append({"path": t["completion_file_path"], "name": t.get("completion_file_name", "файл")})

def migrate_data(data):
    du = [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}]
    if "users" not in data:
        data["users"] = du
    for u in data["users"]:
        if not is_hashed(u.get("password", "")):
            u["password"] = hash_password(u["password"])
    for c in data.get("clients", []):
        client_deals = [d for d in data.get("deals", []) if d.get("client_id") == c["id"]]
        first_deal_id = client_deals[0]["id"] if client_deals else None
        for k, v in [("email",""),("address",""),("base_comment",""),("category","Покупатель"),("discount",0),("extra_phones",[]),("extra_emails",[]),("extra_addresses",[]),("client_files",[]),("client_comments",[]),("manager",""),("comments",[]),("tasks",[])]:
            if k not in c or c[k] == "-":
                c[k] = v
        for ea in c.get("extra_addresses", []):
            if isinstance(ea, str):
                idx = c["extra_addresses"].index(ea)
                c["extra_addresses"][idx] = {"address": ea, "resp_name": "", "resp_role": "", "resp_phone": "", "resp_email": ""}
        for t in c.get("tasks", []):
            if "manager" not in t:
                t["manager"] = c.get("manager", "")
            if "deadline" in t and " " in str(t["deadline"]):
                t["deadline"] = str(t["deadline"]).split(" ")[0]
            if "completion_report" not in t:
                t["completion_report"] = ""
            if "deal_id" not in t:
                t["deal_id"] = first_deal_id
            migrate_task_files(t)
    for d in data.get("deals", []):
        if "deal_title" not in d:
            d["deal_title"] = ""
        if "deal_comments" not in d:
            d["deal_comments"] = []
        if "deal_files" not in d:
            d["deal_files"] = []
        if "payment_status" not in d:
            d["payment_status"] = "Не оплачено"
        if "manager" not in d:
            d["manager"] = ""
        if "close_files" not in d:
            d["close_files"] = []
            if d.get("close_file_path"):
                d["close_files"].append({"path": d["close_file_path"], "name": d.get("close_file_name", "файл")})
        if d.get("status") == "New":
            d["status"] = "Новый"
        if d.get("status") == "На согласовании":
            d["status"] = "В работе"
    if "internal_tasks" not in data:
        data["internal_tasks"] = []
    if "chat_messages" not in data:
        data["chat_messages"] = []
    if "qa_entries" not in data:
        data["qa_entries"] = []
    data["_migrated"] = "v2"
    return data
def load_data():
    download_db_from_yandex()
    db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}], "_migrated": "v2", "internal_tasks": [], "chat_messages": [], "qa_entries": []}
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
                    for t in c.get("tasks", []):
                        if "completion_report" not in t:
                            t["completion_report"] = ""
                        if "deal_id" not in t:
                            t["deal_id"] = first_deal_id
                        migrate_task_files(t)
                for d in data.get("deals", []):
                    if "deal_title" not in d:
                        d["deal_title"] = ""
                    if "deal_files" not in d:
                        d["deal_files"] = []
                    if "payment_status" not in d:
                        d["payment_status"] = "Не оплачено"
                    if "manager" not in d:
                        d["manager"] = ""
                    if "close_files" not in d:
                        d["close_files"] = []
                        if d.get("close_file_path"):
                            d["close_files"].append({"path": d["close_file_path"], "name": d.get("close_file_name", "файл")})
                    if d.get("status") == "На согласовании":
                        d["status"] = "В работе"
                if "internal_tasks" not in data:
                    data["internal_tasks"] = []
                if "chat_messages" not in data:
                    data["chat_messages"] = []
                if "qa_entries" not in data:
                    data["qa_entries"] = []
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
        st.toast(toast_msg, icon="\u2705")
    st.rerun()

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
            st.markdown(f"- {t.get('type', 'Связаться')} \u2014 {format_date(t.get('deadline', ''))} \u2014 {t.get('text', '')}")
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
                    d['close_files'] = save_uploaded_files(close_files, d["client_id"], "deal_close") if close_files else []
                    break
            save_data(st.session_state.crm_store)
            st.toast("Сделка завершена", icon="\u2705")
            st.rerun()
        else:
            st.error("Заполните отчёт")

if "crm_store" not in st.session_state:
    with st.spinner("Загрузка данных..."):
        st.session_state.crm_store = load_data()
if "f_ph" not in st.session_state:
    st.session_state.f_ph = []
if "f_em" not in st.session_state:
    st.session_state.f_em = []
if "f_ad" not in st.session_state:
    st.session_state.f_ad = []
if "last_id" not in st.session_state:
    st.session_state.last_id = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Клиенты и сделки"
if "client_form_version" not in st.session_state:
    st.session_state.client_form_version = 0
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_login" not in st.session_state:
    st.session_state.user_login = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "cloud_ok" not in st.session_state:
    st.session_state.cloud_ok = check_cloud_status()
if "open_deal_id" not in st.session_state:
    st.session_state.open_deal_id = None
if "yandex_folders_ready" not in st.session_state:
    init_yandex_folders()
    st.session_state.yandex_folders_ready = True
if "deal_file_uploader_ver" not in st.session_state:
    st.session_state.deal_file_uploader_ver = {}
if "expanded_client_id" not in st.session_state:
    st.session_state.expanded_client_id = None
if "expanded_deal_id" not in st.session_state:
    st.session_state.expanded_deal_id = None
if "expanded_task_key" not in st.session_state:
    st.session_state.expanded_task_key = None
if "internal_subtab" not in st.session_state:
    st.session_state.internal_subtab = "Задачи сотрудникам"

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
                    st.toast("Успешный вход", icon="\U0001F513")
                    st.rerun()
                else:
                    st.error("Неверный логин или пароль.")
    st.stop()

st.markdown(f"""
<div class="greeting-block">
<h1 style='text-align: center; margin-bottom: 0.1rem;'>Айплинт CRM</h1>
<p style='text-align: center; color: #7F8C9A; font-size: 0.95rem; margin-top: 0; margin-bottom: 0;'>Продуктивного тебе дня, {st.session_state.user_name} \U0001F60A</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    if st.session_state.cloud_ok:
        st.success("Облако активно")
    else:
        st.warning("Облако недоступно (работа локально)")
    st.markdown("---")
    st.markdown(f"**{st.session_state.user_name}**")
    st.markdown(f"Роль: `{st.session_state.user_role}`")
    with st.expander("Сменить пароль"):
        cul = st.session_state.user_login
        np = st.text_input("Новый пароль:", type="password", key="self_new_pwd")
        cp = st.text_input("Повторите пароль:", type="password", key="self_conf_pwd")
        if st.button("Обновить", key="btn_save_self_pwd", use_container_width=True):
            if np and np == cp:
                for u in st.session_state.crm_store["users"]:
                    if u["login"] == cul:
                        u["password"] = hash_password(np)
                        commit_and_rerun(st.session_state.crm_store, "Пароль изменён")
            else:
                st.error("Пароли не совпадают")
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
                    else:
                        st.error("Логин уже занят")
                else:
                    st.error("Заполните все поля")
            st.markdown("---")
            for u in st.session_state.crm_store.get("users", []):
                ucl, ucr = st.columns([3, 1])
                with ucl:
                    st.markdown(f"**{u.get('name', u['login'])}** ({u['role']})")
                with ucr:
                    if u["login"] != st.session_state.user_login:
                        if st.button("X", key=f"del_u_{u['login']}", help="Удалить"):
                            st.session_state.crm_store["users"] = [x for x in st.session_state.crm_store["users"] if x["login"] != u["login"]]
                            commit_and_rerun(st.session_state.crm_store, "Сотрудник удалён")
    st.markdown("---")
    if st.button("Выйти", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_login = None
        st.session_state.user_name = None
        st.rerun()

nc1, nc2, nc3 = st.columns(3)
with nc1:
    if st.button("Клиенты и сделки", use_container_width=True, type="primary" if st.session_state.active_tab == "Клиенты и сделки" else "secondary"):
        st.session_state.active_tab = "Клиенты и сделки"
        st.rerun()
with nc2:
    if st.button("Задачи", use_container_width=True, type="primary" if st.session_state.active_tab == "Задачи" else "secondary"):
        st.session_state.active_tab = "Задачи"
        st.rerun()
with nc3:
    if st.button("Внутренние задачи", use_container_width=True, type="primary" if st.session_state.active_tab == "Внутренние задачи" else "secondary"):
        st.session_state.active_tab = "Внутренние задачи"
        st.rerun()
st.markdown("---")

_active_tab_name = st.session_state.active_tab
st.components.v1.html(f"""
<script>
(function() {{
    var w, doc;
    try {{ if (window.parent && window.parent !== window) {{ w = window.parent; doc = w.document; }} else {{ w = window; doc = document; }} }} catch(e) {{ w = window; doc = document; }}
    var label = doc.getElementById('sticky-tab-label');
    if (!label) {{ label = doc.createElement('div'); label.id = 'sticky-tab-label'; doc.body.appendChild(label); }}
    label.textContent = '{_active_tab_name}';
    var lastVisible = null;
    function findScrollEl() {{
        var sels = ['section[data-testid="stMain"]', '[data-testid="stScrollContent"]', '.stApp', 'main', '#root'];
        for (var i = 0; i < sels.length; i++) {{ var el = doc.querySelector(sels[i]); if (el && el.scrollHeight > el.clientHeight) return el; }}
        return null;
    }}
    function checkScroll() {{
        var el = findScrollEl();
        var st = el ? el.scrollTop : (w.scrollY || 0);
        var shouldShow = st > 80;
        if (shouldShow !== lastVisible) {{ if (shouldShow) {{ label.classList.add('visible'); }} else {{ label.classList.remove('visible'); }} lastVisible = shouldShow; }}
    }}
    var se = findScrollEl();
    if (se) se.addEventListener('scroll', checkScroll, {{passive:true}});
    w.addEventListener('scroll', checkScroll, {{passive:true}});
    setInterval(checkScroll, 500);
}})();
</script>
""", height=0)

cu = st.session_state.user_name
mgrs = get_managers_list()

if st.session_state.active_tab == "Клиенты и сделки":
    fv = st.session_state.client_form_version
    with st.expander("Добавить клиента", expanded=False, key=f"add_client_form_{fv}"):
        acl, acr = st.columns(2)
        with acl:
            cn = st.text_input("ФИО / Компания", key=f"cn_{fv}")
            cp = st.text_input("Основной телефон", key=f"cp_{fv}")
            ce = st.text_input("Основной Email", key=f"ce_{fv}")
            cd = st.number_input("Скидка (%)", min_value=0, max_value=100, step=1, key=f"cd_{fv}")
            cm = st.selectbox("Ответственный:", mgrs, index=mgrs.index(cu) if cu in mgrs else 0, key=f"cm_{fv}")
        with acr:
            ca = st.text_input("Основной адрес", key=f"ca_{fv}")
            cc = st.selectbox("Категория", ["Дизайнер", "Строитель", "Дилер", "Покупатель"], key=f"cc_{fv}")
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
                    else:
                        st.warning("Введите текст")
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
                clients = st.session_state.crm_store["clients"]
                nid = (max([c['id'] for c in clients]) if clients else 0) + 1
                nc = {
                    "id": nid, "name": cn, "phone": format_phone(cp), "email": ce, "address": ca,
                    "category": cc, "discount": int(cd), "base_comment": "", "manager": cm,
                    "extra_phones": [{"phone": format_phone(p["phone"]), "name": p["name"], "role": p["role"]} for p in st.session_state.f_ph if p["phone"].strip()],
                    "extra_emails": [e for e in st.session_state.f_em if e.strip()],
                    "extra_addresses": [{"address": a["address"], "resp_name": a["resp_name"], "resp_role": a["resp_role"], "resp_phone": a["resp_phone"], "resp_email": a["resp_email"]} for a in st.session_state.f_ad if a["address"].strip()],
                    "client_files": [], "client_comments": [], "comments": [], "tasks": []
                }
                if cf:
                    fi_list = save_uploaded_files(cf, nid, "profile")
                    if fi_list:
                        nc["client_files"].extend([{"file_path": fi["path"], "file_name": fi["name"]} for fi in fi_list])
                if st.session_state.get("pending_client_comments"):
                    nc["client_comments"] = list(st.session_state["pending_client_comments"])
                    st.session_state["pending_client_comments"] = []
                st.session_state.crm_store["clients"].append(nc)
                save_data(st.session_state.crm_store)
                st.session_state.f_ph, st.session_state.f_em, st.session_state.f_ad = [], [], []
                st.session_state.last_id = nid
                st.session_state.client_form_version += 1
                st.session_state.expanded_client_id = nid
                st.toast(f"Клиент {cn} добавлен", icon="\u2705")
                st.rerun()
            else:
                st.error("Заполните ФИО и телефон")

    st.markdown("### Поиск")
    sq = st.text_input("По имени, компании или телефону:", key="search_input_key", placeholder="Введите текст...").strip().lower()
    ctf = st.selectbox("Категория:", ["Все", "Дизайнер", "Строитель", "Дилер", "Покупатель"])
    all_clients = st.session_state.crm_store["clients"]
    fcl = []
    sd = re.sub(r"\D", "", sq)
    if sd and sd[0] in ("7", "8") and len(sd) > 1:
        sd = sd[1:]
    for cl in all_clients:
        if ctf != "Все" and cl.get("category", "Покупатель") != ctf:
            continue
        if sq:
            ct = f"{cl['name']} {cl.get('email','')} {cl.get('address','')} {cl.get('base_comment','')}".lower()
            mb = sq in ct
            acd = re.sub(r"\D", "", cl['phone'])
            for p in cl.get("extra_phones", []):
                acd += " " + re.sub(r"\D", "", p["phone"])
                ct += " " + p["name"].lower()
            mp = sd and (sd in acd)
            if not (mb or mp or sq in ct):
                continue
        fcl.append(cl)

    if all_clients:
        for cl in fcl:
            is_cl_exp = st.session_state.expanded_client_id == cl["id"]
            cl_tasks_all = cl.get("tasks", [])
            cl_overdue = any(not t.get("done") and is_task_overdue(t) for t in cl_tasks_all)
            cl_active = any(not t.get("done") for t in cl_tasks_all)
            if cl_overdue:
                cl_bg = "#FFEBEE"
                cl_bc = "#C62828"
            elif cl_active:
                cl_bg = "#E8F5E9"
                cl_bc = "#4CAF50"
            else:
                cl_bg = "#FFFFFF"
                cl_bc = "#DCE0E5"
            cl_deals = [d for d in st.session_state.crm_store["deals"] if d["client_id"] == cl["id"]]
            cl_label = f"{'\u25BC' if is_cl_exp else '\u25B6'} {cl['name']} \u2014 {cl['phone']} [{cl.get('category', 'Покупатель')}] | Сделок: {len(cl_deals)} | Задач: {len(cl_tasks_all)}"
            st.markdown(f"<style>.st-key-cl_btn_wrap_{cl['id']} button {{ background-color: {cl_bg} !important; border-left-color: {cl_bc} !important; }}</style>", unsafe_allow_html=True)
            with st.container(key=f"cl_btn_wrap_{cl['id']}"):
                if st.button(cl_label, key=f"cl_toggle_{cl['id']}", use_container_width=True, type="primary" if is_cl_exp else "secondary"):
                    if is_cl_exp:
                        st.session_state.expanded_client_id = None
                    else:
                        st.session_state.expanded_client_id = cl["id"]
                        st.session_state.expanded_deal_id = None
                        st.session_state.expanded_task_key = None
                    st.rerun()
            if is_cl_exp:
                with st.container(border=True):
                    info_col, comm_col = st.columns(2)
                    with info_col:
                        st.markdown("**Информация о клиенте:**")
                        render_phone_inline(cl['phone'], cl['id'])
                        st.markdown(f"{cl.get('email','')} | {cl.get('address','')}")
                        st.markdown(f"Скидка: **{cl.get('discount',0)}%** | Ответственный: **{cl.get('manager','\u2014')}**")
                        cph = re.sub(r"\D", "", cl['phone'])
                        if cph.startswith("8") and len(cph) == 11:
                            cph = "7" + cph[1:]
                        elif not cph:
                            cph = "79990000000"
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
                        if not cl.get("client_comments"):
                            st.caption("Пока нет комментариев")
                        cc_clr_key = f"clr_cc_{cl['id']}"
                        if st.session_state.get(cc_clr_key):
                            st.session_state[f"new_cc_input_{cl['id']}"] = ""
                            st.session_state[cc_clr_key] = False
                        nci = st.text_input("Добавить комментарий:", key=f"new_cc_input_{cl['id']}", placeholder="Введите комментарий...")
                        if st.button("Добавить комментарий", key=f"cc_btn_{cl['id']}", use_container_width=True):
                            if nci.strip():
                                cl.setdefault("client_comments", []).append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": nci.strip()})
                                st.session_state[cc_clr_key] = True
                                commit_and_rerun(st.session_state.crm_store, "Комментарий добавлен")
                            else:
                                st.warning("Введите текст")

                    st.markdown("---")
                    files_col, upload_col = st.columns(2)
                    with files_col:
                        st.markdown("**Файлы:**")
                        render_file_thumbs(cl.get("client_files", []), f"cli_{cl['id']}", allow_delete=True, entity_id=cl["id"])
                    with upload_col:
                        st.markdown("**Загрузить файлы:**")
                        ucf = st.file_uploader("Выберите файлы:", key=f"cf_up_{cl['id']}", accept_multiple_files=True, label_visibility="collapsed")
                        if st.button("Сохранить файлы", key=f"cf_btn_{cl['id']}", use_container_width=True):
                            if ucf:
                                fi_list = save_uploaded_files(ucf, cl["id"], "profile")
                                if fi_list:
                                    cl.setdefault("client_files", []).extend([{"file_path": fi["path"], "file_name": fi["name"]} for fi in fi_list])
                                    save_data(st.session_state.crm_store)
                                    st.toast("Файлы сохранены", icon="\U0001F4C1")
                                    st.rerun()
                            else:
                                st.warning("Выберите файл(ы)")

                    st.markdown("---")
                    st.markdown("**Задачи по клиенту:**")
                    client_only_tasks = [t for t in cl_tasks_all if not t.get("deal_id")]
                    if client_only_tasks:
                        client_only_tasks.sort(key=lambda t: (t.get("done", False), get_task_sort_date(t)))
                        for ti, t in enumerate(client_only_tasks):
                            task_key = f"cl_{cl['id']}_{ti}"
                            is_tk_exp = st.session_state.expanded_task_key == task_key
                            tk_overdue = is_task_overdue(t)
                            tk_done = t.get("done", False)
                            if tk_done:
                                tk_bg = "#F5F6F8"
                                tk_bc = "#C9CFD7"
                            elif tk_overdue:
                                tk_bg = "#FFEBEE"
                                tk_bc = "#C62828"
                            else:
                                tk_bg = "#E8F5E9"
                                tk_bc = "#4CAF50"
                            tk_status = "\u2705" if tk_done else ("\u23F3" if not tk_overdue else "\u26A0")
                            tk_label = f"{'    \u25BC' if is_tk_exp else '    \u25B6'} {tk_status} {t.get('type', 'Связаться')} \u2014 {t.get('text', '')} | {format_date(t.get('deadline', ''))}"
                            st.markdown(f"<style>.st-key-tk_btn_wrap_{task_key} button {{ background-color: {tk_bg} !important; border-left-color: {tk_bc} !important; }}</style>", unsafe_allow_html=True)
                            with st.container(key=f"tk_btn_wrap_{task_key}"):
                                if st.button(tk_label, key=f"tk_toggle_{task_key}", use_container_width=True, type="primary" if is_tk_exp else "secondary"):
                                    st.session_state.expanded_task_key = None if is_tk_exp else task_key
                                    st.rerun()
                            if is_tk_exp:
                                with st.container(border=True):
                                    st.markdown(f"**Тип:** {t.get('type', 'Связаться')}")
                                    st.markdown(f"**Срок:** {format_date(t.get('deadline', ''))}")
                                    st.markdown(f"**Ответственный:** {t.get('manager', '\u2014')}")
                                    if t.get('products'):
                                        st.markdown(f"**Товары:** {t['products']}")
                                    if t.get('ship_addr'):
                                        st.markdown(f"**Адрес:** {t['ship_addr']}")
                                    if t.get('receiver'):
                                        st.markdown(f"**Получатель:** {t['receiver']} ({t.get('receiver_phone', '')})")
                                    if t.get('order_amount', 0) > 0:
                                        st.markdown(f"**Сумма:** {t['order_amount']:,.0f} руб.".replace(",", " "))
                                    if t.get('task_comment'):
                                        st.markdown(f"**Комментарии:** {t['task_comment']}")
                                    if t.get("task_files"):
                                        st.markdown("**Файлы задачи:**")
                                        render_file_thumbs(t["task_files"], f"cltask_{cl['id']}_{ti}")
                                    st.markdown("---")
                                    if not tk_done:
                                        show_key = f"show_clt_complete_{cl['id']}_{ti}"
                                        if st.button("Выполнить задачу", key=f"btn_clt_complete_{cl['id']}_{ti}", type="primary", use_container_width=True):
                                            st.session_state[show_key] = not st.session_state.get(show_key, False)
                                            st.rerun()
                                        if st.session_state.get(show_key, False):
                                            rt = st.text_input("Отчёт (обязательно):", key=f"clt_rt_{cl['id']}_{ti}")
                                            uf = st.file_uploader("Файлы/фото отчёта:", key=f"clt_uf_{cl['id']}_{ti}", accept_multiple_files=True)
                                            if st.button("Подтвердить", key=f"clt_go_{cl['id']}_{ti}", use_container_width=True, type="primary"):
                                                if rt.strip():
                                                    t["done"] = True
                                                    t["completion_report"] = rt.strip()
                                                    fi_list = save_uploaded_files(uf, cl["id"], "task_report")
                                                    if fi_list:
                                                        t["completion_files"] = fi_list
                                                    st.session_state[show_key] = False
                                                    commit_and_rerun(st.session_state.crm_store, "Задача выполнена")
                                                else:
                                                    st.warning("Введите отчёт")
                                        ndd = st.date_input("Изменить срок:", value=parse_deadline(t.get("deadline", "")), format="DD/MM/YYYY", key=f"clt_dl_{cl['id']}_{ti}")
                                        if st.button("Обновить срок", key=f"clt_dl_btn_{cl['id']}_{ti}"):
                                            t["deadline"] = ndd.isoformat()
                                            commit_and_rerun(st.session_state.crm_store, "Срок обновлён")
                                    else:
                                        if t.get("completion_report"):
                                            st.caption(f"Отчёт: {t['completion_report']}")
                                        if t.get("completion_files"):
                                            render_file_thumbs(t["completion_files"], f"cltask_c_{cl['id']}_{ti}")
                    else:
                        st.caption("Задач по клиенту нет")

                    show_ct_key = f"show_ct_cl_{cl['id']}"
                    if st.button("Создать задачу по клиенту", key=f"btn_ct_cl_{cl['id']}", type="primary", use_container_width=True):
                        st.session_state[show_ct_key] = not st.session_state.get(show_ct_key, False)
                        st.rerun()
                    if st.session_state.get(show_ct_key, False):
                        with st.container(border=True):
                            ntt = st.selectbox("Тип:", ["Связаться", "Отправить заказ"], key=f"ct_cl_type_{cl['id']}")
                            ntm = st.selectbox("Ответственный:", mgrs, index=mgrs.index(cu) if cu in mgrs else 0, key=f"ct_cl_mgr_{cl['id']}")
                            ntd = st.date_input("Срок:", format="DD/MM/YYYY", key=f"ct_cl_d_{cl['id']}")
                            ne = {}
                            if ntt == "Отправить заказ":
                                ne["products"] = st.text_area("Товары", key=f"ct_cl_p_{cl['id']}")
                                ne["ship_addr"] = st.text_area("Адрес", key=f"ct_cl_a_{cl['id']}")
                                ne["receiver"] = st.text_input("Получатель", key=f"ct_cl_r_{cl['id']}")
                                ne["receiver_phone"] = format_phone(st.text_input("Тел. получателя", key=f"ct_cl_rp_{cl['id']}"))
                                ne["ship_pay"] = st.selectbox("Оплата", ["Включено в счёт", "Оплата при получении"], key=f"ct_cl_sp_{cl['id']}")
                                ne["tk_num"] = st.text_input("Трек-номер", key=f"ct_cl_tk_{cl['id']}")
                                ne["order_amount"] = st.number_input("Сумма (руб.)", min_value=0.0, step=100.0, key=f"ct_cl_oa_{cl['id']}")
                                ne["task_comment"] = st.text_area("Комментарии", key=f"ct_cl_c_{cl['id']}")
                            else:
                                ne["order_amount"] = 0
                                ne["task_comment"] = st.text_area("Комментарии", key=f"ct_cl_cs_{cl['id']}")
                            ntf = st.file_uploader("Файлы задачи:", key=f"ct_cl_file_{cl['id']}", accept_multiple_files=True)
                            if st.button("Создать", key=f"ct_cl_go_{cl['id']}", use_container_width=True, type="primary"):
                                at = auto_task_title(ntt, cl["name"], "")
                                tfi_list = save_uploaded_files(ntf, cl["id"], "task_file") if ntf else []
                                te = {"text": at, "deadline": ntd.isoformat(), "done": False, "type": ntt, "task_files": tfi_list, "manager": ntm, "completion_report": "", "completion_files": [], "deal_id": None}
                                te.update(ne)
                                cl.setdefault("tasks", []).append(te)
                                st.session_state[show_ct_key] = False
                                commit_and_rerun(st.session_state.crm_store, "Задача создана")

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
                            ec = st.selectbox("Категория", ["Дизайнер", "Строитель", "Дилер", "Покупатель"], index=["Дизайнер", "Строитель", "Дилер", "Покупатель"].index(cl.get('category', 'Покупатель')) if cl.get('category', 'Покупатель') in ["Дизайнер", "Строитель", "Дилер", "Покупатель"] else 3, key=f"ec_{cl['id']}")
                            em = st.selectbox("Ответственный:", mgrs, index=mgrs.index(cl.get('manager', '')) if cl.get('manager', '') in mgrs else 0, key=f"em_{cl['id']}")
                            if st.button("Сохранить", key=f"es_{cl['id']}", use_container_width=True, type="primary"):
                                cl['name'], cl['phone'], cl['email'], cl['address'], cl['discount'], cl['category'], cl['manager'] = en, format_phone(ep), ee, ea_val, int(ed), ec, em
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

                    st.markdown("---")
                    st.markdown(f"**Сделки клиента ({len(cl_deals)}):**")
                    if cl_deals:
                        for d in cl_deals:
                            is_dl_exp = st.session_state.expanded_deal_id == d["id"]
                            dl_tasks = [t for t in cl.get("tasks", []) if t.get("deal_id") == d["id"]]
                            dl_overdue = any(not t.get("done") and is_task_overdue(t) for t in dl_tasks)
                            dl_active = any(not t.get("done") for t in dl_tasks)
                            if dl_overdue:
                                dl_bg = "#FFEBEE"
                                dl_bc = "#C62828"
                            elif dl_active:
                                dl_bg = "#E8F5E9"
                                dl_bc = "#4CAF50"
                            else:
                                dl_bg = "#FFFFFF"
                                dl_bc = "#DCE0E5"
                            dl_label = f"{'  \u25BC' if is_dl_exp else '  \u25B6'} {d['title']} ({d['status']}) \u2014 {d.get('budget', 0):,.0f} руб. | Задач: {len(dl_tasks)}"
                            if d.get("deal_title"):
                                dl_label = f"{'  \u25BC' if is_dl_exp else '  \u25B6'} {d['title']} \u2014 {d['deal_title']} ({d['status']}) \u2014 {d.get('budget', 0):,.0f} руб. | Задач: {len(dl_tasks)}"
                            st.markdown(f"<style>.st-key-dl_btn_wrap_{d['id']} button {{ background-color: {dl_bg} !important; border-left-color: {dl_bc} !important; }}</style>", unsafe_allow_html=True)
                            with st.container(key=f"dl_btn_wrap_{d['id']}"):
                                if st.button(dl_label, key=f"dl_toggle_{d['id']}", use_container_width=True, type="primary" if is_dl_exp else "secondary"):
                                    if is_dl_exp:
                                        st.session_state.expanded_deal_id = None
                                    else:
                                        st.session_state.expanded_deal_id = d["id"]
                                        st.session_state.expanded_task_key = None
                                    st.rerun()
                            if is_dl_exp:
                                with st.container(border=True):
                                    st.markdown(f"**Бюджет:** {d.get('budget', 0):,.0f} руб.".replace(",", " "))
                                    ps = d.get("payment_status", "Не оплачено")
                                    inject_payment_container_css(d["id"], ps)
                                    with st.container(key=f"ps_wrap_{d['id']}"):
                                        new_ps = st.selectbox("Статус оплаты:", ["Не оплачено", "Оплачено"], index=0 if ps == "Не оплачено" else 1, key=f"ps_{d['id']}")
                                    if new_ps != ps:
                                        d["payment_status"] = new_ps
                                        commit_and_rerun(st.session_state.crm_store, "Статус оплаты обновлён")
                                    if d.get("manager"):
                                        st.markdown(f"**Ответственный:** {d.get('manager')}")
                                    st.markdown("---")
                                    if st.button("Создать задачу", key=f"ct_btn_{d['id']}", use_container_width=True, type="primary"):
                                        st.session_state[f"show_ct_{d['id']}"] = not st.session_state.get(f"show_ct_{d['id']}", False)
                                        st.rerun()
                                    if st.session_state.get(f"show_ct_{d['id']}", False):
                                        with st.container(border=True):
                                            ntt = st.selectbox("Тип:", ["Связаться", "Отправить заказ"], key=f"ct_type_{d['id']}")
                                            ntm = st.selectbox("Ответственный:", mgrs, index=mgrs.index(cu) if cu in mgrs else 0, key=f"ct_mgr_{d['id']}")
                                            ntd = st.date_input("Срок:", format="DD/MM/YYYY", key=f"ct_d_{d['id']}")
                                            ne = {}
                                            if ntt == "Отправить заказ":
                                                ne["products"] = st.text_area("Товары", key=f"ct_p_{d['id']}")
                                                ne["ship_addr"] = st.text_area("Адрес", key=f"ct_a_{d['id']}")
                                                ne["receiver"] = st.text_input("Получатель", key=f"ct_r_{d['id']}")
                                                ne["receiver_phone"] = format_phone(st.text_input("Тел. получателя", key=f"ct_rp_{d['id']}"))
                                                ne["ship_pay"] = st.selectbox("Оплата", ["Включено в счёт", "Оплата при получении"], key=f"ct_sp_{d['id']}")
                                                ne["tk_num"] = st.text_input("Трек-номер", key=f"ct_tk_{d['id']}")
                                                ne["order_amount"] = st.number_input("Сумма (руб.)", min_value=0.0, step=100.0, key=f"ct_oa_{d['id']}")
                                                ne["task_comment"] = st.text_area("Комментарии", key=f"ct_c_{d['id']}")
                                            else:
                                                ne["order_amount"] = 0
                                                ne["task_comment"] = st.text_area("Комментарии", key=f"ct_cs_{d['id']}")
                                            ntf = st.file_uploader("Файлы задачи:", key=f"ct_file_{d['id']}", accept_multiple_files=True)
                                            if st.button("Создать", key=f"ct_go_{d['id']}", use_container_width=True, type="primary"):
                                                at = auto_task_title(ntt, cl["name"], d.get("title", ""))
                                                tfi_list = save_uploaded_files(ntf, d["client_id"], "task_file") if ntf else []
                                                te = {"text": at, "deadline": ntd.isoformat(), "done": False, "type": ntt, "task_files": tfi_list, "manager": ntm, "completion_report": "", "completion_files": [], "deal_id": d["id"]}
                                                te.update(ne)
                                                cl.setdefault("tasks", []).append(te)
                                                st.session_state[f"show_ct_{d['id']}"] = False
                                                commit_and_rerun(st.session_state.crm_store, "Задача создана")
                                    st.markdown("---")
                                    dl_files_col, dl_upload_col = st.columns(2)
                                    with dl_files_col:
                                        st.markdown("**Файлы сделки:**")
                                        render_file_thumbs(d.get("deal_files", []), f"deal_file_{d['id']}", allow_delete=True, entity_id=d["id"])
                                    with dl_upload_col:
                                        st.markdown("**Загрузить файлы:**")
                                        df_ver = st.session_state.deal_file_uploader_ver.get(d["id"], 0)
                                        udf = st.file_uploader("Выберите файлы:", key=f"df_up_{d['id']}_{df_ver}", accept_multiple_files=True, label_visibility="collapsed")
                                        if st.button("Загрузить", key=f"df_btn_{d['id']}", use_container_width=True):
                                            if udf:
                                                fi_list = save_uploaded_files(udf, d["client_id"], "deal_file")
                                                if fi_list:
                                                    d.setdefault("deal_files", []).extend([{"file_path": fi["path"], "file_name": fi["name"]} for fi in fi_list])
                                                    st.session_state.deal_file_uploader_ver[d["id"]] = df_ver + 1
                                                    save_data(st.session_state.crm_store)
                                                    st.toast("Файлы загружены", icon="\U0001F4C1")
                                                    st.rerun()
                                            else:
                                                st.warning("Выберите файл(ы)")
                                    render_task_files_in_deal(cl, d["id"], f"deal_{d['id']}")
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
                                            st.session_state[dc_clr_key] = True
                                            commit_and_rerun(st.session_state.crm_store, "Комментарий добавлен")
                                        else:
                                            st.warning("Введите текст")
                                    st.markdown("---")
                                    current_status = d.get("status", "Новый")
                                    if current_status == "Новый":
                                        if st.button("Взять в работу", key=f"deal_next_{d['id']}", use_container_width=True, type="primary"):
                                            d["status"] = "В работе"
                                            d["manager"] = cu
                                            commit_and_rerun(st.session_state.crm_store, "Сделка взята в работу")
                                    elif current_status == "В работе":
                                        if st.button("Закрыть сделку", key=f"deal_close_{d['id']}", use_container_width=True, type="primary"):
                                            close_deal_dialog(d["id"])
                                    elif current_status == "Сделка закрыта":
                                        if st.button("Вернуть в работу", key=f"deal_reopen_{d['id']}", use_container_width=True):
                                            d["status"] = "В работе"
                                            commit_and_rerun(st.session_state.crm_store, "Сделка возвращена")
                                        if st.button("В архив", key=f"deal_archive_{d['id']}", use_container_width=True, type="primary"):
                                            d["status"] = "Архив"
                                            commit_and_rerun(st.session_state.crm_store, "Сделка в архиве")
                                    elif current_status == "Архив":
                                        if st.button("Вернуть в работу", key=f"arch_reopen_{d['id']}", use_container_width=True):
                                            d["status"] = "В работе"
                                            commit_and_rerun(st.session_state.crm_store, "Сделка возвращена")
                                        if st.button("В закрытые", key=f"arch_toclosed_{d['id']}", use_container_width=True, type="primary"):
                                            d["status"] = "Сделка закрыта"
                                            commit_and_rerun(st.session_state.crm_store, "Сделка в закрытых")
                                    if st.session_state.user_role == "admin":
                                        st.markdown("---")
                                        if st.button("Удалить сделку", key=f"deal_del_{d['id']}", use_container_width=True):
                                            st.session_state.crm_store["deals"] = [x for x in st.session_state.crm_store["deals"] if x["id"] != d["id"]]
                                            st.session_state.expanded_deal_id = None
                                            commit_and_rerun(st.session_state.crm_store, "Сделка удалена")
                                    st.markdown("---")
                                    st.markdown(f"**Задачи сделки ({len(dl_tasks)}):**")
                                    if dl_tasks:
                                        dl_tasks.sort(key=lambda t: (t.get("done", False), get_task_sort_date(t)))
                                        for ti, t in enumerate(dl_tasks):
                                            task_key = f"{d['id']}_{ti}"
                                            is_tk_exp = st.session_state.expanded_task_key == task_key
                                            tk_done = t.get("done", False)
                                            tk_overdue = is_task_overdue(t)
                                            if tk_done:
                                                tk_bg = "#F5F6F8"
                                                tk_bc = "#C9CFD7"
                                            elif tk_overdue:
                                                tk_bg = "#FFEBEE"
                                                tk_bc = "#C62828"
                                            else:
                                                tk_bg = "#E8F5E9"
                                                tk_bc = "#4CAF50"
                                            tk_status = "\u2705" if tk_done else ("\u26A0" if tk_overdue else "\u23F3")
                                            tk_label = f"{'    \u25BC' if is_tk_exp else '    \u25B6'} {tk_status} {t.get('type', 'Связаться')} \u2014 {t.get('text', '')} | {format_date(t.get('deadline', ''))}"
                                            st.markdown(f"<style>.st-key-tk_btn_wrap_{task_key} button {{ background-color: {tk_bg} !important; border-left-color: {tk_bc} !important; }}</style>", unsafe_allow_html=True)
                                            with st.container(key=f"tk_btn_wrap_{task_key}"):
                                                if st.button(tk_label, key=f"tk_toggle_{task_key}", use_container_width=True, type="primary" if is_tk_exp else "secondary"):
                                                    st.session_state.expanded_task_key = None if is_tk_exp else task_key
                                                    st.rerun()
                                            if is_tk_exp:
                                                with st.container(border=True):
                                                    st.markdown(f"**Тип:** {t.get('type', 'Связаться')}")
                                                    st.markdown(f"**Срок:** {format_date(t.get('deadline', ''))}")
                                                    st.markdown(f"**Ответственный:** {t.get('manager', '\u2014')}")
                                                    if t.get('products'):
                                                        st.markdown(f"**Товары:** {t['products']}")
                                                    if t.get('ship_addr'):
                                                        st.markdown(f"**Адрес:** {t['ship_addr']}")
                                                    if t.get('receiver'):
                                                        st.markdown(f"**Получатель:** {t['receiver']} ({t.get('receiver_phone', '')})")
                                                    if t.get('ship_pay'):
                                                        st.markdown(f"**Оплата:** {t['ship_pay']}")
                                                    if t.get('tk_num'):
                                                        st.markdown(f"**Трек:** `{t['tk_num']}`")
                                                    if t.get('order_amount', 0) > 0:
                                                        st.markdown(f"**Сумма:** {t['order_amount']:,.0f} руб.".replace(",", " "))
                                                    if t.get('task_comment'):
                                                        st.markdown(f"**Комментарии:** {t['task_comment']}")
                                                    if t.get("task_files"):
                                                        st.markdown("**Файлы задачи:**")
                                                        render_file_thumbs(t["task_files"], f"dt_file_{d['id']}_{ti}")
                                                    if t.get('type', 'Связаться') == "Отправить заказ":
                                                        render_deal_files_in_task(d, f"dt_{d['id']}_{ti}")
                                                    st.markdown("---")
                                                    if not tk_done:
                                                        render_print_button(t, cl, t.get('type', 'Связаться'), format_date(t.get('deadline', '')), f"dt_{d['id']}_{ti}")
                                                        st.markdown("---")
                                                        show_key = f"show_dt_complete_{d['id']}_{ti}"
                                                        if st.button("Выполнить задачу", key=f"btn_dt_complete_{d['id']}_{ti}", type="primary", use_container_width=True):
                                                            st.session_state[show_key] = not st.session_state.get(show_key, False)
                                                            st.rerun()
                                                        if st.session_state.get(show_key, False):
                                                            rt = st.text_input("Отчёт (обязательно):", key=f"dt_rt_{d['id']}_{ti}")
                                                            uf = st.file_uploader("Файлы/фото отчёта:", key=f"dt_uf_{d['id']}_{ti}", accept_multiple_files=True)
                                                            if st.button("Подтвердить выполнение", key=f"dt_go_{d['id']}_{ti}", use_container_width=True, type="primary"):
                                                                if rt.strip():
                                                                    t["done"] = True
                                                                    t["completion_report"] = rt.strip()
                                                                    fi_list = save_uploaded_files(uf, d["client_id"], "task_report")
                                                                    if fi_list:
                                                                        t["completion_files"] = fi_list
                                                                    st.session_state[show_key] = False
                                                                    commit_and_rerun(st.session_state.crm_store, "Задача выполнена")
                                                                else:
                                                                    st.warning("Введите отчёт")
                                                        st.markdown("---")
                                                        cd2 = parse_deadline(t.get("deadline", ""))
                                                        ndd = st.date_input("Изменить срок:", value=cd2, format="DD/MM/YYYY", key=f"dt_dl_{d['id']}_{ti}")
                                                        if st.button("Обновить срок", key=f"dt_dl_btn_{d['id']}_{ti}"):
                                                            t["deadline"] = ndd.isoformat()
                                                            commit_and_rerun(st.session_state.crm_store, "Срок обновлён")
                                                    else:
                                                        if t.get("completion_report"):
                                                            st.caption(f"Отчёт: {t['completion_report']}")
                                                        if t.get("completion_files"):
                                                            st.markdown("**Файлы отчёта:**")
                                                            render_file_thumbs(t["completion_files"], f"dt_cfile_{d['id']}_{ti}")
                                    else:
                                        st.caption("Нет задач")
                    else:
                        if not cl_deals:
                            st.caption("Сделок нет")
    else:
        st.info("База клиентов пуста. Создайте первого клиента.")

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
    mf = st.selectbox("Ответственный", ["Мои задачи", "Все"] + mgrs, index=0)
    di = {d["id"]: d for d in st.session_state.crm_store.get("deals", [])}
    aat = []
    for cl in st.session_state.crm_store.get("clients", []):
        for ti, tk in enumerate(cl.get("tasks", [])):
            if not tk.get("done", False):
                tm = tk.get("manager", "")
                if mf == "Мои задачи":
                    if tm and tm != cu:
                        continue
                elif mf != "Все":
                    if tm != mf:
                        continue
                task_deal = di.get(tk.get("deal_id"))
                mdt = task_deal["title"] if task_deal else ""
                aat.append({"client_id": cl["id"], "client_name": cl["name"], "client_phone": cl["phone"], "deal_title": mdt, "sort_date": get_task_sort_date(tk), "deadline_str": tk.get("deadline", ""), "type": tk.get("type", "Связаться"), "text": tk.get("text", ""), "task_obj": tk, "task_idx": ti, "client_obj": cl})
    aat.sort(key=lambda x: x["sort_date"])
    tt_list = [t for t in aat if t["sort_date"] <= now_time.date()]
    ft_list = [t for t in aat if t["sort_date"] > now_time.date()]
    def render_task_block(t, sk):
        task = t["task_obj"]
        cl = t["client_obj"]
        tp = task.get("type", "Связаться")
        io_ = is_task_overdue(task)
        sl = "Просрочено" if io_ else ("Сегодня" if t["sort_date"] == now_time.date() else "Срок")
        fd = format_date(t["deadline_str"])
        with st.expander(f"{fd} \u2014 {t['client_name']} \u2014 {t['type']}", expanded=False, key=f"tb_{sk}_{t['client_id']}_{t['task_idx']}"):
            st.markdown(f"**{sl}** \u2014 {fd} | {tp}")
            st.markdown(f"\U0001F464 **{t['client_name']}** ({t['client_phone']})")
            if tp == "Отправить заказ":
                st.markdown(f"Товары: {task.get('products', '')}")
                st.markdown(f"Адрес: {task.get('ship_addr', '')}")
                st.markdown(f"Получатель: {task.get('receiver', '')} ({task.get('receiver_phone', '')})")
                if task.get('order_amount', 0) > 0:
                    st.markdown(f"Сумма: {task['order_amount']:,.0f} руб.".replace(",", " "))
                if task.get('tk_num'):
                    st.markdown(f"Трек: `{task['tk_num']}`")
                task_deal = di.get(task.get("deal_id"))
                render_deal_files_in_task(task_deal, f"task_{sk}_{t['client_id']}_{t['task_idx']}")
            if task.get('task_comment'):
                st.markdown(f"**Комментарии:** {task['task_comment']}")
            st.markdown(f"**Ответственный:** {task.get('manager', '\u2014')}")
            render_print_button(task, cl, tp, fd, f"task_{sk}_{t['client_id']}_{t['task_idx']}")
            with st.expander("Выполнить задачу", expanded=False):
                rt = st.text_input("Отчёт:", key=f"rt_{sk}_{t['client_id']}_{t['task_idx']}")
                uf = st.file_uploader("Файлы/фото отчёта:", key=f"uf_{sk}_{t['client_id']}_{t['task_idx']}", accept_multiple_files=True)
                cn = st.checkbox("Создать следующую задачу", key=f"cn_{sk}_{t['client_id']}_{t['task_idx']}")
                ne = {}
                ntd = None
                ntt = None
                if cn:
                    ntt = st.selectbox("Тип:", ["Связаться", "Отправить заказ"], key=f"nt_type_{sk}_{t['client_id']}_{t['task_idx']}")
                    ntm = st.selectbox("Ответственный:", mgrs, index=mgrs.index(cu) if cu in mgrs else 0, key=f"nt_mgr_{sk}_{t['client_id']}_{t['task_idx']}")
                    if ntt == "Отправить заказ":
                        ne["products"] = st.text_area("Товары", key=f"nt_p_{sk}_{t['client_id']}_{t['task_idx']}")
                        ne["ship_addr"] = st.text_area("Адрес", key=f"nt_a_{sk}_{t['client_id']}_{t['task_idx']}")
                        ne["receiver"] = st.text_input("Получатель", key=f"nt_r_{sk}_{t['client_id']}_{t['task_idx']}")
                        ne["receiver_phone"] = format_phone(st.text_input("Тел. получателя", key=f"nt_rp_{sk}_{t['client_id']}_{t['task_idx']}"))
                        ne["ship_pay"] = st.selectbox("Оплата", ["Включено в счёт", "Оплата при получении"], key=f"nt_sp_{sk}_{t['client_id']}_{t['task_idx']}")
                        ne["tk_num"] = st.text_input("Трек-номер", key=f"nt_tk_{sk}_{t['client_id']}_{t['task_idx']}")
                        ne["order_amount"] = st.number_input("Сумма (руб.)", min_value=0.0, step=100.0, key=f"nt_oa_{sk}_{t['client_id']}_{t['task_idx']}")
                        ne["task_comment"] = st.text_area("Комментарии", key=f"nt_c_{sk}_{t['client_id']}_{t['task_idx']}")
                    else:
                        ne["order_amount"] = 0
                        ne["task_comment"] = st.text_area("Комментарии", key=f"nt_cs_{sk}_{t['client_id']}_{t['task_idx']}")
                    ntd = st.date_input("Дата новой задачи", format="DD/MM/YYYY", key=f"nt_d_{sk}_{t['client_id']}_{t['task_idx']}")
                if st.button("Подтвердить выполнение", key=f"cbtn_{sk}_{t['client_id']}_{t['task_idx']}", use_container_width=True, type="primary"):
                    if rt.strip():
                        task["done"] = True
                        task["completion_report"] = rt.strip()
                        fi_list = save_uploaded_files(uf, t["client_id"], "task_report")
                        if fi_list:
                            task["completion_files"] = fi_list
                        if cn and ntt:
                            at = auto_task_title(ntt, t['client_name'], t['deal_title'])
                            te = {"text": at, "deadline": ntd.isoformat(), "done": False, "type": ntt, "task_files": [], "manager": ntm, "completion_report": "", "completion_files": [], "deal_id": task.get("deal_id")}
                            te.update(ne)
                            cl.setdefault("tasks", []).append(te)
                        commit_and_rerun(st.session_state.crm_store, "Задача выполнена")
                    else:
                        st.warning("Введите отчёт")
    task_l, task_r = st.columns(2)
    with task_l:
        with st.container(border=True):
            st.subheader(f"На сегодня ({len(tt_list)})")
            if tt_list:
                for t in tt_list:
                    render_task_block(t, "today")
            else:
                st.success("Все задачи на сегодня закрыты.")
    with task_r:
        with st.container(border=True):
            st.subheader(f"Предстоящие ({len(ft_list)})")
            if ft_list:
                for t in ft_list:
                    render_task_block(t, "future")
            else:
                st.caption("План на будущие дни пуст.")

elif st.session_state.active_tab == "Внутренние задачи":
    sub1, sub2, sub3 = st.tabs(["Задачи сотрудникам", "Чат", "Шпаргалка"])

    with sub1:
        all_users = [u.get("name", u["login"]) for u in st.session_state.crm_store.get("users", [])]
        col_a, col_b = st.columns([3, 1])
        with col_a:
            itf = st.selectbox("Фильтр:", ["Мне", "От меня", "Все"], key="itf_filter")
        with col_b:
            st.write("")
            if st.button("Новая задача", use_container_width=True, type="primary"):
                st.session_state.show_new_itask = not st.session_state.get("show_new_itask", False)
                st.rerun()
        if st.session_state.get("show_new_itask", False):
            with st.container(border=True):
                it_title = st.text_input("Заголовок:", key="it_title")
                it_desc = st.text_area("Описание:", key="it_desc")
                it_to = st.selectbox("Кому:", all_users, index=all_users.index(cu) if cu in all_users else 0, key="it_to")
                it_dl = st.date_input("Срок:", format="DD/MM/YYYY", key="it_dl")
                it_pri = st.selectbox("Приоритет:", ["Обычный", "Важно", "Срочно"], key="it_pri")
                if st.button("Создать задачу", key="it_create", use_container_width=True, type="primary"):
                    if it_title.strip():
                        st.session_state.crm_store.setdefault("internal_tasks", []).append({
                            "id": str(uuid.uuid4())[:8],
                            "title": it_title.strip(),
                            "description": it_desc.strip(),
                            "assigned_to": it_to,
                            "created_by": cu,
                            "deadline": it_dl.isoformat(),
                            "priority": it_pri,
                            "done": False,
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        st.session_state.show_new_itask = False
                        commit_and_rerun(st.session_state.crm_store, "Задача создана")
                    else:
                        st.warning("Введите заголовок")
        itasks = st.session_state.crm_store.get("internal_tasks", [])
        filtered_it = []
        for t in itasks:
            if itf == "Мне":
                if t.get("assigned_to") == cu:
                    filtered_it.append(t)
            elif itf == "От меня":
                if t.get("created_by") == cu:
                    filtered_it.append(t)
            else:
                filtered_it.append(t)
        filtered_it.sort(key=lambda x: (x.get("done", False), x.get("deadline", "")))
        for t in filtered_it:
            pri_color = "#C62828" if t.get("priority") == "Срочно" else ("#E65100" if t.get("priority") == "Важно" else "#2C3E50")
            done_mark = "\u2705" if t.get("done") else "\u2B1C"
            with st.expander(f"{done_mark} {t['title']} \u2014 {t.get('assigned_to', '')} | {format_date(t.get('deadline', ''))}", expanded=False, key=f"itask_{t['id']}"):
                st.markdown(f"**От:** {t.get('created_by', '')} \u2192 **Кому:** {t.get('assigned_to', '')}")
                st.markdown(f"**Срок:** {format_date(t.get('deadline', ''))} | **Приоритет:** <span style='color:{pri_color};font-weight:600'>{t.get('priority', '')}</span>", unsafe_allow_html=True)
                if t.get("description"):
                    st.markdown(f"**Описание:** {t['description']}")
                st.markdown(f"**Создано:** {t.get('created_at', '')}")
                if not t.get("done"):
                    if st.button("Выполнить", key=f"it_done_{t['id']}", use_container_width=True, type="primary"):
                        t["done"] = True
                        t["done_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        commit_and_rerun(st.session_state.crm_store, "Задача выполнена")
                else:
                    st.caption(f"Выполнена: {t.get('done_at', '')}")
                    if st.button("Вернуть в работу", key=f"it_reopen_{t['id']}", use_container_width=True):
                        t["done"] = False
                        t.pop("done_at", None)
                        commit_and_rerun(st.session_state.crm_store, "Задача возвращена")
                if t.get("created_by") == cu or st.session_state.user_role == "admin":
                    if st.button("Удалить", key=f"it_del_{t['id']}", use_container_width=True):
                        st.session_state.crm_store["internal_tasks"] = [x for x in itasks if x["id"] != t["id"]]
                        commit_and_rerun(st.session_state.crm_store, "Задача удалена")
        if not filtered_it:
            st.caption("Нет задач")

    with sub2:
        chat = st.session_state.crm_store.get("chat_messages", [])
        chat_container = st.container(height=400)
        with chat_container:
            for msg in chat[-100:]:
                is_me = msg.get("user") == cu
                cls = "chat-msg-me" if is_me else "chat-msg-other"
                st.markdown(f"""
                <div class="chat-msg {cls}">
                    <div style="font-size:0.75rem; opacity:0.7; margin-bottom:2px;">{msg.get('user', '')} \u2014 {msg.get('time', '')}</div>
                    {msg.get('text', '')}
                </div>
                """, unsafe_allow_html=True)
            if not chat:
                st.caption("Сообщений пока нет")
        chat_clr = st.session_state.get("chat_clr")
        if chat_clr:
            st.session_state["chat_input"] = ""
            st.session_state["chat_clr"] = False
        msg_text = st.text_input("Сообщение:", key="chat_input", placeholder="Введите сообщение...")
        if st.button("Отправить", key="chat_send", use_container_width=True, type="primary"):
            if msg_text.strip():
                st.session_state.crm_store.setdefault("chat_messages", []).append({
                    "id": str(uuid.uuid4())[:8],
                    "user": cu,
                    "text": msg_text.strip(),
                    "time": datetime.now().strftime("%d.%m.%Y %H:%M")
                })
                st.session_state["chat_clr"] = True
                commit_and_rerun(st.session_state.crm_store)
            else:
                st.warning("Введите текст")

    with sub3:
        qa_entries = st.session_state.crm_store.get("qa_entries", [])
        qa_search = st.text_input("Поиск по шпаргалке:", key="qa_search", placeholder="Введите вопрос или ключевое слово...").strip().lower()
        if st.session_state.user_role == "admin":
            with st.expander("Добавить запись", expanded=False):
                qa_q = st.text_input("Вопрос:", key="qa_q")
                qa_a = st.text_area("Ответ:", key="qa_a")
                qa_cat = st.text_input("Категория:", key="qa_cat", placeholder="Напр: Доставка, Оплата, Продукция...")
                if st.button("Добавить", key="qa_add", use_container_width=True, type="primary"):
                    if qa_q.strip() and qa_a.strip():
                        st.session_state.crm_store.setdefault("qa_entries", []).append({
                            "id": str(uuid.uuid4())[:8],
                            "question": qa_q.strip(),
                            "answer": qa_a.strip(),
                            "category": qa_cat.strip() or "Общее",
                            "created_by": cu,
                            "created_at": datetime.now().strftime("%Y-%m-%d")
                        })
                        commit_and_rerun(st.session_state.crm_store, "Запись добавлена")
                    else:
                        st.warning("Заполните вопрос и ответ")
        filtered_qa = []
        for qa in qa_entries:
            if qa_search:
                ct = f"{qa.get('question', '')} {qa.get('answer', '')} {qa.get('category', '')}".lower()
                if qa_search not in ct:
                    continue
            filtered_qa.append(qa)
        qa_cats = sorted(set(qa.get("category", "Общее") for qa in filtered_qa))
        for cat in qa_cats:
            st.markdown(f"**{cat}**")
            for qa in [q for q in filtered_qa if q.get("category", "Общее") == cat]:
                with st.container(border=True):
                    st.markdown(f"<div class='qa-card'><b>Q: {qa.get('question', '')}</b><br><br>{qa.get('answer', '')}</div>", unsafe_allow_html=True)
                    if st.session_state.user_role == "admin":
                        if st.button("Удалить", key=f"qa_del_{qa['id']}", use_container_width=True):
                            st.session_state.crm_store["qa_entries"] = [x for x in qa_entries if x["id"] != qa["id"]]
                            commit_and_rerun(st.session_state.crm_store, "Запись удалена")
        if not filtered_qa:
            st.caption("Записей не найдено")
