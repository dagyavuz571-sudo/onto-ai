import streamlit as st
import numpy as np
from groq import Groq
import json
import os
import time
import uuid # Benzersiz ID'ler için

# --- 1. AYARLAR VE CSS MİMARİSİ ---
st.set_page_config(page_title="Onto-AI", layout="wide", initial_sidebar_state="expanded")

# ÖZEL CSS: FONT, ANİMASYON, LOGO VE PROFİL
st.markdown("""
    <style>
    /* Google Font: Inter (Modern ve Okunaklı) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Ana Arka Plan */
    .stApp { background-color: #0e0e0e; color: #f0f0f0; }
    
    /* Yan Menü */
    [data-testid="stSidebar"] { background-color: #161616; border-right: 1px solid #2a2a2a; }
    
    /* Üst Bar (Header) Gizleme - Kendi Header'ımızı yapacağız */
    header { visibility: hidden; }
    
    /* PROFİL İKONU (Sağ Üst) */
    .profile-icon {
        position: fixed; top: 20px; right: 30px; z-index: 999;
        width: 40px; height: 40px; border-radius: 50%;
        background: linear-gradient(135deg, #333, #555);
        color: white; text-align: center; line-height: 40px;
        font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        border: 1px solid #444; cursor: pointer;
    }
    
    /* LOGO (Sol Üst) */
    .app-logo {
        font-size: 24px; font-weight: 700; color: #e0e0e0;
        letter-spacing: -1px; margin-bottom: 20px;
    }
    .logo-accent { color: #888; }
    
    /* SOHBET BALONLARI (Minimalist) */
    .stChatMessage { background: transparent; border: none; padding: 10px 0; }
    
    /* Kullanıcı Balonu */
    [data-testid="chatAvatarIcon-user"] { background-color: #333 !important; color: white !important; }
    
    /* AI Balonu ve Logosu */
    [data-testid="chatAvatarIcon-assistant"] { 
        background-color: #000 !important; 
        border: 1px solid #444;
    }
    
    /* YANIT İSMİ (Sol Üst - Minimal) */
    .ai-name { font-size: 11px; color: #666; margin-bottom: 4px; font-weight: 600; text-transform: uppercase; }
    
    /* ANİMASYON (Yükleniyor...) */
    @keyframes pulse {
        0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; }
    }
    .thinking-pulse {
        color: #888; font-size: 14px; font-style: italic;
        animation: pulse 1.5s infinite ease-in-out;
    }
    
    /* GİRİŞ KUTUSU (En Alt) */
    .stChatInput { border-color: #333 !important; }
    
    /* Butonlar */
    .stButton button { width: 100%; border-radius: 8px; border: 1px solid #333; background: #111; color: #ccc; }
    .stButton button:hover { border-color: #666; color: white; background: #222; }
    
    </style>
""", unsafe_allow_html=True)

# --- 2. VERİTABANI YÖNETİMİ (JSON) ---
DB_FILE = "onto_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"sessions": {}, "current_session_id": None}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

# Başlangıç Yüklemesi
if "db" not in st.session_state:
    st.session_state.db = load_db()

# Yeni Sohbet Fonksiyonu
def create_new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.db["sessions"][new_id] = {
        "title": "Yeni Sohbet",
        "messages": [],
        "created_at": time.time()
    }
    st.session_state.db["current_session_id"] = new_id
    save_db(st.session_state.db)
    st.rerun()

# Eğer hiç oturum yoksa başlat
if not st.session_state.db["current_session_id"]:
    create_new_chat()

current_id = st.session_state.db["current_session_id"]
current_chat = st.session_state.db["sessions"].get(current_id, {"messages": []})

# --- 3. ÜST BAR VE PROFİL ---
# Profil İkonunu HTML ile yerleştiriyoruz (CSS ile sağ üstte sabitlendi)
st.markdown('<div class="profile-icon">U</div>', unsafe_allow_html=True)

# Logo Alanı
st.markdown('<div class="app-logo">Onto<span class="logo-accent">AI</span></div>', unsafe_allow_html=True)

