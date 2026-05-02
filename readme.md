# 📖 Comunidade GAME: Enredo e Regras Oficiais

## 🌌 O Ecossistema (Os 4 Elementos do Jogo)

### 1. O Atacante (Guerreiro / Classe: Dano)
*   **Arma:** Artefato com emissor Laser.
*   **Mecânica de Energia (Stamina):** O atacante não pode atirar infinitamente. Ele tem uma energia (munição) de 100%. Cada tiro gasta um pouco. Quando chega a 0%, a arma "trava" (Superaquecimento) e precisa de alguns segundos para recarregar (reinicializar).
*   **Comunicação:** O NodeMCU do artefato publica via **Wi-Fi/MQTT** o nível de stamina a cada tiro e a cada "Recarregamento" — apenas telemetria para a Estação de Controle.

### 2. O Defensor (Paladino / Classe: Tanque)
*   **Arma:** Um "Escudo de Luz" com um NodeMCU, **02 Sensores (LDRs)** e uma Fita de **05 LEDs**.
*   **Mecânica de Defesa:** O Defensor deve se jogar na frente dos lasers do atacante para proteger a torre. Cada vez que o laser bate no sensor do escudo, o defensor perde um dos 5 LEDs (energia cai). A lógica de hit detection roda **localmente** no próprio NodeMCU do Escudo, sem depender da rede.
*   **Exaustão (Quebra do Escudo):** Se o escudo zerar a energia (0 LEDs acesos), o escudo "quebra". O Defensor deve dar espaço para o Atacante ter visão da Torre até a energia do escudo reiniciar.
*   **Comunicação:** O NodeMCU publica via **Wi-Fi/MQTT** seu status de HP e avisa quando o escudo recarrega. Em caso de Penalidade, publica um evento especial que a Torre escuta diretamente pelo broker.

### 3. A Torre (A Grande Base)
*   **Hardware:** NodeMCU + Fita de **30 LEDs** disposta de forma circular + **02 Sensores LDRs** + DFPlayer Mini (Caixa de Som).
*   **Mecânica do Alvo:** É o coração da equipe. Inicia com 100% de Vida. Se um tiro passar pelo escudo do defensor e acertar a torre, ela toma *Dano Simples* — detectado diretamente pelo LDR, sem validação pela rede. A lógica de dano roda **local** e o resultado é publicado via MQTT.
*   **Comunicação:** Publica sua porcentagem de vida via **Wi-Fi/MQTT**. Também assina o tópico de penalidade do Defensor para aplicar Dano Duplo quando necessário.

### 4. O Nexus (Estação de Controle / O Mestre)
*   **Hardware:** Notebook operado pelo Controlador (Central de Dados). Conectado à mesma rede Wi-Fi dos NodeMCUs.
*   **Broker MQTT:** Roda o **Mosquitto** localmente no notebook. Todos os NodeMCUs publicam e assinam tópicos nesse broker — sem depender de internet.
*   **Roteador:** Um **TP-Link dedicado ao jogo** (rede isolada, sem internet necessária) garante estabilidade total independente do ambiente do evento.
*   **Painel (Dashboard):** Aplicação Python assina `game/#` e exibe a energia do Ataque, a resistência do Defensor e o HP da Torre em tempo real com animações.
*   **Estatísticas (Analytics):** Contabiliza o MVP, tiros acertados, quebras de escudo e penalidades ao fim de cada partida.

---

## 📡 Arquitetura de Comunicação Wi-Fi

> **Decisão de Projeto:** O laser atingindo o sensor LDR é sempre o gatilho real do jogo. A rede Wi-Fi serve **exclusivamente como telemetria** — informar a central os níveis de energia de cada componente.

```
[Atacante NodeMCU]  ─────────────────────────────┐
[Defensor NodeMCU]  ──── Wi-Fi / MQTT ────────────┼──► [TP-Link Dedicado] ──► [Notebook/Nexus]
[Torre NodeMCU]     ─────────────────────────────┘      Broker: Mosquitto
                                                         (rodando no notebook)
```

### Tópicos MQTT por Componente

