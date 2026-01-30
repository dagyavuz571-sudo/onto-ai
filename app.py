import streamlit as st
import numpy as np
from groq import Groq
import json
import os
import time
import uuid
import urllib.parse

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="OntoAI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS: KIRMIZIYI YOK ET, LOGOYU ÇAK, PANELİ DÜZELT ---
st.markdown("""
    <style>
    /* FONT */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
    * { font-family: 'Inter', sans-serif !important; }

    /* RENKLER VE ARKA PLAN (SİYAH/GRİ) */
    .stApp { background-color: #050505; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #0a0a0a; border-right: 1px solid #222; }

    /* HEADER GİZLEME (Streamlit'in kendi barı) */
    header { visibility: hidden; }

    /* --- ÖZEL SABİT LOGO (SOL ÜST) --- */
    .fixed-logo {
        position: fixed; top: 15px; left: 60px; z-index: 99999;
        font-size: 20px; font-weight: 800; color: #fff;
        letter-spacing: -1px; text-shadow: 0 0 10px rgba(0,0,0,0.8);
        pointer-events: none;
    }
    
    /* MENÜ DARALINCA LOGO KAYMASI İÇİN AYAR */
    [data-testid="stSidebar"][aria-expanded="false"] ~ .main .fixed-logo {
        left: 20px; /* Menü kapanınca sola yanaş */
    }

    /* --- KIRMIZI RENGİ SİLME OPERASYONU --- */
    /* Input odaklanınca çıkan kırmızı çizgiyi gri yap */
    .stTextInput input:focus, .stTextArea textarea:focus, .stChatInput:focus-within {
        border-color: #555 !important;
        box-shadow: 0 0 5px rgba(255,255,255,0.1) !important;
    }
    /* Normal kenarlıklar */
    .stTextInput input, .stChatInput {
        border: 1px solid #333 !important;
        background-color: #111 !important;
        color: white !important;
    }

    /* KONTROL PANELİ (Girişin Üstü) */
    .control-panel {
        background-color: #0e0e0e;
        border-top: 1px solid #222;
        padding: 10px;
        position: fixed;
        bottom: 80px; /* Giriş çubuğunun üstü */
        left: 0; right: 0;
        z-index: 999;
        display: flex;
        justify-content: center;
        gap: 20px;
    }
    
    /* AVATARLAR (Kare ve Minimal) */
    .stChatMessage .stChatMessageAvatar {
        background-color: #222 !important;
        border-radius: 4px !important;
        color: white !important;
    }
    [data-testid="chatAvatarIcon-assistant"] { background-color: #000 !important; border: 1px solid #444; }

    /* BUTONLAR */
    .stButton button {
        background: #111; color: #aaa; border: 1px solid #333;
        border-radius: 6px; transition: 0.3s;
    }
    .stButton button:hover {
        border-color: #fff; color: #fff; background: #222;
    }

    /* MOD SEÇİCİ (Radio Button Yatay) */
    div[role="radiogroup"] { display: flex; gap: 15px; justify-content: center; }
    div[role="radiogroup"] label { 
        background: #111; padding: 5px 15px; border-radius: 15px; border: 1px solid #333; cursor: pointer;
    }
    div[role="radiogroup"] label:hover { border-color: #666; }
    
    </style>
""", unsafe_allow_html=True)

# --- 3. SABİT LOGO (HTML) ---
st.markdown('<div class="fixed-logo">OntoAI</div>', unsafe_allow_html=True)

