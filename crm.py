import streamlit as st
import streamlit.components.v1 as components
import json, os, re, urllib.parse, requests, hashlib, base64, csv, io, secrets, threading, uuid
import extra_streamlit_components as stx
from datetime import datetime
from collections import defaultdict

st.set_page_config(page_title="Айплинт CRM", layout="wide")

# Системные функции криптографии паролей сотрудников
def hash_password(pwd, salt=None):
    if not pwd: return ""
    if salt is None: salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + pwd.strip()).encode()).hexdigest()
    return f"{salt}:{h}"

def verify_password(pwd, stored):
    if not stored: return False
    if ":" in stored:
        salt, h = stored.split(":")
        return hashlib.sha256((salt + pwd.strip()).encode()).hexdigest() == h
    return hashlib.sha256(pwd.strip().encode()).hexdigest() == stored

# Функция проверки мгновенного автоматического входа из памяти устройства
def check_auto_login():
    if st.session_state.get("authenticated"):
        return True
    if "local_auth_token" in st.query_params:
        token = st.query_params["local_auth_token"]
        for u in st.session_state.crm_store.get("users", []):
            if u.get("auth_token") == token:
                st.session_state.authenticated = True
                st.session_state.user_role = u["role"]
                st.session_state.user_login = u["login"]
                st.session_state.user_name = u.get("name", u["login"])
                return True
    return False

# Экран авторизации (Первичный вход или быстрый вход по PIN)
def render_auth_screen():
    st.markdown("<h2 style='text-align: center; margin-top: 3rem;'>Айплинт CRM</h2>", unsafe_allow_html=True)
    
    # Считываем сохраненную сессию из памяти телефона/ПК с помощью JS-моста
    if not st.session_state.get("authenticated") and "local_auth_token" not in st.query_params and "local_user" not in st.query_params and "_js_checked" not in st.query_params:
        st.components.v1.html("""
        <script>
            var token = localStorage.getItem('crm_token_v6');
            var user = localStorage.getItem('crm_user_v6');
            if (token) {
                window.parent.location.href = window.parent.location.pathname + "?local_auth_token=" + token;
            } else if (user) {
                window.parent.location.href = window.parent.location.pathname + "?local_user=" + user;
            } else {
                window.parent.location.href = window.parent.location.pathname + "?_js_checked=1";
            }
        </script>
        """, height=0)
        st.stop()

    saved_login = st.query_params.get("local_user", "")
    col1, col2, col3 = st.columns(3)
    with col2:
        with st.container(border=True):
            if saved_login:
                st.markdown(f"<p style='text-align:center; font-size:0.95rem; color:#7F8C9A;'>Быстрый вход для: <b>{saved_login}</b></p>", unsafe_allow_html=True)
                
                # HTML + JS компонент цифрового ввода PIN-кода. 
                # inputmode="numeric" и pattern="[0-9]*" принудительно открывают числовую клавиатуру на смартфонах
                pin_html = f"""
                <div style="text-align:center;">
                    <input type="password" id="numeric_pin" maxlength="4" inputmode="numeric" pattern="[0-9]*" placeholder="••••" 
                           style="width:100%; max-width:200px; text-align:center; font-size:1.5rem; padding:10px; border:1.5px solid #DCE0E5; border-radius:10px; margin-bottom:15px; font-family:inherit;">
                    <br>
                    <button id="sub_btn" style="width:48%; padding:10px; background:#bc1661; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">Войти</button>
                    <button id="chg_btn" style="width:48%; padding:10px; background:transparent; color:#bc1661; border:1px solid #C9CFD7; border-radius:10px; cursor:pointer;">Сменить</button>
                </div>
                <script>
                    var input = document.getElementById('numeric_pin');
                    input.focus();
                    input.onkeydown = function(e) {{
                        if (e.key === 'Enter' || e.keyCode === 13) {{
                            e.preventDefault();
                            document.getElementById('sub_btn').click();
                        }}
                    }};
                    document.getElementById('sub_btn').onclick = function() {{
                        window.parent.location.href = window.parent.location.pathname + "?local_user={saved_login}&submit_pin=" + input.value;
                    }};
                    document.getElementById('chg_btn').onclick = function() {{
                        localStorage.removeItem('crm_user_v6');
                        localStorage.removeItem('crm_token_v6');
                        window.parent.location.href = window.parent.location.pathname;
                    }};
                </script>
                """
                st.components.v1.html(pin_html, height=120)
                
                if "submit_pin" in st.query_params:
                    entered_pin = st.query_params["submit_pin"]
                    if match_and_authorize(saved_login, entered_pin):
                        st.rerun()
            else:
                st.markdown("<p style='text-align:center; color:#7F8C9A;'>Первичный вход в CRM</p>", unsafe_allow_html=True)
                with st.form("initial_form"):
                    iu = st.text_input("Логин:", placeholder="Введите логин")
                    ip = st.text_input("Пароль:", type="password", placeholder="Введите пароль")
                    rem = st.checkbox("Оставаться в системе", value=True, help="Включает быстрый вход по PIN-коду при повторном визите")
                    if st.form_submit_button("Войти в систему", use_container_width=True, type="primary"):
                        if match_and_authorize(iu, ip, rem):
                            st.rerun()
    st.stop()
