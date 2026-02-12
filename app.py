import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import time

# 1. AUTO-INSTALAÇÃO DO NAVEGADOR (Crucial para o Streamlit Cloud)
if "playwright_installed" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.playwright_installed = True

from playwright.async_api import async_playwright

# 2. CONFIGURAÇÃO DA INTERFACE
st.set_page_config(page_title="FOOTBALL STUDIO PRO - LIVE 2026", layout="wide")

if 'historico' not in st.session_state: st.session_state.historico = []
if 'ultimo_res' not in st.session_state: st.session_state.ultimo_res = ""

# --- MOTOR DE ESTRATÉGIA ---
def analisar_sinal(hist):
    if len(hist) < 3: 
        return "ANALISANDO MESA...", "#1e293b", "Aguardando coletar 3 rodadas..."
    
    ultimos = hist[-3:]
    # Estratégia de Quebra de Sequência (H=Home/P, A=Away/B)
    if all(x == 'P' for x in ultimos): return "ENTRAR EM AWAY (B)", "#dc2626", "Sequência de 3 Home! Entre na QUEBRA."
    if all(x == 'B' for x in ultimos): return "ENTRAR EM HOME (P)", "#2563eb", "Sequência de 3 Away! Entre na QUEBRA."
    
    return "MONITORANDO...", "#1e293b", "Aguardando padrão de entrada..."

# --- INTERFACE VISUAL PREMIUM ---
def render_ui(hist, txt, cor, desc):
    js_h = str(hist)
    return f"""
    <div style="background:#0e1117; color:white; font-family:sans-serif; padding:15px; border-radius:15px; border:1px solid #334155; display:grid; grid-template-columns:1fr 1fr; gap:15px;">
        <div style="background:{cor}; padding:20px; border-radius:12px; text-align:center; border:2px solid white; box-shadow: 0 0 20px {cor};">
            <h2 style="margin:0; font-size:1rem;">SINAL AO VIVO</h2>
            <h1 style="margin:5px 0; font-size:1.8rem;">{txt}</h1>
            <p style="margin:0; font-size:0.8rem; opacity:0.8;">{desc}</p>
        </div>
        <div style="background:#1e293b; padding:20px; border-radius:12px; text-align:center;">
            <h2 style="margin:0; font-size:1rem;">ÚLTIMOS RESULTADOS</h2>
            <div id="h" style="margin-top:15px; font-weight:bold;"></div>
        </div>
        <script>
            const d = {js_h}.slice(-10).reverse();
            document.getElementById('h').innerHTML = d.map(x => `<span style="background:${{x=='P'?'#2563eb':x=='B'?'#dc2626':'#16a34a'}}; padding:5px 10px; border-radius:5px; margin:2px; display:inline-block; border:1px solid rgba(255,255,255,0.1);">${{x}}</span>`).join("");
        </script>
    </div>
    """

# --- SIDEBAR DE COMANDO ---
st.sidebar.title("🤖 COMANDO DO ROBÔ")
# Link que você extraiu com o código da Evolution
url_input = st.sidebar.text_input("Link da Mesa (Evolution):", "https://maxima.bet.br")
ligar = st.sidebar.toggle("LIGAR ANÁLISE AO VIVO")

# Exibe o Painel Central
txt, cor, desc = analisar_sinal(st.session_state.historico)
components.html(render_ui(st.session_state.historico, txt, cor, desc), height=250)

# --- CAPTURA AO VIVO (MODELO EVOLUTION 2026) ---
async def capturar_ao_vivo(url):
    async with async_playwright() as p:
        try:
            # Modo furtivo para evitar detecção (Chromium)
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
            page = await context.new_page()
            
            await page.goto(url, timeout=90000, wait_until="load")
            
            # 1. AGUARDA O CARREGADOR (O loader que você enviou no HTML)
            # Ele espera a tela de carregamento sumir antes de buscar as cartas
            try:
                await page.wait_for_selector('[class*="loadingScreen"]', state="hidden", timeout=30000)
            except:
                pass # Se não achar o loader, continua
            
            # 2. BUSCA EM TODOS OS QUADROS (IFRAMES)
            for frame in page.frames:
                # Seletor universal para as bolinhas de histórico da Evolution
                item = frame.locator('[data-automation-id="history-item"], .stats-history-item, [class*="HistoryItem"]').first
                
                if await item.is_visible(timeout=10000):
                    texto = (await item.inner_text()).upper()
                    await browser.close()
                    
                    # Identificação: Home (P), Away (B) ou Tie (T)
                    if any(x in texto for x in ["H", "HOME", "C", "CASA"]): return "P"
                    if any(x in texto for x in ["A", "AWAY", "V", "VISITANTE"]): return "B"
                    return "T"
            
            await browser.close()
            return None
        except Exception as e:
            return None

# --- LOOP DE ATUALIZAÇÃO ---
if ligar:
    with st.spinner("Sincronizando com a mesa ao vivo..."):
        res = asyncio.run(capturar_ao_vivo(url_input))
        
        # Só adiciona se for uma rodada nova
        if res and res != st.session_state.ultimo_res:
            st.session_state.historico.append(res)
            st.session_state.ultimo_res = res
            if len(st.session_state.historico) > 50: st.session_state.historico.pop(0)
            st.rerun() # Atualiza a tela imediatamente
    
    time.sleep(5) # Intervalo de 5 segundos para a próxima carta
    st.rerun()
else:
    st.info("Ative o robô para iniciar a leitura dos dados ao vivo.")
