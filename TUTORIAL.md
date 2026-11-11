# 📘 Tutorial de Operação e Instalação: Personal Automation Hub (PAH)

Guia passo a passo para configuração, inicialização, execução de testes e resolução de problemas no projeto **Personal Automation Hub (PAH)** (`personal-automation-hub`).

---

## 🛠️ 1. Visão Geral e Arquitetura

> Um motor de automação robusto, modular e centralizado para gerenciar, agendar e executar tarefas diárias em segundo plano de forma autônoma. Este projeto atua como um orquestrador central que roda em segundo plano gerenciando agendamentos por tempo (CRON/Intervalos) e escutando eventos do sistema de arquivos em tempo real (Watchdog). Ele foi proj...

- **Tecnologias Principais:** Python 3.11+
- **Diretório do Módulo:** `personal-automation-hub`

---

## 📋 2. Pré-requisitos do Sistema

Antes de iniciar a configuração local, certifique-se de ter os seguintes componentes instalados em seu ambiente de desenvolvimento:

- **Git:** Para clonagem e versionamento.
- **Ambiente de Runtime:** Ferramentas correspondentes à stack do projeto (Python 3.11+):
  - Node.js 18+ / Python 3.11+ / Go 1.24+ / Java 21 LTS / Flutter SDK / CMake.
- **Docker Engine & Docker Compose:** Recomendado para execução de containers e dependências.

---

## 🚀 3. Passo a Passo de Setup e Instalação

### Passo 1: Acessar a Pasta do Projeto
```bash
cd personal-automation-hub
```

### Passo 2: Instalação de Dependências
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

---

## ⚙️ 4. Configuração do Ambiente

Configure o arquivo de variáveis de ambiente (`.env` ou configurações de projeto) localizado no diretório raiz de `personal-automation-hub`:

```ini
# Configurações Gerais
ENVIRONMENT=development
LOG_LEVEL=info

# URLs de Conexão e Serviços
DATABASE_URL=sqlite:///./app.db
REDIS_URL=redis://localhost:6379/0
```

---

## 💻 5. Guia de Execução

### Inicializando a Aplicação
Inicie a aplicação ou serviço utilizando o comando correspondente:

```bash
python3 main.py # ou uvicorn/streamlit/fastapi app
```

---

## 🧪 6. Testes e Validação

Para validar o funcionamento do módulo e garantir que não há regressões, execute a suíte de testes:

```bash
python3 -m pytest tests/ -v
```

---

## 🔍 7. Troubleshooting e Resolução de Problemas

1. **Porta em uso ou Conflito de Rede:**
   - Cancele processos pendentes na porta utilizada ou utilize `docker compose down` e suba novamente.
2. **Erros de Dependências Ausentes:**
   - Certifique-se de estar executando os comandos dentro do diretório `personal-automation-hub` e com as versões corretas das linguagens.
3. **Falhas na Suíte de Testes:**
   - Verifique se as variáveis de ambiente necessárias foram inicializadas corretamente.
