import streamlit as st
import json, os, re, urllib.parse, requests
from datetime import datetime

FILE_NAME = "web_crm_database_v2.json"
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR): 
    os.makedirs(UPLOAD_DIR)

# Актуальный базовый URL для API Яндекс Диска
YANDEX_API_URL = "https://yandex.net"

# Чтение и очистка токена из секретов Streamlit Cloud
raw_token = st.secrets.get("YANDEX_DISK_TOKEN", "")
if isinstance(raw_token, str):
    YANDEX_TOKEN = raw_token.strip().strip('"').strip("'")
else:
    YANDEX_TOKEN = ""

def yandex_headers():
    return {
        "Authorization": f"OAuth {YANDEX_TOKEN}",
        "Accept": "application/json"
    }

# Найти функцию init_yandex_folders и полностью заменить её этим кодом:

def init_yandex_folders():
    if not YANDEX_TOKEN: return
    try:
        # Проверяем, существует ли уже папка Айплинт_CRM на Диске
        check_url = "https://yandex.net"
        res_main = requests.get(check_url, params={"path": "disk:/Айплинт_CRM"}, headers=yandex_headers())
        
        # Если папки нет (код 404), принудительно создаем её через PUT
        if res_main.status_code == 404:
            requests.put(check_url, params={"path": "disk:/Айплинт_CRM"}, headers=yandex_headers())
            st.sidebar.info("📂 Создана корневая папка 'Айплинт_CRM' на Яндекс.Диске")
            
        # Теперь проверяем внутреннюю папку uploads внутри Айплинт_CRM
        res_uploads = requests.get(check_url, params={"path": "disk:/Айплинт_CRM/uploads"}, headers=yandex_headers())
        if res_uploads.status_code == 404:
            requests.put(check_url, params={"path": "disk:/Айплинт_CRM/uploads"}, headers=yandex_headers())
            
    except Exception as e:
        st.sidebar.error(f"⚠️ Не удалось инициализировать структуру папок: {e}")

# Найти функцию download_db_from_yandex и полностью заменить её этим кодом:

def download_db_from_yandex():
    if not YANDEX_TOKEN: return
    init_yandex_folders()
    try:
        url = f"{YANDEX_API_URL}/download"
        res = requests.get(url, params={"path": f"disk:/Айплинт_CRM/{FILE_NAME}"}, headers=yandex_headers())
        
        if res.status_code == 200:
            download_url = res.json().get("href")
            file_res = requests.get(download_url)
            if file_res.status_code == 200:
                with open(FILE_NAME, "w", encoding="utf-8") as f:
                    f.write(file_res.text)
                st.sidebar.success("🔄 База успешно синхронизирована с Яндекс.Диском!")
                
        elif res.status_code == 404:
            # 🟢 ИСПРАВЛЕНО: Если файла в облаке нет, создаем его локально И СРАЗУ ЖЕ отправляем на Яндекс.Диск
            if not os.path.exists(FILE_NAME):
                with open(FILE_NAME, "w", encoding="utf-8") as f:
                    json.dump({"clients": [], "deals": []}, f)
                
                # Принудительный вызов выгрузки, чтобы пустой файл инициализировался в облаке
                st.sidebar.info("✨ Инициализация новой базы данных в облаке...")
                upload_url_init = f"{YANDEX_API_URL}/upload"
                res_init = requests.get(upload_url_init, params={"path": f"disk:/Айплинт_CRM/{FILE_NAME}", "overwrite": "true"}, headers=yandex_headers())
                if res_init.status_code == 200:
                    href_init = res_init.json().get("href")
                    with open(FILE_NAME, "rb") as f_init:
                        requests.put(href_init, files={"file": f_init})
                        st.sidebar.success("📁 Файл базы данных успешно создан на Яндекс.Диске!")
        else:
            st.sidebar.warning(f"ℹ️ Нетипичный ответ Яндекса при загрузке: {res.status_code}")
    except Exception as e:
        st.sidebar.error(f"🔴 Ошибка загрузки базы: {e}")