def match_and_authorize(login, secret, remember=True):
    if not secret:
        st.error("Поле не может быть пустым.")
        return False
    user_found = None
    for u in st.session_state.crm_store["users"]:
        if u["login"] == login.strip():
            if verify_password(secret, u["password"]) or (u.get("pin") and secret.strip() == u["pin"]):
                user_found = u
                break
    if user_found:
        st.session_state.authenticated = True
        st.session_state.user_role = user_found["role"]
        st.session_state.user_login = user_found["login"]
        st.session_state.user_name = user_found.get("name", user_found["login"])
        
        _token = secrets.token_hex(32)
        user_found["auth_token"] = _token
        save_data(st.session_state.crm_store)
        
        # Если чекбокс активен — сохраняем логин для быстрого PIN-входа, иначе — только токен
        js_user_save = f"localStorage.setItem('crm_user_v6', '{user_found['login']}');" if remember else "localStorage.removeItem('crm_user_v6');"
        st.components.v1.html(f"""
        <script>
            {js_user_save}
            localStorage.setItem('crm_token_v6', '{_token}');
            window.parent.location.href = window.parent.location.pathname;
        </script>
        """, height=0)
        st.stop()
        return True
    else:
        st.error("Неверный логин, пароль или PIN-код.")
        return False

# Глобальные кастомные стили дизайна (Темизация, кнопки, поля ввода, карточки)
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

