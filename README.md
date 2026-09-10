<div align="center">
  <!-- Você pode trocar esse link por uma imagem do seu próprio app depois! -->
  <img src="https://img.icons8.com/fluency/96/000000/bot.png" alt="Ícone de Robô" width="80"/>
  
  <h1>RPA: Extrator de Relatórios Sansys & Data Cleaning</h1>

  <p>
    <img src="https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/Playwright-Web_Automation-2EAD33?style=for-the-badge&logo=playwright&logoColor=white" alt="Playwright">
    <img src="https://img.shields.io/badge/Pandas-Data_Cleaning-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas">
    <img src="https://img.shields.io/badge/Tkinter-GUI-4B8BBE?style=for-the-badge&logo=python&logoColor=white" alt="Tkinter">
  </p>

  <p><em>Uma solução corporativa completa com interface gráfica, agendamento autônomo e tratamento automático de dados.</em></p>
</div>

<br>

<h2>📌 Sobre o Projeto</h2>
<p>
  Este projeto é uma solução de <b>Automação Robótica de Processos (RPA)</b> desenvolvida em Python para interagir com sistemas web legados baseados em ExtJS (Sansys). Ele soluciona o gargalo de tarefas operacionais repetitivas, realizando extrações complexas em minutos de forma 100% invisível (Modo Headless).
</p>
<p>
  O robô acessa o sistema, navega por menus dinâmicos burlando IDs voláteis através de técnicas de leitura de atributos customizados (<code>cfgname</code>) e manipulação de teclado. Após o download, ele descompacta arquivos, utiliza <b>Pandas</b> para limpar cabeçalhos inúteis e remover colunas com dados sensíveis (adequação LGPD), e salva os relatórios padronizados diretamente em um diretório departamental mapeado em rede. Tudo isso orquestrado por uma <b>Interface Gráfica (GUI) em Abas</b> com agendamento diário.
</p>

<br>

<h2> Principais Funcionalidades</h2>

<table>
  <tr>
    <td width="200">🌐 <b>Navegação Resiliente</b></td>
    <td>Automação robusta com Playwright projetada para lidar com lentidão extrema e elementos dinâmicos (ExtJS) utilizando mapeamento por <code>cfgname</code> e interações de teclado.</td>
  </tr>
  <tr>
    <td>📊 <b>Data Cleaning Automático</b></td>
    <td>Processamento embutido com Pandas: extrai Zips, pula linhas de cabeçalho do sistema e remove colunas sensíveis automaticamente antes de salvar a planilha final.</td>
  </tr>
  <tr>
    <td>⏰ <b>Agendamento (Threads)</b></td>
    <td>Motor de <i>scheduling</i> trabalhando em segundo plano para não congelar a interface gráfica. Permite configurar múltiplos horários para diferentes relatórios.</td>
  </tr>
  <tr>
    <td>📂 <b>Organização Dinâmica</b></td>
    <td>Salva as configurações localmente em um <code>config.json</code> e roteia os relatórios tratados para caminhos de rede baseados no nome do usuário do Windows.</td>
  </tr>
  <tr>
    <td>🚀 <b>Portabilidade (Standalone)</b></td>
    <td>Compilado via PyInstaller (<i>--onefile</i>) gerando um único executável leve (<code>.exe</code>), sem necessidade de instalação do Python na máquina do usuário final.</td>
  </tr>
</table>

<br>

<h2>📂 Arquitetura do Sistema</h2>

<details>
  <summary><b>Clique para visualizar a estrutura unificada</b></summary>
  <br>
  
  ```text
  ├── robo-extrator-v4.py   # Script monolítico: UI (Tkinter), Agendador, RPA e Tratamento de Dados
  ├── config.json           # Arquivo gerado automaticamente para cache de credenciais e horários
  ├── requirements.txt      # Mapeamento de dependências (Playwright, Pandas, Schedule, Openpyxl)
  └── README.md             # Documentação do projeto
