import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
import time # Zamanlama için ekledik

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI Final", layout="centered")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stApp { margin-top: -40px; }</style>", unsafe_allow_html=True)

st.title("🧬 Onto-AI")
st.caption("Otomatik Hata Düzeltme ve Görsel Motoru")

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
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

# --- 3. HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hocam sistemi 'Otomatik Yeniden Deneme' moduna aldım. Eğer Google tıkarsa 5 saniye bekleyip tekrar deneyeceğim."}]

# --- 4. GÖRSEL ÜRETİCİ ---
def generate_image_url(prompt, w):
    style = "surreal, abstract" if w < 0.4 else "photorealistic, 8k"
    return f"https://pollinations.ai/p/{urllib.parse.quote(prompt + ', ' + style)}?width=1024&height=1024&seed={np.random.randint(1000)}"

# --- 5. SOHBET AKIŞI ---
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
        genai.configure(api_key=api_key)
        # KOTASI EN YÜKSEK MODEL: gemini-1.5-flash
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("🧐 Düşünüyorum...")
            
            # --- OTOMATİK RETRY (YENİDEN DENEME) DÖNGÜSÜ ---
            success = False
            retries = 0
            while not success and retries < 3: # En fazla 3 kere dene
                try:
                    sys_inst = f"Sen Onto-AI'sin. w: {w_agency}. Soru: {user_input}"
                    response = model.generate_content(sys_inst)
                    reply = response.text
                    placeholder.markdown(reply)
                    
                    # Görsel Üretimi
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
                        placeholder.warning(f"🚦 Kota dolu. {retries}. deneme yapılıyor (5 sn içinde)...")
                        time.sleep(5) # 5 saniye bekle ve tekrar dene
                    else:
                        placeholder.error(f"Hata: {e}")
                        break
            
            if not success and retries >= 3:
                placeholder.error("❌ Google şu an çok yoğun veya kotanız tamamen bitti. Lütfen yeni bir API Key ile (yeni proje) deneyin.")
