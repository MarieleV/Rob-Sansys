import os
from playwright.sync_api import sync_playwright

def testar_backlog(usuario, senha):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='pt-BR')
        page = context.new_page()

        print("Acessando o sistema...")
        page.goto("https://aguasdejoinville.com.br/sansys/index.html#/")

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

        print("Navegando pelo menu para evitar tela branca...")
        
        # Garante que o menu lateral está aberto
        try:
            page.locator("i.material-icons").filter(has_text="menu").click(timeout=3000)
            page.wait_for_timeout(2000)
        except:
            pass

        page.get_by_text("Operacional", exact=True).first.click()
        page.wait_for_timeout(1000)
        # Clica no caminho do menu: Serviços > Relatórios > OPE0002
        page.get_by_text("Serviços", exact=True).first.click()
        page.wait_for_timeout(1000)
        
        page.get_by_text("Relatórios", exact=True).first.click()
        page.wait_for_timeout(1000)
        
        # Clica no relatório específico
        page.locator("a").filter(has_text="OPE0002").first.click()
        page.wait_for_timeout(6000) # Espera a tela legada carregar bem!

        print("\n" + "="*50)
        print("ROBÔ PAUSADO! Use o 'Pick Locator' (ícone de alvo) no Inspector")
        print("="*50)
        
        # O robô vai congelar AQUI e abrir o painel de inspeção
        page.pause()

        browser.close()

if __name__ == "__main__":
    # COLOQUE SUAS CREDENCIAIS AQUI
    USER = "mariele.vieira"
    PASS = "M@rilia1811"
    testar_backlog(USER, PASS)