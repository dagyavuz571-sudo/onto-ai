import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
import time

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI: Final", layout="centered")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stApp { margin-top: -40px; }</style>", unsafe_allow_html=True)

st.title("🧬 Onto-AI: Zırhlı Mod")
st.caption("Kesintisiz Analiz ve Görselleştirme")

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    # Secrets kontrolü
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Yeni Hat Aktif")
    else:
        api_key = st.text_input("Google API Key:", type="password")
    
    st.divider()
    t_value = st.slider("Gelişim (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik Algısı (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Sohbeti Sıfırla"):
        st.session_state.messages = []
        st.rerun()

# --- 3. MODEL BULUCU (Sadece Bir Kez Çalışır) ---
@st.cache_resource
def get_best_model(key):
    try:
        genai.configure(api_key=key)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Yüksek kotalı (1.5 Flash) modeline odaklan
        for target in ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']:
            for m in models:
                if target in m:
                    return m
        return models[0]
    except:
        return "gemini-1.5-flash" # Varsayılan fallback

# --- 4. GÖRSEL ÜRETİCİ ---
def generate_image_url(prompt, w):
    style = "surreal, abstract" if w < 0.4 else "photorealistic, 8k"
    return f"https://pollinations.ai/p/{urllib.parse.quote(prompt + ', ' + style)}?width=1024&height=1024&seed={np.random.randint(1000)}"

# --- 5. SOHBET AKIŞI ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hocam sistemi 'Kota Koruma' moduna aldım. Hazırım."}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "img" in msg: st.image(msg["img"])

if user_input := st.chat_input("Yazın veya 'Çiz' deyin..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)
    
    if not api_key:
        st.error("API Key eksik!")
    else:
        model_name = get_best_model(api_key)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        with st.chat_message("assistant"):
            msg_placeholder = st.empty()
            
            try:
                sys_inst = f"Sen Onto-AI'sin. w: {w_agency}. Soru: {user_input}"
                response = model.generate_content(sys_inst)
                reply = response.text
                msg_placeholder.markdown(reply)
                
                # Görsel Çizme
                is_draw = any(x in user_input.lower() for x in ["çiz", "resim", "görsel", "draw", "image"])
                img_url = generate_image_url(user_input, w_agency) if is_draw else None
                if img_url: st.image(img_url)
                
                # Kayıt
                new_msg = {"role": "assistant", "content": reply}
                if img_url: new_msg["img"] = img_url
                st.session_state.messages.append(new_msg)

            except Exception as e:
                if "429" in str(e):
                    msg_placeholder.error("🚦 **KOTA TAMAMEN DOLU!** Bu API anahtarı Google tarafından bugünlük durduruldu. Lütfen [AI Studio](https://aistudio.google.dev/) üzerinden **YENİ BİR PROJE** oluşturup yeni bir anahtar alın.")
                else:
                    msg_placeholder.error(f"Hata: {e}")
