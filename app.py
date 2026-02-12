import streamlit as st
import streamlit.components.v1 as components
import asyncio
import time
from playwright.async_api import async_playwright

st.set_page_config(page_title="PAINEL PRO - DEBUG MODE", layout="wide")

# Inicialização de Memória
for key in ['historico', 'greens', 'reds', 'ultimo_res', 'debug_log']:
    if key not in st.session_state:
        st.session_state[key] = [] if 'log' in key or 'hist' in key else 0

# --- LÓGICA DE SINAIS (Simplificada para teste) ---
def analisar_sinais(hist):
    if len(hist) < 3: return "ANALISANDO...", "#1e293b", "Aguardando mais dados."
    ultimos = hist[-3:]
    if all(x == 'P' for x in ultimos): return "ENTRAR EM AWAY (B)", "#dc2626", "Sequência detectada!"
    if all(x == 'B' for x in ultimos): return "ENTRAR EM HOME (P)", "#2563eb", "Sequência detectada!"
    return "AGUARDANDO...", "#1e293b", "Monitorando padrões..."

# --- CAPTURA COM TRATAMENTO DE ERROS ---
async def capturar_com_debug(url):
    logs = []
    try:
        async with async_playwright() as p:
            logs.append("🚀 Iniciando navegador...")
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
            page = await context.new_page()
            
            logs.append(f"🔗 Acessando: {url[:30]}...")
            await page.goto(url, timeout=45000, wait_until="networkidle")
            
            logs.append("🔍 Procurando frame da Evolution...")
            frame_handle = page.frame_locator('iframe[src*="evolution"]').first
            
            # Tenta encontrar o elemento de resultado
            logs.append("⏳ Aguardando resultado na mesa...")
            item = frame_handle.locator('.stats-history-item').first
            await item.wait_for(state="visible", timeout=15000)
            
            texto = await item.inner_text()
            logs.append(f"✅ Capturado com sucesso: {texto}")
            await browser.close()
            
            if "Home" in texto or "H" in texto: return "P", logs
            if "Away" in texto or "A" in texto: return "B", logs
            return "T", logs
    except Exception as e:
        logs.append(f"❌ ERRO: {str(e)}")
        return None, logs

# --- INTERFACE ---
st.sidebar.title("CONTROLE")
url_input = st.sidebar.text_input("Link da Mesa:", "COLE_A_URL_AQUI")
ligar = st.sidebar.toggle("LIGAR ROBÔ")

# Renderização do Painel (Mesmo estilo anterior)
txt, cor, desc = analisar_sinais(st.session_state.historico)
st.markdown(f"<div style='background:{cor}; padding:20px; border-radius:10px; text-align:center;'><h2>{txt}</h2><p>{desc}</p></div>", unsafe_allow_html=True)

# Exibição dos Logs de Depuração (Para você saber onde trava)
with st.expander("🛠️ Ver Logs do Robô (Debug)", expanded=True):
    for log in st.session_state.debug_log:
        st.write(log)

if ligar:
    res, novos_logs = asyncio.run(capturar_com_debug(url_input))
    st.session_state.debug_log = novos_logs
    
    if res and (not st.session_state.historico or res != st.session_state.ultimo_res):
        st.session_state.historico.append(res)
        st.session_state.ultimo_res = res
        st.rerun()
    
    time.sleep(5)
    st.rerun()
