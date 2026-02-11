import streamlit as st
import pandas as pd
import asyncio
from playwright.async_api import async_playwright
import datetime

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Football Studio Live", page_icon="⚽", layout="centered")

# ESTILO CSS PARA AS CORES DAS CARTAS
st.markdown("""
    <style>
    .home-win { color: #ff4b4b; font-weight: bold; font-size: 24px; }
    .away-win { color: #1c83e1; font-weight: bold; font-size: 24px; }
    .draw-win { color: #fffd8d; font-weight: bold; font-size: 24px; }
    </style>
    """, unsafe_allow_stdio=True)

st.title("⚽ Football Studio Monitor")
st.subheader("Resultados em Tempo Real")

# INICIALIZAÇÃO DO HISTÓRICO
if 'dados' not in st.session_state:
    st.session_state.dados = []

# BARRA LATERAL
url_alvo = st.sidebar.text_input("URL do Jogo", "https://maxima.bet.br/pb/live-casino/home/-1/All?categoryName=all&openGames=217032-real&gameNames=Football%20Studio")
rodar_bot = st.sidebar.button("▶️ Iniciar Web App")

# ESPAÇOS NA TELA QUE VÃO MUDAR
placeholder_alerta = st.empty()
placeholder_ultimo = st.empty()
placeholder_tabela = st.empty()

async def capturar_dados():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # Roda escondido
        page = await browser.new_page()
        await page.goto(url_alvo)
        
        while True:
            try:
                # Localiza o resultado dentro do iframe da Evolution
                frame = page.frame_locator('iframe[src*="evolution"]').first
                resultado_selector = frame.locator('.stats-history-item').first
                
                if await resultado_selector.is_visible():
                    res = await resultado_selector.inner_text()
                    agora = datetime.datetime.now().strftime("%H:%M:%S")
                    
                    # Se for um resultado novo, adiciona na lista
                    novo_item = {"Hora": agora, "Vencedor": res.strip()}
                    
                    if not st.session_state.dados or st.session_state.dados[0]['Vencedor'] != res.strip():
                        st.session_state.dados.insert(0, novo_item)
                        
                        # Atualiza a Interface
                        with placeholder_ultimo:
                            st.metric(label="ÚLTIMA VITÓRIA", value=res.strip())
                        
                        with placeholder_tabela:
                            df = pd.DataFrame(st.session_state.dados).head(10)
                            st.table(df)
                
                await asyncio.sleep(4) # Espera 4 segundos para a próxima leitura
            except:
                continue

# EXECUÇÃO
if rodar_bot:
    st.sidebar.success("Bot Conectado!")
    asyncio.run(capturar_dados())
else:
    st.info("Clique no botão à esquerda para começar a monitorar.")
