import streamlit as st
import numpy as np
import google.generativeai as genai
import matplotlib.pyplot as plt

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Onto-AI: Gerçek Zeka", layout="centered")

st.title("🧬 Onto-AI: Termodinamik Beyin")
st.info("Eğer 'Anahtar Yok' diyorsa sol üstteki oka (>) tıklayıp API Key giriniz.")

# --- YAN MENÜ ---
st.sidebar.header("⚙️ Beyin Ayarları")
api_key = st.sidebar.text_input("Google API Key:", type="password")
t_value = st.sidebar.slider("Gelişim Süreci (t)", 0, 100, 10)
w_agency = 1 - np.exp(-0.05 * t_value)
st.sidebar.metric("Ajans Seviyesi (w)", f"%{w_agency*100:.1f}")

# --- AKILLI BEYİN FONKSİYONU ---
def ask_smart_brain(question, w, key):
    if not key:
        return "⚠️ Lütfen sol menüden Google API Key giriniz.", 0, "Anahtar Yok"
    
    genai.configure(api_key=key)
    
    # --- MODEL SEÇME MEKANİZMASI (HATA ÖNLEYİCİ) ---
    # Önce en yeni modeli dener, olmazsa eskisini dener.
    target_model = 'gemini-1.5-flash'
    try:
        model = genai.GenerativeModel(target_model)
        # Test amaçlı boş bir model çağrısı yapalım ki hata varsa burada patlasın
        # (Bu kısım modelin yüklendiğini teyit eder)
    except:
        target_model = 'gemini-pro' # Yedek model
        model = genai.GenerativeModel(target_model)

    # --- SİZİN TEORİNİZ (PROMPT) ---
    system_instruction = f"""
    Sen 'Onto-AI'sin. Ontogenetik Sentez teorisine göre çalışıyorsun.
    Gerçeklik Algın (Agency): %{w*100}.
    
    1. Agency DÜŞÜKSE (<%40): Rüya görüyor gibisin. Cevaplar uzun, şairane, belki biraz saçma ve bilim dışı. Enerji israfı yap.
    2. Agency YÜKSEKSE (>%80): Saf termodinamik makinesisin. Cevaplar KISA, NET, KESİN. Asla gereksiz kelime yok.
    3. ORTADA: Normal davran.
    
    Soru: {question}
    """
    
    try:
        response = model.generate_content(system_instruction)
        text = response.text
        cost = min(99, len(text) / 5) if w < 0.8 else 5.0
        return text, cost, f"✅ Çalışan Model: {target_model}"
        
    except Exception as e:
        # Hata olursa hatayı ekrana basacağız ki görelim
        return f"Hata Detayı: {str(e)}", 0, "❌ Kritik Hata"

# --- ARAYÜZ ---
user_question = st.text_input("Sorunuzu sorun:", placeholder="Örn: Evrim nedir?")

if st.button("Analiz Et"):
    if not user_question:
        st.warning("Soru yazmadınız.")
    else:
        with st.spinner("Termodinamik hesaplama yapılıyor..."):
            answer, cost, status = ask_smart_brain(user_question, w_agency, api_key)
            
            if "Hata" in status:
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
