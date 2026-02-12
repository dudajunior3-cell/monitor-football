import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import time

# Garante que o navegador seja instalado na primeira execução
if "playwright_installed" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.playwright_installed = True

from playwright.async_api import async_playwright

st.set_page_config(page_title="FOOTBALL STUDIO PRO 24H", layout="wide")

# Inicialização de Memória
if 'historico' not in st.session_state: st.session_state.historico = []
if 'ultimo_res' not in st.session_state: st.session_state.ultimo_res = ""

# --- MOTOR DE ESTRATÉGIA ---
def analisar(hist):
    if len(hist) < 3: return "ANALISANDO MESA...", "#1e293b", "Coletando dados..."
    u = hist[-3:]
    if all(x == 'P' for x in u): return "ENTRAR EM AWAY (B)", "#dc2626", "Gatilho: Quebra de 3 Home"
    if all(x == 'B' for x in u): return "ENTRAR EM HOME (P)", "#2563eb", "Gatilho: Quebra de 3 Away"
    return "AGUARDANDO PADRÃO", "#1e293b", "Monitorando tendências..."

# --- INTERFACE ---
def render_ui(hist, txt, cor, desc):
    js_h = str(hist)
    return f"""
    <div style="background:#0e1117; color:white; font-family:sans-serif; padding:15px; border-radius:15px; border:1px solid #334155; display:grid; grid-template-columns:1fr 1fr; gap:15px;">
        <div style="background:{cor}; padding:20px; border-radius:12px; text-align:center; border:2px solid white;">
            <h2 style="margin:0; font-size:1rem;">STATUS</h2><h1>{txt}</h1><p>{desc}</p>
        </div>
        <div style="background:#1e293b; padding:20px; border-radius:12px; text-align:center;">
            <h2 style="margin:0; font-size:1rem;">HISTÓRICO LIVE</h2><div id="h" style="margin-top:10px;"></div>
        </div>
        <script>
            const d = {js_h}.slice(-10).reverse();
            document.getElementById('h').innerHTML = d.map(x => `<span style="background:${{x=='P'?'#2563eb':x=='B'?'#dc2626':'#16a34a'}}; padding:5px 10px; border-radius:5px; margin:2px;">${{x}}</span>`).join("");
        </script>
    </div>
    """

st.sidebar.title("🤖 PAINEL DE COMANDO")
url_input = st.sidebar.text_input("Link Direto da Mesa:", "https://maxima.bet.br")
ligar = st.sidebar.toggle("LIGAR MONITORAMENTO 24H")

txt, cor, desc = analisar(st.session_state.historico)
components.html(render_ui(st.session_state.historico, txt, cor, desc), height=250)

# --- CAPTURA DE DADOS (MERGULHO EM IFRAMES) ---
async def capturar_site(url):
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
            page = await context.new_page()
            await page.goto(url, timeout=60000)
            
            # Varre todos os frames em busca da classe do histórico da Evolution
            for frame in page.frames:
                # Buscamos o primeiro item da lista de histórico que seja visível
                item = frame.locator('.stats-history-item, [class*="HistoryItem"], [class*="result-item"]').first
                if await item.is_visible(timeout=10000):
                    texto = (await item.inner_text()).upper()
                    await browser.close()
                    if any(x in texto for x in ["H", "HOME", "CASA", "C"]): return "P"
                    if any(x in texto for x in ["A", "AWAY", "VISITANTE", "V"]): return "B"
                    return "T"
            await browser.close()
            return None
        except: return None

if ligar:
    with st.spinner("Sincronizando..."):
        res = asyncio.run(capturar_site(url_input))
        if res and res != st.session_state.ultimo_res:
            st.session_state.historico.append(res)
            st.session_state.ultimo_res = res
            st.rerun()
    time.sleep(5)
    st.rerun()
