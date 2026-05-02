"""
MÓDULO DE PAINEL — Interface Visual do Nexus

Dashboard em Tkinter (nativo do Python — sem instalação extra).
Atualiza a cada 100ms lendo o estado de jogo.

Layout:
┌─────────────────────────────────────┐
│  NEXUS — Central de Comando         │
├──────────────┬──────────────────────┤
│  🏰 TORRE   │  ⚡ ATACANTE         │
│  barra verde │  barra azul          │
│              ├──────────────────────│
│              │  🛡️  DEFENSOR        │
│              │  barra roxa          │
├──────────────┴──────────────────────┤
│  Log de eventos (rolagem)           │
├─────────────────────────────────────┤
│  [  INICIAR PARTIDA  ]              │
└─────────────────────────────────────┘
"""

import tkinter as tk
from tkinter import font as tkfont
from config import (
    TITULO_JANELA, LARGURA_JANELA, ALTURA_JANELA,
    INTERVALO_GUI_MS,
    HP_MAXIMO_TORRE, HP_MAXIMO_DEFENSOR, STAMINA_MAXIMA,
)
from jogo_nexus import estado
import mqtt_nexus


# ── Paleta de cores ───────────────────────────────────
COR_FUNDO       = "#0d0f1a"   # azul-noite
COR_PAINEL      = "#151828"   # levemente mais claro
COR_TEXTO       = "#e8eaf0"
COR_SUBTEXTO    = "#7a8099"
COR_TORRE_OK    = "#22c55e"   # verde
COR_TORRE_MEIO  = "#eab308"   # amarelo
COR_TORRE_BAIXO = "#ef4444"   # vermelho
COR_ATACANTE    = "#3b82f6"   # azul
COR_SUPERAQUEC  = "#f97316"   # laranja
COR_DEFENSOR    = "#a855f7"   # roxo
COR_ESCUDO_Q    = "#6b7280"   # cinza (escudo quebrado)
COR_BOTAO       = "#16a34a"   # verde escuro
COR_BOTAO_HOVER = "#15803d"
COR_ALERTA      = "#f97316"
COR_LOG_FUNDO   = "#0a0c16"


