import os
import json
import time
import zipfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import schedule
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright
import io            
import subprocess    

ARQUIVO_CONFIG = "config.json"

REPORTS = ["075", "468", "579", "679", "786", "918", "939"]
CAJ_WEB = ["075_Web", "989_StatusCliente", "989_Encerrado"]
BACKLOGS = ["Fiscalizacao", "Notificacao"]
TODOS_RELATORIOS = REPORTS + CAJ_WEB + BACKLOGS

DEFAULT_H1 = {
    "075": "08:00", "468": "08:15", "579": "08:30", "679": "08:45", "786": "08:48", "918": "08:52", "939": "08:54",
    "075_Web": "08:55", "989_StatusCliente": "09:00", "989_Encerrado": "09:05",
    "Fiscalizacao": "09:10", "Notificacao": "09:15"
}

NOMES_FINAIS = {
    "075": "Rel-075",
    "075_Web": "Rel-075-Web",
    "786": "Rel-786",
    "468": "Rel-468",
    "579": "Rel-579",
    "918": "Rel-918",  
    "679": "Rel-679", 
    "939": "Rel-939",  
    "989_StatusCliente": "Rel-989-StatusCliente",
    "989_Encerrado": "Rel-989-Encerrado",
    "Fiscalizacao": "Backlog-Fisc",
    "Notificacao": "Backlog-Not"
}

COLUNAS_REMOVER = {
    "075": [
        "Endereço", "CEP", "Inscrição imobiliária", "Proprietário",
        "CPF CNPJ Proprietário", "Telefone Residencial proprietário",
        "Telefone Comercial proprietário", "Telefone Celular proprietário",
        "Email proprietário", "Morador", "CPF CNPJ Morador",
        "Telefone Residencial Morador", "Telefone Comercial Morador",
        "Telefone Celular Morador", "Email Morador"
    ],
}

TIMEOUT_PROCESSAMENTO_MS = 1200000


