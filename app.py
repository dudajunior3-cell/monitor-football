import streamlit as st
import asyncio
import os
import time

# 1. AUTO-INSTALAÇÃO DO MOTOR (Playwright)
# Necessário para rodar no Streamlit Cloud sem erros de navegação
if "play_ready" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.play_ready = True

from playwright.async_api import async_playwright

# 2. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="PAINEL PRO - LOGIN AUTO", layout="wide")

# Inicialização de Memória da Sessão
if 'historico' not in st.session_state: st.session_state.historico = []
if 'logs' not in st.session_state: st.session_state.logs = []

def add_log(msg):
    # Adiciona carimbo de tempo e mantém apenas os últimos 7 logs para limpeza
    st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    if len(st.session_state.logs) > 7: st.session_state.logs.pop(0)

# --- SIDEBAR DE ACESSO ---
st.sidebar.title("🔐 ACESSO AO CASSINO")
user = st.sidebar.text_input("Usuário/E-mail:", placeholder="seuemail@gmail.com")
password = st.sidebar.text_input("Senha:", type="password")
url_base = st.sidebar.text_input("Página de Login:", "https://maxima.bet.br")
ligar = st.sidebar.toggle("INICIAR ROBÔ COM LOGIN")

# --- CONSOLE DE MONITORAMENTO ---
st.subheader("🖥️ Console do Robô (Monitoramento)")
with st.container(border=True):
    if not st.session_state.logs:
        st.write("Aguardando comando para iniciar...")
    else:
        for log in st.session_state.logs:
            st.write(log)

# --- MOTOR DE NAVEGAÇÃO E LOGIN REFORÇADO ---
async def iniciar_sessao_e_capturar(u, p, url):
    async with async_playwright() as playwright:
        try:
            add_log("🚀 Abrindo navegador furtivo...")
            # Lança o navegador com argumentos para evitar detecção e rodar em servidores cloud
            browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
            page = await context.new_page()

            add_log("🔗 Acessando site da MaximaBet...")
            await page.goto(url, timeout=60000, wait_until="networkidle")

            # LÓGICA DE LOGIN REFORÇADA
            add_log("⌨️ Tentando realizar login...")
            
            # Passo 1: Abrir o modal de login se necessário
            try:
                login_trigger = page.locator('button:has-text("Entrar"), button:has-text("Login"), .login-btn').first
                await login_trigger.click(timeout=15000)
                add_log("✅ Formulário de login detectado.")
            except:
                add_log("⚠️ Aviso: Formulário não detectado, tentando preencher campos diretamente.")

            # Passo 2: Preenchimento automático (Busca por seletores comuns)
            await page.locator('input[placeholder*="Usuário"], input[placeholder*="E-mail"], input').first.fill(u)
            await page.locator('input[placeholder*="Senha"], input[type="password"]').first.fill(p)
            
            # Passo 3: Clique no botão de submissão
            submit_btn = page.locator('button[type="submit"], button:has-text("Entrar"), .submit-button').last
            await submit_btn.click()
            
            add_log("⏳ Credenciais enviadas. Aguardando autenticação...")
            await page.wait_for_timeout(10000) # Tempo maior para processar o login e possíveis redirecionamentos

            # Passo 4: Direcionamento para o Football Studio
            add_log("🏟️ Abrindo mesa Football Studio...")
            await page.goto("https://maxima.bet.brpb/live-casino/home/-1/All?openGames=217032-real", timeout=60000)
            
            # Passo 5: Captura do Resultado dentro do Iframe da Evolution
            frame = page.frame_locator('iframe').first
            item = frame.locator('.stats-history-item, [class*="HistoryItem"], [class*="result"]').first
            await item.wait_for(state="visible", timeout=30000)
            
            res_raw = (await item.inner_text()).upper()
            add_log(f"✅ SUCESSO! Resultado na mesa: {res_raw}")
            await browser.close()
            
            # Converte para formato do painel
            if any(x in res_raw for x in ["H", "HOME", "C"]): return "P"
            if any(x in res_raw for x in ["A", "AWAY", "V"]): return "B"
            return "T"
            
        except Exception as e:
            add_log(f"❌ Erro no motor: {str(e)[:50]}...")
            return None

# --- LOOP DE EXECUÇÃO ---
# Esta parte agora está fora de qualquer função para garantir que o Streamlit a execute
if ligar:
    if not user or not password:
        st.warning("⚠️ Por favor, preencha Usuário e Senha para iniciar.")
    else:
        # Executa o motor assíncrono
        resultado = asyncio.run(iniciar_sessao_e_capturar(user, password, url_base))
        
        # Se capturou um dado novo, adiciona ao histórico
        if resultado:
            if not st.session_state.historico or resultado != st.session_state.historico[-1]:
                st.session_state.historico.append(resultado)
                # Mantém histórico limpo (últimos 50)
                if len(st.session_state.historico) > 50: st.session_state.historico.pop(0)
                st.rerun() 
        
        # Intervalo de 15 segundos entre leituras para segurança da conta
        time.sleep(15)
        st.rerun() # Reinicia o ciclo de monitoramento