def upload_db_to_yandex():
    if not YANDEX_TOKEN or not os.path.exists(FILE_NAME): return
    try:
        url = f"{YANDEX_API_URL}/upload"
        res = requests.get(url, params={"path": f"disk:/Айплинт_CRM/{FILE_NAME}", "overwrite": "true"}, headers=yandex_headers())
        if res.status_code == 200:
            upload_url = res.json().get("href")
            with open(FILE_NAME, "rb") as f:
                put_res = requests.put(upload_url, files={"file": f})
                # Успешные коды ответов Яндекса: 200 (ОК) или 201 (Создано)
                if put_res.status_code == 200 or put_res.status_code == 201:
                    st.toast("✅ База данных успешно синхронизирована с Яндекс.Диском!", icon="☁️")
                else:
                    st.sidebar.error(f"🔴 Ошибка записи файла на Диск: {put_res.status_code}")
        else:
            st.sidebar.error(f"🔴 Яндекс отказал в ссылке выгрузки. Код: {res.status_code}")
    except Exception as e:
        st.sidebar.error(f"🔴 Ошибка синхронизации с облаком: {e}")

def upload_file_to_yandex(local_path, remote_name):
    if not YANDEX_TOKEN or not os.path.exists(local_path): return
    try:
        safe_remote_name = urllib.parse.quote(remote_name)
        url = f"{YANDEX_API_URL}/upload"
        remote_path = f"disk:/Айплинт_CRM/uploads/{safe_remote_name}"
        res = requests.get(url, params={"path": remote_path, "overwrite": "true"}, headers=yandex_headers())
        if res.status_code == 200:
            upload_url = res.json().get("href")
            with open(local_path, "rb") as f:
                requests.put(upload_url, files={"file": f})
    except Exception as e:
        st.sidebar.warning(f"⚠️ Ошибка загрузки файла {remote_name} в облако: {e}")

def format_phone(p_str):
    if not p_str: return ""
    digits = re.sub(r"\D", "", p_str)
    if len(digits) == 11 and digits in ["7", "8"]: digits = digits[1:]
    if len(digits) == 10: return f"+7 {digits[0:3]} {digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
    return p_str.strip()

def save_uploaded_file(u_file, c_id, prefix=""):
    if u_file is not None:
        s_name = u_file.name
        unique_name = f"{c_id}_{prefix}_{int(datetime.now().timestamp())}_{s_name}"
        s_path = os.path.join(UPLOAD_DIR, unique_name)
        with open(s_path, "wb") as f: f.write(u_file.getbuffer())
        upload_file_to_yandex(s_path, unique_name)
        return {"path": s_path, "name": s_name}
    return None

def display_file_or_image(f_path, f_name, key_unique):
    if f_path and os.path.exists(f_path):
        file_ext = os.path.splitext(f_path)[1].lower()
        if file_ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]: 
            st.image(f_path, caption=f_name, width=250)
        else:
            try:
                with open(f_path, "rb") as f: 
                    st.download_button(label=f"📎 Скачать {f_name}", data=f.read(), file_name=f_name, key=key_unique)
            except Exception: st.caption("📁 Файл на сервере.")

def load_data():
    download_db_from_yandex()
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as f:
                data = json.load(f)
                for c in data.get("clients", []):
                    for k, val in [("email", ""), ("address", ""), ("base_comment", ""), ("category", "Покупатель"), ("discount", 0), ("extra_phones", []), ("extra_emails", []), ("extra_addresses", []), ("client_files", [])]:
                        if k not in c or c[k] == "-": c[k] = val
                for d in data.get("deals", []):
                    if "deal_comments" not in d: d["deal_comments"] = []
                    if d.get("status") == "New": d["status"] = "Новый"
                return data
        except Exception: return {"clients": [], "deals": []}
    return {"clients": [], "deals": []}

def save_data(data):
    try:
        with open(FILE_NAME, "w", encoding="utf-8") as f: 
            json.dump(data, f, ensure_ascii=False, indent=4)
        upload_db_to_yandex()
    except Exception as e: st.sidebar.error(f"Ошибка сохранения JSON: {e}")

if "crm_store" not in st.session_state: st.session_state.crm_store = load_data()
if "f_ph" not in st.session_state: st.session_state.f_ph = []
if "f_em" not in st.session_state: st.session_state.f_em = []
if "f_ad" not in st.session_state: st.session_state.f_ad = []
if "last_id" not in st.session_state: st.session_state.last_id = None
if "search_input_key" not in st.session_state: st.session_state.search_input_key = ""
if "active_tab" not in st.session_state: st.session_state.active_tab = "Задачи"
if "form_version" not in st.session_state: st.session_state.form_version = 0

st.set_page_config(page_title="Айплинт CRM", layout="wide")
st.title("💼 Айплинт CRM: Клиенты и Сделки")

col_m1, col_menu2, col_menu3 = st.columns(3)
with col_m1:
    if st.button("📅 Расписание и План", use_container_width=True, type="primary" if st.session_state.active_tab == "Задачи" else "secondary"):
        st.session_state.active_tab = "Задачи"; st.rerun()
