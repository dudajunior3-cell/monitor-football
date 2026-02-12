import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import time

# Instalação do navegador (Silenciosa)
if "play_ready" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.play_ready = True

from playwright.async_api import async_playwright

# CONFIGURAÇÃO DO PAINEL
st.set_page_config(page_title="FOOTBALL STUDIO - ANALISADOR PRO", layout="wide")

if 'historico' not in st.session_state: st.session_state.historico = []

# --- LÓGICA DE SINAIS ---
def gerar_sinal(hist):
    if len(hist) < 3: return "ANALISANDO MESA...", "#1e293b", "Aguardando 3 rodadas..."
    u = hist[-3:]
    if all(x == 'P' for x in u): return "⚠️ ENTRAR EM AWAY (B)", "#dc2626", "Sequência de 3 Home! Entre na quebra."
    if all(x == 'B' for x in u): return "⚠️ ENTRAR EM HOME (P)", "#2563eb", "Sequência de 3 Away! Entre na quebra."
    return "✅ MONITORANDO...", "#1e293b", "Buscando padrão de entrada..."

# --- INTERFACE ---
def render_ui(hist, txt, cor, desc):
    js_h = str(hist)
    return f"""
    <div style="background:#0e1117; color:white; font-family:sans-serif; padding:20px; border-radius:15px; border:1px solid #334155; display:grid; grid-template-columns:1fr 1fr; gap:20px;">
        <div style="background:{cor}; padding:25px; border-radius:15px; text-align:center; border:2px solid white; box-shadow:0 0 20px {cor};">
            <h2 style="margin:0;">🎯 SINAL ATUAL</h2><h1 style="font-size:2.2rem;">{txt}</h1><p>{desc}</p>
        </div>
        <div style="background:#1e293b; padding:25px; border-radius:15px; text-align:center;">
            <h2 style="margin:0;">🕒 ÚLTIMOS RESULTADOS</h2><div id="h" style="margin-top:20px;"></div>
        </div>
        <script>
            const d = {js_h}.slice(-10).reverse();
            document.getElementById('h').innerHTML = d.map(x => `<span style="background:${{x=='P'?'#2563eb':x=='B'?'#dc2626':'#16a34a'}}; padding:8px 12px; border-radius:8px; margin:4px; display:inline-block; font-weight:bold;">${{x}}</span>`).join("");
        </script>
    </div>
    """

st.sidebar.title("🤖 COMANDO DO ROBÔ")
url_input = st.sidebar.text_input("Link Direto da Mesa (Evolution):")
ligar = st.sidebar.toggle("LIGAR MONITORAMENTO")

txt, cor, desc = gerar_sinal(st.session_state.historico)
components.html(render_ui(st.session_state.historico, txt, cor, desc), height=300)

# --- CAPTURA ---
async def capturar(url):
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent="Mozilla/5.0")
            await page.goto(url, timeout=60000)
            # Busca em todos os frames (Deep Scan)
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
    if res and (not st.session_state.historico or res != st.session_state.historico[-1]):
        st.session_state.historico.append(res)
        st.rerun()
    time.sleep(5)
    st.rerun()
