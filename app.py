import streamlit as st
import asyncio
import os
import time
from playwright.async_api import async_playwright

# Instalação forçada na nuvem
if "ready" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.ready = True

st.set_page_config(page_title="PRO MONITOR 2026", layout="wide")

if 'historico' not in st.session_state: st.session_state.historico = []
if 'logs' not in st.session_state: st.session_state.logs = []

def add_log(msg):
    st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    if len(st.session_state.logs) > 5: st.session_state.logs.pop(0)

# --- INTERFACE ---
st.sidebar.title("🤖 COMANDO")
url_input = st.sidebar.text_input("Link da Mesa:", placeholder="Cole o link completo aqui...")
ligar = st.sidebar.toggle("LIGAR MONITORAMENTO")

# Painel de Sinais
if st.session_state.historico:
    ultimo = st.session_state.historico[-1]
    cor = "#2563eb" if ultimo == 'P' else "#dc2626" if ultimo == 'B' else "#16a34a"
    st.markdown(f"<div style='background:{cor}; padding:20px; border-radius:10px; text-align:center;'><h2>ÚLTIMO: {ultimo}</h2></div>", unsafe_allow_html=True)
else:
    st.info("Aguardando primeira captura...")

with st.expander("🛠️ Console de Depuração", expanded=True):
    for log in st.session_state.logs: st.write(log)

# --- MOTOR DE CAPTURA ---
async def capturar_robusto(url):
    async with async_playwright() as p:
        try:
            add_log("Iniciando motor...")
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context(user_agent="Mozilla/5.0")
            page = await context.new_page()
            
            # Tenta carregar apenas o essencial do DOM
            add_log("Acessando mesa...")
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            
            # Procura em todos os frames (iframes)
            add_log("Sincronizando dados...")
            for frame in page.frames:
                try:
                    # Busca agressiva por qualquer indicador de resultado
                    item = frame.locator('.stats-history-item, [class*="HistoryItem"], [class*="result"]').first
                    if await item.is_visible(timeout=5000):
                        texto = (await item.inner_text()).upper()
                        await browser.close()
                        if any(x in texto for x in ["H", "HOME", "C"]): return "P"
                        if any(x in texto for x in ["A", "AWAY", "V"]): return "B"
                        return "T"
                except: continue
            
            await browser.close()
            return None
        except Exception as e:
            add_log(f"Erro: {str(e)[:40]}")
            return None

if ligar and url_input:
    res = asyncio.run(capturar_robusto(url_input))
    if res and (not st.session_state.historico or res != st.session_state.historico[-1]):
        st.session_state.historico.append(res)
        st.rerun()
    time.sleep(5)
    st.rerun()
