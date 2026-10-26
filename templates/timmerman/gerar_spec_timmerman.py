"""Escreve templates/timmerman/timmerman2021.txt a partir das tabelas de Timmerman (IJROBP 2022;112(1):4-21,
tabelas 8-2021) para 1, 2, 3, 4, 5, 8, 10, 15, 20 e 30 fracoes, nos sitios Brain, Thorax e Pelvis.

Uso (na raiz do repositorio):
    python templates/timmerman/gerar_spec_timmerman.py
    python gerar_template.py templates/timmerman/timmerman2021.txt templates/timmerman
Valores em Gy, exatamente como nas tabelas. "Ponto" = 0,035 cc.
"""
import io
import os

cGy = lambda gy: int(round(gy * 100))
PT = '0.035'

# ---------------- tabelas SBRT: 1, 2, 3, 4, 5, 8 fracoes (vol fixo por tecido) ----------------
SBRT_N = [1, 2, 3, 4, 5, 8]
SBRT = {
    # nome: (volume cc, [(vmax, ponto) por fracao])
    'optic':    ('0.2',  [(8, 10), (11.7, 13.7), (15.3, 17.4), (19.2, 21.2), (23, 25), (27.2, 29.6)]),
    'cochlea':  (None,   [(None, 9), (None, 11.7), (None, 14.4), (None, 18), (None, 22), (None, 26.4)]),
    'tronco':   ('0.5',  [(10, 15), (13, 19.1), (15.9, 23.1), (20.8, 27.2), (23, 31), (27.2, 37.6)]),
    'medula':   ('0.35', [(10, 14), (13, 18.3), (15.9, 22.5), (18, 25.6), (22, 28), (26.4, 33.6)]),
    'cauda':    ('5',    [(14, 16), (18, 20.8), (21.9, 25.5), (26, 28.8), (30, 31.5), (34, 38.4)]),
    'sacral':   ('5',    [(14.4, 16), (18.5, 20.8), (22.5, 25.5), (26, 28.8), (30, 32), (34, 38.4)]),
    'esofago':  ('5',    [(20, 24), (24.3, 28.3), (27.9, 32.4), (30.4, 35.6), (32.5, 38), (36.8, 43.2)]),
    'plexo':    ('3',    [(13.6, 16.4), (17.8, 21.2), (22, 26), (24.8, 29.6), (27, 32.5), (32.8, 39.2)]),
    'coracao':  ('15',   [(16, 22), (20, 26), (24, 30), (28, 34), (32, 38), (34.4, 40)]),
    'vasos':    ('10',   [(31, 37), (35, 41), (39, 45), (43, 49), (47, 53), (55.2, 62)]),
    'traqueia': (None,   [(27.5, 30), (34.5, 38), (39, 43), (42.4, 47), (45, 50), (50, 56)]),   # 4 cc em 1-2 fr, 5 cc em 3+
    'bronquios': ('0.5', [(17.4, 20.2), (21.6, 25.1), (25.8, 30), (28.8, 34.8), (32, 40), (38.4, 48.8)]),
    'costelas': ('5',    [(28, 33), (34, 41.5), (40, 50), (43, 54), (45, 57), (50, 63)]),
    'pele':     ('10',   [(25.5, 27.5), (28.3, 30.3), (31, 33), (33.6, 36), (36.5, 38.5), (43.2, 45.6)]),
    'estomago': ('5',    [(17.4, 22), (20, 26), (22.5, 30), (25, 33.2), (26.5, 35), (31.2, 42)]),
    'intestino': ('30',  [(17.6, 20), (19.2, 24), (20.7, 28.5), (22.4, 31.6), (24, 34.5), (28.8, 40)]),
    'colon':    ('20',   [(20.5, 31), (25.8, 39), (28.8, 45), (30.8, 48.5), (32.5, 52.5), (35.2, 57.5)]),
    'ureter':   (None,   [(None, 35), (None, 37.5), (None, 40), (None, 43), (None, 45), (None, 53)]),
    'bexiga':   ('15',   [(12, 25), (14.5, 29), (17, 33), (18.5, 35.6), (20, 38), (22.4, 44.8)]),
    'bulbo':    ('3',    [(16, None), (20.5, None), (25, None), (27, None), (30, None), (35, None)]),
    'femur':    ('10',   [(15, None), (19.5, None), (24, None), (27, None), (30, None), (35, None)]),
}
SBRT_RETO = [(30, 33.7, 23), (38, 41.3, 26.7), (43, 47, 30.3), (47.2, 51.6, 34), (50, 55, 37.5), (56, 61.5, 45)]  # 3.5cc, ponto, 20cc
SBRT_LUNG_V = [8, 10, 11.4, 12.8, 13.5, 15.2]   # V(dose) < 37%

