import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
from datetime import datetime

# --- 1. TASARIM ---
st.set_page_config(page_title="Onto-AI", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #1a1c24; border-right: 1px solid #4ecca3; }
    .stChatMessage { border-radius: 10px; border: 1px solid rgba(78, 204, 163, 0.2); margin-bottom: 5px; }
    h1, h2, h3 { color: #4ecca3 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HAFIZA YÖNETİMİ ---
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = []

# --- 3. YAN MENÜ ---
with st.sidebar:
    st.title("🧬 Onto-Arşiv")
    
    if st.button("➕ Yeni Sohbet"):
        if st.session_state.current_chat:
            title = f"Sohbet {datetime.now().strftime('%H:%M:%S')}"
            st.session_state.all_sessions[title] = list(st.session_state.current_chat)
        st.session_state.current_chat = []
        st.rerun()
    
    st.divider()
    st.subheader("📂 Geçmiş")
    for title in list(st.session_state.all_sessions.keys()):
        if st.button(f"📄 {title}"):
            st.session_state.current_chat = list(st.session_state.all_sessions[title])
            st.rerun()
            
    st.divider()
    api_key = st.secrets["GOOGLE_API_KEY"] if "GOOGLE_API_KEY" in st.secrets else st.text_input("API Key:", type="password")
    t_value = st.slider("Gelişim (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik (w)", f"%{w_agency*100:.1f}")

# --- 4. ANA EKRAN ---
st.title("Onto-AI")

# --- HATA ALAN KISIM BURASIYDI: GÜVENLİ HALE GETİRİLDİ ---
for msg in st.session_state.current_chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # msg["img"] varsa VE içi boş değilse resmi bas
        if msg.get("img") is not None and str(msg["img"]).startswith("http"):
            try:
                st.image(msg["img"], use_container_width=True)
            except:
                st.caption("⚠️ Görsel yüklenemedi.")

# --- 5. CEVAP MOTORU ---
if prompt := st.chat_input("Buraya yazın..."):
    st.session_state.current_chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    if not api_key:
        st.error("API Key eksik.")
    else:
        try:
            genai.configure(api_key=api_key)
            # En yeni Gemini 3 modellerini deneyelim, yoksa geri düşelim
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = "models/gemini-1.5-flash" # Varsayılan
            for m in models:
                if "gemini-3" in m: target_model = m; break
            
            model = genai.GenerativeModel(target_model)
            
            with st.chat_message("assistant"):
                sys_inst = f"Sen Onto-AI'sin. w seviyesi: {w_agency}. Bu değere göre davran. Soru: {prompt}"
                response = model.generate_content(sys_inst)
                reply = response.text
                st.markdown(reply)
                
                # Görsel üretme (w değerine göre stil ekleyelim)
                is_draw = any(x in prompt.lower() for x in ["çiz", "resim", "görsel", "draw"])
                img_url = None
                if is_draw:
                    style = "hyper-realistic, scientific" if w_agency > 0.7 else "surreal, abstract"
                    # URL'yi oluştururken boşlukları temizleyelim
                    encoded_prompt = urllib.parse.quote(f"{prompt}, {style}")
                    img_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={np.random.randint(1000)}"
                    try:
                        st.image(img_url)
                    except:
                        img_url = None # Hata alırsan hafızaya boş veri yazma
                
                st.session_state.current_chat.append({"role": "assistant", "content": reply, "img": img_url})
        except Exception as e:
            st.error(f"Hata: {e}")
