import streamlit as st
import streamlit.components.v1 as components
import asyncio
from playwright.async_api import async_playwright

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Painel PRO Football Studio", layout="wide")

# Inicializa o histórico na sessão do Streamlit para não perder os dados
if 'historico' not in st.session_state:
    st.session_state.historico = []

# --- INTERFACE HTML ---
# Removi a lógica de 'message' do JS, agora o Python injeta os dados direto
def gerar_html(resultados):
    # Converte a lista do Python para uma string JS: ["P", "B", "T"]
    js_results = str(resultados)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ margin:0; font-family: sans-serif; background: #0e1117; color:white; }}
            .grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:15px; padding:20px; }}
            .card {{ background:#1e293b; padding:15px; border-radius:10px; text-align:center; border: 1px solid #334155; }}
            .P {{ background:#2563eb; padding:5px 10px; margin:2px; border-radius:4px; }}
            .B {{ background:#dc2626; padding:5px 10px; margin:2px; border-radius:4px; }}
            .T {{ background:#16a34a; padding:5px 10px; margin:2px; border-radius:4px; }}
        </style>
    </head>
    <body>
        <div class="grid">
            <div class="card"><h3>📊 Stats</h3><div id="stats"></div></div>
            <div class="card"><h3>🔥 Sequência</h3><div id="streak"></div></div>
            <div class="card"><h3>🕒 Histórico</h3><div id="history"></div></div>
        </div>
        <canvas id="chart" style="max-height:200px"></canvas>

        <script>
            const results = {js_results};
            
            // Lógica de exibição
            if(results.length > 0) {{
                document.getElementById("history").innerHTML = results.slice(-10).reverse().map(r => `<span class="${{r}}">${{r}}</span>`).join("");
                
                let last = results[results.length-1];
                let count = 0;
                for(let i=results.length-1; i>=0; i--) {{
                    if(results[i] === last) count++; else break;
                }}
                document.getElementById("streak").innerHTML = `${{last}} ${{count}}x`;
                
                let p = results.filter(r => r === 'P').length;
                let b = results.filter(r => r === 'B').length;
                document.getElementById("stats").innerHTML = `H: ${{((p/results.length)*100).toFixed(0)}}% | A: ${{((b/results.length)*100).toFixed(0)}}%`;
            }}
        </script>
    </body>
    </html>
    """

# --- SIDEBAR ---
st.sidebar.title("Configurações")
url_cassino = st.sidebar.text_input("Link do Jogo:", "URL_DO_CASSINO_AQUI")
iniciar = st.sidebar.toggle("LIGAR MONITORAMENTO")

# Renderiza o componente
placeholder_html = st.empty()
with placeholder_html:
    components.html(gerar_html(st.session_state.historico), height=500)

# --- LÓGICA DO ROBÔ ---
async def capturar_dado():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url_cassino, timeout=60000)
            # Tenta localizar o iframe da Evolution
            frame = page.frame_locator('iframe[src*="evolution"]').first
            # Pega o último resultado (seletor comum da Evolution)
            elemento = frame.locator('.stats-history-item').first
            texto = await elemento.inner_text()
            
            letra = "T"
            if "Home" in texto or "H" in texto: letra = "P"
            elif "Away" in texto or "A" in texto: letra = "B"
            
            await browser.close()
            return letra
        except Exception as e:
            await browser.close()
            return None

# Loop de atualização (O segredo está no st.rerun)
if iniciar:
    resultado = asyncio.run(capturar_dado())
    if resultado:
        # Só adiciona se for diferente do último para não repetir
        if not st.session_state.historico or resultado != st.session_state.historico[-1]:
            st.session_state.historico.append(resultado)
            if len(st.session_state.historico) > 100: st.session_state.historico.pop(0)
            st.rerun() # Força o Streamlit a recarregar a página com o dado novo
    
    st.info("Buscando novos dados...")
    import time
    time.sleep(5)
    st.rerun()
