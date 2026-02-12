import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import time

# 1. Instalação Automática (Para rodar 24h na nuvem)
if "play_ready" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.play_ready = True

from playwright.async_api import async_playwright

# 2. Configurações Visuais
st.set_page_config(page_title="PRO PANEL - LIVE MONITOR", layout="wide")

if 'historico' not in st.session_state: st.session_state.historico = []
if 'ultimo' not in st.session_state: st.session_state.ultimo = ""

# --- MOTOR DE ANÁLISE ---
def gerar_sinal(hist):
    if len(hist) < 3: return "SINCRONIZANDO...", "#1e293b", "Aguardando primeiras rodadas..."
    u = hist[-3:]
    if all(x == 'P' for x in u): return "ENTRAR EM AWAY", "#dc2626", "Quebra de 3 Home detectada!"
    if all(x == 'B' for x in u): return "ENTRAR EM HOME", "#2563eb", "Quebra de 3 Away detectada!"
    return "MONITORANDO...", "#1e293b", "Aguardando sinal de entrada..."

# --- INTERFACE ---
def render_ui(hist, txt, cor, desc):
    js_h = str(hist)
    return f"""
    <div style="background:#0e1117; color:white; font-family:sans-serif; padding:15px; border-radius:15px; border:1px solid #334155; display:grid; grid-template-columns:1fr 1fr; gap:15px;">
        <div style="background:{cor}; padding:20px; border-radius:12px; text-align:center; border:2px solid white; box-shadow:0 0 15px {cor};">
            <h2 style="margin:0;">🎯 SINAL AO VIVO</h2><h1>{txt}</h1><p>{desc}</p>
        </div>
        <div style="background:#1e293b; padding:20px; border-radius:12px; text-align:center;">
            <h2 style="margin:0;">🕒 HISTÓRICO</h2><div id="h" style="margin-top:10px;"></div>
        </div>
        <script>
            const d = {js_h}.slice(-10).reverse();
            document.getElementById('h').innerHTML = d.map(x => `<span style="background:${{x=='P'?'#2563eb':x=='B'?'#dc2626':'#16a34a'}}; padding:6px 12px; border-radius:5px; margin:3px; display:inline-block; font-weight:bold;">${{x}}</span>`).join("");
        </script>
    </div>
    """

# --- SIDEBAR ---
st.sidebar.title("🤖 COMANDO")
# Cole aqui o link que você me mandou
url_input = st.sidebar.text_input("Link da Mesa:", "https://betconstructlatam.evo-games.com/frontend/evo/r2/#provider=evolution&EVOSESSIONID=trbqoj5z3xjsn3uhtri4o565rdvwalxu987257e449c90275ff0a1479ffc95f09b27f98aeeb0cc857&locale=pt-BR&ua_launch_id=18937ed9e3e1234391d73513&cdn=https%3A%2F%2Fstatic.egcdn.com&lang=bp&game=topcard&table_id=TopCard000000001&app=")
ligar = st.sidebar.toggle("ATIVAR LEITURA 24H")

txt, cor, desc = gerar_sinal(st.session_state.historico)
components.html(render_ui(st.session_state.historico, txt, cor, desc), height=250)

# --- CAPTURA DE DADOS (MOTOR EVO-R2) ---
async def capturar(url):
    async with async_playwright() as p:
        try:
            # Modo furtivo para não ser detectado
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context(user_agent="Mozilla/5.0")
            page = await context.new_page()
            await page.goto(url, timeout=60000)
            
            # Localiza o seletor exato do histórico na versão r2 da Evolution
            # Busca pela classe 'stats-history-item' que é o padrão 2026
            item = page.locator('.stats-history-item, [class*="HistoryItem"], [class*="result"]').first
            await item.wait_for(state="visible", timeout=30000)
            
            res_raw = (await item.inner_text()).upper()
            await browser.close()
            
            if any(x in res_raw for x in ["H", "HOME", "C"]): return "P"
            if any(x in res_raw for x in ["A", "AWAY", "V"]): return "B"
            return "T"
        except: return None

if ligar:
    with st.spinner("Lendo mesa..."):
        res = asyncio.run(capturar(url_input))
        if res and res != st.session_state.ultimo:
            st.session_state.historico.append(res)
            st.session_state.ultimo = res
            st.rerun()
    time.sleep(5)
    st.rerun()
