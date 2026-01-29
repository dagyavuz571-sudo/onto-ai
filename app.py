import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
from datetime import datetime

# --- 1. TASARIM VE ESTETİK ---
st.set_page_config(page_title="Onto-AI: Termodinamik Core", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #050505, #111111); color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #0c0c0c; border-right: 1px solid #00ffcc; }
    .stChatMessage { border-radius: 12px; border: 1px solid rgba(0, 255, 204, 0.1); margin-bottom: 8px; background: rgba(255, 255, 255, 0.02); }
    h1, h2, h3 { color: #00ffcc !important; font-family: 'Inter', sans-serif; }
    .stMetric { background: rgba(0, 255, 204, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(0, 255, 204, 0.2); }
    </style>
""", unsafe_allow_html=True)

# --- 2. HAFIZA VE ARŞİV YÖNETİMİ ---
if "all_sessions" not in st.session_state: st.session_state.all_sessions = {}
if "current_chat" not in st.session_state: st.session_state.current_chat = []

# --- 3. YAN MENÜ (KONTROL PANELİ) ---
with st.sidebar:
    st.title("🧬 Onto-Arşiv")
    
    if st.button("➕ Yeni Sohbet Başlat"):
        if st.session_state.current_chat:
            title = f"Analiz {datetime.now().strftime('%H:%M:%S')}"
            st.session_state.all_sessions[title] = list(st.session_state.current_chat)
        st.session_state.current_chat = []
        st.rerun()
    
    st.divider()
    st.subheader("📂 Geçmiş Kayıtlar")
    for title in list(st.session_state.all_sessions.keys()):
        if st.button(f"📄 {title}", use_container_width=True):
            st.session_state.current_chat = list(st.session_state.all_sessions[title])
            st.rerun()
            
    st.divider()
    
    # API Girişi
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Bağlantı Aktif")
    else:
        api_key = st.text_input("Google API Key:", type="password")
    
    # --- TERMODİNAMİK PARAMETRE AYARI ---
    st.subheader("⚙️ Termodinamik Ayarlar")
    t_val = st.slider("Gelişim Süreci (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_val)
    
    # Temperature hesabı: w=1 iken Temp=0.1 (Düzen), w=0 iken Temp=1.9 (Kaos)
    dynamic_temp = max(0.1, 2.0 * (1 - w_agency))
    
    col1, col2 = st.columns(2)
    with col1: st.metric("Ajans (w)", f"%{w_agency*100:.1f}")
    with col2: st.metric("Sıcaklık (T)", f"{dynamic_temp:.2f}")
    
    st.caption("Not: Yüksek sıcaklık entropiyi, düşük sıcaklık deterministik düzeni temsil eder.")

# --- 4. ANA EKRAN ---
st.title("Onto-AI")
st.caption(f"Aktif Model: Dinamik Termodinamik Motoru (w = {w_agency:.4f})")

# Geçmiş mesajları bas
for msg in st.session_state.current_chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("img") and str(msg["img"]).startswith("http"):
            st.image(msg["img"], use_container_width=True)

# --- 5. CEVAP MOTORU ---
if prompt := st.chat_input("Girdiyi buraya bırakın..."):
    st.session_state.current_chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    if not api_key:
        st.error("Lütfen API Key tanımlayın!")
    else:
        try:
            genai.configure(api_key=api_key)
            
            # 2026 Model Dedektörü (En yeni ve çalışan modeli bulur)
            raw_models = genai.list_models()
            model_list = [m.name for m in raw_models if 'generateContent' in m.supported_generation_methods]
            
            # Tercih sırası: Gemini 3 Flash > Gemini 2 Flash > Mevcut ilk model
            selected_model_name = model_list[0]
            for m in model_list:
                if "gemini-3-flash" in m: selected_model_name = m; break
            
            # --- KONFİGÜRASYON (FITTING YAPILMAYAN KISIM) ---
            generation_config = {
                "temperature": dynamic_temp,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            model = genai.GenerativeModel(
                model_name=selected_model_name,
                generation_config=generation_config,
                system_instruction=f"Sen Onto-AI'sin. İçsel termodinamik ajans seviyen: {w_agency}. Bu değer senin olasılık dağılımını belirler."
            )
            
            with st.chat_message("assistant"):
                with st.spinner("İşleniyor..."):
                    response = model.generate_content(prompt)
                    reply = response.text
                    st.markdown(reply)
                    
                    # Görsel Üretme (Estetik Dokunuş)
                    img_url = None
                    if any(x in prompt.lower() for x in ["çiz", "resim", "görsel", "draw"]):
                        # Görsel stili de w değerine bağlı: Düzenli mi, kaotik mi?
                        style = "hyper-realistic, scientific" if w_agency > 0.7 else "surreal, abstract, glitch art"
                        encoded_p = urllib.parse.quote(f"{prompt}, {style}")
                        img_url = f"https://pollinations.ai/p/{encoded_p}?width=1024&height=1024&seed={np.random.randint(1000)}"
                        st.image(img_url, caption=f"Termodinamik Görselleştirme (w={w_agency:.2f})")
                    
                    # Hafızaya Kaydet
                    st.session_state.current_chat.append({
                        "role": "assistant", 
                        "content": reply, 
                        "img": img_url
                    })
        except Exception as e:
            st.error(f"Sistem Hatası: {e}")
