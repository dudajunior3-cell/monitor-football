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
st.set_page_config(page_title="FOOTBALL STUDIO - LIVE PRO", layout="wide")

if 'historico' not in st.session_state: st.session_state.historico = []
if 'ultimo' not in st.session_state: st.session_state.ultimo = ""

# --- MOTOR DE ESTRATÉGIA ---
def analisar_sinal(hist):
    if len(hist) < 3: 
        return "ANALISANDO MESA...", "#1e293b", "Aguardando coletar 3 rodadas..."
    
    u = hist[-3:]
    # Estratégia de Quebra de Sequência (P=Home, B=Away)
    if all(x == 'P' for x in u): return "ENTRAR EM AWAY (B)", "#dc2626", "Sequência de 3 Home! Entre na quebra."
    if all(x == 'B' for x in u): return "ENTRAR EM HOME (P)", "#2563eb", "Sequência de 3 Away! Entre na quebra."
    
    return "MONITORANDO...", "#1e293b", "Aguardando padrão confirmado..."

# --- INTERFACE VISUAL PREMIUM ---
def render_ui(hist, txt, cor, desc):
    js_h = str(hist)
    return f"""
    <div style="background:#0e1117; color:white; font-family:sans-serif; padding:15px; border-radius:15px; border:1px solid #334155; display:grid; grid-template-columns:1fr 1fr; gap:15px;">
        <div style="background:{cor}; padding:20px; border-radius:12px; text-align:center; border:2px solid white; box-shadow: 0 0 15px {cor};">
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
            document.getElementById('h').innerHTML = d.map(x => `<span style="background:${{x=='P'?'#2563eb':x=='B'?'#dc2626':'#16a34a'}}; padding:5px 10px; border-radius:5px; margin:2px; display:inline-block;">${{x}}</span>`).join("");
        </script>
    </div>
    """

# --- SIDEBAR DE COMANDO ---
st.sidebar.title("🤖 COMANDO DO ROBÔ")
# Cole aqui o link direto que você me mandou
link_direto = "https://betconstructlatam.evo-games.com/frontend/evo/r2/#provider=evolution&EVOSESSIONID=trbqoj5z3xjsn3uhtri4o565rdvwalxu987257e449c90275ff0a1479ffc95f09b27f98aeeb0cc857&locale=pt-BR&ua_launch_id=18937ed9e3e1234391d73513&cdn=https%3A%2F%2Fstatic.egcdn.com&lang=bp&game=topcard&table_id=TopCard000000001&app="
url_input = st.sidebar.text_input("Link da Mesa (Evolution):", link_direto)
ligar = st.sidebar.toggle("LIGAR ANÁLISE AO VIVO")

# Exibe o Painel Central
txt, cor, desc = analisar_sinal(st.session_state.historico)
components.html(render_ui(st.session_state.historico, txt, cor, desc), height=250)

# --- CAPTURA DIRETA (SEM IFRAME) ---
async def capturar_ao_vivo(url):
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0")
            page = await context.new_page()
            await page.goto(url, timeout=60000, wait_until="load")
            
            # Como o link é direto, não precisamos buscar por frames! 
            # Lemos o elemento de histórico da Evolution R2 diretamente.
            item = page.locator('.stats-history-item, [class*="HistoryItem"], [class*="result"]').first
            await item.wait_for(state="visible", timeout=30000)
            
            texto = (await item.inner_text()).upper()
            await browser.close()
            
            if any(x in texto for x in ["H", "HOME", "C", "CASA"]): return "P"
            if any(x in texto for x in ["A", "AWAY", "V", "VISITANTE"]): return "B"
            return "T"
        except: return None

# --- LOOP DE ATUALIZAÇÃO ---
if ligar:
    with st.spinner("Sincronizando..."):
        res = asyncio.run(capturar_ao_vivo(url_input))
        if res and res != st.session_state.ultimo:
            st.session_state.historico.append(res)
            st.session_state.ultimo = res
            if len(st.session_state.historico) > 50: st.session_state.historico.pop(0)
            st.rerun() # Atualiza os cards pretos imediatamente
    
    time.sleep(5)
    st.rerun()
else:
    st.info("Ative o robô para iniciar a leitura dos dados direto do servidor.")
