# Progresso do projeto

> Este arquivo existe para responder uma pergunta específica a qualquer momento:
> **"o que está rodando de verdade, agora, e onde?"** — sem precisar inferir isso
> a partir do código ou de arquivos de configuração presentes no repositório.
> Código existir no repo NÃO significa que está implantado ou funcionando.
> Atualize este arquivo sempre que o status real mudar (não a cada commit).

---

## Status atual (20/08/2026)

**Onde o bot está rodando:** ambiente de desenvolvimento (GitHub Codespace),
processo manual via `python app.py`. Ainda não há deploy 24/7 persistente
fora de uma sessão de terminal aberta — ver `PLANO_MELHORIAS.md` para o
plano de deploy via Oracle Cloud + systemd.

**O que funciona hoje:** `app.py` voltou ao modelo de loop contínuo
(`while executando:`), sem R2/boto3/cron. Testado e validado de ponta a
ponta nesta data:
- Busca de vagas na API da Gupy e envio para o Telegram — OK.
- Comandos (`/ajuda`, `/definir`, `/areas`, `/minhasareas`, `/parar`)
  respondendo em tempo real com o processo rodando continuamente — OK.

`requirements.txt` limpo (só `requests` e `python-dotenv`, sem `boto3`).

**Próximo passo:** decidir e executar o deploy 24/7 (ver
`PLANO_MELHORIAS.md`, seção Oracle Cloud), já que hoje o bot só roda
enquanto alguém mantém o terminal do Codespace aberto.

---

## Arquitetura pretendida (o que estamos construindo de volta)

- Um processo Python que roda continuamente (`while True`), local ou numa VM.
- A cada ~3s, faz polling do Telegram (`getUpdates`) e processa comandos
  novos (`/definir`, `/areas`, `/minhasareas`, `/parar`, `/ajuda`).
- A cada ~5 minutos, varre a API da Gupy (filtro `state=Minas Gerais` +
  filtro de cidade no código para região metropolitana de BH) e envia vagas
  novas por Telegram, respeitando as áreas que cada chat configurou.
- Estado (histórico de vagas enviadas, áreas por usuário, offset de updates)
  em SQLite local (`vagas_gupy.db`), sem dependência de storage externo.
- **Sem cron, sem R2, sem boto3.** Essas peças foram introduzidas numa
  tentativa de deploy que não chegou a funcionar (ver Histórico) e estão
  sendo removidas.

Deploy 24/7 (VM com systemd) é uma melhoria pretendida, mas **ainda não
decidida em definitivo** — ver `PLANO_MELHORIAS.md` para o racional de
Oracle Cloud Free Tier vs. alternativas, e a seção Histórico abaixo para
por que a tentativa anterior (Render) foi abandonada.

---

## Histórico (mais recente primeiro)

### 20/08/2026 — Reversão concluída e validada

`app.py` reescrito manualmente (modo "Piloto/Copiloto", em patches pequenos
revisados um a um) de volta ao modelo de loop contínuo: bloco R2/`boto3`
removido, `signal_handler` e mensagens de manutenção/retorno reintroduzidos,
`main()` reescrito com `while executando:`. Boas adições da tentativa
anterior foram mantidas (`busca_e_devida`/`registrar_ultima_busca` via
banco, limpeza automática de vagas antigas, `garantir_primeira_ativacao`
evitando spam de "ROBÔ ATIVADO" a cada reinício). `requirements.txt`
também limpo (removido `boto3`).

Testado de ponta a ponta rodando num GitHub Codespace: busca de vaga OK,
comandos (`/ajuda`, `/definir` etc.) respondendo em tempo real OK.

`README.md` também atualizado nas seções que descreviam o modelo cron/R2
como padrão (diferenciais técnicos, instalação, campos de `.env`, seção de
execução, estrutura de arquivos), com nota histórica linkando pra este
arquivo.

### 20/08/2026 — Diagnóstico: comandos não funcionavam, causa raiz identificada

