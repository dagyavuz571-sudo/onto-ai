import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI: 2026 Edition", layout="centered")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stApp { margin-top: -40px; }</style>", unsafe_allow_html=True)

st.title("🧬 Onto-AI")
st.caption("2026 Dinamik Model Yönetimi")

# --- 2. YAN MENÜ VE MODEL KEŞFİ ---
with st.sidebar:
    st.header("⚙️ Sistem Paneli")
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("API Key:", type="password")
    
    st.divider()

    # --- MODEL DEDEKTÖRÜ ---
    st.subheader("🔍 Mevcut Modeller")
    model_list = []
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Google'ın o an sunduğu her şeyi çekiyoruz
            raw_models = genai.list_models()
            model_list = [m.name.replace("models/", "") for m in raw_models if 'generateContent' in m.supported_generation_methods]
            
            # Kullanıcının seçmesi için kutu (En yeniyi en başa koyalım)
            selected_model = st.selectbox("Çalışan Bir Beyin Seç:", sorted(model_list, reverse=True))
            st.info(f"Aktif: {selected_model}")
        except Exception as e:
            st.error("Modeller listelenemedi. Anahtarı kontrol edin.")
            selected_model = "gemini-3-flash-preview" # Fallback

    st.divider()
    t_value = st.slider("Gelişim (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik Algısı (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Sohbeti Temizle"):
        st.session_state.messages = []
        st.rerun()

# --- 3. HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Merhaba hocam. Google'ın 2026 kataloğuna bağlandım. Listeden istediğin modeli seçebilirsin."}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "img" in msg: st.image(msg["img"])

# --- 4. GÖRSEL ÜRETİCİ ---
def generate_image_url(prompt, w):
    style = "surreal" if w < 0.4 else "8k, cinematic"
    return f"https://pollinations.ai/p/{urllib.parse.quote(prompt + ', ' + style)}?width=1024&height=1024&seed={np.random.randint(1000)}"

# --- 5. ANA MOTOR ---
if user_input := st.chat_input("Mesajınızı yazın..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)
    
    if not api_key:
        st.error("API Key eksik!")
    else:
        with st.chat_message("assistant"):
            try:
                model = genai.GenerativeModel(selected_model)
                sys_inst = f"Sen Onto-AI'sin. w: {w_agency}. Soru: {user_input}"
                
                response = model.generate_content(sys_inst)
                reply = response.text
                st.markdown(reply)
                
                # Görsel Çizme
                is_draw = any(x in user_input.lower() for x in ["çiz", "resim", "görsel", "draw", "image"])
                img_url = generate_image_url(user_input, w_agency) if is_draw else None
                if img_url: st.image(img_url)
                
                st.session_state.messages.append({"role": "assistant", "content": reply, "img": img_url if img_url else None})
            
            except Exception as e:
                if "429" in str(e):
                    st.error("🚦 Kota Sınırı! Seçtiğiniz modelin günlük hakkı bitti. Lütfen listeden başka bir model seçin.")
                else:
                    st.error(f"Hata: {e}")
