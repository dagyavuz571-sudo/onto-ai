import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
from datetime import datetime

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI: Full", layout="wide")
st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #1a1c24; border-right: 1px solid #4ecca3; }
    .stChatMessage { border-radius: 10px; border: 1px solid rgba(78, 204, 163, 0.2); margin-bottom: 10px; }
    h1, h2, h3 { color: #4ecca3 !important; }
    /* Galeri Resimleri için */
    .stImage { border: 1px solid #333; border-radius: 5px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HAFIZA VE GALERİ YÖNETİMİ ---
if "all_sessions" not in st.session_state: st.session_state.all_sessions = {}
if "messages" not in st.session_state: st.session_state.messages = []
if "gallery" not in st.session_state: st.session_state.gallery = [] # ÖGELERİM KISMI

# --- 3. FONKSİYONLAR ---
def get_live_model(api_key):
    """Google'da o an çalışan modeli bulur."""
    genai.configure(api_key=api_key)
    try:
        all_models = genai.list_models()
        valid = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
        if not valid: return None, "Model Yok"
        
        # Öncelik: Flash > Pro
        best = valid[0]
        for m in valid:
            if "flash" in m.lower() and "exp" not in m.lower():
                best = m
                break
        return best, valid
    except Exception as e:
        return None, str(e)

# --- 4. YAN MENÜ ---
with st.sidebar:
    st.title("🧬 Onto-AI")
    
    # API KEY
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Google API Key:", type="password")

    st.divider()

    # --- SOHBET YÖNETİMİ (GERİ GELDİ) ---
    st.subheader("🗂️ Sohbetler")
    if st.button("➕ Yeni Sohbet"):
        if st.session_state.messages:
            # Kaydet ve temizle
            title = f"Kayıt {datetime.now().strftime('%H:%M')}"
            st.session_state.all_sessions[title] = list(st.session_state.messages)
        st.session_state.messages = []
        st.rerun()
    
    # Eski kayıtları listele
    if st.session_state.all_sessions:
        selected_chat = st.selectbox("Geçmiş:", list(st.session_state.all_sessions.keys()))
        if st.button("Yükle"):
            st.session_state.messages = list(st.session_state.all_sessions[selected_chat])
            st.rerun()

    st.divider()

    # --- ÖGELERİM (YENİ!) ---
    st.subheader("🎨 Ögelerim (Galeri)")
    with st.expander("Oluşturulan Görselleri Gör"):
        if not st.session_state.gallery:
            st.caption("Henüz görsel yok.")
        else:
            # En sondan başa doğru göster (Yeni en üstte)
            for item in reversed(st.session_state.gallery):
                st.image(item["url"], caption=item["prompt"], use_container_width=True)
                st.markdown("---")

    st.divider()
    
    # --- AYARLAR ---
    t_val = st.slider("Gelişim (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_val)
    st.metric("Ajans (w)", f"%{w_agency*100:.1f}")

# --- 5. ANA EKRAN ---
st.title("Onto-AI")

# Mesajları Bas
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("img"): st.image(msg["img"], use_container_width=True)

# --- 6. İŞLEM MOTORU ---
if prompt := st.chat_input("Yazın veya 'çiz' deyin..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    if not api_key:
        st.error("Anahtar girilmedi.")
    else:
        # Modeli Bul
        active_model, _ = get_live_model(api_key)
        
        if not active_model:
            st.error("Google'a bağlanılamadı. Key'i kontrol edin.")
        else:
            with st.chat_message("assistant"):
                status = st.empty()
                status.info("İşleniyor...")
                
                try:
                    # Termodinamik Sıcaklık
                    temp = max(0.1, 1.6 * (1 - w_agency))
                    
                    model = genai.GenerativeModel(
                        model_name=active_model,
                        generation_config={"temperature": temp}
                    )
                    
                    # Persona
                    sys_msg = f"Sen Onto-AI'sin. Ajans (w) seviyen: {w_agency:.2f}. Buna göre konuş."
                    
                    response = model.generate_content(f"{sys_msg}\nSoru: {prompt}")
                    reply = response.text
                    status.markdown(reply)
                    
                    # --- GÖRSEL VE GALERİ MANTIĞI ---
                    img_url = None
                    if any(x in prompt.lower() for x in ["çiz", "resim", "görsel"]):
                        safe_p = urllib.parse.quote(prompt[:50])
                        style = "scientific" if w_agency > 0.6 else "surreal"
                        img_url = f"https://pollinations.ai/p/{safe_p}_{style}?width=1024&height=1024&seed={np.random.randint(100)}"
                        st.image(img_url)
                        
                        # GALERİYE KAYDET (ÖGELERİM)
                        st.session_state.gallery.append({
                            "url": img_url,
                            "prompt": prompt,
                            "date": datetime.now()
                        })
                    
                    # Sohbet Hafızasına Ekle
                    st.session_state.messages.append({"role": "assistant", "content": reply, "img": img_url})
                    
                except Exception as e:
                    if "429" in str(e):
                        status.error("🚦 Kota Doldu. Biraz bekleyin.")
                    else:
                        status.error(f"Hata: {e}")
