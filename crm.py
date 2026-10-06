
# ============================================================
# ПОЛНЫЙ ФИКС: защита от потери данных при сохранении
# Заменяет: _collect_all_timestamps, download_db_from_yandex,
#           upload_db_to_yandex_sync, upload_db_to_yandex_async,
#           save_data, commit_and_rerun, _smart_rerun
# ============================================================

import threading

# Глобальный lock для сериализации сохранений между потоками
_save_lock = threading.Lock()


def _collect_all_timestamps(data):
    """Собирает все last_modified из клиентов, сделок и задач для точного сравнения."""
    timestamps = []
    for c in data.get("clients", []):
        timestamps.append(c.get("last_modified", ""))
        for t in c.get("tasks", []):
            timestamps.append(t.get("last_modified", ""))
    for d in data.get("deals", []):
        timestamps.append(d.get("last_modified", ""))
    # Внутренние задачи тоже учитываем
    for t in data.get("internal_tasks", []):
        timestamps.append(t.get("last_modified", ""))
    return [ts for ts in timestamps if ts]


def _download_disk_data():
    """Скачивает JSON с Диска и возвращает dict или None при ошибке."""
    if not YANDEX_TOKEN:
        return None
    try:
        res = requests.get(
            f"{YANDEX_API_URL}/download",
            params={"path": f"disk:/CRM_NE_TROGAT/{FILE_NAME}"},
            headers=yandex_headers(),
            timeout=10
        )
        if res.status_code == 200:
            dl = requests.get(res.json().get("href"), timeout=30)
            if dl.status_code == 200:
                return json.loads(dl.text)
    except:
        pass
    return None


def download_db_from_yandex():
    """Скачивает базу с Диска. Не перезаписывает локальный файл, 
    если данные на Диске старее локальных."""
    if not YANDEX_TOKEN:
        return
    disk_data = _download_disk_data()
    if disk_data is not None:
        if os.path.exists(FILE_NAME):
            try:
                old_data = json.loads(open(FILE_NAME, "r", encoding="utf-8").read())
                old_ts = _collect_all_timestamps(old_data)
                new_ts = _collect_all_timestamps(disk_data)
                old_max = max(old_ts) if old_ts else ""
                new_max = max(new_ts) if new_ts else ""
                if new_max < old_max:
                    # Данные на Диске старее локальных — не перезаписываем
                    return
            except:
                # При любой ошибке сравнения — НЕ перезаписываем локальные данные
                return
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            json.dump(disk_data, f, ensure_ascii=False, indent=2)
        return
    # Диск недоступен — создаём пустую базу, если локального файла нет
    if not os.path.exists(FILE_NAME):
        db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}], "_migrated": "v2", "internal_tasks": [], "chat_messages": [], "qa_entries": [], "suppliers": []}
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)


def upload_db_to_yandex_sync():
    """Синхронная загрузка на Диск с 3 попытками. Возвращает True при успехе."""
    if not YANDEX_TOKEN or not os.path.exists(FILE_NAME):
        return False
    for attempt in range(3):
        try:
            res = requests.get(
                f"{YANDEX_API_URL}/upload",
                params={"path": f"disk:/CRM_NE_TROGAT/{FILE_NAME}", "overwrite": "true"},
                headers=yandex_headers(),
                timeout=15
            )
            if res.status_code == 200:
                with open(FILE_NAME, "rb") as f:
                    resp = requests.put(res.json().get("href"), data=f, timeout=30)
                if resp.status_code in (200, 201):
                    return True
        except:
            pass
    return False


def upload_db_to_yandex_async():
    """Сохраняет async-интерфейс для обратной совместимости, 
    но вызывает синхронную загрузку."""
    upload_db_to_yandex_sync()


