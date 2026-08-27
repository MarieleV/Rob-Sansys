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

# Configuração central de cada relatório: horário padrão do 1º agendamento,
# quais colunas remover da planilha final, e como preencher os campos de data.
# Cada função de preenchimento recebe (self, page, datas) e faz o resto sozinha.
REPORTS = ["075", "786", "468", "579"]

DEFAULT_H1 = {"075": "08:00", "786": "08:15", "468": "08:30", "579": "08:45"}

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
        self.root.geometry("450x680")
        self.root.resizable(False, False)

        self.usuario_var = tk.StringVar()
        self.senha_var = tk.StringVar()

        # 3 horários de agendamento + 1 checkbox de extração manual, por relatório
        self.horarios = {
            codigo: [tk.StringVar(value=DEFAULT_H1[codigo] if i == 0 else "") for i in range(3)]
            for codigo in REPORTS
        }
        self.relatorio_vars = {codigo: tk.BooleanVar(value=True) for codigo in REPORTS}

        self.status_var = tk.StringVar(value="Status: Aguardando comando...")

        self.criar_interface()
        self.carregar_configuracoes()

        self.thread_agendamento = threading.Thread(target=self.rodar_agendamentos, daemon=True)
        self.thread_agendamento.start()

    # ------------------------------------------------------------------ UI
    def criar_interface(self):
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Login
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

        # 2. Extração imediata (checkboxes + botão)
        frame_relatorios = ttk.Frame(self.main_frame)
        frame_relatorios.pack(pady=5)
        ttk.Label(frame_relatorios, text="Extração Imediata:").pack(pady=5)

        frame_checks = ttk.Frame(frame_relatorios)
        frame_checks.pack()
        for codigo in REPORTS:
            ttk.Checkbutton(frame_checks, text=codigo, variable=self.relatorio_vars[codigo]).pack(side=tk.LEFT, padx=2)

        ttk.Button(self.main_frame, text="▶ Extrair", command=self.iniciar_extracao_agora, width=35).pack(pady=10)

        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=5)

        # 3. Agendamentos (grade 2x2 de LabelFrames, um por relatório)
        container_1 = ttk.Frame(self.main_frame)
        container_1.pack(fill='x', pady=5)
        container_2 = ttk.Frame(self.main_frame)
        container_2.pack(fill='x', pady=5)

        containers = [container_1, container_1, container_2, container_2]
        lados = [tk.LEFT, tk.RIGHT, tk.LEFT, tk.RIGHT]

        for codigo, container, lado in zip(REPORTS, containers, lados):
            frame = ttk.LabelFrame(container, text=f"Agendar {codigo}")
            frame.pack(side=lado, fill='both', expand=True, padx=5)
            for var in self.horarios[codigo]:
                ttk.Entry(frame, textvariable=var, width=10, justify="center").pack(pady=3)

        ttk.Button(self.main_frame, text="Salvar Agendamentos", command=self.agendar_extracao).pack(pady=10)

        # Status
        ttk.Label(self.main_frame, textvariable=self.status_var, foreground="blue", justify="center").pack(side=tk.BOTTOM, pady=5)

    def minimizar_login(self):
        self.frame_form_login.pack_forget()
        self.lbl_usuario_salvo.config(text=f"{self.usuario_var.get()}")
        self.frame_login_minimizado.pack(pady=5)

    def expandir_login(self):
        self.frame_login_minimizado.pack_forget()
        self.frame_form_login.pack(pady=5)

    # ------------------------------------------------------------ Config
    def carregar_configuracoes(self):
        if not os.path.exists(ARQUIVO_CONFIG):
            return
        try:
            with open(ARQUIVO_CONFIG, "r") as f:
                dados = json.load(f)

            self.usuario_var.set(dados.get("usuario", ""))
            self.senha_var.set(dados.get("senha", ""))

            for codigo in REPORTS:
                for i, var in enumerate(self.horarios[codigo]):
                    padrao = DEFAULT_H1[codigo] if i == 0 else ""
                    var.set(dados.get(f"h{i + 1}_{codigo}", padrao))
                self.relatorio_vars[codigo].set(dados.get(f"relatorio_{codigo}", True))

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
        }
        for codigo in REPORTS:
            for i, var in enumerate(self.horarios[codigo]):
                dados[f"h{i + 1}_{codigo}"] = var.get().strip()
            dados[f"relatorio_{codigo}"] = self.relatorio_vars[codigo].get()

        with open(ARQUIVO_CONFIG, "w") as f:
            json.dump(dados, f)

    # --------------------------------------------------------- Agendamento
    def rodar_agendamentos(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def agendar_extracao(self):
        validos = {
            codigo: [h.get().strip() for h in self.horarios[codigo] if h.get().strip()]
            for codigo in REPORTS
        }

        if not any(validos.values()):
            messagebox.showwarning("Aviso", "Preencha pelo menos um horário em algum relatório para agendar.")
            return

        try:
            schedule.clear()
            for codigo, horas in validos.items():
                for h in horas:
                    schedule.every().day.at(h).do(self.disparar_agendado, relatorio=codigo)

            self.salvar_horarios_silencioso()

            resumo = "\n".join(f"{codigo}: {', '.join(horas)}" for codigo, horas in validos.items() if horas)

            self.status_var.set("Status: Agendamentos ativos em segundo plano.")
            messagebox.showinfo("Agendamento", f"Agendamentos configurados para rodar todos os dias:\n\n{resumo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Formato de hora inválido. Use HH:MM.\nErro: {e}")

    def disparar_agendado(self, relatorio):
        usuario, senha = self.usuario_var.get(), self.senha_var.get()
        if not usuario or not senha:
            return
        self.status_var.set(f"Status: Iniciando extração agendada do {relatorio}...")
        threading.Thread(target=self.automacao_playwright, args=(usuario, senha, [relatorio]), daemon=True).start()

    def iniciar_extracao_agora(self):
        usuario, senha = self.usuario_var.get(), self.senha_var.get()
        if not usuario or not senha:
            messagebox.showwarning("Atenção", "Por favor, configure o usuário e a senha antes.")
            self.expandir_login()
            return

        relatorios_selecionados = [c for c in REPORTS if self.relatorio_vars[c].get()]
        if not relatorios_selecionados:
            messagebox.showwarning("Atenção", "Selecione pelo menos um relatório para baixar.")
            return

        self.status_var.set("Status: Iniciando extrações... Aguarde.")
        threading.Thread(target=self.automacao_playwright, args=(usuario, senha, relatorios_selecionados), daemon=True).start()

    # ------------------------------------------------------ Preenchimento
    def preencher_campo_data(self, page, indice, valor, espera=500):
        """Limpa e digita um valor em um campo de data pelo índice do textbox."""
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
        """Preenche os campos específicos de cada relatório antes de executar."""
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

    # --------------------------------------------------------- Automação
    def automacao_playwright(self, usuario, senha, lista_relatorios):
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)  # mude para False para ver o navegador
                pasta_destino = os.path.join(os.path.expanduser("~"), "Downloads")
                arquivos_baixados = []

                datas = {
                    "data_completa": datetime.now().strftime("%d%m%Y"),
                    "mes_ano": datetime.now().strftime("%m%Y"),
                    "mes_ano_barra": datetime.now().strftime("%m/%Y"),
                    "primeiro_dia_ano": datetime.now().strftime("0101%Y"),
                }

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
                    except Exception:
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
                    if os.path.exists(caminho_salvo):
                        os.remove(caminho_salvo)
                    download.save_as(caminho_salvo)

                    try:
                        self.root.after(0, lambda c=codigo: self.status_var.set(f"Status: Processando e limpando o {c}..."))
                        caminho_final, extensao = self.padronizar_arquivo(caminho_salvo, extensao_sugerida, pasta_relatorio)
                        self.limpar_planilha(caminho_final, extensao, codigo)
                        arquivos_baixados.append(f"Pasta: Relatorio_{codigo} (Arquivo limpo e pronto!)")
                    except Exception as e:
                        print(f"Erro ao processar o arquivo do {codigo}: {e}")
                        arquivos_baixados.append(f"Erro ao processar o {codigo}")

                    context.close()

                browser.close()

                msg_final = "Processo concluído! Os arquivos estão em 'Downloads':\n\n" + "\n".join(arquivos_baixados)
                self.root.after(0, lambda: self.status_var.set("Status: Sucesso! Processo concluído."))
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", msg_final))

        except Exception as e:
            erro_msg = str(e)
            self.root.after(0, lambda: self.status_var.set("Status: Erro na extração."))
            self.root.after(0, lambda erro=erro_msg: messagebox.showerror("Erro", f"Ocorreu um erro durante a extração:\n{erro}"))

    # ---------------------------------------------------- Pós-processamento
    def padronizar_arquivo(self, caminho_salvo, extensao_sugerida, pasta_relatorio):
        """Descompacta (se for zip) e renomeia o arquivo baixado para Base_Relatorio.<ext>."""
        if extensao_sugerida.lower() == '.zip':
            with zipfile.ZipFile(caminho_salvo, 'r') as zip_ref:
                lista_arquivos = zip_ref.namelist()
                nome_original_no_zip = lista_arquivos[0]
                zip_ref.extract(nome_original_no_zip, pasta_relatorio)

            _, extensao = os.path.splitext(nome_original_no_zip)
            caminho_extraido = os.path.join(pasta_relatorio, nome_original_no_zip)
            try:
                os.remove(caminho_salvo)
            except Exception:
                pass
        else:
            extensao = extensao_sugerida
            caminho_extraido = caminho_salvo

        caminho_padronizado = os.path.join(pasta_relatorio, f"Base_Relatorio{extensao}")
        if os.path.exists(caminho_padronizado):
            os.remove(caminho_padronizado)
        os.rename(caminho_extraido, caminho_padronizado)
        return caminho_padronizado, extensao

    def limpar_planilha(self, caminho, extensao, codigo):
        """Pula as 3 linhas de cabeçalho e remove colunas sensíveis, se houver."""
        try:
            ext = extensao.lower()
            if ext in ('.xlsx', '.xls'):
                df = pd.read_excel(caminho, skiprows=3)
            elif ext == '.csv':
                df = pd.read_csv(caminho, skiprows=3, sep=';')
            else:
                return

            colunas_presentes = [c for c in COLUNAS_REMOVER.get(codigo, []) if c in df.columns]
            if colunas_presentes:
                df.drop(columns=colunas_presentes, inplace=True)

            if ext in ('.xlsx', '.xls'):
                df.to_excel(caminho, index=False)
            else:
                df.to_csv(caminho, index=False, sep=';')
        except Exception as e_planilha:
            print(f"Aviso: Não foi possível limpar os dados da planilha do {codigo}: {e_planilha}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AppAutomacao(root)
    root.mainloop()