# --- 4. YAN MENÜ (FONKSİYONEL) ---
with st.sidebar:
    st.markdown("### MERKEZ")
    
    # Yeni Sohbet Butonu
    if st.button("＋ Yeni Sohbet", help="Temiz bir sayfa aç"):
        create_new_chat()
    
    st.markdown("---")
    
    # Arama Kutusu
    search_query = st.text_input("🔍 Ara...", placeholder="Sohbetlerde ara").lower()
    
    st.markdown("### GEÇMİŞ")
    
    # Sohbet Listesi (Ters Sırada - En yeni en üstte)
    # Sözlükteki oturumları listeye çevirip tarihe göre sırala
    sorted_sessions = sorted(
        st.session_state.db["sessions"].items(),
        key=lambda x: x[1].get("created_at", 0),
        reverse=True
    )
    
    for s_id, s_data in sorted_sessions:
        title = s_data["title"]
        # Arama filtresi
        if search_query and search_query not in title.lower():
            continue
            
        # Aktif sohbeti vurgula
        btn_label = f"Build: {title}" if len(title) < 20 else f"{title[:18]}..."
        if st.button(btn_label, key=s_id, type="primary" if s_id == current_id else "secondary"):
            st.session_state.db["current_session_id"] = s_id
            save_db(st.session_state.db)
            st.rerun()

    st.markdown("---")
    
    # ONTOGENETİK KONTROL
    st.caption("ONTOGENETİK DURUM (w)")
    t_val = st.slider("Gelişim", 0, 100, 50, label_visibility="collapsed")
    w_agency = 1 - np.exp(-0.05 * t_val)
    st.progress(w_agency)
    st.caption(f"w: {w_agency:.2f}")

    # API Key
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
    else:
        api_key = st.text_input("API Key", type="password")

# --- 5. SOHBET ALANI ---

# Mesajları Ekrana Bas
for msg in current_chat["messages"]:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown('<div class="ai-name">Onto-AI</div>', unsafe_allow_html=True)
        
        st.markdown(msg["content"])
        if msg.get("img"):
            st.image(msg["img"], width=400)

# --- 6. GİRİŞ VE MOTOR ---
# En Önemlisi: st.chat_input kullanıyoruz (En alta sabitler)
if prompt := st.chat_input("Düşünceni aktar..."):
    
    # 1. Başlık Güncelleme (İlk mesajsa)
    if len(current_chat["messages"]) == 0:
        new_title = " ".join(prompt.split()[:4]) # İlk 4 kelimeyi başlık yap
        st.session_state.db["sessions"][current_id]["title"] = new_title
    
    # 2. Kullanıcı Mesajını Ekle
    current_chat["messages"].append({"role": "user", "content": prompt})
    st.session_state.db["sessions"][current_id] = current_chat
    save_db(st.session_state.db)
    
    # Hemen ekranda göster
    with st.chat_message("user"):
        st.markdown(prompt)
    
    if not api_key:
        st.error("API Key Eksik")
    else:
        client = Groq(api_key=api_key)
        
        with st.chat_message("assistant"):
            st.markdown('<div class="ai-name">Onto-AI</div>', unsafe_allow_html=True)
            
            # ANİMASYONLU BEKLEME
            placeholder = st.empty()
            placeholder.markdown('<div class="thinking-pulse">⚡ Onto-AI analiz ediyor...</div>', unsafe_allow_html=True)
            
            try:
                # Yapay Zeka Düşünme Süresi (Simülasyon - Hissetmek için)
                time.sleep(1.2) 
                
                # Sistem Talimatı
                role_desc = "Özgün, eleştirel bir zeka" if w_agency > 0.7 else "Yardımcı, net bir asistan"
                sys_msg = (
                    f"Sen Onto-AI'sin. w={w_agency:.2f}. Rolün: {role_desc}. "
                    f"Sadece Türkçe konuş. Kısa ve net cevap ver. "
                    f"Kullanıcı görsel isterse reddetme, betimle."
                )

                # Yanıt Üretimi
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                reply = resp.choices[0].message.content
                
                # Görsel Kontrolü (Otomatik)
                img_url = None
                if any(x in prompt.lower() for x in ["çiz", "resim", "görsel"]):
                    safe_p = urllib.parse.quote(prompt[:100])
                    seed = int(time.time())
                    img_url = f"https://pollinations.ai/p/{safe_p}?width=1024&height=1024&seed={seed}&nologo=true"
                    reply += "\n\n*(Görsel oluşturuldu)*"

                # Yanıtı Bas (Animasyonu siler, yerine metni koyar)
                placeholder.markdown(reply)
                if img_url:
                    st.image(img_url, caption="Onto-AI Render")

                # Veritabanına Kayıt
                current_chat["messages"].append({"role": "assistant", "content": reply, "img": img_url})
                st.session_state.db["sessions"][current_id] = current_chat
                save_db(st.session_state.db)
                
                # Başlığı güncellemek için sidebarı yenilememiz gerekebilir ama 
                # akışı bozmamak için şimdilik bırakıyoruz. Sonraki reload'da düzelir.

            except Exception as e:
                placeholder.error(f"Bağlantı Hatası: {e}")
