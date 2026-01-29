import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
import time

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI: Debug Mode", layout="centered")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stApp { margin-top: -40px; }</style>", unsafe_allow_html=True)

st.title("🧬 Onto-AI")
st.caption("Gelişmiş Hata Ayıklama ve Analiz Motoru")

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

# --- 3. HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hocam hazırım. Eğer takılırsam tam burada hatayı söyleyeceğim."}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "img" in msg: st.image(msg["img"])

# --- 4. GÖRSEL ÜRETİCİ ---
def generate_image_url(prompt, w):
    style = "abstract" if w < 0.4 else "photorealistic"
    return f"https://pollinations.ai/p/{urllib.parse.quote(prompt + ', ' + style)}?width=1024&height=1024&seed={np.random.randint(1000)}"

# --- 5. ANALİZ MOTORU ---
if user_input := st.chat_input("Mesajınızı yazın..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)
    
    if not api_key:
        st.error("API Key eksik!")
    else:
        with st.chat_message("assistant"):
            log_placeholder = st.empty() # Adım adım ne yaptığını yazacak
            
            try:
                log_placeholder.info("🔗 Google Sunucusuna bağlanılıyor...")
                genai.configure(api_key=api_key)
                
                # Modeli seçerken en stabil olanı zorla
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                log_placeholder.info("🧠 Teori işleniyor, cevap üretiliyor...")
                
                sys_inst = f"Sen Onto-AI'sin. w: {w_agency}. Soru: {user_input}"
                
                # Cevap isteği (Eğer burada takılırsa hata verecek)
                response = model.generate_content(sys_inst)
                
                if response:
                    reply = response.text
                    log_placeholder.markdown(reply)
                    
                    # Görsel üretme kontrolü
                    is_draw = any(x in user_input.lower() for x in ["çiz", "resim", "görsel", "draw", "image"])
                    img_url = generate_image_url(user_input, w_agency) if is_draw else None
                    if img_url: st.image(img_url)
                    
                    # Kaydet
                    new_msg = {"role": "assistant", "content": reply}
                    if img_url: new_msg["img"] = img_url
                    st.session_state.messages.append(new_msg)
                else:
                    log_placeholder.error("Google boş yanıt döndürdü.")
                    
            except Exception as e:
                err_str = str(e)
                if "429" in err_str:
                    log_placeholder.error("🚦 KOTA HATASI: Bu API anahtarı bugünlük limitini doldurdu. Lütfen AI Studio'dan YENİ BİR PROJE açıp yeni key alın.")
                elif "404" in err_str:
                    log_placeholder.error("❌ MODEL HATASI: Sunucu modeli bulamadı. Lütfen requirements.txt dosyasını kontrol edin.")
                else:
                    log_placeholder.error(f"⚠️ KRİTİK HATA: {err_str}")
