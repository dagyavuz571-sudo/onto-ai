import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
from datetime import datetime

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI: Auto-Detect", layout="wide")
st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #1a1c24; border-right: 1px solid #4ecca3; }
    .stChatMessage { border-radius: 10px; border: 1px solid rgba(78, 204, 163, 0.2); margin-bottom: 10px; }
    h1, h2, h3 { color: #4ecca3 !important; }
    .stSuccess { background-color: rgba(40, 167, 69, 0.1); color: #28a745; }
    </style>
""", unsafe_allow_html=True)

# --- 2. MODEL TARAYICI FONKSİYON (KRİTİK KISIM) ---
def get_live_model_name(api_key):
    """Google sunucusundan o an çalışan modelleri çeker."""
    genai.configure(api_key=api_key)
    try:
        all_models = genai.list_models()
        # Sadece metin üretebilenleri (generateContent) al
        valid_models = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
        
        if not valid_models:
            return None, ["Hiçbir model bulunamadı."]
            
        # Tercih Sıralaması: Önce isminde 'flash' geçenler (Hızlıdır), sonra 'pro'
        best_model = valid_models[0]
        for m in valid_models:
            if "flash" in m.lower() and "exp" not in m.lower(): # Experimental olmayan Flash'ı bulmaya çalış
                best_model = m
                break
        
        return best_model, valid_models
    except Exception as e:
        return None, [str(e)]

# --- 3. YAN MENÜ ---
with st.sidebar:
    st.title("🧬 Onto-AI")
    
    # API Key
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Google API Key:", type="password")

    st.divider()
    
    # --- MODEL DURUMU ---
    active_model_name = None
    if api_key:
        with st.spinner("Sunucu taranıyor..."):
            best_model, all_list = get_live_model_name(api_key)
            if best_model:
                st.success(f"✅ Aktif: {best_model.replace('models/', '')}")
                active_model_name = best_model
                
                with st.expander("Tüm Liste (Debug)"):
                    for m in all_list:
                        st.write(f"- {m}")
            else:
                st.error("Model bulunamadı!")
                st.write(all_list)
    else:
        st.warning("Önce Anahtar Girin.")

    st.divider()
    t_val = st.slider("Gelişim (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_val)
    st.metric("Ajans (w)", f"%{w_agency*100:.1f}")
    
    # Temizle Butonu
    if st.button("🗑️ Temizle"):
        st.session_state.messages = []
        st.rerun()

# --- 4. SOHBET HAFIZASI ---
if "messages" not in st.session_state: st.session_state.messages = []

st.title("Onto-AI")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("img"): st.image(msg["img"], use_container_width=True)

# --- 5. ÇALIŞTIRMA ---
if prompt := st.chat_input("Mesaj..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    if not active_model_name:
        st.error("Çalışan bir model bulunamadı. Lütfen sol menüdeki listeyi kontrol edin.")
    else:
        with st.chat_message("assistant"):
            status = st.empty()
            status.info(f"Using: {active_model_name}")
            
            try:
                # Termodinamik Sıcaklık
                temp = max(0.1, 1.6 * (1 - w_agency))
                
                model = genai.GenerativeModel(
                    model_name=active_model_name,
                    generation_config={"temperature": temp}
                )
                
                # Persona
                sys_msg = f"Sen Onto-AI'sin. Ajans (w) seviyen: {w_agency:.2f}. Buna göre davran."
                
                response = model.generate_content(f"{sys_msg}\nSoru: {prompt}")
                reply = response.text
                status.markdown(reply)
                
                # Görsel
                img_url = None
                if any(x in prompt.lower() for x in ["çiz", "resim", "görsel"]):
                    safe_p = urllib.parse.quote(prompt[:50])
                    style = "scientific" if w_agency > 0.6 else "artistic"
                    img_url = f"https://pollinations.ai/p/{safe_p}_{style}?width=1024&height=1024&seed={np.random.randint(100)}"
                    st.image(img_url)
                
                st.session_state.messages.append({"role": "assistant", "content": reply, "img": img_url})
                
            except Exception as e:
                err = str(e)
                if "429" in err:
                    status.error("🚦 Kota Doldu! (Google Free Tier sınırındasınız)")
                else:
                    status.error(f"Hata: {err}")
