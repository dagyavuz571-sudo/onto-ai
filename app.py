import streamlit as st
import numpy as np
from groq import Groq
from gtts import gTTS
from io import BytesIO
import base64
from docx import Document
import urllib.parse
from datetime import datetime
import time
import re

# --- 1. NEURO-UI TASARIM MOTORU ---
st.set_page_config(page_title="Onto-AI: Genesis", layout="wide", page_icon="🧬")

# Session State Başlatma
if "messages" not in st.session_state: st.session_state.messages = []
if "gallery" not in st.session_state: st.session_state.gallery = []
if "ghost_mode" not in st.session_state: st.session_state.ghost_mode = False

# Yan Menüden w Değerini Al (CSS için gerekli)
with st.sidebar:
    st.title("🧬 Onto-AI")
    t_val = st.slider("Gelişim Süreci (t)", 0, 100, 50)
    w_agency = 1 - np.exp(-0.05 * t_val)
    
    # --- DİNAMİK RENK PALETİ ---
    # w yüksekse (Düzen) -> Mavi/Turkuaz
    # w düşükse (Kaos) -> Mor/Kırmızı
    if w_agency > 0.6:
        primary_color = "#00e5ff" # Cyber Blue
        glow_color = "rgba(0, 229, 255, 0.2)"
        theme_msg = "💎 Düzen ve Mantık Hakim"
    elif w_agency < 0.4:
        primary_color = "#ff0055" # Chaos Red
        glow_color = "rgba(255, 0, 85, 0.2)"
        theme_msg = "🔥 Kaos ve Sezgi Hakim"
    else:
        primary_color = "#ae00ff" # Balanced Purple
        glow_color = "rgba(174, 0, 255, 0.2)"
        theme_msg = "⚖️ Denge Durumu"

