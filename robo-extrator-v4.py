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

ARQUIVO_CONFIG = "config.json"

# Configurações Centrais
REPORTS = ["075", "786", "468", "579"]
BACKLOGS = ["Fiscalizacao", "Notificacao"]
TODOS_RELATORIOS = REPORTS + BACKLOGS

DEFAULT_H1 = {
    "075": "08:00", "786": "08:15", "468": "08:30", "579": "08:45",
    "Fiscalizacao": "09:00", "Notificacao": "09:15"
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

class AppAutomacao:
    def __init__(self, root):
        self.root = root
        self.root.title("Robô de Relatórios - CAJ")
        # 🌟 MUDANÇA: Aumentei um pouquinho a largura de 480 para 540 para caber os 4 blocos lado a lado
        self.root.geometry("540x720")
        self.root.resizable(False, False)

        self.usuario_var = tk.StringVar()
        self.senha_var = tk.StringVar()

        # Variáveis para TODOS os relatórios
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

        # 1. Login (Fixo no topo)
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

        # 2. Notebook (Abas para organizar a tela)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True, pady=5)

        # ABA 1: Relatórios Gerenciais
        self.aba_gerenciais = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.aba_gerenciais, text="Gerenciais")
        # 🌟 MUDANÇA: Mudei o último número de 2 para 4 (assim cria 4 colunas lado a lado)
        self.montar_aba_relatorios(self.aba_gerenciais, REPORTS, 4)

        # ABA 2: Backlogs
        self.aba_backlogs = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.aba_backlogs, text="Backlogs")
        # Os backlogs mantemos em 2, pois são apenas dois relatórios, assim eles dividem a tela no meio direitinho
        self.montar_aba_relatorios(self.aba_backlogs, BACKLOGS, 2)

        # 3. Botões Globais (Fixos na base)
        frame_botoes = ttk.Frame(self.main_frame)
        frame_botoes.pack(fill='x', pady=10)
        
        ttk.Button(frame_botoes, text="▶ Extrair Imediato (Marcados)", command=self.iniciar_extracao_agora, width=35).pack(pady=5)
        ttk.Button(frame_botoes, text="Salvar Todos os Agendamentos", command=self.agendar_extracao, width=35).pack(pady=5)

        # Status
        ttk.Label(self.main_frame, textvariable=self.status_var, foreground="blue", justify="center").pack(side=tk.BOTTOM, pady=5)

    def montar_aba_relatorios(self, aba, lista_codigos, colunas_grid):
        """Monta dinamicamente as caixas de seleção e agendamento dentro de uma aba"""
        # Checkboxes
        ttk.Label(aba, text="Selecionar para Extração Imediata:").pack(pady=5)
        frame_checks = ttk.Frame(aba)
        frame_checks.pack(pady=5)
        for codigo in lista_codigos:
            ttk.Checkbutton(frame_checks, text=codigo, variable=self.relatorio_vars[codigo]).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(aba, orient='horizontal').pack(fill='x', pady=10)
        
        # Grid de Agendamentos
        ttk.Label(aba, text="Horários de Agendamento (HH:MM):").pack(pady=5)
        frame_grid = ttk.Frame(aba)
        frame_grid.pack(fill='both', expand=True)
        
        # 🌟 O TRUQUE PARA CENTRALIZAR: Configura as colunas para dividirem o espaço igualmente
        for i in range(colunas_grid):
            frame_grid.grid_columnconfigure(i, weight=1)
        
        for index, codigo in enumerate(lista_codigos):
            row = index // colunas_grid
            col = index % colunas_grid
            # Adicionei um padding interno para a caixinha ficar mais robusta visualmente
            frame = ttk.LabelFrame(frame_grid, text=f"Agendar {codigo}")
            frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            for var in self.horarios[codigo]:
                ttk.Entry(frame, textvariable=var, width=10, justify="center").pack(pady=2)

    def minimizar_login(self):
        self.frame_form_login.pack_forget()
        self.lbl_usuario_salvo.config(text=f"{self.usuario_var.get()}")
        self.frame_login_minimizado.pack(pady=5)

    def expandir_login(self):
        self.frame_login_minimizado.pack_forget()
        self.frame_form_login.pack(pady=5)

    # ------------------------------------------------------------ Config & Schedule
    def carregar_configuracoes(self):
        if not os.path.exists(ARQUIVO_CONFIG):
            return
        try:
            with open(ARQUIVO_CONFIG, "r") as f:
                dados = json.load(f)

            self.usuario_var.set(dados.get("usuario", ""))
            self.senha_var.set(dados.get("senha", ""))

            for codigo in TODOS_RELATORIOS:
                for i, var in enumerate(self.horarios[codigo]):
                    padrao = DEFAULT_H1.get(codigo, "") if i == 0 else ""
                    var.set(dados.get(f"h{i + 1}_{codigo}", padrao))
                self.relatorio_vars[codigo].set(dados.get(f"relatorio_{codigo}", True))

            if self.usuario_var.get() and self.senha_var.get():
                self.minimizar_login()
        except Exception as e:
            print(f"Erro ao carregar: {e}")

    def salvar_configuracoes(self):
        usuario, senha = self.usuario_var.get().strip(), self.senha_var.get().strip()
        if not usuario or not senha:
            messagebox.showwarning("Atenção", "Preencha usuário e senha para salvar.")
            return
        self.salvar_horarios_silencioso()
        messagebox.showinfo("Sucesso", "Salvo com sucesso!")
        self.minimizar_login()

    def salvar_horarios_silencioso(self):
        dados = {"usuario": self.usuario_var.get().strip(), "senha": self.senha_var.get().strip()}
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
        usuario, senha = self.usuario_var.get(), self.senha_var.get()
        if not usuario or not senha: return
        self.status_var.set(f"Status: Iniciando extração de {relatorio}...")
        
        # Encaminha para a automação correta
        if relatorio in REPORTS:
            threading.Thread(target=self.automacao_playwright, args=(usuario, senha, [relatorio]), daemon=True).start()
        else:
            threading.Thread(target=self.automacao_backlogs, args=(usuario, senha, [relatorio]), daemon=True).start()

    def iniciar_extracao_agora(self):
        usuario, senha = self.usuario_var.get(), self.senha_var.get()
        if not usuario or not senha:
            messagebox.showwarning("Atenção", "Configure o usuário e senha.")
            self.expandir_login()
            return

        gerenciais_selecionados = [c for c in REPORTS if self.relatorio_vars[c].get()]
        backlogs_selecionados = [c for c in BACKLOGS if self.relatorio_vars[c].get()]

        if not gerenciais_selecionados and not backlogs_selecionados:
            messagebox.showwarning("Atenção", "Selecione pelo menos um relatório.")
            return

        self.status_var.set("Status: Iniciando extrações... Aguarde.")
        
        # Dispara as threads (elas podem rodar em paralelo se o sistema aguentar, 
        # mas por segurança do Playwright, disparamos sequencialmente usando uma função mestre)
        threading.Thread(target=self.rotear_extracoes_manuais, args=(usuario, senha, gerenciais_selecionados, backlogs_selecionados), daemon=True).start()

    def rotear_extracoes_manuais(self, usuario, senha, gerenciais, backlogs):
        if gerenciais:
            self.automacao_playwright(usuario, senha, gerenciais)
        if backlogs:
            self.automacao_backlogs(usuario, senha, backlogs)
        self.root.after(0, lambda: self.status_var.set("Status: Sucesso! Processo concluído."))

    # --------------------------------------------------------- Automação Gerenciais
    def preencher_campo_data(self, page, indice, valor, espera=500):
        campo = page.get_by_role("textbox").nth(indice)
        campo.click(force=True)
        page.keyboard.press("Home")
        page.wait_for_timeout(200)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        page.wait_for_timeout(200)
        campo.press_sequentially(valor, delay=100)
        page.keyboard.press("Tab")
        page.wait_for_timeout(espera)

    def preencher_filtros(self, page, codigo, datas):
        if codigo == "075":
            self.preencher_campo_data(page, 0, datas["mes_ano"])
            page.get_by_role("textbox", name="Grupo Faturamento (Informe 0").fill("0", force=True)
            page.wait_for_timeout(3000)
        elif codigo == "786":
            self.preencher_campo_data(page, 0, "01012024")
            self.preencher_campo_data(page, 1, datas["data_completa"], espera=2000)
        elif codigo == "468":
            self.preencher_campo_data(page, 0, datas["primeiro_dia_ano"])
        elif codigo == "579":
            self.preencher_campo_data(page, 0, datas["mes_ano_barra"])

    def automacao_playwright(self, usuario, senha, lista_relatorios):
        try:
            with sync_playwright() as playwright:
                # Modifique headless=False caso queira ver o navegador na versão final
                browser = playwright.chromium.launch(headless=True)
                # O "rf" na frente permite usar barras do Windows (\) e variáveis ao mesmo tempo!
                pasta_destino = rf"C:\Users\{usuario}\CAJ\GFC - Documentos\CFC\8.PROJETOS EM ANDAMENTO\Relatórios Robô Sansys"
                arquivos_baixados = []

                datas = {
                    "data_completa": datetime.now().strftime("%d%m%Y"),
                    "mes_ano": datetime.now().strftime("%m%Y"),
                    "mes_ano_barra": datetime.now().strftime("%m/%Y"),
                    "primeiro_dia_ano": datetime.now().strftime("0101%Y"),
                }

                for codigo in lista_relatorios:
                    self.root.after(0, lambda c=codigo: self.status_var.set(f"Acessando Gerencial: {c}..."))
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

                    self.root.after(0, lambda c=codigo: self.status_var.set(f"Extraindo Gerencial: {c}..."))
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

                    self.preencher_filtros(page, codigo, datas)
                    page.get_by_text("Executar", exact=True).click()

                    botao_download = page.locator('button[cfgname="acompanharExecucaoRelatorioFonteDado.acompanhar.btDownload"]')
                    botao_download.wait_for(state="visible", timeout=1200000)
                    with page.expect_download(timeout=300000) as download_info:
                        botao_download.click()
                    download = download_info.value

                    pasta_relatorio = os.path.join(pasta_destino, f"Relatorio_{codigo}")
                    os.makedirs(pasta_relatorio, exist_ok=True)
                    nome_sugerido = download.suggested_filename
                    _, extensao_sugerida = os.path.splitext(nome_sugerido)
                    caminho_salvo = os.path.join(pasta_relatorio, nome_sugerido)
                    if os.path.exists(caminho_salvo): os.remove(caminho_salvo)
                    download.save_as(caminho_salvo)

                    try:
                        self.root.after(0, lambda c=codigo: self.status_var.set(f"Limpando o Gerencial {c}..."))
                        caminho_final, extensao = self.padronizar_arquivo(caminho_salvo, extensao_sugerida, pasta_relatorio)
                        self.limpar_planilha(caminho_final, extensao, codigo)
                        arquivos_baixados.append(f"Relatorio_{codigo}")
                    except Exception as e:
                        print(f"Erro ao processar {codigo}: {e}")

                    context.close()
                browser.close()
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set("Erro na extração Gerencial."))
            print(f"Erro: {e}")

    # --------------------------------------------------------- Automação Backlogs (NOVO)
    def automacao_backlogs(self, usuario, senha, lista_backlogs):
        try:
            with sync_playwright() as playwright:
                # Modifique headless=False caso queira ver o navegador na versão final
                browser = playwright.chromium.launch(headless=True)
                
                for tipo in lista_backlogs:
                    self.root.after(0, lambda t=tipo: self.status_var.set(f"Extraindo Backlog: {t}..."))
                    
                    context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='pt-BR')
                    page = context.new_page()
                    page.goto("https://aguasdejoinville.com.br/sansys/index.html#/")

                    # Login
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

                    # Navegação
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

                    # Filtros Comuns
                    try:
                        campo_servicos = page.locator(".x-form-item").filter(has_text="Serviços de:").locator("input")
                        campo_servicos.click(force=True, timeout=2000)
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        campo_servicos.press_sequentially("Unidade Comercial", delay=50)
                        page.keyboard.press("Tab")
                        page.wait_for_timeout(1000)
                    except: pass

                    try:
                        campo_pesquisa = page.locator('input[cfgname="relOPE0002.relatorio.tpPesquisa"]')
                        campo_pesquisa.click(force=True, timeout=2000)
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        campo_pesquisa.press_sequentially("Empresa", delay=50)
                        page.keyboard.press("Tab")
                        page.wait_for_timeout(1500)
                    except: pass

                    try:
                        page.get_by_text("01 - CIA AGUAS DE JOINVILLE").dblclick(timeout=2000)
                        page.wait_for_timeout(500)
                    except: pass

                    try:
                        campo_data_ini = page.get_by_role("textbox", name="Período Solicitação Inicial:")
                        campo_data_ini.click(force=True)
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        campo_data_ini.press_sequentially("01012025", delay=50)
                        page.keyboard.press("Tab")
                    except: pass

                    try:
                        data_hoje = datetime.now().strftime("%d%m%Y")
                        campo_data_fim = page.get_by_role("textbox", name="Período Solicitação Final:")
                        campo_data_fim.click(force=True)
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        campo_data_fim.press_sequentially(data_hoje, delay=50)
                        page.keyboard.press("Tab")
                    except: pass

                    # Filtros Específicos
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
                        campo_setor = page.locator('input[cfgname="relOPE0002.relatorio.opeSetorOperacional"]')
                        campo_setor.click(force=True, timeout=2000)
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        campo_setor.press_sequentially(texto_setor, delay=50)
                        page.keyboard.press("Tab")
                        page.wait_for_timeout(1000)
                    except: pass

                    try:
                        campo_formato = page.locator('input[cfgname="relOPE0002.relatorio.relFormatoRelatorio"]')
                        campo_formato.click(force=True, timeout=2000)
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        campo_formato.press_sequentially("EXCEL", delay=50)
                        page.keyboard.press("Tab")
                        page.wait_for_timeout(1000)
                    except: pass

                    # Download
                    with page.expect_download(timeout=300000) as download_info:
                        page.get_by_role("button", name="Confirmar").click()
                        
                    download = download_info.value
                    pasta_destino = rf"C:\Users\{usuario}\CAJ\GFC - Documentos\CFC\8.PROJETOS EM ANDAMENTO\Relatórios Robô Sansys"
                    pasta_relatorio = os.path.join(pasta_destino, f"Relatorio_{tipo}")
                    os.makedirs(pasta_relatorio, exist_ok=True)
                    
                    caminho_salvo = os.path.join(pasta_relatorio, f"Base_Relatorio_{tipo}.xls")
                    
                    if os.path.exists(caminho_salvo):
                        os.remove(caminho_salvo)
                        
                    download.save_as(caminho_salvo)
                    page.wait_for_timeout(2000) 
                    context.close()
                browser.close()
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set("Erro na extração dos Backlogs."))
            print(f"Erro: {e}")

    # ---------------------------------------------------- Pós-processamento (Inalterado)
    def padronizar_arquivo(self, caminho_salvo, extensao_sugerida, pasta_relatorio):
        if extensao_sugerida.lower() == '.zip':
            with zipfile.ZipFile(caminho_salvo, 'r') as zip_ref:
                lista_arquivos = zip_ref.namelist()
                nome_original_no_zip = lista_arquivos[0]
                zip_ref.extract(nome_original_no_zip, pasta_relatorio)

            _, extensao = os.path.splitext(nome_original_no_zip)
            caminho_extraido = os.path.join(pasta_relatorio, nome_original_no_zip)
            try: os.remove(caminho_salvo)
            except: pass
        else:
            extensao = extensao_sugerida
            caminho_extraido = caminho_salvo

        caminho_padronizado = os.path.join(pasta_relatorio, f"Base_Relatorio{extensao}")
        if os.path.exists(caminho_padronizado):
            os.remove(caminho_padronizado)
        os.rename(caminho_extraido, caminho_padronizado)
        return caminho_padronizado, extensao

    def limpar_planilha(self, caminho, extensao, codigo):
        try:
            ext = extensao.lower()
            if ext in ('.xlsx', '.xls'): df = pd.read_excel(caminho, skiprows=3)
            elif ext == '.csv': df = pd.read_csv(caminho, skiprows=3, sep=';')
            else: return

            colunas_presentes = [c for c in COLUNAS_REMOVER.get(codigo, []) if c in df.columns]
            if colunas_presentes:
                df.drop(columns=colunas_presentes, inplace=True)

            if ext in ('.xlsx', '.xls'): df.to_excel(caminho, index=False)
            else: df.to_csv(caminho, index=False, sep=';')
        except Exception as e_planilha:
            print(f"Aviso: Não foi possível limpar os dados da planilha do {codigo}: {e_planilha}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AppAutomacao(root)
    root.mainloop()