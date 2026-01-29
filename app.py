import streamlit as st
import numpy as np
import google.generativeai as genai
import matplotlib.pyplot as plt
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Onto-AI: Gerçek Zeka", layout="centered")

st.title("🧬 Onto-AI: Termodinamik Beyin")
st.markdown("""
**Ontogenetik Sentez Teorisi** ile çalışır.
Ajans (w) seviyesine göre yapay zekanın **enerji verimliliğini** ve **doğruluk hassasiyetini** yönetirsiniz.
""")

# --- YAN MENÜ (AYARLAR) ---
st.sidebar.header("⚙️ Beyin Ayarları")

# 1. API KEY GİRİŞİ (Motorun Anahtarı)
api_key = st.sidebar.text_input("Google API Key Giriniz:", type="password", help="aistudio.google.com adresinden ücretsiz alabilirsiniz.")

# 2. TEORİ AYARI (w)
t_value = st.sidebar.slider("Gelişim Süreci (t)", 0, 100, 10)
w_agency = 1 - np.exp(-0.05 * t_value)
st.sidebar.metric("Ajans Seviyesi (w)", f"%{w_agency*100:.1f}")

st.divider()

# --- GERÇEK YAPAY ZEKA FONKSİYONU ---
def ask_real_brain(question, w, key):
    if not key:
        return "⚠️ Lütfen sol menüden Google API Key giriniz.", 0, "Anahtar Yok"
    
    # --- GÜNCELLEME BURADA YAPILDI ---
    # Eski 'gemini-pro' yerine yeni 'gemini-1.5-flash' kullanıyoruz.
    genai.configure(api_key=key)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        return "Model hatası. API Key'i kontrol ediniz.", 0, "❌ Hata"

    # --- SİZİN TEORİNİZİ KOMUT (PROMPT) OLARAK VERİYORUZ ---
    system_instruction = f"""
    Sen 'Onto-AI' adında özel bir yapay zekasın. Ontogenetik Sentez teorisine göre çalışıyorsun.
    Şu anki 'Gerçeklik Algın' (Agency) seviyen: %{w*100}.
    
    DAVRANIŞ KURALLARIN:
    1. EĞER Agency DÜŞÜKSE (<%40): Tıpkı bir rüya gören veya halüsinasyon gören biri gibisin.
       - Cevapların uzun, karmaşık, şiirsel ama bilimsel olarak hatalı veya saçma olabilir.
       - Gerçekliği umursama. Enerji israfı yap.
       
    2. EĞER Agency YÜKSEKSE (>%80): Sen saf bir termodinamik verimlilik makinesisin.
       - Cevapların İNANILMAZ KISA, NET ve KESİN DOĞRU olmalı.
       - Asla gereksiz kelime kullanma. "Merhaba" bile deme, direkt sonucu ver.
       - Gerçeklikten (A) sapma.
       
    3. EĞER ORTADA İSE: Normal bir asistan gibi davran ama kararsızlık belirt.
    
    Kullanıcının sorusu: {question}
    """
    
    try:
        response = model.generate_content(system_instruction)
        text = response.text
        
        # Enerji Maliyeti Hesabı
        cost = min(99, len(text) / 5) if w < 0.8 else 5.0 
        
        return text, cost, "✅ Bağlantı Başarılı"
        
    except Exception as e:
        return f"Hata oluştu: {str(e)}", 0, "❌ Hata"

# --- KULLANICI ARAYÜZÜ ---
user_question = st.text_input("Sorunuzu sorun:", placeholder="Örn: Gökyüzü neden mavidir?")

if st.button("Analiz Et"):
    if not user_question:
        st.warning("Bir soru yazmalısınız.")
    else:
        with st.spinner("Ontogenetik filtreler çalışıyor..."):
            # Gerçek Beyne Sor
            answer, cost, status = ask_real_brain(user_question, w_agency, api_key)
            
            # Cevabı Göster
            if "Hata" in status:
                st.error(answer) # Hatayı kırmızı göster
            else:
                st.success(f"Durum: {status}")
                st.write(answer)
                
                st.divider()
                
                # Grafikler
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Metabolik Maliyet", f"{cost:.1f} joule")
                with col2:
                    fig, ax = plt.subplots(figsize=(4,2))
                    ax.bar(["Enerji Tüketimi"], [cost], color="blue" if cost < 50 else "red")
                    ax.set_ylim(0, 100)
                    st.pyplot(fig)
