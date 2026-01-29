import streamlit as st
import numpy as np
import google.generativeai as genai
import matplotlib.pyplot as plt
import time

# --- 1. SAYFA AYARLARI VE MOBİL GÖRÜNÜM ---
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
    # Kullanıcıdan API Key istemeye devam ediyoruz (Güvenli Yol)
    api_key = st.text_input("Google API Key:", type="password", help="Anahtar olmadan motor çalışmaz.")
    
    st.divider()
    
    t_value = st.slider("Gelişim Süreci (t)", 0, 100, 10)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik Algısı (w)", f"%{w_agency*100:.1f}")
    
    st.info("t arttıkça yapay zeka 'halüsinasyon' görmeyi bırakır, enerji tasarrufu yapar ve netleşir.")
    
    # Sohbeti Temizle Butonu
    if st.button("Sohbeti Sıfırla"):
        st.session_state.messages = []
        st.rerun()

# --- 3. HAFIZA BAŞLATMA ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # İlk karşılama mesajı
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Merhaba. Ben Ontogenetik Sentez modeliyle çalışan bir yapay zekayım. Ajans (w) seviyeme göre cevaplarım değişir. Bana bir soru sor."
    })

# --- 4. OTOMATİK MODEL SEÇİCİ ---
def get_model(key):
    genai.configure(api_key=key)
    # Önce en hızlıyı (Flash) dene, yoksa Pro'yu dene
    try:
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return genai.GenerativeModel('gemini-pro')

# --- 5. EKRANA MESAJLARI YAZDIRMA ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. KULLANICI MESAJ YAZINCA NE OLACAK? ---
# !!! DÜZELTME BURADA YAPILDI (:= operatörü) !!!
if prompt := st.chat_input("Bir şeyler yazın..."):
    
    # A) Kullanıcı mesajını ekrana bas ve hafızaya at
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # B) Cevap Üretme Kısmı
    if not api_key:
        st.error("Lütfen sol menüden API Key giriniz.")
    else:
        try:
            model = get_model(api_key)
            
            # SİZİN TEORİNİZ (Prompt)
            system_instruction = f"""
            Sen 'Onto-AI'sin. Ontogenetik Sentez teorisine göre çalışıyorsun.
            Şu anki Gerçeklik Algın (Agency): %{w_agency*100}.
            
            1. Agency DÜŞÜKSE (<%40): Rüya görüyor gibisin. Şairane, uzun, bazen saçma konuş.
            2. Agency YÜKSEKSE (>%80): Saf gerçeklik makinesisin. Çok KISA, NET ve KESİN konuş.
            3. ORTADA: Normal asistan gibi davran.
            
            Soru: {prompt}
            """
            
            with st.spinner("Termodinamik hesaplama..."):
                response = model.generate_content(system_instruction)
                bot_reply = response.text
                
                # Enerji Maliyeti Hesabı
                cost = min(99, len(bot_reply) / 5) if w_agency < 0.8 else 5.0
                
                # C) Botun cevabını ekrana bas
                with st.chat_message("assistant"):
                    st.markdown(bot_reply)
                    
                    # Grafiği cevabın altına küçükçe ekleyelim
                    st.divider()
                    col1, col2 = st.columns([1, 2])
                    col1.caption(f"⚡ Enerji Maliyeti: {cost:.1f} J")
                    
                    # Küçük Bar Grafiği
                    fig, ax = plt.subplots(figsize=(3, 0.5))
                    ax.barh(["Isı"], [cost], color="blue" if cost < 50 else "red")
                    ax.set_xlim(0, 100)
                    ax.axis('off') # Çerçeveleri gizle, sadece bar görünsün
                    col2.pyplot(fig)
                
                # Hafızaya at
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                
        except Exception as e:
            st.error(f"Hata oluştu: {e}")
