import streamlit as st
import streamlit.components.v1 as components
import asyncio
import time
from playwright.async_api import async_playwright

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="PAINEL PRO - FOOTBALL STUDIO", layout="wide")

# Inicialização de Memória
if 'historico' not in st.session_state: st.session_state.historico = []
if 'ultimo_res' not in st.session_state: st.session_state.ultimo_res = ""
if 'debug_log' not in st.session_state: st.session_state.debug_log = []

# --- ESTRATÉGIA ---
def analisar(hist):
    if len(hist) < 3: return "ANALISANDO MESA...", "#1e293b", "Aguardando 3 rodadas..."
    u = hist[-3:]
    if all(x == 'P' for x in u): return "ENTRAR EM AWAY (B)", "#dc2626", "Gatilho de Sequência!"
    if all(x == 'B' for x in u): return "ENTRAR EM HOME (P)", "#2563eb", "Gatilho de Sequência!"
    return "MONITORANDO...", "#1e293b", "Buscando padrões..."

# --- INTERFACE ---
def render(hist, txt, cor, desc):
    js_h = str(hist)
    return f"""
    <div style="background:#0e1117; color:white; font-family:sans-serif; padding:15px; border-radius:15px; border:1px solid #334155; display:grid; grid-template-columns:1fr 1fr; gap:15px;">
        <div style="background:{cor}; padding:20px; border-radius:12px; text-align:center; border:2px solid white;">
            <h2 style="margin:0;">🎯 SINAL ATUAL</h2><h1 style="font-size:1.8rem;">{txt}</h1><p>{desc}</p>
        </div>
        <div style="background:#1e293b; padding:20px; border-radius:12px; text-align:center;">
            <h2 style="margin:0;">🕒 ÚLTIMOS</h2><div id="h" style="margin-top:15px; font-weight:bold;"></div>
        </div>
        <script>
            const d = {js_h}.slice(-10).reverse();
            document.getElementById('h').innerHTML = d.map(x => `<span style="background:${{x=='P'?'#2563eb':x=='B'?'#dc2626':'#16a34a'}}; padding:5px 10px; border-radius:5px; margin:2px;">${{x}}</span>`).join("");
        </script>
    </div>
    """

# --- SIDEBAR ---
st.sidebar.title("🕹️ CONTROLE")
# Link Sugerido (Mais completo)
url_padrao = "https://maxima.bet.br"
url_input = st.sidebar.text_input("Link da Mesa:", url_padrao)
ligar = st.sidebar.toggle("LIGAR ROBÔ AGORA")

txt, cor, desc = analisar(st.session_state.historico)
components.html(render(st.session_state.historico, txt, cor, desc), height=250)

with st.expander("🛠️ LOGS DE MONITORAMENTO", expanded=True):
    for log in st.session_state.debug_log: st.write(log)

# --- CAPTURA AVANÇADA ---
async def capturar(url):
    logs = ["🚀 Iniciando motor..."]
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
            page = await context.new_page()
            
            logs.append("🔗 Conectando. Aguardando site carregar...")
            await page.goto(url, timeout=60000, wait_until="networkidle")
            
            # BUSCA PROFUNDA EM TODOS OS QUADROS (IFRAMES)
            logs.append("🔍 Procurando mesa nos quadros do site...")
            for frame in page.frames:
                try:
                    # Tenta localizar o elemento de histórico por classe ou texto
                    item = frame.locator('[class*="history-item"], [class*="HistoryItem"], .stats-history-item').first
                    if await item.is_visible(timeout=3000):
                        texto = await item.inner_text()
                        t = texto.upper()
                        logs.append(f"✅ SUCESSO! Resultado: {t}")
                        await browser.close()
                        if any(x in t for x in ["H", "HOME", "C", "CASA"]): return "P", logs
                        if any(x in t for x in ["A", "AWAY", "V", "VISITANTE"]): return "B", logs
                        return "T", logs
                except: continue
            
            await browser.close()
            logs.append("❌ Falha: Mesa não detectada. Verifique o link.")
            return None, logs
    except Exception as e:
        logs.append(f"❌ Erro de conexão.")
        return None, logs

if ligar:
    res, n_logs = asyncio.run(capturar(url_input))
    st.session_state.debug_log = n_logs
    if res and (not st.session_state.historico or res != st.session_state.ultimo_res):
        st.session_state.historico.append(res)
        st.session_state.ultimo_res = res
        st.rerun()
    time.sleep(5)
    st.rerun()
