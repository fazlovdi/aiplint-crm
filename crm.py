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
        db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}], "_migrated": "v2"}
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
    return o.getvalue().encode("utf-8-sig")

def get_client_by_id(c_id):
    for c in st.session_state.crm_store["clients"]:
        if c["id"] == c_id:
            return c
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
    try:
        return datetime.strptime(dl, "%Y-%m-%d").date() < datetime.now().date()
    except Exception:
        try:
            return datetime.strptime(dl, "%Y-%m-%d %H:%M") < datetime.now()
        except Exception:
            return False

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
    components.html(f"""
    <div class="phone-action-group" style="padding:4px 0;">
        <span style="font-size:1rem;font-weight:600;color:#2C3E50;">{phone}</span>
        <button onclick="navigator.clipboard.writeText('{phone}').then(function(){{var b=this;b.textContent='\u2713';setTimeout(function(){{b.textContent='\U0001F4CB';}},1500);}}.bind(this));" class="phone-btn" title="Скопировать">\U0001F4CB</button>
        <a href="tel:+{cph}" class="phone-btn" style="text-decoration:none;" title="Позвонить">\U0001F4DE</a>
    </div>
    """, height=40)

def render_extra_phone_inline(phone, name, role, uid):
    cph = re.sub(r"\D", "", phone)
    if cph.startswith("8") and len(cph) == 11:
        cph = "7" + cph[1:]
    elif not cph:
        cph = "79990000000"
    info = f"{phone} \u2014 {name} ({role})" if name else phone
    components.html(f"""
    <div class="phone-action-group" style="padding:4px 0;flex-wrap:wrap;gap:8px;white-space:normal;">
        <span style="font-size:0.9rem;color:#3C4A5A;flex:1 1 auto;min-width:0;word-break:break-word;">{info}</span>
        <button onclick="navigator.clipboard.writeText('{phone}').then(function(){{var b=this;b.textContent='\u2713';setTimeout(function(){{b.textContent='\U0001F4CB';}},1500);}}.bind(this));" class="phone-btn" title="Скопировать">\U0001F4CB</button>
        <a href="tel:+{cph}" class="phone-btn" style="text-decoration:none;" title="Позвонить">\U0001F4DE</a>
    </div>
    """, height=44)

def render_file_action_buttons(fp, fn, kp):
    if fp and not fp.startswith("CRM_NE_TROGAT") and os.path.exists(fp):
        try:
            with open(fp, "rb") as f:
                fb = f.read()
        except Exception:
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
        except Exception:
            pass
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("Скачать", data=fb, file_name=fn, key=f"dl_{kp}")
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

def build_print_html(task, cl, tp, fd):
    def esc(s):
        return str(s if s else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    products_html = esc(task.get('products', '')).replace('\n', '<br>')
    oav = task.get('order_amount', 0)
    dpc = cl.get('discount', 0)
    dam = oav * dpc / 100
    tam = oav - dam
    cost_html = ""
    if oav and oav > 0:
        cost_html = (
            f"<div style='margin-top:6px;'>Сумма: {oav:,.0f} руб.</div>"
            f"<div>Скидка: {dpc}% ({dam:,.0f} руб.)</div>"
            f"<div style='font-size:16px;font-weight:bold;'>Итого: {tam:,.0f} руб.</div>"
        ).replace(",", " ")
    file_reminder = ""
    if task.get("file_path"):
        file_reminder = (
            "<div style='color:#D65757;font-weight:bold;margin:14px 0;"
            "border:2px solid #D65757;padding:8px;border-radius:8px;'>"
            "&#9888; Не забудь распечатать вложенный файл!</div>"
        )
    lb = get_logo_base64()
    if lb:
        logo_html = f"<img src='data:image/png;base64,{lb}' width='180' style='float:left;margin-right:20px;'/>"
    else:
        logo_html = "<div style='font-size:24px;font-weight:bold;float:left;margin-right:20px;'>АЙПЛИНТ</div>"
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
    js_func = f"doPrint_{safe_key}"
    var_name = f"_pd_{safe_key}"
    components.html(f"""
    <style>
    #{btn_id} {{ width: 100%; padding: 10px; background: #bc1661; color: white; border: none; border-radius: 10px; cursor: pointer; font-size: 14px; font-weight: 600; font-family: inherit; transition: background 0.15s; }}
    #{btn_id}:hover {{ background: #9a1452; }}
    </style>
    <button id="{btn_id}" onclick="{js_func}()">Распечатать задачу</button>
    <script>
    var {var_name} = {html_json};
    function {js_func}() {{
        var html = {var_name};
        var w = window.open('', '_blank');
        if (!w) {{ alert('Разрешите всплывающие окна для печати'); return; }}
        w.document.open(); w.document.write(html); w.document.close(); w.focus();
        setTimeout(function() {{ try {{ w.print(); }} catch(e) {{}} }}, 500);
        w.onafterprint = function() {{ setTimeout(function() {{ w.close(); }}, 300); }};
    }}
    </script>
    """, height=45)

def migrate_data(data):
    du = [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}]
    if "users" not in data:
        data["users"] = du
    for u in data["users"]:
        if not is_hashed(u.get("password", "")):
            u["password"] = hash_password(u["password"])
        if "remember_tokens" not in u:
            u["remember_tokens"] = []
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
            if "completion_file_path" not in t:
                t["completion_file_path"] = None
            if "completion_file_name" not in t:
                t["completion_file_name"] = None
            if "deal_id" not in t:
                t["deal_id"] = first_deal_id
    for d in data.get("deals", []):
        if "deal_comments" not in d:
            d["deal_comments"] = []
        if d.get("status") == "New":
            d["status"] = "Новый"
        if d.get("status") == "На согласовании":
            d["status"] = "В работе"
    data["_migrated"] = "v2"
    return data

