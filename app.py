import streamlit as st
import streamlit.components.v1 as components
import asyncio
import time
from playwright.async_api import async_playwright

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="PAINEL PRO - FOOTBALL STUDIO", layout="wide")

# Inicialização de Memória (Sessão)
for key in ['historico', 'greens', 'reds', 'ultimo_res', 'debug_log']:
    if key not in st.session_state:
        st.session_state[key] = [] if 'log' in key or 'hist' in key else 0

# --- LÓGICA DE ESTRATÉGIA ---
def analisar_sinais(hist):
    if len(hist) < 3: 
        return "ANALISANDO MESA...", "#1e293b", "Aguardando coletar 3 rodadas para validar padrão."
    
    ultimos = hist[-3:]
    
    # 1. Estratégia de Quebra de Sequência (Gale)
    if all(x == 'P' for x in ultimos): 
        return "ENTRAR EM AWAY (B)", "#dc2626", "Sequência de 3 Home detectada. Entre na QUEBRA."
    if all(x == 'B' for x in ultimos): 
        return "ENTRAR EM HOME (P)", "#2563eb", "Sequência de 3 Away detectada. Entre na QUEBRA."
    
    # 2. Alerta de Empate (Vácuo)
    if 'T' not in hist[-12:]:
        return "POSSÍVEL EMPATE (T)", "#16a34a", "Mais de 12 rodadas sem empate. Probabilidade alta!"

    return "MONITORANDO...", "#1e293b", "Padrão neutro. Aguarde um sinal de entrada confirmado."

# --- INTERFACE VISUAL PREMIUM ---
def render_html(hist, txt, cor, desc):
    js_hist = str(hist)
    return f"""
    <div style="background:#0e1117; color:white; font-family:sans-serif; padding:15px; border-radius:15px; border:1px solid #334155;">
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">
            <div style="background:{cor}; padding:20px; border-radius:12px; text-align:center; border:2px solid white; box-shadow:0 0 15px {cor};">
                <h2 style="margin:0; font-size:1.2rem;">🎯 SINAL ATUAL</h2>
                <h1 style="margin:5px 0; font-size:1.8rem;">{txt}</h1>
                <p style="margin:0; font-size:0.9rem; opacity:0.8;">{desc}</p>
            </div>
            <div style="background:#1e293b; padding:20px; border-radius:12px; text-align:center;">
                <h2 style="margin:0; font-size:1.2rem;">🕒 ÚLTIMOS RESULTADOS</h2>
                <div id="h" style="margin-top:15px; font-weight:bold; letter-spacing:3px;"></div>
            </div>
        </div>
        <script>
            const data = {js_hist}.slice(-10).reverse();
            document.getElementById('h').innerHTML = data.map(x => `<span style="background:${{x=='P'?'#2563eb':x=='B'?'#dc2626':'#16a34a'}}; padding:5px 10px; border-radius:5px; margin:2px;">${{x}}</span>`).join("");
        </script>
    </div>
    """

# --- SIDEBAR E CONFIGS ---
st.sidebar.title("🕹️ CONTROLE")
# Cole aqui o link da imagem que você me mandou
url_input = st.sidebar.text_input("Link da Mesa:", "https://maxima.bet.br")
ligar = st.sidebar.toggle("LIGAR ROBÔ AGORA")

# Exibição do Painel
txt, cor, desc = analisar_sinais(st.session_state.historico)
components.html(render_html(st.session_state.historico, txt, cor, desc), height=250)

# Logs de Debug (Aberto por padrão para você acompanhar)
with st.expander("🛠️ LOGS DE MONITORAMENTO (DEBUG)", expanded=True):
    for log in st.session_state.debug_log:
        st.write(log)

# --- CAPTURA EM TEMPO REAL ---
async def capturar_site(url):
    logs = []
    try:
        async with async_playwright() as p:
            logs.append("🚀 Iniciando navegador modo furtivo...")
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
            page = await context.new_page()
            
            logs.append("🔗 Conectando à mesa...")
            await page.goto(url, timeout=90000, wait_until="networkidle")
            
            logs.append("🔍 Localizando quadro de resultados...")
            frame = page.frame_locator('iframe').first 
            
            # Seletor otimizado para Football Studio
            item = frame.locator('.stats-history-item, [class*="HistoryItem"], [class*="result"]').first
            await item.wait_for(state="visible", timeout=45000)
            
            texto = await item.inner_text()
            logs.append(f"✅ SUCESSO! Resultado na tela: {texto}")
            await browser.close()
            
            # Converte para nosso sistema: Home(P), Away(B), Tie(T)
            if any(h in texto for h in ["H", "Home", "C", "Casa"]): return "P", logs
            if any(a in texto for a in ["A", "Away", "V", "Visitante"]): return "B", logs
            return "T", logs
    except Exception as e:
        logs.append(f"❌ ERRO: O jogo não respondeu. Verifique o link.")
        logs.append(f"Detalhe: {str(e)[:50]}")
        return None, logs

# LOOP DE EXECUÇÃO
if ligar:
    res, novos_logs = asyncio.run(capturar_site(url_input))
    st.session_state.debug_log = novos_logs
    
    if res and (not st.session_state.historico or res != st.session_state.ultimo_res):
        st.session_state.historico.append(res)
        st.session_state.ultimo_res = res
        st.rerun()
    
    time.sleep(5) # Espera 5 segundos para a próxima leitura
    st.rerun()
else:
    st.info("Ative o robô na lateral para começar a monitorar a mesa.")