with col_menu2:
    if st.button("👥  База клиентов", use_container_width=True, type="primary" if st.session_state.active_tab == "Slow" or st.session_state.active_tab == "Slow_Card" or st.session_state.active_tab == "Клиенты" else "secondary"):
        st.session_state.active_tab = "Клиенты"; st.rerun()
with col_menu3:
    if st.button("📋  Канбан сделок", use_container_width=True, type="primary" if st.session_state.active_tab == "Сделки" else "secondary"):
        st.session_state.active_tab = "Сделки"; st.rerun()

st.markdown("---")
if st.session_state.active_tab == "Задачи":
    st.header("🎯 Расписание и оперативный план")
    all_active_tasks = []
    now_time = datetime.now()

    for client in st.session_state.crm_store.get("clients", []):
        client_deals = [d for d in st.session_state.crm_store.get("deals", []) if d["client_id"] == client["id"]]
        main_deal_title = client_deals[0]["title"] if client_deals else ""
        
        for task in client.get("tasks", []):
            if not task.get("done", False):
                try:
                    task_deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
                except Exception:
                    task_deadline = now_time
                
                all_active_tasks.append({
                    "client_id": client["id"],
                    "client_name": client["name"],
                    "client_phone": client["phone"],
                    "deal_title": main_deal_title,
                    "deadline_obj": task_deadline,
                    "deadline_str": task["deadline"],
                    "type": task.get("type", "Связаться"),
                    "text": task["text"],
                    "details": f"📍 Адрес: {task.get('ship_addr','')} | 👤 Получатель: {task.get('receiver','')}" if task.get("type") == "Отправить заказ" else f"📝 Коммент: {task.get('task_comment','') or task.get('task_comment_simple','')}"
                })

    all_active_tasks.sort(key=lambda x: x["deadline_obj"])
    today_tasks = [t for t in all_active_tasks if t["deadline_obj"].date() <= now_time.date()]
    future_tasks = [t for t in all_active_tasks if t["deadline_obj"].date() > now_time.date()]

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        with st.container(border=True):
            st.subheader(f"🚨 Просроченные и на сегодня ({len(today_tasks)})")
            if today_tasks:
                for idx, t in enumerate(today_tasks):
                    icon = "📞" if t["type"] == "Связаться" else "📦"
                    time_alert = "🔴 ПРОСРОЧЕНО" if t["deadline_obj"] < now_time else "🕒 На сегодня"
                    st.markdown(f"**{time_alert} ({t['deadline_str']})** | {icon} **{t['type']}**")
                    st.markdown(f"👤 Клиент: **{t['client_name']}** ({t['client_phone']})  \n📄 {t['text']}  \n* {t['details']}")
                    if t["deal_title"]:
                        if st.button(f"🔍 Перейти к {t['deal_title']}", key=f"focus_tod_{idx}"):
                            st.session_state.search_input_key = t["deal_title"]
                            st.session_state.last_id = t["client_id"]
                            st.session_state.active_tab = "Клиенты"
                            st.rerun()
                    st.markdown("---")
            else: st.success("🎉 На сегодня все задачи закрыты!")

    with col_t2:
        with st.container(border=True):
            st.subheader(f"📅 Предстоящие задачи ({len(future_tasks)})")
            if future_tasks:
                for idx, t in enumerate(future_tasks):
                    icon = "📞" if t["type"] == "Связаться" else "📦"
                    st.markdown(f"**🕒 Срок: {t['deadline_str']}** | {icon} **{t['type']}**")
                    st.markdown(f"👤 Клиент: **{t['client_name']}** ({t['client_phone']})  \n📄 {t['text']}  \n* {t['details']}")
                    if t["deal_title"]:
                        if st.button(f"🔍 Перейти к {t['deal_title']}", key=f"focus_fut_{idx}"):
                            st.session_state.search_input_key = t["deal_title"]
                            st.session_state.last_id = t["client_id"]
                            st.session_state.active_tab = "Клиенты"
                            st.rerun()
                    st.markdown("---")
            else: st.caption("План на будущие дни пуст.")