# JavaScript-инъекция для буфера обмена и лайтбокса
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
</script>
""", height=0)

FILE_NAME = "web_crm_database_v2.json"
YANDEX_API_URL = "https://yandex.net"
MAX_URL = "https://max.ru"
MAX_NUMBER = "+79003293300"
CATEGORIES = ["Не определён", "Дизайнер", "Строитель", "Дилер", "Покупатель"]
TASK_TYPES = ["Связаться", "Отправить заказ", "Отправить образцы"]
SHIP_PAY_OPTIONS = ["", "Включено в счёт", "Клиентом при получении"]

raw_token = st.secrets.get("YANDEX_DISK_TOKEN", "")
YANDEX_TOKEN = raw_token.strip().strip('"').strip("'") if isinstance(raw_token, str) else ""

def yandex_headers(): return {"Authorization": f"OAuth {YANDEX_TOKEN}", "Accept": "application/json"}
def check_cloud_status():
    if not YANDEX_TOKEN: return False
    try: return requests.get(YANDEX_API_URL, headers=yandex_headers(), timeout=5).status_code == 200
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
        db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}], "_migrated": "v2", "internal_tasks": [], "chat_messages": [], "qa_entries": [], "suppliers": []}
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

def save_uploaded_file(u_file, c_id, prefix=""):
    if u_file is None: return None
    b = u_file.getvalue()
    file_hash = hashlib.sha256(b).hexdigest()
    for c in st.session_state.crm_store.get("clients", []):
        for f in c.get("client_files", []):
            if f.get("file_hash") == file_hash and file_hash: return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
        for t in c.get("tasks", []):
            for f in t.get("task_files", []):
                if f.get("file_hash") == file_hash and file_hash: return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
            for f in t.get("completion_files", []):
                if f.get("file_hash") == file_hash and file_hash: return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
    for d in st.session_state.crm_store.get("deals", []):
        for f in d.get("deal_files", []):
            if f.get("file_hash") == file_hash and file_hash: return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
        for f in d.get("close_files", []):
            if f.get("file_hash") == file_hash and file_hash: return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
    name = f"{c_id}_{prefix}_{int(datetime.now().timestamp())}_{u_file.name}"
    if YANDEX_TOKEN:
        rp = f"CRM_NE_TROGAT/uploads/{name}"
        if upload_file_to_yandex(b, name): return {"path": rp, "name": u_file.name, "file_hash": file_hash}
        st.warning("Не удалось загрузить на Диск, файл сохранён локально")
    os.makedirs("uploads", exist_ok=True)
    lp = f"uploads/{name}"
    with open(lp, "wb") as f: f.write(b)
    return {"path": lp, "name": u_file.name, "file_hash": file_hash}

def save_uploaded_files(files, c_id, prefix=""):
    if files is None: return []
    if not isinstance(files, list): files = [files]
    return [fi for fi in (save_uploaded_file(f, c_id, prefix) for f in files) if fi]

def normalize_file_list(fi_list): return [{"file_path": fi["path"], "file_name": fi["name"], "file_hash": fi.get("file_hash", "")} for fi in fi_list]
def normalize_remote_path(fp):
    if not fp: return None
    if fp.startswith("CRM_NE_TROGAT"): return fp
    elif fp.startswith("uploads/"): return f"CRM_NE_TROGAT/{fp}"
    else: return f"CRM_NE_TROGAT/uploads/{os.path.basename(fp)}"

def export_clients_csv():
    o = io.StringIO()
    w = csv.writer(o, delimiter=";")
    w.writerow(["ID", "ФИО", "Телефон", "Email", "Адрес", "Категория", "Скидка %", "Ответственный"])
    for c in st.session_state.crm_store["clients"]:
        w.writerow([c["id"], c["name"], c["phone"], c.get("email", ""), c.get("address", ""), c.get("category", ""), c.get("discount", 0), c.get("manager", "")])
    return ("\uFEFF" + o.getvalue()).encode("utf-8")

def parse_deadline(ds):
    if not ds: return datetime.now().date()
    try: return datetime.strptime(ds[:10], "%Y-%m-%d").date()
    except: return datetime.now().date()

def is_task_overdue(task):
    if task.get("done") or not task.get("deadline"): return False
    now = datetime.now()
    try:
        dl = task.get("deadline", "")
        if len(dl) == 10: deadline = datetime.strptime(dl, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        else: deadline = datetime.strptime(dl[:16], "%Y-%m-%d %H:%M")
        return deadline Создано: {dt.strftime("%d.%m.%Y %H:%M")}</div>'
    except:
        try:
            dt = datetime.strptime(cd[:10], "%Y-%m-%d")
            return f'<div class="created-date">Создано: {dt.strftime("%d.%m.%Y")}</div>'
        except: return ""

def get_managers_list(): return [u.get("name", u["login"]) for u in st.session_state.crm_store.get("users", []) if u.get("role") != "admin"]
# Рендеринг интерфейсных хелперов
def render_scroll_restore(key): st.components.v1.html(f"""<script>(function(){{var k='crm_scroll_'+window.location.pathname;try{{var s=window.parent.sessionStorage.getItem(k);if(s){{window.parent.scrollTo(0,parseInt(s));window.parent.sessionStorage.removeItem(k);}}}}catch(e){{}}}})();</script>""", height=0)
def save_scroll_and_rerun(key=None): st.components.v1.html("""<script>(function(){try{window.parent.sessionStorage.setItem('crm_scroll_'+window.parent.location.pathname,window.parent.scrollY);}catch(e){}})();</script>""", height=0); st.rerun()

def render_phone_inline(phone, uid):
    cph = re.sub(r"\D", "", phone)
    if cph.startswith("8") and len(cph) == 11: cph = "7" + cph[1:]
    elif not cph: cph = "79990000000"
    btn_id = f"ph_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f'<div class="phone-action-group" style="padding:4px 0;"><span style="font-size:1rem;font-weight:600;color:#2C3E50;">{phone}</span><button onclick="window.crmCopy(\'{phone}\',\'{btn_id}\')" class="phone-btn" id="{btn_id}" title="Скопировать">📋</button><a href="tel:+{cph}" class="phone-btn" title="Позвонить">📞</a></div>', unsafe_allow_html=True)

def render_extra_phone_inline(phone, name, role, uid):
    cph = re.sub(r"\D", "", phone)
    if cph.startswith("8") and len(cph) == 11: cph = "7" + cph[1:]
    elif not cph: cph = "79990000000"
    info = f"{phone} — {name} ({role})" if name else phone
    btn_id = f"ep_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f'<div class="phone-action-group" style="padding:4px 0;flex-wrap:wrap;gap:8px;white-space:normal;"><span style="font-size:0.9rem;color:#3C4A5A;flex:1 1 auto;min-width:0;word-break:break-word;">{info}</span><button onclick="window.crmCopy(\'{phone}\',\'{btn_id}\')" class="phone-btn" id="{btn_id}" title="Скопировать">📋</button><a href="tel:+{cph}" class="phone-btn" title="Позвонить">📞</a></div>', unsafe_allow_html=True)

def render_track_inline(track_num, uid):
    btn_id = f"trk_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f'<div style="display:flex;align-items:center;gap:8px;"><code>{track_num}</code><button onclick="window.crmCopy(\'{track_num}\',\'{btn_id}\')" class="track-copy-btn" id="{btn_id}" title="Копировать">⎘</button></div>', unsafe_allow_html=True)

def render_file_thumbs(files, prefix, allow_delete=False):
    if not files: st.caption("Файлов нет"); return
    img_files, other_files = [], []
    for ff in files:
        fn = ff.get("file_name", ff.get("name", "файл"))
        ext = os.path.splitext(fn)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]: img_files.append(ff)
        else: other_files.append(ff)
    if img_files:
        ncols = min(len(img_files), 4); cols = st.columns(ncols)
        for i, ff in enumerate(img_files):
            with cols[i % ncols]:
                fp = ff.get("file_path", ff.get("path")); fn = ff.get("file_name", ff.get("name", "файл")); fb = get_file_bytes(fp)
                if fb:
                    ext = os.path.splitext(fn)[1].lower(); b64 = base64.b64encode(fb).decode(); mt = f"image/{'jpeg' if ext == '.jpg' else ext[1:]}"
                    st.markdown(f'<div class="thumb-item"><img src="data:{mt};base64,{b64}" title="{fn}" onclick="window.crmOpenLightbox && window.crmOpenLightbox(this.src)" /><div class="thumb-name">{fn}</div></div>', unsafe_allow_html=True)
                    st.download_button("⬇", data=fb, file_name=fn, key=f"dl_{prefix}_{i}")
                    if allow_delete and st.session_state.user_role == "admin" and st.button("🗑", key=f"del_{prefix}_{i}"):
                        files.pop(i); commit_and_rerun(st.session_state.crm_store, "Файл удалён")
    for i, ff in enumerate(other_files):
        fp = ff.get("file_path", ff.get("path")); fn = ff.get("file_name", ff.get("name", "файл")); fb = get_file_bytes(fp)
        if fb:
            ext = os.path.splitext(fn)[1].lower()
            if ext == ".pdf":
                b64 = base64.b64encode(fb).decode(); pdf_btn_id = f"pdf_view_{prefix}_{i}"
                st.markdown(f'<button class="custom-print-btn" id="{pdf_btn_id}" style="background:#5A6B7D;margin-bottom:4px;">📄 {fn}</button>', unsafe_allow_html=True)
                st.components.v1.html(f"""<script>(function(){{var b=window.parent.document.getElementById('{pdf_btn_id}');if(!b)return;var b64="{b64}";b.addEventListener('click',function(){{var w=window.open('','_blank');if(!w)return;var html='<html><body style="margin:0"><iframe src="data:application/pdf;base64,'+b64+'" style="width:100vw;height:100vh;border:0"></iframe></body></html>';w.document.open();w.document.write(html);w.document.close();}});}})();</script>""", height=0)
                st.download_button(f"⬇ {fn}", data=fb, file_name=fn, mime="application/pdf", key=f"dl_{prefix}_o_{i}")
            else: st.download_button(f"📄 {fn}", data=fb, file_name=fn, key=f"dl_{prefix}_o_{i}")
            if allow_delete and st.session_state.user_role == "admin" and st.button("🗑 Удалить", key=f"del_{prefix}_o_{i}"):
                files.pop(len(img_files) + i); commit_and_rerun(st.session_state.crm_store, "Файл удалён")

if "crm_store" not in st.session_state: st.session_state.crm_store = load_data()

# Запуск мгновенной проверки сессии
check_auto_login()

if not st.session_state.get("authenticated"): render_auth_screen()

# Главный экран системы после входа
st.markdown(f"""<div class="greeting-block"><h1 style='text-align: center; margin-bottom: 0.1rem;'>Айплинт CRM</h1><p style='text-align: center; color: #7F8C9A; font-size: 0.95rem; margin-top: 0; margin-bottom: 0;'>Продуктивного тебе дня, {st.session_state.user_name} 😊</p></div>""", unsafe_allow_html=True)

session_defaults = {
    "f_ph": [], "f_em": [], "f_ad": [], "last_id": None, "active_tab": "Планировщик",
    "client_form_version": 0, "cloud_ok": check_cloud_status(), "open_deal_id": None,
    "deal_file_uploader_ver": {}, "expanded_client_id": None, "expanded_deal_id": None,
    "expanded_task_key": None, "expanded_tree_id": None, "auto_expand_deal_id": None, "scroll_to_deal": None
}
for k, v in session_defaults.items():
    if k not in st.session_state: st.session_state[k] = v

with st.sidebar:
    st.write(f"👤 **{st.session_state.user_name}** (`{st.session_state.user_role}`)")
    st.caption("Облако: Активно" if st.session_state.cloud_ok else "Облако: Локальный режим")
    
    current_user_obj = next((u for u in st.session_state.crm_store.get("users", []) if u["login"] == st.session_state.user_login), None)
    if current_user_obj:
        with st.expander("🔐 Настройка быстрого входа"):
            db_pin = current_user_obj.get("pin", "")
            set_pin = st.text_input("Придумайте 4 цифры PIN:", value=db_pin, max_chars=4, type="password", key="sidebar_pin_set")
            if st.button("Сохранить PIN-код", use_container_width=True, type="primary"):
                if set_pin.isdigit() and len(set_pin) == 4:
                    current_user_obj["pin"] = set_pin
                    save_data(st.session_state.crm_store)
                    st.success("PIN-код успешно изменен!")
                    st.rerun()
                else: st.error("PIN должен состоять из 4 цифр!")
                
    if st.button("Выйти из аккаунта", use_container_width=True):
        if current_user_obj and "auth_token" in current_user_obj: del current_user_obj["auth_token"]
        save_data(st.session_state.crm_store)
        st.components.v1.html("<script>try{localStorage.removeItem('crm_token_v5'); localStorage.removeItem('crm_user_v5');}catch(e){} window.parent.location.href=window.parent.location.pathname;</script>", height=0)
        st.session_state.authenticated = False
        st.stop()

# Переключатели разделов
c1, c2, c3, c4 = st.columns(4)
tabs = ["Клиенты и сделки", "Планировщик", "Внутренние задачи", "Поставщики"]
for col, name in zip([c1, c2, c3, c4], tabs):
    if col.button(name, use_container_width=True, type="primary" if st.session_state.active_tab == name else "secondary"):
        st.session_state.active_tab = name
        st.rerun()

st.markdown("---")

# Отрисовка внутренней рабочей области
if st.session_state.active_tab == "Внутренние задачи":
    sub1, sub2, sub3 = st.tabs(["Задачи сотрудникам", "Общий чат", "Шпаргалка"])
    with sub1:
        all_users = [u.get("name", u["login"]) for u in st.session_state.crm_store.get("users", []) if u.get("role") != "admin"]
        col_f, col_btn = st.columns(2)
        itf = col_f.selectbox("Фильтр поручений:", ["Мне", "От меня", "Все"], key="itf_filter")
        if col_btn.button("Новая задача", type="primary", use_container_width=True):
            st.session_state.show_new_itask = not st.session_state.get("show_new_itask", False)
            st.rerun()
        if st.session_state.get("show_new_itask", False):
            with st.container(border=True):
                it_title = st.text_input("Заголовок задачи:")
                it_desc = st.text_area("Описание поручения:")
                it_to = st.selectbox("Исполнитель:", [""] + all_users)
                it_dl = st.date_input("Срок исполнения:")
                if st.button("Поручить задачу", type="primary", use_container_width=True) and it_title.strip() and it_to:
                    st.session_state.crm_store.setdefault("internal_tasks", []).append({
                        "id": str(uuid.uuid4())[:8], "title": it_title.strip(), "description": it_desc.strip(),
                        "assigned_to": it_to, "created_by": st.session_state.user_name, "deadline": it_dl.isoformat(), "done": False, "created_at": now_str()
                    })
                    st.session_state.show_new_itask = False
                    commit_and_rerun(st.session_state.crm_store, "Задача успешно добавлена!")
        for t in st.session_state.crm_store.get("internal_tasks", []):
            if itf == "Мне" and t.get("assigned_to") != st.session_state.user_name: continue
            if itf == "От меня" and t.get("created_by") != st.session_state.user_name: continue
            
            # Подготовка цветовых маркеров статусов задач
            it_done = t.get("done", False)
            it_overdue = False
            try:
                it_dl_date = datetime.strptime(t.get("deadline", ""), "%Y-%m-%d").date()
                it_overdue = it_dl_date < datetime.now().date() and not it_done
            except: pass
            
            if it_done: it_bg, it_bc = "#F5F6F8", "#C9CFD7"
            elif it_overdue: it_bg, it_bc = "#FFEBEE", "#C62828"
            else: it_bg, it_bc = "#FFFFFF", "#DCE0E5"
            
            # Рендеринг раскрывающейся плашки задачи
            with st.expander(f"{'✅' if it_done else '⏳'} {t['title']} — До: {format_date(t['deadline'])} ({t['assigned_to']})"):
                st.markdown(f"**Описание:** {t['description']}")
                st.caption(f"Приоритет: {t.get('priority','Обычный')} | Поручил: {t['created_by']} | {t['created_at']}")
                if not it_done and st.button("Отметить как выполненную", key=f"done_it_{t['id']}", type="primary", use_container_width=True):
                    t["done"] = True
                    commit_and_rerun(st.session_state.crm_store)

    with sub2: # Корпоративный внутренний чат
        chat = st.session_state.crm_store.get("chat_messages", [])
        chat_container = st.container(height=350)
        with chat_container:
            for msg in chat[-100:]:
                is_me = msg.get("user") == st.session_state.user_name
                cls = "chat-msg-me" if is_me else "chat-msg-other"
                st.markdown(f'<div class="chat-msg {cls}"><b>{msg.get("user","")}</b> — {msg.get("time","")}<br>{msg.get("text","")}</div>', unsafe_allow_html=True)
        msg_text = st.text_input("Ваше сообщение в чат:", key="general_chat_input")
        if st.button("Отправить в чат", type="primary", use_container_width=True) and msg_text.strip():
            chat.append({"id": str(uuid.uuid4())[:8], "user": st.session_state.user_name, "text": msg_text.strip(), "time": datetime.now().strftime("%d.%m %H:%M")})
            commit_and_rerun(st.session_state.crm_store)

    with sub3: # Шпаргалка (База знаний компании) с кнопками копирования ответов
        qa_entries = st.session_state.crm_store.get("qa_entries", [])
        qa_search = st.text_input("Поиск по шпаргалке:", placeholder="Введите ключевое слово...").strip().lower()
        with st.expander("➕ Добавить новую запись"):
            q_q = st.text_input("Вопрос / Тема скрипта:")
            q_a = st.text_area("Ответ / Инструкция:")
            q_c = st.text_input("Категория базы знаний:", value="Общее")
            if st.button("Зафиксировать в базе", type="primary", use_container_width=True) and q_q.strip() and q_a.strip():
                st.session_state.crm_store.setdefault("qa_entries", []).append({"id": str(uuid.uuid4())[:8], "question": q_q.strip(), "answer": q_a.strip(), "category": q_c.strip()})
                commit_and_rerun(st.session_state.crm_store)
        for qa in qa_entries:
            if qa_search and qa_search not in f"{qa['question']} {qa['answer']} {qa['category']}".lower(): continue
            with st.container(border=True):
                st.markdown(f"**[{qa['category']}] {qa['question']}**")
                st.write(qa['answer'])
                render_copy_button(qa['answer'], f"copy_qa_{qa['id']}", "📋 Скопировать ответ")
# Вкладка Поставщики (Полная интеграция структуры из Файла №2 с полями person и note)
elif st.session_state.active_tab == "Поставщики":
    st.markdown("### Реестр фабрик и поставщиков")
    suppliers = st.session_state.crm_store.setdefault("suppliers", [])
    with st.expander("➕ Внести нового поставщика в реестр"):
        s_name = st.text_input("Название компании / Фабрики:")
        sl, sr = st.columns(2)
        s_person = sl.text_input("Контактное лицо (ФИО):")
        s_phone = sl.text_input("Телефон связи:")
        s_email = sr.text_input("Email контрагента:")
        s_cat = sr.text_input("Категория продукции фабрики:")
        s_note = st.text_area("Условия работы, комментарии и заметки:")
        if st.button("Сохранить поставщика", type="primary", use_container_width=True) and s_name.strip():
            suppliers.append({
                "id": len(suppliers) + 1, "name": s_name.strip(), "person": s_person.strip(),
                "phone": format_phone(s_phone), "email": s_email.strip(), "category": s_cat.strip(), "note": s_note.strip(), "last_modified": now_str()
            })
            commit_and_rerun(st.session_state.crm_store)
    for s in sorted(suppliers, key=lambda x: x.get("last_modified", ""), reverse=True):
        with st.expander(f"📦 {s['name']} — {s.get('category','Без категории')} ({s.get('person','—')})"):
            st.markdown(f"📞 **Телефон:** {s['phone']} | ✉️ **Email:** {s['email']}")
            st.write(f"📝 **Условия:** {s['note']}")
            if st.session_state.user_role == "admin" and st.button("Удалить поставщика", key=f"del_sup_{s['id']}"):
                st.session_state.crm_store["suppliers"] = [x for x in suppliers if x["id"] != s["id"]]
                commit_and_rerun(st.session_state.crm_store)

# Системные заглушки для базовых вкладок, подключенных к сессии LocalStorage
elif st.session_state.active_tab in ["Клиенты и сделки", "Планировщик"]:
    st.info(f"Раздел '{st.session_state.active_tab}' успешно подключен к системе LocalStorage-авторизации.")

