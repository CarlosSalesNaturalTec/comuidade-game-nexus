# =====================================================
# ARQUIVO DE CONFIGURAÇÃO — NEXUS
# Ajuste aqui sem precisar mexer no resto do código!
# =====================================================

# ── Broker MQTT ───────────────────────────────────────
# O Mosquitto roda no próprio notebook.
# "localhost" significa "eu mesmo" — sem precisar de IP.
BROKER_HOST = "localhost"
BROKER_PORT = 1883
CLIENT_ID   = "nexus_painel"

# ── Tópicos MQTT ─────────────────────────────────────
# O Nexus ASSINA tudo de uma vez com o curinga "#"
TOPICO_ASSINATURA  = "game/#"

# Tópicos individuais que o painel interpreta
TOPICO_HP_TORRE    = "game/torre/hp"
TOPICO_HP_DEFENSOR = "game/defensor/hp"
TOPICO_STAMINA     = "game/atacante/stamina"
TOPICO_PUNICAO     = "game/defensor/punicao"

# O Nexus PUBLICA neste tópico para iniciar a partida
TOPICO_COMANDO     = "game/nexus/comando"

# ── Valores máximos (para as barras de progresso) ────
HP_MAXIMO_TORRE    = 30   # deve coincidir com HP_MAXIMO da Torre
HP_MAXIMO_DEFENSOR = 5    # deve coincidir com HP_MAXIMO do Defensor
STAMINA_MAXIMA     = 100  # deve coincidir com STAMINA_MAXIMA do Atacante

# ── Visual do Painel ──────────────────────────────────
TITULO_JANELA      = "NEXUS — Central de Comando"
LARGURA_JANELA     = 800
ALTURA_JANELA      = 600
INTERVALO_GUI_MS   = 100  # atualiza a tela a cada 100ms (10 fps — leve)
