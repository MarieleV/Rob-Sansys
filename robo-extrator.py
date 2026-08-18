import os
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import schedule
from playwright.sync_api import sync_playwright

# Arquivo onde os dados de login e horários serão salvos
ARQUIVO_CONFIG = "config.json"

class AppAutomacao:
    def __init__(self, root):
        self.root = root
        self.root.title("Robô de Extração - Águas de Joinville")
        self.root.geometry("400x500") 
        self.root.resizable(False, False)
        
        # Variáveis da Interface
        self.usuario_var = tk.StringVar()
        self.senha_var = tk.StringVar()
        self.horario1_var = tk.StringVar(value="08:00")
        self.horario2_var = tk.StringVar(value="")
        self.horario3_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Status: Aguardando comando...")
        
        self.criar_interface()
        self.carregar_configuracoes()
        
        # Inicia a thread que fica verificando os agendamentos
        self.thread_agendamento = threading.Thread(target=self.rodar_agendamentos, daemon=True)
        self.thread_agendamento.start()

    def criar_interface(self):
        # Frame principal que engloba tudo
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # ==========================================
        # 1. ÁREA DE LOGIN 
        # ==========================================
        self.area_login = ttk.Frame(self.main_frame)
        self.area_login.pack(fill='x', pady=5)

        # --- CONTAINER EXPANDIDO (Formulário) ---
        self.frame_form_login = ttk.Frame(self.area_login)
        self.frame_form_login.pack(pady=5)
        
        frame_campos = ttk.Frame(self.frame_form_login)
        frame_campos.pack()
        
        ttk.Label(frame_campos, text="Usuário:").grid(row=0, column=0, sticky=tk.E, padx=5, pady=5)
        ttk.Entry(frame_campos, textvariable=self.usuario_var, width=28).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_campos, text="Senha:").grid(row=1, column=0, sticky=tk.E, padx=5, pady=5)
        ttk.Entry(frame_campos, textvariable=self.senha_var, show="*", width=28).grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(self.frame_form_login, text="Salvar Credenciais", command=self.salvar_configuracoes).pack(pady=10)

        # --- CONTAINER MINIMIZADO (Botão Editar) ---
        self.frame_login_minimizado = ttk.Frame(self.area_login)
        
        self.lbl_usuario_salvo = ttk.Label(self.frame_login_minimizado, text="", foreground="green")
        self.lbl_usuario_salvo.pack(side=tk.LEFT, padx=10)
        ttk.Button(self.frame_login_minimizado, text="Editar Credenciais", command=self.expandir_login).pack(side=tk.LEFT)

        # ==========================================
        # 2. SEPARADOR E AÇÃO MANUAL
        # ==========================================
        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=10)

        ttk.Button(self.main_frame, text="▶ Extrair Agora", command=self.iniciar_extracao_agora, width=35).pack(pady=5)

        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=10)

        # ==========================================
        # 3. SEÇÃO DE AGENDAMENTO (3 Horários)
        # ==========================================
        frame_agenda = ttk.Frame(self.main_frame)
        frame_agenda.pack(pady=5)
        
        ttk.Label(frame_agenda, text="Horários de Agendamento (HH:MM):").grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        ttk.Label(frame_agenda, text="Horário 1:").grid(row=1, column=0, sticky=tk.E, padx=5, pady=2)
        ttk.Entry(frame_agenda, textvariable=self.horario1_var, width=10).grid(row=1, column=1, pady=2)

        ttk.Label(frame_agenda, text="Horário 2:").grid(row=2, column=0, sticky=tk.E, padx=5, pady=2)
        ttk.Entry(frame_agenda, textvariable=self.horario2_var, width=10).grid(row=2, column=1, pady=2)

        ttk.Label(frame_agenda, text="Horário 3:").grid(row=3, column=0, sticky=tk.E, padx=5, pady=2)
        ttk.Entry(frame_agenda, textvariable=self.horario3_var, width=10).grid(row=3, column=1, pady=2)

        ttk.Button(frame_agenda, text="Agendar", command=self.agendar_extracao).grid(row=4, column=0, columnspan=2, pady=15)

        # ==========================================
        # STATUS
        # ==========================================
        ttk.Label(self.main_frame, textvariable=self.status_var, foreground="blue", justify="center").pack(side=tk.BOTTOM, pady=5)

    # ==========================================
    # FUNÇÕES DE MINIMIZAR/EXPANDIR A TELA
    # ==========================================
    def minimizar_login(self):
        self.frame_form_login.pack_forget() 
        self.lbl_usuario_salvo.config(text=f"✔ Logado como: {self.usuario_var.get()}")
        self.frame_login_minimizado.pack(pady=5) 

    def expandir_login(self):
        self.frame_login_minimizado.pack_forget() 
        self.frame_form_login.pack(pady=5) 

    # ==========================================
    # FUNÇÕES DE CONFIGURAÇÃO
    # ==========================================
    def carregar_configuracoes(self):
        if os.path.exists(ARQUIVO_CONFIG):
            try:
                with open(ARQUIVO_CONFIG, "r") as f:
                    dados = json.load(f)
                    user = dados.get("usuario", "")
                    pwd = dados.get("senha", "")
                    
                    self.usuario_var.set(user)
                    self.senha_var.set(pwd)
                    self.horario1_var.set(dados.get("horario1", "08:00"))
                    self.horario2_var.set(dados.get("horario2", ""))
                    self.horario3_var.set(dados.get("horario3", ""))
                    
                    if user and pwd:
                        self.minimizar_login()
            except Exception as e:
                print(f"Erro ao carregar configurações: {e}")

    def salvar_configuracoes(self):
        usuario = self.usuario_var.get().strip()
        senha = self.senha_var.get().strip()

        if not usuario or not senha:
            messagebox.showwarning("Atenção", "Preencha usuário e senha para salvar.")
            return

        # Salva também os horários atuais para não perder
        dados = {
            "usuario": usuario,
            "senha": senha,
            "horario1": self.horario1_var.get().strip(),
            "horario2": self.horario2_var.get().strip(),
            "horario3": self.horario3_var.get().strip()
        }
        with open(ARQUIVO_CONFIG, "w") as f:
            json.dump(dados, f)
            
        messagebox.showinfo("Sucesso", "Credenciais salvas com sucesso!")
        self.minimizar_login()

    def salvar_horarios_silencioso(self):
        try:
            with open(ARQUIVO_CONFIG, "r") as f:
                dados = json.load(f)
        except:
            dados = {}
            
        dados["horario1"] = self.horario1_var.get().strip()
        dados["horario2"] = self.horario2_var.get().strip()
        dados["horario3"] = self.horario3_var.get().strip()
        
        with open(ARQUIVO_CONFIG, "w") as f:
            json.dump(dados, f)

    # ==========================================
    # MOTOR DA AUTOMAÇÃO (AGENDAMENTO E PLAYWRIGHT)
    # ==========================================
    def rodar_agendamentos(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def agendar_extracao(self):
        horarios = [
            self.horario1_var.get().strip(),
            self.horario2_var.get().strip(),
            self.horario3_var.get().strip()
        ]
        
        horarios_validos = [h for h in horarios if h != ""]
        
        if not horarios_validos:
            messagebox.showwarning("Aviso", "Preencha pelo menos um horário para agendar.")
            return

        try:
            schedule.clear()
            for h in horarios_validos:
                schedule.every().day.at(h).do(self.iniciar_extracao_agora)
                
            self.salvar_horarios_silencioso()
                
            texto_status = " e ".join(horarios_validos)
            self.status_var.set(f"Status: Agendado para {texto_status} todos os dias.")
            messagebox.showinfo("Agendamento", f"Extração agendada para:\n{texto_status} diariamente.")
        except Exception as e:
            messagebox.showerror("Erro", f"Formato de hora inválido. Use HH:MM. Erro: {e}")

    def iniciar_extracao_agora(self):
        usuario = self.usuario_var.get()
        senha = self.senha_var.get()
        
        if not usuario or not senha:
            messagebox.showwarning("Atenção", "Por favor, configure o usuário e a senha antes.")
            self.expandir_login()
            return

        self.status_var.set("Status: Extraindo relatório... Aguarde.")
        threading.Thread(target=self.automacao_playwright, args=(usuario, senha), daemon=True).start()

    def automacao_playwright(self, usuario, senha):
        try:
            with sync_playwright() as playwright:
                # Troque headless=False para headless=True depois de validar!
                browser = playwright.chromium.launch(headless=False) 
                context = browser.new_context()
                page = context.new_page()
                
                page.goto("https://aguasdejoinville.com.br/sansys/index.html#/")
                
                page.get_by_placeholder("Usuário").click(force=True)
                page.get_by_placeholder("Usuário").fill(usuario, force=True)
                page.get_by_placeholder("Usuário").press("Tab")
                
                page.get_by_placeholder("Senha").fill(senha, force=True)
                page.get_by_placeholder("Senha").press("Enter") 
                
                page.wait_for_timeout(2000)
                page.keyboard.press("Enter") 
                page.wait_for_timeout(5000)
                
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
                
                pasta_destino = os.path.join(os.path.expanduser("~"), "Downloads")
                nome_renomeado = "Relatorio_Fonte_Dado_075.zip" 
                caminho_final = os.path.join(pasta_destino, nome_renomeado)
                
                if os.path.exists(caminho_final):
                    os.remove(caminho_final)

                download.save_as(caminho_final)
                
                context.close()
                browser.close()
                
                self.root.after(0, lambda: self.status_var.set("Status: Sucesso! Arquivo salvo em Downloads."))
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso em:\n{caminho_final}"))
                
        except Exception as e:
            erro_msg = str(e)
            self.root.after(0, lambda: self.status_var.set("Status: Erro na extração."))
            self.root.after(0, lambda erro=erro_msg: messagebox.showerror("Erro", f"Ocorreu um erro durante a extração:\n{erro}"))

if __name__ == "__main__":
    root = tk.Tk()
    app = AppAutomacao(root)
    root.mainloop()