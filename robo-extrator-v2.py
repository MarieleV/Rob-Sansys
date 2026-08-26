import os
import json
import time
import zipfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import schedule
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

# Arquivo onde os dados de login e configurações serão salvos
ARQUIVO_CONFIG = "config.json"

class AppAutomacao:
    def __init__(self, root):
        self.root = root
        self.root.title("Robô de Extração - Águas de Joinville")
        self.root.geometry("450x650") # Aumentei um pouco a altura para caber os novos menus
        self.root.resizable(False, False)
        
        # Variáveis da Interface
        self.usuario_var = tk.StringVar()
        self.senha_var = tk.StringVar()
        
        # Variáveis de Agendamento do 075
        self.h1_075_var = tk.StringVar(value="08:00")
        self.h2_075_var = tk.StringVar(value="")
        self.h3_075_var = tk.StringVar(value="")
        
        # Variáveis de Agendamento do 786
        self.h1_786_var = tk.StringVar(value="08:15")
        self.h2_786_var = tk.StringVar(value="")
        self.h3_786_var = tk.StringVar(value="")
        
        # Variáveis para os Checkboxes de Extração Manual
        self.relatorio_075_var = tk.BooleanVar(value=True)
        self.relatorio_786_var = tk.BooleanVar(value=True)
        
        self.status_var = tk.StringVar(value="Status: Aguardando comando...")
        
        self.criar_interface()
        self.carregar_configuracoes()
        
        # Inicia a thread que fica verificando os agendamentos
        self.thread_agendamento = threading.Thread(target=self.rodar_agendamentos, daemon=True)
        self.thread_agendamento.start()

    def criar_interface(self):
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # ==========================================
        # 1. ÁREA DE LOGIN 
        # ==========================================
        self.area_login = ttk.Frame(self.main_frame)
        self.area_login.pack(fill='x', pady=5)

        self.frame_form_login = ttk.Frame(self.area_login)
        self.frame_form_login.pack(pady=5)
        
        frame_campos = ttk.Frame(self.frame_form_login)
        frame_campos.pack()
        
        ttk.Label(frame_campos, text="Usuário:").grid(row=0, column=0, sticky=tk.E, padx=5, pady=5)
        ttk.Entry(frame_campos, textvariable=self.usuario_var, width=28).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_campos, text="Senha:").grid(row=1, column=0, sticky=tk.E, padx=5, pady=5)
        ttk.Entry(frame_campos, textvariable=self.senha_var, show="*", width=28).grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(self.frame_form_login, text="Salvar Credenciais", command=self.salvar_configuracoes).pack(pady=10)

        self.frame_login_minimizado = ttk.Frame(self.area_login)
        
        self.lbl_usuario_salvo = ttk.Label(self.frame_login_minimizado, text="", foreground="green")
        self.lbl_usuario_salvo.pack(side=tk.LEFT, padx=10)
        ttk.Button(self.frame_login_minimizado, text="Editar Credenciais", command=self.expandir_login).pack(side=tk.LEFT)

        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=5)

        # ==========================================
        # 2. SELEÇÃO DE RELATÓRIOS E AÇÃO MANUAL
        # ==========================================
        frame_relatorios = ttk.Frame(self.main_frame)
        frame_relatorios.pack(pady=5)
        
        ttk.Label(frame_relatorios, text="Extração Manual (Imediata):").pack(pady=5)
        
        frame_checks = ttk.Frame(frame_relatorios)
        frame_checks.pack()
        ttk.Checkbutton(frame_checks, text="Relatório 075", variable=self.relatorio_075_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(frame_checks, text="Relatório 786", variable=self.relatorio_786_var).pack(side=tk.LEFT, padx=10)

        ttk.Button(self.main_frame, text="▶ Extrair Agora", command=self.iniciar_extracao_agora, width=35).pack(pady=10)

        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=5)

        # ==========================================
        # 3. SEÇÃO DE AGENDAMENTO INDEPENDENTE
        # ==========================================
        frame_agendas_container = ttk.Frame(self.main_frame)
        frame_agendas_container.pack(fill='x', pady=5)

        # Agendamento 075 (Esquerda)
        frame_agenda_075 = ttk.LabelFrame(frame_agendas_container, text="Agendar 075 (HH:MM)")
        frame_agenda_075.pack(side=tk.LEFT, fill='both', expand=True, padx=5)
        
        ttk.Entry(frame_agenda_075, textvariable=self.h1_075_var, width=10, justify="center").pack(pady=3)
        ttk.Entry(frame_agenda_075, textvariable=self.h2_075_var, width=10, justify="center").pack(pady=3)
        ttk.Entry(frame_agenda_075, textvariable=self.h3_075_var, width=10, justify="center").pack(pady=3)

        # Agendamento 786 (Direita)
        frame_agenda_786 = ttk.LabelFrame(frame_agendas_container, text="Agendar 786 (HH:MM)")
        frame_agenda_786.pack(side=tk.RIGHT, fill='both', expand=True, padx=5)
        
        ttk.Entry(frame_agenda_786, textvariable=self.h1_786_var, width=10, justify="center").pack(pady=3)
        ttk.Entry(frame_agenda_786, textvariable=self.h2_786_var, width=10, justify="center").pack(pady=3)
        ttk.Entry(frame_agenda_786, textvariable=self.h3_786_var, width=10, justify="center").pack(pady=3)

        ttk.Button(self.main_frame, text="Salvar Agendamentos", command=self.agendar_extracao).pack(pady=10)

        # ==========================================
        # STATUS
        # ==========================================
        ttk.Label(self.main_frame, textvariable=self.status_var, foreground="blue", justify="center").pack(side=tk.BOTTOM, pady=5)

    def minimizar_login(self):
        self.frame_form_login.pack_forget() 
        self.lbl_usuario_salvo.config(text=f"✔ Logado como: {self.usuario_var.get()}")
        self.frame_login_minimizado.pack(pady=5) 

    def expandir_login(self):
        self.frame_login_minimizado.pack_forget() 
        self.frame_form_login.pack(pady=5) 

    def carregar_configuracoes(self):
        if os.path.exists(ARQUIVO_CONFIG):
            try:
                with open(ARQUIVO_CONFIG, "r") as f:
                    dados = json.load(f)
                    self.usuario_var.set(dados.get("usuario", ""))
                    self.senha_var.set(dados.get("senha", ""))
                    
                    self.h1_075_var.set(dados.get("h1_075", "08:00"))
                    self.h2_075_var.set(dados.get("h2_075", ""))
                    self.h3_075_var.set(dados.get("h3_075", ""))
                    
                    self.h1_786_var.set(dados.get("h1_786", "08:15"))
                    self.h2_786_var.set(dados.get("h2_786", ""))
                    self.h3_786_var.set(dados.get("h3_786", ""))
                    
                    self.relatorio_075_var.set(dados.get("relatorio_075", True))
                    self.relatorio_786_var.set(dados.get("relatorio_786", True))
                    
                    if self.usuario_var.get() and self.senha_var.get():
                        self.minimizar_login()
            except Exception as e:
                print(f"Erro ao carregar configurações: {e}")

    def salvar_configuracoes(self):
        usuario = self.usuario_var.get().strip()
        senha = self.senha_var.get().strip()

        if not usuario or not senha:
            messagebox.showwarning("Atenção", "Preencha usuário e senha para salvar.")
            return

        self.salvar_horarios_silencioso()
        messagebox.showinfo("Sucesso", "Credenciais e preferências salvas com sucesso!")
        self.minimizar_login()

    def salvar_horarios_silencioso(self):
        dados = {
            "usuario": self.usuario_var.get().strip(),
            "senha": self.senha_var.get().strip(),
            "h1_075": self.h1_075_var.get().strip(),
            "h2_075": self.h2_075_var.get().strip(),
            "h3_075": self.h3_075_var.get().strip(),
            "h1_786": self.h1_786_var.get().strip(),
            "h2_786": self.h2_786_var.get().strip(),
            "h3_786": self.h3_786_var.get().strip(),
            "relatorio_075": self.relatorio_075_var.get(),
            "relatorio_786": self.relatorio_786_var.get()
        }
        with open(ARQUIVO_CONFIG, "w") as f:
            json.dump(dados, f)

    def rodar_agendamentos(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def agendar_extracao(self):
        h_075 = [self.h1_075_var.get().strip(), self.h2_075_var.get().strip(), self.h3_075_var.get().strip()]
        h_786 = [self.h1_786_var.get().strip(), self.h2_786_var.get().strip(), self.h3_786_var.get().strip()]
        
        validos_075 = [h for h in h_075 if h != ""]
        validos_786 = [h for h in h_786 if h != ""]

        if not validos_075 and not validos_786:
            messagebox.showwarning("Aviso", "Preencha pelo menos um horário em algum relatório para agendar.")
            return

        try:
            schedule.clear()
            for h in validos_075:
                schedule.every().day.at(h).do(self.disparar_agendado, relatorio="075")
            for h in validos_786:
                schedule.every().day.at(h).do(self.disparar_agendado, relatorio="786")
                
            self.salvar_horarios_silencioso()
            
            resumo = ""
            if validos_075: resumo += f"075: {', '.join(validos_075)}\n"
            if validos_786: resumo += f"786: {', '.join(validos_786)}\n"
                
            self.status_var.set("Status: Agendamentos ativos em segundo plano.")
            messagebox.showinfo("Agendamento", f"Agendamentos configurados para rodar todos os dias:\n\n{resumo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Formato de hora inválido. Use HH:MM.\nErro: {e}")

    # Método acionado pelo relógio do agendador
    def disparar_agendado(self, relatorio):
        usuario = self.usuario_var.get()
        senha = self.senha_var.get()
        if not usuario or not senha:
            return # Se não tiver senha, o agendamento morre silenciosamente
        self.status_var.set(f"Status: Iniciando extração agendada do {relatorio}...")
        threading.Thread(target=self.automacao_playwright, args=(usuario, senha, [relatorio]), daemon=True).start()

    # Método acionado pelo botão manual
    def iniciar_extracao_agora(self):
        usuario = self.usuario_var.get()
        senha = self.senha_var.get()
        
        if not usuario or not senha:
            messagebox.showwarning("Atenção", "Por favor, configure o usuário e a senha antes.")
            self.expandir_login()
            return

        relatorios_selecionados = []
        if self.relatorio_075_var.get():
            relatorios_selecionados.append("075")
        if self.relatorio_786_var.get():
            relatorios_selecionados.append("786")
            
        if not relatorios_selecionados:
            messagebox.showwarning("Atenção", "Selecione pelo menos um relatório (075 ou 786) para baixar.")
            return

        self.status_var.set("Status: Iniciando extrações... Aguarde.")
        threading.Thread(target=self.automacao_playwright, args=(usuario, senha, relatorios_selecionados), daemon=True).start()

    def automacao_playwright(self, usuario, senha, lista_relatorios):
        try:
            with sync_playwright() as playwright:
                # O NAVEGADOR ESTÁ 100% INVISÍVEL
                browser = playwright.chromium.launch(headless=True) 
                
                pasta_destino = os.path.join(os.path.expanduser("~"), "Downloads")
                arquivos_baixados = []

                for codigo in lista_relatorios:
                    self.root.after(0, lambda c=codigo: self.status_var.set(f"Status: Acessando sistema para o relatório {c}..."))
                    
                    context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='pt-BR')
                    page = context.new_page()
                    
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

                    self.root.after(0, lambda c=codigo: self.status_var.set(f"Status: Extraindo relatório {c}..."))
                    
                    try:
                        page.locator("i.material-icons").filter(has_text="menu").click(timeout=3000)
                        page.wait_for_timeout(2000)
                    except:
                        pass

                    page.get_by_text("Gerencial", exact=True).click()
                    page.get_by_text("Relatório Customizado", exact=True).click()
                    page.locator("a").filter(has_text="Processar Relatório Fonte de Dado").first.click()
                    page.wait_for_timeout(4000)

                    page.locator('div[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.cdRelatorioFonteDado_header"]').click()
                    page.locator('div[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.cdRelatorioFonteDado_cell"]').get_by_text(codigo, exact=True).first.click()
                    page.locator('button[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.icAbrir"]').first.click()
                    page.wait_for_timeout(4000)
                    
                    data_completa = datetime.now().strftime("%d%m%Y")
                    mes_ano = datetime.now().strftime("%m%Y") 
                    
                    if codigo == "075":
                        campo_data_075 = page.get_by_role("textbox").nth(0)
                        campo_data_075.click(force=True)
                        page.keyboard.press("Home")
                        page.wait_for_timeout(200)
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        page.wait_for_timeout(200)
                        
                        campo_data_075.press_sequentially(mes_ano, delay=100)
                        page.keyboard.press("Tab")
                        page.wait_for_timeout(500)
                        
                        page.get_by_role("textbox", name="Grupo Faturamento (Informe 0").fill("0", force=True)
                        page.wait_for_timeout(3000)
                        
                    elif codigo == "786":
                        campo_data_inicial = page.get_by_role("textbox").nth(0)
                        campo_data_inicial.click(force=True)
                        page.keyboard.press("Home")
                        page.wait_for_timeout(200)
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        page.wait_for_timeout(200)
                        
                        campo_data_inicial.press_sequentially("01012024", delay=100) 
                        page.keyboard.press("Tab")
                        page.wait_for_timeout(500)

                        campo_data_final = page.get_by_role("textbox").nth(1)
                        campo_data_final.click(force=True)
                        page.keyboard.press("Home")
                        page.wait_for_timeout(200)
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        page.wait_for_timeout(200)
                        
                        campo_data_final.press_sequentially(data_completa, delay=100)
                        page.keyboard.press("Tab")
                        page.wait_for_timeout(2000)
                    
                    page.get_by_text("Executar", exact=True).click()

                    botao_download = page.locator('button[cfgname="acompanharExecucaoRelatorioFonteDado.acompanhar.btDownload"]')
                    botao_download.wait_for(state="visible", timeout=1200000)
                    
                    with page.expect_download(timeout=60000) as download_info:
                        botao_download.click()
                        
                    download = download_info.value
                    
                    pasta_relatorio = os.path.join(pasta_destino, f"Relatorio_{codigo}")
                    os.makedirs(pasta_relatorio, exist_ok=True)
                    
                    nome_zip = f"Download_Relatorio_{codigo}.zip"
                    caminho_zip = os.path.join(pasta_relatorio, nome_zip)
                    
                    if os.path.exists(caminho_zip):
                        os.remove(caminho_zip)

                    download.save_as(caminho_zip)
                    
                    try:
                        self.root.after(0, lambda c=codigo: self.status_var.set(f"Status: Extraindo e limpando o {c}..."))
                        with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                            lista_arquivos = zip_ref.namelist()
                            
                            if lista_arquivos:
                                nome_original_no_zip = lista_arquivos[0]
                                zip_ref.extract(nome_original_no_zip, pasta_relatorio)
                                
                                _, extensao = os.path.splitext(nome_original_no_zip)
                                nome_padronizado = f"Base_Relatorio{extensao}"
                                
                                caminho_arquivo_extraido = os.path.join(pasta_relatorio, nome_original_no_zip)
                                caminho_arquivo_padronizado = os.path.join(pasta_relatorio, nome_padronizado)
                                
                                if os.path.exists(caminho_arquivo_padronizado):
                                    os.remove(caminho_arquivo_padronizado)
                                os.rename(caminho_arquivo_extraido, caminho_arquivo_padronizado)
                                
                                # ========================================================
                                # LIMPEZA DA PLANILHA E EXCLUSÃO DE COLUNAS DO 075
                                # ========================================================
                                try:
                                    df = None
                                    if extensao.lower() in ['.xlsx', '.xls']:
                                        df = pd.read_excel(caminho_arquivo_padronizado, skiprows=3)
                                    elif extensao.lower() == '.csv':
                                        df = pd.read_csv(caminho_arquivo_padronizado, skiprows=3, sep=';')
                                        
                                    if df is not None:
                                        # Aplica a regra de negócio exclusiva do relatório 075
                                        if codigo == "075":
                                            colunas_para_remover = [
                                                "Endereço", "CEP", "Inscrição imobiliária", "Proprietário", 
                                                "CPF CNPJ Proprietário", "Telefone Residencial proprietário", 
                                                "Telefone Comercial proprietário", "Telefone Celular proprietário", 
                                                "Email proprietário", "Morador", "CPF CNPJ Morador", 
                                                "Telefone Residencial Morador", "Telefone Comercial Morador", 
                                                "Telefone Celular Morador", "Email Morador"
                                            ]
                                            
                                            # Verifica quais colunas realmente existem para evitar erros caso o sistema mude o nome
                                            colunas_presentes = [col for col in colunas_para_remover if col in df.columns]
                                            
                                            if colunas_presentes:
                                                df.drop(columns=colunas_presentes, inplace=True)
                                        
                                        # Salva o arquivo final limpo e customizado
                                        if extensao.lower() in ['.xlsx', '.xls']:
                                            df.to_excel(caminho_arquivo_padronizado, index=False)
                                        elif extensao.lower() == '.csv':
                                            df.to_csv(caminho_arquivo_padronizado, index=False, sep=';')
                                            
                                except Exception as e_planilha:
                                    print(f"Aviso: Não foi possível limpar os dados da planilha: {e_planilha}")
                                # ========================================================
                                
                        arquivos_baixados.append(f"Pasta: Relatorio_{codigo} (Arquivo limpo e pronto!)")
                        
                    except Exception as e:
                        print(f"Erro ao extrair zip do {codigo}: {e}")
                        arquivos_baixados.append(f"Erro ao extrair o {codigo}")
                    
                    context.close()

                browser.close()
                
                msg_final = "Processo concluído! Os arquivos estão em 'Downloads':\n\n" + "\n".join(arquivos_baixados)
                self.root.after(0, lambda: self.status_var.set("Status: Sucesso! Processo concluído."))
                
                # Só exibe o pop-up na tela se foi disparado pelo botão manual. 
                # Se for agendado, não trava a tela de ninguém.
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", msg_final))
                
        except Exception as e:
            erro_msg = str(e)
            self.root.after(0, lambda: self.status_var.set("Status: Erro na extração."))
            self.root.after(0, lambda erro=erro_msg: messagebox.showerror("Erro", f"Ocorreu um erro durante a extração:\n{erro}"))

if __name__ == "__main__":
    root = tk.Tk()
    app = AppAutomacao(root)
    root.mainloop()