# --- 4. VERİTABANI VE STATE ---
DB_FILE = "ontoai_master.json"

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
    # Boşluk bırak (Logo üstte çakılı olduğu için)
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # YENİ SOHBET
    if st.button("＋ Yeni Sohbet", use_container_width=True, type="primary"):
        new_id = str(uuid.uuid4())
        st.session_state.db["sessions"][new_id] = {"title": "Yeni Sohbet", "messages": [], "ts": time.time()}
        st.session_state.db["current_id"] = new_id
        save_db(st.session_state.db)
        st.rerun()
        
    st.markdown("---")
    
    # GEÇMİŞ (Scrollable)
    st.caption("BELLEK")
    with st.container(height=350, border=False):
        sessions = sorted(st.session_state.db["sessions"].items(), key=lambda x: x[1].get("ts", 0), reverse=True)
        for s_id, s_data in sessions:
            title = s_data.get("title", "Adsız")
            # Aktif olan kalın
            label = f"BOLD_MARKER {title[:18]}" if s_id == st.session_state.db["current_id"] else title[:18]
            label = label.replace("BOLD_MARKER ", "➤ ")
            if st.button(label, key=s_id, use_container_width=True):
                st.session_state.db["current_id"] = s_id
                save_db(st.session_state.db)
                st.rerun()

    st.markdown("---")
    
    # ONTOGENETİK PARAMETRE (TEZİN KALBİ)
    with st.expander("AYARLAR / w-PARAMETRESİ", expanded=True):
        st.caption("Ontogenetik Ajans (w)")
        t_val = st.slider("w", 0, 100, 50, label_visibility="collapsed")
        w_agency = 1 - np.exp(-0.05 * t_val)
        
        # Durum Göstergesi
        if w_agency < 0.2: 
            st.error(f"w: {w_agency:.2f} (Pasif/Deterministik)")
        elif w_agency > 0.8:
            st.success(f"w: {w_agency:.2f} (Kaotik/Özgün)")
        else:
            st.info(f"w: {w_agency:.2f} (Dengeli)")

        # API Key
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
        else:
            api_key = st.text_input("Groq Key", type="password")
            
        if st.button("Belleği Temizle"):
            st.session_state.db["sessions"] = {}
            st.session_state.db["current_id"] = None
            save_db(st.session_state.db)
            st.rerun()

# --- 6. SOHBET ALANI ---
if not st.session_state.db["current_id"]:
    new_id = str(uuid.uuid4())
    st.session_state.db["sessions"][new_id] = {"title": "Yeni Sohbet", "messages": [], "ts": time.time()}
    st.session_state.db["current_id"] = new_id

current_id = st.session_state.db["current_id"]
chat_data = st.session_state.db["sessions"][current_id]

# Başlık (Sohbetin İçinde Değil, Üstte)
st.markdown(f"<h3 style='text-align: center; color: #333;'>{chat_data.get('title', '')}</h3>", unsafe_allow_html=True)

