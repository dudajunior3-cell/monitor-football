import streamlit as st
import streamlit.components.v1 as components
import asyncio
import time
from playwright.async_api import async_playwright

# 1. CONFIGURAÇÃO DA INTERFACE
st.set_page_config(page_title="FOOTBALL STUDIO - LIVE PRO", layout="wide")

# Inicializa o histórico na sessão para não perder os dados
if 'historico' not in st.session_state: st.session_state.historico = []
if 'ultimo_res' not in st.session_state: st.session_state.ultimo_res = ""

# --- MOTOR DE ESTRATÉGIA ---
def analisar_sinal(hist):
    if len(hist) < 3: 
        return "ANALISANDO MESA...", "#1e293b", "Aguardando coletar 3 rodadas..."
    
    ultimos = hist[-3:]
    # Estratégia de Quebra de Sequência (P=Home, B=Away)
    if all(x == 'P' for x in ultimos): return "ENTRAR EM AWAY (B)", "#dc2626", "Sequência de 3 Home! Entre na quebra."
    if all(x == 'B' for x in ultimos): return "ENTRAR EM HOME (P)", "#2563eb", "Sequência de 3 Away! Entre na quebra."
    
    return "MONITORANDO...", "#1e293b", "Aguardando padrão confirmado..."

# --- INTERFACE VISUAL PREMIUM ---
def render_ui(hist, txt, cor, desc):
    js_h = str(hist)
    return f"""
    <div style="background:#0e1117; color:white; font-family:sans-serif; padding:15px; border-radius:15px; border:1px solid #334155; display:grid; grid-template-columns:1fr 1fr; gap:15px;">
        <div style="background:{cor}; padding:20px; border-radius:12px; text-align:center; border:2px solid white; box-shadow: 0 0 15px {cor};">
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
            document.getElementById('h').innerHTML = d.map(x => `<span style="background:${{x=='P'?'#2563eb':x=='B'?'#dc2626':'#16a34a'}}; padding:5px 10px; border-radius:5px; margin:2px; display:inline-block;">${{x}}</span>`).join("");
        </script>
    </div>
    """

# --- SIDEBAR DE COMANDO ---
st.sidebar.title("🤖 COMANDO DO ROBÔ")
# Link direto da mesa aberta (conforme seu print)
link_mesa = "https://maxima.bet.br"
url_input = st.sidebar.text_input("Link da Mesa:", link_mesa)
ligar = st.sidebar.toggle("LIGAR ANÁLISE AO VIVO")

# Exibe o Painel Central
txt, cor, desc = analisar_sinal(st.session_state.historico)
components.html(render_ui(st.session_state.historico, txt, cor, desc), height=250)

# --- CAPTURA AO VIVO (MOTOR PLAYWRIGHT) ---
async def capturar_ao_vivo(url):
    async with async_playwright() as p:
        try:
            # Iniciamos o navegador simulando um usuário real para não ser bloqueado
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
            page = await context.new_page()
            
            await page.goto(url, timeout=60000, wait_until="networkidle")
            
            # 1. A BRECHA: Procuramos o Iframe que contém 'evolution' ou 'betconstruct'
            # No Football Studio, os resultados ficam na classe '.stats-history-item'
            # ou dentro de elementos SVG que representam as cartas.
            
            for frame in page.frames:
                # Tentamos localizar o seletor universal de histórico da Evolution
                item = frame.locator('.stats-history-item, [class*="HistoryItem"], [class*="result-item"]').first
                
                if await item.is_visible(timeout=5000):
                    texto = (await item.inner_text()).upper()
                    await browser.close()
                    
                    # Normalização para o seu sistema: Home (P), Away (B) ou Tie (T)
                    if any(x in texto for x in ["H", "HOME", "CASA", "C"]): return "P"
                    if any(x in texto for x in ["A", "AWAY", "VISITANTE", "V"]): return "B"
                    return "T"
            
            await browser.close()
            return None
        except:
            return None


# --- LOOP DE ATUALIZAÇÃO ---
if ligar:
    with st.spinner("Sincronizando com a mesa..."):
        res = asyncio.run(capturar_ao_vivo(url_input))
        # Só atualiza a tela se o resultado for realmente novo
        if res and res != st.session_state.ultimo_res:
            st.session_state.historico.append(res)
            st.session_state.ultimo_res = res
            if len(st.session_state.historico) > 50: st.session_state.historico.pop(0)
            st.rerun() # Comando CRÍTICO para atualizar os cards
    
    time.sleep(5) # Espera 5 segundos para a próxima rodada
    st.rerun()
else:
    st.info("Ative o robô para iniciar a leitura dos dados ao vivo.")

