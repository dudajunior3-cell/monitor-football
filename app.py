import streamlit as st
import asyncio
import os
import time
from playwright.async_api import async_playwright

# 1. Instalação do Navegador
if "play_ready" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.play_ready = True

st.set_page_config(page_title="FOOTBALL STUDIO - AUTO LOGIN", layout="wide")

# Inicialização de Memória
if 'historico' not in st.session_state: st.session_state.historico = []
if 'logs' not in st.session_state: st.session_state.logs = []

def add_log(msg):
    st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    if len(st.session_state.logs) > 5: st.session_state.logs.pop(0)

# --- SIDEBAR DE ACESSO ---
st.sidebar.title("🔐 ACESSO AO CASSINO")
user = st.sidebar.text_input("Usuário/E-mail:")
password = st.sidebar.text_input("Senha:", type="password")
url_login = st.sidebar.text_input("Página de Login:", "https://maxima.bet.br")
ligar = st.sidebar.toggle("INICIAR ROBÔ COM LOGIN")

# Painel de Status
with st.expander("🛠️ Console do Robô (Monitoramento)", expanded=True):
    for log in st.session_state.logs: st.write(log)

# --- MOTOR DE NAVEGAÇÃO E LOGIN ---
async def iniciar_sessao_e_capturar(u, p, url):
    async with async_playwright() as playwright:
        try:
            add_log("Abrindo navegador furtivo...")
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
            page = await context.new_page()

            add_log("Acessando site...")
            await page.goto(url, timeout=60000)

            # LÓGICA DE LOGIN (Ajustada para BetConstruct)
            add_log("Tentando realizar login...")
            # Clica no botão de Login se estiver visível
            await page.locator('button:has-text("Login"), .login-btn, #login-button').first.click()
            
            # Digita as credenciais nos campos (seletores comuns)
            await page.locator('input, input[name="username"]').first.fill(u)
            await page.locator('input[type="password"]').first.fill(p)
            await page.locator('button[type="submit"], .submit-btn').first.click()
            
            add_log("Aguardando autenticação...")
            await page.wait_for_timeout(5000) # Espera o login processar

            # NAVEGA PARA O JOGO
            add_log("Abrindo Football Studio...")
            # Usamos o link da mesa que você já tem
            await page.goto("https://maxima.bet.brpb/live-casino/home/-1/All?openGames=217032-real", timeout=60000)
            
            # CAPTURA DO RESULTADO
            frame = page.frame_locator('iframe').first
            item = frame.locator('.stats-history-item, [class*="HistoryItem"]').first
            await item.wait_for(state="visible", timeout=30000)
            
            res_raw = (await item.inner_text()).upper()
            add_log(f"✅ SUCESSO! Capturado: {res_raw}")
            await browser.close()
            
            if any(x in res_raw for x in ["H", "HOME", "C"]): return "P"
            if any(x in res_raw for x in ["A", "AWAY", "V"]): return "B"
            return "T"
        except Exception as e:
            add_log(f"❌ Erro: {str(e)[:40]}")
            return None

if ligar and user and password:
    resultado = asyncio.run(iniciar_sessao_e_capturar(user, password, url_login))
    if resultado:
        if not st.session_state.historico or resultado != st.session_state.historico[-1]:
            st.session_state.historico.append(resultado)
            st.rerun()
    time.sleep(10) # Intervalo maior para não sobrecarregar o login
    st.rerun()
