#!/usr/bin/env bash
# Atualiza o bot na VM: puxa código novo e reinicia o serviço systemd.
# Rodar direto na VM, dentro do diretório do repositório.
set -euo pipefail

git pull
source venv/bin/activate
pip install -r requirements.txt
deactivate

sudo systemctl restart vagas-gupy-bot
sudo systemctl status vagas-gupy-bot --no-pager
