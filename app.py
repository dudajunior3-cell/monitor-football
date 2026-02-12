import streamlit as st
import os
import asyncio
import time

# Configuração da Interface
st.set_page_config(page_title="PRO MONITOR v1.0", layout="wide")

if 'historico' not in st.session_state:
    st.session_state.historico = []

st.title("⚽ Football Studio - Monitor PRO")

# BARRA LATERAL
st.sidebar.header("⚙️ Configurações")

# Passo 1: Botão para instalar o motor (Manual para não travar o deploy)
if st.sidebar.button("🚀 ATIVAR MOTOR DO ROBÔ"):
    with st.spinner("Instalando componentes do navegador..."):
        os.system("playwright install chromium")
        st.success("Motor ativado com sucesso!")

# Passo 2: Link e Controle
url_input = st.sidebar.text_input("Link da Mesa (Evolution):", placeholder="Cole o link aqui...")
ligar = st.sidebar.toggle("LIGAR MONITORAMENTO")

# PAINEL DE RESULTADOS
st.subheader("📊 Histórico em Tempo Real")
if st.session_state.historico:
    cols = st.columns(10)
    for i, res in enumerate(st.session_state.historico[-10:][::-1]):
        cor = "#2563eb" if res == 'H' else "#dc2626" if res == 'A' else "#16a34a"
        cols[i].markdown(f"<div style='background:{cor}; color:white; text-align:center; padding:15px; border-radius:10px; font-weight:bold; font-size:1.5rem;'>{res}</div>", unsafe_allow_html=True)
else:
    st.info("Aguardando ativação e link para começar a análise...")

# FUNÇÃO DE CAPTURA LEVE
async def capturar_dado(url):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page()
            await page.goto(url, timeout=45000)
            
            # Busca simples: Procura o primeiro item de histórico
            # H = Home, A = Away, T = Tie
            item = page.locator('[class*="HistoryItem"], .stats-history-item').first
            texto = (await item.inner_text()).upper()[0] # Pega apenas a primeira letra
            
            await browser.close()
            return texto if texto in ["H", "A", "T"] else None
        except:
            return None

# LOOP DE EXECUÇÃO
if ligar and url_input:
    resultado = asyncio.run(capturar_dado(url_input))
    if resultado:
        if not st.session_state.historico or resultado != st.session_state.historico[-1]:
            st.session_state.historico.append(resultado)
            if len(st.session_state.historico) > 50: st.session_state.historico.pop(0)
            st.rerun()
    
    time.sleep(5)
    st.rerun()
