# Deploy 24/7 — Oracle Cloud Free Tier

Guia pra rodar o bot 24/7 numa VM gratuita da Oracle Cloud (Always Free — não é
trial, é perpétuo dentro dos limites). `app.py` roda uma vez e termina a cada
chamada (não é mais um processo contínuo), então o disparo periódico fica a cargo de
um **systemd timer**, que roda o serviço a cada 5 minutos.

## 1. Criar a VM (manual, no console Oracle Cloud)

1. Criar conta na [Oracle Cloud](https://www.oracle.com/cloud/free/) (exige cartão
   de crédito pra verificação, mas o Always Free tier não cobra dentro dos limites).
2. No console, criar uma instância Compute **"Always Free eligible"**:
   - Shape: `VM.Standard.A1.Flex` (ARM, mais generoso — até 4 OCPUs / 24GB RAM no
     free tier). Se a região não tiver capacidade ARM disponível no momento (comum
     em algumas regiões), tentar outra região ou usar o shape AMD
     `VM.Standard.E2.1.Micro` como alternativa (mais limitado, mas também Always
     Free).
   - Imagem: Ubuntu 24.04 LTS (ou a LTS mais recente disponível).
3. Gerar/baixar o par de chaves SSH no momento da criação da instância.
4. Anotar o IP público da instância.
5. Regras de segurança (Security List / Network Security Group): **não é preciso
   abrir nenhuma porta além da 22 (SSH)** — o bot só faz requisições de saída (API
   da Gupy e API do Telegram), não expõe servidor HTTP.

## 2. Preparar a VM (via SSH)

```bash
ssh -i /caminho/da/chave.key ubuntu@<IP_DA_VM>

sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git
```

## 3. Clonar e instalar o bot

```bash
cd ~
git clone https://github.com/carlosbrito92/vagas-gupy-mg-telegram-bot.git
cd vagas-gupy-mg-telegram-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

## 4. Configurar o `.env`

```bash
cp .env.example .env
nano .env
```

Preencher `TELEGRAM_TOKEN` e `CHAT_ID_GRUPO` reais. **Nunca commitar esse arquivo**
(já está no `.gitignore`).

## 5. Configurar o systemd timer

Templates em [`deploy/vagas-gupy-bot.service`](deploy/vagas-gupy-bot.service)
(execução única, `Type=oneshot`) e [`deploy/vagas-gupy-bot.timer`](deploy/vagas-gupy-bot.timer)
(dispara o service a cada 5 minutos). Copiar os dois pra VM e ajustar `User`/paths no
`.service` caso o usuário SSH não seja `ubuntu`:

```bash
sudo cp deploy/vagas-gupy-bot.service /etc/systemd/system/vagas-gupy-bot.service
sudo cp deploy/vagas-gupy-bot.timer /etc/systemd/system/vagas-gupy-bot.timer
sudo nano /etc/systemd/system/vagas-gupy-bot.service   # ajustar User/paths se necessário

sudo systemctl daemon-reload
sudo systemctl enable --now vagas-gupy-bot.timer
sudo systemctl status vagas-gupy-bot.timer
sudo systemctl list-timers vagas-gupy-bot.timer   # confirma o próximo disparo
```

Não habilitar/iniciar o `.service` diretamente — ele é `oneshot`, só existe pra ser
chamado pelo `.timer`.

## 6. Ver logs

```bash
sudo journalctl -u vagas-gupy-bot -f
```

O serviço também grava em `bot.log` no diretório do projeto (redundante com o
journalctl, mas útil pra `grep` rápido sem sudo). Já está no `.gitignore`.

## 7. Atualizar o bot depois de um `git push`

Na VM, dentro do diretório do repositório:

```bash
./deploy/deploy.sh
```

O script (`deploy/deploy.sh`) faz `git pull`, reinstala dependências e reinicia o
serviço. Pra um projeto pessoal isso é suficiente — não há CI/CD automatizado
(GitHub Action fazendo SSH a cada push) configurado propositalmente, pra manter a
complexidade baixa.

## Fora de escopo (deliberadamente)

- Docker — desnecessário pra uma única VM pessoal, adiciona complexidade sem
  benefício real aqui.
- CI/CD automatizado (GitHub Actions com deploy via SSH) — avaliado e descartado
  por ora; o `deploy.sh` manual basta pro porte do projeto.
- Múltiplas VMs / balanceamento de carga — sem necessidade nesta escala.
