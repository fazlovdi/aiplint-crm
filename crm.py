import streamlit as st
import streamlit.components.v1 as components
import json, os, re, html, urllib.parse, requests, hashlib, base64, csv, io, secrets, threading, uuid, sqlite3, copy, time, certifi, traceback
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
    /* Размытый фон диалогов и приглушённые родительские окна. */
    dialog[open]::backdrop { background: rgba(24, 32, 44, 0.22) !important; backdrop-filter: blur(4px) !important; }
    [data-testid="stDialog"] { backdrop-filter: blur(3px); }
    .st-key-crm_modal_layer_active { position: relative !important; z-index: 100005 !important; background: #FFFFFF !important; border-radius: 14px !important; }
    [class*="st-key-crm_modal_layer_parent_"] { position: fixed !important; top: 12vh !important; left: 50% !important; transform: translateX(-50%) scale(0.97) !important; width: min(86vw, 940px) !important; max-height: 70vh !important; overflow: auto !important; padding: 1rem !important; border: 1px solid rgba(150,160,175,.55) !important; border-radius: 16px !important; background: rgba(242,245,249,.78) !important; backdrop-filter: blur(2px) !important; box-shadow: 0 18px 50px rgba(20,30,45,.22) !important; opacity: .72 !important; z-index: 100000 !important; pointer-events: none !important; }
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
    /* Верхние кнопки переключения разделов: исходный размер шрифта, габариты кнопок уменьшены на 10% */
    .stHorizontalBlock:has(> div:nth-child(6) [data-testid="stButton"]) > div:nth-child(-n+6) [data-testid="stButton"] > button {
        font-size: 0.85rem !important;
        padding: 0.585rem 0.9rem !important;
        border-radius: 10.8px !important;
        min-height: 0 !important;
    }
    .stHorizontalBlock:has(> div:nth-child(6) [data-testid="stButton"]) > div:nth-child(-n+6) [data-testid="stButton"] > button p,
    .stHorizontalBlock:has(> div:nth-child(6) [data-testid="stButton"]) > div:nth-child(-n+6) [data-testid="stButton"] > button span { font-size: 0.85rem !important; }
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

    /* Отключить всплывающие подсказки Streamlit при наведении на элементы */
    [data-testid="stTooltip"],
    [data-testid="stTooltipContent"],
    [role="tooltip"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

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
    for folder in ["CRM_NE_TROGAT", "CRM_NE_TROGAT/uploads", "CRM_NE_TROGAT/backups", "CRM_NE_TROGAT/logs"]:
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
    """Чтение резервной базы с Яндекс Диска отключено намеренно: Диск — только для резервных копий."""
    return None

def upload_db_to_yandex_sync():
    """Создаёт отдельную версию резервной копии; существующие копии не перезаписываются."""
    if not YANDEX_TOKEN or not os.path.exists(FILE_NAME):
        return False
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            _queue_yandex_snapshot(f.read())
        return True
    except Exception:
        return False

def upload_db_to_yandex_async():
    """Совместимый интерфейс: ставит актуальный снимок базы в очередь фоновой синхронизации."""
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            _queue_yandex_snapshot(f.read())
    except Exception:
        pass

# Состояние фоновых задач должно переживать каждый rerun Streamlit.
# Обычные глобальные переменные пересоздаются при повторном выполнении скрипта,
# из-за чего могли плодиться очереди и повторные резервные копии.
@st.cache_resource(show_spinner=False)
def _get_crm_background_state():
    return {
        "save_lock": threading.Lock(),
        "cloud_lock": threading.Lock(),
        "cloud_pending_snapshot": None,
        "cloud_worker_running": False,
        "cloud_last_ok": None,
        "cloud_last_error": "",
        "cloud_last_backup_name": "",
        "startup_backup_queued": False,
        "process_start_logged": False,
        "cloud_executor": ThreadPoolExecutor(max_workers=1, thread_name_prefix="crm-yandex-sync"),
        "json_lock": threading.Lock(),
        "json_pending_snapshot": None,
        "json_worker_running": False,
        "json_executor": ThreadPoolExecutor(max_workers=1, thread_name_prefix="crm-json-mirror"),
        "log_lock": threading.Lock(),
        "log_executor": ThreadPoolExecutor(max_workers=1, thread_name_prefix="crm-log-sync"),
    }

_CRM_BG_STATE = _get_crm_background_state()

def _validate_backup_snapshot(snapshot_text):
    """Проверяет JSON-структуру и грубые признаки повреждения русской кодировки до загрузки."""
    try:
        data = json.loads(snapshot_text)
    except Exception as exc:
        raise ValueError(f"JSON не читается: {exc}")
    if not isinstance(data, dict):
        raise ValueError("Корень JSON должен быть объектом")
    for key in ("clients", "deals", "users"):
        if key not in data or not isinstance(data.get(key), list):
            raise ValueError(f"В JSON отсутствует корректный список '{key}'")
    if not data["users"]:
        raise ValueError("В резервной копии нет пользователей; загрузка запрещена")
    # Не допускаем перезапись рабочей копии заведомо пустым результатом
    # аварийного fallback (один admin и без клиентов/сделок).
    if (not data["clients"] and not data["deals"] and len(data["users"]) == 1
            and isinstance(data["users"][0], dict)
            and data["users"][0].get("login") == "admin"):
        raise ValueError("Подозрительная пустая база (только admin, без клиентов и сделок); резервная копия не загружена")
    # Не загружаем заведомо повреждённый текст (replacement character или частая UTF-8 mojibake).
    text_parts = []
    def collect_strings(value):
        if isinstance(value, str):
            text_parts.append(value)
        elif isinstance(value, dict):
            for k, v in value.items():
                collect_strings(k)
                collect_strings(v)
        elif isinstance(value, list):
            for item in value:
                collect_strings(item)
    collect_strings(data)
    all_text = " ".join(text_parts)
    if "\ufffd" in all_text:
        raise ValueError("Найдены символы замены � — возможное повреждение кодировки")
    markers = ("Р°", "Рµ", "Рё", "Рё", "Р°", "С‚", "СЏ", "СЋ", "СЂ", "Ð", "Ñ")
    marker_count = sum(all_text.count(marker) for marker in markers)
    threshold = max(25, int(max(len(all_text), 1) * 0.001))
    if marker_count > threshold:
        raise ValueError("Обнаружены многочисленные признаки повреждения русской кодировки; резервная копия не загружена")
    return data

def _sanitize_backup_data(data):
    """Убирает из резервной копии активные сессии, remember-токены и устаревший открытый PIN.

    Рабочую базу не меняет: очистка выполняется только для переносимого бэкапа.
    Хэши паролей и login_pin сохраняются, чтобы после ручного восстановления
    пользователи могли войти обычным способом.
    """
    safe_data = copy.deepcopy(data)
    for user in safe_data.get("users", []):
        if not isinstance(user, dict):
            continue
        for key in ("auth_sessions", "remember_tokens", "remember_token", "session_token", "session_tokens", "pin"):
            user.pop(key, None)
    return safe_data

def _prepare_backup_snapshot(snapshot_text):
    """Проверяет JSON и готовит безопасный снимок для записи на Яндекс Диск."""
    data = _validate_backup_snapshot(snapshot_text)
    safe_data = _sanitize_backup_data(data)
    safe_text = json.dumps(safe_data, ensure_ascii=False, separators=(",", ":"))
    _validate_backup_snapshot(safe_text)
    return safe_text

def _upload_yandex_snapshot(snapshot_text, daily=False):
    """Сохраняет одну перезаписываемую актуальную копию и отдельную архивную копию за день."""

    if not YANDEX_TOKEN:
        raise RuntimeError("Не задан YANDEX_DISK_TOKEN")

    safe_text = _prepare_backup_snapshot(snapshot_text)
    payload = safe_text.encode("utf-8")

    if daily:
        # Архивная копия: один файл на календарный день, не перезаписывается.
        remote_name = f"CRM_daily_{moscow_now().strftime('%Y-%m-%d')}.json"
        overwrite = "false"
    else:
        # Актуальная копия: всегда один и тот же файл, обновляется новыми данными.
        remote_name = "CRM_latest.json"
        overwrite = "true"

    remote_path = f"disk:/CRM_NE_TROGAT/backups/{remote_name}"
    last_error = "Не удалось загрузить резервную копию на Яндекс Диск"

    for attempt in range(3):
        try:
            res = requests.get(
                f"{YANDEX_API_URL}/upload",
                params={"path": remote_path, "overwrite": overwrite},
                headers=yandex_headers(), timeout=15)

            if res.status_code == 200:
                href = res.json().get("href")
                if href:
                    resp = requests.put(
                        href, data=payload, timeout=30,
                        headers={"Content-Type": "application/json; charset=utf-8"})
                    if resp.status_code in (200, 201, 202):
                        _CRM_BG_STATE["cloud_last_backup_name"] = remote_name
                        return True
                    last_error = f"HTTP {resp.status_code} при загрузке резервной копии"
                else:
                    last_error = "Яндекс Диск не вернул ссылку для загрузки"
            elif res.status_code == 409 and daily:
                # Дневной архив уже существует; не создаём второй файл за этот день.
                _CRM_BG_STATE["cloud_last_backup_name"] = remote_name
                return True
            else:
                last_error = f"HTTP {res.status_code} при создании резервной копии"
        except Exception as exc:
            last_error = str(exc)[:300]

        if attempt < 2:
            time.sleep(0.5 * (attempt + 1))

    raise RuntimeError(last_error)

def _upload_yandex_pre_restore_snapshot(snapshot_text):
    """Сохраняет текущую рабочую базу отдельным неизменяемым файлом перед восстановлением."""
    if not YANDEX_TOKEN:
        raise RuntimeError("Не задан YANDEX_DISK_TOKEN — безопасное восстановление остановлено")
    safe_text = _prepare_backup_snapshot(snapshot_text)
    payload = safe_text.encode("utf-8")
    remote_name = f"CRM_pre_restore_{moscow_now().strftime('%Y%m%d_%H%M%S_%f')}.json"
    remote_path = f"disk:/CRM_NE_TROGAT/backups/{remote_name}"
    last_error = "Не удалось сохранить резервную копию текущей базы перед восстановлением"
    for attempt in range(3):
        try:
            res = requests.get(
                f"{YANDEX_API_URL}/upload",
                params={"path": remote_path, "overwrite": "false"},
                headers=yandex_headers(), timeout=15)
            if res.status_code == 200:
                href = res.json().get("href")
                if not href:
                    last_error = "Яндекс Диск не вернул ссылку для предохранительной копии"
                else:
                    resp = requests.put(
                        href, data=payload, timeout=30,
                        headers={"Content-Type": "application/json; charset=utf-8"})
                    if resp.status_code in (200, 201, 202):
                        return remote_name
                    last_error = f"HTTP {resp.status_code} при загрузке предохранительной копии"
            else:
                last_error = f"HTTP {res.status_code} при создании предохранительной копии"
        except Exception as exc:
            last_error = str(exc)[:300]
        if attempt < 2:
            time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(last_error)

def _cloud_sync_worker():
    """Объединяет серию быстрых сохранений в один фоновый upload."""
    state = _CRM_BG_STATE
    debounce_seconds = 45
    while True:
        time.sleep(debounce_seconds)
        with state["cloud_lock"]:
            snapshot = state["cloud_pending_snapshot"]
            state["cloud_pending_snapshot"] = None
            if snapshot is None:
                state["cloud_worker_running"] = False
                return
        try:
            ok = _upload_yandex_snapshot(snapshot)
            state["cloud_last_ok"] = bool(ok)
            state["cloud_last_error"] = "" if ok else "Не удалось загрузить базу на Яндекс Диск"
            _crm_log("BACKUP_UPLOAD_OK" if ok else "BACKUP_UPLOAD_ERROR", {"target": "CRM_latest.json"}, remote=True)
            try:
                _upload_yandex_snapshot(snapshot, daily=True)
            except Exception:
                pass
        except Exception as exc:
            state["cloud_last_ok"] = False
            state["cloud_last_error"] = str(exc)[:300]
            _crm_log("BACKUP_UPLOAD_ERROR", {"target": "CRM_latest.json"}, exc=exc, remote=True)

def _queue_yandex_snapshot(snapshot_text):
    state = _CRM_BG_STATE
    if not YANDEX_TOKEN:
        return
    with state["cloud_lock"]:
        state["cloud_pending_snapshot"] = snapshot_text
        if not state["cloud_worker_running"]:
            state["cloud_worker_running"] = True
            state["cloud_executor"].submit(_cloud_sync_worker)

def _queue_startup_backup_once():
    """Ставит начальную копию в очередь только один раз на процесс приложения."""
    state = _CRM_BG_STATE
    if not YANDEX_TOKEN:
        return
    with state["cloud_lock"]:
        if state["startup_backup_queued"]:
            return
        try:
            conn = _sqlite_connect()
            try:
                row = conn.execute("SELECT data FROM crm_state WHERE id = 1").fetchone()
            finally:
                conn.close()
            if not row or not row[0]:
                return
            state["startup_backup_queued"] = True
            snapshot = row[0]
        except Exception:
            return
    _queue_yandex_snapshot(snapshot)

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

# Журнал событий CRM. Копия на Яндекс Диске переживает перезапуск Streamlit Cloud.
_CRM_LOG_DIR = "CRM_NE_TROGAT/logs"
_CRM_LOG_LOCAL_DIR = Path("/tmp/crm_system_logs")
_CRM_LOG_LOCAL_DIR.mkdir(parents=True, exist_ok=True)


def _crm_log(event, details=None, exc=None, remote=True):
    """Записывает безопасное событие локально и, для важных событий, в журнал на Яндекс Диске."""
    try:
        record = {
            "time_moscow": now_str(),
            "event": str(event)[:100],
            "user": str(st.session_state.get("user_login", "system") or "system")[:80],
        }
        if isinstance(details, dict):
            # Не сохраняем значения ключей, которые могут содержать секреты/персональные данные.
            safe_details = {}
            for key, value in list(details.items())[:20]:
                key_text = str(key)[:80]
                if any(word in key_text.lower() for word in ("password", "token", "pin", "secret", "cookie", "authorization")):
                    continue
                safe_details[key_text] = str(value)[:300]
            if safe_details:
                record["details"] = safe_details
        if exc is not None:
            record["error_type"] = type(exc).__name__[:100]
            err_text = str(exc)[:800]
            if YANDEX_TOKEN:
                err_text = err_text.replace(YANDEX_TOKEN, "[REDACTED]")
            record["error"] = err_text
            try:
                trace_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-3500:]
                if YANDEX_TOKEN:
                    trace_text = trace_text.replace(YANDEX_TOKEN, "[REDACTED]")
                record["traceback"] = trace_text
            except Exception:
                pass
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        day = moscow_now().strftime("%Y-%m-%d")
        local_path = _CRM_LOG_LOCAL_DIR / f"CRM_log_{day}.jsonl"
        with _CRM_BG_STATE["log_lock"]:
            with open(local_path, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
        # Синхронизация в фоне, чтобы запись в CRM не ждала сетевые запросы к Яндекс Диску.
        if remote and YANDEX_TOKEN:
            _CRM_BG_STATE["log_executor"].submit(_append_crm_log_to_yandex, day, line)
    except Exception:
        # Ошибка журналирования не должна ломать работу CRM.
        pass


def _append_crm_log_to_yandex(day, new_line):
    """Добавляет строку в дневной JSONL-файл на Яндекс Диске через безопасный read/modify/write."""
    if not YANDEX_TOKEN:
        return False
    remote_path = f"disk:/{_CRM_LOG_DIR}/CRM_log_{day}.jsonl"
    # Создать каталог, если это первый запуск журнала.
    try:
        folder_res = requests.put(YANDEX_API_URL, params={"path": f"disk:/{_CRM_LOG_DIR}"}, headers=yandex_headers(), timeout=8)
        if folder_res.status_code not in (201, 202, 409):
            # Каталог мог уже существовать; окончательный результат проверит upload ниже.
            pass
    except Exception:
        pass

    existing = b""
    try:
        dres = requests.get(f"{YANDEX_API_URL}/download", params={"path": remote_path}, headers=yandex_headers(), timeout=8)
        if dres.status_code == 200:
            href = dres.json().get("href")
            if href:
                fres = requests.get(href, timeout=12)
                if fres.status_code == 200:
                    existing = fres.content
    except Exception:
        existing = b""

    # Защита от бесконечного роста одного дневного файла: оставляем последние 5000 строк.
    try:
        old_lines = existing.decode("utf-8", errors="replace").splitlines()
    except Exception:
        old_lines = []
    all_lines = (old_lines + [new_line.rstrip("\n")])[-5000:]
    payload = ("\n".join(all_lines) + "\n").encode("utf-8")
    try:
        ures = requests.get(f"{YANDEX_API_URL}/upload", params={"path": remote_path, "overwrite": "true"}, headers=yandex_headers(), timeout=10)
        if ures.status_code != 200:
            return False
        href = ures.json().get("href")
        if not href:
            return False
        put_res = requests.put(href, data=payload, timeout=20, headers={"Content-Type": "application/x-ndjson; charset=utf-8"})
        return put_res.status_code in (200, 201, 202)
    except Exception:
        return False


def _get_yandex_crm_logs():
    """Возвращает доступные дневные журналы с Яндекс Диска, от новых к старым."""
    if not YANDEX_TOKEN:
        raise RuntimeError("Не задан YANDEX_DISK_TOKEN в Streamlit Secrets")
    res = requests.get(
        YANDEX_API_URL,
        params={"path": f"disk:/{_CRM_LOG_DIR}", "limit": 100, "sort": "-modified"},
        headers=yandex_headers(), timeout=15,
    )
    if res.status_code == 404:
        return []
    res.raise_for_status()
    items = res.json().get("_embedded", {}).get("items", [])
    files = [x for x in items if x.get("type") == "file" and str(x.get("name", "")).startswith("CRM_log_") and str(x.get("name", "")).endswith(".jsonl")]
    return sorted(files, key=lambda x: str(x.get("modified", "")), reverse=True)


def _read_yandex_crm_log(remote_name):
    if not YANDEX_TOKEN:
        raise RuntimeError("Не задан YANDEX_DISK_TOKEN в Streamlit Secrets")
    if not re.fullmatch(r"CRM_log_\d{4}-\d{2}-\d{2}\.jsonl", str(remote_name)):
        raise ValueError("Недопустимое имя файла журнала")
    remote_path = f"disk:/{_CRM_LOG_DIR}/{remote_name}"
    res = requests.get(f"{YANDEX_API_URL}/download", params={"path": remote_path}, headers=yandex_headers(), timeout=15)
    res.raise_for_status()
    href = res.json().get("href")
    if not href:
        raise RuntimeError("Яндекс Диск не вернул ссылку на журнал")
    file_res = requests.get(href, timeout=20)
    file_res.raise_for_status()
    return file_res.content.decode("utf-8", errors="replace")


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

    # По умолчанию показываем и загружаем содержимое только первых трёх файлов,
    # чтобы окна с большим количеством вложений открывались быстрее.
    _show_all_key = f"files_show_all_{prefix}"
    _show_all = bool(st.session_state.get(_show_all_key, False))

    # Сначала новые вложения: используем дату файла, если она есть, затем
    # timestamp из имени сохранённого файла; для старых вложений без даты
    # сохраняем естественный порядок списка (новые добавляются в конец).
    def _file_recency(entry):
        _original_idx, _file = entry
        _date_value = str(_file.get("created_at") or _file.get("uploaded_at") or _file.get("last_modified") or "")
        if _date_value:
            return (2, _date_value)
        _path_value = str(_file.get("file_path", _file.get("path", "")) or "")
        _match = re.search(r"_(\d{9,})_", _path_value)
        if _match:
            return (2, _match.group(1))
        return (1, _original_idx)

    _sorted_file_entries = sorted(enumerate(files), key=_file_recency, reverse=True)
    _visible_count = len(files) if _show_all else min(3, len(files))
    _visible_files = _sorted_file_entries[:_visible_count]
    file_paths = [ff.get("file_path", ff.get("path")) for _, ff in _visible_files]
    with ThreadPoolExecutor(max_workers=min(4, max(1, len(file_paths)))) as executor:
        file_bytes_list = list(executor.map(get_file_bytes, file_paths))

    for (i, ff), fb in zip(_visible_files, file_bytes_list):
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

    if len(files) > 3:
        _remaining = len(files) - _visible_count
        _button_label = "Скрыть дополнительные файлы" if _show_all else "Показать все файлы"
        _button_key = f"show_all_files_btn_{prefix}"
        if st.button(_button_label, key=_button_key, use_container_width=True):
            st.session_state[_show_all_key] = not _show_all
            st.rerun()


def _task_products_from_calculation(deal, calculation_id):
    """Возвращает позиции расчёта для задачи, без стоимости и доставки."""
    if not deal or not calculation_id:
        return []
    calc = next((x for x in deal.get("calculations", []) if str(x.get("id")) == str(calculation_id) and not x.get("deleted")), None)
    if not calc:
        return []
    catalog = st.session_state.crm_store.get("products", DEFAULT_PRODUCT_CATALOG)
    result = []
    for row in _calculation_rows(calc, catalog):
        sku = str(row.get("sku", "") or "").strip()
        name = str(row.get("name", "") or "").strip()
        qty = row.get("quantity", 0)
        try:
            qty_text = f"{float(qty):g}"
        except (TypeError, ValueError):
            qty_text = str(qty)
        unit = str(row.get("unit", "шт.") or "шт.")
        title = " ".join(x for x in (sku, name) if x)
        if title:
            result.append(f"{title} — {qty_text} {unit}")
    return result


def render_task_products_editor(deal, key_prefix, existing_products="", existing_calc_id=""):
    """Выбор расчёта и список товарных позиций с возможностью добавить строку вручную."""
    active = [c for c in (deal or {}).get("calculations", []) if not c.get("deleted")]
    calc_ids = [str(c.get("id")) for c in active]
    calc_by_id = {str(c.get("id")): c for c in active}
    if key_prefix.startswith("nt_"):
        _suffix = key_prefix[3:]
        calc_key = f"nt_order_calc_{_suffix}"
        products_key = f"nt_prod_{_suffix}"
    elif key_prefix.startswith("edit_"):
        _suffix = key_prefix[5:]
        calc_key = f"edit_order_calc_{_suffix}"
        products_key = f"edit_prod_{_suffix}"
    else:
        calc_key = f"{key_prefix}_order_calc"
        products_key = f"{key_prefix}_prod"
    last_calc_key = f"{key_prefix}_last_products_calc"
    if products_key not in st.session_state:
        st.session_state[products_key] = str(existing_products or "")
    selected_id = ""
    if active:
        if st.session_state.get(calc_key) not in calc_ids:
            st.session_state[calc_key] = str(existing_calc_id) if str(existing_calc_id) in calc_ids else calc_ids[0]
        selected_id = st.selectbox(
            "Расчёт заказа:", calc_ids,
            format_func=lambda cid: calc_by_id[cid].get("name", "Расчёт"),
            key=calc_key
        )
        if last_calc_key not in st.session_state:
            # При первом открытии редактирования сохраняем ручные товары из задачи.
            # Если список пустой, заполняем его товарами выбранного расчёта.
            if not str(st.session_state.get(products_key, "") or "").strip():
                st.session_state[products_key] = "\\n".join(_task_products_from_calculation(deal, selected_id))
            st.session_state[last_calc_key] = str(selected_id)
        elif st.session_state.get(last_calc_key) != str(selected_id):
            # При явной смене расчёта обновляем список из нового расчёта.
            st.session_state[products_key] = "\\n".join(_task_products_from_calculation(deal, selected_id))
            st.session_state[last_calc_key] = str(selected_id)
    else:
        st.caption("В сделке пока нет сохранённых расчётов.")
    products = str(st.session_state.get(products_key, "") or "")
    st.markdown("**Товары:**")
    if products.strip():
        for line in products.splitlines():
            if line.strip():
                st.markdown(f"- {html.escape(line.strip())}", unsafe_allow_html=True)
    else:
        st.caption("Товары не добавлены.")
    add_key = f"{key_prefix}_add_product"
    # Streamlit запрещает менять значение ключа виджета после его создания в текущем проходе.
    # Флаг очищается до создания text_input на следующем проходе.
    if st.session_state.pop(f"{add_key}_clear_pending", False):
        st.session_state[add_key] = ""
    st.markdown(f"<style>.st-key-{add_key} input::placeholder {{font-size:0.78rem!important;font-style:italic!important;color:#9AA3AD!important;opacity:1!important;}}</style>", unsafe_allow_html=True)
    _add_col, _btn_col = st.columns([5, 1])
    with _add_col:
        st.text_input("Добавить товар", key=add_key, placeholder="Добавить товар...", label_visibility="collapsed")
    with _btn_col:
        if st.button("Добавить", key=f"{key_prefix}_add_product_btn", use_container_width=True):
            new_line = str(st.session_state.get(add_key, "") or "").strip()
            if new_line:
                current = str(st.session_state.get(products_key, "") or "").strip()
                st.session_state[products_key] = (current + "\n" if current else "") + new_line
                st.session_state[f"{add_key}_clear_pending"] = True
                st.rerun()
    return str(selected_id), str(st.session_state.get(products_key, "") or "")

def build_print_html(task, cl, tp, fd):
    def esc(s): return str(s if s else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    products_html = esc(task.get('products', '')).replace('\n', '<br>')
    oav = task.get('order_amount', 0)
    cost_html = f"<div style='margin-top:6px;font-size:16px;font-weight:bold;'>Сумма: {oav:,.0f} руб.</div>".replace(",", " ") if oav and oav > 0 else ""
    file_reminder = "<div style='color:#D65757;font-weight:bold;margin:14px 0;border:2px solid #D65757;padding:8px;border-radius:8px;'>&#9888; Не забудь распечатать вложенные файлы!</div>" if task.get("task_files") else ""
    lb = get_logo_base64()
    logo_html = f"<img src='data:image/png;base64,{lb}' width='180' style='float:left;margin-right:20px;'/>" if lb else "<div style='font-size:24px;font-weight:bold;float:left;margin-right:20px;'>АЙПЛИНТ</div>"
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><title>Бланк задачи</title><style>body {{ font-family: Arial, sans-serif; margin: 40px; color: #222; }} .header {{ text-align: center; border-bottom: 2px solid #333; padding: 10px; }} .row {{ margin: 8px 0; }} hr {{ border: none; border-top: 1px solid #ccc; margin: 14px 0; }} .sig {{ margin-top: 30px; }} .sig p {{ margin: 12px 0; }}</style></head><body><div>{logo_html}</div><div class="header"><h2>БЛАНК ЗАДАЧИ</h2><p>{moscow_now().strftime('%d.%m.%Y')}</p></div><div class="row"><b>Задача:</b> №{esc(task.get('task_number', ''))}</div><div class="row"><b>Клиент:</b> {esc(cl['name'])} ({esc(cl['phone'])})</div><div class="row"><b>Тип:</b> {esc(tp)}</div>{'' if tp in ("Отправить заказ", "Отправить образцы") else f'<div class="row"><b>Тема:</b> {esc(task.get("text", ""))}</div>'}<div class="row"><b>Срок:</b> {esc(fd)}</div><div class="row"><b>Ответственный:</b> {esc(task.get('manager', ''))}</div><hr><div class="row"><b>Товары:</b><br>{products_html}</div><div class="row"><b>Город:</b> {esc(task.get('ship_city', ''))}</div><div class="row"><b>Адрес:</b> {esc(task.get('ship_addr', ''))}</div><div class="row"><b>Получатель:</b> {esc(task.get('receiver', ''))} ({esc(task.get('receiver_phone', ''))})</div><div class="row"><b>Оплата:</b> {esc(task.get('ship_pay', ''))}</div><div class="row"><b>Трек:</b> {esc(task.get('tk_num', ''))}</div>{cost_html}{file_reminder}<div class="sig"><p>Отпустил: _____________</p><p>Получил: _____________</p></div></body></html>"""

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

def _crm_workspace_client_id(name, args=(), kwargs=None):
    """Best-effort resolve the client associated with a dialog."""
    kwargs = kwargs or {}
    store = st.session_state.get("crm_store", {})
    clients = store.get("clients", []) if isinstance(store, dict) else []
    deals = store.get("deals", []) if isinstance(store, dict) else []
    def find_client(value):
        if isinstance(value, dict):
            cid = value.get("client_id")
            if cid is None:
                cid = value.get("cl_id")
            if cid is None:
                cid = value.get("id")
            if cid is not None:
                matched = next((c for c in clients if str(c.get("id")) == str(cid)), None)
                if matched is not None:
                    return matched.get("id")
        if value is not None:
            matched = next((c for c in clients if str(c.get("id")) == str(value)), None)
            if matched is not None:
                return matched.get("id")
        return None
    # Named client parameters are safest and work across most dialogs.
    for key in ("cl_id", "client_id", "client", "cl"):
        if key in kwargs:
            found = find_client(kwargs[key])
            if found: return found
    # Function-specific argument positions.
    if name in ("client_detail_dialog", "client_deals_dialog", "create_deal_dialog", "client_create_task_dialog", "client_create_deal_task_dialog", "client_tasks_dialog") and args:
        found = find_client(args[0])
        if found: return found
    if name in ("deal_detail_dialog", "task_detail_dialog"):
        for value in args:
            found = find_client(value)
            if found: return found
    if name in ("client_requisites_dialog", "client_requisites_view_dialog") and args:
        found = find_client(args[0])
        if found: return found
    deal_id = kwargs.get("deal_id")
    if deal_id is None and name in ("deal_calculation_dialog", "invoice_document_dialog", "deal_report_dialog", "close_deal_dialog", "deal_create_task_dialog") and args:
        deal_id = args[0]
    if deal_id is not None:
        deal = next((d for d in deals if str(d.get("id")) == str(deal_id)), None)
        if deal:
            found = find_client(deal.get("client_id"))
            if found: return found
    # Some dialog calls pass a deal object or a client object positionally.
    for value in args:
        found = find_client(value)
        if found: return found
        if isinstance(value, dict) and value.get("client_id") is not None:
            deal = next((d for d in deals if str(d.get("id")) == str(value.get("id"))), None)
            if deal:
                found = find_client(deal.get("client_id"))
                if found: return found
    return None

def _crm_workspace_client_name(client_id):
    store = st.session_state.get("crm_store", {})
    client = next((c for c in store.get("clients", []) if str(c.get("id")) == str(client_id)), None)
    return str((client or {}).get("name") or "Клиент")

def _crm_workspace_tab_label(entry):
    """Compact tab caption based on the actual task/deal number."""
    name = str(entry.get("name", ""))
    args = entry.get("args", ()) or ()
    kwargs = entry.get("kwargs", {}) or {}
    if name == "client_detail_dialog":
        return "Карточка клиента"

    # Task detail/report dialogs receive the task object as the first argument.
    if name in ("task_detail_dialog", "task_report_dialog", "task_execution_report_dialog") and args:
        task = args[0] if isinstance(args[0], dict) else None
        if task and task.get("task_number"):
            return str(task["task_number"])

    # Deal detail dialogs receive the deal object as the first argument.
    if name == "deal_detail_dialog" and args:
        deal = args[0] if isinstance(args[0], dict) else None
        if deal:
            return str(deal.get("deal_number") or deal.get("title") or f"Сделка {deal.get('id', '')}")

    # Calculations, invoices and reports are identified by their parent deal number.
    deal_id = kwargs.get("deal_id")
    if deal_id is None and name in ("deal_calculation_dialog", "invoice_document_dialog", "deal_report_dialog", "close_deal_dialog") and args:
        deal_id = args[0]
    if deal_id is not None:
        deal = next((d for d in st.session_state.get("crm_store", {}).get("deals", []) if str(d.get("id")) == str(deal_id)), None)
        if deal:
            base = str(deal.get("deal_number") or deal.get("title") or f"Сделка {deal_id}")
            if name == "deal_calculation_dialog":
                calc_id = args[1] if len(args) > 1 else kwargs.get("calc_id")
                calculations = [c for c in deal.get("calculations", []) if not c.get("deleted")]
                pos = next((i + 1 for i, c in enumerate(calculations) if str(c.get("id")) == str(calc_id)), None)
                return f"{base} · Расчёт {pos}" if pos else f"{base} · Расчёт"
            if name == "invoice_document_dialog":
                return f"{base} · Счёт"
            if name == "deal_report_dialog":
                return f"{base} · Отчёт"
            if name == "close_deal_dialog":
                return f"{base} · Завершение"
            return base

    # Other dialogs: prefer a numbered task/deal/client object if one is passed.
    for value in args:
        if isinstance(value, dict):
            if value.get("task_number"):
                return str(value["task_number"])
            if value.get("deal_number"):
                return str(value["deal_number"])
    title = str(entry.get("title") or name or "Окно")
    return title.replace("Подробности", "").strip() or "Окно"

def _crm_workspace_tab_key(entry):
    """Stable tab identity: the same entity/dialog can only occupy one tab."""
    name = str(entry.get("name", ""))
    args = entry.get("args", ()) or ()
    kwargs = entry.get("kwargs", {}) or {}
    if name == "deal_detail_dialog" and args:
        deal = args[0]
        entity_id = deal.get("id") if isinstance(deal, dict) else deal
        return f"{name}|deal:{entity_id}"
    if name in ("client_detail_dialog", "client_requisites_dialog", "client_requisites_view_dialog") and args:
        return f"{name}|client:{args[0]}|{repr(tuple(args[1:]))}"
    if name in ("deal_calculation_dialog", "invoice_document_dialog", "deal_report_dialog", "close_deal_dialog") and args:
        return f"{name}|deal:{args[0]}|calc:{args[1] if len(args) > 1 else ''}"
    return name + "|" + repr(entry.get("signature", ""))

def _crm_workspace_open_dialog(entry, client_id=None, from_host=False):
    """Add a dialog as a tab in the current client workspace, or create one."""
    windows = st.session_state.setdefault("_crm_windows", [])
    active_id = st.session_state.get("_crm_active_window_id")
    window = next((w for w in windows if w.get("id") == active_id), None)
    if client_id:
        # Prefer an existing window for this client, including a minimized one.
        window = next((w for w in windows if str(w.get("client_id")) == str(client_id)), window if window and str(window.get("client_id")) == str(client_id) else None)
    if not window:
        client_id = client_id or None
        window_id = "cw_" + hashlib.sha1((str(client_id or "general") + "|" + str(moscow_now().timestamp()) + "|" + str(len(windows))).encode("utf-8")).hexdigest()[:12]
        window = {"id": window_id, "client_id": str(client_id) if client_id else None,
                  "title": _crm_workspace_client_name(client_id) if client_id else str(entry.get("title") or "CRM"),
                  "tabs": [], "active_tab": 0, "minimized": False}
        windows.append(window)
    # If a deal was opened directly, add the client as a permanent first tab.
    if client_id and entry.get("name") != "client_detail_dialog":
        client_entry = {"name": "client_detail_dialog", "title": "Карточка клиента", "width": "large",
                        "args": (client_id,), "kwargs": {},
                        "signature": (_crm_dialog_signature_value((client_id,)), _crm_dialog_signature_value({}))}
        _client_tab_key = _crm_workspace_tab_key(client_entry)
        _existing_client_tab = next((i for i, t in enumerate(window["tabs"]) if _crm_workspace_tab_key(t) == _client_tab_key), None)
        if _existing_client_tab is None:
            window["tabs"].insert(0, client_entry)
            if window.get("active_tab", 0) >= 0:
                window["active_tab"] += 1
    key = _crm_workspace_tab_key(entry)
    existing = next((i for i, t in enumerate(window["tabs"]) if _crm_workspace_tab_key(t) == key), None)
    if existing is None:
        window["tabs"].append(entry.copy())
        existing = len(window["tabs"]) - 1
    else:
        # Refresh object references and arguments for an already-open tab.
        window["tabs"][existing].update(entry)
    window["active_tab"] = existing
    window["minimized"] = False
    st.session_state["_crm_active_window_id"] = window["id"]
    st.session_state["_crm_active_dialog"] = window["tabs"][existing]
    st.session_state["_crm_dialog_requested_this_run"] = True
    _crm_workspace_queue_save()

# Workspace state is stored separately from the CRM database, per login.
def _crm_workspace_remote_path(login):
    safe = hashlib.sha256(str(login or "anonymous").encode("utf-8")).hexdigest()[:24]
    return f"disk:/CRM_NE_TROGAT/workspaces/workspace_{safe}.json"

def _crm_workspace_save_remote(login, payload):
    try:
        folder = "disk:/CRM_NE_TROGAT/workspaces"
        requests.put(YANDEX_API_URL, params={"path": folder}, headers=yandex_headers(), timeout=5)
        path = _crm_workspace_remote_path(login)
        r = requests.get(f"{YANDEX_API_URL}/upload", params={"path": path, "overwrite": "true"}, headers=yandex_headers(), timeout=8)
        if r.status_code not in (200, 201): return False
        href = r.json().get("href")
        if not href: return False
        up = requests.put(href, data=payload.encode("utf-8"), timeout=10)
        return up.status_code in (200, 201, 202)
    except Exception:
        return False

def _crm_workspace_load_remote(login):
    try:
        path = _crm_workspace_remote_path(login)
        r = requests.get(f"{YANDEX_API_URL}/download", params={"path": path}, headers=yandex_headers(), timeout=5)
        if r.status_code != 200: return None
        href = r.json().get("href")
        if not href: return None
        data = requests.get(href, timeout=8)
        if data.status_code != 200: return None
        obj = data.json()
        return obj if isinstance(obj, dict) and obj.get("version") == 1 else None
    except Exception:
        return None

_WORKSPACE_SAVE_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="crm-workspace-save")
def _crm_workspace_queue_save():
    try:
        login = str(st.session_state.get("user_login") or st.session_state.get("user_name") or "")
        if not login: return
        windows = st.session_state.get("_crm_windows", [])
        safe_windows = []
        for w in windows:
            safe_tabs = []
            for tab in w.get("tabs", []):
                safe_tabs.append({k: tab.get(k) for k in ("name", "title", "width", "args", "kwargs", "signature")})
            safe_windows.append({"id": w.get("id"), "client_id": w.get("client_id"), "title": w.get("title"),
                                "tabs": safe_tabs, "active_tab": w.get("active_tab", 0), "minimized": bool(w.get("minimized"))})
        payload = json.dumps({"version": 1, "windows": safe_windows, "active_window_id": st.session_state.get("_crm_active_window_id")}, ensure_ascii=False, default=str)
        # Avoid repeated network writes for identical state during Streamlit reruns.
        if st.session_state.get("_crm_last_queued_workspace_payload") == payload:
            return
        st.session_state["_crm_last_queued_workspace_payload"] = payload
        _WORKSPACE_SAVE_EXECUTOR.submit(_crm_workspace_save_remote, login, payload)
    except Exception:
        pass

def _crm_workspace_init():
    if st.session_state.get("_crm_workspace_initialized"):
        return
    st.session_state["_crm_workspace_initialized"] = True
    login = str(st.session_state.get("user_login") or st.session_state.get("user_name") or "")
    if not login:
        return
    saved = _crm_workspace_load_remote(login)
    if not saved: return
    store = st.session_state.get("crm_store", {})
    clients = {str(c.get("id")) for c in store.get("clients", [])}
    deals = {str(d.get("id")) for d in store.get("deals", [])}
    restored = []
    for w in saved.get("windows", [])[:20]:
        cid = str(w.get("client_id")) if w.get("client_id") is not None else None
        if cid and cid not in clients: continue
        tabs = []
        for t in w.get("tabs", [])[:30]:
            if t.get("name") not in _CRM_DIALOG_REGISTRY: continue
            args = t.get("args", [])
            if not isinstance(args, (list, tuple)): args = []
            # Reconnect serialized entity dictionaries to the latest objects in crm_store.
            def _rehydrate_workspace_arg(value):
                if isinstance(value, dict):
                    obj_id = value.get("id")
                    if obj_id is not None:
                        for _collection in ("clients", "deals", "users", "internal_tasks"):
                            _match = next((x for x in store.get(_collection, []) if str(x.get("id")) == str(obj_id)), None)
                            if _match is not None: return _match
                        for _client in store.get("clients", []):
                            for _task in _client.get("tasks", []) if isinstance(_client.get("tasks"), list) else []:
                                if str(_task.get("id")) == str(obj_id): return _task
                        for _deal in store.get("deals", []):
                            for _task in _deal.get("tasks", []) if isinstance(_deal.get("tasks"), list) else []:
                                if str(_task.get("id")) == str(obj_id): return _task
                    return {k: _rehydrate_workspace_arg(v) for k, v in value.items()}
                if isinstance(value, list): return [_rehydrate_workspace_arg(v) for v in value]
                return value
            args = [_rehydrate_workspace_arg(a) for a in args]
            # Validate references that can be stale after records are removed.
            if t.get("name") in ("client_detail_dialog", "client_deals_dialog", "create_deal_dialog", "client_tasks_dialog", "client_create_task_dialog", "client_create_deal_task_dialog") and args and str(args[0]) not in clients: continue
            if t.get("name") in ("deal_calculation_dialog", "invoice_document_dialog", "deal_report_dialog", "close_deal_dialog") and args and str(args[0]) not in deals: continue
            _restored_kwargs = _rehydrate_workspace_arg(t.get("kwargs", {}))
            _restored_signature = (_crm_dialog_signature_value(tuple(args)), _crm_dialog_signature_value(_restored_kwargs))
            tabs.append({"name": t["name"], "title": t.get("title", "CRM"), "width": t.get("width", "large"),
                         "args": tuple(args), "kwargs": _restored_kwargs, "signature": _restored_signature})
        if tabs:
            restored.append({"id": w.get("id") or "cw_restored", "client_id": cid, "title": w.get("title") or (_crm_workspace_client_name(cid) if cid else "CRM"),
                            "tabs": tabs, "active_tab": max(0, min(int(w.get("active_tab", 0) or 0), len(tabs)-1)), "minimized": bool(w.get("minimized"))})
    st.session_state["_crm_windows"] = restored
    active_id = saved.get("active_window_id")
    st.session_state["_crm_active_window_id"] = active_id if any(w.get("id") == active_id and not w.get("minimized") for w in restored) else next((w.get("id") for w in restored if not w.get("minimized")), None)

def _crm_dialog(title, width="large"):
    def _decorate(func):
        _CRM_DIALOG_REGISTRY[func.__name__] = {"func": func, "title": title, "width": width}
        def _request_dialog(*args, **kwargs):
            if st.session_state.get("_crm_rendering_background_dialog", False):
                return None

            signature = (_crm_dialog_signature_value(args), _crm_dialog_signature_value(kwargs))
            entry = {"name": func.__name__, "title": title, "width": width,
                     "args": args, "kwargs": kwargs, "signature": signature}
            inside_host = bool(st.session_state.get("_crm_inside_dialog_host", False))

            # A legacy dispatcher may request the same dialog again on every rerun.
            # If this exact dialog is already the active tab, do not rewrite workspace
            # state, queue another remote save, or trigger another rerun.
            active = st.session_state.get("_crm_active_dialog") or {}
            same_dialog = (
                active.get("name") == entry["name"]
                and active.get("signature") == entry["signature"]
            )
            if same_dialog:
                # The active workspace already renders this exact dialog.
                # Legacy dispatchers can call wrappers again on every rerun;
                # never let that replay steal focus from another tab.
                return None

            client_id = _crm_workspace_client_id(func.__name__, args, kwargs)
            # If a legacy dispatcher repeats a dialog that is already open in any
            # workspace, do not let it steal focus from the tab the user selected.
            _entry_key = _crm_workspace_tab_key(entry)
            _already_open = any(
                _crm_workspace_tab_key(_tab) == _entry_key
                for _window in st.session_state.get("_crm_windows", [])
                for _tab in _window.get("tabs", [])
            )
            if _already_open and not inside_host:
                st.session_state["_crm_dialog_requested_this_run"] = True
                return None
            _crm_workspace_open_dialog(entry, client_id=client_id, from_host=inside_host)
            if inside_host:
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

def _render_task_shipping_fields(task, client, deal, key_prefix):
    """Поля отправки: изменение даты/статуса сохраняется по устойчивым ID записи."""
    statuses = ["Собирается", "Закупается материал", "Готово к отправке"]
    status_key = f"task_shipping_status_{key_prefix}"
    date_key = f"task_estimated_ship_date_{key_prefix}"

    task_number = str(task.get("task_number", ""))
    client_id = str((client or {}).get("id", task.get("client_id", "")) or "")
    deal_id = str((deal or {}).get("id", task.get("deal_id", "")) or "")
    task_type = str(task.get("type", "") or "")

    def _persist_shipping_fields():
        store = st.session_state.get("crm_store", {})
        found_client = next((x for x in store.get("clients", [])
                             if str(x.get("id", "")) == client_id), None)
        # Support the application's legacy client lookup/storage layout.
        if found_client is None:
            try:
                found_client = get_client_by_id(client_id)
            except Exception:
                found_client = None
        if not found_client:
            return
        found_task = next((x for x in found_client.get("tasks", [])
                           if str(x.get("task_number", "")) == task_number
                           and str(x.get("deal_id", "") or "") == deal_id
                           and str(x.get("type", "") or "") == task_type), None)
        if not found_task:
            return
        status_value = st.session_state.get(status_key, found_task.get("shipping_status", "")) or ""
        date_value = st.session_state.get(date_key)
        date_iso = date_value.isoformat() if date_value else ""
        found_task["shipping_status"] = status_value
        found_task["estimated_ship_date"] = date_iso
        found_task["last_modified"] = now_str()
        found_client["last_modified"] = now_str()
        if deal_id:
            found_deal = next((x for x in store.get("deals", [])
                               if str(x.get("id", "")) == deal_id), None)
            if found_deal:
                found_deal["last_modified"] = now_str()
        # Pass a copy so save_data does not replace the live store object while
        # the current dialog is rendering and leave its references stale.
        save_data(copy.deepcopy(store))

    current_status = task.get("shipping_status", "") or ""
    current_date_raw = task.get("estimated_ship_date", "") or ""
    try:
        current_date = datetime.strptime(str(current_date_raw)[:10], "%Y-%m-%d").date() if current_date_raw else None
    except (TypeError, ValueError):
        current_date = None

    if status_key not in st.session_state:
        st.session_state[status_key] = current_status
    if date_key not in st.session_state:
        st.session_state[date_key] = current_date

    st.selectbox(
        "Статус",
        options=statuses,
        index=statuses.index(current_status) if current_status in statuses else None,
        placeholder="Выберите статус",
        key=status_key,
        on_change=_persist_shipping_fields,
    )
    st.date_input(
        "Ориентировочная дата отправки",
        value=current_date,
        format="DD.MM.YYYY",
        key=date_key,
        on_change=_persist_shipping_fields,
    )


def render_soft_delete_comments(comments, key_prefix, time_key="time", author_key="user"):
    """Показывает комментарии; удаление только помечает запись и зачеркивает её."""
    if not isinstance(comments, list):
        return
    for _i, _item in enumerate(comments):
        if not isinstance(_item, dict):
            continue
        _meta = " · ".join(str(_item.get(k, "")) for k in (time_key, author_key) if _item.get(k))
        _text = linkify_text(str(_item.get("text", "") or ""))
        _deleted = bool(_item.get("deleted"))
        _content, _action = st.columns([12, 1])
        with _content:
            _shown = f"<s>{_text}</s>" if _deleted else _text
            st.markdown((f"- *{html.escape(_meta)}*: {_shown}" if _meta else f"- {_shown}"), unsafe_allow_html=True)
        with _action:
            if not _deleted and st.button("×", key=f"soft_comment_del_{key_prefix}_{_i}", help="Удалить комментарий"):
                st.session_state[f"soft_comment_confirm_{key_prefix}_{_i}"] = True
        _ck = f"soft_comment_confirm_{key_prefix}_{_i}"
        if st.session_state.get(_ck) and not _deleted:
            st.caption("Удалить комментарий? Он останется в истории зачёркнутым.")
            _yes, _no = st.columns(2)
            with _yes:
                if st.button("Подтвердить удаление", key=f"soft_comment_yes_{key_prefix}_{_i}", type="primary"):
                    _item["deleted"] = True
                    _item["deleted_at"] = now_str()
                    _item["deleted_by"] = st.session_state.get("user_name", st.session_state.get("user_login", ""))
                    st.session_state.pop(_ck, None)
                    commit_and_rerun(st.session_state.crm_store, "Комментарий зачёркнут")
            with _no:
                if st.button("Отмена", key=f"soft_comment_no_{key_prefix}_{_i}"):
                    st.session_state.pop(_ck, None)
                    st.rerun()

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
                        if _tp not in ("Отправить заказ", "Отправить образцы"):
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
                    st.markdown(format_created_date(t), unsafe_allow_html=True)
                    if not show_edit_task:
                        if _tp not in ("Отправить заказ", "Отправить образцы"):
                            st.markdown(f"**Тема:** {t.get('text', '')}")
                        st.markdown(f"**Тип:** {t.get('type', 'Связаться')}")
                with _status_inner:
                    if show_shipping_status and _tp in ("Отправить заказ", "Отправить образцы"):
                        _render_task_shipping_fields(t, cl, d, key_prefix)
                    elif not show_shipping_status:
                        render_print_button(t, cl, _tp, _fd, f"td_{key_prefix}")
            if show_edit_task:
                # Inline editing mode
                et_type = st.selectbox("\u0422\u0438\u043f:", TASK_TYPES, index=TASK_TYPES.index(t.get("type", "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f")) if t.get("type", "\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f") in TASK_TYPES else 0, key=f"edit_type_{key_prefix}")
                if et_type not in ("Отправить заказ", "Отправить образцы"):
                    et_topic = st.text_input("Тема:", value=t.get("text", ""), key=f"edit_topic_{key_prefix}")
                else:
                    et_topic = et_type
                et_mgr = st.selectbox("\u041e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439:", get_managers_list(), index=0 if t.get("manager", "") not in get_managers_list() else (get_managers_list()).index(t.get("manager", "")), key=f"edit_mgr_{key_prefix}", placeholder=MGR_PLACEHOLDER)
                if et_type in ("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u043a\u0430\u0437", "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437\u0446\u044b"):
                    _selected_calc_id_edit, et_products = render_task_products_editor(
                        d, f"edit_{key_prefix}", t.get("products", ""), t.get("calculation_id", "")
                    )
                    et_city = st.text_input("Город:", value=t.get("ship_city", ""), key=f"edit_city_{key_prefix}")
                    et_addr = st.text_area("\u0410\u0434\u0440\u0435\u0441 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438:", value=t.get("ship_addr", ""), key=f"edit_addr_{key_prefix}")
                    et_recv = st.text_input("\u041f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c:", value=t.get("receiver", ""), key=f"edit_recv_{key_prefix}")
                    et_rphone = st.text_input("\u0422\u0435\u043b\u0435\u0444\u043e\u043d \u043f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044f:", value=t.get("receiver_phone", ""), key=f"edit_rphone_{key_prefix}")
                    et_pay = st.selectbox("\u041e\u043f\u043b\u0430\u0442\u0430:", SHIP_PAY_OPTIONS, index=SHIP_PAY_OPTIONS.index(t.get("ship_pay", "")) if t.get("ship_pay", "") in SHIP_PAY_OPTIONS else 0, key=f"edit_pay_{key_prefix}", placeholder="\u0423\u043a\u0430\u0436\u0438 \u043f\u043b\u0430\u0442\u0435\u043b\u044c\u0449\u0438\u043a\u0430")
                    _selected_calc_edit = next((c for c in (d or {}).get("calculations", []) if str(c.get("id")) == str(_selected_calc_id_edit)), None)
                    _auto_amount_edit = _deal_items_total(_selected_calc_edit.get("items", [])) if _selected_calc_edit else 0
                    _amount_key_edit = f"edit_amount_{key_prefix}"
                    if _auto_amount_edit > 0:
                        st.session_state[_amount_key_edit] = f"{_auto_amount_edit:g}"
                    et_amount = st.text_input("Сумма заказа (руб.):", value=f"{_auto_amount_edit:g}" if _auto_amount_edit > 0 else (str(t.get("order_amount", 0)) if t.get("order_amount", 0) > 0 else ""), key=_amount_key_edit, placeholder="Сумма из расчёта без доставки", disabled=bool(_auto_amount_edit))
                    et_tk = st.text_input("Трек (подпиши если габариты не указаны):", value=t.get("tk_num", ""), key=f"edit_tk_{key_prefix}")
                    et_comment = st.text_area("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438:", value=t.get("task_comment", ""), key=f"edit_comment_{key_prefix}")
                else:
                    et_comment = st.text_area("\\u041a\\u043e\\u043c\\u043c\\u0435\\u043d\\u0442\\u0430\\u0440\\u0438\\u0438:", value=t.get("task_comment", ""), key=f"edit_comment_{key_prefix}")
                    et_products = t.get("products", "")
                    et_city = t.get("ship_city", "")
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
                            t["ship_city"] = et_city
                            t["ship_addr"] = et_addr
                            t["receiver"] = et_recv
                            t["receiver_phone"] = et_rphone
                            t["ship_pay"] = et_pay
                            t["order_amount"] = round(float(et_amount.replace(",", ".")), 2) if et_amount and et_amount.strip() else 0
                            if et_type in ("Отправить заказ", "Отправить образцы") and _selected_calc_id_edit:
                                t["calculation_id"] = str(_selected_calc_id_edit)
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
                if t.get('products'):
                    st.markdown("**Товары:**")
                    for _product_line in str(t.get("products", "")).splitlines():
                        if _product_line.strip():
                            st.markdown(f"- {html.escape(_product_line.strip())}", unsafe_allow_html=True)
                if t.get('type') in ("Отправить заказ", "Отправить образцы"):
                    st.markdown(f"**Город:** {t.get('ship_city', '')}")
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
                            save_data(st.session_state.crm_store)
                            st.toast("Задача взята в работу", icon="✅")
                            st.rerun()
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
                                nt_comment2 = st.text_input("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439:", key=f"cnt_comment_{key_prefix}")
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
                                            "products": "", "ship_city": "", "ship_addr": "", "receiver": "", "receiver_phone": "", "ship_pay": "", "tk_num": ""
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
                render_soft_delete_comments(t["task_comments"], f"task_{key_prefix}", "time", "user")
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
            st.markdown("**Добавить файлы в задачу:**")
            _tu_ver = st.session_state.get(f"task_upload_ver_{key_prefix}", 0)
            ntf_existing = st.file_uploader("Выберите файлы:", key=f"task_upload_{key_prefix}_{_tu_ver}", accept_multiple_files=True, label_visibility="collapsed")
            _task_file_upload_col, _task_file_pick_col = st.columns(2)
            with _task_file_upload_col:
                if st.button("Загрузить", key=f"task_upload_btn_{key_prefix}", use_container_width=True):
                    if ntf_existing:
                        with st.spinner("Загрузка файлов..."):
                            fi_list = save_uploaded_files(ntf_existing, (d["client_id"] if d else cl["id"]), "task_file")
                        if fi_list:
                            t.setdefault("task_files", []).extend(normalize_file_list(fi_list))
                            t["last_modified"] = now_str()
                            cl["last_modified"] = now_str()
                            if d: d["last_modified"] = now_str()
                            st.session_state[f"task_upload_ver_{key_prefix}"] = _tu_ver + 1
                            commit_and_rerun(st.session_state.crm_store, "Файлы добавлены")
                    else: st.warning("Выберите файл(ы)")
            with _task_file_pick_col:
                if st.button("Выбрать из загруженных", key=f"task_pick_existing_btn_{key_prefix}", use_container_width=True):
                    _pick_key = f"task_pick_existing_open_{key_prefix}"
                    st.session_state[_pick_key] = not st.session_state.get(_pick_key, False)
            if st.session_state.get(f"task_pick_existing_open_{key_prefix}", False):
                _source_task_files = (d or {}).get("deal_files", []) if d else cl.get("client_files", [])
                _source_task_files = [f for f in (_source_task_files or []) if isinstance(f, dict) and (f.get("file_path") or f.get("path"))]
                _task_file_options = {f"{i+1}. {f.get('file_name') or f.get('name') or os.path.basename(str(f.get('file_path') or f.get('path') or 'Файл'))} · {i}": f for i, f in enumerate(_source_task_files)}
                if _task_file_options:
                    _picked_task_file_keys = st.multiselect("Файлы из карточки клиента:" if not d else "Файлы из окна сделки:", list(_task_file_options), key=f"task_pick_existing_select_{key_prefix}")
                    if st.button("Прикрепить выбранные", key=f"task_pick_existing_apply_{key_prefix}", use_container_width=True, type="primary"):
                        _already_hashes = {str(f.get("file_hash", "") or f.get("file_path", "")) for f in t.get("task_files", []) if isinstance(f, dict)}
                        _added = []
                        for _picked_key in _picked_task_file_keys:
                            _picked_file = dict(_task_file_options[_picked_key])
                            _identity = str(_picked_file.get("file_hash", "") or _picked_file.get("file_path", "") or _picked_file.get("path", ""))
                            if _identity and _identity not in _already_hashes:
                                if not _picked_file.get("file_path") and _picked_file.get("path"):
                                    _picked_file["file_path"] = _picked_file["path"]
                                if not _picked_file.get("file_name") and _picked_file.get("name"):
                                    _picked_file["file_name"] = _picked_file["name"]
                                _added.append(_picked_file)
                                _already_hashes.add(_identity)
                        if _added:
                            t.setdefault("task_files", []).extend(_added)
                            t["last_modified"] = now_str()
                            cl["last_modified"] = now_str()
                            if d: d["last_modified"] = now_str()
                            st.session_state[f"task_pick_existing_open_{key_prefix}"] = False
                            commit_and_rerun(st.session_state.crm_store, "Файлы прикреплены к задаче")
                        else:
                            st.info("Выберите файлы, которые ещё не прикреплены к задаче.")
                else:
                    st.caption("В карточке клиента/сделке пока нет загруженных файлов.")

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
    if "ship_city" not in t: t["ship_city"] = ""
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
# Характеристики товаров перенесены из актуального файла «Прайс.xlsx».
PRODUCT_CHARACTERISTICS_BY_SKU = {
    'APLNT1003': 'Магнитный профиль в комплекте со вставкой под покраску',
    'APLNT1007': 'Магнитный профиль в комплекте с основой для керамогранита',
    'APLNT1001': 'Профиль с нижним основанием для ламината/шпона собственного производства',
    'APLNT1002': 'Профиль с укороченным нижним основанием под любые вставки',
    'APLNT1050': 'Ультратонкий алюминиевый, высота 40 мм, видимая толщина всего 1 мм',
    'APLNT1051': 'Ультратонкий алюминиевый, высота 60 мм, видимая толщина всего 1 мм',
    'APLNT1052': 'С нишей для светодиодной подсветки, высота 40 мм, толщина 1 мм',
    'APLNT1053': 'С нишей для светодиодной подсветки, высота 60 мм, толщина 1 мм',
    'APLNT1004': 'Высокая плотность, толщина 11 мм, высота 64 мм. Готова под финишную покраску стены',
    'APLNT1006': 'Эксклюзивный декор из гибкого камня на заказ, длина до 3.2 м',
    'APLNT1005': 'Гибкий радиусный профиль со вставкой под покраску на заказ',
    'APLNT1007-R': 'Радиусный профиль для криволинейных стен на заказ',
    'APLNT1010-1': 'COB лента без точек, 24V, цвет 3000К (тёплый белый), ширина 5 мм',
    'APLNT1010-2': 'COB лента без точек, 24V, цвет 4000К (нейтральный белый), ширина 5 мм',
    'APLNT1010-3': 'COB лента без точек, 24V, цвет 6500К (холодный белый), ширина 5 мм',
    'APLNT1020-1': 'С регулировкой яркости и плавным пуском',
    'APLNT1020-2': 'С регулировкой яркости и плавным пуском',
    'APLNT1020-3': 'С регулировкой яркости и плавным пуском',
    'APLNT1030': 'Встроенный датчик освещенности, дальность 6 м, 220V',
    'APLNT1060': 'Для идеальной подготовки основания, глубина 17 мм, высота 80 мм',
}

# Заполняем характеристики в каталоге по артикулу; остальные поля и цены не меняем.
for _default_product in DEFAULT_PRODUCT_CATALOG:
    _default_sku = str(_default_product.get("sku", "") or "").strip()
    _default_id = str(_default_product.get("id", "") or "").strip()
    _default_spec = PRODUCT_CHARACTERISTICS_BY_SKU.get(_default_id) or PRODUCT_CHARACTERISTICS_BY_SKU.get(_default_sku)
    if _default_spec:
        _default_product["characteristics"] = _default_spec

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
    """Локальный JSON-загрузчик для первичной миграции/аварийного fallback. Яндекс Диск не читается."""
    # Никогда не подменяем ошибку чтения пустой базой с одним admin.
    # При отсутствии/повреждении JSON останавливаем инициализацию, чтобы не
    # записать этот fallback в SQLite и не отправить его в резервные копии.
    if not os.path.exists(FILE_NAME):
        raise FileNotFoundError(f"Файл базы данных {FILE_NAME!r} не найден; пустая база автоматически не создаётся")
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Корень JSON должен быть объектом")
        for required_key in ("clients", "deals", "users"):
            if required_key not in data or not isinstance(data.get(required_key), list):
                raise ValueError(f"В JSON отсутствует корректный список '{required_key}'")
        if not data["users"]:
            raise ValueError("В JSON нет пользователей")
        if (not data["clients"] and not data["deals"] and len(data["users"]) == 1
                and isinstance(data["users"][0], dict)
                and data["users"][0].get("login") == "admin"):
            raise ValueError("Обнаружена подозрительная пустая база: только admin, без клиентов и сделок")
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
                    if "ship_city" not in t: t["ship_city"] = ""
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
    except Exception as exc:
        raise RuntimeError(f"Не удалось безопасно прочитать/подготовить JSON-базу {FILE_NAME!r}: {exc}") from exc
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

def _load_valid_yandex_backup_for_initialization():
    """Ищет валидную резервную копию на Диске только для первичной инициализации пустой SQLite.

    Ничего не скачивает поверх существующей базы: функция вызывается только когда
    таблица crm_state ещё не содержит данных. Подозрительные/повреждённые копии
    пропускаются, а не используются для восстановления.
    """
    if not YANDEX_TOKEN:
        return None
    try:
        listing = requests.get(
            YANDEX_API_URL,
            params={"path": "disk:/CRM_NE_TROGAT/backups", "limit": 100},
            headers=yandex_headers(), timeout=15)
        if listing.status_code != 200:
            return None
        items = listing.json().get("_embedded", {}).get("items", [])
        candidates = [x for x in items if isinstance(x, dict)
                      and str(x.get("name", "")).lower().endswith(".json")
                      and x.get("path")]
        # Сначала проверяем CRM_latest, затем остальные по дате изменения.
        candidates.sort(key=lambda x: (x.get("name") != "CRM_latest.json", x.get("modified", "")), reverse=False)
        if candidates and candidates[0].get("name") == "CRM_latest.json":
            latest = candidates.pop(0)
            candidates.sort(key=lambda x: x.get("modified", ""), reverse=True)
            candidates.insert(0, latest)
        else:
            candidates.sort(key=lambda x: x.get("modified", ""), reverse=True)
        for item in candidates:
            try:
                response = requests.get(
                    f"{YANDEX_API_URL}/download",
                    params={"path": item["path"]},
                    headers=yandex_headers(), timeout=15)
                if response.status_code != 200:
                    continue
                href = response.json().get("href")
                if not href:
                    continue
                downloaded = requests.get(href, timeout=30)
                if downloaded.status_code != 200:
                    continue
                raw = downloaded.content.decode("utf-8-sig")
                data = _validate_backup_snapshot(raw)
                # Приводим к текущей схеме в памяти; оригинал на Диске не меняется.
                if data.get("_migrated") != "v2":
                    data = migrate_data(data)
                else:
                    data.setdefault("internal_tasks", [])
                    data.setdefault("chat_messages", [])
                    data.setdefault("qa_entries", [])
                    data.setdefault("suppliers", [])
                    data.setdefault("notifications", [])
                    data.setdefault("products", copy.deepcopy(DEFAULT_PRODUCT_CATALOG))
                return data
            except Exception:
                # Проверяем следующую копию; никогда не принимаем сомнительный файл.
                continue
    except Exception:
        return None
    return None


def _ensure_sqlite_store():
    """Создаёт SQLite из локального JSON или валидной резервной копии при первой инициализации."""
    with _sqlite_init_lock:
        conn = _sqlite_connect()
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS crm_state (id INTEGER PRIMARY KEY CHECK (id = 1), data TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL)")
            row = conn.execute("SELECT data FROM crm_state WHERE id = 1").fetchone()
            if row is None:
                # Сначала используем локальный JSON, если он есть. Если его нет,
                # пытаемся восстановиться только из проверенной резервной копии.
                # Существующая запись SQLite выше имеет приоритет и не затрагивается.
                if os.path.exists(FILE_NAME):
                    initial_data = _load_data_from_json()
                else:
                    initial_data = _load_valid_yandex_backup_for_initialization()
                    if initial_data is None:
                        # Сохраняем понятную ошибку и не создаём пустую базу.
                        _load_data_from_json()
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
                # Не выдаём повреждённое/аварийно пустое содержимое SQLite за рабочую базу.
                _validate_backup_snapshot(row[0])
                _remember_session_base(data, row[1])
                if not st.session_state.get("_crm_load_logged_this_session"):
                    _crm_log("DATABASE_LOAD_OK", {"source": "SQLite", "revision": row[1], "clients": len(data.get("clients", [])), "deals": len(data.get("deals", []))})
                    st.session_state["_crm_load_logged_this_session"] = True
                return data
        finally:
            conn.close()
    except Exception as exc:
        _crm_log("DATABASE_LOAD_ERROR", {"stage": "SQLite/JSON fallback"}, exc=exc)
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

_save_lock = _CRM_BG_STATE["save_lock"]

# JSON-файл — переносимое зеркало SQLite, а не основная база. Его запись и fsync
# не должны блокировать обработку нажатия кнопки в основном потоке Streamlit.
# Очередь хранит только последний снимок, чтобы быстрые последовательные сохранения
# не создавали длинную очередь файловых операций.
# Состояние очереди JSON-зеркала находится в общем ресурсе Streamlit.

def _write_json_mirror(snapshot):
    tmp_name = FILE_NAME + ".tmp"
    with open(tmp_name, "w", encoding="utf-8") as f:
        f.write(snapshot)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_name, FILE_NAME)

def _json_mirror_worker():
    state = _CRM_BG_STATE
    while True:
        with state["json_lock"]:
            snapshot = state["json_pending_snapshot"]
            state["json_pending_snapshot"] = None
            if snapshot is None:
                state["json_worker_running"] = False
                return
        try:
            _write_json_mirror(snapshot)
        except Exception as exc:
            # Ошибка зеркала не отменяет подтверждённую транзакцию SQLite.
            print(f"CRM JSON mirror write failed: {type(exc).__name__}: {str(exc)[:300]}")

def _queue_json_mirror(snapshot):
    state = _CRM_BG_STATE
    with state["json_lock"]:
        state["json_pending_snapshot"] = snapshot
        if not state["json_worker_running"]:
            state["json_worker_running"] = True
            state["json_executor"].submit(_json_mirror_worker)

def _download_disk_data():
    """Чтение JSON-базы с Яндекс Диска отключено: резервные копии только записываются."""
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

            # JSON — только переносимое зеркало; запись большого файла и fsync
            # выполняются в фоне. SQLite уже содержит подтверждённую транзакцию.
            _queue_json_mirror(snapshot)

            if conflicts:
                try:
                    st.warning("Обнаружены параллельные изменения. Чтобы не потерять данные коллег, конфликтующие поля оставлены в последней сохранённой версии. Проверьте запись и при необходимости внесите изменение повторно.")
                except Exception:
                    pass
        except Exception as e:
            _crm_log("DATABASE_SAVE_ERROR", {"stage": "SQLite transaction"}, exc=e)
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
# Журналируем запуск и текущую доступность базы, затем ставим резервное копирование в очередь.
if not _CRM_BG_STATE["process_start_logged"]:
    _crm_log("APP_START", {"database": "SQLite", "restore_from_yandex_enabled": True})
    _CRM_BG_STATE["process_start_logged"] = True
# При запуске приложения создаём резервную копию текущей SQLite, не читая данные с Яндекс Диска.
_queue_startup_backup_once()
# Каталог товаров добавляется совместимо с уже работающей базой.
if "products" not in st.session_state.crm_store:
    st.session_state.crm_store["products"] = copy.deepcopy(DEFAULT_PRODUCT_CATALOG)
    save_data(st.session_state.crm_store)

# Автоматически заполняем пустые характеристики в существующем каталоге.
# Значения взяты из актуального «Прайс.xlsx»; цены и прочие поля не меняются.
_products_specs_changed = False
for _product_row in st.session_state.crm_store.get("products", []):
    _product_id = str(_product_row.get("id", "") or "").strip()
    _product_sku = str(_product_row.get("sku", "") or "").strip()
    _product_spec = PRODUCT_CHARACTERISTICS_BY_SKU.get(_product_id) or PRODUCT_CHARACTERISTICS_BY_SKU.get(_product_sku)
    if _product_spec and not str(_product_row.get("characteristics", "") or "").strip():
        _product_row["characteristics"] = _product_spec
        _products_specs_changed = True
if _products_specs_changed:
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
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    session_record = {
        "token_hash": token_hash,
        "created_at": now_str(),
        "expires_at": (moscow_now() + timedelta(hours=12)).isoformat(timespec="seconds"),
    }
    sessions.append(session_record)
    user.pop("auth_token", None)
    user["auth_sessions"] = sessions[-30:]
    save_data(st.session_state.crm_store)

    # save_data() refreshes crm_store with a deep-copied merged snapshot. Rebind the
    # user and verify that the new token hash survived the merge before issuing the cookie.
    login_key = str(user.get("login", ""))
    user = next((u for u in st.session_state.crm_store.get("users", [])
                 if str(u.get("login", "")) == login_key), None)
    if user is None:
        raise RuntimeError("Не удалось сохранить пользователя для новой сессии")
    saved_sessions = user.get("auth_sessions", [])
    token_is_saved = any(
        isinstance(item, dict) and secrets.compare_digest(str(item.get("token_hash", "")), token_hash)
        for item in saved_sessions
    )
    if not token_is_saved:
        if not isinstance(saved_sessions, list):
            saved_sessions = []
        saved_sessions.append(session_record)
        user["auth_sessions"] = saved_sessions[-30:]
        user.pop("auth_token", None)
        save_data(st.session_state.crm_store)
        user = next((u for u in st.session_state.crm_store.get("users", [])
                     if str(u.get("login", "")) == login_key), None)
        if user is None or not any(
            isinstance(item, dict) and secrets.compare_digest(str(item.get("token_hash", "")), token_hash)
            for item in user.get("auth_sessions", [])
        ):
            raise RuntimeError("Токен сессии не сохранился в базе CRM")

    st.session_state.authenticated = True
    st.session_state.user_role = user.get("role")
    st.session_state.user_login = user.get("login")
    st.session_state.user_name = user.get("name", user.get("login", ""))
    st.session_state.remember_login = bool(remember)
    st.session_state._auth_token_current = token
    st.session_state._auth_last_activity = moscow_now()
    try:
        _activity_now_ms = str(int(time.time() * 1000))
        # CookieManager will write these values on the current browser response.
        cookie_manager.set("crm_last_activity", _activity_now_ms,
                           expires_at=moscow_now().replace(microsecond=0) + timedelta(days=3650),
                           key="set_crm_last_activity_cookie")
        cookie_manager.delete("crm_session_expired")
    except Exception:
        pass
    # One signed-by-randomness bearer cookie; server-side record limits it to 60 minutes
    # of inactivity. The browser cookie can persist, but an expired server session cannot.
    if remember:
        cookie_manager.set(
            "auth_token", token,
            expires_at=moscow_now().replace(microsecond=0) + timedelta(days=3650),
            key="set_auth_token_cookie",
        )
    else:
        # Session cookie: keep this login only for the current browser session.
        cookie_manager.set("auth_token", token, key="set_auth_token_cookie")
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

    # CookieManager updates can be lost when the caller immediately triggers st.rerun().
    # Write the bearer/session cookies synchronously in the browser, then reload only after
    # the browser confirms the writes have been issued. This also makes the PIN screen
    # survive a hard page refresh instead of falling back to username/password.
    try:
        _cookie_token_js = json.dumps(token)
        _cookie_login_js = json.dumps(str(user.get("login", "")))
        _cookie_remember_js = "true" if remember else "false"
        components.html(f"""
        <script>
        (() => {{
          const status = document.getElementById('auth-cookie-write-status');
          try {{
            const win = window.parent;
            const doc = win.document;
            const secure = win.location.protocol === 'https:' ? '; Secure' : '';
            const base = '; path=/; SameSite=Lax' + secure;
            const token = {_cookie_token_js};
            const login = {_cookie_login_js};
            const remember = {_cookie_remember_js};
            const readCookie = (name) => {{
              const prefix = name + '=';
              const item = doc.cookie.split('; ').find(v => v.startsWith(prefix));
              return item ? decodeURIComponent(item.slice(prefix.length)) : '';
            }};
            const persistence = remember ? '; max-age=315360000' : '';
            doc.cookie = 'auth_token=' + encodeURIComponent(token) + base + persistence;
            doc.cookie = 'crm_last_activity=' + encodeURIComponent(String(Date.now())) + base + persistence;
            doc.cookie = 'crm_session_expired=' + base + '; max-age=0';
            if (remember) {{
              doc.cookie = 'remembered_user=' + encodeURIComponent(login) + base + '; max-age=315360000';
            }} else {{
              doc.cookie = 'remembered_user=' + base + '; max-age=0';
            }}
            // Never reload just because cookie assignment did not throw: browsers can silently
            // reject a cookie. Confirm that the exact session token is readable first.
            const deadline = Date.now() + 2500;
            const confirmAndReload = () => {{
              const tokenSaved = readCookie('auth_token') === token;
              const loginSaved = !remember || readCookie('remembered_user') === login;
              if (tokenSaved && loginSaved) {{
                if (status) status.textContent = 'Сессия сохранена. Выполняется вход…';
                win.setTimeout(() => win.location.reload(), 150);
              }} else if (Date.now() < deadline) {{
                win.setTimeout(confirmAndReload, 100);
              }} else {{
                if (status) status.textContent = 'Браузер не сохранил токен авторизации. Разрешите cookies для этого сайта и повторите вход. PIN-код сохранён.';
              }}
            }};
            confirmAndReload();
          }} catch (e) {{
            if (status) status.textContent = 'Не удалось сохранить сессию в браузере. Разрешите cookies для этого сайта и повторите вход.';
          }}
        }})();
        </script>
        <div id="auth-cookie-write-status" style="font-size:12px;color:#b42318;padding:6px 0"></div>
        """, height=42, width=500)
        # Stop this run so the browser-side cookie write/reload, not an immediate Python
        # rerun, completes the login transition.
        st.stop()
    except Exception:
        # Keep the regular Streamlit cookie manager as a fallback on unusual deployments.
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
        "expires_at": (moscow_now() + timedelta(hours=12)).isoformat(timespec="seconds"),
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

# Отслеживаем реальную активность в браузере без периодических Streamlit-rerun.
# События записывают timestamp в cookie; обновление страницы само по себе активностью не считается.
st.components.v1.html("""
<script>
(() => {
  try {
    const doc = window.parent.document;
    const readCookie = (name) => {
      const prefix = name + '=';
      const item = doc.cookie.split('; ').find(v => v.startsWith(prefix));
      return item ? decodeURIComponent(item.slice(prefix.length)) : '';
    };
    const writeCookie = (name, value) => {
      doc.cookie = name + '=' + encodeURIComponent(value) + '; path=/; SameSite=Lax' + (window.parent.location.protocol === 'https:' ? '; Secure' : '');
    };
    const now = Date.now();
    const previous = Number(readCookie('crm_last_activity'));
    // Если предыдущая активность уже старше 12 часов, не продлеваем сессию одним поздним кликом.
    if (previous && now - previous >= 12 * 60 * 60 * 1000) {
      writeCookie('crm_session_expired', '1');
    }
    if (!window.parent.__crmActivityTrackerInstalled) {
      window.parent.__crmActivityTrackerInstalled = true;
      const win = window.parent;
      const IDLE_LIMIT = 12 * 60 * 60 * 1000;
      let lastWrite = 0;
      let idleTimer = null;
      const expireAndReload = () => {
        writeCookie('crm_session_expired', '1');
        // Clear the activity timestamp to prevent repeated reloads on the login screen.
        writeCookie('crm_last_activity', '');
        // Trigger a Streamlit page load so server-side auth state is cleared and
        // the authorization screen is rendered even when the user does nothing.
        win.location.reload();
      };
      const scheduleIdleLogout = () => {
        if (idleTimer !== null) win.clearTimeout(idleTimer);
        const last = Number(readCookie('crm_last_activity')) || Date.now();
        const remaining = Math.max(0, IDLE_LIMIT - (Date.now() - last));
        idleTimer = win.setTimeout(() => {
          const latest = Number(readCookie('crm_last_activity')) || last;
          if (Date.now() - latest >= IDLE_LIMIT) {
            expireAndReload();
          } else {
            scheduleIdleLogout();
          }
        }, remaining + 50);
      };
      const markActivity = () => {
        const current = Date.now();
        const old = Number(readCookie('crm_last_activity'));
        if (old && current - old >= IDLE_LIMIT) {
          expireAndReload();
          return;
        }
        writeCookie('crm_session_expired', '');
        // Update activity cookie and reset the browser-side idle timer.
        if (current - lastWrite >= 1000 || !old) {
          writeCookie('crm_last_activity', String(current));
          lastWrite = current;
        }
        scheduleIdleLogout();
      };
      // If the tab was already idle for an hour before this page script ran,
      // expire immediately rather than treating the page load as activity.
      const initialActivity = Number(readCookie('crm_last_activity'));
      if (initialActivity && Date.now() - initialActivity >= IDLE_LIMIT) {
        expireAndReload();
        return;
      }
      scheduleIdleLogout();
      ['pointerdown', 'keydown', 'touchstart', 'scroll', 'click', 'input', 'wheel'].forEach(
        eventName => doc.addEventListener(eventName, markActivity, {passive: true, capture: true})
      );
      win.addEventListener('pageshow', scheduleIdleLogout);
      win.addEventListener('focus', scheduleIdleLogout);
    }
  } catch (_) {}
})();
</script>
""", height=0, width=0)

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
            # Expiry is evaluated against the last real browser activity below.
            # Do not reject the token here solely because its stored expiry is old:
            # an active browser may have written a newer activity cookie before rerun.
            if saved_hash and secrets.compare_digest(str(saved_hash), token_hash):
                return True
        else:
            saved_token = auth_session
        if saved_token and secrets.compare_digest(str(saved_token), str(token)):
            return True
    return False

_auth_token = cookies.get("auth_token")
_remembered_login = str(cookies.get("remembered_user") or "").strip()
_client_activity_raw = cookies.get("crm_last_activity")
_client_expired = str(cookies.get("crm_session_expired") or "").strip() == "1"
_client_activity = None
try:
    # Browser timestamp is milliseconds since epoch; reject malformed/future values.
    _activity_ms = int(str(_client_activity_raw or "0"))
    if _activity_ms > 0:
        _candidate_activity = datetime.fromtimestamp(_activity_ms / 1000, tz=moscow_now().tzinfo)
        if _candidate_activity <= moscow_now() + timedelta(seconds=30):
            _client_activity = _candidate_activity
except (TypeError, ValueError, OverflowError, OSError):
    _client_activity = None

if st.session_state.get("_force_password_login"):
    _remembered_login = ""

# Возвращает серверное время окончания сессии, если токен найден в auth_sessions.
def _auth_token_expiry(user, token):
    if not token:
        return None
    token_hash = hashlib.sha256(str(token).encode("utf-8")).hexdigest()
    for _session in user.get("auth_sessions", []):
        if not isinstance(_session, dict):
            continue
        _saved_hash = str(_session.get("token_hash", ""))
        if _saved_hash and secrets.compare_digest(_saved_hash, token_hash):
            try:
                _expiry = datetime.fromisoformat(str(_session.get("expires_at", "")))
                if _expiry.tzinfo is None:
                    _expiry = _expiry.replace(tzinfo=moscow_now().tzinfo)
                return _expiry
            except (TypeError, ValueError):
                return None
    return None

# Восстанавливаем сессию после refresh только по действующему токену.
# Время последней активности берём из браузера/серверного срока, а не из времени перезагрузки.
if _auth_token and not st.session_state.get("authenticated") and not st.session_state.get("_force_password_login") and not _client_expired:
    for _cookie_user in st.session_state.crm_store.get("users", []):
        if _user_has_auth_token(_cookie_user, _auth_token):
            _stored_expiry = _auth_token_expiry(_cookie_user, _auth_token)
            if _stored_expiry is not None:
                _server_last_activity = _stored_expiry - timedelta(hours=12)
            else:
                # Legacy tokens without expiry are migrated to the current inactivity policy.
                _server_last_activity = _client_activity or moscow_now()
            _restored_last_activity = max(
                [_server_last_activity] + ([_client_activity] if _client_activity else [])
            )
            if moscow_now() - _restored_last_activity >= timedelta(hours=12):
                st.session_state["_auth_expired"] = True
                break
            st.session_state.authenticated = True
            st.session_state.user_role = _cookie_user.get("role")
            st.session_state.user_login = _cookie_user.get("login")
            st.session_state.user_name = _cookie_user.get("name", _cookie_user.get("login", ""))
            st.session_state.remember_login = True
            st.session_state._auth_token_current = _auth_token
            st.session_state._auth_last_activity = _restored_last_activity
            break

# Sliding expiry обновляется только при новой активности в браузере или по серверному времени.
if st.session_state.get("authenticated"):
    _last_activity = st.session_state.get("_auth_last_activity")
    if not isinstance(_last_activity, datetime):
        _last_activity = _client_activity or moscow_now()
    if _client_expired or moscow_now() - _last_activity >= timedelta(hours=12):
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_login = None
        st.session_state.user_name = None
        st.session_state.pop("_auth_last_activity", None)
        st.session_state.pop("_auth_token_current", None)
        st.session_state["_auth_expired"] = True
        try:
            cookie_manager.delete("auth_token")
        except Exception:
            pass
    else:
        # Только timestamp активности, который новее сохранённого, двигает idle-таймер.
        if _client_activity and _client_activity > _last_activity:
            _previous_last_activity = _last_activity
            _last_activity = _client_activity
            st.session_state._auth_last_activity = _last_activity
            # Persist the sliding expiry at most once per minute, not on every keystroke/rerun.
            if _auth_token and (_last_activity - _previous_last_activity) >= timedelta(seconds=60):
                _token_hash = hashlib.sha256(str(_auth_token).encode("utf-8")).hexdigest()
                _expiry_changed = False
                for _active_user in st.session_state.crm_store.get("users", []):
                    for _active_session in _active_user.get("auth_sessions", []):
                        if isinstance(_active_session, dict) and secrets.compare_digest(str(_active_session.get("token_hash", "")), _token_hash):
                            _active_session["expires_at"] = (_last_activity + timedelta(hours=12)).isoformat(timespec="seconds")
                            _expiry_changed = True
                if _expiry_changed:
                    save_data(st.session_state.crm_store)

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



# Не удаляем auth_token просто потому, что CookieManager вернул пустой снимок
# во время первичной загрузки: это могло бы уничтожить действующую сессию при refresh.

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
        st.info("Сессия завершена после 12 часов бездействия. Войдите снова.")
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
                st.components.v1.html("""<script>
                (function(){
                  function tunePin(){
                    try {
                      const doc = window.parent.document;
                      doc.querySelectorAll('input[placeholder="Введите PIN-код"]').forEach(function(el){
                        el.setAttribute('inputmode','numeric');
                        el.setAttribute('pattern','[0-9]*');
                        el.setAttribute('enterkeyhint','go');
                        el.setAttribute('autocomplete','new-password');
                        el.setAttribute('autocorrect','off');
                        el.setAttribute('autocapitalize','off');
                        el.setAttribute('name','crm_pin_' + Math.random().toString(36).slice(2));
                        el.setAttribute('data-lpignore','true');
                        el.setAttribute('data-1p-ignore','true');
                        el.setAttribute('data-bwignore','true');
                        el.setAttribute('data-form-type','other');
                        el.setAttribute('data-autofill','off');
                        el.setAttribute('spellcheck','false');
                        // Do not use readonly: it can prevent Streamlit inputs from accepting keystrokes.
                        if (!el.dataset.crmPinEnterBound) {
                          el.dataset.crmPinEnterBound = '1';
                          el.addEventListener('keydown', function(ev){
                            if (ev.key === 'Enter' && !ev.isComposing) {
                              ev.preventDefault();
                              const btn = doc.querySelector('.st-key-remembered_pin_login_btn button');
                              if (btn && !btn.disabled) btn.click();
                            }
                          });
                        }
                      });
                    } catch(e) {}
                  }
                  function focusPin(){
                    try {
                      const doc = window.parent.document;
                      const el = doc.querySelector('input[placeholder="Введите PIN-код"]');
                      if (el && doc.activeElement !== el) el.focus({preventScroll:true});
                    } catch(e) {}
                  }
                  tunePin();
                  // Autofocus when the PIN screen first appears; retries allow Streamlit to finish rendering.
                  setTimeout(focusPin, 100);
                  setTimeout(focusPin, 350);
                  try {
                    const root = window.parent.document.querySelector('[data-testid="stAppViewContainer"]') || window.parent.document.body;
                    if (root && !root.__pinInputModeObserver) {
                      root.__pinInputModeObserver = new MutationObserver(function(){
                        tunePin();
                      });
                      root.__pinInputModeObserver.observe(root, {childList:true, subtree:true});
                    }
                  } catch(e) {}
                })();
                </script>""", height=0)
                _pin_submit = st.button(
                    "Войти по PIN-коду", use_container_width=True, type="primary",
                    key="remembered_pin_login_btn",
                )
                if _pin_submit:
                    if re.fullmatch(r"\d{4,8}", _pin_input or "") and _pin_verify(_remembered_user, _pin_input):
                        _create_browser_session(_remembered_user, remember=True)
                        st.toast("PIN подтверждён. Выполняется вход…", icon="🔓")
                    else:
                        st.error("Неверный PIN-код. Проверьте, что введены 4–8 цифр.")
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
                st.caption("Сессия действует до 12 часов бездействия. При активности CRM продлевает сессию автоматически.")
                _new_pin = st.text_input("Создайте PIN-код (4–8 цифр):", type="default", max_chars=8, key="new_login_pin", placeholder="Придумайте PIN-код")
                _confirm_pin = st.text_input("Повторите PIN-код:", type="default", max_chars=8, key="confirm_login_pin", placeholder="Повторите PIN-код")
                st.markdown("""<style>
                .st-key-new_login_pin input,
                .st-key-confirm_login_pin input {
                    -webkit-text-security: disc !important;
                    text-security: disc !important;
                }
                </style>""", unsafe_allow_html=True)
                st.components.v1.html("""<script>
                (function(){
                  const tunePinFields = () => {
                    try {
                      const doc = window.parent.document;
                      const rules = [
                        ['.st-key-new_login_pin input', 'create'],
                        ['.st-key-confirm_login_pin input', 'confirm']
                      ];
                      rules.forEach(([selector, fieldName]) => {
                        doc.querySelectorAll(selector).forEach((el) => {
                          el.setAttribute('autocomplete', 'new-password');
                          el.setAttribute('autocorrect', 'off');
                          el.setAttribute('autocapitalize', 'off');
                          el.setAttribute('spellcheck', 'false');
                          el.setAttribute('name', 'crm_pin_' + fieldName + '_' + Math.random().toString(36).slice(2));
                          el.setAttribute('data-lpignore', 'true');
                          el.setAttribute('data-1p-ignore', 'true');
                          el.setAttribute('data-bwignore', 'true');
                          el.setAttribute('data-form-type', 'other');
                          el.setAttribute('data-autofill', 'off');
                          el.setAttribute('inputmode', 'numeric');
                          el.setAttribute('pattern', '[0-9]*');
                          // Keep the input editable; readonly interferes with Streamlit rerenders.
                        });
                      });
                    } catch(e) {}
                  };
                  tunePinFields();
                  try {
                    const root = window.parent.document.querySelector('[data-testid="stAppViewContainer"]') || window.parent.document.body;
                    if (root && !root.__crmPinFieldsObserver) {
                      root.__crmPinFieldsObserver = new MutationObserver(tunePinFields);
                      root.__crmPinFieldsObserver.observe(root, {childList:true, subtree:true});
                    }
                  } catch(e) {}
                })();
                </script>""", height=0)
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
        font-size: 2.8rem !important;
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
        font-size: 2.8rem !important;
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
        font-size: 2.8rem !important;
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
    if not YANDEX_TOKEN:
        st.error("Резервное копирование отключено: не задан YANDEX_DISK_TOKEN в Secrets")
    elif _CRM_BG_STATE["cloud_last_ok"] is True:
        st.success(f"Резервная копия загружена: {_CRM_BG_STATE['cloud_last_backup_name'] or 'последняя загрузка подтверждена'}")
    elif _CRM_BG_STATE["cloud_last_ok"] is False:
        st.error(f"Резервная копия НЕ загружена: {_CRM_BG_STATE['cloud_last_error'] or 'ошибка загрузки'}")
    else:
        st.caption("Резервное копирование: ожидается подтверждение первой загрузки")
    if st.session_state.get("user_role") == "admin":
        with st.expander("Ручное восстановление из резервной копии"):
            st.warning("Используйте только после сбоя основной базы. Восстановление заменит текущие данные CRM.")
            _restore_file = st.file_uploader("Загрузите скачанный с Яндекс Диска JSON-файл", type=["json"], key="crm_manual_restore_json")
            _restore_confirm = st.checkbox("Подтверждаю замену текущей базы данными из выбранной копии", key="crm_manual_restore_confirm")
            if st.button("Восстановить базу из файла", key="crm_manual_restore_button", disabled=not (_restore_file and _restore_confirm), use_container_width=True):
                try:
                    _restore_text = _restore_file.getvalue().decode("utf-8-sig")
                    _restore_data = _sanitize_backup_data(_validate_backup_snapshot(_restore_text))
                    _ensure_sqlite_store()
                    # Сначала снимаем текущее состояние ИЗ ОСНОВНОЙ SQLite-базы,
                    # а не из JSON-зеркала, которое может отставать. Если копию
                    # нельзя надёжно сохранить на Яндекс Диск — восстановление не начинаем.
                    _safety_conn = _sqlite_connect()
                    try:
                        _safety_row = _safety_conn.execute("SELECT data FROM crm_state WHERE id = 1").fetchone()
                        if not _safety_row or not _safety_row[0]:
                            raise RuntimeError("Текущая база пуста или не читается; восстановление остановлено")
                        _safety_data = json.loads(_safety_row[0])
                        _safety_text = json.dumps(_safety_data, ensure_ascii=False, separators=(",", ":"))
                        _validate_backup_snapshot(_safety_text)
                    finally:
                        _safety_conn.close()
                    _safety_backup_name = _upload_yandex_pre_restore_snapshot(_safety_text)

                    _restore_conn = _sqlite_connect()
                    try:
                        _restore_conn.execute("BEGIN IMMEDIATE")
                        _restore_row = _restore_conn.execute("SELECT revision FROM crm_state WHERE id = 1").fetchone()
                        _restore_revision = int(_restore_row[0] if _restore_row else 0) + 1
                        _restore_compact = json.dumps(_restore_data, ensure_ascii=False, separators=(",", ":"))
                        _restore_conn.execute("INSERT INTO crm_state (id, data, revision, updated_at) VALUES (1, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET data=excluded.data, revision=excluded.revision, updated_at=excluded.updated_at", (_restore_compact, _restore_revision, now_str()))
                        _restore_conn.execute("COMMIT")
                    except Exception:
                        _restore_conn.execute("ROLLBACK")
                        raise
                    finally:
                        _restore_conn.close()
                    _restore_tmp = FILE_NAME + ".tmp"
                    with open(_restore_tmp, "w", encoding="utf-8") as _restore_f:
                        _restore_f.write(_restore_compact)
                        _restore_f.flush()
                        os.fsync(_restore_f.fileno())
                    os.replace(_restore_tmp, FILE_NAME)
                    st.session_state["crm_store"] = copy.deepcopy(_restore_data)
                    _remember_session_base(_restore_data, _restore_revision)
                    st.success(f"База восстановлена из выбранной копии. Перед заменой сохранена текущая база: {_safety_backup_name}. Страница будет перезагружена.")
                    st.rerun()
                except Exception as _restore_exc:
                    st.error(f"Не удалось восстановить базу: {str(_restore_exc)[:300]}")
                    st.info("Если не удалось создать предохранительную копию на Яндекс Диске, текущая база не заменялась.")
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
                            "expires_at": (moscow_now() + timedelta(hours=12)).isoformat(timespec="seconds"),
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
    if st.session_state.get("user_role") == "admin":
        with st.expander("Журнал системы"):
            st.caption("История событий и ошибок хранится на Яндекс Диске и сохраняется после Reboot.")
            if st.button("Открыть журнал в CRM", key="crm_open_system_logs", use_container_width=True):
                st.session_state["show_system_logs"] = True
                st.rerun()
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
        _tok = cookies.get("auth_token") or st.session_state.get("_auth_token_current")
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
            cookie_manager.delete("crm_last_activity")
            cookie_manager.delete("crm_session_expired")
        except Exception:
            pass
        st.session_state["_force_password_login"] = True
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_login = None
        st.session_state.user_name = None
        st.session_state.remember_login = False
        st.session_state.pop("_auth_last_activity", None)
        st.session_state.pop("_auth_token_current", None)
        st.rerun()

# Просмотр журнала в рабочей области доступен только администратору.
if st.session_state.get("show_system_logs") and st.session_state.get("user_role") == "admin":
    st.markdown("## Журнал системы CRM")
    st.caption("Журнал хранится на Яндекс Диске отдельно от базы CRM. Секреты и пароли не записываются.")
    _log_top_left, _log_top_right = st.columns([1, 5])
    with _log_top_left:
        if st.button("Закрыть журнал", key="crm_close_system_logs"):
            st.session_state["show_system_logs"] = False
            st.rerun()
    with _log_top_right:
        if st.button("Обновить список журналов", key="crm_refresh_system_logs"):
            st.rerun()
    try:
        _crm_log_files = _get_yandex_crm_logs()
        if not _crm_log_files:
            st.info("На Яндекс Диске пока нет файлов журнала. Новые события будут записываться после запуска этой версии CRM.")
        else:
            _crm_log_options = [x.get("name", "") for x in _crm_log_files]
            _crm_log_selected = st.selectbox("Файл журнала (дата)", _crm_log_options, key="crm_system_log_file")
            if _crm_log_selected:
                _crm_log_text = _read_yandex_crm_log(_crm_log_selected)
                _crm_log_lines = _crm_log_text.splitlines()
                _crm_log_tail = "\n".join(_crm_log_lines[-500:])
                st.caption(f"Всего строк в выбранном файле: {len(_crm_log_lines)}. Показаны последние 500.")
                st.text_area("События", value=_crm_log_tail, height=420, key="crm_system_log_text")
                st.download_button("Скачать выбранный журнал", data=_crm_log_text.encode("utf-8"), file_name=_crm_log_selected, mime="application/x-ndjson", key="crm_download_system_log")
    except Exception as _crm_log_view_exc:
        st.error(f"Не удалось прочитать журнал: {str(_crm_log_view_exc)[:300]}")
    st.markdown("---")

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

def _crm_workspace_clear_legacy_dialog_markers():
    # Closing a workspace item must not let legacy dialog flags recreate it on rerun.
    for _key in list(st.session_state.keys()):
        if str(_key).startswith("dialog_") or str(_key).startswith("_open_created_"):
            st.session_state.pop(_key, None)
    st.session_state["_crm_dialog_requested_this_run"] = True

def _crm_workspace_render_bottom_panel(in_workspace=False):
    _bottom_windows = st.session_state.get("_crm_windows", [])
    if not _bottom_windows:
        return
    # Window buttons reuse the tab frame styling, while the original 5:0.7
    # column ratio is retained so the label button receives the full width it needs.
    _bottom_active_window_id = st.session_state.get("_crm_active_window_id")
    st.markdown("""<style>
    .st-key-crm_workspace_bottom {
        display:flex !important; flex-direction:row !important; flex-wrap:nowrap !important;
        align-items:center !important; justify-content:flex-start !important;
        gap:0 !important; column-gap:0 !important; row-gap:0 !important;
        width:100% !important; overflow-x:auto !important;
        background:transparent !important; border:0 !important; border-radius:0 !important;
        padding:0 !important; margin:0 !important; box-sizing:border-box !important;
    }
    .st-key-crm_workspace_bottom [class*="st-key-crm_workspace_window_item_"] {
        display:flex !important; flex:0 0 auto !important; flex-direction:row !important;
        flex-wrap:nowrap !important; align-items:center !important; justify-content:flex-start !important;
        gap:0 !important; column-gap:0 !important; row-gap:0 !important;
        width:max-content !important; min-width:max-content !important;
        max-width:none !important; margin:0 !important; overflow:visible !important;
        border:1px solid #D9DEE7 !important; border-radius:7px !important;
        background:#F3F5F8 !important; padding:0 3px !important;
        box-shadow:none !important; outline:0 !important;
    }
    .st-key-crm_workspace_bottom [class*="st-key-crm_workspace_window_item_"] [data-testid="stHorizontalBlock"] {
        display:flex !important; flex-wrap:nowrap !important; gap:0 !important;
        width:100% !important; min-width:0 !important; align-items:center !important;
    }
    .st-key-crm_workspace_bottom [class*="st-key-crm_workspace_window_item_"] [data-testid="column"] {
        min-width:0 !important; padding:0 !important;
    }
    .st-key-crm_workspace_bottom [class*="st-key-crm_workspace_window_item_"] .stButton,
    .st-key-crm_workspace_bottom [class*="st-key-crm_workspace_window_item_"] [data-testid="stButton"] {
        width:100% !important; min-width:0 !important; border:0 !important;
        background:transparent !important; box-shadow:none !important; outline:0 !important;
        padding:0 !important; margin:0 !important;
    }
    .st-key-crm_workspace_bottom [class*="st-key-crm_workspace_window_item_"] button {
        box-sizing:border-box !important; display:inline-flex !important;
        width:100% !important; min-width:0 !important; max-width:none !important;
        min-height:38px !important; align-items:center !important; justify-content:center !important;
        border:0 !important; border-radius:0 !important; outline:0 !important;
        box-shadow:none !important; padding:0.5rem 0.55rem !important;
        color:#65758B !important; font-weight:500 !important; background:transparent !important;
        white-space:nowrap !important; writing-mode:horizontal-tb !important;
    }
    .st-key-crm_workspace_bottom [class*="st-key-crm_workspace_window_item_"] button p,
    .st-key-crm_workspace_bottom [class*="st-key-crm_workspace_window_item_"] button span { white-space:nowrap !important; }
    .st-key-crm_workspace_bottom [class*="st-key-crm_workspace_window_item_"] [data-testid="column"]:first-child button {
        padding:0.5rem 0.45rem 0.5rem 0.7rem !important;
    }
    .st-key-crm_workspace_bottom [class*="st-key-crm_workspace_window_item_"] [data-testid="column"]:last-child button {
        min-width:27px !important; width:27px !important; min-height:30px !important;
        height:30px !important; padding:0 !important; margin:0 !important;
        color:#8A94A3 !important; font-size:18px !important; line-height:1 !important;
    }
    .st-key-crm_workspace_bottom [class*="st-key-crm_workspace_window_item_"] [data-testid="column"]:last-child button:hover { color:#BC1661 !important; }
    .st-key-crm_workspace_bottom [class*="st-key-crm_workspace_window_item_"]:has([data-testid="stBaseButton-primary"]) { border-color:#BC1661 !important; }
    .st-key-crm_workspace_bottom [class*="st-key-crm_workspace_window_item_"]:has([data-testid="stBaseButton-primary"]) button { color:#BC1661 !important; }
    </style>""", unsafe_allow_html=True)
    with st.container(key="crm_workspace_bottom", horizontal=True, wrap=False, gap=None, horizontal_alignment="left"):
        for _w in list(_bottom_windows):
            _label = str(_w.get("title") or "CRM")[:24] + (f" · {len(_w.get('tabs', []))}" if _w.get("tabs") else "")
            if not in_workspace:
                _label = ("▣ " if _w.get("minimized") else "● ") + _label
            with st.container(key=f"crm_workspace_window_item_{_w.get('id')}", horizontal=True, wrap=False, gap=None, width="content", horizontal_alignment="left"):
                _window_label_col, _window_close_col = st.columns([5, 0.7], gap=None)
                with _window_label_col:
                    _window_is_active = (_w.get("id") == _bottom_active_window_id and not _w.get("minimized"))
                    if st.button(_label, key=f"crm_workspace_restore_{_w.get('id')}", type="primary" if (in_workspace and _window_is_active) or (not in_workspace and not _w.get("minimized")) else "secondary", use_container_width=True):
                        _w["minimized"] = False
                        st.session_state["_crm_active_window_id"] = _w.get("id")
                        st.rerun()
                with _window_close_col:
                    if st.button("×", key=f"crm_workspace_taskbar_close_{_w.get('id')}", use_container_width=True):
                        st.session_state["_crm_windows"] = [w for w in st.session_state.get("_crm_windows", []) if w.get("id") != _w.get("id")]
                        if st.session_state.get("_crm_active_window_id") == _w.get("id"):
                            st.session_state["_crm_active_window_id"] = next((w.get("id") for w in st.session_state["_crm_windows"] if not w.get("minimized")), None)
                            st.session_state.pop("_crm_active_dialog", None)
                        _crm_workspace_clear_legacy_dialog_markers()
                        _crm_workspace_queue_save()
                        st.rerun()

nc1, nc2, nc3, nc4, nc5, nc6 = st.columns(6)
with nc1:
    if st.button("Клиенты", use_container_width=True, type="primary" if st.session_state.active_tab == "Клиенты" else "secondary"):
        st.session_state.active_tab = "Клиенты"
        st.session_state["_dialog_return_stack"] = []
        st.session_state["_crm_modal_stack"] = []
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
        st.session_state["_crm_modal_stack"] = []
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
        st.session_state["_crm_modal_stack"] = []
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
        st.session_state["_crm_modal_stack"] = []
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
        st.session_state["_crm_modal_stack"] = []
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
        st.session_state["_crm_modal_stack"] = []
        st.session_state.pop("dialog_task_key", None)
        st.session_state.pop("dialog_deal_key", None)
        st.session_state.pop("_open_created_deal", None)
        st.rerun()
st.markdown("---")

# На главном экране панель окон расположена сразу под навигацией CRM.
_crm_nav_active_id = st.session_state.get("_crm_active_window_id")
_crm_nav_active_window = next((w for w in st.session_state.get("_crm_windows", []) if w.get("id") == _crm_nav_active_id), None)
if not _crm_nav_active_window or _crm_nav_active_window.get("minimized"):
    _crm_workspace_render_bottom_panel()

# Toast при загрузке если есть непрочитанные
_unread_count = get_unread_count()
if _unread_count > 0 and not st.session_state.get("crm_toast_shown", False):
    st.toast(f"У вас {_unread_count} новых уведомлений", icon="\U0001F514")
    st.session_state["crm_toast_shown"] = True

render_notifications_panel()
render_close_deal_dialog_trigger()

cu = st.session_state.user_name

# Доступна до рендеринга форм задач: сумма товаров без доставки с учётом скидок.
def _deal_items_total(items):
    total = 0.0
    for item in items or []:
        qty = max(0.0, float(item.get("quantity", 0) or 0))
        price = max(0.0, float(item.get("unit_price", 0) or 0))
        discount = min(100.0, max(0.0, float(item.get("discount", 0) or 0)))
        total += qty * price * (1 - discount / 100.0)
    return round(total, 2)

def render_task_form(deal_id, cl_id, key_suffix, default_type="Связаться"):
    ntype = st.selectbox("Тип задачи:", TASK_TYPES, index=TASK_TYPES.index(default_type) if default_type in TASK_TYPES else 0, key=f"nt_type_{key_suffix}")
    if ntype not in ("Отправить заказ", "Отправить образцы"):
        ntopic = st.text_input("Тема задачи:", key=f"nt_topic_{key_suffix}")
    else:
        ntopic = ntype
    ntm = st.selectbox("Ответственный:", get_managers_list(), index=None, key=f"nt_mgr_{key_suffix}", placeholder=MGR_PLACEHOLDER)
    ntd = st.date_input("Срок:", format="DD.MM.YYYY", key=f"nt_d_{key_suffix}")
    _selected_calc_id_new = ""
    if ntype in ("Отправить заказ", "Отправить образцы"):
        _deal_for_new_task = get_deal_by_id(deal_id) if deal_id else None
        _selected_calc_id_new, nproducts = render_task_products_editor(
            _deal_for_new_task, f"nt_{key_suffix}",
            st.session_state.get(f"nt_{key_suffix}_prod", ""),
            st.session_state.get(f"nt_{key_suffix}_order_calc", "")
        )
        nship_city = st.text_input("Город:", key=f"nt_city_{key_suffix}")
        nship_addr = st.text_area("Адрес доставки:", key=f"nt_addr_{key_suffix}")
        _client_options = {str(c.get("id", "")): c for c in st.session_state.crm_store.get("clients", [])}
        _client_display = {str(c.get("id", "")): str(c.get("name", "Клиент")) for c in _client_options.values()}
        for _client_item in _client_options.values():
            for _extra_phone in _client_item.get("extra_phones", []) or []:
                if isinstance(_extra_phone, dict):
                    _contact_key = f"{_client_item.get('id')}|{_extra_phone.get('phone','')}"
                    _client_display[_contact_key] = f"{_client_item.get('name','Клиент')} — {(_extra_phone.get('name') or 'Доп. контакт')} ({_extra_phone.get('phone','')})"
        _receiver_row, _picker_row = st.columns([4, 1.5])
        with _receiver_row:
            nreceiver = st.text_input("Получатель:", key=f"nt_recv_{key_suffix}")
        with _picker_row:
            st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
            if st.button("Выбрать клиента", key=f"nt_choose_client_{key_suffix}", use_container_width=True):
                st.session_state[f"nt_show_client_picker_{key_suffix}"] = not st.session_state.get(f"nt_show_client_picker_{key_suffix}", False)
        if st.session_state.get(f"nt_show_client_picker_{key_suffix}", False):
            _picked_contact = st.selectbox("Клиент / доп. контакт", list(_client_display), format_func=lambda x: _client_display.get(x, x), key=f"nt_client_picker_{key_suffix}", index=None, placeholder="Выберите клиента")
            if st.button("Заполнить поля", key=f"nt_apply_client_{key_suffix}", use_container_width=True):
                if _picked_contact:
                    _parts = str(_picked_contact).split("|", 1)
                    _picked_client = _client_options.get(_parts[0])
                    if _picked_client:
                        if len(_parts) > 1:
                            _extra = next((p for p in _picked_client.get("extra_phones", []) or [] if isinstance(p, dict) and str(p.get("phone", "")) == _parts[1]), {})
                            st.session_state[f"nt_recv_{key_suffix}"] = str(_extra.get("name", "") or _picked_client.get("name", ""))
                            st.session_state[f"nt_rphone_{key_suffix}"] = str(_extra.get("phone", ""))
                        else:
                            st.session_state[f"nt_recv_{key_suffix}"] = str(_picked_client.get("name", ""))
                            st.session_state[f"nt_rphone_{key_suffix}"] = str(_picked_client.get("phone", ""))
                    st.session_state[f"nt_show_client_picker_{key_suffix}"] = False
                    st.rerun()
        nreceiver_phone = st.text_input("Телефон получателя:", key=f"nt_rphone_{key_suffix}")
        nship_pay = st.selectbox("Оплата:", SHIP_PAY_OPTIONS, index=0, key=f"nt_pay_{key_suffix}", placeholder="Укажи плательщика")
        _selected_calc_new = next((c for c in (_deal_for_new_task or {}).get("calculations", []) if str(c.get("id")) == str(_selected_calc_id_new)), None)
        _auto_amount_new = _deal_items_total(_selected_calc_new.get("items", [])) if _selected_calc_new else 0
        _amount_key_new = f"nt_amount_{key_suffix}"
        if _auto_amount_new > 0:
            st.session_state[_amount_key_new] = f"{_auto_amount_new:g}"
        norder_amount = st.text_input("Сумма заказа (руб.):", value=f"{_auto_amount_new:g}" if _auto_amount_new > 0 else "", key=_amount_key_new, placeholder="Сумма из расчёта без доставки", disabled=bool(_auto_amount_new))
        ntk_num = st.text_input("Трек (подпиши если габариты не указаны):", key=f"nt_tk_{key_suffix}", placeholder="Введите трек-номер")
        ncomment = st.text_area("Комментарии:", key=f"nt_c_{key_suffix}")
        _nt_file_ver = st.session_state.get(f"nt_file_ver_{key_suffix}", 0)
        ntf = st.file_uploader("Файлы задачи:", key=f"nt_file_{key_suffix}_{_nt_file_ver}", accept_multiple_files=True)
    else:
        nproducts = ""
        nship_city = ""
        nship_addr = ""
        nreceiver = ""
        nreceiver_phone = ""
        nship_pay = ""
        norder_amount = ""
        ntk_num = ""
        ncomment = st.text_area("Комментарии:", key=f"nt_c_{key_suffix}")
        _nt_file_ver = st.session_state.get(f"nt_file_ver_{key_suffix}", 0)
        ntf = st.file_uploader("Файлы задачи:", key=f"nt_file_{key_suffix}_{_nt_file_ver}", accept_multiple_files=True)
    _create_file_upload_col, _create_file_pick_col = st.columns(2)
    with _create_file_upload_col:
        if st.button("Загрузить", key=f"nt_file_upload_btn_{key_suffix}", use_container_width=True):
            if ntf:
                _new_uploaded_task_files = normalize_file_list(save_uploaded_files(ntf, cl_id, "task_file"))
                st.session_state.setdefault(f"nt_uploaded_files_{key_suffix}", []).extend(_new_uploaded_task_files)
                st.session_state[f"nt_file_ver_{key_suffix}"] = _nt_file_ver + 1
                st.rerun()
            else:
                st.warning("Выберите файл(ы) для загрузки.")
    with _create_file_pick_col:
        if st.button("Выбрать из загруженных", key=f"nt_pick_existing_btn_{key_suffix}", use_container_width=True):
            _create_pick_key = f"nt_pick_existing_open_{key_suffix}"
            st.session_state[_create_pick_key] = not st.session_state.get(_create_pick_key, False)
    _create_source_deal = get_deal_by_id(deal_id) if deal_id else None
    _create_source_client = get_client_by_id(cl_id)
    _create_source_files = (_create_source_deal or {}).get("deal_files", []) if deal_id else (_create_source_client or {}).get("client_files", [])
    _create_source_files = [f for f in (_create_source_files or []) if isinstance(f, dict) and (f.get("file_path") or f.get("path"))]
    _create_file_options = {f"{i+1}. {f.get('file_name') or f.get('name') or os.path.basename(str(f.get('file_path') or f.get('path') or 'Файл'))} · {i}": f for i, f in enumerate(_create_source_files)}
    if st.session_state.get(f"nt_pick_existing_open_{key_suffix}", False):
        if _create_file_options:
            st.multiselect("Файлы из карточки клиента:" if not deal_id else "Файлы из окна сделки:", list(_create_file_options), key=f"nt_pick_existing_select_{key_suffix}")
        else:
            st.caption("В карточке клиента/сделке пока нет загруженных файлов.")
    if st.button("Создать", key=f"nt_go_{key_suffix}", use_container_width=True, type="primary"):
        if ntype not in ("Отправить заказ", "Отправить образцы") and not ntopic.strip():
            st.warning("Введите тему задачи")
        else:
            tfi_list = list(st.session_state.get(f"nt_uploaded_files_{key_suffix}", []) or [])
            if ntf:
                tfi_list.extend(normalize_file_list(save_uploaded_files(ntf, cl_id, "task_file")))
            _picked_create_keys = st.session_state.get(f"nt_pick_existing_select_{key_suffix}", []) or []
            _picked_create_files = []
            for _picked_create_key in _picked_create_keys:
                if _picked_create_key in _create_file_options:
                    _picked_file = dict(_create_file_options[_picked_create_key])
                    if not _picked_file.get("file_path") and _picked_file.get("path"):
                        _picked_file["file_path"] = _picked_file["path"]
                    if not _picked_file.get("file_name") and _picked_file.get("name"):
                        _picked_file["file_name"] = _picked_file["name"]
                    _picked_create_files.append(_picked_file)
            _task_file_seen = {str(f.get("file_hash", "") or f.get("file_path", "")) for f in tfi_list if isinstance(f, dict)}
            for _picked_file in _picked_create_files:
                _identity = str(_picked_file.get("file_hash", "") or _picked_file.get("file_path", "") or _picked_file.get("path", ""))
                if _identity and _identity not in _task_file_seen:
                    tfi_list.append(_picked_file)
                    _task_file_seen.add(_identity)
            prefix = "ЗС" if deal_id else "ЗК"
            tn = generate_task_number(prefix)
            te = {
                "text": ntopic.strip(), "deadline": ntd.isoformat(), "done": False, "type": ntype,
                "task_files": tfi_list, "manager": ntm or "",
                "completion_report": "", "completion_files": [],
                "deal_id": deal_id, "task_comment": ncomment.strip(),
                "order_amount": round(float(norder_amount.replace(",", ".")), 2) if norder_amount and norder_amount.strip() else 0, "last_modified": now_str(),
                "task_number": tn, "created_at": now_str(), "created_by": st.session_state.get("user_login", ""),
                "in_work": False, "ready_to_ship": False, "delegated_to": None, "needs_rework": False, "reviewed": False,
                "task_comments": [], "flagged": False,
                "products": nproducts, "ship_city": nship_city, "ship_addr": nship_addr,
                "receiver": nreceiver, "receiver_phone": nreceiver_phone,
                "ship_pay": nship_pay, "tk_num": ntk_num.strip(),
                "calculation_id": str(_selected_calc_id_new) if _selected_calc_id_new else ""
            }
            cl = get_client_by_id(cl_id)
            if cl:
                cl.setdefault("tasks", []).append(te)
                st.session_state.pop(f"nt_uploaded_files_{key_suffix}", None)
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
    # При открытом окне сделки проверяем оплату по документам Точки не чаще раза в минуту.
    for _calc in d.get("calculations", []) or []:
        _tochka_auto_refresh_payment_status(d, _calc)
    with st.container(border=True):
        st.markdown(f"**{d.get('deal_number', d.get('title', ''))}**")
        st.markdown(format_created_date(d), unsafe_allow_html=True)
        st.markdown(f"**Бюджет:** {d.get('budget', 0):,.0f} руб.".replace(",", " "))
        ps = d.get("payment_status", "Не оплачено")
        inject_payment_container_css(d["id"], ps)
        with st.container(key=f"ps_wrap_{d['id']}"):
            new_ps = st.selectbox("Статус оплаты:", ["Не оплачено", "Оплачен частично", "Оплачено"], index=["Не оплачено", "Оплачен частично", "Оплачено"].index(ps) if ps in ["Не оплачено", "Оплачен частично", "Оплачено"] else 0, key=f"ps_{d['id']}")
        _bank_payment_status = _tochka_bank_payment_status(d)
        if _bank_payment_status and _bank_payment_status != ps:
            st.markdown(
                f"<div style='font-size:0.78rem;color:#7B8490;font-style:italic;margin-top:-0.35rem;'>Внимание: статус CRM не совпадает с данными банка (по данным банка: {html.escape(_bank_payment_status)}).</div>",
                unsafe_allow_html=True,
            )
        if new_ps != ps:
            d["payment_status"] = new_ps
            d["payment_status_manual_override"] = bool(new_ps == "Не оплачено" and _bank_payment_status == "Оплачено")
            d["last_modified"] = now_str()
            _sync_deal_board_stage_from_payment(d)
            if new_ps == "Оплачено":
                try:
                    _ensure_paid_deal_torg12(d)
                except Exception as exc:
                    st.session_state["_paid_torg12_error"] = str(exc)[:300]
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
            render_soft_delete_comments(d["deal_comments"], f"deal_card_{d['id']}", "time", "author")
        dc_clr_key = f"clr_dc_{d['id']}"
        if st.session_state.get(dc_clr_key):
            st.session_state[f"dc_input_{d['id']}"] = ""
            st.session_state[dc_clr_key] = False
        nc = st.text_input("Добавить комментарий:", key=f"dc_input_{d['id']}")
        if st.button("Добавить", key=f"dc_btn_{d['id']}", use_container_width=True):
            if nc.strip():
                d.setdefault("deal_comments", []).append({"time": moscow_now().strftime("%d.%m.%Y %H:%M"), "author": st.session_state.get("user_name", ""), "text": nc.strip()})
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
        elif current_status in ("В работе", "Оплачено"):
            if st.button("Закрыть сделку", key=f"deal_close_{d['id']}", use_container_width=True, type="primary"):
                st.session_state["dialog_close_deal_id"] = d["id"]
                st.rerun()
        if current_status in ("В работе", "Оплачено", "Ожидание оплаты"):
            st.markdown("<hr style='border:0;height:1px;background:#DCE0E5;margin:0.8rem 0;'>", unsafe_allow_html=True)
            _pause_reason_input = st.text_area("Причина:", value=st.session_state.get(f"deal_pause_reason_input_{d['id']}", ""), key=f"deal_pause_reason_input_{d['id']}", height=90, placeholder="Укажите причину паузы")
            if st.button("Поставить на паузу", key=f"deal_pause_{d['id']}", use_container_width=True):
                if not _pause_reason_input.strip():
                    st.warning("Укажите причину, прежде чем поставить сделку на паузу.")
                else:
                    d["paused_from_status"] = current_status
                    d["pause_reason"] = _pause_reason_input.strip()
                    d["status"] = "На паузе"
                    d["last_modified"] = now_str()
                    commit_and_rerun(st.session_state.crm_store, "Сделка поставлена на паузу")
        elif current_status == "На паузе":
            st.markdown("<hr style='border:0;height:1px;background:#DCE0E5;margin:0.8rem 0;'>", unsafe_allow_html=True)
            if d.get("pause_reason"):
                st.markdown(f"<div style='font-size:0.9rem;margin:0.35rem 0 0.75rem;'><b>Сделка на паузе по причине:</b> {html.escape(str(d['pause_reason']))}.</div>", unsafe_allow_html=True)
            if st.button("Вернуть в работу", key=f"deal_unpause_{d['id']}", use_container_width=True):
                d["status"] = "Оплачено" if d.get("payment_status") == "Оплачено" else ("Ожидание оплаты" if _deal_has_active_payment_document(d) else "В работе")
                d.pop("paused_from_status", None)
                d["last_modified"] = now_str()
                commit_and_rerun(st.session_state.crm_store, "Сделка возвращена из паузы")
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
    # Карточки сделок оформлены в том же компактном стиле, что и карточки задач:
    # пастельный фон, тонкая рамка и цветная полоса слева.
    _deal_status = d.get("status", "Новый")
    _deal_style = {
        "Новый": ("#E3F2FD", "#2196F3"),
        "В работе": ("#E8F5E9", "#4CAF50"),
        "Ожидание оплаты": ("#FFF8E1", "#F9A825"),
        "Оплачено": ("#E8F5E9", "#2E7D32"),
        "На паузе": ("#F3E5F5", "#8E24AA"),
        "Сделка закрыта": ("#ECEFF1", "#78909C"),
        "Архив": ("#F5F5F5", "#9E9E9E"),
    }
    dl_bg, dl_bc = _deal_style.get(_deal_status, ("#FFFFFF", "#CBD5E1"))
    st.markdown(f"""<style>
    .st-key-dls_wrap_{deal_id} button {{
        background-color: {dl_bg} !important;
        color: #2C3E50 !important;
        border: 1px solid {dl_bc} !important;
        border-left: 4px solid {dl_bc} !important;
        border-radius: 9px !important;
        padding: 0.55rem 0.7rem !important;
        min-height: 66px !important;
        height: auto !important;
        box-shadow: 0 1px 2px rgba(30,45,65,0.05) !important;
        transition: box-shadow 0.15s ease, border-color 0.15s ease !important;
        white-space: normal !important;
        text-align: left !important;
    }}
    .st-key-dls_wrap_{deal_id} button p {{
        font-size: 0.86rem !important;
        line-height: 1.42 !important;
        font-weight: 500 !important;
        text-align: left !important;
        white-space: normal !important;
    }}
    .st-key-dls_wrap_{deal_id} button:hover {{
        box-shadow: 0 3px 9px rgba(30,45,65,0.12) !important;
        border-color: {dl_bc} !important;
    }}
    </style>""", unsafe_allow_html=True)
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
    app_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        ("DejaVu", os.path.join(app_dir, "fonts", "DejaVuSans.ttf"), os.path.join(app_dir, "fonts", "DejaVuSans-Bold.ttf")),
        ("DejaVuSystem", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
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
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, Image, PageBreak
    font, bold = _pdf_font_setup()
    out=io.BytesIO()
    doc=SimpleDocTemplate(out, pagesize=landscape(A4), rightMargin=10*mm, leftMargin=10*mm, topMargin=0.5*mm, bottomMargin=10*mm, title=f"Коммерческое предложение №{_deal_doc_number(deal)}")
    styles=getSampleStyleSheet()
    brand=colors.HexColor("#bc1661")
    title=ParagraphStyle("OfferTitle", parent=styles["Title"], fontName=bold, fontSize=15, leading=19, alignment=TA_CENTER, textColor=colors.HexColor("#202833"), spaceAfter=8*mm)
    h=ParagraphStyle("OfferH", parent=styles["Heading2"], fontName=bold, fontSize=9, leading=11, textColor=brand, spaceBefore=2*mm, spaceAfter=1.5*mm)
    body=ParagraphStyle("OfferBody", parent=styles["BodyText"], fontName=font, fontSize=7.6, leading=10, spaceAfter=1.2*mm, textColor=colors.HexColor("#343D4A"))
    small=ParagraphStyle("OfferSmall", parent=body, fontSize=6.4, leading=8)
    date_style=ParagraphStyle("OfferDateRight", parent=body, alignment=TA_RIGHT, spaceAfter=0)
    cell=ParagraphStyle("OfferCell", parent=small, fontSize=6.2, leading=7.5)
    cellhead=ParagraphStyle("OfferCellHead", parent=cell, fontName=bold, alignment=TA_CENTER, textColor=colors.white)
    date=moscow_now().date()
    validity=date+timedelta(days=30)
    # Use the same brand logo treatment as the Ozon invoice PDF.
    def _offer_asset_image(filename, width_mm, max_height_mm=None):
        candidates=[os.path.join(os.getcwd(), filename), os.path.join(os.path.dirname(os.path.abspath(__file__)), filename), os.path.join("assets", filename), os.path.join("static", filename)]
        path=next((x for x in candidates if os.path.isfile(x)), None)
        if not path: return None
        try:
            im=Image(path); im.drawWidth=width_mm*mm
            ratio=im.imageHeight/float(im.imageWidth or 1); im.drawHeight=im.drawWidth*ratio
            if max_height_mm and im.drawHeight>max_height_mm*mm:
                scale=(max_height_mm*mm)/im.drawHeight; im.drawWidth*=scale; im.drawHeight*=scale
            im.hAlign="LEFT"
            return im
        except Exception: return None
    logo=_offer_asset_image("Логотип iPlinth с розовым шевроном-1.png", 187.5, 52.5)
    header=Table([[logo or Paragraph("iPlinth",body), Paragraph(f"Дата выдачи: {date.strftime('%d.%m.%Y')}<br/>Срок действия: 30 дней (до {validity.strftime('%d.%m.%Y')})", date_style)]], colWidths=[150*mm,127*mm], hAlign="LEFT")
    header.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(1,0),(1,0),"RIGHT"),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(0,0),0),("RIGHTPADDING",(1,0),(1,0),20*mm),("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    flow=[header, Spacer(1,4*mm), Paragraph(f"КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ № {html.escape(_deal_doc_number(deal))}", title),
          Paragraph("1. СВЕДЕНИЯ О ПОСТАВЩИКЕ", h),
          Paragraph("Наименование организации: ИП Фазлов Дамир Ибрагимович<br/>ИНН: 731701704975<br/>Адрес производства: г. Казань, ул. Кулагина, д. 3<br/>Телефон / Email: +7 (900) 329-33-00 / info@iplinth.ru", body),
          Paragraph(f"Кому: {html.escape(str(client.get('name','') or ''))}", body),
          Paragraph("2. СМЕТА НА ПОСТАВКУ МАТЕРИАЛОВ", h),
          Paragraph("Условия налогообложения: все цены указаны без НДС в связи с применением УСН.", small), Spacer(1,2*mm)]
    rows=_calculation_rows(calc, st.session_state.crm_store.get("products", DEFAULT_PRODUCT_CATALOG))
    show_discount=any(float(r.get("discount",0) or 0)>0 for r in rows)
    headers=["№","Артикул / наименование","Цвет","Технические характеристики","Ед. изм.","Цена"]
    if show_discount: headers += ["Скидка","Цена со скидкой"]
    headers += ["Кол-во","Сумма"]
    table_data=[[Paragraph(x,cellhead) for x in headers]]
    for i,r in enumerate(rows,1):
        item_name=f"<b>{html.escape(str(r['sku']))}</b><br/>{html.escape(str(r['name']))}"
        line=[Paragraph(str(i),cell), Paragraph(item_name,cell), Paragraph(html.escape(str(r['color'] or '—')),cell), Paragraph(html.escape(str(r['spec'] or '—')),cell), Paragraph(html.escape(str(r['unit'] or '')),cell), Paragraph(_money(r['price']),cell)]
        if show_discount: line += [Paragraph(f"{r['discount']:g}%",cell), Paragraph(_money(r['after']),cell)]
        line += [Paragraph(f"{r['quantity']:g}",cell), Paragraph(_money(r['amount']),cell)]
        table_data.append(line)
    if not rows:
        table_data.append([Paragraph("—",cell), Paragraph("Товары не добавлены в расчёт",cell)] + [""]*(len(headers)-2))
    total=sum(r['amount'] for r in rows)
    delivery=max(0.0,float(calc.get("delivery_amount",0) or 0))
    if delivery:
        delivery_row=[""]*len(headers); delivery_row[1]=Paragraph("Доставка",cell); delivery_row[-1]=Paragraph(_money(delivery),cell); table_data.append(delivery_row)
    total_row=[""]*len(headers); total_row[-2]=Paragraph("ИТОГО:",cell); total_row[-1]=Paragraph(_money(total+delivery),cell); table_data.append(total_row)
    if show_discount:
        widths=[8*mm,43*mm,15*mm,43*mm,12*mm,19*mm,13*mm,22*mm,13*mm,22*mm]
    else:
        widths=[9*mm,49*mm,17*mm,55*mm,14*mm,25*mm,18*mm,28*mm]
    tbl=Table(table_data,colWidths=widths,repeatRows=1,hAlign="LEFT")
    last_row=len(table_data)-1
    tbl_style=[("BACKGROUND",(0,0),(-1,0),brand),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#E5A8C4")),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("BACKGROUND",(0,last_row),(-1,last_row),colors.HexColor("#FCEEF4")),("FONTNAME",(0,last_row),(-1,last_row),bold),
        ("SPAN",(0,last_row),(len(headers)-3,last_row)),("ALIGN",(len(headers)-2,1),(-1,-1),"RIGHT")]
    tbl.setStyle(TableStyle(tbl_style))
    flow += [tbl, PageBreak(), Spacer(1,20*mm), Paragraph("3. ДОПОЛНИТЕЛЬНЫЕ УСЛОВИЯ И ХАРАКТЕРИСТИКИ", h),
             Paragraph("• Условия оплаты: 100%.<br/>• Сроки поставки: отгрузка в течение 3 рабочих дней с момента поступления оплаты на расчётный счёт Поставщика.<br/>• При отгрузке предоставляется комплект закрывающих документов (УПД, товарная накладная), а также сертификаты соответствия на продукцию.", body),
             Spacer(1,2*mm), Paragraph("4. ПОДПИСЬ И ПЕЧАТЬ ПОСТАВЩИКА", h)]
    stamp=_offer_asset_image("печать.png",35,28)
    signature=_offer_asset_image("подпись.png",35,18)
    class _OfferStampSignature(Flowable):
        def __init__(self, stamp_img, signature_img):
            super().__init__(); self.stamp_img=stamp_img; self.signature_img=signature_img; self.width=85*mm; self.height=30*mm
        def draw(self):
            if self.stamp_img:
                self.canv.saveState(); self.canv.drawImage(self.stamp_img.filename,0,0,width=self.stamp_img.drawWidth,height=self.stamp_img.drawHeight,preserveAspectRatio=True,mask='auto'); self.canv.restoreState()
            if self.signature_img:
                self.canv.drawImage(self.signature_img.filename,-8*mm,7*mm,width=self.signature_img.drawWidth,height=self.signature_img.drawHeight,preserveAspectRatio=True,mask='auto')
    sign=Table([[Paragraph("ИП Фазлов Дамир Ибрагимович<br/>Подпись и печать",body),_OfferStampSignature(stamp,signature)]],colWidths=[90*mm,90*mm])
    sign.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)]))
    flow.append(sign)
    doc.build(flow)
    return out.getvalue()



