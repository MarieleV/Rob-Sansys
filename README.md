<div align="center">
  <!-- Você pode trocar esse link por uma imagem do seu próprio app depois! -->
  <img src="https://img.icons8.com/fluency/96/000000/bot.png" alt="Ícone de Robô" width="80"/>
  
  <h1>RPA: Extrator de Relatórios & Integração SharePoint</h1>

  <p>
    <img src="https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/Playwright-Web_Automation-2EAD33?style=for-the-badge&logo=playwright&logoColor=white" alt="Playwright">
    <img src="https://img.shields.io/badge/SharePoint-Cloud-0078D4?style=for-the-badge&logo=microsoftsharepoint&logoColor=white" alt="SharePoint">
    <img src="https://img.shields.io/badge/UI-CustomTkinter-4B8BBE?style=for-the-badge&logo=appveyor&logoColor=white" alt="CustomTkinter">
  </p>

  <p><em>Uma solução corporativa completa com interface gráfica e agendamento autônomo em background.</em></p>
</div>

<br>

<h2>📌 Sobre o Projeto</h2>
<p>
  Este projeto é uma solução de <b>Automação Robótica de Processos (RPA)</b> desenvolvida em Python. Ele resolve o gargalo de tarefas manuais e repetitivas, realizando processos que levariam horas em apenas alguns minutos. O robô é capaz de fazer login em um sistema web corporativo, navegar por menus dinâmicos, preencher filtros, aguardar o processamento de relatórios pesados, descompactar arquivos localmente e enviá-los automaticamente para a nuvem (Microsoft SharePoint).
</p>
<p>
  Toda a operação é gerenciada por uma <b>Interface Gráfica Desktop (GUI)</b> que permite ao usuário executar a tarefa na hora ou <b>agendar um horário diário</b> para execução invisível (Modo Headless).
</p>

<br>

<h2>✨ Principais Funcionalidades</h2>

<table>
  <tr>
    <td width="200">🌐 <b>Navegação Resiliente</b></td>
    <td>Automação com Playwright projetada para lidar com carregamentos assíncronos e lentidão extrema de sistemas corporativos.</td>
  </tr>
  <tr>
    <td>☁️ <b>Integração Cloud</b></td>
    <td>Autenticação e upload seguro de arquivos Excel extraídos via API REST do Office365.</td>
  </tr>
  <tr>
    <td>⏰ <b>Agendamento (Threads)</b></td>
    <td>Motor de <i>scheduling</i> trabalhando em segundo plano para não congelar a interface gráfica enquanto o robô aguarda o horário estipulado.</td>
  </tr>
  <tr>
    <td>🔒 <b>Segurança de Dados</b></td>
    <td>Isolamento de rotas e links internos através de variáveis de ambiente (<code>.env</code>), garantindo conformidade e segurança.</td>
  </tr>
  <tr>
    <td>🖥️ <b>Interface Moderna</b></td>
    <td>Aplicação visual construída com <i>CustomTkinter</i>, capturando credenciais dinamicamente e exibindo logs em tempo real.</td>
  </tr>
</table>

<br>

<h2>📂 Arquitetura do Sistema</h2>

<details>
  <summary><b>Clique para visualizar a estrutura modular de pastas</b></summary>
  <br>
  
  ```text
  ├── src/
  │   ├── main.py           # Ponto de entrada e inicialização
  │   ├── gui.py            # Front-end: Desenho da UI e captura de eventos
  │   ├── automacao.py      # Back-end: Core RPA (Playwright + SharePoint API)
  │   └── agendador.py      # Controle temporal e multiprocessamento
  ├── .env.example          # Template seguro das variáveis de configuração
  ├── .gitignore            # Ocultação de ambientes e caches
  ├── requirements.txt      # Mapeamento de dependências
  └── README.md             # Documentação do projeto
