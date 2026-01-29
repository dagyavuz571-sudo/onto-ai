import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse

# --- 1. AYARLAR VE TASARIM ---
st.set_page_config(page_title="Onto-AI Pro", layout="centered")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stApp { margin-top: -40px; }</style>", unsafe_allow_html=True)

st.title("🧬 Onto-AI")
st.caption("Yüksek Kotalı Termodinamik Motor")

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    # Secrets'tan anahtarı çek
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Sistem Hazır")
    else:
        api_key = st.text_input("Google API Key:", type="password")
    
    st.divider()
    t_value = st.slider("Gelişim (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Sohbeti Sıfırla"):
        st.session_state.messages = []
        st.rerun()

# --- 3. HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Merhaba hocam! Kotayı korumak için en stabil modeli (1.5-Flash) kullanıyorum. Bir şey mi çizelim yoksa teorini mi konuşalım?"}]

# --- 4. KOTA KORUMALI MODEL SEÇİCİ ---
def get_stable_model(key):
    genai.configure(api_key=key)
    try:
        # Sunucudaki modelleri tara
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # HİYERARŞİ: 1.5-Flash (1500 Kota) > 1.0-Pro > En son ne varsa
        # Kotası düşük olan 2.x modellerini listeye bile almadık!
        for target in ['gemini-1.5-flash', 'gemini-1.0-pro', 'gemini-pro']:
            for m in available:
                if target in m:
                    return genai.GenerativeModel(m), m
        return genai.GenerativeModel(available[0]), available[0]
    except:
        return None, None

# --- 5. GÖRSEL ÜRETİCİ ---
def generate_image_url(prompt, w):
    style = "surreal, artistic" if w < 0.4 else "photorealistic, 8k"
    return f"https://pollinations.ai/p/{urllib.parse.quote(prompt + ', ' + style)}?width=1024&height=1024&seed={np.random.randint(1000)}"

# --- 6. SOHBET AKIŞI ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "img" in msg: st.image(msg["img"])

if user_input := st.chat_input("Mesaj yazın veya 'Çiz' deyin..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)
    
    if not api_key:
        st.error("API Key eksik!")
    else:
        model, m_name = get_stable_model(api_key)
        if not model:
            st.error("Model bağlantısı kurulamadı.")
        else:
            with st.chat_message("assistant"):
                try:
                    # Metin Üretimi
                    sys_inst = f"Sen Onto-AI'sin. w: {w_agency}. Soru: {user_input}"
                    response = model.generate_content(sys_inst)
                    reply = response.text
                    st.markdown(reply)
                    
                    # Görsel Üretimi (Eğer 'çiz' kelimesi varsa)
                    is_draw = any(x in user_input.lower() for x in ["çiz", "resim", "görsel", "draw", "image"])
                    img_url = generate_image_url(user_input, w_agency) if is_draw else None
                    if img_url: st.image(img_url)
                    
                    # Kayıt
                    new_msg = {"role": "assistant", "content": reply}
                    if img_url: new_msg["img"] = img_url
                    st.session_state.messages.append(new_msg)
                    
                except Exception as e:
                    if "429" in str(e):
                        st.error("🚦 Kota Sınırı! Çok hızlı sordun, 30 saniye bekle hocam.")
                    else:
                        st.error(f"Hata: {e}")
