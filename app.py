import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import time

# 1. Instalação Automática do Navegador
if "play_ready" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.play_ready = True

from playwright.async_api import async_playwright

st.set_page_config(page_title="FOOTBALL STUDIO PRO", layout="wide")

if 'historico' not in st.session_state: st.session_state.historico = []

# --- INTERFACE ---
st.title("⚽ Football Studio - Monitor PRO")

def render_ui(hist):
    js_h = str(hist)
    return f"""
    <div style="background:#1e293b; padding:20px; border-radius:15px; text-align:center; color:white; font-family:sans-serif;">
        <h3>🕒 ÚLTIMOS RESULTADOS</h3>
        <div id="h" style="margin-top:10px; font-weight:bold; font-size:1.2rem;"></div>
    </div>
    <script>
        const d = {js_h}.slice(-10).reverse();
        document.getElementById('h').innerHTML = d.map(x => `<span style="background:${{x=='P'?'#2563eb':x=='B'?'#dc2626':'#16a34a'}}; padding:8px 12px; border-radius:8px; margin:4px; display:inline-block;">${{x}}</span>`).join("");
    </script>
    """

st.sidebar.title("🤖 COMANDO")
# Cole aqui o link da Evolution que começa com https://betconstructlatam.evo-games.com...
url_input = st.sidebar.text_input("Link Direto da Mesa:")
ligar = st.sidebar.toggle("LIGAR MONITORAMENTO")

components.html(render_ui(st.session_state.historico), height=150)

# --- CAPTURA ---
async def capturar(url):
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            for frame in page.frames:
                item = frame.locator('.stats-history-item, [class*="HistoryItem"]').first
                if await item.is_visible(timeout=5000):
                    texto = (await item.inner_text()).upper()
                    await browser.close()
                    if any(x in texto for x in ["H", "HOME", "C"]): return "P"
                    if any(x in texto for x in ["A", "AWAY", "V"]): return "B"
                    return "T"
            await browser.close()
            return None
        except: return None

if ligar and url_input:
    res = asyncio.run(capturar(url_input))
    if res:
        if not st.session_state.historico or res != st.session_state.historico[-1]:
            st.session_state.historico.append(res)
            st.rerun()
    time.sleep(5)
    st.rerun()
