import os
import json
import time
import zipfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import schedule
from playwright.sync_api import sync_playwright

# Arquivo onde os dados de login e configurações serão salvos
ARQUIVO_CONFIG = "config.json"

class AppAutomacao:
    def __init__(self, root):
        self.root = root
        self.root.title("Robô de Extração - Águas de Joinville")
        self.root.geometry("420x580") 
        self.root.resizable(False, False)
        
        # Variáveis da Interface
        self.usuario_var = tk.StringVar()
        self.senha_var = tk.StringVar()
        self.horario1_var = tk.StringVar(value="08:00")
        self.horario2_var = tk.StringVar(value="")
        self.horario3_var = tk.StringVar(value="")
        
        # Novas variáveis para os Checkboxes (Marcados por padrão)
        self.relatorio_075_var = tk.BooleanVar(value=True)
        self.relatorio_786_var = tk.BooleanVar(value=True)
        
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

        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=5)

        # ==========================================
        # 2. SELEÇÃO DE RELATÓRIOS E AÇÃO MANUAL
        # ==========================================
        frame_relatorios = ttk.Frame(self.main_frame)
        frame_relatorios.pack(pady=5)
        
        ttk.Label(frame_relatorios, text="Selecione os relatórios para baixar:").pack(pady=5)
        
        frame_checks = ttk.Frame(frame_relatorios)
        frame_checks.pack()
        ttk.Checkbutton(frame_checks, text="Relatório 075", variable=self.relatorio_075_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(frame_checks, text="Relatório 786", variable=self.relatorio_786_var).pack(side=tk.LEFT, padx=10)

        ttk.Button(self.main_frame, text="▶ Extrair Agora", command=self.iniciar_extracao_agora, width=35).pack(pady=10)

        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=5)

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
                    
                    # Carrega as preferências dos relatórios (padrão é True se não existir)
                    self.relatorio_075_var.set(dados.get("relatorio_075", True))
                    self.relatorio_786_var.set(dados.get("relatorio_786", True))
                    
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

        dados = {
            "usuario": usuario,
            "senha": senha,
            "horario1": self.horario1_var.get().strip(),
            "horario2": self.horario2_var.get().strip(),
            "horario3": self.horario3_var.get().strip(),
            "relatorio_075": self.relatorio_075_var.get(),
            "relatorio_786": self.relatorio_786_var.get()
        }
        with open(ARQUIVO_CONFIG, "w") as f:
            json.dump(dados, f)
            
        messagebox.showinfo("Sucesso", "Credenciais e preferências salvas com sucesso!")
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
        dados["relatorio_075"] = self.relatorio_075_var.get()
        dados["relatorio_786"] = self.relatorio_786_var.get()
        
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

        # Valida se pelo menos um relatório está marcado antes de agendar
        if not self.relatorio_075_var.get() and not self.relatorio_786_var.get():
            messagebox.showwarning("Aviso", "Marque pelo menos um relatório (075 ou 786) para poder agendar.")
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

        # Verifica quais relatórios foram selecionados na interface
        relatorios_selecionados = []
        if self.relatorio_075_var.get():
            relatorios_selecionados.append("075")
        if self.relatorio_786_var.get():
            relatorios_selecionados.append("786")
            
        if not relatorios_selecionados:
            messagebox.showwarning("Atenção", "Selecione pelo menos um relatório (075 ou 786) para baixar.")
            return

        self.status_var.set("Status: Iniciando extrações... Aguarde.")
        
        # Passamos a lista de selecionados para a função do robô
        threading.Thread(target=self.automacao_playwright, args=(usuario, senha, relatorios_selecionados), daemon=True).start()

    # ==========================================
    # DESEMPACOTAMENTO DO ZIP
    # ==========================================
    def extrair_zip_relatorio(self, caminho_zip, pasta_destino, codigo):
        """
        Extrai o zip do relatório para uma subpasta própria (Relatorio_<codigo>)
        e renomeia o arquivo mais recente extraído para um nome fixo,
        substituindo a versão anterior. Retorna o caminho final do arquivo
        (ou None se não foi possível extrair/encontrar nada).
        """
        pasta_extracao = os.path.join(pasta_destino, f"Relatorio_{codigo}")
        os.makedirs(pasta_extracao, exist_ok=True)

        with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
            zip_ref.extractall(pasta_extracao)

        # Lista apenas arquivos (ignora subpastas eventualmente criadas pelo zip)
        arquivos_extraidos = [
            os.path.join(pasta_extracao, f)
            for f in os.listdir(pasta_extracao)
            if os.path.isfile(os.path.join(pasta_extracao, f))
        ]

        if not arquivos_extraidos:
            return None

        # Pega o arquivo mais recente (por data de modificação)
        arquivo_mais_recente = max(arquivos_extraidos, key=os.path.getmtime)
        extensao = os.path.splitext(arquivo_mais_recente)[1]

        # Nome fixo: sempre o mesmo, substituindo a versão anterior
        nome_fixo = f"Relatorio_{codigo}_atual{extensao}"
        caminho_fixo = os.path.join(pasta_extracao, nome_fixo)

        if arquivo_mais_recente != caminho_fixo:
            # os.replace substitui o destino automaticamente, mesmo no Windows
            os.replace(arquivo_mais_recente, caminho_fixo)

        return caminho_fixo

    def automacao_playwright(self, usuario, senha, lista_relatorios):
        try:
            with sync_playwright() as playwright:
                # Troque headless=False para headless=True depois de validar!
                browser = playwright.chromium.launch(headless=False) 
                context = browser.new_context()
                page = context.new_page()
                
                # LOGIN INICIAL
                page.goto("https://aguasdejoinville.com.br/sansys/index.html#/")
                
                page.get_by_placeholder("Usuário").click(force=True)
                page.get_by_placeholder("Usuário").fill(usuario, force=True)
                page.get_by_placeholder("Usuário").press("Tab")
                
                page.get_by_placeholder("Senha").fill(senha, force=True)
                page.get_by_placeholder("Senha").press("Enter") 
                
                page.wait_for_timeout(2000)
                page.keyboard.press("Enter") 
                page.wait_for_timeout(5000)
                
                pasta_destino = os.path.join(os.path.expanduser("~"), "Downloads")
                arquivos_baixados = []

                # O ROBÔ VAI REPETIR TUDO ABAIXO APENAS PARA OS CÓDIGOS SELECIONADOS
                for codigo in lista_relatorios:
                    # Atualiza o status na tela
                    self.root.after(0, lambda c=codigo: self.status_var.set(f"Status: Extraindo relatório {c}..."))
                    
                    page.locator("i.material-icons", has_text="menu").click()
                    page.wait_for_timeout(3000)

                    page.get_by_text("Gerencial", exact=True).click()
                    page.get_by_text("Relatório Customizado", exact=True).click()
                    page.get_by_text("Processar Relatório Fonte de Dado", exact=True).click()
                    page.wait_for_timeout(3000)

                    page.locator('div[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.cdRelatorioFonteDado_header"]').click()
                    
                    page.locator('div[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.cdRelatorioFonteDado_cell"]').get_by_text(codigo, exact=True).first.click()
                    page.locator('button[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.icAbrir"]').first.click()
                    page.wait_for_timeout(4000)
                    
                    # ========================================================
                    # LÓGICA CONDICIONAL DOS FILTROS
                    # ========================================================
                    if codigo == "075":
                        # Filtros do 075
                        page.locator("img.x-form-date-trigger:visible").first.click()
                        page.wait_for_timeout(500) 
                        page.locator("button:visible", has_text="Hoje").first.click()
                        
                        page.get_by_role("textbox", name="Grupo Faturamento (Informe 0").fill("0", force=True)
                        page.wait_for_timeout(3000)
                        
                    elif codigo == "786":
                        # Filtros do 786
                        campo_data_inicial = page.get_by_role("textbox").nth(0)
                        campo_data_inicial.click(force=True)
                        page.wait_for_timeout(500)
                        
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        page.wait_for_timeout(200)
                        
                        campo_data_inicial.press_sequentially("01012024", delay=100) 
                        page.wait_for_timeout(1000)
                        
                        page.keyboard.press("Tab")
                        page.wait_for_timeout(500)

                        page.locator("img.x-form-date-trigger:visible").nth(1).click()
                        page.wait_for_timeout(500)
                        page.locator("button:visible", has_text="Hoje").first.click()
                        page.wait_for_timeout(2000)
                    # ========================================================
                    
                    page.get_by_text("Executar", exact=True).click()

                    botao_download = page.locator('button[cfgname="acompanharExecucaoRelatorioFonteDado.acompanhar.btDownload"]')
                    botao_download.wait_for(state="visible", timeout=1200000)
                    
                    with page.expect_download(timeout=60000) as download_info:
                        botao_download.click()
                        
                    download = download_info.value
                    
                    # Nomeia o arquivo
                    nome_renomeado = f"Relatorio_Fonte_Dado_{codigo}.zip" 
                    caminho_final = os.path.join(pasta_destino, nome_renomeado)
                    
                    if os.path.exists(caminho_final):
                        os.remove(caminho_final)

                    download.save_as(caminho_final)

                    # --- DESEMPACOTAR O ZIP ---
                    try:
                        self.root.after(0, lambda c=codigo: self.status_var.set(f"Status: Descompactando relatório {c}..."))

                        caminho_arquivo_final = self.extrair_zip_relatorio(caminho_final, pasta_destino, codigo)

                        if caminho_arquivo_final:
                            print(f"Relatório {codigo} extraído e salvo em: {caminho_arquivo_final}")
                            arquivos_baixados.append(os.path.relpath(caminho_arquivo_final, pasta_destino))
                        else:
                            print(f"Aviso: nenhum arquivo encontrado dentro de {nome_renomeado}")
                            arquivos_baixados.append(nome_renomeado)

                    except zipfile.BadZipFile:
                        print(f"Erro: {nome_renomeado} não é um arquivo zip válido (ou está corrompido).")
                        arquivos_baixados.append(f"{nome_renomeado} (falhou ao extrair)")
                    except Exception as e:
                        print(f"Erro ao extrair o zip: {e}")
                        arquivos_baixados.append(f"{nome_renomeado} (falhou ao extrair)")
                    # --------------------------------
                    
                    # Se houver mais relatórios na fila, ele recarrega a página para limpar a tela
                    if len(lista_relatorios) > 1 and codigo != lista_relatorios[-1]:
                        page.goto("https://aguasdejoinville.com.br/sansys/index.html#/")
                        page.wait_for_timeout(5000)

                # ========================================================
                # FINALIZAÇÃO
                # ========================================================
                context.close()
                browser.close()
                
                msg_final = "Arquivos salvos em Downloads:\n" + "\n".join(arquivos_baixados)
                
                self.root.after(0, lambda: self.status_var.set("Status: Sucesso! Processo concluído."))
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", msg_final))
                
        except Exception as e:
            erro_msg = str(e)
            self.root.after(0, lambda: self.status_var.set("Status: Erro na extração."))
            self.root.after(0, lambda erro=erro_msg: messagebox.showerror("Erro", f"Ocorreu um erro durante a extração:\n{erro}"))

if __name__ == "__main__":
    root = tk.Tk()
    app = AppAutomacao(root)
    root.mainloop()