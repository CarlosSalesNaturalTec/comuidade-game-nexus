"""
NEXUS — Estação de Controle
Projeto: GAME — Comunidade de Inclusão Digital

Ponto de entrada do painel.
Execute com:  python main.py
"""

import tkinter as tk
import mqtt_nexus
from painel import Painel


def main():
    print("==============================================")
    print("   NEXUS — Estação de Controle     v1.0")
    print("   Comunidade Game")
    print("==============================================")
    print()

    # ── 1. Iniciar o cliente MQTT em background ───────
    mqtt_nexus.iniciar()

    # ── 2. Criar a janela principal ───────────────────
    root = tk.Tk()
    app  = Painel(root)

    # Garante que o MQTT é encerrado ao fechar a janela
    root.protocol("WM_DELETE_WINDOW", app.ao_fechar)

    # ── 3. Iniciar o loop visual (Tkinter toma o controle) ──
    root.mainloop()

    print("[NEXUS] Painel encerrado.")


if __name__ == "__main__":
    main()
