import streamlit as st
import numpy as np
import google.generativeai as genai
import matplotlib.pyplot as plt
import time

# --- 1. SAYFA VE MOBİL AYARLAR ---
st.set_page_config(page_title="Onto-AI Chat", layout="centered")

# Mobil için gereksiz menüleri gizle
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stApp { margin-top: -40px; }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("🧬 Onto-AI")
st.caption("Termodinamik Doğruluk Motoru")

# --- 2. YAN MENÜ (AYARLAR) ---
with st.sidebar:
    st.header("⚙️ Beyin Ayarları")
    api_key = st.text_input("Google API Key:", type="password", help="Anahtar olmadan motor çalışmaz.")
    
    st.divider()
    
    t_value = st.slider("Gelişim Süreci (t)", 0, 100, 10)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik Algısı (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Sohbeti Sıfırla"):
        st.session_state.messages = []
        st.rerun()

# --- 3. HAFIZA BAŞLATMA ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Merhaba. Ben Ontogenetik Sentez modeliyle çalışan bir yapay zekayım. Bana bir soru sor."
    })

# --- 4. AKILLI MODEL SEÇİCİ (HATA ÖNLEYİCİ) ---
def get_working_model(key):
    """Google'a sorar: 'Elinde hangi modeller var?' ve çalışan ilkini seçer."""
    genai.configure(api_key=key)
    try:
        # Google'daki tüm modelleri listele
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # İlk bulduğun çalışan modeli (örn: gemini-pro) döndür
                return genai.GenerativeModel(m.name)
        return None
    except:
        return None

# --- 5. EKRANA MESAJLARI YAZDIRMA ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. KULLANICI MESAJ YAZINCA ---
# Walrus (:=) hatası da düzeltildi.
if prompt := st.chat_input("Bir şeyler yazın..."):
    
    # Kullanıcı mesajını ekrana bas
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Cevap Üretme
    if not api_key:
        st.error("Lütfen sol menüden API Key giriniz.")
    else:
        # --- MODELİ BURADA ÇAĞIRIYORUZ ---
        model = get_working_model(api_key)
        
        if not model:
            st.error("HATA: API Key geçersiz veya Google servisine ulaşılamıyor.")
        else:
            try:
                # SİZİN TEORİNİZ (Prompt)
                system_instruction = f"""
                Sen 'Onto-AI'sin. Ontogenetik Sentez teorisine göre çalışıyorsun.
                Şu anki Gerçeklik Algın (Agency): %{w_agency*100}.
                
                1. Agency DÜŞÜKSE (<%40): Rüya görüyor gibisin. Şairane, uzun, bazen saçma konuş.
                2. Agency YÜKSEKSE (>%80): Saf gerçeklik makinesisin. Çok KISA, NET ve KESİN konuş.
                3. ORTADA: Normal asistan gibi davran.
                
                Soru: {prompt}
                """
                
                with st.chat_message("assistant"):
                    with st.spinner("Termodinamik hesaplama..."):
                        response = model.generate_content(system_instruction)
                        bot_reply = response.text
                        
                        # Enerji Maliyeti Hesabı
                        cost = min(99, len(bot_reply) / 5) if w_agency < 0.8 else 5.0
                        
                        st.markdown(bot_reply)
                        
                        # Grafik
                        st.divider()
                        col1, col2 = st.columns([1, 2])
                        col1.caption(f"⚡ Enerji Maliyeti: {cost:.1f} J")
                        
                        fig, ax = plt.subplots(figsize=(3, 0.5))
                        ax.barh(["Isı"], [cost], color="blue" if cost < 50 else "red")
                        ax.set_xlim(0, 100)
                        ax.axis('off')
                        col2.pyplot(fig)
                
                # Hafızaya at
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                
            except Exception as e:
                st.error(f"Beklenmedik bir hata: {e}")
