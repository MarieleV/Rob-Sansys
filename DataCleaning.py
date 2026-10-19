import os
import json
import threading
import gc
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

# Suporte opcional para Arrastar e Soltar (Drag & Drop)
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    TkinterDnD = object

ARQUIVO_CONFIG_LIMPADOR = "config_limpador.json"

# Colunas a remover no 075
COLUNAS_REMOVER = {
    "075": [
        "Endereço", "CEP", "Inscrição imobiliária", "Proprietário",
        "CPF CNPJ Proprietário", "Telefone Residencial proprietário",
        "Telefone Comercial proprietário", "Telefone Celular proprietário",
        "Email proprietário", "Morador", "CPF CNPJ Morador",
        "Telefone Residencial Morador", "Telefone Comercial Morador",
        "Telefone Celular Morador", "Email Morador"
    ]
}

LISTA_RELATORIOS = ["075 - Relatório 075"]


class LimpadorBase:
    def __init__(self, root):
        self.root = root
        self.root.title("CAJ - Limpador de Dados")
        self.root.geometry("640x520")
        self.root.configure(bg="#FFFFFF")
        self.root.resizable(False, False)

        self.relatorio_selecionado = tk.StringVar(value=LISTA_RELATORIOS[0])
        self.pasta_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Selecione ou arraste um arquivo bruto para começar.")

        self.criar_interface()
        self.carregar_configuracao()

        if HAS_DND and isinstance(self.root, TkinterDnD.DnDWrapper):
            self.card_upload.drop_target_register(DND_FILES)
            self.card_upload.dnd_bind('<<Drop>>', self.ao_soltar_arquivo)

    def criar_interface(self):
        # ---------------- BARRA SUPERIOR (CONFIGURAÇÕES DISCRETAS)
        top_bar = tk.Frame(self.root, bg="#F8F9FA", height=50, bd=1, relief="solid")
        top_bar.pack(fill=tk.X, side=tk.TOP)

        # Relatório Selector
        lbl_rel = tk.Label(top_bar, text="Relatório:", font=("Segoe UI", 9, "bold"), bg="#F8F9FA", fg="#444444")
        lbl_rel.pack(side=tk.LEFT, padx=(15, 5), pady=10)

        combo_rel = ttk.Combobox(
            top_bar,
            textvariable=self.relatorio_selecionado,
            values=LISTA_RELATORIOS,
            state="readonly",
            width=20,
            font=("Segoe UI", 9)
        )
        combo_rel.pack(side=tk.LEFT, padx=(0, 15), pady=10)

        # Destino Selector
        lbl_pasta = tk.Label(top_bar, text="Salvar em:", font=("Segoe UI", 9, "bold"), bg="#F8F9FA", fg="#444444")
        lbl_pasta.pack(side=tk.LEFT, padx=(5, 5), pady=10)

        entry_pasta = tk.Entry(top_bar, textvariable=self.pasta_var, font=("Segoe UI", 9), bd=1, relief="solid", bg="#FFFFFF", fg="#333333")
        entry_pasta.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), pady=10)

        btn_pasta = tk.Button(
            top_bar,
            text="📁",
            font=("Segoe UI", 10),
            bg="#E9ECEF",
            fg="#333333",
            bd=0,
            padx=8,
            cursor="hand2",
            command=self.selecionar_pasta
        )
        btn_pasta.pack(side=tk.LEFT, padx=(0, 15), pady=10)

        # ---------------- ÁREA CENTRAL (CARTOON / DROPZONE MINIMALISTA)
        main_area = tk.Frame(self.root, bg="#FFFFFF")
        main_area.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)

        self.card_upload = tk.Frame(main_area, bg="#FFFFFF", cursor="hand2")
        self.card_upload.pack(fill=tk.BOTH, expand=True)
        self.card_upload.bind("<Button-1>", lambda e: self.selecionar_arquivo())

        # Ícone de Upload Círculo Canvas
        canvas_icon = tk.Canvas(self.card_upload, width=120, height=120, bg="#FFFFFF", highlightthickness=0)
        canvas_icon.pack(pady=(20, 10))
        canvas_icon.bind("<Button-1>", lambda e: self.selecionar_arquivo())

        # Círculo cinza claro de fundo
        canvas_icon.create_oval(10, 10, 110, 110, fill="#F2F2F2", outline="")
        # Seta de upload
        canvas_icon.create_line(60, 75, 60, 42, fill="#757575", width=6, capstyle="round")
        canvas_icon.create_line(45, 55, 60, 40, fill="#757575", width=6, capstyle="round")
        canvas_icon.create_line(75, 55, 60, 40, fill="#757575", width=6, capstyle="round")
        canvas_icon.create_line(45, 82, 75, 82, fill="#757575", width=5, capstyle="round")

        # Texto Principal
        lbl_titulo = tk.Label(
            self.card_upload,
            text="Arraste e solte o arquivo bruto para fazer a limpeza",
            font=("Segoe UI", 12),
            bg="#FFFFFF",
            fg="#202124"
        )
        lbl_titulo.pack(pady=(10, 4))
        lbl_titulo.bind("<Button-1>", lambda e: self.selecionar_arquivo())

        # Subtexto
        lbl_sub = tk.Label(
            self.card_upload,
            text="Suporta planilhas e relatórios gerados diretamente pelo Sansys (.xls, .xlsx, .csv)",
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg="#5F6368"
        )
        lbl_sub.pack(pady=(0, 25))
        lbl_sub.bind("<Button-1>", lambda e: self.selecionar_arquivo())

        # Botão Azul em Destaque (YouTube/Google Style)
        self.btn_selecionar = tk.Button(
            self.card_upload,
            text="SELECIONAR ARQUIVO",
            font=("Segoe UI", 10, "bold"),
            bg="#0B57D0",
            fg="#FFFFFF",
            bd=0,
            padx=24,
            pady=10,
            cursor="hand2",
            activebackground="#0842A0",
            activeforeground="#FFFFFF",
            command=self.selecionar_arquivo
        )
        self.btn_selecionar.pack()

        # ---------------- BARRA DE STATUS INFERIOR
        self.lbl_status = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg="#5F6368",
            pady=15
        )
        self.lbl_status.pack(side=tk.BOTTOM)

    # ------------------------------------------------ CONFIGURAÇÃO PERSISTENTE
    def carregar_configuracao(self):
        if os.path.exists(ARQUIVO_CONFIG_LIMPADOR):
            try:
                with open(ARQUIVO_CONFIG_LIMPADOR, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    pasta_salva = data.get("caminho_destino", "")
                    if os.path.exists(pasta_salva):
                        self.pasta_var.set(os.path.normpath(pasta_salva))
            except Exception:
                pass

    def salvar_configuracao(self):
        pasta = self.pasta_var.get().strip()
        if pasta:
            try:
                with open(ARQUIVO_CONFIG_LIMPADOR, "w", encoding="utf-8") as f:
                    json.dump({"caminho_destino": pasta}, f, indent=4)
            except Exception:
                pass

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta onde o arquivo limpo será salvo")
        if pasta:
            pasta_norm = os.path.normpath(pasta)
            self.pasta_var.set(pasta_norm)
            self.salvar_configuracao()

    # ------------------------------------------------ SELEÇÃO E DRAG & DROP
    def selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o arquivo bruto do Sansys",
            filetypes=[("Arquivos de Planilha", "*.xlsx *.xls *.csv"), ("Todos os Arquivos", "*.*")]
        )
        if caminho:
            self.iniciar_processamento(os.path.normpath(caminho))

    def ao_soltar_arquivo(self, event):
        caminho = event.data.strip('{ }')
        if os.path.exists(caminho):
            self.iniciar_processamento(os.path.normpath(caminho))

    # ------------------------------------------------ PROCESSAMENTO RÁPIDO
    def iniciar_processamento(self, caminho_arquivo):
        pasta = self.pasta_var.get().strip()

        if not pasta or not os.path.exists(pasta):
            messagebox.showwarning("Atenção", "Por favor, selecione uma pasta de destino válida na barra superior.")
            return

        self.salvar_configuracao()
        self.btn_selecionar.config(state="disabled", bg="#A8C7FA")
        self.status_var.set("⏳ Limpando e formatando arquivo... Aguarde.")

        threading.Thread(target=self.processar_limpeza_thread, args=(caminho_arquivo, pasta), daemon=True).start()

    def ler_arquivo_otimizado(self, caminho_arquivo, skiprows=3):
        ext = os.path.splitext(caminho_arquivo)[1].lower()

        try:
            with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as f:
                inicio = f.read(2048)
                if "<table" in inicio.lower() or "<html" in inicio.lower():
                    dfs = pd.read_html(caminho_arquivo, skiprows=skiprows, encoding="utf-8")
                    if dfs:
                        return dfs[0]
        except Exception:
            pass

        if ext in [".xlsx", ".xls"]:
            try:
                return pd.read_excel(caminho_arquivo, skiprows=skiprows)
            except Exception:
                dfs = pd.read_html(caminho_arquivo, skiprows=skiprows)
                if dfs:
                    return dfs[0]
                raise
        elif ext == ".csv":
            return pd.read_csv(caminho_arquivo, skiprows=skiprows, sep=";", encoding="utf-8", errors="ignore")
        else:
            raise ValueError("Formato de arquivo não suportado.")

    def processar_limpeza_thread(self, arquivo, pasta):
        try:
            codigo_relatorio = self.relatorio_selecionado.get().split(" - ")[0]

            # 1. Leitura rápida ignorando 3 linhas de cabeçalho
            df = self.ler_arquivo_otimizado(arquivo, skiprows=3)

            # 2. Remoção de colunas sensíveis
            colunas_remover = COLUNAS_REMOVER.get(codigo_relatorio, [])
            colunas_presentes = [c for c in colunas_remover if c in df.columns]
            if colunas_presentes:
                df.drop(columns=colunas_presentes, inplace=True)

            # 3. Nome final do arquivo
            nome_saida = f"Rel-{codigo_relatorio}.xlsx"
            caminho_final = os.path.join(pasta, nome_saida)

            # 4. Escrita rápida
            df.to_excel(caminho_final, index=False)

            df = None
            gc.collect()

            self.root.after(0, lambda: self.sucesso_processamento(caminho_final))

        except Exception as e:
            msg = str(e).splitlines()[0] if str(e) else "Erro desconhecido"
            self.root.after(0, lambda: self.erro_processamento(msg))

    def sucesso_processamento(self, caminho_final):
        self.btn_selecionar.config(state="normal", bg="#0B57D0")
        self.status_var.set("✅ Concluído! O arquivo limpo já está na sua pasta.")
        messagebox.showinfo("Sucesso!", f"Relatório limpo e formatado com sucesso!\n\nSalvo em:\n{caminho_final}")

    def erro_processamento(self, msg_erro):
        self.btn_selecionar.config(state="normal", bg="#0B57D0")
        self.status_var.set("❌ Falha na limpeza do arquivo.")
        messagebox.showerror("Erro na Limpeza", f"Ocorreu um erro ao processar o arquivo:\n{msg_erro}")


# Execução com suporte a Drag and Drop se instalado
if __name__ == "__main__":
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    app = LimpadorBase(root)
    root.mainloop()