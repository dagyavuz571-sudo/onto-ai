import streamlit as st
import numpy as np
from groq import Groq
import json
import os
import time
import uuid
import urllib.parse

# --- 1. MASAÜSTÜ İÇİN ZORUNLU AYAR ---
st.set_page_config(
    page_title="Onto-AI",
    layout="wide",
    initial_sidebar_state="expanded"  # <--- BURASI ÇOK ÖNEMLİ: Menüyü zorla açık tutar
)

# --- 2. CSS (Masaüstü ve Renkler) ---
st.markdown("""
    <style>
    /* Google Font: Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Arka Planlar (Simsiyah Tema) */
    .stApp { background-color: #0E0E0E; color: #E0E0E0; }
    
    /* SOL MENÜ (SIDEBAR) TASARIMI */
    [data-testid="stSidebar"] {
        background-color: #121212; /* Menü Rengi */
        border-right: 1px solid #333; /* Sağ Çizgi */
    }
    
    /* ÜSTTEKİ KIRMIZI ÇİZGİYİ GİZLE AMA MENÜ BUTONUNU GİZLEME! */
    header[data-testid="stHeader"] {
        background-color: transparent;
    }
    /* Sadece renkli çizgiyi (decoration) gizliyoruz, buton kalıyor */
    .stDeployButton { display: none; } 
    
    /* PROFİL KUTUSU (Sol Menünün en altına sabitleme hilesi) */
    .profile-box {
        margin-top: 20px;
        padding: 15px;
        background-color: #1A1A1A;
        border-radius: 10px;
        border: 1px solid #333;
        text-align: center;
        color: #888;
        font-size: 12px;
    }
    
    /* MESAJ KUTULARI */
    .stChatMessage { background: transparent; border: none; }
    [data-testid="chatAvatarIcon-user"] { background-color: #333; }
    [data-testid="chatAvatarIcon-assistant"] { background-color: #000; border: 1px solid #444; }
    
    /* INPUT ALANI (Sabit Alt) */
    .stChatInput { bottom: 30px; }
    
    /* SOHBET GEÇMİŞİ BUTONLARI */
    .stButton button {
        text-align: left;
        border: none;
        background: transparent;
        color: #bbb;
    }
    .stButton button:hover {
        background: #222;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. VERİTABANI ---
DB_FILE = "onto_desktop.json"

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

# --- 4. SOL MENÜ (ÇEKMECE) ---
with st.sidebar:
    # LOGO
    st.markdown("## Onto**AI**")
    
    # YENİ SOHBET (Büyük Buton)
    if st.button("＋ Yeni Sohbet", type="primary", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.db["sessions"][new_id] = {"title": "Yeni Sohbet", "messages": [], "ts": time.time()}
        st.session_state.db["current_id"] = new_id
        save_db(st.session_state.db)
        st.rerun()
        
    st.markdown("---")
    
    # AYARLAR (Ontogenetik Sürgü)
    st.caption("ONTOGENETİK DURUM (w)")
    t_val = st.slider("Agency", 0, 100, 50, label_visibility="collapsed")
    w_agency = 1 - np.exp(-0.05 * t_val)
    
    # Durum Metni
    if w_agency < 0.3: status = "Pasif (Onaylayıcı)"
    elif w_agency > 0.7: status = "Aktif (Özgün)"
    else: status = "Dengeli"
    st.caption(f"Durum: {status}")

    st.markdown("---")

    # GEÇMİŞ LİSTESİ (Scrol edilebilir alan)
    st.caption("GEÇMİŞ")
    
    # Tarihe göre sırala
    sessions = sorted(st.session_state.db["sessions"].items(), key=lambda x: x[1].get("ts", 0), reverse=True)
    
    for s_id, s_data in sessions:
        title = s_data.get("title", "Adsız Sohbet")
        # Aktif olanı işaretle
        prefix = "👉 " if s_id == st.session_state.db["current_id"] else ""
        if st.button(f"{prefix}{title[:20]}", key=s_id, use_container_width=True):
            st.session_state.db["current_id"] = s_id
            save_db(st.session_state.db)
            st.rerun()

    # BOŞLUK BIRAK VE PROFİLİ EN ALTA KOY
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # API KEY GİRİŞİ
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
    else:
        api_key = st.text_input("API Key", type="password", placeholder="gsk_...")
    
    # PROFİL KUTUSU (Görsel)
    st.markdown("""
        <div class="profile-box">
            <b>Kullanıcı Profili</b><br>
            Plan: Sınırsız<br>
            Sürüm: v4.1 Desktop
        </div>
    """, unsafe_allow_html=True)

# --- 5. ANA EKRAN ---

# Aktif Oturum Yoksa Yarat
if not st.session_state.db["current_id"]:
    new_id = str(uuid.uuid4())
    st.session_state.db["sessions"][new_id] = {"title": "Yeni Sohbet", "messages": [], "ts": time.time()}
    st.session_state.db["current_id"] = new_id

current_id = st.session_state.db["current_id"]
chat_data = st.session_state.db["sessions"][current_id]

# BAŞLIK (Sabit Üstte görünen isim)
st.markdown(f"### {chat_data.get('title', 'Onto-AI')}")

# Mesajları Göster
for msg in chat_data["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("img"): st.image(msg["img"], width=500)

# --- 6. MOTOR ---
if prompt := st.chat_input("Bir şeyler yaz..."):
    
    # İlk mesajsa başlık yap
    if not chat_data["messages"]:
        st.session_state.db["sessions"][current_id]["title"] = prompt[:30]

    # Kullanıcıyı Kaydet
    chat_data["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    if not api_key:
        st.error("Sol menüden API Key girmen lazım.")
    else:
        client = Groq(api_key=api_key)
        
        with st.chat_message("assistant"):
            status = st.empty()
            status.markdown("`⚡ Analiz ediliyor...`")
            
            try:
                # Prompt Mühendisliği
                if w_agency < 0.3:
                    persona = "Sen PASİF bir asistansın. Çok kısa, net, ansiklopedik cevaplar ver. Yorum katma."
                elif w_agency > 0.7:
                    persona = "Sen ÖZGÜN bir zihinsin. Kendi fikirlerini savun, eleştirel yaklaş, felsefi derinlik kat."
                else:
                    persona = "Sen DENGELİ bir asistansın. Yardımcı ol."
                
                sys_msg = f"Sen Onto-AI'sin. {persona}. Kullanıcı görsel isterse reddetme, 'Betimliyorum...' de."

                # Llama 3 Çağrısı
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": prompt}],
                    temperature=0.7
                )
                reply = resp.choices[0].message.content
                
                # Resim Var mı?
                img_url = None
                if any(x in prompt.lower() for x in ["çiz", "resim", "görsel"]):
                    safe_p = urllib.parse.quote(prompt[:100])
                    seed = int(time.time())
                    # w'ye göre stil
                    style = "minimalist" if w_agency < 0.5 else "cinematic"
                    img_url = f"https://pollinations.ai/p/{safe_p}_{style}?width=1024&height=1024&seed={seed}&nologo=true"
                
                status.markdown(reply)
                if img_url: st.image(img_url)
                
                # Kaydet
                chat_data["messages"].append({"role": "assistant", "content": reply, "img": img_url})
                st.session_state.db["sessions"][current_id] = chat_data
                save_db(st.session_state.db)
                
            except Exception as e:
                status.error(f"Hata: {e}")