def _merge_data(local_data, disk_data):
    """Сливает изменения из disk_data в local_data, 
    сохраняя локальные изменения для сущностей, изменённых локально 
    позже, чем на Диске."""
    # Строим карту таймстампов из Диска
    disk_ts_map = {}
    for c in disk_data.get("clients", []):
        cid = c.get("id")
        disk_ts_map[f"client_{cid}"] = c.get("last_modified", "")
        for t in c.get("tasks", []):
            disk_ts_map[f"task_{t.get('id')}"] = t.get("last_modified", "")
    for d in disk_data.get("deals", []):
        disk_ts_map[f"deal_{d.get('id')}"] = d.get("last_modified", "")
    for t in disk_data.get("internal_tasks", []):
        disk_ts_map[f"itask_{t.get('id')}"] = t.get("last_modified", "")

    # Строим карту таймстампов из локальных данных
    local_ts_map = {}
    for c in local_data.get("clients", []):
        cid = c.get("id")
        local_ts_map[f"client_{cid}"] = c.get("last_modified", "")
        for t in c.get("tasks", []):
            local_ts_map[f"task_{t.get('id')}"] = t.get("last_modified", "")
    for d in local_data.get("deals", []):
        local_ts_map[f"deal_{d.get('id')}"] = d.get("last_modified", "")
    for t in local_data.get("internal_tasks", []):
        local_ts_map[f"itask_{t.get('id')}"] = t.get("last_modified", "")

    # Индексы локальных сущностей по ID
    local_clients = {c.get("id"): c for c in local_data.get("clients", [])}
    local_deals = {d.get("id"): d for d in local_data.get("deals", [])}
    local_tasks = {}  # (client_id, task_id) -> (client, task)
    for c in local_data.get("clients", []):
        for t in c.get("tasks", []):
            local_tasks[t.get("id")] = (c, t)
    local_itasks = {t.get("id"): t for t in local_data.get("internal_tasks", [])}

    # Индексы дисковых сущностей по ID
    disk_clients = {c.get("id"): c for c in disk_data.get("clients", [])}
    disk_deals = {d.get("id"): d for d in disk_data.get("deals", [])}
    disk_tasks = {}
    for c in disk_data.get("clients", []):
        for t in c.get("tasks", []):
            disk_tasks[t.get("id")] = (c, t)
    disk_itasks = {t.get("id"): t for t in disk_data.get("internal_tasks", [])}

    # Обновляем локальные сущности, если на Диске они новее
    for tid, (disk_c, disk_t) in disk_tasks.items():
        if tid in local_tasks:
            local_c, local_t = local_tasks[tid]
            disk_ts = disk_ts_map.get(f"task_{tid}", "")
            local_ts = local_ts_map.get(f"task_{tid}", "")
            if disk_ts > local_ts:
                # На Диске новее — берём версию с Диска
                idx = local_c["tasks"].index(local_t)
                local_c["tasks"][idx] = disk_t
    
    for cid, disk_c in disk_clients.items():
        if cid in local_clients:
            local_c = local_clients[cid]
            disk_ts = disk_ts_map.get(f"client_{cid}", "")
            local_ts = local_ts_map.get(f"client_{cid}", "")
            if disk_ts > local_ts:
                # На Диске новее — обновляем поля клиента (кроме задач)
                local_tasks_list = local_c.get("tasks", [])
                disk_c_copy = dict(disk_c)
                disk_c_copy["tasks"] = local_tasks_list  # задачи уже слиты выше
                idx = local_data["clients"].index(local_c)
                local_data["clients"][idx] = disk_c_copy

    for did, disk_d in disk_deals.items():
        if did in local_deals:
            local_d = local_deals[did]
            disk_ts = disk_ts_map.get(f"deal_{did}", "")
            local_ts = local_ts_map.get(f"deal_{did}", "")
            if disk_ts > local_ts:
                idx = local_data["deals"].index(local_d)
                local_data["deals"][idx] = disk_d

    for tid, disk_t in disk_itasks.items():
        if tid in local_itasks:
            local_t = local_itasks[tid]
            disk_ts = disk_ts_map.get(f"itask_{tid}", "")
            local_ts = local_ts_map.get(f"itask_{tid}", "")
            if disk_ts > local_ts:
                idx = local_data["internal_tasks"].index(local_t)
                local_data["internal_tasks"][idx] = disk_t

    # Добавляем новые сущности с Диска, которых нет локально
    existing_client_ids = set(local_clients.keys())
    for cid, disk_c in disk_clients.items():
        if cid not in existing_client_ids:
            local_data["clients"].append(disk_c)

    existing_deal_ids = set(local_deals.keys())
    for did, disk_d in disk_deals.items():
        if did not in existing_deal_ids:
            local_data["deals"].append(disk_d)

    existing_itask_ids = set(local_itasks.keys())
    for tid, disk_t in disk_itasks.items():
        if tid not in existing_itask_ids:
            local_data["internal_tasks"].append(disk_t)

    return local_data


def save_data(data):
    """Сохраняет данные локально и на Диск.
    Перед сохранением проверяет, нет ли на Диске более свежей версии.
    Если на Диске есть более свежие сущности — сливает их в локальные данные."""
    with _save_lock:
        try:
            # 1. Проверяем Диск перед сохранением
            disk_data = _download_disk_data()
            if disk_data is not None:
                disk_ts = _collect_all_timestamps(disk_data)
                local_ts = _collect_all_timestamps(data)
                disk_max = max(disk_ts) if disk_ts else ""
                local_max = max(local_ts) if local_ts else ""
                
                if disk_max > local_max:
                    # На Диске есть более свежие данные — сливаем
                    data = _merge_data(data, disk_data)
                    # Обновляем session_state слитыми данными
                    st.session_state.crm_store = data
            
            # 2. Записываем локальный файл
            with open(FILE_NAME, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            # 3. Загружаем на Диск (синхронно, с retry)
            ok = upload_db_to_yandex_sync()
            if not ok and YANDEX_TOKEN:
                st.sidebar.warning(
                    "Данные сохранены локально, но не загружены на Диск. "
                    "При обновлении страницы изменения могут не сохраниться."
                )
        except Exception as e:
            st.sidebar.error(f"Ошибка сохранения: {e}")


def commit_and_rerun(data=None, toast_msg=None):
    """Сохраняет данные, показывает toast и перезагружает страницу."""
    if data is not None:
        save_data(data)
    if toast_msg:
        st.toast(toast_msg, icon="✅")
    _smart_rerun()


def _smart_rerun():
    """Перезагрузка с учётом открытого диалога."""
    if st.session_state.get("_in_dialog", False):
        st.rerun(scope="fragment")
    else:
        st.rerun()
