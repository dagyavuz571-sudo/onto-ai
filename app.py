import streamlit as st
import numpy as np
import google.generativeai as genai
import time

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI", layout="centered")

# Mobil Görünüm İyileştirme
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stApp { margin-top: -40px; }
</style>
""", unsafe_allow_html=True)

st.title("🧬 Onto-AI")
st.caption("Termodinamik Doğruluk Motoru")

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Beyin Ayarları")
    api_key = st.text_input("Google API Key:", type="password")
    
    st.divider()
    
    # Sürgü
    t_value = st.slider("Gelişim Süreci (t)", 0, 100, 10)
    w_agency = 1 - np.exp(-0.05 * t_value)
    
    # Ekrana yazdıralım
    st.metric("Gerçeklik Algısı (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Sohbeti Temizle"):
        st.session_state.messages = []
        st.rerun()

# --- 3. HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Merhaba. Ben Onto-AI. Ajans seviyeme göre cevap veririm. Sorunu sor."
    })

# --- 4. MODEL SEÇİCİ ---
def get_model(key):
    genai.configure(api_key=key)
    try:
        # Önce en hızlıyı dene
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        # Olmazsa eskisini dene
        return genai.GenerativeModel('gemini-pro')

# --- 5. MESAJLARI GÖSTER ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. CEVAP MOTORU ---
if prompt := st.chat_input("Bir şeyler yazın..."):
    
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    if not api_key:
        st.error("Lütfen API Key giriniz.")
    else:
        try:
            model = get_model(api_key)
            
            # GÜVENLİK FİLTRELERİNİ KAPATIYORUZ (Cevabı engellemesin diye)
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            system_instruction = f"""
            Sen 'Onto-AI'sin. 
            Şu anki Gerçeklik Algın (Agency): %{w_agency*100}.
            
            GÖREVİN:
            1. Eğer Agency <%40 ise: Rüya gören, biraz dengesiz, şairane ve uzun cevap ver.
            2. Eğer Agency >%80 ise: ROBOT GİBİ OL. Cevap sadece 1-2 cümle olsun. Kesin bilgi ver. "Merhaba" deme.
            3. Ortada ise: Normal davran.
            
            Soru: {prompt}
            """
            
            with st.chat_message("assistant"):
                with st.spinner("Düşünüyor..."):
                    response = model.generate_content(system_instruction, safety_settings=safety_settings)
                    
                    if response.text:
                        bot_reply = response.text
                    else:
                        bot_reply = "Filtreye takıldı veya cevap üretilemedi. Lütfen tekrar dene."

                    # Enerji Hesabı
                    cost = min(99, len(bot_reply) / 5) if w_agency < 0.8 else 5.0
                    
                    # Sadece Yazı ve Küçük Bir Not
                    st.markdown(bot_reply)
                    st.caption(f"⚡ Termodinamik Maliyet: {cost:.1f} J")
            
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
        except Exception as e:
            st.error(f"Hata: {e}")