class Painel:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(TITULO_JANELA)
        self.root.geometry(f"{LARGURA_JANELA}x{ALTURA_JANELA}")
        self.root.configure(bg=COR_FUNDO)
        self.root.resizable(False, False)

        self._construir_interface()
        self._atualizar()   # inicia o loop de atualização

    # ─────────────────────────────────────────────────
    # CONSTRUÇÃO DA INTERFACE
    # ─────────────────────────────────────────────────

    def _construir_interface(self):
        fonte_titulo   = tkfont.Font(family="Consolas", size=16, weight="bold")
        fonte_label    = tkfont.Font(family="Consolas", size=11, weight="bold")
        fonte_valor    = tkfont.Font(family="Consolas", size=22, weight="bold")
        fonte_pequena  = tkfont.Font(family="Consolas", size=9)
        fonte_botao    = tkfont.Font(family="Consolas", size=13, weight="bold")
        fonte_log      = tkfont.Font(family="Consolas", size=9)

        # ── Cabeçalho ─────────────────────────────────
        cabecalho = tk.Frame(self.root, bg=COR_FUNDO, pady=10)
        cabecalho.pack(fill="x")
        tk.Label(
            cabecalho, text="⚔  NEXUS — Central de Comando  ⚔",
            font=fonte_titulo, bg=COR_FUNDO, fg=COR_TEXTO
        ).pack()

        # ── Área de métricas (3 colunas) ──────────────
        metricas = tk.Frame(self.root, bg=COR_FUNDO)
        metricas.pack(fill="x", padx=20, pady=(0, 8))

        # Torre (coluna esquerda — mais larga)
        col_torre = tk.Frame(metricas, bg=COR_PAINEL, bd=0, relief="flat")
        col_torre.pack(side="left", fill="both", expand=True, padx=(0, 8))

        tk.Label(col_torre, text="🏰  TORRE", font=fonte_label,
                 bg=COR_PAINEL, fg=COR_TEXTO, pady=8).pack()

        self.canvas_torre = tk.Canvas(col_torre, height=28,
                                      bg=COR_PAINEL, highlightthickness=0)
        self.canvas_torre.pack(fill="x", padx=12, pady=(0, 4))

        self.lbl_hp_torre = tk.Label(
            col_torre, text=f"{HP_MAXIMO_TORRE} / {HP_MAXIMO_TORRE}",
            font=fonte_valor, bg=COR_PAINEL, fg=COR_TORRE_OK
        )
        self.lbl_hp_torre.pack(pady=(0, 10))

        # Atacante + Defensor (coluna direita, empilhados)
        col_direita = tk.Frame(metricas, bg=COR_FUNDO)
        col_direita.pack(side="left", fill="both", expand=True)

        # Atacante
        frame_atk = tk.Frame(col_direita, bg=COR_PAINEL)
        frame_atk.pack(fill="both", expand=True, pady=(0, 8))

        tk.Label(frame_atk, text="⚡  ATACANTE", font=fonte_label,
                 bg=COR_PAINEL, fg=COR_TEXTO, pady=8).pack()

        self.canvas_atk = tk.Canvas(frame_atk, height=20,
                                    bg=COR_PAINEL, highlightthickness=0)
        self.canvas_atk.pack(fill="x", padx=12, pady=(0, 4))

        self.lbl_stamina = tk.Label(
            frame_atk, text="100%", font=fonte_valor,
            bg=COR_PAINEL, fg=COR_ATACANTE
        )
        self.lbl_stamina.pack()

        self.lbl_status_atk = tk.Label(
            frame_atk, text="aguardando...", font=fonte_pequena,
            bg=COR_PAINEL, fg=COR_SUBTEXTO, pady=6
        )
        self.lbl_status_atk.pack()

        # Defensor
        frame_def = tk.Frame(col_direita, bg=COR_PAINEL)
        frame_def.pack(fill="both", expand=True)

        tk.Label(frame_def, text="🛡️   DEFENSOR", font=fonte_label,
                 bg=COR_PAINEL, fg=COR_TEXTO, pady=8).pack()

        self.canvas_def = tk.Canvas(frame_def, height=20,
                                    bg=COR_PAINEL, highlightthickness=0)
        self.canvas_def.pack(fill="x", padx=12, pady=(0, 4))

        self.lbl_hp_def = tk.Label(
            frame_def, text=f"{HP_MAXIMO_DEFENSOR} / {HP_MAXIMO_DEFENSOR}",
            font=fonte_valor, bg=COR_PAINEL, fg=COR_DEFENSOR
        )
        self.lbl_hp_def.pack()

        self.lbl_status_def = tk.Label(
            frame_def, text="aguardando...", font=fonte_pequena,
            bg=COR_PAINEL, fg=COR_SUBTEXTO, pady=6
        )
        self.lbl_status_def.pack()

        # ── Log de eventos ────────────────────────────
        frame_log = tk.Frame(self.root, bg=COR_LOG_FUNDO, pady=4)
        frame_log.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        tk.Label(frame_log, text="📋  LOG DE EVENTOS", font=fonte_pequena,
                 bg=COR_LOG_FUNDO, fg=COR_SUBTEXTO).pack(anchor="w", padx=8)

        self.txt_log = tk.Text(
            frame_log, height=7, font=fonte_log,
            bg=COR_LOG_FUNDO, fg=COR_TEXTO,
            relief="flat", state="disabled",
            wrap="word", padx=8, pady=4,
            insertbackground=COR_TEXTO
        )
        self.txt_log.pack(fill="both", expand=True, padx=4)

        # ── Botão START ───────────────────────────────
        frame_botao = tk.Frame(self.root, bg=COR_FUNDO, pady=10)
        frame_botao.pack(fill="x")

        self.btn_start = tk.Button(
            frame_botao,
            text="▶   INICIAR PARTIDA",
            font=fonte_botao,
            bg=COR_BOTAO, fg="white",
            activebackground=COR_BOTAO_HOVER,
            activeforeground="white",
            relief="flat", padx=30, pady=12,
            cursor="hand2",
            command=self._ao_clicar_start,
        )
        self.btn_start.pack()

        self._ultimo_log = []   # para detectar mudança e evitar redesenho desnecessário

    # ─────────────────────────────────────────────────
    # LOOP DE ATUALIZAÇÃO (chama a si mesmo a cada 100ms)
    # ─────────────────────────────────────────────────

    def _atualizar(self):
        dados = estado.snapshot()

        self._atualizar_torre(dados)
        self._atualizar_atacante(dados)
        self._atualizar_defensor(dados)
        self._atualizar_log(dados["eventos"])
        self._atualizar_botao(dados)

        if dados["game_over"]:
            self._mostrar_game_over(dados)

        self.root.after(INTERVALO_GUI_MS, self._atualizar)

    # ─────────────────────────────────────────────────
    # ATUALIZAÇÕES INDIVIDUAIS
    # ─────────────────────────────────────────────────

    def _atualizar_torre(self, dados):
        hp  = dados["hp_torre"]
        pct = hp / HP_MAXIMO_TORRE

        # Escolhe a cor conforme o HP
        if pct > 0.60:
            cor = COR_TORRE_OK
        elif pct > 0.30:
            cor = COR_TORRE_MEIO
        else:
            cor = COR_TORRE_BAIXO

        self._desenhar_barra(self.canvas_torre, pct, cor)
        self.lbl_hp_torre.config(
            text=f"{hp} / {HP_MAXIMO_TORRE}", fg=cor
        )

    def _atualizar_atacante(self, dados):
        stamina = dados["stamina_atacante"]
        status  = dados["status_atacante"]
        pct     = stamina / STAMINA_MAXIMA

        superaquecido = (status == "superaquecido")
        cor = COR_SUPERAQUEC if superaquecido else COR_ATACANTE

        self._desenhar_barra(self.canvas_atk, pct, cor)
        self.lbl_stamina.config(text=f"{stamina}%", fg=cor)

        texto_status = "🔥 SUPERAQUECIDA — recarregando..." if superaquecido else f"stamina: {stamina}%"
        self.lbl_status_atk.config(text=texto_status, fg=COR_ALERTA if superaquecido else COR_SUBTEXTO)

    def _atualizar_defensor(self, dados):
        hp      = dados["hp_defensor"]
        status  = dados["status_defensor"]
        pct     = hp / HP_MAXIMO_DEFENSOR

        quebrado = (status == "quebrado" or hp == 0)
        cor = COR_ESCUDO_Q if quebrado else COR_DEFENSOR

        self._desenhar_barra(self.canvas_def, pct, cor)
        self.lbl_hp_def.config(
            text=f"{hp} / {HP_MAXIMO_DEFENSOR}", fg=cor
        )

        texto_status = "⚠️  ESCUDO QUEBRADO — recuando!" if quebrado else f"escudos: {hp}"
        self.lbl_status_def.config(text=texto_status, fg=COR_ALERTA if quebrado else COR_SUBTEXTO)

    def _atualizar_log(self, eventos):
        if eventos == self._ultimo_log:
            return  # nada mudou — não redesenha

        self._ultimo_log = list(eventos)
        self.txt_log.config(state="normal")
        self.txt_log.delete("1.0", "end")
        for linha in eventos:
            self.txt_log.insert("end", linha + "\n")
        self.txt_log.see("end")   # rolagem automática para a última linha
        self.txt_log.config(state="disabled")

    def _atualizar_botao(self, dados):
        if dados["partida_ativa"]:
            self.btn_start.config(text="⚔  PARTIDA EM ANDAMENTO", state="disabled",
                                  bg="#374151", fg=COR_SUBTEXTO)
        else:
            self.btn_start.config(text="▶   INICIAR PARTIDA", state="normal",
                                  bg=COR_BOTAO, fg="white")

    # ─────────────────────────────────────────────────
    # UTILIDADES
    # ─────────────────────────────────────────────────

    def _desenhar_barra(self, canvas: tk.Canvas, pct: float, cor: str):
        """Desenha a barra de progresso no canvas."""
        canvas.update_idletasks()
        largura = canvas.winfo_width()
        altura  = canvas.winfo_height()
        if largura <= 1:
            return

        canvas.delete("all")
        # Fundo cinza escuro
        canvas.create_rectangle(0, 0, largura, altura, fill="#1e2235", outline="")
        # Barra colorida
        preenchimento = int(largura * max(0.0, min(1.0, pct)))
        if preenchimento > 0:
            canvas.create_rectangle(0, 0, preenchimento, altura, fill=cor, outline="")
        # Borda sutil
        canvas.create_rectangle(0, 0, largura - 1, altura - 1,
                                 outline="#2a3050", fill="")

    def _mostrar_game_over(self, dados):
        """Substitui o painel por uma tela de estatísticas finais."""
        # Evita múltiplas chamadas
        if hasattr(self, "_game_over_exibido"):
            return
        self._game_over_exibido = True

        janela = tk.Toplevel(self.root)
        janela.title("GAME OVER — Estatísticas")
        janela.geometry("480x360")
        janela.configure(bg=COR_FUNDO)
        janela.resizable(False, False)

        fonte_titulo = tkfont.Font(family="Consolas", size=18, weight="bold")
        fonte_stat   = tkfont.Font(family="Consolas", size=11)
        fonte_botao  = tkfont.Font(family="Consolas", size=12, weight="bold")

        tk.Label(janela, text="💥  TORRE DESTRUÍDA!",
                 font=fonte_titulo, bg=COR_FUNDO, fg=COR_TORRE_BAIXO,
                 pady=20).pack()

        stats = [
            ("⚡ Tiros do Atacante",        dados["tiros"]),
            ("🔥 Recargas da Arma",          dados["recargas"]),
            ("🛡️  Hits absorvidos pelo Escudo", dados["hits_defensor"]),
            ("💔 Quebras do Escudo",          dados["quebras"]),
            ("🚨 Penalidades (Dano Duplo)",   dados["penalidades"]),
        ]

        frame_stats = tk.Frame(janela, bg=COR_PAINEL, padx=20, pady=10)
        frame_stats.pack(fill="x", padx=20)

        for rotulo, valor in stats:
            linha = tk.Frame(frame_stats, bg=COR_PAINEL)
            linha.pack(fill="x", pady=3)
            tk.Label(linha, text=rotulo, font=fonte_stat,
                     bg=COR_PAINEL, fg=COR_TEXTO, anchor="w").pack(side="left")
            tk.Label(linha, text=str(valor), font=fonte_stat,
                     bg=COR_PAINEL, fg=COR_ALERTA, anchor="e").pack(side="right")

        def nova_partida():
            janela.destroy()
            del self._game_over_exibido
            mqtt_nexus.publicar_start()

        tk.Button(
            janela, text="▶  NOVA PARTIDA",
            font=fonte_botao, bg=COR_BOTAO, fg="white",
            relief="flat", padx=20, pady=10,
            cursor="hand2", command=nova_partida
        ).pack(pady=20)

    def _ao_clicar_start(self):
        mqtt_nexus.publicar_start()

    def ao_fechar(self):
        mqtt_nexus.parar()
        self.root.destroy()
