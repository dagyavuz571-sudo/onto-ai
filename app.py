import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
import time

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI: Final v4", layout="centered")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stApp { margin-top: -40px; }</style>", unsafe_allow_html=True)

st.title("🧬 Onto-AI")
st.caption("Dinamik Model Dedektörü ve Görsel Motoru")

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Beyin Ayarları")
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Anahtar Aktif")
    else:
        api_key = st.text_input("Google API Key:", type="password")
    
    st.divider()
    t_value = st.slider("Gelişim Süreci (t)", 0, 100, 50)
    # Teorik Ajans Formülü
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik Algısı (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Sohbeti Sıfırla"):
        st.session_state.messages = []
        st.rerun()

# --- 3. DİNAMİK MODEL BULUCU (404 SAVAR) ---
def get_best_model_auto(key):
    genai.configure(api_key=key)
    try:
        # Sunucudaki modelleri tara ve sadece mesaj üretebilenleri listele
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Öncelik sırasına göre kontrol et
        priority = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro', 'gemini-pro']
        for target in priority:
            for m in models:
                if target in m:
                    return genai.GenerativeModel(m), m
        
        # Hiçbiri yoksa çalışan ilk Gemini'yi al
        return genai.GenerativeModel(models[0]), models[0]
    except Exception as e:
        return None, str(e)

# --- 4. SOHBET HAFIZASI ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hocam her şey hazır. Model ismini sistem otomatik buluyor. Ne konuşalım?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "img" in msg: st.image(msg["img"])

# --- 5. ANALİZ VE GÖRSELLEŞTİRME ---
if user_input := st.chat_input("Mesajınızı yazın..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)
    
    if not api_key:
        st.error("API Key eksik!")
    else:
        # MODELİ BURADA BULUYORUZ
        model, model_name = get_best_model_auto(api_key)
        
        if not model:
            st.error(f"⚠️ Kritik Hata: Google modellerine ulaşılamıyor. Hata: {model_name}")
        else:
            with st.chat_message("assistant"):
                placeholder = st.empty()
                placeholder.info(f"🧐 {model_name} üzerinden analiz yapılıyor...")
                
                try:
                    sys_inst = f"Sen Onto-AI'sin. w: {w_agency}. Soru: {user_input}"
                    response = model.generate_content(sys_inst)
                    reply = response.text
                    placeholder.markdown(reply)
                    
                    # Görsel üretme (Opsiyonel)
                    is_draw = any(x in user_input.lower() for x in ["çiz", "resim", "görsel", "draw", "image"])
                    if is_draw:
                        style = "surreal" if w_agency < 0.4 else "photorealistic"
                        img_url = f"https://pollinations.ai/p/{urllib.parse.quote(user_input + ', ' + style)}?width=1024&height=1024&seed={np.random.randint(1000)}"
                        st.image(img_url, caption="Onto-AI Vision")
                        st.session_state.messages.append({"role": "assistant", "content": reply, "img": img_url})
                    else:
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                        
                except Exception as e:
                    if "429" in str(e):
                        placeholder.error("🚦 Kota Sınırı! Lütfen 30 saniye bekleyin veya yeni bir PROJE anahtarı alın.")
                    else:
                        placeholder.error(f"Hata: {e}")
