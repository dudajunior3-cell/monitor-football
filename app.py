import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import time

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="PAINEL PRO - FOOTBALL STUDIO", layout="wide")

# Inicialização de Memória
if 'historico' not in st.session_state: st.session_state.historico = []
if 'ultimo_res' not in st.session_state: st.session_state.ultimo_res = ""

# --- FUNÇÃO DE INSTALAÇÃO DO MOTOR ---
def instalar_motor():
    with st.spinner("Instalando componentes do navegador (aguarde)..."):
        # Tenta instalar o chromium na nuvem
        os.system("playwright install chromium")
        st.success("Motor instalado! O app irá reiniciar.")
        time.sleep(2)
        st.rerun()

# --- LÓGICA DE SINAIS ---
def analisar_sinais(hist):
    if len(hist) < 3: return "ANALISANDO MESA...", "#1e293b", "Aguardando 3 rodadas..."
    u = hist[-3:]
    # Estratégia de Quebra de Sequência (P=Home, B=Away)
    if all(x == 'P' for x in u): return "ENTRAR EM AWAY (B)", "#dc2626", "Sequência de 3 Home! Entre na quebra."
    if all(x == 'B' for x in u): return "ENTRAR EM HOME (P)", "#2563eb", "Sequência de 3 Away! Entre na quebra."
    return "MONITORANDO...", "#1e293b", "Buscando padrões de entrada..."

# --- INTERFACE VISUAL ---
def render_ui(hist, txt, cor, desc):
    js_h = str(hist)
    return f"""
    <div style="background:#0e1117; color:white; font-family:sans-serif; padding:15px; border-radius:15px; border:1px solid #334155; display:grid; grid-template-columns:1fr 1fr; gap:15px;">
        <div style="background:{cor}; padding:20px; border-radius:12px; text-align:center; border:2px solid white; box-shadow: 0 0 15px {cor};">
            <h2 style="margin:0; font-size:1rem;">🎯 SINAL ATUAL</h2>
            <h1 style="margin:5px 0; font-size:1.8rem;">{txt}</h1>
            <p style="margin:0; font-size:0.8rem; opacity:0.8;">{desc}</p>
        </div>
        <div style="background:#1e293b; padding:20px; border-radius:12px; text-align:center;">
            <h2 style="margin:0; font-size:1rem;">🕒 ÚLTIMOS RESULTADOS</h2>
            <div id="h" style="margin-top:15px; font-weight:bold;"></div>
        </div>
        <script>
            const d = {js_h}.slice(-10).reverse();
            document.getElementById('h').innerHTML = d.map(x => `<span style="background:${{x=='P'?'#2563eb':x=='B'?'#dc2626':'#16a34a'}}; padding:5px 10px; border-radius:5px; margin:2px; display:inline-block;">${{x}}</span>`).join("");
        </script>
    </div>
    """

# --- SIDEBAR ---
st.sidebar.title("🤖 CONTROLE")
if st.sidebar.button("⚙️ INSTALAR MOTOR (CLIQUE 1 VEZ)"):
    instalar_motor()

url_input = st.sidebar.text_input("Link da Mesa (Evolution):", placeholder="Cole o link completo aqui...")
ligar = st.sidebar.toggle("LIGAR ROBÔ")

# Exibição
txt, cor, desc = analisar_sinais(st.session_state.historico)
components.html(render_ui(st.session_state.historico, txt, cor, desc), height=250)

# --- CAPTURA ---
async def capturar(url):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page(user_agent="Mozilla/5.0")
            await page.goto(url, timeout=60000)
            
            # Busca em todos os frames da página
            for frame in page.frames:
                item = frame.locator('.stats-history-item, [class*="HistoryItem"]').first
                if await item.is_visible(timeout=5000):
                    texto = (await item.inner_text()).upper()
                    await browser.close()
                    if any(x in texto for x in ["H", "HOME", "C"]): return "P"
                    if any(x in texto for x in ["A", "AWAY", "V"]): return "B"
                    return "T"
            await browser.close()
            return None
        except Exception as e:
            st.sidebar.error(f"Erro: Use o botão de Instalação.")
            return None

# Loop de Execução
if ligar and url_input:
    res = asyncio.run(capturar(url_input))
    if res and res != st.session_state.ultimo_res:
        st.session_state.historico.append(res)
        st.session_state.ultimo_res = res
        st.rerun()
    time.sleep(5)
    st.rerun()
