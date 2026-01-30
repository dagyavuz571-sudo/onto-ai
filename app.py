import streamlit as st
import numpy as np
from groq import Groq
import urllib.parse
from datetime import datetime
import time
import json
import os

# --- 1. MİNİMALİST AYARLAR (SİYAH/BEYAZ) ---
st.set_page_config(page_title="Onto-AI", layout="wide", initial_sidebar_state="collapsed")

# CSS: Sadece Siyah, Beyaz, Gri ve Font Düzenlemeleri
st.markdown("""
    <style>
    /* Genel Arka Plan */
    .stApp { background-color: #000000; color: #e0e0e0; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Yan Menü */
    [data-testid="stSidebar"] { background-color: #111111; border-right: 1px solid #333; }
    
    /* Input Alanı */
    .stTextInput input { background-color: #111111; color: white; border: 1px solid #333; }
    
    /* Mesaj Kutuları (Sınırları Kaldır, Saf Metin) */
    .stChatMessage { background-color: transparent; border: none; border-bottom: 1px solid #222; }
    
    /* Butonlar (Minimalist Gri) */
    .stButton button {
        background-color: #111111; color: #cccccc; border: 1px solid #333; border-radius: 4px;
        font-size: 12px; transition: all 0.2s;
    }
    .stButton button:hover { border-color: #fff; color: #fff; }
    
    /* Başlıklar */
    h1, h2, h3 { color: #ffffff !important; font-weight: 300; letter-spacing: 2px; }
    
    /* İlerleme Çubuğu (Gri) */
    .stProgress > div > div > div > div { background-color: #888888; }
    
    /* Emoji Temizliği */
    .stAlert { background-color: #111; color: #ccc; border: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

# --- 2. KALICI HAFIZA SİSTEMİ (JSON) ---
DB_FILE = "chat_history.json"

def load_history():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(messages):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)

if "messages" not in st.session_state:
    st.session_state.messages = load_history()

# --- 3. YAN MENÜ (AYARLAR) ---
with st.sidebar:
    st.markdown("### ONTO-AI / KONTROL")
    
    # API KEY
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
    else:
        api_key = st.text_input("API Key", type="password")

    st.markdown("---")
    
    # ONTOGENETİK AYAR (Sadece Gri Bar)
    t_val = st.slider("Gelişim (w)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_val)
    st.markdown(f"<div style='text-align:center; color:#888;'>w: {w_agency:.2f}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("SOHBETİ SIFIRLA"):
        st.session_state.messages = []
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

# --- 4. ANA EKRAN ---
st.title("ONTO-AI")

# Mesajları Göster
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # Kopyalama için "code block" hilesi (Sağ üstte copy butonu çıkar)
        if msg["role"] == "assistant":
            st.code(msg["content"], language="markdown")
        else:
            st.markdown(msg["content"])
            
        if msg.get("img"):
            st.image(msg["img"], use_container_width=True)

# --- 5. GİRİŞ VE MOTOR ---
# Resim ve Gönder Butonlarını Yan Yana Koymak İçin Form
with st.container():
    col1, col2 = st.columns([5, 1])
    
    with col1:
        prompt = st.chat_input("Girdi...")
        
    with col2:
        # Resim Butonu (Yazı barının yanında)
        if st.button("ÇİZ", help="Son yazılanı veya rastgele bir şeyi çizer"):
            prompt = "GÖRSEL_MOD: Rastgele soyut bir kavram çiz." # Tetikleyici

if prompt:
    # 1. Kullanıcı Mesajı
    user_msg = prompt
    if prompt == "GÖRSEL_MOD: Rastgele soyut bir kavram çiz.":
        user_msg = "[Görsel Oluşturma İsteği]"
    
    st.session_state.messages.append({"role": "user", "content": user_msg})
    with st.chat_message("user"): st.markdown(user_msg)

    if not api_key:
        st.warning("API Key Eksik.")
    else:
        client = Groq(api_key=api_key)
        
        with st.chat_message("assistant"):
            # Minimalist Yükleniyor...
            with st.spinner("..."):
                try:
                    # --- SİSTEM TALİMATI (TÜRKÇE ZORLAMASI) ---
                    # w değerine göre karakter değişimi
                    if w_agency < 0.3:
                        mod = "PASİF MOD. Sadece onaylayıcı ol. Kısa cevap ver. Ansiklopedik bilgi ver."
                    elif w_agency > 0.7:
                        mod = "AKTİF MOD. Eleştirel ol. Felsefi derinlik kat. Kendi fikrini savun."
                    else:
                        mod = "DENGE MODU. Yardımcı ol."

                    sys_msg = (
                        f"Sen Onto-AI sistemisin. w={w_agency:.2f}. {mod} "
                        f"KESİN KURALLAR:"
                        f"1. Sadece ve sadece TÜRKÇE konuş. Yabancı terim kullanma (örneğin 'feedback' deme, 'geri bildirim' de)."
                        f"2. Cevapların minimalist ve net olsun."
                        f"3. Emojileri ASLA kullanma."
                        f"4. Eğer kullanıcı 'çiz' derse veya görsel isterse reddetme, betimle."
                    )
                    
                    # Görsel İstemi mi?
                    is_image_request = any(x in prompt.lower() for x in ["çiz", "resim", "görsel", "görsel_mod"])
                    
                    if is_image_request:
                        # Görsel Modu
                        safe_p = urllib.parse.quote(prompt[:100])
                        seed = int(time.time())
                        style = "black and white, minimalist, sketch" # Stil de minimalist
                        img_url = f"https://pollinations.ai/p/{safe_p}_{style}?width=1024&height=1024&seed={seed}&nologo=true"
                        
                        reply = f"Görsel oluşturuldu (w={w_agency:.2f})."
                        st.code(reply, language="markdown")
                        st.image(img_url, caption="Onto-AI Görsel Çıktısı")
                        
                        st.session_state.messages.append({"role": "assistant", "content": reply, "img": img_url})
                    
                    else:
                        # Metin Modu
                        resp = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": sys_msg},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7
                        )
                        reply = resp.choices[0].message.content
                        
                        # Kopyalama butonu çıksın diye st.code içine basıyoruz
                        st.code(reply, language="markdown") 
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                    
                    # Kalıcı Kayıt
                    save_history(st.session_state.messages)

                except Exception as e:
                    st.error("Hata.")
