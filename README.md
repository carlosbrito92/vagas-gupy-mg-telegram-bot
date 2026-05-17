
# 🤖 São Paulo Jobs Scout — Bot de Monitoramento Gupy no Telegram

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-24%2F7%20online-brightgreen)](https://t.me/vagasgupysp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 O que é isso?

Um **robô de caça** que varre silenciosamente a plataforma Gupy em busca de oportunidades no estado de **São Paulo** e as entrega fresquinhas no Telegram, sem há necessidade do usuário ficar recarregando páginas o dia todo.

O bot foi projetado para rodar **24 horas por dia**, verificar novas vagas a cada 5 minutos. Quando encontra algo novo, *katchau!*, as informações da vaga são enviadas diretamente para o grupo.

---

## 📱 Veja funcionando ao vivo

👉 **[Grupo Telegram: Vagas Gupy | São Paulo](https://web.telegram.org/k/#@vagasgupysp)**

Lá o robô está ativo 24/7. Entre, veja o formato das mensagens e acompanhe as oportunidades em tempo real.

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
🎯 VAGA GUPY - SÃO PAULO!

💼 Vaga: Analista de Dados Pleno
🏢 Empresa: Nubank
📍 Local: São Paulo - SP
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
git clone https://github.com/opablodantas/vagas-gupy-sp-telegram-bot
cd vagas-gupy-sp-telegram-bot
```

### 2. Ambiente virtual e dependências
```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
```

### 3. Configure o `.env` (igual do projeto original, adaptado)
```env
TELEGRAM_TOKEN=seu_token_aqui
CHAT_ID_GRUPO=numero_do_grupo_aqui
```

### 4. Rode
```bash
python main.py
```

Pronto. Ele vai começar a varrer e enviar vagas.

---

## ⚙️ Quer mudar para outro estado? Fácil

No arquivo `main.py`, altere a lista `filtros_de_busca`:

```python
filtros_de_busca = [
    {"nome": "RIO GRANDE DO SUL", "params": {'state': 'Rio Grande do Sul', 'limit': 10}}
]
```


## 🔄 Execução contínua vs. Agendada

Este código foi modificado para rodar **em loop infinito**, diferente do original que rodava uma vez e parava.

- **Loop padrão**: verifica a cada 5 minutos
- **Para parar**: `Ctrl+C` (ele avisa o grupo antes de sair)
- **Para rodar em segundo plano** (Linux/macOS): `nohup python main.py &`
- **Para Windows**: pode usar Task Scheduler ou manter o terminal aberto

Se quiser o comportamento original (uma execução e para), basta remover o `while` do `main()`.

---

## 📁 Estrutura do projeto

```
.
├── main.py              # Código principal do bot
├── vagas_gupy.db        # Banco SQLite (criado automaticamente)
├── .env                 # Suas credenciais (não comitar!)
├── requirements.txt     # Dependências
└── README.md            # Este arquivo
```

---

## 🙏 Créditos e inspiração

Este projeto foi **fortemente inspirado** no trabalho original do **[Lucas Nunes](https://github.com/lucasnunestrabalho99-sudo)** e seu repositório:

🔗 **[telegram-vagas-gupy-bot](https://github.com/lucasnunestrabalho99-sudo/telegram-vagas-gupy-bot/tree/main)**

O código original cobria vagas para **Rio de Janeiro + Home Office** com uma execução única.  
A versão que você está vendo agora:

- Adaptou para **apenas São Paulo** (state filter)
- Adicionou **execução contínua** (loop de 5 minutos)
- Incluiu **avisos de manutenção** (start/stop no Telegram)
- Manteve o core de API + SQLite intacto

**Todo respeito ao trabalho original.** Se você quer ver a implementação base ou entender como funciona a interceptação da API da Gupy, o repositório do Lucas é o melhor ponto de partida.

---

## 📄 Licença

MIT — Use, modifique, compartilhe. Só não esquece de dar os créditos, combinado?

---

**Grupo ao vivo:** [@vagasgupysp](https://web.telegram.org/k/#@vagasgupysp)
