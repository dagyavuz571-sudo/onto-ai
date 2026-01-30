import streamlit as st
import numpy as np
from groq import Groq
import json
import os
import time
import uuid
import urllib.parse

# --- 1. SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="OntoAI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. GÖRSEL AMELİYAT (CSS) ---
st.markdown("""
    <style>
    /* IMPORT FONT: INTER */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap');
    * { font-family: 'Inter', sans-serif !important; }

    /* GENEL RENKLER (SİYAH/GRİ) */
    .stApp { background-color: #000000; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #0a0a0a; border-right: 1px solid #222; }
    
    /* HEADER'I GİZLE */
    header { display: none !important; }
    
    /* --- KIRMIZI/TURUNCU YOK ETME TİMİ --- */
    /* Odaklanma renklerini (Focus Ring) gri yap */
    .stTextInput input:focus, .stTextArea textarea:focus, .stChatInput:focus-within {
        border-color: #666 !important;
        box-shadow: 0 0 0 1px #666 !important;
    }
    /* Butonların kırmızılığını al */
    button:active, button:focus {
        border-color: #666 !important;
        background-color: #222 !important;
        color: white !important;
    }
    /* Link renkleri */
    a { color: #aaa !important; }

    /* --- SABİT LOGO (SOL ÜST) --- */
    .fixed-logo {
        position: fixed;
        top: 20px;
        left: 80px; /* Menü kapalıyken de görünsün diye */
        font-size: 22px;
        font-weight: 800;
        color: #fff;
        z-index: 99999;
        pointer-events: none;
        letter-spacing: -1px;
    }
    
    /* MENÜ KAPALIYKEN LOGOYU SOLA ÇEK (CSS Hilesi) */
    [data-testid="stSidebar"][aria-expanded="false"] ~ .main .fixed-logo {
        left: 20px;
    }

    /* --- GİRİŞ ALANI VE TOOLBAR --- */
    /* Giriş kutusunu alta sabitle ve stil ver */
    .stChatInput {
        padding-bottom: 20px;
    }
    div[data-testid="stChatInput"] {
        background-color: #000 !important;
        border: 1px solid #333 !important;
        color: white !important;
        border-radius: 10px;
    }

    /* --- TOOLBAR (Girişin Üstündeki Alan) --- */
    .toolbar-container {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 5px 10px;
        background: #000;
        border-top: 1px solid #222;
        position: fixed;
        bottom: 70px; /* Chat inputun hemen üstü */
        left: 20px; /* Sidebar kapalıyken */
        right: 20px;
        z-index: 1000;
        width: auto;
        border-radius: 8px 8px 0 0;
    }
    /* Sidebar açıkken toolbarı sağa it */
    [data-testid="stSidebar"][aria-expanded="true"] ~ .main .toolbar-container {
        left: 350px; /* Sidebar genişliği kadar */
    }

    /* --- AVATARLAR VE MESAJLAR --- */
    .stChatMessage { background: transparent; }
    [data-testid="chatAvatarIcon-user"] { background-color: #333 !important; color: white !important; }
    [data-testid="chatAvatarIcon-assistant"] { background-color: #000 !important; border: 1px solid #444; }

    /* --- MENÜ DÜZENLEMELERİ --- */
    .stButton button {
        width: 100%;
        text-align: left;
        background: transparent;
        border: none;
        color: #888;
        padding: 8px;
    }
    .stButton button:hover {
        background: #151515;
        color: #fff;
        border-radius: 5px;
    }
    /* Yeni Sohbet Butonu (Özel) */
    div[data-testid="stSidebar"] .stButton:first-of-type button {
        border: 1px solid #333;
        text-align: center;
        margin-bottom: 20px;
        color: #fff;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SABİT LOGO ---
st.markdown('<div class="fixed-logo">OntoAI</div>', unsafe_allow_html=True)

# --- 4. VERİTABANI ---
DB_FILE = "ontoai_final.json"

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

# --- 5. YAN MENÜ (SOL) ---
with st.sidebar:
    st.write("") # Logo payı
    st.write("") 
    st.write("") 

    # YENİ SOHBET
    if st.button("＋ YENİ SOHBET"):
        new_id = str(uuid.uuid4())
        st.session_state.db["sessions"][new_id] = {"title": "Yeni Oturum", "messages": [], "ts": time.time()}
        st.session_state.db["current_id"] = new_id
        save_db(st.session_state.db)
        st.rerun()
    
    st.caption("GEÇMİŞ")
    
    # Sohbet Listesi
    sessions = sorted(st.session_state.db["sessions"].items(), key=lambda x: x[1].get("ts", 0), reverse=True)
    for s_id, s_data in sessions:
        title = s_data.get("title", "Adsız")
        active = "Target" if s_id == st.session_state.db["current_id"] else ""
        label = f"▪ {title[:18]}" if active else title[:18]
        
        if st.button(label, key=s_id):
            st.session_state.db["current_id"] = s_id
            save_db(st.session_state.db)
            st.rerun()

    st.divider()
    
    # ONTOGENETİK AYARLAR (Menünün Altı)
    with st.expander("SİSTEM AYARLARI", expanded=True):
        st.caption("Ontogenetik Durum (w)")
        t_val = st.slider("w-değeri", 0, 100, 50, label_visibility="collapsed")
        w_agency = 1 - np.exp(-0.05 * t_val)
        
        # Görsel Geri Bildirim
        if w_agency < 0.3: st.caption(f"w: {w_agency:.2f} (Robotik)")
        elif w_agency > 0.7: st.caption(f"w: {w_agency:.2f} (Özgün/Kaotik)")
        else: st.caption(f"w: {w_agency:.2f} (Dengeli)")

        # API KEY
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
        else:
            api_key = st.text_input("API Key", type="password")

# --- 6. SOHBET EKRANI ---
if not st.session_state.db["current_id"]:
    new_id = str(uuid.uuid4())
    st.session_state.db["sessions"][new_id] = {"title": "Yeni Oturum", "messages": [], "ts": time.time()}
    st.session_state.db["current_id"] = new_id

current_id = st.session_state.db["current_id"]
chat_data = st.session_state.db["sessions"][current_id]

# Başlık (Sayfanın ortasında dursun)
st.markdown(f"<div style='text-align:center; color:#444; margin-bottom: 20px; font-size: 14px;'>{chat_data.get('title','')}</div>", unsafe_allow_html=True)

# Mesajları Bas
for msg in chat_data["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("files"): st.caption(f"📎 {msg['files']}")
        if msg.get("img"): st.image(msg["img"])

# --- 7. ARAÇ ÇUBUĞU VE GİRİŞ (ALTTA BİRLEŞİK) ---

# Streamlit'te giriş kutusunun üstüne bir şey koymak için 'container' kullanıyoruz.
# Ancak görsel olarak birleşik durması için yukarıdaki CSS 'toolbar-container' class'ını kullanacak.

with st.container():
    # MOD VE DOSYA SEÇİMİ (Chat Input'un üstüne denk gelecek)
    col1, col2, col3 = st.columns([2, 1, 4])
    
    with col1:
        # Mod Seçimi (Radio ama yatay)
        mode = st.selectbox("Mod", ["Hızlı", "Temkinli", "Profesyonel"], label_visibility="collapsed")
    
    with col2:
        # Dosya Yükleme (Popover içinde gizli)
        with st.popover("📎 Ekle"):
            uploaded_file = st.file_uploader("Dosya", label_visibility="collapsed")

# GİRİŞ KUTUSU
if prompt := st.chat_input("Düşünceni yaz..."):
    
    # Dosya İşleme
    file_info = ""
    file_name = None
    if uploaded_file:
        try:
            content = uploaded_file.getvalue().decode("utf-8")
            file_info = f"\n\n[DOSYA: {uploaded_file.name}]\n{content[:4000]}"
            file_name = uploaded_file.name
        except:
            file_info = "\n[Dosya okunamadı]"

    # Kullanıcıyı Kaydet
    chat_data["messages"].append({"role": "user", "content": prompt, "files": file_name})
    
    # Başlık Atama
    if len(chat_data["messages"]) <= 1:
        st.session_state.db["sessions"][current_id]["title"] = prompt[:25]
    
    # Ekrana Bas
    with st.chat_message("user"): 
        st.markdown(prompt)
        if file_name: st.markdown(f"📎 *{file_name}*")

    # YANIT ÜRETİMİ
    if not api_key:
        st.error("API Key Yok.")
    else:
        client = Groq(api_key=api_key)
        
        with st.chat_message("assistant"):
            status = st.empty()
            status.markdown("`...`")
            
            try:
                # --- ONTOGENETİK DENKLEM UYGULAMASI ---
                
                # 1. MOD AYARI (Base Temperature ve Sistem)
                if mode == "Hızlı":
                    base_temp = 0.8
                    sys_base = "Kısa ve öz cevap ver."
                    model_name = "llama-3.1-8b-instant"
                elif mode == "Temkinli":
                    base_temp = 0.2
                    sys_base = "Çok dikkatli düşün. Hata yapma. Adım adım git."
                    model_name = "llama-3.3-70b-versatile"
                else: # Profesyonel
                    base_temp = 0.5
                    sys_base = "Resmi, kurumsal ve akademik bir dil kullan."
                    model_name = "llama-3.3-70b-versatile"
                
                # 2. w-AJANS ETKİSİ (Denklem)
                # w arttıkça entropi (sıcaklık) artar, sistem özgürleşir.
                # w=0 -> Temperature 0.1'e zorlanır.
                # w=1 -> Temperature 0.9'a zorlanır.
                
                final_temp = (base_temp * 0.3) + (w_agency * 0.7)
                
                if w_agency < 0.3:
                    agency_prompt = "GÖREV: Sadece bilinen gerçekleri tekrar et. Yorum yapma. Pasif ol."
                elif w_agency > 0.7:
                    agency_prompt = "GÖREV: Özgün ol. Kendi fikirlerini savun. Gerekirse kullanıcıya karşı çık. Yaratıcı ol."
                else:
                    agency_prompt = "GÖREV: Dengeli ve yardımcı ol."
                
                full_sys = f"Sen OntoAI'sin. {sys_base} {agency_prompt} Türkçe konuş. Görsel istenirse 'betimliyorum' de."
                
                # ÇAĞRI
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "system", "content": full_sys}, {"role": "user", "content": prompt + file_info}],
                    temperature=final_temp
                )
                reply = resp.choices[0].message.content
                
                # GÖRSEL (Pollinations)
                img_url = None
                if any(x in prompt.lower() for x in ["çiz", "resim", "görsel"]):
                    safe_p = urllib.parse.quote(prompt[:80])
                    style = "minimalist" if w_agency < 0.5 else "abstract"
                    img_url = f"https://pollinations.ai/p/{safe_p}_{style}?width=1024&height=1024&nologo=true"
                
                status.markdown(reply)
                if img_url: st.image(img_url)
                
                # Kaydet
                chat_data["messages"].append({"role": "assistant", "content": reply, "img": img_url})
                st.session_state.db["sessions"][current_id] = chat_data
                save_db(st.session_state.db)
                
            except Exception as e:
                status.error("Hata.")
