import streamlit as st
import numpy as np
from groq import Groq
import json
import os
import time
import uuid

# --- 1. GEMINI/CHATGPT ARAYÜZ AYARLARI ---
st.set_page_config(
    page_title="Onto-AI",
    layout="wide",
    initial_sidebar_state="expanded" # MENÜYÜ ZORLA AÇIK TUT
)

# --- 2. CSS İLE ARAYÜZÜ "HACKLEME" ---
st.markdown("""
    <style>
    /* 1. Streamlit'in kendi çirkin üst barını ve hamburger menüsünü yok et */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 2. Arka Plan Renkleri (Gemini/GPT Dark Mode) */
    .stApp { background-color: #131314; color: #E3E3E3; } /* Ana Ekran */
    [data-testid="stSidebar"] { background-color: #1E1F20; border-right: 1px solid #333; } /* Sol Menü */
    
    /* 3. Sol Menüdeki Butonları "Liste Elemanı" Gibi Yap */
    .stButton button {
        background-color: transparent;
        color: #E3E3E3;
        border: none;
        text-align: left;
        padding: 10px;
        width: 100%;
        transition: background 0.2s;
        border-radius: 8px;
    }
    .stButton button:hover {
        background-color: #333;
        color: white;
    }
    
    /* 4. Yeni Sohbet Butonu (Özel Stil) */
    div[data-testid="stSidebar"] .stButton:first-child button {
        background-color: #2D2E2F;
        border: 1px solid #444;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* 5. Mesaj Balonları (Sınırları Kaldır) */
    .stChatMessage { background: transparent; }
    [data-testid="chatAvatarIcon-user"] { background-color: #333; }
    [data-testid="chatAvatarIcon-assistant"] { background-color: #000; border: 1px solid #444; }

    /* 6. Yazı Yazma Alanı (En alta yapışık) */
    .stChatInput { bottom: 20px; }
    
    /* Font Ayarı */
    * { font-family: 'Inter', sans-serif; }
    </style>
""", unsafe_allow_html=True)

# --- 3. VERİTABANI (JSON) ---
DB_FILE = "chat_db.json"

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

# --- 4. SOL MENÜ (SABİT) ---
with st.sidebar:
    # LOGO
    st.markdown("### **Onto**AI", unsafe_allow_html=True)
    
    # YENİ SOHBET BUTONU
    if st.button("＋ Yeni Sohbet", key="new_chat"):
        new_id = str(uuid.uuid4())
        st.session_state.db["sessions"][new_id] = {"title": "Yeni Sohbet", "messages": [], "time": time.time()}
        st.session_state.db["current_id"] = new_id
        save_db(st.session_state.db)
        st.rerun()

    st.markdown("---")
    st.caption("Son Sohbetler")

    # GEÇMİŞ LİSTESİ (Sıralı)
    sorted_chats = sorted(
        st.session_state.db["sessions"].items(),
        key=lambda x: x[1].get("time", 0),
        reverse=True
    )

    for c_id, c_data in sorted_chats:
        # Başlık çok uzunsa kes
        title = c_data["title"]
        display_title = (title[:22] + '..') if len(title) > 22 else title
        
        # Aktif sohbeti işaretle (Boya)
        if c_id == st.session_state.db["current_id"]:
            display_title = f"➤ {display_title}"
            
        if st.button(display_title, key=c_id):
            st.session_state.db["current_id"] = c_id
            save_db(st.session_state.db)
            st.rerun()

    # EN ALTTA AYARLAR (Spacer ile aşağı itiyoruz)
    st.markdown("<br>" * 5, unsafe_allow_html=True) 
    st.markdown("---")
    
    # Ontogenetik Ayar (Mini)
    t_val = st.slider("Onto-Seviye (w)", 0, 100, 50, label_visibility="collapsed")
    w_agency = 1 - np.exp(-0.05 * t_val)
    st.caption(f"w: {w_agency:.2f}")

    # API Key
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
    else:
        api_key = st.text_input("API Key", type="password", placeholder="gsk_...")

# --- 5. ANA EKRAN (SOHBET) ---

# Aktif sohbet yoksa oluştur
if not st.session_state.db["current_id"]:
    new_id = str(uuid.uuid4())
    st.session_state.db["sessions"][new_id] = {"title": "Yeni Sohbet", "messages": [], "time": time.time()}
    st.session_state.db["current_id"] = new_id

current_id = st.session_state.db["current_id"]
chat_data = st.session_state.db["sessions"][current_id]

# MESAJLARI BAS
if not chat_data["messages"]:
    # Boş ekran, Gemini gibi "Nasıl yardım edebilirim?" yazısı
    st.markdown("""
    <div style="text-align: center; margin-top: 50px; opacity: 0.5;">
        <h1>Merhaba, İnsan.</h1>
        <p>Ontogenetik bilincim seninle konuşmaya hazır.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in chat_data["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("img"): st.image(msg["img"], width=400)

# --- 6. GİRİŞ ÇUBUĞU (SABİT) ---
if prompt := st.chat_input("Bir şeyler sor..."):
    
    # Başlık güncelleme (İlk mesajsa)
    if len(chat_data["messages"]) == 0:
        new_title = prompt if len(prompt) < 30 else prompt[:30]
        st.session_state.db["sessions"][current_id]["title"] = new_title

    # Kullanıcıyı ekle
    chat_data["messages"].append({"role": "user", "content": prompt})
    st.session_state.db["sessions"][current_id] = chat_data
    save_db(st.session_state.db)
    
    # Ekrana bas
    with st.chat_message("user"): st.markdown(prompt)

    if not api_key:
        st.warning("API Key girmedin.")
    else:
        client = Groq(api_key=api_key)
        
        with st.chat_message("assistant"):
            # Gemini tarzı nabız animasyonu
            placeholder = st.empty()
            placeholder.markdown("`⚡ Düşünüyor...`")
            
            try:
                # Sistem Talimatı
                sys_msg = (
                    f"Sen Onto-AI'sin. w={w_agency:.2f}. "
                    f"w düşükse kısa ve onaylayıcı ol. w yüksekse eleştirel ve özgün ol. "
                    f"Görsel istenirse 'betimliyorum' de."
                )
                
                # Cevap
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                reply = completion.choices[0].message.content
                
                # Resim Kontrolü
                img_url = None
                if any(x in prompt.lower() for x in ["çiz", "resim", "görsel"]):
                    safe_p = urllib.parse.quote(prompt[:100])
                    img_url = f"https://pollinations.ai/p/{safe_p}?width=1024&height=1024&seed={int(time.time())}&nologo=true"

                # Cevabı Bas
                placeholder.markdown(reply)
                if img_url: st.image(img_url)
                
                # Kaydet
                chat_data["messages"].append({"role": "assistant", "content": reply, "img": img_url})
                st.session_state.db["sessions"][current_id] = chat_data
                save_db(st.session_state.db)
                
                # Sol menüdeki başlık güncellensin diye ufak bir rerun (İsteğe bağlı)
                # st.rerun() 

            except Exception as e:
                placeholder.error("Hata oluştu.")
