import streamlit as st
import numpy as np
from groq import Groq
import json
import os
import time
import uuid
import urllib.parse
from datetime import datetime

# --- 1. AYARLAR ---
st.set_page_config(
    page_title="Onto-AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS: KIRMIZIYI YOK ET, AVATARLARI DEĞİŞTİR, MENÜYÜ DÜZENLE ---
st.markdown("""
    <style>
    /* Google Font: Inter (Ciddiyet için) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Arka Planlar (Simsiyah - Minimalist) */
    .stApp { background-color: #050505; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #0E0E0E; border-right: 1px solid #222; }
    
    /* KIRMIZI ÇERÇEVELERİ YOK ET (Input Alanı) */
    .stChatInput, .stTextInput input, .stTextArea textarea {
        border-color: #333 !important;
        box-shadow: none !important;
    }
    .stChatInput:focus-within {
        border-color: #666 !important; /* Odaklanınca Koyu Gri */
    }
    
    /* AVATARLARI DEĞİŞTİRME (Kare ve Minimalist) */
    .stChatMessage .stChatMessageAvatar {
        background-color: transparent !important;
        border-radius: 4px !important; /* Yuvarlak değil karemsi */
    }
    /* Kullanıcı Avatarı (Sağ taraf gibi davranır ama soldadır) */
    [data-testid="chatAvatarIcon-user"] {
        background: #333 !important;
        color: #fff !important;
        border-radius: 4px;
    }
    /* AI Avatarı */
    [data-testid="chatAvatarIcon-assistant"] {
        background: #000 !important;
        border: 1px solid #444;
        border-radius: 4px;
    }

    /* MENÜ DÜZENİ (Üstte Yeni Sohbet, Altta Ayarlar) */
    /* Bu bir CSS hilesidir: Sidebar'daki elementleri esneterek ayarları alta iteriz */
    [data-testid="stSidebarUserContent"] {
        display: flex;
        flex-direction: column;
        height: 100vh;
    }
    .sidebar-spacer { flex-grow: 1; } /* Bu boşluk div'i her şeyi alta itecek */
    
    /* BUTON STİLLERİ (Emoji yok, gri ve ciddi) */
    .stButton button {
        background-color: #111;
        color: #ccc;
        border: 1px solid #333;
        border-radius: 6px;
        transition: all 0.2s;
        text-align: left !important;
    }
    .stButton button:hover {
        border-color: #fff;
        color: #fff;
        background-color: #222;
    }
    
    /* Radyo Butonları (Hızlı/Temkinli Mod Seçici) */
    [data-testid="stRadio"] > label { display: none; } /* Başlığı gizle */
    [data-testid="stRadio"] div[role="radiogroup"] {
        display: flex;
        gap: 10px;
        background: transparent;
    }
    
    /* Dosya Yükleyici */
    [data-testid="stFileUploader"] {
        padding: 10px;
        border: 1px dashed #333;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. VERİTABANI ---
DB_FILE = "onto_db_v4.json"

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

# --- 4. SOL MENÜ (ÖZEL YAPI) ---
with st.sidebar:
    # 1. ÜST BÖLÜM: Logo ve Yeni Sohbet
    st.markdown("### ONTO**AI**")
    
    if st.button("＋ YENİ SOHBET", use_container_width=True, type="primary"):
        new_id = str(uuid.uuid4())
        st.session_state.db["sessions"][new_id] = {
            "title": "Yeni Oturum", "messages": [], "ts": time.time()
        }
        st.session_state.db["current_id"] = new_id
        save_db(st.session_state.db)
        st.rerun()

    st.markdown("---")
    
    # 2. ORTA BÖLÜM: Sohbet Geçmişi
    st.caption("BELLEK")
    sessions = sorted(st.session_state.db["sessions"].items(), key=lambda x: x[1].get("ts", 0), reverse=True)
    
    # Scroll edilebilir alan (Çok fazla sohbet varsa sayfa uzamasın)
    with st.container(height=300, border=False):
        for s_id, s_data in sessions:
            title = s_data.get("title", "Adsız")
            # Aktif olanı işaretle
            label = f"▪ {title[:20]}" if s_id == st.session_state.db["current_id"] else title[:20]
            if st.button(label, key=s_id, use_container_width=True):
                st.session_state.db["current_id"] = s_id
                save_db(st.session_state.db)
                st.rerun()

    # 3. BOŞLUK (CSS ile ayarları en alta itmek için)
    st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)
    
    # 4. ALT BÖLÜM: Ayarlar ve Ontogenetik Durum
    with st.expander("AYARLAR / LOGO"):
        # Ontogenetik Sürgü (GERÇEK İŞLEV)
        st.caption("ONTOGENETİK DURUM (w)")
        t_val = st.slider("w", 0, 100, 50, label_visibility="collapsed")
        w_agency = 1 - np.exp(-0.05 * t_val)
        
        st.write(f"w: {w_agency:.2f}")
        
        # API Key
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
        else:
            api_key = st.text_input("API Key", type="password")
            
        if st.button("TÜM BELLEĞİ SİL"):
            st.session_state.db["sessions"] = {}
            st.session_state.db["current_id"] = None
            save_db(st.session_state.db)
            st.rerun()

# --- 5. ANA EKRAN ---

# Oturum Kontrolü
if not st.session_state.db["current_id"]:
    new_id = str(uuid.uuid4())
    st.session_state.db["sessions"][new_id] = {"title": "Yeni Oturum", "messages": [], "ts": time.time()}
    st.session_state.db["current_id"] = new_id

current_id = st.session_state.db["current_id"]
chat_data = st.session_state.db["sessions"][current_id]

# Başlık
st.subheader(chat_data.get("title", "Onto-AI"))

# Mesajları Göster (Custom Avatar Logic)
for msg in chat_data["messages"]:
    with st.chat_message(msg["role"]): 
        # NOT: CSS ile avatarlar kare ve renksiz yapıldı
        st.markdown(msg["content"])
        if msg.get("files"):
            st.markdown(f"**EK:** `{msg['files']}`") # Dosya ismini göster

# --- 6. GİRİŞ ALANI VE KONTROLLER (ALTA SABİT) ---

# Giriş alanının hemen üstüne "Mod Seçici" ve "Dosya" koyuyoruz
with st.container():
    # MOD SEÇİCİ (Hızlı / Temkinli / Profesyonel)
    col_mode, col_file = st.columns([3, 1])
    
    with col_mode:
        thinking_mode = st.radio(
            "Düşünme Modu:",
            ["Hızlı", "Temkinli", "Profesyonel"],
            horizontal=True,
            label_visibility="collapsed"
        )
    
    with col_file:
        # Dosya Yükleme (Expander içinde gizli, yer kaplamasın)
        with st.popover("Dosya Ekle"):
            uploaded_file = st.file_uploader("Dosya seç", type=['txt', 'pdf', 'csv', 'py'])

# Giriş Kutusu (Kırmızı kenar yok, CSS ile düzeltildi)
if prompt := st.chat_input("Mesaj yaz..."):
    
    # 1. Dosya İşleme
    file_content = ""
    file_name = None
    if uploaded_file is not None:
        try:
            # Sadece metin okuyabiliriz şimdilik (OCR yok)
            stringio = uploaded_file.getvalue().decode("utf-8")
            file_content = f"\n\n[DOSYA İÇERİĞİ - {uploaded_file.name}]:\n{stringio}\n"
            file_name = uploaded_file.name
        except:
            file_content = f"\n\n[DOSYA EKLENDİ - {uploaded_file.name} (İçerik okunamadı)]"

    # 2. Kullanıcı Kaydı
    full_prompt = prompt + file_content
    chat_data["messages"].append({
        "role": "user", 
        "content": prompt, # Ekranda dosya içeriği kirliliği yapma, sadece prompt göster
        "files": file_name
    })
    
    # Başlık Atama
    if len(chat_data["messages"]) == 1:
        st.session_state.db["sessions"][current_id]["title"] = prompt[:20]

    with st.chat_message("user"): st.markdown(prompt)
    if file_name: st.markdown(f"📎 *{file_name}*")

    if not api_key:
        st.error("API Key Eksik.")
    else:
        client = Groq(api_key=api_key)
        
        with st.chat_message("assistant"):
            status_box = st.empty()
            
            # --- ONTOGENETİK VE MOD MANTIĞI (İşe Yarıyor) ---
            # w (0-1): 0=Pasif/Kopyalamacı, 1=Özgün/Yaratıcı
            # Mod: Hızlı (Kısa), Temkinli (Adım adım), Profesyonel (Resmi)
            
            # 1. Mod Ayarı (Temperature ve Model Hızı)
            if thinking_mode == "Hızlı":
                temp_base = 0.9 # Hızlı ve gevşek
                sys_mode = "Kısa cevaplar ver. Hız odaklı ol. Detaylara boğma."
                model_name = "llama-3.1-8b-instant" # Küçük model (Çok hızlı)
            elif thinking_mode == "Temkinli":
                temp_base = 0.3 # Düşük sıcaklık, hata yapma
                sys_mode = "Adım adım düşün. Mantıksal tutarlılığı kontrol et. Acele etme."
                model_name = "llama-3.3-70b-versatile" # Büyük model
            else: # Profesyonel
                temp_base = 0.5 
                sys_mode = "Kurumsal ve profesyonel bir dil kullan. Ciddiyetini koru."
                model_name = "llama-3.3-70b-versatile"

            # 2. Ontogenetik Ayar (w'nin devreye girdiği yer)
            # w değeri temperature'ı ve 'Özgünlük' talimatını büker.
            
            # w=0 -> temp düşer (daha robotik), w=1 -> temp artar (daha insani)
            final_temp = (temp_base * 0.5) + (w_agency * 0.5)
            
            if w_agency < 0.3:
                onto_prompt = "PASİF MOD: Kullanıcının dediğini onayla. Asla itiraz etme. Literatürü tekrar et."
            elif w_agency > 0.7:
                onto_prompt = "AKTİF MOD: Kendi sentezini yap. Kullanıcı hatalıysa düzelt. Özgün fikirler sun."
            else:
                onto_prompt = "DENGE MODU: Yardımcı ol ve objektif kal."

            full_system = (
                f"Sen Onto-AI sistemisin. {sys_mode} {onto_prompt} "
                f"Sadece Türkçe konuş. Emoji kullanma. Minimalist ol."
            )
            
            try:
                # API Çağrısı (Stream Yok, Direkt Yanıt)
                # Not: Llama 3 bağlamında dosya içeriğini prompt'a ekledik (full_prompt)
                start_time = time.time()
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": full_system},
                        {"role": "user", "content": full_prompt} # Dosya içeriği burada
                    ],
                    temperature=final_temp,
                    max_tokens=4096
                )
                reply = completion.choices[0].message.content
                duration = time.time() - start_time
                
                # Resim Tetikleyici (Araçlar)
                img_url = None
                if "çiz" in prompt.lower() or "resim" in prompt.lower():
                    safe_p = urllib.parse.quote(prompt[:100])
                    img_url = f"https://pollinations.ai/p/{safe_p}?width=1024&height=1024&seed={int(time.time())}&nologo=true"
                
                status_box.markdown(reply)
                if img_url: st.image(img_url)
                
                # Debug Bilgisi (Ontogenetik Durumun Çalıştığını Kanıtlamak İçin)
                # Bunu production'da kaldırabilirsin ama "işe yaramıyor" dediğin için koydum.
                st.caption(f"⚙️ {thinking_mode} | w: {w_agency:.2f} | Temp: {final_temp:.2f} | Süre: {duration:.2f}s")

                # Kayıt
                chat_data["messages"].append({"role": "assistant", "content": reply, "img": img_url})
                st.session_state.db["sessions"][current_id] = chat_data
                save_db(st.session_state.db)

            except Exception as e:
                status_box.error(f"Hata: {e}")
