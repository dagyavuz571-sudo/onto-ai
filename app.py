import streamlit as st
import numpy as np
import os
from groq import Groq
import urllib.parse
from datetime import datetime
import time

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI: Llama 3", layout="wide")
st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #1a1c24; border-right: 1px solid #4ecca3; }
    .stChatMessage { border-radius: 10px; border: 1px solid rgba(78, 204, 163, 0.2); margin-bottom: 10px; }
    h1, h2, h3 { color: #4ecca3 !important; }
    .stImage { border: 1px solid #333; border-radius: 5px; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HAFIZA YÖNETİMİ ---
if "all_sessions" not in st.session_state: st.session_state.all_sessions = {}
if "messages" not in st.session_state: st.session_state.messages = []
if "gallery" not in st.session_state: st.session_state.gallery = []

# --- 3. YAN MENÜ ---
with st.sidebar:
    st.title("🦙 Onto-AI (Llama 3)")
    
    # API KEY GİRİŞİ (SECRETS VEYA ELLE)
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
        st.success("✅ Groq LPU Aktif")
    else:
        api_key = st.text_input("Groq API Key (gsk_...):", type="password")
        if not api_key:
            st.caption("[Anahtarı Buradan Alın](https://console.groq.com/keys)")

    st.divider()

    # Sohbet Arşivi
    st.subheader("🗂️ Sohbetler")
    if st.button("➕ Yeni Sohbet"):
        if st.session_state.messages:
            title = f"Kayıt {datetime.now().strftime('%H:%M')}"
            st.session_state.all_sessions[title] = list(st.session_state.messages)
        st.session_state.messages = []
        st.rerun()
    
    if st.session_state.all_sessions:
        selected_chat = st.selectbox("Geçmiş:", list(st.session_state.all_sessions.keys()))
        if st.button("Yükle"):
            st.session_state.messages = list(st.session_state.all_sessions[selected_chat])
            st.rerun()

    st.divider()
    
    # Galeri
    with st.expander("🎨 Galeri"):
        if st.session_state.gallery:
            for item in reversed(st.session_state.gallery):
                st.image(item["url"], caption=item["prompt"], use_container_width=True)
        else:
            st.caption("Boş")

    st.divider()
    t_val = st.slider("Gelişim (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_val)
    st.metric("Ajans (w)", f"%{w_agency*100:.1f}")

# --- 4. ANA EKRAN ---
st.title("Onto-AI")
st.caption("Powered by Meta Llama 3 & Groq LPU")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("img"): st.image(msg["img"], use_container_width=True)

# --- 5. LLAMA 3 MOTORU ---
if prompt := st.chat_input("Yazın veya 'çiz' deyin..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    if not api_key:
        st.error("Lütfen Groq API Key girin!")
    else:
        # Groq İstemcisi
        client = Groq(api_key=api_key)
        
        with st.chat_message("assistant"):
            try:
                # Termodinamik Sıcaklık (Llama buna çok iyi tepki verir)
                temp = max(0.01, 1.8 * (1 - w_agency))
                
                # Sistem Mesajı (Persona)
                sys_msg = (
                    f"Sen Onto-AI'sin. Termodinamik Ajans (w) seviyen: {w_agency:.2f}. "
                    f"Eğer w 1'e yakınsa: Çok kısa, analitik, duygusuz ve makine gibi konuş. "
                    f"Eğer w 0'a yakınsa: Çok yaratıcı, felsefi, karmaşık ve duygusal konuş. "
                    f"GÖRSEL TALİMATI: Eğer kullanıcı 'çiz' veya 'resim' derse, resmi kendin çizemeyeceğini söyleme. "
                    f"'Görseli w={w_agency:.2f} parametresine göre oluşturuyorum' diyerek betimleme yap. "
                    f"Sistem görseli otomatik ekleyecek."
                )

                # Llama 3.3 70B (Şu an en iyisi)
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama-3.3-70b-versatile", 
                    temperature=temp,
                    max_tokens=1024,
                )
                
                reply = chat_completion.choices[0].message.content
                st.markdown(reply)
                
                # Görsel Üretme (Pollinations - Llama çizemez ama biz çizeriz)
                img_url = None
                if any(x in prompt.lower() for x in ["çiz", "resim", "görsel", "draw"]):
                    with st.spinner("🎨 Görsel işleniyor..."):
                        try:
                            # Promptu Llama'dan değil direkt kullanıcıdan alıyoruz
                            safe_p = urllib.parse.quote(prompt[:100])
                            style = "scientific, macro photography" if w_agency > 0.6 else "abstract, surrealism, dali style"
                            seed = int(time.time())
                            img_url = f"https://pollinations.ai/p/{safe_p}_{style}?width=1024&height=1024&seed={seed}"
                            
                            st.image(img_url, caption=f"w={w_agency:.2f}")
                            st.session_state.gallery.append({"url": img_url, "prompt": prompt})
                        except:
                            st.warning("Görsel sunucusuna bağlanılamadı.")

                # Kayıt
                st.session_state.messages.append({"role": "assistant", "content": reply, "img": img_url})
                
            except Exception as e:
                st.error(f"Hata: {e}")
