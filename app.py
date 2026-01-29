import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
from datetime import datetime

# --- 1. ESTETİK VE TASARIM (CSS) ---
st.set_page_config(page_title="Onto-AI", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Ana Arka Plan */
    .stApp {
        background: radial-gradient(circle at top right, #1a1a2e, #16213e, #0f3460);
        color: #e94560;
    }
    
    /* Yan Menü (Sidebar) Estetiği */
    [data-testid="stSidebar"] {
        background-color: rgba(22, 33, 62, 0.8);
        border-right: 1px solid #4ecca3;
    }
    
    /* Mesaj Balonları */
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
        border: 1px solid rgba(78, 204, 163, 0.2);
    }
    
    /* Başlık ve Metrik Estetiği */
    h1, h2, h3 { color: #4ecca3 !important; font-family: 'Courier New', Courier, monospace; }
    .stMetric { background: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 10px; }
    
    /* Sohbet Geçmişi Butonları */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        background-color: transparent;
        border: 1px solid #4ecca3;
        color: #4ecca3;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #4ecca3;
        color: #1a1a2e;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. SİSTEM VE HAFIZA YÖNETİMİ ---
# Tüm sohbetlerin tutulduğu ana depo
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {} # { "Başlık": [mesajlar] }

# Mevcut aktif sohbet
if "current_chat" not in st.session_state:
    st.session_state.current_chat = []

# --- 3. YAN MENÜ (ARŞİV VE AYARLAR) ---
with st.sidebar:
    st.title("🧬 Onto-Arşiv")
    
    # Yeni Sohbet Başlat
    if st.button("➕ Yeni Sohbet Başlat"):
        if st.session_state.current_chat:
            # Mevcut sohbeti kaydet
            title = f"Sohbet {datetime.now().strftime('%H:%M:%S')}"
            st.session_state.all_sessions[title] = st.session_state.current_chat
        st.session_state.current_chat = []
        st.rerun()
    
    st.divider()
    
    # Eski Sohbetleri Listele
    st.subheader("📂 Geçmiş Kayıtlar")
    for title in list(st.session_state.all_sessions.keys()):
        if st.button(f"📄 {title}"):
            st.session_state.current_chat = st.session_state.all_sessions[title]
            st.rerun()
            
    st.divider()
    
    # Model ve Ajans Ayarları
    st.subheader("⚙️ Parametreler")
    api_key = st.secrets["GOOGLE_API_KEY"] if "GOOGLE_API_KEY" in st.secrets else st.text_input("API Key:", type="password")
    
    t_value = st.slider("Gelişim (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik (w)", f"%{w_agency*100:.1f}")

# --- 4. ANA EKRAN (SOHBET ALANI) ---
st.title("Onto-AI")
st.caption("Termodinamik Doğruluk Motoru v2026")

# Mesajları Görüntüle
for msg in st.session_state.current_chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "img" in msg: st.image(msg["img"])

# --- 5. CEVAP MOTORU ---
if prompt := st.chat_input("Düşünceni buraya bırak..."):
    # Kullanıcı mesajını ekle
    st.session_state.current_chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    if not api_key:
        st.error("API Anahtarı bulunamadı.")
    else:
        try:
            genai.configure(api_key=api_key)
            # Model dedektörü (çalışan ilk modeli bulur)
            raw_models = genai.list_models()
            model_list = [m.name for m in raw_models if 'generateContent' in m.supported_generation_methods]
            model = genai.GenerativeModel(model_list[0]) # En üstteki aktif modeli al
            
            with st.chat_message("assistant"):
                with st.spinner("Analiz ediliyor..."):
                    sys_inst = f"Sen Onto-AI'sin. w: {w_agency}. Soru: {prompt}"
                    response = model.generate_content(sys_inst)
                    reply = response.text
                    st.markdown(reply)
                    
                    # Görsel üretme (Opsiyonel)
                    is_draw = any(x in prompt.lower() for x in ["çiz", "resim", "görsel", "draw"])
                    img_url = None
                    if is_draw:
                        img_url = f"https://pollinations.ai/p/{urllib.parse.quote(prompt)}?width=1024&height=1024&seed={np.random.randint(1000)}"
                        st.image(img_url)
                    
                    # Hafızaya kaydet
                    st.session_state.current_chat.append({
                        "role": "assistant", 
                        "content": reply, 
                        "img": img_url if img_url else None
                    })
        except Exception as e:
            st.error(f"Sistem Hatası: {e}")
