import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import time

# Garante a instalação das dependências do navegador
if "installed" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.installed = True

from playwright.async_api import async_playwright

st.set_page_config(page_title="FOOTBALL STUDIO PRO - LIVE", layout="wide")

# Inicialização de Memória
if 'historico' not in st.session_state: st.session_state.historico = []
if 'ultimo_res' not in st.session_state: st.session_state.ultimo_res = ""
if 'logs' not in st.session_state: st.session_state.logs = []

def add_log(msg):
    st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    if len(st.session_state.logs) > 5: st.session_state.logs.pop(0)

# --- LÓGICA DE SINAIS ---
def analisar(hist):
    if len(hist) < 3: return "ANALISANDO MESA...", "#1e293b", "Aguardando 3 rodadas..."
    u = hist[-3:]
    if all(x == 'P' for x in u): return "ENTRAR EM AWAY (B)", "#dc2626", "Quebra de Sequência!"
    if all(x == 'B' for x in u): return "ENTRAR EM HOME (P)", "#2563eb", "Quebra de Sequência!"
    return "MONITORANDO...", "#1e293b", "Buscando padrão..."

# --- INTERFACE ---
st.sidebar.title("🤖 COMANDO DO ROBÔ")
url_input = st.sidebar.text_input("Link da Mesa (Evolution):", "https://betconstructlatam.evo-games.com...")
ligar = st.sidebar.toggle("LIGAR ANÁLISE AO VIVO")

# Exibição do Painel
txt, cor, desc = analisar(st.session_state.historico)
st.markdown(f"""
    <div style="background:{cor}; padding:20px; border-radius:15px; text-align:center; border:2px solid white;">
        <h1 style="color:white; margin:0;">{txt}</h1>
        <p style="color:white; opacity:0.8;">{desc}</p>
    </div>
""", unsafe_allow_html=True)

# Cards de Histórico
cols = st.columns(10)
for i, res in enumerate(st.session_state.historico[-10:][::-1]):
    bg = "#2563eb" if res == 'P' else "#dc2626" if res == 'B' else "#16a34a"
    cols[i].markdown(f"<div style='background:{bg}; color:white; text-align:center; border-radius:5px; padding:5px; font-weight:bold;'>{res}</div>", unsafe_allow_html=True)

# Logs de Depuração em tempo real
with st.expander("🛠️ Status do Motor (Debug)", expanded=True):
    for log in st.session_state.logs: st.write(log)

# --- MOTOR DE CAPTURA ASSÍNCRONO ---
async def capturar(url):
    async with async_playwright() as p:
        try:
            add_log("Iniciando navegador...")
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = await browser.new_context(user_agent="Mozilla/5.0")
            page = await context.new_page()
            
            add_log("Acessando link...")
            await page.goto(url, timeout=60000, wait_until="load")
            
            add_log("Buscando dados da mesa...")
            # Busca persistente (tentamos por 30 segundos encontrar qualquer classe de resultado)
            item = page.locator('.stats-history-item, [class*="HistoryItem"], [class*="result"]').first
            await item.wait_for(state="visible", timeout=30000)
            
            texto = (await item.inner_text()).upper()
            add_log(f"Sucesso! Lido: {texto}")
            await browser.close()
            
            if any(x in texto for x in ["H", "HOME", "C"]): return "P"
            if any(x in texto for x in ["A", "AWAY", "V"]): return "B"
            return "T"
        except Exception as e:
            add_log(f"Falha: {str(e)[:40]}")
            return None

if ligar:
    res = asyncio.run(capturar(url_input))
    if res and res != st.session_state.ultimo_res:
        st.session_state.historico.append(res)
        st.session_state.ultimo_res = res
        st.rerun()
    time.sleep(5)
    st.rerun()
