import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
import time

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI: Auto-Pilot", layout="centered")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stApp { margin-top: -40px; }</style>", unsafe_allow_html=True)

st.title("🧬 Onto-AI")
st.caption("Dinamik Model Tespit Sistemi")

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Beyin Ayarları")
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Anahtar Tanımlı")
    else:
        api_key = st.text_input("Google API Key:", type="password")
    
    st.divider()
    t_value = st.slider("Gelişim Süreci (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik Algısı (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Sohbeti Sıfırla"):
        st.session_state.messages = []
        st.rerun()

# --- 3. AKILLI MODEL BULUCU ---
def find_working_model(key):
    genai.configure(api_key=key)
    try:
        # Google'daki tüm modelleri tara
        all_models = genai.list_models()
        # Sadece metin üretebilenleri ayır
        available = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
        
        # Öncelik sırasıyla ara: Flash > Pro
        for target in ['flash', 'pro']:
            for m in available:
                if target in m.lower():
                    return genai.GenerativeModel(m), m
        return genai.GenerativeModel(available[0]), available[0]
    except Exception as e:
        return None, str(e)

# --- 4. GÖRSEL ÜRETİCİ ---
def generate_image_url(prompt, w):
    style = "surreal" if w < 0.4 else "photorealistic"
    return f"https://pollinations.ai/p/{urllib.parse.quote(prompt + ', ' + style)}?width=1024&height=1024&seed={np.random.randint(1000)}"

# --- 5. SOHBET HAFIZASI ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hocam her şey hazır. Model ismini sistem otomatik tespit edecek. İlk sorunuzu sorun."}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "img" in msg: st.image(msg["img"])

# --- 6. CEVAP ÜRETME ---
if user_input := st.chat_input("Mesajınızı yazın..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)
    
    if not api_key:
        st.error("Lütfen API Key tanımlayın!")
    else:
        with st.chat_message("assistant"):
            status_box = st.empty()
            status_box.info("🔍 Uygun model aranıyor...")
            
            model, model_name = find_working_model(api_key)
            
            if not model:
                status_box.error(f"⚠️ Kritik Hata: Modeller listelenemedi. Hata: {model_name}")
            else:
                status_box.info(f"🧠 {model_name} üzerinden analiz ediliyor...")
                try:
                    sys_inst = f"Sen Onto-AI'sin. w: {w_agency}. Soru: {user_input}"
                    response = model.generate_content(sys_inst)
                    reply = response.text
                    status_box.markdown(reply)
                    
                    # Görsel üretme
                    is_draw = any(x in user_input.lower() for x in ["çiz", "resim", "görsel", "draw", "image"])
                    img_url = generate_image_url(user_input, w_agency) if is_draw else None
                    if img_url: st.image(img_url)
                    
                    # Hafızaya Kayıt
                    new_msg = {"role": "assistant", "content": reply}
                    if img_url: new_msg["img"] = img_url
                    st.session_state.messages.append(new_msg)

                except Exception as e:
                    if "429" in str(e):
                        status_box.error("🚦 Kota Sınırı! Lütfen yeni bir PROJE anahtarı tanımlayın.")
                    else:
                        status_box.error(f"Hata oluştu: {e}")
