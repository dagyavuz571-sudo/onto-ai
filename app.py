import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
import time

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI: 2026 Edition", layout="centered")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stApp { margin-top: -40px; }</style>", unsafe_allow_html=True)

st.title("🧬 Onto-AI")
st.caption("2026 Çoklu Model ve Görsel Motoru")

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Beyin Merkezi")
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Bağlantı Güvenli")
    else:
        api_key = st.text_input("API Key:", type="password")
    
    st.divider()
    
    # --- MODEL SEÇİMİ (BURASI YENİ!) ---
    st.subheader("🤖 Modelini Seç")
    model_choice = st.selectbox(
        "Zeka Seviyesi:",
        ["Gemini 1.5 Flash (Stabil/Yüksek Kota)", 
         "Gemini 3 Flash Preview (En Yeni/Düşük Kota)",
         "Gemini 3 Pro Preview (En Zeki/Çok Düşük Kota)"]
    )
    
    # Model isimlerini eşleyelim
    model_map = {
        "Gemini 1.5 Flash (Stabil/Yüksek Kota)": "gemini-1.5-flash",
        "Gemini 3 Flash Preview (En Yeni/Düşük Kota)": "gemini-3-flash-preview",
        "Gemini 3 Pro Preview (En Zeki/Çok Düşük Kota)": "gemini-3-pro-preview"
    }
    selected_model_name = model_map[model_choice]

    st.divider()
    t_value = st.slider("Gelişim Süreci (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik Algısı (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Hafızayı Sil"):
        st.session_state.messages = []
        st.rerun()

# --- 3. HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Merhaba hocam! Gemini 3 desteği eklendi. Dikkat: Yeni modellerin günlük kotası çok hızlı dolabilir."}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "img" in msg: st.image(msg["img"])

# --- 4. GÖRSEL ÜRETİCİ ---
def generate_image_url(prompt, w):
    style = "surreal, artistic" if w < 0.4 else "photorealistic, 8k"
    return f"https://pollinations.ai/p/{urllib.parse.quote(prompt + ', ' + style)}?width=1024&height=1024&seed={np.random.randint(1000)}"

# --- 5. ANA MOTOR ---
if user_input := st.chat_input("Yazın veya 'Çiz' deyin..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)
    
    if not api_key:
        st.error("API Key eksik!")
    else:
        genai.configure(api_key=api_key)
        
        with st.chat_message("assistant"):
            status = st.empty()
            status.info(f"🧠 {selected_model_name} üzerinden analiz yapılıyor...")
            
            try:
                # Modeli başlat
                model = genai.GenerativeModel(selected_model_name)
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
                err_msg = str(e)
                if "429" in err_msg:
                    status.error("🚦 KOTA SINIRI! Gemini 3 Preview kotanız doldu. Lütfen 1 dakika bekleyin veya sol menüden '1.5 Flash' modeline geçin.")
                elif "404" in err_msg:
                    status.error(f"❌ MODEL BULUNAMADI: {selected_model_name} şu an bu sunucuda aktif değil. Lütfen başka bir model seçin.")
                else:
                    status.error(f"Hata: {e}")
