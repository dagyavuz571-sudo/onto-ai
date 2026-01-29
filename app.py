import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI Vision", layout="centered")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stApp { margin-top: -40px; }</style>", unsafe_allow_html=True)

st.title("🧬 Onto-AI: Final")
st.caption("Kesintisiz Mod + Görsel Üretim")

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Beyin Ayarları")
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Sistem Online")
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
    st.session_state.messages = [{"role": "assistant", "content": "Yeni anahtar ve yüksek kota ile hazırım hocam. Ne çizelim?"}]

# --- 4. GÖRSEL ÜRETİCİ ---
def generate_image_url(prompt, w):
    # Ajans seviyesine göre stil belirle
    style = "abstract, dreamlike" if w < 0.4 else "hyper-realistic, scientific, 8k"
    full_prompt = f"{prompt}, {style}"
    return f"https://pollinations.ai/p/{urllib.parse.quote(full_prompt)}?width=1024&height=1024&seed={np.random.randint(1000)}"

# --- 5. SOHBET AKIŞI ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "img" in msg: st.image(msg["img"])

if user_input := st.chat_input("Mesaj yazın veya 'Resmini çiz' deyin..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)
    
    if not api_key:
        st.error("API Key eksik!")
    else:
        try:
            # DİREKT EN YÜKSEK KOTALI MODELİ ZORLUYORUZ
            genai.configure(api_key=api_key)
            # Not: Eğer 404 alırsanız burayı 'gemini-pro' yapın ama 1.5-flash en iyisidir.
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            with st.chat_message("assistant"):
                with st.spinner("Analiz ediliyor..."):
                    # 429 (Kota) hatasını yakalamak için alt try-except
                    try:
                        # Metin Yanıtı
                        sys_inst = f"Sen Onto-AI'sin. w: {w_agency}. Soru: {user_input}"
                        response = model.generate_content(sys_inst)
                        reply = response.text
                        st.markdown(reply)
                        
                        # Görsel Kontrolü
                        is_draw = any(x in user_input.lower() for x in ["çiz", "resim", "görsel", "draw", "image"])
                        img_url = generate_image_url(user_input, w_agency) if is_draw else None
                        if img_url: st.image(img_url, caption=f"Ajans: %{w_agency*100:.1f}")
                        
                        # Kaydet
                        new_msg = {"role": "assistant", "content": reply}
                        if img_url: new_msg["img"] = img_url
                        st.session_state.messages.append(new_msg)

                    except Exception as e:
                        if "429" in str(e):
                            st.error("🚦 Kota Hatası: Bu anahtarın günlük limiti dolmuş. Lütfen yeni bir API Key (yeni proje ile) tanımlayın.")
                        else:
                            st.error(f"Google API Hatası: {e}")
                            
        except Exception as e:
            st.error(f"Bağlantı Hatası: {e}")
