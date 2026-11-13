<div align="center">
  <!-- Você pode trocar esse link por uma imagem do seu próprio app depois! -->
  <img src="https://img.icons8.com/fluency/96/000000/bot.png" alt="Ícone de Robô" width="80"/>

  <h1>RPA: Extrator de Relatórios Sansys</h1>
</div>

<p align="center">
  Automação corporativa com interface gráfica, agendamento autônomo e tratamento automático de dados.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-334155?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/RPA-Web%20Automation-475569?style=for-the-badge" alt="RPA" />
  <img src="https://img.shields.io/badge/Data-Cleaning-64748B?style=for-the-badge&logo=pandas&logoColor=white" alt="Data Cleaning" />
</p>

---

<p align="center">
Solução de <b>Automação Robótica de Processos (RPA)</b> em Python para interagir com sistemas web legados baseados em ExtJS (Sansys). O robô elimina tarefas operacionais repetitivas, realizando extrações complexas em minutos de forma 100% invisível (modo <i>headless</i>).
</p>

<p align="center">
<b>Como funciona:</b> o robô acessa o sistema e navega por menus dinâmicos contornando IDs voláteis com leitura de atributos customizados (<code>cfgname</code>) e manipulação de teclado. Após o download, descompacta os arquivos, usa <b>Pandas</b> para limpar cabeçalhos e remover colunas com dados sensíveis (adequação à LGPD) e salva os relatórios padronizados em um diretório departamental mapeado em rede. Tudo orquestrado por uma <b>interface gráfica em abas</b> com agendamento diário.
</p>

<p align="center">
  <a href="#-principais-funcionalidades">Funcionalidades</a> ·
  <a href="#-tech-stack">Tech Stack</a> ·
  <a href="#-arquitetura-do-sistema">Arquitetura</a> ·
  <a href="#-como-rodar-localmente">Como rodar</a>
</p>

<!-- AJUSTE: adicione um print da interface (abas de configuração e agendamento),
     com credenciais e caminhos de rede ocultos. -->

---

##  → Principais Funcionalidades

<table align="center" width="100%">
  <tr>
    <td width="50%" valign="top">
      <h3>Navegação Resiliente</h3>
      <p>Automação com Playwright projetada para lidar com lentidão extrema e elementos dinâmicos (ExtJS), usando mapeamento por <code>cfgname</code> e interações de teclado.</p>
    </td>
    <td width="50%" valign="top">
      <h3>Data Cleaning Automático</h3>
      <p>Processamento embutido com Pandas: extrai arquivos Zip, ignora as linhas de cabeçalho do sistema e remove colunas sensíveis antes de salvar a planilha final.</p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>Agendamento em Threads</h3>
      <p>Motor de <i>scheduling</i> em segundo plano, sem congelar a interface gráfica. Permite configurar múltiplos horários para diferentes relatórios.</p>
    </td>
    <td width="50%" valign="top">
      <h3>Organização Dinâmica</h3>
      <p>Salva as configurações localmente em um <code>config.json</code> e direciona os relatórios tratados para caminhos de rede baseados no usuário do Windows.</p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>Portabilidade (Standalone)</h3>
      <p>Compilado com PyInstaller (<code>--onefile</code>) em um único executável leve (<code>.exe</code>), sem exigir Python instalado na máquina do usuário final.</p>
    </td>
    <td width="50%" valign="top">
      <h3>Adequação à LGPD</h3>
      <p>Colunas com dados pessoais são descartadas automaticamente durante o tratamento, de modo que só informações necessárias chegam ao diretório compartilhado.</p>
    </td>
  </tr>
</table>

<br/>

##  → Tech Stack

<div align="center">
  <table align="center" cellspacing="10" cellpadding="10">
    <tr>
      <td align="center" width="25%">
        <img src="https://cdn.simpleicons.org/python/CBD5E1" width="40" height="40" alt="Python"/><br/>Python
      </td>
      <td align="center" width="25%">
        <img src="https://cdn.simpleicons.org/pandas/CBD5E1" width="40" height="40" alt="Pandas"/><br/>Pandas
      </td>
      <td align="center" width="25%">
        <img src="https://cdn.simpleicons.org/json/CBD5E1" width="40" height="40" alt="JSON"/><br/>JSON
      </td>
      <td align="center" width="25%">
        <img src="https://cdn.simpleicons.org/git/CBD5E1" width="40" height="40" alt="Git"/><br/>Git
      </td>
    </tr>
  </table>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/Playwright-334155?style=flat-square" alt="Playwright" />
  <img src="https://img.shields.io/badge/Tkinter-334155?style=flat-square" alt="Tkinter" />
  <img src="https://img.shields.io/badge/Schedule-334155?style=flat-square" alt="Schedule" />
  <img src="https://img.shields.io/badge/Openpyxl-334155?style=flat-square" alt="Openpyxl" />
  <img src="https://img.shields.io/badge/PyInstaller-334155?style=flat-square" alt="PyInstaller" />
  <img src="https://img.shields.io/badge/Threading-334155?style=flat-square" alt="Threading" />
</p>

<br/>

##  → Arquitetura do Sistema

<details>
  <summary><b>Clique para visualizar a estrutura</b></summary>
  <br/>

```text
├── robo-extrator.py      # Script principal: UI (Tkinter), agendador, RPA e tratamento de dados
├── DataCleaning.py       # Script independente apenas para tratamento de dados
├── config.json           # Gerado automaticamente: cache de credenciais e horários
├── requirements.txt      # Dependências (Playwright, Pandas, Schedule, Openpyxl)
└── README.md             # Documentação do projeto
```

</details>

<br/>

##  → Como Rodar Localmente

<!-- AJUSTE: confira os comandos abaixo com o seu ambiente (nome do script, navegador usado pelo Playwright
     e flags do PyInstaller). -->

**Pré-requisitos:** Python 3.12+ e acesso ao sistema Sansys.

**1. Clone o repositório e instale as dependências**

```bash
git clone https://github.com/MarieleV/<nome-do-repositorio>.git
cd <nome-do-repositorio>
pip install -r requirements.txt
playwright install chromium
```

**2. Execute o robô**

```bash
python robo-extrator.py
```

**3. (Opcional) Gere o executável**

```bash
pyinstaller --onefile --noconsole robo-extrator.py
```

> [!WARNING]
> O `config.json` armazena credenciais localmente. Adicione-o ao `.gitignore` e nunca o versione.

<br/>

<p align="center">
  <a href="https://github.com/MarieleV">
    <img src="https://img.shields.io/badge/Mariele%20Vieira-334155?style=for-the-badge&logo=github&logoColor=white" alt="GitHub" />
  </a>
  <a href="https://www.linkedin.com/in/mariele-vieira" target="_blank">
    <img src="https://img.shields.io/badge/LinkedIn-475569?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" />
  </a>
  <a href="mailto:silvamariele797@gmail.com">
    <img src="https://img.shields.io/badge/E--mail-64748B?style=for-the-badge&logo=gmail&logoColor=white" alt="E-mail" />
  </a>
</p>
