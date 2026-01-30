import streamlit as st
import numpy as np
from groq import Groq
import json
import os
import time
import uuid
import urllib.parse

# --- 1. SİSTEM AYARLARI ---
st.set_page_config(
    page_title="Onto-AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS İLE "SABİT ÜST BAR" VE TASARIM ---
st.markdown("""
    <style>
    /* Google Font: Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    /* TEMEL AYARLAR */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0E0E0E; color: #E0E0E0; }
    
    /* STREAMLIT'İN KENDİ HEADER'INI GİZLE */
    header { visibility: hidden; }
    
    /* --- ÖZEL SABİT ÜST BAR (HEADER) --- */
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 60px;
        background-color: #161616; /* Koyu Gri Bar */
        border-bottom: 1px solid #333;
        z-index: 99999; /* Her şeyin üstünde */
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Header Sol: İsim */
    .header-title {
        font-size: 18px;
        font-weight: 600;
        color: #fff;
        margin-left: 50px; /* Mobilde hamburger menüye yer açmak için */
    }
    .header-subtitle { font-size: 12px; color: #888; margin-left: 8px; font-weight: 400; }
    
    /* Header Sağ: Profil */
    .header-profile {
        width: 35px;
        height: 35px;
        background: linear-gradient(135deg, #444, #222);
        border-radius: 50%;
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        border: 1px solid #555;
        cursor: pointer;
    }
    
    /* İÇERİĞİ AŞAĞI İTME (Header altında kalmasın diye) */
    .main .block-container {
        padding-top: 80px !important; 
        padding-bottom: 100px !important;
    }

    /* YAN MENÜ (SIDEBAR) */
    [data-testid="stSidebar"] {
        background-color: #121212;
        border-right: 1px solid #222;
        padding-top: 20px;
    }
    
    /* MESAJ KUTULARI (Minimalist) */
    .stChatMessage { background: transparent; border: none; padding: 10px 0; }
    [data-testid="chatAvatarIcon-user"] { background-color: #333; }
    [data-testid="chatAvatarIcon-assistant"] { background-color: #000; border: 1px solid #333; }
    
    /* INPUT ALANI (Sabit Alt) */
    .stChatInput {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 800px;
        z-index: 1000;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SABİT HEADER'I ÇİZME (HTML) ---
# Bu kısım sayfa ne kadar kayarsa kaysın en üstte sabit kalır.
st.markdown("""
    <div class="fixed-header">
        <div style="display:flex; align-items:center;">
            <div class="header-title">Onto-AI</div>
            <div class="header-subtitle">v3.0 Genesis</div>
        </div>
        <div class="header-profile" title="Kullanıcı Profili">U</div>
    </div>
""", unsafe_allow_html=True)

# --- 4. VERİTABANI VE AYARLAR ---
DB_FILE = "onto_v3.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"sessions": {}, "current_id": None}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

if "db" not in st.session_state:
    st.session_state.db = load_db()

# --- 5. YAN MENÜ (ÇEKMECE) ---
with st.sidebar:
    # "Onto-AI" logosu zaten üst barda, buraya menü elemanlarını koyuyoruz.
    
    if st.button("＋ Yeni Konuşma", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.db["sessions"][new_id] = {"title": "Yeni Sohbet", "messages": [], "ts": time.time()}
        st.session_state.db["current_id"] = new_id
        save_db(st.session_state.db)
        st.rerun()

    st.markdown("---")
    
    # Ontogenetik Ayar (w) - Özgünlük Burada
    st.caption("🧠 ZİHİN DURUMU (w)")
    t_val = st.slider("Agency Level", 0, 100, 50, label_visibility="collapsed")
    w_agency = 1 - np.exp(-0.05 * t_val)
    
    # w Durumuna Göre Etiket
    if w_agency < 0.3: status_text = "Pasif / Onaylayıcı"
    elif w_agency > 0.7: status_text = "Aktif / Özgün"
    else: status_text = "Dengeli"
    st.caption(f"Durum: {status_text} ({w_agency:.2f})")
    
    st.markdown("---")
    
    # Sohbet Geçmişi
    st.caption("GEÇMİŞ")
    sessions = sorted(st.session_state.db["sessions"].items(), key=lambda x: x[1].get("ts", 0), reverse=True)
    
    for s_id, s_data in sessions:
        title = s_data.get("title", "Sohbet")
        if st.button(f"💬 {title[:18]}..", key=s_id, use_container_width=True):
            st.session_state.db["current_id"] = s_id
            save_db(st.session_state.db)
            st.rerun()

    # Araçlar
    with st.expander("🛠️ Araçlar"):
        if st.button("🗑️ Tümünü Sil"):
            st.session_state.db["sessions"] = {}
            st.session_state.db["current_id"] = None
            save_db(st.session_state.db)
            st.rerun()
            
    # API Key
    st.markdown("---")
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
    else:
        api_key = st.text_input("API Key", type="password", placeholder="gsk_...")

# --- 6. SOHBET MANTIĞI ---

# Aktif Oturum Kontrolü
if not st.session_state.db["current_id"]:
    new_id = str(uuid.uuid4())
    st.session_state.db["sessions"][new_id] = {"title": "Yeni Sohbet", "messages": [], "ts": time.time()}
    st.session_state.db["current_id"] = new_id

current_id = st.session_state.db["current_id"]
chat_data = st.session_state.db["sessions"][current_id]

# Mesajları Göster
if not chat_data["messages"]:
    # Boş Ekran (Temiz ve Minimal)
    st.markdown(f"""
    <div style="text-align: center; margin-top: 10vh; opacity: 0.3;">
        <h1>Onto-AI</h1>
        <p>w-Ajans Seviyesi: {w_agency:.2f}</p>
    </div>
    """, unsafe_allow_html=True)

for msg in chat_data["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("img"): st.image(msg["img"])

# --- 7. INPUT VE AI MOTORU ---
if prompt := st.chat_input("Mesaj gönder..."):
    
    # Başlık Atama (İlk mesajsa)
    if not chat_data["messages"]:
        st.session_state.db["sessions"][current_id]["title"] = prompt[:25]
    
    # Kullanıcıyı Kaydet
    chat_data["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    if not api_key:
        st.error("API Key eksik.")
    else:
        client = Groq(api_key=api_key)
        
        with st.chat_message("assistant"):
            # Düşünme Efekti (Basit text)
            status = st.empty()
            status.markdown("*Düşünülüyor...*")
            
            try:
                # --- ONTOGENETİK PROMPT MÜHENDİSLİĞİ ---
                if w_agency < 0.3:
                    persona = "Sen PASİF bir asistansın. Kısa cevap ver. Yorum yapma. Sadece onayla."
                elif w_agency > 0.7:
                    persona = "Sen ÖZGÜN bir zihinsin. Kendi fikirlerini savun. Eleştirel ol. Felsefi yaklaş."
                else:
                    persona = "Sen YARDIMCI bir asistansın. Dengeli ve net ol."
                
                sys_msg = (
                    f"Sen Onto-AI'sin. {persona} "
                    f"Kullanıcı 'çiz' derse reddetme, betimle. "
                    f"Asla 'Merhaba İnsan' gibi garip girişler yapma. Doğal ol."
                )

                # Yanıt Al
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": prompt}],
                    temperature=0.7
                )
                reply = resp.choices[0].message.content
                
                # Resim Kontrolü (Arka Planda)
                img_url = None
                if any(x in prompt.lower() for x in ["çiz", "resim", "görsel"]):
                    safe_p = urllib.parse.quote(prompt[:100])
                    seed = int(time.time())
                    # w'ye göre stil
                    style = "minimalist" if w_agency < 0.5 else "surreal"
                    img_url = f"https://pollinations.ai/p/{safe_p}_{style}?width=1024&height=1024&seed={seed}&nologo=true"
                
                # Ekrana Bas
                status.markdown(reply)
                if img_url: st.image(img_url)
                
                # Kaydet
                chat_data["messages"].append({"role": "assistant", "content": reply, "img": img_url})
                st.session_state.db["sessions"][current_id] = chat_data
                save_db(st.session_state.db)
                
            except Exception as e:
                status.error("Hata oluştu.")
