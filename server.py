"""
Vila em Tempo Real - OLARIA
Programação Orientada a Eventos (LPP 2026/2)

O SERVIDOR É A FONTE DA VERDADE:
  * o cliente só PEDE (eventos "..._solicitada" / "..._solicitado");
  * o servidor decide, muda o estado e EMITE os FATOS (eventos no passado);
  * a RECUSA também é um evento (operacao.recusada), enviado só a quem pediu;
  * temporizadores do servidor (produção, obra, queima) também emitem eventos.

Regra de ouro das disputas: cada tratador valida e altera o estado SEM `await`
no meio. Assim, dois pedidos simultâneos são decididos um de cada vez.

Como executar:  uvicorn server:app --reload     (http://localhost:8000)
"""
import copy
import time

import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = socketio.ASGIApp(sio, static_files={
    "/": "client/index.html",
    "/assets": "client/assets",      # mapa, peças e sprites da vila
})

# ============================== REGRAS DA OLARIA ==============================
CUSTO_FORNO = 50          # argila gasta para construir um forno
TEMPO_OBRA = 8            # segundos até o forno ficar pronto
LIMITE_OLEIROS = 3        # máximo de oleiros ocupados ao mesmo tempo
MAX_FORNOS = 6            # lotes do mapa (lote1..lote6)
INTERVALO = 5             # segundos entre as produções de argila
PRODUCAO_INICIAL = 10     # argila produzida a cada intervalo
GANHO_POR_FORNO = 5       # cada forno concluído aumenta a produção
CUSTO_FORNADA = 20        # argila gasta para encher o forno de telhas
TEMPO_QUEIMA = 6          # segundos queimando
JANELA = 6                # segundos para retirar a fornada antes de trincar
TELHAS_POR_FORNADA = 10   # telhas que saem de uma fornada boa

estado = {
    "fase": "aguardando",            # aguardando -> aberta -> encerrada
    "argila": 150,                   # recurso primário
    "telhas": 0,                     # recurso refinado
    "trabalhadores": 0,              # oleiros ocupados agora
    "limite": LIMITE_OLEIROS,
    "producao": PRODUCAO_INICIAL,    # argila por intervalo
    "intervalo": INTERVALO,
    "tempo_obra": TEMPO_OBRA,
    "custo": CUSTO_FORNO,
    "custo_fornada": CUSTO_FORNADA,
    "tempo_queima": TEMPO_QUEIMA,
    "janela": JANELA,
    "telhas_por_fornada": TELHAS_POR_FORNADA,
    "max_fornos": MAX_FORNOS,
    "concluidas": 0,                 # fornos construídos
    "em_obra": 0,                    # fornos em construção
    "trincadas": 0,                  # fornadas perdidas
    "fornos": [],                    # [{id, situacao, fornada}]  situacao: obra|livre|queimando|pronta
    "placar": {},                    # nome -> telhas retiradas
}
prazos = {}          # id do forno -> instante (monotonic) em que a fase atual termina
jogadores = {}       # sid -> {"nome": ..., "papel": ...}


# ================================ APOIO ======================================
def instantaneo():
    """Cópia do estado, com o tempo que falta em cada forno (para quem chega depois)."""
    foto = copy.deepcopy(estado)
    agora = time.monotonic()
    for f in foto["fornos"]:
        falta = prazos.get(f["id"], agora) - agora
        f["restante"] = round(max(0.0, falta), 2) if f["situacao"] != "livre" else 0
    return foto


def fato(causa, **extras):
    """Monta o payload de um FATO: o estado atual, a CAUSA (o evento ou o
    temporizador que gerou o fato) e dados extras."""
    return {"estado": instantaneo(), "causa": causa, **extras}


# ============================ CONEXÃO (Etapa 1) ===============================
@sio.event
async def connect(sid, environ, auth):
    auth = auth or {}
    jogadores[sid] = {
        "nome": auth.get("nome", "Anônimo"),
        "papel": auth.get("papel", "jogador"),
    }
    # servidor -> UM cliente: quem acabou de chegar precisa do estado atual
    await sio.emit("estado.sincronizado", fato("conexao"), to=sid)


@sio.event
async def disconnect(sid):
    jogadores.pop(sid, None)
