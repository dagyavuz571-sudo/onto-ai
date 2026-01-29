import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
import time

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI Final", layout="centered")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stApp { margin-top: -40px; }</style>", unsafe_allow_html=True)

st.title("🧬 Onto-AI: Kesin Çözüm")
st.caption("Dinamik Model Seçici ve Kota Koruyucu")

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Anahtar Aktif")
    else:
        api_key = st.text_input("Google API Key:", type="password")
    
    st.divider()
    t_value = st.slider("Gelişim (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik Algısı (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Sohbeti Sıfırla"):
        st.session_state.messages = []
        st.rerun()

# --- 3. MEVCUT MODELİ BULAN AKILLI SİSTEM ---
def get_working_model_auto(key):
    genai.configure(api_key=key)
    try:
        # Sunucunun desteklediği TÜM modelleri çek
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Öncelik Sırası: En iyiden en stabil olana
        targets = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro', 'gemini-pro']
        
        for t in targets:
            for m in available_models:
                if t in m:
                    return genai.GenerativeModel(m), m
        
        # Hiçbiri tutmazsa listedeki ilk modeli ver
        return genai.GenerativeModel(available_models[0]), available_models[0]
    except Exception as e:
        return None, str(e)

# --- 4. GÖRSEL ÜRETİCİ ---
def generate_image_url(prompt, w):
    style = "surreal, abstract" if w < 0.4 else "photorealistic, cinematic"
    return f"https://pollinations.ai/p/{urllib.parse.quote(prompt + ', ' + style)}?width=1024&height=1024&seed={np.random.randint(1000)}"

# --- 5. SOHBET AKIŞI ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hocam her şey hazır. Model ismini sistem otomatik seçiyor. Ne çizelim?"}]

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
        # Modeli otomatik tespit et
        model, model_name = get_working_model_auto(api_key)
        
        if not model:
            st.error(f"Model listesi alınamadı. Hata: {model_name}")
        else:
            with st.chat_message("assistant"):
                status_placeholder = st.empty()
                status_placeholder.info(f"🧠 Aktif Model: {model_name} üzerinden analiz yapılıyor...")
                
                success = False
                retries = 0
                while not success and retries < 2:
                    try:
                        sys_inst = f"Sen Onto-AI'sin. w: {w_agency}. Soru: {user_input}"
                        response = model.generate_content(sys_inst)
                        reply = response.text
                        
                        status_placeholder.markdown(reply)
                        
                        # Görsel Çizme
                        is_draw = any(x in user_input.lower() for x in ["çiz", "resim", "görsel", "draw", "image"])
                        img_url = generate_image_url(user_input, w_agency) if is_draw else None
                        if img_url: st.image(img_url)
                        
                        # Kayıt
                        new_msg = {"role": "assistant", "content": reply}
                        if img_url: new_msg["img"] = img_url
                        st.session_state.messages.append(new_msg)
                        success = True
                        
                    except Exception as e:
                        if "429" in str(e):
                            retries += 1
                            status_placeholder.warning(f"🚦 Kota yoğunluğu. {retries}. deneme yapılıyor (5 sn)...")
                            time.sleep(5)
                        else:
                            st.error(f"Hata: {e}")
                            break
