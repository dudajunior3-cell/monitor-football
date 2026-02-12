import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import time

# Auto-instalação do Playwright
if "playwright_installed" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.playwright_installed = True

from playwright.async_api import async_playwright

st.set_page_config(page_title="FOOTBALL STUDIO LIVE PRO", layout="wide")

if 'historico' not in st.session_state: st.session_state.historico = []
if 'ultimo_res' not in st.session_state: st.session_state.ultimo_res = ""

# --- MOTOR DE ESTRATÉGIA ---
def analisar(hist):
    if len(hist) < 3: return "ANALISANDO MESA...", "#1e293b", "Aguardando coletar 3 rodadas..."
    u = hist[-3:]
    if all(x == 'P' for x in u): return "ENTRAR EM AWAY (B)", "#dc2626", "Quebra de 3 Home!"
    if all(x == 'B' for x in u): return "ENTRAR EM HOME (P)", "#2563eb", "Quebra de 3 Away!"
    return "MONITORANDO...", "#1e293b", "Buscando padrões ao vivo..."

# --- INTERFACE ---
def render(hist, txt, cor, desc):
    js_h = str(hist)
    return f"""
    <div style="background:#0e1117; color:white; font-family:sans-serif; padding:15px; border-radius:15px; border:1px solid #334155; display:grid; grid-template-columns:1fr 1fr; gap:15px;">
        <div style="background:{cor}; padding:25px; border-radius:12px; text-align:center; border:2px solid white; box-shadow: 0 0 20px {cor};">
            <h2 style="margin:0;">SINAL LIVE</h2><h1 style="margin:10px 0;">{txt}</h1><p>{desc}</p>
        </div>
        <div style="background:#1e293b; padding:25px; border-radius:12px; text-align:center;">
            <h2 style="margin:0;">ÚLTIMOS RESULTADOS</h2><div id="h" style="margin-top:20px; font-weight:bold; font-size:1.2rem;"></div>
        </div>
        <script>
            const d = {js_h}.slice(-10).reverse();
            document.getElementById('h').innerHTML = d.map(x => `<span style="background:${{x=='P'?'#2563eb':x=='B'?'#dc2626':'#16a34a'}}; padding:8px 12px; border-radius:6px; margin:4px; display:inline-block; border:1px solid rgba(255,255,255,0.1);">${{x}}</span>`).join("");
        </script>
    </div>
    """

st.sidebar.title("🤖 COMANDO PRO")
url_input = st.sidebar.text_input("Link Direto da Mesa:", "https://maxima.bet.br")
ligar = st.sidebar.toggle("LIGAR MONITORAMENTO")

txt, cor, desc = analisar(st.session_state.historico)
components.html(render(st.session_state.historico, txt, cor, desc), height=280)

async def capturar(url):
    async with async_playwright() as p:
        try:
            # Modo super furtivo para não ser detectado pelo cassino
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
            page = await context.new_page()
            await page.goto(url, timeout=90000, wait_until="networkidle")
            
            # Busca em todos os frames por classes de resultado (H, A ou T)
            for frame in page.frames:
                item = frame.locator('.stats-history-item, [class*="HistoryItem"], [class*="result"]').first
                if await item.is_visible(timeout=10000):
                    texto = (await item.inner_text()).upper()
                    await browser.close()
                    if any(x in texto for x in ["H", "HOME", "C"]): return "P"
                    if any(x in texto for x in ["A", "AWAY", "V"]): return "B"
                    return "T"
            await browser.close()
            return None
        except: return None

if ligar:
    with st.spinner("Sincronizando com a mesa ao vivo..."):
        res = asyncio.run(capturar(url_input))
        if res and res != st.session_state.ultimo_res:
            st.session_state.historico.append(res)
            st.session_state.ultimo_res = res
            st.rerun() # Comando fundamental para atualizar os cards
    time.sleep(5)
    st.rerun()
