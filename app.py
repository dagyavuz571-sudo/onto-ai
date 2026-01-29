import streamlit as st
import numpy as np
import google.generativeai as genai
import matplotlib.pyplot as plt

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Onto-AI: Final", layout="centered")

# --- PROFESYONEL MOBİL GÖRÜNÜM İÇİN CSS ---
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stApp {
    margin-top: -80px;
}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("🧬 Onto-AI: Termodinamik Beyin")
st.info("Bu sürüm, mevcut en uygun yapay zeka modelini OTOMATİK bulur.")

# --- YAN MENÜ ---
st.sidebar.header("⚙️ Beyin Ayarları")
api_key = st.sidebar.text_input("Google API Key:", type="password")
t_value = st.sidebar.slider("Gelişim Süreci (t)", 0, 100, 10)
w_agency = 1 - np.exp(-0.05 * t_value)
st.sidebar.metric("Ajans Seviyesi (w)", f"%{w_agency*100:.1f}")

# --- OTOMATİK MODEL BULUCU ---
def find_working_model(key):
    """Google'ın sunduğu modelleri listeler ve çalışan ilkini seçer."""
    genai.configure(api_key=key)
    try:
        available_models = []
        for m in genai.list_models():
            # Sadece metin üretebilen modelleri al
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # Listeden işimize yarayan ilkini seç (Genelde gemini-pro veya gemini-1.0-pro)
        if available_models:
            return available_models[0] # İlk bulduğunu döndür
        else:
            return None
    except Exception as e:
        return None

# --- BEYİN FONKSİYONU ---
def ask_brain_auto(question, w, key):
    if not key:
        return "⚠️ Önce API Key giriniz.", 0, "Anahtar Yok"
    
    # Otomatik Model Seçimi
    model_name = find_working_model(key)
    
    if not model_name:
        return "HATA: API Key hatalı veya Google modellerine erişilemiyor.", 0, "Bağlantı Hatası"

    try:
        model = genai.GenerativeModel(model_name)
        
        # SİZİN TEORİNİZ (PROMPT)
        system_instruction = f"""
        Sen 'Onto-AI'sin. Ontogenetik Sentez teorisine göre çalışıyorsun.
        Gerçeklik Algın (Agency): %{w*100}.
        
        1. Agency DÜŞÜKSE (<%40): Rüya görüyor gibisin. Cevaplar uzun, şairane, tutarsız.
        2. Agency YÜKSEKSE (>%80): Saf gerçeklik makinesisin. Cevaplar KISA, NET ve KESİN DOĞRU.
        3. ORTADA: Normal davran.
        
        Soru: {question}
        """
        
        response = model.generate_content(system_instruction)
        text = response.text
        cost = min(99, len(text) / 5) if w < 0.8 else 5.0
        
        return text, cost, f"✅ Çalışan Model: {model_name}"
        
    except Exception as e:
        return f"Model Hatası: {str(e)}", 0, "❌ Hata"

# --- ARAYÜZ ---
user_question = st.text_input("Sorunuzu sorun:", placeholder="Örn: Gerçek nedir?")

if st.button("Analiz Et"):
    if not user_question:
        st.warning("Soru yazmadınız.")
    else:
        with st.spinner("Uygun model aranıyor ve çalıştırılıyor..."):
            answer, cost, status = ask_brain_auto(user_question, w_agency, api_key)
            
            if "Hata" in status or "⚠️" in answer:
                st.error(answer)
            else:
                st.success(f"Durum: {status}")
                st.write(answer)
                
                # Grafik
                st.divider()
                col1, col2 = st.columns(2)
                col1.metric("Enerji Maliyeti", f"{cost:.1f} J")
                fig, ax = plt.subplots(figsize=(4,2))
                ax.bar(["Maliyet"], [cost], color="blue" if cost < 50 else "red")
                col2.pyplot(fig)
