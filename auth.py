import streamlit as st
import streamlit.components.v1 as components
import hashlib
import secrets

def hash_password(pwd, salt=None):
    if not pwd: return ""
    if salt is None: salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + pwd.strip()).encode()).hexdigest()
    return f"{salt}:{h}"

def verify_password(pwd, stored):
    if not stored: return False
    if ":" in stored:
        parts = stored.split(":")
        if len(parts) == 2:
            salt, h = parts
            return hashlib.sha256((salt + pwd.strip()).encode()).hexdigest() == h
    if len(stored) == 64 and all(c in "0123456789abcdef" for c in stored):
        return hashlib.sha256(pwd.strip().encode()).hexdigest() == stored
    return pwd.strip() == stored

def check_auto_login():
    """Мгновенный авто-вход без CookieManager."""
    if st.session_state.get("authenticated"):
        return True
    
    # Считываем токен, переданный из локального хранилища браузера
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

def render_auth_screen(save_data_func):
    st.markdown("<h2 style='text-align: center; margin-top: 3rem;'>Айплинт CRM</h2>", unsafe_allow_html=True)
    
    # JS-мост для чтения вечной сессии из памяти телефона
    if not st.session_state.get("authenticated") and "local_auth_token" not in st.query_params and "local_user" not in st.query_params and "_js_checked" not in st.query_params:
        st.components.v1.html("""
        <script>
            var token = localStorage.getItem('crm_token_v5');
            var user = localStorage.getItem('crm_user_v5');
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
                st.markdown(f"<p style='text-align:center; font-size:0.95rem; color:#7F8C9A;'>Вход для аккаунта: <b>{saved_login}</b></p>", unsafe_allow_html=True)
                
                # HTML+JS форма для ввода PIN-кода. Решает все ваши проблемы с клавиатурой, шрифтом и кнопкой Enter
                pin_html = f"""
                <div style="text-align:center;">
                    <input type="password" id="numeric_pin" maxlength="4" inputmode="numeric" pattern="[0-9]*" placeholder="••••" 
                           style="width:100%; max-width:200px; text-align:center; font-size:1rem; padding:10px; border:1.5px solid #DCE0E5; border-radius:10px; margin-bottom:15px; font-family:inherit;">
                    <br>
                    <button id="sub_btn" style="width:48%; padding:10px; background:#bc1661; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">Войти</button>
                    <button id="chg_btn" style="width:48%; padding:10px; background:transparent; color:#bc1661; border:1px solid #C9CFD7; border-radius:10px; cursor:pointer;">Сменить</button>
                </div>
                <script>
                    var input = document.getElementById('numeric_pin');
                    input.focus();
                    
                    // Вход по нажатию Enter (Ввод)
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
                        localStorage.removeItem('crm_user_v5');
                        localStorage.removeItem('crm_token_v5');
                        window.parent.location.href = window.parent.location.pathname;
                    }};
                </script>
                """
                st.components.v1.html(pin_html, height=110)
                
                # Обработка отправки PIN-кода из HTML-формы
                if "submit_pin" in st.query_params:
                    entered_pin = st.query_params["submit_pin"]
                    if match_and_authorize(saved_login, entered_pin, save_data_func):
                        st.rerun()
            else:
                # Первичный вход (если заходят первый раз)
                st.markdown("<p style='text-align:center; color:#7F8C9A;'>Первичный вход в CRM</p>", unsafe_allow_html=True)
                with st.form("initial_form"):
                    iu = st.text_input("Логин:", placeholder="Введите логин")
                    ip = st.text_input("Пароль:", type="password", placeholder="Введите пароль")
                    submit = st.form_submit_button("Войти в систему", use_container_width=True, type="primary")
                    
                    if submit:
                        if match_and_authorize(iu, ip, save_data_func):
                            st.rerun()
    st.stop()

def match_and_authorize(login, secret, save_data_func):
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
        save_data_func(st.session_state.crm_store)
        
        # Записываем данные в LocalStorage телефона через JS-инъекцию
        st.components.v1.html(f"""
        <script>
            localStorage.setItem('crm_user_v5', '{user_found["login"]}');
            localStorage.setItem('crm_token_v5', '{_token}');
            window.parent.location.href = window.parent.location.pathname;
        </script>
        """, height=0)
        st.stop()
        return True
    else:
        st.error("Неверный логин, пароль или PIN-код.")
        return False

def render_profile_settings(current_user_obj, save_data_func):
    st.markdown("### 🔓 Настройка PIN-кода")
    db_pin = current_user_obj.get("pin", "")
    set_pin = st.text_input("Придумайте 4 цифры PIN:", value=db_pin, max_chars=4, type="password", key="auth_profile_pin")
    
    if st.button("Сохранить PIN-код", use_container_width=True, type="primary"):
        if set_pin.isdigit() and len(set_pin) == 4:
            current_user_obj["pin"] = set_pin
            save_data_func(st.session_state.crm_store)
            st.success("PIN-код успешно изменен!")
            st.rerun()
        else:
            st.error("Ошибка: PIN должен состоять строго из 4 ЦИФР!")
