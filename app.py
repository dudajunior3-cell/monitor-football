import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import time

# 1. AUTO-INSTALAÇÃO DO NAVEGADOR
if "play_ready" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.play_ready = True

from playwright.async_api import async_playwright

# 2. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="FOOTBALL STUDIO - LIVE PRO 2026", layout="wide")

if 'historico' not in st.session_state: st.session_state.historico = []
if 'ultimo' not in st.session_state: st.session_state.ultimo = ""

# --- MOTOR DE ESTRATÉGIA ---
def analisar_sinal(hist):
    if len(hist) < 3: 
        return "SINCRONIZANDO...", "#1e293b", "Aguardando coletar 3 rodadas..."
    
    u = hist[-3:]
    if all(x == 'P' for x in u): return "ENTRAR EM AWAY (B)", "#dc2626", "Sequência de 3 Home! Entre na quebra."
    if all(x == 'B' for x in u): return "ENTRAR EM HOME (P)", "#2563eb", "Sequência de 3 Away! Entre na quebra."
    return "MONITORANDO...", "#1e293b", "Aguardando padrão confirmado..."

# --- INTERFACE VISUAL ---
def render_ui(hist, txt, cor, desc):
    js_h = str(hist)
    return f"""
    <div style="background:#0e1117; color:white; font-family:sans-serif; padding:15px; border-radius:15px; border:1px solid #334155; display:grid; grid-template-columns:1fr 1fr; gap:15px;">
        <div style="background:{cor}; padding:20px; border-radius:12px; text-align:center; border:2px solid white; box-shadow: 0 0 15px {cor};">
            <h2 style="margin:0; font-size:1rem;">🎯 SINAL AO VIVO</h2>
            <h1 style="margin:5px 0; font-size:1.8rem;">{txt}</h1>
            <p style="margin:0; font-size:0.8rem; opacity:0.8;">{desc}</p>
        </div>
        <div style="background:#1e293b; padding:20px; border-radius:12px; text-align:center;">
            <h2 style="margin:0; font-size:1rem;">🕒 ÚLTIMOS RESULTADOS</h2>
            <div id="h" style="margin-top:10px; font-weight:bold;"></div>
        </div>
        <script>
            const d = {js_h}.slice(-10).reverse();
            document.getElementById('h').innerHTML = d.map(x => `<span style="background:${{x=='P'?'#2563eb':x=='B'?'#dc2626':'#16a34a'}}; padding:6px 12px; border-radius:5px; margin:3px; display:inline-block; font-weight:bold;">${{x}}</span>`).join("");
        </script>
    </div>
    """

st.sidebar.title("🤖 COMANDO DO ROBÔ")
url_input = st.sidebar.text_input("Link da Mesa (Evolution):", st.session_state.get('url', 'COLE_O_LINK_AQUI'))
ligar = st.sidebar.toggle("LIGAR ANÁLISE AO VIVO")

txt, cor, desc = analisar_sinal(st.session_state.historico)
components.html(render_ui(st.session_state.historico, txt, cor, desc), height=250)

# --- CAPTURA DIRETA DO SERVIDOR ---
async def capturar_ao_vivo(url):
    async with async_playwright() as p:
        try:
            # Launcher com argumentos para evitar detecção
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
            page = await context.new_page()
            
            await page.goto(url, timeout=90000, wait_until="load")
            
            # Seletor universal para as bolinhas de histórico da Evolution
            item = page.locator('.stats-history-item, [class*="HistoryItem"], [class*="result"]').first
            await item.wait_for(state="visible", timeout=30000)
            
            res_raw = (await item.inner_text()).upper()
            await browser.close()
            
            if any(x in res_raw for x in ["H", "HOME", "C", "CASA"]): return "P"
            if any(x in res_raw for x in ["A", "AWAY", "V", "VISITANTE"]): return "B"
            return "T"
        except: return None

if ligar and url_input:
    with st.spinner("Lendo mesa direto do servidor..."):
        res = asyncio.run(capturar_ao_vivo(url_input))
        if res and res != st.session_state.ultimo:
            st.session_state.historico.append(res)
            st.session_state.ultimo = res
            st.rerun()
    
    time.sleep(5)
    st.rerun()
