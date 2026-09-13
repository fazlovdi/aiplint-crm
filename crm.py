import streamlit as st
import streamlit.components.v1 as components
import json, os, re, urllib.parse, requests, hashlib, base64, csv, io, secrets, threading, uuid
from datetime import datetime

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
    h1 { font-size: 1.75rem; margin-bottom: 0.5rem; } h2 { font-size: 1.4rem; margin-top: 1rem; } h3 { font-size: 1.1rem; }
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
    ::-webkit-scrollbar { width: 8px; height: 8px; } ::-webkit-scrollbar-track { background: transparent; } ::-webkit-scrollbar-thumb { background: #C9CFD7; border-radius: 4px; }
    .stMarkdown p, .stMarkdown li { color: #3C4A5A; line-height: 1.6; }
    .stMarkdown strong { color: #2C3E50; font-weight: 600; }
    code { background-color: #EEF0F3; color: #5A6B7D; border-radius: 6px; padding: 0.1rem 0.35rem; font-size: 0.9em; }
    .stHorizontalBlock .stButton button { border-radius: 12px; font-size: 0.95rem; font-weight: 600; padding: 0.65rem 1rem; }
    [data-testid="stFileUploader"] { border-radius: 14px; border: 2px dashed #C9CFD7; background-color: #FAFBFC; padding: 0.75rem; }
    .deal-col-header h4 { margin: 0; font-size: 1.1rem; }
    .deal-col-header p { margin: 0.2rem 0 0.8rem 0; color: #7F8C9A; font-size: 0.85rem; }
    .greeting-block { margin-bottom: 1.5rem !important; }
    .phone-action-group { display: flex; align-items: center; gap: 6px; white-space: nowrap; }
    .phone-btn { background: #EEF0F3 !important; border: 1px solid #DCE0E5 !important; border-radius: 8px !important; padding: 6px 10px !important; font-size: 0.85rem !important; color: #5A6B7D !important; cursor: pointer !important; min-width: 44px !important; height: 32px !important; display: inline-flex; align-items: center; justify-content: center; }
    .phone-btn:hover { background: #DCE0E5 !important; }
</style>
""", unsafe_allow_html=True)

FILE_NAME = "web_crm_database_v2.json"
YANDEX_API_URL = "https://cloud-api.yandex.net/v1/disk/resources"
MAX_URL = "https://max.ru"
MAX_NUMBER = "+79003293300"

raw_token = st.secrets.get("YANDEX_DISK_TOKEN", "")
if isinstance(raw_token, str):
    YANDEX_TOKEN = raw_token.strip().strip('"').strip("'")
else:
    YANDEX_TOKEN = ""

# --- Цветные рамки ---

def inject_border_css(key, color):
    if color:
        st.markdown(f"""
        <style>
            .st-key-{key} > .stExpander > details {{
                border: 2px solid {color} !important;
                border-radius: 14px !important;
            }}
        </style>
        """, unsafe_allow_html=True)

# --- Пароли ---

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

# --- Яндекс.Диск ---

def yandex_headers():
    return {"Authorization": f"OAuth {YANDEX_TOKEN}", "Accept": "application/json"}

def check_cloud_status():
    if not YANDEX_TOKEN: return False
    try:
        res = requests.get(YANDEX_API_URL, headers=yandex_headers(), timeout=5)
        return res.status_code == 200
    except Exception: return False

def init_yandex_folders():
    if not YANDEX_TOKEN: return
    for folder in ["CRM_NE_TROGAT", "CRM_NE_TROGAT/uploads"]:
        try: requests.put(YANDEX_API_URL, params={"path": f"disk:/{folder}"}, headers=yandex_headers(), timeout=10)
        except Exception: pass

def download_db_from_yandex():
    if not YANDEX_TOKEN: return
    try:
        res = requests.get(f"{YANDEX_API_URL}/download", params={"path": f"disk:/CRM_NE_TROGAT/{FILE_NAME}"}, headers=yandex_headers(), timeout=10)
        if res.status_code == 200:
            dl = requests.get(res.json().get("href"), timeout=30)
            if dl.status_code == 200:
                with open(FILE_NAME, "w", encoding="utf-8") as f: f.write(dl.text)
                return
    except Exception: pass
    if not os.path.exists(FILE_NAME):
        db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}], "_migrated": "v2"}
        with open(FILE_NAME, "w", encoding="utf-8") as f: json.dump(db, f, ensure_ascii=False, indent=2)

def upload_db_to_yandex_async():
    if not YANDEX_TOKEN or not os.path.exists(FILE_NAME): return
    def _u():
        try:
            res = requests.get(f"{YANDEX_API_URL}/upload", params={"path": f"disk:/CRM_NE_TROGAT/{FILE_NAME}", "overwrite": "true"}, headers=yandex_headers(), timeout=10)
            if res.status_code == 200:
                with open(FILE_NAME, "rb") as f: requests.put(res.json().get("href"), data=f, timeout=30)
        except Exception: pass
    threading.Thread(target=_u, daemon=True).start()

def upload_file_to_yandex(file_bytes, remote_name):
    if not YANDEX_TOKEN: return False
    try:
        res = requests.get(f"{YANDEX_API_URL}/upload", params={"path": f"disk:/CRM_NE_TROGAT/uploads/{remote_name}", "overwrite": "true"}, headers=yandex_headers(), timeout=10)
        if res.status_code == 200:
            return requests.put(res.json().get("href"), data=file_bytes, timeout=30).status_code in (200, 201)
    except Exception: pass
    return False

@st.cache_data(ttl=300, show_spinner=False)
def download_file_from_yandex(remote_path):
    if not YANDEX_TOKEN: return None
    try:
        res = requests.get(f"{YANDEX_API_URL}/download", params={"path": f"disk:/{remote_path}"}, headers=yandex_headers(), timeout=10)
        if res.status_code == 200:
            fr = requests.get(res.json().get("href"), timeout=30)
            if fr.status_code == 200: return fr.content
    except Exception: pass
    return None

# --- Утилиты ---

def format_phone(p_str):
    if not p_str: return ""
    d = re.sub(r"\D", "", p_str)
    if len(d) == 11 and d[0] in ("7", "8"): d = d[1:]
    if len(d) == 10: return f"+7 {d[0:3]} {d[3:6]}-{d[6:8]}-{d[8:10]}"
    return p_str.strip()

def save_uploaded_file(u_file, c_id, prefix=""):
    if u_file is None: return None
    name = f"{c_id}_{prefix}_{int(datetime.now().timestamp())}_{u_file.name}"
    b = u_file.getvalue()
    if YANDEX_TOKEN:
        rp = f"CRM_NE_TROGAT/uploads/{name}"
        if upload_file_to_yandex(b, name): return {"path": rp, "name": u_file.name}
        st.warning("Не удалось загрузить на Диск, файл сохранён локально")
    os.makedirs("uploads", exist_ok=True)
    lp = f"uploads/{name}"
    with open(lp, "wb") as f: f.write(b)
    return {"path": lp, "name": u_file.name}

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
    return o.getvalue().encode("utf-8-sig")

def get_client_by_id(c_id):
    for c in st.session_state.crm_store["clients"]:
        if c["id"] == c_id: return c
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
    try: return datetime.strptime(dl, "%Y-%m-%d").date() < datetime.now().date()
    except:
        try: return datetime.strptime(dl, "%Y-%m-%d %H:%M") < datetime.now()
        except: return False

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

def get_managers_list():
    return [u.get("name", u["login"]) for u in st.session_state.crm_store.get("users", []) if u.get("role") != "admin"]

def auto_task_title(tt, cn, dt):
    if tt == "Отправить заказ": return f"Отправка по {dt}" if dt else f"Отправка: {cn}"
    return f"Связаться: {cn}"

# --- Телефон с кнопками ---

def render_phone_inline(phone, uid):
    cph = re.sub(r"\D", "", phone)
    if cph.startswith("8") and len(cph) == 11: cph = "7" + cph[1:]
    elif not cph: cph = "79990000000"
    components.html(f"""
    <div class="phone-action-group" style="padding:4px 0;">
        <span style="font-size:1rem;font-weight:600;color:#2C3E50;">{phone}</span>
        <button onclick="navigator.clipboard.writeText('{phone}').then(function(){{var b=this;b.textContent='✓';setTimeout(function(){{b.textContent='📋';}},1500);}}.bind(this));" class="phone-btn" title="Скопировать">📋</button>
        <a href="tel:+{cph}" class="phone-btn" style="text-decoration:none;" title="Позвонить">📞</a>
    </div>
    """, height=40)

def render_extra_phone_inline(phone, name, role, uid):
    cph = re.sub(r"\D", "", phone)
    if cph.startswith("8") and len(cph) == 11: cph = "7" + cph[1:]
    elif not cph: cph = "79990000000"
    info = f"{phone} — {name} ({role})" if name else phone
    components.html(f"""
    <div class="phone-action-group" style="padding:2px 0;flex-wrap:wrap;">
        <span style="font-size:0.9rem;color:#3C4A5A;">{info}</span>
        <button onclick="navigator.clipboard.writeText('{phone}').then(function(){{var b=this;b.textContent='✓';setTimeout(function(){{b.textContent='📋';}},1500);}}.bind(this));" style="background:#EEF0F3;border:1px solid #DCE0E5;border-radius:6px;padding:4px 8px;cursor:pointer;font-size:0.8rem;color:#5A6B7D;min-width:36px;height:28px;display:inline-flex;align-items:center;justify-content:center;" title="Скопировать">📋</button>
        <a href="tel:+{cph}" style="background:#EEF0F3;border:1px solid #DCE0E5;border-radius:6px;padding:4px 8px;text-decoration:none;font-size:0.8rem;color:#5A6B7D;min-width:36px;height:28px;display:inline-flex;align-items:center;justify-content:center;" title="Позвонить">📞</a>
    </div>
    """, height=32)

def render_file_action_buttons(fp, fn, kp):
    if fp and not fp.startswith("CRM_NE_TROGAT") and os.path.exists(fp):
        try:
            with open(fp, "rb") as f: fb = f.read()
        except: fb = None
    else:
        rp = normalize_remote_path(fp)
        fb = download_file_from_yandex(rp) if rp else None
    if not fb: st.caption("Файл недоступен"); return
    ext = os.path.splitext(fn)[1].lower()
    if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
        try: st.image(fb, caption=fn)
        except: pass
        c1, c2 = st.columns(2)
        with c1: st.download_button("Скачать", data=fb, file_name=fn, key=f"dl_{kp}")
        with c2:
            b64 = base64.b64encode(fb).decode()
            mt = f"image/{'jpeg' if ext == '.jpg' else ext[1:]}"
            safe_kp = re.sub(r'[^a-zA-Z0-9_]', '_', kp)
            btn_id = f"img_print_btn_{safe_kp}"
            js_func = f"doImgPrint_{safe_kp}"
            var_name = f"_img_{safe_kp}"
            img_html_json = json.dumps(f"<html><head><meta charset='utf-8'></head><body style='margin:0;text-align:center;'><img src='data:{mt};base64,{b64}' style='max-width:100%;' /></body></html>")
            components.html(f"""
            <style>
            #{btn_id} {{ width: 100%; padding: 8px; background: #bc1661; color: white; border: none; border-radius: 10px; cursor: pointer; font-size: 14px; font-weight: 600; transition: background 0.15s; }}
            #{btn_id}:hover {{ background: #9a1452; }}
            </style>
            <button id="{btn_id}" onclick="{js_func}()">Распечатать</button>
            <script>
            var {var_name} = {img_html_json};
            function {js_func}() {{
                var w = window.open('', '_blank');
                if (!w) {{ alert('Разрешите всплывающие окна для печати'); return; }}
                w.document.open(); w.document.write({var_name}); w.document.close(); w.focus();
                setTimeout(function() {{ try {{ w.print(); }} catch(e) {{}} }}, 500);
                w.onafterprint = function() {{ setTimeout(function() {{ w.close(); }}, 300); }};
            }}
            </script>
            """, height=45)
    elif ext == ".pdf":
        st.download_button("Открыть / Скачать PDF", data=fb, file_name=fn, mime="application/pdf", key=f"dl_{kp}")
    else:
        st.download_button("Скачать", data=fb, file_name=fn, key=f"dl_{kp}")

# --- Печать задачи ---

def build_print_html(task, cl, tp, fd):
    def esc(s): return str(s if s else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    products_html = esc(task.get('products', '')).replace('\n', '<br>')
    oav = task.get('order_amount', 0)
    dpc = cl.get('discount', 0)
    dam = oav * dpc / 100
    tam = oav - dam
    cost_html = ""
    if oav and oav > 0:
        cost_html = (f"<div style='margin-top:6px;'>Сумма: {oav:,.0f} руб.</div>"
            f"<div>Скидка: {dpc}% ({dam:,.0f} руб.)</div>"
            f"<div style='font-size:16px;font-weight:bold;'>Итого: {tam:,.0f} руб.</div>").replace(",", " ")
    file_reminder = ""
    if task.get("file_path"):
        file_reminder = ("<div style='color:#D65757;font-weight:bold;margin:14px 0;border:2px solid #D65757;padding:8px;border-radius:8px;'>&#9888; Не забудь распечатать вложенный файл!</div>")
    lb = get_logo_base64()
    logo_html = f"<img src='data:image/png;base64,{lb}' width='180' style='float:left;margin-right:20px;'/>" if lb else "<div style='font-size:24px;font-weight:bold;float:left;margin-right:20px;'>АЙПЛИНТ</div>"
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><title>Бланк задачи</title>
<style>body {{ font-family: Arial, sans-serif; margin: 40px; color: #222; }} .clearfix::after {{ content: ""; display: table; clear: both; }} .header {{ text-align: center; border-bottom: 2px solid #333; padding: 10px; }} .row {{ margin: 8px 0; }} hr {{ border: none; border-top: 1px solid #ccc; margin: 14px 0; }} .sig {{ margin-top: 30px; }} .sig p {{ margin: 12px 0; }} @media print {{ body {{ margin: 15px; }} }}</style>
</head><body><div class="clearfix">{logo_html}</div>
<div class="header"><h2>БЛАНК ЗАДАЧИ</h2><p>{datetime.now().strftime('%d/%m/%Y')}</p></div>
<div class="row"><b>Клиент:</b> {esc(cl['name'])} ({esc(cl['phone'])})</div>
<div class="row"><b>Тип:</b> {esc(tp)}</div><div class="row"><b>Срок:</b> {esc(fd)}</div>
<div class="row"><b>Ответственный:</b> {esc(task.get('manager', ''))}</div><hr>
<div class="row"><b>Товары:</b><br>{products_html}</div>
<div class="row"><b>Адрес:</b> {esc(task.get('ship_addr', ''))}</div>
<div class="row"><b>Получатель:</b> {esc(task.get('receiver', ''))} ({esc(task.get('receiver_phone', ''))})</div>
<div class="row"><b>Оплата:</b> {esc(task.get('ship_pay', ''))}</div>
<div class="row"><b>Трек:</b> {esc(task.get('tk_num', ''))}</div>{cost_html}{file_reminder}
<div class="sig"><p>Отпустил: _____________</p><p>Получил: _____________</p></div></body></html>"""

def render_print_button(task, cl, tp, fd, key_suffix):
    html_content = build_print_html(task, cl, tp, fd)
    html_json = json.dumps(html_content).replace('<', '\\u003c')
    safe_key = key_suffix.replace('-', '_').replace('.', '_')
    btn_id = f"print_btn_{safe_key}"
    js_func = f"doPrint_{safe_key}"
    var_name = f"_pd_{safe_key}"
    components.html(f"""
    <style>#{btn_id} {{ width: 100%; padding: 10px; background: #bc1661; color: white; border: none; border-radius: 10px; cursor: pointer; font-size: 14px; font-weight: 600; font-family: inherit; transition: background 0.15s; }} #{btn_id}:hover {{ background: #9a1452; }}</style>
    <button id="{btn_id}" onclick="{js_func}()">Распечатать задачу</button>
    <script>var {var_name} = {html_json};
    function {js_func}() {{
        var html = {var_name}; var w = window.open('', '_blank');
        if (!w) {{ alert('Разрешите всплывающие окна для печати'); return; }}
        w.document.open(); w.document.write(html); w.document.close(); w.focus();
        setTimeout(function() {{ try {{ w.print(); }} catch(e) {{}} }}, 500);
        w.onafterprint = function() {{ setTimeout(function() {{ w.close(); }}, 300); }};
    }}</script>
    """, height=45)

# --- Данные ---

def migrate_data(data):
    du = [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}]
    if "users" not in data: data["users"] = du
    for u in data["users"]:
        if not is_hashed(u.get("password", "")): u["password"] = hash_password(u["password"])
        if "remember_tokens" not in u: u["remember_tokens"] = []
    for c in data.get("clients", []):
        for k, v in [("email",""),("address",""),("base_comment",""),("category","Покупатель"),("discount",0),("extra_phones",[]),("extra_emails",[]),("extra_addresses",[]),("client_files",[]),("client_comments",[]),("manager",""),("comments",[]),("tasks",[])]:
            if k not in c or c[k] == "-": c[k] = v
        for ea in c.get("extra_addresses", []):
            if isinstance(ea, str): c["extra_addresses"][c["extra_addresses"].index(ea)] = {"address": ea, "resp_name": "", "resp_role": "", "resp_phone": "", "resp_email": ""}
        for t in c.get("tasks", []):
            if "manager" not in t: t["manager"] = c.get("manager", "")
            if "deadline" in t and " " in str(t["deadline"]): t["deadline"] = str(t["deadline"]).split(" ")[0]
            if "completion_report" not in t: t["completion_report"] = ""
            if "completion_file_path" not in t: t["completion_file_path"] = None
            if "completion_file_name" not in t: t["completion_file_name"] = None
    for d in data.get("deals", []):
        if "deal_comments" not in d: d["deal_comments"] = []
        if d.get("status") == "New": d["status"] = "Новый"
    data["_migrated"] = "v2"
    return data

def load_data():
    download_db_from_yandex()
    db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}], "_migrated": "v2"}
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as f: data = json.load(f)
            if data.get("_migrated") != "v2":
                data = migrate_data(data)
                with open(FILE_NAME, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)
                upload_db_to_yandex_async()
            else:
                for c in data.get("clients", []):
                    for t in c.get("tasks", []):
                        if "completion_report" not in t: t["completion_report"] = ""
                        if "completion_file_path" not in t: t["completion_file_path"] = None
                        if "completion_file_name" not in t: t["completion_file_name"] = None
            return data
        except: return db
    return db

def save_data(data):
    try:
        with open(FILE_NAME, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)
        upload_db_to_yandex_async()
    except Exception as e: st.sidebar.error(f"Ошибка сохранения: {e}")

def commit_and_rerun(data=None, toast_msg=None):
    if data is not None: save_data(data)
    if toast_msg: st.toast(toast_msg, icon="✅")
    st.rerun()

@st.dialog("Завершить сделку", width="medium")
def close_deal_dialog(deal_id):
    deal = None
    for d in st.session_state.crm_store["deals"]:
        if d["id"] == deal_id: deal = d; break
    if not deal: st.error("Сделка не найдена"); return
    client = get_client_by_id(deal["client_id"])
    incomplete = [t for t in (client.get("tasks", []) if client else []) if not t.get("done")]
    if incomplete:
        st.warning(f"Нельзя завершить сделку: {len(incomplete)} невыполненных задач(и).")
        st.markdown("**Невыполненные задачи:**")
        for t in incomplete:
            st.markdown(f"- {t.get('type', 'Связаться')} — {format_date(t.get('deadline', ''))} — {t.get('text', '')}")
        if st.button("Понятно", use_container_width=True): st.rerun()
        return
    st.markdown("Заполните отчёт о выполнении сделки:")
    report = st.text_area("Отчёт (обязательно):", key=f"close_deal_report_{deal_id}")
    if st.button("Завершить сделку", type="primary", use_container_width=True):
        if report.strip():
            for d in st.session_state.crm_store["deals"]:
                if d["id"] == deal_id:
                    d['status'] = "Сделка закрыта"; d['closed_date'] = datetime.now().strftime("%Y-%m-%d"); d['close_report'] = report.strip(); break
            save_data(st.session_state.crm_store)
            st.toast("Сделка завершена", icon="✅"); st.rerun()
        else: st.error("Заполните отчёт")

# --- Session state ---

if "crm_store" not in st.session_state:
    with st.spinner("Загрузка данных..."): st.session_state.crm_store = load_data()
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
    init_yandex_folders(); st.session_state.yandex_folders_ready = True
if "current_remember_token" not in st.session_state: st.session_state.current_remember_token = None
if "set_remember_token" not in st.session_state: st.session_state.set_remember_token = None
if "deal_note_ver" not in st.session_state: st.session_state.deal_note_ver = {}

# --- Авторизация ---

def check_login(username, password):
    for u in st.session_state.crm_store.get("users", []):
        if u["login"] == username.strip() and verify_password(password, u["password"]):
            st.session_state.authenticated = True
            st.session_state.user_role = u["role"]
            st.session_state.user_login = u["login"]
            st.session_state.user_name = u.get("name", u["login"])
            return True
    return False

def find_user_by_token(token):
    for u in st.session_state.crm_store.get("users", []):
        if token in u.get("remember_tokens", []): return u
    return None

def clear_remember_token():
    current = st.session_state.get("current_remember_token")
    if current:
        for u in st.session_state.crm_store.get("users", []):
            if u["login"] == st.session_state.user_login:
                if current in u.get("remember_tokens", []): u["remember_tokens"].remove(current)
                break
        save_data(st.session_state.crm_store)
    components.html("<script>try{localStorage.removeItem('crm_remember_token');}catch(e){}</script>", height=0)
    try: del st.query_params["remember_token"]
    except: pass

if not st.session_state.authenticated:
    try: qp_token = st.query_params.get("remember_token", None)
    except AttributeError: qp_token = None
    if qp_token:
        user = find_user_by_token(qp_token)
        if user:
            st.session_state.authenticated = True
            st.session_state.user_role = user["role"]
            st.session_state.user_login = user["login"]
            st.session_state.user_name = user.get("name", user["login"])
            st.session_state.current_remember_token = qp_token
            st.rerun()
        else:
            try: del st.query_params["remember_token"]
            except: pass
            components.html("<script>try{localStorage.removeItem('crm_remember_token');}catch(e){}</script>", height=0)
    if not st.session_state.authenticated:
        components.html("""
        <script>
        try {
            var token = localStorage.getItem('crm_remember_token');
            if (token) { var url = new URL(window.parent.location.href); if (!url.searchParams.has('remember_token')) { url.searchParams.set('remember_token', token); window.parent.location.href = url.toString(); } }
        } catch(e) { try { var token = localStorage.getItem('crm_remember_token'); if (token) { var url = new URL(window.top.location.href); if (!url.searchParams.has('remember_token')) { url.searchParams.set('remember_token', token); window.top.location.href = url.toString(); } } } catch(e2) {} }
        </script>
        """, height=0)
    if not st.session_state.authenticated:
        st.markdown("<h2 style='text-align: center; margin-top: 3rem;'>Айплинт CRM</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #7F8C9A; margin-bottom: 2rem;'>Авторизуйтесь для входа в систему</p>", unsafe_allow_html=True)
        lc, mc, rc = st.columns([1, 2, 1])
        with mc:
            with st.container(border=True):
                iu = st.text_input("Логин:", placeholder="Введите логин")
                ip = st.text_input("Пароль:", type="password", placeholder="Введите пароль")
                rm = st.checkbox("Запомнить меня на этом устройстве", value=True, key="remember_me_chk")
                st.markdown("---")
                if st.button("Войти", use_container_width=True, type="primary"):
                    if check_login(iu, ip):
                        if rm:
                            token = secrets.token_hex(32)
                            for u in st.session_state.crm_store["users"]:
                                if u["login"] == iu.strip(): u.setdefault("remember_tokens", []).append(token); break
                            save_data(st.session_state.crm_store)
                            st.session_state.current_remember_token = token
                            st.session_state.set_remember_token = token
                            try: st.query_params["remember_token"] = token
                            except: pass
                        st.toast("Успешный вход", icon="🔓"); st.rerun()
                    else: st.error("Неверный логин или пароль.")
        st.stop()

# --- Заголовок ---

st.markdown(f"""
<div class="greeting-block">
<h1 style='text-align: center; margin-bottom: 0.1rem;'>Айплинт CRM</h1>
<p style='text-align: center; color: #7F8C9A; font-size: 0.95rem; margin-top: 0; margin-bottom: 0;'>Продуктивного тебе дня, {st.session_state.user_name} 😊</p>
</div>
""", unsafe_allow_html=True)

if st.session_state.get("set_remember_token"):
    _tok = st.session_state.pop("set_remember_token")
    components.html(f"<script>try{{localStorage.setItem('crm_remember_token','{_tok}');}}catch(e){{}}</script>", height=0)

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
                for u in st.session_state.crm_store["users"]:
                    if u["login"] == cul: u["password"] = hash_password(np); commit_and_rerun(st.session_state.crm_store, "Пароль изменён")
            else: st.error("Пароли не совпадают")
    if st.session_state.user_role == "admin":
        with st.expander("Экспорт базы"):
            st.download_button("Скачать CSV", data=export_clients_csv(), file_name="clients_export.csv", mime="text/csv", use_container_width=True)
    st.markdown("---")
    if st.button("Выйти", use_container_width=True):
        clear_remember_token()
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_login = None
        st.session_state.user_name = None
        st.session_state.current_remember_token = None
        st.rerun()

# --- Навигация ---

nc1, nc2, nc3 = st.columns(3)
with nc1:
    if st.button("Клиенты", use_container_width=True, type="primary" if st.session_state.active_tab == "Клиенты" else "secondary"): st.session_state.active_tab = "Клиенты"; st.rerun()
with nc2:
    if st.button("Задачи", use_container_width=True, type="primary" if st.session_state.active_tab == "Задачи" else "secondary"): st.session_state.active_tab = "Задачи"; st.rerun()
with nc3:
    if st.button("Сделки", use_container_width=True, type="primary" if st.session_state.active_tab == "Сделки" else "secondary"): st.session_state.active_tab = "Сделки"; st.rerun()
st.markdown("---")

# --- Вкладка «Задачи» ---

if st.session_state.active_tab == "Задачи":
    now_time = datetime.now()
    all_deals = st.session_state.crm_store["deals"]
    active_deals = [d for d in all_deals if d["status"] in ("Новый", "В работе")]
    active_sum = sum(d.get("budget", 0) for d in active_deals)
    overdue_count = sum(1 for c in st.session_state.crm_store.get("clients", []) for t in c.get("tasks", []) if is_task_overdue(t))
    closed_this_month = len([d for d in all_deals if d["status"] == "Сделка закрыта" and d.get("closed_date", "").startswith(now_time.strftime("%Y-%m"))])
    total_clients = len(st.session_state.crm_store["clients"])
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Активные сделки", len(active_deals), f"{active_sum:,.0f} руб.".replace(",", " "))
    d2.metric("Просрочено", overdue_count)
    d3.metric("Закрыто за месяц", closed_this_month)
    d4.metric("Клиентов", total_clients)
    st.markdown("---")
    cu = st.session_state.user_name
    mgrs = get_managers_list()
    mf = st.selectbox("Ответственный", ["Мои задачи", "Все"] + mgrs, index=0)
    di = {}
    for d in st.session_state.crm_store.get("deals", []): di.setdefault(d["client_id"], d)
    aat = []
    for cl in st.session_state.crm_store.get("clients", []):
        cd = di.get(cl["id"])
        mdt = cd["title"] if cd else ""
        for ti, tk in enumerate(cl.get("tasks", [])):
            if not tk.get("done", False):
                tm = tk.get("manager", "")
                if mf == "Мои задачи":
                    if tm and tm != cu: continue
                elif mf != "Все":
                    if tm != mf: continue
                aat.append({"client_id": cl["id"], "client_name": cl["name"], "client_phone": cl["phone"], "deal_title": mdt, "sort_date": get_task_sort_date(tk), "deadline_str": tk.get("deadline", ""), "type": tk.get("type", "Связаться"), "text": tk.get("text", ""), "task_obj": tk, "task_idx": ti, "client_obj": cl})
    aat.sort(key=lambda x: x["sort_date"])
    tt = [t for t in aat if t["sort_date"] <= now_time.date()]
    ft = [t for t in aat if t["sort_date"] > now_time.date()]

    def render_task_block(t, sk):
        task = t["task_obj"]; cl = t["client_obj"]
        tp = task.get("type", "Связаться")
        io_ = is_task_overdue(task)
        sl = "Просрочено" if io_ else ("Сегодня" if t["sort_date"] == now_time.date() else "Срок")
        fd = format_date(t["deadline_str"])
        ht = f"{fd} — {t['client_name']} — {t['type']}"
        exp_key = f"tb_{sk}_{t['client_id']}_{t['task_idx']}"
        inject_border_css(exp_key, "#D65757" if io_ else "#4CAF50")
        with st.expander(ht, expanded=False, key=exp_key):
            st.markdown(f"**{sl}** — {fd} | {tp}")
            st.markdown(f"👤 **{t['client_name']}** ({t['client_phone']})")
            if tp == "Отправить заказ":
                st.markdown("---"); st.markdown("**Данные отправки:**")
                st.markdown(f"Товары: {task.get('products', '')}")
                st.markdown(f"Адрес: {task.get('ship_addr', '')}")
                st.markdown(f"Получатель: {task.get('receiver', '')} ({task.get('receiver_phone', '')})")
                st.markdown(f"Оплата: {task.get('ship_pay', '')}")
                if task.get('order_amount', 0) > 0:
                    oa = task['order_amount']; dp = cl.get('discount', 0); da = oa * dp / 100; ta = oa - da
                    st.markdown(f"Сумма: {oa:,.0f} | Скидка: {dp}% ({da:,.0f}) | **Итого: {ta:,.0f}**".replace(",", " "))
                if task.get('tk_num'): st.markdown(f"Трек: `{task['tk_num']}`")
            st.markdown("---")
            st.markdown(f"**Ответственный:** {task.get('manager', '—')}")
            st.markdown("---")
            st.markdown("**Файл:**")
            if task.get("file_path"):
                st.markdown(f"📄 {task.get('file_name', '')}")
                render_file_action_buttons(task["file_path"], task.get("file_name", ""), f"task_{sk}_{t['client_id']}_{t['task_idx']}")
                if st.session_state.user_role == "admin":
                    if st.button("Удалить файл", key=f"del_tfile_{sk}_{t['client_id']}_{t['task_idx']}"):
                        task["file_path"] = None; task["file_name"] = None
                        commit_and_rerun(st.session_state.crm_store, "Файл удалён")
            ntf = st.file_uploader("Добавить файл:", key=f"new_tfile_{sk}_{t['client_id']}_{t['task_idx']}")
            if st.button("Сохранить файл", key=f"save_tfile_{sk}_{t['client_id']}_{t['task_idx']}"):
                if ntf:
                    fi = save_uploaded_file(ntf, t["client_id"], "task_file")
                    if fi: task["file_path"] = fi["path"]; task["file_name"] = fi["name"]
                        commit_and_rerun(st.session_state.crm_store, "Файл сохранён")
                else: st.warning("Выберите файл")
            st.markdown("---")
            render_print_button(task, cl, tp, fd, f"task_{sk}_{t['client_id']}_{t['task_idx']}")
            st.markdown("---")
            cd2 = parse_deadline(task.get("deadline", ""))
            st.markdown("**Изменить срок:**")
            dl_c1, dl_c2 = st.columns([3, 1])
            with dl_c1:
                ndd = st.date_input("Дата", value=cd2, format="DD/MM/YYYY", key=f"dl_d_{sk}_{t['client_id']}_{t['task_idx']}")
            with dl_c2:
                st.write("")
                if st.button("Обновить", key=f"dl_btn_{sk}_{t['client_id']}_{t['task_idx']}"):
                    task["deadline"] = ndd.isoformat()
                    commit_and_rerun(st.session_state.crm_store, "Срок обновлён")
            st.markdown("---")
            with st.expander("Выполнить задачу", expanded=False):
                rt = st.text_input("Отчёт:", key=f"rt_{sk}_{t['client_id']}_{t['task_idx']}")
                uf = st.file_uploader("Файл/фото отчёта:", key=f"uf_{sk}_{t['client_id']}_{t['task_idx']}")
                cn = st.checkbox("Создать следующую задачу", key=f"cn_{sk}_{t['client_id']}_{t['task_idx']}")
                ne = {}; ntd = None; ntt = None
                if cn:
                    st.markdown("---")
                    ntt = st.selectbox("Тип:", ["Связаться", "Отправить заказ"], key=f"nt_type_{sk}_{t['client_id']}_{t['task_idx']}")
                    ntm = st.selectbox("Ответственный:", mgrs, index=mgrs.index(cu) if cu in mgrs else 0, key=f"nt_mgr_{sk}_{t['client_id']}_{t['task_idx']}")
                    if ntt == "Отправить заказ":
                        ne["products"] = st.text_area("Товары", key=f"nt_p_{sk}_{t['client_id']}_{t['task_idx']}")
                        ne["ship_addr"] = st.text_input("Адрес", key=f"nt_a_{sk}_{t['client_id']}_{t['task_idx']}")
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
                        with st.spinner("Сохранение..."):
                            task["done"] = True; task["completion_report"] = rt.strip()
                            fi = save_uploaded_file(uf, t["client_id"], "task_report")
                            if fi: task["completion_file_path"] = fi["path"]; task["completion_file_name"] = fi["name"]
                            rp = f"Закрыта задача [{tp}] '{task['text']}'. Отчёт: {rt.strip()}"
                            if tp == "Отправить заказ": rp += f" | Кому: {task.get('receiver', '')} | Трек: {task.get('tk_num', 'нет')}"
                            cl["comments"].append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": rp, "file_path": fi["path"] if fi else None, "file_name": fi["name"] if fi else None})
                            if cn and ntt:
                                at = auto_task_title(ntt, t['client_name'], t['deal_title'])
                                te = {"text": at, "deadline": ntd.isoformat(), "done": False, "type": ntt, "file_path": None, "file_name": None, "manager": ntm, "completion_report": "", "completion_file_path": None, "completion_file_name": None}
                                te.update(ne); cl.setdefault("tasks", []).append(te)
                            commit_and_rerun(st.session_state.crm_store, "Задача выполнена")
                    else: st.warning("Введите отчёт")
            with st.expander("Редактировать задачу", expanded=False):
                nm = st.selectbox("Ответственный:", mgrs, index=mgrs.index(task.get("manager", cu)) if task.get("manager", cu) in mgrs else 0, key=f"ed_mgr_{sk}_{t['client_id']}_{t['task_idx']}")
                edl = st.date_input("Срок", value=parse_deadline(task.get("deadline", "")), format="DD/MM/YYYY", key=f"ed_dl_{sk}_{t['client_id']}_{t['task_idx']}")
                if tp == "Отправить заказ":
                    ep = st.text_area("Товары", value=task.get('products', ''), key=f"ed_p_{sk}_{t['client_id']}_{t['task_idx']}")
                    ea = st.text_input("Адрес", value=task.get('ship_addr', ''), key=f"ed_a_{sk}_{t['client_id']}_{t['task_idx']}")
                    er = st.text_input("Получатель", value=task.get('receiver', ''), key=f"ed_r_{sk}_{t['client_id']}_{t['task_idx']}")
                    erp = st.text_input("Тел. получателя", value=task.get('receiver_phone', ''), key=f"ed_rp_{sk}_{t['client_id']}_{t['task_idx']}")
                    esp = st.selectbox("Оплата", ["Включено в счёт", "Оплата при получении"], index=["Включено в счёт", "Оплата при получении"].index(task.get('ship_pay', 'Включено в счёт')) if task.get('ship_pay', 'Включено в счёт') in ["Включено в счёт", "Оплата при получении"] else 0, key=f"ed_sp_{sk}_{t['client_id']}_{t['task_idx']}")
                    etn = st.text_input("Трек-номер", value=task.get('tk_num', ''), key=f"ed_tn_{sk}_{t['client_id']}_{t['task_idx']}")
                    eoa = st.number_input("Сумма (руб.)", min_value=0.0, step=100.0, value=float(task.get("order_amount", 0)), key=f"ed_oa_{sk}_{t['client_id']}_{t['task_idx']}")
                ec = st.text_area("Комментарии", value=task.get('task_comment', ''), key=f"ed_c_{sk}_{t['client_id']}_{t['task_idx']}")
                if st.button("Сохранить", key=f"ed_btn_{sk}_{t['client_id']}_{t['task_idx']}", use_container_width=True, type="primary"):
                    task["manager"] = nm; task["deadline"] = edl.isoformat(); task["task_comment"] = ec
                    if tp == "Отправить заказ":
                        task["products"] = ep; task["ship_addr"] = ea; task["receiver"] = er
                        task["receiver_phone"] = format_phone(erp); task["ship_pay"] = esp
                        task["tk_num"] = etn; task["order_amount"] = eoa
                    commit_and_rerun(st.session_state.crm_store, "Задача сохранена")

    task_l, task_r = st.columns(2)
    with task_l:
        with st.container(border=True):
            st.subheader(f"На сегодня ({len(tt)})")
            if tt:
                for t in tt: render_task_block(t, "today")
            else: st.success("Все задачи на сегодня закрыты.")
    with task_r:
        with st.container(border=True):
            st.subheader(f"Предстоящие ({len(ft)})")
            if ft:
                for t in ft: render_task_block(t, "future")
            else: st.caption("План на будущие дни пуст.")
# --- Вкладки и навигация ---

def render_tabs():
    # Используем колонки для имитации вкладок в стиле iOS (акцент на читаемость, мягкие границы)
    cols = st.columns([1, 1, 1])
    tab_names = ["Задачи", "Канбан сделок", "Расписание и план"]
    
    # Определяем активную вкладку
    active_tab = st.session_state.active_tab
    
    for i, name in enumerate(tab_names):
        is_active = (name == active_tab)
        with cols[i]:
            # Кнопка-вкладка в стиле iOS: мягкий фон, скругление, акцент при активности
            if is_active:
                st.markdown(f"""
                <style>
                    .ios-tab-active-{i} {{
                        background-color: #FFFFFF;
                        border: 1px solid #DCE0E5;
                        border-bottom: 2px solid #bc1661;
                        color: #2C3E50;
                        font-weight: 600;
                        padding: 8px 12px;
                        border-radius: 12px 12px 0 0;
                        text-align: center;
                        cursor: default;
                    }}
                </style>
                <div class="ios-tab-active-{i}">{name}</div>
                """, unsafe_allow_html=True)
            else:
                # Неактивная вкладка: полупрозрачная, без яркой рамки
                st.markdown(f"""
                <style>
                    .ios-tab-inactive-{i} {{
                        background-color: transparent;
                        color: #9DA5B4;
                        font-weight: 500;
                        padding: 8px 12px;
                        border-radius: 12px 12px 0 0;
                        text-align: center;
                        cursor: pointer;
                    }}
                    .ios-tab-inactive-{i}:hover {{
                        background-color: #F5F6F8;
                        color: #5A6B7D;
                    }}
                </style>
                <div class="ios-tab-inactive-{i}" onclick="window.location.href='?tab={name.replace(' ', '_')}';">
                    {name}
                </div>
                """, unsafe_allow_html=True)

    # Обработка переключения вкладок через query params (простой роутинг)
    try:
        q_tab = st.query_params.get("tab", None)
        if q_tab:
            mapped = q_tab.replace("_", " ")
            if mapped in tab_names and mapped != active_tab:
                st.session_state.active_tab = mapped
                st.rerun()
    except Exception:
        pass

# --- Канбан сделок ---

def render_kanban():
    st.subheader("Канбан сделок")
    deals = st.session_state.crm_store.get("deals", [])
    clients = st.session_state.crm_store.get("clients", [])

    # Статусы для канбана
    statuses = ["Новый", "В работе", "На согласовании", "Сделка закрыта"]
    col_widths = [0.25, 0.25, 0.25, 0.25]
    kanban_cols = st.columns(col_widths)

    for idx, status in enumerate(statuses):
        with kanban_cols[idx]:
            st.markdown(f"### {status}")
            filtered = [d for d in deals if d.get("status") == status]
            
            for d in filtered:
                client = get_client_by_id(d["client_id"])
                c_name = client["name"] if client else "Неизвестный клиент"
                c_phone = client["phone"] if client else ""
                
                # Карточка сделки в стиле iOS: мягкая тень, скругления, без кислотных цветов
                st.markdown(f"""
                <style>
                    .kanban-card {{
                        background: #FFFFFF;
                        border-radius: 14px;
                        padding: 12px;
                        margin-bottom: 10px;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
                        border: 1px solid #E8EBEF;
                    }}
                    .kanban-title {{
                        font-size: 1rem;
                        font-weight: 600;
                        color: #2C3E50;
                        margin: 0 0 4px 0;
                    }}
                    .kanban-client {{
                        font-size: 0.85rem;
                        color: #7F8C9A;
                        margin: 0 0 8px 0;
                    }}
                    .kanban-amount {{
                        font-size: 1.1rem;
                        font-weight: 700;
                        color: #34495E;
                    }}
                    .kanban-actions button {{
                        width: 100%;
                        margin-top: 8px;
                    }}
                </style>
                <div class="kanban-card">
                    <div class="kanban-title">{d.get('title', 'Без названия')}</div>
                    <div class="kanban-client">Клиент: {c_name}<br>{c_phone}</div>
                    <div class="kanban-amount">Сумма: {d.get('amount', 0):,.0f} ₽</div>
                    <div style="margin-top:8px;">
                        <button onclick="window.location.href='?deal_id={d['id']}'" style="width:100%; padding:6px; border-radius:8px; border:1px solid #C9CFD7; background:#FFFFFF; color:#5A6B7D; font-size:0.85rem;">Подробнее</button>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if not filtered:
                st.caption("Нет сделок в этом статусе")

    # Диалог завершения сделки (вызывается из query param)
    try:
        deal_id_param = st.query_params.get("deal_id", None)
        if deal_id_param:
            close_deal_dialog(deal_id_param)
    except Exception:
        pass

# --- Расписание и план ---

def render_schedule():
    st.subheader("Расписание и план")
    today = datetime.now().date()
    tasks_all = []
    
    # Собираем все задачи из клиентов
    for c in st.session_state.crm_store.get("clients", []):
        for t in c.get("tasks", []):
            tasks_all.append({
                "task": t,
                "client": c,
                "deadline_date": get_task_sort_date(t),
                "is_overdue": is_task_overdue(t)
            })
    
    # Сортировка: сначала просроченные, потом ближайшие
    tasks_sorted = sorted(tasks_all, key=lambda x: (not x["is_overdue"], x["deadline_date"]))

    # Группировка по датам
    from collections import defaultdict
    by_date = defaultdict(list)
    for item in tasks_sorted:
        d = item["deadline_date"]
        if d == datetime.max.date(): d = today  # если нет дедлайна — считаем сегодня
        by_date[d].append(item)

    dates_ordered = sorted(by_date.keys())

    for d in dates_ordered:
        # Заголовок даты в стиле iOS
        label = "Сегодня" if d == today else d.strftime("%d/%m")
        st.markdown(f"""
        <style>
            .schedule-date-header {{
                font-size: 1.1rem;
                font-weight: 700;
                color: #2C3E50;
                margin: 1.2rem 0 0.6rem 0;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .schedule-arrow {{
                width: 16px; height: 16px;
                fill: #7F8C9A;
                cursor: pointer;
            }}
        </style>
        <div class="schedule-date-header">
            <span>{label}</span>
        </div>
        """, unsafe_allow_html=True)

        items = by_date[d]
        for idx, it in enumerate(items):
            t = it["task"]
            c = it["client"]
            is_over = it["is_overdue"]

            # Стрелка-переключатель для сворачивания
            key_exp = f"sched_exp_{d}_{idx}"
            default_expanded = False  # по умолчанию свернуто
            
            with st.expander(
                f"{'⚠️ ' if is_over else ''}{t.get('type', 'Задача')} — {c['name']}",
                expanded=default_expanded
            ):
                # Детали задачи
                st.write(f"**Текст:** {t.get('text', '')}")
                if t.get("deadline"):
                    st.write(f"**Срок:** {format_date(t.get('deadline'))}")
                if t.get("manager"):
                    st.write(f"**Ответственный:** {t['manager']}")
                if t.get("products"):
                    st.write(f"**Товары:** {t['products']}")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button("Отметить как выполненное", key=f"done_{key_exp}", type="secondary", use_container_width=True):
                        t["done"] = True
                        commit_and_rerun(st.session_state.crm_store, "Задача отмечена как выполненная")
                with col2:
                    render_print_button(t, c, t.get("type", "Задача"), format_date(t.get("deadline", "")), key_exp)

# --- Основной рендер страницы ---

if st.session_state.authenticated:
    render_tabs()
    
    if st.session_state.active_tab == "Задачи":
        # Здесь можно вставить существующий блок задач (если он у тебя отдельно)
        st.info("Вкладка «Задачи» — используй существующий код блока задач")
    elif st.session_state.active_tab == "Канбан сделок":
        render_kanban()
    elif st.session_state.active_tab == "Расписание и план":
        render_schedule()
else:
    # Страница авторизации (упрощённая, с исправленными рамками полей)
    st.title("Айплинт CRM — Вход")
    with st.form("login_form"):
        username = st.text_input("Логин", placeholder="admin", help="По умолчанию: admin / admin")
        password = st.text_input("Пароль", type="password", placeholder="Введите пароль")
        submitted = st.form_submit_button("Войти", type="primary")
        
        if submitted:
            if check_login(username, password):
                st.toast("Вход выполнен", icon="✅")
                st.rerun()
            else:
                st.error("Неверный логин или пароль")
