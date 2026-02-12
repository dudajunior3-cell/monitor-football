import streamlit as st
import asyncio
import os
import time

# 1. AUTO-INSTALAÇÃO DO MOTOR (Playwright)
if "play_ready" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.play_ready = True

from playwright.async_api import async_playwright

# 2. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="PAINEL PRO - LOGIN AUTO", layout="wide")

# Inicialização de Memória
if 'historico' not in st.session_state: st.session_state.historico = []
if 'logs' not in st.session_state: st.session_state.logs = []

def add_log(msg):
    st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    if len(st.session_state.logs) > 6: st.session_state.logs.pop(0)

# --- SIDEBAR DE ACESSO ---
st.sidebar.title("🔐 ACESSO AO CASSINO")
user = st.sidebar.text_input("Usuário/E-mail:", placeholder="seuemail@gmail.com")
password = st.sidebar.text_input("Senha:", type="password")
url_base = st.sidebar.text_input("Página de Login:", "https://maxima.bet.br")
ligar = st.sidebar.toggle("INICIAR ROBÔ COM LOGIN")

# Exibição do Console de Monitoramento
st.subheader("🖥️ Console do Robô (Monitoramento)")
with st.container(border=True):
    if not st.session_state.logs:
        st.write("Aguardando comando para iniciar...")
    for log in st.session_state.logs:
        st.write(log)

# --- MOTOR DE NAVEGAÇÃO E LOGIN REFORÇADO ---
async def iniciar_sessao_e_capturar(u, p, url):
    async with async_playwright() as playwright:
        try:
            add_log("Abrindo navegador furtivo...")
            browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
            page = await context.new_page()

            add_log("Acessando site...")
            await page.goto(url, timeout=60000, wait_until="networkidle")

            # LÓGICA DE LOGIN REFORÇADA
            add_log("Tentando realizar login...")
            
            # Passo 1: Clicar no botão que abre o formulário
            try:
                login_trigger = page.locator('button:has-text("Entrar"), button:has-text("Login"), .login-btn').first
                await login_trigger.click(timeout=15000)
                add_log("Formulário de login detectado.")
            except:
                add_log("Aviso: Tentando preencher campos diretamente.")

            # Passo 2: Preencher Usuário e Senha (Busca por Placeholder)
            await page.locator('input[placeholder*="Usuário"], input[placeholder*="E-mail"], input').first.fill(u)
            await page.locator('input[placeholder*="Senha"], input[type="password"]').first.fill(p)
            
            # Passo 3: Clicar no botão de submissão final
            submit_btn = page.locator('button[type="submit"], button:has-text("Entrar"), .submit-button').last
            await submit_btn.click()
            
            add_log("Credenciais enviadas. Aguardando autenticação...")
            await page.wait_for_timeout(7000) # Tempo para processar o login

            # Passo 4: Ir para a mesa do jogo
            add_log("Abrindo Football Studio...")
            await page.goto("https://maxima.bet.brpb/live-casino/home/-1/All?openGames=217032-real", timeout=60000)
            
            # Passo 5: Captura do Resultado dentro do Iframe
            frame = page.frame_locator('iframe').first
            item = frame.locator('.stats-history-item, [class*="HistoryItem"], [class*="result"]').first
            await item.wait_for(state="visible", timeout=30000)
            
            res_raw = (await item.inner_text()).upper()
            add_log(f"✅ SUCESSO! Resultado: {res_raw}")
            await browser.close()
            
            # Conversão para o Painel
            if any(x in res_raw for x in ["H", "HOME", "C"]): return "P"
            if any(x in res_raw for x in ["A", "AWAY", "V"]): return "B"
            return "T"
            
        except Exception as e:
            add_log(f"❌ Erro: {str(e)[:50]}...")
            return None

# --- LOOP DE EXECUÇÃO ---
if ligar and user and password:
    resultado = asyncio.run(iniciar_sessao_e_capturar(user, password, url_base))
    if resultado:
        if not st.session_state.historico or resultado != st.session_state.historico[-1]:
            st.session_state.historico.append(resultado)
            st.rerun()
    
    # Intervalo de 15 segundos para segurança da conta
    time.sleep(15)
    st.rerun()
