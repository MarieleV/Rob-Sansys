import os
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import schedule
from playwright.sync_api import sync_playwright

# Arquivo onde os dados de login serão salvos
ARQUIVO_CONFIG = "config.json"

class AppAutomacao:
    def __init__(self, root):
        self.root = root
        self.root.title("Robô de Extração - Águas de Joinville")
        self.root.geometry("400x350")
        self.root.resizable(False, False)
        
        # Variáveis da Interface
        self.usuario_var = tk.StringVar()
        self.senha_var = tk.StringVar()
        self.horario_var = tk.StringVar(value="08:00")
        self.status_var = tk.StringVar(value="Status: Aguardando comando...")
        
        self.criar_interface()
        self.carregar_configuracoes()
        
        # Inicia a thread que fica verificando os agendamentos
        self.thread_agendamento = threading.Thread(target=self.rodar_agendamentos, daemon=True)
        self.thread_agendamento.start()

    def criar_interface(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Seção de Login
        ttk.Label(frame, text="Usuário:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.usuario_var, width=30).grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Senha:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.senha_var, show="*", width=30).grid(row=1, column=1, pady=5)

        ttk.Button(frame, text="Salvar Credenciais", command=self.salvar_configuracoes).grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Separator(frame, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky='ew', pady=10)

        # Seção de Ações
        ttk.Button(frame, text="▶ Extrair Agora", command=self.iniciar_extracao_agora).grid(row=4, column=0, columnspan=2, pady=5, sticky='ew')

        # Seção de Agendamento
        frame_agenda = ttk.Frame(frame)
        frame_agenda.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Label(frame_agenda, text="Horário (HH:MM):").pack(side=tk.LEFT, padx=5)
        ttk.Entry(frame_agenda, textvariable=self.horario_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_agenda, text="Agendar", command=self.agendar_extracao).pack(side=tk.LEFT, padx=5)

        # Status
        ttk.Label(frame, textvariable=self.status_var, foreground="blue").grid(row=6, column=0, columnspan=2, pady=15)

    def carregar_configuracoes(self):
        """Carrega o usuário e senha salvos anteriormente."""
        if os.path.exists(ARQUIVO_CONFIG):
            try:
                with open(ARQUIVO_CONFIG, "r") as f:
                    dados = json.load(f)
                    self.usuario_var.set(dados.get("usuario", ""))
                    self.senha_var.set(dados.get("senha", ""))
            except Exception as e:
                print(f"Erro ao carregar configurações: {e}")

    def salvar_configuracoes(self):
        """Salva o usuário e senha em um arquivo JSON."""
        dados = {
            "usuario": self.usuario_var.get(),
            "senha": self.senha_var.get()
        }
        with open(ARQUIVO_CONFIG, "w") as f:
            json.dump(dados, f)
        messagebox.showinfo("Sucesso", "Credenciais salvas com sucesso!")

    def rodar_agendamentos(self):
        """Loop infinito que checa se está na hora de rodar as tarefas agendadas."""
        while True:
            schedule.run_pending()
            time.sleep(1)

    def agendar_extracao(self):
        horario = self.horario_var.get()
        try:
            # Limpa agendamentos anteriores para não duplicar
            schedule.clear()
            schedule.every().day.at(horario).do(self.iniciar_extracao_agora)
            self.status_var.set(f"Status: Agendado para as {horario} todos os dias.")
            messagebox.showinfo("Agendamento", f"Extração agendada para as {horario} diariamente.")
        except Exception as e:
            messagebox.showerror("Erro", f"Formato de hora inválido. Use HH:MM. Erro: {e}")

    def iniciar_extracao_agora(self):
        usuario = self.usuario_var.get()
        senha = self.senha_var.get()
        
        if not usuario or not senha:
            messagebox.showwarning("Atenção", "Por favor, preencha o usuário e a senha.")
            return

        self.status_var.set("Status: Extraindo relatório... Aguarde.")
        
        # Roda a automação em uma thread separada para não travar a interface
        threading.Thread(target=self.automacao_playwright, args=(usuario, senha), daemon=True).start()

    def automacao_playwright(self, usuario, senha):
        """A função 1 original adaptada."""
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=False) # Headless=True para não atrapalhar o uso do PC
                context = browser.new_context()
                page = context.new_page()
                
                page.goto("https://aguasdejoinville.com.br/sansys/index.html#/")
                
                # Login usando as variáveis da interface
                page.get_by_placeholder("Usuário").click(force=True)
                page.get_by_placeholder("Usuário").fill(usuario, force=True)
                page.get_by_placeholder("Usuário").press("Tab")
                
                page.get_by_placeholder("Senha").fill(senha, force=True)
                page.get_by_placeholder("Senha").press("Enter")
                page.wait_for_timeout(2000)
                page.get_by_placeholder("Senha").press("Enter")   
                
                page.wait_for_timeout(3000)
                
                page.locator("i.material-icons", has_text="menu").click()
                page.wait_for_timeout(3000)

                page.get_by_text("Gerencial", exact=True).click()
                page.get_by_text("Relatório Customizado", exact=True).click()
                page.get_by_text("Processar Relatório Fonte de Dado", exact=True).click()

                page.wait_for_timeout(3000)

                page.locator('div[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.cdRelatorioFonteDado_header"]').click()
                page.locator('div[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.cdRelatorioFonteDado_cell"]').get_by_text("075", exact=True).first.click()
                page.locator('button[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.icAbrir"]').first.click()
                
                page.wait_for_timeout(3000)
                
                page.locator("img.x-form-date-trigger:visible").first.click()
                page.wait_for_timeout(500) 
                page.locator("button:visible", has_text="Hoje").first.click()
                
                page.get_by_role("textbox", name="Grupo Faturamento (Informe 0").fill("0", force=True)
                page.wait_for_timeout(3000)
                
                page.get_by_text("Executar", exact=True).click()

                botao_download = page.locator('button[cfgname="acompanharExecucaoRelatorioFonteDado.acompanhar.btDownload"]')
                botao_download.wait_for(state="visible", timeout=1200000)
                
                with page.expect_download(timeout=60000) as download_info:
                    botao_download.click()
                    
                download = download_info.value
                
                # Definindo a pasta Downloads do usuário atual e o novo nome do arquivo
                pasta_destino = os.path.join(os.path.expanduser("~"), "Downloads")
                nome_renomeado = "Relatorio_Fonte_Dado_075.zip" # <-- AQUI VOCÊ DEFINE O NOVO NOME
                caminho_final = os.path.join(pasta_destino, nome_renomeado)
                
                # Se já existir um arquivo com esse nome, exclui para substituir
                if os.path.exists(caminho_final):
                    os.remove(caminho_final)

                download.save_as(caminho_final)
                
                context.close()
                browser.close()
                
                # Atualiza a interface
                self.root.after(0, lambda: self.status_var.set("Status: Sucesso! Arquivo salvo em Downloads."))
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso em:\n{caminho_final}"))
                
        except Exception as e:
            # Salva a mensagem de erro em formato de texto antes que o Python a delete
            erro_msg = str(e)
            
            self.root.after(0, lambda: self.status_var.set("Status: Erro na extração."))
            # Passamos o erro_msg para dentro do lambda
            self.root.after(0, lambda erro=erro_msg: messagebox.showerror("Erro", f"Ocorreu um erro durante a extração:\n{erro}"))

if __name__ == "__main__":
    root = tk.Tk()
    app = AppAutomacao(root)
    root.mainloop()