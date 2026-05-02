# Configuração do Nexus no Windows

## 1. Instalar o Python (se ainda não tiver)

Baixe em: https://www.python.org/downloads/
Durante a instalação, marque:
  ✅ "Add Python to PATH"  ← obrigatório!

Verifique no terminal:
```
python --version
```

---

## 2. Instalar o Mosquitto (broker MQTT)

O Mosquitto é o servidor MQTT que roda no notebook.
Todos os NodeMCUs se conectam a ele.

1. Baixe em: https://mosquitto.org/download/
   Escolha o instalador Windows (.exe) mais recente.

2. Execute o instalador. Durante a instalação:
   - Marque "Install service"
   - Anote o caminho de instalação (geralmente `C:\Program Files\mosquitto`)

3. Após instalar, configure o Mosquitto para aceitar conexões locais.
   Abra o arquivo:
   `C:\Program Files\mosquitto\mosquitto.conf`

   Adicione as linhas abaixo no FINAL do arquivo:
   ```
   listener 1883
   allow_anonymous true
   ```
   Salve o arquivo.

4. Abra o Prompt de Comando como Administrador e rode:
   ```
   net stop mosquitto
   net start mosquitto
   ```
   Ou abra o "Gerenciador de Serviços" (services.msc),
   localize "Mosquitto Broker" e clique em Reiniciar.

5. Teste o broker:
   Abra dois Prompts de Comando separados.

   Terminal 1 (subscriber):
   ```
   "C:\Program Files\mosquitto\mosquitto_sub.exe" -t game/# -v
   ```

   Terminal 2 (publisher — simula um NodeMCU):
   ```
   "C:\Program Files\mosquitto\mosquitto_pub.exe" -t game/torre/hp -m "{\"hp\": 20}"
   ```

   Se o Terminal 1 exibir a mensagem, o broker está funcionando!

---

## 3. Configurar o IP fixo do notebook

Todos os NodeMCUs têm o IP `192.168.1.100` hardcoded como broker.
O notebook precisa ter esse IP na rede do jogo.

1. Conecte o notebook ao roteador TP-Link (SSID: GAME_NEXUS).
2. Abra: Painel de Controle → Central de Rede → Ethernet ou Wi-Fi → Propriedades.
3. Clique em "Protocolo TCP/IPv4" → Propriedades.
4. Marque "Usar o seguinte endereço IP:" e preencha:
   ```
   Endereço IP:     192.168.1.100
   Máscara:         255.255.255.0
   Gateway padrão:  192.168.1.1
   ```
5. Clique OK.

---

## 4. Instalar as dependências Python do Nexus

No terminal, dentro da pasta `game-nexus`:
```
python -m venv .venv       # somente na primeira execução para criar o ambiente virtual
.venv\Scripts\activate
pip install -r requirements.txt
```
Nas execuções seguintes:
`.venv\Scripts\activate`


---

## 5. Iniciar o painel

```
python main.py
```

A janela do painel abrirá. Quando todos os NodeMCUs
estiverem conectados e ligados, clique em:

**▶  INICIAR PARTIDA**

---

## Checklist antes de cada evento

- [ ] Notebook conectado ao TP-Link (SSID: GAME_NEXUS)
- [ ] IP fixo do notebook configurado como 192.168.1.100
- [ ] Serviço Mosquitto ativo (services.msc → Mosquitto Broker → Iniciado)
- [ ] NodeMCU Atacante ligado (Serial Monitor mostra "Aguardando START")
- [ ] NodeMCU Defensor ligado (Serial Monitor mostra "Aguardando START")
- [ ] NodeMCU Torre ligado (Serial Monitor mostra "Aguardando START")
- [ ] Painel Python aberto (`python main.py`)
- [ ] Clicar em INICIAR PARTIDA

## Estrutura de arquivos do projeto

```
game-nexus/
├── main.py           ← execute este para abrir o painel
├── painel.py         ← interface visual (Tkinter)
├── mqtt_nexus.py     ← comunicação MQTT com o broker
├── jogo_nexus.py     ← estado da partida e estatísticas
├── config.py         ← configurações (IPs, tópicos, limites)
├── requirements.txt  ← dependências (só paho-mqtt)
└── SETUP.md          ← este arquivo
```