def _make_torg12_pdf(deal, client, calc):
    """Формирует ТОРГ-12 в одностраничной компоновке по предоставленному образцу."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.lib.utils import simpleSplit

    font, bold = _pdf_font_setup()
    out = io.BytesIO()
    doc_no = _deal_doc_number(deal)
    date = moscow_now().date()
    catalog = st.session_state.crm_store.get("products", DEFAULT_PRODUCT_CATALOG)
    rows = _calculation_rows(calc, catalog)
    if not rows:
        raise ValueError("В расчёте нет товарных позиций для накладной.")

    def esc(v):
        return str(v or "").replace("\n", " ").strip()

    def money(v):
        return _money(round(float(v or 0), 2)).replace(" ", "\u00a0")

    reqs = [r for r in (client.get("requisites", []) or []) if not r.get("deleted")]
    req = reqs[0] if reqs else {}
    buyer_name = req.get("legal_name") or client.get("company") or client.get("name") or ""
    buyer_inn = req.get("inn", "")
    buyer_kpp = req.get("kpp", "")
    buyer_address = req.get("address") or client.get("address") or client.get("main_address") or ""
    supplier = "ИП Фазлов Дамир Ибрагимович, ИНН 731701704975"
    supplier_full = ("ИП Фазлов Дамир Ибрагимович, ИНН 731701704975, "
                     "420064, РОССИЯ, ТАТАРСТАН Респ, КАЗАНЬ г, РАУИСА ГАРЕЕВА ул, "
                     "ДОМ 113, кв 156, р/с 40802810801500486358, в банке ООО «Банк Точка», "
                     "БИК 044525104, к/с 30101810745374525104")
    buyer_full = buyer_name
    if buyer_inn:
        buyer_full += f", ИНН {buyer_inn}"
    if buyer_address:
        buyer_full += f", {buyer_address}"
    if buyer_kpp:
        buyer_full += f", КПП {buyer_kpp}"

    page_w, page_h = landscape(A4)
    c = canvas.Canvas(out, pagesize=(page_w, page_h), pageCompression=1)
    c.setTitle(f"Товарная накладная №{doc_no} от {date.strftime('%d.%m.%Y')}")
    W, H = page_w/mm, page_h/mm

    def txt(x, y, text, size=6.0, face=None, align="left"):
        face = face or font
        c.setFont(face, size)
        text = esc(text)
        if align == "center":
            c.drawCentredString(x*mm, H*mm-y*mm, text)
        elif align == "right":
            c.drawRightString(x*mm, H*mm-y*mm, text)
        else:
            c.drawString(x*mm, H*mm-y*mm, text)

    def line(x1, y1, x2, y2, width=0.35):
        c.setLineWidth(width)
        c.line(x1*mm, H*mm-y1*mm, x2*mm, H*mm-y2*mm)

    def rect(x, y, w, h, width=0.35):
        c.setLineWidth(width)
        c.rect(x*mm, H*mm-(y+h)*mm, w*mm, h*mm, stroke=1, fill=0)

    def wrap(text, x, y, maxw, size=5.3, face=None, leading=2.5, maxlines=3):
        face = face or font
        words = simpleSplit(esc(text), face, size, maxw*mm)
        c.setFont(face, size)
        for j, part in enumerate(words[:maxlines]):
            c.drawString(x*mm, H*mm-(y+j*leading)*mm, part)

    # Верхние реквизиты — без заливок, как в исходной унифицированной форме.
    x_label, x_val, x_end = 10, 37, 222
    top_rows = [
        ("Грузоотправитель", supplier_full),
        ("Грузополучатель", buyer_full),
        ("Поставщик", supplier_full),
        ("Плательщик", buyer_full),
        ("Основание", f"Счёт № {doc_no}"),
    ]
    y0, row_h = 15, 9.3
    for i, (label, value) in enumerate(top_rows):
        y = y0 + i*row_h
        txt(x_label, y+3.2, label, 6.0)
        wrap(value, x_val, y+2.5, x_end-x_val-2, 5.5, leading=2.4, maxlines=2)
        line(x_val, y+7.2, x_end, y+7.2, 0.3)

    # Коды формы справа.
    txt(278, 7, "Код", 5.5, align="center")
    txt(250, 17, "Форма по ОКУД", 5.2, align="right")
    txt(250, 26, "по ОКПО", 5.2, align="right")
    txt(250, 35, "Вид деятельности по ОКПД", 5.2, align="right")
    txt(250, 44, "по ОКПО", 5.2, align="right")
    txt(250, 53, "по ОКПО", 5.2, align="right")
    rect(263, 8, 25, 45)
    for yy in [17, 26, 35, 44]:
        line(263, yy, 288, yy)
    txt(275.5, 24, "2019777673", 5.5, align="center")
    txt(275.5, 42, "2019777673", 5.5, align="center")
    txt(275.5, 51, "2010059549", 5.5, align="center")

    # Заголовок и блок номера/даты/транспортной накладной.
    txt(66, 73, "Товарная накладная", 14, bold, align="center")
    rect(107, 63, 73, 12)
    line(143.5, 63, 143.5, 75)
    txt(125.2, 67.0, "Номер документа", 5.5, align="center")
    txt(161.8, 67.0, "Дата составления", 5.5, align="center")
    txt(125.2, 73.1, doc_no, 6.0, align="center")
    txt(161.8, 73.1, date.strftime("%d.%m.%Y"), 6.0, align="center")
    # Надпись находится над своим блоком, а не поверх его рамки.
    txt(255.5, 57.5, "Транспортная накладная", 5.6, align="center")
    rect(223, 60, 65, 16)
    line(223, 68, 288, 68)
    line(263, 60, 263, 76)
    txt(243, 65.0, "номер", 5.0, align="center")
    txt(243, 73.0, "дата", 5.0, align="center")
    txt(255.5, 79.5, "Вид операции: __________________", 4.8, align="center")

    # Табличная часть ТОРГ-12. Вертикали строятся по группам заголовков,
    # а в строках товаров и итогов присутствуют границы всех 15 колонок.
    xs = [10, 25, 84, 92, 111, 123, 138, 148, 158, 180, 199, 221, 235, 250, 263, 288]
    y_top, y_h1, y_h2, y_h3, y_body = 82, 90, 96, 101, 107
    # Рисуем сетку сегментами: вертикали в объединённых заголовках не продолжаются
    # через ячейки, которые по форме ТОРГ-12 должны оставаться объединёнными.
    rect(xs[0], y_top, xs[-1]-xs[0], y_body-y_top)
    line(xs[1], y_top, xs[1], y_body)   # № по порядку / товар
    line(xs[2], y_top, xs[2], y_body)   # товар / единица измерения
    line(xs[3], y_h2, xs[3], y_body)    # код / наименование единицы
    line(xs[4], y_top, xs[4], y_body)   # единица измерения / упаковка
    line(xs[5], y_top, xs[5], y_body)   # упаковка / количество
    line(xs[6], y_h1, xs[6], y_body)    # количество: в одном месте / мест, штук
    line(xs[7], y_top, xs[7], y_body)   # количество / масса брутто
    line(xs[8], y_top, xs[8], y_body)   # масса брутто / количество нетто
    line(xs[9], y_top, xs[9], y_body)   # количество нетто / цена
    line(xs[10], y_top, xs[10], y_body)
    line(xs[11], y_top, xs[11], y_body) # сумма без НДС / НДС
    line(xs[12], y_h1, xs[12], y_body)  # НДС: ставка / сумма
    line(xs[13], y_top, xs[13], y_body) # НДС / сумма с НДС
    line(xs[14], y_h1, xs[14], y_body)  # сумма с НДС: отдельные значения в строках данных
    # Горизонтали заголовка рисуем отдельными сегментами с учётом объединённых ячеек.
    # В колонке № по порядку ячейка объединена по высоте, поэтому линии там нет.
    # В колонке «Товар» нужны верхняя и нижняя границы подзаголовка, но не
    # промежуточная линия, проходящая через многострочное описание.
    line(xs[1], y_h1, xs[2], y_h1)
    line(xs[2], y_h1, xs[-1], y_h1)
    line(xs[2], y_h2, xs[-1], y_h2)
    line(xs[1], y_h3, xs[2], y_h3)
    line(xs[2], y_h3, xs[-1], y_h3)

    # Крупные заголовки расположены внутри своих объединённых ячеек.
    txt((xs[0]+xs[1])/2, 85.2, "Номер по", 4.8, align="center")
    txt((xs[0]+xs[1])/2, 88.0, "порядку", 4.8, align="center")
    txt((xs[1]+xs[2])/2, 85.8, "Товар", 5.2, align="center")
    txt((xs[1]+xs[2])/2, 94.0, "наименование, характеристика, сорт, артикул", 4.1, align="center")
    txt((xs[1]+xs[2])/2, 99.2, "товара", 4.5, align="center")
    txt((xs[2]+xs[4])/2, 85.7, "Единица измерения", 4.7, align="center")
    txt((xs[2]+xs[3])/2, 99.2, "код", 4.5, align="center")
    txt((xs[3]+xs[4])/2, 99.2, "наименование", 4.0, align="center")
    txt((xs[4]+xs[5])/2, 85.2, "Вид", 4.8, align="center")
    txt((xs[4]+xs[5])/2, 88.0, "упаковки", 4.8, align="center")
    txt((xs[5]+xs[7])/2, 85.5, "Количество", 4.7, align="center")
    txt((xs[5]+xs[6])/2, 94.0, "в одном", 4.2, align="center")
    txt((xs[5]+xs[6])/2, 98.0, "месте", 4.2, align="center")
    txt((xs[6]+xs[7])/2, 94.0, "мест,", 4.2, align="center")
    txt((xs[6]+xs[7])/2, 98.0, "штук", 4.2, align="center")
    txt((xs[7]+xs[8])/2, 85.2, "Масса", 4.5, align="center")
    txt((xs[7]+xs[8])/2, 88.0, "брутто", 4.5, align="center")
    txt((xs[8]+xs[9])/2, 85.2, "Количество", 4.4, align="center")
    txt((xs[8]+xs[9])/2, 88.0, "(масса нетто)", 4.0, align="center")
    txt((xs[9]+xs[10])/2, 86.0, "Цена, руб. коп.", 4.4, align="center")
    txt((xs[10]+xs[11])/2, 85.0, "Сумма без учёта", 4.2, align="center")
    txt((xs[10]+xs[11])/2, 88.0, "НДС, руб. коп.", 4.2, align="center")
    txt((xs[11]+xs[13])/2, 85.5, "НДС", 4.8, align="center")
    txt((xs[11]+xs[12])/2, 94.0, "ставка, %", 4.1, align="center")
    txt((xs[12]+xs[13])/2, 94.0, "сумма, руб.", 4.0, align="center")
    txt((xs[12]+xs[13])/2, 98.0, "коп.", 4.0, align="center")
    txt((xs[13]+xs[15])/2, 85.0, "Сумма с учётом", 4.2, align="center")
    txt((xs[13]+xs[15])/2, 88.0, "НДС, руб. коп.", 4.2, align="center")
    for i, x in enumerate(xs[:-1]):
        txt((x+xs[i+1])/2, 104.7, str(i+1), 4.6, align="center")

    # Строки товаров. НДС — 22%, как в приложенном образце; сумма расчёта трактуется как сумма с НДС.
    row_y = y_body
    item_heights = []
    for r in rows:
        label = esc(r.get("name"))
        if r.get("sku"):
            label += f" (Артикул: {esc(r.get('sku'))})"
        if r.get("color"):
            label += f", {esc(r.get('color'))}"
        wrapped = simpleSplit(label, font, 5.0, (xs[3]-xs[1]-2)*mm)
        h = max(8.5, min(15.0, len(wrapped)*2.5+3.5))
        item_heights.append(h)
    # If many items, reduce row heights to retain the original one-page form.
    available = 43.0
    if sum(item_heights) > available:
        scale = available / sum(item_heights)
        item_heights = [max(5.5, h*scale) for h in item_heights]
    for i, (r, h) in enumerate(zip(rows, item_heights), 1):
        line(xs[0], row_y+h, xs[-1], row_y+h)
        for x in xs[1:-1]:
            line(x, row_y, x, row_y+h)
        total_inc = float(r["amount"])
        net = round(total_inc / 1.22, 2)
        vat = round(total_inc-net, 2)
        txt((xs[0]+xs[1])/2, row_y+h/2+1.5, str(i), 5.2, align="center")
        label = esc(r.get("name"))
        if r.get("sku"):
            label += f" (Артикул: {esc(r.get('sku'))})"
        if r.get("color"):
            label += f", {esc(r.get('color'))}"
        wrap(label, xs[1]+1.5, row_y+3, xs[2]-xs[1]-3, 4.7, leading=2.5, maxlines=max(1, int(h/2.5)))
        unit = esc(r.get("unit") or "шт.")
        okei = "006" if unit.lower() in ("м", "м.", "метр", "метры") else ("796" if unit.lower() in ("шт", "шт.") else "")
        txt((xs[3]+xs[4])/2, row_y+h/2+1.5, okei, 5.0, align="center")
        txt((xs[4]+xs[5])/2, row_y+h/2+1.5, unit, 5.0, align="center")
        txt((xs[9]+xs[10])/2, row_y+h/2+1.5, f"{float(r['quantity']):g}", 5.0, align="center")
        txt((xs[10]+xs[11])/2, row_y+h/2+1.5, money(net/float(r["quantity"]) if r["quantity"] else 0), 4.8, align="center")
        txt((xs[11]+xs[12])/2, row_y+h/2+1.5, money(net), 4.8, align="center")
        txt((xs[12]+xs[13])/2, row_y+h/2+1.5, "22", 4.8, align="center")
        txt((xs[13]+xs[14])/2, row_y+h/2+1.5, money(vat), 4.8, align="center")
        txt((xs[14]+xs[15])/2, row_y+h/2+1.5, money(total_inc), 4.8, align="center")
        row_y += h

    # Итоговая строка.
    line(xs[0], row_y+5.5, xs[-1], row_y+5.5)
    txt((xs[1]+xs[6])/2, row_y+3.6, "Всего по накладной", 5.2, bold, align="center")
    qty_total = sum(float(r["quantity"]) for r in rows)
    inc_total = round(sum(float(r["amount"]) for r in rows), 2)
    net_total = round(inc_total/1.22, 2)
    vat_total = round(inc_total-net_total, 2)
    txt((xs[9]+xs[10])/2, row_y+3.6, f"{qty_total:g}", 5.0, align="center")
    txt((xs[10]+xs[11])/2, row_y+3.6, money(net_total/qty_total if qty_total else 0), 4.8, align="center")
    txt((xs[11]+xs[12])/2, row_y+3.6, money(net_total), 4.8, align="center")
    txt((xs[12]+xs[13])/2, row_y+3.6, "22", 4.8, align="center")
    txt((xs[13]+xs[14])/2, row_y+3.6, money(vat_total), 4.8, align="center")
    txt((xs[14]+xs[15])/2, row_y+3.6, money(inc_total), 4.8, align="center")

    # Нижняя часть формы: строки приложения, суммы прописью и подписи.
    y = row_y+10
    # Подгоняем нижний блок под высоту листа: печати и даты не должны обрезаться.
    footer_scale = min(1.0, max(0.55, (198.0-y)/81.0))
    def fy(offset):
        return y + offset * footer_scale
    txt(10, fy(2), "Товарная накладная имеет приложение на", 5.2)
    line(65, fy(2.5), 170, fy(2.5))
    txt(171, fy(2), "листах и содержит", 5.2)
    line(197, fy(2.5), 219, fy(2.5))
    txt(220, fy(2), "порядковых номеров записей.", 5.2)
    txt(10, fy(11), "Всего мест", 5.2)
    line(29, fy(11.5), 130, fy(11.5))
    txt(76, fy(14), "(прописью)", 3.8, align="center")
    txt(152, fy(11), "Масса груза (нетто)", 5.2)
    line(188, fy(11.5), 287, fy(11.5))
    txt(220, fy(14), "(прописью)", 3.8, align="center")
    txt(152, fy(20), "Масса груза (брутто)", 5.2)
    line(188, fy(20.5), 287, fy(20.5))
    txt(220, fy(23), "(прописью)", 3.8, align="center")
    txt(10, fy(30), "Приложение (паспорта, сертификаты и т.п.) на", 5.2)
    line(83, fy(30.5), 134, fy(30.5))
    txt(135, fy(30), "листах", 5.2)
    txt(152, fy(30), "По доверенности №", 5.2)
    line(182, fy(30.5), 205, fy(30.5))
    txt(207, fy(30), "от «____» __________ года", 5.2)
    txt(10, fy(39), "Всего отпущено на сумму", 5.2)
    amount_words = f"{money(inc_total)} руб. 00 коп."
    line(45, fy(39.5), 130, fy(39.5))
    txt(46, fy(39), amount_words, 5.0)
    txt(10, fy(48), "Отпуск груза разрешил", 5.2)
    line(39, fy(48.5), 69, fy(48.5))
    txt(54, fy(51), "(должность)", 3.7, align="center")
    line(71, fy(48.5), 102, fy(48.5))
    txt(86, fy(51), "(подпись)", 3.7, align="center")
    line(104, fy(48.5), 133, fy(48.5))
    txt(118, fy(51), "(расшифровка подписи)", 3.4, align="center")
    txt(10, fy(57), "Главный (старший) бухгалтер", 5.2)
    line(66, fy(57.5), 96, fy(57.5))
    txt(81, fy(60), "(подпись)", 3.7, align="center")
    line(98, fy(57.5), 127, fy(57.5))
    txt(112, fy(60), "(расшифровка подписи)", 3.4, align="center")
    txt(10, fy(66), "Отпуск груза произвёл", 5.2)
    line(39, fy(66.5), 69, fy(66.5))
    txt(54, fy(69), "(должность)", 3.7, align="center")
    line(71, fy(66.5), 102, fy(66.5))
    txt(86, fy(69), "(подпись)", 3.7, align="center")
    line(104, fy(66.5), 133, fy(66.5))
    txt(118, fy(69), "(расшифровка подписи)", 3.4, align="center")
    txt(36, fy(80), "М.П.", 5.2)
    txt(65, fy(80), "« _____ » ______________________ _____ года", 5.0)

    # Правая колонка подписей и получения груза.
    line(150, fy(26), 150, fy(81))
    txt(153, fy(39), "выданной ______________________________________________", 5.2)
    line(153, fy(45), 288, fy(45))
    line(153, fy(51), 288, fy(51))
    txt(153, fy(57), "Груз принял", 5.2)
    line(192, fy(57.5), 222, fy(57.5))
    txt(207, fy(60), "(должность)", 3.7, align="center")
    line(224, fy(57.5), 254, fy(57.5))
    txt(239, fy(60), "(подпись)", 3.7, align="center")
    line(256, fy(57.5), 288, fy(57.5))
    txt(272, fy(60), "(расшифровка подписи)", 3.3, align="center")
    txt(153, fy(66), "Груз получил", 5.2)
    line(192, fy(66.5), 222, fy(66.5))
    txt(207, fy(69), "(должность)", 3.7, align="center")
    line(224, fy(66.5), 254, fy(66.5))
    txt(239, fy(69), "(подпись)", 3.7, align="center")
    line(256, fy(66.5), 288, fy(66.5))
    txt(272, fy(69), "(расшифровка подписи)", 3.3, align="center")
    txt(179, fy(80), "М.П.", 5.2)
    txt(206, fy(80), "« _____ » __________________ _____ года", 4.8)

    # Номер/дата листа внизу, как в образце.
    txt(10, 205, f"Товарная накладная №{doc_no} от {date.strftime('%d.%m.%Y')}. Лист 1 из 1", 4.2)
    c.showPage()
    c.save()
    return out.getvalue()


def _make_invoice_pdf(deal, client, calc, requisites):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Flowable
    from reportlab.lib.utils import ImageReader
    from PIL import Image as PILImage
    font,bold=_pdf_font_setup()
    out=io.BytesIO()
    doc=SimpleDocTemplate(out,pagesize=A4,rightMargin=13*mm,leftMargin=13*mm,topMargin=2*mm,bottomMargin=12*mm,title=f"Счёт №{_deal_doc_number(deal)}")
    styles=getSampleStyleSheet()
    brand=colors.HexColor("#bc1661")
    title=ParagraphStyle("InvTitle",parent=styles["Title"],fontName=bold,fontSize=13,leading=16,alignment=TA_CENTER,spaceAfter=8*mm,textColor=colors.HexColor("#202833"))
    body=ParagraphStyle("InvBody",parent=styles["BodyText"],fontName=font,fontSize=8,leading=10,spaceAfter=1.3*mm,textColor=colors.HexColor("#343D4A"))
    small=ParagraphStyle("InvSmall",parent=body,fontSize=6.7,leading=8)
    cell=ParagraphStyle("InvCell",parent=small,fontSize=6.8,leading=8)
    head=ParagraphStyle("InvHead",parent=cell,fontName=bold,alignment=TA_CENTER,textColor=colors.white)
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
    calc_name=str(calc.get("name") or _calculation_display_name(deal,calc))
    suffix=calc_name.replace("Расчёт", "", 1).strip()
    # В назначении платежа и номерах документов используем только обычный дефис.
    suffix=suffix.replace("—", "-").replace("–", "-").replace("−", "-")
    invoice_no=f"Счёт {suffix} от {date.strftime('%d.%m.%Y')}"

    # Images are expected in the repository root next to crm.py. Try common deployment paths.
    def _asset_image(filename, width_mm, max_height_mm=None):
        candidates=[os.path.join(os.getcwd(), filename), os.path.join(os.path.dirname(os.path.abspath(__file__)), filename), os.path.join("assets", filename), os.path.join("static", filename)]
        path=next((x for x in candidates if os.path.isfile(x)), None)
        if not path:
            return None
        try:
            im=Image(path)
            im.drawWidth=width_mm*mm
            ratio=im.imageHeight / float(im.imageWidth or 1)
            im.drawHeight=im.drawWidth*ratio
            if max_height_mm and im.drawHeight > max_height_mm*mm:
                scale=(max_height_mm*mm)/im.drawHeight
                im.drawWidth*=scale; im.drawHeight*=scale
            im.hAlign="LEFT"
            return im
        except Exception:
            return None

    logo=_asset_image("Логотип iPlinth с розовым шевроном-1.png", 157.5, 51)
    # Платёжный QR по формату ST00012 (ГОСТ Р 56042-2014): реквизиты получателя,
    # назначение и точная сумма счёта. Это QR для перевода по банковским реквизитам,
    # а не QR СБП/эквайринга.
    from reportlab.graphics.barcode.qr import QrCodeWidget
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics import renderPDF
    class _PaymentQR(Flowable):
        def __init__(self, payload, size=25*mm):
            super().__init__(); self.payload=payload; self.width=size; self.height=size
        def draw(self):
            widget=QrCodeWidget(self.payload)
            x1,y1,x2,y2=widget.getBounds()
            drawing=Drawing(self.width,self.height,transform=[self.width/max(x2-x1,1),0,0,self.height/max(y2-y1,1),0,0])
            drawing.add(widget)
            renderPDF.draw(drawing,self.canv,0,0)
    amount_kopecks=int(round(total*100))
    qr_payload=(
        "ST00012|Name=ИП Фазлов Дамир Ибрагимович"
        "|PersonalAcc=40802810800000438327"
        "|BankName=ООО ОЗОН Банк|BIC=044525068"
        "|CorrespAcc=30101810645374525068"
        "|PayeeINN=731701704975"
        f"|Purpose={invoice_no}|Sum={amount_kopecks}"
    )
    payment_qr=_PaymentQR(qr_payload, 25*mm)
    header_cells=[[logo or Paragraph("iPlinth",body), payment_qr]]
    header=Table(header_cells,colWidths=[145*mm,30*mm],rowHeights=[52*mm],hAlign="LEFT")
    header.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(1,0),(1,0),"RIGHT"),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    flow=[header,Spacer(1,5*mm),Paragraph(html.escape(invoice_no),title),Spacer(1,2*mm),
          Paragraph(
              f"Получатель: {html.escape('ИП Фазлов Дамир Ибрагимович' if requisites.get('payer_type') == 'person' else 'ИП Фазлов Дамир Ибрагимович, ИНН 731701704975, ОГРНИП 322169000220971, р/с 40802810800000438327, в банке ООО \"ОЗОН Банк\", БИК 044525068, к/с 30101810645374525068')}", body),
          Paragraph(f"Плательщик: {html.escape(payer_details)}",body),Spacer(1,3*mm)]
    data=[[Paragraph(x,head) for x in ["№","Название товара или услуги","Кол-во","Ед. изм.","Цена","НДС","Сумма"]]]
    for i,r in enumerate(rows,1):
        name=f"<b>{html.escape(str(r['name']))}</b><br/><font size='6'>(Артикул: {html.escape(str(r['sku']))})</font>"
        if r['color']: name += f"<br/><font size='6'>Цвет/RAL: {html.escape(str(r['color']))}</font>"
        data.append([Paragraph(str(i),cell),Paragraph(name,cell),Paragraph(f"{r['quantity']:g}",cell),Paragraph(html.escape(str(r['unit'])),cell),Paragraph(_money(r['after']),cell),Paragraph("Без НДС",cell),Paragraph(_money(r['amount']),cell)])
    if delivery:
        data.append([Paragraph(str(len(rows)+1),cell),Paragraph("Доставка",cell),Paragraph("1",cell),Paragraph("усл.",cell),Paragraph(_money(delivery),cell),Paragraph("Без НДС",cell),Paragraph(_money(delivery),cell)])
    tbl=Table(data,colWidths=[9*mm,72*mm,17*mm,18*mm,24*mm,18*mm,27*mm],repeatRows=1,hAlign="LEFT")
    tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),brand),("GRID",(0,0),(-1,-1),0.4,brand),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    _line_count=len(rows)+(1 if delivery else 0)
    _count_mod=_line_count%100; _count_last=_line_count%10
    _count_word="наименование" if _count_last==1 and _count_mod!=11 else ("наименования" if 2<=_count_last<=4 and not 12<=_count_mod<=14 else "наименований")
    flow += [tbl,Spacer(1,3*mm),Paragraph(f"Всего {_line_count} {_count_word} на сумму {_number_to_russian_words(int(total))} {int(round((total-int(total))*100)):02d} копеек.",body),Paragraph(f"<b>Итог к оплате: {_money(total)} ₽</b> &nbsp;&nbsp; Без НДС",ParagraphStyle("InvTotal",parent=body,fontName=bold,fontSize=10,alignment=TA_RIGHT,textColor=brand)),Paragraph(f"Срок оплаты: Не позднее {due.strftime('%d.%m.%Y')} г.",body),Spacer(1,8*mm)]

    stamp=_asset_image("печать.png", 35, 28)
    signature=_asset_image("подпись.png", 35, 18)
    # Put signature on top of the stamp while keeping both aligned in one row.
    class _StampSignature(Flowable):
        def __init__(self, stamp_img, signature_img):
            super().__init__(); self.stamp_img=stamp_img; self.signature_img=signature_img
            self.width=85*mm; self.height=30*mm
        def draw(self):
            if self.stamp_img:
                self.canv.saveState(); self.canv.translate(0,0); self.canv.drawImage(self.stamp_img.filename, 0, 0, width=self.stamp_img.drawWidth, height=self.stamp_img.drawHeight, preserveAspectRatio=True, mask='auto'); self.canv.restoreState()
            if self.signature_img:
                sw=self.signature_img.drawWidth; sh=self.signature_img.drawHeight
                # Signature overlaps the stamp, slightly above its centre.
                self.canv.drawImage(self.signature_img.filename, -8*mm, 7*mm, width=sw, height=sh, preserveAspectRatio=True, mask='auto')
    sign=Table([[Paragraph("Поставщик: ИП Фазлов Дамир Ибрагимович<br/>Подпись и печать",body),_StampSignature(stamp,signature)]],colWidths=[90*mm,90*mm])
    sign.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)]))
    flow.append(sign)
    doc.build(flow)
    return out.getvalue(), due.strftime("%d.%m.%Y")


def _save_generated_document(deal, pdf_bytes, filename, kind, calc, extra=None):
    """Надёжно сохраняет PDF и прикрепляет его к актуальной записи сделки."""
    deal_id = deal.get("id")
    current_deal = get_deal_by_id(deal_id) or deal
    safe_name = re.sub(r"[^\wА-Яа-яЁё№(). —-]+", "_", filename).strip().replace("/", "_")
    digest = hashlib.sha256(pdf_bytes).hexdigest()
    path = ""
    if YANDEX_TOKEN:
        remote_name = f"deal_{deal_id}_{uuid.uuid4().hex[:8]}_{safe_name}"
        if upload_file_to_yandex(pdf_bytes, remote_name):
            path = f"CRM_NE_TROGAT/uploads/{remote_name}"
    if not path:
        os.makedirs("uploads", exist_ok=True)
        local_name = f"deal_{deal_id}_{uuid.uuid4().hex[:8]}_{safe_name}"
        path = os.path.join("uploads", local_name)
        with open(path, "wb") as f:
            f.write(pdf_bytes)
    created_at = now_str()
    file_obj = {"file_path": path, "file_name": safe_name, "file_hash": digest,
                "description": f"{kind} · {calc.get('name', 'Расчёт')}",
                "document_type": kind, "calculation_id": str(calc.get("id")), "created_at": created_at}
    current_deal.setdefault("deal_files", []).append(file_obj)
    doc_obj = {"id": uuid.uuid4().hex, "kind": kind, "file_name": safe_name,
               "file_hash": digest, "calculation_id": str(calc.get("id")),
               "calculation_name": calc.get("name", ""), "created_at": created_at,
               "payer": copy.deepcopy(extra or {}),
               "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii")}
    current_deal.setdefault("generated_documents", []).append(doc_obj)
    current_deal["last_modified"] = created_at
    save_data(st.session_state.crm_store)
    return file_obj


def _ensure_paid_deal_torg12(deal):
    """Создаёт ТОРГ-12 один раз после полной оплаты на основании последнего расчёта."""
    current = get_deal_by_id(deal.get("id")) or deal
    calculations = [c for c in (current.get("calculations", []) or []) if not c.get("deleted") and c.get("items")]
    if not calculations:
        return False
    calc = max(calculations, key=lambda c: str(c.get("updated_at", c.get("created_at", ""))))
    if any(doc.get("kind") == "Товарная накладная ТОРГ-12" and str(doc.get("calculation_id", "")) == str(calc.get("id"))
           for doc in (current.get("generated_documents", []) or [])):
        return False
    client = get_client_by_id(current.get("client_id")) or {}
    pdf = _make_torg12_pdf(current, client, calc)
    if isinstance(pdf, tuple):
        pdf = pdf[0]
    filename = f"ТОРГ-12 №{_deal_doc_number(current)} от {moscow_now().strftime('%d.%m.%Y')}.pdf"
    _save_generated_document(current, pdf, filename, "Товарная накладная ТОРГ-12", calc)
    return True


def _open_pdf_link(pdf_bytes, filename, key):
    b64=base64.b64encode(pdf_bytes).decode("ascii")
    st.session_state[key]={"data":b64,"filename":filename}


@_crm_dialog("Реквизиты плательщика", width="large")
def client_requisites_view_dialog(client_id, return_to_invoice=False, requisite_id=None):
    """Просмотр сохранённых реквизитов без редактирования; всегда читает актуальную запись из CRM."""
    client = get_client_by_id(client_id)
    if not client:
        st.error("Клиент не найден")
        return
    req = next((r for r in (client.get("requisites", []) or [])
                if str(r.get("id")) == str(requisite_id) and not r.get("deleted")), None)
    if not req:
        st.error("Сохранённые реквизиты не найдены. Возможно, запись была удалена.")
        if st.button("Закрыть", key=f"req_view_missing_close_{client_id}_{requisite_id}"):
            st.session_state.pop("dialog_client_requisites_view", None)
            if return_to_invoice:
                inv = st.session_state.get("dialog_invoice_request") or {}
                invoice_document_dialog(inv.get("deal_id"), inv.get("calc_id"))
            else:
                _pop_dialog_return()
                st.rerun()
        return

    close_key = f"req_view_close_{client_id}_{requisite_id}_{'invoice' if return_to_invoice else 'client'}"
    with st.container(key=f"{close_key}_row"):
        sp, cc = st.columns([20, 1])
        with cc:
            if st.button("✕", key=close_key, use_container_width=True):
                st.session_state.pop("dialog_client_requisites_view", None)
                if return_to_invoice:
                    inv = st.session_state.get("dialog_invoice_request") or {}
                    invoice_document_dialog(inv.get("deal_id"), inv.get("calc_id"))
                else:
                    _pop_dialog_return()
                    st.rerun()
    st.caption("Сохранённые реквизиты · режим просмотра")
    labels = [
        ("legal_name", "Наименование юр. лица / ФИО плательщика"),
        ("payer_type", "Тип плательщика"),
        ("inn", "ИНН"), ("kpp", "КПП"), ("address", "Юридический адрес"),
        ("bank_name", "Банк"), ("bik", "БИК"), ("corr_account", "Корреспондентский счёт"),
        ("settlement_account", "Расчётный счёт"), ("phone", "Телефон"), ("email", "Email")]
    payer_labels = {"company": "Юридическое лицо (ООО)", "ip": "Индивидуальный предприниматель", "person": "Физическое лицо"}
    for i in range(0, len(labels), 2):
        cols = st.columns(2)
        for col, (field, label) in zip(cols, labels[i:i+2]):
            value = req.get(field, "") or "—"
            if field == "payer_type":
                value = payer_labels.get(str(value), str(value))
            with col:
                st.text_input(label, value=str(value), key=f"req_view_{client_id}_{requisite_id}_{field}_{'invoice' if return_to_invoice else 'client'}", disabled=True)
    if req.get("created_at"):
        st.caption(f"Созданы: {req.get('created_at')}" + (f" · Обновлены: {req.get('updated_at')}" if req.get("updated_at") else ""))


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
    # При явном открытии существующей записи заново загружаем сохранённые значения в поля Streamlit.
    if st.session_state.pop(f"{key}_force_load", False):
        for _field_name, _ in fields:
            st.session_state.pop(f"{key}_{_field_name}", None)
        st.session_state.pop(dirty, None)
        st.session_state.pop(warning, None)
    for k,_ in fields:
        if f"{key}_{k}" not in st.session_state:
            default_value = (existing_req or {}).get(k, "company" if k == "payer_type" else "")
            if k == "email" and not str(default_value or "").strip():
                _initial_payer_type = (existing_req or {}).get("payer_type", "company")
                if _initial_payer_type == "person":
                    default_value = str(client.get("email", "") or "").strip()
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
    _payer_type_key = f"{key}_payer_type"
    def _payer_type_changed():
        st.session_state[dirty] = True
        if st.session_state.get(_payer_type_key) == "person":
            # Для физлица используем ФИО и email из карточки клиента, если они заполнены.
            client_name = str(client.get("name", "") or "").strip()
            client_email = str(client.get("email", "") or "").strip()
            if client_name:
                st.session_state[f"{key}_legal_name"] = client_name
            if client_email:
                st.session_state[f"{key}_email"] = client_email

    st.selectbox("Тип плательщика",["company","ip","person"],format_func=lambda x:{"company":"Юридическое лицо (ООО)","ip":"Индивидуальный предприниматель","person":"Физическое лицо"}[x],key=_payer_type_key,on_change=_payer_type_changed)
    _is_person_payer = st.session_state.get(_payer_type_key) == "person"
    if _is_person_payer:
        st.text_input("ФИО плательщика",key=f"{key}_legal_name",on_change=lambda:st.session_state.__setitem__(dirty,True))
        st.text_input("Email (обязательно)",key=f"{key}_email",on_change=lambda:st.session_state.__setitem__(dirty,True))
    else:
        c1,c2=st.columns(2)
        with c1:
            st.text_input("Наименование юр. лица / ФИО плательщика",key=f"{key}_legal_name",on_change=lambda:st.session_state.__setitem__(dirty,True))
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
        payer_type = st.session_state.get(f"{key}_payer_type")
        email = str(st.session_state.get(f"{key}_email", "") or "").strip()
        if not name or (payer_type != "person" and not inn):
            st.error("Укажи ФИО физического лица либо наименование плательщика и ИНН для организации/ИП.")
        elif payer_type == "person" and not email:
            st.error("Для физического лица Email обязателен для заполнения.")
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
            # Сохраняем реквизиты и затем проверяем результат уже в актуальном
            # хранилище сессии: при конфликте с другой сессией трёхстороннее
            # слияние могло оставить последнюю версию клиента без нашей записи.
            _saved_req_id = str(req.get("id", ""))
            save_data(st.session_state.crm_store)
            _saved_client = get_client_by_id(client_id)
            _saved_reqs = (_saved_client or {}).get("requisites", []) or []
            _saved_record = next((r for r in _saved_reqs if str(r.get("id", "")) == _saved_req_id), None)
            _needs_repair = _saved_record is None or any(
                str((_saved_record or {}).get(_field, "") or "") != str(req.get(_field, "") or "")
                for _field, _ in fields
            )
            if _saved_client is not None and _saved_req_id and _needs_repair:
                # После сохранения проверяем не только наличие ID, но и все поля.
                # При конфликтном слиянии восстанавливаем значения записи реквизитов
                # в актуальном объекте клиента, не трогая другие данные CRM.
                if _saved_record is None:
                    _saved_record = copy.deepcopy(req)
                    _saved_client.setdefault("requisites", []).append(_saved_record)
                else:
                    for _field, _ in fields:
                        _saved_record[_field] = copy.deepcopy(req.get(_field, ""))
                    for _meta in ("created_at", "created_by", "updated_at", "updated_by", "deleted"):
                        if _meta in req:
                            _saved_record[_meta] = copy.deepcopy(req[_meta])
                _saved_client["last_modified"] = now_str()
                save_data(st.session_state.crm_store)
                _verified_client = get_client_by_id(client_id)
                _verified_record = next((r for r in ((_verified_client or {}).get("requisites", []) or []) if str(r.get("id", "")) == _saved_req_id), None)
                if _verified_record is None or any(
                    str(_verified_record.get(_field, "") or "") != str(req.get(_field, "") or "")
                    for _field, _ in fields
                ):
                    st.error("Не удалось подтвердить сохранение всех полей реквизитов в базе. Окно оставлено открытым — попробуй сохранить ещё раз.")
                    return
            st.session_state.pop("dialog_client_requisites_client_id",None)
            st.session_state.pop("dialog_client_requisites_return_to_invoice",None)
            for k,_ in fields: st.session_state.pop(f"{key}_{k}",None)
            st.session_state.pop(dirty,None); st.session_state.pop(warning,None); st.session_state.pop(f"{key}_save_requested",None)
            st.toast("Реквизиты сохранены",icon="✅")
            if return_to_invoice:
                inv=st.session_state.get("dialog_invoice_request") or {}
                inv["selected_requisite_id"]=req["id"]
                st.session_state["dialog_invoice_request"]=inv
                if inv.get("deal_id") is not None and inv.get("calc_id") is not None:
                    st.session_state[f"invoice_req_select_{inv.get('deal_id')}_{inv.get('calc_id')}"] = str(req["id"])
                invoice_document_dialog(inv.get("deal_id"),inv.get("calc_id"))
            else:
                _pop_dialog_return(); st.rerun()



# -------------------- Интеграция с Ozon Pay Acquiring --------------------
def _ozon_config():
    """Читает ключи Ozon Pay из [ozon] в Streamlit Secrets или env."""
    values = {}
    try:
        section = st.secrets.get("ozon", {})
        if hasattr(section, "items"):
            values = dict(section.items())
    except Exception:
        values = {}
    aliases = {
        "access_key": ("access_key", "token_id", "id_token", "accessKey"),
        "secret_key": ("secret_key", "secretKey"),
        "notification_secret_key": ("notification_secret_key", "notificationSecretKey"),
        "redirect_url": ("redirect_url", "redirectUrl"),
        "success_url": ("success_url", "successUrl"),
        "fail_url": ("fail_url", "failUrl"),
    }
    env = {
        "access_key": "OZON_ACCESS_KEY",
        "secret_key": "OZON_SECRET_KEY",
        "notification_secret_key": "OZON_NOTIFICATION_SECRET_KEY",
        "redirect_url": "OZON_REDIRECT_URL",
        "success_url": "OZON_SUCCESS_URL",
        "fail_url": "OZON_FAIL_URL",
    }
    result = {}
    for key, names in aliases.items():
        value = next((values.get(n) for n in names if values.get(n)), None) or os.environ.get(env[key], "")
        if value:
            result[key] = str(value).strip()
    result.setdefault("base_url", "https://payapi.ozon.ru")
    # В личном кабинете для токена пользователь указал iplinth.ru как URL после оплаты.
    result.setdefault("redirect_url", result.get("success_url") or "https://iplinth.ru/")
    return result


def _ozon_signature(*parts):
    import hashlib
    cfg = _ozon_config()
    secret = cfg.get("secret_key")
    if not secret:
        raise RuntimeError("Не настроен secret_key Ozon Pay. Добавьте [ozon].secret_key в Streamlit Secrets.")
    return hashlib.sha256(("".join("" if part is None else str(part) for part in parts) + secret).encode("utf-8")).hexdigest()


def _ozon_request(path, payload):
    cfg = _ozon_config()
    if not cfg.get("access_key") or not cfg.get("secret_key"):
        raise RuntimeError("Не настроены access_key и secret_key Ozon Pay в Streamlit Secrets.")
    url = cfg.get("base_url", "https://payapi.ozon.ru").rstrip("/") + "/" + path.lstrip("/")
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json", "Accept": "application/json"}, timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError(f"Не удалось связаться с Ozon Pay: {exc}") from exc
    try:
        body = response.json()
    except ValueError:
        body = {}
    if not response.ok:
        detail = body.get("message") or body.get("error") or body.get("code") or (response.text or "")[:300]
        extra = body.get("details")
        if extra:
            detail = f"{detail}; детали: {str(extra)[:500]}"
        raise RuntimeError(f"Ozon Pay вернул HTTP {response.status_code}" + (f": {detail}" if detail else ""))
    if isinstance(body, dict) and body.get("code") not in (None, 0, "0") and body.get("message"):
        detail = body.get("message")
        if body.get("details"):
            detail = f"{detail}; детали: {str(body.get('details'))[:500]}"
        raise RuntimeError(f"Ozon Pay: {detail}")
    return body


def _ozon_create_payment(deal, calc):
    cfg = _ozon_config()
    if not cfg.get("access_key") or not cfg.get("secret_key"):
        raise RuntimeError("Добавьте в Streamlit Secrets раздел [ozon] с access_key и secret_key.")
    total = round(float(_deal_calc_total(calc) or 0), 2)
    if total <= 0:
        raise ValueError("В расчёте нет положительной суммы для оплаты.")
    ext_id = "iplinth-" + uuid.uuid4().hex
    # Ozon Pay protobuf ожидает int64 в value; передаём сумму в копейках,
    # а не строку с десятичной точкой (например, 12,90 ₽ -> 1290).
    amount = {"currencyCode": "643", "value": str(int(round(total * 100)))}
    # По таблице подписей Ozon для createPayment: extId + accessKey + secretKey.
    sign = _ozon_signature(ext_id, cfg["access_key"])
    payload = {
        "accessKey": cfg["access_key"],
        "amount": amount,
        "extId": ext_id,
        "payType": "SBP",
        "redirectUrl": cfg.get("redirect_url") or "https://iplinth.ru/",
        "requestSign": sign,
        "ttl": 86400,
    }
    if cfg.get("notification_url"):
        payload["notificationUrl"] = cfg["notification_url"]
    response = _ozon_request("/v1/createPayment", payload)
    data = response.get("data", response) if isinstance(response, dict) else {}
    details = data.get("paymentDetails") or data.get("payment_details") or {}
    sbp = details.get("sbp") or {}
    payment_id = details.get("paymentId") or details.get("payment_id")
    payment_payload = sbp.get("payload") or details.get("payload") or data.get("redirectUrl") or data.get("paymentLink") or data.get("payLink")
    if not payment_id:
        raise RuntimeError("Ozon Pay не вернул paymentDetails.paymentId. Проверьте ответ API и статус токена.")
    if not payment_payload:
        raise RuntimeError("Платёж создан, но Ozon Pay не вернул SBP payload/ссылку. Идентификатор сохранён не был; проверьте ответ API в кабинете Ozon.")
    return {
        "kind": "payment_link", "bank": "Ozon Pay", "payment_id": str(payment_id),
        "ext_id": ext_id, "payment_link": str(payment_payload), "amount": total,
        "status": details.get("status") or "PAYMENT_NEW", "created_at": now_str(),
        "payment_method": "SBP", "ttl": 86400,
    }


def _ozon_refresh_status(record):
    cfg = _ozon_config()
    payment_id = str(record.get("payment_id") or "").strip()
    if not payment_id:
        raise RuntimeError("В записи Ozon Pay нет payment_id.")
    sign = _ozon_signature(payment_id, cfg.get("access_key", ""))
    response = _ozon_request("/v1/getPaymentDetails", {
        "accessKey": cfg["access_key"], "id": payment_id, "requestSign": sign,
    })
    data = response.get("data", response) if isinstance(response, dict) else {}
    items = data.get("items") or []
    statuses = [str(item.get("status", "")).upper() for item in items if isinstance(item, dict) and item.get("status")]
    if statuses:
        # Подтверждённая оплата важнее промежуточных операций.
        priority = ["PAYMENT_CONFIRMED", "PAYMENT_AUTHORIZED", "PAYMENT_PROCESSING", "PAYMENT_NEW", "PAYMENT_REJECTED", "PAYMENT_CANCELED"]
        status = next((candidate for candidate in priority if candidate in statuses), statuses[0])
        record["operations"] = items
    else:
        details = data.get("paymentDetails") or {}
        status = details.get("status") or data.get("status")
    if not status:
        raise RuntimeError("Ozon Pay не вернул статус платежа.")
    record["status"] = str(status)
    record["checked_at"] = now_str()
    return record


# -------------------- Интеграция с Точка.API --------------------
def _tochka_config():
    """Читает секреты интеграции из Streamlit Secrets или переменных окружения."""
    secret_values = {}
    try:
        section = st.secrets.get("tochka", {})
        if hasattr(section, "items"):
            secret_values = dict(section.items())
    except Exception:
        secret_values = {}
    env_names = {
        "token": "TOCHKA_TOKEN",
        "customer_code": "TOCHKA_CUSTOMER_CODE",
        "account_id": "TOCHKA_ACCOUNT_ID",
        "merchant_id": "TOCHKA_MERCHANT_ID",
        "tax_system_code": "TOCHKA_TAX_SYSTEM_CODE",
        "supplier_name": "TOCHKA_SUPPLIER_NAME",
        "supplier_inn": "TOCHKA_SUPPLIER_INN",
        "supplier_phone": "TOCHKA_SUPPLIER_PHONE",
        "redirect_url": "TOCHKA_REDIRECT_URL",
        "fail_redirect_url": "TOCHKA_FAIL_REDIRECT_URL",
        "base_url": "TOCHKA_BASE_URL",
    }
    result = {}
    for key, env_name in env_names.items():
        value = secret_values.get(key) or os.environ.get(env_name, "")
        if value:
            result[key] = str(value).strip()
    result.setdefault("base_url", "https://enter.tochka.com/uapi")
    # Данные поставщика совпадают с данными, уже используемыми в PDF-счёте CRM;
    # их можно переопределить в secrets.
    result.setdefault("supplier_name", "ИП Фазлов Дамир Ибрагимович")
    result.setdefault("supplier_inn", "731701704975")
    result.setdefault("supplier_phone", "+79003293300")
    return result


def _tochka_missing_config(required):
    cfg = _tochka_config()
    return [key for key in required if not cfg.get(key)]


def _tochka_request(method, path, payload=None, expect_pdf=False):
    cfg = _tochka_config()
    if not cfg.get("token"):
        raise RuntimeError("Не настроен токен Точка.API. Добавьте [tochka].token в Streamlit Secrets.")
    url = cfg["base_url"].rstrip("/") + "/" + path.lstrip("/")
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Accept": "application/pdf" if expect_pdf else "application/json",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    # Extend Requests' normal CA bundle with the official certificates stored
    # beside crm.py. Certificate verification stays enabled.
    _cert_root = Path(__file__).resolve().parent
    _custom_cert_paths = [
        _cert_root / "russian_trusted_root_ca_pem.crt",
        _cert_root / "russian_trusted_sub_ca_pem.crt",
    ]
    _existing_custom_certs = [p for p in _custom_cert_paths if p.is_file()]
    _verify_bundle = certifi.where()
    if _existing_custom_certs:
        _bundle_path = _cert_root / ".tochka_ca_bundle.pem"
        try:
            _bundle_is_current = _bundle_path.is_file() and all(
                _bundle_path.stat().st_mtime >= p.stat().st_mtime
                for p in _existing_custom_certs
            )
        except OSError:
            _bundle_is_current = False
        if not _bundle_is_current:
            with open(_bundle_path, "wb") as _bundle:
                with open(certifi.where(), "rb") as _default_ca:
                    _bundle.write(_default_ca.read())
                    _bundle.write(b"\n")
                for _cert_path in _existing_custom_certs:
                    with open(_cert_path, "rb") as _custom_ca:
                        _bundle.write(_custom_ca.read())
                        _bundle.write(b"\n")
        _verify_bundle = str(_bundle_path)
    try:
        response = requests.request(
            method, url, headers=headers, json=payload, timeout=30,
            verify=_verify_bundle,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Не удалось связаться с Точка.API: {exc}") from exc
    if not response.ok:
        detail = ""
        try:
            body = response.json()
            detail = str(body.get("message") or body.get("Message") or body.get("code") or "")
            errors = body.get("Errors") or body.get("errors") or []
            if errors and not detail:
                detail = "; ".join(str(x.get("message", "")) for x in errors[:2] if isinstance(x, dict))
        except Exception:
            detail = (response.text or "")[:350]
        raise RuntimeError(f"Точка.API вернул HTTP {response.status_code}" + (f": {detail}" if detail else ""))
    if expect_pdf:
        return response.content
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError("Точка.API вернул ответ в неожиданном формате.") from exc


def _tochka_data(response):
    return response.get("Data", response.get("data", response)) if isinstance(response, dict) else {}


def _tochka_check_connection():
    """Read-only smoke test: validates JWT access to customers and accounts endpoints.

    Does not create invoices, payment links, or any other bank operation.
    The response bodies are intentionally not shown in the UI because they can
    contain customer and banking details.
    """
    missing = _tochka_missing_config(["token", "customer_code", "account_id"])
    if missing:
        raise RuntimeError("Не заполнены параметры Точки в Streamlit Secrets: " + ", ".join(missing))
    _tochka_request("GET", "/open-banking/v1.0/customers")
    _tochka_request("GET", "/open-banking/v1.0/accounts")
    return True


def _tochka_unit(value):
    allowed = {"шт.", "тыс.шт.", "компл.", "пар.", "усл.ед.", "упак.", "услуга.", "пач.", "мин.", "ч.", "сут.", "г.", "кг.", "л.", "м.", "м2.", "м3.", "км.", "га.", "кВт.", "кВт.ч."}
    value = str(value or "").strip()
    aliases = {"м.п.": "м.", "пог. м": "м.", "пог.м": "м.", "м²": "м2.", "м2": "м2.", "м³": "м3.", "м3": "м3.", "усл.": "услуга.", "комплект": "компл.", "компл": "компл.", "шт": "шт."}
    value = aliases.get(value.lower(), value)
    return value if value in allowed else "шт."


def _tochka_invoice_number(deal, calc):
    calculations = deal.get("calculations", [])
    index = next((i + 1 for i, item in enumerate(calculations) if str(item.get("id")) == str(calc.get("id"))), 1)
    base = re.sub(r"[^0-9A-Za-zА-Яа-яЁё-]+", "-", str(_deal_doc_number(deal))).strip("-") or "CRM"
    suffix = moscow_now().strftime("%y%m%d%H%M%S")
    return f"{base[:20]}-{index}-{suffix}"[:40]


def _tochka_build_invoice_payload(deal, calc, requisites):
    cfg = _tochka_config()
    if requisites.get("payer_type") not in ("company", "ip"):
        raise ValueError("Точка.API не выставляет счёт по реквизитам физическому лицу. Для физлица используйте платёжную ссылку.")
    if not str(requisites.get("inn", "")).strip():
        raise ValueError("Для счёта в Точке нужен ИНН плательщика.")
    if not str(requisites.get("legal_name", "")).strip():
        raise ValueError("Укажите наименование организации или ФИО ИП.")
    rows = _calculation_rows(calc, st.session_state.crm_store.get("products", DEFAULT_PRODUCT_CATALOG))
    delivery = max(0.0, float(calc.get("delivery_amount", 0) or 0))
    positions = []
    for row in rows:
        if row["quantity"] <= 0:
            continue
        positions.append({
            "positionName": str(row["name"] or "Товар")[:256],
            "unitCode": _tochka_unit(row["unit"]),
            "ndsKind": "without_nds",
            "price": f'{row["after"]:.2f}',
            "quantity": f'{row["quantity"]:g}',
            "totalAmount": f'{row["amount"]:.2f}',
        })
    if delivery > 0:
        positions.append({
            "positionName": "Доставка",
            "unitCode": "услуга.",
            "ndsKind": "without_nds",
            "price": f"{delivery:.2f}",
            "quantity": "1",
            "totalAmount": f"{delivery:.2f}",
        })
    total = round(sum(float(p["totalAmount"]) for p in positions), 2)
    if not positions or total <= 0:
        raise ValueError("В расчёте нет позиций с положительной суммой.")
    today = moscow_now().date()
    next_month = 1 if today.month == 12 else today.month + 1
    year = today.year + 1 if today.month == 12 else today.year
    due = today.replace(year=year, month=next_month, day=monthrange(year, next_month)[1])
    second_side = {
        "taxCode": str(requisites.get("inn", "")).strip(),
        "type": requisites.get("payer_type"),
        "secondSideName": str(requisites.get("legal_name", "")).strip(),
    }
    optional_fields = {
        "legalAddress": requisites.get("address"),
        "kpp": requisites.get("kpp"),
        "bankName": requisites.get("bank_name"),
        "bankCorrAccount": requisites.get("corr_account"),
    }
    second_side.update({key: str(value).strip() for key, value in optional_fields.items() if value})
    # В формате Точка accountId покупателя обычно содержит номер счёта и БИК через "/".
    buyer_account = str(requisites.get("settlement_account") or "").strip()
    buyer_bik = str(requisites.get("bik") or "").strip()
    if buyer_account and buyer_bik:
        second_side["accountId"] = f"{buyer_account}/{buyer_bik}"
    invoice_number = _tochka_invoice_number(deal, calc)
    return {
        "Data": {
            "accountId": cfg["account_id"],
            "customerCode": cfg["customer_code"],
            "SecondSide": second_side,
            "Content": {
                "Invoice": {
                    "Positions": positions,
                    "date": today.isoformat(),
                    "totalAmount": f"{total:.2f}",
                    "number": invoice_number,
                    "basedOn": f'Сделка №{_deal_doc_number(deal)} · {calc.get("name", "Расчёт")}'[:250],
                    "comment": f'Счёт из CRM по расчёту «{calc.get("name", "Расчёт")}»'[:250],
                    "paymentExpiryDate": due.isoformat(),
                }
            },
        }
    }


def _tochka_create_invoice(deal, calc, requisites):
    missing = _tochka_missing_config(["token", "customer_code", "account_id"])
    if missing:
        raise RuntimeError("Не настроены параметры Точки: " + ", ".join(missing) + ".")
    payload = _tochka_build_invoice_payload(deal, calc, requisites)
    response = _tochka_request("POST", "/invoice/v1.0/bills", payload)
    data = _tochka_data(response)
    document_id = data.get("documentId") or data.get("documentID")
    if not document_id:
        raise RuntimeError("Точка не вернула documentId созданного счёта.")
    return {
        "kind": "invoice",
        "bank": "Точка",
        "document_id": str(document_id),
        "invoice_number": payload["Data"]["Content"]["Invoice"]["number"],
        "customer_code": _tochka_config().get("customer_code", ""),
        "amount": float(payload["Data"]["Content"]["Invoice"]["totalAmount"]),
        "status": "payment_waiting",
        "created_at": now_str(),
        "payment_expiry_date": payload["Data"]["Content"]["Invoice"]["paymentExpiryDate"],
    }


def _tochka_get_invoice_pdf(record):
    customer_code = urllib.parse.quote(str(record.get("customer_code") or _tochka_config().get("customer_code", "")), safe="")
    document_id = urllib.parse.quote(str(record.get("document_id", "")), safe="")
    return _tochka_request("GET", f"/invoice/v1.0/bills/{customer_code}/{document_id}/file", expect_pdf=True)


def _tochka_create_payment_link(deal, calc, requisites):
    required = ["token", "customer_code", "tax_system_code", "supplier_name", "supplier_inn", "supplier_phone"]
    missing = _tochka_missing_config(required)
    if missing:
        raise RuntimeError("Для платёжной ссылки с чеком настройте в secrets: " + ", ".join(missing) + ".")
    if not str(requisites.get("email", "")).strip():
        raise ValueError("Для платёжной ссылки с фискальным чеком нужен email покупателя.")
    rows = _calculation_rows(calc, st.session_state.crm_store.get("products", DEFAULT_PRODUCT_CATALOG))
    items = []
    for row in rows:
        if row["quantity"] <= 0 or row["after"] <= 0:
            continue
        items.append({
            "vatType": "none",
            "name": str(row["name"] or "Товар")[:256],
            "amount": f'{row["after"]:.2f}',
            "quantity": row["quantity"],
            "paymentMethod": "full_prepayment",
            "paymentObject": "goods",
            "measure": _tochka_unit(row["unit"]),
        })
    delivery = max(0.0, float(calc.get("delivery_amount", 0) or 0))
    if delivery > 0:
        items.append({
            "vatType": "none",
            "name": "Доставка",
            "amount": f"{delivery:.2f}",
            "quantity": 1,
            "paymentMethod": "full_prepayment",
            "paymentObject": "service",
            "measure": "услуга.",
        })
    total = round(sum(float(item["amount"]) * float(item["quantity"]) for item in items), 2)
    if not items or total <= 0:
        raise ValueError("В расчёте нет позиций с положительной суммой.")
    purpose = f'Оплата по сделке №{_deal_doc_number(deal)}, {calc.get("name", "Расчёт")}'[:140]
    payment_id = f"crm-{uuid.uuid4().hex[:32]}"[:45]
    cfg = _tochka_config()
    client_obj = {
        "name": str(requisites.get("legal_name") or (get_client_by_id(deal.get("client_id")) or {}).get("name") or "Покупатель")[:256],
        "email": str(requisites.get("email")).strip(),
    }
    if requisites.get("phone"):
        client_obj["phone"] = str(requisites.get("phone")).strip()
    data = {
        "customerCode": cfg["customer_code"],
        "amount": f"{total:.2f}",
        "purpose": purpose,
        "paymentMode": ["sbp", "card"],
        "paymentLinkId": payment_id,
        "taxSystemCode": cfg["tax_system_code"],
        "Client": client_obj,
        "Items": items,
        "Supplier": {
            "phone": cfg["supplier_phone"],
            "name": cfg["supplier_name"],
            "taxCode": cfg["supplier_inn"],
        },
    }
    if cfg.get("merchant_id"):
        data["merchantId"] = cfg["merchant_id"]
    if cfg.get("redirect_url"):
        data["redirectUrl"] = cfg["redirect_url"]
    if cfg.get("fail_redirect_url"):
        data["failRedirectUrl"] = cfg["fail_redirect_url"]
    response = _tochka_request("POST", "/acquiring/v1.0/payments_with_receipt", {"Data": data})
    result = _tochka_data(response)
    operation_id = result.get("operationId")
    payment_link = result.get("paymentLink")
    if not operation_id or not payment_link:
        raise RuntimeError("Точка не вернула operationId или ссылку на оплату.")
    return {
        "kind": "payment_link",
        "bank": "Точка",
        "operation_id": str(operation_id),
        "payment_link": str(payment_link),
        "payment_link_id": payment_id,
        "amount": total,
        "status": result.get("status", "CREATED"),
        "created_at": now_str(),
        "customer_code": cfg["customer_code"],
    }


def _tochka_refresh_status(record):
    customer_code = urllib.parse.quote(str(record.get("customer_code") or _tochka_config().get("customer_code", "")), safe="")
    if record.get("kind") == "invoice":
        document_id = urllib.parse.quote(str(record.get("document_id", "")), safe="")
        response = _tochka_request("GET", f"/invoice/v1.0/bills/{customer_code}/{document_id}/payment-status")
        data = _tochka_data(response)
        status = data.get("status") or data.get("paymentStatus") or data.get("payment_status")
    else:
        operation_id = urllib.parse.quote(str(record.get("operation_id", "")), safe="")
        response = _tochka_request("GET", f"/acquiring/v1.0/payments/{operation_id}")
        data = _tochka_data(response)
        operations = data.get("Operation") or data.get("operation") or []
        if isinstance(operations, list) and operations:
            data = operations[0]
        status = data.get("status")
        if data.get("paidAt"):
            record["paid_at"] = data["paidAt"]

    # Сумма фактической оплаты сохраняется только из явно обозначенных полей API.
    # Поле amount само по себе не используем: оно может означать полную сумму ссылки/счёта.
    paid_amount = None
    for key in ("paidAmount", "amountPaid", "paid_amount", "paidSum", "paymentAmount", "amountPaidTotal"):
        value = data.get(key)
        if value not in (None, "") and not isinstance(value, (dict, list, bool)):
            try:
                paid_amount = float(str(value).replace(" ", "").replace(",", "."))
                break
            except (TypeError, ValueError):
                pass
    if paid_amount is not None and paid_amount >= 0:
        record["paid_amount"] = paid_amount

    if not status:
        raise RuntimeError("В ответе Точки не найден статус платежа.")
    record["status"] = str(status)
    record["checked_at"] = now_str()
    return record


def _tochka_bank_payment_status(deal):
    """Возвращает подтверждённый банком статус сделки, если его можно определить."""
    statuses = []
    known_unpaid = {
        "PAYMENT_PENDING", "PENDING", "NEW", "CREATED", "WAITING_FOR_PAYMENT",
        "PAYMENT_NOT_PAID", "NOT_PAID", "UNPAID", "INVOICE_CREATED", "WAITING",
        "PAYMENT_WAITING", "PAYMENT_CREATED", "REGISTERED"
    }
    paid = {"PAYMENT_PAID", "PAYMENT_CONFIRMED", "APPROVED", "PAID", "SUCCESS", "SUCCEEDED", "COMPLETED"}
    partial = {"PAYMENT_PARTIALLY_PAID", "PARTIALLY_PAID", "PARTIAL_PAYMENT", "PARTIALLYPAID", "PARTIAL_PAID"}
    for calc in deal.get("calculations", []) or []:
        for record in (calc.get("tochka_documents", []) or []) + (calc.get("ozon_documents", []) or []):
            if record.get("deleted"):
                continue
            status = str(record.get("status", "")).strip().upper()
            if not status or not record.get("checked_at"):
                continue
            if status in paid:
                statuses.append("Оплачено")
            elif status in partial:
                statuses.append("Оплачен частично")
            elif status in known_unpaid:
                statuses.append("Не оплачено")
    if not statuses:
        return None
    if "Оплачено" in statuses:
        return "Оплачено"
    if "Оплачен частично" in statuses:
        return "Оплачен частично"
    return "Не оплачено"


def _deal_has_active_payment_document(deal):
    """True, если в сделке есть хотя бы один активный счёт или платёжная ссылка Точки."""
    for calc in deal.get("calculations", []) or []:
        for record in (calc.get("tochka_documents", []) or []) + (calc.get("ozon_documents", []) or []):
            if not record.get("deleted") and record.get("kind") in ("invoice", "payment_link"):
                return True
    return False


def _sync_deal_board_stage_from_payment(deal):
    """Синхронизирует колонку сделки с оплатой и наличием выставленных документов, сохраняя паузу и финальные этапы."""
    status = deal.get("status", "Новый")
    if status in ("На паузе", "Сделка закрыта", "Архив"):
        return
    payment_status = deal.get("payment_status", "Не оплачено")
    has_payment_document = _deal_has_active_payment_document(deal)
    if payment_status == "Оплачено":
        if status in ("Новый", "В работе", "Ожидание оплаты", "Оплачено"):
            deal["status"] = "Оплачено"
    elif has_payment_document and status in ("Новый", "В работе", "Ожидание оплаты", "Оплачено"):
        deal["status"] = "Ожидание оплаты"
    elif status == "Оплачено":
        deal["status"] = "В работе"


def _tochka_apply_paid_status(deal, record):
    """Обрабатывает подтверждённую полную оплату; частичная оплата не меняет статус и не уведомляет."""
    status = str(record.get("status", "")).strip().upper()
    paid_statuses = {"PAYMENT_PAID", "PAYMENT_CONFIRMED", "APPROVED", "PAID", "SUCCESS", "SUCCEEDED", "COMPLETED"}
    try:
        paid_amount = float(record.get("paid_amount", 0) or 0)
        total_amount = float(record.get("amount", 0) or 0)
    except (TypeError, ValueError):
        paid_amount, total_amount = 0.0, 0.0
    fully_paid = status in paid_statuses or (
        "paid_amount" in record and total_amount > 0 and paid_amount >= total_amount - 0.01
    )
    if not fully_paid:
        return False

    changed = False
    # Ручной статус менеджера не затираем. Факт банковской оплаты при этом
    # всё равно учитывается для уведомления и предупреждения о расхождении.
    if not deal.get("payment_status_manual_override"):
        if deal.get("payment_status") != "Оплачено":
            deal["payment_status"] = "Оплачено"
            deal["last_modified"] = now_str()
            changed = True
        old_stage = deal.get("status")
        _sync_deal_board_stage_from_payment(deal)
        if deal.get("status") != old_stage:
            changed = True

    try:
        _ensure_paid_deal_torg12(deal)
    except Exception as exc:
        st.session_state["_paid_torg12_error"] = str(exc)[:300]

    if not record.get("paid_notification_sent"):
        manager = deal.get("manager", "")
        if manager:
            deal_label = str(deal.get("deal_number") or deal.get("title") or deal.get("id") or "")
            amount = record.get("amount")
            amount_text = f" на сумму {float(amount):,.2f} ₽".replace(",", " ") if amount not in (None, "") else ""
            message = f"Заказ по сделке №{deal_label} оплачен полностью{amount_text}."
            tg_message = f"💳 <b>Заказ оплачен полностью</b>\nСделка: {deal_label}{amount_text}"
            add_notification(manager, message, tg_message)
            record["paid_notification_sent"] = True
            changed = True
    return changed

def _tochka_auto_refresh_payment_status(deal, calc):
    """Проверяет неоплаченные документы не чаще раза в минуту, пока открыто окно счёта."""
    changed = False
    for record in (calc.get("tochka_documents", []) or []) + (calc.get("ozon_documents", []) or []):
        if record.get("deleted"):
            continue
        if str(record.get("status", "")).strip().upper() in {"PAYMENT_PAID", "PAYMENT_CONFIRMED", "APPROVED", "PAID", "SUCCESS", "SUCCEEDED", "COMPLETED"}:
            if _tochka_apply_paid_status(deal, record):
                changed = True
            continue
        checked_at = record.get("checked_at", "")
        try:
            checked_dt = datetime.strptime(str(checked_at), "%Y-%m-%d %H:%M:%S") if checked_at else None
        except Exception:
            checked_dt = None
        if checked_dt and (moscow_now() - checked_dt).total_seconds() < 60:
            continue
        try:
            old_status = str(record.get("status", ""))
            if record.get("bank") == "Ozon Pay":
                _ozon_refresh_status(record)
            else:
                _tochka_refresh_status(record)
            if str(record.get("status", "")) != old_status:
                changed = True
            if _tochka_apply_paid_status(deal, record):
                changed = True
        except Exception:
            # Автопроверка не должна мешать работе формы; пользователь может проверить вручную.
            continue
    if changed:
        save_data(st.session_state.crm_store)


def _tochka_qr_png(url):
    """Создаёт QR локально, без отправки платёжной ссылки сторонним сервисам."""
    try:
        import qrcode
        image = qrcode.make(url)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception:
        pass
    try:
        from reportlab.graphics.barcode.qr import QrCodeWidget
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics import renderPM
        widget = QrCodeWidget(url)
        x1, y1, x2, y2 = widget.getBounds()
        width, height = max(1, x2 - x1), max(1, y2 - y1)
        size = 240
        drawing = Drawing(size, size, transform=[size / width, 0, 0, size / height, 0, 0])
        drawing.add(widget)
        return renderPM.drawToString(drawing, fmt="PNG", dpi=150)
    except Exception:
        return None


def _tochka_status_label(record):
    status = str(record.get("status", "")).upper()
    labels = {
        "PAYMENT_WAITING": "Ожидает оплаты",
        "PAYMENT_PAID": "Оплачен",
        "PAYMENT_CONFIRMED": "Оплачен",
        "PAYMENT_NEW": "Ожидает оплаты",
        "PAYMENT_PROCESSING": "Обрабатывается",
        "PAYMENT_REJECTED": "Оплата отклонена",
        "PAYMENT_CANCELED": "Платёж отменён",
        "PAYMENT_AUTHORIZED": "Оплата авторизована",
        "PAYMENT_PARTIALLY_PAID": "Оплачен частично",
        "PARTIALLY_PAID": "Оплачен частично",
        "PARTIAL_PAYMENT": "Оплачен частично",
        "PAYMENT_EXPIRED": "Истёк срок оплаты",
        "CREATED": "Ссылка создана, ожидает оплаты",
        "APPROVED": "Оплачен",
        "AUTHORIZED": "Оплата авторизована, ожидает списания",
        "ON-REFUND": "Возврат выполняется",
        "REFUNDED": "Возвращён",
        "REFUNDED_PARTIALLY": "Частично возвращён",
        "EXPIRED": "Срок ссылки истёк",
        "WAIT_FULL_PAYMENT": "Ожидает полного платежа",
    }
    return labels.get(status, record.get("status", "Статус неизвестен"))


def _tochka_record_store(deal, calc, record):
    calc.setdefault("tochka_documents", [])
    calc["tochka_documents"].append(record)
    calc["updated_at"] = now_str()
    # Счёт или платёжная ссылка переводят активную сделку в колонку ожидания оплаты.
    if deal.get("status", "Новый") not in ("На паузе", "Сделка закрыта", "Архив") and deal.get("payment_status") != "Оплачено":
        deal["status"] = "Ожидание оплаты"
    deal["last_modified"] = now_str()
    save_data(st.session_state.crm_store)



@_crm_dialog("Сформировать счёт", width="large")
def invoice_document_dialog(deal_id, calc_id):
    deal=next((d for d in st.session_state.crm_store.get("deals",[]) if str(d.get("id"))==str(deal_id)),None)
    if not deal:
        st.error("Сделка не найдена"); return
    calc=next((c for c in deal.get("calculations",[]) if str(c.get("id"))==str(calc_id)),None)
    if not calc:
        st.error("Расчёт не найден"); return
    _tochka_auto_refresh_payment_status(deal, calc)
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
    selected_req = None
    ids=[str(r.get("id")) for r in requisites]
    selected=str(state.get("selected_requisite_id", "") or "")
    if selected not in ids: selected=""
    req_select_col, req_view_col = st.columns([4, 1.65], vertical_alignment="bottom")
    with req_select_col:
        sel=st.selectbox(
            "Реквизиты плательщика:", [""] + ids,
            index=(ids.index(selected) + 1) if selected else 0,
            format_func=lambda rid: "Выбери сохранённые реквизиты" if not rid else next((r.get("legal_name", "Реквизиты") for r in requisites if str(r.get("id"))==str(rid)), "Реквизиты"),
            key=f"invoice_req_select_{deal_id}_{calc_id}",
        )
    state["selected_requisite_id"] = sel or ""
    selected_req=next((r for r in requisites if str(r.get("id"))==str(sel)),None) if sel else None
    with req_view_col:
        if st.button("Посмотреть реквизиты", key=f"invoice_req_view_{deal_id}_{calc_id}", use_container_width=True, disabled=not selected_req):
            _push_dialog_return()
            st.session_state["dialog_client_requisites_view"] = {"client_id": client.get("id"), "return_to_invoice": True, "requisite_id": selected_req.get("id")}
            st.rerun()
    if not requisites:
        st.info("Для клиента пока не сохранены реквизиты плательщика. Нажми «Добавить новые реквизиты».")
    elif not selected_req:
        st.warning("Обязательно выбери реквизиты плательщика перед созданием счёта или платежа.")
    if selected_req:
        st.caption(f"Тип: { {'company':'Юрлицо','ip':'ИП','person':'Физлицо'}.get(selected_req.get('payer_type'),'—') } · ИНН: {selected_req.get('inn','—')} · Email: {selected_req.get('email','—')}")
    if st.button("+ Добавить новые реквизиты",key=f"invoice_add_req_{deal_id}_{calc_id}",use_container_width=True):
        st.session_state["dialog_client_requisites_client_id"]=client.get("id")
        st.session_state["dialog_client_requisites_return_to_invoice"]=True
        client_requisites_dialog(client.get("id"),True)
        st.rerun()

    st.markdown("**Банк для формирования счёта или платежа**")
    bank_choice = st.selectbox(
        "Выбери банк", ["Точка Банк", "Ozon Pay"],
        index=0 if st.session_state.get(f"invoice_bank_choice_{deal_id}_{calc_id}", "Точка Банк") == "Точка Банк" else 1,
        key=f"invoice_bank_choice_{deal_id}_{calc_id}", label_visibility="collapsed",
    )

    if bank_choice == "Точка Банк":
        st.divider()
        st.markdown("### Точка Банк")
        st.caption("Счёт через API доступен юридическим лицам и ИП. Для физлиц используйте платёжную ссылку с онлайн-чеком.")
        cfg = _tochka_config()
        missing_invoice = _tochka_missing_config(["token", "customer_code", "account_id"])
        missing_link = _tochka_missing_config(["token", "customer_code", "tax_system_code", "supplier_name", "supplier_inn", "supplier_phone"])
        if missing_invoice:
            st.info("Для банковского счёта добавьте параметры Точки в Streamlit Secrets: token, customer_code и account_id.")
        t_invoice_col, t_link_col = st.columns(2)
        with t_invoice_col:
            invoice_disabled = not selected_req or selected_req.get("payer_type") not in ("company", "ip") or bool(missing_invoice) or not bool(calc.get("items"))
            if st.button("Создать счёт в Точке", key=f"tochka_invoice_create_{deal_id}_{calc_id}", use_container_width=True, disabled=invoice_disabled):
                try:
                    record = _tochka_create_invoice(deal, calc, selected_req)
                    _tochka_record_store(deal, calc, record)
                    # save_data() обновляет crm_store глубокой копией — повторно получаем
                    # актуальные объекты, чтобы PDF прикрепился к сохранённой сделке.
                    deal = next((d for d in st.session_state.crm_store.get("deals", []) if str(d.get("id")) == str(deal_id)), deal)
                    calc = next((c for c in deal.get("calculations", []) if str(c.get("id")) == str(calc_id)), calc)
                    try:
                        pdf = _tochka_get_invoice_pdf(record)
                        filename = f"Счёт Точка {record['invoice_number']}.pdf"
                        _save_generated_document(deal, pdf, filename, "Счёт Точка", calc, {"payer_type": selected_req.get("payer_type"), "tochka_document_id": record["document_id"], "bank": "Точка"})
                        _open_pdf_link(pdf, filename, f"tochka_pdf_{deal_id}_{calc_id}_{record['document_id']}")
                        st.success(f"Счёт создан в Точке № {record['invoice_number']} и сохранён в файлах сделки.")
                    except Exception as pdf_exc:
                        st.warning(f"Счёт создан в Точке, но PDF пока не удалось получить: {pdf_exc}. Идентификатор сохранён в CRM.")
                except Exception as exc:
                    st.error(f"Не удалось создать счёт в Точке: {exc}")
        with t_link_col:
            link_disabled = not selected_req or bool(missing_link) or not bool(calc.get("items"))
            if st.button("Создать платёжную ссылку / QR", key=f"tochka_link_create_{deal_id}_{calc_id}", use_container_width=True, disabled=link_disabled):
                try:
                    record = _tochka_create_payment_link(deal, calc, selected_req)
                    _tochka_record_store(deal, calc, record)
                    st.success("Платёжная ссылка Точки создана. Ссылка и QR-код доступны ниже.")
                except Exception as exc:
                    st.error(f"Не удалось создать платёжную ссылку Точки: {exc}")
        if missing_link:
            st.caption("Для ссылок с фискальным чеком дополнительно нужны tax_system_code в Streamlit Secrets и email плательщика в реквизитах. Эквайринг должен быть подключён в Точке.")
    else:
        st.divider()
        st.markdown("### Ozon Pay")
        st.caption("Ozon Pay API создаёт платёж через СБП (ссылку/QR) и позволяет проверять статус. Для счёта юридическому лицу CRM формирует отдельный PDF и сохраняет его в блоке документов и платежей Ozon.")
        ozon_cfg = _ozon_config()
        ozon_missing = [key for key in ("access_key", "secret_key") if not ozon_cfg.get(key)]
        if ozon_missing:
            st.info("Для Ozon Pay добавьте в Streamlit Secrets раздел [ozon] с access_key и secret_key.")
        ozon_create_disabled = bool(ozon_missing) or not bool(calc.get("items")) or _deal_calc_total(calc) <= 0
        invoice_pdf_key = f"ozon_legal_invoice_pdf_{deal_id}_{calc_id}"
        ozon_invoice_col, ozon_payment_col = st.columns(2)
        with ozon_invoice_col:
            if st.button("Сформировать PDF-счёт в CRM", key=f"ozon_legal_invoice_make_{deal_id}_{calc_id}", use_container_width=True,
                         disabled=(not selected_req or not bool(calc.get("items")))):
                try:
                    pdf_bytes, due_date = _make_invoice_pdf(deal, client, calc, selected_req)
                    filename = f"Счёт {str(calc.get('name') or 'Расчёт').replace('Расчёт', '').strip() or 'Айплинт'} от {moscow_now().strftime('%d.%m.%Y')}.pdf"
                    saved_file = _save_generated_document(
                        deal, pdf_bytes, filename, "Счёт Ozon (PDF из CRM)", calc,
                        {"payer_type": selected_req.get("payer_type"), "bank": "Ozon", "requisite_id": selected_req.get("id")}
                    )
                    # _save_generated_document сохраняет данные CRM; заново получаем
                    # актуальные объекты, чтобы не записать устаревшую копию сделки.
                    deal = next((d for d in st.session_state.crm_store.get("deals", []) if str(d.get("id")) == str(deal_id)), deal)
                    calc = next((c for c in deal.get("calculations", []) if str(c.get("id")) == str(calc_id)), calc)
                    # Сохраняем счёт также как документ расчёта, чтобы он отображался
                    # в общем блоке документов и платежей Ozon, а не отдельной историей PDF.
                    calc.setdefault("ozon_documents", []).append({
                        "id": uuid.uuid4().hex,
                        "kind": "invoice_pdf",
                        "bank": "Ozon",
                        "amount": float(_deal_calc_total(calc) or 0),
                        "status": "pdf_created",
                        "file_name": saved_file.get("file_name", filename),
                        "file_hash": saved_file.get("file_hash", hashlib.sha256(pdf_bytes).hexdigest()),
                        "calculation_id": str(calc.get("id")),
                        "requisite_id": str(selected_req.get("id", "")),
                        "created_at": now_str(),
                    })
                    calc["updated_at"] = now_str()
                    deal["last_modified"] = now_str()
                    save_data(st.session_state.crm_store)
                    st.session_state[invoice_pdf_key] = {"bytes": base64.b64encode(pdf_bytes).decode("ascii"), "filename": filename, "file_hash": saved_file.get("file_hash"), "due_date": due_date}
                    st.success("PDF-счёт Ozon сформирован, сохранён в файлах сделки и добавлен в блок документов и платежей Ozon.")
                except Exception as exc:
                    st.error(f"Не удалось сформировать PDF-счёт: {exc}")
        with ozon_payment_col:
            if st.button("Создать платёжную ссылку Ozon Pay / QR", key=f"ozon_payment_create_{deal_id}_{calc_id}", use_container_width=True, disabled=ozon_create_disabled):
                try:
                    ozon_record = _ozon_create_payment(deal, calc)
                    calc.setdefault("ozon_documents", []).append(ozon_record)
                    calc["updated_at"] = now_str()
                    if deal.get("status", "Новый") not in ("На паузе", "Сделка закрыта", "Архив") and deal.get("payment_status") != "Оплачено":
                        deal["status"] = "Ожидание оплаты"
                    deal["last_modified"] = now_str()
                    save_data(st.session_state.crm_store)
                    st.success("Платёж Ozon Pay создан. Ссылка и QR-код доступны ниже.")
                except Exception as exc:
                    st.error(f"Не удалось создать платёж Ozon Pay: {exc}")
    st.divider()
    st.markdown("### Документы и оплаты по сделке")
    # PDF-счета, сформированные внутри CRM (в том числе для Ozon Pay), не являются банковскими
    # платежными записями, поэтому показываем их отдельно в этой общей, всегда видимой истории.
    generated = [doc for doc in (deal.get("generated_documents", []) or [])
                 if str(doc.get("calculation_id", "")) == str(calc_id)
                 and ("счёт" in str(doc.get("kind", "")).lower() or "счет" in str(doc.get("kind", "")).lower())
                 and str(doc.get("kind", "")).lower() != "счёт ozon (pdf из crm)" ]
    generated = list(reversed(generated))
    if generated:
        st.markdown("#### PDF-счета, сформированные CRM")
        for gen_index, gen_doc in enumerate(generated):
            with st.container(border=True):
                st.markdown(f"**{gen_doc.get('file_name', 'Счёт PDF')}**")
                st.caption(f"{gen_doc.get('kind', 'Счёт')} · Создано: {gen_doc.get('created_at', '—')}")
                # Для только что сформированного PDF байты доступны в session_state.
                matching_pdf = None
                for _pdf_key in (f"ozon_legal_invoice_pdf_{deal_id}_{calc_id}", f"tochka_pdf_{deal_id}_{calc_id}_{gen_doc.get('payer', {}).get('tochka_document_id', '')}"):
                    _pdf_state = st.session_state.get(_pdf_key)
                    if _pdf_state:
                        if _pdf_state.get("bytes"):
                            matching_pdf = (base64.b64decode(_pdf_state["bytes"]), _pdf_state.get("filename", gen_doc.get("file_name", "Счёт.pdf")))
                            break
                        if _pdf_state.get("data"):
                            matching_pdf = (base64.b64decode(_pdf_state["data"]), _pdf_state.get("filename", gen_doc.get("file_name", "Счёт.pdf")))
                            break
                if matching_pdf is None:
                    _file_obj = next((f for f in (deal.get("deal_files", []) or [])
                                      if f.get("file_hash") == gen_doc.get("file_hash") or
                                      (f.get("file_name") == gen_doc.get("file_name") and str(f.get("calculation_id", "")) == str(calc_id))), None)
                    _local_path = (_file_obj or {}).get("file_path", "")
                    if _local_path and os.path.isfile(_local_path):
                        try:
                            with open(_local_path, "rb") as _pdf_file:
                                matching_pdf = (_pdf_file.read(), gen_doc.get("file_name", "Счёт.pdf"))
                        except Exception:
                            matching_pdf = None
                if matching_pdf:
                    st.download_button("Скачать PDF", data=matching_pdf[0], file_name=matching_pdf[1], mime="application/pdf", key=f"generated_doc_download_{deal_id}_{calc_id}_{gen_index}")
                else:
                    st.caption("PDF сохранён в файлах сделки. Если файл хранится во внешнем облаке, скачивание доступно в разделе файлов сделки.")
    # История документов находится вне переключателя банка и всегда видна.
    # Документы принадлежат конкретному расчёту: показываем только его счета и ссылки.
    # Вёрстку и отображение документов оставляем без изменений.
    bank_records = [(calc, record) for record in (calc.get("tochka_documents", []) or [])]
    bank_records = list(reversed(bank_records))
    if bank_records:
        st.markdown("#### Документы и оплаты Точки по сделке")
        for index, (record_calc, record) in enumerate(bank_records):
            record_calc_id = str(record_calc.get("id", calc_id))
            deleted = bool(record.get("deleted"))
            confirm_key = f"tochka_delete_confirm_{deal_id}_{record_calc_id}_{index}"
            with st.container(border=True):
                title = f"Банковский счёт № {record.get('invoice_number')}" if record.get("kind") == "invoice" else "Платёжная ссылка"
                amount_text = f"{title} · {_money(record.get('amount', 0))} ₽"
                st.caption(f"Расчёт: {record_calc.get('name', 'Расчёт')}")
                if deleted:
                    st.markdown(f"<div style='text-decoration:line-through;color:#9299A3;font-weight:600'>{amount_text}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-decoration:line-through;color:#9299A3'>Статус: {_tochka_status_label(record)}</div>", unsafe_allow_html=True)
                    st.caption("Документ удалён из активного списка, запись сохранена в истории.")
                else:
                    st.markdown(f"**{amount_text}**")
                    st.write(f"Статус: **{_tochka_status_label(record)}**")
                if record.get("created_at"):
                    created_text = f"Создано: {record['created_at']}" + (f" · Проверено: {record['checked_at']}" if record.get("checked_at") else "")
                    if deleted:
                        st.markdown(f"<div style='text-decoration:line-through;color:#9299A3'>{created_text}</div>", unsafe_allow_html=True)
                    else:
                        st.caption(created_text)
                if not deleted and record.get("kind") == "payment_link" and record.get("payment_link"):
                    st.markdown(f"[Открыть платёжную ссылку]({record['payment_link']})")
                    st.code(record["payment_link"], language=None)
                    qr_png = _tochka_qr_png(record["payment_link"])
                    if qr_png:
                        st.image(qr_png, caption="QR-код для оплаты", width=220)
                    else:
                        st.caption("Не удалось создать QR-код в текущем окружении. Ссылка на оплату доступна выше.")
                if not deleted and record.get("kind") == "invoice":
                    pdf_key = f"tochka_pdf_{deal_id}_{record_calc_id}_{record.get('document_id')}"
                    bank_pdf_state = st.session_state.get(pdf_key)
                    if bank_pdf_state:
                        st.download_button("Скачать PDF счёта Точки", data=base64.b64decode(bank_pdf_state["data"]), file_name=bank_pdf_state["filename"], mime="application/pdf", key=f"tochka_pdf_dl_{deal_id}_{record_calc_id}_{index}")
                if not deleted:
                    refresh_col, delete_col = st.columns([3, 1])
                    with refresh_col:
                        if st.button("Обновить статус оплаты", key=f"tochka_status_{deal_id}_{record_calc_id}_{index}", use_container_width=True):
                            try:
                                _tochka_refresh_status(record)
                                _tochka_apply_paid_status(deal, record)
                                save_data(st.session_state.crm_store)
                                st.success(f"Статус обновлён: {_tochka_status_label(record)}")
                            except Exception as exc:
                                st.error(f"Не удалось обновить статус: {exc}")
                    with delete_col:
                        _record_status_code = str(record.get("status", "")).strip().upper()
                        _record_is_fully_paid = _record_status_code in {"PAYMENT_PAID", "APPROVED", "PAID", "SUCCESS", "SUCCEEDED", "COMPLETED"}
                        _record_is_partially_paid = _record_status_code in {"PAYMENT_PARTIALLY_PAID", "PARTIALLY_PAID", "PARTIAL_PAYMENT"}
                        if _record_is_fully_paid or _record_is_partially_paid:
                            _paid_label = "Оплачен" if _record_is_fully_paid else "Частично оплачен"
                            st.markdown(f"<div style='color:#218739;font-weight:600;text-align:center;padding:0.45rem 0;font-size:0.82rem'>{_paid_label}</div>", unsafe_allow_html=True)
                        elif st.button("Удалить", key=f"tochka_delete_{deal_id}_{record_calc_id}_{index}", use_container_width=True):
                            st.session_state[confirm_key] = True
                    if not (_record_is_fully_paid or _record_is_partially_paid) and st.session_state.get(confirm_key):
                        st.warning("Зачеркнуть этот документ? Он останется в истории CRM.")
                        yes_col, no_col = st.columns(2)
                        with yes_col:
                            if st.button("Да, удалить", key=f"tochka_delete_yes_{deal_id}_{record_calc_id}_{index}", use_container_width=True):
                                record["deleted"] = True
                                record["deleted_at"] = now_str()
                                st.session_state.pop(confirm_key, None)
                                save_data(st.session_state.crm_store)
                                st.rerun()
                        with no_col:
                            if st.button("Отмена", key=f"tochka_delete_no_{deal_id}_{record_calc_id}_{index}", use_container_width=True):
                                st.session_state.pop(confirm_key, None)
                                st.rerun()


    ozon_records = calc.get("ozon_documents", []) or []
    if ozon_records:
        st.markdown("#### Документы и оплаты Ozon Pay по этому расчёту")
        for ozon_index, ozon_record in enumerate(reversed(ozon_records)):
            ozon_deleted = bool(ozon_record.get("deleted"))
            with st.container(border=True):
                is_ozon_pdf = ozon_record.get("kind") == "invoice_pdf"
                ozon_title = (f"PDF-счёт Ozon · {_money(ozon_record.get('amount', 0))} ₽" if is_ozon_pdf
                              else f"Платёж Ozon Pay · {_money(ozon_record.get('amount', 0))} ₽")
                if ozon_deleted:
                    st.markdown(f"<div style='text-decoration:line-through;color:#9299A3;font-weight:600'>{ozon_title}</div>", unsafe_allow_html=True)
                    st.caption("Документ скрыт из активного списка, запись сохранена в истории.")
                else:
                    st.markdown(f"**{ozon_title}**")
                    if is_ozon_pdf:
                        st.write("Статус: **PDF-счёт сформирован в CRM**")
                        _pdf_state = st.session_state.get(f"ozon_legal_invoice_pdf_{deal_id}_{calc_id}")
                        _pdf_data = None
                        _pdf_name = ozon_record.get("file_name", "Счёт Ozon.pdf")
                        if _pdf_state and _pdf_state.get("bytes") and (_pdf_state.get("file_hash") == ozon_record.get("file_hash") or _pdf_state.get("filename") == _pdf_name):
                            _pdf_data = base64.b64decode(_pdf_state["bytes"])
                            _pdf_name = _pdf_state.get("filename", _pdf_name)
                        if _pdf_data is None:
                            _file_obj = next((f for f in (deal.get("deal_files", []) or [])
                                              if f.get("file_hash") == ozon_record.get("file_hash") or f.get("file_name") == _pdf_name), None)
                            _local_path = (_file_obj or {}).get("file_path", "")
                            if _local_path:
                                try:
                                    _pdf_data = get_file_bytes(_local_path)
                                except Exception:
                                    _pdf_data = None
                        if _pdf_data:
                            st.download_button("Скачать PDF-счёт", data=_pdf_data, file_name=_pdf_name, mime="application/pdf",
                                               key=f"ozon_pdf_download_{deal_id}_{calc_id}_{ozon_index}", use_container_width=True)
                        else:
                            st.caption("PDF сохранён в файлах сделки. Если он хранится во внешнем облаке, открой его в разделе файлов сделки.")
                    else:
                        st.write(f"Статус: **{_tochka_status_label(ozon_record)}**")
                        if ozon_record.get("payment_link"):
                            st.markdown(f"[Открыть оплату Ozon Pay]({ozon_record['payment_link']})")
                            st.code(ozon_record["payment_link"], language=None)
                            ozon_qr = _tochka_qr_png(ozon_record["payment_link"])
                            if ozon_qr:
                                st.image(ozon_qr, caption="QR-код для оплаты через СБП", width=220)
                if ozon_record.get("created_at"):
                    st.caption(f"Создано: {ozon_record['created_at']}" + (f" · Проверено: {ozon_record['checked_at']}" if ozon_record.get("checked_at") else ""))
                if not ozon_deleted:
                    ozon_status_code = str(ozon_record.get("status", "")).strip().upper()
                    if is_ozon_pdf:
                        ozon_refresh_col, ozon_delete_col = st.columns([3, 1])
                        with ozon_refresh_col:
                            st.caption("Это PDF-документ, сформированный CRM; банковский статус оплаты для него не запрашивается.")
                            st.markdown("<div style='color:#d00000;font-weight:800;margin-top:4px;'>ПРОВЕРЬ ОПЛАТУ И СМЕНИ СТАТУС ОПЛАТЫ САМОСТОЯТЕЛЬНО!</div>", unsafe_allow_html=True)
                        with ozon_delete_col:
                            if st.button("Удалить", key=f"ozon_delete_{deal_id}_{calc_id}_{ozon_index}", use_container_width=True):
                                st.session_state[f"ozon_delete_confirm_{deal_id}_{calc_id}_{ozon_index}"] = True
                    else:
                        ozon_refresh_col, ozon_delete_col = st.columns([3, 1])
                        with ozon_refresh_col:
                            if st.button("Обновить статус оплаты", key=f"ozon_status_{deal_id}_{calc_id}_{ozon_index}", use_container_width=True):
                                try:
                                    _ozon_refresh_status(ozon_record)
                                    _tochka_apply_paid_status(deal, ozon_record)
                                    save_data(st.session_state.crm_store)
                                    st.success(f"Статус Ozon Pay обновлён: {_tochka_status_label(ozon_record)}")
                                except Exception as exc:
                                    st.error(f"Не удалось обновить статус Ozon Pay: {exc}")
                        with ozon_delete_col:
                            if ozon_status_code in {"PAYMENT_CONFIRMED", "PAYMENT_PAID", "APPROVED", "PAID", "SUCCESS", "SUCCEEDED", "COMPLETED"}:
                                st.markdown("<div style='color:#218739;font-weight:600;text-align:center;padding:0.45rem 0;font-size:0.82rem'>Оплачен</div>", unsafe_allow_html=True)
                            elif st.button("Удалить", key=f"ozon_delete_{deal_id}_{calc_id}_{ozon_index}", use_container_width=True):
                                st.session_state[f"ozon_delete_confirm_{deal_id}_{calc_id}_{ozon_index}"] = True
                    ozon_confirm_key = f"ozon_delete_confirm_{deal_id}_{calc_id}_{ozon_index}"
                    if (is_ozon_pdf or ozon_status_code not in {"PAYMENT_CONFIRMED", "PAYMENT_PAID", "APPROVED", "PAID", "SUCCESS", "SUCCEEDED", "COMPLETED"}) and st.session_state.get(ozon_confirm_key):
                        st.warning("Зачеркнуть этот документ? Он останется в истории CRM.")
                        ozon_yes, ozon_no = st.columns(2)
                        with ozon_yes:
                            if st.button("Да, удалить", key=f"ozon_delete_yes_{deal_id}_{calc_id}_{ozon_index}", use_container_width=True):
                                ozon_record["deleted"] = True
                                ozon_record["deleted_at"] = now_str()
                                st.session_state.pop(ozon_confirm_key, None)
                                save_data(st.session_state.crm_store)
                                st.rerun()
                        with ozon_no:
                            if st.button("Отмена", key=f"ozon_delete_no_{deal_id}_{calc_id}_{ozon_index}", use_container_width=True):
                                st.session_state.pop(ozon_confirm_key, None)
                                st.rerun()


def _calculation_payment_badge(calc):
    """Возвращает отметку об оплате расчёта по статусам его банковских документов."""
    records = [r for r in (calc.get("tochka_documents", []) or []) + (calc.get("ozon_documents", []) or []) if not r.get("deleted")]
    statuses = {str(r.get("status", "")).strip().upper() for r in records}
    fully_paid = {"PAYMENT_PAID", "PAYMENT_CONFIRMED", "APPROVED", "PAID", "SUCCESS", "SUCCEEDED", "COMPLETED"}
    partially_paid = {"PAYMENT_PARTIALLY_PAID", "PARTIALLY_PAID", "PARTIAL_PAYMENT"}
    if statuses & fully_paid:
        return "Оплачен"
    if statuses & partially_paid:
        return "Частично оплачен"
    return ""


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
            deleted_col, restore_col = st.columns([3.2, 1.0])
            with deleted_col:
                st.markdown(
                    f"<div style='text-decoration:line-through;color:#9299A3;padding:0.35rem 0;'>{calc.get('name', 'Расчёт')} — {calc['total']:,.0f} ₽ (удалён)</div>".replace(",", " "),
                    unsafe_allow_html=True,
                )
            with restore_col:
                if st.button("Восстановить", key=f"calc_restore_{d['id']}_{calc['id']}", use_container_width=True):
                    calc["deleted"] = False
                    calc.pop("deleted_at", None)
                    calc.pop("deleted_by", None)
                    d["last_modified"] = now_str()
                    d.setdefault("change_log", []).append({"date": now_str(), "author": st.session_state.get("user_name", st.session_state.get("user_login", "")), "fields": f"Расчёт «{calc.get('name', 'Расчёт')}» восстановлен"})
                    save_data(st.session_state.crm_store)
                    st.rerun()
            continue
        _calc_paid_badge = _calculation_payment_badge(calc)
        name_col, total_col, edit_col, delete_col = st.columns([3.0, 1.4, 1.0, 1.0])
        with name_col:
            st.markdown(f"**{calc.get('name', 'Расчёт')}**")
        with total_col:
            st.markdown(f"{calc['total']:,.0f} ₽".replace(",", " "))
        with edit_col:
            if st.button("Открыть", key=f"calc_edit_{d['id']}_{calc['id']}", use_container_width=True):
                _push_dialog_return()
                st.session_state["dialog_calculation_deal_id"] = str(d["id"])
                st.session_state["dialog_calculation_calc_id"] = str(calc["id"])
                st.rerun()
        with delete_col:
            if _calc_paid_badge:
                st.markdown(f"<div style='color:#218739;font-weight:600;text-align:center;padding:0.45rem 0;font-size:0.82rem'>{html.escape(_calc_paid_badge)}</div>", unsafe_allow_html=True)
            else:
                confirm_key = f"confirm_delete_calc_{d['id']}_{calc['id']}"
                if st.button("Удалить", key=f"calc_delete_{d['id']}_{calc['id']}", use_container_width=True):
                    st.session_state[confirm_key] = True
                    st.rerun()
            if not _calc_paid_badge and st.session_state.get(confirm_key):
                _confirm_ui_key = f"calc_delete_confirm_ui_{d['id']}_{calc['id']}"
                st.markdown(f"""<style>
                .st-key-{_confirm_ui_key} {{background:#FFF7F7!important;border:1px solid #F0C5C5!important;border-radius:10px!important;padding:0.7rem 0.8rem!important;margin:0.25rem 0 0.55rem!important;}}
                .st-key-{_confirm_ui_key} [data-testid="stMarkdownContainer"] p {{margin:0.15rem 0 0.55rem!important;color:#8B3030!important;font-weight:600!important;line-height:1.35!important;}}
                .st-key-{_confirm_ui_key} [data-testid="stHorizontalBlock"] {{gap:0.6rem!important;align-items:center!important;}}
                .st-key-{_confirm_ui_key} .stButton button {{min-height:38px!important;height:auto!important;white-space:normal!important;border-radius:8px!important;font-weight:600!important;padding:0.45rem 0.55rem!important;}}
                </style>""", unsafe_allow_html=True)
                with st.container(key=_confirm_ui_key):
                    st.markdown(f"Удалить расчёт «{html.escape(str(calc.get('name', 'Расчёт')))}»?")
                    confirm_col, cancel_col = st.columns([1, 1], gap="small")
                    with confirm_col:
                        if st.button("Да, удалить", key=f"calc_delete_yes_{d['id']}_{calc['id']}", type="primary", use_container_width=True):
                            calc["deleted"] = True
                            calc["deleted_at"] = now_str()
                            calc["deleted_by"] = st.session_state.get("user_name", st.session_state.get("user_login", ""))
                            d["last_modified"] = now_str()
                            d.setdefault("change_log", []).append({"date": now_str(), "author": st.session_state.get("user_name", st.session_state.get("user_login", "")), "fields": f"Расчёт «{calc.get('name', 'Расчёт')}» помечен удалённым"})
                            st.session_state.pop(confirm_key, None)
                            save_data(st.session_state.crm_store)
                            st.rerun()
                    with cancel_col:
                        if st.button("Отмена", key=f"calc_delete_no_{d['id']}_{calc['id']}", use_container_width=True):
                            st.session_state.pop(confirm_key, None)
                            st.rerun()

    if st.button("Добавить новый расчёт", key=f"calc_add_{d['id']}", type="primary", use_container_width=True):
        calc = {"id": uuid.uuid4().hex, "name": _calculation_display_name(d, {"id": "__new__"}, len(calculations)), "items": [],
                "delivery_amount": 0.0, "discount_type": "Без скидки", "individual_discount": 0.0,
                "total": 0.0, "deleted": False, "_draft": True, "created_at": now_str()}
        calculations.append(calc)
        save_data(st.session_state.crm_store)
        _push_dialog_return()
        st.session_state["dialog_calculation_deal_id"] = str(d["id"])
        st.session_state["dialog_calculation_calc_id"] = str(calc["id"])
        st.rerun()


@_crm_dialog("Расчёт сделки", width="large")
def deal_calculation_dialog(deal_id, calc_id):
    """Отдельное окно редактирования расчёта в стиле окон задач."""
    def _calc_refresh():
        # КП прикрепляется к блоку файлов родительского окна сделки, поэтому после его
        # создания нужно обновить всё приложение; прочие действия оставляют fragment rerun.
        if st.session_state.pop("_refresh_parent_deal_files", False):
            try:
                st.rerun(scope="app")
            except (TypeError, ValueError):
                st.rerun()
        elif st.session_state.get("_crm_inside_dialog_host", False):
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

    def _save_current_calc_before_document():
        """Считывает актуальные значения виджетов и сохраняет расчёт перед созданием документа."""
        calc["name"] = str(st.session_state.get(name_key, calc.get("name") or _calculation_display_name(deal, calc))).strip() or _calculation_display_name(deal, calc)
        calc["discount_type"] = st.session_state.get(f"{key}_discount_type", calc.get("discount_type", "Без скидки"))
        calc["delivery_amount"] = float(st.session_state.get(f"{key}_delivery", calc.get("delivery_amount", 0)) or 0)
        calc["individual_discount"] = float(st.session_state.get(f"{key}_individual_discount", calc.get("individual_discount", 0)) or 0)
        catalog_now = st.session_state.crm_store.get("products", DEFAULT_PRODUCT_CATALOG)
        products_now = {str(x.get("id", x.get("sku", ""))): x for x in catalog_now}
        for row in calc.get("items", []):
            rid = row.get("row_id")
            if not rid:
                continue
            old_pid = str(row.get("product_id", ""))
            pid = str(st.session_state.get(f"{key}_{rid}_product", old_pid))
            product_now = products_now.get(pid)
            if product_now:
                row["product_id"] = pid
                row["product_name"] = product_now.get("name", row.get("product_name", ""))
                row["unit"] = product_now.get("unit", row.get("unit", "шт."))
                row["unit_price"] = float(product_now.get("price", row.get("unit_price", 0)) or 0) if pid != old_pid else float(row.get("unit_price", product_now.get("price", 0)) or 0)
            row["color_ral"] = st.session_state.get(f"{key}_{rid}_color", row.get("color_ral", ""))
            row["quantity"] = float(st.session_state.get(f"{key}_{rid}_qty", row.get("quantity", 1)) or 0)
            row["discount"] = float(st.session_state.get(f"{key}_{rid}_discount", row.get("discount", 0)) or 0)
        calc["total"] = _deal_calc_total(calc)
        calc["_draft"] = False
        calc["updated_at"] = now_str()
        calc["updated_by"] = st.session_state.get("user_name", st.session_state.get("user_login", ""))
        deal["budget"] = calc["total"]
        deal["last_modified"] = now_str()
        save_data(st.session_state.crm_store)
        st.session_state[dirty_key] = False
        st.session_state[snapshot_key] = copy.deepcopy(calc)

    close_css = f"calc_close_row_{key}"
    st.markdown(f'''<style>
    .st-key-{close_css} .stButton > button {{width:100%!important;min-height:40px!important;padding:0.45rem 0.7rem!important;font-size:0.9rem!important;line-height:1.15!important;white-space:normal!important;}}
    .st-key-{close_css} .stButton > button:hover {{filter:brightness(0.97);}}
    .st-key-{close_css} [data-testid="column"]:last-child .stButton > button {{width:36px!important;min-width:36px!important;max-width:36px!important;height:36px!important;min-height:36px!important;max-height:36px!important;padding:0!important;font-size:1.1rem!important;line-height:1!important;white-space:nowrap!important;background:#FFFFFF!important;border:1px solid #DCE0E5!important;border-radius:8px!important;color:#5A6B7D!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0 auto!important;}}
    .st-key-{close_css} [data-testid="column"]:last-child .stButton > button:hover {{background:#EEF0F3!important;border-color:#C9CFD7!important;}}
    </style>''', unsafe_allow_html=True)
    with st.container(key=close_css):
        offer_col, invoice_col, torg_col, _spacer, close_col = st.columns([7.0, 7.0, 7.0, 5.0, 1.0])
        with offer_col:
            if st.button("Сформировать КП", key=f"{key}_make_offer", use_container_width=True, type="primary"):
                try:
                    _save_current_calc_before_document()
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
                    st.session_state["_refresh_parent_deal_files"] = True
                except Exception as exc:
                    st.session_state[f"{key}_doc_error"] = f"Не удалось сформировать КП: {exc}"
                _calc_refresh()
        with invoice_col:
            if st.button("Счёт на оплату", key=f"{key}_make_invoice", use_container_width=True):
                _save_current_calc_before_document()
                # Переключаем единое окно с расчёта на счёт: очищаем состояние
                # расчёта, чтобы диспетчер вкладки «Сделки» не открыл его снова.
                st.session_state.pop("dialog_calculation_deal_id", None)
                st.session_state.pop("dialog_calculation_calc_id", None)
                st.session_state["dialog_invoice_request"] = {"deal_id": deal_id, "calc_id": calc_id, "selected_requisite_id": ""}
                # При каждом новом открытии выбора плательщика он должен быть пустым,
                # а не восстанавливать значение из предыдущего запуска Streamlit.
                st.session_state.pop(f"invoice_req_select_{deal_id}_{calc_id}", None)
                invoice_document_dialog(deal_id, calc_id)
        with torg_col:
            if st.button("Товарная накладная ТОРГ-12", key=f"{key}_make_torg12", use_container_width=True):
                try:
                    _save_current_calc_before_document()
                    if not calc.get("items"):
                        raise ValueError("Добавь хотя бы одну товарную позицию в расчёт.")
                    calc["_draft"] = False
                    calc["updated_at"] = now_str()
                    deal["budget"] = calc["total"]
                    deal["last_modified"] = now_str()
                    save_data(st.session_state.crm_store)
                    client = get_client_by_id(deal.get("client_id")) or {}
                    pdf = _make_torg12_pdf(deal, client, calc)
                    filename = f"ТОРГ-12 №{_deal_doc_number(deal)} от {moscow_now().strftime('%d.%m.%Y')}.pdf"
                    _save_generated_document(deal, pdf, filename, "Товарная накладная ТОРГ-12", calc)
                    _open_pdf_link(pdf, filename, f"torg12_pdf_{deal_id}_{calc_id}")
                    st.session_state[f"{key}_doc_message"] = "Товарная накладная ТОРГ-12 сохранена в файлах сделки."
                    st.session_state["_refresh_parent_deal_files"] = True
                except Exception as exc:
                    st.session_state[f"{key}_doc_error"] = f"Не удалось сформировать ТОРГ-12: {exc}"
                _calc_refresh()
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
                    st.session_state.pop("dialog_calculation_deal_id", None)
                    st.session_state.pop("dialog_calculation_calc_id", None)
                    _pop_dialog_return()
                    st.rerun()

    _doc_error = st.session_state.pop(f"{key}_doc_error", None)
    if _doc_error:
        st.error(_doc_error)
    _doc_message = st.session_state.pop(f"{key}_doc_message", None)
    if _doc_message:
        st.success(_doc_message)
    _offer_pdf_state = st.session_state.get(f"offer_pdf_{deal_id}_{calc_id}")
    _torg12_pdf_state = st.session_state.get(f"torg12_pdf_{deal_id}_{calc_id}")
    _persisted_docs = [doc for doc in (deal.get("generated_documents", []) or [])
                       if str(doc.get("calculation_id", "")) == str(calc_id)]
    for _doc_kind, _state_key in (("Коммерческое предложение", f"offer_pdf_{deal_id}_{calc_id}"),
                                  ("Товарная накладная ТОРГ-12", f"torg12_pdf_{deal_id}_{calc_id}")):
        _matches = [doc for doc in _persisted_docs if doc.get("kind") == _doc_kind and doc.get("pdf_base64")]
        if _matches and not st.session_state.get(_state_key):
            _last_doc = max(_matches, key=lambda d: str(d.get("created_at", "")))
            st.session_state[_state_key] = {"data": _last_doc["pdf_base64"], "filename": _last_doc.get("file_name", "Документ.pdf")}
    _offer_pdf_state = st.session_state.get(f"offer_pdf_{deal_id}_{calc_id}")
    _torg12_pdf_state = st.session_state.get(f"torg12_pdf_{deal_id}_{calc_id}")
    if _offer_pdf_state or _torg12_pdf_state:
        _doc_cols = st.columns(2, gap="small")
        if _offer_pdf_state:
            with _doc_cols[0]:
                st.download_button("Скачать КП PDF",data=base64.b64decode(_offer_pdf_state["data"]),file_name=_offer_pdf_state["filename"],mime="application/pdf",key=f"offer_pdf_dl_{deal_id}_{calc_id}",use_container_width=True)
        if _torg12_pdf_state:
            with _doc_cols[1]:
                st.download_button("Скачать ТОРГ-12 PDF",data=base64.b64decode(_torg12_pdf_state["data"]),file_name=_torg12_pdf_state["filename"],mime="application/pdf",key=f"torg12_pdf_dl_{deal_id}_{calc_id}",use_container_width=True)
        st.divider()

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
    dtype_options = list(DISCOUNT_TYPES.keys())
    if calc.get("discount_type") not in dtype_options:
        calc["discount_type"] = "Без скидки"
    dtype_key = f"{key}_discount_type"
    def _on_discount_type_change():
        _new_type = st.session_state.get(dtype_key, "Без скидки")
        if _new_type == "Индивидуальная":
            _new_discount = float(st.session_state.get(f"{key}_individual_discount", calc.get("individual_discount", 0)) or 0)
        else:
            _new_discount = float(DISCOUNT_TYPES.get(_new_type, 0))
        for _row in calc.get("items", []):
            _rid = _row.get("row_id")
            if _rid:
                st.session_state[f"{key}_{_rid}_discount"] = _new_discount
                _row["discount"] = _new_discount
        st.session_state[dirty_key] = True
    name_col, dtype_col = st.columns([1.6, 1])
    with name_col:
        st.text_input("Название расчёта:", key=name_key, on_change=lambda: st.session_state.__setitem__(dirty_key, True))
    with dtype_col:
        selected_dtype = st.selectbox("Тип скидки:", dtype_options,
            index=dtype_options.index(calc.get("discount_type", "Без скидки")), key=dtype_key,
            on_change=_on_discount_type_change)
    st.divider()
    catalog = st.session_state.crm_store.get("products", DEFAULT_PRODUCT_CATALOG)
    active_products = [p for p in catalog if p.get("active", True)]
    if not active_products:
        st.warning("В каталоге нет активных товаров. Добавьте товары в разделе «Товары и прайс».")
        return
    items = calc.setdefault("items", [])
    custom_key = f"{key}_individual_discount"
    def _on_individual_discount_change():
        # Изменение общей индивидуальной скидки немедленно переносим во все строки.
        # Callback выполняется до повторного построения виджетов, поэтому можно
        # безопасно обновить их session_state, а затем и локальные данные расчёта.
        _new_discount = min(100.0, max(0.0, float(st.session_state.get(custom_key, 0) or 0)))
        for _row in calc.get("items", []):
            _rid = _row.get("row_id")
            if _rid:
                st.session_state[f"{key}_{_rid}_discount"] = _new_discount
            _row["discount"] = _new_discount
        st.session_state[dirty_key] = True

    if selected_dtype == "Индивидуальная":
        custom_col, *_ = st.columns([2.8, 1.05, 0.62, 1.15, 0.72, 0.72, 0.78])
        with custom_col:
            custom_default = st.number_input("Индивидуальная скидка, %", min_value=0.0, max_value=100.0,
                value=float(calc.get("individual_discount", 0) or 0), step=1.0, format="%g", key=custom_key,
                on_change=_on_individual_discount_change)
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
            # При смене товара показываем цену выбранной позиции из актуального прайса
            # сразу в этом же рендере, а не старую цену предыдущего товара.
            display_price = float(product.get("price", 0) or 0) if selected_pid != current_pid else float(item.get("unit_price", product.get("price", 0)) or 0)
            st.markdown(f"<div style='padding-top:0.15rem;text-align:right;font-size:0.8rem;color:#64748b;white-space:nowrap'>{display_price:,.0f} ₽</div>".replace(",", " "), unsafe_allow_html=True)
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
    st.markdown(f'<div style="text-align:right;color:#bc1661;font-size:1.45rem;font-weight:800;margin:0.35rem 0 0.55rem 0">Итого: {total:,.0f} ₽</div>'.replace(",", " "), unsafe_allow_html=True)
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
        # После сохранения оставляем окно расчёта открытым, чтобы можно было
        # продолжить работу с расчётом без повторного открытия окна.
        _calc_refresh()

def render_deal_detail(d, cl, cu, key_prefix):
    """Детали сделки в 2 колонки — как render_task_detail."""
    # Синхронизируем оплату Точки при просмотре сделки; проверки ограничены интервалом в минуту.
    for _calc in d.get("calculations", []) or []:
        _tochka_auto_refresh_payment_status(d, _calc)
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
            st.markdown(f"**Клиент:** {cl.get('name', '—') if cl else '—'}")
            st.markdown(f"**Бюджет:** {d.get('budget', 0):,.0f} руб.".replace(",", " "))
            ps = d.get("payment_status", "Не оплачено")
            mgr_options_dd = get_managers_list()
            current_mgr_dd = d.get("manager", "")
            current_idx_dd = mgr_options_dd.index(current_mgr_dd) if current_mgr_dd in mgr_options_dd else 0
            _bank_payment_status = _tochka_bank_payment_status(d)
            _pay_col, _mgr_col = st.columns(2)
            with _pay_col:
                inject_payment_container_css(deal_id, ps)
                with st.container(key=f"ps_wrap_{deal_id}"):
                    new_ps = st.selectbox("Статус оплаты:", ["Не оплачено", "Оплачен частично", "Оплачено"], index=["Не оплачено", "Оплачен частично", "Оплачено"].index(ps) if ps in ["Не оплачено", "Оплачен частично", "Оплачено"] else 0, key=f"dls_ps_{deal_id}")
                if _bank_payment_status and _bank_payment_status != ps:
                    st.markdown(
                        f"<div style='font-size:0.78rem;color:#7B8490;font-style:italic;margin-top:-0.35rem;'>Внимание: статус CRM не совпадает с данными банка (по данным банка: {html.escape(_bank_payment_status)}).</div>",
                        unsafe_allow_html=True,
                    )
            with _mgr_col:
                new_mgr_dd = st.selectbox("Ответственный:", mgr_options_dd, index=current_idx_dd, key=f"deal_mgr_inline_{deal_id}", placeholder=MGR_PLACEHOLDER)
            if new_ps != ps:
                d["payment_status"] = new_ps
                d["payment_status_manual_override"] = True
                d["last_modified"] = now_str()
                _sync_deal_board_stage_from_payment(d)
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
            elif current_status in ("В работе", "Оплачено"):
                st.markdown(f"<div style='font-size:1rem;font-weight:600;margin:0.4rem 0;'>Статус: {html.escape(current_status)}</div>", unsafe_allow_html=True)
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
            # Кнопки завершения и архивации доступны в любой колонке/статусе сделки.
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
                render_soft_delete_comments(d["deal_comments"], f"deal_{deal_id}", "time", "author")
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
                    d.setdefault("deal_comments", []).append({"time": moscow_now().strftime("%d.%m.%Y %H:%M"), "author": st.session_state.get("user_name", ""), "text": nc.strip()})
                    d["last_modified"] = now_str()
                    st.session_state[dc_clr_key] = True
                    commit_and_rerun(st.session_state.crm_store, "Комментарий добавлен")
                else:
                    st.warning("Введите текст")
            st.markdown("---")
            st.markdown("**Файлы сделки:**")
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
            render_deal_products_block(d, key_prefix)
            st.markdown("---")
            _deal_tasks_list = [task for task in (cl.get("tasks", []) if cl else []) if str(task.get("deal_id", "")) == str(deal_id)]
            _deal_tasks_list.sort(key=lambda task: task.get("created_at", ""), reverse=True)
            if _deal_tasks_list:
                st.markdown("**Задачи по сделке**")
                for _ti, _task in enumerate(_deal_tasks_list):
                    _task_col, _date_col, _open_col = st.columns([2, 2, 1])
                    with _task_col:
                        _task_number_label = html.escape(str(_task.get("task_number", "")))
                        _task_type_label = html.escape(str(_task.get("type", "Связаться") or "Связаться"))
                        st.markdown(f"**{_task_number_label}** · {_task_type_label}")
                    with _date_col:
                        _created = str(_task.get("created_at", "") or "")
                        try:
                            _created_dt = datetime.strptime(_created[:19], "%Y-%m-%d %H:%M:%S")
                            _created_label = _created_dt.strftime("Создано %d.%m.%Y, %H:%M")
                        except Exception:
                            _created_label = f"Создано {_created}" if _created else "Создано —"
                        st.markdown(f"<div style='font-size:0.82rem;font-style:italic;color:#7B8490;'>{html.escape(_created_label)}</div>", unsafe_allow_html=True)
                    with _open_col:
                        if st.button("Открыть", key=f"deal_task_open_{deal_id}_{_ti}", use_container_width=True):
                            _push_dialog_return()
                            st.session_state["dialog_task_number"] = str(_task.get("task_number", ""))
                            st.session_state["dialog_task_client_id"] = cl.get("id") if cl else d.get("client_id")
                            st.session_state["dialog_task_deal_id"] = str(deal_id)
                            st.session_state["dialog_task_key"] = f"deal_task_{deal_id}_{_task.get('task_number', '')}"
                            st.rerun()
            else:
                st.caption("Задач по сделке пока нет.")
            _dls_ct_key = f"dls_show_ct_{deal_id}"
            if st.button("Создать задачу по сделке", key=f"dls_btn_ct_detail_{deal_id}", use_container_width=True, type="primary"):
                _push_dialog_return()
                st.session_state["dialog_create_deal_task_deal_id"] = deal_id
                st.session_state["dialog_create_deal_task_client_id"] = d["client_id"]
                st.rerun()
            st.markdown("<hr style='border:0;height:1px;background:#DCE0E5;margin:0.8rem 0;'>", unsafe_allow_html=True)
            st.markdown("**Внесённые изменения**")
            _deal_changes = d.get("change_log", [])
            if _deal_changes:
                for _chg in reversed(_deal_changes[-20:]):
                    st.markdown(f"<div class='created-date'>{_chg.get('date', '')} | {_chg.get('author', '')} — {_chg.get('fields', '')}</div>", unsafe_allow_html=True)
            else:
                st.caption("История изменений появится после редактирования сделки.")
            # Кнопка паузы/возврата в самом низу правой колонки, по ширине как «Создать напоминание».
            _stage_now = d.get("status", "Новый")
            if _stage_now in ("В работе", "Оплачено", "Ожидание оплаты", "На паузе"):
                st.markdown("<hr style='border:0;height:1px;background:#DCE0E5;margin:0.8rem 0;'>", unsafe_allow_html=True)
                if _stage_now == "На паузе" and d.get("pause_reason"):
                    st.markdown(f"<div style='font-size:0.9rem;color:#505866;margin:0.35rem 0 0.75rem;'><b>Сделка на паузе по причине:</b> {html.escape(str(d['pause_reason']))}.</div>", unsafe_allow_html=True)
                if _stage_now != "На паузе":
                    _pause_reason = st.text_area("Причина:", key=f"dls_pause_reason_{deal_id}", height=90, placeholder="Укажите причину паузы")
                else:
                    _pause_reason = ""
                _pause_spacer1, _pause_btn_col, _pause_spacer2 = st.columns([1, 2, 1])
                with _pause_btn_col:
                    if _stage_now == "На паузе":
                        _pause_action_clicked = st.button("Вернуть в работу", key=f"dls_unpause_{deal_id}", use_container_width=True)
                    else:
                        _pause_action_clicked = st.button("Поставить на паузу", key=f"dls_pause_{deal_id}", use_container_width=True)
                if _pause_action_clicked:
                    if _stage_now == "На паузе":
                        d["status"] = "Оплачено" if d.get("payment_status") == "Оплачено" else ("Ожидание оплаты" if _deal_has_active_payment_document(d) else "В работе")
                        d.pop("paused_from_status", None)
                        _pause_message = "Сделка возвращена из паузы"
                    elif not _pause_reason.strip():
                        st.warning("Укажите причину, прежде чем поставить сделку на паузу.")
                        st.stop()
                    else:
                        d["paused_from_status"] = _stage_now
                        d["pause_reason"] = _pause_reason.strip()
                        d["status"] = "На паузе"
                        _pause_message = "Сделка поставлена на паузу"
                    d["last_modified"] = now_str()
                    commit_and_rerun(st.session_state.crm_store, _pause_message)


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
            render_soft_delete_comments(cl.get("client_comments", []), f"client_{cl['id']}", "time", "author")
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
                    cl.setdefault("client_comments", []).append({"time": moscow_now().strftime("%d.%m.%Y %H:%M"), "author": st.session_state.get("user_name", ""), "text": nci.strip()})
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
            # Список задач по клиенту — сразу под блоком файлов
            _client_only_tasks = [t for t in cl.get("tasks", []) if not t.get("deal_id")]
            _client_only_tasks.sort(key=lambda task: task.get("created_at", ""), reverse=True)
            st.markdown(f"**Список задач по клиенту ({len(_client_only_tasks)})**")
            if _client_only_tasks:
                for _ti, _task in enumerate(_client_only_tasks):
                    _task_col, _date_col, _open_col = st.columns([2, 2, 1])
                    with _task_col:
                        _task_number_label = html.escape(str(_task.get("task_number", "")))
                        _task_type_label = html.escape(str(_task.get("type", "Связаться") or "Связаться"))
                        st.markdown(f"**{_task_number_label}** · {_task_type_label}")
                    with _date_col:
                        _created = str(_task.get("created_at", "") or "")
                        try:
                            _created_dt = datetime.strptime(_created[:19], "%Y-%m-%d %H:%M:%S")
                            _created_label = _created_dt.strftime("Создано %d.%m.%Y, %H:%M")
                        except Exception:
                            _created_label = f"Создано {_created}" if _created else "Создано —"
                        st.markdown(f"<div style='font-size:0.82rem;font-style:italic;color:#7B8490;'>{html.escape(_created_label)}</div>", unsafe_allow_html=True)
                    with _open_col:
                        if st.button("Открыть", key=f"client_task_open_{cl['id']}_{_ti}", use_container_width=True):
                            _push_dialog_return()
                            for _stale_key in ("dialog_client_requisites_client_id", "dialog_invoice_request", "_pending_reminder_dialog", "dialog_task_completion", "dialog_deal_report", "dialog_create_deal_task_deal_id", "dialog_create_client_task_client_id", "dialog_create_client_task_deal_select_cl_id"):
                                st.session_state.pop(_stale_key, None)
                            st.session_state["dialog_task_number"] = str(_task.get("task_number", ""))
                            st.session_state["dialog_task_client_id"] = str(cl.get("id", ""))
                            st.session_state["dialog_task_deal_id"] = ""
                            st.session_state["dialog_task_key"] = f"client_task_{cl['id']}_{_task.get('task_number', '')}"
                            st.session_state["active_tab"] = "Клиенты"
                            st.rerun()
            else:
                st.caption("Задач по клиенту пока нет.")
            if st.button("Добавить задачу по клиенту", key=f"rcc_task_{cl['id']}", use_container_width=True, type="primary"):
                _push_dialog_return()
                st.session_state["dialog_create_client_task_client_id"] = cl["id"]
                st.session_state.pop("dialog_client_key", None)
                st.rerun()

            st.markdown('<hr style="border:0;height:1px;background:#DCE0E5;margin:0.8rem 0;">', unsafe_allow_html=True)

            # Список сделок клиента — в том же стиле, что список задач по сделке
            _client_deals_list = [deal for deal in st.session_state.crm_store.get("deals", []) if str(deal.get("client_id", "")) == str(cl.get("id", ""))]
            _client_deals_list.sort(key=lambda deal: deal.get("created_at", ""), reverse=True)
            st.markdown(f"**Список сделок ({len(_client_deals_list)})**")
            if _client_deals_list:
                for _di, _deal in enumerate(_client_deals_list):
                    _deal_col, _date_col, _open_col = st.columns([2, 2, 1])
                    with _deal_col:
                        _deal_number = html.escape(str(_deal.get("deal_number", _deal.get("title", ""))))
                        _deal_title = html.escape(str(_deal.get("deal_title", "") or ""))
                        _deal_status = html.escape(str(_deal.get("status", "Новый") or "Новый"))
                        st.markdown(f"**{_deal_number}** · {_deal_title} <span style='color:#7B8490'>({ _deal_status })</span>", unsafe_allow_html=True)
                    with _date_col:
                        _created = str(_deal.get("created_at", "") or "")
                        try:
                            _created_dt = datetime.strptime(_created[:19], "%Y-%m-%d %H:%M:%S")
                            _created_label = _created_dt.strftime("Создано %d.%m.%Y, %H:%M")
                        except Exception:
                            _created_label = f"Создано {_created}" if _created else "Создано —"
                        st.markdown(f"<div style='font-size:0.82rem;font-style:italic;color:#7B8490;'>{html.escape(_created_label)}</div>", unsafe_allow_html=True)
                    with _open_col:
                        if st.button("Открыть", key=f"client_deal_open_{cl['id']}_{_di}", use_container_width=True):
                            _push_dialog_return()
                            st.session_state.pop("dialog_client_key", None)
                            st.session_state["dialog_deal_key"] = _deal["id"]
                            st.rerun()
            else:
                st.caption("Сделок пока нет.")
            if st.button("Добавить сделку", key=f"rcc_deal_{cl['id']}", use_container_width=True, type="primary"):
                _push_dialog_return()
                st.session_state["dialog_create_deal_from_client"] = cl["id"]
                st.session_state.pop("dialog_client_key", None)
                st.rerun()

            st.markdown('<hr style="border:0;height:1px;background:#DCE0E5;margin:0.8rem 0;">', unsafe_allow_html=True)
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
                        # «Открыть» показывает сохранённую запись в отдельном окне просмотра.
                        # Значения читаются непосредственно из актуального объекта клиента,
                        # без ключей виджетов редактора, которые могли содержать пустое состояние.
                        st.session_state["dialog_client_requisites_view"] = {"client_id": cl["id"], "return_to_invoice": False, "requisite_id": _req.get("id")}
                        st.rerun()
                with _req_cols[2]:
                    _req_confirm_key = f"client_req_del_confirm_{cl['id']}_{_req.get('id',_ri)}"
                    if not _req.get("deleted") and st.button("Удалить", key=f"client_req_del_{cl['id']}_{_req.get('id',_ri)}", use_container_width=True):
                        st.session_state[_req_confirm_key] = True
                        st.rerun()
                if not _req.get("deleted") and st.session_state.get(_req_confirm_key):
                    st.warning(f"Удалить реквизиты «{_req_name}»? Они останутся в истории карточки клиента.")
                    _req_yes, _req_no = st.columns(2)
                    with _req_yes:
                        if st.button("Да, удалить", key=f"client_req_del_yes_{cl['id']}_{_req.get('id',_ri)}", type="primary", use_container_width=True):
                            _req["deleted"] = True
                            _req["deleted_at"] = now_str()
                            _req["deleted_by"] = st.session_state.get("user_name", st.session_state.get("user_login", ""))
                            cl["last_modified"] = now_str()
                            cl.setdefault("change_log", []).append({"date": now_str(), "author": st.session_state.get("user_name", st.session_state.get("user_login", "")), "fields": f"Реквизиты «{_req_name}» помечены удалёнными"})
                            st.session_state.pop(_req_confirm_key, None)
                            save_data(st.session_state.crm_store)
                            st.rerun()
                    with _req_no:
                        if st.button("Отмена", key=f"client_req_del_no_{cl['id']}_{_req.get('id',_ri)}", use_container_width=True):
                            st.session_state.pop(_req_confirm_key, None)
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
                cd_mgr = st.selectbox("Ответственный:", get_managers_list(), index=None, key=f"cd_mgr_{cl['id']}", placeholder=MGR_PLACEHOLDER)
                cd_budget = st.text_input("Бюджет (руб.):", value="", key=f"cd_budget_{cl['id']}", placeholder="Введите сумму")
                cd_ps = st.selectbox("Статус оплаты:", ["Не оплачено", "Оплачен частично", "Оплачено"], index=0, key=f"cd_ps_{cl['id']}")
                if st.button("Создать", key=f"cd_go_{cl['id']}", use_container_width=True, type="primary"):
                    deals = st.session_state.crm_store.get("deals", [])
                    did = f"deal_{moscow_now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
                    dn = generate_deal_number()
                    new_deal = {"id": did, "client_id": cl["id"], "title": dn, "deal_number": dn, "deal_title": cd_title.strip(), "budget": int(cd_budget) if cd_budget and cd_budget.strip().isdigit() else 0, "status": "В работе", "manager": cd_mgr or "", "deal_comments": [], "deal_files": [], "payment_status": cd_ps, "close_files": [], "archive_files": [], "last_modified": now_str(), "created_at": now_str(), "created_by": st.session_state.get("user_login", ""), "change_log": [], "deal_chat": []}
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
            _fcc_clicked = st.button("Добавить комментарий", key=f"cc_form_btn_{fv}", use_container_width=True)
            if _fcc_clicked:
                if ncc.strip():
                    st.session_state.setdefault("pending_client_comments", []).append({"time": moscow_now().strftime("%d.%m.%Y %H:%M"), "text": ncc.strip()})
                    st.session_state[cc_form_clr] = True
                    st.rerun()
                else: st.warning("Введите текст")
            if st.session_state.get("pending_client_comments"):
                for _pci, pc in enumerate(st.session_state["pending_client_comments"]):
                    _pc_row, _pc_del = st.columns([10, 1])
                    with _pc_row:
                        _pc_text = html.escape(str(pc.get("text", "")))
                        _pc_line = f"- *{pc.get('time', '')}*: {_pc_text}"
                        st.markdown(f"<s>{_pc_line}</s>" if pc.get("deleted") else _pc_line, unsafe_allow_html=True)
                    with _pc_del:
                        if not pc.get("deleted") and st.button("×", key=f"pending_comment_delete_{fv}_{_pci}", help="Удалить комментарий"):
                            st.session_state[f"pending_comment_confirm_{fv}_{_pci}"] = True
                    _pck = f"pending_comment_confirm_{fv}_{_pci}"
                    if st.session_state.get(_pck) and not pc.get("deleted"):
                        st.warning("Удалить комментарий? Он останется зачёркнутым.")
                        _pc_yes, _pc_no = st.columns(2)
                        with _pc_yes:
                            if st.button("Подтвердить", key=f"pending_comment_yes_{fv}_{_pci}", type="primary"):
                                pc["deleted"] = True
                                st.session_state.pop(_pck, None)
                                st.rerun()
                        with _pc_no:
                            if st.button("Отмена", key=f"pending_comment_no_{fv}_{_pci}"):
                                st.session_state.pop(_pck, None)
                                st.rerun()
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
            _new_name_norm = re.sub(r"\s+", " ", cn.strip()).casefold()
            _new_phone_norm = re.sub(r"\D", "", cp)
            _dupes = []
            for _existing in st.session_state.crm_store.get("clients", []):
                _old_name_norm = re.sub(r"\s+", " ", str(_existing.get("name", "")).strip()).casefold()
                _old_phone_norm = re.sub(r"\D", "", str(_existing.get("phone", "")))
                _phone_match = bool(_new_phone_norm and _old_phone_norm and ( _new_phone_norm == _old_phone_norm or (len(_new_phone_norm) >= 10 and len(_old_phone_norm) >= 10 and _new_phone_norm[-10:] == _old_phone_norm[-10:])))
                if _phone_match or (_new_name_norm and _new_name_norm == _old_name_norm):
                    _dupes.append(_existing)
            if _dupes:
                st.warning("Возможный дубль клиента уже существует:")
                for _dup in _dupes[:5]:
                    st.markdown(f"- **{html.escape(str(_dup.get('name', '')))}** · {html.escape(str(_dup.get('phone', '')))}")
            elif not cm: st.error("Выберите ответственного")
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
                    if _et_type_key in st.session_state and st.session_state[_et_type_key] in ("Отправить заказ", "Отправить образцы"):
                        t["text"] = st.session_state[_et_type_key]
                    elif _et_topic_key in st.session_state:
                        t["text"] = st.session_state[_et_topic_key]
                    elif t.get("type") in ("Отправить заказ", "Отправить образцы"):
                        t["text"] = t.get("type", "")
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
                    _et_city_key = f"edit_city_{key_prefix}"
                    _et_recv_key = f"edit_recv_{key_prefix}"
                    _et_rphone_key = f"edit_rphone_{key_prefix}"
                    _et_pay_key = f"edit_pay_{key_prefix}"
                    _et_amount_key = f"edit_amount_{key_prefix}"
                    _et_tk_key = f"edit_tk_{key_prefix}"
                    if _et_prod_key in st.session_state: t["products"] = st.session_state[_et_prod_key]
                    if _et_addr_key in st.session_state: t["ship_addr"] = st.session_state[_et_addr_key]
                    if _et_city_key in st.session_state: t["ship_city"] = st.session_state[_et_city_key]
                    if _et_recv_key in st.session_state: t["receiver"] = st.session_state[_et_recv_key]
                    if _et_rphone_key in st.session_state: t["receiver_phone"] = st.session_state[_et_rphone_key]
                    if _et_pay_key in st.session_state: t["ship_pay"] = st.session_state[_et_pay_key]
                    if _et_amount_key in st.session_state:
                        _amt = st.session_state[_et_amount_key]
                        try:
                            t["order_amount"] = round(float(str(_amt).replace(",", ".")), 2) if _amt and str(_amt).strip() else 0
                        except (TypeError, ValueError):
                            t["order_amount"] = 0
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
            next_values["comment"] = st.text_input("Комментарий:", key=f"task_completion_next_comment_{key_prefix}")
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
                        "task_comments": [], "flagged": False, "products": "", "ship_city": "", "ship_addr": "", "receiver": "",
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
        cd_mgr = st.selectbox("Ответственный:", get_managers_list(), index=None, key=f"cdlg_mgr_{cl_id}", placeholder=MGR_PLACEHOLDER)
        cd_budget = st.text_input("Бюджет (руб.):", value="", key=f"cdlg_budget_{cl_id}", placeholder="Введите сумму")
        cd_ps = st.selectbox("Статус оплаты:", ["Не оплачено", "Оплачен частично", "Оплачено"], index=0, key=f"cdlg_ps_{cl_id}")
    with _deal_create_right:
        st.markdown("**Комментарии**")
        cd_comment = st.text_area("Комментарий:", key=f"cdlg_comment_{cl_id}", placeholder="Введите новый комментарий...", height=68, label_visibility="collapsed")
        cd_files = st.file_uploader("Файлы сделки:", key=f"cdlg_files_{cl_id}", accept_multiple_files=True)
    if st.button("Создать", key=f"cdlg_go_{cl_id}", use_container_width=True, type="primary"):
        deals = st.session_state.crm_store.get("deals", [])
        did = f"deal_{moscow_now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
        dn = generate_deal_number()
        new_deal = {"id": did, "client_id": cl_id, "title": dn, "deal_number": dn, "deal_title": cd_title.strip(),
                    "budget": int(cd_budget) if cd_budget and cd_budget.strip().isdigit() else 0,
                    "status": "В работе", "manager": cd_mgr or "", "payment_status": cd_ps,
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
                    task_detail_dialog(t, cl, None, f"clienttask_{cl_id}_{t.get('task_number', '')}_client")
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
                    task_detail_dialog(t, cl, d, f"clienttask_{cl_id}_{t.get('task_number', '')}_{d.get('id', '')}")
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
        # Индексируем сделки один раз: не просматриваем всю базу для каждого клиента.
        _clients_deals_by_id = {}
        for _deal_item in st.session_state.crm_store.get("deals", []):
            _clients_deals_by_id.setdefault(_deal_item.get("client_id"), []).append(_deal_item)

        # Карточки клиентов в том же визуальном стиле, что и задачи/сделки:
        # пастельный фон, тонкая рамка, цветной акцент слева и компактные метаданные.
        _client_cards_css = []
        for _style_client in _visible_clients:
            _style_id = _style_client["id"]
            _style_deals = _clients_deals_by_id.get(_style_id, [])
            _style_active_deals = any(_sd.get("status", "Новый") in ("Новый", "В работе") for _sd in _style_deals)
            _style_tasks = _style_client.get("tasks", [])
            _style_overdue_tasks = any(not _st.get("done") and is_task_overdue(_st) for _st in _style_tasks)
            _style_active_tasks = any(not _st.get("done") for _st in _style_tasks)
            _style_accent = "#C62828" if _style_overdue_tasks else ("#4CAF50" if _style_active_tasks or _style_active_deals else "#AAB4C0")
            _style_bg = "#F8FAFC" if _style_accent == "#AAB4C0" else ("#FFF8F8" if _style_accent == "#C62828" else "#F5FBF6")
            _client_cards_css.append(f"""
            .st-key-client_card_{_style_id} {{
                background:{_style_bg}!important; border:1px solid #E0E6EF!important;
                border-left:4px solid {_style_accent}!important; border-radius:9px!important;
                padding:0.45rem 0.7rem 0.25rem 0.7rem!important; margin:0.35rem 0!important;
                box-shadow:0 1px 2px rgba(30,45,65,0.04)!important;
            }}
            .st-key-client_card_{_style_id} .stButton > button {{
                min-height:35px!important; height:auto!important; padding:0.3rem 0.35rem!important;
                border-radius:6px!important; white-space:normal!important;
            }}
            .st-key-client_name_{_style_id} button {{
                background:transparent!important; border:0!important; box-shadow:none!important;
                color:#2C3E50!important; font-weight:700!important; font-size:0.94rem!important;
                text-align:left!important; justify-content:flex-start!important; padding:0.15rem 0!important;
            }}
            .st-key-client_name_{_style_id} button:hover {{ color:#BC1661!important; }}
            .st-key-client_deals_{_style_id}, .st-key-client_tasks_{_style_id} {{
                display:flex!important; justify-content:center!important; align-items:center!important;
            }}
            .st-key-client_deals_{_style_id} [data-testid='stButton'], .st-key-client_tasks_{_style_id} [data-testid='stButton'] {{
                width:100%!important; display:flex!important; justify-content:center!important;
            }}
            .st-key-client_deals_{_style_id} button,.st-key-client_tasks_{_style_id} button {{
                width:100%!important; margin:0 auto!important; background:rgba(255,255,255,0.65)!important; border:1px solid #E0E6EF!important;
                box-shadow:none!important; font-weight:700!important; font-size:0.82rem!important;
            }}
            .st-key-client_deals_{_style_id} button {{ color:{'#2E7D32' if _style_active_deals else '#526174'}!important; }}
            .st-key-client_tasks_{_style_id} button {{ color:{'#C62828' if _style_overdue_tasks else ('#2E7D32' if _style_active_tasks else '#526174')}!important; }}
            .st-key-client_deals_{_style_id} button:hover,.st-key-client_tasks_{_style_id} button:hover {{ border-color:#BC1661!important; }}
            """)
        if _client_cards_css:
            st.markdown("<style>" + "".join(_client_cards_css) + "</style>", unsafe_allow_html=True)

        # Единая шапка колонок для всего списка клиентов.
        # Используем CSS sticky непосредственно на контейнере Streamlit:
        # JS внутри st.components.v1.html работает в sandboxed iframe и не может
        # надёжно управлять DOM родительской страницы.
        st.markdown("""<style>
        .st-key-clients_columns_header {
            position: sticky !important;
            top: 0 !important;
            z-index: 99999 !important;
            background: #FFFFFF !important;
            border-bottom: 1px solid #DCE2EA !important;
            padding: 0.28rem 0 !important;
            margin-top: 0.15rem !important;
            box-shadow: 0 4px 7px rgba(30,45,65,0.12) !important;
            box-sizing: border-box !important;
        }
        .st-key-clients_columns_header p { margin: 0 !important; }
        .st-key-clients_columns_header [data-testid='stMarkdownContainer'] { height:100% !important; }
        .st-key-clients_columns_header [data-testid='stMarkdownContainer'] > div {
            min-height: 30px !important; height:100% !important;
            display:flex !important; align-items:center !important; justify-content:center !important;
        }
        .st-key-clients_columns_header [data-testid='stHorizontalBlock'] {
            align-items: stretch !important;
        }
        .st-key-clients_columns_header [data-testid='stColumn'] {
            display:flex !important; align-items:center !important; justify-content:center !important;
        }
        .st-key-clients_columns_header [data-testid='stMarkdownContainer'] > div > div {
            width:100% !important; text-align:center !important;
        }
        /* Кнопки счётчиков строго по центру тех же колонок, что и заголовки. */
        .st-key-client_deals_ [data-testid='stButton'] { width:100%; }
        </style>""", unsafe_allow_html=True)
        with st.container(key="clients_columns_header"):
            _h_main, _h_city, _h_phone, _h_category, _h_deals, _h_tasks, _h_sum = st.columns([3.4, 1.35, 1.65, 1.35, 0.8, 0.8, 1.5], gap="small")
            with _h_main: st.markdown("<div style='width:100%;font-weight:700;font-size:.78rem;color:#526174;text-align:left;padding:.2rem 0'>Клиент</div>", unsafe_allow_html=True)
            with _h_city: st.markdown("<div style='width:100%;font-weight:700;font-size:.78rem;color:#526174;text-align:center;padding:.2rem 0'>Город</div>", unsafe_allow_html=True)
            with _h_phone: st.markdown("<div style='width:100%;font-weight:700;font-size:.78rem;color:#526174;text-align:center;padding:.2rem 0'>Телефон</div>", unsafe_allow_html=True)
            with _h_category: st.markdown("<div style='width:100%;font-weight:700;font-size:.78rem;color:#526174;text-align:center;padding:.2rem 0'>Категория</div>", unsafe_allow_html=True)
            with _h_deals: st.markdown("<div style='width:100%;font-weight:700;font-size:.75rem;color:#2C3E50;text-align:center;padding:.2rem 0;transform:translateX(-4px)'>Сделки</div>", unsafe_allow_html=True)
            with _h_tasks: st.markdown("<div style='width:100%;font-weight:700;font-size:.75rem;color:#2C3E50;text-align:center;padding:.2rem 0;transform:translateX(-15px)'>Задачи</div>", unsafe_allow_html=True)
            with _h_sum: st.markdown("<div style='width:100%;font-weight:700;font-size:.75rem;color:#2C3E50;text-align:center;padding:.2rem 0;transform:translateX(-15px)'>Сумма сделок</div>", unsafe_allow_html=True)

        for cl in _visible_clients:
            cl_deals = _clients_deals_by_id.get(cl["id"], [])
            cl_tasks_all = cl.get("tasks", [])
            deals_sum = sum(d.get("budget", 0) for d in cl_deals)
            has_active_deals = any(d.get("status", "Новый") in ("Новый", "В работе") for d in cl_deals)
            has_overdue_tasks = any(not t.get("done") and is_task_overdue(t) for t in cl_tasks_all)
            has_active_tasks = any(not t.get("done") for t in cl_tasks_all)
            _cid = cl["id"]
            with st.container(key=f"client_card_{_cid}"):
                _main_col, _city_col, _phone_col, _category_col, _deals_col, _tasks_col, _sum_col = st.columns([3.4, 1.35, 1.65, 1.35, 0.8, 0.8, 1.5], gap="small")
                with _main_col:
                    with st.container(key=f"client_name_{_cid}"):
                        if st.button(cl.get("name", "Без названия"), key=f"tbl_name_{_cid}", use_container_width=True):
                            st.session_state["dialog_client_key"] = _cid
                with _city_col:
                    st.markdown(f"<div style='font-size:.78rem;color:#68778A;padding-top:.55rem;text-align:center;overflow-wrap:anywhere'>{html.escape(str(cl.get('city', '') or '—'))}</div>", unsafe_allow_html=True)
                with _phone_col:
                    st.markdown(f"<div style='font-size:.78rem;color:#68778A;padding-top:.55rem;text-align:center;overflow-wrap:anywhere'>{html.escape(str(cl.get('phone', '') or '—'))}</div>", unsafe_allow_html=True)
                with _category_col:
                    st.markdown(f"<div style='font-size:.78rem;color:#526174;padding-top:.55rem;text-align:center;overflow-wrap:anywhere'>{html.escape(str(cl.get('category', 'Не определён') or 'Не определён'))}</div>", unsafe_allow_html=True)
                with _deals_col:
                    with st.container(key=f"client_deals_{_cid}"):
                        if st.button(str(len(cl_deals)), key=f"tbl_deals_btn_{_cid}", use_container_width=True):
                            st.session_state["dialog_client_deals_key"] = _cid
                with _tasks_col:
                    with st.container(key=f"client_tasks_{_cid}"):
                        if st.button(str(len(cl_tasks_all)), key=f"tbl_tasks_{_cid}", use_container_width=True):
                            st.session_state["dialog_client_tasks_key"] = _cid
                with _sum_col:
                    _sum_str = f"{deals_sum:,.0f} руб.".replace(",", " ")
                    st.markdown(f"<div style='font-size:.84rem;font-weight:750;color:#2C3E50;text-align:center;padding-top:.15rem;white-space:nowrap'>{_sum_str}</div>", unsafe_allow_html=True)
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
    _req_view_state = st.session_state.get("dialog_client_requisites_view")
    _req_dialog_client_id = st.session_state.get("dialog_client_requisites_client_id")
    _invoice_dialog_state = st.session_state.get("dialog_invoice_request")
    _client_tab_calc_deal_id = st.session_state.get("dialog_calculation_deal_id")
    _client_tab_calc_id = st.session_state.get("dialog_calculation_calc_id")
    # Расчёт — дочернее окно сделки. Оно должно иметь приоритет над карточкой
    # клиента/сделки, иначе старое состояние родительского окна перехватывает rerun.
    if _req_view_state:
        client_requisites_view_dialog(_req_view_state.get("client_id"), bool(_req_view_state.get("return_to_invoice")), _req_view_state.get("requisite_id"))
    elif _client_tab_calc_deal_id and _client_tab_calc_id:
        _client_tab_calc_deal = next((d for d in st.session_state.crm_store.get("deals", []) if str(d.get("id")) == str(_client_tab_calc_deal_id)), None)
        _client_tab_calc = next((c for c in (_client_tab_calc_deal or {}).get("calculations", []) if str(c.get("id")) == str(_client_tab_calc_id) and not c.get("deleted")), None)
        if _client_tab_calc_deal and _client_tab_calc:
            # Consume the one-shot legacy request before opening the workspace tab.
            # Leaving these IDs in session_state causes every later button click to
            # dispatch the calculation dialog again and steal the interaction.
            st.session_state.pop("dialog_calculation_deal_id", None)
            st.session_state.pop("dialog_calculation_calc_id", None)
            deal_calculation_dialog(_client_tab_calc_deal_id, _client_tab_calc_id)
        else:
            st.session_state.pop("dialog_calculation_deal_id", None)
            st.session_state.pop("dialog_calculation_calc_id", None)
    elif _req_dialog_client_id:
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
        closed_deals.sort(key=lambda d: str(d.get("last_modified") or d.get("created_at") or ""), reverse=True)
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
        arch_deals.sort(key=lambda d: str(d.get("last_modified") or d.get("created_at") or ""), reverse=True)
        if arch_deals:
            for d in arch_deals:
                render_deal_standalone(d, cid_map.get(d.get("client_id")), cu)
        else:
            st.caption("Архив пуст.")
    # Search + manager filter — same style as Clients tab
    with st.container(key="deals_sticky_header"):
        fc1, fc2, fc3 = st.columns([3, 2.4, 2])
        with fc1:
            _deal_search_now = st.text_input("Поиск", key="deal_tab_search", placeholder="Поиск...", label_visibility="collapsed")
            deal_search = (_deal_search_now or "").strip().lower()
        with fc2:
            deal_sort_mode = st.selectbox(
                "Сортировка", ["По дате создания", "По дате изменения", "По номеру сделки"],
                index=1, key="deal_tab_sort", label_visibility="collapsed"
            )
        with fc3:
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
    # Пять активных колонок: новые, в работе, ожидание оплаты, оплачено, на паузе.
    fdeals = []
    _board_stage_changed = False
    for d in all_deals:
        _old_board_stage = d.get("status", "Новый")
        _sync_deal_board_stage_from_payment(d)
        if d.get("status", "Новый") != _old_board_stage:
            _board_stage_changed = True
        s = d.get("status", "Новый")
        if s not in ("Новый", "В работе", "Ожидание оплаты", "Оплачено", "На паузе"):
            continue
        cl = cid_map.get(d.get("client_id"))
        if mgr_filter != "Все" and d.get("manager", "") != mgr_filter:
            continue
        if deal_search:
            hay = f"{d.get('deal_number', '')} {d.get('deal_title', '')} {d.get('title', '')} {(cl.get('name', '') if cl else '')}".lower()
            if deal_search not in hay:
                continue
        fdeals.append(d)
    if _board_stage_changed:
        save_data(st.session_state.crm_store)
    if deal_sort_mode == "По дате создания":
        fdeals.sort(key=lambda d: str(d.get("created_at") or ""), reverse=True)
    elif deal_sort_mode == "По номеру сделки":
        fdeals.sort(key=lambda d: [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", str(d.get("deal_number") or d.get("title") or ""))], reverse=False)
    else:
        fdeals.sort(key=lambda d: str(d.get("last_modified") or d.get("created_at") or ""), reverse=True)
    new_deals = [d for d in fdeals if d.get("status", "Новый") == "Новый"]
    work_deals = [d for d in fdeals if d.get("status", "") == "В работе"]
    waiting_payment_deals = [d for d in fdeals if d.get("status", "") == "Ожидание оплаты"]
    paid_deals = [d for d in fdeals if d.get("status", "") == "Оплачено"]
    paused_deals = [d for d in fdeals if d.get("status", "") == "На паузе"]
    st.markdown("""<style>
    /* Визуальная система доски сделок повторяет доску задач. */
    .st-key-deals_col_new, .st-key-deals_col_work, .st-key-deals_col_waiting,
    .st-key-deals_col_paid, .st-key-deals_col_paused {
        background: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 0.7rem 0.65rem 0.8rem 0.65rem !important;
        min-height: 150px !important;
        box-shadow: 0 1px 2px rgba(30,45,65,0.025) !important;
    }
    .st-key-deals_col_new h3, .st-key-deals_col_work h3,
    .st-key-deals_col_waiting h3, .st-key-deals_col_paid h3,
    .st-key-deals_col_paused h3 {
        color: #344256 !important;
        font-size: 0.98rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.015em !important;
        line-height: 1.35 !important;
        padding-bottom: 0.55rem !important;
        margin-bottom: 0.6rem !important;
        border-bottom: 1px solid #E5EAF0 !important;
    }
    .st-key-deals_col_new [data-testid="stCaptionContainer"],
    .st-key-deals_col_work [data-testid="stCaptionContainer"],
    .st-key-deals_col_waiting [data-testid="stCaptionContainer"],
    .st-key-deals_col_paid [data-testid="stCaptionContainer"],
    .st-key-deals_col_paused [data-testid="stCaptionContainer"] {
        color: #8492A6 !important;
        font-size: 0.82rem !important;
    }
    </style>""", unsafe_allow_html=True)
    col_new, col_work, col_waiting, col_paid, col_paused = st.columns(5, gap="small")
    with col_new:
        with st.container(key="deals_col_new", border=True):
            st.subheader(f"Новые ({len(new_deals)})")
            if new_deals:
                for d in new_deals:
                    render_deal_standalone(d, cid_map.get(d.get("client_id")), cu)
            else:
                st.caption("Новых сделок нет.")
    with col_work:
        with st.container(key="deals_col_work", border=True):
            st.subheader(f"В работе ({len(work_deals)})")
            if work_deals:
                for d in work_deals:
                    render_deal_standalone(d, cid_map.get(d.get("client_id")), cu)
            else:
                st.caption("Сделок в работе нет.")
    with col_waiting:
        with st.container(key="deals_col_waiting", border=True):
            st.subheader(f"Ожидание оплаты ({len(waiting_payment_deals)})")
            if waiting_payment_deals:
                for d in waiting_payment_deals:
                    render_deal_standalone(d, cid_map.get(d.get("client_id")), cu)
            else:
                st.caption("Сделок в ожидании оплаты нет.")
    with col_paid:
        with st.container(key="deals_col_paid", border=True):
            st.subheader(f"Оплачено ({len(paid_deals)})")
            if paid_deals:
                for d in paid_deals:
                    render_deal_standalone(d, cid_map.get(d.get("client_id")), cu)
            else:
                st.caption("Оплаченных сделок нет.")
    with col_paused:
        with st.container(key="deals_col_paused", border=True):
            st.subheader(f"На паузе ({len(paused_deals)})")
            if paused_deals:
                for d in paused_deals:
                    render_deal_standalone(d, cid_map.get(d.get("client_id")), cu)
            else:
                st.caption("Сделок на паузе нет.")
    # Единая диспетчеризация окон сделок: сначала дочернее окно, затем карточка сделки.
    # Streamlit должен отрисовать только один @st.dialog за один проход.
    _dialog_deal_key = st.session_state.get("dialog_deal_key")
    _created_deal_id = st.session_state.get("_open_created_deal")
    _active_deal_dialog_id = _dialog_deal_key or _created_deal_id
    _deal_report_state = st.session_state.get("dialog_deal_report")
    _deal_task_dialog_id = st.session_state.get("dialog_create_deal_task_deal_id")
    _dialog_task_number = st.session_state.get("dialog_task_number")
    _dialog_task_client_id = st.session_state.get("dialog_task_client_id")
    _dialog_task_deal_id = st.session_state.get("dialog_task_deal_id")
    _dialog_task_key = st.session_state.get("dialog_task_key")

    _task_completion_state = st.session_state.get("dialog_task_completion")
    _pending_reminder = st.session_state.get("_pending_reminder_dialog")
    _req_view_state = st.session_state.get("dialog_client_requisites_view")
    _req_dialog_client_id = st.session_state.get("dialog_client_requisites_client_id")
    _invoice_dialog_state = st.session_state.get("dialog_invoice_request")
    _dialog_calculation_deal_id = st.session_state.get("dialog_calculation_deal_id")
    _dialog_calculation_calc_id = st.session_state.get("dialog_calculation_calc_id")
    # На вкладке «Сделки» дочерние окна должны иметь приоритет над карточкой сделки.
    # Иначе после нажатия «Сформировать счёт» старый dialog_deal_key открывает сделку.
    if _req_view_state:
        client_requisites_view_dialog(_req_view_state.get("client_id"), bool(_req_view_state.get("return_to_invoice")), _req_view_state.get("requisite_id"))
    elif _req_dialog_client_id:
        client_requisites_dialog(_req_dialog_client_id, bool(st.session_state.get("dialog_client_requisites_return_to_invoice", False)))
    elif _invoice_dialog_state:
        invoice_document_dialog(_invoice_dialog_state.get("deal_id"), _invoice_dialog_state.get("calc_id"))
    elif _dialog_calculation_deal_id and _dialog_calculation_calc_id:
        _tab_calc_deal = next((d for d in st.session_state.crm_store.get("deals", []) if str(d.get("id")) == str(_dialog_calculation_deal_id)), None)
        _tab_calc = next((c for c in (_tab_calc_deal or {}).get("calculations", []) if str(c.get("id")) == str(_dialog_calculation_calc_id) and not c.get("deleted")), None)
        if _tab_calc_deal and _tab_calc:
            # Consume this one-shot request; otherwise it is replayed on every rerun.
            st.session_state.pop("dialog_calculation_deal_id", None)
            st.session_state.pop("dialog_calculation_calc_id", None)
            deal_calculation_dialog(_dialog_calculation_deal_id, _dialog_calculation_calc_id)
        else:
            st.session_state.pop("dialog_calculation_deal_id", None)
            st.session_state.pop("dialog_calculation_calc_id", None)
            _active = st.session_state.get("_crm_active_dialog") or {}
            if _active.get("name") == "deal_calculation_dialog":
                st.session_state.pop("_crm_active_dialog", None)
    elif _pending_reminder:
        create_reminder_dialog(_pending_reminder["entity_type"], _pending_reminder["entity_id"], _pending_reminder["entity_label"])
    elif _task_completion_state:
        task_completion_report_dialog(_task_completion_state.get("client_id"), _task_completion_state.get("task_number"), _task_completion_state.get("key_prefix", "task"))
    elif _deal_report_state:
        deal_report_dialog(_deal_report_state.get("deal_id"), _deal_report_state.get("action", "close"))
    elif _deal_task_dialog_id:
        _task_client_id = st.session_state.get("dialog_create_deal_task_client_id")
        deal_create_task_dialog(_deal_task_dialog_id, _task_client_id)
    elif _dialog_task_key and _dialog_task_number and _dialog_task_client_id:
        _target_client = get_client_by_id(_dialog_task_client_id)
        _target_task = None
        _target_deal = None
        if _target_client:
            for _candidate_task in _target_client.get("tasks", []):
                if (str(_candidate_task.get("task_number", "")) == str(_dialog_task_number)
                        and str(_candidate_task.get("deal_id", "") or "") == str(_dialog_task_deal_id or "")):
                    _target_task = _candidate_task
                    break
        if _target_task:
            if _target_task.get("deal_id"):
                _target_deal = next((x for x in st.session_state.crm_store.get("deals", [])
                                     if str(x.get("id", "")) == str(_target_task.get("deal_id", ""))), None)
            task_detail_dialog(_target_task, _target_client, _target_deal, _dialog_task_key)
        else:
            st.session_state.pop("dialog_task_key", None)
            st.session_state.pop("dialog_task_number", None)
            st.session_state.pop("dialog_task_client_id", None)
            st.session_state.pop("dialog_task_deal_id", None)
            st.warning("Не удалось найти выбранную задачу. Обновите список и попробуйте ещё раз.")
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
    # Ensure older catalog rows expose the Characteristics column in the editor.
    for _product_row in _catalog:
        _product_row.setdefault("characteristics", "")
    if _is_catalog_admin:
        st.info("Изменяйте текущие цены, добавляйте новые товары и снимайте позиции с продажи через флажок «Активен». Удалять товар не нужно: архивные позиции остаются в истории сделок.")
        _edited_catalog = st.data_editor(
            _catalog,
            key="products_catalog_editor_v2",
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.TextColumn("ID", help="Служебный идентификатор; для новых товаров можно оставить пустым"),
                "sku": st.column_config.TextColumn("Артикул"),
                "name": st.column_config.TextColumn("Наименование", required=True),
                "characteristics": st.column_config.TextColumn("Характеристики"),
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
                _clean_rows.append({"id":_pid,"sku":_sku,"name":_name,"characteristics":str(_row.get("characteristics", "") or ""),"unit":str(_row.get("unit", "шт.") or "шт."),"price":_price,"note":str(_row.get("note", "") or ""),"active":bool(_row.get("active", True))})
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
    .tasks-page-heading { display:flex; align-items:center; justify-content:space-between; gap:16px; margin: 0; padding: 0; border:0; }
    .tasks-page-title-row, .tasks-page-title, .tasks-page-subtitle, .tasks-page-mark { display:none !important; }
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
        col_sq, col_sort, col_mf = st.columns([3.2, 2.4, 1.8], gap="small")
        with col_sq:
            _task_search_now = st.text_input("Поиск", key="task_search_input", placeholder="⌕  Поиск по задачам...", label_visibility="collapsed")
            task_search = (_task_search_now or "").strip().lower()
        with col_sort:
            task_sort_mode = st.selectbox(
                "Сортировка", ["По дате создания", "По дате изменения", "По номеру задачи"],
                index=1, key="task_tab_sort", label_visibility="collapsed"
            )
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
        # Сортировка по выбору пользователя применяется внутри каждой колонки;
        # дедлайн по-прежнему определяет колонку «На сегодня»/«Предстоящие».
        def _task_sort_key(entry):
            task = entry["task_obj"]
            if task_sort_mode == "По дате создания":
                return str(task.get("created_at") or "")
            if task_sort_mode == "По номеру задачи":
                return [(0, int(x)) if x.isdigit() else (1, x.lower()) for x in re.split(r"(\d+)", str(task.get("task_number") or ""))]
            return str(task.get("last_modified") or task.get("created_at") or "")
        _sort_reverse = task_sort_mode != "По номеру задачи"
        aat.sort(key=_task_sort_key, reverse=_sort_reverse)
        new_tasks.sort(key=_task_sort_key, reverse=_sort_reverse)
        review_tasks.sort(key=_task_sort_key, reverse=_sort_reverse)
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
                    # Перед открытием задачи передаём диспетчеру её однозначные
                    # идентификаторы. Одного dialog_task_key недостаточно:
                    # основной диспетчер ожидает также номер и ID клиента/сделки.
                    _push_dialog_return()
                    st.session_state["dialog_task_number"] = str(task.get("task_number", ""))
                    st.session_state["dialog_task_client_id"] = str(cl.get("id", t.get("client_id", "")))
                    st.session_state["dialog_task_deal_id"] = str(task.get("deal_id", "") or "")
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
        def _archived_task_sort_key(entry):
            task = entry["task_obj"]
            if task_sort_mode == "По дате создания":
                return str(task.get("created_at") or "")
            if task_sort_mode == "По номеру задачи":
                return [(0, int(x)) if x.isdigit() else (1, x.lower()) for x in re.split(r"(\d+)", str(task.get("task_number") or ""))]
            return str(task.get("last_modified") or task.get("created_at") or "")
        archived_tasks.sort(key=_archived_task_sort_key, reverse=(task_sort_mode != "По номеру задачи"))
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

# Восстанавливаем персональное рабочее пространство после входа/перезапуска.
_crm_workspace_init()

# Глобальная диспетчеризация legacy-маркеров: сохраняем совместимость с существующими
# действиями CRM, но каждое окно отображается вкладкой в рабочем пространстве.
if not st.session_state.get("_crm_dialog_requested_this_run", False) and not st.session_state.get("_crm_windows"):
    _global_req_view_state = st.session_state.get("dialog_client_requisites_view")
    _global_req_dialog_client_id = st.session_state.get("dialog_client_requisites_client_id")
    _global_invoice_dialog_state = st.session_state.get("dialog_invoice_request")
    _global_calc_deal_id = st.session_state.get("dialog_calculation_deal_id")
    _global_calc_id = st.session_state.get("dialog_calculation_calc_id")
    if _global_req_view_state:
        client_requisites_view_dialog(_global_req_view_state.get("client_id"), bool(_global_req_view_state.get("return_to_invoice")), _global_req_view_state.get("requisite_id"))
    elif _global_req_dialog_client_id:
        client_requisites_dialog(_global_req_dialog_client_id, bool(st.session_state.get("dialog_client_requisites_return_to_invoice", False)))
    elif _global_invoice_dialog_state:
        invoice_document_dialog(_global_invoice_dialog_state.get("deal_id"), _global_invoice_dialog_state.get("calc_id"))
    elif _global_calc_deal_id and _global_calc_id:
        _global_calc_deal = next((d for d in st.session_state.crm_store.get("deals", []) if str(d.get("id")) == str(_global_calc_deal_id)), None)
        _global_calc = next((c for c in (_global_calc_deal or {}).get("calculations", []) if str(c.get("id")) == str(_global_calc_id) and not c.get("deleted")), None)
        if _global_calc_deal and _global_calc:
            # Consume the legacy marker before dispatching the dialog.
            # Persistent markers were reopening the calculation on unrelated clicks.
            st.session_state.pop("dialog_calculation_deal_id", None)
            st.session_state.pop("dialog_calculation_calc_id", None)
            deal_calculation_dialog(_global_calc_deal_id, _global_calc_id)
        else:
            st.session_state.pop("dialog_calculation_deal_id", None)
            st.session_state.pop("dialog_calculation_calc_id", None)

# Рабочая панель: полноэкранное рабочее пространство с вкладками в стиле Chrome.
_crm_windows = st.session_state.get("_crm_windows", [])
_crm_active_window_id = st.session_state.get("_crm_active_window_id")
_crm_active_window = next((w for w in _crm_windows if w.get("id") == _crm_active_window_id), None)

_crm_windows = st.session_state.get("_crm_windows", [])
_crm_active_window_id = st.session_state.get("_crm_active_window_id")
_crm_active_window = next((w for w in _crm_windows if w.get("id") == _crm_active_window_id), None)
if _crm_active_window and not _crm_active_window.get("minimized"):
    st.markdown("""<style>
    .st-key-crm_workspace_window { position: fixed !important; z-index: 100000 !important; inset: 0 !important; width: 100vw !important; height: 100vh !important; max-width: none !important; max-height: none !important; transform: none !important; margin: 0 !important; overflow: auto !important; box-sizing: border-box !important; background: #f8f9fa !important; border: 0 !important; border-radius: 0 !important; box-shadow: none !important; padding: 0 16px 14px 16px !important; }
    .st-key-crm_workspace_backdrop { position: fixed !important; inset: 0 !important; z-index: 99990 !important; background: rgba(20,24,30,.22) !important; pointer-events: none !important; }
    /* Horizontal tabs with adjacent close controls; minimize stays at top right. */
    .st-key-crm_workspace_tabbar { position:relative !important; width:100% !important; padding:0 104px 0 0 !important; box-sizing:border-box !important; }
    .st-key-crm_workspace_tabbar [data-testid="stHorizontalBlock"] {
        display:flex !important; flex-direction:row !important; flex-wrap:nowrap !important;
        gap:0 !important; column-gap:0 !important; row-gap:0 !important;
        align-items:center !important; justify-content:flex-start !important;
        border-bottom:1px solid #E3E8EF !important; padding:0.15rem 0 0 !important;
        width:100% !important; overflow-x:auto !important;
    }
    /* Each tab container must occupy only its own content width, not share
       the available row width with neighboring tabs. */
    .st-key-crm_workspace_tabbar [data-testid="stHorizontalBlock"] > * {
        flex:0 0 auto !important; flex-grow:0 !important; flex-shrink:0 !important;
        width:max-content !important; min-width:max-content !important;
        max-width:none !important; margin:0 !important;
    }
    .st-key-crm_workspace_tabbar [data-testid="stHorizontalBlock"] > [data-testid="column"],
    .st-key-crm_workspace_tabbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex:0 0 auto !important; width:max-content !important;
        min-width:max-content !important; max-width:none !important;
    }
    .st-key-crm_workspace_tabbar .stButton { width:max-content !important; min-width:max-content !important; }
    .st-key-crm_workspace_tabbar .stButton,
    .st-key-crm_workspace_tabbar [data-testid="stButton"] {
        width:max-content !important; min-width:max-content !important;
        border:0 !important; outline:0 !important; box-shadow:none !important;
        background:transparent !important; padding:0 !important; margin:0 !important;
    }
    .st-key-crm_workspace_tabbar .stButton > button,
    .st-key-crm_workspace_tabbar [data-testid="stButton"] > button,
    .st-key-crm_workspace_tabbar button[data-testid^="stBaseButton-"] {
        box-sizing:border-box !important; display:inline-flex !important;
        width:max-content !important; min-width:max-content !important; max-width:none !important;
        min-height:38px !important; align-items:center !important; justify-content:center !important;
        border:0 !important; border-style:none !important; outline:0 !important;
        border-radius:0 !important; padding:0.5rem 0.55rem !important;
        color:#65758B !important; font-weight:500 !important;
        background:transparent !important; box-shadow:none !important;
        white-space:nowrap !important; writing-mode:horizontal-tb !important;
    }
    .st-key-crm_workspace_tabbar .stButton > button p,
    .st-key-crm_workspace_tabbar .stButton > button span { white-space:nowrap !important; }
    /* Each tab has exactly one frame: the keyed tab container. Its two
       Streamlit buttons are deliberately borderless and visually transparent. */
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_tab_item_"] {
        display:flex !important; flex:0 0 auto !important; flex-grow:0 !important;
        flex-direction:row !important; flex-wrap:nowrap !important;
        align-items:center !important; justify-content:flex-start !important;
        gap:0 !important; column-gap:0 !important; width:max-content !important;
        min-width:max-content !important; max-width:none !important;
        margin:0 !important; overflow:visible !important;
        border:1px solid #D9DEE7 !important; border-radius:7px !important;
        background:#F3F5F8 !important; padding:0 3px !important;
        box-shadow:none !important; outline:0 !important;
    }
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_tab_item_"] .stButton,
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_tab_item_"] [data-testid="stButton"] {
        border:0 !important; background:transparent !important;
        box-shadow:none !important; outline:0 !important;
    }
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_tab_item_"] button,
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_tab_item_"] button:hover,
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_tab_item_"] button:focus,
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_tab_item_"] button:active {
        border:0 !important; border-style:none !important; border-bottom:0 !important;
        border-radius:0 !important; outline:0 !important; box-shadow:none !important;
        background:transparent !important;
    }
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_tab_item_"] .stButton:first-child > button {
        padding:0.5rem 0.45rem 0.5rem 0.7rem !important;
    }
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_tab_item_"] .stButton:last-child > button {
        min-width:27px !important; width:27px !important; min-height:30px !important;
        height:30px !important; padding:0 !important; margin:0 !important;
        color:#8A94A3 !important; font-size:18px !important; line-height:1 !important;
    }
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_tab_item_"] .stButton:last-child > button:hover {
        color:#BC1661 !important;
    }
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_tab_item_"]:has([data-testid="stBaseButton-primary"]) {
        border-color:#BC1661 !important;
    }
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_tab_item_"]:has([data-testid="stBaseButton-primary"]) button {
        color:#BC1661 !important;
    }
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_minimize_wrap"] {
        position:absolute !important; top:0 !important; right:0 !important;
        width:96px !important; min-width:96px !important; z-index:10 !important;
    }
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_minimize_wrap"] .stButton,
    .st-key-crm_workspace_tabbar [class*="st-key-crm_workspace_minimize_wrap"] button {
        width:96px !important; min-width:96px !important; max-width:96px !important;
        white-space:nowrap !important;
    }
    .st-key-crm_workspace_window hr { display:none !important; }
    .st-key-crm_workspace_window hr { display:none !important; }
    .st-key-crm_workspace_content [class*="st-key-close_row_"] { display:none !important; }
    /* One center divider and a clear 16px gutter on each side. */
    .st-key-crm_workspace_content { position:relative !important; }
    .st-key-crm_workspace_content:before {
        content:"" !important; position:absolute !important; z-index:5 !important;
        pointer-events:none !important; top:0 !important; bottom:0 !important;
        left:50% !important; width:0 !important;
        border-left:1px solid #D5DCE5 !important;
    }
    .st-key-crm_workspace_content [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child,
    .st-key-crm_workspace_content [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
        padding-right:16px !important; box-sizing:border-box !important;
    }
    .st-key-crm_workspace_content [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child,
    .st-key-crm_workspace_content [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
        padding-left:16px !important; box-sizing:border-box !important;
    }
    </style>""", unsafe_allow_html=True)
    with st.container(key="crm_workspace_backdrop"):
        st.write("")
    with st.container(key="crm_workspace_window"):
        # Window switcher is placed at the top of the workspace, above its tabs.
        # The same panel is available on the Clients, Deals and Tasks main sections.
        _crm_workspace_render_bottom_panel(in_workspace=True)
        st.markdown(
            "<div class='crm-workspace-window-switcher-divider'></div>"
            "<style>.crm-workspace-window-switcher-divider { border-top:1px solid #D9DEE7; "
            "margin:2px 0 3px 0; padding:0; height:0; }</style>",
            unsafe_allow_html=True,
        )
        _tabs = _crm_active_window.get("tabs", [])
        _active_index = max(0, min(int(_crm_active_window.get("active_tab", 0) or 0), len(_tabs)-1)) if _tabs else -1
        _tab_count = len(_tabs)
        with st.container(key="crm_workspace_tabbar", horizontal=True, wrap=False, gap=None, horizontal_alignment="left"):
            for _i, _tab in enumerate(_tabs):
                _tab_title = _crm_workspace_tab_label(_tab).replace("###", "")[:32]
                with st.container(key=f"crm_workspace_tab_item_{_crm_active_window['id']}_{_i}", horizontal=True, wrap=False, gap=None, width="content", horizontal_alignment="left"):
                    if st.button(_tab_title, key=f"crm_workspace_tab_{_crm_active_window['id']}_{_i}", type="primary" if _i == _active_index else "secondary", help=_tab_title):
                        _crm_active_window["active_tab"] = _i
                        st.session_state["_crm_active_dialog"] = _tab
                        st.rerun()
                    # All workspace tabs, including the client card, can be closed.
                    if st.button("×", key=f"crm_workspace_tab_close_{_crm_active_window['id']}_{_i}", help="Закрыть вкладку"):
                        _tabs_now = _crm_active_window.get("tabs", [])
                        _closing_client_card = str(_tab.get("name", "")) == "client_detail_dialog"
                        if _closing_client_card:
                            # Closing the client card closes this entire workspace window,
                            # including every other tab that belongs to the same window.
                            _closed_window_id = _crm_active_window.get("id")
                            st.session_state["_crm_windows"] = [
                                w for w in st.session_state.get("_crm_windows", [])
                                if w.get("id") != _closed_window_id
                            ]
                            st.session_state["_crm_active_window_id"] = next(
                                (w.get("id") for w in st.session_state["_crm_windows"] if not w.get("minimized")),
                                None,
                            )
                            st.session_state.pop("_crm_active_dialog", None)
                        else:
                            if 0 <= _i < len(_tabs_now): _tabs_now.pop(_i)
                            if not _tabs_now:
                                st.session_state["_crm_windows"] = [w for w in st.session_state.get("_crm_windows", []) if w.get("id") != _crm_active_window.get("id")]
                                st.session_state["_crm_active_window_id"] = next((w.get("id") for w in st.session_state["_crm_windows"] if not w.get("minimized")), None)
                                st.session_state.pop("_crm_active_dialog", None)
                            else:
                                _new_active = _active_index - 1 if _i < _active_index else min(_i, len(_tabs_now)-1) if _i == _active_index else _active_index
                                _new_active = max(0, min(_new_active, len(_tabs_now)-1))
                                _crm_active_window["active_tab"] = _new_active
                                st.session_state["_crm_active_dialog"] = _tabs_now[_new_active]
                        _crm_workspace_clear_legacy_dialog_markers()
                        _crm_workspace_queue_save()
                        st.rerun()
            with st.container(key=f"crm_workspace_minimize_wrap_{_crm_active_window['id']}"):
                if st.button("Свернуть", key=f"crm_workspace_minimize_{_crm_active_window['id']}", help="Свернуть окно"):
                    _crm_active_window["minimized"] = True
                    st.session_state["_crm_active_window_id"] = None
                    _crm_workspace_queue_save()
                    st.rerun()

        with st.container(key="crm_workspace_content"):
            # Preserve original CRM button sizes, spacing and layout in window contents.
            _crm_dialog_columns = st.columns
            if _active_index >= 0:
                _active_entry = _tabs[_active_index]
                _active_spec = _CRM_DIALOG_REGISTRY.get(_active_entry.get("name"))
                if _active_spec:
                    st.session_state["_crm_active_dialog"] = _active_entry
                    st.session_state["_crm_inside_dialog_host"] = True
                    try:
                        _active_spec["func"](*_active_entry.get("args", ()), **_active_entry.get("kwargs", {}))
                    finally:
                        st.session_state["_crm_inside_dialog_host"] = False


# When no expanded workspace is open, the same panel is rendered under the main CRM navigation.

# Панель окон рендерится в нужном месте через _crm_workspace_render_bottom_panel().
