import streamlit as st
import streamlit.components.v1 as components
import extra_streamlit_components as stx
import hashlib
import secrets
import base64
from datetime import datetime, timedelta

def get_cookie_manager():
    return stx.CookieManager()

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

def render_auth_screen(save_data_func):
    cookie_manager = get_cookie_manager()
    cookies = cookie_manager.get_all()
    
    # 1. Автоматический вход по долгосрочному токену
    if not st.session_state.get("authenticated"):
        stored_token = cookies.get("crm_auth_token")
        if stored_token:
            for u in st.session_state.crm_store.get("users", []):
                if u.get("auth_token") == stored_token:
                    st.session_state.authenticated = True
                    st.session_state.user_role = u["role"]
                    st.session_state.user_login = u["login"]
                    st.session_state.user_name = u.get("name", u["login"])
                    st.rerun()

    # 2. Вход через Face ID при успешном возврате из JavaScript
    if "bio_login_success" in st.query_params:
        logged_user = st.query_params.get("bio_login_success")
        for u in st.session_state.crm_store.get("users", []):
            if u["login"] == logged_user:
                st.session_state.authenticated = True
                st.session_state.user_role = u["role"]
                st.session_state.user_login = u["login"]
                st.session_state.user_name = u.get("name", u["login"])
                st.query_params.clear()
                st.rerun()

    if not st.session_state.get("authenticated"):
        st.markdown("<h2 style='text-align: center; margin-top: 2rem;'>Айплинт CRM</h2>", unsafe_allow_html=True)
        saved_login = cookies.get("crm_saved_login") or ""
        
        auth_mode = st.radio("Способ входа:", ["Пароль или PIN", "Face ID / Биометрия"], horizontal=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container(border=True):
                if auth_mode == "Пароль или PIN":
                    iu = st.text_input("Логин:", value=saved_login, placeholder="Введите логин")
                    ip = st.text_input("Пароль или 4-значный PIN:", type="password", placeholder="Введите пароль или PIN")
                    remember_me = st.checkbox("Больше не запрашивать пароль", value=True)
                    save_login_opt = st.checkbox("Запомнить логин на устройстве", value=True)
                    
                    if st.button("Войти", use_container_width=True, type="primary"):
                        user_found = None
                        for u in st.session_state.crm_store.get("users", []):
                            if u["login"] == iu.strip():
                                if verify_password(ip, u["password"]) or (u.get("pin") and ip.strip() == u["pin"]):
                                    user_found = u
                                    break
                        
                        if user_found:
                            st.session_state.authenticated = True
                            st.session_state.user_role = user_found["role"]
                            st.session_state.user_login = user_found["login"]
                            st.session_state.user_name = user_found.get("name", user_found["login"])
                            
                            if save_login_opt:
                                cookie_manager.set("crm_saved_login", user_found["login"], expires_at=datetime.now() + timedelta(days=365))
                            else:
                                cookie_manager.delete("crm_saved_login")
                                
                            if remember_me:
                                _token = secrets.token_hex(32)
                                user_found["auth_token"] = _token
                                save_data_func(st.session_state.crm_store)
                                cookie_manager.set("crm_auth_token", _token, expires_at=datetime.now() + timedelta(days=60))
                            
                            st.toast("Успешный вход!", icon="🔓")
                            st.rerun()
                        else:
                            st.error("Неверный логин, пароль или PIN.")
                elif auth_mode == "Face ID / Биометрия":
                    st.markdown("<p style='text-align:center; color:#7F8C9A;'>Вход по биометрии временно отключен ограничениями браузера. Используйте вход по PIN-коду.</p>", unsafe_allow_html=True)
        st.stop()

def render_profile_settings(current_user_obj, save_data_func):
    st.markdown("### 🔓 Быстрый вход по PIN-коду")
    st.markdown("<small style='color:#7F8C9A;'>Задайте 4 цифры, чтобы заходить в CRM со смартфона в одно нажатие, не вводя длинный пароль.</small>", unsafe_allow_html=True)
    
    db_pin = current_user_obj.get("pin", "")
    set_pin = st.text_input("Придумайте 4 цифры PIN:", value=db_pin, max_chars=4, type="password", key="auth_profile_pin")
    
    if st.button("Сохранить PIN-код", use_container_width=True, type="primary"):
        if set_pin.isdigit() and len(set_pin) == 4:
            current_user_obj["pin"] = set_pin
            save_data_func(st.session_state.crm_store)
            st.success("PIN-код успешно сохранен! Теперь его можно вводить в поле пароля при входе.")
        else:
            st.error("PIN должен состоять строго из 4 цифр!")
