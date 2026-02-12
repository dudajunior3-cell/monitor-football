import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import time
from playwright.async_api import async_playwright

# 1. AUTO-INSTALAÇÃO DO MOTOR
if "motor_pronto" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.motor_pronto = True

# 2. CONFIGURAÇÃO DA PÁGINA (ESTILO FOOTWIN)
st.set_page_config(page_title="FOOTWIN CLONE - MONITOR PRO", layout="wide")

# Inicialização de Memória
for key in ['historico', 'greens', 'reds', 'ultimo_res']:
    if key not in st.session_state:
        st.session_state[key] = [] if 'historico' in key else (0 if key in ['greens', 'reds'] else "")

# --- LÓGICA DE ASSERTIVIDADE ---
def calcular_stats(hist):
    if len(hist) < 3: return "ANALISANDO...", "#161616", "Buscando padrões..."
    u = hist[-3:]
    # Estratégia de Quebra (Simulando a da plataforma)
    if all(x == 'P' for x in u): return "ENTRADA CONFIRMADA: AWAY", "#891717", "Padrão de 3 Home detectado!"
    if all(x == 'B' for x in u): return "ENTRADA CONFIRMADA: HOME", "#0eabe4", "Padrão de 3 Away detectado!"
    return "AGUARDANDO PADRÃO", "#161616", "Análise em tempo real ativa"

# --- INTERFACE VISUAL PREMIUM (CSS DO FOOTWIN) ---
def render_ui(hist, txt, cor, desc, g, r):
    js_h = str(hist)
    return f"""
    <div style="background:#000; color:white; font-family:'Segoe UI', sans-serif; padding:15px; border-radius:20px;">
        <!-- HEADER ESTILO FOOTWIN -->
        <div style="display:flex; justify-content:space-between; align-items:center; background:#161616; padding:15px; border-radius:15px; border:1px solid #333; margin-bottom:15px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="background:#0eabe4; width:10px; height:10px; border-radius:50%; box-shadow:0 0 10px #0eabe4;"></div>
                <h4 style="margin:0;">Padrões detectados</h4>
            </div>
            <div style="font-weight:bold; color:#0eabe4;">LIVE ANALYZER</div>
        </div>

        <!-- CARD DE SINAL CENTRAL -->
        <div style="background:{cor}; padding:30px; border-radius:20px; text-align:center; border:1px solid rgba(255,255,255,0.2); box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
            <h1 style="margin:0; font-size:1.8rem; text-transform:uppercase; letter-spacing:2px;">{txt}</h1>
            <p style="margin:10px 0 0 0; opacity:0.7;">{desc}</p>
        </div>

        <!-- GRID DE STATUS E HISTÓRICO -->
        <div style="display:grid; grid-template-columns: 1fr 1.5fr; gap:15px; margin-top:15px;">
            <div style="background:#161616; padding:15px; border-radius:15px; border:1px solid #333; text-align:center;">
                <p style="margin:0; color:#888; font-size:0.8rem;">ASSERTIVIDADE</p>
                <div style="display:flex; justify-content:space-around; margin-top:10px;">
                    <div style="color:#0eabe4;"><b>{g}</b><br>Greens</div>
                    <div style="color:#891717;"><b>{r}</b><br>Reds</div>
                </div>
            </div>
            <div style="background:#161616; padding:15px; border-radius:15px; border:1px solid #333; text-align:center;">
                <p style="margin:0; color:#888; font-size:0.8rem;">ÚLTIMOS RESULTADOS</p>
                <div id="h" style="margin-top:10px; font-weight:bold;"></div>
            </div>
        </div>
        <script>
            const d = {js_h}.slice(-10).reverse();
            document.getElementById('h').innerHTML = d.map(x => `<span style="background:${{x=='P'?'#0eabe4':x=='B'?'#891717':'#16a34a'}}; padding:6px 10px; border-radius:6px; margin:2px; display:inline-block; font-size:0.8rem;">${{x}}</span>`).join("");
        </script>
    </div>
    """

# --- SIDEBAR ---
st.sidebar.title("🎮 FOOTWIN CONFIG")
url_input = st.sidebar.text_input("Link da Mesa (Evolution):")
ligar = st.sidebar.toggle("ATIVAR ROBÔ LIVE")

# Exibe a Interface
txt, cor, desc = calcular_stats(st.session_state.historico)
components.html(render_ui(st.session_state.historico, txt, cor, desc, st.session_state.greens, st.session_state.reds), height=380)

# --- MOTOR DE CAPTURA ---
async def capturar(url):
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
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
        except: return None

if ligar and url_input:
    res = asyncio.run(capturar(url_input))
    if res and res != st.session_state.ultimo_res:
        # Lógica Simples de Green/Red para o Painel
        if st.session_state.ultimo_res == "P" and res == "B": st.session_state.greens += 1
        elif st.session_state.ultimo_res == "B" and res == "P": st.session_state.greens += 1
        
        st.session_state.historico.append(res)
        st.session_state.ultimo_res = res
        st.rerun()
    time.sleep(5)
    st.rerun()