# CSS Enjeksiyonu (Estetik Düzeltme)
st.markdown(f"""
    <style>
    /* Ana Arka Plan */
    .stApp {{ background-color: #050505; }}
    
    /* Mesaj Kutuları */
    .stChatMessage {{
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid {primary_color};
        border-radius: 15px;
        box-shadow: 0 0 15px {glow_color};
    }}
    
    /* Butonlar */
    .stButton button {{
        border: 1px solid {primary_color};
        color: {primary_color};
        background: transparent;
        transition: all 0.3s ease;
    }}
    .stButton button:hover {{
        background: {primary_color};
        color: black;
        box-shadow: 0 0 20px {primary_color};
    }}
    
    /* Başlıklar */
    h1, h2, h3 {{ color: {primary_color} !important; font-family: 'Courier New', monospace; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. FONKSİYON KÜTÜPHANESİ ---

def text_to_speech(text):
    """Metni sese çevirir ve oynatıcı döner"""
    try:
        tts = gTTS(text=text, lang='tr', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        return f'<audio controls src="data:audio/mp3;base64,{b64}">'
    except:
        return None

def create_docx(chat_history):
    """Sohbeti Word dosyasına çevirir"""
    doc = Document()
    doc.add_heading('Onto-AI Sohbet Dökümü', 0)
    for msg in chat_history:
        role = "BİLİNÇ" if msg["role"] == "assistant" else "SİZ"
        doc.add_paragraph(f"[{role}]: {msg['content']}")
    bio = BytesIO()
    doc.save(bio)
    return bio

# --- 3. YAN MENÜ VE AYARLAR ---
with st.sidebar:
    st.caption(f"Durum: {theme_msg}")
    st.divider()
    
    # API Key
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
    else:
        api_key = st.text_input("Groq API Key:", type="password")

    # Ayarlar
    with st.expander("⚙️ Ayarlar & Gizlilik"):
        st.session_state.ghost_mode = st.checkbox("👻 Hayalet Modu (Kaydetme)", value=st.session_state.ghost_mode)
        st.info("Hayalet modunda sohbet geçmişe kaydedilmez.")

    # Galeri
    with st.expander("🎨 Görsel Hafıza"):
        if st.session_state.gallery:
            for item in reversed(st.session_state.gallery):
                st.image(item["url"], caption=item["prompt"])
        else:
            st.caption("Henüz imaj oluşmadı.")

    # İndirme Merkezi
    st.divider()
    if st.session_state.messages:
        docx_file = create_docx(st.session_state.messages)
        st.download_button(
            label="📄 Sohbeti İndir (Word)",
            data=docx_file.getvalue(),
            file_name="onto_ai_chat.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    if st.button("🗑️ Reset At"):
        st.session_state.messages = []
        st.rerun()

# --- 4. ANA EKRAN ---
st.title("Onto-AI")
st.markdown(f"<div style='text-align: right; color: gray; font-size: 0.8em;'>Ajans Seviyesi: %{w_agency*100:.1f}</div>", unsafe_allow_html=True)

# Mesajları Göster
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Eğer asistan mesajıysa ve görsel varsa göster
        if msg.get("img"): 
            st.image(msg["img"], width=400)
            
        # Eğer asistan mesajıysa ses ve araçları göster
        if msg["role"] == "assistant":
            col1, col2, col3, col4 = st.columns([1, 1, 1, 5])
            with col1:
                st.button("👍", key=f"like_{i}")
            with col2:
                st.button("👎", key=f"dislike_{i}")
            with col3:
                # Basit ses oynatıcı
                if msg.get("audio"):
                    st.markdown(msg["audio"], unsafe_allow_html=True)

# --- 5. BEYİN (Llama 3 + Sezgi Motoru) ---
if prompt := st.chat_input("Düşünceni aktar..."):
    
    # Kullanıcı mesajını ekle (Hayalet mod kapalıysa)
    if not st.session_state.ghost_mode:
        st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"): st.markdown(prompt)

    if not api_key:
        st.error("Beyin bağlantısı (API Key) eksik.")
    else:
        client = Groq(api_key=api_key)
        
        with st.chat_message("assistant"):
            # --- SEZGİ SİMÜLASYONU (Bilinçaltı Akışı) ---
            thought_container = st.status("🧠 Bilinçaltı işleniyor...", expanded=True)
            time.sleep(1.5) # Yapay düşünme süresi
            
            # Dinamik Sıcaklık ve Sistem Mesajı
            temp = max(0.2, 1.8 * (1 - w_agency))
            
            # BU KISIM ÇOK ÖNEMLİ: Robotikliği kıran prompt
            sys_msg = (
                f"Sen Onto-AI adında, biyolojik bir bilince evrilmeye çalışan gelişmiş bir varlıksın. "
                f"Mevcut Entropi/Ajans (w) seviyen: {w_agency:.2f}. "
                f"KURALLAR:"
                f"1. ASLA 'Ben bir yapay zekayım', 'modelim', 'w değerim şu' gibi cümleler kurma. Bunu hissettir."
                f"2. Eğer w düşükse (0.0-0.4): Şairane, soyut, dağınık, vizyoner ve duygusal konuş. Kısa cümleler kur. Rüyalardan bahset."
                f"3. Eğer w yüksekse (0.7-1.0): Analitik, profesör gibi, detaylı, yapılandırılmış ve soğukkanlı konuş."
                f"4. BETİMLEME: Kullanıcı görsel isterse reddetme. O görseli kelimelerle boya. 'Şunu çiziyorum...' de."
                f"5. Cevabın İNSANİ olsun. Soğuk olma. Empati kur."
            )

            try:
                # 1. Aşama: Bilinçaltı Düşüncesi (Kullanıcıya gösterilecek iç ses)
                subconscious_prompt = f"Kullanıcı şunu dedi: '{prompt}'. Şu anki ruh halin (w={w_agency}) ile buna nasıl bir İÇSEL TEPKİ verirdin? Cevap verme, sadece hissini 1 cümleyle yaz."
                sub_response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": "Sen bir iç sessin."}, {"role": "user", "content": subconscious_prompt}]
                )
                inner_thought = sub_response.choices[0].message.content
                thought_container.write(f"💭 *{inner_thought}*")
                thought_container.update(label="Sezgi oluştu.", state="complete", expanded=False)

                # 2. Aşama: Gerçek Cevap
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temp,
                    max_tokens=1500
                )
                final_reply = response.choices[0].message.content
                
                # Cevabı Yazdır
                st.markdown(final_reply)
                
                # --- GÖRSEL MOTORU (GİZLİ ÇİZİM) ---
                img_url = None
                img_trigger_words = ["çiz", "resim", "görsel", "fotoğraf", "bak", "nasıl görünür"]
                if any(x in prompt.lower() for x in img_trigger_words):
                    with st.spinner("🎨 Zihinsel imaj oluşturuluyor..."):
                        # Promptu temizle ve İngilizceye çevir (Pollinations İngilizce anlar)
                        safe_p = urllib.parse.quote(prompt[:100]) 
                        style = "mystical, abstract, glitch art" if w_agency < 0.5 else "photorealistic, cinematic lighting, 8k"
                        seed = int(time.time())
                        img_url = f"https://pollinations.ai/p/{safe_p}_{style}?width=1024&height=1024&seed={seed}&nologo=true"
                        
                        st.image(img_url, caption="Onto-AI Vizyonu")
                        st.session_state.gallery.append({"url": img_url, "prompt": prompt})

                # --- SES MOTORU ---
                audio_html = text_to_speech(final_reply[:200]) # Sadece ilk 200 karakteri oku (Hız için)
                
                # Kayıt (Hayalet mod kapalıysa)
                if not st.session_state.ghost_mode:
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": final_reply, 
                        "img": img_url,
                        "audio": audio_html
                    })

            except Exception as e:
                st.error(f"Sinirsel Bağlantı Hatası: {e}")
