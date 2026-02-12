import streamlit as st
import streamlit.components.v1 as components
import asyncio
import time
from playwright.async_api import async_playwright

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FOOTBALL STUDIO - LIVE PRO", layout="wide")

# Inicialização de Memória (Estado da Sessão)
if 'historico' not in st.session_state: st.session_state.historico = []
if 'ultimo_res' not in st.session_state: st.session_state.ultimo_res = ""

# --- MOTOR DE ESTRATÉGIA ---
def analisar_sinal(hist):
    if len(hist) < 3: 
        return "ANALISANDO MESA...", "#1e293b", "Aguardando coletar 3 rodadas..."
    
    ultimos = hist[-3:]
    # Estratégia de Quebra de Sequência
    if all(x == 'P' for x in ultimos): return "ENTRAR EM AWAY (B)", "#dc2626", "Sequência de 3 Home! Entre na quebra."
    if all(x == 'B' for x in ultimos): return "ENTRAR EM HOME (P)", "#2563eb", "Sequência de 3 Away! Entre na quebra."
    
    return "MONITORANDO...", "#1e293b", "Aguardando padrão confirmado..."

# --- INTERFACE VISUAL ---
def render_ui(hist, txt, cor, desc):
    js_h = str(hist)
    return f"""
    <div style="background:#0e1117; color:white; font-family:sans-serif; padding:15px; border-radius:15px; border:1px solid #334155; display:grid; grid-template-columns:1fr 1fr; gap:15px;">
        <div style="background:{cor}; padding:20px; border-radius:12px; text-align:center; border:2px solid white;">
            <h2 style="margin:0; font-size:1rem;">SINAL AO VIVO</h2>
            <h1 style="margin:5px 0; font-size:1.8rem;">{txt}</h1>
            <p style="margin:0; font-size:0.8rem; opacity:0.8;">{desc}</p>
        </div>
        <div style="background:#1e293b; padding:20px; border-radius:12px; text-align:center;">
            <h2 style="margin:0; font-size:1rem;">ÚLTIMOS RESULTADOS</h2>
            <div id="h" style="margin-top:15px; font-weight:bold;"></div>
        </div>
        <script>
            const d = {js_h}.slice(-10).reverse();
            document.getElementById('h').innerHTML = d.map(x => `<span style="background:${{x=='P'?'#2563eb':x=='B'?'#dc2626':'#16a34a'}}; padding:5px 10px; border-radius:5px; margin:2px;">${{x}}</span>`).join("");
        </script>
    </div>
    """

# --- SIDEBAR ---
st.sidebar.title("🤖 COMANDO DO ROBÔ")
# Use o link longo que você pegou do jogo aberto
url_input = st.sidebar.text_input("Link da Mesa:", "https://maxima.bet.br")
ligar = st.sidebar.toggle("LIGAR ANÁLISE AO VIVO")

# Exibe o Painel
txt, cor, desc = analisar_sinal(st.session_state.historico)
components.html(render_ui(st.session_state.historico, txt, cor, desc), height=250)

# --- CAPTURA E ATUALIZAÇÃO ---
async def capturar_ao_vivo(url):
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent="Mozilla/5.0")
            await page.goto(url, timeout=60000)
            
            # Procura em todos os frames da página pelo resultado
            for frame in page.frames:
                item = frame.locator('[class*="history-item"], [class*="HistoryItem"], .stats-history-item').first
                if await item.is_visible(timeout=5000):
                    texto = (await item.inner_text()).upper()
                    await browser.close()
                    if any(x in texto for x in ["H", "HOME", "C"]): return "P"
                    if any(x in texto for x in ["A", "AWAY", "V"]): return "B"
                    return "T"
            await browser.close()
            return None
        except: return None

if ligar:
    with st.spinner("Lendo mesa..."):
        res = asyncio.run(capturar_ao_vivo(url_input))
        if res and res != st.session_state.ultimo_res:
            st.session_state.historico.append(res)
            st.session_state.ultimo_res = res
            st.rerun() # Força a atualização da interface
    
    time.sleep(5) # Espera 5 segundos para a próxima rodada
    st.rerun()
