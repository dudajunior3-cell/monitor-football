import streamlit as st
import streamlit.components.v1 as components
import asyncio
import time
from playwright.async_api import async_playwright

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="PAINEL PRO - FOOTBALL STUDIO", layout="wide")

# INICIALIZAÇÃO DE ESTADOS (MEMÓRIA DO ROBÔ)
if 'historico' not in st.session_state:
    st.session_state.historico = []
if 'greens' not in st.session_state:
    st.session_state.greens = 0
if 'reds' not in st.session_state:
    st.session_state.reds = 0
if 'ultimo_sinal' not in st.session_state:
    st.session_state.ultimo_sinal = None # Armazena qual foi a última sugestão

# --- MOTOR DE ESTRATÉGIA ---
def processar_estratégia(historico):
    if len(historico) < 3:
        return "ANALISANDO MESA...", "#1e293b", "Aguardando mais rodadas para validar padrão."

    ultimos = historico[-3:]
    
    # Validação de Green/Red (Verifica se o último sinal bateu)
    if st.session_state.ultimo_sinal:
        sugerido = st.session_state.ultimo_sinal
        real = historico[-1]
        if sugerido == real:
            st.session_state.greens += 1
            st.toast("✅ GREEN CONFIRMADO!", icon="💰")
        else:
            st.session_state.reds += 1
            st.toast("❌ RED DETECTADO", icon="📉")
        st.session_state.ultimo_sinal = None

    # GATILHOS DE ENTRADA
    # 1. Quebra de Sequência (3 iguais)
    if all(x == 'P' for x in ultimos):
        st.session_state.ultimo_sinal = 'B'
        return "ENTRAR EM AWAY (VERMELHO)", "#dc2626", "Sequência de 3 Home detectada. Entre na quebra."
    
    if all(x == 'B' for x in ultimos):
        st.session_state.ultimo_sinal = 'P'
        return "ENTRAR EM HOME (AZUL)", "#2563eb", "Sequência de 3 Away detectada. Entre na quebra."

    # 2. Padrão de Alternância (Xadrez)
    if len(historico) >= 4:
        u4 = historico[-4:]
        if u4 == ['P','B','P','B'] or u4 == ['B','P','B','P']:
            st.session_state.ultimo_sinal = 'P' if u4[-1] == 'B' else 'B'
            return "PADRÃO XADREZ", "#facc15", "Alternância detectada. Entre oposto à última cor."

    return "AGUARDANDO PADRÃO...", "#1e293b", "Mesa em modo neutro. Sem sinais no momento."

# --- INTERFACE HTML/CSS PREMIUM ---
def render_painel(hist, txt, cor, desc, g, r):
    js_hist = str(hist)
    win_rate = (g / (g + r) * 100) if (g + r) > 0 else 0
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin:0; font-family: 'Segoe UI', sans-serif; background: #0e1117; color:white; }}
            .container {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:15px; padding:20px; }}
            .card {{ background:#1e293b; padding:15px; border-radius:12px; border: 1px solid #334155; text-align:center; }}
            .sinal-box {{ background: {cor}; border: 2px solid white; box-shadow: 0 0 15px {cor}; animation: pulse 2s infinite; }}
            .P {{ background:#2563eb; padding:5px 10px; border-radius:5px; margin:2px; font-weight:bold; }}
            .B {{ background:#dc2626; padding:5px 10px; border-radius:5px; margin:2px; font-weight:bold; }}
            .T {{ background:#16a34a; padding:5px 10px; border-radius:5px; margin:2px; font-weight:bold; }}
            @keyframes pulse {{ 0% {{ opacity:1; }} 50% {{ opacity:0.7; }} 100% {{ opacity:1; }} }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card"><h3>💰 Assertividade</h3><h2 style="color:#22c55e">{g}G</h2><h2 style="color:#ef4444">{r}R</h2><p>{win_rate:.1f}% Win</p></div>
            <div class="card sinal-box"><h3>🎯 Sinal Atual</h3><h2 style="margin:5px 0">{txt}</h2><p>{desc}</p></div>
            <div class="card"><h3>🕒 Histórico</h3><div id="h" style="margin-top:10px"></div></div>
        </div>
        <script>
            const data = {js_hist}.slice(-12).reverse();
            document.getElementById('h').innerHTML = data.map(x => `<span class="${{x}}">${{x}}</span>`).join("");
        </script>
    </body>
    </html>
    """

# --- SIDEBAR E CONFIGS ---
st.sidebar.header("🕹️ CONTROLE DO ROBÔ")
url = st.sidebar.text_input("Link da Mesa:", "URL_DO_JOGO_AQUI")
ligar = st.sidebar.toggle("ATIVAR MONITORAMENTO")

# EXIBIÇÃO DO PAINEL
txt, cor, desc = processar_estratégia(st.session_state.historico)
components.html(render_painel(st.session_state.historico, txt, cor, desc, st.session_state.greens, st.session_state.reds), height=300)

# --- SCRAPER (CAPTURA EM TEMPO REAL) ---
async def capturar_site():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=30000)
            frame = page.frame_locator('iframe[src*="evolution"]').first
            res = await frame.locator('.stats-history-item').first.inner_text()
            await browser.close()
            if "Home" in res or "H" in res: return "P"
            if "Away" in res or "A" in res: return "B"
            if "Tie" in res or "T" in res: return "T"
        except: return None

# LOOP PRINCIPAL
if ligar:
    with st.status("Robô em campo...", expanded=False):
        novo = asyncio.run(capturar_site())
        if novo and (not st.session_state.historico or novo != st.session_state.historico[-1]):
            st.session_state.historico.append(novo)
            st.rerun()
    time.sleep(5)
    st.rerun()
else:
    st.warning("O Robô está desligado. Ative a chave na lateral.")
