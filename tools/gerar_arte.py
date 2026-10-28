"""
Gera a arte da OLARIA a partir do kit do professor.

- client/assets/sprites-olaria.png : forno (livre, queimando, pronto, trincado) + canteiro
- client/assets/tileset-vila.png   : troca 3 peças do cenário (argila, telhas secando, barreiro)

Uso (na raiz do projeto):  python tools/gerar_arte.py
Requer:  pip install pillow
A arte é original deste trabalho (desenhada por código, pixel a pixel).
"""
from pathlib import Path
from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent.parent / "client" / "assets"

# ---- paleta (combina com a arte do kit) ----
OUT = (74, 52, 24, 255)            # contorno marrom escuro do kit
SOMBRA = (40, 70, 40, 110)
TERRA = (196, 98, 56, 255)         # tijolo / telha
TERRA_L = (226, 138, 88, 255)
TERRA_D = (148, 70, 40, 255)
BOCA = (38, 24, 16, 255)
ARG = (170, 108, 70, 255)          # argila
ARG_L = (206, 146, 102, 255)
ARG_D = (122, 76, 48, 255)
LAMA = (150, 100, 70, 255)
FOGO1 = (255, 214, 74, 255)
FOGO2 = (255, 138, 34, 255)
FOGO3 = (222, 64, 24, 255)
FUMACA = (205, 205, 205, 210)
BRILHO = (255, 236, 150, 255)
BRANCO = (255, 255, 240, 255)


def sombra(d, caixa):
    d.ellipse(caixa, fill=SOMBRA)


def forno(situacao, quadro=0):
    """Desenha um forno 32x32. situacao: livre | queimando | pronta | trincada"""
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sombra(d, (3, 25, 29, 31))

    # corpo (cúpula + base reta) como máscara, para os tijolos ficarem dentro
    mascara = Image.new("L", (32, 32), 0)
    md = ImageDraw.Draw(mascara)
    md.ellipse((5, 7, 26, 28), fill=255)
    md.rectangle((5, 18, 26, 28), fill=255)

    corpo = Image.new("RGBA", (32, 32), TERRA)
    cd = ImageDraw.Draw(corpo)
    for i, y in enumerate((11, 15, 19, 23, 27)):          # fileiras de tijolos
        cd.line((4, y, 27, y), fill=TERRA_D)
        for x in range((i % 2) * 3 + 6, 28, 6):
            cd.line((x, y - 4, x, y), fill=TERRA_D)
    cd.line((7, 12, 9, 9), fill=TERRA_L)                  # brilho
    cd.line((6, 17, 6, 22), fill=TERRA_L)
    im.paste(corpo, (0, 0), mascara)

    # contorno
    d.arc((5, 7, 26, 28), 180, 360, fill=OUT)
    d.line((5, 18, 5, 28), fill=OUT)
    d.line((26, 18, 26, 28), fill=OUT)
    d.line((5, 28, 26, 28), fill=OUT)
    d.arc((5, 7, 26, 28), 180, 215, fill=OUT)

    # chaminé
    d.rectangle((13, 3, 18, 9), fill=TERRA_D, outline=OUT)
    d.rectangle((12, 2, 19, 3), fill=TERRA, outline=OUT)

    # boca do forno (arco)
    dentro = BOCA
    if situacao == "pronta":
        dentro = BRILHO
    d.rectangle((12, 20, 19, 28), fill=dentro)
    d.ellipse((12, 15, 19, 25), fill=dentro)
    d.arc((12, 15, 19, 25), 180, 360, fill=OUT)
    d.line((12, 20, 12, 28), fill=OUT)
    d.line((19, 20, 19, 28), fill=OUT)

    if situacao == "queimando":
        base = [(13, 28), (15, 21), (16, 24), (17, 19), (18, 28)] if quadro == 0 \
            else [(13, 28), (14, 19), (16, 23), (18, 21), (18, 28)]
        d.polygon(base, fill=FOGO3)
        d.polygon([(14, 28), (16, 22), (17, 28)], fill=FOGO2)
        d.polygon([(15, 28), (16, 25), (17, 28)], fill=FOGO1)
        # fumaça saindo da chaminé
        pos = [(15, 2), (17, 0)] if quadro == 0 else [(16, 3), (14, 1)]
        for (x, y) in pos:
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=FUMACA)
    elif situacao == "pronta":
        d.rectangle((14, 24, 17, 28), fill=BRANCO)
        d.line((12, 20, 19, 20), fill=FOGO1)
        # pilha de telhas em frente (prontas para retirar)
        d.rectangle((21, 21, 29, 28), fill=TERRA_L, outline=OUT)
        d.line((22, 24, 28, 24), fill=TERRA_D)
        d.line((22, 26, 28, 26), fill=TERRA_D)
        # brilhos (chamam a atenção)
        for (x, y) in ((3, 10), (28, 12), (9, 4)):
            d.point((x, y), fill=FOGO1)
            d.point((x - 1, y), fill=BRANCO); d.point((x + 1, y), fill=BRANCO)
            d.point((x, y - 1), fill=BRANCO); d.point((x, y + 1), fill=BRANCO)
    elif situacao == "trincada":
        # rachaduras no corpo e cacos no chão
        d.line([(10, 10), (12, 13), (10, 16), (13, 19)], fill=OUT)
        d.line([(22, 11), (20, 14), (23, 17)], fill=OUT)
        for (x, y) in ((22, 27), (25, 28), (6, 29)):
            d.polygon([(x, y), (x + 3, y - 1), (x + 4, y + 1), (x + 1, y + 2)], fill=TERRA, outline=OUT)
    return im


