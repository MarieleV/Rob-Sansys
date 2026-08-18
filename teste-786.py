import os
from playwright.sync_api import sync_playwright

# ==========================================
# INSIRA SUAS CREDENCIAIS PARA O TESTE
# ==========================================
USUARIO = "mariele.vieira"
SENHA = "M@rilia1811"

def testar_relatorio_786():
    print("Iniciando teste isolado do relatório 786...")
    
    with sync_playwright() as playwright:
        # Abrindo o navegador visível
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print("1. Acessando o sistema...")
            page.goto("https://aguasdejoinville.com.br/sansys/index.html#/")
            
            # --- LOGIN ---
            page.get_by_placeholder("Usuário").click(force=True)
            page.get_by_placeholder("Usuário").fill(USUARIO, force=True)
            page.get_by_placeholder("Usuário").press("Tab")
            
            page.get_by_placeholder("Senha").fill(SENHA, force=True)
            page.get_by_placeholder("Senha").press("Enter") 
            
            page.wait_for_timeout(2000)
            page.keyboard.press("Enter") 
            page.wait_for_timeout(5000)
            
            # --- NAVEGAÇÃO NO MENU ---
            print("2. Navegando até os relatórios...")
            page.locator("i.material-icons", has_text="menu").click()
            page.wait_for_timeout(3000)

            page.get_by_text("Gerencial", exact=True).click()
            page.get_by_text("Relatório Customizado", exact=True).click()
            page.get_by_text("Processar Relatório Fonte de Dado", exact=True).click()
            page.wait_for_timeout(3000)

            # --- ABRINDO O RELATÓRIO 786 ---
            print("3. Selecionando o relatório 786...")
            page.locator('div[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.cdRelatorioFonteDado_header"]').click()
            page.locator('div[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.cdRelatorioFonteDado_cell"]').get_by_text("786", exact=True).first.click()
            page.locator('button[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.icAbrir"]').first.click()
            
            print("Aguardando tela de filtros...")
            page.wait_for_timeout(4000)
            
            # ========================================================
            # --- PREENCHENDO FILTROS ESPECÍFICOS DO 786 ---
            # ========================================================
            print("4. Preenchendo Data Inicial (01/01/2024)...")
            
            # Pega a primeira caixa de texto
            campo_data_inicial = page.get_by_role("textbox").nth(0)
            
            # Clica dentro dela
            campo_data_inicial.click(force=True)
            page.wait_for_timeout(500)
            
            # Seleciona tudo e apaga (para garantir que o campo está limpo)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.wait_for_timeout(200)
            
            # Digita tecla por tecla como um humano (delay de 100 milissegundos entre as teclas)
            campo_data_inicial.press_sequentially("01012024", delay=100) 
            page.wait_for_timeout(1000)
            
            # Aperta Tab para confirmar a saída do campo
            page.keyboard.press("Tab")
            page.wait_for_timeout(500)
            
            # ========================================================

            print("5. Preenchendo Data Final (Hoje)...")
            # Clica no segundo ícone de calendário da tela
            page.locator("img.x-form-date-trigger:visible").nth(1).click()
            page.wait_for_timeout(500)
            # Clica no botão Hoje do calendário
            page.locator("button:visible", has_text="Hoje").first.click()
            page.wait_for_timeout(2000)

            # ========================================================
            
            # --- EXECUTAR E BAIXAR ---
            print("6. Executando o relatório...")
            page.get_by_text("Executar", exact=True).click()

            print("Aguardando o processamento (pode demorar)...")
            botao_download = page.locator('button[cfgname="acompanharExecucaoRelatorioFonteDado.acompanhar.btDownload"]')
            botao_download.wait_for(state="visible", timeout=1200000)
            
            print("7. Botão liberado! Iniciando download...")
            with page.expect_download(timeout=60000) as download_info:
                botao_download.click()
                
            download = download_info.value
            
            pasta_destino = os.path.join(os.path.expanduser("~"), "Downloads")
            caminho_final = os.path.join(pasta_destino, "Relatorio_Fonte_Dado_786.zip")
            
            if os.path.exists(caminho_final):
                os.remove(caminho_final)

            download.save_as(caminho_final)
            print(f"\n✅ SUCESSO! Relatório 786 salvo em: {caminho_final}")
            
        except Exception as e:
            print(f"\n❌ OCORREU UM ERRO:\n{e}")
            
        finally:
            print("Fechando navegador...")
            context.close()
            browser.close()

if __name__ == "__main__":
    testar_relatorio_786()