class AppAutomacao:
    def __init__(self, root):
        self.root = root
        self.root.title("Robô de Relatórios - CAJ")
        self.root.geometry("720x760")
        self.root.resizable(False, False)

        self.usuario_var = tk.StringVar()
        self.senha_var = tk.StringVar()
        self.caminho_var = tk.StringVar()

        self.horarios = {
            codigo: [tk.StringVar(value=DEFAULT_H1[codigo] if i == 0 else "") for i in range(3)]
            for codigo in TODOS_RELATORIOS
        }
        self.relatorio_vars = {codigo: tk.BooleanVar(value=True) for codigo in TODOS_RELATORIOS}
        self.status_var = tk.StringVar(value="Status: Aguardando comando...")

        self.criar_interface()
        self.carregar_configuracoes()

        self.thread_agendamento = threading.Thread(target=self.rodar_agendamentos, daemon=True)
        self.thread_agendamento.start()

    # ------------------------------------------------------------------ UI
    def criar_interface(self):
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.area_login = ttk.Frame(self.main_frame)
        self.area_login.pack(fill='x', pady=5)

        self.frame_form_login = ttk.Frame(self.area_login)
        self.frame_form_login.pack(pady=5)

        frame_campos = ttk.Frame(self.frame_form_login)
        frame_campos.pack()
        ttk.Label(frame_campos, text="Usuário:").grid(row=0, column=0, sticky=tk.E, padx=5, pady=5)
        ttk.Entry(frame_campos, textvariable=self.usuario_var, width=28).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(frame_campos, text="Senha:").grid(row=1, column=0, sticky=tk.E, padx=5, pady=5)
        ttk.Entry(frame_campos, textvariable=self.senha_var, show="*", width=28).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(frame_campos, text="Salvar em:").grid(row=2, column=0, sticky=tk.E, padx=5, pady=5)
        frame_dir = ttk.Frame(frame_campos)
        frame_dir.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(frame_dir, textvariable=self.caminho_var, width=35).pack(side=tk.LEFT)
        ttk.Button(frame_dir, text="📁", width=3, command=self.selecionar_pasta).pack(side=tk.LEFT, padx=3)

        ttk.Button(self.frame_form_login, text="Salvar Credenciais e Pasta", command=self.salvar_configuracoes).pack(pady=10)

        self.frame_login_minimizado = ttk.Frame(self.area_login)
        self.lbl_usuario_salvo = ttk.Label(self.frame_login_minimizado, text="", foreground="green")
        self.lbl_usuario_salvo.pack(side=tk.LEFT, padx=10)
        ttk.Button(self.frame_login_minimizado, text="Editar Credenciais/Pasta", command=self.expandir_login).pack(side=tk.LEFT)

        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=5)

        #  FRAME SUPERIOR ÀS ABAS (Com o botão discreto à direita)
        frame_top_abas = ttk.Frame(self.main_frame)
        frame_top_abas.pack(fill='x', pady=(5, 0))

        self.marcar_todos_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame_top_abas, 
            text="Selecionar Todos", 
            variable=self.marcar_todos_var, 
            command=self.alternar_todos
        ).pack(side=tk.RIGHT, padx=5)

        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True, pady=5)

        self.aba_gerenciais = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.aba_gerenciais, text="Gerenciais")
        self.montar_aba_relatorios(self.aba_gerenciais, REPORTS, 4)

        self.aba_caj_web = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.aba_caj_web, text="CAJ Web")
        self.montar_aba_relatorios(self.aba_caj_web, CAJ_WEB, 3)

        self.aba_backlogs = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.aba_backlogs, text="Backlogs")
        self.montar_aba_relatorios(self.aba_backlogs, BACKLOGS, 2)

        frame_botoes = ttk.Frame(self.main_frame)
        frame_botoes.pack(fill='x', pady=10)
        
        ttk.Button(frame_botoes, text="Extrair Relatórios Marcados", command=self.iniciar_extracao_agora, width=35).pack(pady=5)
        ttk.Button(frame_botoes, text="Salvar Todos os Agendamentos", command=self.agendar_extracao, width=35).pack(pady=5)

        self.status_var = tk.StringVar(value="Status: Aguardando comando...")
        ttk.Label(self.main_frame, textvariable=self.status_var, foreground="blue", justify="center").pack(side=tk.BOTTOM, pady=5)

    #  FUNÇÃO QUE ALTERNA TODAS AS CAIXINHAS AO MESMO TEMPO
    def alternar_todos(self):
        estado = self.marcar_todos_var.get()
        for var in self.relatorio_vars.values():
            var.set(estado)

    def montar_aba_relatorios(self, aba, lista_codigos, colunas_grid):
        ttk.Label(aba, text="Selecionar para Extração Imediata:").pack(pady=5)
        frame_checks = ttk.Frame(aba)
        frame_checks.pack(pady=5)
        for codigo in lista_codigos:
            ttk.Checkbutton(frame_checks, text=codigo, variable=self.relatorio_vars[codigo]).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(aba, orient='horizontal').pack(fill='x', pady=10)
        
        ttk.Label(aba, text="Horários de Agendamento (HH:MM):").pack(pady=5)
        frame_grid = ttk.Frame(aba)
        frame_grid.pack(fill='both', expand=True)
        
        for i in range(colunas_grid):
            frame_grid.grid_columnconfigure(i, weight=1)
        
        for index, codigo in enumerate(lista_codigos):
            row = index // colunas_grid
            col = index % colunas_grid
            frame = ttk.LabelFrame(frame_grid, text=f"Agendar {codigo}")
            frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            for var in self.horarios[codigo]:
                ttk.Entry(frame, textvariable=var, width=12, justify="center").pack(pady=2)

    def selecionar_pasta(self):
        pasta_selecionada = filedialog.askdirectory(title="Selecione onde os relatórios serão salvos")
        if pasta_selecionada:
            self.caminho_var.set(os.path.normpath(pasta_selecionada))

    def minimizar_login(self):
        self.frame_form_login.pack_forget()
        self.lbl_usuario_salvo.config(text=f"Usuário: {self.usuario_var.get()} | Pasta Configurada")
        self.frame_login_minimizado.pack(pady=5)

    def expandir_login(self):
        self.frame_login_minimizado.pack_forget()
        self.frame_form_login.pack(pady=5)

    # ------------------------------------------------------------ Config & Schedule
    def carregar_configuracoes(self):
        if not os.path.exists(ARQUIVO_CONFIG):
            self.caminho_var.set(os.path.join(os.path.expanduser("~"), "Downloads"))
            return
        try:
            with open(ARQUIVO_CONFIG, "r") as f:
                dados = json.load(f)

            self.usuario_var.set(dados.get("usuario", ""))
            self.senha_var.set(dados.get("senha", ""))
            self.caminho_var.set(dados.get("caminho_destino", os.path.join(os.path.expanduser("~"), "Downloads")))

            for codigo in TODOS_RELATORIOS:
                for i, var in enumerate(self.horarios[codigo]):
                    padrao = DEFAULT_H1.get(codigo, "") if i == 0 else ""
                    var.set(dados.get(f"h{i + 1}_{codigo}", padrao))
                self.relatorio_vars[codigo].set(dados.get(f"relatorio_{codigo}", True))

            if self.usuario_var.get() and self.senha_var.get() and self.caminho_var.get():
                self.minimizar_login()
        except Exception as e:
            print(f"Erro ao carregar: {e}")

    def salvar_configuracoes(self):
        usuario, senha, caminho = self.usuario_var.get().strip(), self.senha_var.get().strip(), self.caminho_var.get().strip()
        if not usuario or not senha or not caminho:
            messagebox.showwarning("Atenção", "Preencha usuário, senha e escolha a pasta para salvar.")
            return
        self.salvar_horarios_silencioso()
        messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
        self.minimizar_login()

    def salvar_horarios_silencioso(self):
        dados = {
            "usuario": self.usuario_var.get().strip(), 
            "senha": self.senha_var.get().strip(),
            "caminho_destino": self.caminho_var.get().strip()
        }
        for codigo in TODOS_RELATORIOS:
            for i, var in enumerate(self.horarios[codigo]):
                dados[f"h{i + 1}_{codigo}"] = var.get().strip()
            dados[f"relatorio_{codigo}"] = self.relatorio_vars[codigo].get()
        with open(ARQUIVO_CONFIG, "w") as f:
            json.dump(dados, f)

    def rodar_agendamentos(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def agendar_extracao(self):
        validos = {c: [h.get().strip() for h in self.horarios[c] if h.get().strip()] for c in TODOS_RELATORIOS}
        if not any(validos.values()):
            messagebox.showwarning("Aviso", "Preencha pelo menos um horário.")
            return
        try:
            schedule.clear()
            for codigo, horas in validos.items():
                for h in horas:
                    schedule.every().day.at(h).do(self.disparar_agendado, relatorio=codigo)
            self.salvar_horarios_silencioso()
            self.status_var.set("Status: Agendamentos ativos em segundo plano.")
            messagebox.showinfo("Sucesso", "Agendamentos configurados!")
        except Exception as e:
            messagebox.showerror("Erro", f"Formato de hora inválido.\nErro: {e}")

    def disparar_agendado(self, relatorio):
        usuario, senha, caminho = self.usuario_var.get(), self.senha_var.get(), self.caminho_var.get()
        if not usuario or not senha or not caminho:
            return
        self.status_var.set(f"Status: Iniciando extração agendada de {relatorio}...")

        def rodar():
            if relatorio in REPORTS + CAJ_WEB:
                resultados = self.automacao_playwright(usuario, senha, caminho, [relatorio])
            else:
                resultados = self.automacao_backlogs(usuario, senha, caminho, [relatorio])
            self.root.after(0, lambda: self.mostrar_resumo_final(resultados, caminho))

        threading.Thread(target=rodar, daemon=True).start()

    def iniciar_extracao_agora(self):
        usuario, senha, caminho = self.usuario_var.get(), self.senha_var.get(), self.caminho_var.get()
        if not usuario or not senha or not caminho:
            messagebox.showwarning("Atenção", "Configure o usuário, senha e pasta.")
            self.expandir_login()
            return

        lista_playwright = [c for c in REPORTS + CAJ_WEB if self.relatorio_vars[c].get()]
        lista_backlogs = [c for c in BACKLOGS if self.relatorio_vars[c].get()]

        if not lista_playwright and not lista_backlogs:
            messagebox.showwarning("Atenção", "Selecione pelo menos um relatório.")
            return

        self.status_var.set("Status: Iniciando extrações... Aguarde.")
        threading.Thread(target=self.rotear_extracoes_manuais, args=(usuario, senha, caminho, lista_playwright, lista_backlogs), daemon=True).start()

    def rotear_extracoes_manuais(self, usuario, senha, caminho_destino, lista_playwright, lista_backlogs):
        # Cada função de automação agora retorna uma lista de tuplas
        # (codigo, sucesso: bool, mensagem_erro: str) — um item por relatório,
        # independentemente de outros itens terem falhado.
        resultados_totais = []

        def rodar_playwright():
            resultados_totais.extend(
                self.automacao_playwright(usuario, senha, caminho_destino, lista_playwright)
            )

        def rodar_backlogs():
            resultados_totais.extend(
                self.automacao_backlogs(usuario, senha, caminho_destino, lista_backlogs)
            )

        if lista_playwright:
            t_play = threading.Thread(target=rodar_playwright)
            t_play.start()
            t_play.join()

        if lista_backlogs:
            t_backlog = threading.Thread(target=rodar_backlogs)
            t_backlog.start()
            t_backlog.join()

        self.root.after(0, lambda: self.mostrar_resumo_final(resultados_totais, caminho_destino))

    def mostrar_resumo_final(self, resultados, caminho_destino):
        """Monta e exibe o resumo detalhado por relatório, no formato:
        Rel-075: Concluído com sucesso
        Rel-939: Falha em "Aguardando processamento do relatório" - Timeout ...
        """
        if not resultados:
            self.status_var.set("Status: Nenhum relatório foi processado.")
            messagebox.showwarning("Atenção", "Nenhum relatório foi processado.")
            return

        linhas = []
        houve_sucesso = False
        houve_falha = False

        for codigo, sucesso, etapa, motivo in resultados:
            nome = NOMES_FINAIS.get(codigo, codigo)
            if sucesso:
                houve_sucesso = True
                linhas.append(f"✅ {nome}: Concluído com sucesso")
            else:
                houve_falha = True
                motivo_curto = (motivo or "motivo desconhecido").strip()
                if len(motivo_curto) > 160:
                    motivo_curto = motivo_curto[:160] + "..."
                if etapa:
                    linhas.append(f'❌ {nome}: Falha em "{etapa}" - {motivo_curto}')
                else:
                    linhas.append(f"❌ {nome}: Falha - {motivo_curto}")

        texto_resumo = "\n".join(linhas)

        if houve_falha and houve_sucesso:
            titulo = "Extração Concluída com Falhas"
        elif houve_falha:
            titulo = "Falha na Extração"
        else:
            titulo = "Extração Concluída"

        self.status_var.set(f"Status: {titulo}.")
        messagebox.showinfo(titulo, f"{texto_resumo}\n\nSalvos em:\n{caminho_destino}")

    def clicar_visivel(self, locator):
        try:
            locator.first.wait_for(state="attached", timeout=8000)
        except: pass 
        for i in range(locator.count()):
            if locator.nth(i).is_visible():
                try:
                    locator.nth(i).click()
                    return
                except: pass
        if locator.count() > 0:
            locator.last.click(force=True)

    def selecionar_opcao_combo_extjs(self, page, locator_campo, texto_opcao, timeout=3000):
        """Para combos ExtJS 'somente-seleção' (ex: 'Pesquisar Por:'), onde o campo
        mostra 'Selecione...' e não aceita digitação/fill() - só aceita clicar
        numa opção da lista que abre ao clicar no campo. Abre a lista e clica
        no texto exato da opção desejada."""
        try:
            self.clicar_visivel(locator_campo)
            page.wait_for_timeout(500)
            opcao = page.get_by_text(texto_opcao, exact=True)
            opcao.first.click(timeout=timeout)
            page.wait_for_timeout(500)
        except Exception as e:
            print(f"Não foi possível selecionar '{texto_opcao}' no combo: {e}")
            raise

    # --------------------------------------------------------- PREENCHIMENTO E FILTROS
    def preencher_campo_robusto(self, page, locator, valor, delay=50):
        try:
            locator.click(force=True, timeout=2000)
            locator.focus()
            page.wait_for_timeout(200)
            locator.press("Control+a")
            page.wait_for_timeout(200)
            locator.press("Delete")
            page.wait_for_timeout(200)
            
            page.keyboard.press("Home")
            for _ in range(10):
                page.keyboard.press("ArrowLeft")
            page.wait_for_timeout(100)
            
            locator.press_sequentially(valor, delay=delay)
            page.wait_for_timeout(400)
            page.keyboard.press("Enter")
            page.keyboard.press("Tab")
            page.wait_for_timeout(600)
        except Exception as e:
            print(f"Erro ao preencher: {e}")

    def preencher_campo_data(self, page, indice, valor, delay=50):
        campo = page.get_by_role("textbox").nth(indice)
        self.preencher_campo_robusto(page, campo, valor, delay)

    def preencher_campo_data_forcado(self, page, indice, valor, delay=50):
        """Versão reforçada de preencher_campo_data: usada em campos que não
        aceitam sobrescrita direta (ex: VOL_FATURADO do 679). Limpa com
        fill('') antes, confere se realmente esvaziou e, se sobrar algo,
        reforça com Ctrl+A + Delete + Backspace - mesma lógica aplicada
        nos campos corrigidos do Backlog."""
        campo = page.get_by_role("textbox").nth(indice)

        try:
            campo.fill("", force=True)
        except:
            pass
        page.wait_for_timeout(250)

        try:
            valor_atual = campo.input_value()
        except:
            valor_atual = ""

        if valor_atual.strip():
            campo.click(force=True, timeout=2000)
            page.wait_for_timeout(200)
            page.keyboard.press("Control+a")
            page.wait_for_timeout(200)
            page.keyboard.press("Delete")
            page.wait_for_timeout(200)
            page.keyboard.press("Backspace")
            page.wait_for_timeout(300)

        self.preencher_campo_robusto(page, campo, valor, delay)

    def preencher_filtros(self, page, codigo, datas):
        if codigo in ["075", "075_Web"]:
            self.preencher_campo_data(page, 0, datas["mes_ano"])
            
            campo_grupo = page.get_by_role("textbox", name="Grupo Faturamento (Informe 0")
            campo_grupo.click(force=True)
            page.keyboard.press("Home")
            for _ in range(10): page.keyboard.press("ArrowLeft")
            campo_grupo.fill("0", force=True)
            page.wait_for_timeout(3000)
            
        elif codigo == "786":
            self.preencher_campo_data(page, 0, "01012024")
            self.preencher_campo_data(page, 1, datas["data_completa"])
            
        elif codigo == "468":
            self.preencher_campo_data(page, 0, datas["primeiro_dia_ano"])
            
        elif codigo == "579":
            self.preencher_campo_data(page, 0, datas["mes_ano_barra"])
            
        elif codigo == "918":
            self.preencher_campo_data(page, 0, datas["primeiro_dia_ano"])
            self.preencher_campo_data(page, 1, datas["data_completa"])

        elif codigo == "679":
            self.preencher_campo_data(page, 0, datas["mes_ano_barra"])
            self.preencher_campo_data_forcado(page, 1, "Sim", delay=100)
            
        elif codigo == "939":
            self.preencher_campo_data(page, 0, datas["primeiro_julho_ano"])
            self.preencher_campo_data(page, 1, datas["data_completa"])
            
        elif codigo in ["989_StatusCliente", "989_Encerrado"]:
            codigos_str = "14931,14903,14901,14654,14633,14631,14605,14604,14603,14601,14271,14261,14254,14233,14231,14213,14211,14203,14201"
            self.preencher_campo_data(page, 0, codigos_str, delay=10)
            self.preencher_campo_data(page, 1, "01012025")
            self.preencher_campo_data(page, 2, datas["data_completa"])
            self.preencher_campo_data(page, 3, "S")
            
            status = "A" if codigo == "989_StatusCliente" else "E"
            self.preencher_campo_data(page, 4, status)

    def automacao_playwright(self, usuario, senha, pasta_destino, lista_relatorios):
        """Processa cada relatório de forma isolada: uma falha em um relatório
        NÃO interrompe os demais. Retorna uma lista de tuplas
        (codigo, sucesso, etapa_onde_parou, mensagem_de_erro)."""
        resultados = []

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel="msedge", headless=True)

                datas = {
                    "data_completa": datetime.now().strftime("%d%m%Y"),
                    "mes_ano": datetime.now().strftime("%m%Y"),
                    "mes_ano_barra": datetime.now().strftime("%m/%Y"),
                    "primeiro_dia_ano": datetime.now().strftime("0101%Y"),
                    "primeiro_julho_ano": datetime.now().strftime("0107%Y")
                }

                for codigo in lista_relatorios:
                    etapa_atual = "Abrindo navegador/contexto"
                    context = None
                    try:
                        if codigo == "075_Web":
                            codigo_sistema = "075"
                        elif codigo.startswith("989"):
                            codigo_sistema = "989"
                        else:
                            codigo_sistema = codigo

                        self.root.after(0, lambda c=codigo: self.status_var.set(f"Acessando Sistema para: {c}..."))
                        context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='pt-BR')
                        page = context.new_page()

                        etapa_atual = "Login no sistema"
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

                        self.root.after(0, lambda c=codigo: self.status_var.set(f"Extraindo: {c}..."))

                        etapa_atual = "Abrindo menu Gerencial"
                        try:
                            self.clicar_visivel(page.locator("i.material-icons").filter(has_text="menu"))
                            page.wait_for_timeout(2000)
                        except: pass

                        self.clicar_visivel(page.get_by_text("Gerencial", exact=True))
                        page.wait_for_timeout(1000)
                        self.clicar_visivel(page.get_by_text("Relatório Customizado", exact=True))
                        page.wait_for_timeout(1000)
                        self.clicar_visivel(page.locator("a").filter(has_text="Processar Relatório Fonte de Dado"))
                        page.wait_for_timeout(4000)

                        etapa_atual = f"Selecionando relatório {codigo_sistema} na grade"
                        self.clicar_visivel(page.locator('div[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.cdRelatorioFonteDado_header"]'))
                        page.wait_for_timeout(1000)

                        self.clicar_visivel(page.locator('div[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.cdRelatorioFonteDado_cell"]').get_by_text(codigo_sistema, exact=True))
                        page.wait_for_timeout(1000)

                        self.clicar_visivel(page.locator('button[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.icAbrir"]'))
                        page.wait_for_timeout(4000)

                        etapa_atual = "Preenchendo filtros do relatório"
                        self.preencher_filtros(page, codigo, datas)

                        etapa_atual = "Executando o relatório"
                        for _ in range(4):
                            self.clicar_visivel(page.get_by_text("Executar", exact=True))
                            try:
                                page.locator("text=Execução do seu relatório").wait_for(state="attached", timeout=3000)
                                break
                            except:
                                pass

                        etapa_atual = "Aguardando processamento do relatório"
                        page.locator("text=Você já pode fazer o download").wait_for(
                            state="attached", timeout=TIMEOUT_PROCESSAMENTO_MS
                        )
                        page.wait_for_timeout(2000)

                        etapa_atual = "Baixando arquivo"
                        with page.expect_download(timeout=300000) as download_info:
                            botoes_dl = page.locator("button").filter(has_text="Download")
                            for i in range(botoes_dl.count() - 1, -1, -1):
                                btn = botoes_dl.nth(i)
                                if btn.is_visible():
                                    btn.click(force=True)
                                    page.wait_for_timeout(500)
                                    btn.click(force=True)
                                    break
                            else:
                                botoes_dl.last.click(force=True)

                        download = download_info.value

                        if codigo == "075_Web":
                            nome_pasta = "Relatorio_web"
                        elif codigo.startswith("989"):
                            nome_pasta = "Relatorio_989"
                        else:
                            nome_pasta = f"Relatorio_{codigo}"

                        pasta_relatorio = os.path.join(pasta_destino, nome_pasta)
                        os.makedirs(pasta_relatorio, exist_ok=True)

                        import tempfile
                        pasta_temp = tempfile.gettempdir()
                        nome_sugerido = download.suggested_filename
                        caminho_temp_salvo = os.path.join(pasta_temp, nome_sugerido)

                        if os.path.exists(caminho_temp_salvo):
                            try: os.remove(caminho_temp_salvo)
                            except: pass

                        download.save_as(caminho_temp_salvo)

                        etapa_atual = "Limpando e salvando a planilha final"
                        self.root.after(0, lambda c=codigo: self.status_var.set(f"Limpando e Consolidando o {c}..."))

                        caminho_bruto_temp = self.padronizar_arquivo_temp(caminho_temp_salvo, pasta_temp)

                        nome_base = NOMES_FINAIS.get(codigo, f"Relatorio_{codigo}")
                        caminho_final_onedrive = os.path.join(pasta_relatorio, f"{nome_base}.xlsx")

                        self.limpar_planilha_direto(caminho_bruto_temp, caminho_final_onedrive, codigo)

                        resultados.append((codigo, True, "", ""))

                    except Exception as e:
                        mensagem = str(e).splitlines()[0] if str(e) else "Erro desconhecido"
                        print(f"Falha ao extrair {codigo} na etapa '{etapa_atual}': {e}")
                        resultados.append((codigo, False, etapa_atual, mensagem))
                        self.root.after(
                            0,
                            lambda c=codigo, et=etapa_atual: self.status_var.set(
                                f"Falha em {c} ({et}). Seguindo para o próximo..."
                            )
                        )
                    finally:
                        if context is not None:
                            try:
                                context.close()
                            except: pass

                browser.close()

        except Exception as e:
            # Falha catastrófica (ex: navegador não abriu). Marca como falha
            # qualquer relatório desta lista que ainda não tenha um resultado.
            ja_processados = {r[0] for r in resultados}
            for codigo in lista_relatorios:
                if codigo not in ja_processados:
                    resultados.append((codigo, False, "Inicialização do navegador", str(e)))
            self.root.after(0, lambda: self.status_var.set("Erro geral na extração Playwright."))

        return resultados

    # --------------------------------------------------------- Automação Backlogs
    def automacao_backlogs(self, usuario, senha, pasta_destino, lista_backlogs):
        """Mesma lógica de isolamento por item usada em automacao_playwright."""
        resultados = []

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel="msedge", headless=True)

                for tipo in lista_backlogs:
                    etapa_atual = "Abrindo navegador/contexto"
                    context = None
                    try:
                        self.root.after(0, lambda t=tipo: self.status_var.set(f"Extraindo Backlog: {t}..."))

                        context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='pt-BR')
                        page = context.new_page()

                        etapa_atual = "Login no sistema"
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

                        etapa_atual = "Abrindo menu Operacional > Serviços > Relatórios"
                        try:
                            self.clicar_visivel(page.locator("i.material-icons").filter(has_text="menu"))
                            page.wait_for_timeout(2000)
                        except: pass

                        self.clicar_visivel(page.get_by_text("Operacional", exact=True))
                        page.wait_for_timeout(1000)
                        self.clicar_visivel(page.get_by_text("Serviços", exact=True))
                        page.wait_for_timeout(1000)
                        self.clicar_visivel(page.get_by_text("Relatórios", exact=True))
                        page.wait_for_timeout(1000)
                        self.clicar_visivel(page.locator("a").filter(has_text="OPE0002"))
                        page.wait_for_timeout(6000)

                        etapa_atual = "Preenchendo filtros do backlog"
                        try:
                            # ".x-form-item" pode conter mais de um <input> (o campo visível
                            # do combobox ExtJS + um input oculto de valor). Usamos .first
                            # para sempre agir sobre o mesmo elemento e evitar que o
                            # Ctrl+A/Delete seja enviado para o elemento errado.
                            campo_servicos_todos = page.locator(".x-form-item").filter(has_text="Serviços de:").locator("input")
                            self.clicar_visivel(campo_servicos_todos)
                            page.wait_for_timeout(300)

                            campo_servicos = campo_servicos_todos.first

                            # 1ª tentativa: limpar direto pelo valor (não depende de foco/teclado,
                            # funciona mesmo se o Ctrl+A não estiver pegando no combobox).
                            try:
                                campo_servicos.fill("", force=True)
                            except:
                                pass
                            page.wait_for_timeout(250)

                            # Confere se realmente limpou. Se ainda tiver "Selecione..." ou
                            # qualquer outro texto, força Ctrl+A + Delete como reforço.
                            try:
                                valor_atual = campo_servicos.input_value()
                            except:
                                valor_atual = ""

                            if valor_atual.strip():
                                campo_servicos.click(force=True, timeout=2000)
                                page.wait_for_timeout(200)
                                page.keyboard.press("Control+a")
                                page.wait_for_timeout(200)
                                page.keyboard.press("Delete")
                                page.wait_for_timeout(200)
                                page.keyboard.press("Backspace")
                                page.wait_for_timeout(300)

                            self.preencher_campo_robusto(page, campo_servicos, "Unidade Comercial")
                        except: pass

                        try:
                            campo_pesquisa_todos = page.locator('input[cfgname="relOPE0002.relatorio.tpPesquisa"]')
                            self.clicar_visivel(campo_pesquisa_todos)
                            page.wait_for_timeout(300)

                            campo_pesquisa = campo_pesquisa_todos.first

                            try:
                                campo_pesquisa.fill("", force=True)
                            except:
                                pass
                            page.wait_for_timeout(250)

                            try:
                                valor_atual = campo_pesquisa.input_value()
                            except:
                                valor_atual = ""

                            if valor_atual.strip():
                                campo_pesquisa.click(force=True, timeout=2000)
                                page.wait_for_timeout(200)
                                page.keyboard.press("Control+a")
                                page.wait_for_timeout(200)
                                page.keyboard.press("Delete")
                                page.wait_for_timeout(200)
                                page.keyboard.press("Backspace")
                                page.wait_for_timeout(300)

                            self.preencher_campo_robusto(page, campo_pesquisa, "Empresa")
                        except: pass

                        try:
                            page.get_by_text("01 - CIA AGUAS DE JOINVILLE").dblclick(timeout=2000)
                            page.wait_for_timeout(500)
                        except: pass

                        try:
                            campo_data_ini = page.get_by_role("textbox", name="Período Solicitação Inicial:")
                            self.preencher_campo_robusto(page, campo_data_ini, "01012025")
                        except: pass

                        try:
                            data_hoje = datetime.now().strftime("%d%m%Y")
                            campo_data_fim = page.get_by_role("textbox", name="Período Solicitação Final:")
                            self.preencher_campo_robusto(page, campo_data_fim, data_hoje)
                        except: pass

                        if tipo == "Fiscalizacao":
                            situacoes = ["Para Reprogramar", "Pendente", "Postergada", "Programado"]
                            texto_setor = "CIA - CFC"
                        else:
                            situacoes = ["Pendente", "Postergada", "Programado"]
                            texto_setor = "CIA - CFC Notificação"

                        for sit in situacoes:
                            try:
                                page.get_by_text(sit, exact=True).dblclick(timeout=1000)
                            except: pass

                        try:
                            campo_setor_todos = page.locator('input[cfgname="relOPE0002.relatorio.opeSetorOperacional"]')
                            self.clicar_visivel(campo_setor_todos)
                            page.wait_for_timeout(300)

                            campo_setor = campo_setor_todos.first

                            try:
                                campo_setor.fill("", force=True)
                            except:
                                pass
                            page.wait_for_timeout(250)

                            try:
                                valor_atual = campo_setor.input_value()
                            except:
                                valor_atual = ""

                            if valor_atual.strip():
                                campo_setor.click(force=True, timeout=2000)
                                page.wait_for_timeout(200)
                                page.keyboard.press("Control+a")
                                page.wait_for_timeout(200)
                                page.keyboard.press("Delete")
                                page.wait_for_timeout(200)
                                page.keyboard.press("Backspace")
                                page.wait_for_timeout(300)

                            self.preencher_campo_robusto(page, campo_setor, texto_setor)
                        except: pass

                        try:
                            campo_formato_todos = page.locator('input[cfgname="relOPE0002.relatorio.relFormatoRelatorio"]')
                            self.clicar_visivel(campo_formato_todos)
                            page.wait_for_timeout(300)

                            campo_formato = campo_formato_todos.first

                            try:
                                campo_formato.fill("", force=True)
                            except:
                                pass
                            page.wait_for_timeout(250)

                            try:
                                valor_atual = campo_formato.input_value()
                            except:
                                valor_atual = ""

                            if valor_atual.strip():
                                campo_formato.click(force=True, timeout=2000)
                                page.wait_for_timeout(200)
                                page.keyboard.press("Control+a")
                                page.wait_for_timeout(200)
                                page.keyboard.press("Delete")
                                page.wait_for_timeout(200)
                                page.keyboard.press("Backspace")
                                page.wait_for_timeout(300)

                            self.preencher_campo_robusto(page, campo_formato, "EXCEL")
                        except: pass

                        page.wait_for_timeout(2000)

                        etapa_atual = "Confirmando e baixando o arquivo"
                        with page.expect_download(timeout=300000) as download_info:
                            self.clicar_visivel(page.get_by_role("button", name="Confirmar"))

                        download = download_info.value

                        pasta_relatorio = os.path.join(pasta_destino, f"Relatorio_{tipo}")
                        os.makedirs(pasta_relatorio, exist_ok=True)

                        nome_base = NOMES_FINAIS.get(tipo, f"Backlog_{tipo}")

                        import tempfile
                        pasta_temp = tempfile.gettempdir()
                        caminho_temp_xls = os.path.join(pasta_temp, f"{nome_base}_bruto.xls")

                        caminho_final_onedrive = os.path.join(pasta_relatorio, f"{nome_base}.xlsx")

                        if os.path.exists(caminho_temp_xls):
                            try: os.remove(caminho_temp_xls)
                            except: pass

                        download.save_as(caminho_temp_xls)

                        etapa_atual = "Limpando e salvando a planilha final"
                        self.root.after(0, lambda t=tipo: self.status_var.set(f"Limpando o Backlog {t}..."))
                        self.limpar_planilha_direto(caminho_temp_xls, caminho_final_onedrive, tipo)

                        page.wait_for_timeout(2000)

                        resultados.append((tipo, True, "", ""))

                    except Exception as e:
                        mensagem = str(e).splitlines()[0] if str(e) else "Erro desconhecido"
                        print(f"Falha ao extrair backlog {tipo} na etapa '{etapa_atual}': {e}")
                        resultados.append((tipo, False, etapa_atual, mensagem))
                        self.root.after(
                            0,
                            lambda t=tipo, et=etapa_atual: self.status_var.set(
                                f"Falha em {t} ({et}). Seguindo para o próximo..."
                            )
                        )
                    finally:
                        if context is not None:
                            try:
                                context.close()
                            except: pass

                browser.close()

        except Exception as e:
            ja_processados = {r[0] for r in resultados}
            for tipo in lista_backlogs:
                if tipo not in ja_processados:
                    resultados.append((tipo, False, "Inicialização do navegador", str(e)))
            self.root.after(0, lambda: self.status_var.set("Erro geral na extração dos Backlogs."))

        return resultados

    # ---------------------------------------------------- Pós-processamento Otimizado
    def padronizar_arquivo_temp(self, caminho_salvo_temp, pasta_temp):
        _, extensao_sugerida = os.path.splitext(caminho_salvo_temp)
        
        if extensao_sugerida.lower() == '.zip':
            with zipfile.ZipFile(caminho_salvo_temp, 'r') as zip_ref:
                lista_arquivos = zip_ref.namelist()
                nome_original_no_zip = lista_arquivos[0]
                zip_ref.extract(nome_original_no_zip, pasta_temp)

            caminho_extraido = os.path.join(pasta_temp, nome_original_no_zip)
            try: os.remove(caminho_salvo_temp)
            except: pass
            return caminho_extraido
        else:
            return caminho_salvo_temp

    def limpar_planilha_direto(self, caminho_temp, caminho_final_onedrive, codigo):
        try:
            if codigo == "679":
                linhas_pular = None 
            elif codigo in ["Fiscalizacao", "Notificacao"]:
                linhas_pular = 4
            else:
                linhas_pular = 3

            if caminho_temp.endswith(('.xlsx', '.xls')): 
                with open(caminho_temp, 'rb') as f:
                    df = pd.read_excel(f, skiprows=linhas_pular)
            elif caminho_temp.endswith('.csv'): 
                with open(caminho_temp, 'r', encoding='utf-8', errors='ignore') as f:
                    df = pd.read_csv(f, skiprows=linhas_pular, sep=';')
            else: 
                return

            if codigo == "075_Web":
                colunas_para_juntar = [
                    "Ativ. Econômica - Residencial",
                    "Ativ. Econômica - Comercial",
                    "Ativ. Econômica - Industrial",
                    "Ativ. Econômica - Pública"
                ]
                
                for c in colunas_para_juntar:
                    if c not in df.columns:
                        df[c] = ""

                def concatenar_ativ(row):
                    valores = []
                    for c in colunas_para_juntar:
                        val = str(row[c]).strip()
                        if val and val.lower() != 'nan':
                            valores.append(val)
                    return " - ".join(valores) 

                df["Ativ. Econômica"] = df.apply(concatenar_ativ, axis=1)

                colunas_para_manter = [
                    "Matrícula", "Localização", "Numero Hidrometro", "Endereço",
                    "Bairro", "CEP", "Morador", "Ativ. Econômica"
                ]
                
                colunas_finais = [c for c in colunas_para_manter if c in df.columns]
                df = df[colunas_finais]
                
            elif codigo in ["918", "939"]:
                pasta_relatorio = os.path.dirname(caminho_final_onedrive)
                pasta_historico = os.path.join(pasta_relatorio, "Historico")
                os.makedirs(pasta_historico, exist_ok=True) 
                
                lista_dfs = []
                
                for arquivo in os.listdir(pasta_historico):
                    if arquivo.endswith(('.xlsx', '.xls', '.csv')):
                        caminho_hist = os.path.join(pasta_historico, arquivo)
                        try:
                            if arquivo.endswith('.csv'):
                                df_hist = pd.read_csv(caminho_hist, sep=';', encoding='utf-8', errors='ignore', skiprows=linhas_pular)
                            else:
                                df_hist = pd.read_excel(caminho_hist, skiprows=linhas_pular)
                            lista_dfs.append(df_hist)
                        except Exception as e:
                            print(f"Ignorando leitura do arquivo {arquivo}: {e}")
                
                lista_dfs.append(df)
                
                if lista_dfs:
                    df = pd.concat(lista_dfs, ignore_index=True)
                    df.drop_duplicates(inplace=True)
            
            else:
                colunas_presentes = [c for c in COLUNAS_REMOVER.get(codigo, []) if c in df.columns]
                if colunas_presentes:
                    df.drop(columns=colunas_presentes, inplace=True)

            df.to_excel(caminho_final_onedrive, index=False)
            
            import gc
            df = None 
            gc.collect() 
            if os.path.exists(caminho_temp):
                try: os.remove(caminho_temp)
                except: pass
                
        except Exception as e_planilha:
            print(f"Aviso: Não foi possível limpar os dados da planilha do {codigo}: {e_planilha}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppAutomacao(root)
    root.mainloop()