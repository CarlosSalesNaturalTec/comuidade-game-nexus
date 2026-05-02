"""
MÓDULO DE JOGO — Estado e Estatísticas do Nexus

Guarda tudo que acontece na partida em um único lugar.
O painel visual lê daqui para exibir as informações.
"""

import threading
from config import HP_MAXIMO_TORRE, HP_MAXIMO_DEFENSOR, STAMINA_MAXIMA


class EstadoJogo:
    """
    Representa o estado completo de uma partida.
    Thread-safe: usa Lock para que o MQTT (thread separada)
    e o painel visual (thread principal) não colidam ao
    ler e escrever os dados ao mesmo tempo.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.reiniciar()

    def reiniciar(self):
        """Reseta todos os dados para o início de uma nova partida."""
        with self._lock:
            # ── Valores de jogo em tempo real ────────────
            self.hp_torre         = HP_MAXIMO_TORRE
            self.hp_defensor      = HP_MAXIMO_DEFENSOR
            self.stamina_atacante = STAMINA_MAXIMA
            self.status_atacante  = "aguardando"   # "ativo" | "superaquecido"
            self.status_defensor  = "aguardando"   # "ativo" | "quebrado"

            # ── Estado geral da partida ───────────────────
            self.partida_ativa    = False
            self.game_over        = False

            # ── Estatísticas para o relatório final ───────
            self.tiros_atacante      = 0   # total de tiros disparados
            self.recargas_atacante   = 0   # quantas vezes a arma superaqueceu
            self.hits_defensor       = 0   # tiros absorvidos pelo escudo
            self.quebras_defensor    = 0   # quantas vezes o escudo zerou
            self.penalidades         = 0   # faltas técnicas do defensor
            self.danos_duplos        = 0   # danos duplos aplicados à Torre

            # ── Log de eventos para a área de mensagens ──
            self.eventos = []              # lista de strings (últimas mensagens)

    # ─────────────────────────────────────────────────
    # ATUALIZAÇÕES — chamadas pelo módulo MQTT
    # ─────────────────────────────────────────────────

    def atualizar_torre(self, hp: int):
        with self._lock:
            hp_anterior = self.hp_torre
            self.hp_torre = hp

            if hp < hp_anterior and self.partida_ativa:
                self._log(f"🏰 Torre: {hp}/{HP_MAXIMO_TORRE} HP")

            if hp <= 0 and self.partida_ativa:
                self.game_over     = True
                self.partida_ativa = False
                self._log("💥 TORRE DESTRUÍDA! FIM DE JOGO!")

    def atualizar_defensor(self, hp: int, status: str):
        with self._lock:
            hp_anterior = self.hp_defensor
            self.hp_defensor  = hp
            self.status_defensor = status

            if hp < hp_anterior and self.partida_ativa:
                self.hits_defensor += 1
                self._log(f"🛡️  Escudo absorveu tiro! HP: {hp}/{HP_MAXIMO_DEFENSOR}")

            if hp == 0 and status == "quebrado" and self.partida_ativa:
                self.quebras_defensor += 1
                self._log(f"⚠️  Escudo QUEBRADO! ({self.quebras_defensor}ª quebra)")

            if hp == HP_MAXIMO_DEFENSOR and hp_anterior == 0:
                self._log("✅ Escudo recarregado! Defensor de volta ao combate.")

    def atualizar_atacante(self, stamina: int, status: str):
        with self._lock:
            stamina_anterior = self.stamina_atacante
            self.stamina_atacante = stamina
            self.status_atacante  = status

            if stamina < stamina_anterior and self.partida_ativa:
                self.tiros_atacante += 1
                self._log(f"⚡ Tiro! Stamina: {stamina}%")

            if status == "superaquecido" and self.partida_ativa:
                self.recargas_atacante += 1
                self._log(f"🔥 Arma SUPERAQUECIDA! ({self.recargas_atacante}ª recarga)")

            if status == "ativo" and stamina_anterior == 0:
                self._log("🔋 Arma recarregada! Atacante pronto.")

    def registrar_punicao(self):
        with self._lock:
            self.penalidades  += 1
            self.danos_duplos += 1
            self._log(f"🚨 DANO DUPLO aplicado! ({self.penalidades}ª penalidade)")

    def iniciar_partida(self):
        with self._lock:
            self.partida_ativa = True
            self.game_over     = False
            self._log("🎮 PARTIDA INICIADA! Boa sorte a todos!")

    # ─────────────────────────────────────────────────
    # LEITURA — chamadas pelo painel visual
    # ─────────────────────────────────────────────────

    def snapshot(self) -> dict:
        """Retorna uma cópia segura do estado atual para o painel."""
        with self._lock:
            return {
                "hp_torre":         self.hp_torre,
                "hp_defensor":      self.hp_defensor,
                "stamina_atacante": self.stamina_atacante,
                "status_atacante":  self.status_atacante,
                "status_defensor":  self.status_defensor,
                "partida_ativa":    self.partida_ativa,
                "game_over":        self.game_over,
                "tiros":            self.tiros_atacante,
                "recargas":         self.recargas_atacante,
                "hits_defensor":    self.hits_defensor,
                "quebras":          self.quebras_defensor,
                "penalidades":      self.penalidades,
                "eventos":          list(self.eventos[-8:]),  # últimas 8 mensagens
            }

    # ─────────────────────────────────────────────────
    # UTILITÁRIO INTERNO
    # ─────────────────────────────────────────────────

    def _log(self, mensagem: str):
        """Adiciona mensagem ao log — sem lock (já chamado dentro de lock)."""
        print(f"[NEXUS] {mensagem}")
        self.eventos.append(mensagem)
        if len(self.eventos) > 50:
            self.eventos.pop(0)


# ── Instância global — compartilhada entre MQTT e painel ──
estado = EstadoJogo()
