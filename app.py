import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse

# --- 1. AYARLAR VE MOBİL ---
st.set_page_config(page_title="Onto-AI Pro", layout="centered")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stApp { margin-top: -40px; }</style>", unsafe_allow_html=True)

st.title("🧬 Onto-AI")
st.caption("Termodinamik Sentez Motoru (Kota Korumalı)")

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
    st.metric("Gerçeklik Algısı (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Sohbeti Sıfırla"):
        st.session_state.messages = []
        st.rerun()

# --- 3. HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Merhaba! Kota dostu ve en stabil modelle çalışmaya hazırım. Ne çizelim veya ne konuşalım?"}]

# --- 4. CİMRİ MODEL SEÇİCİ (BU KISIM HAYAT KURTARIR) ---
def get_safe_model(key):
    genai.configure(api_key=key)
    try:
        models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # ÖNCELİK SIRALAMASI: En yüksek kotalıdan en düşüğe
        # 2.5-flash'ı en sona attık çünkü kotası hemen bitiyor.
        priority = ['gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-1.0-pro', 'gemini-pro', 'gemini-2.5-flash']
        
        for target in priority:
            if target in models:
                return genai.GenerativeModel(target), target
        return genai.GenerativeModel(models[0]), models[0]
    except:
        return None, None

# --- 5. GÖRSEL ÜRETİCİ ---
def generate_image_url(prompt, w):
    style = "surreal, colorful, artistic" if w < 0.4 else "photorealistic, cinematic, 8k"
    full_prompt = f"{prompt}, {style}"
    return f"https://pollinations.ai/p/{urllib.parse.quote(full_prompt)}?width=1024&height=1024&seed={np.random.randint(1000)}"

# --- 6. SOHBET AKIŞI ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "img" in msg: st.image(msg["img"])

if user_input := st.chat_input("Yazın veya 'Çiz' deyin..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)
    
    if not api_key:
        st.error("Lütfen API Key tanımlayın!")
    else:
        model, m_name = get_safe_model(api_key)
        if not model:
            st.error("Google modellerine bağlanılamadı.")
        else:
            with st.chat_message("assistant"):
                with st.spinner(f"Onto-AI ({m_name}) işliyor..."):
                    try:
                        # METİN ÜRETİMİ
                        sys_inst = f"Sen Onto-AI'sin. w: {w_agency}. Soru: {user_input}"
                        response = model.generate_content(sys_inst)
                        reply = response.text
                        st.markdown(reply)
                        
                        # GÖRSEL ÜRETİMİ
                        is_draw = any(x in user_input.lower() for x in ["çiz", "resim", "görsel", "draw", "image"])
                        img_url = generate_image_url(user_input, w_agency) if is_draw else None
                        if img_url: st.image(img_url, caption=f"Ajans: {w_agency:.2f}")
                        
                        # KAYIT
                        new_msg = {"role": "assistant", "content": reply}
                        if img_url: new_msg["img"] = img_url
                        st.session_state.messages.append(new_msg)
                        
                    except Exception as e:
                        if "429" in str(e):
                            st.error("🚦 **KOTA DOLDU!** Google ücretsiz kullanım sınırına takıldınız. Lütfen 1 dakika bekleyin veya yeni bir API Key deneyin.")
                        else:
                            st.error(f"Hata oluştu: {e}")
