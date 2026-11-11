# 🚀 Personal Automation Hub (PAH)
> Um motor de automação robusto, modular e centralizado para gerenciar, agendar e executar tarefas diárias em segundo plano de forma autônoma.

Este projeto atua como um orquestrador central que roda em segundo plano gerenciando agendamentos por tempo (CRON/Intervalos) e escutando eventos do sistema de arquivos em tempo real (Watchdog). Ele foi projetado usando princípios de arquitetura pluggable, permitindo a adição de novas tarefas no diretório `/tasks` sem alterar o motor central.

---

## 🛠️ Stack Tecnológico
* **Linguagem:** Python 3.11+ (Recomendado 3.12+)
* **Agendamento e Orquestração:** `APScheduler` (Advanced Python Scheduler)
* **Monitoramento do Sistema:** `watchdog` (Eventos em tempo real do sistema operacional)
* **Manipulação de Dados:** `pandas` (Limpeza, agregação e estruturação de dados em CSV/Planilhas)
* **Interações HTTP & Web APIs:** `requests`
* **Versão:** `v1.0.0`

---

## 🏗️ 1. Arquitetura do Sistema

O fluxo de dados e controle do Personal Automation Hub segue o modelo abaixo:

```text
+-----------------------+      +-------------------------------+
|   Agendador de Tempo  |      |  Monitor de Eventos de Disco  |
|     (APScheduler)     |      |          (Watchdog)           |
+-----------+-----------+      +---------------+---------------+
            |                                  |
            | (Dispara Evento/Task)            | (Dispara Novo Arquivo)
            +-----------------+----------------+
                              |
                              v
                  +-----------+-----------+
                  |      Task Runner      |  <--- [Isolamento de Exceções]
                  |  (core.runner.py)     |  <--- [Medição de Performance]
                  +-----------+-----------+
                              |
            +-----------------+-----------------+
            |                 |                 |
            v                 v                 v
     +------+------+   +------+------+   +------+------+
     | Organizar   |   | Relatório   |   | Limpeza de  |  ... (Novas tasks em /tasks)
     | Downloads   |   | Diário      |   | Sistema     |
     +-------------+   +-------------+   +-------------+
            |                 |                 |
            +-----------------+-----------------+
                              |
                              v
                +-------------+-------------+
                | Sistema de Logs & Alertas |
                | (logs/automation.log)     |
                +---------------------------+
```

### Componentes Principais
1. **Orquestrador Central (`main.py`)**: Inicializa o ambiente, captura sinais do sistema operacional para encerramento gracioso (`SIGINT`, `SIGTERM`), e inicia os serviços de monitoramento de diretórios e agendamento de tempo.
2. **Logger (`core/logger.py`)**: Fornece um logger thread-safe com rotação automática de arquivos (tamanho máximo de 5MB e até 5 arquivos de backup) gravando em `logs/automation.log` e no terminal simultaneamente.
3. **Dynamic Task Loader (`core/loader.py`)**: Examina o diretório `/tasks` em tempo de execução, descobrindo e importando novos arquivos Python dinamicamente, permitindo a extensão do sistema sem refatorações.
4. **Task Runner (`core/runner.py`)**: Envelopa as funções em um bloco seguro de tratamento de erros. Garante que se uma tarefa falhar, as outras continuarão rodando de forma estável. Registra o tempo de execução e stacktraces detalhados em caso de falhas.
5. **Scheduler (`core/scheduler.py`)**: Encapsula o `BackgroundScheduler` para gerenciar tarefas baseadas em intervalos regulares ou regras complexas do tipo CRON.
6. **Watcher (`core/watcher.py`)**: Controla os observadores do `watchdog` para mapear gatilhos em tempo real em diretórios específicos e disparar ações associadas.

---

## 📂 2. Estrutura de Diretórios

