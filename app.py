import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import time
from playwright.async_api import async_playwright

# AUTO-INSTALAÇÃO DO MOTOR
if "motor_ready" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.motor_ready = True

st.set_page_config(page_title="FOOTWIN - PAINEL PRO", layout="wide")

# MEMÓRIA
if 'historico' not in st.session_state: st.session_state.historico = []
if 'ultimo_res' not in st.session_state: st.session_state.ultimo_res = ""

# --- LÓGICA DE SINAIS ---
def analisar_sinal(hist):
    if len(hist) < 3: return "ANALISANDO...", "#161616", "Buscando padrões em tempo real"
    u = hist[-3:]
    if all(x == 'P' for x in u): return "ENTRADA: AWAY (B)", "#891717", "Gatilho de Sequência Confirmado"
    if all(x == 'B' for x in u): return "ENTRADA: HOME (P)", "#0eabe4", "Gatilho de Sequência Confirmado"
    return "AGUARDANDO PADRÃO", "#161616", "Monitorando mesa Football Studio"

# --- INTERFACE VISUAL CLONE FOOTWIN ---
def render_ui(hist, txt, cor, desc):
    js_h = str(hist)
    return f"""
    <div style="background:#000; color:white; font-family:sans-serif; padding:10px; border-radius:20px;">
        <!-- HEADER -->
        <div style="display:flex; justify-content:space-around; background:#000; padding:10px; border-bottom:2px solid #111; margin-bottom:20px;">
            <div style="text-align:center; color:#0eabe4; border-bottom:2px solid #0eabe4; padding-bottom:5px;">🏠 Home</div>
            <div style="text-align:center; color:#555;">📺 Canais</div>
        </div>

        <!-- CARD DE SINAL -->
        <div style="background:{cor}; padding:40px; border-radius:20px; text-align:center; border:1px solid rgba(255,255,255,0.1); box-shadow: 0 10px 30px rgba(0,0,0,1);">
            <h1 style="margin:0; font-size:2rem; letter-spacing:3px;">{txt}</h1>
            <p style="margin:10px 0 0 0; opacity:0.6;">{desc}</p>
        </div>

        <!-- STATUS BAR -->
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin-top:20px;">
            <div style="background:#161616; padding:15px; border-radius:15px; text-align:center; border:1px solid #333;">
                <p style="margin:0; color:#555; font-size:0.8rem;">PADRÕES DETECTADOS</p>
                <div style="color:#0eabe4; font-weight:bold; margin-top:5px;">Ativo</div>
            </div>
            <div style="background:#161616; padding:15px; border-radius:15px; text-align:center; border:1px solid #333;">
                <p style="margin:0; color:#555; font-size:0.8rem;">ÚLTIMOS RESULTADOS</p>
                <div id="h" style="margin-top:5px;"></div>
            </div>
        </div>
        <script>
            const d = {js_h}.slice(-8).reverse();
            document.getElementById('h').innerHTML = d.map(x => `<span style="background:${{x=='P'?'#0eabe4':x=='B'?'#891717':'#16a34a'}}; padding:4px 8px; border-radius:4px; margin:2px; font-size:0.7rem;">${{x}}</span>`).join("");
        </script>
    </div>
    """

# --- SIDEBAR ---
st.sidebar.title("🎮 CONTROLE")
url_input = st.sidebar.text_input("Link da Evolution (TopCard):")
ligar = st.sidebar.toggle("LIGAR MONITORAMENTO")

# EXIBIÇÃO
txt, cor, desc = analisar_sinal(st.session_state.historico)
components.html(render_ui(st.session_state.historico, txt, cor, desc), height=450)

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
    if res and res != st.session_state.ultimo_res:
        st.session_state.historico.append(res)
        st.session_state.ultimo_res = res
        st.rerun()
    time.sleep(5)
    st.rerun()
