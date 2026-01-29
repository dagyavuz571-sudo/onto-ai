import streamlit as st
import numpy as np
import google.generativeai as genai

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI Final", layout="centered")

# Mobil Tasarım
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stApp { margin-top: -40px; }
</style>
""", unsafe_allow_html=True)

st.title("🧬 Onto-AI")
st.caption("Kesintisiz Mod: Stabil Versiyon")

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Beyin Ayarları")
    
    # Secrets Kontrolü
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Yeni Anahtar Aktif")
    else:
        api_key = st.text_input("Google API Key Giriniz:", type="password")
    
    st.divider()
    
    t_value = st.slider("Gelişim (t)", 0, 100, 10)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Sohbeti Temizle"):
        st.session_state.messages = []
        st.rerun()

# --- 3. HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hocam her şey hazır. Yeni anahtarla kotamız tertemiz. Sorunu sorabilirsin."}]

# --- 4. SOHBET ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Buraya yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    if not api_key:
        st.error("Lütfen API Key tanımlayın!")
    else:
        try:
            # DİREKT EN YÜKSEK KOTALI MODELİ ZORLUYORUZ
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash') # En cömert model budur
            
            system_instruction = f"""
            Sen 'Onto-AI'sin. w seviyen: %{w_agency*100}. 
            Teorine göre davran. Soru: {prompt}
            """
            
            with st.chat_message("assistant"):
                with st.spinner("Termodinamik analiz yapılıyor..."):
                    # Kota hatası için try-except
                    try:
                        response = model.generate_content(system_instruction)
                        bot_reply = response.text
                        st.markdown(bot_reply)
                        
                        # Hafızaya ekle
                        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                    
                    except Exception as e:
                        if "429" in str(e):
                            st.error("🚦 Google Kotası Doldu! Lütfen 60 saniye bekleyin veya yeni bir API Key deneyin.")
                        else:
                            st.error(f"Google Mesajı: {e}")
                            
        except Exception as e:
            st.error(f"Bağlantı Hatası: {e}")