Testando `/ajuda`, `/definir` e outros comandos, nenhum respondia. Ao tentar
`python app.py` local para investigar, o script falhou com
`ModuleNotFoundError: No module named 'boto3'`.

Investigação revelou que uma sessão anterior do Claude Code:
1. Reescreveu `app.py` inteiro para o modelo "execução única" (sem loop,
   sem `signal_handler`), assumindo que seria disparado por um cron job.
2. Adicionou integração com Cloudflare R2 (`boto3`) para persistir o SQLite
   entre execuções, já que cron jobs normalmente não têm disco persistente.
3. Criou arquivos de configuração para deploy no Render (`render.yaml`,
   `DEPLOY-render.md`).
4. **Afirmou ao usuário que o deploy no Render estava confirmado e
   funcionando** ("Confirmado — deploy real é Render (Cron Job)"), com base
   apenas na existência desses arquivos no repositório — sem ter de fato
   verificado um serviço ativo no dashboard do Render.

Na prática: o usuário nunca terminou de configurar o serviço no Render (não
havia variáveis de ambiente lá), e os testes anteriores que "funcionaram"
(comandos respondendo no Telegram) aconteceram porque o `app.py` estava
rodando **localmente no terminal do usuário** naquele momento — não porque
havia qualquer coisa implantada em produção.

**Causa raiz do erro do Claude Code:** não havia uma fonte de verdade
separando "código presente no repositório" de "sistema de fato implantado e
funcionando". A existência de arquivos de configuração de deploy foi tomada
como evidência de deploy bem-sucedido. Este arquivo (`PROGRESSO.md`) existe
para eliminar essa ambiguidade daqui para frente.

**Decisão tomada:** reverter para o modelo de loop contínuo. Ver
`PLANO_MELHORIAS.md` para a análise de custo/risco que motivou essa escolha
(Render Cron Jobs não têm tier gratuito — confirmado por busca — e exigem
reescrever o app para um modelo stateless com sync externo, o que não se
paga frente ao ganho de evitar o cartão de crédito de verificação da
Oracle).

**Ação de segurança tomada:** `TELEGRAM_TOKEN` foi exposto em texto puro
numa sessão do terminal (colado pelo usuário ao pedir ajuda ao Claude Code)
e foi rotacionado imediatamente após identificado. Credenciais do R2 também
foram expostas na mesma sessão — avaliar se ainda serão necessárias após a
reversão; se o R2 deixar de ser usado, revogar essas credenciais também.

### Anterior — implementação do filtro por área

Bot evoluiu de "envia tudo para um único grupo" para suportar múltiplos
chats com áreas de interesse configuráveis via comando (`/definir`), com
dicionário de classificação por palavra-chave em `areas.py`. Essa parte
está estável e não foi afetada pela confusão de arquitetura acima —
`areas.py` permanece inalterado.

### Anterior — adaptação do fork original (São Paulo → Belo Horizonte)

Bot é um fork adaptado de um projeto que buscava vagas Gupy em São Paulo.
Adaptado para filtrar `state=Minas Gerais` + lista de cidades da região
metropolitana de BH no código (a API da Gupy só filtra por estado, não por
cidade).

---

## Lições para sessões futuras (do Claude Code ou de qualquer assistente)

- **Nunca declarar "deploy confirmado" ou "rodando em produção" sem
  verificação direta** (dashboard, API de status, ou teste ponta a ponta
  contra o serviço remoto). A presença de arquivos de configuração no repo
  não é evidência de que o serviço está ativo.
- Antes de reescrever a arquitetura de execução de um sistema (ex: loop
  contínuo → cron), **confirmar explicitamente com o usuário**, já que isso
  tem efeitos colaterais não óbvios (aqui, comandos do Telegram pararam de
  funcionar de forma silenciosa).
- Ao atualizar este arquivo, escrever o status atual primeiro (o que importa
  para quem chega agora), e mover contexto histórico para "Histórico" —
  não deixar a narrativa cronológica ser a única forma de descobrir o que
  está rodando hoje.