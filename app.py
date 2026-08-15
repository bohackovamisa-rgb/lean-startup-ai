import streamlit as st
import json
import re
import requests

st.set_page_config(page_title="AI Lean Startup", page_icon="🚀", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.score-box { background: linear-gradient(135deg, #0f172a, #1e293b); padding: 20px; border-radius: 12px; border: 1px solid #334155; text-align: center; color: white; margin-bottom: 20px;}
.score-value { font-size: 3.5em; font-weight: 900; background: -webkit-linear-gradient(45deg, #10b981, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.canvas-block { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; height: 100%; min-height: 160px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
.canvas-title { font-weight: 800; color: #0f172a; margin-bottom: 10px; font-size: 0.9em; text-transform: uppercase; border-bottom: 2px solid #38bdf8; padding-bottom: 5px;}
.chat-mentor { background: #f0fdf4; padding: 15px; border-radius: 12px; border-left: 5px solid #22c55e; margin-bottom: 10px; color: #0f172a; }
.chat-user { background: #f1f5f9; padding: 15px; border-radius: 12px; margin-bottom: 10px; text-align: right; color: #334155; }
.crisis-box { background: rgba(239, 68, 68, 0.1); border: 2px solid #ef4444; padding: 20px; border-radius: 12px; color: #991b1b; font-weight: 600; font-size: 1.1em;}
</style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GEMINI_API_KEY", "") or st.secrets.get("AI_API_KEY", "")

if "validation_score" not in st.session_state: st.session_state.validation_score = 0
if "canvas" not in st.session_state: 
    st.session_state.canvas = {
        "problem": "", "reseni": "", "hodnota": "", "nefer_vyhoda": "", 
        "cilovka": "", "metriky": "", "kanaly": "", "naklady": "", "prijmy": ""
    }
if "mentor_history" not in st.session_state: st.session_state.mentor_history = []
if "customer_history" not in st.session_state: st.session_state.customer_history = []
if "krize_aktivni" not in st.session_state: st.session_state.krize_aktivni = None
if "aktivni_model_nazev" not in st.session_state: st.session_state.aktivni_model_nazev = "Automatická detekce"

with st.sidebar:
    st.title("🚀 Startup Hub")
    if not api_key:
        api_key = st.text_input("Vložte API Key:", type="password")
    
    st.caption(f"Aktivní engine: `{st.session_state.aktivni_model_nazev}`")
    st.divider()
    st.markdown("### 📊 Validation Score")
    st.markdown(f"""
    <div class="score-box">
        <div style="font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px;">Ověření byznys modelu</div>
        <div class="score-value">{st.session_state.validation_score} %</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.validation_score == 0:
        st.info("Představte svůj nápad mentorovi v záložce 2.")
    elif st.session_state.validation_score < 40:
        st.warning("Fáze: Hledání Problem-Solution Fit. Ověřte problém u reálných uživatelů.")
    elif st.session_state.validation_score < 75:
        st.info("Fáze: Příprava MVP a pilotního testování.")
    else:
        st.success("Fáze: Validovaný model připravený k nasazení!")

st.title("🚀 AI Lean Startup Simulátor")

if not api_key:
    st.warning("Systém nemá nastaven API klíč. Zadejte jej v postranním panelu.")
    st.stop()

def call_ai_direct_rest(prompt_text):
    key = api_key.strip()
    
    if key.startswith("gsk_"):
        st.session_state.aktivni_model_nazev = "Groq Llama-3"
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt_text}], "temperature": 0.3},
            timeout=30
        )
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        raise Exception(f"Groq API chyba: {data}")

    elif key.startswith("sk-") and not key.startswith("sk-ant"):
        st.session_state.aktivni_model_nazev = "OpenAI GPT-4o"
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt_text}], "temperature": 0.3},
            timeout=30
        )
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        raise Exception(f"OpenAI API chyba: {data}")

    else:
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        res_list = requests.get(list_url, timeout=15).json()
        
        dostupne_modely = []
        if "models" in res_list:
            dostupne_modely = [
                m["name"] for m in res_list["models"] 
                if "generateContent" in m.get("supportedGenerationMethods", [])
            ]
        
        if not dostupne_modely:
            dostupne_modely = ["models/gemini-1.5-flash", "models/gemini-2.0-flash", "models/gemini-1.5-pro"]

        dostupne_modely.sort(key=lambda x: 0 if "flash" in x.lower() else (1 if "pro" in x.lower() else 2))

        posledni_err = None
        for m_name in dostupne_modely:
            clean_m = m_name.replace("models/", "")
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_m}:generateContent?key={key}"
            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "generationConfig": {"temperature": 0.3}
            }
            try:
                r = requests.post(endpoint, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
                res_json = r.json()
                
                if "candidates" in res_json and len(res_json["candidates"]) > 0:
                    st.session_state.aktivni_model_nazev = f"Gemini ({clean_m})"
                    return res_json["candidates"][0]["content"]["parts"][0]["text"]
                elif "error" in res_json:
                    posledni_err = res_json["error"].get("message", "Neznámá chyba")
            except Exception as e:
                posledni_err = str(e)
                continue

        raise Exception(f"Google API odmítlo všechny modely. Hlášení: {posledni_err}")

tab_canvas, tab_mentor, tab_zakaznik, tab_krize = st.tabs([
    "🧩 1. Magický Lean Canvas", "🎓 2. Lean Mentor", "🗣️ 3. Simulátor zákazníka", "🌪️ 4. Generátor krizí"
])

# ==================== TAB 1: LEAN CANVAS ====================
with tab_canvas:
    st.markdown("Plánovací nástroj synchronizovaný s výstupy z rozhovoru v záložce **Lean Mentor**.")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>1. Problém</div>{st.session_state.canvas['problem']}</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>8. Klíčové Metriky</div>{st.session_state.canvas['metriky']}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>4. Řešení (MVP)</div>{st.session_state.canvas['reseni']}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>2. Unikátní Hodnota</div>{st.session_state.canvas['hodnota']}</div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>5. Nefér Výhoda</div>{st.session_state.canvas['nefer_vyhoda']}</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>9. Prodejní Kanály</div>{st.session_state.canvas['kanaly']}</div>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>3. Cílová Skupina (Early Adopters)</div>{st.session_state.canvas['cilovka']}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col6, col7 = st.columns(2)
    with col6:
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>6. Struktura Nákladů</div>{st.session_state.canvas['naklady']}</div>", unsafe_allow_html=True)
    with col7:
        st.markdown(f"<div class='canvas-block'><div class='canvas-title'>7. Zdroje Příjmů</div>{st.session_state.canvas['prijmy']}</div>", unsafe_allow_html=True)

# ==================== TAB 2: MENTOR ====================
with tab_mentor:
    st.subheader("Konzultace s Lean Startup Mentorem")
    st.caption("Mentor analyzuje váš byznys model podle metodiky Lean Startup (Eric Ries, Steve Blank). Žádné prázdné fráze, ale věcná validace hypotéz.")
    
    for msg in st.session_state.mentor_history:
        div_class = "chat-user" if msg["role"] == "user" else "chat-mentor"
        st.markdown(f"<div class='{div_class}'><b>{'Vy' if msg['role']=='user' else 'Lean Mentor'}:</b><br>{msg['content']}</div>", unsafe_allow_html=True)
        
    with st.form("form_mentor", clear_on_submit=True):
        user_input = st.text_area("Popište svůj nápad, hypotézu nebo odpovězte mentorovi na předchozí otázky:")
        if st.form_submit_button("Odeslat mentorovi", type="primary"):
            if user_input.strip():
                st.session_state.mentor_history.append({"role": "user", "content": user_input})
                
                prompt = f"""
                Jsi zkušený, konstruktivní a věcný Lean Startup mentor a akcelerátorový partner (metodika Eric Ries / Steve Blank / Y Combinator).
                Mluvíš česky.

                TVŮJ PŘÍSTUP:
                1. Žádná agresivní klišé, žádné shazování zakladatele, žádné fráze jako "Probuďte se ze sna!".
                2. Buď věcný, analytický, profesionální partner k diskusi.
                3. Rozuměj fázím vývoje: Pokud má zakladatel funkční MVP k pilotáži, netlač ho do korporátních metrik pro 100 000 uživatelů. Soustřeď se na to, jak úspěšně spustit a vyhodnotit první pilotní testy (Early Adopters).
                4. Zhodnoť argumenty zakladatele, potvrď, co dává smysl, a polož 1-2 přesné diagnostické otázky k ověření rizik (např. nákupní proces ve škole, zapojení učitelů, přesné odlišení od stávajících zvyklostí).

                Aktuální stav Lean Canvasu: {json.dumps(st.session_state.canvas, ensure_ascii=False)}
                Aktuální skóre validace (0-100): {st.session_state.validation_score}
                Vstup od zakladatele: {user_input}

                POKYN: Odpověz VÝHRADNĚ ve validním JSON formátu bez jakýchkoliv markdown značek okolo.
                Struktura:
                {{
                    "odpoved_mentora": "Strukturovaná, věcná zpětná vazba + 1-2 přesné otázky k ověření hypotézy.",
                    "nove_skore": [Číslo 0-100 podle toho, nakolik je model ujasněný a promyšlený],
                    "canvas_updaty": {{
                        "problem": "Stručný souhrn problému",
                        "reseni": "Stručný souhrn řešení / MVP",
                        "hodnota": "Unikátní hodnota (USP)",
                        "nefer_vyhoda": "Bariéra vstupu / nefér výhoda",
                        "cilovka": "Konkrétní Early Adopters",
                        "metriky": "Klíčové metriky úspěchu pilotu",
                        "kanaly": "Jak se dostat k nákupčímu",
                        "naklady": "Hlavní nákladové položky",
                        "prijmy": "Cenový model / monetizace"
                    }}
                }}
                """
                
                with st.spinner("Mentor analyzuje byznys model..."):
                    try:
                        raw_text = call_ai_direct_rest(prompt)
                        raw_text = re.sub(r'^```json\s*', '', raw_text)
                        raw_text = re.sub(r'\s*```$', '', raw_text)
                        
                        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                        if match:
                            ai_data = json.loads(match.group(0))
                            st.session_state.mentor_history.append({"role": "mentor", "content": ai_data.get("odpoved_mentora", "Rozumím.")})
                            st.session_state.validation_score = ai_data.get("nove_skore", st.session_state.validation_score)
                            
                            new_canvas = ai_data.get("canvas_updaty", {})
                            for k in st.session_state.canvas.keys():
                                if k in new_canvas and new_canvas[k]: 
                                    st.session_state.canvas[k] = new_canvas[k]
                        else:
                            st.session_state.mentor_history.append({"role": "mentor", "content": raw_text})
                    except Exception as e:
                        st.session_state.mentor_history.append({"role": "mentor", "content": f"Chyba při zpracování: {str(e)}"})
                st.rerun()

# ==================== TAB 3: ZÁKAZNÍK ====================
with tab_zakaznik:
    st.subheader("Customer Discovery (Rozhovory nanečisto)")
    st.write("Otestujte svou hodnotovou nabídku na konkrétní personě zákazníka.")
    
    with st.container(border=True):
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1: persona_vek = st.text_input("Věk zákazníka:", value="52")
        with col_c2: persona_role = st.text_input("Povolání / Pozice:", value="Ředitel / Učitel odborné školy")
        with col_c3: persona_zajem = st.text_input("Charakteristika / Priority:", value="Konzervativní, málo času na novinky, limitovaný rozpočet")
    
    st.divider()
    for msg in st.session_state.customer_history:
        div_class = "chat-user" if msg["role"] == "user" else "chat-mentor"
        st.markdown(f"<div class='{div_class}'><b>{'Vy' if msg['role']=='user' else 'Zákazník'}:</b><br>{msg['content']}</div>", unsafe_allow_html=True)
    
    with st.form("form_customer", clear_on_submit=True):
        cust_input = st.text_area("Oslovte zákazníka nebo mu položte otevřenou otázku pro ověření problému:")
        if st.form_submit_button("Vést rozhovor", type="primary"):
            if cust_input.strip():
                st.session_state.customer_history.append({"role": "user", "content": cust_input})
                
                prompt_cust = f"""
                Hraješ roli reálného potenciálního zákazníka. Tvé parametry: Věk {persona_vek}, Pozice: {persona_role}, Vlastnosti: {persona_zajem}.
                Kontext projektu zakladatele: {json.dumps(st.session_state.canvas, ensure_ascii=False)}.
                Mluvíš česky. Reaguj autenticky a realisticky podle své role. Zajímej se o to, co ti to ušetří, kolik času tě to bude stát a jak složité je to zavést.

                Vstup od zakladatele: {cust_input}
                """
                with st.spinner("Zákazník formuluje odpověď..."):
                    try:
                        res_cust = call_ai_direct_rest(prompt_cust)
                        st.session_state.customer_history.append({"role": "customer", "content": res_cust})
                    except Exception as e:
                        st.error(f"Chyba: {e}")
                st.rerun()

# ==================== TAB 4: KRIZE ====================
with tab_krize:
    st.subheader("Black Swan (Simulace tržních rizik)")
    st.write("Vygenerujte realistickou tržní komplikaci a otestujte schopnost týmu reagovat.")
    
    if st.button("🚨 Simulovat tržní komplikaci", type="primary"):
        prompt_krize = f"""
        Kontext projektu: {json.dumps(st.session_state.canvas, ensure_ascii=False)}.
        Vymysli věcnou, vysoce realistickou tržní nebo provozní komplikaci (např. zpoždění dotačních titulů na školách, nezájem části sboru o novou metodiku, změna legislativy).
        Popiš situaci ve 2-3 větách a polož otázku na strategické řešení.
        """
        with st.spinner("Generuji krizový scénář..."):
            try:
                st.session_state.krize_aktivni = call_ai_direct_rest(prompt_krize)
            except Exception as e:
                st.error(f"Chyba: {e}")
        st.rerun()
        
    if st.session_state.krize_aktivni:
        st.markdown(f"<div class='crisis-box'>⚠️ <b>SCÉNÁŘ K ŘEŠENÍ:</b><br><br>{st.session_state.krize_aktivni}</div><br>", unsafe_allow_html=True)
        
        with st.form("form_reseni_krize"):
            reseni = st.text_area("Váš návrh řešení a mitigace rizika:")
            if st.form_submit_button("Vyhodnotit řešení"):
                if reseni.strip():
                    prompt_reseni = f"""
                    Krizová situace: {st.session_state.krize_aktivni}.
                    Navržené řešení zakladatele: {reseni}.
                    Zhodnoť věcně a realisticky, zda je toto řešení proveditelné a jaká nová rizika případně přináší. Ohodnoť 1-10 body.
                    """
                    with st.spinner("Vyhodnocuji..."):
                        try:
                            st.info(call_ai_direct_rest(prompt_reseni))
                        except Exception as e:
                            st.error(f"Chyba: {e}")
