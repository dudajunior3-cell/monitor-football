import streamlit as st
import streamlit.components.v1 as components
import asyncio
import time
from playwright.async_api import async_playwright

# 1. CONFIGURAÇÃO DO PAINEL
st.set_page_config(page_title="FOOTBALL STUDIO - LIVE PRO", layout="wide")

# Inicializa as variáveis de memória para não perder o histórico ao atualizar
if 'historico' not in st.session_state: st.session_state.historico = []
if 'ultimo_res' not in st.session_state: st.session_state.ultimo_res = ""
if 'status_robo' not in st.session_state: st.session_state.status_robo = "Desconectado"

# --- MOTOR DE ESTRATÉGIA AO VIVO ---
def gerar_sinal(hist):
    if len(hist) < 3: 
        return "ANALISANDO MESA...", "#1e293b", "Aguardando coletar 3 rodadas..."
    
    ultimos = hist[-3:]
    # Estratégia de Quebra de Sequência (Gale 1)
    if all(x == 'P' for x in ultimos): 
        return "ENTRAR EM AWAY (B)", "#dc2626", "Sequência de 3 Home! Entre na quebra."
    if all(x == 'B' for x in ultimos): 
        return "ENTRAR EM HOME (P)", "#2563eb", "Sequência de 3 Away! Entre na quebra."
    
    # Alerta de Empate Imite
    if 'T' not in hist[-12:]:
        return "POSSÍVEL EMPATE (T)", "#16a34a", "Alerta: Mesa há muito tempo sem empate!"

    return "MONITORANDO...", "#1e293b", "Padrão neutro. Aguarde a próxima rodada."

# --- INTERFACE HTML PREMIUM ---
def renderizar_ui(hist, sinal, cor, desc):
    js_hist = str(hist)
    return f"""
    <div style="background:#0e1117; color:white; font-family:sans-serif; padding:15px; border-radius:15px; border:1px solid #334155;">
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">
            <div style="background:{cor}; padding:25px; border-radius:12px; text-align:center; border:2px solid white; box-shadow:0 0 20px {cor};">
                <h2 style="margin:0; font-size:1.1rem;">SINAL AO VIVO</h2>
                <h1 style="margin:10px 0; font-size:2rem;">{sinal}</h1>
                <p style="margin:0; font-size:0.9rem; opacity:0.8;">{desc}</p>
            </div>
            <div style="background:#1e293b; padding:25px; border-radius:12px; text-align:center;">
                <h2 style="margin:0; font-size:1.1rem;">ÚLTIMOS RESULTADOS</h2>
                <div id="lista" style="margin-top:20px; font-weight:bold; font-size:1.2rem;"></div>
            </div>
        </div>
        <script>
            const r = {js_hist}.slice(-10).reverse();
            document.getElementById('lista').innerHTML = r.map(x => 
                `<span style="background:${{x=='P'?'#2563eb':x=='B'?'#dc2626':'#16a34a'}}; padding:8px 12px; border-radius:6px; margin:3px; border:1px solid rgba(255,255,255,0.2);">${{x}}</span>`
            ).join("");
        </script>
    </div>
    """

# --- SIDEBAR DE CONTROLE ---
st.sidebar.title("🤖 COMANDO DO ROBÔ")
url_mesa = st.sidebar.text_input("Link da Mesa (Copie do navegador):", "https://maxima.bet.br")
ativar = st.sidebar.toggle("LIGAR ANÁLISE AO VIVO")

# Exibe o Painel
sinal_txt, sinal_cor, sinal_desc = gerar_sinal(st.session_state.historico)
components.html(renderizar_ui(st.session_state.historico, sinal_txt, sinal_cor, sinal_desc), height=280)

st.write(f"**Status do Robô:** {st.session_state.status_robo}")

# --- FUNÇÃO DE CAPTURA EM TEMPO REAL ---
async def capturar_dados_live(url):
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = await context.new_page()
            
            await page.goto(url, timeout=60000, wait_until="load")
            
            # Tenta encontrar o histórico em qualquer frame disponível (Deep Search)
            frame = None
            for f in page.frames:
                if await f.locator('.stats-history-item, [class*="HistoryItem"]').first.is_visible(timeout=5000):
                    frame = f
                    break
            
            if not frame: return None
            
            # Pega o primeiro item do histórico (a carta que acabou de sair)
            elemento = frame.locator('.stats-history-item, [class*="HistoryItem"]').first
            texto = (await elemento.inner_text()).upper()
            await browser.close()
            
            if any(x in texto for x in ["H", "HOME", "C"]): return "P"
            if any(x in texto for x in ["A", "AWAY", "V"]): return "B"
            return "T"
        except:
            return None

# --- LOOP DE MONITORAMENTO ---
if ativar:
    st.session_state.status_robo = "🟢 MONITORANDO MESA..."
    resultado = asyncio.run(capturar_dados_live(url_mesa))
    
    if resultado:
        # Só adiciona se for uma rodada nova para não repetir o sinal
        if not st.session_state.historico or resultado != st.session_state.ultimo_res:
            st.session_state.historico.append(resultado)
            st.session_state.ultimo_res = resultado
            if len(st.session_state.historico) > 100: st.session_state.historico.pop(0)
            st.rerun()
    
    time.sleep(4) # Intervalo curto para análise "ao vivo"
    st.rerun()
else:
    st.session_state.status_robo = "🔴 DESLIGADO"
    st.info("Ative o robô na lateral para iniciar a análise em tempo real.")