# ---------------- tabelas estendidas: 10, 15, 20, 30 fracoes ----------------
EXT_N = [10, 15, 20, 30]
EXT = {
    'optic':    ('0.5', [(30.6, 33.1), (39, 42), (42, 48), (44, 52)]),
    'cochlea':  ('0.5', [(25, 27), (30, 33), (32, 36), (36, 40)]),
    'tronco':   ('5',   [(32, 38), (40, 44), (44, 50), (52, 60)]),
    'medula':   ('5',   [(31, 36), (39, 42), (42, 46), (47.4, 52.8)]),
    'cauda':    ('5',   [(35, 41), (40.5, 48), (44, 52), (50, 60)]),
    'sacral':   ('5',   [(35, 41), (40.5, 48), (44, 52), (50, 60)]),
    'esofago':  ('5',   [(40, 48), (45, 54), (48, 58), (51, 60)]),
    'plexo':    ('3',   [(37, 43), (48, 52.5), (54, 58), (62, 66)]),
    'coracao':  ('15',  [(36.6, 42.5), (42, 48.9), (46, 52), (60, 68)]),
    'vasos':    ('10',  [(55.7, 62.9), (57, 65), (60, 70), (60, 76)]),
    'traqueia': ('5',   [(52, 59), (55.5, 63), (58, 66), (60, 69)]),
    'pele':     ('10',  [(46.3, 48.9), (54, 57), (60, 64), (70, 76)]),
    'estomago': ('50',  [(33.9, 45), (39, 51), (42, 54), (45, 60)]),
    'intestino': ('120', [(33.9, 41), (39, 46.5), (42, 50), (45, 54)]),
    'colon':    ('20',  [(47, 60), (47, 64.5), (50, 66), (54, 70)]),
    'bulbo':    ('3',   [(38, 44), (42, 48), (44, 52), (48, 56)]),
    'femur':    ('10',  [(38, 43.5), (40, 46.5), (44, 50), (48, 56)]),
}
EXT_EYE = [(26, 30), (33, 37.5), (36, 42), (38, 45)]       # Dmean, ponto
EXT_LENS = [7, 9, 10, 10]                                   # ponto
EXT_RETO = [(52, 49, 46, 43, 65), (60, 57, 52.5, 49.5, 70.5), (66, 62, 58, 54, 74), (75, 70, 65, 60, 79)]  # 10,20,30,40cc, ponto
EXT_BEX = [(48, 45, 53, 125), (55.5, 52.5, 61.5, 125), (60, 56, 66, 125), (70, 65, 79, 150)]            # 90cc, 2o vol, ponto, 2o vol cc
EXT_LUNG_V = [16, 18, 19, 20]

# dose do PTV assumida (Gy) por sitio e fracao: SUPOSICAO, ajustar conforme a clinica
RX = {
    'Brain':  {1: 20, 2: 24, 3: 27, 4: 28, 5: 30, 8: 32, 10: 30, 15: 37.5, 20: 40, 30: 60},
    'Thorax': {1: 34, 2: 24, 3: 54, 4: 48, 5: 50, 8: 60, 10: 50, 15: 45, 20: 55, 30: 60},
    'Pelvis': {1: 24, 2: 20, 3: 30, 4: 28, 5: 35, 8: 40, 10: 30, 15: 37.5, 20: 60, 30: 60},
}


def serial(name, vol, vmax, pt):
    L = [name]
    if vol and vmax:
        L.append(f'  D{vol}cc <= {cGy(vmax)}')
    if pt:
        L.append(f'  D{PT}cc <= {cGy(pt)}')
    return L


def ptv(dose, n):
    return [f'PTV_{dose:g}Gy@{n}Fr  PD={cGy(dose)}', f'  D95% >= {cGy(dose)}  tol {cGy(dose * 0.05)}']


def get(tab, key, i):
    vol, rows = tab[key]
    return vol, rows[i][0], rows[i][1]