| Componente | Tópico | Payload Exemplo |
|---|---|---|
| Atacante | `game/atacante/stamina` | `{"stamina": 75, "status": "ativo"}` |
| Defensor | `game/defensor/hp` | `{"hp": 3, "status": "ativo"}` |
| Defensor | `game/defensor/punicao` | `{"tipo": "DANO_DUPLO"}` |
| Torre | `game/torre/hp` | `{"hp": 60}` |
| Nexus | `game/nexus/comando` | `{"cmd": "START"}` |

### Fluxo da Penalidade de Dano Duplo (via MQTT)

```
Escudo com HP=0 detecta hit no LDR (lógica local)
    └─► publica: game/defensor/punicao → {"tipo": "DANO_DUPLO"}
            └─► Torre (assinante do tópico) aplica dano × 2 localmente
                    └─► publica: game/torre/hp → {"hp": 40}
                            └─► Nexus exibe alarme visual + aciona DFPlayer com som de explosão
```

O delay de ~20ms nesse fluxo é imperceptível e não afeta a experiência de jogo.

### Configuração do Roteador TP-Link (modo isolado)

*   **SSID:** `GAME_NEXUS` (sem senha ou senha interna)
*   **DHCP:** Ativo na faixa `192.168.1.x`
*   **Internet:** Não necessária — rede completamente isolada
*   **Broker Mosquitto:** `192.168.1.100` (IP fixo do notebook)

---

## 📜 Regras do Campo de Batalha

**Regra 1: Gestão de Energia (Recarga Constante)**
O poder no jogo é fluído. Tanto o atacante quanto o defensor não "morrem". Suas baterias se esgotam e se renovam automaticamente com o passar de alguns segundos. Cabe às equipes entrarem em sintonia: *O Atacante deve atirar quando o Escudo do Defensor cair, mas precisa garantir que não vai gastar sua munição atirando nas paredes.*

**Regra 2: A Hitbox Perfeita**
Os tiros só são validados se o Laser incidir precisamente nos sensores de luz (LDR). O sensor detecta o hit localmente, sem validação pela rede. Valem tiros diretos.

**Regra 3: A Penalidade Severa (Falta Técnica)**
O Defensor cujo escudo teve a energia esgotada está "Imobilizado" virtualmente. Ele não pode proteger a torre até os 5 LEDs reacenderem.
*   **A Punição:** Se o Atacante conseguir acertar o LDR do Escudo Descarregado porque o defensor insistiu em continuar bloqueando a torre (fazendo uma parede humana de forma indevida), **O ESCUDO PUBLICA UM EVENTO DE PENALIDADE NO MQTT**. A Torre assina esse tópico e **aplica Dano Duplo imediatamente!**
*   **A Lição Prática:** As crianças aprendem sobre posicionamento estratégico, ética no esporte e limites de sistema *(Se sobrecarregar um sistema já sem energia, ele explode algo maior!)*.

**Regra 4: Vitória**
O jogo não termina por tempo. Ele é intenso até o fim. O jogo termina apenas quando a energia vital da Torre da equipe adversária chegar exatamente a 0%.

---

## 🎭 A Linha do Tempo da Partida

### **1. O Pre-Game (Calibração)**
O Controlador (no Notebook) acessa o painel digital. Ele aciona um botão "Start" na tela. O Nexus publica `{"cmd": "START"}` no tópico `game/nexus/comando`.
As 30 luzes da Torre acendem (brancas e depois verdes). O DFPlayer anuncia com uma voz épica: *"Batalha Iniciada! Protejam a Base."* Os Escudos acendem os 5 LEDs em azul.

### **2. O Mid-Game (Fogo Cruzado)**
O Atacante avança disparando contra a Torre.
O Defensor se coloca na frente (fisicamente). O laser bate no LDR do escudo! O NodeMCU do escudo processa o hit localmente, apaga um LED e publica `{"hp": 4}` no MQTT. O notebook registra: *"Impacto absorvido!"*.
O Atacante dispara 5 vezes seguidas rápido demais! Sua arma "engasga" e a luz da arma pisca vermelho. O NodeMCU publica `{"stamina": 0, "status": "superaquecido"}`. O notebook marca: *"Atacante 1 precisou reinicializar energia"*.

