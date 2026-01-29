import streamlit as st
import numpy as np
from openai import OpenAI
import urllib.parse
from datetime import datetime

# --- 1. TASARIM ---
st.set_page_config(page_title="Onto-AI: DeepSeek", layout="wide")
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

# --- 3. YAN MENÜ ---
with st.sidebar:
    st.title("🧬 Onto-AI (DeepSeek)")
    
    # DeepSeek API Key Girişi
    if "DEEPSEEK_API_KEY" in st.secrets:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
        st.success("✅ DeepSeek Hattı Aktif")
    else:
        api_key = st.text_input("DeepSeek API Key:", type="password")
        st.caption("Key'i 'platform.deepseek.com' adresinden alabilirsiniz.")

    st.divider()
    
    # Termodinamik Ayar
    t_val = st.slider("Gelişim (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_val)
    st.metric("Ajans (w)", f"%{w_agency*100:.1f}")
    
    # Sıcaklık Hesabı (DeepSeek buna bayılır)
    # w=1 (Düzen) -> Temp=0.0 | w=0 (Kaos) -> Temp=1.3
    dynamic_temp = max(0.0, 1.5 * (1 - w_agency))
    
    if st.button("🗑️ Temizle"):
        st.session_state.current_chat = []
        st.rerun()

# --- 4. ANA EKRAN ---
st.title("Onto-AI")

for msg in st.session_state.current_chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("img"): st.image(msg["img"], use_container_width=True)

# --- 5. DEEPSEEK MOTORU ---
if prompt := st.chat_input("Mesaj yazın..."):
    st.session_state.current_chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    if not api_key:
        st.error("DeepSeek API Key eksik!")
    else:
        # DeepSeek Bağlantısı
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        with st.chat_message("assistant"):
            status = st.empty()
            status.info("🧠 DeepSeek V3 Düşünüyor...")
            
            try:
                # Sistem Mesajı (Persona)
                system_msg = f"Sen Onto-AI'sin. Termodinamik Ajans (w) seviyen: {w_agency:.2f}. Bu değer 1'e yakınsa çok kısa, net ve robotik konuş. 0'a yakınsa şairane, karmaşık ve uzun konuş."
                
                response = client.chat.completions.create(
                    model="deepseek-chat", # Veya "deepseek-reasoner"
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=dynamic_temp, # Termodinamik müdahale burada
                    stream=False
                )
                
                reply = response.choices[0].message.content
                status.markdown(reply)
                
                # Görsel (Pollinations devam eder)
                img_url = None
                if any(x in prompt.lower() for x in ["çiz", "resim", "görsel"]):
                    safe_p = urllib.parse.quote(prompt[:50])
                    style = "scientific" if w_agency > 0.6 else "dreamlike"
                    img_url = f"https://pollinations.ai/p/{safe_p}_{style}?width=1024&height=1024&seed={np.random.randint(100)}"
                    st.image(img_url)
                
                st.session_state.current_chat.append({"role": "assistant", "content": reply, "img": img_url})
                
            except Exception as e:
                st.error(f"Hata: {e}")