def sprites():
    kit = Image.open(ASSETS / "sprites-vila.png").convert("RGBA")
    canteiro = kit.crop((32, 0, 64, 32))                    # quadro 1 do kit
    quadros = [
        forno("livre"),            # 0
        canteiro,                  # 1 obra em andamento
        forno("queimando", 0),     # 2
        forno("queimando", 1),     # 3
        forno("pronta"),           # 4
        forno("trincada"),         # 5
    ]
    folha = Image.new("RGBA", (32 * len(quadros), 32), (0, 0, 0, 0))
    for i, q in enumerate(quadros):
        folha.paste(q, (32 * i, 0))
    folha.save(ASSETS / "sprites-olaria.png")


# ---------------------------- peças do cenário ----------------------------
def peca_argila():
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((1, 11, 14, 15), fill=SOMBRA)
    d.polygon([(2, 13), (3, 9), (6, 5), (9, 4), (12, 7), (14, 13)], fill=ARG, outline=OUT)
    d.polygon([(7, 6), (9, 5), (11, 8), (9, 9)], fill=ARG_L)
    d.polygon([(10, 9), (13, 12), (11, 13), (9, 12)], fill=ARG_D)
    d.line((4, 11, 6, 9), fill=ARG_L)
    return im


def peca_telhas():
    """Telhas secando em uma prateleira (secador)."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 13, 15, 16), fill=SOMBRA)
    d.rectangle((1, 3, 2, 14), fill=(122, 79, 42, 255), outline=OUT)      # postes
    d.rectangle((13, 3, 14, 14), fill=(122, 79, 42, 255), outline=OUT)
    for y in (4, 8, 12):
        d.rectangle((2, y, 13, y + 2), fill=TERRA_L, outline=OUT)
        for x in (5, 8, 11):
            d.line((x, y, x, y + 2), fill=TERRA_D)
    return im


def peca_barreiro():
    """Poço de onde sai a argila."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 6, 15, 15), fill=SOMBRA)
    d.ellipse((1, 4, 14, 13), fill=ARG_D, outline=OUT)
    d.ellipse((3, 6, 12, 11), fill=LAMA)
    d.line((5, 8, 8, 8), fill=ARG_L)
    d.point((10, 9), fill=ARG_L)
    return im


def cenario():
    arq = ASSETS / "tileset-vila.png"
    t = Image.open(arq).convert("RGBA")
    # índices (a partir de 0): 44 toras -> argila | 45 horta -> telhas | 46 trigo -> barreiro
    for indice, peca in ((44, peca_argila()), (45, peca_telhas()), (46, peca_barreiro())):
        x, y = (indice % 16) * 16, (indice // 16) * 16
        t.paste((0, 0, 0, 0), (x, y, x + 16, y + 16))
        t.alpha_composite(peca, (x, y))
    t.save(arq)


if __name__ == "__main__":
    sprites()
    cenario()
    print("Arte da olaria gerada em", ASSETS)
