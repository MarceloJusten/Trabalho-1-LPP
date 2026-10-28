# Especificação — Olaria em Tempo Real

**Integrantes:** Marcelo Henrique Justen (@MarceloJusten-github) e Julio Max
**Tipo de vila (sorteio):** 11 — Olaria (argila → telhas; a telha trinca se ficar muito tempo no forno)

> Este documento foi escrito ANTES do código. Descreve o comportamento na linguagem da olaria e não cita tecnologia.

## 1. Regras da vila

- **Recurso primário:** argila. **Recurso refinado:** telhas. A olaria começa com 150 argilas e 0 telhas.
- **Papéis:** o **Mestre** abre e encerra a temporada e não constrói nem queima. O **Jogador** constrói fornos, queima e retira telhas.
- **Produção automática:** com a temporada aberta, a cada **5 segundos** o barreiro rende **10 argilas** (todos são avisados).
- **Oleiros (trabalhadores):** a olaria tem **3 oleiros**. Cada obra e cada fornada ocupa **1 oleiro**; ele só fica livre quando a obra termina, a fornada é retirada ou as telhas trincam.
- **Construir um forno:** custa **50 argilas**, ocupa 1 oleiro e leva **8 segundos**. A olaria comporta **no máximo 6 fornos** (um por lote do terreno).
- **Quando a obra termina:** o oleiro fica livre, o forno passa a existir (livre para uso) e a produção sobe **+5 argilas** por intervalo.
- **Queimar telhas (fornada):** precisa de **1 forno livre** e **1 oleiro livre** e custa **20 argilas**. A queima leva **6 segundos**.
- **Fornada pronta:** quando a queima termina, as telhas estão boas, mas **só por 6 segundos**. Nesse tempo qualquer Jogador pode **retirar a fornada**: entram **10 telhas** no estoque, o forno e o oleiro ficam livres.
- **O que expira:** se ninguém retirar a fornada dentro dos 6 segundos, **as telhas trincam**: as 10 telhas se perdem, o forno e o oleiro ficam livres e a fornada é contada como perdida.
- **Retirada:** com várias fornadas prontas, o pedido de retirada atende a que vai trincar primeiro. Cada fornada só pode ser retirada uma vez.
- **Recusas** (só quem pediu é avisado, nada muda): temporada não aberta; Mestre tentando construir/queimar/retirar; Jogador tentando abrir ou encerrar; argila insuficiente; sem oleiro livre; todos os lotes já têm forno; nenhum forno construído; todos os fornos em uso; nenhuma fornada pronta para retirar.
- **Encerrar:** o Mestre encerra a temporada. A produção e os temporizadores param e todo novo pedido de ação é recusado. O resultado mostra as telhas produzidas e quem mais retirou.

## 2. Eventos

Padrão de nomes: `objeto.acao_no_passado` para o que se confirma e `objeto.acao_solicitada` para o que se pede.

| Evento | Emite | Recebe | O que muda no estado |
|---|---|---|---|
| `estado.sincronizado` | Servidor | Só quem acabou de entrar | Nada muda; quem chegou recebe a olaria como está |
| `vila.abertura_solicitada` | Mestre | Servidor | (é um pedido; nada muda) |
| `vila.iniciada` | Servidor | Todos | A temporada passa a "aberta" e a produção de argila começa |
| `construcao.solicitada` | Jogador | Servidor | (é um pedido; nada muda) |
| `construcao.iniciada` | Servidor | Todos | −50 argilas, +1 oleiro ocupado, aparece um forno em obra |
| `construcao.concluida` | Servidor | Todos | −1 oleiro ocupado, o forno fica livre, produção +5 por intervalo |
| `recurso.produzido` | Servidor | Todos | +argila (produção atual) no estoque |
| `fornada.solicitada` | Jogador | Servidor | (é um pedido; nada muda) |
| `fornada.iniciada` | Servidor | Todos | −20 argilas, +1 oleiro ocupado, o forno livre passa a queimar |
| `fornada.pronta` | Servidor | Todos | O forno passa a "pronto" e começa a contagem de 6 s para trincar |
| `fornada.retirada_solicitada` | Jogador | Servidor | (é um pedido; nada muda) |
| `fornada.retirada` | Servidor | Todos | +10 telhas, −1 oleiro ocupado, o forno fica livre, o placar do Jogador sobe |
| `telha.trincada` | Servidor | Todos | As 10 telhas se perdem, −1 oleiro ocupado, o forno fica livre, +1 fornada perdida |
| `operacao.recusada` | Servidor | Só quem pediu | Nada muda; o motivo é informado |
| `vila.encerramento_solicitado` | Mestre | Servidor | (é um pedido; nada muda) |
| `vila.encerrada` | Servidor | Todos | A temporada passa a "encerrada"; novos pedidos são recusados |

**Quem causa cada fato** (aparece no painel como "causa"): `construcao.iniciada` ← `construcao.solicitada`; `construcao.concluida` ← `construcao.iniciada` (temporizador); `fornada.iniciada` ← `fornada.solicitada`; `fornada.pronta` ← `fornada.iniciada` (temporizador); `fornada.retirada` ← `fornada.retirada_solicitada`; `telha.trincada` ← `fornada.pronta` (temporizador); `recurso.produzido` ← temporizador.

## 3. Cenários de teste (Dado / Quando / Então, escritos com eventos)

### Recusa
Dado que o Mestre ainda não abriu a temporada, quando o Jogador A emite `construcao.solicitada`, então o servidor emite `operacao.recusada` (motivo: "A temporada não está aberta") apenas para o Jogador A; o Jogador B e o Mestre não recebem nada e as argilas continuam em 150.

### Passagem do tempo
Dado que a temporada está aberta e o Jogador A emitiu `construcao.solicitada` (argilas em 100, oleiros em 1/3), quando passam 5 segundos, então o servidor emite `recurso.produzido` (causa: temporizador) para todos e as argilas sobem; e quando passam 8 segundos desde o pedido, o servidor emite `construcao.concluida` (causa: `construcao.iniciada`) para todos, os oleiros voltam a 0/3 e a produção sobe de 10 para 15.

### Disputa entre dois jogadores
Dado que há uma fornada pronta no único forno, quando os jogadores A e B emitem `fornada.retirada_solicitada` ao mesmo tempo, então o servidor emite `fornada.retirada` para todos (apenas uma vez, as telhas sobem 10, nunca 20) e emite `operacao.recusada` ("Nenhuma fornada pronta para retirar") apenas para o jogador que perdeu.

### Expiração (o que expira na olaria)
Dado que o Jogador A emitiu `fornada.solicitada` e o forno queimou por 6 segundos (o servidor emitiu `fornada.pronta`), quando passam mais 6 segundos sem nenhum `fornada.retirada_solicitada`, então o servidor emite `telha.trincada` (causa: `fornada.pronta`) para todos, as telhas não aumentam, o oleiro e o forno ficam livres; e se alguém tivesse retirado a fornada antes disso, `telha.trincada` não seria emitido.

### Limite de oleiros
Dado que 2 dos 3 oleiros estão ocupados, quando os jogadores A e B emitem `construcao.solicitada` ao mesmo tempo, então o servidor emite `construcao.iniciada` para um deles (oleiros em 3/3) e `operacao.recusada` ("Sem oleiro livre") apenas para o outro.
