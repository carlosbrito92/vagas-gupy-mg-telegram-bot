import os
import time
import sqlite3
import requests
import unicodedata
import signal
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta

from areas import AREAS

# --- 1. CONFIGURAÇÕES E CAMINHOS ---
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(DIRETORIO_ATUAL, '.env'))
CAMINHO_BANCO = os.path.join(DIRETORIO_ATUAL, 'vagas_gupy.db')

TOKEN = os.getenv("TELEGRAM_TOKEN")
# CHAT_ID_GRUPO agora é opcional: se definido, esse chat recebe TODAS as
# vagas de BH e região, sem filtro de área (comportamento antigo, tipo "firehose").
# Além disso, qualquer chat que rodar /definir passa a receber só as áreas escolhidas.
CHAT_ID_PADRAO = os.getenv("CHAT_ID_GRUPO")

TRADUCAO_MODELO = {
    "on-site": "Presencial",
    "hybrid": "Híbrido",
    "remote": "Remoto"
}

TRADUCAO_TIPO_VAGA = {
    "vacancy_type_effective": "Efetivo",
    "vacancy_type_apprentice": "Jovem Aprendiz",
    "vacancy_type_internship": "Estágio",
    "vacancy_type_temporary": "Temporário",
    "vacancy_type_freelancer": "Freelancer"
}

# A API da Gupy só filtra por ESTADO, não por cidade.
# Por isso buscamos "Minas Gerais" e filtramos a cidade no código
# usando essa lista (case-insensitive, sem acento é opcional).
CIDADES_ALVO = [
    "belo horizonte",
    "contagem",
    "betim",
    "nova lima",
    "santa luzia",
    "ribeirão das neves",
    "sabará",
    "vespasiano",
]

INTERVALO_BUSCA_SEGUNDOS = 300  # 5 minutos: intervalo mínimo entre buscas de vaga.
# Cada execução do script (disparada pelo cron job) sempre checa comandos, mas só
# faz busca de vaga se já tiver passado esse tempo desde a última busca registrada
# em bot_estado — ver busca_e_devida().
INTERVALO_ENTRE_ENVIOS_SEGUNDOS = 3
INTERVALO_LIMPEZA_DIAS = 30  # de quanto em quanto tempo apaga vagas_enviadas antigas
DIAS_RETENCAO_VAGAS_ENVIADAS = 30  # idade a partir da qual uma vaga enviada é apagada


# Flag para controle de interrupção (Ctrl+C)
executando = True

# --- 2. NORMALIZAÇÃO DE TEXTO E CLASSIFICAÇÃO DE ÁREA ---
def normalizar(texto):
    """Remove acentuação e coloca em minúsculo, para comparação de texto."""
    if not texto:
        return ''
    nfkd = unicodedata.normalize('NFKD', texto)
    sem_acento = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.lower()


def classificar_vaga(titulo, descricao=''):
    """
    Retorna a lista de áreas (chaves de AREAS) às quais a vaga pertence.

    Regra: só o TÍTULO é considerado — precisa bater com pelo menos uma
    keyword da área. O parâmetro `descricao` não é usado na classificação.
    """
    titulo_norm = f' {normalizar(titulo)} '
    areas_encontradas = []
    for area, keywords in AREAS.items():
        if any(kw in titulo_norm for kw in keywords):
            areas_encontradas.append(area)
    return areas_encontradas


def areas_validas_str():
    return ", ".join(sorted(AREAS.keys()))


