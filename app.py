import streamlit as st
import numpy as np
import google.generativeai as genai
import urllib.parse
from datetime import datetime

# --- KOTA KALKANI: MODEL SIRALAMASI ---
# Eğer ilk model 429 verirse, sırayla diğerlerini deneyecek.
MODEL_HIERARCHY = [
    "gemini-3-flash", 
    "gemini-2.0-flash", 
    "gemini-1.5-flash", 
    "gemini-pro"
]

def generate_with_fallback(prompt, config, api_key):
    genai.configure(api_key=api_key)
    errors = []
    
    for model_name in MODEL_HIERARCHY:
        try:
            model = genai.GenerativeModel(model_name=model_name, generation_config=config)
            response = model.generate_content(prompt)
            return response, model_name
        except Exception as e:
            errors.append(f"{model_name}: {str(e)}")
            continue # Bir sonraki modeli dene
            
    raise Exception(f"Tüm modellerin kotası doldu! Detaylar: {errors}")

# --- (Arayüz ve Diğer Kısımlar Aynı Kalıyor, Sadece Üretim Kısmını Güncelledim) ---

if prompt := st.chat_input("Girdiyi buraya bırakın..."):
    # ... (Önceki hafıza kayıt kodları) ...
    
    if not api_key:
        st.error("API Key eksik!")
    else:
        with st.chat_message("assistant"):
            status_box = st.empty()
            status_box.info("🔍 Müsait bir zeka kanalı aranıyor...")
            
            # w-değerine bağlı dinamik sıcaklık hesabı
            t_val = st.session_state.get('t_val', 50) # Örnek
            w_agency = 1 - np.exp(-0.05 * t_val)
            dynamic_temp = max(0.1, 2.0 * (1 - w_agency))
            
            config = {"temperature": dynamic_temp, "top_p": 0.95}
            
            try:
                # YEDEKLEMELİ ÜRETİM SİSTEMİ
                response, active_model = generate_with_fallback(prompt, config, api_key)
                reply = response.text
                status_box.markdown(reply)
                st.caption(f"✅ Yanıt {active_model} üzerinden alındı.")
                
                # ... (Görsel ve Hafıza Kayıt Kodları) ...
            except Exception as e:
                if "429" in str(e):
                    st.error("🚦 MAKSİMUM KOTA İHLALİ: Google tüm modellerinizi bugünlük askıya aldı. Lütfen yeni bir API Key (Yeni Proje) kullanın.")
                else:
                    st.error(f"Sistem Hatası: {e}")
