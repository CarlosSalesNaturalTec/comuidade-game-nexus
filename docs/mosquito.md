# Mosquitto MQTT Broker — Guia de Instalação e Configuração

**Projeto:** Comunidade GAME — Inclusão Digital  
**Plataforma:** Windows 10 / 11  
**Componente:** Nexus (Estação de Controle)

---

## O que é o Mosquitto?

O **Mosquitto** é um servidor (broker) MQTT gratuito e de código aberto, mantido pela Eclipse Foundation. No projeto GAME ele funciona como a **central de mensagens**: todos os NodeMCUs (Atacante, Defensor e Torre) publicam seus dados nele, e o painel Python do Nexus lê essas informações em tempo real.

```
NodeMCU Atacante  ─┐
NodeMCU Defensor  ─┼──► Mosquitto (notebook) ──► Painel Python
NodeMCU Torre     ─┘         porta 1883
```

O Mosquitto roda **localmente no notebook** como um serviço do Windows — sem precisar de internet, sem precisar de nuvem.

---

## 1. Download e Instalação

### 1.1 Baixar o instalador

Acesse: **https://mosquitto.org/download/**

Na seção **Windows**, baixe o arquivo `.exe` mais recente (ex.: `mosquitto-2.x.x-install-windows-x64.exe`).

> ⚠️ Escolha a versão **64-bit** se o seu Windows for 64-bit (o mais comum). Verifique em: *Configurações → Sistema → Sobre → Tipo de sistema*.

### 1.2 Executar o instalador

1. Clique com o botão direito no arquivo baixado e escolha **"Executar como administrador"**.
2. Siga o assistente de instalação clicando em **Next**.
3. Na tela de componentes, certifique-se de que **"Service"** está marcado:

   ```
   ✅ Mosquitto Service    ← instala como serviço do Windows
   ✅ Client tools         ← instala mosquitto_pub e mosquitto_sub (para testes)
   ```

4. O caminho de instalação padrão é:
   ```
   C:\Program Files\mosquitto\
   ```
   Mantenha esse caminho — os comandos neste guia assumem ele.

5. Clique em **Install** e aguarde. Clique em **Finish**.

### 1.3 Verificar a instalação

Abra o **Prompt de Comando** (não precisa ser administrador) e digite:

```cmd
sc query mosquitto
```

Se a instalação foi bem-sucedida, a resposta será algo como:

```
SERVICE_NAME: mosquitto
    STATE: 4 RUNNING
```

---

## 2. Configuração

Por padrão, o Mosquitto 2.x **recusa conexões de outros dispositivos** por segurança. É necessário editar o arquivo de configuração para permitir que os NodeMCUs se conectem.

### 2.1 Abrir o arquivo de configuração

O arquivo fica em:
```
C:\Program Files\mosquitto\mosquitto.conf
```

Para editá-lo é necessário permissão de administrador. Faça assim:

1. Pressione **Win + S** e pesquise por `Notepad` (Bloco de Notas).
2. Clique com o botão direito no resultado e escolha **"Executar como administrador"**.
3. Dentro do Bloco de Notas: **Arquivo → Abrir**.
4. Navegue até `C:\Program Files\mosquitto\` e abra `mosquitto.conf`.

### 2.2 Adicionar as configurações do projeto GAME

Role até o **final do arquivo** e adicione exatamente estas linhas:

```conf
# ─── Configurações do Projeto GAME ───────────────────
# Aceita conexões de qualquer dispositivo na rede local
listener 1883

# Permite conexão sem usuário e senha (rede isolada do evento)
allow_anonymous true
```

Salve o arquivo (**Ctrl + S**).

> 💡 **Por que essas linhas?**  
> `listener 1883` → abre a porta 1883 para conexões externas (por padrão só aceita `localhost`).  
> `allow_anonymous true` → permite que os NodeMCUs conectem sem precisar de senha.  
> Na rede isolada do evento (TP-Link sem internet) isso é seguro.

### 2.3 Reiniciar o serviço

Após salvar o arquivo, o Mosquitto precisa ser reiniciado para aplicar as mudanças.

**Opção A — Pelo Prompt de Comando (administrador):**

Abra o Prompt de Comando como administrador e execute:

```cmd
net stop mosquitto
net start mosquitto
```

Resposta esperada:
```
O serviço Mosquitto Broker está sendo interrompido.
O serviço Mosquitto Broker foi interrompido com êxito.
O serviço Mosquitto Broker está sendo iniciado.
O serviço Mosquitto Broker foi iniciado com êxito.
```

**Opção B — Pelo Gerenciador de Serviços:**

1. Pressione **Win + R**, digite `services.msc` e pressione **Enter**.
2. Role a lista até encontrar **"Mosquitto Broker"**.
3. Clique com o botão direito → **Reiniciar**.

---

## 3. Teste do Broker

Antes de ligar qualquer NodeMCU, valide que o broker está funcionando corretamente usando as ferramentas de linha de comando que vieram com o instalador.

Abra **dois** Prompts de Comando separados lado a lado.

### Terminal 1 — Subscriber (ouvinte)

Este terminal vai ficar escutando todas as mensagens do jogo:

```cmd
"C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -t "game/#" -v
```

O cursor ficará parado aguardando mensagens. Isso é normal.

### Terminal 2 — Publisher (simulando um NodeMCU)

Este terminal vai simular uma mensagem da Torre:

```cmd
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t "game/torre/hp" -m "{\"hp\": 24}"
```

**Resultado esperado no Terminal 1:**
```
game/torre/hp {"hp": 24}
```

Se a mensagem apareceu, o broker está funcionando corretamente.

### Simulação completa de início de partida

Execute cada linha no Terminal 2 em sequência para simular uma partida:

```cmd
:: Nexus envia START
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t "game/nexus/comando" -m "{\"cmd\": \"START\"}"