# --- 3. BANCO DE DADOS ---
def iniciar_banco():
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vagas_enviadas (
            chat_id TEXT NOT NULL,
            link TEXT NOT NULL,
            data_publicacao TEXT,
            titulo TEXT,
            PRIMARY KEY (chat_id, link)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios_areas (
            chat_id TEXT NOT NULL,
            area TEXT NOT NULL,
            PRIMARY KEY (chat_id, area)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_estado (
            chave TEXT PRIMARY KEY,
            valor TEXT
        )
    ''')

    # Migração: bancos criados antes desta versão não têm a coluna enviado_em.
    colunas = [row[1] for row in cursor.execute("PRAGMA table_info(vagas_enviadas)")]
    if 'enviado_em' not in colunas:
        cursor.execute('ALTER TABLE vagas_enviadas ADD COLUMN enviado_em TEXT')

    conn.commit()
    return conn, cursor


def cidade_e_alvo(cidade):
    """Verifica se a cidade da vaga está na região metropolitana de BH"""
    if not cidade:
        return False
    cidade_normalizada = normalizar(cidade.strip())
    return any(alvo in cidade_normalizada for alvo in CIDADES_ALVO)


def obter_areas_do_chat(cursor, chat_id):
    cursor.execute('SELECT area FROM usuarios_areas WHERE chat_id = ?', (str(chat_id),))
    return [row[0] for row in cursor.fetchall()]


def definir_areas_do_chat(cursor, conn, chat_id, areas):
    """Substitui completamente as áreas de um chat pela lista fornecida."""
    cursor.execute('DELETE FROM usuarios_areas WHERE chat_id = ?', (str(chat_id),))
    for area in areas:
        cursor.execute('INSERT INTO usuarios_areas VALUES (?, ?)', (str(chat_id), area))
    conn.commit()


def remover_chat(cursor, conn, chat_id):
    cursor.execute('DELETE FROM usuarios_areas WHERE chat_id = ?', (str(chat_id),))
    conn.commit()


def obter_todos_chats_inscritos(cursor):
    """Lista todos os chat_ids que têm ao menos uma área configurada."""
    cursor.execute('SELECT DISTINCT chat_id FROM usuarios_areas')
    return [row[0] for row in cursor.fetchall()]


def get_offset_updates(cursor):
    cursor.execute("SELECT valor FROM bot_estado WHERE chave = 'update_offset'")
    row = cursor.fetchone()
    return int(row[0]) if row else 0


def set_offset_updates(cursor, conn, offset):
    cursor.execute(
        "INSERT INTO bot_estado (chave, valor) VALUES ('update_offset', ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
        (str(offset),)
    )
    conn.commit()


def obter_ultima_busca(cursor):
    cursor.execute("SELECT valor FROM bot_estado WHERE chave = 'ultima_busca_em'")
    row = cursor.fetchone()
    return datetime.fromisoformat(row[0]) if row else None


def registrar_ultima_busca(cursor, conn):
    cursor.execute(
        "INSERT INTO bot_estado (chave, valor) VALUES ('ultima_busca_em', ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
        (datetime.now().isoformat(),)
    )
    conn.commit()


def busca_e_devida(cursor):
    ultima = obter_ultima_busca(cursor)
    if ultima is None:
        return True
    return (datetime.now() - ultima).total_seconds() >= INTERVALO_BUSCA_SEGUNDOS


def obter_ultima_limpeza(cursor):
    cursor.execute("SELECT valor FROM bot_estado WHERE chave = 'ultima_limpeza_em'")
    row = cursor.fetchone()
    return datetime.fromisoformat(row[0]) if row else None


def registrar_ultima_limpeza(cursor, conn):
    cursor.execute(
        "INSERT INTO bot_estado (chave, valor) VALUES ('ultima_limpeza_em', ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
        (datetime.now().isoformat(),)
    )
    conn.commit()


def limpeza_e_devida(cursor):
    ultima = obter_ultima_limpeza(cursor)
    if ultima is None:
        return True
    return (datetime.now() - ultima).days >= INTERVALO_LIMPEZA_DIAS


def limpar_vagas_antigas(cursor, conn):
    """Apaga de vagas_enviadas registros com mais de DIAS_RETENCAO_VAGAS_ENVIADAS dias
    (com base em quando o bot enviou, não na data de publicação da vaga na Gupy).
    Registros de antes desta versão, sem enviado_em preenchido, não são apagados."""
    limite = (datetime.now() - timedelta(days=DIAS_RETENCAO_VAGAS_ENVIADAS)).isoformat()
    cursor.execute(
        'DELETE FROM vagas_enviadas WHERE enviado_em IS NOT NULL AND enviado_em < ?',
        (limite,)
    )
    apagadas = cursor.rowcount
    conn.commit()
    if apagadas:
        print(f"🧹 Limpeza: {apagadas} vaga(s) com mais de {DIAS_RETENCAO_VAGAS_ENVIADAS} dias removida(s) de vagas_enviadas.")
    return apagadas


# --- 4. FUNÇÕES DE MENSAGEM DO TELEGRAM ---
def enviar_mensagem_telegram(chat_id, mensagem, silencioso_em_erro=True):
    """Envia uma mensagem simples para um chat_id específico"""
    if not TOKEN or not chat_id:
        return None
    try:
        url_tg = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload_tg = {
            "chat_id": chat_id,
            "text": mensagem,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        r = requests.post(url_tg, json=payload_tg, timeout=10)
        return r
    except Exception as e:
        if not silencioso_em_erro:
            print(f"❌ Erro ao enviar mensagem para {chat_id}: {e}")
        return None


def garantir_primeira_ativacao(cursor, conn):
    """Manda o aviso de 'robô ativado' só uma vez (na primeira execução com banco novo),
    não a cada tick do cron — evita spam a cada 5 minutos."""
    cursor.execute("SELECT valor FROM bot_estado WHERE chave = 'ativado_em'")
    if cursor.fetchone():
        return
    mensagem = "✅ <b>ROBÔ ATIVADO</b>\n\nO robô de vagas está funcionando e vai continuar enviando as vagas disponíveis."
    if CHAT_ID_PADRAO:
        enviar_mensagem_telegram(CHAT_ID_PADRAO, mensagem)
    cursor.execute(
        "INSERT INTO bot_estado (chave, valor) VALUES ('ativado_em', ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
        (datetime.now().isoformat(),)
    )
    conn.commit()

def enviar_mensagem_manutencao():
    mensagem = "⚠️ <b>MANUTENÇÃO</b>\n\nO robô de vagas está passando por manutenção no momento. Em breve retornaremos com as atualizações!"
    if CHAT_ID_PADRAO:
        enviar_mensagem_telegram(CHAT_ID_PADRAO, mensagem)


def signal_handler(signum, frame):
    global executando
    print("\n🛑 Recebido sinal de interrupção. Encerrando o bot...")
    executando = False
    enviar_mensagem_manutencao()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def configurar_comandos_bot():
    """Registra os comandos no Telegram para aparecerem como sugestão ao digitar '/'."""
    if not TOKEN:
        return
    comandos = [
        {"command": "areas", "description": "Lista as áreas disponíveis para filtro"},
        {"command": "definir", "description": "Define suas áreas de interesse (ex: /definir dados e ia, desenvolvimento)"},
        {"command": "minhasareas", "description": "Mostra suas áreas configuradas atualmente"},
        {"command": "parar", "description": "Cancela o recebimento de vagas"},
        {"command": "ajuda", "description": "Mostra os comandos disponíveis"},
    ]
    try:
        url_tg = f"https://api.telegram.org/bot{TOKEN}/setMyCommands"
        r = requests.post(url_tg, json={"commands": comandos}, timeout=10)
        if r.status_code == 200 and r.json().get("ok"):
            print("✅ Comandos registrados no Telegram (sugestão ao digitar '/').")
        else:
            print(f"⚠️ Falha ao registrar comandos: {r.text}")
    except Exception as e:
        print(f"⚠️ Erro ao registrar comandos: {e}")


# --- 5. COMANDOS DO BOT (polling via getUpdates) ---
TEXTO_AJUDA = (
    "🤖 <b>Comandos disponíveis</b>\n\n"
    "/areas — lista as áreas disponíveis para filtro\n"
    "/definir área1, área2 — define suas áreas de interesse (substitui as anteriores)\n"
    "/minhasareas — mostra suas áreas configuradas atualmente\n"
    "/parar — cancela o recebimento de vagas\n"
    "/ajuda — mostra esta mensagem\n\n"
    "Exemplo: <code>/definir dados e ia, desenvolvimento</code>"
)


def processar_comando(cursor, conn, chat_id, texto):
    texto = texto.strip()
    if not texto.startswith('/'):
        return

    partes = texto.split(maxsplit=1)
    comando = partes[0].lower().split('@')[0]  # remove @nomebot se houver
    argumento = partes[1] if len(partes) > 1 else ''

    if comando in ('/start', '/ajuda', '/help'):
        enviar_mensagem_telegram(chat_id, TEXTO_AJUDA)

    elif comando == '/areas':
        mensagem = "📋 <b>Áreas disponíveis:</b>\n\n" + "\n".join(f"• {a}" for a in sorted(AREAS.keys()))
        mensagem += "\n\nUse <code>/definir área1, área2</code> para escolher."
        enviar_mensagem_telegram(chat_id, mensagem)

    elif comando == '/definir':
        if not argumento:
            enviar_mensagem_telegram(chat_id, "⚠️ Envie as áreas separadas por vírgula. Exemplo:\n<code>/definir dados e ia, fiscal</code>")
            return

        areas_pedidas = [normalizar(a.strip()) for a in argumento.split(',') if a.strip()]
        areas_validas = []
        areas_invalidas = []
        for a in areas_pedidas:
            if a in AREAS:
                areas_validas.append(a)
            else:
                areas_invalidas.append(a)

        if not areas_validas:
            enviar_mensagem_telegram(
                chat_id,
                f"❌ Nenhuma área reconhecida em: {argumento}\n\nÁreas disponíveis:\n{areas_validas_str()}"
            )
            return

        definir_areas_do_chat(cursor, conn, chat_id, areas_validas)

        mensagem = f"✅ Áreas definidas: {', '.join(areas_validas)}"
        if areas_invalidas:
            mensagem += f"\n\n⚠️ Não reconhecidas (ignoradas): {', '.join(areas_invalidas)}"
        enviar_mensagem_telegram(chat_id, mensagem)

    elif comando == '/minhasareas':
        areas_atuais = obter_areas_do_chat(cursor, chat_id)
        if areas_atuais:
            enviar_mensagem_telegram(chat_id, "📌 Suas áreas atuais: " + ", ".join(areas_atuais))
        else:
            enviar_mensagem_telegram(chat_id, "Você ainda não definiu nenhuma área. Use /areas para ver as opções e /definir para escolher.")

    elif comando == '/parar':
        remover_chat(cursor, conn, chat_id)
        enviar_mensagem_telegram(chat_id, "🛑 Você não receberá mais vagas. Use /definir a qualquer momento para voltar a receber.")

    else:
        enviar_mensagem_telegram(chat_id, "Comando não reconhecido. Use /ajuda para ver os comandos disponíveis.")


def checar_novos_comandos(cursor, conn):
    """Faz polling do getUpdates do Telegram e processa comandos novos."""
    if not TOKEN:
        return

    offset = get_offset_updates(cursor)
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {"offset": offset + 1, "timeout": 0}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return

        dados = r.json()
        updates = dados.get('result', [])

        maior_update_id = offset
        for update in updates:
            maior_update_id = max(maior_update_id, update.get('update_id', offset))

            mensagem = update.get('message')
            if not mensagem:
                continue

            chat_id = mensagem.get('chat', {}).get('id')
            texto = mensagem.get('text', '')

            if chat_id and texto:
                try:
                    processar_comando(cursor, conn, chat_id, texto)
                except Exception as e:
                    print(f"⚠️ Erro ao processar comando de {chat_id}: {e}")

        if updates:
            set_offset_updates(cursor, conn, maior_update_id)

    except Exception as e:
        print(f"⚠️ Erro ao consultar getUpdates: {e}")


# --- 6. MOTOR DE BUSCA DA GUPY (MINAS GERAIS, FILTRADO PARA BH E REGIÃO) ---
def montar_mensagem_vaga(vaga_info, contexto_nome):
    titulo, empresa, local, modelo, tipo, pcd, data_f, hora_f, link_vaga = vaga_info
    titulo_mensagem = f"🎯 <b>VAGA GUPY - {contexto_nome}!</b>"
    return (
        f"{titulo_mensagem}\n\n"
        f"💼 <b>Vaga:</b> {titulo}\n"
        f"🏢 <b>Empresa:</b> {empresa}\n"
        f"📍 <b>Local:</b> {local}\n"
        f"💻 <b>Modelo:</b> {modelo}\n"
        f"📄 <b>Tipo:</b> {tipo}\n"
        f"♿ <b>PCD:</b> {pcd}\n"
        f"📅 <b>Data:</b> {data_f} às {hora_f}\n\n"
        f"🔗 <a href='{link_vaga}'>Clique aqui para se candidatar na plataforma</a>"
    )


def ja_enviada_para_chat(cursor, chat_id, link_vaga):
    cursor.execute('SELECT 1 FROM vagas_enviadas WHERE chat_id = ? AND link = ?', (str(chat_id), link_vaga))
    return cursor.fetchone() is not None


def marcar_enviada_para_chat(cursor, conn, chat_id, link_vaga, data_f, titulo):
    cursor.execute(
        'INSERT OR IGNORE INTO vagas_enviadas VALUES (?, ?, ?, ?, ?)',
        (str(chat_id), link_vaga, data_f, titulo, datetime.now().isoformat())
    )
    conn.commit()


def buscar_vagas_gupy(cursor, conn):
    print("🚀 Iniciando varredura detalhada na API da Gupy...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://portal.gupy.io'
    }
    url_api = "https://employability-portal.gupy.io/api/v1/jobs"
    params_base = {'state': 'Minas Gerais', 'limit': 10}

    vagas_velhas = 0
    LIMITE_VELHAS = 20
    PAGINA_MAXIMA = 35

    total_enviados = 0

    # Cache de destinatários: recalculado uma vez por ciclo de busca,
    # não a cada página, pra não bater no banco toda hora.
    chats_inscritos = obter_todos_chats_inscritos(cursor)

    for pagina in range(1, PAGINA_MAXIMA + 1):
        print(f"   ⏳ Lendo página {pagina} de {PAGINA_MAXIMA}...")
        offset = (pagina - 1) * 10
        params_atuais = params_base.copy()
        params_atuais['offset'] = offset

        try:
            resposta = requests.get(url_api, headers=headers, params=params_atuais, timeout=15)

            if resposta.status_code != 200:
                print(f"🛑 Erro de conexão. Código HTTP: {resposta.status_code}")
                break

            try:
                dados_json = resposta.json()
            except Exception:
                print("🛑 Fomos bloqueados! O servidor não enviou os dados JSON.")
                break

            lista_vagas = dados_json.get('data', [])
            if not lista_vagas:
                print("   🔚 Não há mais vagas disponíveis nesta busca.")
                break

            for vaga in lista_vagas:
                link_vaga = vaga.get('jobUrl', '')
                if not link_vaga:
                    continue

                cidade = vaga.get('city', '')
                estado = vaga.get('state', 'Minas Gerais')

                if not cidade_e_alvo(cidade):
                    continue

                titulo = vaga.get('name', 'Título Indisponível')
                descricao = vaga.get('description', '')
                empresa = vaga.get('careerPageName', 'Empresa não informada')
                local = f"{cidade} - {estado}"
                modelo = TRADUCAO_MODELO.get(vaga.get('workplaceType', ''), "Não informado")
                tipo = TRADUCAO_TIPO_VAGA.get(vaga.get('type', ''), "Outros")
                pcd = "Sim" if vaga.get('disabilities') else "Não informado"

                data_iso = vaga.get('publishedDate', '')
                try:
                    data_limpa = data_iso.split('.')[0]
                    data_utc = datetime.strptime(data_limpa, "%Y-%m-%dT%H:%M:%S")
                    data_brt = data_utc - timedelta(hours=3)
                    data_f = data_brt.strftime("%d/%m/%Y")
                    hora_f = data_brt.strftime("%H:%M")
                except Exception:
                    data_f, hora_f = "Sem data", "--:--"

                # "Vaga vista antes" é rastreado por chat_id padrão (firehose),
                # usado só para controlar quando parar de paginar.
                vista_pelo_padrao = CHAT_ID_PADRAO and ja_enviada_para_chat(cursor, CHAT_ID_PADRAO, link_vaga)
                if vista_pelo_padrao:
                    vagas_velhas += 1
                else:
                    vagas_velhas = 0

                vaga_info = (titulo, empresa, local, modelo, tipo, pcd, data_f, hora_f, link_vaga)
                areas_da_vaga = classificar_vaga(titulo, descricao)

                # 1) Chat padrão (grupo "firehose", recebe tudo de BH e região)
                if CHAT_ID_PADRAO and not vista_pelo_padrao:
                    mensagem = montar_mensagem_vaga(vaga_info, "BELO HORIZONTE E REGIÃO")
                    r = enviar_mensagem_telegram(CHAT_ID_PADRAO, mensagem)
                    if r is not None and r.status_code == 200:
                        marcar_enviada_para_chat(cursor, conn, CHAT_ID_PADRAO, link_vaga, data_f, titulo)
                        total_enviados += 1
                        print(f"✅ [padrão] Enviada ({cidade}): {titulo[:40]}...")
                    time.sleep(INTERVALO_ENTRE_ENVIOS_SEGUNDOS)

                # 2) Chats inscritos por área
                if areas_da_vaga:
                    for chat_id in chats_inscritos:
                        if str(chat_id) == str(CHAT_ID_PADRAO):
                            continue  # já tratado acima
                        areas_do_chat = obter_areas_do_chat(cursor, chat_id)
                        if not any(a in areas_do_chat for a in areas_da_vaga):
                            continue
                        if ja_enviada_para_chat(cursor, chat_id, link_vaga):
                            continue

                        nome_area = areas_da_vaga[0]
                        mensagem = montar_mensagem_vaga(vaga_info, nome_area.upper())
                        r = enviar_mensagem_telegram(chat_id, mensagem)
                        if r is not None and r.status_code == 200:
                            marcar_enviada_para_chat(cursor, conn, chat_id, link_vaga, data_f, titulo)
                            total_enviados += 1
                            print(f"✅ [{nome_area}] Enviada para {chat_id}: {titulo[:40]}...")
                        time.sleep(INTERVALO_ENTRE_ENVIOS_SEGUNDOS)

                if vagas_velhas >= LIMITE_VELHAS:
                    break

            if vagas_velhas >= LIMITE_VELHAS:
                print(f"   🛑 Muitas vagas antigas ({LIMITE_VELHAS}). Encerrando varredura deste ciclo.")
                break

        except Exception as e:
            print(f"⚠️ Erro de execução: {e}")
            break

    print(f"\n✅ Varredura finalizada! {total_enviados} envios feitos neste ciclo.")
    return total_enviados


# --- 7. LOOP PRINCIPAL ---
def main():
    global executando

    if not TOKEN:
        print("❌ ERRO: Token do Telegram não encontrado no arquivo .env!")
        return

    conn, cursor = iniciar_banco()

    print("🤖 Bot de vagas Gupy iniciado!")
    print("📌 Monitorando vagas para Belo Horizonte e região metropolitana")
    print(f"⏰ Busca de vagas a cada {INTERVALO_BUSCA_SEGUNDOS // 60} minutos")
    print(f"💬 Checagem de comandos a cada {INTERVALO_ENTRE_ENVIOS_SEGUNDOS} segundos")
    print("🔴 Para parar o bot, pressione Ctrl+C\n")

    garantir_primeira_ativacao(cursor, conn)
    configurar_comandos_bot()

    while executando:
        try:
            checar_novos_comandos(cursor, conn)

            if busca_e_devida(cursor):
                print(f"\n{'='*50}")
                print(f"🔄 BUSCA - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                print(f"{'='*50}")

                total = buscar_vagas_gupy(cursor, conn)
                if total == 0:
                    print("📭 Nenhuma vaga nova encontrada nesta busca.")

                registrar_ultima_busca(cursor, conn)

            if limpeza_e_devida(cursor):
                limpar_vagas_antigas(cursor, conn)
                registrar_ultima_limpeza(cursor, conn)

            time.sleep(INTERVALO_ENTRE_ENVIOS_SEGUNDOS)

        except Exception as e:
            print(f"❌ Erro crítico no loop principal: {e}")
            time.sleep(60)

    conn.close()


if __name__ == '__main__':
    main()