elif st.session_state.active_tab == "Клиенты":
    st.header("👥 База постоянных клиентов")
    
    with st.expander("➕ Зарегистрировать нового клиента", expanded=False, key=f"add_client_form_{st.session_state.form_version}"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            c_name = st.text_input("ФИО / Компания")
            c_phone = st.text_input("Основной телефон")
            c_email = st.text_input("Основной Email")
            c_discount = st.number_input("Скидка (%)", min_value=0, max_value=100, step=1)
        with col_f2:
            c_address = st.text_input("Основной адрес")
            c_category = st.selectbox("Категория", ["Дизайнер", "Строитель", "Дилер", "Покупатель"])
            c_comment = st.text_area("Описание")
            
        st.markdown("---")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.markdown("**👥 Сотрудники**")
            for i, ph in enumerate(st.session_state.f_ph):
                st.session_state.f_ph[i]["phone"] = st.text_input(f"Телефон #{i+1}", value=ph["phone"], key=f"f_ph_{i}")
                st.session_state.f_ph[i]["name"] = st.text_input(f"ФИО #{i+1}", value=ph["name"], key=f"f_nm_{i}")
                st.session_state.f_ph[i]["role"] = st.text_input(f"Должность #{i+1}", value=ph["role"], key=f"f_rl_{i}")
            if st.button("➕ Добавить сотрудника"): 
                st.session_state.f_ph.append({"phone":"", "name":"", "role":""}); st.rerun()
        with col_s2:
            st.markdown("**✉️ Доп. Email**")
            for i, em in enumerate(st.session_state.f_em): st.session_state.f_em[i] = st.text_input(f"Email #{i+1}", value=em, key=f"f_em_{i}")
            if st.button("➕ Добавить Email"): st.session_state.f_em.append(""); st.rerun()
        with col_s3:
            st.markdown("**📍 Доп. Адреса**")
            for i, ad in enumerate(st.session_state.f_ad): st.session_state.f_ad[i] = st.text_input(f"Адрес #{i+1}", value=ad, key=f"f_ad_{i}")
            if st.button("➕ Добавить Адрес"): st.session_state.f_ad.append(""); st.rerun()

        if st.button("Внести клиента в базу", use_container_width=True, type="primary"):
            if c_name and c_phone:
                clients = st.session_state.crm_store["clients"]
                new_id = (max([c['id'] for c in clients]) if clients else 0) + 1
                new_client = {
                    "id": new_id, "name": c_name, "phone": format_phone(c_phone), "email": c_email, "address": c_address, 
                    "category": c_category, "discount": int(c_discount), "base_comment": c_comment,
                    "extra_phones": [{"phone": format_phone(p["phone"]), "name": p["name"], "role": p["role"]} for p in st.session_state.f_ph if p["phone"].strip()],
                    "extra_emails": [e for e in st.session_state.f_em if e.strip()], "extra_addresses": [a for a in st.session_state.f_ad if a.strip()],
                    "client_files": [], "comments": [], "tasks": []
                }
                st.session_state.crm_store["clients"].append(new_client)
                save_data(st.session_state.crm_store)
                st.session_state.f_ph, st.session_state.f_em, st.session_state.f_ad = [], [], []
                st.session_state.last_id = new_id
                st.session_state.form_version += 1
                st.session_state["scroll_to_card"] = True
                st.toast(f"🎉 Клиент {c_name} успешно добавлен в базу!", icon="✅")
                st.rerun()
            else: st.error("Заполните ФИО и телефон!")

    st.markdown("### 🔍 Фильтры базы")
    col_search1, col_search2 = st.columns(2)
    with col_search1: 
        search_query = st.text_input("Поиск по имени, компании или телефону:", key="search_input_key", placeholder="Введите text...").strip().lower()
    with col_search2: 
        category_filter = st.selectbox("Фильтр по категории:", ["Все", "Дизайнер", "Строитель", "Дилер", "Покупатель"])
    all_clients = st.session_state.crm_store["clients"]
    filtered_clients = []
    search_digits = re.sub(r"\D", "", search_query)
    if search_digits and search_digits in ["7", "8"] and len(search_digits) > 1: 
        search_digits = search_digits[1:]

    for client in all_clients:
        if category_filter != "Все" and client.get("category", "Покупатель") != category_filter: continue
        if search_query:
            client_text = f"{client['name']} {client.get('email','')} {client.get('address','')} {client.get('base_comment','')}".lower()
            match_by_text = search_query in client_text
            all_client_digits = re.sub(r"\D", "", client['phone'])
            for p in client.get("extra_phones", []):
                all_client_digits += " " + re.sub(r"\D", "", p["phone"])
                client_text += " " + p["name"].lower()
            match_by_phone = search_digits and (search_digits in all_client_digits)
            match_by_employee_name = search_query in client_text
            if not (match_by_text or match_by_phone or match_by_employee_name): continue
        filtered_clients.append(client)
    if all_clients:
        with st.expander(f"🔍 Посмотреть карточки клиентов (Найдено: {len(filtered_clients)})", expanded=True):
            for client in filtered_clients:
                is_target_card = (st.session_state.last_id == client["id"])
                # Исправленный скрытый якорь под строгие стандарты Streamlit
                anchor_html = f"data:text/html;charset=utf-8,<div id='client-card-{client['id']}' style='display:none;'></div>"
                st.iframe(anchor_html, height=1, width=1)
                
                with st.expander(f"👤 {client['name']} — ID: {client['id']} `[{client.get('category', 'Покупатель')}]`", expanded=is_target_card):
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        st.markdown(f"📞 Тел: **{client['phone']}** | ✉️ Email: `{client.get('email','')}` | 📍 ...Адрес: *{client.get('address','')}*")
                        st.markdown(f"🏷️ Скидка: `{client.get('discount',0)}%` | 📝 Описание: {client.get('base_comment','')}")
                        
                        clean_phone = re.sub(r"\D", "", client['phone'])
                        if clean_phone.startswith("8") and len(clean_phone) == 11: clean_phone = "7" + clean_phone[1:]
                        elif not clean_phone: clean_phone = "79990000000"
                        
                        st.markdown("**💬 Быстрая связь в мессенджерах:**")
                        col_msg1, col_menu_msg2, col_menu_msg3 = st.columns(3)
                        with col_msg1:
                            wa_text = "Здравствуйте! По поводу вашего заказа из Айплинт CRM..."
                            encoded_text = urllib.parse.quote(wa_text)
                            wa_url = f"https://wa.me{clean_phone}?text={encoded_text}"
                            st.link_button("💬 WhatsApp", wa_url, use_container_width=True)
                        with col_menu_msg2:
                            tg_url = f"https://t.me+{clean_phone}"
                            st.link_button("✈️ Telegram", tg_url, use_container_width=True)
                        with col_menu_msg3:
                            max_url = f"sms:{clean_phone}" 
                            st.link_button("📱 Мессенджер Max", max_url, use_container_width=True)
                        
                        if client.get("extra_phones"):
                            st.markdown("**👥 Дополнительные сотрудники:**")
                            for p in client["extra_phones"]: st.markdown(f"• **{p['phone']}** — {p['name']} ({p['role']})")
                        
                        st.markdown("---")
                        st.markdown("📁 **Постоянные документы клиента:**")
                        if "client_files" not in client: client["client_files"] = []
                        for cf_idx, cf in enumerate(client["client_files"]): display_file_or_image(cf.get("file_path"), cf.get("file_name"), f"cf_dl_{client['id']}_{cf_idx}")
                        
                        uploaded_cf = st.file_uploader("➕ Загрузить файл в профиль:", key=f"cf_up_{client['id']}")
                        if st.button("💾 Сохранить файл в карточку", key=f"cf_btn_{client['id']}", use_container_width=True):
                            if uploaded_cf is not None:
                                f_info = save_uploaded_file(uploaded_cf, client["id"], "profile")
                                client["client_files"].append({"file_path": f_info["path"], "file_name": f_info["name"]})
                                save_data(st.session_state.crm_store); st.rerun()

                        with st.expander("✏️ Редактировать данные"):
                            en = st.text_input("ФИО", value=client['name'], key=f"en_{client['id']}")
                            ep = st.text_input("Телефон", value=client['phone'], key=f"ep_{client['id']}")
                            ee = st.text_input("Email", value=client.get('email',''), key=f"ee_{client['id']}")
                            ea = st.text_input("Адрес", value=client.get('address',''), key=f"ea_{client['id']}")
                            ed = st.number_input("Скидка (%)", min_value=0, max_value=100, value=int(client.get('discount',0)), key=f"ed_{client['id']}")
                            ec = st.text_area("Описание", value=client.get('base_comment',''), key=f"ec_{client['id']}")
                            if st.button("💾 Сохранить", key=f"es_{client['id']}", use_container_width=True):
                                client['name'], client['phone'], client['email'], client['address'], client['discount'], client['base_comment'] = en, format_phone(ep), ee, ea, int(ed), ec
                                save_data(st.session_state.crm_store); st.rerun()
                    with col_c2:
                        deals = st.session_state.crm_store["deals"]
                        auto_title = f"Заказ №{datetime.now().strftime('%y')}-{(len(deals) + 1):05d}"
                        st.markdown(f"**Запустить новую сделку:**")
                        st.info(f"Будет создан: **{auto_title}**")
                        db = st.number_input("Бюджет (руб.)", min_value=0.0, step=5000.0, key=f"db_{client['id']}")
                        if st.button("🚀 Открыть сделку", key=f"dbn_{client['id']}", use_container_width=True):
                            max_d_id = max([d['id'] for d in deals]) if deals else 0
                            st.session_state.crm_store["deals"].append({"id": max_d_id + 1, "client_id": client["id"], "title": auto_title, "budget": db, "status": "Новый", "deal_comments": []})
                            save_data(st.session_state.crm_store); st.rerun()
                            
        # Исправленный плавный JS-скролл без применения удаленного st.components.v1.html
        if st.session_state.get("scroll_to_card") and st.session_state.last_id:
            st.session_state["scroll_to_card"] = False
            js_scroll = f"data:text/html;charset=utf-8,<script>window.parent.document.getElementById('client-card-{st.session_state.last_id}').scrollIntoView({{behavior: 'smooth', block: 'center'}});</script>"
            st.iframe(js_scroll, height=1, width=1)
    else: st.info("База клиентов пуста.")
elif st.session_state.active_tab == "Сделки":
    st.header("📋  Канбан-доска сделок")
    dl = st.session_state.crm_store["deals"]
    t_new = sum(d.get("budget",0) for d in dl if d["status"] == "Новый")
    t_prg = sum(d.get("budget",0) for d in dl if d["status"] == "В работе")
    t_cls = sum(d.get("budget",0) for d in dl if d["status"] == "Сделка закрыта")
    st_new, st_prg, st_cls = st.columns(3)

    def draw_deal_card(deal, client):
        with st.container(border=True):
            card_title = f"🏷️ {deal['title']} | {client['name']} ({deal.get('budget', 0):,.0f} руб.)".replace(",", " ")
            
            with st.expander(card_title, expanded=False):
                st.caption(f"Категория: `[{client.get('category','Покупатель')}]` | 🔥 Скидка: `{client.get('discount',0)}%` | 📞 {client['phone']}")
                st.markdown("---")
                
                if deal.get("deal_comments"):
                    for com in deal["deal_comments"]: st.markdown(f"💬 *{com['time']}* — {com['text']}")
                
                input_key = f"ndc_val_{deal['id']}"
                ndc = st.text_input("Заметка к заказу:", key=input_key, placeholder="Например: Согласовали доставку")
                if st.button("💬 Сохранить заметку", key=f"ndcb_{deal['id']}", use_container_width=True):
                    if ndc.strip(): 
                        deal["deal_comments"].append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": ndc.strip()})
                        save_data(st.session_state.crm_store)
                        if input_key in st.session_state: del st.session_state[input_key]
                        st.rerun()
                
                st.markdown("---")
                if client.get("comments"):
                    with st.expander("📜 Отчеты по закрытым задачам"):
                        for com in client["comments"]: display_file_or_image(com.get("file_path"), com.get("file_name"), f"deal_h_{deal['id']}_{com['time'].replace(':','_')}")

                st.markdown("📌 **Задачи:**")
                if client.get("tasks"):
                    for i, task in enumerate(client["tasks"]):
                        if task["done"]: st.markdown(f"✅ ~~{task['text']}~~")
                        else:
                            try: is_over = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M") < datetime.now() if "deadline" in task else False
                            except ValueError: is_over = False
                            t_type = task.get("type", "Связаться")
                            icon = "📞" if t_type == "Связаться" else "📦"
                            
                            if is_over: st.error(f"⏰ ПРОСРОЧЕНО [{icon} {t_type}]: {task['text']}")
                            else: st.warning(f"⏰ [{icon} {t_type}]: {task['text']} ({task.get('deadline','')})")
                            
                            if t_type == "Отправить заказ":
                                with st.container(border=True):
                                    st.caption("📋 Сведения для отправки:")
                                    st.markdown(f"📦 **Товары:** {task.get('products', '')}\n📍 **Адрес:** {task.get('ship_addr', '')}\n👤 **Получатель:** {task.get('receiver', '')} ({task.get('receiver_phone', '')})\n💳 **Оплата ТК:** {task.get('ship_pay', '')}")
                                    if task.get('tk_num'): st.markdown(f"🔢 **Трек-номер ТК:** `{task['tk_num']}`")
                                    if task.get('task_comment'): st.markdown(f"📝 **Коммент:** *{task['task_comment']}*")
                            
                            display_file_or_image(task.get("file_path"), task.get("file_name","файл"), f"task_file_view_{deal['id']}_{i}")
                            
                            clean_products = task.get('products', '').replace('\n', '<br>').replace("'", "`")
                            clean_addr = task.get('ship_addr', '').replace("'", "`")
                            clean_rec = task.get('receiver', '').replace("'", "`")
                            clean_comm = task.get('task_comment', '').replace('\n', '<br>').replace("'", "`") if task.get('task_comment') else task.get('task_comment_simple', '').replace('\n', '<br>').replace("'", "`")
                            clean_tk = task.get('tk_num', '')
                            
                            print_btn_html = f"""
                            <a href="data:text/html;charset=utf-8,<html><head><title>Накладная</title><style>body{{font-family:Arial;margin:40px;line-height:1.6;}} .h{{text-align:center;border-bottom:2px solid %23000;padding-bottom:10px;}} .s{{margin-bottom:12px;}} .b{{font-weight:bold;}}</style></head><body><div class='h'><h2>БЛАНК ЗАДАЧИ К {deal['title']}</h2><p>Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p></div><br><div class='s'><span class='b'>Клиент:</span> {client['name']} ({client['phone']})</div><div class='s'><span class='b'>Тип действия:</span> {t_type}</div><div class='s'><span class='b'>Срок (Дедлайн):</span> {task.get('deadline','')}</div><hr><h3>ДАННЫЕ ЗАКАЗА:</h3><div class='s'><span class='b'>Товары:</span><br>{clean_products}</div><div class='s'><span class='b'>Адрес доставки:</span> {clean_addr}</div><div class='s'><span class='b'>Получатель:</span> {clean_rec} ({task.get('receiver_phone', '')})</div><div class='s'><span class='b'>Оплата ТК:</span> {task.get('ship_pay', '')}</div><div class='s'><span class='b'>Трек-номер:</span> {clean_tk}</div><div class='s'><span class='b'>Комментарий:</span> {clean_comm}</div><br><br><br><p style='text-align:right;'>Ответственный: _________________</p><script>window.print();</script></body></html>" target="_blank" style="text-decoration:none;"><button style="width:100%; padding:10px; background-color:%23262730; color:white; border:1px solid %23464855; border-radius:4px; cursor:pointer; font-family:sans-serif; font-size:14px;">🖨️ Открыть бланк для печати</button></a>
                            """
                            st.iframe(f"data:text/html;charset=utf-8,{print_btn_html}", height=55)
                            with st.expander("✏️ Редактировать задачу"):
                                edit_t_text = st.text_input("Изменить суть задачи:", value=task["text"].split(" (Файл:"), key=f"ed_t_txt_{deal['id']}_{i}")
                                if st.button("💾 Сохранить изменения задачи", key=f"ed_t_btn_{deal['id']}_{i}", use_container_width=True):
                                    if edit_t_text.strip():
                                        task["text"] = edit_t_text.strip() + (" (Файл: " + task["file_name"] + ")" if task.get("file_path") else "")
                                        save_data(st.session_state.crm_store)
                                        st.rerun()
                            
                            if st.checkbox("Выполнить задачу", key=f"tsk_{deal['id']}_{i}"):
                                with st.container(border=True):
                                    rt = st.text_input("Что сделано? (Отчет):", key=f"rt_{deal['id']}_{i}")
                                    uf = st.file_uploader("Файл/Фото отчета:", key=f"uf_{deal['id']}_{i}")
                                    cn = st.checkbox("Следующая задача", key=f"cn_{deal['id']}_{i}")
                                    if st.button("💾 Подтвердить", key=f"cbtn_{deal['id']}_{i}", use_container_width=True):
                                        if rt.strip():
                                            task["done"] = True; f_info = save_uploaded_file(uf, deal['id'], "task_report")
                                            rep = f"✅ Закрыта задача [{t_type}] '{task['text']}'. Отчет: {rt.strip()}"
                                            if t_type == "Отправить заказ": rep += f" | Кому: {task.get('receiver', '')} | Трек: {task.get('tk_num', 'нет')}"
                                            client["comments"].append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": rep, "file_path": f_info["path"] if f_info else None, "file_name": f_info["name"] if f_info else None})
                                            if cn: client["tasks"].append({"text": "Новое действие", "deadline": datetime.now().strftime("%Y-%m-%d %H:%M"), "done": False, "type": "Связаться"})
                                            save_data(st.session_state.crm_store); st.rerun()
                else: st.caption("Нет задач.")
                
                with st.expander("➕ Новая задача"):
                    task_type = st.selectbox("Тип задачи:", ["Связаться", "Отправить заказ"], key=f"t_type_sel_{deal['id']}")
                    tt = st.text_input("Суть задачи (необязательно):", key=f"tt_{deal['id']}")
                    ex_data = {}
                    if task_type == "Отправить заказ":
                        ex_data["products"] = st.text_area("Перечень товаров", key=f"t_p_{deal['id']}")
                        ex_data["ship_addr"] = st.text_input("Адрес доставки", key=f"t_a_{deal['id']}")
                        ex_data["receiver"] = st.text_input("ФИО получателя", key=f"t_r_{deal['id']}")
                        ex_data["receiver_phone"] = format_phone(st.text_input("Телефон получателя", key=f"t_rp_{deal['id']}"))
                        ex_data["ship_pay"] = st.selectbox("Оплата доставки", ["Включено в счёт", "Оплата при получении"], key=f"t_sp_{deal['id']}")
                        ex_data["tk_num"] = st.text_input("Трек-номер ТК", key=f"t_tk_{deal['id']}")
                        ex_data["task_comment"] = st.text_area("Комментарий", key=f"t_c_{deal['id']}")
                        auto_task_title = tt.strip() if tt.strip() else f"Отправка по {deal['title']}"
                    else: 
                        ex_data["task_comment"] = st.text_area("Комментарий к звонку", key=f"t_cs_{deal['id']}")
                        auto_task_title = tt.strip() if tt.strip() else f"Связаться по {deal['title']}"
                    t_uf = st.file_uploader("📎 Прикрепить ТЗ/Файл:", key=f"t_f_{deal['id']}")
                    cd, ct = st.columns(2)
                    with cd: td = st.date_input("Дата", key=f"td_{deal['id']}")
                    with ct: tm = st.time_input("Время", key=f"tm_{deal['id']}")
                    if st.button("Поставить задачу", key=f"tsv_{deal['id']}", use_container_width=True):
                        f_info = save_uploaded_file(t_uf, deal['id'], "task_init")
                        t_ent = {"text": auto_task_title + (f" (Файл: {f_info['name']})" if f_info else ""), "deadline": f"{td} {tm.strftime('%H:%M')}", "done": False, "type": task_type, "file_path": f_info["path"] if f_info else None, "file_name": f_info["name"] if f_info else None}
                        t_ent.update(ex_data); client.setdefault("tasks", []).append(t_ent)
                        if f_info: client["comments"].append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "text": f"📎 К задаче прикреплен файл: {f_info['name']}", "file_path": f_info["path"], "file_name": f_info["name"]})
                        save_data(st.session_state.crm_store); st.rerun()
                st.markdown("---")
                cb1, cb2 = st.columns(2)
                if deal['status'] == "Новый":
                    if cb1.button("👉 В работу", key=f"wf_{deal['id']}", use_container_width=True): deal['status'] = "В работе"; save_data(st.session_state.crm_store); st.rerun()
                elif deal['status'] == "В работе":
                    if cb1.button("👈 Назад", key=f"wb_{deal['id']}", use_container_width=True): deal['status'] = "Новый"; save_data(st.session_state.crm_store); st.rerun()
                    if cb2.button("🎉 Закрыть", key=f"wc_{deal['id']}", use_container_width=True): deal['status'] = "Сделка закрыта"; save_data(st.session_state.crm_store); st.rerun()
                elif deal['status'] == "Сделка закрыта":
                    if cb1.button("🔄 Возобновить", key=f"wr_{deal['id']}", use_container_width=True): deal['status'] = "В работе"; save_data(st.session_state.crm_store); st.rerun()

    def get_client(c_id):
        for c in st.session_state.crm_store["clients"]:
            if c["id"] == c_id: return c
        return {"name": "Неизвестно", "phone": "-", "comments": [], "tasks": [], "category": "Покупатель", "discount": 0}

    with st_new:
        st.markdown(f"#### 🔵 НОВЫЕ СДЕЛКИ  \n💰 `{t_new:,.0f} руб.`")
        for d in st.session_state.crm_store["deals"]:
            if d["status"] == "Новый": draw_deal_card(d, get_client(d["client_id"]))
    with st_prg:
        st.markdown(f"#### 🟡 В РАБОТЕ  \n💰 `{t_prg:,.0f} руб.`")
        for d in st.session_state.crm_store["deals"]:
            if d["status"] == "В работе": draw_deal_card(d, get_client(d["client_id"]))
    with st_cls:
        st.markdown(f"#### 🟢 ЗАКРЫТЫ  \n💰 `{t_cls:,.0f} руб.`")
        for d in st.session_state.crm_store["deals"]:
            if d["status"] == "Сделка закрыта": draw_deal_card(d, get_client(d["client_id"]))