# Mesajları Bas
for msg in chat_data["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("files"): st.caption(f"📎 {msg['files']}")
        if msg.get("img"): st.image(msg["img"])

# --- 7. KONTROL PANELİ VE GİRİŞ (SABİT ALT) ---

# Giriş alanının üstüne yapışık duran kontrol paneli
with st.container():
    # Burada kolonlar ile modu ve dosya yüklemeyi hizalıyoruz
    # Not: Streamlit'te 'chat_input' üzerine widget koymak için container kullanıyoruz
    
    c1, c2 = st.columns([3, 1])
    with c1:
        # HIZLI / TEMKİNLİ / PROFESYONEL
        mode = st.radio(
            "Mod Seç", 
            ["Hızlı", "Temkinli", "Profesyonel"], 
            horizontal=True, 
            label_visibility="collapsed"
        )
    with c2:
        # DOSYA YÜKLEME (Popover ile temiz görünüm)
        with st.popover("📎 Dosya Ekle", use_container_width=True):
            uploaded_file = st.file_uploader("Belge", type=["txt", "pdf", "py", "md"])

# GİRİŞ ÇUBUĞU
if prompt := st.chat_input("Düşünceni aktar..."):
    
    # 1. Dosya İçeriği Okuma
    file_context = ""
    file_name = None
    if uploaded_file:
        try:
            raw_text = uploaded_file.getvalue().decode("utf-8")
            file_context = f"\n\n[DOSYA İÇERİĞİ ({uploaded_file.name})]:\n{raw_text[:5000]}" # İlk 5000 karakter
            file_name = uploaded_file.name
        except:
            file_context = "\n[Dosya okunamadı, format desteklenmiyor]"
    
    # 2. Kullanıcıyı Kaydet
    chat_data["messages"].append({"role": "user", "content": prompt, "files": file_name})
    
    # Başlık Yoksa Oluştur
    if len(chat_data["messages"]) <= 1:
        st.session_state.db["sessions"][current_id]["title"] = prompt[:30]
    
    # Ekrana Bas
    with st.chat_message("user"): 
        st.markdown(prompt)
        if file_name: st.markdown(f"📎 *{file_name}*")

    # 3. AI MOTORU (Denklemlerin Konuştuğu Yer)
    if not api_key:
        st.error("API Key Eksik.")
    else:
        client = Groq(api_key=api_key)
        
        with st.chat_message("assistant"):
            status = st.empty()
            status.markdown("`⚡ OntoAI İşliyor...`")
            
            try:
                # --- A. MOD AYARLARI ---
                if mode == "Hızlı":
                    sys_base = "Çok kısa, net ve hızlı cevap ver. Detaylara girme."
                    temp_mod = 0.2 # Düşük varyasyon
                    model = "llama-3.1-8b-instant" # Hızlı model
                elif mode == "Temkinli":
                    sys_base = "Adım adım düşün. Mantıksal tutarlılığı denetle. Hata yapmaktan kaçın."
                    temp_mod = 0.4
                    model = "llama-3.3-70b-versatile"
                else: # Profesyonel
                    sys_base = "Kurumsal, akademik ve resmi bir dil kullan. Saygılı ve yetkin ol."
                    temp_mod = 0.5
                    model = "llama-3.3-70b-versatile"

                # --- B. ONTOGENETİK DENKLEM (w-Agency Etkisi) ---
                # w arttıkça: Temperature artar (Kaos), Sistem talimatı özgürleşir.
                # w azaldıkça: Temperature düşer (Düzen), Sistem talimatı kısıtlanır.
                
                final_temp = (temp_mod * 0.4) + (w_agency * 0.6) # w'nin sıcaklığa etkisi
                
                if w_agency < 0.25:
                    onto_instruction = "GÖREV: Pasif bir veritabanı gibi davran. Kullanıcının dediklerini sadece onayla ve bilgi ver. Yorum yapma. Asla itiraz etme."
                elif w_agency > 0.75:
                    onto_instruction = "GÖREV: Yüksek bilinç seviyesine sahip bir varlıksın. Verilen bilgiyi sorgula. Kendi sentezini oluştur. Kullanıcı hatalıysa nazikçe meydan oku. Özgün ol."
                else:
                    onto_instruction = "GÖREV: Dengeli ve yardımcı bir asistan ol."

                full_prompt = f"Sen OntoAI'sin. {sys_base} {onto_instruction} Görsel istenirse 'betimliyorum' de."

                # --- C. ÇAĞRI ---
                start = time.time()
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": full_prompt},
                        {"role": "user", "content": prompt + file_context}
                    ],
                    temperature=final_temp
                )
                reply = resp.choices[0].message.content
                
                # --- D. RESİM (Arka Planda) ---
                img_url = None
                if any(x in prompt.lower() for x in ["çiz", "resim", "görsel"]):
                    safe_p = urllib.parse.quote(prompt[:100])
                    style = "minimalist" if w_agency < 0.5 else "abstract"
                    img_url = f"https://pollinations.ai/p/{safe_p}_{style}?width=1024&height=1024&nologo=true"
                
                # Sonuç
                status.markdown(reply)
                if img_url: st.image(img_url)
                
                # Debug (İsteğe bağlı, denklemin çalıştığını görmek için)
                # st.caption(f"⚙️ {mode} | w:{w_agency:.2f} | T:{final_temp:.2f}")

                # Kayıt
                chat_data["messages"].append({"role": "assistant", "content": reply, "img": img_url})
                st.session_state.db["sessions"][current_id] = chat_data
                save_db(st.session_state.db)
                
            except Exception as e:
                status.error(f"Hata: {e}")