### **3. O Evento de Punição (Erro Crítico)**
O Escudo do Defensor apaga todos os LEDs (HP = 0). O NodeMCU publica `{"hp": 0, "status": "quebrado"}`. O controlador avisa: *"Escudo Quebrado! Sai da frente!"*.
O Defensor não recua por desespero de perder. O laser acerta o LDR do escudo descarregado. O NodeMCU detecta localmente e publica: `game/defensor/punicao → {"tipo": "DANO_DUPLO"}`.
O notebook apita um alarme crítico, os 30 LEDs da torre piscam de vermelho bruscamente, o DFPlayer toca uma explosão forte: **DANO DUPLO APLICADO!**

### **4. Game Over e Telemetria**
A torre esgota as 30 luzes e publica `{"hp": 0}`. O Nexus detecta a condição de fim de jogo, pausa todo o sistema e exibe no telão:
> *"Torre destruída! Atacante deu 18 tiros (precisou de 3 reinicializações de energia). O Defensor defendeu 6 tiros corretamente (Teve 4 quebras de escudo) e cometeu 1 Penalidade que custou o jogo."*

---

## 🛠️ Visão do "Mestre" (A Lógica da Programação)

### Princípio Central
> **Toda lógica de jogo roda localmente em cada NodeMCU. A rede Wi-Fi é exclusivamente telemetria.**

### Lógica do Defensor (Escudo) — Pseudo-código

```cpp
void loop() {
  int leitura = analogRead(LDR);

  if (leitura < LIMIAR_HIT) {         // laser detectado localmente
    if (hpEscudo > 0) {
      hpEscudo--;
      atualizarLEDs();
      mqtt.publish("game/defensor/hp", hpEscudo);

    } else {                           // escudo já zerado → penalidade
      mqtt.publish("game/defensor/punicao", "DANO_DUPLO");
    }
  }

  if (hpEscudo == 0) {
    delay(TEMPO_RECARGA);              // recarga local, sem rede
    hpEscudo = 5;
    atualizarLEDs();
    mqtt.publish("game/defensor/hp", 5);
  }
}
```

### Lógica da Torre — Pseudo-código

```cpp
// Assinante do tópico de penalidade
void onMqttMessage(topic, payload) {
  if (topic == "game/defensor/punicao" && payload == "DANO_DUPLO") {
    vidaTorre -= (danoLaser * 2);
  }
  if (topic == "game/nexus/comando" && payload == "START") {
    iniciarPartida();
  }
  mqtt.publish("game/torre/hp", vidaTorre);
}

// Hit local pelo LDR (independente da rede)
void loop() {
  int leitura = analogRead(LDR);
  if (leitura < LIMIAR_HIT) {
    vidaTorre -= danoLaser;
    atualizarLEDs();
    tocarSomImpacto();
    mqtt.publish("game/torre/hp", vidaTorre);
  }
}
```

### Dashboard (Python — Nexus)

```python
import paho.mqtt.client as mqtt
import json

def on_message(client, userdata, msg):
    dados = json.loads(msg.payload)
    topic = msg.topic

    if topic == "game/torre/hp":
        atualizar_barra_hp_torre(dados["hp"])
    elif topic == "game/defensor/hp":
        atualizar_barra_hp_defensor(dados["hp"])
    elif topic == "game/atacante/stamina":
        atualizar_barra_stamina(dados["stamina"])
    elif topic == "game/defensor/punicao":
        disparar_alarme_visual_e_sonoro()

client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883)   # Mosquitto rodando no notebook
client.subscribe("game/#")          # assina todos os tópicos do jogo
client.loop_forever()
```

---

## 📦 Resumo de Hardware do Projeto

| Componente | Hardware | Qtd |
|---|---|---|
| Atacante | NodeMCU ESP8266 + módulo Laser | 1 |
| Defensor | NodeMCU ESP8266 + 2x LDR + Fita 5 LEDs | 1 |
| Torre | NodeMCU ESP8266 + 2x LDR + Fita 30 LEDs + DFPlayer Mini | 1 |
| Nexus | Notebook (Python + Mosquitto MQTT) | 1 |
| Roteador | TP-Link TD-VG5611 (rede isolada, sem internet) | 1 |
