
# 🤖 BH Jobs Scout — Bot de Monitoramento Gupy no Telegram

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 O que é isso?

Um **robô de caça** que varre silenciosamente a plataforma Gupy em busca de oportunidades em **Belo Horizonte e região metropolitana** e as entrega fresquinhas no Telegram, sem há necessidade do usuário ficar recarregando páginas o dia todo.

O bot foi projetado para rodar **24 horas por dia**, verificar novas vagas a cada 5 minutos. Quando encontra algo novo, *katchau!*, as informações da vaga são enviadas diretamente para o grupo.

---

## 🧠 Como funciona — sem firula

Diferente de bots que abrem navegador e consomem memória, este aqui foi pensado e projetado para:

- **Interceptar a API oculta** da Gupy (a mesma que o site usa)
- **Consomir JSON puro** — rápido e leve
- **Usar SQLite** como memória de elefante: nunca repete a mesma vaga
- **Traduzir automaticamente** dados UTC para horário de Brasília
- **Converte termos técnicos** (remote → Remoto, on-site → Presencial)

Ou seja: você recebe a vaga formatada, bonita e no fuso certo, sem duplicação.

---

## 🧩 O que ele entrega no Telegram?

Abaixo está um exemplo de como cada mensagem de uma nova vaga é enviada pelo bot, assim contendo as seguintes informações:

```
🎯 VAGA GUPY - BELO HORIZONTE E REGIÃO!

💼 Vaga: Analista de Dados Pleno
🏢 Empresa: Nubank
📍 Local: Belo Horizonte - Minas Gerais
💻 Modelo: Híbrido
📄 Tipo: Efetivo
♿ PCD: Não informado
📅 Data: 15/05/2026 às 14:32

🔗 Clique aqui para se candidatar
```

Tudo com **links diretos** e formatação limpa para mobile e pra ser prático.

---

## 🛡️ Diferenciais técnicos (a parte que interessa pra quem programa)

| Característica | Abordagem aqui | Abordagem comum |
|----------------|----------------|------------------|
| Extração | API direct (requests) | Selenium (navegador) |
| Consumo RAM | ~50MB | 500MB+ |
| Velocidade por vaga | < 0.5s | 3-5s |
| Controle de duplicatas | SQLite persistente | Memória volátil |
| Execução contínua | Loop com signal handler | Cron job / agendador |

**Tratamento de interrupção incluso**: se o bot for parado de propósito (Ctrl+C) ou por alguma problema na aplicação, ele avisa o grupo que entrou em manutenção e avisa quando voltar.

---

## 🚀 Instalação em 4 passos

### 1. Clone o repositório
```bash
git clone https://github.com/carlosbrito92/vagas-gupy-mg-telegram-bot
cd vagas-gupy-mg-telegram-bot
```

### 2. Ambiente virtual e dependências
```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
```

### 3. Configure o `.env`
Copie `.env.example` para `.env` e preencha os valores:
```bash
cp .env.example .env
```
```env
TELEGRAM_TOKEN=seu_token_aqui
CHAT_ID_GRUPO=numero_do_grupo_aqui
```

### 4. Rode
```bash
python app.py
```

Pronto. Ele vai começar a varrer e enviar vagas.

---

## ⚙️ Quer mudar a região de busca? Fácil

A API da Gupy só filtra por **estado inteiro**, não por cidade. Por isso o bot busca `state: 'Minas Gerais'` e depois filtra a cidade no código, dentro de `CIDADES_ALVO`.

Para mudar de estado, edite o `state` em `filtros_de_busca` (`app.py`, dentro de `buscar_vagas_gupy()`):

```python
filtros_de_busca = [
    {"nome": "BELO HORIZONTE E REGIÃO", "params": {'state': 'Minas Gerais', 'limit': 10}}
]
```

Para mudar as cidades-alvo dentro do estado, edite a lista `CIDADES_ALVO` no topo de `app.py`:

```python
CIDADES_ALVO = [
    "belo horizonte",
    "contagem",
    "betim",
    ...
]
```


## 🔄 Execução contínua vs. Agendada

Este código foi modificado para rodar **em loop infinito**, diferente do original que rodava uma vez e parava.

- **Loop padrão**: verifica a cada 5 minutos
- **Para parar**: `Ctrl+C` (ele avisa o grupo antes de sair)
- **Para rodar em segundo plano** (Linux/macOS): `nohup python app.py &`
- **Para Windows**: pode usar Task Scheduler ou manter o terminal aberto

Se quiser o comportamento original (uma execução e para), basta remover o `while` do `main()`.

---

## 📁 Estrutura do projeto

```
.
├── app.py               # Código principal do bot
├── requirements.txt     # Dependências
├── .env.example         # Modelo de variáveis de ambiente
├── .gitignore
├── vagas_gupy.db        # Banco SQLite (criado automaticamente, ignorado no git)
├── .env                 # Suas credenciais (não comitar!)
└── README.md            # Este arquivo
```

---

## 🙏 Créditos e inspiração

Este projeto foi **fortemente inspirado** no trabalho original do **[Lucas Nunes](https://github.com/lucasnunestrabalho99-sudo)** e seu repositório:

🔗 **[telegram-vagas-gupy-bot](https://github.com/lucasnunestrabalho99-sudo/telegram-vagas-gupy-bot/tree/main)**

O código original cobria vagas para **Rio de Janeiro + Home Office** com uma execução única.  
A versão que você está vendo agora:

- Adaptou para **São Paulo** (state filter)
- Adicionou **execução contínua** (loop de 5 minutos)
- Incluiu **avisos de manutenção** (start/stop no Telegram)
- Manteve o core de API + SQLite intacto

A partir dessa versão para São Paulo, o bot foi **readaptado para Belo Horizonte e região metropolitana**: o filtro passou a buscar `state: 'Minas Gerais'` na API da Gupy e restringir o resultado, no código, a uma lista de cidades da região metropolitana de BH (`CIDADES_ALVO`).

**Todo respeito ao trabalho original.** Se você quer ver a implementação base ou entender como funciona a interceptação da API da Gupy, o repositório do Lucas é o melhor ponto de partida.

---

## 📄 Licença

MIT — Use, modifique, compartilhe. Só não esquece de dar os créditos, combinado?

