import streamlit as st
import numpy as np
import google.generativeai as genai
import time

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
st.caption("Termodinamik Doğruluk Motoru")

# --- 2. YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Beyin Ayarları")
    
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Sistem Online")
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
        "content": "Merhaba. Ben Onto-AI. Sistemim her duruma karşı korumalıdır. Sorunu sor."
    })

# --- 4. AKILLI MODEL SEÇİCİ (BU FONKSİYON HAYAT KURTARIR) ---
def generate_response_safe(model_key, prompt_text, system_inst):
    genai.configure(api_key=model_key)
    
    # LİSTE: [Birinci Tercih, İkinci Tercih]
    # Önce Hızlıyı (1.5 Flash) dener, olmazsa Eskiyi (Pro) dener.
    models_to_try = ['gemini-1.5-flash', 'gemini-pro']
    
    last_error = ""
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            
            # Filtreleri Kapat
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Cevap Üretmeyi Dene
            response = model.generate_content(system_inst + f"\nSoru: {prompt_text}", safety_settings=safety_settings)
            
            # Eğer buraya geldiyse hata vermemiş demektir, cevabı döndür ve döngüden çık.
            return response.text, model_name 
            
        except Exception as e:
            # Hata verirse (404 veya 429), bunu kaydet ve bir sonraki modele geç
            last_error = str(e)
            continue 
            
    # Eğer döngü bitti ve hala cevap yoksa:
    return f"HATA: Hiçbir model çalışmadı. Son hata: {last_error}", "Yok"

# --- 5. MESAJLARI GÖSTER ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. KULLANICI GİRİŞİ ---
if prompt := st.chat_input("Bir şeyler yazın..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    if not api_key:
        st.error("Anahtar yok! Secrets ayarını kontrol et.")
    else:
        with st.chat_message("assistant"):
            with st.spinner("Termodinamik analiz..."):
                
                # SİZİN TEORİNİZ
                system_instruction = f"""
                Sen 'Onto-AI'sin. Gerçeklik Algın (w): %{w_agency*100}.
                1. w DÜŞÜKSE: Rüya gören, mistik, uzun cevap ver.
                2. w YÜKSEKSE: ROBOT GİBİ OL. Kısa, net, kesin.
                """
                
                # GÜVENLİ FONKSİYONU ÇAĞIRIYORUZ
                bot_reply, used_model = generate_response_safe(api_key, prompt, system_instruction)
                
                # Enerji Hesabı
                cost = min(99, len(bot_reply) / 5) if w_agency < 0.8 else 5.0
                
                st.markdown(bot_reply)
                
                # Hangi modelin çalıştığını küçükçe gösterelim (Debug için)
                st.caption(f"⚡ Maliyet: {cost:.1f} J | 🧠 Model: {used_model}")
        
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
