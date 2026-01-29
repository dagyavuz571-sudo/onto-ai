import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
import time

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI Final", layout="centered")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stApp { margin-top: -40px; }</style>", unsafe_allow_html=True)

st.title("🧬 Onto-AI: Zırhlı Sürüm")
st.caption("Yüksek Kotalı ve Kararlı Yapay Zeka")

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Yeni Proje Aktif")
    else:
        api_key = st.text_input("Google API Key:", type="password")
    
    st.divider()
    t_value = st.slider("Gelişim Süreci (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik Algısı (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Sohbeti Sıfırla"):
        st.session_state.messages = []
        st.rerun()

# --- 3. MODEL SEÇİCİ (EN YÜKSEK KOTALI MODEL) ---
def get_safe_model(key):
    genai.configure(api_key=key)
    # Gemini 1.5 Flash: Günde 1500 soru hakkı verir. 
    # Gemini 2.x veya Pro modellerine çarpmamak için ismi sabitledik.
    try:
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return genai.GenerativeModel('gemini-pro')

# --- 4. GÖRSEL MOTORU ---
def generate_image_url(prompt, w):
    style = "surreal" if w < 0.4 else "photorealistic"
    return f"https://pollinations.ai/p/{urllib.parse.quote(prompt + ', ' + style)}?width=1024&height=1024&seed={np.random.randint(1000)}"

# --- 5. SOHBET HAFIZASI ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hocam yeni hat üzerinden bağlandım. 1500 soruluk kotamız var. Hazırım!"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "img" in msg: st.image(msg["img"])

# --- 6. CEVAP ÜRETME ---
if user_input := st.chat_input("Mesaj yazın veya 'Çiz' deyin..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)
    
    if not api_key:
        st.error("Lütfen yeni bir API Key tanımlayın!")
    else:
        model = get_safe_model(api_key)
        with st.chat_message("assistant"):
            status = st.empty()
            status.info("🧐 Analiz ediliyor...")
            
            try:
                sys_inst = f"Sen Onto-AI'sin. w: {w_agency}. Soru: {user_input}"
                response = model.generate_content(sys_inst)
                reply = response.text
                status.markdown(reply)
                
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
                    status.error("🚦 KOTA DOLDU! Bu proje bugünlük limitine ulaşmış. Lütfen AI Studio'da YENİ BİR PROJE açıp yeni key alın.")
                else:
                    status.error(f"Hata: {e}")
