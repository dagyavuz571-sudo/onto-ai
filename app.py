import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
from datetime import datetime

# --- 1. ESTETİK TASARIM ---
st.set_page_config(page_title="Onto-AI: Zırhlı Mod", layout="wide")
st.markdown("<style>.stApp { background: #0e1117; color: #ffffff; } [data-testid='stSidebar'] { background-color: #1a1c24; border-right: 1px solid #4ecca3; } h1, h2, h3 { color: #4ecca3 !important; }</style>", unsafe_allow_html=True)

# --- 2. HAFIZA YÖNETİMİ ---
if "all_sessions" not in st.session_state: st.session_state.all_sessions = {}
if "current_chat" not in st.session_state: st.session_state.current_chat = []

# --- 3. AKILLI MODEL SEÇİCİ (KOTA ODAKLI) ---
def get_quota_friendly_model(key):
    genai.configure(api_key=key)
    try:
        raw_models = genai.list_models()
        available = [m.name for m in raw_models if 'generateContent' in m.supported_generation_methods]
        
        # ÖNCELİK LİSTESİ: Flash modelleri her zaman en yüksek kotaya sahiptir.
        # Pro modellerini en sona attık ki kota bitmesin.
        priority = ['gemini-3-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-3-pro', 'gemini-pro']
        
        for target in priority:
            for m in available:
                if target in m:
                    return genai.GenerativeModel(m), m
        return genai.GenerativeModel(available[0]), available[0]
    except:
        return None, "Bağlantı Hatası"

# --- 4. YAN MENÜ ---
with st.sidebar:
    st.title("🧬 Onto-Arşiv")
    if st.button("➕ Yeni Sohbet"):
        if st.session_state.current_chat:
            title = f"Sohbet {datetime.now().strftime('%H:%M:%S')}"
            st.session_state.all_sessions[title] = list(st.session_state.current_chat)
        st.session_state.current_chat = []
        st.rerun()
    
    st.divider()
    for title in list(st.session_state.all_sessions.keys()):
        if st.button(f"📄 {title}"):
            st.session_state.current_chat = list(st.session_state.all_sessions[title])
            st.rerun()
            
    st.divider()
    api_key = st.secrets["GOOGLE_API_KEY"] if "GOOGLE_API_KEY" in st.secrets else st.text_input("API Key:", type="password")
    t_value = st.slider("Gelişim (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik (w)", f"%{w_agency*100:.1f}")

# --- 5. ANA EKRAN ---
st.title("Onto-AI")
for msg in st.session_state.current_chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("img"): st.image(msg["img"], use_container_width=True)

# --- 6. CEVAP ÜRETME ---
if prompt := st.chat_input("Düşünceni buraya bırak..."):
    st.session_state.current_chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    if not api_key:
        st.error("API Key eksik.")
    else:
        model, m_name = get_quota_friendly_model(api_key)
        if model:
            with st.chat_message("assistant"):
                try:
                    sys_inst = f"Sen Onto-AI'sin. w: {w_agency}. Soru: {prompt}"
                    response = model.generate_content(sys_inst)
                    reply = response.text
                    st.markdown(reply)
                    st.caption(f"🧠 Aktif Model: {m_name}")
                    
                    # Görsel üretme koruması
                    img_url = None
                    if any(x in prompt.lower() for x in ["çiz", "resim", "görsel"]):
                        style = "scientific" if w_agency > 0.7 else "surreal"
                        img_url = f"https://pollinations.ai/p/{urllib.parse.quote(prompt + ',' + style)}?width=1024&height=1024&seed={np.random.randint(1000)}"
                        st.image(img_url)
                    
                    st.session_state.current_chat.append({"role": "assistant", "content": reply, "img": img_url})
                except Exception as e:
                    if "429" in str(e):
                        st.error("🚦 **KOTA DOLDU!** Google bu model için sınırı aştığınızı söylüyor. Lütfen 30 saniye bekleyin veya sistemin başka bir modele geçmesini bekleyin.")
                    else:
                        st.error(f"Hata: {e}")
