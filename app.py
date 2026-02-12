async def capturar_com_debug(url):
    logs = []
    try:
        async with async_playwright() as p:
            logs.append("🚀 Iniciando navegador modo furtivo...")
            # Usamos argumentos para o cassino não detectar o robô
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0")
            page = await context.new_page()
            
            logs.append("🔗 Acessando a mesa direto...")
            await page.goto(url, timeout=90000, wait_until="networkidle") # Aumentado para 90s
            
            logs.append("🔍 Localizando o quadro do jogo...")
            # Na MaximaBet, o jogo geralmente está no primeiro iframe
            frame = page.frame_locator('iframe').first 
            
            logs.append("⏳ Aguardando leitura do histórico...")
            # Este seletor busca as bolinhas de resultado (H, A ou T) no canto da tela
            item = frame.locator('.stats-history-item, [class*="HistoryItem"], [class*="result"]').first
            
            # Espera até que o jogo carregue os resultados na tela
            await item.wait_for(state="visible", timeout=45000)
            
            texto = await item.inner_text()
            logs.append(f"✅ SUCESSO! Capturado: {texto}")
            await browser.close()
            
            # Tradução para o nosso sistema de sinais
            if "H" in texto or "Home" in texto or "C" in texto: return "P", logs
            if "A" in texto or "Away" in texto or "V" in texto: return "B", logs
            return "T", logs
    except Exception as e:
        logs.append(f"❌ ERRO: O jogo demorou a carregar. Tente novamente.")
        logs.append(f"Dica: Verifique sua conexão. Erro técnico: {str(e)[:40]}")
        return None, logs
