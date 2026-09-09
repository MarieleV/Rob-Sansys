import time
import os
from playwright.sync_api import sync_playwright

def testar_backlogs(usuario, senha):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Visível para vermos os testes
        context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='pt-BR')
        page = context.new_page()
        
        print("Acessando o sistema...")
        page.goto("https://aguasdejoinville.com.br/sansys/index.html#/")
        
        # Login (igual ao robô principal)
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
        
        print("Iniciando navegação para os Backlogs...")
        
        # ========================================================
        # COLE AQUI OS COMANDOS QUE VOCÊ COPIAR DO CODEGEN
        # ========================================================
        
        
        # ========================================================

        print("Aguardando 10 segundos antes de fechar...")
        page.wait_for_timeout(10000)
        browser.close()

if __name__ == "__main__":
    # Coloque suas credenciais aqui só para o teste
    USER = "SEU_USUARIO"
    PASS = "SUA_SENHA"
    testar_backlogs(USER, PASS)