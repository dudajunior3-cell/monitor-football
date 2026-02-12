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
    
    # Estratégia de Quebra de Sequência
    if all(x == 'P' for x in ultimos): 
        return "ENTRAR EM AWAY (B)", "#dc2626", "Sequência de 3 Home detectada. Entre na QUEBRA."
    if all(x == 'B' for x in ultimos): 
        return "ENTRAR EM HOME (P)", "#2563eb", "Sequência de 3 Away detectada. Entre na QUEBRA."
    
    # Alerta de Empate
    if 'T' not in hist[-12:]:
        return "POSSÍVEL EMPATE (T)", "#16a34a", "Mais de 12 rodadas sem empate. Probabilidade alta!"

    return "MONITORANDO...", "#1e293b", "Padrão neutro. Aguarde sinal confirmado."

# --- INTERFACE VISUAL ---
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

# --- SIDEBAR ---
st.sidebar.title("🕹️ CONTROLE")
# Link direto que você forneceu
url_padrao = "https://maxima.bet.br"
url_input = st.sidebar.text_input("Link da Mesa:", url_padrao)
ligar = st.sidebar.toggle("LIGAR ROBÔ AGORA")

# Exibição do Painel
txt, cor, desc = analisar_sinais(st.session_state.historico)
components.html(render_html(st.session_state.historico, txt, cor, desc), height=250)

# Debug Expander (Logs de Monitoramento)
with st.expander("🛠️ LOGS DE MONITORAMENTO", expanded=True):
    for log in st.session_state.debug_log:
        st.write(log)

# --- CAPTURA EM TEMPO REAL ---
async def capturar_site(url):
    logs = []
    try:
        async with async_playwright() as p:
            logs.append("🚀 Iniciando motor gráfico...")
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
            page = await context.new_page()
            
            logs.append("🔗 Conectando ao servidor da mesa...")
            await page.goto(url, timeout=90000, wait_until="networkidle")
            
            logs.append("🔍 Sincronizando com o histórico...")
            # Localiza o iframe do jogo
            frame = page.frame_locator('iframe').first 
            
            # Seletor aprimorado para capturar os resultados (Home, Away ou Tie)
            item = frame.locator('[class*="history"], [class*="History"], [class*="result"], .stats-history-item').first
            
            # Espera o elemento ficar visível na tela
            await item.wait_for(state="visible", timeout=45000)
            texto = await item.inner_text()
            
            logs.append(f"✅ SUCESSO! Resultado capturado.")
            await browser.close()
            
            # Normalização dos resultados para o sistema interno
            texto = texto.upper()
            if any(h in texto for h in ["H", "HOME", "C", "CASA"]): return "P", logs
            if any(a in texto for a in ["A", "AWAY", "V", "VISITANTE"]): return "B", logs
            return "T", logs
    except Exception as e:
        logs.append(f"❌ Falha na sincronização. Tentando novamente...")
        return None, logs

# LOOP DE EXECUÇÃO
if ligar:
    res, novos_logs = asyncio.run(capturar_site(url_input))
    st.session_state.debug_log = novos_logs
    
    if res and (not st.session_state.historico or res != st.session_state.ultimo_res):
        st.session_state.historico.append(res)
        st.session_state.ultimo_res = res
        st.rerun()
    
    time.sleep(5) # Intervalo entre as checagens
    st.rerun()
else:
    st.info("Ative o robô no menu lateral para iniciar.")
