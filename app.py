import streamlit as st
import asyncio
import os
import time

# Força a instalação do Playwright assim que o servidor ligar
if "play_ready" not in st.session_state:
    with st.spinner("Instalando motor do robô..."):
        os.system("playwright install chromium")
        st.session_state.play_ready = True

from playwright.async_api import async_playwright

st.set_page_config(page_title="PRO MONITOR 24H", layout="wide")

# Inicialização
if 'historico' not in st.session_state: st.session_state.historico = []

st.sidebar.title("🤖 COMANDO")
url_input = st.sidebar.text_input("Link da Mesa:", placeholder="Cole o link da Evolution aqui...")
ligar = st.sidebar.toggle("LIGAR MONITORAMENTO")

# Painel Simples de Resultados
st.subheader("📊 Histórico Live")
if st.session_state.historico:
    cols = st.columns(10)
    for i, res in enumerate(st.session_state.historico[-10:][::-1]):
        cor = "#2563eb" if res == 'P' else "#dc2626" if res == 'B' else "#16a34a"
        cols[i].markdown(f"<div style='background:{cor}; color:white; text-align:center; padding:10px; border-radius:10px; font-weight:bold;'>{res}</div>", unsafe_allow_html=True)
else:
    st.info("Aguardando capturar a primeira rodada...")

async def capturar(url):
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page(user_agent="Mozilla/5.0")
            await page.goto(url, timeout=60000)
            
            # Busca em todos os frames por resultados
            for frame in page.frames:
                item = frame.locator('.stats-history-item, [class*="HistoryItem"], [class*="result"]').first
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
