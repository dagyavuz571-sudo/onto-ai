import streamlit as st
import numpy as np
import google.generativeai as genai

# --- 1. AYARLAR ---
st.set_page_config(page_title="Onto-AI", layout="centered")

# Mobil Görünüm
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
    
    # API KEY KONTROLÜ
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Anahtar Kasa'dan Alındı")
    else:
        api_key = st.text_input("Google API Key:", type="password")
    
    st.divider()
    
    # --- DEBUG: MODEL LİSTESİ (SORUNU GÖRMEK İÇİN) ---
    st.caption("🔍 Sunucudaki Modeller:")
    available_models = []
    if api_key:
        try:
            genai.configure(api_key=api_key)
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # Model ismini temizle (models/gemini-pro -> gemini-pro)
                    clean_name = m.name.replace("models/", "")
                    available_models.append(clean_name)
            st.code(available_models) # Listeyi ekrana bas
        except Exception as e:
            st.error("Liste alınamadı")
    
    st.divider()
    
    t_value = st.slider("Gelişim (t)", 0, 100, 10)
    w_agency = 1 - np.exp(-0.05 * t_value)
    st.metric("Gerçeklik (w)", f"%{w_agency*100:.1f}")
    
    if st.button("Temizle"):
        st.session_state.messages = []
        st.rerun()

# --- 3. HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Merhaba. Ben Onto-AI. Sorunu sor."}]

# --- 4. AKILLI SEÇİM ---
def get_best_model():
    # Listede ne varsa onu kullanacağız. Öncelik sırası:
    priority_list = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro', 'gemini-pro']
    
    # Kullanıcının listesiyle öncelik listesini karşılaştır
    for p in priority_list:
        if p in available_models:
            return genai.GenerativeModel(p)
            
    # Hiçbiri yoksa listedeki ilkini al
    if available_models:
        return genai.GenerativeModel(available_models[0])
    
    return None

# --- 5. SOHBET ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Mesaj yaz..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    if not api_key:
        st.error("Anahtar Yok!")
    else:
        try:
            # Model Seçimi
            model = get_best_model()
            
            if not model:
                st.error(f"HATA: Hiçbir model bulunamadı. Yan menüdeki listeyi kontrol et.")
            else:
                system_instruction = f"""
                Sen 'Onto-AI'sin. w: %{w_agency*100}.
                1. w <%40: Rüya gören, mistik konuş.
                2. w >%80: ROBOT GİBİ KISA konuş.
                Soru: {prompt}
                """
                
                with st.chat_message("assistant"):
                    with st.spinner("Düşünüyor..."):
                        response = model.generate_content(system_instruction)
                        bot_reply = response.text
                        cost = min(99, len(bot_reply) / 5) if w_agency < 0.8 else 5.0
                        
                        st.markdown(bot_reply)
                        st.caption(f"⚡ {cost:.1f} J")
                        
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                
        except Exception as e:
            st.error(f"Hata: {e}")