def build():
    out = []

    def tpl(name, site, n, structs):
        out.append(f'template: {name}')
        out.append(f'site: {site}')
        out.append(f'description: Timmerman 2021 - {n} fracoes')
        for s in structs:
            out.extend(s)
        out.append('')

    for fam, NS, TAB in (('sbrt', SBRT_N, SBRT), ('ext', EXT_N, EXT)):
        for i, n in enumerate(NS):
            ext = fam == 'ext'
            # ---------- CEREBRO ----------
            S = [ptv(RX['Brain'][n], n), ['GTV'], ['patient(Unsp.Tiss.)']]
            for nm in ('NOE', 'NOD', 'QUIASMA'):
                S.append(serial(nm, *get(TAB, 'optic', i)))
            for nm in ('COCLEA D', 'COCLEA E'):
                S.append(serial(nm, *get(TAB, 'cochlea', i)))
            S.append(serial('TRONCO', *get(TAB, 'tronco', i)))
            S.append(serial('MEDULA', *get(TAB, 'medula', i)))
            if ext:
                for nm in ('OLHO D', 'OLHO E'):
                    S.append([nm, f'  Dmean <= {cGy(EXT_EYE[i][0])}', f'  D{PT}cc <= {cGy(EXT_EYE[i][1])}'])
                for nm in ('CRISTALINO D', 'CRISTALINO E'):
                    S.append([nm, f'  D{PT}cc <= {cGy(EXT_LENS[i])}'])
            else:
                S += [['CRISTALINO D'], ['CRISTALINO E'], ['OLHO D'], ['OLHO E']]
            tpl(f'TimmermanBrain{n}fr', 'Brain', n, S)

            # ---------- TORAX ----------
            S = [ptv(RX['Thorax'][n], n), ['ITV'], ['patient(Unsp.Tiss.)'],
                 serial('MEDULA', *get(TAB, 'medula', i)), serial('ESOFAGO', *get(TAB, 'esofago', i)),
                 serial('PLEXO', *get(TAB, 'plexo', i))]
            coracao = serial('CORACAO', *get(TAB, 'coracao', i))
            if n == 30:
                coracao.append('  V4000 <= 20%')      # coracao: <20% do volume acima de 40 Gy (tabela de 30 fr)
            S += [coracao, serial('VASOS', *get(TAB, 'vasos', i))]
            if ext:
                S.append(serial('TRAQUEIA', *get(TAB, 'traqueia', i)))
            else:
                _, vmax, pt = get(TAB, 'traqueia', i)
                S.append(serial('TRAQUEIA', '4' if n <= 2 else '5', vmax, pt))
                S.append(serial('BRONQUIOS', *get(TAB, 'bronquios', i)))
                S.append(serial('COSTELAS', *get(TAB, 'costelas', i)))
            S.append(serial('pele', *get(TAB, 'pele', i)))
            S.append(serial('ESTOMAGO', *get(TAB, 'estomago', i)))
            lungv = (EXT_LUNG_V if ext else SBRT_LUNG_V)[i]
            S += [['PULMOES', f'  V{cGy(lungv)} <= 37%'], ['PULMAO D'], ['PULMAO E']]
            tpl(f'TimmermanTorax{n}fr', 'Thorax', n, S)

            # ---------- PELVE ----------
            S = [ptv(RX['Pelvis'][n], n), ['CTV'], ['patient(Unsp.Tiss.)'],
                 serial('CAUDA EQUINA', *get(TAB, 'cauda', i)), serial('PLEXO SACRAL', *get(TAB, 'sacral', i)),
                 serial('INTESTINO', *get(TAB, 'intestino', i)), serial('COLON', *get(TAB, 'colon', i))]
            if ext:
                r = EXT_RETO[i]
                S.append(['Reto', f'  D10cc <= {cGy(r[0])}', f'  D20cc <= {cGy(r[1])}', f'  D30cc <= {cGy(r[2])}',
                          f'  D40cc <= {cGy(r[3])}', f'  D{PT}cc <= {cGy(r[4])}'])
                b = EXT_BEX[i]
                S.append(['Bexiga', f'  D90cc <= {cGy(b[0])}', f'  D{b[3]}cc <= {cGy(b[1])}', f'  D{PT}cc <= {cGy(b[2])}'])
            else:
                r = SBRT_RETO[i]
                S.append(['Reto', f'  D3.5cc <= {cGy(r[0])}', f'  D20cc <= {cGy(r[2])}', f'  D{PT}cc <= {cGy(r[1])}'])
                S.append(serial('URETER', *get(TAB, 'ureter', i)))
                S.append(serial('Bexiga', *get(TAB, 'bexiga', i)))
            S.append(serial('Bulbo', *get(TAB, 'bulbo', i)))
            S.append(serial('Femur D', *get(TAB, 'femur', i)))
            S.append(serial('Femur E', *get(TAB, 'femur', i)))
            tpl(f'TimmermanPelve{n}fr', 'Pelvis', n, S)
    return out


HDR = '''# Templates de DVH Criteria gerados a partir de Timmerman R. "A Story of Hypofractionation and the Table
# on the Wall", IJROBP 2022;112(1):4-21 (tabelas 8-2021), para 1, 2, 3, 4, 5, 8, 10, 15, 20 e 30 fracoes.
# Doses em cGy. "Ponto" = 0,035 cc. Serial: D(volume)cc <= Volume max; D0.035cc <= Max point dose.
# Pulmao: V(dose) <= 37% (pneumonite); a regra de volume critico (1500 cc) nao cabe num template fixo.
# A dose do PTV (D95% >= Rx, tol 5%) e uma SUPOSICAO de prescricao tipica: ajuste conforme o caso.
# Gerado por templates/timmerman/gerar_spec_timmerman.py. Para regerar os XML (na raiz do repositorio):
#   python gerar_template.py templates/timmerman/timmerman2021.txt templates/timmerman
'''

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    dest = os.path.join(here, 'timmerman2021.txt')
    io.open(dest, 'w', encoding='utf-8').write(HDR + '\n'.join(build()))
    print('escrito', os.path.normpath(dest))