```text
personal-automation-hub/
├── core/                        # Núcleo de orquestração do Hub
│   ├── __init__.py
│   ├── loader.py                # Importador dinâmico de tarefas de automação
│   ├── logger.py                # Logger centralizado e thread-safe rotativo
│   ├── runner.py                # Executor seguro de isolamento de exceções
│   ├── scheduler.py             # Agendador de intervalos e CRON (APScheduler)
│   └── watcher.py               # Monitorador de arquivos de diretórios (Watchdog)
├── logs/                        # Arquivos físicos de log de execução
│   └── automation.log           # Log rotativo com nível INFO/ERROR
├── tasks/                       # Scripts de automações (Pluggable)
│   ├── __init__.py
│   ├── limpeza_sistema.py       # Exemplo de tarefa de limpeza agendada
│   ├── organizar_downloads.py   # Exemplo de tarefa de monitoramento por watchdog
│   └── relatorio_diario.py      # Exemplo de relatório diário com pandas e API/Webhook
├── tests/                       # Suite de testes automatizados com pytest
│   ├── __init__.py
│   └── test_hub.py              # Testes unitários e de integração
├── README.md                    # Manual de Operação e Arquitetura do Hub
├── requirements.txt             # Dependências de bibliotecas de terceiros
└── main.py                      # Arquivo de entrada principal do orquestrador
```

---

## 🚀 3. Instalação e Configuração

### Pré-requisitos
* Python 3.11 ou superior instalado em sua máquina.

### Passo 1: Clonar e navegar para o diretório
```bash
cd personal-automation-hub
```

### Passo 2: Criar e ativar um Ambiente Virtual (Opcional, mas Altamente Recomendado)
```bash
python3 -m venv venv
source venv/bin/activate  # No Linux/MacOS
# ou
venv\Scripts\activate     # No Windows
```

### Passo 3: Instalar as dependências necessárias
```bash
pip install -r requirements.txt
```

---

## ⚙️ 4. Configuração por Variáveis de Ambiente

As tarefas incluídas utilizam variáveis de ambiente para customização do seu comportamento. Crie um arquivo `.env` na raiz ou declare as seguintes chaves em seu sistema:

| Variável | Valor Padrão | Descrição |
|----------|--------------|-----------|
| `DOWNLOADS_WATCH_DIR` | `Downloads` | Diretório que a tarefa `organizar_downloads` monitora em busca de novos arquivos. |
| `API_REPORT_DATA_URL` | `https://jsonplaceholder.typicode.com/posts` | URL de onde o `relatorio_diario` baixa dados estatísticos estruturados. |
| `NOTIFICATIONS_WEBHOOK_URL` | *(Vazio)* | URL do Webhook (Discord, Slack, etc.) para despachar o relatório diário formatado. |
| `CLEANUP_TARGET_DIR` | `temp_purge` | Pasta alvo para a rotina `limpeza_sistema` verificar arquivos antigos. |
| `CLEANUP_MAX_AGE_SECONDS`| `604800` (7 dias) | Idade máxima do arquivo em segundos antes de ser excluído permanentemente pelo purger. |

---

## 💻 5. Execução & Uso

### Executando em modo interativo
Para iniciar o Hub de Automação no terminal:
```bash
PYTHONPATH=. python3 main.py
```

### Mantendo o Hub Rodando em Segundo Plano (Daemonization)

#### A. No Linux (Systemd Service)
Para rodar como um serviço persistente do sistema operacional no Linux que se auto-inicializa no boot:

1. Crie o arquivo de definição de serviço `/etc/systemd/system/automation-hub.service`:
```ini
[Unit]
Description=Personal Automation Hub Daemon
After=network.target

[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/caminho/completo/para/personal-automation-hub
ExecStart=/caminho/completo/para/personal-automation-hub/venv/bin/python3 main.py
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=personal-automation-hub

[Install]
WantedBy=multi-user.target
```

