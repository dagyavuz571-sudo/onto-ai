import streamlit as st
import numpy as np
import time
import matplotlib.pyplot as plt

# --- UYGULAMA AYARLARI ---
st.set_page_config(page_title="Onto-AI: Truth Seeker", layout="centered")

# --- BAŞLIK VE TEORİ ---
st.title("🧬 Onto-AI: Termodinamik Doğruluk Motoru")
st.markdown("""
**Geliştirici:** Yavuz Dağ  
*Ontogenetik Sentez Teorisi ile Güçlendirilmiştir.* Bu yapay zeka, cevap verirken sadece kelimeleri değil, **enerji maliyetini** de hesaplar.
""")

st.divider()

# --- SİZİN DENKLEMİNİZİN ARAYÜZÜ ---
st.sidebar.header("⚙️ Termodinamik Ayarlar")

# Kullanıcı "Zaman/Olgunluk" (t) değerini seçer
t_value = st.sidebar.slider("Gelişim Süreci (t)", min_value=0, max_value=100, value=10)

# w(t) Hesaplama: Sizin Denkleminiz
# Zaman arttıkça Ajans (İrade) artar
w_agency = 1 - np.exp(-0.05 * t_value)

st.sidebar.metric(label="Ajans Seviyesi (w)", value=f"%{w_agency*100:.1f}")

# --- SİMÜLASYON MOTORU ---
def generate_onto_response(question, w):
    """
    Bu fonksiyon, Ajans (w) seviyesine göre cevabın 'kesinliğini' değiştirir.
    w düşükse: AI halüsinasyon görür (Yaratıcı ama yanlış/pahalı).
    w yüksekse: AI gerçeğe odaklanır (Kısa, net, düşük enerjili).
    """
    
    # Simüle edilmiş cevaplar (Burası ileride gerçek GPT'ye bağlanacak)
    if w < 0.3:
        # Düşük Ajans: Halüsinasyon / Yüksek Entropi
        response = f"Hmm, '{question}' hakkında düşünüyorum... Belki de cevap bir rüyadır? Sinekler aslında melek olabilir. Enerji umurumda değil, rastgele konuşuyorum..."
        energy_cost = 95.0 # Çok pahalı
        status = "⚠️ Yüksek Entropi (Halüsinasyon)"
    elif w < 0.7:
        # Orta Ajans: Geçiş Evresi
        response = f"'{question}' sorusuna bakıyorum. Bazı belirsizlikler var ama genel kanı şu yönde... Biraz daha odaklanmam lazım."
        energy_cost = 45.0
        status = "🔄 İşleniyor..."
    else:
        # Yüksek Ajans: Termodinamik Zorunluluk (Gerçeklik)
        response = f"Analiz: {question}. \n\nSONUÇ: Cevap, fiziksel ve mantıksal gerçeklikle tam uyumlu. Gereksiz bilgi (gürültü) filtrelendi."
        energy_cost = 5.0 # Çok ucuz (Verimli)
        status = "✅ Termodinamik Denge (Gerçek)"
    
    return response, energy_cost, status

# --- KULLANICI ARAYÜZÜ ---
user_question = st.text_input("Sorunuzu sorun:", placeholder="Örn: Evrimsel süreçte doğruluk neden zorunludur?")

if st.button("Analiz Et"):
    if not user_question:
        st.warning("Lütfen bir soru yazın.")
    else:
        # İlerleme çubuğu (Sizin denkleminiz çalışıyor efekti)
        progress_text = "Ontogenetik filtreler devreye giriyor..."
        my_bar = st.progress(0, text=progress_text)

        for percent_complete in range(100):
            time.sleep(0.01)
            my_bar.progress(percent_complete + 1, text=progress_text)
        
        # Cevabı Üret
        answer, cost, status = generate_onto_response(user_question, w_agency)
        
        # --- SONUÇ EKRANI ---
        st.success(status)
        st.write(f"**Onto-AI Cevabı:** {answer}")
        
        st.divider()
        
        # --- GÖRSELLEŞTİRME (SİZİN GRAFİĞİNİZ) ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(label="Harcanan Bilişsel Enerji", value=f"{cost} joule", delta=f"-{100-cost} Tasarruf")
            
        with col2:
            # Grafik Çizimi
            fig, ax = plt.subplots(figsize=(4,3))
            categories = ['Standart AI (Pahalı)', 'Onto-AI (Siz)']
            values = [95, cost]
            colors = ['red', 'blue']
            
            ax.bar(categories, values, color=colors)
            ax.set_ylabel('Enerji Maliyeti (Atık Isı)')
            ax.set_title('Termodinamik Karşılaştırma')
            st.pyplot(fig)

        st.info(f"💡 Teori Notu: Ajans (w) seviyeniz şu an {w_agency:.2f}. Bu seviyede sistem, gerçeğe ulaşmak için {100-cost} birim enerji tasarrufu yaptı.")
