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
    
    # --- GİZLİ KASA KONTROLÜ ---
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Sistem Hazır")
    else:
        api_key = st.text_input("Google API Key:", type="password")
    
    st.divider()
    
    t_value = st.slider("Gelişim Süreci (t)", 0, 100, 10)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik Algısı (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Sohbeti Temizle"):
        st.session_state.messages = []
        st.rerun()

# --- 3. HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Merhaba. Ben Onto-AI. En kararlı sürümümdeyim. Sorunu sor."
    })

# --- 4. MODEL SEÇİCİ (KOTA DOSTU VERSİYON) ---
def get_stable_model(key):
    genai.configure(api_key=key)
    # MACERA YOK! Direkt en yüksek kotalı modeli (1.5 Flash) zorluyoruz.
    # Bu modelde günde 1500 soru sorabilirsiniz.
    try:
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        # Eğer Flash çalışmazsa Pro'ya geç
        return genai.GenerativeModel('gemini-pro')

# --- 5. MESAJLARI GÖSTER ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. CEVAP MOTORU ---
if prompt := st.chat_input("Bir şeyler yazın..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    if not api_key:
        st.error("HATA: Anahtar bulunamadı. Secrets ayarını kontrol edin.")
    else:
        try:
            model = get_stable_model(api_key)
            
            # FİLTRELERİ KAPAT
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            system_instruction = f"""
            Sen 'Onto-AI'sin. Gerçeklik Algın (w): %{w_agency*100}.
            1. w DÜŞÜKSE: Rüya gören, mistik, uzun cevap ver.
            2. w YÜKSEKSE: ROBOT GİBİ OL. Kısa, net, kesin.
            Soru: {prompt}
            """
            
            with st.chat_message("assistant"):
                with st.spinner("Hesaplanıyor..."):
                    # HATA YAKALAMA (429 Hatası için özel önlem)
                    try:
                        response = model.generate_content(system_instruction, safety_settings=safety_settings)
                        bot_reply = response.text if response.text else "Cevap üretilemedi."
                        
                        cost = min(99, len(bot_reply) / 5) if w_agency < 0.8 else 5.0
                        
                        st.markdown(bot_reply)
                        st.caption(f"⚡ Maliyet: {cost:.1f} J")
                        
                        # Başarılı olursa hafızaya ekle
                        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                        
                    except Exception as e:
                        if "429" in str(e):
                            st.warning("🚦 Hız Sınırı! Biraz fazla hızlı sorduk, Google bizi 1 dakikalığına durdurdu. Lütfen bekle.")
                        else:
                            st.error(f"Hata: {e}")
            
        except Exception as e:
            st.error(f"Bağlantı Hatası: {e}")
