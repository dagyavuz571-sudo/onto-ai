import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
from datetime import datetime

# --- 1. AYARLAR VE TASARIM ---
st.set_page_config(page_title="Onto-AI: Stabil", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #1a1c24; border-right: 1px solid #4ecca3; }
    .stChatMessage { border-radius: 10px; border: 1px solid rgba(78, 204, 163, 0.2); margin-bottom: 10px; }
    h1, h2, h3 { color: #4ecca3 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HAFIZA YÖNETİMİ ---
if "all_sessions" not in st.session_state: st.session_state.all_sessions = {}
if "current_chat" not in st.session_state: st.session_state.current_chat = []

# --- 3. SAĞLAM MODEL BULUCU (Macera Yok) ---
def get_stable_model(key, w_val):
    genai.configure(api_key=key)
    try:
        # Sunucudaki modelleri listele
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Öncelik: Her zaman "Flash" modelleri (Çünkü kotası yüksektir)
        # Gemini 3 Pro vs. macerasına girmiyoruz.
        target_model = models[0]
        for m in models:
            if "flash" in m.lower():
                target_model = m
                break
        
        # Termodinamik Sıcaklık Ayarı
        # w yüksekse (düzen) -> Sıcaklık düşük (0.1)
        # w düşükse (kaos) -> Sıcaklık yüksek (1.5)
        temp = max(0.1, 1.5 * (1 - w_val))
        
        config = {
            "temperature": temp,
            "top_p": 0.95,
            "max_output_tokens": 2048,
        }
        
        return genai.GenerativeModel(model_name=target_model, generation_config=config), target_model
    except Exception as e:
        return None, str(e)

# --- 4. YAN MENÜ ---
with st.sidebar:
    st.title("🧬 Onto-Arşiv")
    
    if st.button("➕ Yeni Sohbet"):
        if st.session_state.current_chat:
            title = f"Kayıt {datetime.now().strftime('%H:%M:%S')}"
            st.session_state.all_sessions[title] = list(st.session_state.current_chat)
        st.session_state.current_chat = []
        st.rerun()
    
    st.divider()
    st.caption("Geçmiş:")
    for title in list(st.session_state.all_sessions.keys()):
        if st.button(f"📄 {title}", use_container_width=True):
            st.session_state.current_chat = list(st.session_state.all_sessions[title])
            st.rerun()
            
    st.divider()
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("API Key:", type="password")
        
    t_val = st.slider("Gelişim (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_val)
    st.metric("Ajans (w)", f"%{w_agency*100:.1f}")

# --- 5. ANA EKRAN ---
st.title("Onto-AI")

# Mesajları Göster (Hata Korumalı)
for msg in st.session_state.current_chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("img") and str(msg["img"]).startswith("http"):
            try:
                st.image(msg["img"], use_container_width=True)
            except:
                pass

# --- 6. ÇALIŞAN MOTOR ---
if prompt := st.chat_input("Mesaj yazın..."):
    st.session_state.current_chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    if not api_key:
        st.error("API Key girilmedi.")
    else:
        model, m_name = get_stable_model(api_key, w_agency)
        
        if not model:
            st.error(f"Bağlantı Hatası: {m_name}")
        else:
            with st.chat_message("assistant"):
                status = st.empty()
                status.info("İşleniyor...")
                
                try:
                    # Sistem Talimatı (Persona)
                    sys_prompt = f"Sen Onto-AI'sin. Ajans seviyen: {w_agency}. Buna göre davran."
                    
                    full_response = model.generate_content(f"{sys_prompt}\nSoru: {prompt}")
                    reply = full_response.text
                    status.markdown(reply)
                    
                    # Görsel (Pollinations - En Stabil URL yapısı)
                    img_url = None
                    if any(x in prompt.lower() for x in ["çiz", "resim", "görsel"]):
                        safe_prompt = urllib.parse.quote(prompt[:100]) # Çok uzun promptları kırp
                        style = "scientific" if w_agency > 0.6 else "surreal"
                        img_url = f"https://pollinations.ai/p/{safe_prompt}_{style}?width=1024&height=1024&seed={np.random.randint(100)}"
                        st.image(img_url)
                    
                    st.session_state.current_chat.append({"role": "assistant", "content": reply, "img": img_url})
                    
                except Exception as e:
                    if "429" in str(e):
                        status.error("🚦 Kota Doldu. Lütfen 30 saniye bekleyin. (Google Free Tier sınırındasınız)")
                    else:
                        status.error(f"Hata: {e}")
