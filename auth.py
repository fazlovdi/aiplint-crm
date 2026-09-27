import streamlit as st
import streamlit.components.v1 as components
import extra_streamlit_components as stx
import hashlib
import secrets
from datetime import datetime, timedelta

def get_cookie_manager():
    # Используем кэширование, чтобы менеджер кук не пересоздавался при каждом рендере
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(key="crm_cookie_mgr")
    return st.session_state.cookie_manager

def hash_password(pwd, salt=None):
    if not pwd: return ""
    if salt is None: salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + pwd.strip()).encode()).hexdigest()
    return f"{salt}:{h}"

def verify_password(pwd, stored):
    if not stored: return False
    if ":" in stored:
        parts = stored.split(":")
        if len(parts) == 2 and len(parts[0]) == 32:
            salt, h = parts
            return hashlib.sha256((salt + pwd.strip()).encode()).hexdigest() == h
    return pwd.strip() == stored

def check_auto_login():
    """Проверка кук ДО отрисовки интерфейса. Защищает от вылетов при обновлении страницы."""
    if st.session_state.get("authenticated"):
        return True
        
    cookie_manager = get_cookie_manager()
    stored_token = cookie_manager.get("crm_auth_token")
    
    if stored_token:
        for u in st.session_state.crm_store.get("users", []):
            if u.get("auth_token") == stored_token:
                st.session_state.authenticated = True
                st.session_state.user_role = u["role"]
                st.session_state.user_login = u["login"]
                st.session_state.user_name = u.get("name", u["login"])
                return True
    return False
def render_auth_screen(save_data_func):
    cookie_manager = get_cookie_manager()
    saved_login = cookie_manager.get("crm_saved_login") or ""
    
    # Стили для красивого плиточного или цифрового ввода PIN-кода
    st.markdown("""
    <style>
        .pin-container { max-width: 320px; margin: 0 auto; text-align: center; padding: 20px; }
        /* Форсируем появление цифровой клавиатуры на смартфонах */
        .stTextInput input[type="password"] { inputmode: numeric !important; pattern: [0-9]* !important; text-align: center; font-size: 24px !important; letter-spacing: 10px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='text-align: center; margin-top: 3rem;'>Айплинт CRM</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            # Если логин уже сохранен на устройстве — сразу показываем ввод PIN-кода
            if saved_login:
                st.markdown(f"<p style='text-align:center; font-weight:600;'>Вход для устройства: <code style='font-size:14px;'>{saved_login}</code></p>", unsafe_allow_html=True)
                
                # Поле ввода PIN с ограничением в 4 символа и скрытием точек
                ip = st.text_input("Введите 4-значный PIN-код:", type="password", max_chars=4, key="login_pin_field", placeholder="••••")
                
                # Небольшой JS-костыль, который принудительно включает цифровую клавиатуру (inputmode) на iOS/Android
                components.html("""
                <script>
                setTimeout(function() {
                    var inputs = window.parent.document.querySelectorAll('input[type="password"]');
                    inputs.forEach(function(input) {
                        input.setAttribute('inputmode', 'numeric');
                        input.setAttribute('pattern', '[0-9]*');
                    });
                }, 250);
                </script>
                """, height=0)
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Войти", use_container_width=True, type="primary"):
                        if match_and_authorize(saved_login, ip, cookie_manager, save_data_func, True):
                            st.rerun()
                with c2:
                    if st.button("Сменить аккаунт", use_container_width=True, kind="secondary"):
                        cookie_manager.delete("crm_saved_login")
                        st.rerun()
            else:
                # Обычный вход по логину и паролю (если заходят первый раз)
                st.markdown("<p style='text-align:center; color:#7F8C9A;'>Первичный вход в систему</p>", unsafe_allow_html=True)
                iu = st.text_input("Логин:", placeholder="Введите логин")
                ip = st.text_input("Пароль:", type="password", placeholder="Введите пароль")
                remember_me = st.checkbox("Запомнить меня на этом устройстве", value=True)
                
                if st.button("Войти", use_container_width=True, type="primary"):
                    if match_and_authorize(iu, ip, cookie_manager, save_data_func, remember_me):
                        st.rerun()
    st.stop()

def match_and_authorize(login, secret, cookie_manager, save_data_func, remember):
    user_found = None
    for u in st.session_state.crm_store.get("users", []):
        if u["login"] == login.strip():
            if verify_password(secret, u["password"]) or (u.get("pin") and secret.strip() == u["pin"]):
                user_found = u
                break
                
    if user_found:
        st.session_state.authenticated = True
        st.session_state.user_role = user_found["role"]
        st.session_state.user_login = user_found["login"]
        st.session_state.user_name = user_found.get("name", user_found["login"])
        
        # Автоматически сохраняем логин для последующего быстрого ввода PIN
        cookie_manager.set("crm_saved_login", user_found["login"], expires_at=datetime.now() + timedelta(days=365))
        
        if remember:
            _token = secrets.token_hex(32)
            user_found["auth_token"] = _token
            save_data_func(st.session_state.crm_store)
            cookie_manager.set("crm_auth_token", _token, expires_at=datetime.now() + timedelta(days=90))
        return True
    else:
        st.error("Неверный пароль или PIN-код.")
        return False

def render_profile_settings(current_user_obj, save_data_func):
    st.markdown("### 🔓 Быстрый вход по PIN-коду")
    st.markdown("<small style='color:#7F8C9A;'>Задайте 4 цифры PIN, чтобы приложение сразу запрашивало только их с цифровой клавиатуры телефона.</small>", unsafe_allow_html=True)
    
    db_pin = current_user_obj.get("pin", "")
    set_pin = st.text_input("Придумайте 4 цифры PIN:", value=db_pin, max_chars=4, type="password", key="auth_profile_pin")
    
    if st.button("Сохранить PIN-код", use_container_width=True, type="primary"):
        if set_pin.isdigit() and len(set_pin) == 4:
            current_user_obj["pin"] = set_pin
            save_data_func(st.session_state.crm_store)
            st.success("PIN-код успешно сохранен!")
            st.rerun()
        else:
            st.error("PIN-код должен состоять строго из 4 ЦИФР!")
