import streamlit as st
import google.generativeai as genai
import json
import re

st.set_page_config(page_title="AI Lean Startup", page_icon="🚀", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.score-box { background: linear-gradient(135deg, #0f172a, #1e293b); padding: 20px; border-radius: 12px; border: 1px solid #334155; text-align: center; color: white; margin-bottom: 20px;}
.score-value { font-size: 3.5em; font-weight: 900; background: -webkit-linear-gradient(45deg, #10b981, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.canvas-block { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; height: 100%; min-height: 160px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
.canvas-title { font-weight: 800; color: #0f172a; margin-bottom: 10px; font-size: 0.9em; text-transform: uppercase; border-bottom: 2px solid #38bdf8; padding-bottom: 5px;}
.chat-mentor { background: #e0f2fe; padding: 15px; border-radius: 12px; border-left: 5px solid #0284c7; margin-bottom: 10px; color: #0f172a; }
.chat-user { background: #f1f5f9; padding: 15px; border-radius: 12px; margin-bottom: 10px; text-align: right; color: #334155; }
.crisis-box { background: rgba(239, 68, 68, 0.1); border: 2px solid #ef4444; padding: 20px; border-radius: 12px; color: #991b1b; font-weight: 600; font-size: 1.1em;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# INICIALIZACE PAMĚTI
# ==========================================
if "validation_score" not in st.session_state: st.session_state.validation_score = 0
if "canvas" not in st.session_state: 
    st.session_state.canvas = {
        "problem": "", "reseni": "", "hodnota": "", "nefer_vyhoda": "", 
        "cilovka": "", "metriky": "", "kanaly": "", "naklady": "", "prijmy": ""
    }
if "mentor_history" not in st.session_state: st.session_state.mentor_history = []
if "customer_history" not in st.session_state: st.session_state.customer_history = []
if "krize_aktivni" not in st.session_state: st.session_state.krize_aktivni = None

# ==========================================
# LEVÉ MENU A API KLÍČ
# ==========================================
with st.sidebar:
    st.title("⚙️ Nastavení AI")
    api_key = st.text_input("Vložte Gemini API Key:", type="password", help="Získáte ho zdarma na aistudio.google.com")
    st.caption("Klíč se nikam neukládá, slouží jen pro tuto relaci.")
    
    st.divider()
    st.markdown("### 📊 Validation Score")
    st.markdown(f"""
    <div class="score-box">
        <div style="font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px;">Šance na úspěch</div>
        <div class="score-value">{st.session_state.validation_score} %</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.validation_score == 0:
        st.info("Představte svůj nápad mentorovi v záložce 2, aby mohl projekt ohodnotit.")
    elif st.session_state.validation_score < 30:
        st.error("Riziko krachu: Kritické! Běžte se ptát zákazníků (Záložka 3).")
    elif st.session_state.validation_score > 80:
        st.success("Tohle vypadá na Product-Market Fit! Skvělá práce.")

st.title("🚀 AI Lean Startup Simulátor")

if not api_key:
    st.info("👈 Pro spuštění aplikace vložte váš bezplatný **Google Gemini API klíč** do postranního panelu vlevo a zmáčkněte Enter.")
    st.stop()

# Připojení k AI
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Chyba při připojení k AI: {e}")
    st.stop()

tab_canvas, tab_mentor, tab_zakaznik, tab_krize = st.tabs([
    "🧩 1. Magický Lean Canvas", "🎓 2. Ďáblův advokát", "🗣️ 3. Simulátor zákazníka", "🌪️ 4. Generátor krizí"
])

# ==================== TAB 1: LEAN CANVAS ====================
with tab_canvas:
    st.markdown("Tento plánovací nástroj se vyplňuje **zcela automaticky** na základě toho, jak váš projekt probíráte s AI Mentorem v záložce 2.")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>1. Problém</div>{st.session_state.canvas['problem']}</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>8. Klíčové Metriky</div>{st.session_state.canvas['metriky']}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>4. Řešení</div>{st.session_state.canvas['reseni']}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>2. Unikátní Hodnota</div>{st.session_state.canvas['hodnota']}</div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>5. Nefér Výhoda</div>{st.session_state.canvas['nefer_vyhoda']}</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>9. Prodejní Kanály</div>{st.session_state.canvas['kanaly']}</div>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>3. Cílová Skupina</div>{st.session_state.canvas['cilovka']}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col6, col7 = st.columns(2)
    with col6:
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>6. Struktura Nákladů</div>{st.session_state.canvas['naklady']}</div>", unsafe_allow_html=True)
    with col7:
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>7. Zdroje Příjmů</div>{st.session_state.canvas['prijmy']}</div>", unsafe_allow_html=True)

# ==================== TAB 2: MENTOR ====================
with tab_mentor:
    st.subheader("Konzultace s AI Mentorem")
    st.caption("Představte svůj nápad. Mentor ho zkritizuje, najde vám reálnou konkurenci a sám na pozadí updatuje Lean Canvas!")
    
    for msg in st.session_state.mentor_history:
        div_class = "chat-user" if msg["role"] == "user" else "chat-mentor"
        st.markdown(f"<div class='{div_class}'><b>{'Vy' if msg['role']=='user' else 'Mentor'}:</b><br>{msg['content']}</div>", unsafe_allow_html=True)
        
    with st.form("form_mentor", clear_on_submit=True):
        user_input = st.text_area("Co máte v plánu budovat nebo jaký problém řešíte?")
        if st.form_submit_button("Poslat mentorovi", type="primary"):
            if user_input.strip():
                st.session_state.mentor_history.append({"role": "user", "content": user_input})
                
                prompt = f"""
                Jsi přísný, drsný, ale spravedlivý byznys mentor typu 'Ďáblův advokát' (jako investoři v Shark Tank).
                Mluvíš česky. Studenti ti představují startup. Najdi na trhu reálnou konkurenci a zeptej se jich na ni! 
                Klaď nepříjemné otázky ohledně monetizace a toho, zda to zákazníci vůbec chtějí.
                
                Aktuální Lean Canvas: {json.dumps(st.session_state.canvas, ensure_ascii=False)}
                Aktuální Skóre (0-100): {st.session_state.validation_score}
                Zpráva od studenta: {user_input}
                
                POKYN: Odpověz VÝHRADNĚ v čistém formátu JSON! Nechci žádný jiný text před ani za JSONem (ani markdown bloky ```json).
                Struktura JSONu musí být přesně takto:
                {{
                    "odpoved_mentora": "Tvá přísná odpověď...",
                    "nove_skore": 45,
                    "canvas_updaty": {{
                        "problem": "krátký text", "reseni": "krátký text", "hodnota": "krátký text",
                        "nefer_vyhoda": "krátký text", "cilovka": "krátký text", "metriky": "krátký text",
                        "kanaly": "krátký text", "naklady": "krátký text", "prijmy": "krátký text"
                    }}
                }}
                """
                
                with st.spinner("Mentor přemýšlí a analyzuje trh..."):
                    try:
                        response = model.generate_content(prompt)
                        raw_text = response.text.strip()
                        # Vyčištění textu pro jistotu, kdyby AI poslala markdown
                        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
                        
                        ai_data = json.loads(raw_text)
                        
                        st.session_state.mentor_history.append({"role": "mentor", "content": ai_data.get("odpoved_mentora", "Bez komentáře.")})
                        st.session_state.validation_score = ai_data.get("nove_skore", st.session_state.validation_score)
                        
                        new_canvas = ai_data.get("canvas_updaty", {})
                        for k in st.session_state.canvas.keys():
                            if k in new_canvas and new_canvas[k]: 
                                st.session_state.canvas[k] = new_canvas[k]
                                
                    except Exception as e:
                        st.session_state.mentor_history.append({"role": "mentor", "content": f"Omlouvám se, něco se pokazilo. Zkus to napsat znovu. (Technická chyba: {str(e)})"})
                st.rerun()

# ==================== TAB 3: ZÁKAZNÍK ====================
with tab_zakaznik:
    st.subheader("Customer Discovery (Rozhovory nanečisto)")
    st.write("Abyste si ověřili svůj nápad, musíte jít za zákazníkem. Nastavte si, s kým chcete mluvit, a zkuste mu svůj produkt prodat.")
    
    with st.container(border=True):
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1: persona_vek = st.text_input("Věk zákazníka:", value="65")
        with col_c2: persona_role = st.text_input("Povolání / Status:", value="Důchodkyně")
        with col_c3: persona_zajem = st.text_input("Problém / Charakter:", value="Nerozumí technologiím, je nedůvěřivá")
    
    st.divider()
    for msg in st.session_state.customer_history:
        div_class = "chat-user" if msg["role"] == "user" else "chat-mentor"
        st.markdown(f"<div class='{div_class}'><b>{'Vy' if msg['role']=='user' else 'Zákazník'}:</b><br>{msg['content']}</div>", unsafe_allow_html=True)
    
    with st.form("form_customer", clear_on_submit=True):
        cust_input = st.text_area("Položte zákazníkovi otázku nebo mu představte produkt:")
        if st.form_submit_button("Promluvit si se zákazníkem", type="primary"):
            if cust_input.strip():
                st.session_state.customer_history.append({"role": "user", "content": cust_input})
                
                prompt_cust = f"""
                Hraješ roli cílového zákazníka. Tvé vlastnosti: Věk {persona_vek}, Povolání: {persona_role}, Charakter: {persona_zajem}.
                Studenti se ti snaží vnutit svůj produkt (Jejich aktuální Canvas: {json.dumps(st.session_state.canvas)}).
                Mluvíš česky. Odpovídej přesně z pohledu této persony! Používej adekvátní slang nebo styl mluvy. Pokud produktu nerozumíš, buď zmatený/á. Nesouhlas hned se vším.
                
                Zpráva od studenta: {cust_input}
                """
                with st.spinner("Zákazník poslouchá..."):
                    try:
                        response_cust = model.generate_content(prompt_cust)
                        st.session_state.customer_history.append({"role": "customer", "content": response_cust.text})
                    except:
                        st.error("Chyba při komunikaci se zákazníkem.")
                st.rerun()

# ==================== TAB 4: KRIZE ====================
with tab_krize:
    st.subheader("Black Swan (Krizový management)")
    st.write("Skutečný byznys není procházka růžovým sadem. Kdykoliv může přijít událost, která vaši firmu zničí. Otestujte, jak umíte reagovat pod tlakem.")
    
    if st.button("🚨 Vygenerovat nečekanou tržní krizi!", type="primary"):
        prompt_krize = f"""
        Podívej se na tento Lean Canvas startupu: {json.dumps(st.session_state.canvas, ensure_ascii=False)}.
        Vymysli katastrofický, ale velmi realistický scénář (Black Swan událost), který právě tuto firmu potkal (např. vyhořel jim konkrétní dodavatel, stát zakázal jejich obor, konkurent je zažaloval).
        Popiš krizovou situaci max 3 větami. Mluv česky. Na konci se zeptej týmu: "Jako CEO, jaký je tvůj první krok pro záchranu firmy?"
        """
        with st.spinner("Generuji krizový scénář..."):
            try:
                response_krize = model.generate_content(prompt_krize)
                st.session_state.krize_aktivni = response_krize.text
            except:
                st.error("Nepodařilo se vygenerovat krizi.")
        
    if st.session_state.krize_aktivni:
        st.markdown(f"<div class='crisis-box'>🔥 <b>MÁTE PROBLÉM:</b><br><br>{st.session_state.krize_aktivni}</div><br>", unsafe_allow_html=True)
        
        with st.form("form_reseni_krize"):
            reseni = st.text_area("Vaše krizové řešení (Jak situaci zachráníte?):")
            if st.form_submit_button("Odeslat řešení krize"):
                if reseni.strip():
                    prompt_reseni = f"""
                    Student navrhl toto řešení krize: {reseni}.
                    Krize byla tato: {st.session_state.krize_aktivni}.
                    Zhodnoť to jako přísný krizový manažer. Fungovalo by to v realitě? Odpověz tvrdě, ale spravedlivě. A dej mu hodnocení 0-10 bodů.
                    """
                    with st.spinner("Vyhodnocuji vaše řešení..."):
                        try:
                            response_res = model.generate_content(prompt_reseni)
                            st.info(response_res.text)
                            if st.button("Ukončit krizi"):
                                st.session_state.krize_aktivni = None
                                st.rerun()
                        except:
                            st.error("Chyba při vyhodnocování.")
