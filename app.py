import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
import time

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI: Auto-Retry", layout="wide")
st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #1a1c24; border-right: 1px solid #4ecca3; }
    .stChatMessage { border-radius: 10px; border: 1px solid rgba(78, 204, 163, 0.2); margin-bottom: 10px; }
    h1, h2, h3 { color: #4ecca3 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HAFIZA ---
if "all_sessions" not in st.session_state: st.session_state.all_sessions = {}
if "current_chat" not in st.session_state: st.session_state.current_chat = []

# --- 3. İNATÇI FONKSİYON (RETRY LOGIC) ---
def generate_with_retry(model, prompt, max_retries=3):
    """Hata alırsa bekleyip tekrar deneyen fonksiyon"""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                # Kota hatasıysa bekle ve tekrar dene
                wait_time = (attempt + 1) * 5 # 5sn, 10sn, 15sn bekle
                with st.spinner(f"🚦 Kota yoğunluğu. {attempt+1}. deneme yapılıyor ({wait_time} sn)..."):
                    time.sleep(wait_time)
                continue # Döngüye devam et
            else:
                # Başka hataysa direkt fırlat
                raise e
    return "Üzgünüm, Google şu an çok yoğun. Lütfen 1 dakika sonra deneyin."

# --- 4. YAN MENÜ ---
with st.sidebar:
    st.title("🧬 Onto-AI")
    
    # Google API Key
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Google Hattı Aktif")
    else:
        api_key = st.text_input("Google API Key:", type="password")

    st.divider()
    t_val = st.slider("Gelişim (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_val)
    st.metric("Ajans (w)", f"%{w_agency*100:.1f}")
    
    if st.button("🗑️ Temizle"):
        st.session_state.current_chat = []
        st.rerun()

# --- 5. ANA EKRAN ---
st.title("Onto-AI: İnatçı Mod")

for msg in st.session_state.current_chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("img"): st.image(msg["img"], use_container_width=True)

# --- 6. ÇALIŞMA ALANI ---
if prompt := st.chat_input("Mesaj yazın..."):
    st.session_state.current_chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    if not api_key:
        st.error("Google API Key eksik!")
    else:
        genai.configure(api_key=api_key)
        
        # En güvenli model
        model_name = "gemini-1.5-flash"
        
        # Termodinamik Sıcaklık
        temp = max(0.1, 1.6 * (1 - w_agency))
        
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={"temperature": temp},
            system_instruction=f"Sen Onto-AI'sin. Ajans (w) seviyen: {w_agency:.2f}. Buna göre konuş."
        )
        
        with st.chat_message("assistant"):
            try:
                # İnatçı fonksiyonu çağırıyoruz
                reply = generate_with_retry(model, prompt)
                st.markdown(reply)
                
                # Görsel
                img_url = None
                if any(x in prompt.lower() for x in ["çiz", "resim", "görsel"]):
                    safe_p = urllib.parse.quote(prompt[:50])
                    style = "scientific" if w_agency > 0.6 else "artistic"
                    img_url = f"https://pollinations.ai/p/{safe_p}_{style}?width=1024&height=1024&seed={np.random.randint(100)}"
                    st.image(img_url)
                
                st.session_state.current_chat.append({"role": "assistant", "content": reply, "img": img_url})
                
            except Exception as e:
                st.error(f"Hata: {e}")
