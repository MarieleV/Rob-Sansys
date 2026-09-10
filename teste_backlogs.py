import os
from datetime import datetime
from playwright.sync_api import sync_playwright

def testar_backlogs(usuario, senha):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        relatorios = ["Fiscalizacao", "Notificacao"]

        for tipo in relatorios:
            print(f"\n{'='*50}")
            print(f" INICIANDO EXTRAÇÃO: BACKLOG DE {tipo.upper()}")
            print(f"{'='*50}")

            # MUDANÇA AQUI: Criamos um contexto (uma aba limpa) para CADA relatório
            context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='pt-BR')
            page = context.new_page()

            print("Acessando o sistema...")
            page.goto("https://aguasdejoinville.com.br/sansys/index.html#/")

            # ==========================================
            # LOGIN
            # ==========================================
            page.get_by_placeholder("Usuário").click(force=True)
            page.get_by_placeholder("Usuário").fill(usuario, force=True)
            page.get_by_placeholder("Usuário").press("Tab")
            page.get_by_placeholder("Senha").fill(senha, force=True)
            page.get_by_placeholder("Senha").press("Enter")

            page.wait_for_timeout(3000)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000)
            page.keyboard.press("Enter")
            page.wait_for_timeout(4000)

            print("Navegando pelo menu...")
            try:
                page.locator("i.material-icons").filter(has_text="menu").click(timeout=3000)
                page.wait_for_timeout(2000)
            except:
                pass

            page.get_by_text("Operacional", exact=True).first.click()
            page.wait_for_timeout(1000)
            page.get_by_text("Serviços", exact=True).first.click()
            page.wait_for_timeout(1000)
            page.get_by_text("Relatórios", exact=True).first.click()
            page.wait_for_timeout(1000)
            page.locator("a").filter(has_text="OPE0002").first.click()
            page.wait_for_timeout(6000) 

            print("Preenchendo Filtros Comuns...")

            # 0. Serviços de: Unidade Comercial
            try:
                campo_servicos = page.locator(".x-form-item").filter(has_text="Serviços de:").locator("input")
                campo_servicos.click(force=True, timeout=2000)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                campo_servicos.press_sequentially("Unidade Comercial", delay=50)
                page.keyboard.press("Tab")
                page.wait_for_timeout(1000)
            except Exception as e:
                print(f"Não conseguiu preencher 'Serviços de:': {e}")

            # 0.1 Pesquisar Por: Empresa
            try:
                campo_pesquisa = page.locator('input[cfgname="relOPE0002.relatorio.tpPesquisa"]')
                campo_pesquisa.click(force=True, timeout=2000)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                campo_pesquisa.press_sequentially("Empresa", delay=50)
                page.keyboard.press("Tab")
                page.wait_for_timeout(1500)
            except Exception as e:
                print(f"Não conseguiu preencher 'Pesquisar Por': {e}")

            # 0.2 Estrutura Empresa
            try:
                page.get_by_text("01 - CIA AGUAS DE JOINVILLE").dblclick(timeout=2000)
                page.wait_for_timeout(500)
            except Exception as e:
                print(f"Não conseguiu selecionar a Empresa: {e}")

            # 1. Data Inicial (Fixa: 01/01/2025)
            try:
                campo_data_ini = page.get_by_role("textbox", name="Período Solicitação Inicial:")
                campo_data_ini.click(force=True)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                campo_data_ini.press_sequentially("01012025", delay=50)
                page.keyboard.press("Tab")
            except:
                pass

            # 2. Data Final (Hoje)
            try:
                data_hoje = datetime.now().strftime("%d%m%Y")
                campo_data_fim = page.get_by_role("textbox", name="Período Solicitação Final:")
                campo_data_fim.click(force=True)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                campo_data_fim.press_sequentially(data_hoje, delay=50)
                page.keyboard.press("Tab")
            except:
                pass

            print(f"Aplicando Filtros Específicos para {tipo}...")

            # 3. Situação Serviço (Regra do IF/ELSE)
            if tipo == "Fiscalizacao":
                situacoes = ["Para Reprogramar", "Pendente", "Postergada", "Programado"]
            else:
                situacoes = ["Pendente", "Postergada", "Programado"]

            for sit in situacoes:
                try:
                    page.get_by_text(sit, exact=True).dblclick(timeout=1000)
                except:
                    pass

            # 4. Setor Execução (Regra do IF/ELSE)
            try:
                campo_setor = page.locator('input[cfgname="relOPE0002.relatorio.opeSetorOperacional"]')
                campo_setor.click(force=True, timeout=2000)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                
                texto_setor = "CIA - CFC" if tipo == "Fiscalizacao" else "CIA - CFC Notificação"
                campo_setor.press_sequentially(texto_setor, delay=50)
                
                page.keyboard.press("Tab")
                page.wait_for_timeout(1000)
            except Exception as e:
                print(f"Não conseguiu preencher 'Setor Execução': {e}")

            # 5. Formato EXCEL
            try:
                campo_formato = page.locator('input[cfgname="relOPE0002.relatorio.relFormatoRelatorio"]')
                campo_formato.click(force=True, timeout=2000)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                campo_formato.press_sequentially("EXCEL", delay=50)
                page.keyboard.press("Tab")
                page.wait_for_timeout(1000)
            except Exception as e:
                print(f"Não conseguiu preencher 'Formato': {e}")

            print("Baixando o arquivo...")
            
            with page.expect_download(timeout=300000) as download_info:
                page.get_by_role("button", name="Confirmar").click()
                
            download = download_info.value
            pasta_destino = os.path.join(os.path.expanduser("~"), "Downloads")
            caminho_salvo = os.path.join(pasta_destino, f"Teste_Backlog_{tipo}.xls")
            
            if os.path.exists(caminho_salvo):
                os.remove(caminho_salvo)
                
            download.save_as(caminho_salvo)

            print(f"✅ SUCESSO! Arquivo salvo em: {caminho_salvo}")
            page.wait_for_timeout(2000) 
            
            # 🌟 MUDANÇA AQUI: Fecha a aba limpa para a próxima começar do zero
            context.close()

        print("\n🎉 TODAS AS EXTRAÇÕES FORAM CONCLUÍDAS COM SUCESSO!")
        browser.close()

if __name__ == "__main__":
    # COLOQUE SUAS CREDENCIAIS AQUI PARA O TESTE
    USER = "mariele.vieira"
    PASS = "Senha"
    testar_backlogs(USER, PASS)