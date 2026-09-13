import streamlit as st
import json, os, re, urllib.parse, requests, hashlib, base64, csv, io, secrets, threading, uuid
from datetime import datetime

st.set_page_config(page_title="Айплинт CRM", layout="wide")

st.markdown("""
<style>
    .stApp {
        background-color: #F5F6F8;
        color: #2C3E50;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #EEF0F3;
        border-right: 1px solid #DCE0E5;
    }
    .stContainer { border-radius: 14px; background-color: #FFFFFF; border: 1px solid #E8EBEF; box-shadow: 0 2px 8px rgba(0,0,0,0.03); padding: 1rem 1.25rem; }
    .stExpander { border-radius: 14px; overflow: hidden; border: 1px solid #E8EBEF; background-color: #FFFFFF; margin-bottom: 0.5rem; }
    .stExpander > details { border-radius: 14px; }
    .stExpander > details > summary { font-weight: 600; font-size: 1rem; color: #2C3E50; padding: 0.75rem 1.25rem; list-style: none; border-radius: 14px; cursor: pointer; }
    .stExpander > details > summary:hover { background-color: #F5F6F8; }
    h1, h2, h3, h4 { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif; font-weight: 700; color: #2C3E50 !important; letter-spacing: -0.02em; }
    h1 { font-size: 1.75rem; margin-bottom: 0.5rem; }
    h2 { font-size: 1.4rem; margin-top: 1rem; }
    h3 { font-size: 1.1rem; }
    hr { border: 0; height: 1px; background: #E8EBEF; margin: 1rem 0; }
    button[kind="primary"], .stButton > button[kind="primary"] { background-color: #4F6D9C; color: #FFFFFF; border-radius: 10px; font-weight: 600; font-size: 0.95rem; padding: 0.55rem 1.1rem; border: none; box-shadow: 0 2px 6px rgba(79,109,156,0.2); transition: all 0.15s ease; }
    button[kind="primary"]:hover { background-color: #3F5A82; box-shadow: 0 3px 10px rgba(79,109,156,0.25); }
    button[kind="secondary"], .stButton > button[kind="secondary"] { background-color: transparent; color: #4F6D9C; border: 1px solid #C9CFD7; border-radius: 10px; font-weight: 500; font-size: 0.95rem; padding: 0.55rem 1.1rem; transition: all 0.15s ease; }
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
    .comments-box { border: 1.5px solid #DCE0E5; border-radius: 12px; padding: 0.75rem 1rem; background-color: #FAFBFC; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

FILE_NAME = "web_crm_database_v2.json"
YANDEX_API_URL = "https://cloud-api.yandex.net/v1/disk/resources"

raw_token = st.secrets.get("YANDEX_DISK_TOKEN", "")
if isinstance(raw_token, str):
    YANDEX_TOKEN = raw_token.strip().strip('"').strip("'")
else:
    YANDEX_TOKEN = ""

# --- Цветные рамки через CSS :has() ---

def color_expander_border(color):
    """Красит рамку stExpander, внутри которого вызван."""
    uid = f"exp_{uuid.uuid4().hex[:8]}"
    st.markdown(f"""
    <style>
        div[data-testid="stExpander"]:has(#{uid}) {{
            border: 2px solid {color} !important;
            border-radius: 14px !important;
        }}
    </style>
    <span id="{uid}" style="display:none"></span>
    """, unsafe_allow_html=True)

def color_container_border(color):
    """Красит рамку st.container(border=True), внутри которого вызван."""
    uid = f"cnt_{uuid.uuid4().hex[:8]}"
    st.markdown(f"""
    <style>
        div[data-testid="stVerticalBlockBorderWrapper"]:has(#{uid}) {{
            border-color: {color} !important;
            border-width: 2px !important;
            border-radius: 14px !important;
        }}
    </style>
    <span id="{uid}" style="display:none"></span>
    """, unsafe_allow_html=True)

# --- Пароли ---

def hash_password(pwd, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
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

# --- Яндекс.Диск ---

def yandex_headers():
    return {"Authorization": f"OAuth {YANDEX_TOKEN}", "Accept": "application/json"}

def check_cloud_status():
    if not YANDEX_TOKEN: return False
    try:
        res = requests.get(YANDEX_API_URL, headers=yandex_headers(), timeout=5)
        return res.status_code == 200
    except Exception:
        return False

def init_yandex_folders():
    if not YANDEX_TOKEN: return
    for folder in ["CRM_NE_TROGAT", "CRM_NE_TROGAT/uploads"]:
        try:
            requests.put(YANDEX_API_URL, params={"path": f"disk:/{folder}"}, headers=yandex_headers(), timeout=10)
        except Exception: pass

def download_db_from_yandex():
    if not YANDEX_TOKEN: return
    try:
        url = f"{YANDEX_API_URL}/download"
        res = requests.get(url, params={"path": f"disk:/CRM_NE_TROGAT/{FILE_NAME}"}, headers=yandex_headers(), timeout=10)
        if res.status_code == 200:
            download_url = res.json().get("href")
            file_res = requests.get(download_url, timeout=30)
            if file_res.status_code == 200:
                with open(FILE_NAME, "w", encoding="utf-8") as f:
                    f.write(file_res.text)
                return
    except Exception: pass
    if not os.path.exists(FILE_NAME):
        default_db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}], "_migrated": "v2"}
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            json.dump(default_db, f, ensure_ascii=False, indent=2)

def upload_db_to_yandex_async():
    if not YANDEX_TOKEN or not os.path.exists(FILE_NAME): return
    def _upload():
        try:
            url = f"{YANDEX_API_URL}/upload"
            res = requests.get(url, params={"path": f"disk:/CRM_NE_TROGAT/{FILE_NAME}", "overwrite": "true"}, headers=yandex_headers(), timeout=10)
            if res.status_code == 200:
                upload_url = res.json().get("href")
                with open(FILE_NAME, "rb") as f:
                    requests.put(upload_url, data=f, timeout=30)
        except Exception: pass
    threading.Thread(target=_upload, daemon=True).start()

def upload_file_to_yandex(file_bytes, remote_name):
    if not YANDEX_TOKEN: return False
    try:
        url = f"{YANDEX_API_URL}/upload"
        remote_path = f"disk:/CRM_NE_TROGAT/uploads/{remote_name}"
        res = requests.get(url, params={"path": remote_path, "overwrite": "true"}, headers=yandex_headers(), timeout=10)
        if res.status_code == 200:
            upload_url = res.json().get("href")
            put_res = requests.put(upload_url, data=file_bytes, timeout=30)
            return put_res.status_code in (200, 201)
    except Exception: pass
    return False

@st.cache_data(ttl=300, show_spinner=False)
def download_file_from_yandex(remote_path):
    if not YANDEX_TOKEN: return None
    try:
        res = requests.get(f"{YANDEX_API_URL}/download", params={"path": f"disk:/{remote_path}"}, headers=yandex_headers(), timeout=10)
        if res.status_code == 200:
            download_url = res.json().get("href")
            file_res = requests.get(download_url, timeout=30)
            if file_res.status_code == 200:
                return file_res.content
    except Exception: pass
    return None

# --- Утилиты ---

def format_phone(p_str):
    if not p_str: return ""
    digits = re.sub(r"\D", "", p_str)
    if len(digits) == 11 and digits[0] in ("7", "8"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"+7 {digits[0:3]} {digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
    return p_str.strip()

def save_uploaded_file(u_file, c_id, prefix=""):
    if u_file is None: return None
    unique_name = f"{c_id}_{prefix}_{int(datetime.now().timestamp())}_{u_file.name}"
    file_bytes = u_file.getvalue()
    if YANDEX_TOKEN:
        remote_path = f"CRM_NE_TROGAT/uploads/{unique_name}"
        if upload_file_to_yandex(file_bytes, unique_name):
            return {"path": remote_path, "name": u_file.name}
        st.warning("Не удалось загрузить на Диск, файл сохранён локально")
    os.makedirs("uploads", exist_ok=True)
    local_path = f"uploads/{unique_name}"
    with open(local_path, "wb") as f:
        f.write(file_bytes)
    return {"path": local_path, "name": u_file.name}

def normalize_remote_path(f_path):
    if not f_path: return None
    if f_path.startswith("CRM_NE_TROGAT"): return f_path
    elif f_path.startswith("uploads/"): return f"CRM_NE_TROGAT/{f_path}"
    else: return f"CRM_NE_TROGAT/uploads/{os.path.basename(f_path)}"

@st.cache_data
def get_logo_base64():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def export_clients_csv():
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["ID", "ФИО", "Телефон", "Email", "Адрес", "Категория", "Скидка %", "Ответственный"])
    for c in st.session_state.crm_store["clients"]:
        writer.writerow([c["id"], c["name"], c["phone"], c.get("email", ""), c.get("address", ""), c.get("category", ""), c.get("discount", 0), c.get("manager", "")])
    return output.getvalue().encode("utf-8-sig")

def get_client_by_id(c_id):
    for c in st.session_state.crm_store["clients"]:
        if c["id"] == c_id: return c
    return None

def parse_deadline(deadline_str):
    if not deadline_str: return datetime.now().date()
    try: return datetime.strptime(deadline_str, "%Y-%m-%d").date()
    except Exception:
        try: return datetime.strptime(deadline_str, "%Y-%m-%d %H:%M").date()
        except Exception: return datetime.now().date()

def is_task_overdue(task):
    if task.get("done"): return False
    deadline = task.get("deadline", "")
    if not deadline: return False
    try: return datetime.strptime(deadline, "%Y-%m-%d").date() < datetime.now().date()
    except Exception:
        try: return datetime.strptime(deadline, "%Y-%m-%d %H:%M") < datetime.now()
        except Exception: return False

def get_task_sort_date(task):
    deadline = task.get("deadline", "")
    try: return datetime.strptime(deadline, "%Y-%m-%d").date()
    except Exception:
        try: return datetime.strptime(deadline, "%Y-%m-%d %H:%M").date()
        except Exception: return datetime.max.date()

def format_date(date_str):
    if not date_str: return ""
    try: return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        try: return datetime.strptime(date_str, "%Y-%m-%d %H:%M").strftime("%d/%m/%Y")
        except Exception: return date_str

def get_managers_list():
    users = st.session_state.crm_store.get("users", [])
    return [u.get("name", u["login"]) for u in users]

def auto_task_title(task_type, client_name, deal_title):
    if task_type == "Отправить заказ":
        return f"Отправка по {deal_title}" if deal_title else f"Отправка: {client_name}"
    else:
        return f"Связаться: {client_name}"

def render_file_action_buttons(file_path, file_name, key_prefix):
    if file_path and not file_path.startswith("CRM_NE_TROGAT") and os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
        except Exception:
            file_bytes = None
    else:
        remote_path = normalize_remote_path(file_path)
        file_bytes = download_file_from_yandex(remote_path) if remote_path else None
    if not file_bytes:
        st.caption("Файл недоступен")
        return
    file_ext = os.path.splitext(file_name)[1].lower()
    if file_ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
        try:
            st.image(file_bytes, caption=file_name)
        except Exception:
            pass
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("Скачать", data=file_bytes, file_name=file_name, key=f"dl_{key_prefix}")
        with col2:
            b64 = base64.b64encode(file_bytes).decode()
            mime_type = f"image/{file_ext[1:]}"
            print_html = f"<html><body style='margin:0;text-align:center;'><img src='data:{mime_type};base64,{b64}' style='max-width:100%;' onload='window.print();'/></body></html>"
            print_url = f"data:text/html;charset=utf-8,{urllib.parse.quote(print_html)}"
            st.markdown(f"<a href='{print_url}' target='_blank'><button style='width:100%;padding:8px;background:#4F6D9C;color:white;border:none;border-radius:10px;cursor:pointer;font-size:14px;'>Распечатать</button></a>", unsafe_allow_html=True)
    elif file_ext == ".pdf":
        st.download_button("Открыть / Скачать PDF", data=file_bytes, file_name=file_name, mime="application/pdf", key=f"dl_{key_prefix}")
    else:
        st.download_button("Скачать", data=file_bytes, file_name=file_name, key=f"dl_{key_prefix}")

# --- Данные ---

def migrate_data(data):
    default_users = [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}]
    if "users" not in data:
        data["users"] = default_users
    for u in data["users"]:
        if not is_hashed(u.get("password", "")):
            u["password"] = hash_password(u["password"])
    for c in data.get("clients", []):
        for k, val in [("email", ""), ("address", ""), ("base_comment", ""), ("category", "Покупатель"), ("discount", 0), ("extra_phones", []), ("extra_emails", []), ("extra_addresses", []), ("client_files", []), ("client_comments", []), ("manager", ""), ("comments", []), ("tasks", [])]:
            if k not in c or c[k] == "-":
                c[k] = val
        for ea in c.get("extra_addresses", []):
            if isinstance(ea, str):
                c["extra_addresses"][c["extra_addresses"].index(ea)] = {"address": ea, "resp_name": "", "resp_role": "", "resp_phone": "", "resp_email": ""}
        for t in c.get("tasks", []):
            if "manager" not in t:
                t["manager"] = c.get("manager", "")
            if "deadline" in t and " " in str(t["deadline"]):
                t["deadline"] = str(t["deadline"]).split(" ")[0]
    for d in data.get("deals", []):
        if "deal_comments" not in d:
            d["deal_comments"] = []
        if d.get("status") == "New":
            d["status"] = "Новый"
    data["_migrated"] = "v2"
    return data

def load_data():
    download_db_from_yandex()
    default_db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}], "_migrated": "v2"}
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("_migrated") != "v2":
                data = migrate_data(data)
                with open(FILE_NAME, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                upload_db_to_yandex_async()
            return data
        except Exception:
            return default_db
    return default_db

def save_data(data):
    try:
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        upload_db_to_yandex_async()
    except Exception as e:
        st.sidebar.error(f"Ошибка сохранения: {e}")

def commit_and_rerun(data=None):
    if data is not None:
        save_data(data)
    st.rerun()

@st.dialog("Завершить сделку", width="medium")
def close_deal_dialog(deal_id):
    st.markdown("Заполните отчёт о выполнении сделки:")
    report = st.text_area("Отчёт (обязательно):", key=f"close_deal_report_{deal_id}")
    if st.button("Завершить сделку", type="primary", use_container_width=True):
        if report.strip():
            for d in st.session_state.crm_store["deals"]:
                if d["id"] == deal_id:
                    d['status'] = "Сделка закрыта"
                    d['closed_date'] = datetime.now().strftime("%Y-%m-%d")
                    d['close_report'] = report.strip()
                    break
            save_data(st.session_state.crm_store)
            st.rerun()
        else:
            st.error("Заполните отчёт")

# --- Session state ---

if "crm_store" not in st.session_state:
    with st.spinner("Загрузка данных..."):
        st.session_state.crm_store = load_data()
if "f_ph" not in st.session_state: st.session_state.f_ph = []
if "f_em" not in st.session_state: st.session_state.f_em = []
if "f_ad" not in st.session_state: st.session_state.f_ad = []
if "last_id" not in st.session_state: st.session_state.last_id = None
if "active_tab" not in st.session_state: st.session_state.active_tab = "Задачи"
if "client_form_version" not in st.session_state: st.session_state.client_form_version = 0
if "deal_form_version" not in st.session_state: st.session_state.deal_form_version = 0
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "user_role" not in st.session_state: st.session_state.user_role = None
if "user_login" not in st.session_state: st.session_state.user_login = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "cloud_ok" not in st.session_state: st.session_state.cloud_ok = check_cloud_status()
if "open_deal_id" not in st.session_state: st.session_state.open_deal_id = None
if "yandex_folders_ready" not in st.session_state:
    init_yandex_folders()
    st.session_state.yandex_folders_ready = True

# --- Авторизация ---

def check_login(username, password):
    users_list = st.session_state.crm_store.get("users", [])
    for u in users_list:
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
    col_auth = st.columns([1, 2, 1])
    with col_auth[1]:
        with st.container(border=True):
            input_user = st.text_input("Логин:", placeholder="Введите логин")
            input_pass = st.text_input("Пароль:", type="password", placeholder="Введите пароль")
            st.markdown("---")
            if st.button("Войти", use_container_width=True, type="primary"):
                if check_login(input_user, input_pass):
                    st.toast("Успешный вход", icon="🔓")
                    st.rerun()
                else:
                    st.error("Неверный логин или пароль.")
    st.stop()

st.title("Айплинт CRM")

with st.sidebar:
    if st.session_state.cloud_ok:
        st.success("Облако активно")
    else:
        st.warning("Облако недоступно (работа локально)")
    st.markdown("---")
    st.markdown(f"**{st.session_state.user_name}**")
    st.markdown(f"Роль: `{st.session_state.user_role}`")
    with st.expander("Сменить пароль"):
        current_user_login = st.session_state.user_login
        new_pwd = st.text_input("Новый пароль:", type="password", key="self_new_pwd")
        confirm_pwd = st.text_input("Повторите пароль:", type="password", key="self_conf_pwd")
        if st.button("Обновить", key="btn_save_self_pwd", use_container_width=True):
            if new_pwd and new_pwd == confirm_pwd:
                for u in st.session_state.crm_store["users"]:
                    if u["login"] == current_user_login:
                        u["password"] = hash_password(new_pwd)
                        save_data(st.session_state.crm_store)
                        st.success("Пароль изменён")
                        st.rerun()
            else:
                st.error("Пароли не совпадают")
    if st.session_state.user_role == "admin":
        with st.expander("Экспорт базы"):
            csv_data = export_clients_csv()
            st.download_button("Скачать CSV", data=csv_data, file_name="clients_export.csv", mime="text/csv", use_container_width=True)
    st.markdown("---")
    if st.button("Выйти", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_login = None
        st.session_state.user_name = None
        st.rerun()

# --- Навигация ---

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    if st.button("Задачи", use_container_width=True, type="primary" if st.session_state.active_tab == "Задачи" else "secondary"):
        st.session_state.active_tab = "Задачи"; st.rerun()
with col_m2:
    if st.button("Клиенты", use_container_width=True, type="primary" if st.session_state.active_tab == "Клиенты" else "secondary"):
        st.session_state.active_tab = "Клиенты"; st.rerun()
with col_m3:
    if st.button("Сделки", use_container_width=True, type="primary" if st.session_state.active_tab == "Сделки" else "secondary"):
        st.session_state.active_tab = "Сделки"; st.rerun()
st.markdown("---")

# --- Вкладка «Задачи» ---

if st.session_state.active_tab == "Задачи":
    st.header("Задачи")
    now_time = datetime.now()
    all_deals = st.session_state.crm_store["deals"]
    active_deals = [d for d in all_deals if d["status"] in ("Новый", "В работе")]
    active_sum = sum(d.get("budget", 0) for d in active_deals)
    overdue_count = 0
    for c in st.session_state.crm_store.get("clients", []):
        for t in c.get("tasks", []):
            if is_task_overdue(t):
                overdue_count += 1
    closed_this_month = len([d for d in all_deals if d["status"] == "Сделка закрыта" and d.get("closed_date", "").startswith(now_time.strftime("%Y-%m"))])
    total_clients = len(st.session_state.crm_store["clients"])
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    col_d1.metric("Активные сделки", len(active_deals), f"{active_sum:,.0f} руб.".replace(",", " "))
    col_d2.metric("Просрочено", overdue_count)
    col_d3.metric("Закрыто за месяц", closed_this_month)
    col_d4.metric("Клиентов", total_clients)
    st.markdown("---")

    current_user_name = st.session_state.user_name
    managers = get_managers_list()
    manager_options = ["Мои задачи", "Все"] + managers
    manager_filter = st.selectbox("Ответственный", manager_options, index=0)

    deal_index = {}
    for d in st.session_state.crm_store.get("deals", []):
        deal_index.setdefault(d["client_id"], d)

    all_active_tasks = []
    for client in st.session_state.crm_store.get("clients", []):
        client_deal = deal_index.get(client["id"])
        main_deal_title = client_deal["title"] if client_deal else ""
        for ti, task in enumerate(client.get("tasks", [])):
            if not task.get("done", False):
                task_manager = task.get("manager", "")
                if manager_filter == "Мои задачи":
                    if task_manager and task_manager != current_user_name:
                        continue
                elif manager_filter != "Все":
                    if task_manager != manager_filter:
                        continue
                sort_date = get_task_sort_date(task)
                all_active_tasks.append({
                    "client_id": client["id"], "client_name": client["name"], "client_phone": client["phone"],
                    "deal_title": main_deal_title, "sort_date": sort_date, "deadline_str": task.get("deadline", ""),
                    "type": task.get("type", "Связаться"), "text": task.get("text", ""),
                    "task_obj": task, "task_idx": ti, "client_obj": client
                })
    all_active_tasks.sort(key=lambda x: x["sort_date"])
    today_tasks = [t for t in all_active_tasks if t["sort_date"] <= now_time.date()]
    future_tasks = [t for t in all_active_tasks if t["sort_date"] > now_time.date()]

    def render_task_block(t, section_key):
        task = t["task_obj"]
        client = t["client_obj"]
        t_type = task.get("type", "Связаться")
        is_over = is_task_overdue(task)
        status_label = "Просрочено" if is_over else ("Сегодня" if t["sort_date"] == now_time.date() else "Срок")
        formatted_date = format_date(t["deadline_str"])
        header_text = f"{formatted_date} — {t['client_name']} — {t['type']}"

        with st.expander(header_text, expanded=False):
            if is_over:
                color_expander_border("#D65757")
            st.markdown(f"**{status_label}** — {formatted_date} | {t_type}")
            st.markdown(f"👤 **{t['client_name']}** ({t['client_phone']})")
            if t_type == "Отправить заказ":
                st.markdown("---")
                st.markdown("**Данные отправки:**")
                st.markdown(f"Товары: {task.get('products', '')}")
                st.markdown(f"Адрес: {task.get('ship_addr', '')}")
                st.markdown(f"Получатель: {task.get('receiver', '')} ({task.get('receiver_phone', '')})")
                st.markdown(f"Оплата: {task.get('ship_pay', '')}")
                if task.get('order_amount', 0) > 0:
                    oa = task['order_amount']
                    dp = client.get('discount', 0)
                    da = oa * dp / 100
                    ta = oa - da
                    st.markdown(f"Сумма: {oa:,.0f} | Скидка: {dp}% ({da:,.0f}) | **Итого: {ta:,.0f}**".replace(",", " "))
                if task.get('tk_num'):
                    st.markdown(f"Трек: `{task['tk_num']}`")
            st.markdown("---")
            st.markdown(f"**Ответственный:** {task.get('manager', '—')}")
            st.markdown("---")
            st.markdown("**Файл:**")
            if task.get("file_path"):
                st.markdown(f"📄 {task.get('file_name', '')}")
                render_file_action_buttons(task["file_path"], task.get("file_name", ""), f"task_{section_key}_{t['client_id']}_{t['task_idx']}")
                if st.button("Удалить файл", key=f"del_tfile_{section_key}_{t['client_id']}_{t['task_idx']}"):
                    task["file_path"] = None
                    task["file_name"] = None
                    commit_and_rerun(st.session_state.crm_store)
            new_task_file = st.file_uploader("Добавить файл:", key=f"new_tfile_{section_key}_{t['client_id']}_{t['task_idx']}")
            if st.button("Сохранить файл", key=f"save_tfile_{section_key}_{t['client_id']}_{t['task_idx']}"):
                if new_task_file:
                    f_info = save_uploaded_file(new_task_file, t["client_id"], "task_file")
                    if f_info:
                        task["file_path"] = f_info["path"]
                        task["file_name"] = f_info["name"]
                        commit_and_rerun(st.session_state.crm_store)
            st.markdown("---")
            clean_products = task.get('products', '').replace('\n', '<br>').replace("'", "`")
            clean_addr = task.get('ship_addr', '').replace("'", "`")
            clean_rec = task.get('receiver', '').replace("'", "`")
            clean_tk = task.get('tk_num', '')
            oa_val = task.get('order_amount', 0)
            disc_pct = client.get('discount', 0)
            disc_amt = oa_val * disc_pct / 100
            total_amt = oa_val - disc_amt
            logo_b64 = get_logo_base64()
            logo_tag = f"<img src='data:image/png;base64,{logo_b64}' width='180' style='float:left; margin-right:20px;'/>" if logo_b64 else "<div style='font-size:24px; font-weight:bold; float:left; margin-right:20px;'>АЙПЛИНТ</div>"
            calc_html = f"<div>Сумма: {oa_val:,.0f} руб.</div><div>Скидка: {disc_pct}% ({disc_amt:,.0f} руб.)</div><div style='font-size:18px;font-weight:bold;'>Итого: {total_amt:,.0f} руб.</div>".replace(",", " ") if oa_val > 0 else ""
            print_html = f"""
