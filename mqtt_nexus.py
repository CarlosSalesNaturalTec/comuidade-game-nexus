"""
MÓDULO MQTT — Nexus (Central de Comando)

Assina todos os tópicos do jogo com "game/#" e
roteia cada mensagem para o módulo de estado.
Roda em thread separada para não travar o painel visual.
"""

import json
import paho.mqtt.client as mqtt
from config import (
    BROKER_HOST, BROKER_PORT, CLIENT_ID,
    TOPICO_ASSINATURA, TOPICO_COMANDO,
    TOPICO_HP_TORRE, TOPICO_HP_DEFENSOR,
    TOPICO_STAMINA, TOPICO_PUNICAO,
)
from jogo_nexus import estado

# ── Objeto do cliente MQTT ────────────────────────────
_cliente = mqtt.Client(client_id=CLIENT_ID)

# ─────────────────────────────────────────────────────
# CALLBACKS — chamados automaticamente pelo paho-mqtt
# ─────────────────────────────────────────────────────

def _ao_conectar(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Conectado ao broker em {BROKER_HOST}:{BROKER_PORT}")
        client.subscribe(TOPICO_ASSINATURA)   # assina game/# de uma vez
        print(f"[MQTT] Assinando: {TOPICO_ASSINATURA}")
    else:
        print(f"[MQTT] Falha na conexão — código: {rc}")


def _ao_desconectar(client, userdata, rc):
    if rc != 0:
        print("[MQTT] Desconectado inesperadamente. Reconectando...")


def _ao_receber_mensagem(client, userdata, msg):
    """
    Roteador de mensagens: identifica o tópico e
    atualiza o estado de jogo correspondente.
    """
    topico = msg.topic

    try:
        dados = json.loads(msg.payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(f"[MQTT] Payload inválido em '{topico}': {msg.payload}")
        return

    # ── Torre: HP em tempo real ───────────────────────
    if topico == TOPICO_HP_TORRE:
        hp = dados.get("hp", 0)
        estado.atualizar_torre(hp)

    # ── Defensor: HP e status do escudo ──────────────
    elif topico == TOPICO_HP_DEFENSOR:
        hp     = dados.get("hp",     0)
        status = dados.get("status", "ativo")
        estado.atualizar_defensor(hp, status)

    # ── Atacante: stamina e status da arma ───────────
    elif topico == TOPICO_STAMINA:
        stamina = dados.get("stamina", 0)
        status  = dados.get("status",  "ativo")
        estado.atualizar_atacante(stamina, status)

    # ── Punição: Defensor cometeu falta ──────────────
    elif topico == TOPICO_PUNICAO:
        tipo = dados.get("tipo", "")
        if tipo == "DANO_DUPLO":
            estado.registrar_punicao()


# ─────────────────────────────────────────────────────
# FUNÇÕES PÚBLICAS
# ─────────────────────────────────────────────────────

def iniciar():
    """Conecta ao broker e inicia o loop MQTT em background."""
    _cliente.on_connect    = _ao_conectar
    _cliente.on_disconnect = _ao_desconectar
    _cliente.on_message    = _ao_receber_mensagem

    try:
        _cliente.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    except ConnectionRefusedError:
        print("[MQTT] ERRO: Broker recusou a conexão.")
        print("[MQTT] → Verifique se o Mosquitto está rodando (veja SETUP.md)")
        return

    # loop_start() cria uma thread daemon para processar mensagens
    # sem bloquear o painel visual (Tkinter roda na thread principal)
    _cliente.loop_start()
    print("[MQTT] Loop MQTT iniciado em background.")


def publicar_start():
    """Publica o comando START para todos os NodeMCUs."""
    payload = json.dumps({"cmd": "START"})

    # Publica 3 vezes com intervalo de 100ms
    # Garante que todos os dispositivos recebam mesmo com latência
    for _ in range(3):
        _cliente.publish(TOPICO_COMANDO, payload)

    estado.reiniciar()
    estado.iniciar_partida()
    print(f"[MQTT] START publicado 3x em '{TOPICO_COMANDO}'")


def parar():
    """Encerra o loop MQTT ao fechar o painel."""
    _cliente.loop_stop()
    _cliente.disconnect()
    print("[MQTT] Conexão encerrada.")