def load_data():
    download_db_from_yandex()
    db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}], "_migrated": "v2"}
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
                        if "completion_file_path" not in t:
                            t["completion_file_path"] = None
                        if "completion_file_name" not in t:
                            t["completion_file_name"] = None
                        if "deal_id" not in t:
                            t["deal_id"] = first_deal_id
                for d in data.get("deals", []):
                    if d.get("status") == "На согласовании":
                        d["status"] = "В работе"
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
        st.markdown("**Невыполненные задачи:**")
        for t in incomplete:
            st.markdown(f"- {t.get('type', 'Связаться')} \u2014 {format_date(t.get('deadline', ''))} \u2014 {t.get('text', '')}")
        if st.button("Понятно", use_container_width=True):
            st.rerun()
        return
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
    st.session_state.active_tab = "Задачи"
if "client_form_version" not in st.session_state:
    st.session_state.client_form_version = 0
if "deal_form_version" not in st.session_state:
    st.session_state.deal_form_version = 0
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
if "current_remember_token" not in st.session_state:
    st.session_state.current_remember_token = None
if "set_remember_token" not in st.session_state:
    st.session_state.set_remember_token = None
if "deal_note_ver" not in st.session_state:
    st.session_state.deal_note_ver = {}
if "edit_client_id" not in st.session_state:
    st.session_state.edit_client_id = None
if "add_task_client_id" not in st.session_state:
    st.session_state.add_task_client_id = None
if "expanded_task_id" not in st.session_state:
    st.session_state.expanded_task_id = None

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
        if token in u.get("remember_tokens", []):
            return u
    return None

def clear_remember_token():
    current = st.session_state.get("current_remember_token")
    if current:
        for u in st.session_state.crm_store.get("users", []):
            if u["login"] == st.session_state.user_login:
                if current in u.get("remember_tokens", []):
                    u["remember_tokens"].remove(current)
                break
        save_data(st.session_state.crm_store)
    components.html("<script>try{localStorage.removeItem('crm_remember_token');}catch(e){}</script>", height=0)
    try:
        del st.query_params["remember_token"]
    except Exception:
        pass

