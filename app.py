import streamlit as st
import asyncio
import os
import time
from playwright.async_api import async_playwright

# 1. Instalação Automática (Para rodar 24h na nuvem)
if "ready" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.ready = True

st.set_page_config(page_title="PRO MONITOR 2026", layout="wide")

if 'historico' not in st.session_state: st.session_state.historico = []

# --- INTERFACE ---
st.sidebar.title("🤖 COMANDO")
# Cole o link INTEIRO aqui (aquele que termina em &app=)
url_input = st.sidebar.text_input("Link da Mesa (Evolution):")
ligar = st.sidebar.toggle("LIGAR MONITORAMENTO")

# Painel de Resultados
st.subheader("📊 Histórico Live")
if st.session_state.historico:
    cols = st.columns(10)
    for i, res in enumerate(st.session_state.historico[-10:][::-1]):
        cor = "#2563eb" if res == 'P' else "#dc2626" if res == 'B' else "#16a34a"
        cols[i].markdown(f"<div style='background:{cor}; color:white; text-align:center; padding:10px; border-radius:10px; font-weight:bold;'>{res}</div>", unsafe_allow_html=True)
else:
    st.info("Aguardando capturar a primeira rodada... Certifique-se de que o link está completo.")

# --- MOTOR DE CAPTURA ROBUSTO ---
async def capturar(url):
    async with async_playwright() as p:
        try:
            # Modo furtivo para evitar bloqueios na nuvem
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
            page = await context.new_page()
            
            # Aumentamos o tempo para 90 segundos devido à lentidão da nuvem
            await page.goto(url, timeout=90000, wait_until="load")
            
            # Busca em todos os frames por qualquer indicador de resultado (H, A ou T)
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
        except:
            return None

# Loop de Execução
if ligar and url_input:
    with st.spinner("Sincronizando com a mesa..."):
        res = asyncio.run(capturar(url_input))
        if res and (not st.session_state.historico or res != st.session_state.historico[-1]):
            st.session_state.historico.append(res)
            st.rerun() # Atualiza a tela com o novo resultado
    time.sleep(5)
    st.rerun()
