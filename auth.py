import streamlit as st
import extra_streamlit_components as stx
import hashlib
import secrets
import time
from datetime import datetime, timedelta

def get_cookie_manager():
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(key="crm_cookie_v5")
    return st.session_state.cookie_manager

def hash_password(pwd, salt=None):
    if not pwd: return ""
    if salt is None: salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + pwd.strip()).encode()).hexdigest()
    return f"{salt}:{h}"

def verify_password(pwd, stored):
    if not stored: return False
    # Проверка для хэшированных паролей с солью (формат salt:hash)
    if ":" in stored:
        parts = stored.split(":")
        if len(parts) == 2:
            salt, h = parts
            return hashlib.sha256((salt + pwd.strip()).encode()).hexdigest() == h
    # Проверка для простых хэшей sha256 (длиной 64 символа)
    if len(stored) == 64 and all(c in "0123456789abcdef" for c in stored):
        return hashlib.sha256(pwd.strip().encode()).hexdigest() == stored
    # Проверка для обычного открытого текста или PIN-кода
    return pwd.strip() == stored

def check_auto_login():
    """Проверка сессии при обновлении страницы до рендеринга интерфейса."""
    if st.session_state.get("authenticated"):
        return True
        
    c_mgr = get_cookie_manager()
    stored_token = c_mgr.get("crm_auth_token")
    
    if not stored_token:
        time.sleep(0.05)
        stored_token = c_mgr.get("crm_auth_token")
        
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
    c_mgr = get_cookie_manager()
    saved_login = c_mgr.get("crm_saved_login")
    if not saved_login:
        time.sleep(0.05)
        saved_login = c_mgr.get("crm_saved_login") or ""

    st.markdown("<h2 style='text-align: center; margin-top: 3rem;'>Айплинт CRM</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col2:
        with st.container(border=True):
            if saved_login:
                # Если в сессии есть флаг, что нужно дописать токен авторизации
                if st.session_state.get("auth_pending_token") and st.session_state.get("auth_pending_user"):
                    user_obj = st.session_state["auth_pending_user"]
                    _token = secrets.token_hex(32)
                    user_obj["auth_token"] = _token
                    save_data_func(st.session_state.crm_store)
                    
                    exp_token = (datetime.now() + timedelta(days=90)).date()
                    c_mgr.set("crm_auth_token", _token, expires_at=exp_token)
                    
                    st.session_state.authenticated = True
                    st.session_state.user_role = user_obj["role"]
                    st.session_state.user_login = user_obj["login"]
                    st.session_state.user_name = user_obj.get("name", user_obj["login"])
                    
                    st.session_state.pop("auth_pending_token", None)
                    st.session_state.pop("auth_pending_user", None)
                    st.toast("Вы успешно вошли!", icon="🔓")
                    st.rerun()

                st.markdown(f"<p style='text-align:center; font-size:0.95rem; color:#7F8C9A;'>Устройство авторизовано под учетной записью: <b>{saved_login}</b></p>", unsafe_allow_html=True)
                
                ip = st.text_input("Введите 4-значный PIN-код:", type="password", max_chars=4, key="crm_pin_input_field", placeholder="••••")
                
                st.html("""
                <script>
                function patchPinInput() {
                    var doc = window.parent.document;
                    var input = doc.querySelector('input[key="crm_pin_input_field"]') || doc.querySelector('input[type="password"]');
                    if (input) {
                        input.setAttribute('inputmode', 'numeric');
                        input.setAttribute('pattern', '[0-9]*');
                        input.style.textAlign = 'center';
                        input.style.fontSize = '1rem';
                        input.style.letterSpacing = 'normal';
                        
                        input.onkeydown = function(e) {
                            if (e.key === 'Enter' || e.keyCode === 13) {
                                e.preventDefault();
                                var btn = doc.querySelector('button[kind="primary"]');
                                if (btn) btn.click();
                            }
                        };
                    }
                }
                setTimeout(patchPinInput, 200);
                </script>
                """)
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Войти", use_container_width=True, type="primary", key="pin_submit_btn"):
                        if match_and_authorize(saved_login, ip, c_mgr, save_data_func, True):
                            st.rerun()
                with c2:
                    if st.button("Сменить аккаунт", use_container_width=True, key="change_acc_btn"):
                        c_mgr.delete("crm_saved_login")
                        c_mgr.delete("crm_auth_token")
                        st.rerun()
            else:
                st.markdown("<p style='text-align:center; color:#7F8C9A;'>Первичный вход в CRM</p>", unsafe_allow_html=True)
                iu = st.text_input("Логин:", placeholder="Введите логин", key="init_login_field")
                ip = st.text_input("Пароль:", type="password", placeholder="Введите пароль", key="init_pass_field")
                remember_me = st.checkbox("Запомнить меня на этом устройстве", value=True)
                
                if st.button("Войти", use_container_width=True, type="primary", key="init_submit_btn"):
                    if match_and_authorize(iu, ip, c_mgr, save_data_func, remember_me):
                        st.rerun()
    st.stop()

def match_and_authorize(login, secret, c_mgr, save_data_func, remember):
    if not secret:
        st.error("Поле не может быть пустым.")
        return False
        
    user_found = None
    for u in st.session_state.crm_store.get("users", []):
        if u["login"] == login.strip():
            if verify_password(secret, u["password"]) or (u.get("pin") and secret.strip() == u["pin"]):
                user_found = u
                break
                
    if user_found:
        exp_login = (datetime.now() + timedelta(days=365)).date()
        c_mgr.set("crm_saved_login", user_found["login"], expires_at=exp_login)
        
        if remember:
            # Вместо второго вызова .set вешаем хук ожидания
            st.session_state["auth_pending_token"] = True
            st.session_state["auth_pending_user"] = user_found
        else:
            st.session_state.authenticated = True
            st.session_state.user_role = user_found["role"]
            st.session_state.user_login = user_found["login"]
            st.session_state.user_name = user_found.get("name", user_found["login"])
            st.toast("Вы успешно вошли!", icon="🔓")
        return True
    else:
        st.error("Неверный логин, пароль или PIN-код.")
        return False

def render_profile_settings(current_user_obj, save_data_func):
    st.markdown("### 🔓 Настройка PIN-кода")
    st.markdown("<small style='color:#7F8C9A;'>Установите 4-значный цифровой PIN для быстрого доступа со смартфона.</small>", unsafe_allow_html=True)
    
    db_pin = current_user_obj.get("pin", "")
    set_pin = st.text_input("Придумайте 4 цифры PIN:", value=db_pin, max_chars=4, type="password", key="auth_profile_pin")
    
    if st.button("Сохранить PIN-код", use_container_width=True, type="primary"):
        if set_pin.isdigit() and len(set_pin) == 4:
            current_user_obj["pin"] = set_pin
            save_data_func(st.session_state.crm_store)
            st.success("PIN-код успешно изменен!")
            st.rerun()
        else:
            st.error("Ошибка: PIN-код должен состоять строго из 4 ЦИФР!")