if not st.session_state.authenticated:
    try:
        qp_token = st.query_params.get("remember_token", None)
    except AttributeError:
        qp_token = None
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
            try:
                del st.query_params["remember_token"]
            except Exception:
                pass
            components.html("<script>try{localStorage.removeItem('crm_remember_token');}catch(e){}</script>", height=0)
    if not st.session_state.authenticated:
        components.html("""
        <script>
        try {
            var token = localStorage.getItem('crm_remember_token');
            if (token) {
                var url = new URL(window.parent.location.href);
                if (!url.searchParams.has('remember_token')) {
                    url.searchParams.set('remember_token', token);
                    window.parent.location.href = url.toString();
                }
            }
        } catch(e) {
            try {
                var token = localStorage.getItem('crm_remember_token');
                if (token) {
                    var url = new URL(window.top.location.href);
                    if (!url.searchParams.has('remember_token')) {
                        url.searchParams.set('remember_token', token);
                        window.top.location.href = url.toString();
                    }
                }
            } catch(e2) {}
        }
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
                                if u["login"] == iu.strip():
                                    u.setdefault("remember_tokens", []).append(token)
                                    break
                            save_data(st.session_state.crm_store)
                            st.session_state.current_remember_token = token
                            st.session_state.set_remember_token = token
                            try:
                                st.query_params["remember_token"] = token
                            except Exception:
                                pass
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

if st.session_state.get("set_remember_token"):
    _tok = st.session_state.pop("set_remember_token")
    components.html(f"<script>try{{localStorage.setItem('crm_remember_token','{_tok}');}}catch(e){{}}</script>", height=0)

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
        clear_remember_token()
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_login = None
        st.session_state.user_name = None
        st.session_state.current_remember_token = None
        st.rerun()

nc1, nc2, nc3 = st.columns(3)
with nc1:
    if st.button("Клиенты", use_container_width=True, type="primary" if st.session_state.active_tab == "Клиенты" else "secondary"):
        st.session_state.active_tab = "Клиенты"
        st.rerun()
with nc2:
    if st.button("Задачи", use_container_width=True, type="primary" if st.session_state.active_tab == "Задачи" else "secondary"):
        st.session_state.active_tab = "Задачи"
        st.rerun()
with nc3:
    if st.button("Сделки", use_container_width=True, type="primary" if st.session_state.active_tab == "Сделки" else "secondary"):
        st.session_state.active_tab = "Сделки"
        st.rerun()
st.markdown("---")

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
    for d in st.session_state.crm_store.get("deals", []):
        di[d["id"]] = d
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
    tt = [t for t in aat if t["sort_date"] <= now_time.date()]
    ft = [t for t in aat if t["sort_date"] > now_time.date()]

    def render_task_block(t, sk):
        task = t["task_obj"]
        cl = t["client_obj"]
        tp = task.get("type", "Связаться")
        io_ = is_task_overdue(task)
        sl = "Просрочено" if io_ else ("Сегодня" if t["sort_date"] == now_time.date() else "Срок")
        fd = format_date(t["deadline_str"])
        ht = f"{fd} \u2014 {t['client_name']} \u2014 {t['type']}"
        exp_key = f"tb_{sk}_{t['client_id']}_{t['task_idx']}"
        inject_border_css(exp_key, "#D65757" if io_ else "#4CAF50")
        with st.expander(ht, expanded=False, key=exp_key):
            st.markdown(f"**{sl}** \u2014 {fd} | {tp}")
            st.markdown(f"\U0001F464 **{t['client_name']}** ({t['client_phone']})")
            if tp == "Отправить заказ":
                st.markdown("---")
                st.markdown("**Данные отправки:**")
                st.markdown(f"Товары: {task.get('products', '')}")
                st.markdown(f"Адрес: {task.get('ship_addr', '')}")
                st.markdown(f"Получатель: {task.get('receiver', '')} ({task.get('receiver_phone', '')})")
                st.markdown(f"Оплата: {task.get('ship_pay', '')}")
                if task.get('order_amount', 0) > 0:
                    oa = task['order_amount']
                    dp = cl.get('discount', 0)
                    da = oa * dp / 100
                    ta = oa - da
                    st.markdown(f"Сумма: {oa:,.0f} | Скидка: {dp}% ({da:,.0f}) | **Итого: {ta:,.0f}**".replace(",", " "))
                if task.get('tk_num'):
                    st.markdown(f"Трек: `{task['tk_num']}`")
            st.markdown("---")
            st.markdown(f"**Ответственный:** {task.get('manager', '\u2014')}")
            st.markdown("---")
            st.markdown("**Файл:**")
            if task.get("file_path"):
                st.markdown(f"\U0001F4C4 {task.get('file_name', '')}")
                render_file_action_buttons(task["file_path"], task.get("file_name", ""), f"task_{sk}_{t['client_id']}_{t['task_idx']}")
                if st.session_state.user_role == "admin":
                    if st.button("Удалить файл", key=f"del_tfile_{sk}_{t['client_id']}_{t['task_idx']}"):
                        task["file_path"] = None
                        task["file_name"] = None
                        commit_and_rerun(st.session_state.crm_store, "Файл удалён")
            ntf = st.file_uploader("Добавить файл:", key=f"new_tfile_{sk}_{t['client_id']}_{t['task_idx']}")
            if st.button("Сохранить файл", key=f"save_tfile_{sk}_{t['client_id']}_{t['task_idx']}"):
                if ntf:
                    fi = save_uploaded_file(ntf, t["client_id"], "task_file")
                    if fi:
                        task["file_path"] = fi["path"]
                        task["file_name"] = fi["name"]
                        commit_and_rerun(st.session_state.crm_store, "Файл сохранён")
                else:
                    st.warning("Выберите файл")
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
                ne = {}
                ntd = None
                ntt = None
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
                            task["done"] = True
                            task["completion_report"] = rt.strip()
                            fi = save_uploaded_file(uf, t["client_id"], "task_report")
                            if fi:
                                task["completion_file_path"] = fi["path"]
                                task["completion_file_name"] = fi["name"]
                            rp = f"Закрыта задача [{tp}] '{task['text']}'. Отчёт: {rt.strip()}"
                            if tp == "Отправить заказ":
                                rp += f" | Кому: {task.get('receiver', '')} | Трек: {task.get('tk_num', 'нет')}"
                            cl["comments"].append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": rp, "file_path": fi["path"] if fi else None, "file_name": fi["name"] if fi else None})
                            if cn and ntt:
                                at = auto_task_title(ntt, t['client_name'], t['deal_title'])
                                te = {"text": at, "deadline": ntd.isoformat(), "done": False, "type": ntt, "file_path": None, "file_name": None, "manager": ntm, "completion_report": "", "completion_file_path": None, "completion_file_name": None, "deal_id": task.get("deal_id")}
                                te.update(ne)
                                cl.setdefault("tasks", []).append(te)
                            commit_and_rerun(st.session_state.crm_store, "Задача выполнена")
                    else:
                        st.warning("Введите отчёт")
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
                    task["manager"] = nm
                    task["deadline"] = edl.isoformat()
                    task["task_comment"] = ec
                    if tp == "Отправить заказ":
                        task["products"] = ep
                        task["ship_addr"] = ea
                        task["receiver"] = er
                        task["receiver_phone"] = format_phone(erp)
                        task["ship_pay"] = esp
                        task["tk_num"] = etn
                        task["order_amount"] = eoa
                    commit_and_rerun(st.session_state.crm_store, "Задача сохранена")

    task_l, task_r = st.columns(2)
    with task_l:
        with st.container(border=True):
            st.subheader(f"На сегодня ({len(tt)})")
            if tt:
                for t in tt:
                    render_task_block(t, "today")
            else:
                st.success("Все задачи на сегодня закрыты.")
    with task_r:
        with st.container(border=True):
            st.subheader(f"Предстоящие ({len(ft)})")
            if ft:
                for t in ft:
                    render_task_block(t, "future")
            else:
                st.caption("План на будущие дни пуст.")

elif st.session_state.active_tab == "Сделки":
    deals = st.session_state.crm_store.get("deals", [])
    clients = st.session_state.crm_store.get("clients", [])
    cu = st.session_state.user_name
    mgrs = get_managers_list()
    statuses = ["Новый", "В работе", "Сделка закрыта", "Архив"]
    col_widths = [1, 1, 1, 1]
    kanban_cols = st.columns(col_widths)

    for idx, status in enumerate(statuses):
        with kanban_cols[idx]:
            st.subheader(status)
            filtered = [d for d in deals if d.get("status") == status]
            for d in filtered:
                client = get_client_by_id(d["client_id"])
                c_name = client["name"] if client else "Неизвестный клиент"
                c_phone = client["phone"] if client else ""
                deal_tasks = [t for t in (client.get("tasks", []) if client else []) if t.get("deal_id") == d["id"]]
                deal_has_overdue = any(not t.get("done") and is_task_overdue(t) for t in deal_tasks)
                deal_has_active = any(not t.get("done") for t in deal_tasks)
                if deal_has_overdue:
                    deal_border_color = "#D65757"
                elif deal_has_active:
                    deal_border_color = "#4CAF50"
                else:
                    deal_border_color = None
                deal_exp_key = f"deal_exp_{d['id']}"
                inject_border_css(deal_exp_key, deal_border_color)
                with st.expander(f"{d.get('title', 'Без названия')}", expanded=(st.session_state.get("open_deal_id") == d["id"]), key=deal_exp_key):
                    st.markdown(f"**Клиент:** {c_name}")
                    if c_phone:
                        render_phone_inline(c_phone, d["id"])
                    st.markdown(f"**Бюджет:** {d.get('budget', 0):,.0f} руб.".replace(",", " "))
                    st.markdown(f"**Статус:** {d.get('status')}")

                    if client:
                        deal_tasks.sort(key=lambda t: (t.get("done", False), get_task_sort_date(t)))
                        if deal_tasks:
                            st.markdown(f"**Задачи сделки ({len(deal_tasks)}):**")
                            for ti, t in enumerate(deal_tasks):
                                dl = format_date(t.get("deadline", ""))
                                t_done = t.get("done", False)
                                t_overdue = is_task_overdue(t)
                                if t_done:
                                    status_icon = "\u2705"
                                    border_color = "#C9CFD7"
                                elif t_overdue:
                                    status_icon = "\u26A0\uFE0F"
                                    border_color = "#D65757"
                                else:
                                    status_icon = "\u23F3"
                                    border_color = "#4CAF50"
                                task_exp_key = f"deal_task_{d['id']}_{ti}"
                                inject_border_css(task_exp_key, border_color)
                                with st.expander(f"{status_icon} {t.get('type', 'Связаться')} \u2014 {t.get('text', '')} | Срок: {dl}", expanded=False, key=task_exp_key):
                                    st.markdown(f"**Тип:** {t.get('type', 'Связаться')}")
                                    st.markdown(f"**Срок:** {dl}")
                                    st.markdown(f"**Ответственный:** {t.get('manager', '\u2014')}")
                                    if t_done:
                                        st.markdown(f"**Статус:** \u2705 Выполнено")
                                        if t.get("completion_report"):
                                            st.markdown(f"**Отчёт:** {t['completion_report']}")
                                    elif t_overdue:
                                        st.markdown(f"**Статус:** \u26A0\uFE0F Просрочено")
                                    else:
                                        st.markdown(f"**Статус:** \u23F3 В работе")
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
                                    if t.get("file_path"):
                                        st.markdown(f"**Файл:** {t.get('file_name', '')}")
                                        render_file_action_buttons(t["file_path"], t.get("file_name", ""), f"deal_task_file_{d['id']}_{ti}")
                        else:
                            st.caption("Нет задач")

                    if client and d.get("status") != "Архив":
                        with st.expander("Создать задачу", expanded=False, key=f"deal_new_task_{d['id']}"):
                            ntt = st.selectbox("Тип:", ["Связаться", "Отправить заказ"], key=f"ct_type_{d['id']}")
                            ntm = st.selectbox("Ответственный:", mgrs, index=mgrs.index(cu) if cu in mgrs else 0, key=f"ct_mgr_{d['id']}")
                            ntd = st.date_input("Срок:", format="DD/MM/YYYY", key=f"ct_d_{d['id']}")
                            ne = {}
                            if ntt == "Отправить заказ":
                                ne["products"] = st.text_area("Товары", key=f"ct_p_{d['id']}")
                                ne["ship_addr"] = st.text_input("Адрес", key=f"ct_a_{d['id']}")
                                ne["receiver"] = st.text_input("Получатель", key=f"ct_r_{d['id']}")
                                ne["receiver_phone"] = format_phone(st.text_input("Тел. получателя", key=f"ct_rp_{d['id']}"))
                                ne["ship_pay"] = st.selectbox("Оплата", ["Включено в счёт", "Оплата при получении"], key=f"ct_sp_{d['id']}")
                                ne["tk_num"] = st.text_input("Трек-номер", key=f"ct_tk_{d['id']}")
                                ne["order_amount"] = st.number_input("Сумма (руб.)", min_value=0.0, step=100.0, key=f"ct_oa_{d['id']}")
                                ne["task_comment"] = st.text_area("Комментарии", key=f"ct_c_{d['id']}")
                            else:
                                ne["order_amount"] = 0
                                ne["task_comment"] = st.text_area("Комментарии", key=f"ct_cs_{d['id']}")
                            if st.button("Создать задачу", key=f"ct_btn_{d['id']}", use_container_width=True, type="primary"):
                                at = auto_task_title(ntt, c_name, d.get("title", ""))
                                te = {"text": at, "deadline": ntd.isoformat(), "done": False, "type": ntt, "file_path": None, "file_name": None, "manager": ntm, "completion_report": "", "completion_file_path": None, "completion_file_name": None, "deal_id": d["id"]}
                                te.update(ne)
                                client.setdefault("tasks", []).append(te)
                                commit_and_rerun(st.session_state.crm_store, "Задача создана")

                    if d.get("deal_comments"):
                        st.markdown("**Комментарии:**")
                        for cm in d["deal_comments"]:
                            st.markdown(f"- *{cm.get('time', '')}*: {cm.get('text', '')}")
                    nc = st.text_input("Добавить комментарий:", key=f"dc_input_{d['id']}")
                    if st.button("Добавить комментарий", key=f"dc_btn_{d['id']}", use_container_width=True):
                        if nc.strip():
                            d.setdefault("deal_comments", []).append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": nc.strip()})
                            commit_and_rerun(st.session_state.crm_store, "Комментарий добавлен")
                        else:
                            st.warning("Введите текст")
                    st.markdown("---")

                    current_status = d.get("status", "Новый")
                    if current_status == "Новый":
                        if st.button("Перевести в \u00abВ работе\u00bb", key=f"deal_next_{d['id']}", use_container_width=True, type="primary"):
                            d["status"] = "В работе"
                            commit_and_rerun(st.session_state.crm_store, "Статус обновлён")
                    elif current_status == "В работе":
                        if st.button("Закрыть сделку", key=f"deal_close_{d['id']}", use_container_width=True, type="primary"):
                            close_deal_dialog(d["id"])
                    elif current_status == "Сделка закрыта":
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("Вернуть в работу", key=f"deal_reopen_{d['id']}", use_container_width=True):
                                d["status"] = "В работе"
                                commit_and_rerun(st.session_state.crm_store, "Сделка возвращена в работу")
                        with b2:
                            if st.button("В архив", key=f"deal_archive_{d['id']}", use_container_width=True, type="primary"):
                                d["status"] = "Архив"
                                commit_and_rerun(st.session_state.crm_store, "Сделка в архиве")

                    if st.session_state.user_role == "admin":
                        st.markdown("---")
                        if st.button("Удалить сделку", key=f"deal_del_{d['id']}", use_container_width=True):
                            st.session_state.crm_store["deals"] = [x for x in st.session_state.crm_store["deals"] if x["id"] != d["id"]]
                            commit_and_rerun(st.session_state.crm_store, "Сделка удалена")
            if not filtered:
                st.caption("Нет сделок")

elif st.session_state.active_tab == "Клиенты":
    cu = st.session_state.user_name
    mgrs = get_managers_list()
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
                ncc = st.text_input("Добавить комментарий:", key=f"new_cc_form_{fv}", placeholder="Введите комментарий...")
                if st.button("Добавить комментарий", key=f"cc_form_btn_{fv}", use_container_width=True):
                    if ncc.strip():
                        st.session_state.setdefault("pending_client_comments", []).append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": ncc.strip()})
                        st.toast("Комментарий добавлен", icon="\u2705")
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
                st.success("Поле для телефона добавлено")
        with ac_em:
            st.markdown("**Доп. Email**")
            for i, em in enumerate(st.session_state.f_em):
                st.session_state.f_em[i] = st.text_input(f"Email #{i+1}", value=em, key=f"f_em_{fv}_{i}")
            if st.button("Добавить Email", key=f"add_em_btn_{fv}"):
                st.session_state.f_em.append("")
                st.success("Поле для Email добавлено")
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
                st.success("Поле для адреса добавлено")
        st.markdown("---")
        cf = st.file_uploader("Прикрепить файл:", key=f"cf_{fv}")
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
                    fi = save_uploaded_file(cf, nid, "profile")
                    if fi:
                        nc["client_files"].append({"file_path": fi["path"], "file_name": fi["name"]})
                if st.session_state.get("pending_client_comments"):
                    nc["client_comments"] = list(st.session_state["pending_client_comments"])
                    st.session_state["pending_client_comments"] = []
                st.session_state.crm_store["clients"].append(nc)
                save_data(st.session_state.crm_store)
                st.session_state.f_ph, st.session_state.f_em, st.session_state.f_ad = [], [], []
                st.session_state.last_id = nid
                st.session_state.client_form_version += 1
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
            itc = (st.session_state.last_id == cl["id"])
            cl_has_overdue = any(not t.get("done") and is_task_overdue(t) for t in cl.get("tasks", []))
            cl_has_incomplete = any(not t.get("done") for t in cl.get("tasks", []))
            cl_border_color = None
            if cl_has_overdue:
                cl_border_color = "#D65757"
            elif cl_has_incomplete:
                cl_border_color = "#4CAF50"
            client_exp_key = f"client_card_{cl['id']}"
            inject_border_css(client_exp_key, cl_border_color)
            with st.expander(f"{cl['name']} \u2014 ID: {cl['id']} [{cl.get('category', 'Покупатель')}]", expanded=itc, key=client_exp_key):
                cl_l, cl_r = st.columns(2)
                with cl_l:
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
                    mc3.link_button("Написать в MAX", MAX_URL, use_container_width=True, help=f"Ваш номер в MAX: {MAX_NUMBER}. Найдите клиента по номеру {cl['phone']}.")
                    if cl.get("extra_phones"):
                        st.markdown("**Доп. телефоны:**")
                        for pi, p in enumerate(cl["extra_phones"]):
                            render_extra_phone_inline(p['phone'], p['name'], p['role'], f"{cl['id']}_extra_{pi}")
                    if cl.get("extra_addresses"):
                        st.markdown("**Доп. адреса:**")
                        for ea in cl["extra_addresses"]:
                            if isinstance(ea, dict):
                                st.markdown(f"- **{ea.get('address', '')}**")
                                if ea.get("resp_name"):
                                    st.markdown(f"  - {ea['resp_name']}, {ea.get('resp_role', '')} \u2014 {ea.get('resp_phone', '')}, {ea.get('resp_email', '')}")
                    st.markdown("---")
                    with st.container(border=True):
                        st.markdown("**Комментарии:**")
                        if cl.get("client_comments"):
                            for cc in cl["client_comments"]:
                                st.markdown(f"- *{cc.get('time', '')}*: {cc.get('text', '')}")
                        else:
                            st.caption("Пока нет комментариев")
                        nci = st.text_input("Добавить комментарий:", key=f"new_cc_input_{cl['id']}", placeholder="Введите комментарий...")
                        if st.button("Добавить комментарий", key=f"cc_btn_{cl['id']}", use_container_width=True):
                            if nci.strip():
                                cl.setdefault("client_comments", []).append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": nci.strip()})
                                commit_and_rerun(st.session_state.crm_store, "Комментарий добавлен")
                            else:
                                st.warning("Введите текст")
                    st.markdown("---")
                    st.markdown("**Файлы:**")
                    if "client_files" not in cl:
                        cl["client_files"] = []
                    for cfi, cff in enumerate(cl["client_files"]):
                        st.markdown(f"\U0001F4C4 {cff.get('file_name', '')}")
                        render_file_action_buttons(cff.get("file_path"), cff.get("file_name", "файл"), f"cli_{cl['id']}_{cfi}")
                        if st.session_state.user_role == "admin":
                            if st.button("Удалить файл", key=f"cf_del_{cl['id']}_{cfi}"):
                                cl["client_files"].pop(cfi)
                                commit_and_rerun(st.session_state.crm_store, "Файл удалён")
                    ucf = st.file_uploader("Загрузить файл:", key=f"cf_up_{cl['id']}")
                    if st.button("Сохранить файл", key=f"cf_btn_{cl['id']}", use_container_width=True):
                        if ucf:
                            with st.spinner("Загрузка..."):
                                fi = save_uploaded_file(ucf, cl["id"], "profile")
                                if fi:
                                    cl["client_files"].append({"file_path": fi["path"], "file_name": fi["name"]})
                                    save_data(st.session_state.crm_store)
                                    st.toast("Файл сохранён", icon="\U0001F4C1")
                                    st.rerun()
                        else:
                            st.warning("Выберите файл")
                    with st.expander("Редактировать данные", expanded=False):
                        en = st.text_input("ФИО", value=cl['name'], key=f"en_{cl['id']}")
                        ep = st.text_input("Телефон", value=cl['phone'], key=f"ep_{cl['id']}")
                        ee = st.text_input("Email", value=cl.get('email', ''), key=f"ee_{cl['id']}")
                        ea = st.text_input("Адрес", value=cl.get('address', ''), key=f"ea_{cl['id']}")
                        ed = st.number_input("Скидка (%)", min_value=0, max_value=100, value=int(cl.get('discount', 0)), key=f"ed_{cl['id']}")
                        ec = st.selectbox("Категория", ["Дизайнер", "Строитель", "Дилер", "Покупатель"], index=["Дизайнер", "Строитель", "Дилер", "Покупатель"].index(cl.get('category', 'Покупатель')) if cl.get('category', 'Покупатель') in ["Дизайнер", "Строитель", "Дилер", "Покупатель"] else 3, key=f"ec_{cl['id']}")
                        em = st.selectbox("Ответственный:", mgrs, index=mgrs.index(cl.get('manager', '')) if cl.get('manager', '') in mgrs else 0, key=f"em_{cl['id']}")
                        if st.button("Сохранить основные данные", key=f"es_{cl['id']}", use_container_width=True):
                            cl['name'], cl['phone'], cl['email'], cl['address'], cl['discount'], cl['category'], cl['manager'] = en, format_phone(ep), ee, ea, int(ed), ec, em
                            commit_and_rerun(st.session_state.crm_store, "Данные клиента сохранены")
                        st.markdown("---")
                        with st.expander("Доп. телефоны (редактировать)", expanded=False):
                            for pi, ph in enumerate(cl.get("extra_phones", [])):
                                st.text_input(f"Телефон #{pi+1}", value=ph.get('phone', ''), key=f"ep_e_{cl['id']}_{pi}")
                                st.text_input(f"ФИО #{pi+1}", value=ph.get('name', ''), key=f"ep_n_{cl['id']}_{pi}")
                                st.text_input(f"Должность #{pi+1}", value=ph.get('role', ''), key=f"ep_r_{cl['id']}_{pi}")
                                if st.button("Удалить", key=f"ep_del_{cl['id']}_{pi}"):
                                    cl["extra_phones"].pop(pi)
                                    commit_and_rerun(st.session_state.crm_store, "Телефон удалён")
                            nph = st.text_input("Телефон", key=f"ep_new_ph_{cl['id']}")
                            npn = st.text_input("ФИО", key=f"ep_new_nm_{cl['id']}")
                            npr = st.text_input("Должность", key=f"ep_new_rl_{cl['id']}")
                            if st.button("Добавить телефон", key=f"ep_add_btn_{cl['id']}"):
                                if nph.strip():
                                    cl.setdefault("extra_phones", []).append({"phone": format_phone(nph), "name": npn, "role": npr})
                                    commit_and_rerun(st.session_state.crm_store, "Телефон добавлен")
                                else:
                                    st.warning("Введите телефон")
                        with st.expander("Доп. Email (редактировать)", expanded=False):
                            for ei, eem in enumerate(cl.get("extra_emails", [])):
                                st.text_input(f"Email #{ei+1}", value=eem, key=f"ee_e_{cl['id']}_{ei}")
                                if st.button("Удалить", key=f"ee_del_{cl['id']}_{ei}"):
                                    cl["extra_emails"].pop(ei)
                                    commit_and_rerun(st.session_state.crm_store, "Email удалён")
                            nem = st.text_input("Email", key=f"ee_new_{cl['id']}")
                            if st.button("Добавить Email", key=f"ee_add_btn_{cl['id']}"):
                                if nem.strip():
                                    cl.setdefault("extra_emails", []).append(nem.strip())
                                    commit_and_rerun(st.session_state.crm_store, "Email добавлен")
                                else:
                                    st.warning("Введите Email")
                        with st.expander("Доп. адреса (редактировать)", expanded=False):
                            for ai, ad in enumerate(cl.get("extra_addresses", [])):
                                st.text_input(f"Адрес #{ai+1}", value=ad.get('address', ''), key=f"ea_a_{cl['id']}_{ai}")
                                st.text_input(f"Ответственный #{ai+1}", value=ad.get('resp_name', ''), key=f"ea_rn_{cl['id']}_{ai}")
                                st.text_input(f"Должность #{ai+1}", value=ad.get('resp_role', ''), key=f"ea_rr_{cl['id']}_{ai}")
                                st.text_input(f"Телефон #{ai+1}", value=ad.get('resp_phone', ''), key=f"ea_rp_{cl['id']}_{ai}")
                                st.text_input(f"Email #{ai+1}", value=ad.get('resp_email', ''), key=f"ea_re_{cl['id']}_{ai}")
                                if st.button("Удалить адрес", key=f"ea_del_{cl['id']}_{ai}"):
                                    cl["extra_addresses"].pop(ai)
                                    commit_and_rerun(st.session_state.crm_store, "Адрес удалён")
                            naa = st.text_input("Адрес", key=f"ea_new_addr_{cl['id']}")
                            nar = st.text_input("Ответственный", key=f"ea_new_rn_{cl['id']}")
                            nrr = st.text_input("Должность", key=f"ea_new_rr_{cl['id']}")
                            nrp = st.text_input("Телефон", key=f"ea_new_rp_{cl['id']}")
                            nre = st.text_input("Email", key=f"ea_new_re_{cl['id']}")
                            if st.button("Добавить адрес", key=f"ea_add_btn_{cl['id']}"):
                                if naa.strip():
                                    cl.setdefault("extra_addresses", []).append({"address": naa.strip(), "resp_name": nar.strip(), "resp_role": nrr.strip(), "resp_phone": nrp.strip(), "resp_email": nre.strip()})
                                    commit_and_rerun(st.session_state.crm_store, "Адрес добавлен")
                                else:
                                    st.warning("Введите адрес")
                        if st.session_state.user_role == "admin":
                            st.markdown("---")
                            st.warning(f"Удаление {cl['name']} сотрёт все данные и сделки.")
                            cdl = st.checkbox("Подтверждаю удаление", key=f"confirm_del_cli_{cl['id']}")
                            if cdl and st.button("Удалить клиента", key=f"del_cli_btn_{cl['id']}", use_container_width=True, type="primary"):
                                st.session_state.crm_store["deals"] = [d for d in st.session_state.crm_store["deals"] if d["client_id"] != cl["id"]]
                                st.session_state.crm_store["clients"] = [c for c in st.session_state.crm_store["clients"] if c["id"] != cl["id"]]
                                st.session_state.last_id = None
                                commit_and_rerun(st.session_state.crm_store, "Клиент удалён")
                with cl_r:
                    deals = st.session_state.crm_store["deals"]
                    at = f"Заказ \u2116{datetime.now().strftime('%y')}-{(len(deals) + 1):05d}"
                    st.markdown(f"**Создать сделку:**")
                    st.info(f"Будет создан: **{at}**")
                    db = st.number_input("Бюджет (руб.)", min_value=0.0, step=5000.0, key=f"db_{cl['id']}")
                    if st.button("Создать сделку", key=f"dbn_{cl['id']}", use_container_width=True, type="primary"):
                        ndi = (max([d['id'] for d in deals]) if deals else 0) + 1
                        st.session_state.crm_store["deals"].append({"id": ndi, "client_id": cl["id"], "title": at, "budget": db, "status": "Новый", "deal_comments": []})
                        save_data(st.session_state.crm_store)
                        st.session_state.open_deal_id = ndi
                        st.session_state.active_tab = "Сделки"
                        st.toast("Сделка создана", icon="\u2705")
                        st.rerun()
                    st.markdown("---")
                    st.markdown("**Активные задачи:**")
                    client_tasks = [t for t in cl.get("tasks", []) if not t.get("done", False)]
                    client_tasks.sort(key=lambda t: get_task_sort_date(t))
                    if client_tasks:
                        for ti, t in enumerate(client_tasks):
                            deadline = format_date(t.get("deadline", ""))
                            status_icon = "\u26A0\uFE0F" if is_task_overdue(t) else "\u23F3"
                            with st.expander(f"{status_icon} {t.get('type', 'Связаться')} \u2014 {t.get('text', '')} | Срок: {deadline}", expanded=False, key=f"cli_task_{cl['id']}_{ti}"):
                                st.markdown(f"**Тип:** {t.get('type', 'Связаться')}")
                                st.markdown(f"**Срок:** {deadline}")
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
                                if t.get("file_path"):
                                    st.markdown(f"**Файл:** {t.get('file_name', '')}")
                                    render_file_action_buttons(t["file_path"], t.get("file_name", ""), f"cli_task_file_{cl['id']}_{ti}")
                    else:
                        st.caption("Нет активных задач")
                    st.markdown("---")
                    st.markdown("**Сделки клиента:**")
                    cl_deals = [d for d in deals if d["client_id"] == cl["id"]]
                    if cl_deals:
                        for d in cl_deals:
                            if st.button(f"{d['title']} ({d['status']}) \u2014 {d.get('budget', 0):,.0f} руб.".replace(",", " "), key=f"cli_deal_btn_{cl['id']}_{d['id']}", use_container_width=True):
                                st.session_state.active_tab = "Сделки"
                                st.session_state.open_deal_id = d["id"]
                                st.rerun()
                    else:
                        st.caption("Нет сделок")
            if st.session_state.get("last_id"):
                st.session_state.last_id = None
    else:
        st.info("База клиентов пуста. Создайте первого клиента.")
