import streamlit as st
import streamlit.components.v1 as components
import json, os, re, html, urllib.parse, requests, hashlib, base64, csv, io, secrets, threading, uuid, sqlite3, copy, time
from pathlib import Path

# WebAuthn / Passkeys. Если зависимость ещё не установлена, парольный вход продолжает работать.
try:
    from webauthn import (
        generate_registration_options,
        verify_registration_response,
        generate_authentication_options,
        verify_authentication_response,
    )
    from webauthn.helpers import options_to_json
    from webauthn.helpers.structs import (
        AuthenticatorSelectionCriteria,
        ResidentKeyRequirement,
        UserVerificationRequirement,
    )
    PASSKEY_AVAILABLE = True
except Exception:
    PASSKEY_AVAILABLE = False

PASSKEY_RP_ID = "iplinth-crm.streamlit.app"
PASSKEY_ORIGIN = "https://iplinth-crm.streamlit.app"
PASSKEY_RP_NAME = "Айплинт CRM"
_PASSKEY_COMPONENT_DIR = Path(__file__).resolve().parent / "passkey_component"
crm_passkey_component = components.declare_component(
    "crm_passkey_component", path=str(_PASSKEY_COMPONENT_DIR)
)
from concurrent.futures import ThreadPoolExecutor
from PIL import Image as PILImage
import extra_streamlit_components as stx
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict
from calendar import monthrange

def _safe_id(v):
    """Safely convert value to int, returning 0 for non-numeric values."""
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0

st.set_page_config(
    page_title="Айплинт CRM",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# При первом входе боковая панель по умолчанию свернута.
if "_crm_sidebar_visible" not in st.session_state:
    st.session_state["_crm_sidebar_visible"] = False
st.markdown("""
<style>
    .stApp { background-color: #F5F6F8; color: #2C3E50; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif; }
    /* Уменьшаем пустое пространство над главной шапкой CRM. */
    .block-container { padding-top: 0.45rem !important; }
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
    .stTextArea textarea { overflow-wrap:anywhere !important; white-space:pre-wrap !important; resize:vertical !important; }
    .stTextInput > div > input, .stTextArea > div > textarea, .stNumberInput > div > div > input { background-color: #FFFFFF !important; border-radius: 10px !important; border: 1.5px solid #DCE0E5 !important; padding: 0.55rem 0.8rem !important; color: #2C3E50 !important; font-size: 1rem; }
    input[placeholder*="Поиск"], .stTextInput input[aria-label="Поиск"] { background-color:#FFFFFF !important; }
    .stNumberInput button { display:none !important; }
    .stNumberInput input { -moz-appearance:textfield !important; }
    .stNumberInput input::-webkit-inner-spin-button, .stNumberInput input::-webkit-outer-spin-button { -webkit-appearance:none !important; margin:0 !important; }
    .stTextInput > div > input:focus, .stTextArea > div > textarea:focus, .stNumberInput > div > div > input:focus, .stSelectbox > div > div:focus-within { outline: none; border-color: #DCE0E5 !important; box-shadow: none !important; }
    .stSelectbox > div > div { background-color: #FFFFFF; border-radius: 10px; border: 1.5px solid #DCE0E5; padding: 0.35rem 0.75rem; }
    [data-testid="stMetric"] { background-color: #FFFFFF; border-radius: 14px; padding: 1rem 1.25rem; border: 1px solid #E8EBEF; box-shadow: 0 2px 6px rgba(0,0,0,0.02); }
    [data-testid="stMetric"] label { font-size: 0.78rem; color: #7F8C9A; text-transform: uppercase; letter-spacing: 0.03em; font-weight: 600; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 1.5rem; font-weight: 700; color: #2C3E50; }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #C9CFD7; border-radius: 4px; }
    /* Fix scrollbar going under Streamlit header */
    section[data-testid="stMainViewContainer"] { overflow-y: auto !important; }
    [data-testid="stAppViewBlockContainer"] { overflow: visible !important; }
    /* Скрываем служебную верхнюю панель Streamlit. */
    [data-testid="stHeader"] { display: none !important; }
    #MainMenu, footer { visibility: hidden !important; }
    .stMarkdown p, .stMarkdown li { color: #3C4A5A; line-height: 1.6; }
    .stMarkdown strong { color: #2C3E50; font-weight: 600; }
    .stMarkdown { margin-top: 0.15rem !important; margin-bottom: 0.15rem !important; }
    code { background-color: #EEF0F3; color: #5A6B7D; border-radius: 6px; padding: 0.1rem 0.35rem; font-size: 0.9em; }
    .stHorizontalBlock .stButton button { border-radius: 12px; font-size: 0.95rem; font-weight: 600; padding: 0.65rem 1rem; }
    .stHorizontalBlock { gap: 0.4rem !important; }
    [data-testid="stFileUploader"] { border-radius: 14px; border: 2px dashed #C9CFD7; background-color: #FAFBFC; padding: 0.75rem; }
    .greeting-block { margin-bottom: 0.1rem !important; margin-top: 0.1rem !important; padding-top: 0 !important; padding-bottom: 0 !important; }
    h1 { margin-top: 0.1rem !important; margin-bottom: 0.1rem !important; padding-top: 0 !important; padding-bottom: 0 !important; }
    .stHorizontalBlock { margin-top: 0.1rem !important; margin-bottom: 0.1rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.2rem !important; }
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
    .chat-msg { padding: 5px 8px; border-radius: 8px; margin-bottom: 4px; max-width: 80%; font-size: 0.88rem; line-height: 1.35; }
    .chat-msg-me { background-color: #D978A4; color: #FFFFFF; margin-left: auto; }
    .chat-msg-other { background-color: #F4F5F7; color: #2C3E50; }
    .stTextArea textarea::placeholder, .stTextInput input::placeholder { font-size: 0.875rem !important; color: #808B98 !important; opacity: 1 !important; }
    .qa-card { background: #FFFFFF; border: 1px solid #E8EBEF; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
    #crm-lightbox { position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:999999; display:none; align-items:center; justify-content:center; cursor:pointer; }
    #crm-lightbox img { max-width:90%; max-height:90%; border-radius:8px; }
    .thumb-item { position:relative; width:110px; margin: 0 auto; text-align:center; }
    .thumb-item img { width:110px; height:110px; object-fit:cover; border-radius:8px; cursor:default; border:1px solid #DCE0E5; display:block; margin:0 auto; }
    .thumb-item img:hover { border-color:#DCE0E5; }
    .thumb-name { font-size:0.7rem; color:#7F8C9A; max-width:110px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; margin-bottom:6px; text-align:center; }
    .created-date { font-size: 0.72rem; color: #95A5B7; font-style: italic; margin-bottom: 0.8rem !important; }
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

    .rework-badge { display: inline-block; background: #D32F2F; color: white; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 99px; margin-left: 6px; text-transform: uppercase; letter-spacing: 0.04em; }
    [data-testid="stMultiInput"] > div > div > p { display: none !important; }
    [data-testid="stMultiInput"] > div > div { background-color: #FFFFFF !important; border-radius: 10px !important; border: 1.5px solid #DCE0E5 !important; }
    .stMarkdown p, .stMarkdown li { font-size: 0.9rem; }
    .stButton > button { font-size: 0.85rem !important; }
    .stHorizontalBlock .stButton button { font-size: 0.85rem !important; }
    h3 { font-size: 1rem !important; }
    .arch-search-input > div > input { background-color: #FFFFFF !important; border: 1.5px solid #DCE0E5 !important; border-radius: 10px !important; }

    /* Sticky search bar for deals tab — JS-driven, no parent overflow changes */
    .st-key-deals_sticky_header { transition: none; }
    .deals-sticky-fixed { position: fixed !important; top: 0 !important; left: 0 !important; right: 0 !important; z-index: 9999 !important; background-color: #F5F6F8 !important; padding: 8px 1rem !important; box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important; }
    .deals-sticky-placeholder { height: 0; }
    /* Scroll-to-top button */

    /* Notification dialog: set width on the outer Streamlit dialog wrapper itself */
    [data-testid="stDialog"]:has(.st-key-notif_dlg),
    [data-testid="stDialog"]:has(.st-key-notif_dlg) > div,
    [data-testid="stDialog"]:has(.st-key-notif_dlg) [role="dialog"],
    [data-testid="stDialog"] [role="dialog"]:has(.st-key-notif_dlg) {
        width: 24vw !important;
        min-width: 24vw !important;
        max-width: 24vw !important;
        max-height: 50vh !important;
        box-sizing: border-box !important;
    }
    @media (max-width: 700px) {
        [data-testid="stDialog"]:has(.st-key-notif_dlg),
        [data-testid="stDialog"]:has(.st-key-notif_dlg) > div,
        [data-testid="stDialog"]:has(.st-key-notif_dlg) [role="dialog"],
        [data-testid="stDialog"] [role="dialog"]:has(.st-key-notif_dlg) {
            width: 92vw !important;
            min-width: 92vw !important;
            max-width: 92vw !important;
        }
    }
    .st-key-notif_dlg {
        max-height: 50vh !important;
        overflow-y: auto !important;
    }
    #crm-scroll-top { position: fixed; bottom: 24px; right: 24px; width: 44px; height: 44px; border-radius: 50%; background: #bc1661; color: white; border: none; font-size: 20px; cursor: pointer; z-index: 999998; display: none; box-shadow: 0 2px 8px rgba(188,22,97,0.3); transition: opacity 0.2s; }
    #crm-scroll-top:hover { background: #9a1452; }
    /* Compact task detail */
    .task-detail-compact .stMarkdown { margin-top: 0.05rem !important; margin-bottom: 0.05rem !important; line-height: 1.3 !important; }
    .task-detail-compact .stMarkdown p { line-height: 1.3 !important; margin-bottom: 0.1rem !important; }
    .task-detail-compact .stButton > button { padding: 0.3rem 0.7rem !important; font-size: 0.85rem !important; min-height: 30px !important; margin-top: 0.05rem !important; margin-bottom: 0.05rem !important; }
    .task-detail-compact .stTextInput > div > input, .task-detail-compact .stTextArea > div > textarea, .task-detail-compact .stSelectbox > div > div { padding: 0.35rem 0.6rem !important; font-size: 0.9rem !important; }
    .task-detail-compact .stHorizontalBlock { gap: 0.2rem !important; }
    .task-detail-compact hr { margin: 0.3rem 0 !important; }
    .task-detail-compact .stFileUploader { padding: 0.4rem !important; }
    .task-detail-compact .stContainer { margin-top: 0.05rem !important; margin-bottom: 0.05rem !important; }
    .task-detail-compact [data-testid="stMetric"] { padding: 0.4rem 0.6rem !important; }

    /* Bell button compact */
    .crm-bell-btn button { min-width: 48px !important; font-size: 1rem !important; padding: 0.4rem 0.6rem !important; }
    /* Notification dialog sizing */
    .st-key-notif_dlg { max-height: 50vh !important; overflow-y: auto !important; }
    /* Кнопки «Прочитать все» и «Очистить прочитанные»: стандартный размер Streamlit */
    /* Compact notification list with minimal spacing */
    .st-key-notif_dlg [data-testid="stMarkdown"] { margin-top: 0 !important; margin-bottom: 0 !important; }
    .st-key-notif_dlg p { margin-top: 0 !important; margin-bottom: 2px !important; line-height: 1.2 !important; }
    .st-key-notif_dlg hr { margin: 3px 0 !important; }
    .st-key-notif_dlg [data-testid="stVerticalBlock"] { gap: 0.2rem !important; }
    /* Kanban column scroll for internal tasks */
    .st-key-it_col_new, .st-key-it_col_work, .st-key-it_col_review { min-height: 100px; }

    /* Hide native dialog close button */
    [data-testid="stDialog"] [data-testid="stCloseButton"],
    [data-testid="stDialog"] button[aria-label="Close"],
    [data-testid="stDialog"] header button[kind="header"],
    .stDialog button[kind="header"],
    [data-testid="stDialog"] > div > div > button:first-child {
        display: none !important;
    }
    /* Make dialog content area the positioning context for the close button */
    [data-testid="stDialog"] [data-testid="stVerticalBlock"],
    [data-testid="stDialog"] > div > div,
    [data-testid="stEmotionCache"] [data-testid="stDialog"] > div > div {
        position: relative !important;
    }
    /* Custom close button positioning */
    .crm-dialog-close-btn button {
        position: absolute !important;
        top: 0.4rem !important;
        right: 0.4rem !important;
        width: 36px !important;
        height: 36px !important;
        min-width: 36px !important;
        min-height: 36px !important;
        padding: 0 !important;
        font-size: 1.1rem !important;
        line-height: 1 !important;
        background: #FFFFFF !important;
        border: 1px solid #DCE0E5 !important;
        border-radius: 8px !important;
        color: #5A6B7D !important;
        z-index: 9999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .crm-dialog-close-btn button:hover {
        background: #EEF0F3 !important;
        border-color: #C9CFD7 !important;
    }
    /* Unsaved changes warning box */
    .crm-unsaved-warning {
        border: 2px solid #FF9800 !important;
        border-radius: 10px !important;
        background-color: #FFF8E1 !important;
        padding: 0.5rem 0.8rem !important;
        margin: 0.3rem 0 !important;
    }
    .crm-unsaved-warning p {
        font-size: 0.85rem !important;
        margin-bottom: 0.2rem !important;
    }
    .crm-unsaved-warning .stButton > button {
        font-size: 0.78rem !important;
        padding: 0.25rem 0.5rem !important;
        min-height: 28px !important;
    }

    /* Clients table */
    .clients-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; background: #FFFFFF; border: 1px solid #DCE0E5; border-radius: 8px; overflow: hidden; }
    .clients-table th { background: #EEF0F3; color: #2C3E50; font-weight: 700; padding: 10px 12px; text-align: left; border: 1px solid #DCE0E5; white-space: nowrap; }
    .clients-table td { padding: 8px 12px; border: 1px solid #DCE0E5; color: #2C3E50; vertical-align: middle; }
    .clients-table tr:hover td { background: #F5F6F8; }
    .clients-table .link-cell { color: #bc1661; text-decoration: underline; cursor: pointer; font-weight: 600; }
    .clients-table .link-cell:hover { color: #9a1452; }
    .clients-table .green-link { color: #2E7D32; text-decoration: none; cursor: pointer; font-weight: 700; }
    .clients-table .green-link:hover { color: #1B5E20; }
    .clients-table .red-link { color: #C62828; text-decoration: none; cursor: pointer; font-weight: 700; }
    .clients-table .red-link:hover { color: #8E1B1B; }
    .clients-table .normal-link { color: #2C3E50; text-decoration: none; cursor: pointer; font-weight: 600; }
    .clients-table .normal-link:hover { color: #bc1661; }
    .clients-table .sum-cell { text-align: right; font-weight: 600; white-space: nowrap; }
    /* Compact client list rows */
    .client-row-text { cursor: pointer; font-size: 0.88rem; color: #2C3E50; padding: 2px 0; }
    .client-row-text:hover { color: #bc1661; }
    .client-divider { border-top: 1px solid #E8EBEF; margin: 0; padding: 0; height: 0; }


    /* === FIX: White background for ALL inputs in dialogs === */
    [data-testid="stDialog"] .stTextInput > div > input,
    [data-testid="stDialog"] .stTextArea > div > textarea,
    [data-testid="stDialog"] .stNumberInput > div > div > input,
    [data-testid="stDialog"] .stSelectbox > div > div,
    [data-testid="stDialog"] [data-testid="stBaseInput"],
    [data-testid="stDialog"] [data-baseweb="input"],
    [data-testid="stDialog"] [data-baseweb="base-input"],
    [data-testid="stDialog"] [data-baseweb="textarea"],
    [data-testid="stDialog"] [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1.5px solid #DCE0E5 !important;
        border-radius: 10px !important;
        -webkit-text-fill-color: #2C3E50 !important;
    }
    [data-testid="stDialog"] .stTextInput > div > input:focus,
    [data-testid="stDialog"] .stTextArea > div > textarea:focus,
    [data-testid="stDialog"] .stNumberInput > div > div > input:focus {
        border-color: #C9CFD7 !important;
        box-shadow: none !important;
        background-color: #FFFFFF !important;
    }
    [data-testid="stDialog"] [data-baseweb="base-input"]:focus,
    [data-testid="stDialog"] [data-baseweb="input"]:focus,
    [data-testid="stDialog"] input:focus,
    [data-testid="stDialog"] textarea:focus {
        border-color: #C9CFD7 !important;
        box-shadow: none !important;
        background-color: #FFFFFF !important;
        -webkit-text-fill-color: #2C3E50 !important;
    }
    /* Override any gray background on dialog inputs */
    [data-testid="stDialog"] input[aria-label],
    [data-testid="stDialog"] textarea[aria-label],
    [data-testid="stDialog"] input[type="text"],
    [data-testid="stDialog"] input[type="number"],
    [data-testid="stDialog"] input[type="email"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #DCE0E5 !important;
    }
    [data-testid="stDialog"] [data-baseweb="base-input"][aria-disabled="false"] {
        background-color: #FFFFFF !important;
    }

    /* === FIX: Remove red border from search input === */
    .st-key-search_input_key input,
    .st-key-search_input_key input:focus,
    .st-key-search_input_key input:focus-visible,
    .st-key-search_input_key input:invalid,
    .st-key-search_input_key input:required,
    .st-key-search_input_key input:not(:placeholder-shown),
    .st-key-search_input_key [data-baseweb="base-input"],
    .st-key-search_input_key [data-baseweb="input"] {
        border: 1.5px solid #C9CFD7 !important;
        box-shadow: none !important;
        outline: none !important;
        -webkit-box-shadow: none !important;
    }
    .st-key-search_input_key [data-baseweb="base-input"]:focus,
    .st-key-search_input_key [data-baseweb="input"]:focus {
        border-color: #C9CFD7 !important;
        box-shadow: none !important;
    }

    /* === FIX: Tooltip z-index to prevent overlapping dialogs === */
    [data-testid="stTooltip"] { z-index: 1 !important; pointer-events: none !important; }
    [data-testid="stTooltipContent"] { z-index: 1 !important; pointer-events: none !important; }

    /* === Increase font size for deal/task counts in clients table === */
    .clients-table .green-link { font-size: 1.05rem !important; }
    .clients-table .red-link { font-size: 1.05rem !important; }
    .clients-table .normal-link { font-size: 1.05rem !important; }


    /* Мгновенная визуальная обратная связь при нажатии кнопок */
    .stButton > button, button[kind="primary"], button[kind="secondary"] {
        transform-origin: center center;
        transition: transform 100ms ease, filter 100ms ease, box-shadow 120ms ease, outline-color 120ms ease !important;
        -webkit-tap-highlight-color: transparent;
    }
    .stButton > button:active, button[kind="primary"]:active, button[kind="secondary"]:active {
        transform: scale(0.965) translateY(1px) !important;
        filter: brightness(0.90) !important;
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.18) !important;
        transition-duration: 45ms !important;
    }
    /* После клика кнопка остаётся слегка выделенной, пока фокус не перейдёт дальше */
    .stButton > button:focus, button[kind="primary"]:focus, button[kind="secondary"]:focus {
        outline: 3px solid rgba(188, 22, 97, 0.28) !important;
        outline-offset: 2px !important;
    }
    .stButton > button:focus:not(:active) {
        animation: crm-click-confirm 260ms ease-out;
    }
    @keyframes crm-click-confirm {
        0% { transform: scale(0.975); }
        65% { transform: scale(1.015); }
        100% { transform: scale(1); }
    }
    /* Обратная связь и для ссылок: переходы между разделами, ссылки в таблицах и тексте */
    a[href] {
        -webkit-tap-highlight-color: transparent;
        transition: color 100ms ease, filter 80ms ease, opacity 80ms ease, outline-color 120ms ease !important;
        text-underline-offset: 3px;
    }
    a[href]:hover {
        filter: brightness(0.88);
        text-decoration-thickness: 2px;
    }
    a[href]:active {
        opacity: 0.62 !important;
        filter: brightness(0.78) !important;
        text-decoration: underline !important;
        text-decoration-thickness: 2px !important;
        transition-duration: 35ms !important;
    }
    a[href]:focus-visible {
        outline: 3px solid rgba(188, 22, 97, 0.30) !important;
        outline-offset: 3px;
        border-radius: 3px;
    }
    a[href]:focus:not(:active) {
        animation: crm-link-click-confirm 260ms ease-out;
    }
    @keyframes crm-link-click-confirm {
        0% { opacity: 0.65; filter: brightness(0.78); }
        65% { opacity: 1; filter: brightness(1.08); }
        100% { opacity: 1; filter: brightness(1); }
    }
    @media (prefers-reduced-motion: reduce) {
        .stButton > button, button[kind="primary"], button[kind="secondary"], a[href] {
            transition: none !important;
            animation: none !important;
        }
    }
    /* PIN login button must keep the requested burgundy color regardless of browser theme. */
    .st-key-remembered_pin_login_btn button,
    .st-key-remembered_pin_login_form button[kind="primary"] {
        background: #bc1661 !important; background-color: #bc1661 !important;
        color: #ffffff !important; border-color: #bc1661 !important;
    }
    .st-key-remembered_pin_login_btn button:hover,
    .st-key-remembered_pin_login_form button[kind="primary"]:hover {
        background: #a31353 !important; background-color: #a31353 !important;
    }
</style>
""", unsafe_allow_html=True)

# Явно управляем отображением боковой панели через состояние CRM.
# Важно принудительно задавать параметры и для открытого, и для закрытого состояния:
# стандартная кнопка Streamlit скрыта вместе с верхней панелью.
if st.session_state.get("_crm_sidebar_visible", True):
    st.markdown("""<style>
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            width: 21rem !important;
            min-width: 21rem !important;
            max-width: 21rem !important;
            transform: translateX(0) !important;
            margin-left: 0 !important;
            opacity: 1 !important;
            pointer-events: auto !important;
        }
        section[data-testid="stSidebar"] > div { width: 21rem !important; }
    </style>""", unsafe_allow_html=True)
else:
    st.markdown("""<style>
        section[data-testid="stSidebar"] {
            display: none !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
        }
        section[data-testid="stMain"] { margin-left: 0 !important; width: 100% !important; }
        [data-testid="stAppViewContainer"] > .main { margin-left: 0 !important; width: 100% !important; }
    </style>""", unsafe_allow_html=True)

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

    // Scroll-to-top button
    w.crmInitScrollTop = function() {
        var doc = w.document;
        var btn = doc.getElementById('crm-scroll-top');
        if (!btn) {
            btn = doc.createElement('button');
            btn.id = 'crm-scroll-top';
            btn.innerHTML = '\u2191';
            btn.style.cssText = 'position:fixed;bottom:24px;right:24px;width:44px;height:44px;border-radius:50%;background:#bc1661;color:white;border:none;font-size:20px;cursor:pointer;z-index:999998;display:none;box-shadow:0 2px 8px rgba(188,22,97,0.3);transition:opacity 0.2s;';
            btn.onclick = function() { w.scrollTo({top:0, behavior:'smooth'}); };
            btn.addEventListener('mouseenter', function() { this.style.background = '#9a1452'; });
            btn.addEventListener('mouseleave', function() { this.style.background = '#bc1661'; });
            doc.body.appendChild(btn);
            w.addEventListener('scroll', function() {
                if (w.scrollY > 300) { btn.style.display = 'block'; }
                else { btn.style.display = 'none'; }
            });
        }
    };
    setTimeout(w.crmInitScrollTop, 500);

    // Intercept Escape key in dialogs ONLY when unsaved changes warning is shown
    w.crmInitDialogEscape = function() {
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                var warning = document.querySelector('.crm-unsaved-warning');
                if (warning) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            }
        }, true);
    };
    setTimeout(w.crmInitDialogEscape, 500);

    // Prevent dialog close on outside/backdrop click using CSS only (no MutationObserver)
    // CSS handles pointer-events on the overlay; JS only prevents backdrop clicks
    w.crmPreventDialogBackdrop = function() {
        document.addEventListener('mousedown', function(e) {
            var dlg = document.querySelector('[data-testid="stDialog"]');
            if (dlg && !dlg.contains(e.target) && e.target !== dlg) {
                e.preventDefault();
                e.stopPropagation();
            }
        }, true);
        document.addEventListener('click', function(e) {
            var dlg = document.querySelector('[data-testid="stDialog"]');
            if (dlg && !dlg.contains(e.target) && e.target !== dlg) {
                e.preventDefault();
                e.stopPropagation();
            }
        }, true);
    };
    setTimeout(w.crmPreventDialogBackdrop, 500);


</script>
""", height=0)

FILE_NAME = "web_crm_database_v2.json"
YANDEX_API_URL = "https://cloud-api.yandex.net/v1/disk/resources"
MAX_URL = "https://max.ru"
MAX_NUMBER = "+79003293300"
CATEGORIES = ["Не определён", "Дизайнер", "Строитель", "Дилер", "Покупатель"]
CONTACT_METHODS = ["", "Телефон", "WhatsApp", "Telegram", "MAX", "Директ", "eMail"]
TASK_TYPES = ["Связаться", "Отправить заказ", "Отправить образцы"]
SHIP_PAY_OPTIONS = ["", "Включено в счёт", "Клиентом при получении"]

raw_token = st.secrets.get("YANDEX_DISK_TOKEN", "")
if isinstance(raw_token, str):
    YANDEX_TOKEN = raw_token.strip().strip('"').strip("'")
else:
    YANDEX_TOKEN = ""

MOSCOW_TZ = ZoneInfo("Europe/Moscow")

def moscow_now():
    """Текущее московское время без tzinfo для совместимости с существующими строками дат CRM."""
    return datetime.now(MOSCOW_TZ).replace(tzinfo=None)

def now_str():
    return moscow_now().strftime("%Y-%m-%d %H:%M:%S")

def get_sort_key(entity):
    return entity.get("last_modified", "1970-01-01 00:00:00")

def generate_task_number(prefix):
    year = moscow_now().strftime("%y")
    max_num = 0
    for c in st.session_state.crm_store.get("clients", []):
        for t in c.get("tasks", []):
            tn = t.get("task_number", "")
            if tn.startswith(f"{prefix}{year}-"):
                try: max_num = max(max_num, int(tn.split("-")[1]))
                except: pass
    return f"{prefix}{year}-{max_num + 1}"

def generate_deal_number():
    year = moscow_now().strftime("%y")
    max_num = 0
    for d in st.session_state.crm_store.get("deals", []):
        dn = d.get("deal_number", "")
        if dn.startswith(f"Сделка №{year}-"):
            try: max_num = max(max_num, int(dn.split("-")[1]))
            except: pass
    return f"Сделка №{year}-{max_num + 1}"

def assign_task_numbers(data):
    year = moscow_now().strftime("%y")
    zk_max, zs_max = 0, 0
    for c in data.get("clients", []):
        for t in c.get("tasks", []):
            tn = t.get("task_number", "")
            if tn.startswith(f"ЗК{year}-"):
                try: zk_max = max(zk_max, int(tn.split("-")[1]))
                except: pass
            elif tn.startswith(f"ЗС{year}-"):
                try: zs_max = max(zs_max, int(tn.split("-")[1]))
                except: pass
    for c in data.get("clients", []):
        for t in c.get("tasks", []):
            if not t.get("task_number"):
                if t.get("deal_id"):
                    zs_max += 1
                    t["task_number"] = f"ЗС{year}-{zs_max}"
                else:
                    zk_max += 1
                    t["task_number"] = f"ЗК{year}-{zk_max}"

def assign_deal_numbers(data):
    year = moscow_now().strftime("%y")
    max_num = 0
    for d in data.get("deals", []):
        dn = d.get("deal_number", "")
        if dn.startswith(f"Сделка №{year}-"):
            try: max_num = max(max_num, int(dn.split("-")[1]))
            except: pass
    for d in data.get("deals", []):
        if not d.get("deal_number"):
            max_num += 1
            d["deal_number"] = f"Сделка №{year}-{max_num}"
        if d.get("title", "").startswith("Заказ"):
            d["title"] = d.get("deal_number", d["title"])

def inject_payment_container_css(deal_id, status):
    border_color = "#2E7D32" if status == "Оплачено" else "#C62828"
    bg_color = "#E8F5E9" if status == "Оплачено" else "#FFEBEE"
    st.markdown(f"<style>.st-key-ps_wrap_{deal_id} {{ border: 2px solid {border_color} !important; border-radius: 10px !important; background-color: {bg_color} !important; padding: 8px 12px !important; }}</style>", unsafe_allow_html=True)

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

def yandex_headers():
    return {"Authorization": f"OAuth {YANDEX_TOKEN}", "Accept": "application/json"}

def check_cloud_status():
    if not YANDEX_TOKEN: return False
    try:
        return requests.get(YANDEX_API_URL, headers=yandex_headers(), timeout=5).status_code == 200
    except: return False

def init_yandex_folders():
    if not YANDEX_TOKEN: return
    for folder in ["CRM_NE_TROGAT", "CRM_NE_TROGAT/uploads"]:
        try: requests.put(YANDEX_API_URL, params={"path": f"disk:/{folder}"}, headers=yandex_headers(), timeout=10)
        except: pass

def _collect_all_timestamps(data):
    """Собирает все last_modified из клиентов, сделок, задач и внутренних задач для точного сравнения."""
    timestamps = []
    for c in data.get("clients", []):
        timestamps.append(c.get("last_modified", ""))
        for t in c.get("tasks", []):
            timestamps.append(t.get("last_modified", ""))
    for d in data.get("deals", []):
        timestamps.append(d.get("last_modified", ""))
    for it in data.get("internal_tasks", []):
        timestamps.append(it.get("last_modified", ""))
    for s in data.get("suppliers", []):
        timestamps.append(s.get("last_modified", ""))
    return [ts for ts in timestamps if ts]

def download_db_from_yandex():
    if not YANDEX_TOKEN: return
    try:
        res = requests.get(f"{YANDEX_API_URL}/download", params={"path": f"disk:/CRM_NE_TROGAT/{FILE_NAME}"}, headers=yandex_headers(), timeout=10)
        if res.status_code == 200:
            dl = requests.get(res.json().get("href"), timeout=30)
            if dl.status_code == 200:
                new_text = dl.text
                # Проверяем, не старее ли данные на Диске по сравнению с локальным файлом
                if os.path.exists(FILE_NAME):
                    try:
                        old_data = json.loads(open(FILE_NAME, "r", encoding="utf-8").read())
                        new_data = json.loads(new_text)
                        # Собираем ВСЕ last_modified, включая задачи
                        old_ts = _collect_all_timestamps(old_data)
                        new_ts = _collect_all_timestamps(new_data)
                        old_max = max(old_ts) if old_ts else ""
                        new_max = max(new_ts) if new_ts else ""
                        if new_max < old_max:
                            # Данные на Диске старее локальных — не перезаписываем
                            return
                    except:
                        # При любой ошибке сравнения — НЕ перезаписываем локальные данные
                        return
                with open(FILE_NAME, "w", encoding="utf-8") as f: f.write(new_text)
                return
    except: pass
    if not os.path.exists(FILE_NAME):
        db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}], "_migrated": "v2", "internal_tasks": [], "chat_messages": [], "qa_entries": [], "suppliers": [], "notifications": []}
        with open(FILE_NAME, "w", encoding="utf-8") as f: json.dump(db, f, ensure_ascii=False, indent=2)

def upload_db_to_yandex_sync():
    if not YANDEX_TOKEN or not os.path.exists(FILE_NAME): return False
    for attempt in range(3):
        try:
            res = requests.get(f"{YANDEX_API_URL}/upload", params={"path": f"disk:/CRM_NE_TROGAT/{FILE_NAME}", "overwrite": "true"}, headers=yandex_headers(), timeout=15)
            if res.status_code == 200:
                with open(FILE_NAME, "rb") as f:
                    resp = requests.put(res.json().get("href"), data=f, timeout=30)
                if resp.status_code in (200, 201):
                    return True
        except Exception as e:
            pass
    return False

def upload_db_to_yandex_async():
    """Совместимый интерфейс: ставит актуальный снимок базы в очередь фоновой синхронизации."""
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            _queue_yandex_snapshot(f.read())
    except Exception:
        pass

# Облачная синхронизация не должна блокировать обработчик нажатия кнопки.
# Очередь хранит только самый свежий снимок: если пользователь быстро сделал
# несколько изменений, промежуточные полные копии не отправляются на Диск.
_cloud_sync_lock = threading.Lock()
_cloud_sync_pending_snapshot = None
_cloud_sync_worker_running = False
_cloud_sync_last_ok = None
_cloud_sync_last_error = ""
_cloud_sync_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="crm-yandex-sync")

def _upload_yandex_snapshot(snapshot_text):
    """Загружает переданный снимок JSON на Яндекс Диск с ограниченными повторами."""
    if not YANDEX_TOKEN:
        return True  # Облачная синхронизация не настроена; локальное сохранение работает.
    payload = snapshot_text.encode("utf-8")
    last_error = "Не удалось загрузить базу на Яндекс Диск"
    for attempt in range(3):
        try:
            res = requests.get(
                f"{YANDEX_API_URL}/upload",
                params={"path": f"disk:/CRM_NE_TROGAT/{FILE_NAME}", "overwrite": "true"},
                headers=yandex_headers(), timeout=10)
            if res.status_code == 200:
                href = res.json().get("href")
                if href:
                    resp = requests.put(href, data=payload, timeout=20)
                    if resp.status_code in (200, 201, 202):
                        return True
                    last_error = f"HTTP {resp.status_code} при загрузке файла"
            else:
                last_error = f"HTTP {res.status_code} при запросе ссылки загрузки"
        except Exception as exc:
            last_error = str(exc)[:300]
        if attempt < 2:
            # Короткая пауза только в фоновом потоке, не в обработчике UI.
            import time
            time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(last_error)

def _cloud_sync_worker():
    global _cloud_sync_pending_snapshot, _cloud_sync_worker_running
    global _cloud_sync_last_ok, _cloud_sync_last_error
    while True:
        with _cloud_sync_lock:
            snapshot = _cloud_sync_pending_snapshot
            _cloud_sync_pending_snapshot = None
            if snapshot is None:
                _cloud_sync_worker_running = False
                return
        try:
            ok = _upload_yandex_snapshot(snapshot)
            _cloud_sync_last_ok = bool(ok)
            _cloud_sync_last_error = "" if ok else "Не удалось загрузить базу на Яндекс Диск"
        except Exception as exc:
            _cloud_sync_last_ok = False
            _cloud_sync_last_error = str(exc)[:300]
        # Если во время загрузки пришёл новый снимок, цикл отправит только
        # последний из ожидающих снимков.

def _queue_yandex_snapshot(snapshot_text):
    global _cloud_sync_pending_snapshot, _cloud_sync_worker_running
    if not YANDEX_TOKEN:
        return
    with _cloud_sync_lock:
        _cloud_sync_pending_snapshot = snapshot_text
        if not _cloud_sync_worker_running:
            _cloud_sync_worker_running = True
            _cloud_sync_executor.submit(_cloud_sync_worker)

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

def format_phone(p_str):
    if not p_str: return ""
    d = re.sub(r"\D", "", p_str)
    if len(d) == 11 and d[0] in ("7", "8"): d = d[1:]
    if len(d) == 10: return f"+7 {d[0:3]} {d[3:6]}-{d[6:8]}-{d[8:10]}"
    return p_str.strip()

def save_uploaded_file(u_file, c_id, prefix=""):
    if u_file is None: return None
    b = u_file.getvalue()
    file_hash = hashlib.sha256(b).hexdigest()
    for c in st.session_state.crm_store.get("clients", []):
        for f in c.get("client_files", []):
            if f.get("file_hash") == file_hash and file_hash:
                return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
        for t in c.get("tasks", []):
            for f in t.get("task_files", []):
                if f.get("file_hash") == file_hash and file_hash:
                    return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
            for f in t.get("completion_files", []):
                if f.get("file_hash") == file_hash and file_hash:
                    return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
    for d in st.session_state.crm_store.get("deals", []):
        for f in d.get("deal_files", []):
            if f.get("file_hash") == file_hash and file_hash:
                return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
        for f in d.get("close_files", []):
            if f.get("file_hash") == file_hash and file_hash:
                return {"path": f.get("file_path", f.get("path", "")), "name": u_file.name, "file_hash": file_hash}
    name = f"{c_id}_{prefix}_{int(time.time())}_{u_file.name}"
    if YANDEX_TOKEN:
        rp = f"CRM_NE_TROGAT/uploads/{name}"
        if upload_file_to_yandex(b, name):
            return {"path": rp, "name": u_file.name, "file_hash": file_hash}
        st.warning("Не удалось загрузить на Диск, файл сохранён локально")
    os.makedirs("uploads", exist_ok=True)
    lp = f"uploads/{name}"
    with open(lp, "wb") as f: f.write(b)
    return {"path": lp, "name": u_file.name, "file_hash": file_hash}

def save_uploaded_files(files, c_id, prefix=""):
    if files is None: return []
    if not isinstance(files, list): files = [files]
    return [fi for fi in (save_uploaded_file(f, c_id, prefix) for f in files) if fi]

def normalize_file_list(fi_list):
    return [{"file_path": fi["path"], "file_name": fi["name"], "file_hash": fi.get("file_hash", "")} for fi in fi_list]

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
    return ("﻿" + o.getvalue()).encode("utf-8")

def get_client_by_id(c_id):
    for c in st.session_state.crm_store["clients"]:
        if c["id"] == c_id: return c
    return None

def get_deal_by_id(d_id):
    for d in st.session_state.crm_store.get("deals", []):
        if d["id"] == d_id: return d
    return None

def parse_deadline(ds):
    if not ds: return moscow_now().date()
    try: return datetime.strptime(ds, "%Y-%m-%d").date()
    except:
        try: return datetime.strptime(ds, "%Y-%m-%d %H:%M").date()
        except: return moscow_now().date()

def is_task_overdue(task):
    if task.get("done"): return False
    dl = task.get("deadline", "")
    if not dl: return False
    now = moscow_now()
    try:
        if len(dl) == 10: deadline = datetime.strptime(dl, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        elif len(dl) >= 16: deadline = datetime.strptime(dl[:16], "%Y-%m-%d %H:%M")
        else: return False
    except: return False
    return deadline < now

def get_task_sort_date(task):
    dl = task.get("deadline", "")
    try: return datetime.strptime(dl, "%Y-%m-%d").date()
    except:
        try: return datetime.strptime(dl, "%Y-%m-%d %H:%M").date()
        except: return datetime.max.date()

def format_date(ds):
    if not ds: return ""
    try: return datetime.strptime(ds, "%Y-%m-%d").strftime("%d.%m.%Y")
    except:
        try: return datetime.strptime(ds, "%Y-%m-%d %H:%M").strftime("%d.%m.%Y")
        except: return ds

def format_created_date(entity):
    cd = entity.get("created_at") or entity.get("last_modified", "")
    if not cd or cd == "1970-01-01 00:00:00": return ""
    # Resolve author name from created_by login
    author_name = ""
    cb = entity.get("created_by", "")
    if cb:
        u = get_user_by_login(cb)
        if u: author_name = u.get("name", u.get("login", cb))
        else: author_name = cb
    author_part = f" | Автор: {author_name}" if author_name else ""
    try:
        dt = datetime.strptime(cd[:19], "%Y-%m-%d %H:%M:%S")
        return f'<div class="created-date">Создано: {dt.strftime("%d.%m.%Y %H:%M")}{author_part}</div>'
    except:
        try:
            dt = datetime.strptime(cd[:10], "%Y-%m-%d")
            return f'<div class="created-date">Создано: {dt.strftime("%d.%m.%Y")}{author_part}</div>'
        except: return ""

def get_managers_list():
    return [u.get("name", u["login"]) for u in st.session_state.crm_store.get("users", []) if u.get("role") != "admin"]

def render_copy_button(text, btn_id, label="\U0001F4CB Копировать"):
    safe_text = text.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
    st.markdown(f'<button class="copy-btn-crm" id="{btn_id}" onclick="window.crmCopy(\'{safe_text}\',\'{btn_id}\')">{label}</button>', unsafe_allow_html=True)

def render_scroll_restore(key):
    st.components.v1.html(f"""<script>(function(){{var k='crm_scroll_'+window.location.pathname;try{{var s=window.parent.sessionStorage.getItem(k);if(s){{window.parent.scrollTo(0,parseInt(s));window.parent.sessionStorage.removeItem(k);}}}}catch(e){{}}}})();</script>""", height=0)

def save_scroll_and_rerun(key=None):
    st.components.v1.html("""<script>(function(){try{window.parent.sessionStorage.setItem('crm_scroll_'+window.parent.location.pathname,window.parent.scrollY);}catch(e){}})();</script>""", height=0)
    st.rerun()

def render_phone_inline(phone, uid):
    cph = re.sub(r"\D", "", phone)
    if cph.startswith("8") and len(cph) == 11: cph = "7" + cph[1:]
    elif not cph: cph = "79990000000"
    btn_id = f"ph_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f'<div class="phone-action-group" style="padding:4px 0;"><span style="font-size:1rem;font-weight:600;color:#2C3E50;">{phone}</span><button onclick="window.crmCopy(\'{phone}\',\'{btn_id}\')" class="phone-btn" id="{btn_id}" title="Скопировать">\U0001F4CB</button><a href="tel:+{cph}" class="phone-btn" title="Позвонить">\U0001F4DE</a></div>', unsafe_allow_html=True)

def render_extra_phone_inline(phone, name, role, uid):
    cph = re.sub(r"\D", "", phone)
    if cph.startswith("8") and len(cph) == 11: cph = "7" + cph[1:]
    elif not cph: cph = "79990000000"
    info = f"{phone} — {name} ({role})" if name else phone
    btn_id = f"ep_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f'<div class="phone-action-group" style="padding:4px 0;flex-wrap:wrap;gap:8px;white-space:normal;"><span style="font-size:0.9rem;color:#3C4A5A;flex:1 1 auto;min-width:0;word-break:break-word;">{info}</span><button onclick="window.crmCopy(\'{phone}\',\'{btn_id}\')" class="phone-btn" id="{btn_id}" title="Скопировать">\U0001F4CB</button><a href="tel:+{cph}" class="phone-btn" title="Позвонить">\U0001F4DE</a></div>', unsafe_allow_html=True)

def render_track_inline(track_num, uid):
    btn_id = f"trk_btn_{uid}_{secrets.token_hex(4)}"
    st.markdown(f'<div style="display:flex;align-items:center;gap:8px;"><code>{track_num}</code><button onclick="window.crmCopy(\'{track_num}\',\'{btn_id}\')" class="track-copy-btn" id="{btn_id}" title="Копировать">⎘</button></div>', unsafe_allow_html=True)

def get_file_bytes(fp):
    if fp and not fp.startswith("CRM_NE_TROGAT") and os.path.exists(fp):
        try:
            with open(fp, "rb") as f: return f.read()
        except: return None
    rp = normalize_remote_path(fp)
    return download_file_from_yandex(rp) if rp else None


@st.cache_data(ttl=300, show_spinner=False)
def get_thumbnail_base64(remote_path, size=220):
    """Скачивает файл и возвращает data-URI миниатюры для изображений, None для остальных."""
    fb = get_file_bytes(remote_path)
    if not fb:
        return None
    ext = os.path.splitext(remote_path)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
        return None
    try:
        img = PILImage.open(io.BytesIO(fb))
        img.thumbnail((size, size))
        buf = io.BytesIO()
        if img.mode == "RGBA":
            img.save(buf, format="PNG", optimize=True)
            mime = "image/png"
        else:
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(buf, format="JPEG", quality=80)
            mime = "image/jpeg"
        return f"data:{mime};base64,{base64.b64encode(buf.getvalue()).decode()}"
    except:
        mt = f"image/{'jpeg' if ext == '.jpg' else ext[1:]}"
        return f"data:{mt};base64,{base64.b64encode(fb).decode()}"


def render_file_thumbs(files, prefix, allow_delete=False, show_desc=True):
    """Отображает вложения компактным списком: один файл — одна горизонтальная строка."""
    if not files:
        st.caption("Файлов нет")
        return

    st.markdown("""<style>
    .crm-file-row-icon { width:32px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:9px;background:#F1F4F8;color:#526174;font-size:17px;margin:2px auto; }
    .crm-file-row-name { font-size:.88rem;font-weight:600;color:#253246;overflow-wrap:anywhere;padding:7px 0;line-height:1.25; }
    div[class*="st-key-dl_"] button { min-height:34px!important;height:34px!important;width:38px!important;min-width:38px!important;padding:0!important;border-radius:10px!important;border:1px solid #D7DFEA!important;background:linear-gradient(180deg,#FFFFFF 0%,#F2F5FA 100%)!important;color:#31577D!important;font-size:17px!important;font-weight:700!important;box-shadow:0 1px 3px rgba(30,50,75,.08)!important;transition:all .15s ease!important; }
    div[class*="st-key-dl_"] button:hover { background:#E7F0FA!important;border-color:#A9C3DF!important;transform:translateY(-1px);box-shadow:0 3px 8px rgba(30,50,75,.12)!important; }
    div[class*="st-key-del_"] button { min-height:32px!important;height:32px!important;padding:0 8px!important;border-radius:9px!important;font-size:15px!important; }
    div[class*="st-key-fdesc_"] input { min-height:34px!important;height:34px!important;padding:7px 10px!important;font-size:.8rem!important;line-height:1.2!important;border-radius:9px!important; }
    div[class*="st-key-fdesc_"] div[data-testid="InputInstructions"] { display:none!important; }
    </style>""", unsafe_allow_html=True)

    # Все файлы выводятся сразу, без сетки миниатюр и без пагинации.
    file_paths = [ff.get("file_path", ff.get("path")) for ff in files]
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(file_paths)))) as executor:
        file_bytes_list = list(executor.map(get_file_bytes, file_paths))

    for i, (ff, fb) in enumerate(zip(files, file_bytes_list)):
        fp = ff.get("file_path", ff.get("path"))
        fn = ff.get("file_name", ff.get("name", "файл"))
        ext = os.path.splitext(str(fn))[1].lower()
        icons = {
            ".pdf": "📕", ".doc": "📘", ".docx": "📘", ".rtf": "📘",
            ".xls": "📗", ".xlsx": "📗", ".csv": "📗",
            ".ppt": "📙", ".pptx": "📙",
            ".png": "🖼️", ".jpg": "🖼️", ".jpeg": "🖼️", ".gif": "🖼️", ".webp": "🖼️",
            ".zip": "🗜️", ".rar": "🗜️", ".7z": "🗜️", ".txt": "📄", ".log": "📄",
        }
        icon = icons.get(ext, "📎")
        is_admin_delete = allow_delete and st.session_state.get("user_role") == "admin"
        if show_desc:
            cols = st.columns([0.055, 0.34, 0.37, 0.13, 0.075], gap="small", vertical_alignment="center")
        elif is_admin_delete:
            cols = st.columns([0.06, 0.72, 0.14, 0.08], gap="small", vertical_alignment="center")
        else:
            cols = st.columns([0.06, 0.78, 0.16], gap="small", vertical_alignment="center")

        with cols[0]:
            st.markdown(f'<div class="crm-file-row-icon" title="{html.escape(ext or "Файл", quote=True)}">{icon}</div>', unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f'<div class="crm-file-row-name">{html.escape(str(fn))}</div>', unsafe_allow_html=True)

        if show_desc:
            with cols[2]:
                desc_key = f"fdesc_{prefix}_{i}"
                cur_desc = ff.get("description", "") or ""
                new_desc = st.text_input("Описание файла", value=cur_desc, key=desc_key,
                                         max_chars=200, label_visibility="collapsed",
                                         placeholder="Описание файла…")
                if new_desc != cur_desc:
                    ff["description"] = new_desc
                    if hasattr(st.session_state, "crm_store"):
                        save_data(st.session_state.crm_store)
            dl_col, del_col = 3, 4
        elif is_admin_delete:
            dl_col, del_col = 2, 3
        else:
            dl_col, del_col = 2, None

        with cols[dl_col]:
            if fb is not None:
                st.download_button(label="⬇", help=f"Скачать {fn}", data=fb,
                                   file_name=fn, key=f"dl_{prefix}_{i}",
                                   use_container_width=True)
            else:
                st.caption("Недоступен")

        if is_admin_delete:
            with cols[del_col]:
                if st.button("🗑", key=f"del_{prefix}_{i}", help=f"Удалить {fn}"):
                    files.pop(i)
                    commit_and_rerun(st.session_state.crm_store, "Файл удалён")

        st.markdown('<div style="border-bottom:1px solid #EDF0F4;margin:1px 0 5px 0;"></div>', unsafe_allow_html=True)


def build_print_html(task, cl, tp, fd):
    def esc(s): return str(s if s else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    products_html = esc(task.get('products', '')).replace('\n', '<br>')
    oav = task.get('order_amount', 0)
    cost_html = f"<div style='margin-top:6px;font-size:16px;font-weight:bold;'>Сумма: {oav:,.0f} руб.</div>".replace(",", " ") if oav and oav > 0 else ""
    file_reminder = "<div style='color:#D65757;font-weight:bold;margin:14px 0;border:2px solid #D65757;padding:8px;border-radius:8px;'>&#9888; Не забудь распечатать вложенные файлы!</div>" if task.get("task_files") else ""
    lb = get_logo_base64()
    logo_html = f"<img src='data:image/png;base64,{lb}' width='180' style='float:left;margin-right:20px;'/>" if lb else "<div style='font-size:24px;font-weight:bold;float:left;margin-right:20px;'>АЙПЛИНТ</div>"
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><title>Бланк задачи</title><style>body {{ font-family: Arial, sans-serif; margin: 40px; color: #222; }} .header {{ text-align: center; border-bottom: 2px solid #333; padding: 10px; }} .row {{ margin: 8px 0; }} hr {{ border: none; border-top: 1px solid #ccc; margin: 14px 0; }} .sig {{ margin-top: 30px; }} .sig p {{ margin: 12px 0; }}</style></head><body><div>{logo_html}</div><div class="header"><h2>БЛАНК ЗАДАЧИ</h2><p>{moscow_now().strftime('%d.%m.%Y')}</p></div><div class="row"><b>Задача:</b> №{esc(task.get('task_number', ''))}</div><div class="row"><b>Клиент:</b> {esc(cl['name'])} ({esc(cl['phone'])})</div><div class="row"><b>Тип:</b> {esc(tp)}</div><div class="row"><b>Тема:</b> {esc(task.get('text', ''))}</div><div class="row"><b>Срок:</b> {esc(fd)}</div><div class="row"><b>Ответственный:</b> {esc(task.get('manager', ''))}</div><hr><div class="row"><b>Товары:</b><br>{products_html}</div><div class="row"><b>Адрес:</b> {esc(task.get('ship_addr', ''))}</div><div class="row"><b>Получатель:</b> {esc(task.get('receiver', ''))} ({esc(task.get('receiver_phone', ''))})</div><div class="row"><b>Оплата:</b> {esc(task.get('ship_pay', ''))}</div><div class="row"><b>Трек:</b> {esc(task.get('tk_num', ''))}</div>{cost_html}{file_reminder}<div class="sig"><p>Отпустил: _____________</p><p>Получил: _____________</p></div></body></html>"""

def render_print_button(task, cl, tp, fd, key_suffix):
    html_content = build_print_html(task, cl, tp, fd)
    html_json = json.dumps(html_content).replace('<', '\\u003c')
    safe_key = key_suffix.replace('-', '_').replace('.', '_')
    btn_id = f"print_btn_{safe_key}"
    st.markdown(f'<button class="custom-print-btn" id="{btn_id}" style="width:auto;padding:4px 12px;font-size:0.85rem;">\U0001F5A8\uFE0F</button>', unsafe_allow_html=True)
    st.components.v1.html(f"""<script>(function() {{ var btn = window.parent.document.getElementById('{btn_id}'); if (!btn) return; var html = {html_json}; btn.addEventListener('click', function() {{ var w = window.open('', '_blank'); if (!w) {{ alert('Разрешите всплывающие окна'); return; }} w.document.open(); w.document.write(html); w.document.close(); w.focus(); setTimeout(function() {{ try {{ w.print(); }} catch(e) {{}} }}, 500); w.onafterprint = function() {{ setTimeout(function() {{ w.close(); }}, 300); }}; }}); }})();</script>""", height=0)

def render_print_file_button(files, key_suffix):
    if not files: return
    printable = [f for f in files if os.path.splitext(f.get("file_name", f.get("name", "")))[1].lower() in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf"]]
    for i, ff in enumerate(printable):
        fp = ff.get("file_path", ff.get("path"))
        fn = ff.get("file_name", ff.get("name", "файл"))
        fb = get_file_bytes(fp)
        if fb:
            ext = os.path.splitext(fn)[1].lower()
            btn_id = f"printfile_{key_suffix}_{i}"
            b64 = base64.b64encode(fb).decode()
            if ext == ".pdf":
                st.markdown(f'<button class="custom-print-btn" id="{btn_id}" style="background:#5A6B7D;margin-top:4px;">\U0001F5A8️ {fn}</button>', unsafe_allow_html=True)
                st.components.v1.html(f"""<script>(function(){{var b=window.parent.document.getElementById('{btn_id}');if(!b)return;b.addEventListener('click',function(){{var w=window.open('','_blank');if(!w)return;w.document.open();w.document.write('<html><head><title>{fn}</title></head><body style="margin:0"><iframe src="data:application/pdf;base64,{b64}" style="width:100vw;height:100vh;border:0" onload="setTimeout(function(){{try{{window.print()}}catch(e){{}}}},300)"></iframe></body></html>');w.document.close();}});}})();</script>""", height=0)
            else:
                mt = f"image/{'jpeg' if ext == '.jpg' else ext[1:]}"
                st.markdown(f'<button class="custom-print-btn" id="{btn_id}" style="background:#5A6B7D;margin-top:4px;">\U0001F5A8️ {fn}</button>', unsafe_allow_html=True)
                st.components.v1.html(f"""<script>(function(){{var b=window.parent.document.getElementById('{btn_id}');if(!b)return;b.addEventListener('click',function(){{var w=window.open('','_blank');if(!w)return;w.document.open();w.document.write('<html><head><title>{fn}</title></head><body style="margin:0;text-align:center"><img src="data:{mt};base64,{b64}" style="max-width:100%;max-height:100%" onload="setTimeout(function(){{try{{window.print()}}catch(e){{}}}},300)"/></body></html>');w.document.close();}});}})();</script>""", height=0)


def linkify_text(text):
    """Safely render plain URLs, Markdown links and links copied from HTML."""
    if not text:
        return text
    import html as _html

    raw = str(text)
    raw = re.sub(r'\\([<>_:])', r'\1', raw)

    # Use visible anchor text, not its potentially malformed href attribute.
    raw = re.sub(r'<\s*a\b[^>]*>(.*?)<\s*/\s*a\s*>', lambda m: m.group(1), raw,
                 flags=re.IGNORECASE | re.DOTALL)
    raw = re.sub(r'<\s*/?\s*a\b[^>]*>', '', raw, flags=re.IGNORECASE | re.DOTALL)

    # Repair URL split into Markdown fragments by some messengers/editors.
    split_url = r'\[https?://www\]\(https?://www/?\)\.\[([^\]]+)\]\(https?://[^)\s]+\)'
    raw = re.sub(
        split_url,
        lambda m: 'https://www.' + re.sub(r'^https?://(?:www\.)?', '', m.group(1), flags=re.IGNORECASE),
        raw, flags=re.IGNORECASE
    )
    # Repair another copied form: https://[www.example.com/path](https://example.com/path)
    raw = re.sub(r'https?://\[([^\]]+)\]\((https?://[^)\s]+)\)', r'[\1](\2)', raw, flags=re.IGNORECASE)
    raw = re.sub(r'\\:', ':', raw)

    # Turn links into placeholders first. This prevents matching domains inside
    # already-generated HTML anchors and avoids nested <a> elements.
    links = []
    def save_link(label, url):
        token = f'CRM_LINK_TOKEN_{len(links)}_END'
        links.append((token, label, url))
        return token

    def markdown_link(m):
        label, url = m.group(1).strip(), m.group(2).strip()
        return save_link(label, url)

    raw = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', markdown_link, raw, flags=re.IGNORECASE)

    def plain_url(m):
        url = m.group(0).rstrip('.,;:!?)]}')
        suffix = m.group(0)[len(url):]
        token = save_link(url, url)
        return token + suffix

    raw = re.sub(r'https?://[^\s<>"\']+', plain_url, raw, flags=re.IGNORECASE)

    def bare_domain(m):
        value = m.group(0).rstrip('.,;:!?)]}')
        suffix = m.group(0)[len(value):]
        token = save_link(value, 'https://' + value)
        return token + suffix

    raw = re.sub(r'(?<![=\"/\.])\b(?:www\.)?[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}(?:/[^\s<>\"\']*)?',
                 bare_domain, raw, flags=re.IGNORECASE)
    safe = _html.escape(raw)
    for token, label, url in links:
        safe_anchor = (
            f'<a href="{_html.escape(url, quote=True)}" target="_blank" '
            f'rel="noopener noreferrer" style="color:#bc1661;text-decoration:underline;">'
            f'{_html.escape(label)}</a>'
        )
        safe = safe.replace(_html.escape(token), safe_anchor)
    return safe


def render_entity_chat(entity, entity_type, entity_id):
    chat_key = f"{entity_type}_chat"
    if chat_key not in entity: entity[chat_key] = []
    chat = entity[chat_key]
    st.markdown("**Чат:**")
    chat_container = st.container(height=200)
    with chat_container:
        for msg in chat[-50:]:
            is_me = msg.get("user") == st.session_state.get("user_name", "")
            cls = "chat-msg-me" if is_me else "chat-msg-other"
            st.markdown(f'<div class="chat-msg {cls}"><div style="font-size:0.75rem;opacity:0.7;margin-bottom:2px;">{msg.get("user","")} — {msg.get("time","")}</div>{linkify_text(msg.get("text",""))}</div>', unsafe_allow_html=True)
        if not chat: st.caption("Сообщений нет")
    clr_key = f"clr_{entity_type}_{entity_id}"
    if st.session_state.get(clr_key):
        st.session_state[f"{entity_type}_msg_{entity_id}"] = ""
        st.session_state[clr_key] = False
    msg_text = st.text_area("Сообщение:", key=f"{entity_type}_msg_{entity_id}", placeholder="Введите сообщение...", label_visibility="collapsed", height=68)
    _send_spacer, _send_col, _send_spacer2 = st.columns([1, 2, 1])
    with _send_col:
      _send_clicked = st.button("Отправить", key=f"{entity_type}_send_{entity_id}", use_container_width=True)
    if _send_clicked:
        if msg_text.strip():
            chat.append({"user": st.session_state.get("user_name", ""), "text": msg_text.strip(), "time": moscow_now().strftime("%d.%m.%Y %H:%M")})
            st.session_state[clr_key] = True
            entity["last_modified"] = now_str()
            commit_and_rerun(st.session_state.crm_store)
        else: st.warning("Введите текст")

# Единый диспетчер всплывающих окон CRM.
# Все диалоги используют один и тот же dialog-host, чтобы при переключении
# менялось содержимое одного окна, а не закрывался один диалог и создавался другой.
_CRM_DIALOG_REGISTRY = {}

def _crm_dialog_signature_value(value):
    if isinstance(value, dict):
        return ("dict", value.get("id"), value.get("task_number"), value.get("client_id"),
                value.get("deal_id"), value.get("name"), value.get("login"))
    if isinstance(value, (str, int, float, bool, type(None))):
        return (type(value).__name__, value)
    if isinstance(value, (list, tuple)):
        return (type(value).__name__, tuple(_crm_dialog_signature_value(x) for x in value))
    return (type(value).__name__, repr(value)[:100])

def _crm_dialog(title, width="large"):
    def _decorate(func):
        _CRM_DIALOG_REGISTRY[func.__name__] = {"func": func, "title": title, "width": width}
        def _request_dialog(*args, **kwargs):
            st.session_state["_crm_dialog_requested_this_run"] = True
            signature = (_crm_dialog_signature_value(args), _crm_dialog_signature_value(kwargs))
            current = st.session_state.get("_crm_active_dialog") or {}
            # Сохраняем новые аргументы даже для уже открытого диалога, чтобы использовать
            # актуальные записи из crm_store после сохранения/обновления.
            st.session_state["_crm_active_dialog"] = {
                "name": func.__name__, "title": title, "width": width,
                "args": args, "kwargs": kwargs, "signature": signature,
            }
            # При переключении из одного диалога в другой мы уже находимся
            # внутри dialog-fragment Streamlit. Перерисовываем только его,
            # не перезапуская всю страницу CRM и списки активной вкладки.
            if st.session_state.get("_crm_inside_dialog_host", False):
                try:
                    st.rerun(scope="fragment")
                except TypeError:
                    # Совместимость со старыми версиями Streamlit.
                    st.rerun()
            return None
        _request_dialog.__name__ = func.__name__
        _request_dialog.__doc__ = func.__doc__
        return _request_dialog
    return _decorate

@_crm_dialog("Создать напоминание", width="medium")
def create_reminder_dialog(entity_type, entity_id, entity_label):
    store = st.session_state.crm_store
    users = [u for u in store.get("users", []) if u.get("login") and u.get("role") != "admin" and u.get("login") != "admin"]
    key_suffix = f"{entity_type}_{entity_id}"
    text_key = f"rem_text_{key_suffix}"
    date_key = f"rem_date_{key_suffix}"
    time_key = f"rem_time_{key_suffix}"
    recipient_key = f"rem_recipient_{key_suffix}"
    warning_key = f"rem_close_warning_{key_suffix}"

    if not users:
        st.error("В CRM нет пользователей, которым можно назначить напоминание.")
        return

    # Единое оформление для окна создания напоминания независимо от того,
    # из какой карточки CRM оно открыто. Селекторы намеренно глобальные внутри
    # Streamlit dialog, чтобы CSS родительских карточек не менял вид элементов.
    close_css_key = f"rem_close_row_{key_suffix}"
    st.markdown("""<style>
    /* Кнопка закрытия — единый стиль для всех контекстов */
    [data-testid="stDialog"] [class*="st-key-rem_close_row_"] {
        position:relative!important;z-index:10000!important;width:100%!important;
        margin:0!important;padding:0!important;
    }
    [data-testid="stDialog"] [class*="st-key-rem_close_row_"] [data-testid="stHorizontalBlock"] {
        justify-content:flex-end!important;gap:0!important;
    }
    [data-testid="stDialog"] [class*="st-key-rem_close_row_"] [data-testid="column"]:first-child {
        display:none!important;
    }
    [data-testid="stDialog"] [class*="st-key-rem_close_row_"] [data-testid="column"]:last-child {
        flex:0 0 36px!important;width:36px!important;min-width:36px!important;
    }
    [data-testid="stDialog"] [class*="st-key-rem_close_row_"] .stButton > button {
        width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;
        padding:0!important;font-size:1.2rem!important;line-height:1!important;
        background:#FFFFFF!important;border:1px solid #DCE0E5!important;
        border-radius:8px!important;color:#5A6B7D!important;display:flex!important;
        align-items:center!important;justify-content:center!important;margin:0!important;
    }
    [data-testid="stDialog"] [class*="st-key-rem_close_row_"] .stButton > button:hover {
        background:#EEF0F3!important;border-color:#C9CFD7!important;
    }

    /* Предупреждение о несохранённых изменениях — единый стиль */
    [data-testid="stDialog"] [class*="st-key-rem_unsaved_warn_"] {
        border:2px solid #FF9800!important;border-radius:10px!important;
        background:#FFF8E1!important;padding:0.65rem 0.8rem!important;
        margin:0.35rem 0 0.65rem!important;
    }
    [data-testid="stDialog"] [class*="st-key-rem_unsaved_warn_"] [data-testid="stMarkdownContainer"] p {
        color:#5D4037!important;font-size:0.88rem!important;line-height:1.6!important;
        margin:0.15rem 0 0.45rem!important;
    }
    [data-testid="stDialog"] [class*="st-key-rem_unsaved_warn_"] [data-testid="stHorizontalBlock"] {
        gap:0.5rem!important;align-items:center!important;
    }
    [data-testid="stDialog"] [class*="st-key-rem_unsaved_warn_"] .stButton > button {
        width:100%!important;min-height:36px!important;padding:0.4rem 0.6rem!important;
        border-radius:8px!important;font-size:0.82rem!important;font-weight:600!important;
        white-space:normal!important;line-height:1.25!important;
    }
    [data-testid="stDialog"] [class*="st-key-rem_unsaved_warn_"] .stButton > button[kind="primary"] {
        background:#bc1661!important;color:#FFFFFF!important;border:1px solid #bc1661!important;
    }
    [data-testid="stDialog"] [class*="st-key-rem_unsaved_warn_"] .stButton > button[kind="secondary"] {
        background:#FFFFFF!important;color:#5A6B7D!important;border:1px solid #DCE0E5!important;
    }
    </style>""", unsafe_allow_html=True)
    with st.container(key=close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("✕", key=f"rem_close_btn_{key_suffix}", use_container_width=True):
                _has_unsaved = bool(
                    str(st.session_state.get(text_key, "") or "").strip()
                    or st.session_state.get(date_key) is not None
                    or st.session_state.get(time_key) is not None
                    or st.session_state.get(recipient_key) not in (None, "")
                )
                if _has_unsaved and not st.session_state.get(warning_key, False):
                    st.session_state[warning_key] = True
                    st.rerun()
                else:
                    st.session_state.pop("_pending_reminder_dialog", None)
                    st.session_state.pop(warning_key, None)
                    for _k in (text_key, date_key, time_key, recipient_key):
                        st.session_state.pop(_k, None)
                    st.rerun()

    if st.session_state.get(warning_key):
        warn_container_key = f"rem_unsaved_warn_{key_suffix}"
        with st.container(key=warn_container_key):
            st.markdown("**⚠️ Есть несохранённые изменения**")
            st.markdown("Сохранить перед закрытием?")
            _w1, _w2 = st.columns(2)
            with _w1:
                if st.button("Без сохр.", key=f"rem_discard_{key_suffix}", use_container_width=True):
                    st.session_state.pop("_pending_reminder_dialog", None)
                    st.session_state.pop(warning_key, None)
                    for _k in (text_key, date_key, time_key, recipient_key):
                        st.session_state.pop(_k, None)
                    st.rerun()
            with _w2:
                if st.button("Продолжить редактирование", key=f"rem_continue_{key_suffix}", use_container_width=True):
                    st.session_state.pop(warning_key, None)
                    st.rerun()

    logins = [u["login"] for u in users]
    names = {u["login"]: u.get("name") or u["login"] for u in users}
    st.text_area("О чём напомнить?", key=text_key, height=68, label_visibility="visible")
    c1, c2 = st.columns(2)
    with c1:
        due_date = st.date_input("Дата", value=None, format="DD.MM.YYYY", key=date_key, help=None)
        st.caption("Выберите дату: день, месяц и год")
    with c2:
        due_time = st.time_input("Время", value=moscow_now().time().replace(second=0, microsecond=0), key=time_key, help=None)
        st.caption("Выберите часы и минуты")
    recipient_options = [""] + logins
    recipient = st.selectbox("Получатель", recipient_options, index=0,
        format_func=lambda x: "Выберите получателя" if not x else names.get(x, x),
        key=recipient_key, placeholder="Выберите получателя")

    if st.button("Создать напоминание", key=f"rem_save_{key_suffix}", type="primary", use_container_width=True):
        errors = []
        text_value = str(st.session_state.get(text_key, "") or "").strip()
        if not text_value:
            errors.append("Введите текст напоминания.")
        if due_date is None:
            errors.append("Выберите дату.")
        if due_time is None:
            errors.append("Выберите время.")
        if not recipient:
            errors.append("Выберите получателя.")
        if errors:
            for error in errors:
                st.warning(error)
        else:
            due = datetime.combine(due_date, due_time).replace(second=0, microsecond=0)
            if due <= moscow_now():
                st.warning("Выберите дату и время в будущем.")
            else:
                store.setdefault("reminders", []).append({"id":uuid.uuid4().hex,"entity_type":str(entity_type),"entity_id":str(entity_id),"entity_label":str(entity_label),"text":text_value,"created_at":now_str(),"created_by":st.session_state.get("user_login", ""),"recipient":recipient,"due_at":due.strftime("%Y-%m-%d %H:%M:%S"),"sent":False,"sent_at":""})
                save_data(store)
                st.session_state.pop("_pending_reminder_dialog", None)
                st.session_state.pop(warning_key, None)
                for _k in (text_key, date_key, time_key, recipient_key):
                    st.session_state.pop(_k, None)
                st.toast("Напоминание создано", icon="🔔")
                st.rerun()


def render_reminders(entity_type, entity_id, entity_label, key_prefix):
    store = st.session_state.crm_store
    store.setdefault("reminders", [])
    st.markdown("---")
    st.markdown("**Напоминания**")
    items = [r for r in store["reminders"] if r.get("entity_type")==str(entity_type) and str(r.get("entity_id"))==str(entity_id)]
    items.sort(key=lambda r:r.get("due_at", ""))
    now = moscow_now()
    users = {u.get("login"):u for u in store.get("users", [])}
    if not items:
        st.caption("Напоминаний пока нет")
    for r in items:
        due_raw = r.get("due_at", "")
        try: past = datetime.strptime(due_raw[:19], "%Y-%m-%d %H:%M:%S") <= now
        except Exception: past = False
        try: due_label = datetime.strptime(due_raw[:19], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
        except Exception: due_label = due_raw
        rec = users.get(r.get("recipient"), {})
        txt = html.escape(str(r.get("text", ""))).replace("\n", "<br>")
        text_style = "text-decoration:line-through;color:#7F8C9A;" if past else ""
        with st.container(border=True):
            st.markdown(format_created_date(r), unsafe_allow_html=True)
            _msg_col, _del_col = st.columns([12, 1], gap="small", vertical_alignment="top")
            with _msg_col:
                st.markdown(f"<div class='chat-msg chat-msg-other' style='margin:0 0 2px 0;max-width:100%;{text_style}overflow-wrap:anywhere'>{txt}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:0.75rem;opacity:0.7;margin:6px 0 4px 0;'>Срок: {html.escape(due_label)} · Получатель: {html.escape(str(rec.get('name') or r.get('recipient','—')))}</div>", unsafe_allow_html=True)
            with _del_col:
                if st.button("🗑", key=f"rem_del_{r.get('id')}", help="Удалить напоминание"):
                    st.session_state[f"rem_confirm_del_{r.get('id')}"] = True
            del_key = f"rem_confirm_del_{r.get('id')}"
            if st.session_state.get(del_key):
                st.warning("Удалить это напоминание?")
                yes, no = st.columns(2)
                with yes:
                    if st.button("Удалить", key=f"rem_del_yes_{r.get('id')}", type="primary", use_container_width=True):
                        store["reminders"] = [x for x in store["reminders"] if x.get("id") != r.get("id")]
                        st.session_state.pop(del_key, None)
                        save_data(store)
                        st.rerun()
                with no:
                    if st.button("Отмена", key=f"rem_del_no_{r.get('id')}", use_container_width=True):
                        st.session_state.pop(del_key, None)
                        st.rerun()
    _send_spacer, _send_col, _send_spacer2 = st.columns([1, 2, 1])
    with _send_col:
        if st.button("Создать напоминание", key=f"rem_add_{key_prefix}", use_container_width=True):
            st.session_state["_pending_reminder_dialog"] = {"entity_type": str(entity_type), "entity_id": str(entity_id), "entity_label": str(entity_label)}
            st.rerun()

def process_due_reminders():
    """Переводит наступившие напоминания в персональные уведомления; вызывается при каждом запуске приложения."""
    store = st.session_state.get("crm_store")
    if not isinstance(store, dict): return
    reminders = store.setdefault("reminders", [])
    now = moscow_now()
    due_items = []
    for r in reminders:
        if r.get("sent") or not r.get("recipient"):
            continue
        try: due = datetime.strptime(r.get("due_at", "")[:19], "%Y-%m-%d %H:%M:%S")
        except Exception: continue
        if due <= now:
            r["sent"] = True
            r["sent_at"] = now_str()
            due_items.append(r)
    if not due_items: return
    store.setdefault("notifications", [])
    users = {u.get("login"):u for u in store.get("users", [])}
    for r in due_items:
        body = f"Напоминание: {r.get('text','')}\nОбъект: {r.get('entity_label','')}"
        store["notifications"].append({"id":uuid.uuid4().hex,"to":r["recipient"],"text":body,"date":now_str(),"read":False,"reminder_id":r.get("id")})
    # Persist sent flags before external delivery to minimize duplicate Telegram sends on reruns.
    save_data(store)
    for r in due_items:
        u = users.get(r.get("recipient"), {})
        if u.get("telegram_chat_id"):
            send_telegram(u["telegram_chat_id"], f"🔔 <b>Напоминание</b>\n{html.escape(str(r.get('text','')))}\nОбъект: {html.escape(str(r.get('entity_label','')))}")

def _save_task_shipping_widget_value(task_id, client_id, deal_id, key_prefix, field):
    """Persist shipping widgets from their callbacks, before the dialog is rendered again.

    Saving from the middle of render_task_detail used to replace crm_store with a deep
    copy while the rest of that same render still held references to the old objects.
    Subsequent action buttons could then mutate stale task/client objects.
    """
    store = st.session_state.get("crm_store", {})
    client = next((c for c in store.get("clients", []) if str(c.get("id")) == str(client_id)), None)
    if not client:
        return
    task = next((t for t in client.get("tasks", []) if str(t.get("id")) == str(task_id)), None)
    if task is None:
        return

    if field == "status":
        value = st.session_state.get(f"task_shipping_status_{key_prefix}", "") or ""
        task["shipping_status"] = value
    elif field == "date":
        value = st.session_state.get(f"task_estimated_ship_date_{key_prefix}")
        task["estimated_ship_date"] = value.isoformat() if value else ""

    now = now_str()
    task["last_modified"] = now
    client["last_modified"] = now
    if deal_id:
        for deal in client.get("deals", []):
            if str(deal.get("id")) == str(deal_id):
                deal["last_modified"] = now
                break
    save_data(store)


def _render_task_shipping_fields(task, client, deal, key_prefix):
    """Shipping status/date are saved by callbacks, without invalidating live dialog references."""
    statuses = ["Собирается", "Закупается материал", "Готово к отправке"]
    status_key = f"task_shipping_status_{key_prefix}"
    date_key = f"task_estimated_ship_date_{key_prefix}"
    current_status = task.get("shipping_status", "") or ""
    current_date_raw = task.get("estimated_ship_date", "") or ""
    try:
        current_date = datetime.strptime(str(current_date_raw)[:10], "%Y-%m-%d").date() if current_date_raw else None
    except (TypeError, ValueError):
        current_date = None

    # Seed widget state only when it has not yet been initialized. This prevents
    # rerenders from resetting a user's selection back to the stored value.
    if status_key not in st.session_state:
        st.session_state[status_key] = current_status if current_status in statuses else None
    if date_key not in st.session_state:
        st.session_state[date_key] = current_date

    st.selectbox(
        "Статус",
        options=statuses,
        index=None,
        placeholder="Выберите статус",
        key=status_key,
        on_change=_save_task_shipping_widget_value,
        args=(task.get("id"), client.get("id"), deal.get("id") if deal else None, key_prefix, "status"),
    )
    st.date_input(
        "Ориентировочная дата отправки",
        format="DD.MM.YYYY",
        key=date_key,
        on_change=_save_task_shipping_widget_value,
        args=(task.get("id"), client.get("id"), deal.get("id") if deal else None, key_prefix, "date"),
    )

def render_task_detail(t, cl, d, key_prefix, show_shipping_status=False):
    with st.container(border=True, key=f"task_detail_{key_prefix}"):
        st.markdown(f'<style>.st-key-task_detail_{key_prefix} {{ padding: 0.5rem !important; }} .st-key-task_detail_{key_prefix} .stVerticalBlock {{ gap: 0.15rem !important; }}</style>', unsafe_allow_html=True)
        # CSS to align print and edit buttons
        st.markdown(f"""<style>
        .st-key-task_detail_{key_prefix} .stHorizontalBlock .stButton button,
        .st-key-task_detail_{key_prefix} .stHorizontalBlock .stMarkdown button {{
            min-height: 32px !important;
            padding: 4px 10px !important;
            font-size: 0.85rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        .st-key-task_detail_{key_prefix} .stHorizontalBlock .stMarkdown {{
            margin-top: 0 !important;
            display: flex !important;
            align-items: center !important;
        }}
        /* Remove top gap in right column */
        .st-key-task_detail_{key_prefix} > div > div:nth-child(2) > div > div:first-child {{
            margin-top: 0 !important;
            padding-top: 0 !important;
        }}
        .st-key-task_detail_{key_prefix} > div > div:nth-child(2) {{
            margin-top: 0 !important;
            padding-top: 0 !important;
        }}
        </style>""", unsafe_allow_html=True)
        # Two columns: left = everything, right = comments + files
        show_edit_task = st.session_state.get(f"show_edit_task_{key_prefix}", False)
        left_col, right_col = st.columns(2)
        with left_col:
            _task_header = f"\u0417\u0430\u0434\u0430\u0447\u0430 \u043f\u043e \u0441\u0434\u0435\u043b\u043a\u0435 \u2116{t.get('task_number', '')}" if d else f"\u0417\u0430\u0434\u0430\u0447\u0430 \u2116{t.get('task_number', '')}"
            _tp = t.get('type', '\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f')
            _fd = format_date(t.get('deadline', ''))
            if d:
                _deal_num = d.get('deal_number', d.get('title', ''))
                _deal_id = d.get('id')
                _deal_link_key = f"deal_link_{key_prefix}"
                _hdr_inner, _status_inner = st.columns([3, 2])
                with _hdr_inner:
                    st.subheader(_task_header)
                    if t.get("needs_rework") and not t.get("done"):
                        st.markdown('<p style="color: #D32F2F; font-weight: 700; font-size: 0.9rem; margin: 0.1rem 0;">На доработке</p>', unsafe_allow_html=True)
                    if st.button(f"{_deal_num}", key=_deal_link_key, type="secondary"):
                        # Сохраняем окно задачи, чтобы кнопка закрытия сделки вернула пользователя к задаче.
                        _push_dialog_return()
                        st.session_state.active_tab = "Сделки"
                        st.session_state["dialog_deal_key"] = _deal_id
                        st.session_state.pop("dialog_task_key", None)
                        st.session_state.pop("_open_created_task", None)
                        st.session_state["_in_dialog"] = False
                        st.rerun()
                    st.markdown(format_created_date(t), unsafe_allow_html=True)
                    if not show_edit_task:
                        st.markdown(f"**Тема:** {t.get('text', '')}")
                        st.markdown(f"**Тип:** {t.get('type', 'Связаться')}")
                with _status_inner:
                    if show_shipping_status and _tp in ("Отправить заказ", "Отправить образцы"):
                        _render_task_shipping_fields(t, cl, d, key_prefix)
                    elif not show_shipping_status:
                        render_print_button(t, cl, _tp, _fd, f"td_{key_prefix}")
            else:
                _hdr_inner, _status_inner = st.columns([3, 2])
                with _hdr_inner:
                    st.subheader(_task_header)
                    if t.get("needs_rework") and not t.get("done"):
                        st.markdown('<p style="color: #D32F2F; font-weight: 700; font-size: 0.9rem; margin: 0.1rem 0;">На доработке</p>', unsafe_allow_html=True)
                    # Для задачи, созданной непосредственно по клиенту, ссылка на карточку
                    # клиента расположена и оформлена так же, как ссылка на сделку выше.
                    if cl:
                        _client_link_key = f"task_client_link_{key_prefix}"
                        if st.button(f"{cl.get('name', 'Клиент')}", key=_client_link_key, type="secondary"):
                            _push_dialog_return()
                            st.session_state.active_tab = "Клиенты"
                            st.session_state["dialog_client_key"] = cl.get("id")
                            st.session_state.pop("dialog_task_key", None)
                            st.session_state.pop("_open_created_task", None)
                            st.session_state["_in_dialog"] = False
                            st.rerun()
                    st.markdown(format_created_date(t), unsafe_allow_html=True)
                    if not show_edit_task:
                        st.markdown(f"**Тема:** {t.get('text', '')}")
                        st.markdown(f"**Тип:** {t.get('type', 'Связаться')}")
                with _status_inner:
                    if show_shipping_status and _tp in ("Отправить заказ", "Отправить образцы"):
                        _render_task_shipping_fields(t, cl, d, key_prefix)
                    elif not show_shipping_status:
                        render_print_button(t, cl, _tp, _fd, f"td_{key_prefix}")
            if show_edit_task:
                # Inline editing mode
                et_topic = st.text_input("\u0422\u0435\u043c\u0430:", value=t.get("text", ""), key=f"edit_topic_{key_prefix}")
                et_type = st.selectbox("\u0422\u0438\u043f:", TASK_TYPES, index=TASK_TYPES.index(t.get("type", "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f")) if t.get("type", "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f") in TASK_TYPES else 0, key=f"edit_type_{key_prefix}")
                et_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", get_managers_list(), index=0 if t.get("manager", "") not in get_managers_list() else (get_managers_list()).index(t.get("manager", "")), key=f"edit_mgr_{key_prefix}", placeholder=MGR_PLACEHOLDER)
                et_comment = st.text_area("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438:", value=t.get("task_comment", ""), key=f"edit_comment_{key_prefix}")
                if et_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b"):
                    et_products = st.text_area("\u0422\u043e\u0432\u0430\u0440\u044b:", value=t.get("products", ""), key=f"edit_prod_{key_prefix}")
                    et_addr = st.text_area("\u0410\u0434\u0440\u0435\u0441 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438:", value=t.get("ship_addr", ""), key=f"edit_addr_{key_prefix}")
                    et_recv = st.text_input("\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:", value=t.get("receiver", ""), key=f"edit_recv_{key_prefix}")
                    et_rphone = st.text_input("\u0422\u0435\u043b\u0435\u0444\u043e\u043d \u043f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044f:", value=t.get("receiver_phone", ""), key=f"edit_rphone_{key_prefix}")
                    et_pay = st.selectbox("\u041e\u043f\u043b\u0430\u0442\u0430:", SHIP_PAY_OPTIONS, index=SHIP_PAY_OPTIONS.index(t.get("ship_pay", "")) if t.get("ship_pay", "") in SHIP_PAY_OPTIONS else 0, key=f"edit_pay_{key_prefix}", placeholder="\u0423\u043a\u0430\u0436\u0438 \u043f\u043b\u0430\u0442\u0435\u043b\u044c\u0449\u0438\u043a\u0430")
                    et_amount = st.text_input("\u0421\u0443\u043c\u043c\u0430 \u0437\u0430\u043a\u0430\u0437\u0430 (\u0440\u0443\u0431.):", value=str(t.get("order_amount", 0)) if t.get("order_amount", 0) > 0 else "", key=f"edit_amount_{key_prefix}", placeholder="\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u0443\u043c\u043c\u0443")
                    et_tk = st.text_input("\u0422\u0440\u0435\u043a:", value=t.get("tk_num", ""), key=f"edit_tk_{key_prefix}")
                else:
                    et_products = t.get("products", "")
                    et_addr = t.get("ship_addr", "")
                    et_recv = t.get("receiver", "")
                    et_rphone = t.get("receiver_phone", "")
                    et_pay = t.get("ship_pay", "")
                    et_amount = str(t.get("order_amount", 0)) if t.get("order_amount", 0) > 0 else ""
                    et_tk = t.get("tk_num", "")
                _save_col, _cancel_col = st.columns(2)
                with _save_col:
                    if st.button("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", key=f"edit_save_{key_prefix}", use_container_width=True, type="primary"):
                        if not et_mgr:
                            st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0433\u043e")
                        else:
                            t["text"] = et_topic
                            t["type"] = et_type
                            t["manager"] = et_mgr
                            t["task_comment"] = et_comment
                            t["products"] = et_products
                            t["ship_addr"] = et_addr
                            t["receiver"] = et_recv
                            t["receiver_phone"] = et_rphone
                            t["ship_pay"] = et_pay
                            t["order_amount"] = int(et_amount) if et_amount and et_amount.strip().isdigit() else 0
                            t["tk_num"] = et_tk
                            t["last_modified"] = now_str()
                            cl["last_modified"] = now_str()
                            if d: d["last_modified"] = now_str()
                            st.session_state[f"show_edit_task_{key_prefix}"] = False
                            commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0430")
                with _cancel_col:
                    if st.button("\u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c", key=f"edit_cancel_{key_prefix}", use_container_width=True):
                        st.session_state[f"show_edit_task_{key_prefix}"] = False
                        _smart_rerun()
            else:
                # Display mode: task topic and type are shown directly under the task number above.
                # Deadline: clickable date, no pencil button
                show_edit_dl = st.session_state.get(f"show_edit_dl_{key_prefix}", False)
                if show_edit_dl:
                    ndd = st.date_input("\u0421\u0440\u043e\u043a:", value=parse_deadline(t.get("deadline", "")), format="DD.MM.YYYY", key=f"dl_inline_{key_prefix}")
                    dl_btn_col1, dl_btn_col2 = st.columns(2)
                    with dl_btn_col1:
                        if st.button("\u041e\u043a", key=f"dl_ok_{key_prefix}", use_container_width=True, type="primary"):
                            t["deadline"] = ndd.isoformat()
                            t["last_modified"] = now_str()
                            cl["last_modified"] = now_str()
                            if d: d["last_modified"] = now_str()
                            st.session_state[f"show_edit_dl_{key_prefix}"] = False
                            commit_and_rerun(st.session_state.crm_store, "\u0421\u0440\u043e\u043a \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d")
                    with dl_btn_col2:
                        if st.button("\u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c", key=f"dl_cancel_{key_prefix}", use_container_width=True):
                            st.session_state[f"show_edit_dl_{key_prefix}"] = False
                            _smart_rerun()
                else:
                    dl_btn_key = f"btn_dl_click_{key_prefix}"
                    _dl_color = "#C62828" if is_task_overdue(t) else "#2C3E50"
                    st.markdown(f"<style>.st-key-{dl_btn_key} button {{ background:none!important;border:none!important;color:{_dl_color}!important;font-weight:600!important;font-size:1rem!important;padding:0!important;text-align:left!important; }}</style>", unsafe_allow_html=True)
                    if st.button(f"\u0421\u0440\u043e\u043a: {format_date(t.get('deadline', ''))}", key=dl_btn_key):
                        st.session_state[f"show_edit_dl_{key_prefix}"] = True
                        _smart_rerun()
                # Editable responsible person (replaces delegate button)
                st.markdown("**\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:**")
                mgr_options = get_managers_list()
                current_mgr = t.get("manager", "")
                current_idx = mgr_options.index(current_mgr) if current_mgr in mgr_options else 0
                new_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", mgr_options, index=current_idx, key=f"task_mgr_inline_{key_prefix}", placeholder=MGR_PLACEHOLDER, label_visibility="collapsed")
                if new_mgr != current_mgr and new_mgr:
                    t["manager"] = new_mgr
                    t["delegated_to"] = new_mgr
                    t["in_work"] = False
                    t["done"] = False
                    t["reviewed"] = False
                    t["last_modified"] = now_str()
                    add_notification(new_mgr, f"Вам делегирована задача №{t.get('task_number', '')}: {t.get('text', '')}", f"📌 Вам делегирована задача №{t.get('task_number', '')}: {t.get('text', '')}")
                    cl["last_modified"] = now_str()
                    if d: d["last_modified"] = now_str()
                    commit_and_rerun(st.session_state.crm_store, "\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d")
                st.markdown("---")
                if t.get('products'): st.markdown(f"**\u0422\u043e\u0432\u0430\u0440\u044b:** {t['products']}")
                if t.get('ship_addr'): st.markdown(f"**\u0410\u0434\u0440\u0435\u0441:** {t['ship_addr']}")
                if t.get('receiver'): st.markdown(f"**\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:** {t['receiver']} ({t.get('receiver_phone', '')})")
                if t.get('ship_pay'): st.markdown(f"**\u041e\u043f\u043b\u0430\u0442\u0430:** {t['ship_pay']}")
                if t.get('tk_num'):
                    st.markdown(f"**\u0422\u0440\u0435\u043a:** `{t['tk_num']}`")
                if t.get('order_amount', 0) > 0: st.markdown(f"**\u0421\u0443\u043c\u043c\u0430:** {t['order_amount']:,.0f} \u0440\u0443\u0431.".replace(",", " "))
                if t.get('ready_to_ship'): st.markdown('<span class="ready-badge">\u0413\u043e\u0442\u043e\u0432\u043e \u043a \u043e\u0442\u043f\u0440\u0430\u0432\u043a\u0435</span>', unsafe_allow_html=True)
                if t.get('task_comment'): st.markdown(f"**\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438:** {linkify_text(t['task_comment'])}", unsafe_allow_html=True)
                # Edit pencil button — same compact size, left-aligned, above action buttons
                pencil_key = f"btn_pencil_edit_{key_prefix}"
                st.markdown(f"<style>.st-key-{pencil_key} button {{ padding: 2px 8px !important; font-size: 0.85rem !important; min-height: 32px !important; }}</style>", unsafe_allow_html=True)
                if st.button("\u270e", key=pencil_key):
                    st.session_state[f"show_edit_task_{key_prefix}"] = True
                    _smart_rerun()
                # Action buttons in left column (below task info)
                st.markdown("---")
                tk_done = t.get("done", False)
                if not tk_done:
                    if not t.get("in_work"):
                        if st.button("Взять в работу", key=f"btn_take_work_{key_prefix}", type="primary", use_container_width=True):
                            # Для общей неназначенной задачи ответственным становится тот, кто первым взял её в работу.
                            if not t.get("manager"):
                                t["manager"] = cu
                                t["delegated_to"] = cu
                            t["in_work"] = True
                            t["last_modified"] = now_str()
                            cl["last_modified"] = now_str()
                            if d: d["last_modified"] = now_str()
                            # Сохраняем статус, но оставляем окно задачи открытым.
                            # Так пользователь может продолжить работу с карточкой.
                            save_data(st.session_state.crm_store)
                            st.toast("Задача взята в работу", icon="✅")
                            _smart_rerun()
                    show_key = f"show_complete_{key_prefix}"
                    if st.button("\u0412\u044b\u043f\u043e\u043b\u043d\u0438\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443", key=f"btn_complete_{key_prefix}", type="primary", use_container_width=True):
                        st.session_state["dialog_task_completion"] = {
                            "client_id": cl.get("id"),
                            "task_number": t.get("task_number"),
                            "key_prefix": key_prefix,
                        }
                        st.session_state[show_key] = False
                        _smart_rerun()
                    if st.session_state.get(show_key, False):
                        rt = st.text_area("\u041e\u0442\u0447\u0435\u0442 (\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e):", key=f"rt_{key_prefix}", height=100)
                        uf_ver = st.session_state.get(f"uf_ver_{key_prefix}", 0)
                        uf = st.file_uploader("\u0424\u0430\u0439\u043b\u044b/\u0444\u043e\u0442\u043e \u043e\u0442\u0447\u0435\u0442\u0430:", key=f"uf_{key_prefix}_{uf_ver}", accept_multiple_files=True)
                        create_new_task = st.checkbox("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u043d\u043e\u0432\u0443\u044e \u0437\u0430\u0434\u0430\u0447\u0443 \u043f\u043e \u0441\u0434\u0435\u043b\u043a\u0435", key=f"cnt_{key_prefix}")
                        if create_new_task:
                            with st.container(border=True):
                                nt_topic2 = st.text_input("\u0422\u0435\u043c\u0430:", key=f"cnt_topic_{key_prefix}")
                                nt_mgr2 = st.selectbox("Ответственный:", get_managers_list(), index=None, key=f"cnt_mgr_{key_prefix}", placeholder=MGR_PLACEHOLDER)
                                nt_dl2 = st.date_input("\u0421\u0440\u043e\u043a:", format="DD.MM.YYYY", key=f"cnt_dl_{key_prefix}")
                                nt_comment2 = st.text_area("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:", key=f"cnt_comment_{key_prefix}", height=90)
                                nt_files2 = st.file_uploader("\u0424\u0430\u0439\u043b\u044b:", key=f"cnt_files_{key_prefix}", accept_multiple_files=True)
                        pc1, pc2 = st.columns(2)
                        with pc1:
                            if st.button("\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c", key=f"go_{key_prefix}", use_container_width=True, type="primary"):
                                if rt.strip():
                                    t["done"] = True
                                    t["in_work"] = False
                                    t["needs_rework"] = False
                                    t["completion_report"] = rt.strip()
                                    t["last_modified"] = now_str()
                                    add_notification(t.get("created_by", ""), f"\u0417\u0430\u0434\u0430\u0447\u0430 \u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0435: {t.get('task_number','')} \u2014 {cl.get('name','')} | \u0412\u044b\u043f\u043e\u043b\u043d\u0438\u043b: {st.session_state.get('user_name','')}", f"\u2705 \u0417\u0430\u0434\u0430\u0447\u0430 \u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0435: {t.get('task_number','')} \u2014 {cl.get('name','')} | \u0412\u044b\u043f\u043e\u043b\u043d\u0438\u043b: {st.session_state.get('user_name','')}")
                                    fi_list = save_uploaded_files(uf, (d["client_id"] if d else cl["id"]), "task_report")
                                    if fi_list: t["completion_files"] = normalize_file_list(fi_list)
                                    cl["last_modified"] = now_str()
                                    if d: d["last_modified"] = now_str()
                                    st.session_state[show_key] = False
                                    # Create new task if checkbox was checked
                                    if create_new_task and nt_topic2.strip():
                                        ntfi_list2 = save_uploaded_files(nt_files2, (d["client_id"] if d else cl["id"]), "task_file") if nt_files2 else []
                                        prefix2 = "\u0417\u0421" if d else "\u0417\u041a"
                                        tn2 = generate_task_number(prefix2)
                                        new_task = {
                                            "text": nt_topic2.strip(), "deadline": nt_dl2.isoformat(), "done": False, "type": "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f",
                                            "task_files": normalize_file_list(ntfi_list2), "manager": nt_mgr2 or "",
                                            "completion_report": "", "completion_files": [],
                                            "deal_id": (d["id"] if d else None), "task_comment": nt_comment2.strip(),
                                            "order_amount": 0, "last_modified": now_str(),
                                            "task_number": tn2, "created_at": now_str(), "created_by": st.session_state.get("user_login", ""),
                                            "in_work": False, "ready_to_ship": False, "delegated_to": None, "needs_rework": False, "reviewed": False,
                                            "task_comments": [], "flagged": False,
                                            "products": "", "ship_addr": "", "receiver": "", "receiver_phone": "", "ship_pay": "", "tk_num": ""
                                        }
                                        cl.setdefault("tasks", []).append(new_task)
                                        if nt_mgr2:
                                            add_notification(nt_mgr2, f"\u041d\u043e\u0432\u0430\u044f \u0437\u0430\u0434\u0430\u0447\u0430: {nt_topic2.strip()} | \u041a\u043b\u0438\u0435\u043d\u0442: {cl.get('name','')} | \u0421\u0440\u043e\u043a: {nt_dl2.isoformat()}", f"\U0001F4DD \u041d\u043e\u0432\u0430\u044f \u0437\u0430\u0434\u0430\u0447\u0430: {nt_topic2.strip()} | \u041a\u043b\u0438\u0435\u043d\u0442: {cl.get('name','')} | \u0421\u0440\u043e\u043a: {nt_dl2.isoformat()}")
                                    st.session_state[f"uf_ver_{key_prefix}"] = uf_ver + 1
                                    commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u0430")
                                else: st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043e\u0442\u0447\u0435\u0442")
                        with pc2:
                            if st.button("\u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c", key=f"cancel_complete_{key_prefix}", use_container_width=True):
                                st.session_state[show_key] = False
                                _smart_rerun()
                else:
                    if t.get("needs_rework"):
                        st.markdown('<span class="reworkbadge" style="display:inline-block;background:#D32F2F;color:white;font-size:0.7rem;font-weight:700;padding:2px 8px;border-radius:99px;text-transform:uppercase;">\u041d\u0430 \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0435</span>', unsafe_allow_html=True)
                    if t.get("completion_report"): st.caption(f"\u041e\u0442\u0447\u0435\u0442: {t['completion_report']}")
                    if t.get("rework_comment"): st.warning(f"\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439 \u043a \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0435: {t['rework_comment']}")
                    if t.get("completion_files"):
                        st.markdown("**\u0424\u0430\u0439\u043b\u044b \u043e\u0442\u0447\u0435\u0442\u0430:**")
                        render_file_thumbs(t["completion_files"], f"{key_prefix}_cfiles")
                    if not t.get("reviewed", False):
                        is_author = (st.session_state.user_role == "admin") or (t.get("created_by", "") == st.session_state.get("user_login", ""))
                        if is_author:
                            st.markdown("---")
                            rc1, rc2 = st.columns(2)
                            with rc1:
                                if st.button("\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u0430", key=f"btn_review_{key_prefix}", type="primary", use_container_width=True):
                                    t["reviewed"] = True
                                    t["needs_rework"] = False
                                    t["rework_comment"] = ""
                                    t["last_modified"] = now_str()
                                    cl["last_modified"] = now_str()
                                    if d: d["last_modified"] = now_str()
                                    commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u0435\u043d\u0430 \u0438 \u0432 \u0430\u0440\u0445\u0438\u0432\u0435")
                            with rc2:
                                if st.button("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043d\u0430 \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0443", key=f"btn_rework_{key_prefix}", use_container_width=True):
                                    st.session_state[f"show_rework_{key_prefix}"] = True
                                    _smart_rerun()
                            if st.session_state.get(f"show_rework_{key_prefix}", False):
                                rework_comment = st.text_area("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439 \u043a \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0435 (\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e):", key=f"rework_comment_{key_prefix}", height=100, placeholder="\u041e\u043f\u0438\u0448\u0438\u0442\u0435, \u0447\u0442\u043e \u043d\u0443\u0436\u043d\u043e \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u0430\u0442\u044c")
                                rw1, rw2 = st.columns(2)
                                with rw1:
                                    if st.button("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043d\u0430 \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0443", key=f"btn_rework_send_{key_prefix}", type="primary", use_container_width=True):
                                        if not rework_comment.strip():
                                            st.warning("\u041d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439 \u2014 \u0431\u0435\u0437 \u043d\u0435\u0433\u043e \u043d\u0435\u043b\u044c\u0437\u044f \u043e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443 \u043d\u0430 \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0443")
                                        else:
                                            t["done"] = False
                                            t["in_work"] = False
                                            t["needs_rework"] = True
                                            t["rework_comment"] = rework_comment.strip()
                                            t.setdefault("task_comments", []).append({"author": st.session_state.get("user_login", ""), "text": rework_comment.strip(), "date": now_str()})
                                            t["last_modified"] = now_str()
                                            cl["last_modified"] = now_str()
                                            if d: d["last_modified"] = now_str()
                                            st.session_state[f"show_rework_{key_prefix}"] = False
                                            add_notification(t.get("manager", ""), f"\u0417\u0430\u0434\u0430\u0447\u0430 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0435\u043d\u0430 \u043d\u0430 \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0443: {t.get('task_number','')} \u2014 {cl.get('name','')} | \u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439: {rework_comment.strip()}", f"\u26a0\ufe0f \u0417\u0430\u0434\u0430\u0447\u0430 \u043d\u0430 \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0443: {t.get('task_number','')} \u2014 {cl.get('name','')} | \u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439: {rework_comment.strip()}")
                                            commit_and_rerun(st.session_state.crm_store, "\u0417\u0430\u0434\u0430\u0447\u0430 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0435\u043d\u0430 \u043d\u0430 \u0434\u043e\u0440\u0430\u0431\u043e\u0442\u043a\u0443")
                                with rw2:
                                    if st.button("\u041e\u0442\u043c\u0435\u043d\u0430", key=f"btn_rework_cancel_{key_prefix}", use_container_width=True):
                                        st.session_state[f"show_rework_{key_prefix}"] = False
                                        _smart_rerun()
                        else:
                            st.info("\u041e\u0436\u0438\u0434\u0430\u0435\u0442 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0438 \u0430\u0432\u0442\u043e\u0440\u043e\u043c")
                    else:
                        st.success("\u0417\u0430\u0434\u0430\u0447\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u0435\u043d\u0430")
            render_reminders("task", t.get("task_number", t.get("id", "")), _task_header, f"task_{key_prefix}")
        with right_col:
            # Comments block (now above files) — no gap at top
            if t.get("task_comments"):
                st.markdown("**\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438 \u0437\u0430\u0434\u0430\u0447\u0438:**")
                for tc in t["task_comments"]:
                    st.markdown(f"- *{tc.get('time', '')}* ({tc.get('user', '')}): {linkify_text(tc.get('text', ''))}", unsafe_allow_html=True)
            tc_clr_key = f"clr_tc_{key_prefix}"
            if st.session_state.get(tc_clr_key):
                st.session_state[f"tc_input_{key_prefix}"] = ""
                st.session_state[tc_clr_key] = False
            ntc = st.text_input("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:", key=f"tc_input_{key_prefix}", placeholder="\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439...")
            if st.button("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c", key=f"tc_btn_{key_prefix}", use_container_width=True):
                if ntc.strip():
                    t.setdefault("task_comments", []).append({"time": moscow_now().strftime("%d.%m.%Y %H:%M"), "text": ntc.strip(), "user": st.session_state.get("user_name", "")})
                    t["last_modified"] = now_str()
                    st.session_state[tc_clr_key] = True
                    commit_and_rerun(st.session_state.crm_store, "\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d")
                else: st.warning("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0442\u0435\u043a\u0441\u0442")
            st.markdown("---")
            # Files block (now below comments)
            if t.get("task_files"):
                st.markdown("**\u0424\u0430\u0439\u043b\u044b \u0437\u0430\u0434\u0430\u0447\u0438:**")
                render_file_thumbs(t["task_files"], f"{key_prefix}_files")
            st.markdown("**\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0444\u0430\u0439\u043b\u044b \u0432 \u0437\u0430\u0434\u0430\u0447\u0443:**")
            _tu_ver = st.session_state.get(f"task_upload_ver_{key_prefix}", 0)
            ntf_existing = st.file_uploader("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0444\u0430\u0439\u043b\u044b:", key=f"task_upload_{key_prefix}_{_tu_ver}", accept_multiple_files=True, label_visibility="collapsed")
            if st.button("\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c", key=f"task_upload_btn_{key_prefix}", use_container_width=True):
                if ntf_existing:
                    with st.spinner("\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0444\u0430\u0439\u043b\u043e\u0432..."):
                        fi_list = save_uploaded_files(ntf_existing, (d["client_id"] if d else cl["id"]), "task_file")
                    if fi_list:
                        t.setdefault("task_files", []).extend(normalize_file_list(fi_list))
                        t["last_modified"] = now_str()
                        cl["last_modified"] = now_str()
                        if d: d["last_modified"] = now_str()
                        st.session_state[f"task_upload_ver_{key_prefix}"] = _tu_ver + 1
                        commit_and_rerun(st.session_state.crm_store, "\u0424\u0430\u0439\u043b\u044b \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u044b")
                else: st.warning("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0444\u0430\u0439\u043b(\u044b)")

def render_task_row(t, cl, d, task_key, key_prefix):
    is_tk_exp = st.session_state.expanded_task_key == task_key
    tk_done = t.get("done", False)
    tk_overdue = is_task_overdue(t)
    tk_rework = t.get("needs_rework", False)
    if tk_done and not t.get("reviewed", False): tk_bg, tk_bc = "#FFF8E1", "#FF8F00"
    elif tk_done: tk_bg, tk_bc = "#F5F6F8", "#C9CFD7"
    elif tk_rework: tk_bg, tk_bc = "#FFEBEE", "#D32F2F"
    elif tk_overdue: tk_bg, tk_bc = "#FFEBEE", "#C62828"
    elif t.get("in_work"): tk_bg, tk_bc = "#E8F5E9", "#4CAF50"
    else: tk_bg, tk_bc = "#E3F2FD", "#2196F3"
    tk_label = f"Задача №{t.get('task_number', '')} — {t.get('text', '')} | {format_date(t.get('deadline', ''))}"
    if t.get('ready_to_ship') and not tk_done: tk_label += ' | Готово к отправке'
    if tk_done and not t.get("reviewed", False): tk_label += ' | На проверке'
    tk_selected = is_tk_exp
    tk_border = "#2196F3" if tk_selected else tk_bc
    tk_shadow = "box-shadow: 0 0 0 2px rgba(33,150,243,0.3);" if tk_selected else ""
    _rework_css = ""
    if tk_rework and not tk_done:
        _rework_css = f".st-key-tk_btn_wrap_{task_key} button::after {{ content: 'На доработке'; display: block; color: #D32F2F; font-weight: 700; font-size: 0.8rem; margin-top: 4px; }}"
    st.markdown(f"<style>.st-key-tk_btn_wrap_{task_key} button {{ background-color: {tk_bg} !important; color: #2C3E50 !important; border: 2px solid {tk_border} !important; border-radius: 10px !important; {tk_shadow} }} {_rework_css}</style>", unsafe_allow_html=True)
    with st.container(key=f"tk_btn_wrap_{task_key}"):
        if st.button(tk_label, key=f"tk_card_{task_key}", use_container_width=True, type="primary" if is_tk_exp else "secondary"):
            if is_tk_exp:
                st.session_state.expanded_task_key = None
                save_scroll_and_rerun()
            else:
                st.session_state.expanded_task_key = task_key
                _smart_rerun()
        if not is_tk_exp:
            render_scroll_restore(f"tk_{task_key}")
    if is_tk_exp: render_task_detail(t, cl, d, key_prefix)

def get_entity_border(tasks_list):
    has_overdue = any(not t.get("done") and is_task_overdue(t) for t in tasks_list)
    has_active = any(not t.get("done") for t in tasks_list)
    if has_overdue: return "#FFEBEE", "#C62828"
    elif has_active: return "#E8F5E9", "#4CAF50"
    else: return "#FFFFFF", "#DCE0E5"

def indented(margin=0.03):
    if margin <= 0:
        return st.container()
    cols = st.columns([margin, 1 - margin], gap="small")
    return cols[1]

def render_separator():
    st.markdown('<hr style="border:0;height:1px;background:#DCE0E5;margin:0.8rem 0;">', unsafe_allow_html=True)

def render_centered_title(title):
    st.markdown(f'<p class="section-title">{title}</p>', unsafe_allow_html=True)

def render_centered_button(label, key=None, btn_type="primary"):
    lbl_hash = hashlib.md5(label.encode()).hexdigest()[:6]
    btn_key = f"cb_{lbl_hash}_{key}" if key else f"cb_{lbl_hash}"
    cl1, cl2, cl3 = st.columns([1, 2, 1], gap="small")
    with cl2:
        if st.button(label, key=btn_key, type=btn_type, use_container_width=True):
            return True
    return False

def migrate_task_files(t):
    if "task_files" not in t:
        t["task_files"] = []
        if t.get("file_path"): t["task_files"].append({"file_path": t["file_path"], "file_name": t.get("file_name", "файл"), "file_hash": ""})
    if "completion_files" not in t:
        t["completion_files"] = []
        if t.get("completion_file_path"): t["completion_files"].append({"file_path": t["completion_file_path"], "file_name": t.get("completion_file_name", "файл"), "file_hash": ""})
    if "task_comments" not in t: t["task_comments"] = []
    if "in_work" not in t: t["in_work"] = False
    if "needs_rework" not in t: t["needs_rework"] = False
    if "reviewed" not in t: t["reviewed"] = False
    if "rework_comment" not in t: t["rework_comment"] = ""
    if "created_by" not in t: t["created_by"] = ""
    if "ready_to_ship" not in t: t["ready_to_ship"] = False
    if "delegated_to" not in t: t["delegated_to"] = None
    if "created_at" not in t: t["created_at"] = t.get("last_modified", "")
    if "flagged" not in t: t["flagged"] = False
    if "needs_rework" not in t: t["needs_rework"] = False
    if "reviewed" not in t: t["reviewed"] = False
    if "type" not in t: t["type"] = "Связаться"
    if "products" not in t: t["products"] = ""
    if "ship_addr" not in t: t["ship_addr"] = ""
    if "receiver" not in t: t["receiver"] = ""
    if "receiver_phone" not in t: t["receiver_phone"] = ""
    if "ship_pay" not in t: t["ship_pay"] = ""
    if "tk_num" not in t: t["tk_num"] = ""
    if t.get("type") == "Отправка": t["type"] = "Отправить заказ"

DEFAULT_PRODUCT_CATALOG = [
    {"id":"APLNT1003","sku":"APLNT1003","name":"Комплект «Айплинт встроенный»","unit":"м","price":1395.0,"note":"Всегда в наличии; продажа кратно 2 м","active":True},
    {"id":"APLNT1007-K","sku":"APLNT1007","name":"Комплект «Айплинт керамогранит»","unit":"м","price":1445.0,"note":"Всегда в наличии; продажа кратно 2 м","active":True},
    {"id":"APLNT1001","sku":"APLNT1001","name":"Магнитный профиль «Айплинт 1»","unit":"м","price":1195.0,"note":"Всегда в наличии; продажа кратно 2 м","active":True},
    {"id":"APLNT1002","sku":"APLNT1002","name":"Магнитный профиль «Айплинт 2»","unit":"м","price":1195.0,"note":"Всегда в наличии; продажа кратно 2 м","active":True},
    {"id":"APLNT1050","sku":"APLNT1050","name":"Тонкий плинтус «Айплинт Слим 4»","unit":"м","price":790.0,"note":"Высота 40 мм","active":True},
    {"id":"APLNT1051","sku":"APLNT1051","name":"Тонкий плинтус «Айплинт Слим 6»","unit":"м","price":890.0,"note":"Высота 60 мм","active":True},
    {"id":"APLNT1052","sku":"APLNT1052","name":"Айплинт Слим 4 LED","unit":"м","price":890.0,"note":"Скоро в продаже","active":False},
    {"id":"APLNT1053","sku":"APLNT1053","name":"Айплинт Слим 6 LED","unit":"м","price":890.0,"note":"Скоро в продаже","active":False},
    {"id":"APLNT1004","sku":"APLNT1004","name":"Вставка полимерная под покраску (2 м)","unit":"шт.","price":520.0,"note":"Продажа кратно 2 м; цена за изделие 2 м","active":True},
    {"id":"APLNT1006","sku":"APLNT1006","name":"Вставка из натурального каменного шпона","unit":"м","price":1790.0,"note":"На заказ; длина до 3,2 м","active":True},
    {"id":"APLNT1005","sku":"APLNT1005","name":"Комплект «Айплинт радиусный»","unit":"м/шт.","price":6490.0,"note":"На заказ; срок около 10 календарных дней; единицу уточнять","active":True},
    {"id":"APLNT1007-R","sku":"APLNT1007","name":"Магнитный профиль радиусный (без вставки)","unit":"м/шт.","price":5490.0,"note":"На заказ; срок около 10 календарных дней; единицу уточнять","active":True},
    {"id":"APLNT1010-1","sku":"APLNT1010-1","name":"Светодиодная лента COB 5/3000 (5 м)","unit":"уп.","price":1390.0,"note":"24V, 4000K; наличие уточнять","active":True},
    {"id":"APLNT1010-2","sku":"APLNT1010-2","name":"Светодиодная лента COB 5/4000 (5 м)","unit":"уп.","price":1390.0,"note":"24V, 4000K; наличие уточнять","active":True},
    {"id":"APLNT1010-3","sku":"APLNT1010-3","name":"Светодиодная лента COB 5/6500 (5 м)","unit":"уп.","price":1390.0,"note":"24V, 6500K; наличие уточнять","active":True},
    {"id":"APLNT1020-1","sku":"APLNT1020-1","name":"Блок питания 24V 150W","unit":"шт.","price":1590.0,"note":"Регулятор яркости; наличие уточнять","active":True},
    {"id":"APLNT1020-2","sku":"APLNT1020-2","name":"Блок питания 24V 200W","unit":"шт.","price":1790.0,"note":"Регулятор яркости; наличие уточнять","active":True},
    {"id":"APLNT1020-3","sku":"APLNT1020-3","name":"Блок питания 24V 300W","unit":"шт.","price":2190.0,"note":"Регулятор яркости; наличие уточнять","active":True},
    {"id":"APLNT1030","sku":"APLNT1030","name":"Датчик движения Rexant","unit":"шт.","price":1305.0,"note":"220V; наличие уточнять","active":True},
    {"id":"APLNT1060","sku":"APLNT1060","name":"Шпатель для подготовки основания","unit":"шт.","price":1390.0,"note":"В наличии","active":True},
    {"id":"APLNT1102","sku":"APLNT1102","name":"Образцы магнитного и тонкого плинтусов","unit":"компл.","price":0.0,"note":"Бесплатно","active":True},
]
DISCOUNT_TYPES = {"Без скидки": 0, "Дилерская": 30, "Дизайнер / строитель": 10, "Акционная": 5, "Индивидуальная": 0}

def migrate_data(data):
    du = [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}]
    if "users" not in data: data["users"] = du
    if "notifications" not in data: data["notifications"] = []
    for u in data["users"]:
        if not is_hashed(u.get("password", "")): u["password"] = hash_password(u["password"])
        if "telegram_chat_id" not in u: u["telegram_chat_id"] = ""
    for c in data.get("clients", []):
        client_deals = [d for d in data.get("deals", []) if d.get("client_id") == c["id"]]
        first_deal_id = client_deals[0]["id"] if client_deals else None
        for k, v in [("email",""),("address",""),("base_comment",""),("category","Не определён"),("discount",0),("extra_phones",[]),("extra_emails",[]),("extra_addresses",[]),("client_files",[]),("client_comments",[]),("requisites",[]),("manager",""),("comments",[]),("tasks",[]),("last_modified","1970-01-01 00:00:00"),("client_chat",[]),("created_at","")]:
            if k not in c or c[k] == "-": c[k] = v
        for ea in c.get("extra_addresses", []):
            if isinstance(ea, str):
                idx = c["extra_addresses"].index(ea)
                c["extra_addresses"][idx] = {"address": ea, "resp_name": "", "resp_role": "", "resp_phone": "", "resp_email": ""}
        for t in c.get("tasks", []):
            if "manager" not in t: t["manager"] = c.get("manager", "")
            if "deadline" in t and " " in str(t["deadline"]): t["deadline"] = str(t["deadline"]).split(" ")[0]
            if "completion_report" not in t: t["completion_report"] = ""
            if "deal_id" not in t: t["deal_id"] = first_deal_id
            if "last_modified" not in t: t["last_modified"] = "1970-01-01 00:00:00"
            if "task_number" not in t: t["task_number"] = ""
            if "created_at" not in t: t["created_at"] = ""
            migrate_task_files(t)
    for d in data.get("deals", []):
        if "deal_title" not in d: d["deal_title"] = ""
        if "deal_comments" not in d: d["deal_comments"] = []
        if "deal_files" not in d: d["deal_files"] = []
        if "payment_status" not in d: d["payment_status"] = "Не оплачено"
        if "manager" not in d: d["manager"] = ""
        if "close_files" not in d:
            d["close_files"] = []
            if d.get("close_file_path"): d["close_files"].append({"file_path": d["close_file_path"], "file_name": d.get("close_file_name", "файл"), "file_hash": ""})
        if "last_modified" not in d: d["last_modified"] = "1970-01-01 00:00:00"
        if "deal_chat" not in d: d["deal_chat"] = []
        if "deal_number" not in d: d["deal_number"] = ""
        if "created_at" not in d: d["created_at"] = ""
        if d.get("status") == "New": d["status"] = "Новый"
        if d.get("status") == "На согласовании": d["status"] = "В работе"
        if d.get("title", "").startswith("Заказ"): d["title"] = d.get("deal_number", d["title"])
    assign_task_numbers(data)
    assign_deal_numbers(data)
    if "internal_tasks" not in data: data["internal_tasks"] = []
    if "chat_messages" not in data: data["chat_messages"] = []
    if "qa_entries" not in data: data["qa_entries"] = []
    if "suppliers" not in data: data["suppliers"] = []
    if "products" not in data: data["products"] = copy.deepcopy(DEFAULT_PRODUCT_CATALOG)
    data["_migrated"] = "v2"
    return data

def _load_data_from_json():
    """Старый загрузчик JSON/Яндекс Диска; используется только при первичной миграции в SQLite."""
    download_db_from_yandex()
    db = {"clients": [], "deals": [], "users": [{"login": "admin", "password": hash_password("admin"), "role": "admin", "name": "Администратор"}], "_migrated": "v2", "internal_tasks": [], "chat_messages": [], "qa_entries": [], "suppliers": [], "notifications": []}
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("_migrated") != "v2":
                data = migrate_data(data)
                with open(FILE_NAME, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                upload_db_to_yandex_sync()
            else:
                for c in data.get("clients", []):
                    client_deals = [d for d in data.get("deals", []) if d.get("client_id") == c["id"]]
                    first_deal_id = client_deals[0]["id"] if client_deals else None
                    if "last_modified" not in c: c["last_modified"] = "1970-01-01 00:00:00"
                    if "client_chat" not in c: c["client_chat"] = []
                    if "created_at" not in c: c["created_at"] = c.get("last_modified", "")
                    for t in c.get("tasks", []):
                        if "completion_report" not in t: t["completion_report"] = ""
                        if "deal_id" not in t: t["deal_id"] = first_deal_id
                        if "last_modified" not in t: t["last_modified"] = "1970-01-01 00:00:00"
                        if "task_number" not in t: t["task_number"] = ""
                        if "created_at" not in t: t["created_at"] = t.get("last_modified", "")
                        if "in_work" not in t: t["in_work"] = False
                        if "needs_rework" not in t: t["needs_rework"] = False
                        if "reviewed" not in t: t["reviewed"] = False
                        if "created_by" not in t: t["created_by"] = ""
                        if "ready_to_ship" not in t: t["ready_to_ship"] = False
                        if "delegated_to" not in t: t["delegated_to"] = None
                        if "task_comments" not in t: t["task_comments"] = []
                        if "flagged" not in t: t["flagged"] = False
                        if "type" not in t: t["type"] = "Связаться"
                        if "products" not in t: t["products"] = ""
                        if "ship_addr" not in t: t["ship_addr"] = ""
                        if "receiver" not in t: t["receiver"] = ""
                        if "receiver_phone" not in t: t["receiver_phone"] = ""
                        if "ship_pay" not in t: t["ship_pay"] = ""
                        if "tk_num" not in t: t["tk_num"] = ""
                        if t.get("type") == "Отправка": t["type"] = "Отправить заказ"
                        migrate_task_files(t)
                for d in data.get("deals", []):
                    if "deal_title" not in d: d["deal_title"] = ""
                    if "deal_files" not in d: d["deal_files"] = []
                    if "payment_status" not in d: d["payment_status"] = "Не оплачено"
                    if "manager" not in d: d["manager"] = ""
                    if "close_files" not in d:
                        d["close_files"] = []
                        if d.get("close_file_path"): d["close_files"].append({"file_path": d["close_file_path"], "file_name": d.get("close_file_name", "файл"), "file_hash": ""})
                    if "last_modified" not in d: d["last_modified"] = "1970-01-01 00:00:00"
                    if "deal_chat" not in d: d["deal_chat"] = []
                    if "deal_number" not in d: d["deal_number"] = ""
                    if "created_at" not in d: d["created_at"] = d.get("last_modified", "")
                    if d.get("status") == "На согласовании": d["status"] = "В работе"
                    if d.get("title", "").startswith("Заказ"): d["title"] = d.get("deal_number", d["title"])
                assign_task_numbers(data)
                assign_deal_numbers(data)
                if "internal_tasks" not in data: data["internal_tasks"] = []
                if "chat_messages" not in data: data["chat_messages"] = []
                if "qa_entries" not in data: data["qa_entries"] = []
                if "suppliers" not in data: data["suppliers"] = []
            return data
        except Exception:
            return db
    return db

# SQLite — локальное основное хранилище с транзакциями. JSON сохраняется как
# совместимая копия/экспорт, а Яндекс Диск используется как резервная копия.
SQLITE_FILE = FILE_NAME + ".sqlite3"
_sqlite_init_lock = threading.Lock()

def _sqlite_connect():
    conn = sqlite3.connect(SQLITE_FILE, timeout=30, isolation_level=None)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = FULL")
    return conn

def _ensure_sqlite_store():
    """Создаёт SQLite и переносит существующую JSON-базу только один раз."""
    with _sqlite_init_lock:
        conn = _sqlite_connect()
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS crm_state (id INTEGER PRIMARY KEY CHECK (id = 1), data TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL)")
            row = conn.execute("SELECT data FROM crm_state WHERE id = 1").fetchone()
            if row is None:
                # При первой инициализации берём текущую рабочую базу, включая
                # существующую загрузку с Яндекс Диска и миграции старого формата.
                initial_data = _load_data_from_json()
                initial_json = json.dumps(initial_data, ensure_ascii=False, separators=(",", ":"))
                conn.execute("BEGIN IMMEDIATE")
                try:
                    conn.execute("INSERT OR IGNORE INTO crm_state (id, data, revision, updated_at) VALUES (1, ?, 1, ?)", (initial_json, now_str()))
                    conn.execute("COMMIT")
                except Exception:
                    conn.execute("ROLLBACK")
                    raise
                # Обновляем JSON-зеркало безопасно.
                tmp_name = FILE_NAME + ".tmp"
                with open(tmp_name, "w", encoding="utf-8") as f:
                    f.write(initial_json)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_name, FILE_NAME)
        finally:
            conn.close()

def _remember_session_base(data, revision):
    """Сохраняет неизменяемую базовую копию, относительно которой сравниваются правки сессии."""
    try:
        st.session_state["crm_base_snapshot"] = copy.deepcopy(data)
        st.session_state["crm_base_revision"] = int(revision or 0)
    except Exception:
        pass

def load_data():
    """Читает данные из SQLite и запоминает ревизию для безопасного слияния правок сессии."""
    try:
        _ensure_sqlite_store()
        conn = _sqlite_connect()
        try:
            row = conn.execute("SELECT data, revision FROM crm_state WHERE id = 1").fetchone()
            if row and row[0]:
                data = json.loads(row[0])
                _remember_session_base(data, row[1])
                return data
        finally:
            conn.close()
    except Exception as exc:
        # JSON fallback нужен только для аварийного восстановления; при его использовании
        # базовая ревизия неизвестна, поэтому следующий save применит консервативную политику.
        try:
            st.sidebar.error(f"SQLite недоступна, используется резервная загрузка JSON: {exc}")
        except Exception:
            pass
        data = _load_data_from_json()
        _remember_session_base(data, 0)
        return data
    data = _load_data_from_json()
    _remember_session_base(data, 0)
    return data

_MISSING = object()

def _stable_list_key(items):
    """Возвращает стабильный ключ списка только если он уникален у каждого элемента."""
    if not items or not all(isinstance(x, dict) for x in items):
        return None
    for field in ("id", "login", "task_number", "uuid"):
        values = [x.get(field, _MISSING) for x in items]
        if all(v is not _MISSING and v is not None and v != "" for v in values):
            try:
                if len(set(values)) == len(values):
                    return field
            except TypeError:
                continue
    return None

def _three_way_merge(base, ours, latest, path="", conflicts=None):
    """Трёхстороннее слияние: объединяет независимые правки и не воскрешает удалённые записи."""
    if conflicts is None:
        conflicts = []
    if ours == base:
        return copy.deepcopy(latest), conflicts
    if latest == base:
        return copy.deepcopy(ours), conflicts
    if ours == latest:
        return copy.deepcopy(ours), conflicts

    if isinstance(base, dict) and isinstance(ours, dict) and isinstance(latest, dict):
        result = {}
        keys = set(base) | set(ours) | set(latest)
        for key in keys:
            b = base.get(key, _MISSING)
            o = ours.get(key, _MISSING)
            n = latest.get(key, _MISSING)
            subpath = f"{path}.{key}" if path else str(key)
            if o is _MISSING:
                if b is _MISSING:
                    if n is not _MISSING:
                        result[key] = copy.deepcopy(n)
                elif n is _MISSING:
                    continue
                elif n == b:
                    continue  # наше удаление, запись с другой стороны не менялась
                else:
                    result[key] = copy.deepcopy(n)  # не удаляем более свежую правку коллеги
                    conflicts.append(subpath + " (удаление против изменения)")
                continue
            if n is _MISSING:
                if b is _MISSING:
                    result[key] = copy.deepcopy(o)
                elif o == b:
                    continue  # коллега удалил запись, а наша копия не менялась
                else:
                    # Удаление в актуальной базе приоритетнее устаревшей правки.
                    conflicts.append(subpath + " (изменение против удаления)")
                continue
            result[key], conflicts = _three_way_merge(b, o, n, subpath, conflicts)
        return result, conflicts

    if isinstance(base, list) and isinstance(ours, list) and isinstance(latest, list):
        key = None
        # Проверяем уникальность ключей отдельно в каждом снимке; одинаковые ID
        # между снимками ожидаемы и не должны отключать поэлементное слияние.
        for candidate in ("id", "login", "task_number", "uuid"):
            valid = True
            for sequence in (base, ours, latest):
                values = []
                for item in sequence:
                    if not isinstance(item, dict) or item.get(candidate, _MISSING) in (_MISSING, None, ""):
                        valid = False
                        break
                    values.append(item[candidate])
                if not valid:
                    break
                try:
                    if len(set(values)) != len(values):
                        valid = False
                        break
                except TypeError:
                    valid = False
                    break
            if valid:
                key = candidate
                break
        if key:
            def to_map(seq):
                return {item[key]: item for item in seq}
            bm, om, nm = to_map(base), to_map(ours), to_map(latest)
            merged_map, conflicts = _three_way_merge(bm, om, nm, path, conflicts)
            # Стабильный порядок: сначала актуальный список, затем новые элементы из нашей сессии.
            ordered_keys = [item[key] for item in latest]
            seen_order = set(ordered_keys)
            for item in ours:
                if item[key] not in seen_order:
                    ordered_keys.append(item[key])
                    seen_order.add(item[key])
            for item_key in merged_map:
                if item_key not in seen_order:
                    ordered_keys.append(item_key)
                    seen_order.add(item_key)
            return [merged_map[k] for k in ordered_keys if k in merged_map], conflicts
        # Для списков-комментариев и истории сохраняем независимые добавления, если
        # обе стороны только дописали элементы в конец и не меняли старые.
        if ours[:len(base)] == base and latest[:len(base)] == base:
            combined = copy.deepcopy(latest)
            for item in ours[len(base):]:
                if item not in combined:
                    combined.append(copy.deepcopy(item))
            return combined, conflicts
        # При сложном конфликте в списке без стабильных ID не затираем последнюю версию.
        conflicts.append((path or "список") + " (одновременное изменение списка без стабильных ID)")
        return copy.deepcopy(latest), conflicts

    # Оба участника поменяли одно и то же поле по-разному: сохраняем последнее подтверждённое значение.
    conflicts.append(path or "корневое значение")
    return copy.deepcopy(latest), conflicts

_save_lock = threading.Lock()

def _download_disk_data():
    """Скачивает JSON-базу с Диска и возвращает dict, или None при ошибке."""
    if not YANDEX_TOKEN:
        return None
    try:
        res = requests.get(f"{YANDEX_API_URL}/download",
            params={"path": f"disk:/CRM_NE_TROGAT/{FILE_NAME}"},
            headers=yandex_headers(), timeout=10)
        if res.status_code == 200:
            dl = requests.get(res.json().get("href"), timeout=30)
            if dl.status_code == 200:
                return json.loads(dl.text)
    except:
        pass
    return None

def _merge_data(local_data, disk_data):
    """Сливает локальные данные с данными с Диска по таймстампам.
    Для каждой сущности берёт версию с более свежим last_modified.
    Сущности, которых нет локально, добавляются с Диска."""
    if not disk_data:
        return local_data
    if not local_data:
        return disk_data

    merged = dict(local_data)

    # --- Клиенты ---
    local_clients = {c["id"]: c for c in local_data.get("clients", [])}
    disk_clients = {c["id"]: c for c in disk_data.get("clients", [])}
    merged_clients = []
    # Сначала берём все ID из обоих источников
    all_client_ids = set(local_clients.keys()) | set(disk_clients.keys())
    for cid in all_client_ids:
        lc = local_clients.get(cid)
        dc = disk_clients.get(cid)
        if lc and dc:
            # Берём новейшую версию клиента
            if dc.get("last_modified", "") > lc.get("last_modified", ""):
                client = dict(dc)
            else:
                client = dict(lc)
            # Сливаем задачи внутри клиента
            local_tasks = {t.get("id", i): t for i, t in enumerate(lc.get("tasks", []))}
            disk_tasks = {t.get("id", i): t for i, t in enumerate(dc.get("tasks", []))}
            all_task_ids = set(local_tasks.keys()) | set(disk_tasks.keys())
            merged_tasks = []
            for tid in all_task_ids:
                lt = local_tasks.get(tid)
                dt = disk_tasks.get(tid)
                if lt and dt:
                    if dt.get("last_modified", "") > lt.get("last_modified", ""):
                        merged_tasks.append(dt)
                    else:
                        merged_tasks.append(lt)
                elif lt:
                    merged_tasks.append(lt)
                else:
                    merged_tasks.append(dt)
            client["tasks"] = merged_tasks
            merged_clients.append(client)
        elif lc:
            merged_clients.append(lc)
        else:
            merged_clients.append(dc)
    merged["clients"] = merged_clients

    # --- Сделки ---
    local_deals = {d["id"]: d for d in local_data.get("deals", [])}
    disk_deals = {d["id"]: d for d in disk_data.get("deals", [])}
    all_deal_ids = set(local_deals.keys()) | set(disk_deals.keys())
    merged_deals = []
    for did in all_deal_ids:
        ld = local_deals.get(did)
        dd = disk_deals.get(did)
        if ld and dd:
            if dd.get("last_modified", "") > ld.get("last_modified", ""):
                merged_deals.append(dd)
            else:
                merged_deals.append(ld)
        elif ld:
            merged_deals.append(ld)
        else:
            merged_deals.append(dd)
    merged["deals"] = merged_deals

    # --- Внутренние задачи ---
    local_it = {it.get("id", i): it for i, it in enumerate(local_data.get("internal_tasks", []))}
    disk_it = {it.get("id", i): it for i, it in enumerate(disk_data.get("internal_tasks", []))}
    all_it_ids = set(local_it.keys()) | set(disk_it.keys())
    merged_it = []
    for itid in all_it_ids:
        lit = local_it.get(itid)
        dit = disk_it.get(itid)
        if lit and dit:
            if dit.get("last_modified", "") > lit.get("last_modified", ""):
                merged_it.append(dit)
            else:
                merged_it.append(lit)
        elif lit:
            merged_it.append(lit)
        else:
            merged_it.append(dit)
    merged["internal_tasks"] = merged_it

    # --- Поставщики ---
    local_sup = {s.get("id", i): s for i, s in enumerate(local_data.get("suppliers", []))}
    disk_sup = {s.get("id", i): s for i, s in enumerate(disk_data.get("suppliers", []))}
    all_sup_ids = set(local_sup.keys()) | set(disk_sup.keys())
    merged_sup = []
    for sid in all_sup_ids:
        ls = local_sup.get(sid)
        ds = disk_sup.get(sid)
        if ls and ds:
            if ds.get("last_modified", "") > ls.get("last_modified", ""):
                merged_sup.append(ds)
            else:
                merged_sup.append(ls)
        elif ls:
            merged_sup.append(ls)
        else:
            merged_sup.append(ds)
    merged["suppliers"] = merged_sup

    # --- Пользователи (берём объединение, локальный приоритет) ---
    local_users = {u.get("login"): u for u in local_data.get("users", [])}
    disk_users = {u.get("login"): u for u in disk_data.get("users", [])}
    all_logins = set(local_users.keys()) | set(disk_users.keys())
    merged_users = []
    for login in all_logins:
        lu = local_users.get(login)
        du = disk_users.get(login)
        if lu and du:
            if du.get("last_modified", "") > lu.get("last_modified", ""):
                merged_users.append(du)
            else:
                merged_users.append(lu)
        elif lu:
            merged_users.append(lu)
        else:
            merged_users.append(du)
    merged["users"] = merged_users

    # --- Простые списки (chat, qa, notifications) — берём локальные ---
    for key in ("chat_messages", "qa_entries", "notifications", "_migrated"):
        if key in local_data:
            merged[key] = local_data[key]
        elif key in disk_data:
            merged[key] = disk_data[key]

    return merged

def save_data(data):
    """Транзакционно сохраняет изменения, сливая их с актуальной ревизией без воскрешения удалений."""
    with _save_lock:
        conn = None
        try:
            _ensure_sqlite_store()
            conn = _sqlite_connect()
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT data, revision FROM crm_state WHERE id = 1").fetchone()
            latest_data = json.loads(row[0]) if row and row[0] else {}
            revision = int(row[1]) if row else 0
            base_data = st.session_state.get("crm_base_snapshot")
            base_revision = int(st.session_state.get("crm_base_revision", 0) or 0)
            conflicts = []

            if base_data is None:
                # Неизвестная база сравнения: не перезаписываем общую базу устаревшей сессией.
                merged_data = latest_data if latest_data else copy.deepcopy(data)
                conflicts.append("базовая версия сессии неизвестна; сохранена актуальная база")
            elif base_revision < revision:
                merged_data, conflicts = _three_way_merge(base_data, data, latest_data, conflicts=conflicts)
            else:
                merged_data = copy.deepcopy(data)

            snapshot = json.dumps(merged_data, ensure_ascii=False, separators=(",", ":"))
            new_revision = revision + 1
            conn.execute(
                "INSERT INTO crm_state (id, data, revision, updated_at) VALUES (1, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET data=excluded.data, revision=excluded.revision, updated_at=excluded.updated_at",
                (snapshot, new_revision, now_str()))
            conn.execute("COMMIT")
            conn.close()
            conn = None

            # После commit обновляем рабочую сессию и её базу сравнения.
            try:
                if st.session_state.get("crm_store") is data:
                    st.session_state["crm_store"] = copy.deepcopy(merged_data)
                _remember_session_base(merged_data, new_revision)
                if conflicts:
                    st.session_state["crm_last_save_conflicts"] = conflicts[:20]
            except Exception:
                pass

            _queue_yandex_snapshot(snapshot)

            # JSON — только переносимое зеркало. Основная подтверждённая запись уже в SQLite.
            try:
                tmp_name = FILE_NAME + ".tmp"
                with open(tmp_name, "w", encoding="utf-8") as f:
                    f.write(snapshot)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_name, FILE_NAME)
            except Exception as mirror_exc:
                try:
                    st.sidebar.warning(f"Основная база сохранена, но JSON-копия не обновлена: {mirror_exc}")
                except Exception:
                    pass

            if conflicts:
                try:
                    st.warning("Обнаружены параллельные изменения. Чтобы не потерять данные коллег, конфликтующие поля оставлены в последней сохранённой версии. Проверьте запись и при необходимости внесите изменение повторно.")
                except Exception:
                    pass
        except Exception as e:
            if conn is not None:
                try:
                    conn.execute("ROLLBACK")
                except Exception:
                    pass
                conn.close()
            try:
                st.sidebar.error(f"Ошибка сохранения: {e}")
            except Exception:
                pass

def commit_and_rerun(data=None, toast_msg=None):
    if data is not None:
        save_data(data)
    if toast_msg:
        st.toast(toast_msg, icon="✅")
    _smart_rerun()

_in_dialog = False

def _smart_rerun():
    st.rerun()


def _push_dialog_return():
    """Сохранить текущий диалог в стек перед открытием нового."""
    stack = st.session_state.get("_dialog_return_stack", [])
    current = {}
    for key in ["dialog_client_key", "dialog_deal_key", "dialog_task_key",
                "dialog_client_deals_key", "dialog_client_tasks_key",
                "dialog_deal_task_key", "_open_created_task", "dialog_invoice_request"]:
        val = st.session_state.get(key)
        if val:
            current[key] = val
    if current:
        # Возвращаем не только идентификатор окна, но и вкладку, в которой оно открывалось.
        current["__active_tab__"] = st.session_state.get("active_tab")
        stack.append(current)
        st.session_state["_dialog_return_stack"] = stack


def _pop_dialog_return():
    """Восстановить предыдущий диалог из стека при закрытии текущего."""
    stack = st.session_state.get("_dialog_return_stack", [])
    if stack:
        prev = stack.pop()
        st.session_state["_dialog_return_stack"] = stack
        for key, val in prev.items():
            if key == "__active_tab__":
                if val:
                    st.session_state["active_tab"] = val
            else:
                st.session_state[key] = val
        return True
    return False

# ====== УВЕДОМЛЕНИЯ ======
# Токен берётся из Streamlit secrets или переменной окружения, не хранится в исходнике.
try:
    TELEGRAM_BOT_TOKEN = (st.secrets.get("TELEGRAM_BOT_TOKEN", "") or os.getenv("TELEGRAM_BOT_TOKEN", "")).strip()
except Exception:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

def get_user_by_login(login):
    for u in st.session_state.crm_store.get("users", []):
        if u.get("login") == login:
            return u
    return None

def resolve_login(name_or_login):
    """Преобразует имя сотрудника в логин (для уведомлений)."""
    if not name_or_login:
        return ""
    # Сначала пробуем как логин
    u = get_user_by_login(name_or_login)
    if u:
        return u["login"]
    # Потом ищем по имени
    for u in st.session_state.crm_store.get("users", []):
        if u.get("name") == name_or_login:
            return u["login"]
    return name_or_login

def send_telegram(chat_id, text):
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=5
        )
    except:
        pass

def add_notification(to_login, text, tg_text=None):
    """Создаёт уведомление: внутреннее (колокольчик) + Telegram"""
    to_login = resolve_login(to_login)
    store = st.session_state.crm_store
    if "notifications" not in store:
        store["notifications"] = []
    notif = {
        "id": uuid.uuid4().hex,
        "to": to_login,
        "text": text,
        "date": now_str(),
        "read": False
    }
    store["notifications"].append(notif)
    # Telegram
    u = get_user_by_login(to_login)
    if u and u.get("telegram_chat_id"):
        send_telegram(u["telegram_chat_id"], tg_text or text)

def get_unread_count():
    me = st.session_state.get("user_login", "")
    notifs = st.session_state.crm_store.get("notifications", [])
    return sum(1 for n in notifs if n.get("to") == me and not n.get("read", False))

def get_my_notifications():
    me = st.session_state.get("user_login", "")
    notifs = st.session_state.crm_store.get("notifications", [])
    mine = [n for n in notifs if n.get("to") == me]
    mine.sort(key=lambda n: n.get("date", ""), reverse=True)
    return mine[:30]

def mark_all_notifications_read():
    me = st.session_state.get("user_login", "")
    for n in st.session_state.crm_store.get("notifications", []):
        if n.get("to") == me:
            n["read"] = True
    save_data(st.session_state.crm_store)

@_crm_dialog("🔔 Уведомления", width="large")
def notifications_dialog():
    st.session_state["_in_dialog"] = True
    _key_prefix = "notif_dlg"
    # Close button
    _close_css_key = f"close_row_{_key_prefix}"
    st.markdown(f'<style>.st-key-{_close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-height:36px!important;padding:0!important;font-size:1.2rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:8px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{_close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{_close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=_close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("\u2715", key=f"close_btn_{_key_prefix}", use_container_width=True):
                st.session_state.pop("show_notifications_dialog", None)
                st.session_state["_in_dialog"] = False
                st.rerun()
    notifs = get_my_notifications()
    unread = get_unread_count()
    _nc1, _nc2 = st.columns(2)
    with _nc1:
        if unread > 0:
            if st.button("Прочитать все", key="btn_read_all_dlg", use_container_width=True, type="primary"):
                mark_all_notifications_read()
                save_data(st.session_state.crm_store)
                st.rerun()
    with _nc2:
        if st.button("Очистить прочитанные", key="btn_clear_read_dlg", use_container_width=True):
            me = st.session_state.get("user_login", "")
            st.session_state.crm_store["notifications"] = [
                n for n in st.session_state.crm_store.get("notifications", [])
                if not (n.get("to") == me and n.get("read", False))
            ]
            save_data(st.session_state.crm_store)
            st.rerun()
    if not notifs:
        st.caption("Нет уведомлений")
    else:
        for n in notifs:
            bg = "#E3F2FD" if not n.get("read", False) else "#F5F6F8"
            border = "1px solid #BBDEFB" if not n.get("read", False) else "1px solid #E8EBEF"
            st.markdown(
                f'<div style="background:{bg};border:{border};border-radius:10px;padding:5px 7px;margin-bottom:3px;line-height:1.2;">'
                f'<span style="font-size:0.65rem;color:#95A5B7;">{n.get("date","")}</span><br>'
                f'<span style="font-size:0.82rem;color:#2C3E50;">{n.get("text","")}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

def render_notifications_bell():
    """Кнопка уведомлений на всю ширину левой колонки, счётчик внутри справа от колокольчика."""
    unread = get_unread_count()
    bell_key = "show_notifications_dialog"
    bell_label = f"🔔   {unread}"
    st.markdown("""<style>
    .st-key-crm_bell_wrap { width:100%!important; }
    .st-key-crm_bell_wrap [data-testid="stVerticalBlock"] { width:100%!important; }
    .st-key-crm_bell_wrap [data-testid="stButton"] { width:100%!important; }
    .st-key-crm_bell_wrap [data-testid="stButton"] > button {
        width:100%!important; min-width:100%!important; box-sizing:border-box!important;
        padding:0.45rem 0.5rem!important; display:flex!important;
        align-items:center!important; justify-content:center!important;
        white-space:nowrap!important; font-size:1.15rem!important; font-weight:700!important;
        font-variant-numeric:tabular-nums!important;
    }
    .st-key-crm_bell_wrap [data-testid="stButton"] > button p {
        white-space:nowrap!important; font-size:1.15rem!important; font-weight:700!important;
        margin:0!important; line-height:1.2!important;
    }
    </style>""", unsafe_allow_html=True)
    with st.container(key="crm_bell_wrap"):
        if st.button(bell_label, key="btn_bell", help="Уведомления", use_container_width=True):
            st.session_state[bell_key] = True
            st.rerun()

def render_notifications_panel():
    """Показ диалога уведомлений"""
    if st.session_state.get("show_notifications_dialog", False):
        notifications_dialog()

def render_close_deal_dialog_trigger():
    """Триггер диалога завершения сделки"""
    _close_deal_id = st.session_state.get("dialog_close_deal_id")
    if _close_deal_id:
        close_deal_dialog(_close_deal_id)



@_crm_dialog("Завершить сделку", width="medium")
def close_deal_dialog(deal_id):
    st.session_state["_in_dialog"] = True
    _key_prefix = f"close_deal_{deal_id}"
    # Close button
    _close_css_key = f"close_row_{_key_prefix}"
    st.markdown(f'<style>.st-key-{_close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:6px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{_close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{_close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=_close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("\u2715", key=f"close_btn_{_key_prefix}", use_container_width=True):
                st.session_state.pop("dialog_close_deal_id", None)
                st.session_state["_in_dialog"] = False
                st.rerun()
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
        for t in incomplete:
            st.markdown(f"- №{t.get('task_number', '')} — {format_date(t.get('deadline', ''))} — {t.get('text', '')}")
        if st.button("Понятно", use_container_width=True):
            st.rerun()
        return
    st.markdown("Заполните отчёт о выполнении сделки:")
    report = st.text_area("Отчёт (обязательно):", key=f"close_deal_report_{deal_id}", height=80)
    close_files = st.file_uploader("Файлы закрытия:", key=f"close_deal_file_{deal_id}", accept_multiple_files=True)
    if st.button("Завершить сделку", type="primary", use_container_width=True):
        if report.strip():
            for d in st.session_state.crm_store["deals"]:
                if d["id"] == deal_id:
                    d['status'] = "Сделка закрыта"
                    d['closed_date'] = moscow_now().strftime("%Y-%m-%d")
                    d['close_report'] = report.strip()
                    d['close_files'] = normalize_file_list(save_uploaded_files(close_files, d["client_id"], "deal_close")) if close_files else []
                    d["last_modified"] = now_str()
                    break
            save_data(st.session_state.crm_store)
            st.session_state.pop("dialog_close_deal_id", None)
            st.toast("Сделка завершена", icon="✅")
            st.rerun()
        else:
            st.error("Заполните отчёт")

if "crm_store" not in st.session_state:
    with st.spinner("Загрузка данных..."):
        st.session_state.crm_store = load_data()
# Каталог товаров добавляется совместимо с уже работающей базой.
if "products" not in st.session_state.crm_store:
    st.session_state.crm_store["products"] = copy.deepcopy(DEFAULT_PRODUCT_CATALOG)
    save_data(st.session_state.crm_store)
# Показываем конфликт уже после rerun, чтобы предупреждение не исчезало сразу.
_saved_conflicts = st.session_state.pop("crm_last_save_conflicts", None)
if _saved_conflicts:
    st.warning("При параллельном редактировании часть конфликтующих изменений не применена, чтобы не затереть данные коллеги. Проверьте нужную запись и повторите изменение.")
    with st.expander("Подробнее о конфликте сохранения"):
        for _conflict_path in _saved_conflicts:
            st.caption(str(_conflict_path))
if "f_ph" not in st.session_state: st.session_state.f_ph = []
if "f_em" not in st.session_state: st.session_state.f_em = []
if "f_ad" not in st.session_state: st.session_state.f_ad = []
if "last_id" not in st.session_state: st.session_state.last_id = None
if "active_tab" not in st.session_state: st.session_state.active_tab = "Задачи"
if "client_form_version" not in st.session_state: st.session_state.client_form_version = 0
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "user_role" not in st.session_state: st.session_state.user_role = None
if "user_login" not in st.session_state: st.session_state.user_login = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "cloud_ok" not in st.session_state: st.session_state.cloud_ok = check_cloud_status()
if "open_deal_id" not in st.session_state: st.session_state.open_deal_id = None
if "yandex_folders_ready" not in st.session_state:
    init_yandex_folders()
    st.session_state.yandex_folders_ready = True
if "deal_file_uploader_ver" not in st.session_state: st.session_state.deal_file_uploader_ver = {}
if "expanded_client_id" not in st.session_state: st.session_state.expanded_client_id = None
if "expanded_deal_id" not in st.session_state: st.session_state.expanded_deal_id = None
if "expanded_task_key" not in st.session_state: st.session_state.expanded_task_key = None
if "dialog_task_key" not in st.session_state: st.session_state.dialog_task_key = None
if "dialog_deal_key" not in st.session_state: st.session_state.dialog_deal_key = None
if "dialog_client_key" not in st.session_state: st.session_state.dialog_client_key = None
if "dialog_client_deals_key" not in st.session_state: st.session_state.dialog_client_deals_key = None
if "dialog_client_tasks_key" not in st.session_state: st.session_state.dialog_client_tasks_key = None
if "dialog_create_deal_task_deal_id" not in st.session_state: st.session_state.dialog_create_deal_task_deal_id = None
if "dialog_create_client_task_client_id" not in st.session_state: st.session_state.dialog_create_client_task_client_id = None
if "dialog_create_client_task_deal_select_cl_id" not in st.session_state: st.session_state.dialog_create_client_task_deal_select_cl_id = None
if "dialog_create_deal_from_client" not in st.session_state: st.session_state.dialog_create_deal_from_client = None
if "dialog_deal_task_key" not in st.session_state: st.session_state.dialog_deal_task_key = None
if "client_sort_mode" not in st.session_state: st.session_state.client_sort_mode = "last_modified"
if "client_sort_cat" not in st.session_state: st.session_state.client_sort_cat = "Все"
if "expanded_tree_id" not in st.session_state: st.session_state.expanded_tree_id = None
if "auto_expand_deal_id" not in st.session_state: st.session_state.auto_expand_deal_id = None
if "scroll_to_deal" not in st.session_state: st.session_state.scroll_to_deal = None
if "_dialog_return_stack" not in st.session_state: st.session_state._dialog_return_stack = []
if "dialog_it_key" not in st.session_state: st.session_state.dialog_it_key = None
if "dialog_close_deal_id" not in st.session_state: st.session_state.dialog_close_deal_id = None

def _pin_hash(pin, salt=None):
    """Store a salted PBKDF2 hash; never store a PIN in plain text."""
    salt_bytes = secrets.token_bytes(16) if salt is None else base64.urlsafe_b64decode(str(salt) + "=" * (-len(str(salt)) % 4))
    digest = hashlib.pbkdf2_hmac("sha256", str(pin).encode("utf-8"), salt_bytes, 240000)
    return {
        "salt": base64.urlsafe_b64encode(salt_bytes).decode("ascii").rstrip("="),
        "hash": base64.urlsafe_b64encode(digest).decode("ascii").rstrip("="),
    }


def _pin_verify(user, pin):
    saved = user.get("login_pin")
    if not isinstance(saved, dict) or not saved.get("salt") or not saved.get("hash"):
        return False
    try:
        candidate = _pin_hash(pin, saved["salt"])["hash"]
        return secrets.compare_digest(candidate, str(saved["hash"]))
    except Exception:
        return False


def _create_browser_session(user, remember=True):
    """Create a revocable per-browser session cookie for the current authenticated run."""
    token = secrets.token_urlsafe(32)
    sessions = user.setdefault("auth_sessions", [])
    if not isinstance(sessions, list):
        sessions = []
        user["auth_sessions"] = sessions
    sessions.append({
        "token_hash": hashlib.sha256(token.encode("utf-8")).hexdigest(),
        "created_at": now_str(),
        "expires_at": (moscow_now() + timedelta(minutes=60)).isoformat(timespec="seconds"),
    })
    user.pop("auth_token", None)
    user["auth_sessions"] = sessions[-30:]
    save_data(st.session_state.crm_store)
    st.session_state.authenticated = True
    st.session_state.user_role = user.get("role")
    st.session_state.user_login = user.get("login")
    st.session_state.user_name = user.get("name", user.get("login", ""))
    st.session_state.remember_login = bool(remember)
    st.session_state._auth_last_activity = moscow_now()
    # One signed-by-randomness bearer cookie; server-side record limits it to 60 minutes
    # of inactivity. The browser cookie can persist, but an expired server session cannot.
    cookie_manager.set(
        "auth_token", token,
        expires_at=moscow_now().replace(microsecond=0) + timedelta(days=3650 if remember else 1),
        key="set_auth_token_cookie",
    )
    # This cookie selects the PIN screen on this browser. It contains only the
    # login identifier, never the PIN or password; authentication still requires
    # the valid auth_token or a correct PIN.
    if remember:
        cookie_manager.set(
            "remembered_user", str(user.get("login", "")),
            expires_at=moscow_now().replace(microsecond=0) + timedelta(days=3650),
            key="set_remembered_user_cookie",
        )
    else:
        try:
            cookie_manager.delete("remembered_user")
        except Exception:
            pass


def _passkey_b64url_encode(value):
    return base64.urlsafe_b64encode(bytes(value)).decode("ascii").rstrip("=")


def _passkey_b64url_decode(value):
    value = str(value or "")
    return base64.urlsafe_b64decode(value + ("=" * (-len(value) % 4)))


def _passkey_user_id(login):
    # Stable opaque WebAuthn user ID; does not expose the user's login as userHandle.
    return hashlib.sha256(("iplinth-crm:" + str(login)).encode("utf-8")).digest()


def _passkey_find_user_and_credential(credential_id):
    for user in st.session_state.crm_store.get("users", []):
        for item in user.get("passkeys", []):
            if not isinstance(item, dict):
                continue
            saved_id = str(item.get("credential_id", ""))
            if saved_id and secrets.compare_digest(saved_id, str(credential_id or "")):
                return user, item
    return None, None


def _passkey_make_authentication_pending():
    options = generate_authentication_options(
        rp_id=PASSKEY_RP_ID,
        user_verification=UserVerificationRequirement.REQUIRED,
        timeout=60000,
    )
    return {
        "kind": "login",
        "challenge": _passkey_b64url_encode(options.challenge),
        "options_json": options_to_json(options),
        "event_id": secrets.token_urlsafe(18),
        "created_at": moscow_now().isoformat(timespec="seconds"),
    }


def _passkey_make_registration_pending(user):
    options = generate_registration_options(
        rp_id=PASSKEY_RP_ID,
        rp_name=PASSKEY_RP_NAME,
        user_id=_passkey_user_id(user.get("login", "")),
        user_name=str(user.get("login", "user")),
        user_display_name=str(user.get("name", user.get("login", "user"))),
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        timeout=60000,
    )
    return {
        "kind": "register",
        "challenge": _passkey_b64url_encode(options.challenge),
        "options_json": options_to_json(options),
        "event_id": secrets.token_urlsafe(18),
        "login": str(user.get("login", "")),
        "created_at": moscow_now().isoformat(timespec="seconds"),
    }


def _passkey_pending_is_fresh(pending):
    try:
        created = datetime.fromisoformat(str(pending.get("created_at", "")))
        return moscow_now() - created <= timedelta(minutes=2)
    except (TypeError, ValueError):
        return False


def _passkey_create_login_session(user):
    # Same server-side session model as password login; each device receives its own token.
    token = secrets.token_urlsafe(32)
    sessions = user.setdefault("auth_sessions", [])
    if not isinstance(sessions, list):
        sessions = []
        user["auth_sessions"] = sessions
    sessions.append({
        "token_hash": hashlib.sha256(token.encode("utf-8")).hexdigest(),
        "created_at": now_str(),
        "expires_at": (moscow_now() + timedelta(minutes=60)).isoformat(timespec="seconds"),
    })
    user.pop("auth_token", None)
    # Limit unbounded growth while keeping recent device sessions.
    user["auth_sessions"] = sessions[-30:]
    save_data(st.session_state.crm_store)
    st.session_state.authenticated = True
    st.session_state.user_role = user.get("role")
    st.session_state.user_login = user.get("login")
    st.session_state.user_name = user.get("name", user.get("login", ""))
    st.session_state.remember_login = True
    st.session_state._auth_last_activity = moscow_now()
    cookie_manager.set(
        "auth_token", token,
        expires_at=moscow_now().replace(microsecond=0) + timedelta(days=3650),
        key="set_auth_token_cookie",
    )
    cookie_manager.set(
        "remembered_user", str(user.get("login", "")),
        expires_at=moscow_now().replace(microsecond=0) + timedelta(days=3650),
        key="set_remembered_user_cookie",
    )


def _passkey_process_login_result(result, pending):
    if not isinstance(result, dict) or not pending:
        return False
    if result.get("eventId") != pending.get("event_id") or result.get("action") != "login":
        return False
    try:
        if not _passkey_pending_is_fresh(pending):
            raise ValueError("Срок действия запроса истёк. Нажмите кнопку входа ещё раз.")
        if result.get("error"):
            raise ValueError(str(result.get("error"))[:300])
        credential = result.get("credential")
        if not isinstance(credential, dict):
            raise ValueError("Браузер не вернул данные Passkey.")
        user, passkey = _passkey_find_user_and_credential(credential.get("id", ""))
        if not user or not passkey:
            raise ValueError("Этот Passkey не зарегистрирован в CRM.")
        verified = verify_authentication_response(
            credential=credential,
            expected_challenge=_passkey_b64url_decode(pending["challenge"]),
            expected_rp_id=PASSKEY_RP_ID,
            expected_origin=PASSKEY_ORIGIN,
            credential_public_key=_passkey_b64url_decode(passkey["public_key"]),
            credential_current_sign_count=int(passkey.get("sign_count", 0)),
            require_user_verification=True,
        )
        if not getattr(verified, "user_verified", True):
            raise ValueError("Устройство не подтвердило пользователя.")
        passkey["sign_count"] = int(getattr(verified, "new_sign_count", passkey.get("sign_count", 0)))
        passkey["last_used_at"] = now_str()
        _passkey_create_login_session(user)
        st.session_state.pop("_passkey_login_pending", None)
        st.session_state["_passkey_login_message"] = ""
        st.rerun()
    except Exception as exc:
        st.session_state.pop("_passkey_login_pending", None)
        st.session_state["_passkey_login_message"] = f"Не удалось войти по Passkey: {str(exc)[:250]}"
        st.rerun()
    return True


def _passkey_process_registration_result(result, pending, current_user):
    if not isinstance(result, dict) or not pending:
        return False
    if result.get("eventId") != pending.get("event_id") or result.get("action") != "register":
        return False
    try:
        if not _passkey_pending_is_fresh(pending):
            raise ValueError("Срок действия запроса истёк. Попробуйте добавить Passkey ещё раз.")
        if result.get("error"):
            raise ValueError(str(result.get("error"))[:300])
        credential = result.get("credential")
        if not isinstance(credential, dict):
            raise ValueError("Браузер не вернул данные Passkey.")
        verified = verify_registration_response(
            credential=credential,
            expected_challenge=_passkey_b64url_decode(pending["challenge"]),
            expected_rp_id=PASSKEY_RP_ID,
            expected_origin=PASSKEY_ORIGIN,
            require_user_verification=True,
        )
        registration_info = verified
        credential_id = _passkey_b64url_encode(registration_info.credential_id)
        public_key = _passkey_b64url_encode(registration_info.credential_public_key)
        current_user.setdefault("passkeys", [])
        if not isinstance(current_user["passkeys"], list):
            current_user["passkeys"] = []
        if any(isinstance(p, dict) and p.get("credential_id") == credential_id for p in current_user["passkeys"]):
            raise ValueError("Этот Passkey уже добавлен.")
        current_user["passkeys"].append({
            "credential_id": credential_id,
            "public_key": public_key,
            "sign_count": int(registration_info.sign_count),
            "created_at": now_str(),
            "label": "Passkey / Face ID",
        })
        save_data(st.session_state.crm_store)
        st.session_state.pop("_passkey_register_pending", None)
        st.session_state["_passkey_register_message"] = "Passkey успешно добавлен. Теперь можно входить с Face ID, Touch ID или кодом устройства."
        st.rerun()
    except Exception as exc:
        st.session_state.pop("_passkey_register_pending", None)
        st.session_state["_passkey_register_message"] = f"Не удалось добавить Passkey: {str(exc)[:250]}"
        st.rerun()
    return True


cookie_manager = stx.CookieManager()
cookies = cookie_manager.get_all()

# Авторизация по cookie без токена в URL. Поддерживаем старый auth_token
# для плавного обновления существующих установок и новые независимые сеансы устройств.
def _user_has_auth_token(user, token):
    if not token:
        return False
    if secrets.compare_digest(str(user.get("auth_token", "")), str(token)):
        return True
    token_hash = hashlib.sha256(str(token).encode("utf-8")).hexdigest()
    for auth_session in user.get("auth_sessions", []):
        if isinstance(auth_session, dict):
            saved_hash = auth_session.get("token_hash", "")
            saved_token = auth_session.get("token", "")  # совместимость с ранними тестовыми/старыми записями
            expires_at = auth_session.get("expires_at")
            if expires_at:
                try:
                    if datetime.fromisoformat(str(expires_at)) < moscow_now():
                        continue
                except (TypeError, ValueError):
                    continue
            if saved_hash and secrets.compare_digest(str(saved_hash), token_hash):
                return True
        else:
            saved_token = auth_session
        if saved_token and secrets.compare_digest(str(saved_token), str(token)):
            return True
    return False

_auth_token = cookies.get("auth_token")
_remembered_login = str(cookies.get("remembered_user") or "").strip()
if st.session_state.get("_force_password_login"):
    _remembered_login = ""

# Restore a valid browser session after refresh/reopen. Server-side expiry is sliding:
# it is extended only while the user is active, and inactivity over 60 minutes expires it.
if _auth_token and not st.session_state.get("authenticated") and not st.session_state.get("_force_password_login"):
    for _cookie_user in st.session_state.crm_store.get("users", []):
        if _user_has_auth_token(_cookie_user, _auth_token):
            st.session_state.authenticated = True
            st.session_state.user_role = _cookie_user.get("role")
            st.session_state.user_login = _cookie_user.get("login")
            st.session_state.user_name = _cookie_user.get("name", _cookie_user.get("login", ""))
            st.session_state.remember_login = True
            st.session_state._auth_last_activity = moscow_now()
            break

# Периодический скрытый heartbeat удалён: он вызывал автоматические rerun и перерисовку диалогов.

if st.session_state.get("authenticated"):
    _last_activity = st.session_state.get("_auth_last_activity")
    if isinstance(_last_activity, datetime) and moscow_now() - _last_activity >= timedelta(minutes=60):
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_login = None
        st.session_state.user_name = None
        st.session_state.pop("_auth_last_activity", None)
        st.session_state["_auth_expired"] = True
        try:
            cookie_manager.delete("auth_token")
        except Exception:
            pass
    elif _auth_token:
        # Renew expiry only when enough time has passed to avoid a database write per rerun.
        if not isinstance(_last_activity, datetime) or (moscow_now() - _last_activity).total_seconds() >= 60:
            _token_hash = hashlib.sha256(str(_auth_token).encode("utf-8")).hexdigest()
            _expiry_changed = False
            for _active_user in st.session_state.crm_store.get("users", []):
                for _active_session in _active_user.get("auth_sessions", []):
                    if isinstance(_active_session, dict) and secrets.compare_digest(str(_active_session.get("token_hash", "")), _token_hash):
                        _active_session["expires_at"] = (moscow_now() + timedelta(minutes=60)).isoformat(timespec="seconds")
                        _expiry_changed = True
            if _expiry_changed:
                save_data(st.session_state.crm_store)
            st.session_state._auth_last_activity = moscow_now()
    
def _render_it_edit(it):
    """Inline edit form for internal task."""
    show_it_edit = f"show_it_edit_{it['id']}"
    if st.button("Редактировать", key=f"it_edit_btn_{it['id']}", use_container_width=True):
        st.session_state[show_it_edit] = not st.session_state.get(show_it_edit, False)
        st.rerun()
    if st.session_state.get(show_it_edit, False):
        with st.container(border=True):
            eit_topic = st.text_input("Тема:", value=it.get("text", ""), key=f"eit_topic_{it['id']}")
            eit_mgr = st.selectbox("Ответственный:", get_managers_list(), index=0 if it.get("manager", "") not in get_managers_list() else (get_managers_list()).index(it.get("manager", "")), key=f"eit_mgr_{it['id']}", placeholder=MGR_PLACEHOLDER)
            eit_comment = st.text_area("Комментарий:", value=it.get("comment", ""), key=f"eit_comment_{it['id']}")
            if st.button("Сохранить", key=f"eit_save_{it['id']}", type="primary", use_container_width=True):
                if not eit_mgr:
                    st.warning("Выберите ответственного")
                else:
                    it["text"] = eit_topic
                    it["manager"] = eit_mgr
                    it["comment"] = eit_comment
                    it["last_modified"] = now_str()
                    st.session_state[show_it_edit] = False
                    commit_and_rerun(st.session_state.crm_store, "Задача обновлена")

def _render_it_delete(it):
    """Delete button for internal task (admin only)."""
    if st.session_state.user_role == "admin":
        st.markdown("---")
        if st.button("Удалить задачу", key=f"it_del_{it['id']}", use_container_width=True):
            st.session_state.crm_store["internal_tasks"] = [x for x in st.session_state.crm_store.get("internal_tasks", []) if x.get("id") != it.get("id")]
            st.session_state.expanded_task_key = None
            commit_and_rerun(st.session_state.crm_store, "Задача удалена")

@_crm_dialog("Создать внутреннюю задачу", width="medium")
def create_internal_task_dialog():
    st.session_state["_in_dialog"] = True
    _key_prefix = "create_it"
    _close_warning_key = f"_show_close_warning_{_key_prefix}"
    _show_warning = st.session_state.get(_close_warning_key, False)
    # Close button
    _close_css_key = f"close_row_{_key_prefix}"
    st.markdown(f'<style>.st-key-{_close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:6px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{_close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{_close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=_close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("\u2715", key=f"close_btn_{_key_prefix}", use_container_width=True):
                _has_unsaved = (
                    st.session_state.get("it_topic", "").strip() or
                    st.session_state.get("it_comment", "").strip()
                )
                if _has_unsaved and not _show_warning:
                    st.session_state[_close_warning_key] = True
                    st.rerun()
                else:
                    st.session_state.pop("show_it_form", None)
                    st.session_state.pop(_close_warning_key, None)
                    st.session_state["_in_dialog"] = False
                    st.rerun()
    if _show_warning:
        _warn_key = f"unsaved_warn_{_key_prefix}"
        st.markdown(f'<style>.st-key-{_warn_key} {{ border:2px solid #FF9800!important;border-radius:10px!important;background-color:#FFF8E1!important;padding:0.5rem 0.8rem!important;margin:0.3rem 0!important; }}</style>', unsafe_allow_html=True)
        with st.container(key=_warn_key):
            st.markdown("**⚠️ Есть несохранённые изменения**")
            st.markdown("Закрыть без сохранения?")
            _wc1, _wc2 = st.columns(2)
            with _wc1:
                if st.button("Без сохранения", key=f"cdlg_warn_nosave_{_key_prefix}", use_container_width=True):
                    st.session_state[_close_warning_key] = False
                    st.session_state.pop("show_it_form", None)
                    st.session_state["_in_dialog"] = False
                    st.session_state.pop("it_topic", None)
                    st.session_state.pop("it_comment", None)
                    st.rerun()
            with _wc2:
                if st.button("Отмена", key=f"cdlg_warn_cancel_{_key_prefix}", use_container_width=True):
                    st.session_state[_close_warning_key] = False
                    st.rerun()
    internal_tasks = st.session_state.crm_store.setdefault("internal_tasks", [])
    _cu = st.session_state.user_name
    _cu_login = st.session_state.get("user_login", "")
    it_topic = st.text_input("Тема задачи:", key="it_topic")
    it_mgr = st.selectbox("Ответственный:", get_managers_list(), index=None, key="it_mgr", placeholder=MGR_PLACEHOLDER)
    it_comment = st.text_area("Комментарии:", key="it_comment")
    it_files = st.file_uploader("Файлы:", key="it_files_create", accept_multiple_files=True)
    if st.button("Создать", key="it_go", use_container_width=True, type="primary"):
        if not it_topic.strip():
            st.warning("Введите тему задачи")
        else:
            new_it = {
                "id": (max([_safe_id(t.get("id", 0)) for t in internal_tasks], default=0)) + 1,
                "text": it_topic.strip(),
                "done": False,
                "manager": it_mgr or "",
                "comment": it_comment.strip(),
                "created_at": now_str(),
                "created_by": _cu_login,
                "author": _cu,
                "last_modified": now_str(),
                "completed_report": "",
                "it_status": "new",
                "it_files": normalize_file_list(save_uploaded_files(it_files, "internal", "it_file")) if it_files else []
            }
            internal_tasks.append(new_it)
            if it_mgr:
                add_notification(it_mgr, f"Новая внутренняя задача: {it_topic.strip()}", f"\U0001F4DD Новая внутренняя задача: {it_topic.strip()}")
            st.session_state.pop("show_it_form", None)
            st.session_state.pop("it_topic", None)
            st.session_state.pop("it_comment", None)
            commit_and_rerun(st.session_state.crm_store, "Внутренняя задача создана")


@_crm_dialog("Внутренняя задача", width="medium")
def internal_task_detail_dialog(it_id):
    st.session_state["_in_dialog"] = True
    _key_prefix = f"itdlg_{it_id}"
    it = None
    for _it in st.session_state.crm_store.get("internal_tasks", []):
        if _safe_id(_it.get("id", 0)) == it_id:
            it = _it
            break
    if not it:
        st.error("Задача не найдена")
        return
    _cu = st.session_state.user_name
    _cu_login = st.session_state.get("user_login", "")
    _is_admin = st.session_state.user_role == "admin"
    # Close button
    _close_css_key = f"close_row_{_key_prefix}"
    st.markdown(f'<style>.st-key-{_close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:6px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{_close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{_close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=_close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("\u2715", key=f"close_btn_{_key_prefix}", use_container_width=True):
                st.session_state.pop("dialog_it_key", None)
                st.session_state["_in_dialog"] = False
                st.rerun()
    st.markdown(f"**Задача №{it['id']}**")
    st.markdown(format_created_date(it), unsafe_allow_html=True)
    st.markdown("---")
    _it_left, _it_right = st.columns(2)
    with _it_left:
        st.markdown(f"**Тема:** {it.get('text', '')}")
        _mgrs_it = get_managers_list()
        _mgr_it = it.get("manager", "")
        _mgr_idx_it = _mgrs_it.index(_mgr_it) if _mgr_it in _mgrs_it else 0
        _new_mgr_it = st.selectbox("Ответственный:", _mgrs_it, index=_mgr_idx_it, key=f"itdlg_mgr_{it['id']}")
        if _new_mgr_it and _new_mgr_it != _mgr_it:
            it["manager"] = _new_mgr_it
            it["delegated_to"] = _new_mgr_it
            it["it_status"] = "new"
            it["in_work"] = False
            it["last_modified"] = now_str()
            add_notification(_new_mgr_it, f"Вам делегирована внутренняя задача №{it['id']}: {it.get('text', '')}", f"📌 Вам делегирована внутренняя задача №{it['id']}: {it.get('text', '')}")
            commit_and_rerun(st.session_state.crm_store, "Ответственный изменён")
        if it.get("comment"): st.markdown(f"**Комментарий:** {it['comment']}")
        if it.get("completed_report"): st.markdown(f"**Отчёт:** {it['completed_report']}")
        render_reminders("internal_task", it.get("id", ""), f"Внутренняя задача №{it.get('id', '')}", f"it_{it.get('id')}")
    with _it_right:
        render_entity_chat(it, "it", it["id"])
        st.markdown("---")
        st.markdown("**Файлы:**")
        _it_files = it.get("it_files", [])
        if _it_files: render_file_thumbs(_it_files, f"itdlg_files_{it['id']}", allow_delete=True, show_desc=False)
        _it_up = st.file_uploader("Загрузить файлы:", key=f"itdlg_up_{it['id']}", accept_multiple_files=True)
        if st.button("Загрузить", key=f"itdlg_upload_{it['id']}", use_container_width=True):
            if _it_up:
                it.setdefault("it_files", []).extend(normalize_file_list(save_uploaded_files(_it_up, it['id'], "internal")))
                it["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Файлы загружены")
    _status = it.get("it_status", "new")
    if _status == "new":
        if st.button("Взять в работу", key=f"itdlg_take_{it['id']}", type="primary", use_container_width=True):
            # Если задача не назначена, ответственным становится первый сотрудник, взявший её.
            if not it.get("manager"):
                it["manager"] = _cu
                it["delegated_to"] = _cu
            it["it_status"] = "in_work"
            it["in_work"] = True
            it["needs_rework"] = False
            it["last_modified"] = now_str()
            st.session_state.pop("dialog_it_key", None)
            commit_and_rerun(st.session_state.crm_store, "Задача взята в работу")
    elif (_status == "in_work" or it.get("in_work", False)) and not (it.get("done", False) and not it.get("reviewed", False)):
        _show_it_complete = f"show_itdlg_complete_{it['id']}"
        if st.button("Выполнить", key=f"itdlg_complete_btn_{it['id']}", type="primary", use_container_width=True):
            st.session_state[_show_it_complete] = not st.session_state.get(_show_it_complete, False)
            st.rerun()
        if st.session_state.get(_show_it_complete, False):
            _it_report = st.text_area("Отчёт:", key=f"itdlg_report_{it['id']}", height=80)
            if st.button("Подтвердить выполнение", key=f"itdlg_complete_go_{it['id']}", type="primary", use_container_width=True):
                if _it_report.strip():
                    it["done"] = True
                    it["it_status"] = "review"
                    it["in_work"] = False
                    it["completed_report"] = _it_report.strip()
                    it["last_modified"] = now_str()
                    st.session_state[_show_it_complete] = False
                    st.session_state.pop("dialog_it_key", None)
                    commit_and_rerun(st.session_state.crm_store, "Задача отправлена на проверку")
                else:
                    st.warning("Введите отчёт")
        st.markdown("---")
    elif _status == "review" or (it.get("done") and not it.get("reviewed", False)):
        _it_author = it.get("created_by", "") or it.get("author", "")
        _can_review = _is_admin or _it_author == _cu_login or _it_author == _cu
        if _can_review:
            _rc1, _rc2 = st.columns(2)
            with _rc1:
                if st.button("Отправить на доработку", key=f"itdlg_rework_btn_{it['id']}", type="secondary", use_container_width=True):
                    # Возвращаем задачу ответственному в колонку «Новые» и помечаем её.
                    it["done"] = False
                    it["it_status"] = "new"
                    it["in_work"] = False
                    it["reviewed"] = False
                    it["needs_rework"] = True
                    it["last_modified"] = now_str()
                    st.session_state.pop("dialog_it_key", None)
                    _manager = it.get("manager", "")
                    if _manager:
                        add_notification(_manager, f"Задача №{it['id']} отправлена на доработку", f"↩️ Задача №{it['id']} отправлена на доработку")
                    commit_and_rerun(st.session_state.crm_store, "Задача возвращена ответственному на доработку")
            with _rc2:
                if st.button("Проверка выполнена", key=f"itdlg_archive_btn_{it['id']}", type="primary", use_container_width=True):
                    it["reviewed"] = True
                    it["needs_rework"] = False
                    it["it_status"] = "archived"
                    it["last_modified"] = now_str()
                    st.session_state.pop("dialog_it_key", None)
                    commit_and_rerun(st.session_state.crm_store, "Проверка выполнена — задача перемещена в архив")
        else:
            st.info("Ожидает проверки автором задачи")
        st.markdown("---")
    if _is_admin:
        if st.button("Удалить задачу", key=f"itdlg_del_{it['id']}", use_container_width=True):
            st.session_state.crm_store["internal_tasks"] = [x for x in st.session_state.crm_store.get("internal_tasks", []) if _safe_id(x.get("id", 0)) != it_id]
            st.session_state.pop("dialog_it_key", None)
            commit_and_rerun(st.session_state.crm_store, "Задача удалена")



if not st.session_state.authenticated:
        # Не оставляем токены авторизации в адресной строке.
        try:
            if cookies.get("auth_token"):
                cookie_manager.delete("auth_token")
        except (KeyError, TypeError):
            pass

MGR_PLACEHOLDER = "Выбери ответственного"

st.markdown("""<style>.stTextInput > div > div > p, .stNumberInput > div > div > p, .stTextArea > div > div > p { display: none !important; }</style>""", unsafe_allow_html=True)

def check_login(username, password):
    for u in st.session_state.crm_store.get("users", []):
        if u["login"] == username.strip() and verify_password(password, u["password"]):
            st.session_state.authenticated = True
            st.session_state.user_role = u["role"]
            st.session_state.user_login = u["login"]
            st.session_state.user_name = u.get("name", u["login"])
            return True
    return False

if not st.session_state.authenticated:
    if st.session_state.pop("_auth_expired", False):
        st.info("Сессия завершена после 60 минут бездействия. Войдите снова.")
    # A remembered browser is identified by a non-secret login cookie, but must prove
    # knowledge of the PIN on every fresh page session.
    _remembered_user = get_user_by_login(_remembered_login) if _remembered_login else None
    if _remembered_user and isinstance(_remembered_user.get("login_pin"), dict):
        st.markdown("<h2 style='text-align: center; margin-top: 3rem;'>Айплинт CRM</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #7F8C9A; margin-bottom: 2rem;'>Введите PIN-код для входа</p>", unsafe_allow_html=True)
        lc, mc, rc = st.columns([1, 2, 1])
        with mc:
            with st.container(border=True):
                # PIN input is outside a form so Streamlit reruns as the value changes.
                # Verify on every complete candidate length (4–8 digits) and sign in
                # immediately when the entered PIN matches, including on iPhone.
                _pin_input = st.text_input(
                    "PIN-код:", type="default", max_chars=8,
                    placeholder="Введите PIN-код", key="remembered_pin_input",
                    help="Введите PIN из 4–8 цифр. При правильном PIN вход выполнится автоматически."
                )
                st.markdown("""<style>
                .st-key-remembered_pin_input input {
                    -webkit-text-security: disc !important;
                    text-security: disc !important;
                }
                </style>""", unsafe_allow_html=True)
                st.markdown("""<script>
                (function(){
                  function tunePin(){
                    const inputs = parent.document.querySelectorAll('input[placeholder="Введите PIN-код"]');
                    inputs.forEach(function(el){
                      el.setAttribute('inputmode','numeric');
                      el.setAttribute('pattern','[0-9]*');
                      el.setAttribute('enterkeyhint','go');
                      el.setAttribute('autocomplete','off');
                      el.setAttribute('name','crm_pin_code');
                      el.setAttribute('data-lpignore','true');
                      el.setAttribute('data-1p-ignore','true');
                      el.setAttribute('spellcheck','false');
                    });
                  }
                  tunePin();
                  const root = parent.document.querySelector('[data-testid="stAppViewContainer"]') || parent.document.body;
                  if (root && !root.__pinInputModeObserver) {
                    root.__pinInputModeObserver = new MutationObserver(tunePin);
                    root.__pinInputModeObserver.observe(root, {childList:true, subtree:true});
                  }
                })();
                </script>""", unsafe_allow_html=True)
                _pin_submit = st.button(
                    "Войти по PIN-коду", use_container_width=True, type="primary",
                    key="remembered_pin_login_btn",
                )
                _pin_attempt = bool(_pin_input and re.fullmatch(r"\d{4,8}", _pin_input or ""))
                if _pin_attempt and _pin_verify(_remembered_user, _pin_input):
                    _create_browser_session(_remembered_user, remember=True)
                    st.toast("Успешный вход", icon="🔓")
                    st.rerun()
                elif _pin_submit:
                    if _pin_verify(_remembered_user, _pin_input):
                        _create_browser_session(_remembered_user, remember=True)
                        st.toast("Успешный вход", icon="🔓")
                        st.rerun()
                    else:
                        st.error("Неверный PIN-код.")
                if st.button("Войти по логину и паролю", use_container_width=True, key="switch_to_password_login"):
                    try:
                        cookie_manager.delete("remembered_user")
                        cookie_manager.delete("auth_token")
                    except Exception:
                        pass
                    st.session_state["_force_password_login"] = True
                    st.session_state.pop("remembered_pin_input", None)
                    st.rerun()
        # Keep Face ID / Passkey available even when this browser is remembered for PIN login.
        st.markdown("---")
        st.markdown("**Или войдите по Face ID / Passkey**")
        if st.session_state.get("_passkey_login_message"):
            st.warning(st.session_state.pop("_passkey_login_message"))
        if not PASSKEY_AVAILABLE:
            st.info("Вход по Face ID пока недоступен: проверьте зависимость `webauthn>=2.2,<3` и повторную публикацию приложения.")
        else:
            _pin_pk_pending = st.session_state.get("_passkey_login_pending")
            if not _pin_pk_pending or not _passkey_pending_is_fresh(_pin_pk_pending):
                try:
                    _pin_pk_pending = _passkey_make_authentication_pending()
                    st.session_state["_passkey_login_pending"] = _pin_pk_pending
                except Exception as _pin_pk_exc:
                    _pin_pk_pending = None
                    st.warning(f"Не удалось подготовить вход по Face ID: {str(_pin_pk_exc)[:180]}")
            if _pin_pk_pending:
                _pin_pk_result = crm_passkey_component(
                    mode="login",
                    options_json=_pin_pk_pending["options_json"],
                    event_id=_pin_pk_pending["event_id"],
                    button_label="Войти с Face ID / Passkey",
                    key="crm_passkey_login_component_remembered",
                    default=None,
                )
                _passkey_process_login_result(_pin_pk_result, _pin_pk_pending)
        st.stop()

    st.markdown("<h2 style='text-align: center; margin-top: 3rem;'>Айплинт CRM</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #7F8C9A; margin-bottom: 2rem;'>Авторизуйтесь для входа в систему</p>", unsafe_allow_html=True)
    lc, mc, rc = st.columns([1, 2, 1])
    with mc:
        with st.container(border=True):
            iu = st.text_input("Логин:", placeholder="Введите логин", key="login_username")
            ip = st.text_input("Пароль:", type="password", placeholder="Введите пароль", key="login_password")
            remember_login = st.checkbox("Запомнить меня в этом браузере", value=False, key="remember_login_checkbox")
            if remember_login:
                st.caption("Сессия действует до 60 минут бездействия. При активности CRM продлевает сессию автоматически.")
                _new_pin = st.text_input("Создайте PIN-код (4–8 цифр):", type="password", max_chars=8, key="new_login_pin")
                _confirm_pin = st.text_input("Повторите PIN-код:", type="password", max_chars=8, key="confirm_login_pin")
            else:
                _new_pin = _confirm_pin = ""
            if st.button("Войти", use_container_width=True, type="primary"):
                try:
                    _user_for_login = next((u for u in st.session_state.crm_store.get("users", []) if u.get("login") == iu.strip()), None)
                    if _user_for_login and verify_password(ip, _user_for_login.get("password", "")):
                        if remember_login and (not re.fullmatch(r"\d{4,8}", _new_pin or "") or _new_pin != _confirm_pin):
                            st.error("Для запоминания браузера задайте одинаковый PIN-код из 4–8 цифр.")
                        else:
                            st.session_state.pop("_force_password_login", None)
                            if remember_login:
                                _user_for_login["login_pin"] = _pin_hash(_new_pin)
                                # Persist the PIN hash before issuing cookies/session.
                                save_data(st.session_state.crm_store)
                                # The auth_token cookie remembers this browser; no separate login cookie is needed.
                            else:
                                try:
                                    cookie_manager.delete("remembered_user")
                                except Exception:
                                    pass
                            _create_browser_session(_user_for_login, remember=bool(remember_login))
                            time.sleep(0.3)
                            st.toast("Успешный вход", icon="🔓")
                            st.rerun()
                    else:
                        st.error("Неверный логин или пароль.")
                except Exception as _login_exc:
                    st.error(f"Не удалось завершить вход. Ошибка: {type(_login_exc).__name__}: {str(_login_exc)[:240]}")
                    st.caption("Попробуйте ещё раз. Если ошибка повторится, пришлите этот текст — он поможет исправить причину.")
    st.markdown("---")
    st.markdown("**Или войдите без пароля**")
    if st.session_state.get("_passkey_login_message"):
        st.warning(st.session_state.pop("_passkey_login_message"))
    if not PASSKEY_AVAILABLE:
        st.info("Вход по Face ID пока не подключён: добавьте зависимость `webauthn>=2.2,<3` в requirements.txt и опубликуйте приложение заново.")
    else:
        _pk_pending = st.session_state.get("_passkey_login_pending")
        if not _pk_pending or not _passkey_pending_is_fresh(_pk_pending):
            try:
                _pk_pending = _passkey_make_authentication_pending()
                st.session_state["_passkey_login_pending"] = _pk_pending
            except Exception as _pk_exc:
                _pk_pending = None
                st.caption(f"Вход по Passkey временно недоступен: {str(_pk_exc)[:180]}")
        if _pk_pending:
            _pk_result = crm_passkey_component(
                mode="login",
                options_json=_pk_pending["options_json"],
                event_id=_pk_pending["event_id"],
                button_label="Войти с Face ID / Passkey",
                key="crm_passkey_login_component",
                default=None,
            )
            _passkey_process_login_result(_pk_result, _pk_pending)
    st.stop()

process_due_reminders()

# Главная шапка: уведомления слева, приветствие по центру, дата и часы справа.
# Выравниваем кнопку боковой панели и уведомлений по одной высоте; увеличиваем сам символ.
st.markdown("""<style>
/* Streamlit places a keyed wrapper around each widget; target both wrapper and actual button. */
.st-key-crm_sidebar_toggle_btn,
.st-key-crm_sidebar_toggle_btn [data-testid="stButton"],
.st-key-crm_sidebar_toggle_btn > div {
    align-self: center !important;
    width: 100% !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding-top: 0 !important;
}
.st-key-crm_sidebar_toggle_btn [data-testid="stButton"] > button,
.st-key-crm_sidebar_toggle_btn button {
    width: 22px !important;
    min-width: 22px !important;
    max-width: 22px !important;
    height: 22px !important;
    min-height: 22px !important;
    max-height: 22px !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
    line-height: 1 !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    background: transparent !important;
}
.st-key-crm_sidebar_toggle_btn button:hover,
.st-key-crm_sidebar_toggle_btn button:focus,
.st-key-crm_sidebar_toggle_btn button:active {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    background: transparent !important;
}
.st-key-crm_sidebar_toggle_btn button p,
.st-key-crm_sidebar_toggle_btn button span {
    font-size: 1.175rem !important;
    font-weight: 700 !important;
    line-height: 1 !important;
    margin: 0 !important;
    padding: 0 !important;
}
/* Match the notification button's height so the two controls align exactly. */
.st-key-crm_bell_wrap [data-testid="stButton"] > button {
    height: 44px !important;
    min-height: 44px !important;
    max-height: 44px !important;
    box-sizing: border-box !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}
.st-key-crm_bell_wrap [data-testid="stButton"] > button p {
    line-height: 1 !important;
}
</style>""", unsafe_allow_html=True)
_header_left, _header_center, _header_right = st.columns([1.35, 4, 1.35], vertical_alignment="center")
with _header_left:
    _toggle_col, _bell_col = st.columns([0.32, 1], vertical_alignment="center")
    with _toggle_col:
        _sidebar_icon = "☰" if not st.session_state.get("_crm_sidebar_visible", True) else "‹"
        if st.button(_sidebar_icon, key="crm_sidebar_toggle_btn", use_container_width=True):
            st.session_state["_crm_sidebar_visible"] = not st.session_state.get("_crm_sidebar_visible", True)
            st.rerun()
    with _bell_col:
        render_notifications_bell()
with _header_center:
    # Заголовок визуально остаётся обычным h1; клик запускает загрузку сохранённых данных.
    st.markdown("""<style>
    .st-key-crm_refresh_db_title,
    .st-key-crm_refresh_db_title > div,
    .st-key-crm_refresh_db_title [data-testid="stButton"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        background: transparent !important;
        border: 0 !important;
        box-shadow: none !important;
    }
    .st-key-crm_refresh_db_title [data-testid="stButton"] > button,
    .st-key-crm_refresh_db_title button {
        -webkit-appearance: none !important;
        appearance: none !important;
        display: block !important;
        width: auto !important;
        min-height: 0 !important;
        height: auto !important;
        margin: 0 auto !important;
        padding: 0 !important;
        border: 0 !important;
        border-radius: 0 !important;
        outline: none !important;
        box-shadow: none !important;
        background: transparent !important;
        color: var(--text-color) !important;
        font-family: inherit !important;
        font-size: 3.5rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        text-align: center !important;
        text-decoration: none !important;
        cursor: pointer !important;
        white-space: nowrap !important;
    }
    .st-key-crm_refresh_db_title [data-testid="stButton"] > button:hover,
    .st-key-crm_refresh_db_title [data-testid="stButton"] > button:focus,
    .st-key-crm_refresh_db_title [data-testid="stButton"] > button:active {
        background: transparent !important;
        color: var(--text-color) !important;
        border: 0 !important;
        outline: none !important;
        box-shadow: none !important;
        text-decoration: none !important;
        transform: none !important;
    }
    .st-key-crm_refresh_db_title [data-testid="stButton"] > button,
    .st-key-crm_refresh_db_title [data-testid="stButton"] > button p,
    .st-key-crm_refresh_db_title [data-testid="stButton"] > button span,
    .st-key-crm_refresh_db_title [data-testid="stButton"] > button div {
        font-family: inherit !important;
        font-size: 3.5rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        margin: 0 !important;
        padding: 0 !important;
        color: inherit !important;
        text-decoration: none !important;
    }
    [class*="crm_refresh_db_title"] button,
    [class*="crm_refresh_db_title"] button *,
    [class*="crm_refresh_db_title"] [data-testid="stMarkdownContainer"],
    [class*="crm_refresh_db_title"] p,
    [class*="crm_refresh_db_title"] span,
    [class*="crm_refresh_db_title"] div {
        font-size: 3.5rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
    }
    </style>""", unsafe_allow_html=True)
    if st.button("Айплинт CRM", key="crm_refresh_db_title"):
        with st.spinner("⟳ Обновляем базу данных…"):
            st.session_state.crm_store = load_data()
        st.toast("База данных обновлена", icon="🔄")
    st.markdown(
        f'<p style="text-align:center;color:#7F8C9A;font-size:0.95rem;margin:0!important;padding:0!important;">Продуктивного тебе дня, {html.escape(str(st.session_state.user_name))} 😊</p>',
        unsafe_allow_html=True,
    )
with _header_right:
    components.html("""
    <div id="crm-live-clock" style="text-align:center;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#5A6B7D;white-space:nowrap;width:100%;">
      <div id="crm-live-date" style="font-size:0.82rem;color:#7F8C9A;"></div>
      <div id="crm-live-time" style="font-size:1.15rem;font-weight:700;font-variant-numeric:tabular-nums;"></div>
    </div>
    <script>
    (function(){
      function updateClock(){
        const now = new Date(new Date().toLocaleString('en-US', {timeZone:'Europe/Moscow'}));
        const pad = n => String(n).padStart(2,'0');
        document.getElementById('crm-live-date').textContent =
          pad(now.getDate())+'.'+pad(now.getMonth()+1)+'.'+now.getFullYear();
        document.getElementById('crm-live-time').textContent =
          pad(now.getHours())+':'+pad(now.getMinutes())+':'+pad(now.getSeconds());
      }
      updateClock();
      setInterval(updateClock, 1000);
    })();
    </script>
    """, height=48, scrolling=False)

with st.sidebar:
    if st.session_state.cloud_ok: st.success("Облако активно")
    else: st.warning("Облако недоступно (работа локально)")
    st.markdown("---")
    st.markdown(f"**{st.session_state.user_name}**")
    st.markdown(f"Роль: `{st.session_state.user_role}`")
    with st.expander("Вход по Face ID / Passkey"):
        if not PASSKEY_AVAILABLE:
            st.warning("Для Passkeys добавьте `webauthn>=2.2,<3` в requirements.txt и опубликуйте приложение заново.")
        else:
            _pk_current_user = next((u for u in st.session_state.crm_store.get("users", []) if u.get("login") == st.session_state.get("user_login")), None)
            if _pk_current_user is not None:
                _pk_existing = _pk_current_user.get("passkeys", [])
                if not isinstance(_pk_existing, list):
                    _pk_existing = []
                st.caption(f"Подключено ключей доступа: {len(_pk_existing)}")
                st.caption("На iPhone система предложит Face ID, Touch ID или код-пароль устройства. Код не хранится в CRM.")
                if st.session_state.get("_passkey_register_message"):
                    st.success(st.session_state.pop("_passkey_register_message"))
                _pk_reg_pending = st.session_state.get("_passkey_register_pending")
                if not _pk_reg_pending or _pk_reg_pending.get("login") != st.session_state.get("user_login") or not _passkey_pending_is_fresh(_pk_reg_pending):
                    try:
                        _pk_reg_pending = _passkey_make_registration_pending(_pk_current_user)
                        st.session_state["_passkey_register_pending"] = _pk_reg_pending
                    except Exception as _pk_reg_exc:
                        _pk_reg_pending = None
                        st.caption(f"Не удалось подготовить Passkey: {str(_pk_reg_exc)[:180]}")
                if _pk_reg_pending:
                    _pk_reg_result = crm_passkey_component(
                        mode="register",
                        options_json=_pk_reg_pending["options_json"],
                        event_id=_pk_reg_pending["event_id"],
                        button_label="Добавить Face ID / Passkey",
                        key="crm_passkey_register_component",
                        default=None,
                    )
                    _passkey_process_registration_result(_pk_reg_result, _pk_reg_pending, _pk_current_user)
    with st.expander("Сменить пароль"):
        cul = st.session_state.user_login
        np = st.text_input("Новый пароль:", type="password", key="self_new_pwd")
        cp = st.text_input("Повторите пароль:", type="password", key="self_conf_pwd")
        if st.button("Обновить", key="btn_save_self_pwd", use_container_width=True):
            if np and np == cp:
                _new_token = secrets.token_urlsafe(32)
                for u in st.session_state.crm_store["users"]:
                    if u["login"] == cul:
                        u["password"] = hash_password(np)
                        # При смене пароля отзываем старые устройства и создаём
                        # новый сеанс только для текущего браузера.
                        u.pop("auth_token", None)
                        u["auth_sessions"] = [{
                            "token_hash": hashlib.sha256(_new_token.encode("utf-8")).hexdigest(),
                            "created_at": now_str(),
                            "expires_at": (moscow_now() + timedelta(minutes=60)).isoformat(timespec="seconds"),
                        }]
                save_data(st.session_state.crm_store)
                cookie_manager.set(
                    "auth_token", _new_token,
                    expires_at=moscow_now().replace(microsecond=0) + timedelta(days=3650 if st.session_state.get("remember_login", False) else 1),
                    key="set_auth_token_cookie",
                )
                st.toast("Пароль изменён", icon="✅")
                st.rerun()
            else: st.error("Пароли не совпадают")
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
                    else: st.error("Логин уже занят")
                else: st.error("Заполните все поля")
            st.markdown("---")
            for u in st.session_state.crm_store.get("users", []):
                ucl, ucr = st.columns([3, 1])
                with ucl: st.markdown(f"**{u.get('name', u['login'])}** ({u['role']})")
                with ucr:
                    if u["login"] != st.session_state.user_login:
                        if st.button("X", key=f"del_u_{u['login']}"):
                            st.session_state.crm_store["users"] = [x for x in st.session_state.crm_store["users"] if x["login"] != u["login"]]
                            commit_and_rerun(st.session_state.crm_store, "Сотрудник удалён")
    with st.expander("Telegram уведомления"):
        st.markdown("Введите Chat ID для push-уведомлений в Telegram")
        st.caption("Узнать Chat ID: @userinfobot в Telegram")
        tg_id = st.text_input("Chat ID:", value=str(get_user_by_login(st.session_state.user_login).get("telegram_chat_id", "")) if get_user_by_login(st.session_state.user_login) else "", key="tg_chat_id_input")
        if st.button("Сохранить", key="btn_save_tg", use_container_width=True, type="primary"):
            u = get_user_by_login(st.session_state.user_login)
            if u:
                u["telegram_chat_id"] = tg_id.strip()
                save_data(st.session_state.crm_store)
                st.toast("Chat ID сохранён", icon="✅")
                st.rerun()
    st.markdown("---")
    if st.button("Выйти", use_container_width=True):
        _tok = cookies.get("auth_token")
        if _tok:
            _changed = False
            for u in st.session_state.crm_store.get("users", []):
                old_sessions = u.get("auth_sessions", [])
                if isinstance(old_sessions, list):
                    new_sessions = []
                    for auth_session in old_sessions:
                        if isinstance(auth_session, dict):
                            saved_hash = auth_session.get("token_hash", "")
                            saved_token = auth_session.get("token", "")
                            token_hash = hashlib.sha256(str(_tok).encode("utf-8")).hexdigest()
                            matches = bool(saved_hash and secrets.compare_digest(str(saved_hash), token_hash)) or bool(saved_token and secrets.compare_digest(str(saved_token), str(_tok)))
                        else:
                            matches = bool(auth_session and secrets.compare_digest(str(auth_session), str(_tok)))
                        if matches:
                            _changed = True
                        else:
                            new_sessions.append(auth_session)
                    if len(new_sessions) != len(old_sessions):
                        u["auth_sessions"] = new_sessions
                if u.get("auth_token") and secrets.compare_digest(str(u.get("auth_token")), str(_tok)):
                    u.pop("auth_token", None)
                    _changed = True
            if _changed:
                save_data(st.session_state.crm_store)
        try:
            cookie_manager.delete("auth_token")
            cookie_manager.delete("remembered_user")
        except Exception:
            pass
        st.session_state["_force_password_login"] = True
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_login = None
        st.session_state.user_name = None
        st.session_state.remember_login = False
        st.session_state.pop("_auth_last_activity", None)
        st.rerun()

# Compute counters for tabs — only by authorized user
_cu_login_count = st.session_state.get("user_login", "")
_cu_name_count = st.session_state.get("user_name", "")
_new_deals_count = sum(1 for d in st.session_state.crm_store.get("deals", []) if d.get("status", "Новый") == "Новый" and (d.get("manager", "") == _cu_name_count or st.session_state.get("user_role") == "admin"))
_new_tasks_count = 0
for _c in st.session_state.crm_store.get("clients", []):
    for _t in _c.get("tasks", []):
        if not _t.get("done", False) and not _t.get("in_work", False):
            _tm = _t.get("manager", "")
            _dtm = _t.get("delegated_to", "")
            if _tm == _cu_name_count or _dtm == _cu_name_count or st.session_state.get("user_role") == "admin":
                _new_tasks_count += 1
_new_it_count = sum(1 for it in st.session_state.crm_store.get("internal_tasks", []) if not it.get("done", False) and it.get("it_status", "new") == "new" and (not it.get("manager") or it.get("manager", "") == _cu_name_count or st.session_state.get("user_role") == "admin"))

# Reset modal request tracking before any shared UI can request a dialog.
st.session_state["_crm_dialog_requested_this_run"] = False

nc1, nc2, nc3, nc4, nc5, nc6 = st.columns(6)
with nc1:
    if st.button("Клиенты", use_container_width=True, type="primary" if st.session_state.active_tab == "Клиенты" else "secondary"):
        st.session_state.active_tab = "Клиенты"
        st.session_state["_dialog_return_stack"] = []
        st.session_state.expanded_task_key = None
        st.session_state.pop("dialog_task_key", None)
        st.session_state.pop("_open_created_task", None)
        st.session_state.pop("dialog_deal_key", None)
        st.session_state.pop("_open_created_deal", None)
        st.rerun()
with nc2:
    _deals_label = f"Сделки ({_new_deals_count})" if _new_deals_count > 0 else "Сделки"
    if st.button(_deals_label, use_container_width=True, type="primary" if st.session_state.active_tab == "Сделки" else "secondary"):
        st.session_state.active_tab = "Сделки"
        st.session_state["_dialog_return_stack"] = []
        st.session_state.expanded_task_key = None
        st.session_state.pop("dialog_task_key", None)
        st.session_state.pop("_open_created_task", None)
        st.session_state.pop("dialog_deal_key", None)
        st.session_state.pop("_open_created_deal", None)
        st.rerun()
with nc3:
    _tasks_label = f"Задачи ({_new_tasks_count})" if _new_tasks_count > 0 else "Задачи"
    if st.button(_tasks_label, use_container_width=True, type="primary" if st.session_state.active_tab == "Задачи" else "secondary"):
        st.session_state.active_tab = "Задачи"
        st.session_state["_dialog_return_stack"] = []
        st.session_state.expanded_task_key = None
        st.session_state.pop("dialog_task_key", None)
        st.session_state.pop("_open_created_task", None)
        st.session_state.pop("dialog_deal_key", None)
        st.session_state.pop("_open_created_deal", None)
        st.rerun()
with nc4:
    _it_label = f"Внутренние ({_new_it_count})" if _new_it_count > 0 else "Внутренние"
    if st.button(_it_label, use_container_width=True, type="primary" if st.session_state.active_tab == "Внутренние задачи" else "secondary"):
        st.session_state.active_tab = "Внутренние задачи"
        st.session_state["_dialog_return_stack"] = []
        st.session_state.expanded_task_key = None
        st.session_state.pop("dialog_task_key", None)
        st.session_state.pop("_open_created_task", None)
        st.session_state.pop("dialog_deal_key", None)
        st.session_state.pop("_open_created_deal", None)
        st.rerun()
with nc5:
    if st.button("Поставщики", use_container_width=True, type="primary" if st.session_state.active_tab == "Поставщики" else "secondary"):
        st.session_state.active_tab = "Поставщики"
        st.session_state["_dialog_return_stack"] = []
        st.session_state.expanded_task_key = None
        st.session_state.pop("dialog_task_key", None)
        st.session_state.pop("_open_created_task", None)
        st.session_state.pop("dialog_deal_key", None)
        st.session_state.pop("_open_created_deal", None)
        st.rerun()
with nc6:
    if st.button("Товары и прайс", use_container_width=True, type="primary" if st.session_state.active_tab == "Товары и прайс" else "secondary"):
        st.session_state.active_tab = "Товары и прайс"
        st.session_state["_dialog_return_stack"] = []
        st.session_state.pop("dialog_task_key", None)
        st.session_state.pop("dialog_deal_key", None)
        st.session_state.pop("_open_created_deal", None)
        st.rerun()
st.markdown("---")

# Toast при загрузке если есть непрочитанные
_unread_count = get_unread_count()
if _unread_count > 0 and not st.session_state.get("crm_toast_shown", False):
    st.toast(f"У вас {_unread_count} новых уведомлений", icon="\U0001F514")
    st.session_state["crm_toast_shown"] = True

render_notifications_panel()
render_close_deal_dialog_trigger()

cu = st.session_state.user_name

def render_task_form(deal_id, cl_id, key_suffix, default_type="Связаться"):
    ntype = st.selectbox("Тип задачи:", TASK_TYPES, index=TASK_TYPES.index(default_type) if default_type in TASK_TYPES else 0, key=f"nt_type_{key_suffix}")
    ntopic = st.text_input("Тема задачи:", key=f"nt_topic_{key_suffix}")
    ntm = st.selectbox("Ответственный:", get_managers_list(), index=None, key=f"nt_mgr_{key_suffix}", placeholder=MGR_PLACEHOLDER)
    ntd = st.date_input("Срок:", format="DD.MM.YYYY", key=f"nt_d_{key_suffix}")
    if ntype in ("Отправить заказ", "Отправить образцы"):
        nproducts = st.text_area("Товары:", key=f"nt_prod_{key_suffix}")
        nship_addr = st.text_area("Адрес доставки:", key=f"nt_addr_{key_suffix}")
        nreceiver = st.text_input("Получатель:", key=f"nt_recv_{key_suffix}")
        nreceiver_phone = st.text_input("Телефон получателя:", key=f"nt_rphone_{key_suffix}")
        nship_pay = st.selectbox("Оплата:", SHIP_PAY_OPTIONS, index=0, key=f"nt_pay_{key_suffix}", placeholder="Укажи плательщика")
        norder_amount = st.text_input("Сумма заказа (руб.):", value="", key=f"nt_amount_{key_suffix}", placeholder="Введите сумму")
        ntk_num = st.text_input("Трек:", key=f"nt_tk_{key_suffix}", placeholder="Введите трек-номер")
        ncomment = st.text_area("Комментарии:", key=f"nt_c_{key_suffix}")
        ntf = st.file_uploader("Файлы задачи:", key=f"nt_file_{key_suffix}", accept_multiple_files=True)
    else:
        nproducts = ""
        nship_addr = ""
        nreceiver = ""
        nreceiver_phone = ""
        nship_pay = ""
        norder_amount = ""
        ntk_num = ""
        ncomment = st.text_area("Комментарии:", key=f"nt_c_{key_suffix}")
        ntf = st.file_uploader("Файлы задачи:", key=f"nt_file_{key_suffix}", accept_multiple_files=True)
    if st.button("Создать", key=f"nt_go_{key_suffix}", use_container_width=True, type="primary"):
        if not ntopic.strip():
            st.warning("Введите тему задачи")
        else:
            tfi_list = save_uploaded_files(ntf, cl_id, "task_file") if ntf else []
            prefix = "ЗС" if deal_id else "ЗК"
            tn = generate_task_number(prefix)
            te = {
                "text": ntopic.strip(), "deadline": ntd.isoformat(), "done": False, "type": ntype,
                "task_files": normalize_file_list(tfi_list), "manager": ntm or "",
                "completion_report": "", "completion_files": [],
                "deal_id": deal_id, "task_comment": ncomment.strip(),
                "order_amount": int(norder_amount) if norder_amount and norder_amount.strip().isdigit() else 0, "last_modified": now_str(),
                "task_number": tn, "created_at": now_str(), "created_by": st.session_state.get("user_login", ""),
                "in_work": False, "ready_to_ship": False, "delegated_to": None, "needs_rework": False, "reviewed": False,
                "task_comments": [], "flagged": False,
                "products": nproducts, "ship_addr": nship_addr,
                "receiver": nreceiver, "receiver_phone": nreceiver_phone,
                "ship_pay": nship_pay, "tk_num": ntk_num.strip()
            }
            cl = get_client_by_id(cl_id)
            if cl:
                cl.setdefault("tasks", []).append(te)
                cl["last_modified"] = now_str()
                if deal_id:
                    d = get_deal_by_id(deal_id)
                    if d: d["last_modified"] = now_str()
                if ntm:
                    add_notification(ntm, f"Новая задача: {ntopic.strip()} | Клиент: {cl.get('name','')} | Срок: {ntd.isoformat()}", f"📝 Новая задача: {ntopic.strip()} | Клиент: {cl.get('name','')} | Срок: {ntd.isoformat()}")
                return te
        return False
    return False

def render_deal_card_expanded(d, cl):
    with st.container(border=True):
        st.markdown(f"**{d.get('deal_number', d.get('title', ''))}**")
        st.markdown(format_created_date(d), unsafe_allow_html=True)
        st.markdown(f"**Бюджет:** {d.get('budget', 0):,.0f} руб.".replace(",", " "))
        ps = d.get("payment_status", "Не оплачено")
        inject_payment_container_css(d["id"], ps)
        with st.container(key=f"ps_wrap_{d['id']}"):
            new_ps = st.selectbox("Статус оплаты:", ["Не оплачено", "Оплачено"], index=0 if ps == "Не оплачено" else 1, key=f"ps_{d['id']}")
        if new_ps != ps:
            d["payment_status"] = new_ps
            d["last_modified"] = now_str()
            commit_and_rerun(st.session_state.crm_store, "Статус оплаты обновлён")
        st.markdown("**Ответственный:**")
        mgr_options_cd = get_managers_list()
        current_mgr_cd = d.get("manager", "")
        current_idx_cd = mgr_options_cd.index(current_mgr_cd) if current_mgr_cd in mgr_options_cd else 0
        new_mgr_cd = st.selectbox("Ответственный:", mgr_options_cd, index=current_idx_cd, key=f"card_mgr_inline_{d['id']}", placeholder=MGR_PLACEHOLDER, label_visibility="collapsed")
        if new_mgr_cd != current_mgr_cd and new_mgr_cd:
            d["manager"] = new_mgr_cd
            d["last_modified"] = now_str()
            commit_and_rerun(st.session_state.crm_store, "Ответственный обновлён")
        st.markdown("---")
        dl_files_col, dl_upload_col = st.columns(2)
        with dl_files_col:
            st.markdown("**Файлы сделки:**")
            render_file_thumbs(d.get("deal_files", []), f"deal_file_{d['id']}", allow_delete=True)
        with dl_upload_col:
            st.markdown("**Загрузить файлы:**")
            df_ver = st.session_state.deal_file_uploader_ver.get(d["id"], 0)
            udf = st.file_uploader("Выберите файлы:", key=f"df_up_{d['id']}_{df_ver}", accept_multiple_files=True, label_visibility="collapsed")
            if st.button("Загрузить", key=f"df_btn_{d['id']}", use_container_width=True):
                if udf:
                    with st.spinner("Загрузка файлов..."):
                        fi_list = save_uploaded_files(udf, d["client_id"], "deal_file")
                    if fi_list:
                        d.setdefault("deal_files", []).extend(normalize_file_list(fi_list))
                        d["last_modified"] = now_str()
                        st.session_state.deal_file_uploader_ver[d["id"]] = df_ver + 1
                        save_data(st.session_state.crm_store)
                        st.toast("Файлы загружены", icon="\U0001F4C1")
                        st.rerun()
                else: st.warning("Выберите файл(ы)")
        st.markdown("---")
        if d.get("deal_comments"):
            st.markdown("**Комментарии:**")
            for cm in d["deal_comments"]:
                st.markdown(f"- *{cm.get('time', '')}*: {linkify_text(cm.get('text', ''))}", unsafe_allow_html=True)
        dc_clr_key = f"clr_dc_{d['id']}"
        if st.session_state.get(dc_clr_key):
            st.session_state[f"dc_input_{d['id']}"] = ""
            st.session_state[dc_clr_key] = False
        nc = st.text_area("Добавить комментарий:", key=f"dc_input_{d['id']}", height=90, placeholder="Введите комментарий...")
        if st.button("Добавить", key=f"dc_btn_{d['id']}", use_container_width=True):
            if nc.strip():
                d.setdefault("deal_comments", []).append({"time": moscow_now().strftime("%d.%m.%Y %H:%M"), "text": nc.strip()})
                d["last_modified"] = now_str()
                st.session_state[dc_clr_key] = True
                commit_and_rerun(st.session_state.crm_store, "Комментарий добавлен")
            else: st.warning("Введите текст")
        st.markdown("---")
        render_entity_chat(d, "deal", d["id"])
        st.markdown("---")
        show_edit_deal = st.session_state.get(f"show_edit_deal_{d['id']}", False)
        if show_edit_deal:
            et = st.text_input("Тема:", value=d.get("deal_title", ""), key=f"et_{d['id']}")
            eb = st.text_input("Бюджет (руб.):", value=str(d.get("budget", 0)) if d.get("budget", 0) > 0 else "", key=f"eb_{d['id']}", placeholder="Введите сумму")
            _ces_col, _cec_col = st.columns(2)
            with _ces_col:
                if st.button("Сохранить", key=f"es_{d['id']}", use_container_width=True, type="primary"):
                    d["deal_title"] = et
                    d["budget"] = int(eb) if eb and eb.strip().isdigit() else 0
                    d["last_modified"] = now_str()
                    st.session_state[f"show_edit_deal_{d['id']}"] = False
                    commit_and_rerun(st.session_state.crm_store, "Сделка обновлена")
            with _cec_col:
                if st.button("Отменить", key=f"ec_{d['id']}", use_container_width=True):
                    st.session_state[f"show_edit_deal_{d['id']}"] = False
                    st.rerun()
        else:
            pencil_card_key = f"btn_pencil_card_{d['id']}"
            st.markdown(f"<style>.st-key-{pencil_card_key} button {{ padding: 2px 8px !important; font-size: 0.85rem !important; min-height: 32px !important; }}</style>", unsafe_allow_html=True)
            if st.button("\u270e", key=pencil_card_key):
                st.session_state[f"show_edit_deal_{d['id']}"] = True
                st.rerun()
        st.markdown("---")
        current_status = d.get("status", "Новый")
        if current_status == "Новый":
            if st.button("Взять в работу", key=f"deal_next_{d['id']}", use_container_width=True, type="primary"):
                d["status"] = "В работе"
                if not d.get("manager"): d["manager"] = cu
                d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Сделка взята в работу")
        elif current_status == "В работе":
            if st.button("Закрыть сделку", key=f"deal_close_{d['id']}", use_container_width=True, type="primary"):
                st.session_state["dialog_close_deal_id"] = d["id"]
                st.rerun()
        elif current_status == "Сделка закрыта":
            if st.button("Вернуть в работу", key=f"deal_reopen_{d['id']}", use_container_width=True):
                d["status"] = "В работе"
                d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Сделка возвращена")
            if st.button("В архив", key=f"deal_archive_{d['id']}", use_container_width=True, type="primary"):
                d["status"] = "Архив"
                d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Сделка в архиве")
        elif current_status == "Архив":
            if st.button("Вернуть в работу", key=f"arch_reopen_{d['id']}", use_container_width=True):
                d["status"] = "В работе"
                d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Сделка возвращена")
            if st.button("В закрытые", key=f"arch_toclosed_{d['id']}", use_container_width=True, type="primary"):
                d["status"] = "Сделка закрыта"
                d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Сделка в закрытых")
        if st.session_state.user_role == "admin":
            st.markdown("---")
            if st.button("Удалить сделку", key=f"deal_del_{d['id']}", use_container_width=True):
                st.session_state.crm_store["deals"] = [x for x in st.session_state.crm_store["deals"] if x["id"] != d["id"]]
                st.session_state.expanded_deal_id = None
                commit_and_rerun(st.session_state.crm_store, "Сделка удалена")

def render_deal_in_tree(d, cl):
    is_dl_exp = st.session_state.expanded_deal_id == d["id"] or st.session_state.auto_expand_deal_id == d["id"]
    dl_tasks = [t for t in cl.get("tasks", []) if t.get("deal_id") == d["id"]]
    dl_bg, dl_bc = get_entity_border(dl_tasks)
    dl_label = f"{d.get('deal_number', d.get('title', ''))} ({d['status']}) — {d.get('budget', 0):,.0f} руб. | Задач: {len(dl_tasks)}"
    if d.get("deal_title"):
        dl_label = f"{d.get('deal_number', d.get('title', ''))} — {d['deal_title']} ({d['status']}) — {d.get('budget', 0):,.0f} руб. | Задач: {len(dl_tasks)}"
    dl_selected = is_dl_exp
    dl_border = "#2196F3" if dl_selected else dl_bc
    dl_shadow = "box-shadow: 0 0 0 2px rgba(33,150,243,0.3);" if dl_selected else ""

    with indented(0.03):
        st.markdown(f"<style>.st-key-dl_btn_wrap_{d['id']} button {{ background-color: {dl_bg} !important; color: #2C3E50 !important; border: 2px solid {dl_border} !important; border-radius: 10px !important; {dl_shadow} }}</style>", unsafe_allow_html=True)
        anchor_id = f"deal_anchor_{d['id']}"
        with st.container(key=f"dl_btn_wrap_{d['id']}"):
            if st.button(dl_label, key=f"dl_card_{d['id']}", use_container_width=True, type="primary" if is_dl_exp else "secondary"):
                if is_dl_exp:
                    st.session_state.expanded_deal_id = None
                    save_scroll_and_rerun()
                else:
                    st.session_state.expanded_deal_id = d["id"]
                    st.session_state.expanded_task_key = None
                    st.rerun()
            if not is_dl_exp:
                render_scroll_restore(f"dl_{d['id']}")
        if st.session_state.auto_expand_deal_id == d["id"]:
            st.session_state.auto_expand_deal_id = None
            st.session_state.expanded_deal_id = d["id"]
            st.session_state.scroll_to_deal = anchor_id
        if st.session_state.scroll_to_deal == anchor_id:
            st.markdown(f'<div id="{anchor_id}"></div>', unsafe_allow_html=True)
            st.components.v1.html(f"""<script>setTimeout(function(){{var el=window.parent.document.getElementById('{anchor_id}');if(el)el.scrollIntoView({{behavior:'smooth',block:'center'}});}},300);</script>""", height=0)
            st.session_state.scroll_to_deal = None
        if st.session_state.expanded_deal_id == d["id"]:
            render_deal_card_expanded(d, cl)

        render_centered_title(f"Задачи по сделке ({len(dl_tasks)})")
        with indented(0.03):
            if dl_tasks:
                dl_tasks.sort(key=lambda t: get_sort_key(t), reverse=True)
                for ti, t in enumerate(dl_tasks):
                    task_key = f"dl_{d['id']}_{ti}"
                    render_task_row(t, cl, d, task_key, f"dl_{d['id']}_{ti}")
            show_ct_key = f"show_ct_{d['id']}"
            if render_centered_button("Создать задачу по сделке", key=f"btn_ct_dl_{d['id']}"):
                st.session_state[show_ct_key] = not st.session_state.get(show_ct_key, False)
                st.rerun()
        if st.session_state.get(show_ct_key, False):
            with st.container(border=True):
                if render_task_form(d["id"], d["client_id"], f"deal_{d['id']}"):
                    st.session_state[show_ct_key] = False
                    commit_and_rerun(st.session_state.crm_store, "Задача создана")


def render_deal_standalone(d, cl, cu):
    """Свёрнутая карточка сделки для вкладки «Сделки»."""
    deal_id = d["id"]
    dl_tasks = [t for t in (cl.get("tasks", []) if cl else []) if t.get("deal_id") == deal_id]
    client_name = cl.get("name", "—") if cl else "—"
    num = d.get("deal_number", d.get("title", ""))
    parts = [str(num), client_name]
    if d.get("deal_title"):
        parts.append(d["deal_title"])
    parts.append(f"{d.get('budget', 0):,.0f} руб.".replace(",", " "))
    parts.append(f"Ответственный: {d.get('manager', '—')}")
    parts.append(f"Задач: {len(dl_tasks)}")
    label = " | ".join(parts)
    dl_bg, dl_bc = get_entity_border(dl_tasks)
    st.markdown(f"<style>.st-key-dls_wrap_{deal_id} button {{ background-color: {dl_bg} !important; color: #2C3E50 !important; border: 2px solid {dl_bc} !important; border-radius: 10px !important; white-space: normal !important; height: auto !important; text-align: left !important; }}</style>", unsafe_allow_html=True)
    with st.container(key=f"dls_wrap_{deal_id}"):
        if st.button(label, key=f"dls_btn_{deal_id}", use_container_width=True, type="secondary"):
            st.session_state["dialog_deal_key"] = deal_id
            st.rerun()


def _deal_items_total(items):
    total = 0.0
    for item in items or []:
        qty = max(0.0, float(item.get("quantity", 0) or 0))
        price = max(0.0, float(item.get("unit_price", 0) or 0))
        discount = min(100.0, max(0.0, float(item.get("discount", 0) or 0)))
        total += qty * price * (1 - discount / 100.0)
    return round(total, 2)


def _deal_calc_total(calc):
    return round(_deal_items_total(calc.get("items", [])) + max(0.0, float(calc.get("delivery_amount", 0) or 0)), 2)


def _deal_doc_number(deal):
    """Номер сделки без префикса для названий КП/счёта."""
    raw = str(deal.get("deal_number", deal.get("title", deal.get("id", ""))) or "").strip()
    return re.sub(r"^Сделка\s*№\s*", "", raw, flags=re.IGNORECASE).strip() or raw


def _calculation_display_name(deal, calc, index=None):
    base = f"Расчёт №{_deal_doc_number(deal)}"
    if index is None:
        index = next((i for i, c in enumerate(deal.get("calculations", [])) if str(c.get("id")) == str(calc.get("id"))), 0)
    # First calculation uses the deal number; subsequent calculations are numbered as variants.
    return base if index == 0 else f"{base} — вариант {index + 1}"


def _ensure_calculation_names(deal):
    for i, calc in enumerate(deal.setdefault("calculations", [])):
        if not calc.get("name") or re.match(r"^Расчёт\s+\d+$", str(calc.get("name", "")), re.I):
            calc["name"] = _calculation_display_name(deal, calc, i)


def _money(value):
    try:
        return f"{float(value or 0):,.2f}".replace(",", " ").replace(".", ",")
    except (TypeError, ValueError):
        return "0,00"


def _number_to_russian_words(n):
    """Небольшой конвертер целой части суммы в русские слова для счёта."""
    n = max(0, int(n or 0))
    ones_m = ["ноль", "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
    ones_f = ["ноль", "одна", "две", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
    teens = ["десять", "одиннадцать", "двенадцать", "тринадцать", "четырнадцать", "пятнадцать", "шестнадцать", "семнадцать", "восемнадцать", "девятнадцать"]
    tens = ["", "", "двадцать", "тридцать", "сорок", "пятьдесят", "шестьдесят", "семьдесят", "восемьдесят", "девяносто"]
    hundreds = ["", "сто", "двести", "триста", "четыреста", "пятьсот", "шестьсот", "семьсот", "восемьсот", "девятьсот"]
    def triad(v, feminine=False):
        out=[]
        if v >= 100: out.append(hundreds[v//100])
        x=v%100
        if 10 <= x < 20: out.append(teens[x-10])
        else:
            if x>=20: out.append(tens[x//10])
            u=x%10
            if u: out.append((ones_f if feminine else ones_m)[u])
        return out
    def form(v, one, few, many):
        x=v%100
        if 11 <= x <= 14: return many
        x=v%10
        if x==1: return one
        if 2<=x<=4: return few
        return many
    if n == 0: return "ноль рублей"
    groups=[]
    billions=n//1_000_000_000; millions=(n//1_000_000)%1000; thousands=(n//1000)%1000; rest=n%1000
    if billions: groups += triad(billions) + [form(billions,"миллиард","миллиарда","миллиардов")]
    if millions: groups += triad(millions) + [form(millions,"миллион","миллиона","миллионов")]
    if thousands: groups += triad(thousands, True) + [form(thousands,"тысяча","тысячи","тысяч")]
    if rest: groups += triad(rest)
    groups.append(form(n,"рубль","рубля","рублей"))
    return " ".join(groups)


def _pdf_font_setup():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    candidates = [
        ("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("Liberation", "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
    ]
    for name, regular, bold in candidates:
        if os.path.exists(regular) and os.path.exists(bold):
            try:
                if f"{name}" not in pdfmetrics.getRegisteredFontNames(): pdfmetrics.registerFont(TTFont(name, regular))
                if f"{name}-Bold" not in pdfmetrics.getRegisteredFontNames(): pdfmetrics.registerFont(TTFont(f"{name}-Bold", bold))
                return name, f"{name}-Bold"
            except Exception:
                pass
    return "Helvetica", "Helvetica-Bold"


def _pdf_paragraph(text, style, escape=True):
    from reportlab.platypus import Paragraph
    from reportlab.lib.utils import escape as rl_escape
    value = rl_escape(str(text or "")).replace("\n", "<br/>") if escape else str(text or "")
    return Paragraph(value, style)


def _calculation_rows(calc, catalog):
    pmap = {str(p.get("id", p.get("sku", ""))): p for p in catalog}
    rows=[]
    for item in calc.get("items", []):
        product = pmap.get(str(item.get("product_id", "")), {})
        qty=max(0.0,float(item.get("quantity",0) or 0))
        price=max(0.0,float(item.get("unit_price",product.get("price",0)) or 0))
        discount=min(100.0,max(0.0,float(item.get("discount",0) or 0)))
        after=round(price*(1-discount/100),2)
        amount=round(qty*after,2)
        rows.append({
            "sku": product.get("sku", item.get("sku", item.get("product_id", ""))),
            "name": item.get("product_name", product.get("name", "Товар")),
            "color": item.get("color_ral", ""),
            "spec": product.get("characteristics", product.get("description", "")),
            "unit": item.get("unit", product.get("unit", "шт.")),
            "price": price, "discount": discount, "after": after,
            "quantity": qty, "amount": amount,
        })
    return rows


def _make_commercial_offer_pdf(deal, client, calc):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    font, bold = _pdf_font_setup()
    out=io.BytesIO()
    doc=SimpleDocTemplate(out, pagesize=landscape(A4), rightMargin=10*mm, leftMargin=10*mm, topMargin=9*mm, bottomMargin=10*mm, title=f"Коммерческое предложение №{_deal_doc_number(deal)}")
    styles=getSampleStyleSheet()
    title=ParagraphStyle("OfferTitle", parent=styles["Title"], fontName=bold, fontSize=15, leading=19, alignment=TA_CENTER, textColor=colors.HexColor("#242C36"), spaceAfter=4*mm)
    h=ParagraphStyle("OfferH", parent=styles["Heading2"], fontName=bold, fontSize=9, leading=11, textColor=colors.HexColor("#242C36"), spaceBefore=2*mm, spaceAfter=1.5*mm)
    body=ParagraphStyle("OfferBody", parent=styles["BodyText"], fontName=font, fontSize=7.6, leading=10, spaceAfter=1.2*mm)
    small=ParagraphStyle("OfferSmall", parent=body, fontSize=6.4, leading=8)
    cell=ParagraphStyle("OfferCell", parent=small, fontSize=6.2, leading=7.5)
    cellhead=ParagraphStyle("OfferCellHead", parent=cell, fontName=bold, alignment=TA_CENTER, textColor=colors.white)
    date=moscow_now().date()
    validity=date+timedelta(days=30)
    date_ru=date.strftime("%d.%m.%Y")
    flow=[Paragraph(f"КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ № {html.escape(_deal_doc_number(deal))}", title),
          Paragraph(f"Дата выдачи: {date.strftime('%d.%m.%Y')} &nbsp;&nbsp; Срок действия предложения: 30 дней (до {validity.strftime('%d.%m.%Y')})", body),
          Paragraph("1. СВЕДЕНИЯ О ПОСТАВЩИКЕ", h),
          Paragraph("Наименование организации: ИП Фазлов Дамир Ибрагимович<br/>ИНН: 731701704975<br/>Адрес производства: г. Казань, ул. Кулагина, д. 3<br/>Телефон / Email: +7 (900) 329-33-00 / info@iplinth.ru", body),
          Paragraph(f"Кому: {html.escape(str(client.get('name','') or ''))}", body),
          Paragraph("2. СМЕТА НА ПОСТАВКУ МАТЕРИАЛОВ", h),
          Paragraph("Условия налогообложения: все цены указаны без НДС в связи с применением УСН.", small), Spacer(1, 2*mm)]
    rows=_calculation_rows(calc, st.session_state.crm_store.get("products", DEFAULT_PRODUCT_CATALOG))
    table_data=[[Paragraph(x,cellhead) for x in ["№","Артикул / наименование","Цвет","Технические характеристики","Ед. изм.","Цена","Скидка","Цена со скидкой","Кол-во","Сумма"]]]
    for i,r in enumerate(rows,1):
        item_name=f"<b>{html.escape(str(r['sku']))}</b><br/>{html.escape(str(r['name']))}"
        table_data.append([Paragraph(str(i),cell), Paragraph(item_name,cell), Paragraph(html.escape(str(r['color'] or '—')),cell), Paragraph(html.escape(str(r['spec'] or '—')),cell), Paragraph(html.escape(str(r['unit'] or '')),cell), Paragraph(_money(r['price']),cell), Paragraph(f"{r['discount']:g}%",cell), Paragraph(_money(r['after']),cell), Paragraph(f"{r['quantity']:g}",cell), Paragraph(_money(r['amount']),cell)])
    if not rows:
        table_data.append([Paragraph("—",cell), Paragraph("Товары не добавлены в расчёт",cell), "", "", "", "", "", "", "", ""])
    total=sum(r['amount'] for r in rows)
    delivery=max(0.0,float(calc.get("delivery_amount",0) or 0))
    if delivery:
        table_data.append(["", Paragraph("Доставка",cell), "", "", "", "", "", "", "", Paragraph(_money(delivery),cell)])
    table_data.append(["", "", "", "", "", "", "", "", Paragraph("ИТОГО:",cell), Paragraph(_money(total+delivery),cell)])
    widths=[9*mm,48*mm,17*mm,46*mm,13*mm,20*mm,15*mm,24*mm,14*mm,24*mm]
    tbl=Table(table_data,colWidths=widths,repeatRows=1,hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#343D4A")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#B9C0C9")),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("BACKGROUND",(0,-1),(-1,-1),colors.HexColor("#F1F3F6")),("FONTNAME",(0,-1),(-1,-1),bold),
        ("SPAN",(0,-1),(7,-1)),("ALIGN",(8,1),(-1,-1),"RIGHT"),
    ]))
    flow += [tbl, Spacer(1, 3*mm), Paragraph("3. ДОПОЛНИТЕЛЬНЫЕ УСЛОВИЯ И ХАРАКТЕРИСТИКИ", h),
             Paragraph("• Условия оплаты: 100%.<br/>• Сроки поставки: отгрузка в течение 5 рабочих дней с момента поступления оплаты на расчётный счёт Поставщика.<br/>• При отгрузке предоставляется комплект закрывающих документов (УПД, товарная накладная), а также сертификаты соответствия на продукцию.", body),
             Spacer(1, 2*mm), Paragraph("4. ПОДПИСЬ И ПЕЧАТЬ ПОСТАВЩИКА", h), Paragraph("ИП Фазлов Дамир Ибрагимович", body)]
    doc.build(flow)
    return out.getvalue()


def _make_invoice_pdf(deal, client, calc, requisites):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    font,bold=_pdf_font_setup()
    out=io.BytesIO()
    doc=SimpleDocTemplate(out,pagesize=A4,rightMargin=13*mm,leftMargin=13*mm,topMargin=11*mm,bottomMargin=12*mm,title=f"Счёт №{_deal_doc_number(deal)}")
    styles=getSampleStyleSheet()
    title=ParagraphStyle("InvTitle",parent=styles["Title"],fontName=bold,fontSize=13,leading=16,alignment=TA_LEFT,spaceAfter=4*mm,textColor=colors.HexColor("#202833"))
    body=ParagraphStyle("InvBody",parent=styles["BodyText"],fontName=font,fontSize=8,leading=10,spaceAfter=1.3*mm)
    small=ParagraphStyle("InvSmall",parent=body,fontSize=6.7,leading=8)
    cell=ParagraphStyle("InvCell",parent=small,fontSize=6.8,leading=8)
    head=ParagraphStyle("InvHead",parent=cell,fontName=bold,alignment=TA_CENTER)
    date=moscow_now().date()
    next_month=1 if date.month==12 else date.month+1
    year=date.year+1 if date.month==12 else date.year
    due=date.replace(year=year,month=next_month,day=monthrange(year,next_month)[1])
    rows=_calculation_rows(calc,st.session_state.crm_store.get("products",DEFAULT_PRODUCT_CATALOG))
    delivery=max(0.0,float(calc.get("delivery_amount",0) or 0))
    total=round(sum(r["amount"] for r in rows)+delivery,2)
    payer_name=requisites.get("legal_name","")
    if requisites.get("payer_type")=="person":
        payer_details=f"{payer_name}, ИНН {requisites.get('inn','')}, {requisites.get('address','')}"
    else:
        payer_details=f"{payer_name}, ИНН {requisites.get('inn','')}"+(f"/КПП {requisites.get('kpp','')}" if requisites.get('kpp') else "")+f", {requisites.get('address','')}"
    seller="ИП Фазлов Дамир Ибрагимович"
    bank="ООО \"Банк Точка\""
    seller_inn="731701704975"
    account="40802810801500486358"
    bik="044525104"
    corr="30101810745374525104"
    calc_name=str(calc.get("name") or _calculation_display_name(deal,calc))
    suffix=calc_name.replace("Расчёт", "", 1).strip()
    invoice_no=f"Счёт {suffix} от {date.strftime('%d.%m.%Y')}"
    flow=[Paragraph(f"{_money(total)} ₽",ParagraphStyle("InvAmount",parent=title,fontSize=16,alignment=TA_RIGHT)),
          Paragraph("Получатель",body),
          Table([[Paragraph(f"<b>{seller}</b><br/>ИНН {seller_inn}<br/>Банк получателя: {bank}<br/>БИК {bik}<br/>Кор. счёт {corr}<br/>Счёт {account}<br/>Без НДС",body)]],colWidths=[180*mm],style=TableStyle([("BOX",(0,0),(-1,-1),0.6,colors.HexColor("#AEB6C2")),("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F8F9FB")),("LEFTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)])),
          Spacer(1,5*mm),Paragraph(f"<b>{html.escape(invoice_no)}</b>",title),
          Paragraph(f"Получатель: {seller}, ИНН {seller_inn}, р/с {account}, в банке {bank}, БИК {bik}, к/с {corr}",body),
          Paragraph(f"Плательщик: {html.escape(payer_details)}",body),Spacer(1,3*mm)]
    data=[[Paragraph(x,head) for x in ["№","Название товара или услуги","Кол-во","Ед. изм.","Цена","НДС","Сумма"]]]
    for i,r in enumerate(rows,1):
        name=f"{html.escape(str(r['name']))}<br/><font size='6'>(Артикул: {html.escape(str(r['sku']))})</font>"
        if r['color']: name += f"<br/><font size='6'>Цвет/RAL: {html.escape(str(r['color']))}</font>"
        data.append([Paragraph(str(i),cell),Paragraph(name,cell),Paragraph(f"{r['quantity']:g}",cell),Paragraph(html.escape(str(r['unit'])),cell),Paragraph(_money(r['after']),cell),Paragraph("Без НДС",cell),Paragraph(_money(r['amount']),cell)])
    if delivery:
        data.append([Paragraph(str(len(rows)+1),cell),Paragraph("Доставка",cell),Paragraph("1",cell),Paragraph("усл.",cell),Paragraph(_money(delivery),cell),Paragraph("Без НДС",cell),Paragraph(_money(delivery),cell)])
    tbl=Table(data,colWidths=[9*mm,72*mm,17*mm,18*mm,24*mm,18*mm,27*mm],repeatRows=1,hAlign="LEFT")
    tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E9EDF2")),("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#AEB6C2")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    _line_count = len(rows) + (1 if delivery else 0)
    _count_mod = _line_count % 100
    _count_last = _line_count % 10
    _count_word = "наименование" if _count_last == 1 and _count_mod != 11 else ("наименования" if 2 <= _count_last <= 4 and not 12 <= _count_mod <= 14 else "наименований")
    flow += [tbl,Spacer(1,3*mm),Paragraph(f"Всего {_line_count} {_count_word} на сумму {_number_to_russian_words(int(total))} {int(round((total-int(total))*100)):02d} копеек.",body),Paragraph(f"<b>Итог к оплате: {_money(total)} ₽</b> &nbsp;&nbsp; Без НДС",ParagraphStyle("InvTotal",parent=body,fontName=bold,fontSize=10,alignment=TA_RIGHT)),Paragraph(f"Срок оплаты: Не позднее {due.strftime('%d.%m.%Y')} г.",body),Spacer(1,12*mm)]
    sign=Table([[Paragraph(f"Получатель:<br/><br/>Индивидуальный предприниматель<br/>Фазлов Дамир Ибрагимович",body),Paragraph("Плательщик: ___________________________<br/><br/>Подпись / печать",body)]],colWidths=[90*mm,90*mm])
    sign.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),4)]))
    flow.append(sign)
    doc.build(flow)
    return out.getvalue(), due.strftime("%d.%m.%Y")


def _save_generated_document(deal, pdf_bytes, filename, kind, calc, extra=None):
    """Сохраняет PDF в хранилище CRM и прикрепляет к файлам сделки."""
    safe_name=re.sub(r"[^\wА-Яа-яЁё№(). —-]+", "_", filename).strip().replace("/", "_")
    digest=hashlib.sha256(pdf_bytes).hexdigest()
    path=""
    if YANDEX_TOKEN:
        remote_name=f"deal_{deal.get('id')}_{uuid.uuid4().hex[:8]}_{safe_name}"
        if upload_file_to_yandex(pdf_bytes, remote_name):
            path=f"CRM_NE_TROGAT/uploads/{remote_name}"
    if not path:
        os.makedirs("uploads",exist_ok=True)
        local_name=f"deal_{deal.get('id')}_{uuid.uuid4().hex[:8]}_{safe_name}"
        path=os.path.join("uploads",local_name)
        with open(path,"wb") as f: f.write(pdf_bytes)
    file_obj={"file_path":path,"file_name":safe_name,"file_hash":digest,"description":f"{kind} · {calc.get('name','Расчёт')}","document_type":kind,"calculation_id":str(calc.get("id")),"created_at":now_str()}
    deal.setdefault("deal_files",[]).append(file_obj)
    deal.setdefault("generated_documents",[]).append({"id":uuid.uuid4().hex,"kind":kind,"file_name":safe_name,"file_hash":digest,"calculation_id":str(calc.get("id")),"calculation_name":calc.get("name",""),"created_at":now_str(),"payer":copy.deepcopy(extra or {})})
    deal["last_modified"]=now_str()
    save_data(st.session_state.crm_store)
    return file_obj


def _open_pdf_link(pdf_bytes, filename, key):
    b64=base64.b64encode(pdf_bytes).decode("ascii")
    st.session_state[key]={"data":b64,"filename":filename}


@_crm_dialog("Добавить реквизиты", width="large")
def client_requisites_dialog(client_id, return_to_invoice=False, requisite_id=None):
    client=get_client_by_id(client_id)
    if not client:
        st.error("Клиент не найден")
        return
    client.setdefault("requisites",[])
    existing_req=next((r for r in client.get("requisites",[]) if str(r.get("id"))==str(requisite_id) and not r.get("deleted")),None) if requisite_id else None
    key=f"req_{client_id}_{'invoice' if return_to_invoice else 'client'}_{requisite_id or 'new'}"
    dirty=f"{key}_dirty"; warning=f"{key}_warning"
    fields=[("legal_name","Наименование юр. лица"),("payer_type","Тип плательщика"),("inn","ИНН"),("kpp","КПП"),("address","Юридический адрес"),("bank_name","Банк"),("bik","БИК"),("corr_account","Корр. счёт"),("settlement_account","Расчётный счёт"),("phone","Телефон"),("email","Email")]
    for k,_ in fields:
        if f"{key}_{k}" not in st.session_state:
            default_value = (existing_req or {}).get(k, "company" if k == "payer_type" else "")
            st.session_state[f"{key}_{k}"] = default_value
    close_css=f"{key}_close_row"
    st.markdown(f'<style>.st-key-{close_css} .stButton>button{{width:36px!important;height:36px!important;min-width:36px!important;padding:0!important;background:#fff!important;border:1px solid #DCE0E5!important;color:#5A6B7D!important;}}</style>',unsafe_allow_html=True)
    with st.container(key=close_css):
        sp,cc=st.columns([20,1])
        with cc:
            if st.button("✕",key=f"{key}_close",use_container_width=True):
                if st.session_state.get(dirty,False) and not st.session_state.get(warning,False):
                    st.session_state[warning]=True; st.rerun()
                else:
                    for k,_ in fields: st.session_state.pop(f"{key}_{k}",None)
                    st.session_state.pop(dirty,None); st.session_state.pop(warning,None)
                    st.session_state.pop("dialog_client_requisites_client_id",None)
                    st.session_state.pop("dialog_client_requisites_return_to_invoice",None)
                    if return_to_invoice:
                        invoice=st.session_state.get("dialog_invoice_request") or {}
                        invoice["selected_requisite_id"]=""
                        st.session_state["dialog_invoice_request"]=invoice
                        invoice_document_dialog(invoice.get("deal_id"),invoice.get("calc_id"))
                    else:
                        _pop_dialog_return(); st.rerun()
    if st.session_state.get(warning):
        with st.container(border=True):
            st.warning("Есть несохранённые изменения. Сохранить перед закрытием?")
            a,b,c=st.columns(3)
            with a:
                if st.button("Сохранить",key=f"{key}_warn_save",type="primary",use_container_width=True): st.session_state[f"{key}_save_requested"]=True; st.session_state[warning]=False
            with b:
                if st.button("Без сохр.",key=f"{key}_warn_discard",use_container_width=True):
                    for k,_ in fields: st.session_state.pop(f"{key}_{k}",None)
                    st.session_state.pop(dirty,None); st.session_state.pop(warning,None); st.session_state.pop("dialog_client_requisites_client_id",None)
                    st.session_state.pop("dialog_client_requisites_return_to_invoice",None)
                    if return_to_invoice:
                        inv=st.session_state.get("dialog_invoice_request") or {}; invoice_document_dialog(inv.get("deal_id"),inv.get("calc_id"))
                    else: _pop_dialog_return(); st.rerun()
            with c:
                if st.button("Продолжить",key=f"{key}_warn_continue",use_container_width=True): st.session_state[warning]=False; st.rerun()
    st.markdown("Заполни реквизиты плательщика. Они сохранятся в карточке клиента и будут доступны для следующих счетов.")
    recognize_key=f"{key}_recognize_open"
    if st.button("Распознать реквизиты", key=f"{key}_recognize_btn", use_container_width=True):
        st.session_state[recognize_key] = not st.session_state.get(recognize_key, False)
    if st.session_state.get(recognize_key, False):
        uploaded_req_file=st.file_uploader("Выбери файл с реквизитами", type=["pdf","docx","xlsx","txt","csv"], key=f"{key}_recognize_file", help="Поддерживаются PDF с текстовым слоем, Word, Excel, TXT и CSV. Скан PDF без текстового слоя нужно предварительно распознать OCR.")
        if uploaded_req_file and st.button("Заполнить поля из файла", key=f"{key}_recognize_apply", type="primary", use_container_width=True):
            try:
                raw_text=""
                ext=Path(uploaded_req_file.name).suffix.lower()
                if ext==".pdf":
                    try:
                        from pypdf import PdfReader
                    except ImportError:
                        from PyPDF2 import PdfReader
                    reader=PdfReader(io.BytesIO(uploaded_req_file.getvalue()))
                    raw_text="\n".join(page.extract_text() or "" for page in reader.pages)
                elif ext==".docx":
                    from docx import Document
                    doc=Document(io.BytesIO(uploaded_req_file.getvalue()))
                    raw_text="\n".join([p.text for p in doc.paragraphs]+[" | ".join(c.text for c in row.cells) for table in doc.tables for row in table.rows])
                elif ext in (".xlsx", ".xls"):
                    import openpyxl
                    wb=openpyxl.load_workbook(io.BytesIO(uploaded_req_file.getvalue()),data_only=True,read_only=True)
                    raw_text="\n".join(" ".join(str(v) for v in row if v is not None) for ws in wb.worksheets for row in ws.iter_rows(values_only=True))
                else:
                    raw_text=uploaded_req_file.getvalue().decode("utf-8-sig",errors="replace")
                def _extract_req(patterns):
                    for pat in patterns:
                        m=re.search(pat,raw_text,re.I|re.M)
                        if m:
                            return re.sub(r"\s+"," ",m.group(1)).strip(" ;,\t")
                    return ""
                found={
                    "inn":_extract_req([r"ИНН\s*[:№]?\s*([0-9]{10,12})"]),
                    "kpp":_extract_req([r"КПП\s*[:№]?\s*([0-9]{9})"]),
                    "bik":_extract_req([r"БИК\s*[:№]?\s*([0-9]{9})"]),
                    "corr_account":_extract_req([r"(?:корреспондентский|корр\.?)[^\n:]{0,30}(?:сч[её]т|с/с)?\s*[:№]?\s*(\d{20})",r"301\d{17}"]),
                    "settlement_account":_extract_req([r"(?:расч[её]тный|р/с)[^\n:]{0,25}(?:сч[её]т)?\s*[:№]?\s*(\d{20})",r"408\d{17}"]),
                    "email":_extract_req([r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})"]),
                    "phone":_extract_req([r"(?:тел(?:ефон)?\.?|моб\.?)[^\n:]{0,12}[:]?\s*(\+?[0-9][0-9 ()-]{7,}[0-9])"]),
                    "bank_name":_extract_req([r"(?:банк|наименование банка)\s*[:]?\s*([^\n;]+)"]),
                    "address":_extract_req([r"(?:юридический адрес|адрес)\s*[:]?\s*([^\n;]+)"]),
                }
                lines=[re.sub(r"\s+"," ",x).strip() for x in raw_text.splitlines() if x.strip()]
                name=_extract_req([r"(?:полное наименование|наименование организации|наименование юридического лица|плательщик|получатель)\s*[:]?\s*([^\n]+)",r"(ИП\s+[^\n,;]+)",r"(ООО\s*[«\"“]?[^\n»\"”;,]+[»\"”]?)"])
                if not name:
                    name=next((ln for ln in lines if re.search(r"\b(ООО|АО|ПАО|ИП|индивидуальный предприниматель)\b",ln,re.I)),"")
                found["legal_name"]=name
                found["payer_type"]="ip" if re.search(r"\bИП\b|индивидуальный предприниматель",name,re.I) else "company" if re.search(r"ООО|АО|ПАО|ЗАО|ОАО",name,re.I) else "person"
                count=0
                for field_name,value in found.items():
                    if value:
                        st.session_state[f"{key}_{field_name}"]=value
                        count+=1
                st.session_state[dirty]=True
                st.session_state[recognize_key]=False
                if count:
                    st.success(f"Заполнено полей: {count}. Проверь данные и сохрани реквизиты.")
                    st.rerun()
                else:
                    st.warning("Не удалось найти реквизиты в файле. Если это скан, нужен OCR или файл с выделяемым текстом.")
            except Exception as e:
                st.error(f"Не удалось прочитать файл: {e}")
    c1,c2=st.columns(2)
    with c1:
        st.text_input("Наименование юр. лица / ФИО плательщика",key=f"{key}_legal_name",on_change=lambda:st.session_state.__setitem__(dirty,True))
        st.selectbox("Тип плательщика",["company","ip","person"],format_func=lambda x:{"company":"Юридическое лицо (ООО)","ip":"Индивидуальный предприниматель","person":"Физическое лицо"}[x],key=f"{key}_payer_type",on_change=lambda:st.session_state.__setitem__(dirty,True))
        st.text_input("ИНН",key=f"{key}_inn",on_change=lambda:st.session_state.__setitem__(dirty,True))
        st.text_input("КПП",key=f"{key}_kpp",on_change=lambda:st.session_state.__setitem__(dirty,True))
        st.text_area("Юридический адрес",key=f"{key}_address",height=75,on_change=lambda:st.session_state.__setitem__(dirty,True))
    with c2:
        st.text_input("Наименование банка",key=f"{key}_bank_name",on_change=lambda:st.session_state.__setitem__(dirty,True))
        st.text_input("БИК",key=f"{key}_bik",on_change=lambda:st.session_state.__setitem__(dirty,True))
        st.text_input("Корреспондентский счёт",key=f"{key}_corr_account",on_change=lambda:st.session_state.__setitem__(dirty,True))
        st.text_input("Расчётный счёт",key=f"{key}_settlement_account",on_change=lambda:st.session_state.__setitem__(dirty,True))
        st.text_input("Телефон",key=f"{key}_phone",on_change=lambda:st.session_state.__setitem__(dirty,True))
        st.text_input("Email",key=f"{key}_email",on_change=lambda:st.session_state.__setitem__(dirty,True))
    save_now=st.button("Сохранить реквизиты",key=f"{key}_save",type="primary",use_container_width=True)
    save_warn=bool(st.session_state.pop(f"{key}_save_requested",False))
    if save_now or save_warn:
        name=str(st.session_state.get(f"{key}_legal_name","")).strip()
        inn=str(st.session_state.get(f"{key}_inn","")).strip()
        address=str(st.session_state.get(f"{key}_address","")).strip()
        if not name or not inn:
            st.error("Укажи наименование плательщика и ИНН.")
        else:
            req={k:st.session_state.get(f"{key}_{k}","").strip() if isinstance(st.session_state.get(f"{key}_{k}",""),str) else st.session_state.get(f"{key}_{k}") for k,_ in fields}
            if existing_req:
                existing_req.update(req)
                existing_req["updated_at"]=now_str()
                existing_req["updated_by"]=st.session_state.get("user_name",st.session_state.get("user_login",""))
                req=existing_req
            else:
                req.update({"id":uuid.uuid4().hex,"deleted":False,"created_at":now_str(),"created_by":st.session_state.get("user_name",st.session_state.get("user_login",""))})
                client.setdefault("requisites",[]).append(req)
            client["last_modified"]=now_str()
            client.setdefault("change_log",[]).append({"date":now_str(),"author":st.session_state.get("user_name",st.session_state.get("user_login","")),"fields":f"{'Обновлены' if existing_req else 'Добавлены'} реквизиты «{name}»"})
            save_data(st.session_state.crm_store)
            st.session_state.pop("dialog_client_requisites_client_id",None)
            st.session_state.pop("dialog_client_requisites_return_to_invoice",None)
            for k,_ in fields: st.session_state.pop(f"{key}_{k}",None)
            st.session_state.pop(dirty,None); st.session_state.pop(warning,None); st.session_state.pop(f"{key}_save_requested",None)
            st.toast("Реквизиты сохранены",icon="✅")
            if return_to_invoice:
                inv=st.session_state.get("dialog_invoice_request") or {}
                inv["selected_requisite_id"]=req["id"]
                st.session_state["dialog_invoice_request"]=inv
                invoice_document_dialog(inv.get("deal_id"),inv.get("calc_id"))
            else:
                _pop_dialog_return(); st.rerun()


@_crm_dialog("Сформировать счёт", width="large")
def invoice_document_dialog(deal_id, calc_id):
    deal=next((d for d in st.session_state.crm_store.get("deals",[]) if str(d.get("id"))==str(deal_id)),None)
    if not deal:
        st.error("Сделка не найдена"); return
    calc=next((c for c in deal.get("calculations",[]) if str(c.get("id"))==str(calc_id)),None)
    if not calc:
        st.error("Расчёт не найден"); return
    client=get_client_by_id(deal.get("client_id")) or {}
    requisites=[r for r in client.setdefault("requisites",[]) if not r.get("deleted")]
    state=st.session_state.get("dialog_invoice_request") or {"deal_id":deal_id,"calc_id":calc_id,"selected_requisite_id":""}
    st.session_state["dialog_invoice_request"]=state
    close_key=f"invoice_close_{deal_id}_{calc_id}"
    with st.container(key=f"{close_key}_row"):
        sp,cc=st.columns([20,1])
        with cc:
            if st.button("✕",key=close_key,use_container_width=True):
                st.session_state.pop("dialog_invoice_request",None)
                deal_calculation_dialog(deal_id,calc_id)
    st.markdown(f"**Сделка:** {deal.get('deal_number',deal.get('title',''))}")
    st.markdown(f"**Расчёт:** {calc.get('name','Расчёт')}")
    if not requisites:
        st.info("Для клиента пока не сохранены реквизиты плательщика.")
    else:
        ids=[str(r.get("id")) for r in requisites]
        selected=str(state.get("selected_requisite_id",ids[0]))
        if selected not in ids: selected=ids[0]
        sel=st.selectbox("Реквизиты плательщика",ids,index=ids.index(selected),format_func=lambda rid:next((r.get("legal_name", "Реквизиты") for r in requisites if str(r.get("id"))==str(rid)),"Реквизиты"),key=f"invoice_req_select_{deal_id}_{calc_id}")
        state["selected_requisite_id"]=sel
        selected_req=next((r for r in requisites if str(r.get("id"))==str(sel)),None)
        if selected_req:
            st.caption(f"ИНН: {selected_req.get('inn','—')}  ·  Адрес: {selected_req.get('address','—')}")
    add_col,generate_col=st.columns(2)
    with add_col:
        if st.button("+ Добавить новые реквизиты",key=f"invoice_add_req_{deal_id}_{calc_id}",use_container_width=True):
            st.session_state["dialog_client_requisites_client_id"]=client.get("id")
            st.session_state["dialog_client_requisites_return_to_invoice"]=True
            client_requisites_dialog(client.get("id"),True)
    with generate_col:
        if st.button("Сформировать счёт PDF",key=f"invoice_generate_{deal_id}_{calc_id}",type="primary",use_container_width=True):
            req=next((r for r in requisites if str(r.get("id"))==str(state.get("selected_requisite_id"))),None)
            if not req:
                st.error("Сначала выбери реквизиты плательщика или добавь новые.")
            elif not calc.get("items"):
                st.error("Добавь хотя бы одну товарную позицию в расчёт.")
            else:
                try:
                    pdf,due=_make_invoice_pdf(deal,client,calc,req)
                    display=str(calc.get("name") or _calculation_display_name(deal,calc)).replace("Расчёт","Счёт",1)
                    filename=f"{display} от {moscow_now().strftime('%d.%m.%Y')}.pdf"
                    _save_generated_document(deal,pdf,filename,"Счёт",calc,req)
                    _open_pdf_link(pdf,filename,f"invoice_pdf_{deal_id}_{calc_id}")
                    st.session_state[f"invoice_generated_note_{deal_id}_{calc_id}"]=f"Счёт сохранён в файлах сделки. Срок оплаты: {due}."
                    st.success(f"Счёт сохранён в файлах сделки. Срок оплаты: {due}.")
                except Exception as exc:
                    st.error(f"Не удалось сформировать счёт: {exc}")
    pdf_state=st.session_state.get(f"invoice_pdf_{deal_id}_{calc_id}")
    if pdf_state:
        st.markdown(f'<a href="data:application/pdf;base64,{pdf_state["data"]}" target="_blank" rel="noopener" style="display:inline-block;background:#bc1661;color:white;text-decoration:none;padding:9px 14px;border-radius:8px;font-weight:600">Открыть PDF в новой вкладке</a>',unsafe_allow_html=True)
        st.download_button("Скачать PDF",data=base64.b64decode(pdf_state["data"]),file_name=pdf_state["filename"],mime="application/pdf",key=f"invoice_pdf_dl_{deal_id}_{calc_id}")


def render_deal_products_block(d, key_prefix):
    """Список сохранённых расчётов с мягким удалением и отдельным окном редактора."""
    calculations = d.setdefault("calculations", [])
    _ensure_calculation_names(d)
    # Перенос ранее созданного одиночного расчёта в список без потери данных.
    if not calculations and (d.get("items") or d.get("delivery_amount")):
        calculations.append({
            "id": uuid.uuid4().hex, "name": "Расчёт 1", "items": copy.deepcopy(d.get("items", [])),
            "delivery_amount": float(d.get("delivery_amount", 0) or 0),
            "discount_type": d.get("discount_type", "Без скидки"),
            "individual_discount": float(d.get("individual_discount", 0) or 0),
            "total": float(d.get("budget", 0) or 0), "deleted": False, "created_at": now_str()
        })
        _ensure_calculation_names(d)
        save_data(st.session_state.crm_store)

    st.markdown("**Расчёты по сделке**")
    if not calculations:
        st.caption("Расчётов пока нет.")
    for idx, calc in enumerate(calculations):
        calc.setdefault("id", uuid.uuid4().hex)
        calc.setdefault("deleted", False)
        calc.setdefault("name", f"Расчёт {idx + 1}")
        calc.setdefault("total", _deal_calc_total(calc))
        if calc.get("deleted"):
            st.markdown(
                f"<div style='text-decoration:line-through;color:#9299A3;padding:0.35rem 0;'>{calc.get('name', 'Расчёт')} — {calc['total']:,.0f} ₽ (удалён)</div>".replace(",", " "),
                unsafe_allow_html=True,
            )
            continue
        name_col, total_col, edit_col, delete_col = st.columns([3.0, 1.4, 1.0, 1.0])
        with name_col:
            st.markdown(f"**{calc.get('name', 'Расчёт')}**")
        with total_col:
            st.markdown(f"{calc['total']:,.0f} ₽".replace(",", " "))
        with edit_col:
            if st.button("Открыть", key=f"calc_edit_{d['id']}_{calc['id']}", use_container_width=True):
                _push_dialog_return()
                deal_calculation_dialog(d["id"], calc["id"])
        with delete_col:
            if st.button("Удалить", key=f"calc_delete_{d['id']}_{calc['id']}", use_container_width=True):
                calc["deleted"] = True
                calc["deleted_at"] = now_str()
                calc["deleted_by"] = st.session_state.get("user_name", st.session_state.get("user_login", ""))
                d["last_modified"] = now_str()
                d.setdefault("change_log", []).append({"date": now_str(), "author": st.session_state.get("user_name", st.session_state.get("user_login", "")), "fields": f"Расчёт «{calc.get('name', 'Расчёт')}» помечен удалённым"})
                save_data(st.session_state.crm_store)
                st.rerun()

    if st.button("Добавить новый расчёт", key=f"calc_add_{d['id']}", type="primary", use_container_width=True):
        calc = {"id": uuid.uuid4().hex, "name": _calculation_display_name(d, {"id": "__new__"}, len(calculations)), "items": [],
                "delivery_amount": 0.0, "discount_type": "Без скидки", "individual_discount": 0.0,
                "total": 0.0, "deleted": False, "_draft": True, "created_at": now_str()}
        calculations.append(calc)
        save_data(st.session_state.crm_store)
        _push_dialog_return()
        deal_calculation_dialog(d["id"], calc["id"])


@_crm_dialog("Создание расчёта", width="large")
def deal_calculation_dialog(deal_id, calc_id):
    """Отдельное окно редактирования расчёта в стиле окон задач."""
    def _calc_refresh():
        if st.session_state.get("_crm_inside_dialog_host", False):
            try:
                st.rerun(scope="fragment")
            except TypeError:
                st.rerun()
        else:
            st.rerun()
    deal = next((x for x in st.session_state.crm_store.get("deals", []) if str(x.get("id")) == str(deal_id)), None)
    if not deal:
        st.error("Сделка не найдена")
        return
    calc = next((x for x in deal.setdefault("calculations", []) if str(x.get("id")) == str(calc_id)), None)
    if calc is None:
        st.error("Расчёт не найден")
        return

    key = f"calc_{deal_id}_{calc_id}"
    dirty_key = f"{key}_dirty"
    warning_key = f"{key}_close_warning"
    name_key = f"{key}_name"
    calc.setdefault("items", [])
    calc.setdefault("delivery_amount", 0.0)
    calc.setdefault("discount_type", "Без скидки")
    calc.setdefault("individual_discount", 0.0)
    snapshot_key = f"{key}_original_snapshot"
    if snapshot_key not in st.session_state:
        st.session_state[snapshot_key] = copy.deepcopy(calc)
    if name_key not in st.session_state:
        st.session_state[name_key] = calc.get("name") or _calculation_display_name(deal, calc)
    if re.match(r"^Расчёт\s+\d+$", str(st.session_state.get(name_key, "")), re.I):
        st.session_state[name_key] = _calculation_display_name(deal, calc)

    close_css = f"calc_close_row_{key}"
    st.markdown(f'''<style>.st-key-{close_css} .stButton > button {{width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:6px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important;}} .st-key-{close_css} .stButton > button:hover {{background:#EEF0F3!important;border-color:#C9CFD7!important;}}</style>''', unsafe_allow_html=True)
    st.markdown(f'''<style>
    .st-key-{key}_make_offer button, .st-key-{key}_make_invoice button {{min-width:150px!important;white-space:nowrap!important;padding-left:12px!important;padding-right:12px!important;font-size:0.9rem!important;}}
    .st-key-{close_css} .stButton > button {{width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:6px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important;}}
    .st-key-{close_css} .stButton > button:hover {{background:#EEF0F3!important;border-color:#C9CFD7!important;}}
    </style>''' , unsafe_allow_html=True)
    with st.container(key=close_css):
        offer_col, invoice_col, _spacer, close_col = st.columns([5.2, 5.2, 7.0, 1.0])
        with offer_col:
            if st.button("Сформировать КП", key=f"{key}_make_offer", use_container_width=True, type="primary"):
                try:
                    calc["name"] = str(st.session_state.get(name_key, calc.get("name") or _calculation_display_name(deal, calc))).strip() or _calculation_display_name(deal, calc)
                    calc["discount_type"] = st.session_state.get(f"{key}_discount_type", calc.get("discount_type", "Без скидки"))
                    calc["delivery_amount"] = float(st.session_state.get(f"{key}_delivery", calc.get("delivery_amount", 0)) or 0)
                    calc["individual_discount"] = float(st.session_state.get(f"{key}_individual_discount", calc.get("individual_discount", 0)) or 0)
                    calc["total"] = _deal_calc_total(calc)
                    if not calc.get("items"):
                        raise ValueError("Добавь хотя бы одну товарную позицию в расчёт.")
                    calc["_draft"] = False
                    calc["updated_at"] = now_str()
                    deal["budget"] = calc["total"]
                    deal["last_modified"] = now_str()
                    save_data(st.session_state.crm_store)
                    pdf = _make_commercial_offer_pdf(deal, get_client_by_id(deal.get("client_id")) or {}, calc)
                    filename = f"{calc['name'].replace('Расчёт','КП',1)} от {moscow_now().strftime('%d.%m.%Y')}.pdf"
                    _save_generated_document(deal, pdf, filename, "Коммерческое предложение", calc)
                    _open_pdf_link(pdf, filename, f"offer_pdf_{deal_id}_{calc_id}")
                    st.session_state[f"{key}_doc_message"] = "КП сохранено в файлах сделки."
                except Exception as exc:
                    st.session_state[f"{key}_doc_error"] = f"Не удалось сформировать КП: {exc}"
                _calc_refresh()
        with invoice_col:
            if st.button("Сформировать счёт", key=f"{key}_make_invoice", use_container_width=True):
                calc["name"] = str(st.session_state.get(name_key, calc.get("name") or _calculation_display_name(deal, calc))).strip() or _calculation_display_name(deal, calc)
                calc["discount_type"] = st.session_state.get(f"{key}_discount_type", calc.get("discount_type", "Без скидки"))
                calc["delivery_amount"] = float(st.session_state.get(f"{key}_delivery", calc.get("delivery_amount", 0)) or 0)
                calc["individual_discount"] = float(st.session_state.get(f"{key}_individual_discount", calc.get("individual_discount", 0)) or 0)
                calc["total"] = _deal_calc_total(calc)
                calc["_draft"] = False
                calc["updated_at"] = now_str()
                deal["budget"] = calc["total"]
                deal["last_modified"] = now_str()
                save_data(st.session_state.crm_store)
                st.session_state["dialog_invoice_request"] = {"deal_id": deal_id, "calc_id": calc_id, "selected_requisite_id": ""}
                invoice_document_dialog(deal_id, calc_id)
        with close_col:
            if st.button("✕", key=f"{key}_close", use_container_width=True):
                if st.session_state.get(dirty_key, False) and not st.session_state.get(warning_key, False):
                    st.session_state[warning_key] = True
                    _calc_refresh()
                else:
                    if calc.get("_draft"):
                        deal["calculations"] = [x for x in deal.get("calculations", []) if str(x.get("id")) != str(calc_id)]
                    save_data(st.session_state.crm_store)
                    for k in (dirty_key, warning_key, name_key, snapshot_key):
                        st.session_state.pop(k, None)
                    _pop_dialog_return()
                    st.rerun()

    _doc_error = st.session_state.pop(f"{key}_doc_error", None)
    if _doc_error:
        st.error(_doc_error)
    _doc_message = st.session_state.pop(f"{key}_doc_message", None)
    if _doc_message:
        st.success(_doc_message)
    _offer_pdf_state = st.session_state.get(f"offer_pdf_{deal_id}_{calc_id}")
    if _offer_pdf_state:
        st.markdown(f'<a href="data:application/pdf;base64,{_offer_pdf_state["data"]}" target="_blank" rel="noopener" style="display:inline-block;background:#bc1661;color:white;text-decoration:none;padding:8px 12px;border-radius:8px;font-weight:600;margin:3px 0">Открыть сформированное КП в новой вкладке</a>',unsafe_allow_html=True)
        st.download_button("Скачать КП PDF",data=base64.b64decode(_offer_pdf_state["data"]),file_name=_offer_pdf_state["filename"],mime="application/pdf",key=f"offer_pdf_dl_{deal_id}_{calc_id}")

    if st.session_state.get(warning_key):
        warn_key = f"calc_unsaved_warn_{key}"
        st.markdown(f'<style>.st-key-{warn_key} {{border:2px solid #FF9800!important;border-radius:10px!important;background:#FFF8E1!important;padding:0.65rem 0.8rem!important;margin:0.35rem 0 0.65rem!important;}}</style>', unsafe_allow_html=True)
        with st.container(key=warn_key):
            st.markdown("**⚠️ Есть несохранённые изменения**")
            st.markdown("Сохранить перед закрытием?")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Сохранить", key=f"{key}_warn_save", type="primary", use_container_width=True):
                    st.session_state[warning_key] = False
                    st.session_state[f"{key}_save_requested"] = True
            with c2:
                if st.button("Без сохр.", key=f"{key}_warn_discard", use_container_width=True):
                    if calc.get("_draft"):
                        deal["calculations"] = [x for x in deal.get("calculations", []) if str(x.get("id")) != str(calc_id)]
                    else:
                        _original = st.session_state.get(snapshot_key)
                        if _original is not None:
                            for _i, _saved_calc in enumerate(deal.get("calculations", [])):
                                if str(_saved_calc.get("id")) == str(calc_id):
                                    deal["calculations"][_i] = copy.deepcopy(_original)
                                    break
                    save_data(st.session_state.crm_store)
                    for k in (dirty_key, warning_key, name_key, f"{key}_save_requested", snapshot_key):
                        st.session_state.pop(k, None)
                    _pop_dialog_return()
                    st.rerun()
            with c3:
                if st.button("Продолжить", key=f"{key}_warn_continue", use_container_width=True):
                    st.session_state[warning_key] = False
                    _calc_refresh()

    st.markdown("""<style>
    div[role="dialog"] div[data-testid="stVerticalBlock"] {gap: 0.45rem !important;}
    div[role="dialog"] div[data-testid="stHorizontalBlock"] {gap: 0.55rem !important;}
    div[role="dialog"] .stTextInput, div[role="dialog"] .stNumberInput, div[role="dialog"] .stSelectbox {margin-bottom: -0.25rem !important;}
    div[role="dialog"] [data-testid="stCaptionContainer"] {margin-top: -0.35rem !important;margin-bottom: -0.25rem !important;}
    </style>""", unsafe_allow_html=True)
    st.markdown("### Расчёт сделки")
    name_col, *_ = st.columns([2.8, 1.05, 0.62, 1.15, 0.72, 0.72, 0.78])
    with name_col:
        st.text_input("Название расчёта", key=name_key, on_change=lambda: st.session_state.__setitem__(dirty_key, True))
    catalog = st.session_state.crm_store.get("products", DEFAULT_PRODUCT_CATALOG)
    active_products = [p for p in catalog if p.get("active", True)]
    if not active_products:
        st.warning("В каталоге нет активных товаров. Добавьте товары в разделе «Товары и прайс».")
        return
    items = calc.setdefault("items", [])
    dtype_options = list(DISCOUNT_TYPES.keys())
    if calc.get("discount_type") not in dtype_options:
        calc["discount_type"] = "Без скидки"
    dtype_key = f"{key}_discount_type"
    dtype_col, *_ = st.columns([2.8, 1.05, 0.62, 1.15, 0.72, 0.72, 0.78])
    with dtype_col:
        selected_dtype = st.selectbox("Тип скидки по умолчанию для новых товаров", dtype_options,
            index=dtype_options.index(calc.get("discount_type", "Без скидки")), key=dtype_key,
            on_change=lambda: st.session_state.__setitem__(dirty_key, True))
    custom_key = f"{key}_individual_discount"
    if selected_dtype == "Индивидуальная":
        custom_col, *_ = st.columns([2.8, 1.05, 0.62, 1.15, 0.72, 0.72, 0.78])
        with custom_col:
            custom_default = st.number_input("Индивидуальная скидка, %", min_value=0.0, max_value=100.0,
                value=float(calc.get("individual_discount", 0) or 0), step=1.0, format="%g", key=custom_key,
                on_change=lambda: st.session_state.__setitem__(dirty_key, True))
    else:
        custom_default = float(calc.get("individual_discount", 0) or 0)
    default_discount = custom_default if selected_dtype == "Индивидуальная" else float(DISCOUNT_TYPES.get(selected_dtype, 0))

    for idx, item in enumerate(items):
        item.setdefault("row_id", uuid.uuid4().hex)
        item.setdefault("color_ral", "")
        row_id = item["row_id"]
        pid_key = f"{key}_{row_id}_product"
        pids = [str(p.get("id", p.get("sku", ""))) for p in active_products]
        current_pid = str(item.get("product_id", pids[0] if pids else ""))
        if current_pid not in pids:
            archived = next((p for p in catalog if str(p.get("id", p.get("sku", ""))) == current_pid), None)
            if archived:
                active_products_row = active_products + [archived]
                pids = [str(p.get("id", p.get("sku", ""))) for p in active_products_row]
            else:
                active_products_row = active_products
        else:
            active_products_row = active_products
        pmap = {str(p.get("id", p.get("sku", ""))): p for p in active_products_row}
        # Артикул и единица измерения показываются отдельными компактными колонками,
        # как в прайсе. Они берутся из карточки товара и не редактируются в расчёте.
        # Порядок колонок: артикул, товар, цвет/RAL, единица измерения, количество, скидка, цена.
        cols = st.columns([1.05, 2.8, 1.15, 0.62, 0.72, 0.72, 0.78])
        with cols[0]:
            st.markdown("<div style='font-size:0.72rem;color:#718096;margin:0.2rem 0 0.35rem'>Артикул</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:0.78rem;font-weight:600;padding-top:0.15rem;overflow-wrap:anywhere'>{pmap.get(current_pid, active_products_row[0]).get('sku', current_pid)}</div>", unsafe_allow_html=True)
        with cols[1]:
            selected_pid = st.selectbox("Товар", pids, index=pids.index(current_pid) if current_pid in pids else 0,
                format_func=lambda x, pm=pmap: pm[x].get("name", x), key=pid_key,
                on_change=lambda: st.session_state.__setitem__(dirty_key, True))
        product = pmap[selected_pid]
        price_key = f"{key}_{row_id}_price"
        if price_key not in st.session_state:
            st.session_state[price_key] = float(item.get("unit_price", product.get("price", 0)) or 0)
        with cols[2]:
            st.text_input("Цвет/RAL", value=str(item.get("color_ral", "")), key=f"{key}_{row_id}_color", placeholder="RAL / цвет", on_change=lambda: st.session_state.__setitem__(dirty_key, True))
        with cols[3]:
            st.markdown("<div style='font-size:0.72rem;color:#718096;margin:0.2rem 0 0.35rem'>Ед.</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:0.78rem;font-weight:600;padding-top:0.15rem'>{product.get('unit', item.get('unit', 'шт.'))}</div>", unsafe_allow_html=True)
        with cols[4]:
            st.number_input("Кол-во", min_value=0.0, value=float(item.get("quantity", 1) or 0), step=1.0, format="%g", key=f"{key}_{row_id}_qty", on_change=lambda: st.session_state.__setitem__(dirty_key, True))
        with cols[5]:
            st.number_input("Скидка, %", min_value=0.0, max_value=100.0, value=float(item.get("discount", default_discount) or 0), step=1.0, format="%g", key=f"{key}_{row_id}_discount", on_change=lambda: st.session_state.__setitem__(dirty_key, True))
        with cols[6]:
            st.markdown("<div style='font-size:0.72rem;color:#718096;margin:0.2rem 0 0.35rem;text-align:right'>Цена</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='padding-top:0.15rem;text-align:right;font-size:0.8rem;color:#64748b;white-space:nowrap'>{float(item.get('unit_price', product.get('price', 0)) or 0):,.0f} ₽</div>".replace(",", " "), unsafe_allow_html=True)
        if st.button("Удалить позицию", key=f"{key}_{row_id}_remove"):
            calc["items"] = [x for x in items if x.get("row_id") != row_id]
            st.session_state[dirty_key] = True
            _calc_refresh()
        # Обновляем только локальный объект до нажатия «Сохранить расчёт».
        item["product_id"] = selected_pid
        item["product_name"] = product.get("name", "")
        item["unit"] = product.get("unit", "шт.")
        item["unit_price"] = float(product.get("price", 0) or 0) if selected_pid != current_pid else float(item.get("unit_price", product.get("price", 0)) or 0)
        item["color_ral"] = st.session_state.get(f"{key}_{row_id}_color", item.get("color_ral", ""))
        item["quantity"] = float(st.session_state.get(f"{key}_{row_id}_qty", item.get("quantity", 1)) or 0)
        item["discount"] = float(st.session_state.get(f"{key}_{row_id}_discount", item.get("discount", default_discount)) or 0)
        if selected_pid != current_pid:
            st.session_state[price_key] = float(product.get("price", 0) or 0)
            item["unit_price"] = float(product.get("price", 0) or 0)

    _add_item_left, _add_item_center, _add_item_right = st.columns([1, 2.2, 1])
    with _add_item_center:
        if st.button("+ Добавить товар", key=f"{key}_add_item", use_container_width=True):
            product = active_products[0]
            items.append({"row_id": uuid.uuid4().hex, "product_id": str(product.get("id", product.get("sku", ""))), "product_name": product.get("name", ""), "unit": product.get("unit", "шт."), "quantity": 1.0, "unit_price": float(product.get("price", 0) or 0), "discount": float(custom_default if selected_dtype == "Индивидуальная" else DISCOUNT_TYPES.get(selected_dtype, 0)), "color_ral": ""})
            st.session_state[dirty_key] = True
            _calc_refresh()

    delivery_key = f"{key}_delivery"
    delivery_exists = bool(calc.get("delivery_added", False) or float(calc.get("delivery_amount", 0) or 0) > 0)
    if delivery_exists:
        delivery_col, *_ = st.columns([2.8, 1.05, 0.62, 1.15, 0.72, 0.72, 0.78])
        with delivery_col:
            delivery = st.number_input("Доставка, ₽", min_value=0.0, value=float(calc.get("delivery_amount", 0) or 0), step=100.0, format="%g", key=delivery_key, on_change=lambda: st.session_state.__setitem__(dirty_key, True))
        _delivery_left, _delivery_center, _delivery_right = st.columns([1, 2.2, 1])
        with _delivery_center:
            if st.button("Убрать доставку", key=f"{key}_remove_delivery", use_container_width=True):
                calc["delivery_added"] = False
                calc["delivery_amount"] = 0.0
                st.session_state.pop(delivery_key, None)
                st.session_state[dirty_key] = True
                _calc_refresh()
    else:
        delivery = 0.0
        _delivery_left, _delivery_center, _delivery_right = st.columns([1, 2.2, 1])
        with _delivery_center:
            if st.button("+ Добавить доставку", key=f"{key}_add_delivery", use_container_width=True):
                calc["delivery_added"] = True
                calc["delivery_amount"] = 0.0
                st.session_state[dirty_key] = True
                _calc_refresh()
    total = _deal_items_total(items) + float(delivery or 0)
    st.markdown(f"**Итого: {total:,.0f} ₽**".replace(",", " "))
    _save_clicked = st.button("Сохранить расчёт", key=f"{key}_save", type="primary", use_container_width=True)
    _save_from_warning = bool(st.session_state.pop(f"{key}_save_requested", False))
    if _save_clicked or _save_from_warning:
        calc["name"] = str(st.session_state.get(name_key, "Расчёт") or "Расчёт").strip() or "Расчёт"
        calc["discount_type"] = selected_dtype
        calc["individual_discount"] = float(custom_default or 0)
        calc["delivery_amount"] = float(delivery or 0)
        calc["total"] = _deal_calc_total(calc)
        calc["updated_at"] = now_str()
        calc["updated_by"] = st.session_state.get("user_name", st.session_state.get("user_login", ""))
        calc["_draft"] = False
        deal["budget"] = calc["total"]
        deal["last_modified"] = now_str()
        deal.setdefault("change_log", []).append({"date": now_str(), "author": st.session_state.get("user_name", st.session_state.get("user_login", "")), "fields": f"Расчёт «{calc['name']}» сохранён"})
        save_data(st.session_state.crm_store)
        for k in (dirty_key, warning_key, f"{key}_save_requested", snapshot_key):
            st.session_state.pop(k, None)
        st.toast("Расчёт сохранён", icon="✅")
        _pop_dialog_return()
        st.rerun()

def render_deal_detail(d, cl, cu, key_prefix):
    """Детали сделки в 2 колонки — как render_task_detail."""
    deal_id = d["id"]
    d.setdefault("change_log", [])
    with st.container(border=True, key=f"deal_detail_{key_prefix}"):
        st.markdown(f'<style>.st-key-deal_detail_{key_prefix} {{ padding: 0.5rem !important; }} .st-key-deal_detail_{key_prefix} .stVerticalBlock {{ gap: 0.15rem !important; }}</style>', unsafe_allow_html=True)
        st.markdown(f"""<style>
        .st-key-deal_detail_{key_prefix} .stHorizontalBlock .stButton button,
        .st-key-deal_detail_{key_prefix} .stHorizontalBlock .stMarkdown button {{
            min-height: 32px !important;
            padding: 4px 10px !important;
            font-size: 0.85rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        .st-key-deal_detail_{key_prefix} .stHorizontalBlock .stMarkdown {{
            margin-top: 0 !important;
            display: flex !important;
            align-items: center !important;
        }}
        .st-key-deal_detail_{key_prefix} > div > div:nth-child(2) > div > div:first-child {{
            margin-top: 0 !important;
            padding-top: 0 !important;
        }}
        .st-key-deal_detail_{key_prefix} > div > div:nth-child(2) {{
            margin-top: 0 !important;
            padding-top: 0 !important;
        }}
        </style>""", unsafe_allow_html=True)
        left_col, right_col = st.columns(2)
        with left_col:
            num = d.get("deal_number", d.get("title", ""))
            head = f"**{num}**"
            if d.get("deal_title"):
                head += f" — {d['deal_title']}"
            st.markdown(f"<div style='font-size:1.35rem;font-weight:750;margin-top:0.8rem;margin-bottom:0.7rem;'>{num}</div>", unsafe_allow_html=True)
            if d.get("deal_title"):
                st.markdown(f"**Тема:** {d['deal_title']}")
            st.markdown(format_created_date(d), unsafe_allow_html=True)
            if cl:
                _client_link_col, _client_link_spacer = st.columns([3, 5])
                with _client_link_col:
                    if st.button(f"Клиент: {cl.get('name', '—')}", key=f"deal_client_link_{deal_id}", type="secondary"):
                        # Открываем карточку клиента поверх логики навигации:
                        # сделка сохраняется в стеке и будет восстановлена при закрытии клиента.
                        _push_dialog_return()
                        st.session_state["active_tab"] = "Клиенты"
                        st.session_state["dialog_client_key"] = cl.get("id")
                        st.rerun()
            else:
                st.markdown("**Клиент:** —")
            st.markdown(f"**Бюджет:** {d.get('budget', 0):,.0f} руб.".replace(",", " "))
            ps = d.get("payment_status", "Не оплачено")
            mgr_options_dd = get_managers_list()
            current_mgr_dd = d.get("manager", "")
            current_idx_dd = mgr_options_dd.index(current_mgr_dd) if current_mgr_dd in mgr_options_dd else 0
            _pay_col, _mgr_col = st.columns(2)
            with _pay_col:
                inject_payment_container_css(deal_id, ps)
                with st.container(key=f"ps_wrap_{deal_id}"):
                    new_ps = st.selectbox("Статус оплаты:", ["Не оплачено", "Оплачено"], index=0 if ps == "Не оплачено" else 1, key=f"dls_ps_{deal_id}")
            with _mgr_col:
                new_mgr_dd = st.selectbox("Ответственный:", mgr_options_dd, index=current_idx_dd, key=f"deal_mgr_inline_{deal_id}", placeholder=MGR_PLACEHOLDER)
            if new_ps != ps:
                d["payment_status"] = new_ps
                d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Статус оплаты обновлён")
            if new_mgr_dd != current_mgr_dd and new_mgr_dd:
                d["manager"] = new_mgr_dd
                d["delegated_to"] = new_mgr_dd
                d["last_modified"] = now_str()
                add_notification(new_mgr_dd, f"Вам делегирована сделка №{d.get('deal_number', deal_id)}: {d.get('deal_title', '')}", f"📌 Вам делегирована сделка №{d.get('deal_number', deal_id)}: {d.get('deal_title', '')}")
                commit_and_rerun(st.session_state.crm_store, "Ответственный обновлён")
            show_edit_deal = st.session_state.get(f"dls_show_edit_{deal_id}", False)
            if show_edit_deal:
                et = st.text_input("Тема:", value=d.get("deal_title", ""), key=f"dls_et_{deal_id}")
                eb = st.text_input("Бюджет (руб.):", value=str(d.get("budget", 0)) if d.get("budget", 0) > 0 else "", key=f"dls_eb_{deal_id}", placeholder="Введите сумму")
                _dds_col, _ddc_col = st.columns(2)
                with _dds_col:
                    if st.button("Сохранить", key=f"dls_es_{deal_id}", use_container_width=True, type="primary"):
                        d["deal_title"] = et
                        d["budget"] = int(eb) if eb and eb.strip().isdigit() else 0
                        d["last_modified"] = now_str()
                        d.setdefault("change_log", []).append({"date": now_str(), "author": st.session_state.get("user_name", st.session_state.get("user_login", "")), "fields": "Тема, бюджет"})
                        st.session_state[f"dls_show_edit_{deal_id}"] = False
                        commit_and_rerun(st.session_state.crm_store, "Сделка обновлена")
                with _ddc_col:
                    if st.button("Отменить", key=f"dls_ec_{deal_id}", use_container_width=True):
                        st.session_state[f"dls_show_edit_{deal_id}"] = False
                        _smart_rerun()
            else:
                pencil_deal_key = f"btn_pencil_deal_{deal_id}"
                st.markdown(f"<style>.st-key-{pencil_deal_key} button {{ padding: 2px 8px !important; font-size: 0.85rem !important; min-height: 32px !important; }}</style>", unsafe_allow_html=True)
                if st.button("\u270e", key=pencil_deal_key):
                    st.session_state[f"dls_show_edit_{deal_id}"] = True
                    _smart_rerun()
            st.markdown("---")
            action_key = f"dls_action_{deal_id}"
            action = st.session_state.get(action_key)
            current_status = d.get("status", "Новый")
            if current_status == "Новый":
                if st.button("Взять в работу", key=f"dls_take_{deal_id}", use_container_width=True, type="primary"):
                    d["status"] = "В работе"
                    if not d.get("manager"):
                        d["manager"] = cu
                    d["last_modified"] = now_str()
                    commit_and_rerun(st.session_state.crm_store, "Сделка взята в работу")
            elif current_status == "В работе":
                st.markdown("<div style='font-size:1rem;font-weight:600;margin:0.4rem 0;'>Статус: В работе</div>", unsafe_allow_html=True)
            elif current_status in ("Сделка закрыта", "Архив"):
                if st.button("Вернуть в работу", key=f"dls_reopen_{deal_id}", use_container_width=True):
                    d["status"] = "В работе"
                    d["last_modified"] = now_str()
                    commit_and_rerun(st.session_state.crm_store, "Сделка возвращена")
            if current_status == "Сделка закрыта" and d.get("close_report"):
                st.markdown("---")
                st.markdown(f"**Отчёт:** {d.get('close_report')}")
                if d.get("close_files"):
                    render_file_thumbs(d["close_files"], f"dls_cf_{deal_id}")
            if current_status == "Архив" and d.get("archive_report"):
                st.markdown("---")
                st.markdown(f"**Отчёт:** {d.get('archive_report')}")
                if d.get("archive_files"):
                    render_file_thumbs(d["archive_files"], f"dls_af_{deal_id}")
            render_entity_chat(d, "deal", deal_id)
            if current_status == "В работе":
                st.markdown("---")
                if st.button("Успешно завершена", key=f"dls_close_{deal_id}", use_container_width=True, type="primary"):
                    _push_dialog_return()
                    st.session_state["dialog_deal_report"] = {"deal_id": deal_id, "action": "close"}
                    st.rerun()
                if st.button("В архив", key=f"dls_arch_{deal_id}", use_container_width=True):
                    _push_dialog_return()
                    st.session_state["dialog_deal_report"] = {"deal_id": deal_id, "action": "archive"}
                    st.rerun()
            if st.session_state.user_role == "admin":
                st.markdown("---")
                if st.button("Удалить сделку", key=f"dls_del_{deal_id}", use_container_width=True):
                    st.session_state.crm_store["deals"] = [x for x in st.session_state.crm_store["deals"] if x["id"] != deal_id]
                    st.session_state.pop("dialog_deal_key", None)
                    st.session_state.pop("_open_created_deal", None)
                    st.session_state["_in_dialog"] = False
                    commit_and_rerun(st.session_state.crm_store, "Сделка удалена")
            render_reminders("deal", deal_id, f"Сделка №{d.get('deal_number', d.get('title', deal_id))}", f"deal_{key_prefix}")
        with right_col:
            if d.get("deal_comments"):
                st.markdown("**Комментарии:**")
                for cm in d["deal_comments"]:
                    st.markdown(f"- *{cm.get('time', '')}*: {linkify_text(cm.get('text', ''))}", unsafe_allow_html=True)
            dc_clr_key = f"dls_clr_dc_{deal_id}"
            if st.session_state.get(dc_clr_key):
                st.session_state[f"dls_dc_input_{deal_id}"] = ""
                st.session_state[dc_clr_key] = False
            nc = st.text_area("Комментарий:", key=f"dls_dc_input_{deal_id}", placeholder="Введите новый комментарий...", height=68, label_visibility="collapsed")
            _dcc1, _dcc_btn, _dcc2 = st.columns([1, 2, 1])
            with _dcc_btn:
                _dcc_clicked = st.button("Добавить", key=f"dls_dc_btn_{deal_id}", use_container_width=True)
            if _dcc_clicked:
                if nc.strip():
                    d.setdefault("deal_comments", []).append({"time": moscow_now().strftime("%d.%m.%Y %H:%M"), "text": nc.strip()})
                    d["last_modified"] = now_str()
                    st.session_state[dc_clr_key] = True
                    commit_and_rerun(st.session_state.crm_store, "Комментарий добавлен")
                else:
                    st.warning("Введите текст")
            st.markdown("---")
            st.markdown("<div style='text-align:left;width:100%;'>**Файлы сделки:**</div>", unsafe_allow_html=True)
            st.markdown(f"<style>.st-key-deal_detail_{key_prefix} .st-key-dls_file_{deal_id} {{ margin-left:0!important; justify-content:flex-start!important; text-align:left!important; }}</style>", unsafe_allow_html=True)
            render_file_thumbs(d.get("deal_files", []), f"dls_file_{deal_id}", allow_delete=True)
            st.markdown("**Загрузить файлы:**")
            df_ver = st.session_state.deal_file_uploader_ver.get(f"tab_{deal_id}", 0)
            udf = st.file_uploader("Выберите файлы:", key=f"dls_up_{deal_id}_{df_ver}", accept_multiple_files=True, label_visibility="collapsed")
            _du1, _du_btn, _du2 = st.columns([1, 2, 1])
            with _du_btn:
                _du_clicked = st.button("Загрузить", key=f"dls_upbtn_{deal_id}", use_container_width=True)
            if _du_clicked:
                if udf:
                    with st.spinner("Загрузка файлов..."):
                        fi_list = save_uploaded_files(udf, d["client_id"], "deal_file")
                    if fi_list:
                        d.setdefault("deal_files", []).extend(normalize_file_list(fi_list))
                        d["last_modified"] = now_str()
                        st.session_state.deal_file_uploader_ver[f"tab_{deal_id}"] = df_ver + 1
                        save_data(st.session_state.crm_store)
                        st.toast("Файлы загружены", icon="\U0001F4C1")
                        _smart_rerun()
                else:
                    st.warning("Выберите файл(ы)")
            st.markdown("---")
            _dls_ct_key = f"dls_show_ct_{deal_id}"
            if st.button("Создать задачу по сделке", key=f"dls_btn_ct_detail_{deal_id}", use_container_width=True, type="primary"):
                _push_dialog_return()
                st.session_state["dialog_create_deal_task_deal_id"] = deal_id
                st.session_state["dialog_create_deal_task_client_id"] = d["client_id"]
                st.rerun()
            st.markdown("---")
            render_deal_products_block(d, key_prefix)
            st.markdown("---")
            st.markdown("**Внесённые изменения**")
            _deal_changes = d.get("change_log", [])
            if _deal_changes:
                for _chg in reversed(_deal_changes[-20:]):
                    st.markdown(f"<div class='created-date'>{_chg.get('date', '')} | {_chg.get('author', '')} — {_chg.get('fields', '')}</div>", unsafe_allow_html=True)
            else:
                st.caption("История изменений появится после редактирования сделки.")


def render_client_card_expanded(cl):
    with st.container(border=True):
        # Две колонки: заголовок и информация слева, комментарии и файлы справа
        show_edit = st.session_state.get(f"show_edit_{cl['id']}", False)
        _left_col, _right_col = st.columns(2)
        with _left_col:
            st.subheader(cl.get('name', ''))
            st.markdown(format_created_date(cl), unsafe_allow_html=True)
            if show_edit:
                # Inline editing — поля становятся редактируемыми
                en = st.text_input("ФИО / Компания", value=cl['name'], key=f"en_{cl['id']}")
                st.markdown("---")
                st.markdown("**Информация о клиенте:**")
                ep = st.text_input("Телефон", value=cl['phone'], key=f"ep_{cl['id']}")
                cm_edit_idx = CONTACT_METHODS.index(cl.get('contact_method', '')) if cl.get('contact_method', '') in CONTACT_METHODS else 0
                cm_edit = st.selectbox("Предпочтительный способ связи:", CONTACT_METHODS, index=cm_edit_idx, key=f"cm_edit_{cl['id']}", placeholder="Выбери вариант...")
                ee = st.text_input("Email", value=cl.get('email', ''), key=f"ee_{cl['id']}")
                city_val = st.text_input("Город", value=cl.get('city', ''), key=f"city_{cl['id']}")
                ea_val = st.text_input("Основной адрес", value=cl.get('address', ''), key=f"ea_{cl['id']}")
                ed = st.number_input("Скидка (%)", min_value=0, max_value=100, value=int(cl.get('discount', 0)), key=f"ed_{cl['id']}")
                _cat_col, _promo_col = st.columns(2)
                with _cat_col:
                    ec_idx = CATEGORIES.index(cl.get('category', 'Не определён')) if cl.get('category', 'Не определён') in CATEGORIES else 0
                    ec = st.selectbox("Категория", CATEGORIES, index=ec_idx, key=f"ec_{cl['id']}")
                with _promo_col:
                    promo_code = st.text_input("Промокод", value=cl.get('promo_code', ''), key=f"promo_code_{cl['id']}")
                em = st.selectbox("Ответственный:", get_managers_list(), index=0 if cl.get('manager', '') not in get_managers_list() else (get_managers_list()).index(cl.get('manager', '')), key=f"em_{cl['id']}", placeholder=MGR_PLACEHOLDER)
                st.markdown("---")
                # Доп. телефоны, Email, адреса — те же, что в окне создания клиента
                _eph, _eem, _ead = st.columns(3)
                with _eph:
                    st.markdown("**Доп. телефоны**")
                    _ep_list = cl.get('extra_phones', [])
                    for i, p in enumerate(_ep_list):
                        p['phone'] = st.text_input(f"Телефон #{i+1}", value=p.get('phone', ''), key=f"ep_phone_{cl['id']}_{i}")
                        p['name'] = st.text_input(f"ФИО #{i+1}", value=p.get('name', ''), key=f"ep_name_{cl['id']}_{i}")
                        p['role'] = st.text_input(f"Должность #{i+1}", value=p.get('role', ''), key=f"ep_role_{cl['id']}_{i}")
                    _add_ep_key = f"add_ep_btn_{cl['id']}"
                    if st.button("Добавить телефон", key=_add_ep_key):
                        cl.setdefault('extra_phones', []).append({"phone": "", "name": "", "role": ""})
                        st.rerun()
                with _eem:
                    st.markdown("**Доп. Email**")
                    _ee_list = cl.get('extra_emails', [])
                    for i, e in enumerate(_ee_list):
                        cl['extra_emails'][i] = st.text_input(f"Email #{i+1}", value=e, key=f"ee_val_{cl['id']}_{i}")
                    _add_ee_key = f"add_ee_btn_{cl['id']}"
                    if st.button("Добавить Email", key=_add_ee_key):
                        cl.setdefault('extra_emails', []).append("")
                        st.rerun()
                with _ead:
                    st.markdown("**Доп. адреса**")
                    _ea_list = cl.get('extra_addresses', [])
                    for i, a in enumerate(_ea_list):
                        if isinstance(a, dict):
                            a['address'] = st.text_input(f"Адрес #{i+1}", value=a.get('address', ''), key=f"ea_addr_{cl['id']}_{i}")
                            a['resp_name'] = st.text_input(f"Ответственный #{i+1}", value=a.get('resp_name', ''), key=f"ea_rn_{cl['id']}_{i}")
                            a['resp_role'] = st.text_input(f"Должность #{i+1}", value=a.get('resp_role', ''), key=f"ea_rr_{cl['id']}_{i}")
                            a['resp_phone'] = st.text_input(f"Телефон #{i+1}", value=a.get('resp_phone', ''), key=f"ea_rp_{cl['id']}_{i}")
                            a['resp_email'] = st.text_input(f"Email #{i+1}", value=a.get('resp_email', ''), key=f"ea_re_{cl['id']}_{i}")
                    _add_ea_key = f"add_ea_btn_{cl['id']}"
                    if st.button("Добавить адрес", key=_add_ea_key):
                        cl.setdefault('extra_addresses', []).append({"address": "", "resp_name": "", "resp_role": "", "resp_phone": "", "resp_email": ""})
                        st.rerun()
                st.markdown("---")
                _ces_col, _cec_col = st.columns(2)
                with _ces_col:
                    if st.button("Сохранить", key=f"es_{cl['id']}", use_container_width=True, type="primary"):
                        cl['name'] = en
                        cl['phone'] = format_phone(ep)
                        cl['contact_method'] = cm_edit
                        cl['email'] = ee
                        cl['city'] = city_val.strip()
                        cl['address'] = ea_val
                        cl['discount'] = int(ed)
                        cl['category'] = ec
                        cl['promo_code'] = promo_code.strip()
                        cl['manager'] = em
                        # Доп. телефоны, email, адреса уже обновлены через session_state
                        cl["last_modified"] = now_str()
                        _actor = st.session_state.get("user_name", st.session_state.get("user_login", ""))
                        cl.setdefault("change_log", []).append({"date": now_str(), "author": _actor, "fields": "ФИО / Компания, телефон, способ связи, email, адрес, скидка, категория, ответственный"})
                        st.session_state[f"show_edit_{cl['id']}"] = False
                        commit_and_rerun(st.session_state.crm_store, "Данные клиента сохранены")
                with _cec_col:
                    if st.button("Отменить", key=f"ec_cancel_{cl['id']}", use_container_width=True):
                        st.session_state[f"show_edit_{cl['id']}"] = False
                        st.rerun()
                if st.session_state.user_role == "admin":
                    st.markdown("---")
                    cdl = st.checkbox("Подтверждаю удаление клиента", key=f"cdl_{cl['id']}")
                    if cdl and st.button("Удалить клиента", key=f"del_cli_{cl['id']}", use_container_width=True, type="primary"):
                        st.session_state.crm_store["deals"] = [d for d in st.session_state.crm_store["deals"] if d["client_id"] != cl["id"]]
                        st.session_state.crm_store["clients"] = [c for c in st.session_state.crm_store["clients"] if c["id"] != cl["id"]]
                        st.session_state.expanded_client_id = None
                        st.session_state.pop("dialog_client_key", None)
                        st.session_state["_in_dialog"] = False
                        commit_and_rerun(st.session_state.crm_store, "Клиент удалён")
            else:
                # Категория и промокод в одной строке
                _cat_view, _promo_view = st.columns(2)
                with _cat_view:
                    st.markdown(f"Категория: **{cl.get('category', 'Не определён')}**")
                with _promo_view:
                    st.markdown(f"Промокод: **{cl.get('promo_code', '') or '—'}**")
                st.markdown("---")
                st.markdown("**Информация о клиенте:**")
                st.markdown(f"Телефон: **{cl.get('phone', '')}**")
                cm_idx = CONTACT_METHODS.index(cl.get('contact_method', '')) if cl.get('contact_method', '') in CONTACT_METHODS else 0
                _cm_left, _cm_right = st.columns(2)
                with _cm_left:
                    cm = st.selectbox("Предпочтительный способ связи:", CONTACT_METHODS, index=cm_idx, key=f"cm_{cl['id']}", placeholder="Выбери вариант...")
                if cm != cl.get('contact_method', ''):
                    cl['contact_method'] = cm
                    cl["last_modified"] = now_str()
                    save_data(st.session_state.crm_store)
                st.markdown(f"Email: **{cl.get('email','')}**")
                st.markdown(f"Город: **{cl.get('city','—') or '—'}**")
                st.markdown(f"Основной адрес: **{cl.get('address','')}**")
                st.markdown(f"Скидка: **{cl.get('discount',0)}%**")
                st.markdown(f"Ответственный: **{cl.get('manager','—')}**")
                cph = re.sub(r"\D", "", cl['phone'])
                if cph.startswith("8") and len(cph) == 11: cph = "7" + cph[1:]
                elif not cph: cph = "79990000000"
                mc1, mc2, mc3 = st.columns(3)
                mc1.link_button("WhatsApp", f"https://wa.me/{cph}", use_container_width=True)
                mc2.link_button("Telegram", f"https://t.me/+{cph}", use_container_width=True)
                mc3.link_button("MAX", MAX_URL, use_container_width=True)
                if cl.get("extra_phones"):
                    st.markdown("**Доп. телефоны:**")
                    for pi, p in enumerate(cl["extra_phones"]):
                        st.markdown(f"- {p['phone']} — {p['name']} ({p['role']})")
                if cl.get("extra_addresses"):
                    st.markdown("**Доп. адреса:**")
                    for ea in cl["extra_addresses"]:
                        if isinstance(ea, dict):
                            st.markdown(f"- **{ea.get('address', '')}** {ea.get('resp_name', '')} {ea.get('resp_phone', '')}")
            # Кнопка редактирования между информацией и чатом
            if not show_edit:
                pencil_cli_key = f"btn_pencil_cli_{cl['id']}"
                st.markdown(f"<style>.st-key-{pencil_cli_key} button {{ padding: 2px 8px !important; font-size: 0.85rem !important; min-height: 32px !important; }}</style>", unsafe_allow_html=True)
                if st.button("✎", key=pencil_cli_key, help="Редактировать карточку клиента"):

                    st.session_state[f"show_edit_{cl['id']}"] = True
                    st.rerun()
            # Разделитель под кнопкой редактирования
            st.markdown("---")
            # Чат в левом столбце под информацией
            render_entity_chat(cl, "client", cl["id"])
            render_reminders("client", cl.get("id", ""), cl.get("name", "Клиент"), f"client_{cl.get('id')}")
        with _right_col:
            st.markdown("**Комментарии:**")
            for cc in cl.get("client_comments", []):
                st.markdown(f"- *{cc.get('time', '')}*: {linkify_text(cc.get('text', ''))}", unsafe_allow_html=True)
            if not cl.get("client_comments"): st.caption("Пока нет комментариев")
            cc_clr_key = f"clr_cc_{cl['id']}"
            if st.session_state.get(cc_clr_key):
                st.session_state[f"new_cc_input_{cl['id']}"] = ""
                st.session_state[cc_clr_key] = False
            nci = st.text_area("Комментарий:", key=f"new_cc_input_{cl['id']}", placeholder="Введите новый комментарий...", height=68, label_visibility="collapsed")
            _cc_sp1, _cc_btn_col, _cc_sp2 = st.columns([1, 2, 1])
            with _cc_btn_col:
                _cc_clicked = st.button("Добавить комментарий", key=f"cc_btn_{cl['id']}", use_container_width=True)
            if _cc_clicked:
                if nci.strip():
                    cl.setdefault("client_comments", []).append({"time": moscow_now().strftime("%d.%m.%Y %H:%M"), "text": nci.strip()})
                    cl["last_modified"] = now_str()
                    st.session_state[cc_clr_key] = True
                    commit_and_rerun(st.session_state.crm_store, "Комментарий добавлен")
                else: st.warning("Введите текст")
            # Разделитель перед файлами
            st.markdown("---")
            st.markdown("**Файлы:**")
            render_file_thumbs(cl.get("client_files", []), f"cli_{cl['id']}", allow_delete=True)
            st.markdown("**Загрузить файлы:**")
            ucf = st.file_uploader("Выберите файлы:", key=f"cf_up_{cl['id']}", accept_multiple_files=True, label_visibility="collapsed")
            _sf_sp1, _sf_btn_col, _sf_sp2 = st.columns([1, 2, 1])
            with _sf_btn_col:
                _sf_clicked = st.button("Сохранить файлы", key=f"cf_btn_{cl['id']}", use_container_width=True)
            if _sf_clicked:
                if ucf:
                    with st.spinner("Загрузка файлов..."):
                        fi_list = save_uploaded_files(ucf, cl["id"], "profile")
                    if fi_list:
                        cl.setdefault("client_files", []).extend(normalize_file_list(fi_list))
                        cl["last_modified"] = now_str()
                        save_data(st.session_state.crm_store)
                        st.toast("Файлы сохранены", icon="\U0001F4C1")
                        st.rerun()
                else: st.warning("Выберите файл(ы)")
            st.markdown("---")
            # Кнопки создания сделки и задачи
            _bc1, _bc2 = st.columns(2)
            with _bc1:
                if st.button("Создать задачу по клиенту", key=f"rcc_task_{cl['id']}", use_container_width=True, type="primary"):
                    _push_dialog_return()
                    st.session_state["dialog_create_client_task_client_id"] = cl["id"]
                    st.session_state.pop("dialog_client_key", None)
                    st.rerun()
            with _bc2:
                if st.button("Создать сделку", key=f"rcc_deal_{cl['id']}", use_container_width=True, type="primary"):
                    _push_dialog_return()
                    st.session_state["dialog_create_deal_from_client"] = cl["id"]
                    st.session_state.pop("dialog_client_key", None)
                    st.rerun()
            # Реквизиты для документов — между действиями и историей изменений.
            st.markdown("---")
            st.markdown("**Реквизиты для документов**")
            _reqs = cl.setdefault("requisites", [])
            if not _reqs:
                st.caption("Реквизиты плательщика пока не добавлены.")
            for _ri, _req in enumerate(_reqs):
                _req_cols = st.columns([3.2, 1.1, 1.1])
                _req_name = str(_req.get("legal_name", "Реквизиты без названия"))
                with _req_cols[0]:
                    if _req.get("deleted"):
                        st.markdown(f"<div style='text-decoration:line-through;color:#9299A3;padding:0.35rem 0'>{html.escape(_req_name)} (удалены)</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='padding:0.35rem 0;font-weight:500'>{html.escape(_req_name)}</div>", unsafe_allow_html=True)
                with _req_cols[1]:
                    if not _req.get("deleted") and st.button("Открыть", key=f"client_req_open_{cl['id']}_{_req.get('id',_ri)}", use_container_width=True):
                        _push_dialog_return()
                        st.session_state["dialog_client_requisites_client_id"] = cl["id"]
                        st.session_state["dialog_client_requisites_return_to_invoice"] = False
                        client_requisites_dialog(cl["id"], False, _req.get("id"))
                with _req_cols[2]:
                    if not _req.get("deleted") and st.button("Удалить", key=f"client_req_del_{cl['id']}_{_req.get('id',_ri)}", use_container_width=True):
                        _req["deleted"] = True
                        _req["deleted_at"] = now_str()
                        _req["deleted_by"] = st.session_state.get("user_name", st.session_state.get("user_login", ""))
                        cl["last_modified"] = now_str()
                        cl.setdefault("change_log", []).append({"date": now_str(), "author": st.session_state.get("user_name", st.session_state.get("user_login", "")), "fields": f"Реквизиты «{_req_name}» помечены удалёнными"})
                        save_data(st.session_state.crm_store)
                        st.rerun()
            if st.button("Добавить реквизиты", key=f"client_req_add_{cl['id']}", use_container_width=True, type="primary"):
                _push_dialog_return()
                st.session_state["dialog_client_requisites_client_id"] = cl["id"]
                st.session_state["dialog_client_requisites_return_to_invoice"] = False
                client_requisites_dialog(cl["id"], False)
            # История изменений — после реквизитов
            st.markdown("---")
            st.markdown("**Внесённые изменения**")
            _client_changes = cl.get("change_log", [])
            if _client_changes:
                for _chg in reversed(_client_changes[-20:]):
                    st.markdown(f"<div class='created-date'>{_chg.get('date', '')} | {_chg.get('author', '')} — {_chg.get('fields', '')}</div>", unsafe_allow_html=True)
            else:
                st.caption("История изменений появится после редактирования карточки.")

def render_client_in_tree(cl):
    is_cl_exp = st.session_state.expanded_client_id == cl["id"]
    is_cl_deals_exp = st.session_state.expanded_tree_id == cl["id"]
    cl_tasks_all = cl.get("tasks", [])
    cl_deals = [d for d in st.session_state.crm_store["deals"] if d["client_id"] == cl["id"]]
    all_tasks_for_border = cl_tasks_all + [t for d in cl_deals for t in cl.get("tasks", []) if t.get("deal_id") == d["id"]]
    cl_bg, cl_bc = get_entity_border(all_tasks_for_border)
    cl_label = f"{cl['name']} — {cl['phone']} [{cl.get('category', 'Не определён')}] | Сделок: {len(cl_deals)} | Задач: {len(cl_tasks_all)}"
    if not cl.get("viewed", False):
        cl_label = f"🟠 {cl_label}"
    cl_selected = is_cl_exp or is_cl_deals_exp
    cl_border = "#2196F3" if cl_selected else cl_bc
    cl_shadow = "box-shadow: 0 0 0 2px rgba(33,150,243,0.3);" if cl_selected else ""
    st.markdown(f"<style>.st-key-cl_btn_wrap_{cl['id']} button {{ background-color: {cl_bg} !important; color: {'#FF6D00' if not cl.get('viewed', False) else '#2C3E50'} !important; border: 2px solid {cl_border} !important; border-radius: 10px !important; {cl_shadow} {'font-weight:800!important;text-decoration:underline!important;' if not cl.get('viewed', False) else ''} }}</style>", unsafe_allow_html=True)

    ac, bc = st.columns([1, 30])
    with ac:
        with st.container(key=f"arr_cl_{cl['id']}"):
            if st.button("▾" if is_cl_deals_exp else "▸", key=f"cl_arrow_{cl['id']}", use_container_width=True):
                if is_cl_deals_exp:
                    st.session_state.expanded_tree_id = None
                    save_scroll_and_rerun()
                else:
                    st.session_state.expanded_tree_id = cl["id"]
                    st.rerun()
            if not is_cl_deals_exp:
                render_scroll_restore(f"arr_{cl['id']}")
    with bc:
        with st.container(key=f"cl_btn_wrap_{cl['id']}"):
            if st.button(cl_label, key=f"cl_card_{cl['id']}", use_container_width=True, type="primary" if is_cl_exp else "secondary"):
                if is_cl_exp:
                    st.session_state.expanded_client_id = None
                    save_scroll_and_rerun()
                else:
                    st.session_state.expanded_client_id = cl["id"]
                    cl["viewed"] = True
                    st.session_state.expanded_deal_id = None
                    st.session_state.expanded_task_key = None
                    save_data(st.session_state.crm_store)
                    st.rerun()
            if not is_cl_exp:
                render_scroll_restore(f"cl_{cl['id']}")

    if is_cl_exp:
        render_client_card_expanded(cl)

    if is_cl_deals_exp:
        client_only_tasks = [t for t in cl_tasks_all if not t.get("deal_id")]
        with indented(0.06):
            render_centered_title(f"Задачи по клиенту ({len(client_only_tasks)})")
            if client_only_tasks:
                client_only_tasks.sort(key=lambda t: get_sort_key(t), reverse=True)
                for ti, t in enumerate(client_only_tasks):
                    task_key = f"cl_{cl['id']}_{ti}"
                    render_task_row(t, cl, None, task_key, f"cl_{cl['id']}_{ti}")
            show_ct_key = f"show_ct_cl_{cl['id']}"
            if render_centered_button("Создать задачу по клиенту", key=f"btn_ct_cl_{cl['id']}"):
                st.session_state[show_ct_key] = not st.session_state.get(show_ct_key, False)
                st.rerun()
        if st.session_state.get(show_ct_key, False):
            with st.container(border=True):
                if render_task_form(None, cl["id"], f"cl_{cl['id']}"):
                    st.session_state[show_ct_key] = False
                    commit_and_rerun(st.session_state.crm_store, "Задача создана")

        render_separator()

        render_centered_title(f"Сделки по клиенту ({len(cl_deals)})")
        if cl_deals:
            cl_deals.sort(key=lambda d: get_sort_key(d), reverse=True)
            for d in cl_deals:
                render_deal_in_tree(d, cl)
        else:
            with indented(0.03):
                st.caption("Сделок нет")

        render_separator()

        show_cd_key = f"show_cd_cl_{cl['id']}"
        if render_centered_button("Создать новую сделку", key=f"btn_cd_cl_{cl['id']}"):
            st.session_state[show_cd_key] = not st.session_state.get(show_cd_key, False)
            st.rerun()
        if st.session_state.get(show_cd_key, False):
            with st.container(border=True):
                cd_title = st.text_input("Тема:", key=f"cd_title_{cl['id']}")
                cd_budget = st.text_input("Бюджет (руб.):", value="", key=f"cd_budget_{cl['id']}", placeholder="Введите сумму")
                cd_mgr = st.selectbox("Ответственный:", get_managers_list(), index=0, key=f"cd_mgr_{cl['id']}", placeholder=MGR_PLACEHOLDER)
                cd_ps = st.selectbox("Статус оплаты:", ["Не оплачено", "Оплачено"], index=0, key=f"cd_ps_{cl['id']}")
                if st.button("Создать", key=f"cd_go_{cl['id']}", use_container_width=True, type="primary"):
                    if not cd_mgr:
                        st.warning("Выберите ответственного")
                    else:
                        deals = st.session_state.crm_store.get("deals", [])
                        did = f"deal_{moscow_now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
                        dn = generate_deal_number()
                        new_deal = {"id": did, "client_id": cl["id"], "title": dn, "deal_number": dn, "deal_title": cd_title.strip(), "budget": int(cd_budget) if cd_budget and cd_budget.strip().isdigit() else 0, "status": "В работе", "manager": cd_mgr, "deal_comments": [], "deal_files": [], "payment_status": cd_ps, "close_files": [], "archive_files": [], "last_modified": now_str(), "created_at": now_str(), "created_by": st.session_state.get("user_login", ""), "change_log": [], "deal_chat": []}
                        st.session_state.crm_store.setdefault("deals", []).append(new_deal)
                        cl["last_modified"] = now_str()
                        st.session_state[show_cd_key] = False
                        st.session_state.auto_expand_deal_id = did
                        commit_and_rerun(st.session_state.crm_store, "Сделка создана")

def render_client_form(fv):
    if st.button("Добавить клиента", key=f"add_client_btn_top_{fv}", type="primary", use_container_width=False):
        st.session_state[f"show_add_client_dialog_{fv}"] = True
        st.rerun()
    if st.session_state.get(f"show_add_client_dialog_{fv}", False):
        add_client_dialog(fv)

@_crm_dialog("Добавить клиента", width="large")
def add_client_dialog(fv):
    _add_close_warning_key = f"_show_close_warning_add_client_{fv}"
    _show_add_warning = st.session_state.get(_add_close_warning_key, False)
    _dc_col1, _dc_col2 = st.columns([20, 1])
    with _dc_col2:
        if st.button("✕", key=f"add_client_close_{fv}"):
            # Check for unsaved changes
            _has_unsaved = (
                st.session_state.get(f"cn_{fv}", "").strip() or
                st.session_state.get(f"cp_{fv}", "").strip() or
                st.session_state.get(f"cpromo_{fv}", "").strip() or
                st.session_state.get(f"ce_{fv}", "").strip() or
                st.session_state.get(f"city_new_{fv}", "").strip() or
                st.session_state.get(f"ca_{fv}", "").strip() or
                st.session_state.get(f"new_cc_form_{fv}", "").strip() or
                st.session_state.get("pending_client_comments") or
                any(p.get("phone", "").strip() for p in st.session_state.get("f_ph", [])) or
                any(e.strip() for e in st.session_state.get("f_em", [])) or
                any(a.get("address", "").strip() for a in st.session_state.get("f_ad", []))
            )
            if _has_unsaved and not _show_add_warning:
                st.session_state[_add_close_warning_key] = True
                st.rerun()
            else:
                st.session_state[_add_close_warning_key] = False
                st.session_state[f"show_add_client_dialog_{fv}"] = False
                st.session_state.f_ph, st.session_state.f_em, st.session_state.f_ad = [], [], []
                st.session_state.pop("pending_client_comments", None)
                st.rerun()
    if _show_add_warning:
        _warn_key = f"unsaved_warn_add_{fv}"
        st.markdown(f'<style>.st-key-{_warn_key} {{ border:2px solid #FF9800!important;border-radius:10px!important;background-color:#FFF8E1!important;padding:0.5rem 0.8rem!important;margin:0.3rem 0!important; }}</style>', unsafe_allow_html=True)
        with st.container(key=_warn_key):
            st.markdown("**⚠️ Есть несохранённые изменения**")
            st.markdown("Закрыть без сохранения?")
            _wcol1, _wcol2 = st.columns(2)
            with _wcol1:
                if st.button("Без сохранения", key=f"add_warn_nosave_{fv}", use_container_width=True):
                    st.session_state[_add_close_warning_key] = False
                    st.session_state[f"show_add_client_dialog_{fv}"] = False
                    st.session_state.f_ph, st.session_state.f_em, st.session_state.f_ad = [], [], []
                    st.session_state.pop("pending_client_comments", None)
                    st.rerun()
            with _wcol2:
                if st.button("Отмена", key=f"add_warn_cancel_{fv}", use_container_width=True):
                    st.session_state[_add_close_warning_key] = False
                    st.rerun()
    acl, acr = st.columns(2)
    with acl:
        cn = st.text_input("ФИО / Компания", key=f"cn_{fv}")
        cp = st.text_input("Основной телефон", key=f"cp_{fv}")
        ce = st.text_input("Основной Email", key=f"ce_{fv}")
        cd_cc1, cd_cc2, cd_cc3 = st.columns([1, 1.2, 1])
        with cd_cc1:
            cd = st.number_input("Скидка (%)", min_value=0, max_value=100, step=1, value=None, key=f"cd_{fv}", label_visibility="visible")
        with cd_cc2:
            cc = st.selectbox("Категория", [""] + CATEGORIES, index=0, key=f"cc_{fv}", placeholder="Выбери категорию")
        with cd_cc3:
            cpromo = st.text_input("Промокод", key=f"cpromo_{fv}", placeholder="Введите промокод")
        cm = st.selectbox("Ответственный:", get_managers_list(), index=0, key=f"cm_{fv}", placeholder=MGR_PLACEHOLDER)
        contact_method_new = st.selectbox("Предпочтительный способ связи:", [""] + CONTACT_METHODS, index=0, key=f"new_contact_method_{fv}", placeholder="Выберите способ связи")
        city_new = st.text_input("Город", key=f"city_new_{fv}", placeholder="Введите город")
        ca = st.text_area("Основной адрес", key=f"ca_{fv}", height=68)
    with acr:
        with st.container(border=True):
            st.markdown("**Комментарии:**")
            cc_form_clr = f"clr_cc_form_{fv}"
            if st.session_state.get(cc_form_clr):
                st.session_state[f"new_cc_form_{fv}"] = ""
                st.session_state[cc_form_clr] = False
            ncc = st.text_area("Комментарий:", key=f"new_cc_form_{fv}", placeholder="Введите новый комментарий...", height=68, label_visibility="collapsed")
            _fcc1, _fcc_btn, _fcc2 = st.columns([1, 2, 1])
            with _fcc_btn:
                _fcc_clicked = st.button("Добавить комментарий", key=f"cc_form_btn_{fv}", use_container_width=True)
            if _fcc_clicked:
                if ncc.strip():
                    st.session_state.setdefault("pending_client_comments", []).append({"time": moscow_now().strftime("%d.%m.%Y %H:%M"), "text": ncc.strip()})
                    st.session_state[cc_form_clr] = True
                    st.rerun()
                else: st.warning("Введите текст")
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
            st.rerun()
    with ac_em:
        st.markdown("**Доп. Email**")
        for i, em in enumerate(st.session_state.f_em):
            st.session_state.f_em[i] = st.text_input(f"Email #{i+1}", value=em, key=f"f_em_{fv}_{i}")
        if st.button("Добавить Email", key=f"add_em_btn_{fv}"):
            st.session_state.f_em.append("")
            st.rerun()
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
            st.rerun()
    st.markdown("---")
    _files_left, _files_right = st.columns(2)
    with _files_right:
        with st.container(border=True):
            st.markdown("**Файлы**")
            cf = st.file_uploader("Прикрепить файлы:", key=f"cf_{fv}", accept_multiple_files=True)
    if st.button("Внести клиента в базу", use_container_width=True, type="primary", key=f"add_client_btn_{fv}"):
        if cn and cp:
            if not cm: st.error("Выберите ответственного")
            elif not cc: st.error("Выберите категорию")
            else:
                clients = st.session_state.crm_store["clients"]
                nid = (max([c['id'] for c in clients]) if clients else 0) + 1
                nc = {"id": nid, "name": cn, "phone": format_phone(cp), "email": ce, "city": city_new.strip(), "address": ca, "category": cc, "promo_code": cpromo.strip(), "discount": int(cd) if cd is not None else 0, "base_comment": "", "manager": cm, "contact_method": contact_method_new, "extra_phones": [{"phone": format_phone(p["phone"]), "name": p["name"], "role": p["role"]} for p in st.session_state.f_ph if p["phone"].strip()], "extra_emails": [e for e in st.session_state.f_em if e.strip()], "extra_addresses": [{"address": a["address"], "resp_name": a["resp_name"], "resp_role": a["resp_role"], "resp_phone": a["resp_phone"], "resp_email": a["resp_email"]} for a in st.session_state.f_ad if a["address"].strip()], "client_files": [], "client_comments": [], "comments": [], "tasks": [], "last_modified": now_str(), "created_at": now_str(), "created_by": st.session_state.get("user_login", ""), "viewed": False, "change_log": [], "client_chat": []}
                if cf:
                    fi_list = save_uploaded_files(cf, nid, "profile")
                    if fi_list: nc["client_files"].extend(normalize_file_list(fi_list))
                if st.session_state.get("pending_client_comments"):
                    nc["client_comments"] = list(st.session_state["pending_client_comments"])
                    st.session_state["pending_client_comments"] = []
                st.session_state.crm_store["clients"].append(nc)
                save_data(st.session_state.crm_store)
                st.session_state.f_ph, st.session_state.f_em, st.session_state.f_ad = [], [], []
                st.session_state.last_id = nid
                st.session_state.client_form_version += 1
                st.session_state.expanded_client_id = nid
                st.toast(f"Клиент {cn} добавлен", icon="✅")
                st.rerun()
        else: st.error("Заполните ФИО и телефон")
@_crm_dialog("Подробности задачи", width="large")
def task_detail_dialog(task, cl, d, key_prefix):
    st.session_state["_in_dialog"] = True
    _show_close_warning = st.session_state.get(f"_show_close_warning_{key_prefix}", False)
    _is_editing = st.session_state.get(f"show_edit_task_{key_prefix}", False) or st.session_state.get(f"show_edit_dl_{key_prefix}", False)

    # Close button — right-aligned row under the header
    _close_btn_key = f"close_btn_{key_prefix}"
    _close_css_key = f"close_row_{key_prefix}"
    st.markdown(f'<style>.st-key-{_close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:6px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{_close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{_close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=_close_css_key):
        _print_col, _spacer_col, _close_col = st.columns([1, 20, 1])
        with _print_col:
            render_print_button(task, cl, task.get("type", "Связаться"), format_date(task.get("deadline", "")), f"td_{key_prefix}_top")
        with _close_col:
            if st.button("\u2715", key=_close_btn_key, use_container_width=True):
                if _is_editing and not _show_close_warning:
                    st.session_state[f"_show_close_warning_{key_prefix}"] = True
                    st.rerun()
                else:
                    st.session_state[f"_show_close_warning_{key_prefix}"] = False
                    st.session_state[f"show_edit_task_{key_prefix}"] = False
                    st.session_state[f"show_edit_dl_{key_prefix}"] = False
                    _pop_dialog_return()
                    st.session_state.pop("dialog_task_key", None)
                    st.session_state.pop("dialog_task_number", None)
                    st.session_state.pop("dialog_task_client_id", None)
                    st.session_state.pop("dialog_task_deal_id", None)
                    st.session_state.pop("_open_created_task", None)
                    st.session_state["_in_dialog"] = False
                    st.rerun()

    # Unsaved changes warning
    if _show_close_warning:
        _warn_key = f"unsaved_warn_{key_prefix}"
        st.markdown(f'<style>.st-key-{_warn_key} {{ border:2px solid #FF9800!important;border-radius:10px!important;background-color:#FFF8E1!important;padding:0.5rem 0.8rem!important;margin:0.3rem 0!important; }}</style>', unsafe_allow_html=True)
        with st.container(key=_warn_key):
            st.markdown("**\u26a0\ufe0f \u0415\u0441\u0442\u044c \u043d\u0435\u0441\u043e\u0445\u0440\u0430\u043d\u0451\u043d\u043d\u044b\u0435 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f**")
            st.markdown("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u043f\u0435\u0440\u0435\u0434 \u0437\u0430\u043a\u0440\u044b\u0442\u0438\u0435\u043c?")
            st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
            _wcol1, _wcol2, _wcol3 = st.columns(3)
            with _wcol1:
                if st.button("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", key=f"warn_save_{key_prefix}", type="primary", use_container_width=True):
                    # Read values from session_state widgets
                    _et_topic_key = f"edit_topic_{key_prefix}"
                    _et_type_key = f"edit_type_{key_prefix}"
                    _et_mgr_key = f"edit_mgr_{key_prefix}"
                    _et_comment_key = f"edit_comment_{key_prefix}"
                    if _et_topic_key in st.session_state:
                        t["text"] = st.session_state[_et_topic_key]
                    if _et_type_key in st.session_state:
                        t["type"] = st.session_state[_et_type_key]
                    if _et_mgr_key in st.session_state:
                        _mgr_val = st.session_state[_et_mgr_key]
                        if _mgr_val:
                            t["manager"] = _mgr_val
                            t["delegated_to"] = _mgr_val
                    if _et_comment_key in st.session_state:
                        t["task_comment"] = st.session_state[_et_comment_key]
                    # Extended fields
                    _et_prod_key = f"edit_prod_{key_prefix}"
                    _et_addr_key = f"edit_addr_{key_prefix}"
                    _et_recv_key = f"edit_recv_{key_prefix}"
                    _et_rphone_key = f"edit_rphone_{key_prefix}"
                    _et_pay_key = f"edit_pay_{key_prefix}"
                    _et_amount_key = f"edit_amount_{key_prefix}"
                    _et_tk_key = f"edit_tk_{key_prefix}"
                    if _et_prod_key in st.session_state: t["products"] = st.session_state[_et_prod_key]
                    if _et_addr_key in st.session_state: t["ship_addr"] = st.session_state[_et_addr_key]
                    if _et_recv_key in st.session_state: t["receiver"] = st.session_state[_et_recv_key]
                    if _et_rphone_key in st.session_state: t["receiver_phone"] = st.session_state[_et_rphone_key]
                    if _et_pay_key in st.session_state: t["ship_pay"] = st.session_state[_et_pay_key]
                    if _et_amount_key in st.session_state:
                        _amt = st.session_state[_et_amount_key]
                        t["order_amount"] = int(_amt) if _amt and str(_amt).strip().isdigit() else 0
                    if _et_tk_key in st.session_state: t["tk_num"] = st.session_state[_et_tk_key]
                    # Deadline
                    _dl_key = f"dl_inline_{key_prefix}"
                    if _dl_key in st.session_state:
                        t["deadline"] = str(st.session_state[_dl_key])
                    t["last_modified"] = now_str()
                    cl["last_modified"] = now_str()
                    if d: d["last_modified"] = now_str()
                    save_data(st.session_state.crm_store)
                    st.session_state[f"_show_close_warning_{key_prefix}"] = False
                    st.session_state[f"show_edit_task_{key_prefix}"] = False
                    st.session_state[f"show_edit_dl_{key_prefix}"] = False
                    st.session_state.pop("dialog_task_key", None)
                    st.session_state.pop("dialog_task_number", None)
                    st.session_state.pop("dialog_task_client_id", None)
                    st.session_state.pop("dialog_task_deal_id", None)
                    st.session_state.pop("_open_created_task", None)
                    st.session_state["_in_dialog"] = False
                    st.toast("\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e", icon="\u2705")
                    st.rerun()
            with _wcol2:
                if st.button("\u0411\u0435\u0437 \u0441\u043e\u0445\u0440.", key=f"warn_nosave_{key_prefix}", use_container_width=True):
                    st.session_state[f"_show_close_warning_{key_prefix}"] = False
                    st.session_state[f"show_edit_task_{key_prefix}"] = False
                    st.session_state[f"show_edit_dl_{key_prefix}"] = False
                    st.session_state.pop("dialog_task_key", None)
                    st.session_state.pop("dialog_task_number", None)
                    st.session_state.pop("dialog_task_client_id", None)
                    st.session_state.pop("dialog_task_deal_id", None)
                    st.session_state.pop("_open_created_task", None)
                    st.session_state["_in_dialog"] = False
                    st.rerun()
            with _wcol3:
                if st.button("\u041e\u0442\u043c\u0435\u043d\u0430", key=f"warn_cancel_{key_prefix}", use_container_width=True):
                    st.session_state[f"_show_close_warning_{key_prefix}"] = False
                    st.rerun()

    render_task_detail(task, cl, d, key_prefix, show_shipping_status=True)

@_crm_dialog("Отчёт о выполнении задачи", width="large")
def task_completion_report_dialog(client_id, task_number, key_prefix):
    """Отдельное всплывающее окно отчёта; подробности задачи остаются в состоянии для возврата."""
    cl = next((c for c in st.session_state.crm_store.get("clients", []) if c.get("id") == client_id), None)
    if not cl:
        st.error("Клиент не найден")
        if st.button("Закрыть", key=f"task_report_missing_close_{client_id}_{task_number}"):
            st.session_state.pop("dialog_task_completion", None)
            st.rerun()
        return
    task = next((t for t in cl.get("tasks", []) if str(t.get("task_number", "")) == str(task_number)), None)
    if not task:
        st.error("Задача не найдена")
        if st.button("Закрыть", key=f"task_report_missing_task_close_{client_id}_{task_number}"):
            st.session_state.pop("dialog_task_completion", None)
            st.rerun()
        return
    deal = next((d for d in st.session_state.crm_store.get("deals", []) if d.get("id") == task.get("deal_id")), None)
    report_key = f"task_completion_report_text_{key_prefix}"
    file_ver_key = f"task_completion_file_ver_{key_prefix}"
    file_ver = st.session_state.get(file_ver_key, 0)
    files_key = f"task_completion_files_{key_prefix}_{file_ver}"
    next_key = f"task_completion_next_{key_prefix}"
    close_warning_key = f"_task_completion_close_warning_{key_prefix}"

    # Кнопка закрытия отчёта с предупреждением о незаписанных данных.
    close_css_key = f"task_report_close_row_{key_prefix}"
    st.markdown(f'<style>.st-key-{close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-height:36px!important;padding:0!important;font-size:1.2rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:8px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("✕", key=f"task_report_close_btn_{key_prefix}", use_container_width=True):
                _has_unsaved = bool(
                    str(st.session_state.get(report_key, "") or "").strip()
                    or st.session_state.get(files_key)
                    or st.session_state.get(next_key, False)
                    or str(st.session_state.get(f"task_completion_next_topic_{key_prefix}", "") or "").strip()
                    or str(st.session_state.get(f"task_completion_next_comment_{key_prefix}", "") or "").strip()
                    or st.session_state.get(f"task_completion_next_files_{key_prefix}")
                )
                if _has_unsaved:
                    st.session_state[close_warning_key] = True
                    st.rerun()
                else:
                    st.session_state.pop("dialog_task_completion", None)
                    st.session_state.pop(close_warning_key, None)
                    st.rerun()

    if st.session_state.get(close_warning_key):
        _warn_key = f"task_report_unsaved_warn_{key_prefix}"
        st.markdown(f'<style>.st-key-{_warn_key} {{ border:2px solid #FF9800!important;border-radius:10px!important;background-color:#FFF8E1!important;padding:0.5rem 0.8rem!important;margin:0.3rem 0!important; }}</style>', unsafe_allow_html=True)
        with st.container(key=_warn_key):
            st.markdown("**⚠️ Есть несохранённые изменения**")
            st.markdown("Закрыть отчёт и потерять введённые данные?")
            _discard_col, _continue_col = st.columns(2)
            with _discard_col:
                if st.button("Закрыть без сохранения", key=f"task_report_discard_{key_prefix}", use_container_width=True):
                    st.session_state.pop("dialog_task_completion", None)
                    st.session_state.pop(close_warning_key, None)
                    st.rerun()
            with _continue_col:
                if st.button("Продолжить заполнение", key=f"task_report_continue_{key_prefix}", use_container_width=True):
                    st.session_state.pop(close_warning_key, None)
                    st.rerun()

    report = st.text_area("Отчёт (обязательно):", key=report_key, height=110)
    files = st.file_uploader("Файлы/фото отчёта:", key=files_key, accept_multiple_files=True)
    create_next = st.checkbox("Создать новую задачу по сделке" if deal else "Создать новую задачу по клиенту", key=next_key)
    next_values = {}
    if create_next:
        with st.container(border=True):
            next_values["topic"] = st.text_input("Тема новой задачи:", key=f"task_completion_next_topic_{key_prefix}")
            managers = get_managers_list()
            next_values["manager"] = st.selectbox("Ответственный:", managers, index=None, key=f"task_completion_next_manager_{key_prefix}", placeholder=MGR_PLACEHOLDER)
            next_values["deadline"] = st.date_input("Срок:", format="DD.MM.YYYY", key=f"task_completion_next_deadline_{key_prefix}")
            next_values["comment"] = st.text_area("Комментарий:", key=f"task_completion_next_comment_{key_prefix}", height=90)
            next_values["files"] = st.file_uploader("Файлы новой задачи:", key=f"task_completion_next_files_{key_prefix}", accept_multiple_files=True)
    col_ok, col_cancel = st.columns(2)
    with col_ok:
        if st.button("Подтвердить выполнение", key=f"task_completion_confirm_{key_prefix}", type="primary", use_container_width=True):
            if not report.strip():
                st.warning("Введите отчёт")
            elif create_next and not next_values.get("topic", "").strip():
                st.warning("Введите тему новой задачи")
            else:
                task["done"] = True
                task["in_work"] = False
                task["needs_rework"] = False
                task["completion_report"] = report.strip()
                task["last_modified"] = now_str()
                report_files = save_uploaded_files(files, (deal["client_id"] if deal else cl["id"]), "task_report") if files else []
                if report_files:
                    task["completion_files"] = normalize_file_list(report_files)
                add_notification(task.get("created_by", ""), f"Задача на проверке: {task.get('task_number','')} — {cl.get('name','')} | Выполнил: {st.session_state.get('user_name','')}", f"✅ Задача на проверке: {task.get('task_number','')} — {cl.get('name','')} | Выполнил: {st.session_state.get('user_name','')}")
                cl["last_modified"] = now_str()
                if deal:
                    deal["last_modified"] = now_str()
                if create_next:
                    next_files = save_uploaded_files(next_values.get("files"), (deal["client_id"] if deal else cl["id"]), "task_file") if next_values.get("files") else []
                    prefix = "ЗС" if deal else "ЗК"
                    new_task = {
                        "text": next_values["topic"].strip(), "deadline": next_values["deadline"].isoformat(), "done": False,
                        "type": "Связаться", "task_files": normalize_file_list(next_files), "manager": next_values["manager"] or "",
                        "completion_report": "", "completion_files": [], "deal_id": deal["id"] if deal else None,
                        "task_comment": next_values.get("comment", "").strip(), "order_amount": 0, "last_modified": now_str(),
                        "task_number": generate_task_number(prefix), "created_at": now_str(), "created_by": st.session_state.get("user_login", ""),
                        "in_work": False, "ready_to_ship": False, "delegated_to": None, "needs_rework": False, "reviewed": False,
                        "task_comments": [], "flagged": False, "products": "", "ship_addr": "", "receiver": "",
                        "receiver_phone": "", "ship_pay": "", "tk_num": ""
                    }
                    cl.setdefault("tasks", []).append(new_task)
                    if next_values["manager"]:
                        add_notification(next_values["manager"], f"Новая задача: {new_task['text']} | Клиент: {cl.get('name','')} | Срок: {new_task['deadline']}", f"📝 Новая задача: {new_task['text']} | Клиент: {cl.get('name','')} | Срок: {new_task['deadline']}")
                save_data(st.session_state.crm_store)
                st.session_state[file_ver_key] = file_ver + 1
                st.session_state.pop("dialog_task_completion", None)
                st.toast("Задача отправлена на проверку", icon="✅")
                st.rerun()
    with col_cancel:
        if st.button("Отмена", key=f"task_completion_cancel_{key_prefix}", use_container_width=True):
            _has_unsaved = bool(
                str(st.session_state.get(report_key, "") or "").strip()
                or st.session_state.get(files_key)
                or st.session_state.get(next_key, False)
                or str(st.session_state.get(f"task_completion_next_topic_{key_prefix}", "") or "").strip()
                or str(st.session_state.get(f"task_completion_next_comment_{key_prefix}", "") or "").strip()
                or st.session_state.get(f"task_completion_next_files_{key_prefix}")
            )
            if _has_unsaved:
                st.session_state[close_warning_key] = True
                st.rerun()
            else:
                st.session_state.pop("dialog_task_completion", None)
                st.session_state.pop(close_warning_key, None)
                st.rerun()


@_crm_dialog("Отчёт по сделке", width="large")
def deal_report_dialog(deal_id, action):
    d = get_deal_by_id(deal_id)
    if not d:
        st.error("Сделка не найдена")
        return
    is_close = action == "close"
    btn_label = "Успешно завершена" if is_close else "В архив"
    ex_files = d.get("close_files", []) if is_close else d.get("archive_files", [])
    report_key = f"dls_rep_{deal_id}_{action}"
    upload_key = f"dls_upf_{deal_id}_{action}"
    close_warning_key = f"_deal_report_close_warning_{deal_id}_{action}"
    st.markdown(f"**{btn_label}: отчёт по сделке**")

    close_css_key = f"deal_report_close_row_{deal_id}_{action}"
    st.markdown(f'<style>.st-key-{close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-height:36px!important;padding:0!important;font-size:1.2rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:8px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("✕", key=f"deal_report_close_btn_{deal_id}_{action}", use_container_width=True):
                _has_unsaved = bool(str(st.session_state.get(report_key, "") or "").strip() or st.session_state.get(upload_key))
                if _has_unsaved:
                    st.session_state[close_warning_key] = True
                    st.rerun()
                else:
                    st.session_state.pop("dialog_deal_report", None)
                    st.session_state.pop(close_warning_key, None)
                    _pop_dialog_return()
                    st.rerun()

    if st.session_state.get(close_warning_key):
        _warn_key = f"deal_report_unsaved_warn_{deal_id}_{action}"
        st.markdown(f'<style>.st-key-{_warn_key} {{ border:2px solid #FF9800!important;border-radius:10px!important;background-color:#FFF8E1!important;padding:0.5rem 0.8rem!important;margin:0.3rem 0!important; }}</style>', unsafe_allow_html=True)
        with st.container(key=_warn_key):
            st.markdown("**⚠️ Есть несохранённые изменения**")
            st.markdown("Закрыть отчёт и потерять введённые данные?")
            _discard_col, _continue_col = st.columns(2)
            with _discard_col:
                if st.button("Закрыть без сохранения", key=f"deal_report_discard_{deal_id}_{action}", use_container_width=True):
                    st.session_state.pop("dialog_deal_report", None)
                    st.session_state.pop(close_warning_key, None)
                    _pop_dialog_return()
                    st.rerun()
            with _continue_col:
                if st.button("Продолжить заполнение", key=f"deal_report_continue_{deal_id}_{action}", use_container_width=True):
                    st.session_state.pop(close_warning_key, None)
                    st.rerun()

    rep = st.text_area("Отчёт по сделке (обязательно):", key=report_key, height=100)
    if ex_files:
        st.markdown("**Ранее загруженный файл:**")
        render_file_thumbs(ex_files, f"dls_ex_{deal_id}_{action}")
    up = st.file_uploader("Добавить файл:", key=upload_key, accept_multiple_files=True)
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("Подтвердить", key=f"dls_conf_{deal_id}_{action}", use_container_width=True, type="primary"):
            if not rep.strip():
                st.error("Заполните отчёт по сделке")
            else:
                new_files = normalize_file_list(save_uploaded_files(up, d["client_id"], "deal_close" if is_close else "deal_archive")) if up else []
                merged = list(ex_files)
                seen = {f.get("file_hash") for f in merged if isinstance(f, dict)}
                for f in new_files:
                    if f.get("file_hash") not in seen:
                        merged.append(f)
                        seen.add(f.get("file_hash"))
                if is_close:
                    d["status"] = "Сделка закрыта"
                    d["closed_date"] = moscow_now().strftime("%Y-%m-%d")
                    d["close_report"] = rep.strip()
                    d["close_files"] = merged
                else:
                    d["status"] = "Архив"
                    d["archive_report"] = rep.strip()
                    d["archive_files"] = merged
                d["last_modified"] = now_str()
                st.session_state.pop("dialog_deal_report", None)
                st.session_state.pop(close_warning_key, None)
                _pop_dialog_return()
                commit_and_rerun(st.session_state.crm_store, "Сделка обновлена")
    with bc2:
        if st.button("Отмена", key=f"dls_cancel_{deal_id}_{action}", use_container_width=True):
            _has_unsaved = bool(str(st.session_state.get(report_key, "") or "").strip() or st.session_state.get(upload_key))
            if _has_unsaved:
                st.session_state[close_warning_key] = True
                st.rerun()
            else:
                st.session_state.pop("dialog_deal_report", None)
                st.session_state.pop(close_warning_key, None)
                _pop_dialog_return()
                st.rerun()


@_crm_dialog("Подробности сделки", width="large")
def deal_detail_dialog(d, cl, cu, key_prefix):
    st.session_state["_in_dialog"] = True
    deal_id = d["id"]
    _show_close_warning = st.session_state.get(f"_show_close_warning_{key_prefix}", False)
    _is_editing = st.session_state.get(f"dls_show_edit_{deal_id}", False)

    _close_btn_key = f"close_btn_{key_prefix}"
    _close_css_key = f"close_row_{key_prefix}"
    st.markdown(f'<style>.st-key-{_close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:6px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{_close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{_close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=_close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("\u2715", key=_close_btn_key, use_container_width=True):
                if _is_editing and not _show_close_warning:
                    st.session_state[f"_show_close_warning_{key_prefix}"] = True
                    st.rerun()
                else:
                    st.session_state[f"_show_close_warning_{key_prefix}"] = False
                    st.session_state[f"dls_show_edit_{deal_id}"] = False
                    _pop_dialog_return()
                    st.session_state.pop("dialog_deal_key", None)
                    st.session_state.pop("_open_created_deal", None)
                    st.session_state["_in_dialog"] = False
                    st.rerun()

    if _show_close_warning:
        _warn_key = f"unsaved_warn_{key_prefix}"
        st.markdown(f'<style>.st-key-{_warn_key} {{ border:2px solid #FF9800!important;border-radius:10px!important;background-color:#FFF8E1!important;padding:0.5rem 0.8rem!important;margin:0.3rem 0!important; }}</style>', unsafe_allow_html=True)
        with st.container(key=_warn_key):
            st.markdown("**\u26a0\ufe0f \u0415\u0441\u0442\u044c \u043d\u0435\u0441\u043e\u0445\u0440\u0430\u043d\u0451\u043d\u043d\u044b\u0435 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f**")
            st.markdown("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u043f\u0435\u0440\u0435\u0434 \u0437\u0430\u043a\u0440\u044b\u0442\u0438\u0435\u043c?")
            st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
            _wcol1, _wcol2, _wcol3 = st.columns(3)
            with _wcol1:
                if st.button("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", key=f"warn_save_{key_prefix}", type="primary", use_container_width=True):
                    _et_key = f"dls_et_{deal_id}"
                    _eb_key = f"dls_eb_{deal_id}"
                    _em_key = f"dls_em_{deal_id}"
                    if _et_key in st.session_state: d["deal_title"] = st.session_state[_et_key]
                    if _eb_key in st.session_state:
                        _bv = st.session_state[_eb_key]
                        d["budget"] = int(_bv) if _bv and str(_bv).strip().isdigit() else 0
                    if _em_key in st.session_state:
                        _mv = st.session_state[_em_key]
                        if _mv: d["manager"] = _mv
                    d["last_modified"] = now_str()
                    save_data(st.session_state.crm_store)
                    st.session_state[f"_show_close_warning_{key_prefix}"] = False
                    st.session_state[f"dls_show_edit_{deal_id}"] = False
                    st.session_state.pop("dialog_deal_key", None)
                    st.session_state.pop("_open_created_deal", None)
                    st.session_state["_in_dialog"] = False
                    st.toast("\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e", icon="\u2705")
                    st.rerun()
            with _wcol2:
                if st.button("\u0411\u0435\u0437 \u0441\u043e\u0445\u0440.", key=f"warn_nosave_{key_prefix}", use_container_width=True):
                    st.session_state[f"_show_close_warning_{key_prefix}"] = False
                    st.session_state[f"dls_show_edit_{deal_id}"] = False
                    st.session_state.pop("dialog_deal_key", None)
                    st.session_state.pop("_open_created_deal", None)
                    st.session_state["_in_dialog"] = False
                    st.rerun()
            with _wcol3:
                if st.button("\u041e\u0442\u043c\u0435\u043d\u0430", key=f"warn_cancel_{key_prefix}", use_container_width=True):
                    st.session_state[f"_show_close_warning_{key_prefix}"] = False
                    st.rerun()

    render_deal_detail(d, cl, cu, key_prefix)



@_crm_dialog("Карточка клиента", width="large")
def client_detail_dialog(cl_id):
    st.session_state["_in_dialog"] = True
    cl = get_client_by_id(cl_id)
    if not cl:
        st.error("Клиент не найден")
        return
    cl["viewed"] = True
    _key_prefix = f"client_{cl_id}"
    _show_close_warning = st.session_state.get(f"_show_close_warning_{_key_prefix}", False)
    _is_editing = st.session_state.get(f"show_edit_{cl_id}", False)
    # Close button
    _close_btn_key = f"close_btn_{_key_prefix}"
    _close_css_key = f"close_row_{_key_prefix}"
    st.markdown(f'<style>.st-key-{_close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:6px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{_close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{_close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=_close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("\u2715", key=_close_btn_key, use_container_width=True):
                if _is_editing and not _show_close_warning:
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = True
                    st.rerun()
                else:
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    st.session_state[f"show_edit_{cl_id}"] = False
                    _pop_dialog_return()
                    st.session_state.pop("dialog_client_key", None)
                    st.session_state["_in_dialog"] = False
                    st.rerun()
    if _show_close_warning:
        _warn_key = f"unsaved_warn_{_key_prefix}"
        st.markdown(f'<style>.st-key-{_warn_key} {{ border:2px solid #FF9800!important;border-radius:10px!important;background-color:#FFF8E1!important;padding:0.5rem 0.8rem!important;margin:0.3rem 0!important; }}</style>', unsafe_allow_html=True)
        with st.container(key=_warn_key):
            st.markdown("**\u26a0\ufe0f Есть несохранённые изменения**")
            st.markdown("Сохранить перед закрытием?")
            _wcol1, _wcol2, _wcol3 = st.columns(3)
            with _wcol1:
                if st.button("Сохранить", key=f"warn_save_{_key_prefix}", type="primary", use_container_width=True):
                    _en_key = f"en_{cl_id}"
                    _ep_key = f"ep_{cl_id}"
                    _cm_key = f"cm_edit_{cl_id}"
                    _ee_key = f"ee_{cl_id}"
                    _ea_key = f"ea_{cl_id}"
                    _ed_key = f"ed_{cl_id}"
                    _ec_key = f"ec_{cl_id}"
                    _em_key = f"em_{cl_id}"
                    if _en_key in st.session_state: cl['name'] = st.session_state[_en_key]
                    if _ep_key in st.session_state: cl['phone'] = format_phone(st.session_state[_ep_key])
                    if _cm_key in st.session_state: cl['contact_method'] = st.session_state[_cm_key]
                    if _ee_key in st.session_state: cl['email'] = st.session_state[_ee_key]
                    if _ea_key in st.session_state: cl['address'] = st.session_state[_ea_key]
                    if _ed_key in st.session_state: cl['discount'] = int(st.session_state[_ed_key])
                    if _ec_key in st.session_state: cl['category'] = st.session_state[_ec_key]
                    _promo_key = f"promo_code_{cl_id}"
                    if _promo_key in st.session_state: cl['promo_code'] = str(st.session_state[_promo_key]).strip()
                    if _em_key in st.session_state: cl['manager'] = st.session_state[_em_key]
                    # Сохраняем доп. телефоны, email, адреса из session_state
                    _ep_list = cl.get('extra_phones', [])
                    for i in range(len(_ep_list)):
                        _pk = f"ep_phone_{cl_id}_{i}"
                        _nk = f"ep_name_{cl_id}_{i}"
                        _rk = f"ep_role_{cl_id}_{i}"
                        if _pk in st.session_state: _ep_list[i]['phone'] = st.session_state[_pk]
                        if _nk in st.session_state: _ep_list[i]['name'] = st.session_state[_nk]
                        if _rk in st.session_state: _ep_list[i]['role'] = st.session_state[_rk]
                    _ee_list = cl.get('extra_emails', [])
                    for i in range(len(_ee_list)):
                        _ek = f"ee_val_{cl_id}_{i}"
                        if _ek in st.session_state: _ee_list[i] = st.session_state[_ek]
                    _ea_list = cl.get('extra_addresses', [])
                    for i in range(len(_ea_list)):
                        if isinstance(_ea_list[i], dict):
                            _ak = f"ea_addr_{cl_id}_{i}"
                            _rn = f"ea_rn_{cl_id}_{i}"
                            _rr = f"ea_rr_{cl_id}_{i}"
                            _rp = f"ea_rp_{cl_id}_{i}"
                            _re = f"ea_re_{cl_id}_{i}"
                            if _ak in st.session_state: _ea_list[i]['address'] = st.session_state[_ak]
                            if _rn in st.session_state: _ea_list[i]['resp_name'] = st.session_state[_rn]
                            if _rr in st.session_state: _ea_list[i]['resp_role'] = st.session_state[_rr]
                            if _rp in st.session_state: _ea_list[i]['resp_phone'] = st.session_state[_rp]
                            if _re in st.session_state: _ea_list[i]['resp_email'] = st.session_state[_re]
                    cl["last_modified"] = now_str()
                    save_data(st.session_state.crm_store)
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    st.session_state[f"show_edit_{cl_id}"] = False
                    _pop_dialog_return()
                    st.session_state.pop("dialog_client_key", None)
                    st.session_state["_in_dialog"] = False
                    st.toast("Сохранено", icon="\u2705")
                    st.rerun()
            with _wcol2:
                if st.button("Без сохр.", key=f"warn_nosave_{_key_prefix}", use_container_width=True):
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    st.session_state[f"show_edit_{cl_id}"] = False
                    _pop_dialog_return()
                    st.session_state.pop("dialog_client_key", None)
                    st.session_state["_in_dialog"] = False
                    st.rerun()
            with _wcol3:
                if st.button("Отмена", key=f"warn_cancel_{_key_prefix}", use_container_width=True):
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    st.rerun()
    render_client_card_expanded(cl)


@_crm_dialog("Сделки клиента", width="large")
def client_deals_dialog(cl_id):
    st.session_state["_in_dialog"] = True
    cl = get_client_by_id(cl_id)
    if not cl:
        st.error("Клиент не найден")
        return
    _key_prefix = f"cli_deals_{cl_id}"
    # Close button
    _close_css_key = f"close_row_{_key_prefix}"
    st.markdown(f'<style>.st-key-{_close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:6px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{_close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{_close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=_close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("\u2715", key=f"close_btn_{_key_prefix}", use_container_width=True):
                _pop_dialog_return()
                st.session_state.pop("dialog_client_deals_key", None)
                st.session_state["_in_dialog"] = False
                st.rerun()
    st.subheader(cl.get('name', ''))
    cl_deals = [d for d in st.session_state.crm_store["deals"] if d["client_id"] == cl_id]
    if cl_deals:
        cl_deals.sort(key=lambda d: get_sort_key(d), reverse=True)
        for d in cl_deals:
            _deal_key = f"cd_btn_{d['id']}"
            _num = d.get("deal_number", d.get("title", ""))
            _title = d.get("deal_title", "")
            _status = d.get("status", "Новый")
            _budget = d.get("budget", 0)
            _label = f"{_num} — {_title} ({_status}) — {_budget:,.0f} руб.".replace(",", " ")
            _bg, _bc = get_entity_border([t for t in cl.get("tasks", []) if t.get("deal_id") == d["id"]])
            st.markdown(f"<style>.st-key-{_deal_key} button {{ background-color: {_bg} !important; color: #2C3E50 !important; border: 2px solid {_bc} !important; border-radius: 10px !important; white-space: normal !important; height: auto !important; text-align: left !important; }}</style>", unsafe_allow_html=True)
            with st.container(key=_deal_key):
                if st.button(_label, key=f"cd_go_{d['id']}", use_container_width=True, type="secondary"):
                    _push_dialog_return()
                    st.session_state.pop("dialog_client_deals_key", None)
                    st.session_state["dialog_deal_key"] = d["id"]
                    st.rerun()
    else:
        st.caption("Сделок нет")
    st.markdown("---")
    # Кнопка создания новой сделки — открывает тот же диалог, что и в карточке клиента
    if st.button("Создать новую сделку", key=f"btn_cd_dlg_{cl_id}", use_container_width=True, type="primary"):
        _push_dialog_return()
        st.session_state["dialog_create_deal_from_client"] = cl_id
        st.session_state.pop("dialog_client_deals_key", None)
        st.rerun()




# ============================================================
# Dialog: Создать сделку (из карточки клиента / окна сделок)
# ============================================================
@_crm_dialog("Создать сделку", width="large")
def create_deal_dialog(cl_id):
    st.session_state["_in_dialog"] = True
    _key_prefix = f"cdlg_{cl_id}"
    _show_close_warning = st.session_state.get(f"_show_close_warning_{_key_prefix}", False)
    _has_unsaved = (
        st.session_state.get(f"cdlg_title_{cl_id}", "").strip() or
        st.session_state.get(f"cdlg_budget_{cl_id}", "").strip()
    )
    _close_css_key = f"close_row_{_key_prefix}"
    st.markdown(f'<style>.st-key-{_close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:6px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{_close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{_close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=_close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("\u2715", key=f"close_btn_{_key_prefix}", use_container_width=True):
                if _has_unsaved and not _show_close_warning:
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = True
                    st.rerun()
                else:
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    _pop_dialog_return()
                    st.session_state.pop("dialog_create_deal_from_client", None)
                    st.session_state["_in_dialog"] = False
                    st.rerun()
    if _show_close_warning:
        _warn_key = f"unsaved_warn_{_key_prefix}"
        st.markdown(f'<style>.st-key-{_warn_key} {{ border:2px solid #FF9800!important;border-radius:10px!important;background-color:#FFF8E1!important;padding:0.5rem 0.8rem!important;margin:0.3rem 0!important; }}</style>', unsafe_allow_html=True)
        with st.container(key=_warn_key):
            st.markdown("**\u26a0\ufe0f Есть несохранённые изменения**")
            st.markdown("Закрыть без сохранения?")
            _wcol1, _wcol2 = st.columns(2)
            with _wcol1:
                if st.button("Без сохранения", key=f"cdlg_warn_nosave_{cl_id}", use_container_width=True):
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    _pop_dialog_return()
                    st.session_state.pop("dialog_create_deal_from_client", None)
                    st.session_state["_in_dialog"] = False
                    st.rerun()
            with _wcol2:
                if st.button("Отмена", key=f"cdlg_warn_cancel_{cl_id}", use_container_width=True):
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    st.rerun()
    _cl = get_client_by_id(cl_id)
    if not _cl:
        st.error("Клиент не найден")
        return
    st.markdown(f"**Клиент:** {_cl.get('name', '')}")
    st.markdown("---")
    _deal_create_left, _deal_create_right = st.columns(2)
    with _deal_create_left:
        cd_title = st.text_input("Тема:", key=f"cdlg_title_{cl_id}")
        cd_budget = st.text_input("Бюджет (руб.):", value="", key=f"cdlg_budget_{cl_id}", placeholder="Введите сумму")
        cd_mgr = st.selectbox("Ответственный:", get_managers_list(), index=0, key=f"cdlg_mgr_{cl_id}", placeholder=MGR_PLACEHOLDER)
        cd_ps = st.selectbox("Статус оплаты:", ["Не оплачено", "Оплачено"], index=0, key=f"cdlg_ps_{cl_id}")
    with _deal_create_right:
        st.markdown("**Комментарии**")
        cd_comment = st.text_area("Комментарий:", key=f"cdlg_comment_{cl_id}", placeholder="Введите новый комментарий...", height=68, label_visibility="collapsed")
        cd_files = st.file_uploader("Файлы сделки:", key=f"cdlg_files_{cl_id}", accept_multiple_files=True)
    if st.button("Создать", key=f"cdlg_go_{cl_id}", use_container_width=True, type="primary"):
        if not cd_mgr:
            st.warning("Выберите ответственного")
        else:
            deals = st.session_state.crm_store.get("deals", [])
            did = f"deal_{moscow_now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
            dn = generate_deal_number()
            new_deal = {"id": did, "client_id": cl_id, "title": dn, "deal_number": dn, "deal_title": cd_title.strip(),
                        "budget": int(cd_budget) if cd_budget and cd_budget.strip().isdigit() else 0,
                        "status": "В работе", "manager": cd_mgr, "payment_status": cd_ps,
                        "deal_comments": ([{"time": now_str(), "text": cd_comment.strip()}] if cd_comment.strip() else []), "deal_files": (normalize_file_list(save_uploaded_files(cd_files, cl_id, "deal_file")) if cd_files else []), "close_files": [], "archive_files": [],
                        "last_modified": now_str(), "created_at": now_str(),
                        "created_by": st.session_state.get("user_login", ""), "change_log": [], "deal_chat": []}
            st.session_state.crm_store.setdefault("deals", []).append(new_deal)
            _cl["last_modified"] = now_str()
            save_data(st.session_state.crm_store)
            st.toast("Сделка создана", icon="✅")
            st.session_state.pop("dialog_create_deal_from_client", None)
            st.session_state["_in_dialog"] = False
            _push_dialog_return()
            st.session_state["_open_created_deal"] = did
            st.rerun()


# ============================================================
# Dialog: Создать задачу по сделке (из всплывающего окна сделки)
# ============================================================
@_crm_dialog("Создать задачу по сделке", width="large")
def deal_create_task_dialog(deal_id, client_id):
    st.session_state["_in_dialog"] = True
    _key_prefix = f"cdt_{deal_id}"
    _show_close_warning = st.session_state.get(f"_show_close_warning_{_key_prefix}", False)
    _has_unsaved = (
        st.session_state.get(f"nt_topic_cdt_{deal_id}", "").strip() or
        st.session_state.get(f"nt_c_cdt_{deal_id}", "").strip()
    )
    _close_css_key = f"close_row_{_key_prefix}"
    st.markdown(f'<style>.st-key-{_close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:6px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{_close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{_close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=_close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("\u2715", key=f"close_btn_{_key_prefix}", use_container_width=True):
                if _has_unsaved and not _show_close_warning:
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = True
                    st.rerun()
                else:
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    _pop_dialog_return()
                    st.session_state.pop("dialog_create_deal_task_deal_id", None)
                    st.session_state.pop("dialog_create_deal_task_client_id", None)
                    st.session_state["_in_dialog"] = False
                    st.rerun()
    if _show_close_warning:
        _warn_key = f"unsaved_warn_{_key_prefix}"
        st.markdown(f'<style>.st-key-{_warn_key} {{ border:2px solid #FF9800!important;border-radius:10px!important;background-color:#FFF8E1!important;padding:0.5rem 0.8rem!important;margin:0.3rem 0!important; }}</style>', unsafe_allow_html=True)
        with st.container(key=_warn_key):
            st.markdown("**\u26a0\ufe0f Есть несохранённые изменения**")
            st.markdown("Закрыть без сохранения?")
            _wcol1, _wcol2 = st.columns(2)
            with _wcol1:
                if st.button("Без сохранения", key=f"cdt_warn_nosave_{deal_id}", use_container_width=True):
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    _pop_dialog_return()
                    st.session_state.pop("dialog_create_deal_task_deal_id", None)
                    st.session_state.pop("dialog_create_deal_task_client_id", None)
                    st.session_state["_in_dialog"] = False
                    st.rerun()
            with _wcol2:
                if st.button("Отмена", key=f"cdt_warn_cancel_{deal_id}", use_container_width=True):
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    st.rerun()
    _created_task = render_task_form(deal_id, client_id, f"cdt_{deal_id}")
    if _created_task:
        save_data(st.session_state.crm_store)
        st.toast("Задача создана", icon="✅")
        st.session_state.pop("dialog_create_deal_task_deal_id", None)
        st.session_state.pop("dialog_create_deal_task_client_id", None)
        st.session_state["_in_dialog"] = False
        _push_dialog_return()
        st.session_state["dialog_task_key"] = f"cdt_{deal_id}_{_created_task.get('task_number', '')}"
        st.session_state["_open_created_task"] = _created_task
        st.rerun()


# ============================================================
# Dialog: Создать задачу по клиенту (из всплывающего окна задач)
# ============================================================
@_crm_dialog("Создать задачу по клиенту", width="large")
def client_create_task_dialog(cl_id):
    st.session_state["_in_dialog"] = True
    _key_prefix = f"cct_{cl_id}"
    _show_close_warning = st.session_state.get(f"_show_close_warning_{_key_prefix}", False)
    _has_unsaved = (
        st.session_state.get(f"nt_topic_cct_{cl_id}", "").strip() or
        st.session_state.get(f"nt_c_cct_{cl_id}", "").strip()
    )
    _close_css_key = f"close_row_{_key_prefix}"
    st.markdown(f'<style>.st-key-{_close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:6px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{_close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{_close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=_close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("\u2715", key=f"close_btn_{_key_prefix}", use_container_width=True):
                if _has_unsaved and not _show_close_warning:
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = True
                    st.rerun()
                else:
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    _pop_dialog_return()
                    st.session_state.pop("dialog_create_client_task_client_id", None)
                    st.session_state["_in_dialog"] = False
                    st.rerun()
    if _show_close_warning:
        _warn_key = f"unsaved_warn_{_key_prefix}"
        st.markdown(f'<style>.st-key-{_warn_key} {{ border:2px solid #FF9800!important;border-radius:10px!important;background-color:#FFF8E1!important;padding:0.5rem 0.8rem!important;margin:0.3rem 0!important; }}</style>', unsafe_allow_html=True)
        with st.container(key=_warn_key):
            st.markdown("**\u26a0\ufe0f Есть несохранённые изменения**")
            st.markdown("Закрыть без сохранения?")
            _wcol1, _wcol2 = st.columns(2)
            with _wcol1:
                if st.button("Без сохранения", key=f"cct_warn_nosave_{cl_id}", use_container_width=True):
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    _pop_dialog_return()
                    st.session_state.pop("dialog_create_client_task_client_id", None)
                    st.session_state["_in_dialog"] = False
                    st.rerun()
            with _wcol2:
                if st.button("Отмена", key=f"cct_warn_cancel_{cl_id}", use_container_width=True):
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    st.rerun()
    _created_task = render_task_form(None, cl_id, f"cct_{cl_id}")
    if _created_task:
        save_data(st.session_state.crm_store)
        st.toast("Задача создана", icon="✅")
        st.session_state.pop("dialog_create_client_task_client_id", None)
        st.session_state["_in_dialog"] = False
        _push_dialog_return()
        st.session_state["dialog_task_key"] = f"cct_{cl_id}_{_created_task.get('task_number', '')}"
        st.session_state["_open_created_task"] = _created_task
        st.rerun()


# ============================================================
# Dialog: Создать задачу по сделке (из всплывающего окна задач клиента)
# ============================================================
@_crm_dialog("Создать задачу по сделке", width="large")
def client_create_deal_task_dialog(cl_id):
    st.session_state["_in_dialog"] = True
    _key_prefix = f"ccdt_{cl_id}"
    _show_close_warning = st.session_state.get(f"_show_close_warning_{_key_prefix}", False)
    cl = get_client_by_id(cl_id)
    cl_deals = [d for d in st.session_state.crm_store.get("deals", []) if d["client_id"] == cl_id] if cl else []
    _close_css_key = f"close_row_{_key_prefix}"
    st.markdown(f'<style>.st-key-{_close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:6px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{_close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{_close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=_close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("\u2715", key=f"close_btn_{_key_prefix}", use_container_width=True):
                st.session_state[f"_show_close_warning_{_key_prefix}"] = True
                st.rerun()
    if _show_close_warning:
        _warn_key = f"unsaved_warn_{_key_prefix}"
        st.markdown(f'<style>.st-key-{_warn_key} {{ border:2px solid #FF9800!important;border-radius:10px!important;background-color:#FFF8E1!important;padding:0.5rem 0.8rem!important;margin:0.3rem 0!important; }}</style>', unsafe_allow_html=True)
        with st.container(key=_warn_key):
            st.markdown("**\u26a0\ufe0f Есть несохранённые изменения**")
            st.markdown("Закрыть без сохранения?")
            _wcol1, _wcol2 = st.columns(2)
            with _wcol1:
                if st.button("Без сохранения", key=f"ccdt_warn_nosave_{cl_id}", use_container_width=True):
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    _pop_dialog_return()
                    st.session_state.pop("dialog_create_client_task_deal_select_cl_id", None)
                    st.session_state["_in_dialog"] = False
                    st.rerun()
            with _wcol2:
                if st.button("Отмена", key=f"ccdt_warn_cancel_{cl_id}", use_container_width=True):
                    st.session_state[f"_show_close_warning_{_key_prefix}"] = False
                    st.rerun()
    deal_options = {d["id"]: d.get("deal_number", d.get("title", "")) for d in cl_deals}
    selected_deal_id = st.selectbox("Выберите сделку:", list(deal_options.keys()), format_func=lambda x: deal_options[x], key=f"ccdt_deal_sel_{cl_id}")
    _created_task = None
    if selected_deal_id:
        _created_task = render_task_form(selected_deal_id, cl_id, f"ccdt_{cl_id}")
    if _created_task:
        save_data(st.session_state.crm_store)
        st.toast("Задача создана", icon="✅")
        st.session_state.pop("dialog_create_client_task_deal_select_cl_id", None)
        st.session_state["_in_dialog"] = False
        _push_dialog_return()
        st.session_state["dialog_task_key"] = f"ccdt_{cl_id}_{_created_task.get('task_number', '')}"
        st.session_state["_open_created_task"] = _created_task
        st.rerun()

@_crm_dialog("Задачи клиента", width="large")
def client_tasks_dialog(cl_id):
    st.session_state["_in_dialog"] = True
    cl = get_client_by_id(cl_id)
    if not cl:
        st.error("Клиент не найден")
        return
    _key_prefix = f"cli_tasks_{cl_id}"
    # Close button
    _close_css_key = f"close_row_{_key_prefix}"
    st.markdown(f'<style>.st-key-{_close_css_key} .stButton > button {{ width:36px!important;height:36px!important;min-width:36px!important;min-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:6px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important; }} .st-key-{_close_css_key} .stButton > button:hover {{ background:#EEF0F3!important;border-color:#C9CFD7!important; }} .st-key-{_close_css_key} > div {{ gap:0!important; }}</style>', unsafe_allow_html=True)
    with st.container(key=_close_css_key):
        _spacer_col, _close_col = st.columns([20, 1])
        with _close_col:
            if st.button("\u2715", key=f"close_btn_{_key_prefix}", use_container_width=True):
                _pop_dialog_return()
                st.session_state.pop("dialog_client_tasks_key", None)
                st.session_state["_in_dialog"] = False
                st.rerun()
    st.subheader(cl.get('name', ''))
    # Задачи по клиенту
    client_tasks = [t for t in cl.get("tasks", []) if not t.get("deal_id")]
    cl_deals = [d for d in st.session_state.crm_store["deals"] if d["client_id"] == cl_id]
    deal_tasks = []
    for d in cl_deals:
        for t in cl.get("tasks", []):
            if t.get("deal_id") == d["id"]:
                deal_tasks.append((t, d))

    # Задачи по клиенту
    st.markdown(f"**Задачи по клиенту ({len(client_tasks)})**")
    if client_tasks:
        client_tasks.sort(key=lambda t: get_sort_key(t), reverse=True)
        for ti, t in enumerate(client_tasks):
            _tk_key = f"ct_btn_cl_{cl_id}_{ti}"
            _fd = format_date(t.get("deadline", ""))
            _done = t.get("done", False)
            _icon = "\u2705" if _done else "\u23f3"
            _label = f"{_icon} Задача \u2116{t.get('task_number', '')} — {t.get('text', '')} | {_fd}"
            _bg, _bc = "#F5F6F8", "#C9CFD7"
            if not _done:
                if is_task_overdue(t): _bg, _bc = "#FFEBEE", "#C62828"
                elif t.get("in_work"): _bg, _bc = "#E8F5E9", "#4CAF50"
                else: _bg, _bc = "#E3F2FD", "#2196F3"
            st.markdown(f"<style>.st-key-{_tk_key} button {{ background-color: {_bg} !important; color: #2C3E50 !important; border: 2px solid {_bc} !important; border-radius: 10px !important; white-space: normal !important; height: auto !important; text-align: left !important; }}</style>", unsafe_allow_html=True)
            with st.container(key=_tk_key):
                if st.button(_label, key=f"ct_go_cl_{cl_id}_{ti}", use_container_width=True, type="secondary"):
                    _push_dialog_return()
                    st.session_state.pop("dialog_client_tasks_key", None)
                    st.session_state["dialog_task_number"] = str(t.get("task_number", ""))
                    st.session_state["dialog_task_client_id"] = cl_id
                    st.session_state["dialog_task_deal_id"] = str(t.get("deal_id", "") or "")
                    st.session_state["dialog_task_key"] = f"clienttask_{cl_id}_{t.get('task_number', '')}_client"
                    st.rerun()
    else:
        st.caption("Задач по клиенту нет")

    # Кнопка создания задачи по клиенту — открывает popup диалог
    if st.button("Создать задачу по клиенту", key=f"btn_ct_dlg_cl_{cl_id}", use_container_width=True, type="primary"):
        _push_dialog_return()
        st.session_state["dialog_create_client_task_client_id"] = cl_id
        st.session_state.pop("dialog_client_tasks_key", None)
        st.rerun()

    # Разделитель
    st.markdown('<hr style="border:0;height:1px;background:#DCE0E5;margin:0.8rem 0;">', unsafe_allow_html=True)

    # Задачи по сделке
    st.markdown(f"**Задачи по сделкам ({len(deal_tasks)})**")
    if deal_tasks:
        deal_tasks.sort(key=lambda x: get_sort_key(x[0]), reverse=True)
        for ti, (t, d) in enumerate(deal_tasks):
            _tk_key = f"ct_btn_dl_{cl_id}_{ti}"
            _fd = format_date(t.get("deadline", ""))
            _done = t.get("done", False)
            _icon = "\u2705" if _done else "\u23f3"
            _deal_num = d.get("deal_number", d.get("title", ""))
            _label = f"{_icon} Задача \u2116{t.get('task_number', '')} — {t.get('text', '')} | {_fd} | {_deal_num}"
            _bg, _bc = "#F5F6F8", "#C9CFD7"
            if not _done:
                if is_task_overdue(t): _bg, _bc = "#FFEBEE", "#C62828"
                elif t.get("in_work"): _bg, _bc = "#E8F5E9", "#4CAF50"
                else: _bg, _bc = "#E3F2FD", "#2196F3"
            st.markdown(f"<style>.st-key-{_tk_key} button {{ background-color: {_bg} !important; color: #2C3E50 !important; border: 2px solid {_bc} !important; border-radius: 10px !important; white-space: normal !important; height: auto !important; text-align: left !important; }}</style>", unsafe_allow_html=True)
            with st.container(key=_tk_key):
                if st.button(_label, key=f"ct_go_dl_{cl_id}_{ti}", use_container_width=True, type="secondary"):
                    _push_dialog_return()
                    st.session_state.pop("dialog_client_tasks_key", None)
                    st.session_state["dialog_task_number"] = str(t.get("task_number", ""))
                    st.session_state["dialog_task_client_id"] = cl_id
                    st.session_state["dialog_task_deal_id"] = str(t.get("deal_id", "") or "")
                    st.session_state["dialog_task_key"] = f"clienttask_{cl_id}_{t.get('task_number', '')}_{d.get('id', '')}"
                    st.rerun()
    else:
        st.caption("Задач по сделкам нет")

    # Кнопка создания задачи по сделке — открывает popup диалог
    if cl_deals:
        if st.button("Создать задачу по сделке", key=f"btn_cdt_dlg_{cl_id}", use_container_width=True, type="primary"):
            _push_dialog_return()
            st.session_state["dialog_create_client_task_deal_select_cl_id"] = cl_id
            st.session_state.pop("dialog_client_tasks_key", None)
            st.rerun()
    else:
        st.caption("Нет сделок для создания задачи по сделке")


if st.session_state.active_tab == "Клиенты":
    fv = st.session_state.client_form_version
    render_client_form(fv)
    # Поиск и сортировки в один ряд
    _search_col, _sort_col, _sort_cat_col = st.columns([3, 2, 2])
    with _search_col:
        _search_input_col, _search_clear_col = st.columns([12, 1])
        with _search_input_col:
            _search_input_now = st.text_input("Поиск", key="search_input_key", placeholder="Поиск...", label_visibility="collapsed")
        with _search_clear_col:
            st.markdown("<style>.st-key-client_search_clear button{padding:0!important;min-height:38px!important;font-size:20px!important;line-height:1!important;color:#808B98!important;border:0!important;background:transparent!important;box-shadow:none!important}</style>", unsafe_allow_html=True)
            st.button("×", key="client_search_clear", help="Очистить поиск", on_click=lambda: st.session_state.__setitem__("search_input_key", ""), use_container_width=True)
        sq = (_search_input_now or "").strip().lower()
    with _sort_col:
        sort_options = ["По дате изменения", "По дате создания", "По алфавиту", "По городу"]
        sort_mode = st.selectbox("Сортировка", sort_options, key="client_sort_select", label_visibility="collapsed")
        st.session_state.client_sort_mode = sort_mode
    with _sort_cat_col:
        cat_options = ["Все"] + CATEGORIES
        ctf = st.selectbox("Категория", cat_options, index=0, key="cat_filter", label_visibility="collapsed")
    all_clients = st.session_state.crm_store["clients"]
    fcl = []
    sd = re.sub(r"\D", "", sq)
    if sd and sd[0] in ("7", "8") and len(sd) > 1: sd = sd[1:]
    for cl in all_clients:
        if ctf != "Все" and cl.get("category", "Не определён") != ctf: continue
        if sq:
            ct = f"{cl['name']} {cl.get('city','')} {cl.get('phone','')} {cl.get('email','')} {cl.get('address','')} {cl.get('base_comment','')}".lower()
            mb = sq in ct
            acd = re.sub(r"\D", "", cl['phone'])
            for p in cl.get("extra_phones", []):
                acd += " " + re.sub(r"\D", "", p["phone"])
                ct += " " + p["name"].lower()
            mp = sd and (sd in acd)
            if not (mb or mp or sq in ct): continue
        fcl.append(cl)
    # Сортировка
    if sort_mode == "По дате изменения":
        fcl.sort(key=lambda c: c.get("last_modified", ""), reverse=True)
    elif sort_mode == "По дате создания":
        fcl.sort(key=lambda c: c.get("created_at", ""), reverse=True)
    elif sort_mode == "По алфавиту":
        fcl.sort(key=lambda c: c.get("name", "").lower())
    elif sort_mode == "По городу":
        fcl.sort(key=lambda c: (c.get("city", "") or "").strip().lower())

    # Постраничный вывод: создаём элементы интерфейса только для текущей страницы,
    # а поиск и сортировка по-прежнему применяются ко всей базе.
    _client_page_size = 50
    _client_page_signature = f"{sq}|{ctf}|{sort_mode}|{len(fcl)}"
    if st.session_state.get("_client_page_signature") != _client_page_signature:
        st.session_state["_client_page_signature"] = _client_page_signature
        st.session_state["_client_page"] = 0
    _client_page_count = max(1, (len(fcl) + _client_page_size - 1) // _client_page_size)
    _client_page = min(max(0, int(st.session_state.get("_client_page", 0))), _client_page_count - 1)
    st.session_state["_client_page"] = _client_page
    if all_clients:
        _pg_left, _pg_info, _pg_right = st.columns([1, 4, 1])
        with _pg_left:
            if st.button("← Назад", key="clients_page_prev", disabled=_client_page <= 0, use_container_width=True):
                st.session_state["_client_page"] = _client_page - 1
                st.rerun()
        with _pg_info:
            _first_client_num = _client_page * _client_page_size + 1 if fcl else 0
            _last_client_num = min((_client_page + 1) * _client_page_size, len(fcl))
            st.markdown(f"<div style='text-align:center;padding:7px 0;color:#5A6B7D;font-size:.9rem;'>Клиенты {_first_client_num}–{_last_client_num} из {len(fcl)} · Страница {_client_page + 1} из {_client_page_count}</div>", unsafe_allow_html=True)
        with _pg_right:
            if st.button("Вперёд →", key="clients_page_next", disabled=_client_page >= _client_page_count - 1, use_container_width=True):
                st.session_state["_client_page"] = _client_page + 1
                st.rerun()
        _visible_clients = fcl[_client_page * _client_page_size:(_client_page + 1) * _client_page_size]
    else:
        _visible_clients = []
    if all_clients:
        # Таблица клиентов: город и телефон сразу после наименования
        _hc1, _hc2, _hc3, _hc4, _hc5, _hc6, _hc7 = st.columns([3.5, 1.5, 1.7, 1.2, 1.0, 1.0, 1.5])
        with _hc1:
            st.markdown("<div style='font-weight:700;color:#2C3E50;padding:4px 0;text-align:center;border-bottom:2px solid #DCE0E5;font-size:0.9rem;'>Наименование</div>", unsafe_allow_html=True)
        with _hc2:
            st.markdown("<div style='font-weight:700;color:#2C3E50;padding:4px 0;text-align:center;border-bottom:2px solid #DCE0E5;font-size:0.9rem;'>Город</div>", unsafe_allow_html=True)
        with _hc3:
            st.markdown("<div style='font-weight:700;color:#2C3E50;padding:4px 0;text-align:center;border-bottom:2px solid #DCE0E5;font-size:0.9rem;'>Телефон</div>", unsafe_allow_html=True)
        with _hc4:
            st.markdown("<div style='font-weight:700;color:#2C3E50;padding:4px 0;text-align:center;border-bottom:2px solid #DCE0E5;font-size:0.9rem;'>Категория</div>", unsafe_allow_html=True)
        with _hc5:
            st.markdown("<div style='font-weight:700;color:#2C3E50;padding:4px 0;text-align:center;border-bottom:2px solid #DCE0E5;font-size:0.9rem;'>Сделки</div>", unsafe_allow_html=True)
        with _hc6:
            st.markdown("<div style='font-weight:700;color:#2C3E50;padding:4px 0;text-align:center;border-bottom:2px solid #DCE0E5;font-size:0.9rem;'>Задачи</div>", unsafe_allow_html=True)
        with _hc7:
            st.markdown("<div style='font-weight:700;color:#2C3E50;padding:4px 0;text-align:center;border-bottom:2px solid #DCE0E5;font-size:0.9rem;'>Сумма сделок</div>", unsafe_allow_html=True)
        st.markdown('<div style="border-top:1px solid #DCE0E5;margin-bottom:4px;"></div>', unsafe_allow_html=True)
        # Индексируем сделки один раз: раньше для каждого клиента повторно просматривалась вся база сделок.
        _clients_deals_by_id = {}
        for _deal_item in st.session_state.crm_store.get("deals", []):
            _clients_deals_by_id.setdefault(_deal_item.get("client_id"), []).append(_deal_item)

        # Объединяем CSS всех кнопок списка в один блок вместо трёх style-блоков на каждого клиента.
        _client_row_css = []
        for _style_client in _visible_clients:
            _style_id = _style_client["id"]
            _style_deals = _clients_deals_by_id.get(_style_id, [])
            _style_active_deals = any(_sd.get("status", "Новый") in ("Новый", "В работе") for _sd in _style_deals)
            _style_tasks = _style_client.get("tasks", [])
            _style_overdue_tasks = any(not _st.get("done") and is_task_overdue(_st) for _st in _style_tasks)
            _style_active_tasks = any(not _st.get("done") for _st in _style_tasks)
            _style_deals_color = "#2E7D32" if _style_active_deals else "#2C3E50"
            _style_tasks_color = "#C62828" if _style_overdue_tasks else ("#2E7D32" if _style_active_tasks else "#2C3E50")
            _client_row_css.append(
                f".st-key-tbl_name_{_style_id} button{{background:transparent!important;border:none!important;box-shadow:none!important;text-align:left!important;padding:2px 0!important;font-size:.88rem!important;color:#2C3E50!important;font-weight:600!important}}"
                f".st-key-tbl_name_{_style_id} button:hover{{color:#bc1661!important}}"
                f".st-key-tbl_deals_btn_{_style_id} button,.st-key-tbl_tasks_{_style_id} button{{background:transparent!important;border:none!important;box-shadow:none!important;text-decoration:none!important;padding:2px 0!important;font-size:.88rem!important}}"
                f".st-key-tbl_deals_btn_{_style_id} button{{color:{_style_deals_color}!important;font-weight:{800 if _style_deals_color != '#2C3E50' else 600}!important}}"
                f".st-key-tbl_tasks_{_style_id} button{{color:{_style_tasks_color}!important;font-weight:{800 if _style_tasks_color != '#2C3E50' else 600}!important}}"
                f".st-key-tbl_deals_btn_{_style_id} button:hover,.st-key-tbl_tasks_{_style_id} button:hover{{color:#bc1661!important}}"
            )
        if _client_row_css:
            st.markdown("<style>" + "".join(_client_row_css) + "</style>", unsafe_allow_html=True)

        for cl in _visible_clients:
            cl_deals = _clients_deals_by_id.get(cl["id"], [])
            cl_tasks_all = cl.get("tasks", [])
            all_tasks_count = len(cl_tasks_all)
            deals_sum = sum(d.get("budget", 0) for d in cl_deals)
            # Проверка актуальных сделок
            has_active_deals = any(d.get("status", "Новый") in ("Новый", "В работе") for d in cl_deals)
            # Проверка задач
            has_overdue_tasks = any(not t.get("done") and is_task_overdue(t) for t in cl_tasks_all)
            has_active_tasks = any(not t.get("done") for t in cl_tasks_all)
            # Кнопки-ссылки через st.button
            _name_key = f"tbl_name_{cl['id']}"
            _deals_key = f"tbl_deals_{cl['id']}"
            _tasks_key = f"tbl_tasks_{cl['id']}"
            _deals_count = len(cl_deals)
            _tasks_count = all_tasks_count
            _category = cl.get("category", "Не определён")
            _sum_str = f"{deals_sum:,.0f} руб.".replace(",", " ")
            # Рендерим строку таблицы: название, город, телефон, категория, сделки, задачи, сумма
            _c1, _c2, _c3, _c4, _c5, _c6, _c7 = st.columns([3.5, 1.5, 1.7, 1.2, 1.0, 1.0, 1.5])
            with _c1:
                # Текст вместо кнопки с рамкой — прозрачный фон, без границ, кликабельный
                _name_btn_key = f"tbl_name_{cl['id']}"
                if st.button(cl.get("name", ""), key=_name_btn_key, use_container_width=True):
                    st.session_state["dialog_client_key"] = cl["id"]
            with _c2:
                _city = html.escape(str(cl.get("city", "") or "—"))
                st.markdown(f"<div title='{_city}' style='display:flex;align-items:center;justify-content:center;min-height:32px;font-size:0.84rem;color:#3C4A5A;overflow-wrap:anywhere;'>{_city}</div>", unsafe_allow_html=True)
            with _c3:
                _phone = html.escape(str(cl.get("phone", "") or "—"))
                st.markdown(f"<div style='display:flex;align-items:center;justify-content:center;min-height:32px;font-size:0.82rem;color:#3C4A5A;overflow-wrap:anywhere;'>{_phone}</div>", unsafe_allow_html=True)
            with _c4:
                st.markdown(f"<div style='display:flex;align-items:center;justify-content:center;min-height:32px;font-size:0.88rem;color:#3C4A5A;'>{html.escape(str(_category))}</div>", unsafe_allow_html=True)
            with _c5:
                _deals_btn_key = f"tbl_deals_btn_{cl['id']}"
                _deals_color = "#2E7D32" if has_active_deals else "#2C3E50"
                if st.button(str(_deals_count), key=_deals_btn_key, use_container_width=True):
                    st.session_state["dialog_client_deals_key"] = cl["id"]
            with _c6:
                _tasks_btn_key = f"tbl_tasks_{cl['id']}"
                if has_overdue_tasks:
                    _tasks_color = "#C62828"
                elif has_active_tasks:
                    _tasks_color = "#2E7D32"
                else:
                    _tasks_color = "#2C3E50"
                if st.button(str(_tasks_count), key=_tasks_btn_key, use_container_width=True):
                    st.session_state["dialog_client_tasks_key"] = cl["id"]
            with _c7:
                st.markdown(f"<div style='display:flex;align-items:center;justify-content:flex-end;min-height:32px;font-weight:600;white-space:nowrap;'>{_sum_str}</div>", unsafe_allow_html=True)
            # Разделитель между клиентами — минимальный отступ
            st.markdown('<div class="client-divider"></div>', unsafe_allow_html=True)

    else:
        st.info("База клиентов пуста. Создайте первого клиента.")
    # Показ диалогов
    # Dialog dispatching — only one dialog at a time to prevent stacking
    _dlg_cdt_deal = st.session_state.get("dialog_create_deal_task_deal_id")
    _dlg_cct = st.session_state.get("dialog_create_client_task_client_id")
    _dlg_ccdt = st.session_state.get("dialog_create_client_task_deal_select_cl_id")
    _dlg_create_deal = st.session_state.get("dialog_create_deal_from_client")
    _dialog_deal_task_key = st.session_state.get("dialog_deal_task_key")
    _dialog_client_key = st.session_state.get("dialog_client_key")
    _dialog_cd_key = st.session_state.get("dialog_client_deals_key")
    _dialog_ct_key = st.session_state.get("dialog_client_tasks_key")
    _dialog_deal_key = st.session_state.get("dialog_deal_key")
    _dialog_task_key = st.session_state.get("dialog_task_key")
    _dialog_task_number = st.session_state.get("dialog_task_number")
    _dialog_task_client_id = st.session_state.get("dialog_task_client_id")
    _dialog_task_deal_id = st.session_state.get("dialog_task_deal_id")
    _deal_report_dialog = st.session_state.get("dialog_deal_report")
    
    _task_completion_state = st.session_state.get("dialog_task_completion")
    _pending_reminder = st.session_state.get("_pending_reminder_dialog")
    _req_dialog_client_id = st.session_state.get("dialog_client_requisites_client_id")
    _invoice_dialog_state = st.session_state.get("dialog_invoice_request")
    if _req_dialog_client_id:
        client_requisites_dialog(_req_dialog_client_id, bool(st.session_state.get("dialog_client_requisites_return_to_invoice", False)))
    elif _invoice_dialog_state:
        invoice_document_dialog(_invoice_dialog_state.get("deal_id"), _invoice_dialog_state.get("calc_id"))
    elif _pending_reminder:
        create_reminder_dialog(_pending_reminder["entity_type"], _pending_reminder["entity_id"], _pending_reminder["entity_label"])
    elif _task_completion_state:
        task_completion_report_dialog(_task_completion_state.get("client_id"), _task_completion_state.get("task_number"), _task_completion_state.get("key_prefix", "task"))
    elif _deal_report_dialog:
        deal_report_dialog(_deal_report_dialog.get("deal_id"), _deal_report_dialog.get("action", "close"))
    elif _dlg_cdt_deal:
        _cdt_client_id = st.session_state.get("dialog_create_deal_task_client_id")
        deal_create_task_dialog(_dlg_cdt_deal, _cdt_client_id)
    elif _dialog_task_key and _dialog_task_number and _dialog_task_client_id:
        _target_client = get_client_by_id(_dialog_task_client_id)
        _target_task = None
        _target_deal = None
        if _target_client:
            for _candidate_task in _target_client.get("tasks", []):
                if str(_candidate_task.get("task_number", "")) == str(_dialog_task_number) and str(_candidate_task.get("deal_id", "") or "") == str(_dialog_task_deal_id or ""):
                    _target_task = _candidate_task
                    break
            if _target_task and _target_task.get("deal_id"):
                _target_deal = next((x for x in st.session_state.crm_store.get("deals", []) if str(x.get("id", "")) == str(_target_task.get("deal_id", ""))), None)
        if _target_task and _target_client:
            task_detail_dialog(_target_task, _target_client, _target_deal, _dialog_task_key)
        else:
            st.session_state.pop("dialog_task_key", None)
            st.session_state.pop("dialog_task_number", None)
            st.session_state.pop("dialog_task_client_id", None)
            st.session_state.pop("dialog_task_deal_id", None)
            st.warning("Не удалось найти выбранную задачу. Обновите список и попробуйте ещё раз.")
    elif _dialog_client_key and st.session_state.get("_dialog_return_stack"):
        client_detail_dialog(_dialog_client_key)
    elif _dlg_cct:
        client_create_task_dialog(_dlg_cct)
    elif _dlg_ccdt:
        client_create_deal_task_dialog(_dlg_ccdt)
    elif _dlg_create_deal:
        create_deal_dialog(_dlg_create_deal)
    elif _dialog_deal_task_key and st.session_state.active_tab == "Клиенты":
        _found = False
        for _cl in st.session_state.crm_store.get("clients", []):
            if _found: break
            for _dd in st.session_state.crm_store.get("deals", []):
                if _dd.get("client_id") == _cl["id"]:
                    _deal_tasks = [t for t in _cl.get("tasks", []) if t.get("deal_id") == _dd["id"]]
                    for dti, _tk in enumerate(_deal_tasks):
                        _expected_key = f"dls_dl_{_dd['id']}_{dti}"
                        if _dialog_deal_task_key == _expected_key:
                            _deal = _dd
                            task_detail_dialog(_tk, _cl, _deal, _dialog_deal_task_key)
                            _found = True
                            break
                    if _found: break
    elif st.session_state.get("_open_created_task"):
        _created_tk = st.session_state["_open_created_task"]
        for _cl in st.session_state.crm_store.get("clients", []):
            for _tk in _cl.get("tasks", []):
                if _tk is _created_tk or _tk.get("task_number") == _created_tk.get("task_number"):
                    _deal = None
                    for _d in st.session_state.crm_store.get("deals", []):
                        if _d["id"] == _tk.get("deal_id"):
                            _deal = _d
                            break
                    task_detail_dialog(_tk, _cl, _deal, f"created_{_tk.get('task_number', '')}")
                    break
    elif _dialog_task_key and st.session_state.get("dialog_client_tasks_key"):
        _found = False
        for _cl in st.session_state.crm_store.get("clients", []):
            if _found: break
            for _ti, _tk in enumerate(_cl.get("tasks", [])):
                _tk_keys = []
                _client_tasks = [t for t in _cl.get("tasks", []) if not t.get("deal_id")]
                _cl_deals_list = [d for d in st.session_state.crm_store.get("deals", []) if d.get("client_id") == _cl["id"]]
                _deal_tasks_list = []
                for _dd in _cl_deals_list:
                    for _tt in _cl.get("tasks", []):
                        if _tt.get("deal_id") == _dd["id"]:
                            _deal_tasks_list.append(_tt)
                for cti, _ in enumerate(_client_tasks):
                    _tk_keys.append(f"ct_cl_{_cl['id']}_{cti}")
                for dti, _ in enumerate(_deal_tasks_list):
                    _tk_keys.append(f"ct_dl_{_cl['id']}_{dti}")
                if _dialog_task_key in _tk_keys:
                    _deal = None
                    for _d in st.session_state.crm_store.get("deals", []):
                        if _d["id"] == _tk.get("deal_id"):
                            _deal = _d
                            break
                    task_detail_dialog(_tk, _cl, _deal, _dialog_task_key)
                    _found = True
                    break
    elif st.session_state.get("_open_created_deal"):
        for _d in st.session_state.crm_store.get("deals", []):
            if _d["id"] == st.session_state["_open_created_deal"]:
                _cl = get_client_by_id(_d.get("client_id"))
                deal_detail_dialog(_d, _cl, cu, f"deal_{_d['id']}")
                break
    elif _dialog_client_key:
        client_detail_dialog(_dialog_client_key)
    elif not (st.session_state.get("dialog_deal_report") or st.session_state.get("dialog_create_deal_task_deal_id")) and _dialog_deal_key and st.session_state.active_tab == "Клиенты":
        for _d in st.session_state.crm_store.get("deals", []):
            if _d["id"] == _dialog_deal_key:
                _cl = get_client_by_id(_d.get("client_id"))
                deal_detail_dialog(_d, _cl, cu, f"deal_{_d['id']}")
                break
    elif _dialog_cd_key:
        client_deals_dialog(_dialog_cd_key)
    elif _dialog_ct_key:
        client_tasks_dialog(_dialog_ct_key)

elif st.session_state.active_tab == "Сделки":
    all_deals = st.session_state.crm_store.get("deals", [])
    cid_map = {c["id"]: c for c in st.session_state.crm_store.get("clients", [])}
    # Compute sums
    work_sum = sum(d.get("budget", 0) for d in all_deals if d.get("status", "Новый") == "В работе")
    closed_sum = sum(d.get("budget", 0) for d in all_deals if d.get("status", "") == "Сделка закрыта" and str(d.get("closed_date", ""))[:7] == moscow_now().strftime("%Y-%m"))
    closed_all_sum = sum(d.get("budget", 0) for d in all_deals if d.get("status", "") == "Сделка закрыта")
    # Sum metrics (no heading)
    mcols = st.columns(3 if st.session_state.get("user_role") == "admin" else 2)
    with mcols[0]:
        st.metric("Сумма сделок в работе", f"{work_sum:,.0f} руб.".replace(",", " "))
    with mcols[1]:
        st.metric("Сумма успешно завершенных сделок за месяц", f"{closed_sum:,.0f} руб.".replace(",", " "))
    if st.session_state.get("user_role") == "admin":
        with mcols[2]:
            st.metric("Сумма успешно завершенных сделок за весь период", f"{closed_all_sum:,.0f} руб.".replace(",", " "))
    # Collapsed sections for closed and archive at top
    with st.expander(f"Успешно завершены ({sum(1 for d in all_deals if d.get('status') == 'Сделка закрыта')})", expanded=False):
        closed_search = st.text_input("Поиск среди завершённых:", key="deal_closed_search", placeholder="Введите текст...").strip().lower()
        closed_deals = [d for d in all_deals if d.get("status") == "Сделка закрыта"]
        if closed_search:
            closed_deals = [d for d in closed_deals if closed_search in f"{d.get('deal_number', '')} {d.get('deal_title', '')} {d.get('title', '')} {(cid_map.get(d.get('client_id'), {}) or {}).get('name', '')}".lower()]
        closed_deals.sort(key=lambda d: d.get("last_modified", ""), reverse=True)
        if closed_deals:
            for d in closed_deals:
                render_deal_standalone(d, cid_map.get(d.get("client_id")), cu)
        else:
            st.caption("Завершённых сделок нет.")
    with st.expander(f"Архив ({sum(1 for d in all_deals if d.get('status') == 'Архив')})", expanded=False):
        arch_search = st.text_input("Поиск среди архива:", key="deal_arch_search", placeholder="Введите текст...").strip().lower()
        arch_deals = [d for d in all_deals if d.get("status") == "Архив"]
        if arch_search:
            arch_deals = [d for d in arch_deals if arch_search in f"{d.get('deal_number', '')} {d.get('deal_title', '')} {d.get('title', '')} {(cid_map.get(d.get('client_id'), {}) or {}).get('name', '')}".lower()]
        arch_deals.sort(key=lambda d: d.get("last_modified", ""), reverse=True)
        if arch_deals:
            for d in arch_deals:
                render_deal_standalone(d, cid_map.get(d.get("client_id")), cu)
        else:
            st.caption("Архив пуст.")
    # Search + manager filter — same style as Clients tab
    with st.container(key="deals_sticky_header"):
        fc1, fc2 = st.columns([3, 2])
        with fc1:
            _deal_search_now = st.text_input("Поиск", key="deal_tab_search", placeholder="Поиск...", label_visibility="collapsed")
            deal_search = (_deal_search_now or "").strip().lower()
        with fc2:
            _deal_mgr_list = ["Все"] + get_managers_list()
            _cu_name_deal = st.session_state.get("user_name", "")
            _default_idx_deal = 0
            if _cu_name_deal and _cu_name_deal in _deal_mgr_list:
                _default_idx_deal = _deal_mgr_list.index(_cu_name_deal)
            mgr_filter = st.selectbox("Ответственный", _deal_mgr_list, index=_default_idx_deal, key="deal_tab_mgr", label_visibility="collapsed")
    st.components.v1.html('''<script>
(function(){
  var w=window;
  try{if(window.parent&&window.parent!==window)w=window.parent;}catch(e){}
  var sel='.st-key-deals_sticky_header';
  function init(){
    var el=w.document.querySelector(sel);
    if(!el){setTimeout(init,200);return;}
    var ph=w.document.createElement('div');
    ph.className='deals-sticky-placeholder';
    el.parentNode.insertBefore(ph,el);
    var fixed=false;
    var origTop=0;
    function measure(){
      var r=el.getBoundingClientRect();
      origTop=r.top+w.scrollY;
    }
    function onScroll(){
      if(fixed){
        if(w.scrollY<origTop-1){
          el.classList.remove('deals-sticky-fixed');
          ph.style.height='0px';
          fixed=false;
        }
      } else {
        var r=el.getBoundingClientRect();
        if(r.top<0){
          measure();
          el.classList.add('deals-sticky-fixed');
          ph.style.height=r.height+'px';
          fixed=true;
        }
      }
    }
    w.addEventListener('scroll',onScroll,{passive:true});
    setTimeout(measure,500);
    setTimeout(onScroll,600);
  }
  init();
})();
</script>''', height=0)
    # Filter deals for "Новые" and "В работе" columns only
    fdeals = []
    for d in all_deals:
        s = d.get("status", "Новый")
        if s not in ("Новый", "В работе"):
            continue
        cl = cid_map.get(d.get("client_id"))
        if mgr_filter != "Все" and d.get("manager", "") != mgr_filter:
            continue
        if deal_search:
            hay = f"{d.get('deal_number', '')} {d.get('deal_title', '')} {d.get('title', '')} {(cl.get('name', '') if cl else '')}".lower()
            if deal_search not in hay:
                continue
        fdeals.append(d)
    fdeals.sort(key=lambda d: d.get("last_modified", ""), reverse=True)
    new_deals = [d for d in fdeals if d.get("status", "Новый") == "Новый"]
    work_deals = [d for d in fdeals if d.get("status", "") == "В работе"]
    col_new, col_work = st.columns(2)
    with col_new:
        with st.container(border=True):
            st.subheader(f"Новые ({len(new_deals)})")
            if new_deals:
                for d in new_deals:
                    render_deal_standalone(d, cid_map.get(d.get("client_id")), cu)
            else:
                st.caption("Новых сделок нет.")
    with col_work:
        with st.container(border=True):
            st.subheader(f"В работе ({len(work_deals)})")
            if work_deals:
                for d in work_deals:
                    render_deal_standalone(d, cid_map.get(d.get("client_id")), cu)
            else:
                st.caption("Сделок в работе нет.")
    # Единая диспетчеризация окон сделок: сначала дочернее окно, затем карточка сделки.
    # Streamlit должен отрисовать только один @st.dialog за один проход.
    _dialog_deal_key = st.session_state.get("dialog_deal_key")
    _created_deal_id = st.session_state.get("_open_created_deal")
    _active_deal_dialog_id = _dialog_deal_key or _created_deal_id
    _deal_report_state = st.session_state.get("dialog_deal_report")
    _deal_task_dialog_id = st.session_state.get("dialog_create_deal_task_deal_id")

    _task_completion_state = st.session_state.get("dialog_task_completion")
    _pending_reminder = st.session_state.get("_pending_reminder_dialog")
    if _pending_reminder:
        create_reminder_dialog(_pending_reminder["entity_type"], _pending_reminder["entity_id"], _pending_reminder["entity_label"])
    elif _task_completion_state:
        task_completion_report_dialog(_task_completion_state.get("client_id"), _task_completion_state.get("task_number"), _task_completion_state.get("key_prefix", "task"))
    elif _deal_report_state:
        deal_report_dialog(_deal_report_state.get("deal_id"), _deal_report_state.get("action", "close"))
    elif _deal_task_dialog_id:
        _task_client_id = st.session_state.get("dialog_create_deal_task_client_id")
        deal_create_task_dialog(_deal_task_dialog_id, _task_client_id)
    elif _active_deal_dialog_id and not st.session_state.get("dialog_client_key"):
        for _d in st.session_state.crm_store.get("deals", []):
            if _d["id"] == _active_deal_dialog_id:
                _cl = cid_map.get(_d.get("client_id"))
                deal_detail_dialog(_d, _cl, cu, f"deal_{_d['id']}")
                break

elif st.session_state.active_tab == "Товары и прайс":
    st.markdown("## Товары и прайс")
    st.caption("Редактирование каталога применяется к новым добавлениям товаров. Цены уже сохранённых позиций в сделках не меняются.")
    _is_catalog_admin = st.session_state.get("user_role") == "admin"
    _catalog = st.session_state.crm_store.setdefault("products", copy.deepcopy(DEFAULT_PRODUCT_CATALOG))
    if _is_catalog_admin:
        st.info("Изменяйте текущие цены, добавляйте новые товары и снимайте позиции с продажи через флажок «Активен». Удалять товар не нужно: архивные позиции остаются в истории сделок.")
        _edited_catalog = st.data_editor(
            _catalog,
            key="products_catalog_editor",
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.TextColumn("ID", help="Служебный идентификатор; для новых товаров можно оставить пустым"),
                "sku": st.column_config.TextColumn("Артикул"),
                "name": st.column_config.TextColumn("Наименование", required=True),
                "unit": st.column_config.TextColumn("Ед. изм.", required=True),
                "price": st.column_config.NumberColumn("Цена, ₽", min_value=0, step=10, format="%.2f", required=True),
                "note": st.column_config.TextColumn("Примечание"),
                "active": st.column_config.CheckboxColumn("Активен", default=True),
            },
        )
        if st.button("Сохранить прайс", key="save_products_catalog", type="primary", use_container_width=True):
            _rows = _edited_catalog.to_dict("records") if hasattr(_edited_catalog, "to_dict") else list(_edited_catalog)
            _old_catalog_by_id = {str(x.get("id", x.get("sku", ""))): x for x in st.session_state.crm_store.get("products", [])}
            _clean_rows = []
            _price_changes = []
            _seen_ids = set()
            for _i, _row in enumerate(_rows):
                _raw_name = _row.get("name", "")
                _name = "" if _raw_name is None or str(_raw_name).strip().lower() in ("nan", "none") else str(_raw_name).strip()
                if not _name:
                    continue
                _raw_sku = _row.get("sku", "")
                _sku = "" if _raw_sku is None or str(_raw_sku).strip().lower() in ("nan", "none") else str(_raw_sku).strip()
                _raw_id = _row.get("id", "")
                _pid = str((_raw_id if _raw_id is not None and str(_raw_id).strip().lower() not in ("nan", "none") else "") or _sku or uuid.uuid4()).strip()
                if _pid in _seen_ids:
                    _pid = f"{_pid}-{uuid.uuid4().hex[:6]}"
                _seen_ids.add(_pid)
                try:
                    _price = float(_row.get("price", 0) or 0)
                    if _price != _price: _price = 0.0
                    _price = max(0.0, _price)
                except (TypeError, ValueError): _price = 0.0
                _old_product = _old_catalog_by_id.get(_pid)
                if _old_product is not None:
                    try: _old_price = float(_old_product.get("price", 0) or 0)
                    except (TypeError, ValueError): _old_price = 0.0
                    if round(_old_price, 2) != round(_price, 2):
                        _price_changes.append({"date":now_str(),"product_id":_pid,"sku":_sku,"name":_name,"old_price":_old_price,"new_price":_price,"author":st.session_state.get("user_name", st.session_state.get("user_login", ""))})
                _clean_rows.append({"id":_pid,"sku":_sku,"name":_name,"unit":str(_row.get("unit", "шт.") or "шт."),"price":_price,"note":str(_row.get("note", "") or ""),"active":bool(_row.get("active", True))})
            st.session_state.crm_store["products"] = _clean_rows
            st.session_state.crm_store.setdefault("product_price_history", []).extend(_price_changes)
            save_data(st.session_state.crm_store)
            st.toast("Прайс сохранён", icon="✅")
            st.rerun()
        with st.expander("История изменения цен", expanded=False):
            _price_history = list(reversed(st.session_state.crm_store.get("product_price_history", [])[-100:]))
            if _price_history:
                st.dataframe(_price_history, use_container_width=True, hide_index=True)
            else:
                st.caption("Изменений цен пока нет.")
    else:
        st.dataframe(_catalog, use_container_width=True, hide_index=True)
        st.caption("Изменять прайс может администратор CRM. Обратитесь к нему, если нужно обновить цену или добавить товар.")

elif st.session_state.active_tab == "Задачи":
    now_time = moscow_now()
    # Верхняя шапка раздела задач: современный компактный стиль без изменения общей навигации CRM.
    st.markdown("""
    <style>
    .tasks-page-heading { display:flex; align-items:center; justify-content:space-between; gap:16px; margin: 0.15rem 0 0.8rem 0; padding: 0.1rem 0 0.85rem 0; border-bottom:1px solid #E3E8EF; }
    .tasks-page-title-row { display:flex; align-items:center; gap:12px; }
    .tasks-page-title { color:#26384A; font-size:1.9rem; line-height:1.15; font-weight:750; letter-spacing:-0.04em; }
    .tasks-page-subtitle { color:#8492A6; font-size:0.86rem; margin-top:0.25rem; }
    .tasks-page-mark { width:5px; height:34px; border-radius:8px; background:#BC1661; }
    div[data-testid="stTabs"] { margin-top:0.1rem; }
    div[data-testid="stTabs"] > div[role="tablist"] { gap:0.35rem; border-bottom:1px solid #E3E8EF; padding:0.15rem 0 0.45rem 0; }
    div[data-testid="stTabs"] button[role="tab"] { border:1px solid #E0E6EF; border-radius:9px 9px 0 0; padding:0.55rem 1.15rem; color:#65758B; font-weight:600; background:rgba(255,255,255,0.55); }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color:#BC1661 !important; border-color:#F0C5D8 !important; border-bottom:3px solid #BC1661 !important; background:rgba(188,22,97,0.055) !important; }
    div[data-testid="stTabs"] button[role="tab"] p { font-size:0.92rem; }
    .st-key-task_search_input input { min-height:44px; border-radius:9px !important; }
    .st-key-task_filter_mgr [data-testid="stSelectbox"] > div > div { min-height:44px; border-radius:9px !important; }
    .st-key-task_search_input, .st-key-task_filter_mgr { padding-top:0.1rem; }
    .tasks-filter-caption { color:#8A97A8; font-size:0.74rem; font-weight:650; text-transform:uppercase; letter-spacing:0.055em; margin:0.05rem 0 0.2rem 0.1rem; }
    @media (min-width: 900px) {
      div[data-testid="stTabs"] button[role="tab"] { min-width:118px; }
    }
    </style>
    """, unsafe_allow_html=True)
    plan_sub1, plan_sub2 = st.tabs(["Активные", "Архив"])
    with plan_sub1:
        st.markdown("<div class='tasks-filter-caption'>Поиск и фильтрация</div>", unsafe_allow_html=True)
        col_sq, col_mf = st.columns([3.2, 1.8], gap="small")
        with col_sq:
            _task_search_now = st.text_input("Поиск", key="task_search_input", placeholder="⌕  Поиск по задачам...", label_visibility="collapsed")
            task_search = (_task_search_now or "").strip().lower()
        with col_mf:
            _task_mgr_list = ["Все"] + get_managers_list()
            _cu_name_task = st.session_state.get("user_name", "")
            _default_idx_task = 0
            if _cu_name_task and _cu_name_task in _task_mgr_list:
                _default_idx_task = _task_mgr_list.index(_cu_name_task)
            mf = st.selectbox("Ответственный", _task_mgr_list, index=_default_idx_task, key="task_filter_mgr", label_visibility="collapsed", help="Показать задачи выбранного ответственного")
        di = {d["id"]: d for d in st.session_state.crm_store.get("deals", [])}
        aat = []
        new_tasks = []
        review_tasks = []
        for cl in st.session_state.crm_store.get("clients", []):
            for ti, tk in enumerate(cl.get("tasks", [])):
                tm = tk.get("manager", "")
                dtm = tk.get("delegated_to", "")
                _is_review = tk.get("done", False) and not tk.get("reviewed", False)
                if _is_review:
                    _tcb = tk.get("created_by", "")
                    _tcb_name = ""
                    if _tcb:
                        _u = get_user_by_login(_tcb)
                        if _u: _tcb_name = _u.get("name", _u.get("login", _tcb))
                        else: _tcb_name = _tcb
                    if mf != "Все":
                        if st.session_state.user_role != "admin" and _tcb != st.session_state.get("user_login", "") and _tcb_name != mf: continue
                    elif mf != "Все":
                        if _tcb_name != mf and _tcb != mf: continue
                else:
                    if mf == "Мои задачи":
                        if tm and tm != cu and dtm != cu: continue
                    elif mf != "Все":
                        # Неназначенные задачи видны всем: любой пользователь может взять их в работу.
                        if tm and tm != mf and dtm != mf: continue
                if task_search:
                    search_text = f"{tk.get('text', '')} {tk.get('task_number', '')} {cl.get('name', '')} {cl.get('phone', '')} {tk.get('products', '')} {tk.get('ship_addr', '')} {tk.get('receiver', '')}".lower()
                    if task_search not in search_text: continue
                task_deal = di.get(tk.get("deal_id"))
                mdt = task_deal.get("deal_number", task_deal["title"]) if task_deal else ""
                entry = {"client_id": cl["id"], "client_name": cl["name"], "client_phone": cl["phone"], "deal_title": mdt, "sort_date": get_task_sort_date(tk), "deadline_str": tk.get("deadline", ""), "type": tk.get("type", "Связаться"), "text": tk.get("text", ""), "task_obj": tk, "task_idx": ti, "client_obj": cl}
                if tk.get("done", False) and not tk.get("reviewed", False):
                    review_tasks.append(entry)
                elif not tk.get("done", False):
                    if not tk.get("in_work", False):
                        new_tasks.append(entry)
                    else:
                        aat.append(entry)
        aat.sort(key=lambda x: x["sort_date"])
        new_tasks.sort(key=lambda x: x["sort_date"])
        review_tasks.sort(key=lambda x: x["sort_date"])
        tt_list = [t for t in aat if t["sort_date"] <= now_time.date()]
        ft_list = [t for t in aat if t["sort_date"] > now_time.date()]
        def render_task_block(t, sk):
            task = t["task_obj"]
            cl = t["client_obj"]
            tp = task.get("type", "Связаться")
            io_ = is_task_overdue(task)
            fd = format_date(t["deadline_str"])
            task_key = f"tb_{sk}_{t['client_id']}_{t['task_idx']}"
            if task.get("needs_rework"): tk_bg, tk_bc = "#FFEBEE", "#D32F2F"
            elif io_: tk_bg, tk_bc = "#FFEBEE", "#C62828"
            elif task.get("in_work"): tk_bg, tk_bc = "#E8F5E9", "#4CAF50"
            else: tk_bg, tk_bc = "#E3F2FD", "#2196F3"
            exp_label = f"Задача №{task.get('task_number', '')} {fd} — {t['client_name']} — {t['text']}"
            if task.get('ready_to_ship'): exp_label += ' | Готово к отправке'
            _rework_css = ""
            if task.get('needs_rework'):
                _rework_css = f".st-key-tb_wrap_{task_key} button::after {{ content: 'На доработке'; display: block; color: #D32F2F; font-weight: 700; font-size: 0.8rem; margin-top: 4px; }}"
            st.markdown(f"""<style>
            .st-key-tb_wrap_{task_key} button {{
                background-color: {tk_bg} !important;
                color: #2C3E50 !important;
                border: 1px solid {tk_bc} !important;
                border-left: 4px solid {tk_bc} !important;
                border-radius: 9px !important;
                padding: 0.55rem 0.7rem !important;
                min-height: 66px !important;
                height: auto !important;
                box-shadow: 0 1px 2px rgba(30, 45, 65, 0.05) !important;
                transition: box-shadow 0.15s ease, border-color 0.15s ease !important;
            }}
            .st-key-tb_wrap_{task_key} button p {{
                font-size: 0.86rem !important;
                line-height: 1.42 !important;
                font-weight: 500 !important;
                text-align: left !important;
                white-space: normal !important;
            }}
            .st-key-tb_wrap_{task_key} button:hover {{
                box-shadow: 0 3px 9px rgba(30, 45, 65, 0.12) !important;
                border-color: {tk_bc} !important;
            }}
            {_rework_css}
            </style>""", unsafe_allow_html=True)
            with st.container(key=f"tb_wrap_{task_key}"):
                if st.button(exp_label, key=f"tb_btn_{task_key}", use_container_width=True):
                    st.session_state["dialog_task_key"] = task_key
                    st.rerun()
                render_scroll_restore(f"tb_{task_key}")
        col_new, col_today, col_future, col_review = st.columns(4)
        with col_new:
            with st.container(border=True):
                st.subheader(f"Новые ({len(new_tasks)})")
                if new_tasks:
                    for t in new_tasks: render_task_block(t, "new")
                else: st.caption("Новых задач нет.")
        with col_today:
            with st.container(border=True):
                _today_head, _today_print_col = st.columns([5, 1])
                with _today_head:
                    st.subheader(f"На сегодня ({len(tt_list)})")
                with _today_print_col:
                    if st.button("", key="print_today_tasks_btn", icon=":material/print:", type="secondary"):
                        _print_rows = []
                        for _pt in tt_list:
                            _ptask = _pt["task_obj"]
                            _print_rows.append(
                                "<tr>"
                                f"<td>{html.escape(str(_ptask.get('task_number', '') or ''))}</td>"
                                f"<td>{html.escape(str(_ptask.get('products', '') or '')).replace(chr(10), '<br>')}</td>"
                                f"<td>{html.escape(str(_ptask.get('task_comment', '') or _ptask.get('text', '') or '')).replace(chr(10), '<br>')}</td>"
                                f"<td>{html.escape(str(_ptask.get('tk_num', '') or ''))}</td>"
                                "<td class='notes'></td>"
                                "</tr>"
                            )
                        _print_date = moscow_now().strftime("%d.%m.%Y")
                        _print_html = f'''<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><title>Задачи на сегодня</title><style>
                        @page {{ size: A4 landscape; margin: 10mm; }}
                        body {{ font-family: Arial, sans-serif; color: #111; margin: 0; }}
                        h2 {{ font-size: 18px; margin: 0 0 4px; }}
                        .meta {{ font-size: 11px; margin-bottom: 12px; }}
                        table {{ width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 11px; }}
                        th, td {{ border: 1px solid #555; padding: 6px; vertical-align: top; overflow-wrap: anywhere; }}
                        th {{ background: #eee; text-align: left; }}
                        th:nth-child(1) {{ width: 9%; }} th:nth-child(2) {{ width: 24%; }}
                        th:nth-child(3) {{ width: 29%; }} th:nth-child(4) {{ width: 17%; }} th:nth-child(5) {{ width: 21%; }}
                        td.notes {{ height: 28px; }}
                        @media print {{ th {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }} }}
                        </style></head><body><h2>Задачи на сегодня</h2><div class="meta">Дата: {_print_date} · Всего задач: {len(_print_rows)}</div>
                        <table><thead><tr><th>№ задачи</th><th>Товары</th><th>Комментарий</th><th>Трек</th><th>Отметки</th></tr></thead>
                        <tbody>{''.join(_print_rows) if _print_rows else '<tr><td colspan="5">На сегодня задач нет</td></tr>'}</tbody></table>
                        <script>window.onload = () => {{ window.focus(); window.print(); }};</script></body></html>'''
                        components.html(_print_html, height=0, width=0)
                if tt_list:
                    for t in tt_list: render_task_block(t, "today")
                else: st.success("Все задачи на сегодня закрыты.")
        with col_future:
            with st.container(border=True):
                st.subheader(f"Предстоящие ({len(ft_list)})")
                if ft_list:
                    for t in ft_list: render_task_block(t, "future")
                else: st.caption("План на будущие дни пуст.")
        with col_review:
            with st.container(border=True):
                st.subheader(f"На проверке ({len(review_tasks)})")
                if review_tasks:
                    for t in review_tasks: render_task_block(t, "review")
                else: st.caption("Задач на проверке нет.")
    with plan_sub2:
        archived_tasks = []
        for cl in st.session_state.crm_store.get("clients", []):
            for ti, tk in enumerate(cl.get("tasks", [])):
                if tk.get("done", False) and tk.get("reviewed", False):
                    archived_tasks.append({"client_name": cl["name"], "task_obj": tk, "client_obj": cl, "task_idx": ti})
        archived_tasks.sort(key=lambda x: x["task_obj"].get("last_modified", ""), reverse=True)
        if archived_tasks:
            for at in archived_tasks[:50]:
                task = at["task_obj"]
                cl = at["client_obj"]
                task_key = f"arch_{at['task_idx']}_{cl['id']}"
                exp_label = f"✅ Задача №{task.get('task_number', '')} — {at['client_name']} — {task.get('text', '')} | {format_date(task.get('deadline', ''))}"
                st.markdown(f"<style>.st-key-arch_wrap_{task_key} button {{ text-align: left !important; justify-content: flex-start !important; white-space: normal !important; height: auto !important; }}</style>", unsafe_allow_html=True)
                with st.container(key=f"arch_wrap_{task_key}"):
                    if st.button(exp_label, key=f"arch_btn_{task_key}", use_container_width=True):
                        st.session_state["dialog_task_key"] = task_key
                        st.rerun()
        else:
            st.caption("Архив пуст.")
    # Completion report dialog takes precedence over task details to avoid nested dialogs.
    _task_completion_state = st.session_state.get("dialog_task_completion")
    _dialog_key = st.session_state.get("dialog_task_key")
    _pending_reminder = st.session_state.get("_pending_reminder_dialog")
    if _pending_reminder:
        create_reminder_dialog(_pending_reminder["entity_type"], _pending_reminder["entity_id"], _pending_reminder["entity_label"])
    elif _task_completion_state:
        task_completion_report_dialog(_task_completion_state.get("client_id"), _task_completion_state.get("task_number"), _task_completion_state.get("key_prefix", "task"))
    # Show created task dialog if requested
    elif st.session_state.get("_open_created_task"):
        _created_tk = st.session_state["_open_created_task"]
        for _cl in st.session_state.crm_store.get("clients", []):
            for _tk in _cl.get("tasks", []):
                if _tk is _created_tk or _tk.get("task_number") == _created_tk.get("task_number"):
                    _deal = None
                    for _d in st.session_state.crm_store.get("deals", []):
                        if _d["id"] == _tk.get("deal_id"):
                            _deal = _d
                            break
                    task_detail_dialog(_tk, _cl, _deal, f"created_{_tk.get('task_number', '')}")
                    break
    # Show task detail dialog if requested
    elif _dialog_key:
        _found = False
        for _cl in st.session_state.crm_store.get("clients", []):
            if _found: break
            for _ti, _tk in enumerate(_cl.get("tasks", [])):
                _tk_keys = [f"tb_new_{_cl['id']}_{_ti}", f"tb_today_{_cl['id']}_{_ti}", f"tb_future_{_cl['id']}_{_ti}", f"tb_review_{_cl['id']}_{_ti}", f"arch_{_ti}_{_cl['id']}"]
                if _dialog_key in _tk_keys:
                    _deal = None
                    for _d in st.session_state.crm_store.get("deals", []):
                        if _d["id"] == _tk.get("deal_id"):
                            _deal = _d
                            break
                    task_detail_dialog(_tk, _cl, _deal, _dialog_key)
                    _found = True
                    break

elif st.session_state.active_tab == "Внутренние задачи":
    internal_tasks = st.session_state.crm_store.setdefault("internal_tasks", [])
    _cu = st.session_state.user_name
    _cu_login = st.session_state.get("user_login", "")
    _is_admin = st.session_state.user_role == "admin"

    # Create form — button like "Добавить клиента"
    show_it_key = "show_it_form"
    if st.button("Создать внутреннюю задачу", key="btn_new_it", type="primary", use_container_width=False):
        st.session_state[show_it_key] = True
        st.rerun()
    if st.session_state.get(show_it_key, False):
        create_internal_task_dialog()

    st.markdown("---")

    # Active / Archive tabs
    it_plan_sub1, it_plan_sub2 = st.tabs(["Активные", "Архив"])

    with it_plan_sub1:
        # Search (left) + sort by responsible (right) — same style as Clients tab
        _it_search_col, _it_mgr_col = st.columns([3, 2])
        with _it_search_col:
            _it_search_input_now = st.text_input("Поиск", key="it_search_input", placeholder="Поиск...", label_visibility="collapsed")
            it_search = (_it_search_input_now or "").strip().lower()
        with _it_mgr_col:
            _mgr_list = ["Все"] + get_managers_list()
            _cu_name = st.session_state.get("user_name", "")
            _default_idx = 0
            if _cu_name and _cu_name in _mgr_list:
                _default_idx = _mgr_list.index(_cu_name)
            it_mf = st.selectbox("Ответственный", _mgr_list, index=_default_idx, key="it_filter_mgr", label_visibility="collapsed")

        # Filter tasks
        it_new = []
        it_work = []
        it_review = []
        for it in internal_tasks:
            _status = it.get("it_status", "new")
            if it.get("done") and it.get("reviewed", False):
                continue
            # Неназначенные задачи доступны всем сотрудникам, даже при фильтре по ответственному.
            if it_mf != "Все" and it.get("manager", "") and it.get("manager", "") != it_mf:
                continue
            if it_search:
                _hay = f"{it.get('text', '')} {it.get('manager', '')} {it.get('comment', '')}".lower()
                if it_search not in _hay:
                    continue
            if _status == "review" or (it.get("done") and not it.get("reviewed", False)):
                it_review.append(it)
            elif _status == "in_work" or it.get("in_work", False):
                it_work.append(it)
            else:
                it_new.append(it)

        it_new.sort(key=lambda t: t.get("last_modified", ""), reverse=True)
        it_work.sort(key=lambda t: t.get("last_modified", ""), reverse=True)
        it_review.sort(key=lambda t: t.get("last_modified", ""), reverse=True)

        # 3 columns: Новые, В работе, На проверке
        it_col_new, it_col_work, it_col_review = st.columns(3)
        with it_col_new:
            with st.container(border=True):
                st.subheader(f"Новые ({len(it_new)})")
                if it_new:
                    for it in it_new:
                        _it_key = f"it_card_{it['id']}"
                        _it_bg = "#E3F2FD"
                        _it_bc = "#2196F3"
                        _it_rework_css = ""
                        if it.get("needs_rework", False):
                            _it_rework_css = f".st-key-{_it_key} button::after {{ content: 'На доработке'; display: block; color: #D32F2F; font-weight: 700; font-size: 0.8rem; margin-top: 4px; }}"
                        st.markdown(f"<style>.st-key-{_it_key} button {{ background-color: {_it_bg} !important; color: #2C3E50 !important; border: 2px solid {_it_bc} !important; border-radius: 10px !important; text-align: left !important; white-space: normal !important; height: auto !important; }} {_it_rework_css}</style>", unsafe_allow_html=True)
                        with st.container(key=_it_key):
                            _label = f"Задача №{it['id']} — {it.get('text', '')} | {it.get('manager', '—')}"
                            if st.button(_label, key=f"it_btn_{it['id']}", use_container_width=True):
                                st.session_state["dialog_it_key"] = _safe_id(it.get("id", 0))
                                st.rerun()
                else:
                    st.caption("Новых задач нет.")

        with it_col_work:
            with st.container(border=True):
                st.subheader(f"В работе ({len(it_work)})")
                if it_work:
                    for it in it_work:
                        _it_key = f"it_card_{it['id']}"
                        _it_bg = "#E8F5E9"
                        _it_bc = "#4CAF50"
                        st.markdown(f"<style>.st-key-{_it_key} button {{ background-color: {_it_bg} !important; color: #2C3E50 !important; border: 2px solid {_it_bc} !important; border-radius: 10px !important; text-align: left !important; white-space: normal !important; height: auto !important; }}</style>", unsafe_allow_html=True)
                        with st.container(key=_it_key):
                            _label = f"Задача №{it['id']} — {it.get('text', '')} | {it.get('manager', '—')}"
                            if st.button(_label, key=f"it_btn_{it['id']}", use_container_width=True):
                                st.session_state["dialog_it_key"] = _safe_id(it.get("id", 0))
                                st.rerun()
                else:
                    st.caption("Задач в работе нет.")

        with it_col_review:
            with st.container(border=True):
                st.subheader(f"На проверке ({len(it_review)})")
                if it_review:
                    for it in it_review:
                        _it_key = f"it_card_{it['id']}"
                        _it_bg = "#FFF8E1"
                        _it_bc = "#FF9800"
                        st.markdown(f"<style>.st-key-{_it_key} button {{ background-color: {_it_bg} !important; color: #2C3E50 !important; border: 2px solid {_it_bc} !important; border-radius: 10px !important; text-align: left !important; white-space: normal !important; height: auto !important; }}</style>", unsafe_allow_html=True)
                        with st.container(key=_it_key):
                            _label = f"Задача №{it['id']} — {it.get('text', '')} | {it.get('manager', '—')}"
                            if st.button(_label, key=f"it_btn_{it['id']}", use_container_width=True):
                                st.session_state["dialog_it_key"] = _safe_id(it.get("id", 0))
                                st.rerun()
                else:
                    st.caption("Задач на проверке нет.")

    with it_plan_sub2:
        archived_it = [it for it in internal_tasks if it.get("reviewed", False) or it.get("it_status") == "archived"]
        archived_it.sort(key=lambda t: t.get("last_modified", ""), reverse=True)
        if archived_it:
            for it in archived_it[:50]:
                _it_key = f"it_arch_{it['id']}"
                _label = f"✅ Задача №{it['id']} — {it.get('text', '')} | {it.get('manager', '—')}"
                st.markdown(f"<style>.st-key-{_it_key} button {{ text-align: left !important; justify-content: flex-start !important; white-space: normal !important; height: auto !important; }}</style>", unsafe_allow_html=True)
                with st.container(key=_it_key):
                    if st.button(_label, key=f"it_arch_btn_{it['id']}", use_container_width=True):
                        st.session_state["dialog_it_key"] = _safe_id(it.get("id", 0))
                        st.rerun()
        else:
            st.caption("Архив пуст.")

    # Trigger internal task dialog
    _dialog_it_key = st.session_state.get("dialog_it_key")
    _pending_reminder = st.session_state.get("_pending_reminder_dialog")
    if _pending_reminder:
        create_reminder_dialog(_pending_reminder["entity_type"], _pending_reminder["entity_id"], _pending_reminder["entity_label"])
    elif _dialog_it_key is not None:
        internal_task_detail_dialog(_dialog_it_key)


elif st.session_state.active_tab == "Поставщики":
    st.markdown("### Поставщики")
    suppliers = st.session_state.crm_store.setdefault("suppliers", [])

    show_sup_key = "show_sup_form"
    if render_centered_button("Добавить поставщика", key="btn_new_sup"):
        st.session_state[show_sup_key] = not st.session_state.get(show_sup_key, False)
        st.rerun()
    if st.session_state.get(show_sup_key, False):
        with st.container(border=True):
            sup_name = st.text_input("Название / Имя:", key="sup_name")
            sup_phone = st.text_input("Телефон:", key="sup_phone")
            sup_email = st.text_input("Email:", key="sup_email")
            sup_address = st.text_input("Адрес:", key="sup_address")
            sup_category = st.text_input("Категория товаров:", key="sup_category", placeholder="Что поставляет")
            sup_comment = st.text_area("Комментарии:", key="sup_comment")
            if st.button("Сохранить", key="sup_go", use_container_width=True, type="primary"):
                if not sup_name.strip():
                    st.warning("Введите название")
                else:
                    new_sup = {
                        "id": (max([s.get("id", 0) for s in suppliers], default=0)) + 1,
                        "name": sup_name.strip(),
                        "phone": format_phone(sup_phone) if sup_phone else "",
                        "email": sup_email.strip(),
                        "address": sup_address.strip(),
                        "category": sup_category.strip(),
                        "comment": sup_comment.strip(),
                        "created_at": now_str(),
                        "last_modified": now_str()
                    }
                    suppliers.append(new_sup)
                    st.session_state[show_sup_key] = False
                    commit_and_rerun(st.session_state.crm_store, "Поставщик добавлен")

    st.markdown("---")
    sup_search = st.text_input("Поиск поставщика:", key="sup_search", placeholder="По названию, телефону, категории...").strip().lower()

    filtered_sup = []
    for s in suppliers:
        if sup_search:
            st_text = f"{s.get('name', '')} {s.get('phone', '')} {s.get('email', '')} {s.get('category', '')} {s.get('comment', '')}".lower()
            if sup_search not in st_text: continue
        filtered_sup.append(s)
    filtered_sup.sort(key=lambda s: s.get("name", "").lower())

    if filtered_sup:
        for s in filtered_sup:
            sup_key = f"sup_{s['id']}"
            sup_exp = st.session_state.expanded_task_key == sup_key
            sup_label = f"{s.get('name', 'Без названия')} — {s.get('phone', '—')} | {s.get('category', '—')}"
            sup_selected = sup_exp
            sup_border = "#2196F3" if sup_selected else "#DCE0E5"
            sup_shadow = "box-shadow: 0 0 0 2px rgba(33,150,243,0.3);" if sup_selected else ""
            st.markdown(f"<style>.st-key-sup_wrap_{s['id']} button {{ background-color: #FFFFFF !important; color: #2C3E50 !important; border: 2px solid {sup_border} !important; border-radius: 10px !important; {sup_shadow} }}</style>", unsafe_allow_html=True)
            with st.container(key=f"sup_wrap_{s['id']}"):
                if st.button(sup_label, key=f"sup_card_{s['id']}", use_container_width=True, type="primary" if sup_exp else "secondary"):
                    if sup_exp:
                        st.session_state.expanded_task_key = None
                        save_scroll_and_rerun()
                    else:
                        st.session_state.expanded_task_key = sup_key
                        st.rerun()
                if not sup_exp:
                    render_scroll_restore(f"sup_{s['id']}")
            if sup_exp:
                with st.container(border=True):
                    st.markdown(f"**{s.get('name', '')}**")
                    st.markdown(format_created_date(s), unsafe_allow_html=True)
                    if s.get("phone"):
                        render_phone_inline(s["phone"], f"sup_{s['id']}")
                    info_c, comm_c = st.columns(2)
                    with info_c:
                        st.markdown(f"**Email:** {s.get('email', '—')}")
                        st.markdown(f"**Адрес:** {s.get('address', '—')}")
                        st.markdown(f"**Категория:** {s.get('category', '—')}")
                    with comm_c:
                        if s.get("comment"):
                            st.markdown(f"**Комментарий:** {s['comment']}")
                        else:
                            st.caption("Комментариев нет")
                    st.markdown("---")
                    show_sup_edit = f"show_sup_edit_{s['id']}"
                    if st.button("Редактировать" if not st.session_state.get(show_sup_edit, False) else "Скрыть", key=f"sup_edit_toggle_{s['id']}", use_container_width=True):
                        st.session_state[show_sup_edit] = not st.session_state.get(show_sup_edit, False)
                        st.rerun()
                    if st.session_state.get(show_sup_edit, False):
                        with st.container(border=True):
                            esn = st.text_input("Название:", value=s.get("name", ""), key=f"esn_{s['id']}")
                            esp = st.text_input("Телефон:", value=s.get("phone", ""), key=f"esp_{s['id']}")
                            ese = st.text_input("Email:", value=s.get("email", ""), key=f"ese_{s['id']}")
                            esa = st.text_input("Адрес:", value=s.get("address", ""), key=f"esa_{s['id']}")
                            esc = st.text_input("Категория:", value=s.get("category", ""), key=f"esc_{s['id']}")
                            escom = st.text_area("Комментарий:", value=s.get("comment", ""), key=f"escom_{s['id']}")
                            if st.button("Сохранить", key=f"es_save_{s['id']}", type="primary", use_container_width=True):
                                s["name"] = esn.strip()
                                s["phone"] = format_phone(esp) if esp else ""
                                s["email"] = ese.strip()
                                s["address"] = esa.strip()
                                s["category"] = esc.strip()
                                s["comment"] = escom.strip()
                                s["last_modified"] = now_str()
                                st.session_state[show_sup_edit] = False
                                commit_and_rerun(st.session_state.crm_store, "Поставщик обновлён")
                    if st.session_state.user_role == "admin":
                        st.markdown("---")
                        if st.button("Удалить поставщика", key=f"sup_del_{s['id']}", use_container_width=True):
                            st.session_state.crm_store["suppliers"] = [x for x in suppliers if x["id"] != s["id"]]
                            st.session_state.expanded_task_key = None
                            commit_and_rerun(st.session_state.crm_store, "Поставщик удалён")
                    render_reminders("supplier", s.get("id", ""), s.get("name", "Поставщик"), f"supplier_{s.get('id')}")
    else:
        st.info("Поставщиков нет. Добавьте первого.")

# Supplier cards are inline, so their reminder dialog is dispatched at the script root.
if st.session_state.get("_pending_reminder_dialog") and st.session_state.get("active_tab") == "Поставщики":
    _pending_reminder = st.session_state["_pending_reminder_dialog"]
    create_reminder_dialog(_pending_reminder["entity_type"], _pending_reminder["entity_id"], _pending_reminder["entity_label"])

# Единое окно-оболочка: заголовок и ширина берутся из активного диалога.
# Внутри отображается исходное содержимое соответствующего диалога.
if not st.session_state.get("_crm_dialog_requested_this_run", False):
    st.session_state.pop("_crm_active_dialog", None)

_active_crm_dialog = st.session_state.get("_crm_active_dialog")
if st.session_state.get("_crm_dialog_requested_this_run", False) and _active_crm_dialog:
    _dialog_spec = _CRM_DIALOG_REGISTRY.get(_active_crm_dialog.get("name"))
    if _dialog_spec:
        def _crm_render_active_dialog():
            _target = st.session_state.get("_crm_active_dialog")
            if not _target:
                return
            _spec = _CRM_DIALOG_REGISTRY.get(_target.get("name"))
            if not _spec:
                return
            st.session_state["_crm_inside_dialog_host"] = True
            try:
                _spec["func"](*_target.get("args", ()), **_target.get("kwargs", {}))
            finally:
                st.session_state["_crm_inside_dialog_host"] = False

        _crm_dialog_host = st.dialog(_active_crm_dialog.get("title", "CRM"), width=_active_crm_dialog.get("width", "large"))(_crm_render_active_dialog)
        _crm_dialog_host()
