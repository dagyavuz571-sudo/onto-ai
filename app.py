import streamlit as st
import numpy as np
import google.generativeai as genai

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI", layout="centered")

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stApp { margin-top: -40px; }
</style>
""", unsafe_allow_html=True)

st.title("🧬 Onto-AI")
st.caption("Korumalı Termodinamik Motor")

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Beyin Ayarları")
    
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Sistem Online")
    else:
        api_key = st.text_input("Google API Key:", type="password")
    
    st.divider()
    
    # Model Seçimi (Öncelikli Liste)
    st.caption("🤖 Model Durumu")
    working_model_name = "Tespit Ediliyor..."
    
    t_value = st.slider("Gelişim (t)", 0, 100, 10)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Sohbeti Sıfırla"):
        st.session_state.messages = []
        st.rerun()

# --- 3. HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Merhaba. Kota koruma modu aktif. Sorunu sorabilirsin."}]

# --- 4. AKILLI MODEL SEÇİCİ (KOTA ÖNCELİKLİ) ---
def get_best_model_by_quota(key):
    genai.configure(api_key=key)
    # Daha geniş kotalı (1.5 serisi) modellere öncelik veriyoruz.
    priority = ['gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-1.5-pro', 'gemini-pro']
    
    try:
        available = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for p in priority:
            if p in available:
                return genai.GenerativeModel(p), p
        return genai.GenerativeModel(available[0]), available[0]
    except:
        return genai.GenerativeModel('gemini-1.5-flash'), 'gemini-1.5-flash'

# --- 5. SOHBET ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Mesajınızı yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    if not api_key:
        st.error("API Key Eksik!")
    else:
        try:
            model, m_name = get_best_model_by_quota(api_key)
            
            system_instruction = f"Sen 'Onto-AI'sin. w: %{w_agency*100}. Teorine göre cevap ver. Soru: {prompt}"
            
            with st.chat_message("assistant"):
                with st.spinner("Analiz ediliyor..."):
                    try:
                        response = model.generate_content(system_instruction)
                        bot_reply = response.text
                        st.markdown(bot_reply)
                        st.caption(f"🧠 Kullanılan Model: {m_name}")
                        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                    
                    except Exception as e:
                        if "429" in str(e):
                            st.error("🚦 **Hız Sınırı!** Google ücretsiz kotanız doldu veya çok hızlı soruyorsunuz. Lütfen 30 saniye sonra tekrar deneyin.")
                        else:
                            st.error(f"Bir sorun oluştu: {e}")
                            
        except Exception as e:
            st.error(f"Bağlantı Hatası: {e}")