:: Atacante reporta tiro
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t "game/atacante/stamina" -m "{\"stamina\": 80, \"status\": \"ativo\"}"

:: Defensor absorve hit
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t "game/defensor/hp" -m "{\"hp\": 4, \"status\": \"ativo\"}"

:: Torre recebe dano
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t "game/torre/hp" -m "{\"hp\": 27}"

:: Defensor comete falta
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t "game/defensor/punicao" -m "{\"tipo\": \"DANO_DUPLO\"}"

:: Torre recebe dano duplo
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t "game/torre/hp" -m "{\"hp\": 21}"
```

Se o painel Python estiver aberto (`python main.py`), todas as barras de HP se atualizarão em tempo real enquanto você envia esses comandos.

---

## 4. Configurar Inicialização Automática

Por padrão o Mosquitto já inicia com o Windows após a instalação com a opção "Service". Para confirmar ou alterar esse comportamento:

1. Abra `services.msc`.
2. Localize **Mosquitto Broker**.
3. Clique com o botão direito → **Propriedades**.
4. Em **Tipo de inicialização**, selecione **Automático**.
5. Clique em **OK**.

Com isso, o Mosquitto estará rodando sempre que o notebook ligar — sem precisar iniciar manualmente antes de cada evento.

---

## 5. Diagnóstico de Problemas

### O serviço não inicia

Verifique o log de erros do Mosquitto:

```cmd
"C:\Program Files\mosquitto\mosquitto.exe" -c "C:\Program Files\mosquitto\mosquitto.conf" -v
```

Esse comando roda o Mosquitto em modo verboso diretamente no terminal — qualquer erro de configuração aparecerá na tela.

### NodeMCU não consegue conectar ao broker

Verifique os seguintes pontos em ordem:

| Ponto | Como verificar |
|---|---|
| Mosquitto rodando? | `sc query mosquitto` → STATE deve ser RUNNING |
| Notebook com IP correto? | `ipconfig` → deve aparecer `192.168.1.100` |
| NodeMCU na mesma rede? | Serial Monitor deve mostrar o IP recebido pelo DHCP |
| Firewall bloqueando porta 1883? | Veja a seção abaixo |
| `listener 1883` no .conf? | Abra `mosquitto.conf` e confirme as linhas adicionadas |

### Liberar a porta 1883 no Firewall do Windows

O Firewall do Windows pode bloquear conexões externas na porta 1883 mesmo com o Mosquitto configurado corretamente.

1. Pressione **Win + S** e pesquise **"Firewall do Windows Defender com Segurança Avançada"**.
2. No painel esquerdo, clique em **Regras de Entrada**.
3. No painel direito, clique em **Nova Regra...**.
4. Selecione **Porta** → **Avançar**.
5. Selecione **TCP**, porta específica: `1883` → **Avançar**.
6. Selecione **Permitir a conexão** → **Avançar**.
7. Marque apenas **Privado** (rede local) → **Avançar**.
8. Nome: `MQTT Mosquitto GAME` → **Concluir**.

Reinicie o serviço Mosquitto após criar a regra.

### Mensagens chegando duplicadas no painel

O Mosquitto está funcionando, mas o NodeMCU reconectou e re-assinou os tópicos várias vezes. Verifique no Serial Monitor do NodeMCU se há mensagens repetidas de `[MQTT] Assinando:`. Isso é inofensivo — o painel ignora duplicatas automaticamente.

---

## 6. Referência Rápida

### Comandos de controle do serviço (Prompt como administrador)

```cmd
net start mosquitto          :: inicia o broker
net stop mosquitto           :: para o broker
net stop mosquitto && net start mosquitto   :: reinicia
sc query mosquitto           :: verifica o status
```

### Arquivo de configuração

```
C:\Program Files\mosquitto\mosquitto.conf
```

Conteúdo mínimo necessário para o projeto GAME (adicionar ao final):

```conf
listener 1883
allow_anonymous true
```

### Ferramentas de teste

```cmd
:: Escutar todos os tópicos do jogo
mosquitto_sub -h localhost -t "game/#" -v

:: Publicar mensagem manualmente
mosquitto_pub -h localhost -t "game/torre/hp" -m "{\"hp\": 15}"
```

> 💡 Se `mosquitto_sub` e `mosquitto_pub` não forem reconhecidos sem o caminho completo, adicione `C:\Program Files\mosquitto\` à variável de ambiente `PATH` do Windows.

---

## 7. Estrutura de Tópicos do Projeto GAME

| Tópico | Publicado por | Payload exemplo |
|---|---|---|
| `game/atacante/stamina` | Atacante | `{"stamina": 80, "status": "ativo"}` |
| `game/defensor/hp` | Defensor | `{"hp": 3, "status": "ativo"}` |
| `game/defensor/punicao` | Defensor | `{"tipo": "DANO_DUPLO"}` |
| `game/torre/hp` | Torre | `{"hp": 24}` |
| `game/nexus/comando` | Nexus | `{"cmd": "START"}` |

O Nexus assina `game/#` — o curinga `#` captura todos os tópicos acima com uma única assinatura.