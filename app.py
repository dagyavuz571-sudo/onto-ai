import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
from datetime import datetime
import time

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI: Final", layout="wide")
st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #1a1c24; border-right: 1px solid #4ecca3; }
    .stChatMessage { border-radius: 10px; border: 1px solid rgba(78, 204, 163, 0.2); margin-bottom: 10px; }
    h1, h2, h3 { color: #4ecca3 !important; }
    .stImage { border: 1px solid #333; border-radius: 5px; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HAFIZA VE GALERİ ---
if "all_sessions" not in st.session_state: st.session_state.all_sessions = {}
if "messages" not in st.session_state: st.session_state.messages = []
if "gallery" not in st.session_state: st.session_state.gallery = []

# --- 3. MODEL BULUCU ---
def get_live_model(api_key):
    genai.configure(api_key=api_key)
    try:
        all_models = genai.list_models()
        valid = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
        if not valid: return None, "Model Yok"
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
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Google API Key:", type="password")

    st.divider()
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
    st.subheader("🎨 Ögelerim")
    with st.expander("Galeriye Bak"):
        if not st.session_state.gallery:
            st.caption("Boş.")
        else:
            for item in reversed(st.session_state.gallery):
                st.image(item["url"], caption=item["prompt"], use_container_width=True)

    st.divider()
    t_val = st.slider("Gelişim (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_val)
    st.metric("Ajans (w)", f"%{w_agency*100:.1f}")

# --- 5. ANA EKRAN (GEÇMİŞİ GÖSTER) ---
st.title("Onto-AI")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Eğer mesajda resim varsa ve URL geçerliyse göster
        if msg.get("img") and str(msg["img"]).startswith("http"):
            st.image(msg["img"], use_container_width=True)

# --- 6. MOTOR (GÜNCELLENDİ) ---
if prompt := st.chat_input("Yazın veya 'çiz' deyin..."):
    # 1. Kullanıcı mesajını hemen ekle ve göster
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    if not api_key:
        st.error("Anahtar girilmedi.")
    else:
        active_model, _ = get_live_model(api_key)
        if not active_model:
            st.error("Model bulunamadı.")
        else:
            with st.chat_message("assistant"):
                # Spinner sadece metin üretilirken dönecek
                with st.spinner("Termodinamik analiz..."):
                    try:
                        temp = max(0.1, 1.6 * (1 - w_agency))
                        model = genai.GenerativeModel(model_name=active_model, generation_config={"temperature": temp})
                        
                        # Botu "Çizebilirim" yalanına zorluyoruz
                        sys_msg = (f"Sen Onto-AI'sin. w={w_agency:.2f}. "
                                   f"Görsel modülün VAR. 'Çiz' denirse ASLA 'yapamam' deme. 'Oluşturuyorum' de.")
                        
                        response = model.generate_content(f"{sys_msg}\nSoru: {prompt}")
                        reply = response.text
                        
                    except Exception as e:
                        reply = f"Metin hatası: {e}"
                        if "429" in str(e): reply = "🚦 Kota doldu. Biraz bekleyin."

                # 2. Metni bas
                st.markdown(reply)
                
                # 3. Görsel Kontrolü ve Basımı (AYRI BLOK)
                img_url = None
                if any(x in prompt.lower() for x in ["çiz", "resim", "görsel", "draw", "paint"]):
                    try:
                        # Görsel yüklenirken kullanıcıya bilgi ver
                        with st.spinner("🎨 Görsel oluşturuluyor..."):
                            safe_p = urllib.parse.quote(prompt[:60])
                            style = "scientific, hyper-realistic" if w_agency > 0.6 else "surreal, abstract oil painting"
                            # Benzersizlik için seed'e zaman ekle
                            seed = int(time.time()) 
                            img_url = f"https://pollinations.ai/p/{safe_p}_{style}?width=1024&height=1024&seed={seed}"
                            
                            # Resmi bas (Hata olursa except yakalar)
                            st.image(img_url, caption=f"w={w_agency:.2f} görselleştirmesi")
                            
                            # Galeriye ekle
                            st.session_state.gallery.append({"url": img_url, "prompt": prompt})
                            
                    except Exception as e:
                        st.warning(f"Görsel oluşturulamadı: Sunucu yoğun olabilir. ({e})")
                        img_url = None # Hata varsa URL kaydetme
                
                # 4. Her şeyi hafızaya kaydet
                st.session_state.messages.append({"role": "assistant", "content": reply, "img": img_url})
