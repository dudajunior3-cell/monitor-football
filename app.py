
import streamlit as st
import streamlit.components.v1 as components
import asyncio
from playwright.async_api import async_playwright

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Painel PRO Football Studio", layout="wide")

# 1. SEU HTML INTEGRADO (Com uma pequena alteração para receber dados do Python)
html_interface = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{ margin:0; font-family: 'Segoe UI', sans-serif; background: transparent; color:white; }
.container{ max-width:1100px; margin:auto; padding:20px; }
h1{ text-align:center; margin-bottom:20px; text-shadow: 2px 2px 4px #000; }
.grid{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:15px; }
.card{ background:#1e293b; padding:20px; border-radius:15px; border: 1px solid #334155; box-shadow:0 5px 20px rgba(0,0,0,0.4); }
.history span{ display:inline-block; padding:6px 10px; margin:3px; border-radius:6px; font-weight:bold; }
.P{background:#2563eb;} .B{background:#dc2626;} .T{background:#16a34a;}
.trend{ font-weight:bold; font-size:18px; margin-top:10px; color: #facc15; }
#chart_container { max-width: 300px; margin: 20px auto; }
</style>
</head>
<body>
<div class="container">
    <h1>⚽ Football Studio - Painel PRO</h1>
    <div class="grid">
        <div class="card">
            <h3>📊 Estatísticas (Últimas 100)</h3>
            <p id="stats">Aguardando robô iniciar...</p>
            <div class="trend" id="trend">Analisando tendências...</div>
        </div>
        <div class="card">
            <h3>🔥 Sequência Atual</h3>
            <p id="streak">Sem dados</p>
        </div>
        <div class="card">
            <h3>🕒 Últimos Resultados</h3>
            <div class="history" id="history"></div>
        </div>
    </div>
    <div id="chart_container"><canvas id="chart"></canvas></div>
</div>

<script>
let results = [];
let chart = new Chart(document.getElementById("chart"),{
    type:"doughnut",
    data:{
        labels:["Player","Banker","Tie"],
        datasets:[{ data:[0,0,0], backgroundColor:["#2563eb","#dc2626","#16a34a"] }]
    },
    options: { plugins: { legend: { labels: { color: 'white' } } } }
});

// FUNÇÃO QUE O PYTHON VAI CHAMAR
window.addEventListener("message", (event) => {
    if (event.data.type === "NEW_RESULT") {
        addResult(event.data.val);
    }
});

function addResult(result){
    results.push(result);
    if(results.length>100) results.shift();
    updateStats();
}

function updateStats(){
    let player = results.filter(r=>'P'===r).length;
    let banker = results.filter(r=>'B'===r).length;
    let tie = results.filter(r=>'T'===r).length;
    let total = results.length || 1;

    document.getElementById("stats").innerHTML = `Player: ${(player/total*100).toFixed(1)}% | Banker: ${(banker/total*100).toFixed(1)}%`;
    
    let last = results[results.length-1];
    let count=0;
    for(let i=results.length-1;i>=0;i--){
        if(results[i]===last) count++;
        else break;
    }
    document.getElementById("streak").innerHTML = last ? `${last} ${count}x seguidas` : "Sem dados";
    
    let historyHTML="";
    results.slice(-15).reverse().forEach(r=>{ historyHTML+=`<span class="${r}">${r}</span>`; });
    document.getElementById("history").innerHTML=historyHTML;
    
    chart.data.datasets[0].data=[player, banker, tie];
    chart.update();
}
</script>
</body>
</html>
"""

# 2. LOGICA DO PYTHON (O ROBÔ)
st.sidebar.title("Configurações do Robô")
url_cassino = st.sidebar.text_input("Link do Jogo:", "https://sua-url-aqui.com")
iniciar = st.sidebar.button("LIGAR PAINEL")

# Renderiza a Interface HTML
components.html(html_interface, height=600)

async def monitorar():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url_cassino)
        
        ultimo_enviado = ""
        
        while True:
            try:
                # Localiza o iframe e o resultado
                frame = page.frame_locator('iframe[src*="evolution"]').first
                resultado_raw = await frame.locator('.stats-history-item').first.inner_text()
                
                # Converte o resultado para o formato do seu HTML (P, B ou T)
                letra = ""
                if "Home" in resultado_raw or "H" in resultado_raw: letra = "P"
                elif "Away" in resultado_raw or "A" in resultado_raw: letra = "B"
                elif "Tie" in resultado_raw or "T" in resultado_raw: letra = "T"
                
                if letra and letra != ultimo_enviado:
                    # ENVIA O DADO DO PYTHON PARA O HTML
                    st.components.v1.html(f"""
                        <script>
                        window.parent.postMessage({{type: "NEW_RESULT", val: "{letra}"}}, "*");
                        </script>
                    """, height=0)
                    ultimo_enviado = letra
                
                await asyncio.sleep(5)
            except:
                await asyncio.sleep(5)

if iniciar:
    st.sidebar.success("Robô monitorando...")
    asyncio.run(monitorar())


