# Deploy 24/7 — Render (Cron Job) + Cloudflare R2

Alternativa ao [`DEPLOY.md`](DEPLOY.md) (Oracle Cloud / systemd, processo contínuo),
usada quando não há cartão disponível pra verificação da Oracle Cloud. Arquitetura
diferente: em vez de um processo rodando pra sempre, o Render dispara `python app.py`
periodicamente como **Cron Job**. Cada execução roda, faz o trabalho, e termina —
por isso o estado (banco SQLite) precisa sobreviver entre execuções via Cloudflare R2,
já que instâncias free do Render **não têm disco persistente**.

## Por que Cron Job, não Web Service/Background Worker

- **Web Service**: espera um servidor HTTP escutando numa porta e faz spin-down por
  inatividade de request — não se aplica, o bot não serve HTTP.
- **Background Worker**: processo de longa duração, mas geralmente não tem instância
  free no Render (exige plano pago).
- **Cron Job**: execução curta e periódica, tem free tier — é o encaixe certo pro
  modelo de execução única que o `app.py` usa agora.

## 1. Cloudflare R2 (persistência do banco)

Já coberto na configuração local — recapitulando:

1. Criar um bucket dedicado (ex: `vagas-gupy-bot-db`) no [dashboard R2](https://dash.cloudflare.com/).
2. **Manage R2 API Tokens** → criar token com permissão **Object Read & Write**,
   escopo restrito a esse bucket.
3. Anotar: `Account ID` (aparece no painel R2), `Access Key ID`, `Secret Access Key`,
   nome do bucket.

Essas 4 credenciais vão direto nas variáveis de ambiente do Render (passo 3 abaixo) —
nunca commitadas, nunca coladas em chat/log.

## 2. Criar o Cron Job no Render

No [dashboard do Render](https://dashboard.render.com/):

1. **New** → **Cron Job**.
2. Conectar o repositório `vagas-gupy-mg-telegram-bot` (GitHub).
3. Runtime: **Python 3**.
4. **Build Command**: `pip install -r requirements.txt`
5. **Command**: `python app.py`
6. **Schedule**: `*/5 * * * *` (a cada 5 minutos — mesmo valor de
   `INTERVALO_BUSCA_SEGUNDOS` em `app.py`). Cada execução sempre checa comandos
   pendentes do Telegram; a busca de vagas só roda de fato quando já passou esse
   intervalo desde a última busca registrada (`bot_estado.ultima_busca_em`), então
   rodar o cron mais frequentemente que isso não faz a busca de vaga acontecer mais
   rápido — só deixa comandos (`/ajuda`, `/definir` etc.) mais responsivos.

   **Verificar antes de confirmar**: o plano free do Render pode ter cota mensal de
   minutos/execuções de Cron Job — conferir na tela de pricing atual se `*/5 * * * *`
   (≈288 execuções/dia) cabe no free tier. Se não couber, aumentar o intervalo (ex:
   `*/15 * * * *`) — a busca de vaga simplesmente passa a rodar a cada 15 min em vez
   de 5, ajustando `INTERVALO_BUSCA_SEGUNDOS` em `app.py` pra combinar.

## 3. Variáveis de ambiente

Na aba **Environment** do serviço no Render (não usa `.env` — o Render injeta essas
variáveis diretamente no processo):

```
TELEGRAM_TOKEN=<token do bot>
CHAT_ID_GRUPO=<chat id do grupo firehose>
R2_ACCOUNT_ID=<account id do R2>
R2_ACCESS_KEY_ID=<access key do token R2>
R2_SECRET_ACCESS_KEY=<secret key do token R2>
R2_BUCKET_NAME=<nome do bucket dedicado>
```

## 4. Verificar

Depois do primeiro deploy, checar os logs do Cron Job no painel do Render. Primeira
execução deve mostrar:

```
ℹ️  Não foi possível baixar o banco do R2 (pode ser a primeira execução): ...
🤖 Bot de vagas Gupy — execução única
✅ Comandos registrados no Telegram (sugestão ao digitar '/').
...
☁️  Banco atualizado enviado para o R2.
```

Execuções seguintes devem mostrar `☁️  Banco baixado do R2.` no início — confirma que
o estado está persistindo.

## 5. Atualizar depois de um `git push`

Auto-deploy do Render já cuida disso: por padrão, todo push na branch conectada
dispara um novo build automaticamente. Não precisa de `deploy.sh`/SSH manual como no
caminho Oracle — só confirmar que "Auto-Deploy" está habilitado nas configurações do
serviço.

## Fora de escopo (deliberadamente)

- Docker — Render builda direto do repositório com runtime Python nativo.
- Voltar pro modelo de processo contínuo (`while` + systemd) — só faz sentido se
  migrar pra Oracle Cloud (ou outro host com processo sempre ativo) mais adiante,
  ver `DEPLOY.md`.
