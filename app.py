import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
import time

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI: Final v3", layout="centered")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stApp { margin-top: -40px; }</style>", unsafe_allow_html=True)

st.title("🧬 Onto-AI")
st.caption("Kesintisiz Analiz ve Görsel Motoru")

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Beyin Ayarları")
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Yeni Proje Hattı Aktif")
    else:
        api_key = st.text_input("Google API Key:", type="password")
    
    st.divider()
    t_value = st.slider("Gelişim Süreci (t)", 0, 100, 50)
    # Termodinamik Ajans Formülü
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik Algısı (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Sohbeti Temizle"):
        st.session_state.messages = []
        st.rerun()

# --- 3. GÖRSEL MOTORU (Pollinations) ---
def generate_image_url(prompt, w):
    style = "surreal, abstract" if w < 0.4 else "photorealistic, cinematic, 8k"
    full_prompt = f"{prompt}, {style}"
    return f"https://pollinations.ai/p/{urllib.parse.quote(full_prompt)}?width=1024&height=1024&seed={np.random.randint(1000)}"

# --- 4. SOHBET HAFIZASI ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hocam yeni proje anahtarı ile sistem sıfırlandı. Artık hata almamalıyız. Ne çizelim?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "img" in msg: st.image(msg["img"])

# --- 5. CEVAP ÜRETME (KRİTİK KISIM) ---
if user_input := st.chat_input("Yazın veya 'Resmini çiz' deyin..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)
    
    if not api_key:
        st.error("Lütfen yeni bir API Key tanımlayın!")
    else:
        genai.configure(api_key=api_key)
        
        # 404 ve 429 hatalarını aşmak için denenecek model varyasyonları
        # Bazı sunucular tam yol (models/...) ister, bazıları kısa isim.
        model_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro', 'models/gemini-pro']
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.info("🧐 Analiz yapılıyor...")
            
            response_text = ""
            success = False
            
            for m_name in model_names:
                if success: break
                try:
                    model = genai.GenerativeModel(m_name)
                    sys_inst = f"Sen Onto-AI'sin. w: {w_agency}. Teorik bir yapay zekasın. Soru: {user_input}"
                    
                    response = model.generate_content(sys_inst)
                    response_text = response.text
                    success = True
                    placeholder.markdown(response_text)
                    
                    # Görsel Üretimi
                    is_draw = any(x in user_input.lower() for x in ["çiz", "resim", "görsel", "draw", "image"])
                    img_url = generate_image_url(user_input, w_agency) if is_draw else None
                    if img_url: st.image(img_url, caption=f"Onto-AI Vision (w=%{w_agency*100:.1f})")
                    
                    # Hafızaya Kayıt
                    new_msg = {"role": "assistant", "content": response_text}
                    if img_url: new_msg["img"] = img_url
                    st.session_state.messages.append(new_msg)
                    
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg:
                        placeholder.error("🚦 Kota Sınırı! Bu anahtar yorulmuş. Lütfen 30 saniye bekleyin veya yeni PROJE anahtarı girin.")
                        break # 429 varsa diğer modelleri denemek genelde işe yaramaz
                    elif "404" in error_msg:
                        continue # 404 ise bir sonraki model ismini dene
                    else:
                        placeholder.error(f"Beklenmedik Hata: {e}")
                        break
