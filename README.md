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

## 💬 Comandos do bot

Além do grupo padrão (que recebe **todas** as vagas de BH e região, sem filtro),
qualquer pessoa pode conversar direto com o bot (ou mencionar num grupo onde ele
esteja) pra escolher receber só vagas de áreas específicas:

| Comando | O que faz |
|---|---|
| `/areas` | Lista as áreas disponíveis pra filtro |
| `/definir área1, área2` | Define suas áreas de interesse (substitui as anteriores) |
| `/minhasareas` | Mostra suas áreas configuradas atualmente |
| `/parar` | Cancela o recebimento de vagas |
| `/ajuda` | Mostra a lista de comandos |

Exemplo: `/definir dados e ia, desenvolvimento`

Áreas disponíveis hoje: `administrativo`, `comercial e vendas`, `dados e ia`,
`desenvolvimento`, `financeiro`, `fiscal`, `infra cloud e seguranca`, `juridico`,
`logistica`, `marketing`, `produto e gestao tech`, `rh`. A classificação olha só o
**título** da vaga (lista completa de keywords em `areas.py`).

---

## 🛡️ Diferenciais técnicos (a parte que interessa pra quem programa)

| Característica | Abordagem aqui | Abordagem comum |
|----------------|----------------|------------------|
| Extração | API direct (requests) | Selenium (navegador) |
| Consumo RAM | ~50MB | 500MB+ |
| Velocidade por vaga | < 0.5s | 3-5s |
| Controle de duplicatas | SQLite persistente | Memória volátil |
| Execução | Processo único, sempre rodando (loop) | Reabrir navegador a cada consulta |

**Processo contínuo, sem depender de disparo externo**: `python app.py` sobe uma vez e fica rodando — a cada poucos segundos checa comandos novos no Telegram, e a cada 5 minutos varre vagas novas. Todo o estado (vagas já enviadas, áreas dos usuários, timestamps) fica no SQLite local, que persiste entre reinícios do processo.

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

Pronto. O processo fica rodando em primeiro plano (não termina sozinho) e vai
começar a varrer e enviar vagas. Pra parar, `Ctrl+C` — ele avisa no grupo que
entrou em manutenção antes de encerrar. Pra rodar 24/7 sem depender do seu
terminal aberto, veja a seção de deploy mais abaixo.

---

## 🔧 Fazendo o bot pra você (não só rodando o meu)

Rodar o passo a passo acima já funciona, mas usa **seu próprio bot e grupo** —
não dá pra reaproveitar `TELEGRAM_TOKEN`/`CHAT_ID_GRUPO` de outra pessoa. Veja como
conseguir cada campo do `.env`:

### `TELEGRAM_TOKEN`
1. Fala com o **[@BotFather](https://t.me/BotFather)** no Telegram.
2. `/newbot`, escolhe nome e username (precisa terminar em `bot`).
3. Ele te devolve o token — formato `123456789:AAF...` — copia pro `.env`.

### `CHAT_ID_GRUPO`
1. Cria um grupo no Telegram e adiciona seu bot nele.
2. Manda qualquer mensagem no grupo.
3. Abre no navegador (com o token do passo anterior):
   ```
   https://api.telegram.org/bot<SEU_TOKEN>/getUpdates
   ```
   (troca `<SEU_TOKEN>` pelo token real, sem os `< >`)
4. Procura `"chat":{"id":...}` na resposta — esse número (geralmente negativo,
   tipo `-100...`) é o `CHAT_ID_GRUPO`.

Se vier `"result":[]` vazio, manda outra mensagem no grupo e recarrega a página —
o Telegram só mostra mensagens recentes ainda não confirmadas.

### Campos do `.env`

| Variável | Obrigatória? | Onde conseguir |
|---|---|---|
| `TELEGRAM_TOKEN` | Sim | @BotFather, comando `/newbot` |
| `CHAT_ID_GRUPO` | Sim | `getUpdates` do seu bot, campo `chat.id` |

Não há mais campos de R2/Cloudflare — essa integração foi removida (ver
`PROGRESSO.md` para o histórico de por que ela existiu brevemente e por que
saiu).

Depois disso, se quiser vagas de outra cidade/estado em vez de BH, veja a seção
seguinte.

---

## ⚙️ Quer mudar a região de busca? Fácil

A API da Gupy só filtra por **estado inteiro**, não por cidade. Por isso o bot busca `state: 'Minas Gerais'` e depois filtra a cidade no código, dentro de `CIDADES_ALVO`.

Para mudar de estado, edite o `state` em `params_base` (`app.py`, dentro de `buscar_vagas_gupy()`):

```python
params_base = {'state': 'Minas Gerais', 'limit': 10}
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


## 🔄 Rodando 24/7 (deploy)

`python app.py` é um processo contínuo: sobe, entra num loop e fica rodando até
receber `Ctrl+C` (ou o processo ser encerrado por fora). Ele mesmo cuida do
intervalo entre buscas (5 min por padrão) e do polling de comandos do Telegram
(a cada poucos segundos) — não precisa de nenhum agendador externo disparando
execuções.

Isso também significa que ele só continua rodando enquanto o processo existir.
Pra manter isso de pé 24/7 sem depender do seu terminal aberto, veja
[`DEPLOY.md`](DEPLOY.md) — VM gratuita da Oracle Cloud, rodando o bot como
serviço `systemd` (reinicia sozinho se cair).

> **Nota histórica:** este projeto teve, por um período curto, uma versão
> reescrita para rodar como execução única disparada por cron (pensada para
> Render Cron Job + Cloudflare R2 para persistir o banco entre execuções).
> Essa abordagem foi abandonada — Render Cron Jobs não têm tier gratuito, e o
> modelo quebrava a resposta em tempo real aos comandos do Telegram. Detalhes
> em `PROGRESSO.md`.

---

## 📁 Estrutura do projeto

```
.
├── app.py               # Código principal do bot (loop contínuo)
├── areas.py             # Dicionário de áreas/keywords pro filtro /definir
├── requirements.txt     # Dependências
├── .env.example         # Modelo de variáveis de ambiente
├── .gitignore
├── deploy/               # Templates de deploy (systemd service, script)
├── DEPLOY.md             # Guia de deploy: Oracle Cloud + systemd
├── PROGRESSO.md          # Status real do projeto e histórico de decisões
├── PLANO_MELHORIAS.md    # Roadmap de melhorias futuras
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