2. Ative e inicie o serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable automation-hub.service
sudo systemctl start automation-hub.service
```

3. Verifique o status:
```bash
sudo systemctl status automation-hub.service
```

#### B. No Windows (Windows Task Scheduler)
Para rodar no Windows de forma invisível:
1. Abra o **Agendador de Tarefas do Windows** (Task Scheduler).
2. Clique em **Criar Tarefa Básica** (Create Basic Task).
3. Selecione o gatilho "Ao inicializar o computador" (When the computer starts).
4. Em "Ação", escolha "Iniciar um programa" (Start a program).
5. Preencha:
   * **Programa/script**: Crie um script `.bat` ou execute diretamente o executável do python de seu venv: `C:\caminho\para\venv\Scripts\python.exe`.
   * **Adicionar argumentos**: `main.py`
   * **Iniciar em**: `C:\caminho\completo\para\personal-automation-hub`.
6. Nas Propriedades da tarefa, marque a opção "Executar independentemente de usuário estar conectado ou não" e "Ocultar" para rodar silenciosamente em segundo plano.

---

## 🧪 6. Testes Automatizados

Uma suite completa de testes de alta fidelidade está disponível na pasta `tests/`, cobrindo isolamento, validações, concorrência e mocks das tarefas incluídas.

Para rodar os testes utilizando `pytest`:
```bash
PYTHONPATH=personal-automation-hub python3 -m pytest personal-automation-hub/tests/ -v
```

Saída esperada:
```text
collected 8 items

personal-automation-hub/tests/test_hub.py::test_task_runner_success PASSED
personal-automation-hub/tests/test_hub.py::test_task_runner_failure PASSED
personal-automation-hub/tests/test_hub.py::test_dynamic_task_loader PASSED
personal-automation-hub/tests/test_hub.py::test_scheduler_register PASSED
personal-automation-hub/tests/test_hub.py::test_watcher_register PASSED
personal-automation-hub/tests/test_hub.py::test_task_organizar_downloads PASSED
personal-automation-hub/tests/test_hub.py::test_task_relatorio_diario_api_success PASSED
personal-automation-hub/tests/test_hub.py::test_task_limpeza_sistema PASSED
============================== 8 passed in 0.71s ===============================
```

---

## 🔒 7. Práticas de Segurança e Resiliência
* **Isolamento de Erros:** O Hub implementa um executor encapsulado com cláusula de proteção global (`try-except Exception`). Isso garante que um erro grave em uma tarefa (por exemplo, falha de rede ao chamar uma API no `relatorio_diario`) **nunca** derrube o orquestrador principal ou interrompa o monitoramento de arquivos do `watchdog`.
* **Segurança do Sistema de Arquivos:** O `limpeza_sistema` opera de forma estrita em um diretório temporário isolado por variável de ambiente, garantindo que arquivos fora do diretório pretendido não sejam acidentalmente purgados.
* **Resiliência do Watchdog:** Ao detectar colisões de nomes (arquivos com nomes idênticos sendo movidos repetidamente para a pasta de destino), o `organizar_downloads` adiciona sufixos numéricos sequenciais (`_1`, `_2`) para evitar sobrescrever dados cruciais do usuário de forma silenciosa.

---

## 🔍 8. Troubleshooting (Solução de Problemas)

| Sintoma / Erro | Causa Provável | Solução Recomendada |
|----------------|----------------|---------------------|
| `ModuleNotFoundError` no terminal | As dependências de terceiros não foram devidamente instaladas no interpretador ativo. | Execute `pip install -r requirements.txt` garantindo que seu ambiente virtual esteja ativado. |
| `FileNotFoundError` ao iniciar o watchdog | O diretório especificado na variável de ambiente `DOWNLOADS_WATCH_DIR` não existe. | O motor cria automaticamente o diretório se inexistente, mas certifique-se de que o usuário ativo possui permissões de escrita/leitura na pasta raiz. |
| Webhook diário não dispara notificações | A variável `NOTIFICATIONS_WEBHOOK_URL` está vazia ou a URL fornecida é inválida. | Configure uma URL válida de webhook do Discord/Slack na inicialização do serviço. Caso offline, a rotina armazena com segurança o relatório formatado nos logs locais. |
| CPU alta ou consumo elevado | Intervalo do scheduler configurado com valor excessivamente baixo. | Revise os parâmetros de tempo no trigger das tarefas dentro do diretório `/tasks`. Evite agendar tarefas pesadas com intervalos inferiores a 10 segundos. |