<a href="data:text/html;charset=utf-8,<html><head><title>Задача</title><style>body{{font-family:Arial;margin:40px;}} .h{{text-align:center;border-bottom:2px solid %23000;padding:10px;clear:both;}} .s{{margin:8px 0;}}</style></head><body>{logo_tag}<div class='h'><h2>БЛАНК ЗАДАЧИ</h2><p>{datetime.now().strftime('%d/%m/%Y')}</p></div><div class='s'><b>Клиент:</b> {client['name']} ({client['phone']})</div><div class='s'><b>Тип:</b> {t_type}</div><div class='s'><b>Срок:</b> {formatted_date}</div><div class='s'><b>Ответственный:</b> {task.get('manager','')}</div><hr><div class='s'><b>Товары:</b><br>{clean_products}</div><div class='s'><b>Адрес:</b> {clean_addr}</div><div class='s'><b>Получатель:</b> {clean_rec} ({task.get('receiver_phone', '')})</div><div class='s'><b>Оплата:</b> {task.get('ship_pay', '')}</div><div class='s'><b>Трек:</b> {clean_tk}</div>{calc_html}<br><br><p>Отпустил: _____________</p><p>Получил: _____________</p><script>window.print();</script></body></html>" target="_blank" style="text-decoration:none;"><button style="width:100%;padding:10px;background:#4F6D9C;color:white;border:none;border-radius:10px;cursor:pointer;font-size:14px;">Распечатать задачу</button></a>
"""
            st.markdown(print_html, unsafe_allow_html=True)
            st.markdown("---")
            curr_date = parse_deadline(task.get("deadline", ""))
            st.markdown("**Изменить срок:**")
            col_dl1, col_dl2 = st.columns([3, 1])
            with col_dl1:
                new_dl_date = st.date_input("Дата", value=curr_date, format="DD/MM/YYYY", key=f"dl_d_{section_key}_{t['client_id']}_{t['task_idx']}")
            with col_dl2:
                st.write("")
                if st.button("Обновить", key=f"dl_btn_{section_key}_{t['client_id']}_{t['task_idx']}"):
                    task["deadline"] = new_dl_date.isoformat()
                    commit_and_rerun(st.session_state.crm_store)
            st.markdown("---")
            with st.expander("Выполнить задачу", expanded=False):
                rt = st.text_input("Отчёт:", key=f"rt_{section_key}_{t['client_id']}_{t['task_idx']}")
                uf = st.file_uploader("Файл/фото отчёта:", key=f"uf_{section_key}_{t['client_id']}_{t['task_idx']}")
                create_next = st.checkbox("Создать следующую задачу", key=f"cn_{section_key}_{t['client_id']}_{t['task_idx']}")
                new_ex = {}
                new_td = None
                new_t_type = None
                if create_next:
                    st.markdown("---")
                    new_t_type = st.selectbox("Тип:", ["Связаться", "Отправить заказ"], key=f"nt_type_{section_key}_{t['client_id']}_{t['task_idx']}")
                    new_t_manager = st.selectbox("Ответственный:", managers, index=managers.index(current_user_name) if current_user_name in managers else 0, key=f"nt_mgr_{section_key}_{t['client_id']}_{t['task_idx']}")
                    if new_t_type == "Отправить заказ":
                        new_ex["products"] = st.text_area("Товары", key=f"nt_p_{section_key}_{t['client_id']}_{t['task_idx']}")
                        new_ex["ship_addr"] = st.text_input("Адрес", key=f"nt_a_{section_key}_{t['client_id']}_{t['task_idx']}")
                        new_ex["receiver"] = st.text_input("Получатель", key=f"nt_r_{section_key}_{t['client_id']}_{t['task_idx']}")
                        new_ex["receiver_phone"] = format_phone(st.text_input("Тел. получателя", key=f"nt_rp_{section_key}_{t['client_id']}_{t['task_idx']}"))
                        new_ex["ship_pay"] = st.selectbox("Оплата", ["Включено в счёт", "Оплата при получении"], key=f"nt_sp_{section_key}_{t['client_id']}_{t['task_idx']}")
                        new_ex["tk_num"] = st.text_input("Трек-номер", key=f"nt_tk_{section_key}_{t['client_id']}_{t['task_idx']}")
                        new_ex["order_amount"] = st.number_input("Сумма (руб.)", min_value=0.0, step=100.0, key=f"nt_oa_{section_key}_{t['client_id']}_{t['task_idx']}")
                        new_ex["task_comment"] = st.text_area("Комментарии", key=f"nt_c_{section_key}_{t['client_id']}_{t['task_idx']}")
                    else:
                        new_ex["order_amount"] = 0
                        new_ex["task_comment"] = st.text_area("Комментарии", key=f"nt_cs_{section_key}_{t['client_id']}_{t['task_idx']}")
                    new_td = st.date_input("Дата новой задачи", format="DD/MM/YYYY", key=f"nt_d_{section_key}_{t['client_id']}_{t['task_idx']}")
                if st.button("Подтвердить выполнение", key=f"cbtn_{section_key}_{t['client_id']}_{t['task_idx']}", use_container_width=True, type="primary"):
                    if rt.strip():
                        with st.spinner("Сохранение..."):
                            task["done"] = True
                            f_info = save_uploaded_file(uf, t["client_id"], "task_report")
                            rep = f"Закрыта задача [{t_type}] '{task['text']}'. Отчёт: {rt.strip()}"
                            if t_type == "Отправить заказ":
                                rep += f" | Кому: {task.get('receiver', '')} | Трек: {task.get('tk_num', 'нет')}"
                            client["comments"].append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": rep, "file_path": f_info["path"] if f_info else None, "file_name": f_info["name"] if f_info else None})
                            if create_next and new_t_type:
                                auto_title = auto_task_title(new_t_type, t['client_name'], t['deal_title'])
                                t_ent = {"text": auto_title, "deadline": new_td.isoformat(), "done": False, "type": new_t_type, "file_path": None, "file_name": None, "manager": new_t_manager}
                                t_ent.update(new_ex)
                                client.setdefault("tasks", []).append(t_ent)
                            commit_and_rerun(st.session_state.crm_store)
                    else:
                        st.warning("Введите отчёт")
            with st.expander("Редактировать задачу", expanded=False):
                new_manager = st.selectbox("Ответственный:", managers, index=managers.index(task.get("manager", current_user_name)) if task.get("manager", current_user_name) in managers else 0, key=f"ed_mgr_{section_key}_{t['client_id']}_{t['task_idx']}")
                if t_type == "Отправить заказ":
                    edit_oa = st.number_input("Сумма (руб.)", min_value=0.0, step=100.0, value=float(task.get("order_amount", 0)), key=f"ed_oa_{section_key}_{t['client_id']}_{t['task_idx']}")
                if st.button("Сохранить", key=f"ed_btn_{section_key}_{t['client_id']}_{t['task_idx']}", use_container_width=True):
                    task["manager"] = new_manager
                    if t_type == "Отправить заказ":
                        task["order_amount"] = edit_oa
                    commit_and_rerun(st.session_state.crm_store)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        with st.container(border=True):
            st.subheader(f"На сегодня ({len(today_tasks)})")
            if today_tasks:
                for t in today_tasks:
                    render_task_block(t, "today")
            else:
                st.success("Все задачи на сегодня закрыты.")
    with col_t2:
        with st.container(border=True):
            st.subheader(f"Предстоящие ({len(future_tasks)})")
            if future_tasks:
                for t in future_tasks:
                    render_task_block(t, "future")
            else:
                st.caption("План на будущие дни пуст.")

# --- Вкладка «Клиенты» ---

elif st.session_state.active_tab == "Клиенты":
    st.header("Клиенты")
    current_user_name = st.session_state.user_name
    managers = get_managers_list()

    if st.session_state.user_role == "admin":
        with st.expander("Управление сотрудниками", expanded=False):
            st.markdown("### Новый сотрудник")
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                new_u_login = st.text_input("Логин:", key="admin_new_u_log")
                new_u_pass = st.text_input("Пароль:", key="admin_new_u_pass")
            with col_u2:
                new_u_name = st.text_input("Имя / Должность:", key="admin_new_u_name")
                new_u_role = st.selectbox("Роль:", ["manager", "admin"], key="admin_new_u_role")
            if st.button("Создать", use_container_width=True, type="primary"):
                if new_u_login and new_u_pass and new_u_name:
                    exists = any(u["login"] == new_u_login.strip() for u in st.session_state.crm_store.get("users", []))
                    if not exists:
                        st.session_state.crm_store.setdefault("users", []).append({
                            "login": new_u_login.strip(), "password": hash_password(new_u_pass), "role": new_u_role, "name": new_u_name.strip()
                        })
                        commit_and_rerun(st.session_state.crm_store)
                    else:
                        st.error("Логин уже занят")
                else:
                    st.error("Заполните все поля")
            st.markdown("---")
            st.markdown("### Сотрудники")
            for u in st.session_state.crm_store.get("users", []):
                col_l1, col_l2 = st.columns(2)
                with col_l1:
                    st.markdown(f"**{u.get('name', u['login'])}** — `{u['login']}` ({u['role']})")
                with col_l2:
                    if u["login"] != st.session_state.user_login:
                        confirm_del = st.checkbox("Подтвердить", key=f"confirm_del_user_{u['login']}")
                        if confirm_del:
                            if st.button("Удалить", key=f"del_user_{u['login']}", use_container_width=True):
                                st.session_state.crm_store["users"] = [usr for usr in st.session_state.crm_store["users"] if usr["login"] != u["login"]]
                                commit_and_rerun(st.session_state.crm_store)

    fv = st.session_state.client_form_version
    with st.expander("Добавить клиента", expanded=False, key=f"add_client_form_{fv}"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            c_name = st.text_input("ФИО / Компания", key=f"cn_{fv}")
            c_phone = st.text_input("Основной телефон", key=f"cp_{fv}")
            c_email = st.text_input("Основной Email", key=f"ce_{fv}")
            c_discount = st.number_input("Скидка (%)", min_value=0, max_value=100, step=1, key=f"cd_{fv}")
            c_manager = st.selectbox("Ответственный:", managers, index=managers.index(current_user_name) if current_user_name in managers else 0, key=f"cm_{fv}")
        with col_f2:
            c_address = st.text_input("Основной адрес", key=f"ca_{fv}")
            c_category = st.selectbox("Категория", ["Дизайнер", "Строитель", "Дилер", "Покупатель"], key=f"cc_{fv}")
            st.markdown('<div class="comments-box">', unsafe_allow_html=True)
            st.markdown("**Комментарии:**")
            new_cc_form = st.text_input("Добавить комментарий:", key=f"new_cc_form_{fv}", placeholder="Введите комментарий...")
            if st.button("Добавить", key=f"cc_form_btn_{fv}", use_container_width=True):
                if new_cc_form.strip():
                    st.session_state.setdefault("pending_client_comments", []).append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": new_cc_form.strip()})
                    st.rerun()
            if st.session_state.get("pending_client_comments"):
                for pc in st.session_state["pending_client_comments"]:
                    st.markdown(f"- *{pc['time']}*: {pc['text']}")
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.markdown("**Доп. телефоны**")
            for i, ph in enumerate(st.session_state.f_ph):
                st.session_state.f_ph[i]["phone"] = st.text_input(f"Телефон #{i+1}", value=ph["phone"], key=f"f_ph_{fv}_{i}")
                st.session_state.f_ph[i]["name"] = st.text_input(f"ФИО #{i+1}", value=ph["name"], key=f"f_nm_{fv}_{i}")
                st.session_state.f_ph[i]["role"] = st.text_input(f"Должность #{i+1}", value=ph["role"], key=f"f_rl_{fv}_{i}")
            if st.button("Добавить телефон", key=f"add_ph_btn_{fv}"):
                st.session_state.f_ph.append({"phone":"", "name":"", "role":""}); st.rerun()
        with col_s2:
            st.markdown("**Доп. Email**")
            for i, em in enumerate(st.session_state.f_em):
                st.session_state.f_em[i] = st.text_input(f"Email #{i+1}", value=em, key=f"f_em_{fv}_{i}")
            if st.button("Добавить Email", key=f"add_em_btn_{fv}"):
                st.session_state.f_em.append(""); st.rerun()
        with col_s3:
            st.markdown("**Доп. адреса**")
            for i, ad in enumerate(st.session_state.f_ad):
                st.session_state.f_ad[i]["address"] = st.text_input(f"Адрес #{i+1}", value=ad.get("address", ""), key=f"f_ad_addr_{fv}_{i}")
                st.session_state.f_ad[i]["resp_name"] = st.text_input(f"Ответственный #{i+1}", value=ad.get("resp_name", ""), key=f"f_ad_rn_{fv}_{i}")
                st.session_state.f_ad[i]["resp_role"] = st.text_input(f"Должность #{i+1}", value=ad.get("resp_role", ""), key=f"f_ad_rr_{fv}_{i}")
                st.session_state.f_ad[i]["resp_phone"] = st.text_input(f"Телефон #{i+1}", value=ad.get("resp_phone", ""), key=f"f_ad_rp_{fv}_{i}")
                st.session_state.f_ad[i]["resp_email"] = st.text_input(f"Email #{i+1}", value=ad.get("resp_email", ""), key=f"f_ad_re_{fv}_{i}")
            if st.button("Добавить адрес", key=f"add_ad_btn_{fv}"):
                st.session_state.f_ad.append({"address":"", "resp_name":"", "resp_role":"", "resp_phone":"", "resp_email":""}); st.rerun()
        st.markdown("---")
        c_file = st.file_uploader("Прикрепить файл:", key=f"cf_{fv}")
        if st.button("Внести клиента в базу", use_container_width=True, type="primary", key=f"add_client_btn_{fv}"):
            if c_name and c_phone:
                clients = st.session_state.crm_store["clients"]
                new_id = (max([c['id'] for c in clients]) if clients else 0) + 1
                new_client = {
                    "id": new_id, "name": c_name, "phone": format_phone(c_phone), "email": c_email, "address": c_address,
                    "category": c_category, "discount": int(c_discount), "base_comment": "", "manager": c_manager,
                    "extra_phones": [{"phone": format_phone(p["phone"]), "name": p["name"], "role": p["role"]} for p in st.session_state.f_ph if p["phone"].strip()],
                    "extra_emails": [e for e in st.session_state.f_em if e.strip()],
                    "extra_addresses": [{"address": a["address"], "resp_name": a["resp_name"], "resp_role": a["resp_role"], "resp_phone": a["resp_phone"], "resp_email": a["resp_email"]} for a in st.session_state.f_ad if a["address"].strip()],
                    "client_files": [], "client_comments": [], "comments": [], "tasks": []
                }
                if c_file is not None:
                    f_info = save_uploaded_file(c_file, new_id, "profile")
                    if f_info:
                        new_client["client_files"].append({"file_path": f_info["path"], "file_name": f_info["name"]})
                if st.session_state.get("pending_client_comments"):
                    new_client["client_comments"] = list(st.session_state["pending_client_comments"])
                    st.session_state["pending_client_comments"] = []
                st.session_state.crm_store["clients"].append(new_client)
                save_data(st.session_state.crm_store)
                st.session_state.f_ph, st.session_state.f_em, st.session_state.f_ad = [], [], []
                st.session_state.last_id = new_id
                st.session_state.client_form_version += 1
                st.toast(f"Клиент {c_name} добавлен", icon="✅")
                st.rerun()
            else:
                st.error("Заполните ФИО и телефон")

    st.markdown("### Поиск")
    col_search1, col_search2 = st.columns(2)
    with col_search1:
        search_query = st.text_input("По имени, компании или телефону:", key="search_input_key", placeholder="Введите текст...").strip().lower()
    with col_search2:
        category_filter = st.selectbox("Категория:", ["Все", "Дизайнер", "Строитель", "Дилер", "Покупатель"])
    all_clients = st.session_state.crm_store["clients"]
    filtered_clients = []
    search_digits = re.sub(r"\D", "", search_query)
    if search_digits and search_digits[0] in ("7", "8") and len(search_digits) > 1:
        search_digits = search_digits[1:]
    for client in all_clients:
        if category_filter != "Все" and client.get("category", "Покупатель") != category_filter:
            continue
        if search_query:
            client_text = f"{client['name']} {client.get('email','')} {client.get('address','')} {client.get('base_comment','')}".lower()
            match_by_text = search_query in client_text
            all_client_digits = re.sub(r"\D", "", client['phone'])
            for p in client.get("extra_phones", []):
                all_client_digits += " " + re.sub(r"\D", "", p["phone"])
                client_text += " " + p["name"].lower()
            match_by_phone = search_digits and (search_digits in all_client_digits)
            if not (match_by_text or match_by_phone or search_query in client_text):
                continue
        filtered_clients.append(client)

    if all_clients:
        for client in filtered_clients:
            is_target_card = (st.session_state.last_id == client["id"])
            with st.expander(f"{client['name']} — ID: {client['id']} [{client.get('category', 'Покупатель')}]", expanded=is_target_card):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.markdown(f"**{client['phone']}** | {client.get('email','')} | {client.get('address','')}")
                    st.markdown(f"Скидка: **{client.get('discount',0)}%** | Ответственный: **{client.get('manager','—')}**")
                    clean_phone = re.sub(r"\D", "", client['phone'])
                    if clean_phone.startswith("8") and len(clean_phone) == 11:
                        clean_phone = "7" + clean_phone[1:]
                    elif not clean_phone:
                        clean_phone = "79990000000"
                    col_msg1, col_msg2, col_msg3 = st.columns(3)
                    with col_msg1:
                        wa_text = urllib.parse.quote("Здравствуйте! По поводу вашего заказа...")
                        st.link_button("WhatsApp", f"https://wa.me/{clean_phone}?text={wa_text}", use_container_width=True)
                    with col_msg2:
                        st.link_button("Telegram", f"https://t.me/+{clean_phone}", use_container_width=True)
                    with col_msg3:
                        st.link_button("SMS", f"sms:{clean_phone}", use_container_width=True)
                    if client.get("extra_phones"):
                        st.markdown("**Доп. телефоны:**")
                        for p in client["extra_phones"]:
                            st.markdown(f"- {p['phone']} — {p['name']} ({p['role']})")
                    if client.get("extra_addresses"):
                        st.markdown("**Доп. адреса:**")
                        for ea in client["extra_addresses"]:
                            if isinstance(ea, dict):
                                st.markdown(f"- **{ea.get('address', '')}**")
                                if ea.get("resp_name"):
                                    st.markdown(f"  - {ea['resp_name']}, {ea.get('resp_role', '')} — {ea.get('resp_phone', '')}, {ea.get('resp_email', '')}")
                    st.markdown("---")
                    st.markdown('<div class="comments-box">', unsafe_allow_html=True)
                    st.markdown("**Комментарии:**")
                    if client.get("client_comments"):
                        for cc in client["client_comments"]:
                            st.markdown(f"- *{cc.get('time', '')}*: {cc.get('text', '')}")
                    else:
                        st.caption("Пока нет комментариев")
                    new_cc_input = st.text_input("Добавить комментарий:", key=f"new_cc_input_{client['id']}", placeholder="Введите комментарий...")
                    if st.button("Добавить", key=f"cc_btn_{client['id']}", use_container_width=True):
                        if new_cc_input.strip():
                            client.setdefault("client_comments", []).append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": new_cc_input.strip()})
                            commit_and_rerun(st.session_state.crm_store)
                        else:
                            st.warning("Введите текст")
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown("---")
                    st.markdown("**Файлы:**")
                    if "client_files" not in client:
                        client["client_files"] = []
                    for cf_idx, cf in enumerate(client["client_files"]):
                        st.markdown(f"📄 {cf.get('file_name', '')}")
                        render_file_action_buttons(cf.get("file_path"), cf.get("file_name", "файл"), f"cli_{client['id']}_{cf_idx}")
                        if st.button("Удалить файл", key=f"cf_del_{client['id']}_{cf_idx}"):
                            client["client_files"].pop(cf_idx)
                            commit_and_rerun(st.session_state.crm_store)
                    uploaded_cf = st.file_uploader("Загрузить файл:", key=f"cf_up_{client['id']}")
                    if st.button("Сохранить файл", key=f"cf_btn_{client['id']}", use_container_width=True):
                        if uploaded_cf is not None:
                            with st.spinner("Загрузка..."):
                                f_info = save_uploaded_file(uploaded_cf, client["id"], "profile")
                                if f_info:
                                    client["client_files"].append({"file_path": f_info["path"], "file_name": f_info["name"]})
                                    save_data(st.session_state.crm_store)
                                    st.toast("Файл сохранён", icon="📁")
                                    st.rerun()
                        else:
                            st.warning("Выберите файл")
                    with st.expander("Редактировать данные", expanded=False):
                        en = st.text_input("ФИО", value=client['name'], key=f"en_{client['id']}")
                        ep = st.text_input("Телефон", value=client['phone'], key=f"ep_{client['id']}")
                        ee = st.text_input("Email", value=client.get('email',''), key=f"ee_{client['id']}")
                        ea_val = st.text_input("Адрес", value=client.get('address',''), key=f"ea_{client['id']}")
                        ed = st.number_input("Скидка (%)", min_value=0, max_value=100, value=int(client.get('discount',0)), key=f"ed_{client['id']}")
                        ec = st.selectbox("Категория", ["Дизайнер", "Строитель", "Дилер", "Покупатель"], index=["Дизайнер","Строитель","Дилер","Покупатель"].index(client.get('category','Покупатель')) if client.get('category','Покупатель') in ["Дизайнер","Строитель","Дилер","Покупатель"] else 3, key=f"ec_{client['id']}")
                        em_mgr = st.selectbox("Ответственный:", managers, index=managers.index(client.get('manager','')) if client.get('manager','') in managers else 0, key=f"em_{client['id']}")
                        if st.button("Сохранить основные данные", key=f"es_{client['id']}", use_container_width=True):
                            client['name'], client['phone'], client['email'], client['address'], client['discount'], client['category'], client['manager'] = en, format_phone(ep), ee, ea_val, int(ed), ec, em_mgr
                            commit_and_rerun(st.session_state.crm_store)
                        st.markdown("---")
                        with st.expander("Доп. телефоны (редактировать)", expanded=False):
                            for pi, ph in enumerate(client.get("extra_phones", [])):
                                e_ph = st.text_input(f"Телефон #{pi+1}", value=ph.get('phone',''), key=f"ep_e_{client['id']}_{pi}")
                                e_nm = st.text_input(f"ФИО #{pi+1}", value=ph.get('name',''), key=f"ep_n_{client['id']}_{pi}")
                                e_rl = st.text_input(f"Должность #{pi+1}", value=ph.get('role',''), key=f"ep_r_{client['id']}_{pi}")
                                if st.button("Удалить", key=f"ep_del_{client['id']}_{pi}"):
                                    client["extra_phones"].pop(pi)
                                    commit_and_rerun(st.session_state.crm_store)
                            new_ph = st.text_input("Новый телефон", key=f"ep_new_ph_{client['id']}")
                            new_ph_name = st.text_input("Новое ФИО", key=f"ep_new_nm_{client['id']}")
                            new_ph_role = st.text_input("Новая должность", key=f"ep_new_rl_{client['id']}")
                            if st.button("Добавить телефон", key=f"ep_add_btn_{client['id']}"):
                                if new_ph.strip():
                                    client.setdefault("extra_phones", []).append({"phone": format_phone(new_ph), "name": new_ph_name, "role": new_ph_role})
                                    commit_and_rerun(st.session_state.crm_store)
                        with st.expander("Доп. Email (редактировать)", expanded=False):
                            for ei, em in enumerate(client.get("extra_emails", [])):
                                e_em = st.text_input(f"Email #{ei+1}", value=em, key=f"ee_e_{client['id']}_{ei}")
                                if st.button("Удалить", key=f"ee_del_{client['id']}_{ei}"):
                                    client["extra_emails"].pop(ei)
                                    commit_and_rerun(st.session_state.crm_store)
                            new_em = st.text_input("Новый Email", key=f"ee_new_{client['id']}")
                            if st.button("Добавить Email", key=f"ee_add_btn_{client['id']}"):
                                if new_em.strip():
                                    client.setdefault("extra_emails", []).append(new_em.strip())
                                    commit_and_rerun(st.session_state.crm_store)
                        with st.expander("Доп. адреса (редактировать)", expanded=False):
                            for ai, ad in enumerate(client.get("extra_addresses", [])):
                                e_ad_addr = st.text_input(f"Адрес #{ai+1}", value=ad.get('address',''), key=f"ea_a_{client['id']}_{ai}")
                                e_ad_rn = st.text_input(f"Ответственный #{ai+1}", value=ad.get('resp_name',''), key=f"ea_rn_{client['id']}_{ai}")
                                e_ad_rr = st.text_input(f"Должность #{ai+1}", value=ad.get('resp_role',''), key=f"ea_rr_{client['id']}_{ai}")
                                e_ad_rp = st.text_input(f"Телефон #{ai+1}", value=ad.get('resp_phone',''), key=f"ea_rp_{client['id']}_{ai}")
                                e_ad_re = st.text_input(f"Email #{ai+1}", value=ad.get('resp_email',''), key=f"ea_re_{client['id']}_{ai}")
                                if st.button("Удалить адрес", key=f"ea_del_{client['id']}_{ai}"):
                                    client["extra_addresses"].pop(ai)
                                    commit_and_rerun(st.session_state.crm_store)
                            new_ad_addr = st.text_input("Новый адрес", key=f"ea_new_addr_{client['id']}")
                            new_ad_rn = st.text_input("Ответственный", key=f"ea_new_rn_{client['id']}")
                            new_ad_rr = st.text_input("Должность", key=f"ea_new_rr_{client['id']}")
                            new_ad_rp = st.text_input("Телефон", key=f"ea_new_rp_{client['id']}")
                            new_ad_re = st.text_input("Email", key=f"ea_new_re_{client['id']}")
                            if st.button("Добавить адрес", key=f"ea_add_btn_{client['id']}"):
                                if new_ad_addr.strip():
                                    client.setdefault("extra_addresses", []).append({"address": new_ad_addr.strip(), "resp_name": new_ad_rn.strip(), "resp_role": new_ad_rr.strip(), "resp_phone": new_ad_rp.strip(), "resp_email": new_ad_re.strip()})
                                    commit_and_rerun(st.session_state.crm_store)
                        if st.session_state.user_role == "admin":
                            st.markdown("---")
                            st.warning(f"Удаление {client['name']} сотрёт все данные и сделки.")
                            confirm_del = st.checkbox("Подтверждаю удаление", key=f"confirm_del_cli_{client['id']}")
                            if confirm_del:
                                if st.button("Удалить клиента", key=f"del_cli_btn_{client['id']}", use_container_width=True, type="primary"):
                                    st.session_state.crm_store["deals"] = [d for d in st.session_state.crm_store["deals"] if d["client_id"] != client["id"]]
                                    st.session_state.crm_store["clients"] = [c for c in st.session_state.crm_store["clients"] if c["id"] != client["id"]]
                                    st.session_state.last_id = None
                                    commit_and_rerun(st.session_state.crm_store)
                with col_c2:
                    deals = st.session_state.crm_store["deals"]
                    auto_title = f"Заказ №{datetime.now().strftime('%y')}-{(len(deals) + 1):05d}"
                    st.markdown(f"**Новая сделка:**")
                    st.info(f"Будет создан: **{auto_title}**")
                    db = st.number_input("Бюджет (руб.)", min_value=0.0, step=5000.0, key=f"db_{client['id']}")
                    if st.button("Создать сделку", key=f"dbn_{client['id']}", use_container_width=True, type="primary"):
                        max_d_id = max([d['id'] for d in deals]) if deals else 0
                        new_deal_id = max_d_id + 1
                        st.session_state.crm_store["deals"].append({"id": new_deal_id, "client_id": client["id"], "title": auto_title, "budget": db, "status": "Новый", "deal_comments": []})
                        save_data(st.session_state.crm_store)
                        st.session_state.open_deal_id = new_deal_id
                        st.session_state.active_tab = "Сделки"
                        st.rerun()
            if st.session_state.get("last_id"):
                st.session_state.last_id = None
    else:
        st.info("База клиентов пуста. Создайте первого клиента.")

# --- Вкладка «Сделки» ---

elif st.session_state.active_tab == "Сделки":
    st.header("Сделки")
    deal_search = st.text_input("Поиск по сделкам (название, клиент, трек-номер, получатель):", key="deal_search_input", placeholder="Введите текст...").strip().lower()
    current_user_name = st.session_state.user_name
    managers = get_managers_list()

    client_index = {c["id"]: c for c in st.session_state.crm_store["clients"]}
    _default_client = {"name": "Неизвестно", "phone": "-", "comments": [], "tasks": [], "category": "Покупатель", "discount": 0, "manager": ""}

    def get_client(c_id):
        return client_index.get(c_id, _default_client)

    def deal_matches_search(deal, search):
        if not search:
            return True
        client = get_client(deal["client_id"])
        searchable = f"{deal['title']} {client['name']}".lower()
        for t in client.get("tasks", []):
            searchable += f" {t.get('tk_num', '')} {t.get('receiver', '')}"
        return search in searchable

    def deal_has_overdue(deal):
        client = get_client(deal["client_id"])
        for t in client.get("tasks", []):
            if not t.get("done") and is_task_overdue(t):
                return True
        return False

    def deal_has_tasks(deal):
        client = get_client(deal["client_id"])
        return len(client.get("tasks", [])) > 0

    dl = st.session_state.crm_store["deals"]
    t_new = sum(d.get("budget",0) for d in dl if d["status"] == "Новый")
    t_prg = sum(d.get("budget",0) for d in dl if d["status"] == "В работе")
    t_cls = sum(d.get("budget",0) for d in dl if d["status"] == "Сделка закрыта")
    st_new, st_prg, st_cls = st.columns(3)

    def draw_deal_card(deal, client):
        is_open = (st.session_state.get("open_deal_id") == deal["id"])
        has_overdue = deal_has_overdue(deal)
        has_tasks = deal_has_tasks(deal)
        with st.container(border=True):
            if has_overdue:
                color_container_border("#D65757")
            elif not has_tasks:
                color_container_border("#4CAF50")
            card_title = f"{deal['title']} | {client['name']} ({deal.get('budget', 0):,.0f} руб.)".replace(",", " ")
            with st.expander(card_title, expanded=is_open):
                st.caption(f"Категория: [{client.get('category','Покупатель')}] | Скидка: {client.get('discount',0)}% | {client['phone']} | Ответственный: {client.get('manager','—')}")
                st.markdown("---")
                if deal.get("deal_comments"):
                    for com in deal["deal_comments"]:
                        st.markdown(f"*{com['time']}* — {com['text']}")
                input_key = f"ndc_val_{deal['id']}"
                ndc = st.text_input("Заметка к заказу:", key=input_key, placeholder="Например: Согласовали доставку")
                if st.button("Сохранить заметку", key=f"ndcb_{deal['id']}", use_container_width=True):
                    if ndc.strip():
                        deal["deal_comments"].append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": ndc.strip()})
                        save_data(st.session_state.crm_store)
                        if input_key in st.session_state:
                            del st.session_state[input_key]
                        st.rerun()
                st.markdown("---")
                if client.get("comments"):
                    with st.expander("Отчёты по задачам"):
                        for com in client["comments"]:
                            st.markdown(f"*{com['time']}* — {com.get('text', '')}")
                            if com.get("file_path"):
                                render_file_action_buttons(com["file_path"], com.get("file_name", "файл"), f"dcom_{deal['id']}_{com['time'].replace(':','_')}")
                st.markdown("**Задачи:**")
                if client.get("tasks"):
                    for i, task in enumerate(client["tasks"]):
                        t_type = task.get("type", "Связаться")
                        task_overdue = is_task_overdue(task)
                        formatted_dl = format_date(task.get("deadline", ""))
                        if task.get("done"):
                            header_t = f"✅ {t_type} — {formatted_dl}"
                        else:
                            header_t = f"{t_type} — {formatted_dl} — {task.get('manager','—')}"
                        with st.expander(header_t, expanded=False):
                            if task_overdue:
                                color_expander_border("#D65757")
                            if task.get("done"):
                                st.markdown(f"~~{task['text']}~~ — выполнено")
                            else:
                                st.markdown(f"**{t_type}** | Срок: {formatted_dl} | Ответственный: {task.get('manager','—')}")
                                if t_type == "Отправить заказ":
                                    with st.container(border=True):
                                        st.markdown(f"Товары: {task.get('products', '')}")
                                        st.markdown(f"Адрес: {task.get('ship_addr', '')}")
                                        st.markdown(f"Получатель: {task.get('receiver', '')} ({task.get('receiver_phone', '')})")
                                        st.markdown(f"Оплата: {task.get('ship_pay', '')}")
                                        if task.get('order_amount', 0) > 0:
                                            oa = task['order_amount']
                                            dp = client.get('discount', 0)
                                            da = oa * dp / 100
                                            ta = oa - da
                                            st.markdown(f"Сумма: {oa:,.0f} | Скидка: {dp}% ({da:,.0f}) | **Итого: {ta:,.0f}**".replace(",", " "))
                                        if task.get('tk_num'):
                                            st.markdown(f"Трек: `{task['tk_num']}`")
                                if task.get("file_path"):
                                    st.markdown(f"📄 {task.get('file_name', '')}")
                                    render_file_action_buttons(task["file_path"], task.get("file_name", ""), f"dtk_{deal['id']}_{i}")
                                new_task_file_d = st.file_uploader("Добавить файл:", key=f"ntf_d_{deal['id']}_{i}")
                                if st.button("Сохранить файл", key=f"stf_d_{deal['id']}_{i}"):
                                    if new_task_file_d:
                                        f_info = save_uploaded_file(new_task_file_d, deal['id'], "task_file")
                                        if f_info:
                                            task["file_path"] = f_info["path"]
                                            task["file_name"] = f_info["name"]
                                            commit_and_rerun(st.session_state.crm_store)
                                with st.expander("Редактировать", expanded=False):
                                    new_mgr = st.selectbox("Ответственный:", managers, index=managers.index(task.get("manager", current_user_name)) if task.get("manager", current_user_name) in managers else 0, key=f"ed_mgr_d_{deal['id']}_{i}")
                                    if t_type == "Отправить заказ":
                                        edit_oa = st.number_input("Сумма (руб.)", min_value=0.0, step=100.0, value=float(task.get("order_amount", 0)), key=f"ed_oa_d_{deal['id']}_{i}")
                                    curr_d = parse_deadline(task.get("deadline", ""))
                                    edit_dl = st.date_input("Срок", value=curr_d, format="DD/MM/YYYY", key=f"ed_dl_d_{deal['id']}_{i}")
                                    if st.button("Сохранить", key=f"ed_t_btn_d_{deal['id']}_{i}", use_container_width=True):
                                        task["manager"] = new_mgr
                                        task["deadline"] = edit_dl.isoformat()
                                        if t_type == "Отправить заказ":
                                            task["order_amount"] = edit_oa
                                        commit_and_rerun(st.session_state.crm_store)
                                if not task.get("done"):
                                    if st.checkbox("Выполнить", key=f"tsk_{deal['id']}_{i}"):
                                        with st.container(border=True):
                                            rt = st.text_input("Отчёт:", key=f"rt_{deal['id']}_{i}")
                                            uf = st.file_uploader("Файл/фото отчёта:", key=f"uf_{deal['id']}_{i}")
                                            create_next_d = st.checkbox("Создать следующую задачу", key=f"cn_{deal['id']}_{i}")
                                            new_ex_d = {}
                                            new_td_d = None
                                            new_t_type_d = None
                                            new_t_mgr_d = None
                                            if create_next_d:
                                                st.markdown("---")
                                                new_t_type_d = st.selectbox("Тип:", ["Связаться", "Отправить заказ"], key=f"nt_type_d_{deal['id']}_{i}")
                                                new_t_mgr_d = st.selectbox("Ответственный:", managers, index=managers.index(current_user_name) if current_user_name in managers else 0, key=f"nt_mgr_d_{deal['id']}_{i}")
                                                if new_t_type_d == "Отправить заказ":
                                                    new_ex_d["products"] = st.text_area("Товары", key=f"nt_p_d_{deal['id']}_{i}")
                                                    new_ex_d["ship_addr"] = st.text_input("Адрес", key=f"nt_a_d_{deal['id']}_{i}")
                                                    new_ex_d["receiver"] = st.text_input("Получатель", key=f"nt_r_d_{deal['id']}_{i}")
                                                    new_ex_d["receiver_phone"] = format_phone(st.text_input("Тел.", key=f"nt_rp_d_{deal['id']}_{i}"))
                                                    new_ex_d["ship_pay"] = st.selectbox("Оплата", ["Включено в счёт", "Оплата при получении"], key=f"nt_sp_d_{deal['id']}_{i}")
                                                    new_ex_d["tk_num"] = st.text_input("Трек", key=f"nt_tk_d_{deal['id']}_{i}")
                                                    new_ex_d["order_amount"] = st.number_input("Сумма", min_value=0.0, step=100.0, key=f"nt_oa_d_{deal['id']}_{i}")
                                                    new_ex_d["task_comment"] = st.text_area("Комментарии", key=f"nt_c_d_{deal['id']}_{i}")
                                                else:
                                                    new_ex_d["order_amount"] = 0
                                                    new_ex_d["task_comment"] = st.text_area("Комментарии", key=f"nt_cs_d_{deal['id']}_{i}")
                                                new_td_d = st.date_input("Дата", format="DD/MM/YYYY", key=f"nt_d_d_{deal['id']}_{i}")
                                            if st.button("Подтвердить", key=f"cbtn_{deal['id']}_{i}", use_container_width=True, type="primary"):
                                                if rt.strip():
                                                    with st.spinner("Сохранение..."):
                                                        task["done"] = True
                                                        f_info = save_uploaded_file(uf, deal['id'], "task_report")
                                                        rep = f"Закрыта [{t_type}] '{task['text']}'. Отчёт: {rt.strip()}"
                                                        if t_type == "Отправить заказ":
                                                            rep += f" | Кому: {task.get('receiver', '')} | Трек: {task.get('tk_num', 'нет')}"
                                                        client["comments"].append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": rep, "file_path": f_info["path"] if f_info else None, "file_name": f_info["name"] if f_info else None})
                                                        if create_next_d and new_t_type_d:
                                                            auto_title_d = auto_task_title(new_t_type_d, client['name'], deal['title'])
                                                            t_ent_d = {"text": auto_title_d, "deadline": new_td_d.isoformat(), "done": False, "type": new_t_type_d, "file_path": None, "file_name": None, "manager": new_t_mgr_d}
                                                            t_ent_d.update(new_ex_d)
                                                            client["tasks"].append(t_ent_d)
                                                        commit_and_rerun(st.session_state.crm_store)
                                                else:
                                                    st.warning("Введите отчёт")
                else:
                    st.caption("Нет задач.")
                dfv = f"{st.session_state.deal_form_version}_{deal['id']}"
                with st.expander("Новая задача", expanded=False, key=f"new_task_exp_{dfv}"):
                    color_expander_border("#4CAF50")
                    task_type = st.selectbox("Тип:", ["Связаться", "Отправить заказ"], key=f"t_type_sel_{dfv}")
                    new_task_manager = st.selectbox("Ответственный:", managers, index=managers.index(current_user_name) if current_user_name in managers else 0, key=f"t_mgr_{dfv}")
                    ex_data = {}
                    if task_type == "Отправить заказ":
                        ex_data["products"] = st.text_area("Товары", key=f"t_p_{dfv}")
                        ex_data["ship_addr"] = st.text_input("Адрес", key=f"t_a_{dfv}")
                        ex_data["receiver"] = st.text_input("ФИО получателя", key=f"t_r_{dfv}")
                        ex_data["receiver_phone"] = format_phone(st.text_input("Тел. получателя", key=f"t_rp_{dfv}"))
                        ex_data["ship_pay"] = st.selectbox("Оплата", ["Включено в счёт", "Оплата при получении"], key=f"t_sp_{dfv}")
                        ex_data["tk_num"] = st.text_input("Трек-номер", key=f"t_tk_{dfv}")
                        ex_data["order_amount"] = st.number_input("Сумма (руб.)", min_value=0.0, step=100.0, key=f"t_oa_{dfv}")
                        ex_data["task_comment"] = st.text_area("Комментарии", key=f"t_c_{dfv}")
                    else:
                        ex_data["order_amount"] = 0
                        ex_data["task_comment"] = st.text_area("Комментарии", key=f"t_cs_{dfv}")
                    t_uf = st.file_uploader("Прикрепить файл:", key=f"t_f_{dfv}")
                    td = st.date_input("Дата", format="DD/MM/YYYY", key=f"td_{dfv}")
                    if st.button("Поставить задачу", key=f"tsv_{dfv}", use_container_width=True):
                        f_info = save_uploaded_file(t_uf, deal['id'], "task_init")
                        auto_title = auto_task_title(task_type, client['name'], deal['title'])
                        t_ent = {"text": auto_title, "deadline": td.isoformat(), "done": False, "type": task_type, "file_path": f_info["path"] if f_info else None, "file_name": f_info["name"] if f_info else None, "manager": new_task_manager}
                        t_ent.update(ex_data)
                        client.setdefault("tasks", []).append(t_ent)
                        if f_info:
                            client["comments"].append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": f"Файл: {f_info['name']}", "file_path": f_info["path"], "file_name": f_info["name"]})
                        save_data(st.session_state.crm_store)
                        st.session_state.deal_form_version += 1
                        st.toast("Задача добавлена", icon="✅")
                        st.rerun()
                st.markdown("---")
                cb1, cb2 = st.columns(2)
                if deal['status'] == "Новый":
                    if cb1.button("В работу", key=f"wf_{deal['id']}", use_container_width=True):
                        deal['status'] = "В работе"
                        commit_and_rerun(st.session_state.crm_store)
                elif deal['status'] == "В работе":
                    if cb1.button("Назад", key=f"wb_{deal['id']}", use_container_width=True):
                        deal['status'] = "Новый"
                        commit_and_rerun(st.session_state.crm_store)
                    if cb2.button("Завершить сделку", key=f"wc_{deal['id']}", use_container_width=True, type="primary"):
                        close_deal_dialog(deal['id'])
                elif deal['status'] == "Сделка закрыта":
                    if cb1.button("Возобновить", key=f"wr_{deal['id']}", use_container_width=True):
                        deal['status'] = "В работе"
                        commit_and_rerun(st.session_state.crm_store)
                    if cb2.button("В архив", key=f"ar_{deal['id']}", use_container_width=True):
                        deal['status'] = "Архив"
                        commit_and_rerun(st.session_state.crm_store)
                elif deal['status'] == "Архив":
                    if cb1.button("Возобновить", key=f"ura_{deal['id']}", use_container_width=True):
                        deal['status'] = "В работе"
                        commit_and_rerun(st.session_state.crm_store)

    with st_new:
        st.markdown(f"#### Новые  \n`{t_new:,.0f} руб.`")
        for d in dl:
            if d["status"] == "Новый" and deal_matches_search(d, deal_search):
                draw_deal_card(d, get_client(d["client_id"]))
    with st_prg:
        st.markdown(f"#### В работе  \n`{t_prg:,.0f} руб.`")
        for d in dl:
            if d["status"] == "В работе" and deal_matches_search(d, deal_search):
                draw_deal_card(d, get_client(d["client_id"]))
    with st_cls:
        st.markdown(f"#### Закрыты  \n`{t_cls:,.0f} руб.`")
        for d in dl:
            if d["status"] == "Сделка закрыта" and deal_matches_search(d, deal_search):
                draw_deal_card(d, get_client(d["client_id"]))

    if st.session_state.get("open_deal_id") is not None:
        st.session_state.open_deal_id = None

    archived_deals = [d for d in dl if d["status"] == "Архив" and deal_matches_search(d, deal_search)]
    if archived_deals:
        st.markdown("---")
        with st.expander(f"Архив ({len(archived_deals)})", expanded=False):
            for d in archived_deals:
                draw_deal_card(d, get_client(d["client_id"]))
