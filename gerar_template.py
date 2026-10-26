"""Gera templates de DVH Criteria do Monaco a partir de um arquivo de texto simples.

Uso:
    python gerar_template.py especificacao.txt [pasta_saida]

Formato da especificacao (uma ou mais secoes "template:"):

    template: PTTA_70Gy_28fx          # nome do arquivo .xml gerado
    site: Brain                       # opcional (All, Brain, HN, Thorax, Abdomen, Pelvis, Other)
    description: texto livre          # opcional
    PTV_70Gy@28Fr  PD=7000            # estrutura; PD = dose de prescricao em cGy (opcional)
      D95% >= 7000  tol 350           # metas, indentadas
      D0.027cc <= 7700  tol 350
    Reto                              # estrutura sem metas (fica desabilitada)
    Bexiga
      Dmax <= 8300
      V7000 <= 15%  tol 5
      Dmean <= 2600 tol 100

Metas aceitas (doses em cGy, volumes em % ou cc, tolerancia opcional "tol N"):
    Dmax <= D          tipo 2
    DV% >= D           tipo 5   (ex.: D95% >= 7000)
    DV% <= D           tipo 7   (ex.: D1% <= 2000)
    DVcc <= D          tipo 8   (ex.: D0.5cc <= 2000; o Monaco grava o volume em mm3)
    VD <= V%           tipo 11  (ex.: V6500 <= 25%)
    Dmean <= D         tipo 3   (dose media; campo MeanDoseMaximum)
  Inferidos dos templates antigos, ainda nao conferidos na tela do Monaco:
    VD <= Vcc          tipo 12  (ex.: V1600 <= 15cc)
    VD >= V%           tipo 9   (ex.: V3800 >= 95%)
    Dmin >= D          tipo 1

Checksum: calculado por monaco_checksum.py (formula completa, fecha em 63/63 arquivos; validada no
Monaco em 23/10/2026). Toda estrutura recebe um RefDoseData, como o Monaco faz; estruturas com metas
usam PD (ou a maior dose das metas) como dose de referencia.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CRLF = '\r\n'


def fmt(v):
    """Numero -> texto como o Monaco grava (sem .0, ponto decimal)."""
    if isinstance(v, str):
        return v
    if float(v).is_integer():
        return str(int(v))
    return repr(float(v))


def parse_goal(line):
    s = line.strip()
    tol = 0
    m = re.search(r'\btol\s*([\d.]+)\s*$', s)
    if m:
        tol = float(m.group(1))
        s = s[:m.start()].strip()
    goal = dict(GoalType=None, Dose=None, Volume=-1, Tolerance=tol, isShiftRecovery='false',
                RecoveryTolerance='INF', Index=0, MeanDoseMaximum=-1, MeanDoseMaxTolerance=-1,
                MeanDoseMaxRecoveryTolerance=-1)
    if m := re.fullmatch(r'Dmax\s*<=\s*([\d.]+)', s, re.I):
        goal.update(GoalType=2, Dose=float(m.group(1)))
    elif m := re.fullmatch(r'Dmean\s*<=\s*([\d.]+)', s, re.I):
        goal.update(GoalType=3, Dose='INF', Tolerance=0, MeanDoseMaximum=float(m.group(1)),
                    MeanDoseMaxTolerance=tol, MeanDoseMaxRecoveryTolerance='INF')
    elif m := re.fullmatch(r'D\s*([\d.]+)\s*%\s*(>=|<=)\s*([\d.]+)', s, re.I):
        goal.update(GoalType=5 if m.group(2) == '>=' else 7, Dose=float(m.group(3)), Volume=float(m.group(1)))
    elif m := re.fullmatch(r'D\s*([\d.]+)\s*(cc|cm3|cm³)\s*<=\s*([\d.]+)', s, re.I):
        goal.update(GoalType=8, Dose=float(m.group(3)), Volume=round(float(m.group(1)) * 1000))
    elif m := re.fullmatch(r'V\s*([\d.]+)\s*(<=|>=)\s*([\d.]+)\s*%', s, re.I):
        goal.update(GoalType=11 if m.group(2) == '<=' else 9, Dose=float(m.group(1)), Volume=float(m.group(3)))
    elif m := re.fullmatch(r'V\s*([\d.]+)\s*<=\s*([\d.]+)\s*(cc|cm3|cm³)', s, re.I):
        goal.update(GoalType=12, Dose=float(m.group(1)), Volume=round(float(m.group(2)) * 1000))
    elif m := re.fullmatch(r'Dmin\s*>=\s*([\d.]+)', s, re.I):
        goal.update(GoalType=1, Dose=float(m.group(1)))
    else:
        raise ValueError(f'meta nao reconhecida: {line!r}')
    return goal


def parse_spec(text):
    templates = []
    cur = None
    for raw in text.splitlines():
        line = raw.split('#', 1)[0].rstrip()
        if not line.strip():
            continue
        if line.lower().startswith('template:'):
            cur = dict(name=line.split(':', 1)[1].strip(), site='All', description='', structs=[])
            templates.append(cur)
        elif line.lower().startswith('site:'):
            cur['site'] = line.split(':', 1)[1].strip()
        elif line.lower().startswith('description:'):
            cur['description'] = line.split(':', 1)[1].strip()
        elif line[0] in ' \t':
            cur['structs'][-1]['goals'].append(parse_goal(line))
        else:
            m = re.search(r'\s+PD\s*=\s*([\d.]+)\s*$', line)
            pd = float(m.group(1)) if m else -1
            name = line[:m.start()].strip() if m else line.strip()
            cur['structs'].append(dict(name=name, pd=pd, goals=[]))
    return templates


def leaf(tag, value, ind):
    return f'{" " * ind}<{tag}>{fmt(value)}</{tag}>'


def build_xml(t):
    L = ['<?xml version="1.0"?>',
         '<DvhCriteriaTemplateData xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">',
         '  <Version>1</Version>', '  <Checksum>0</Checksum>',
         f'  <Description>{t["description"]}</Description>' if t.get('description') else '  <Description />',
         f'  <AnatomicalSite>{t["site"]}</AnatomicalSite>', '  <DoseStructureParameters>']
    for s in sorted(t['structs'], key=lambda x: x['name']):
        goals = s['goals']
        enabled = 1 if goals else 0
        ref = s['pd'] if s['pd'] != -1 else (max([g['Dose'] for g in goals if g['Dose'] != 'INF'] +
                                               [g['MeanDoseMaximum'] for g in goals if g['MeanDoseMaximum'] != -1], default=-1))
        L += ['    <DoseStructureParametersData>', leaf('StructName', s['name'], 6), leaf('Enabled', enabled, 6),
              leaf('HighDoseRef', 5, 6), leaf('MinDoseRef', 95, 6), leaf('PrescribedDose', s['pd'], 6),
              '      <RefDoses>', '        <RefDoseData>', leaf('RefType', 0, 10), leaf('RefValue', ref, 10),
              '        </RefDoseData>', '      </RefDoses>']
        if goals:
            L.append('      <DoseGoals>')
            for g in goals:
                L.append('        <DoseGoalData>')
                for k, v in g.items():
                    L.append(leaf(k, v, 10))
                L.append('        </DoseGoalData>')
            L.append('      </DoseGoals>')
        else:
            L.append('      <DoseGoals />')
        L += [leaf('IsUnmapped', 'false', 6), '    </DoseStructureParametersData>']
    L += ['  </DoseStructureParameters>', '</DvhCriteriaTemplateData>']
    xml = CRLF.join(L) + CRLF
    return xml.replace('<Checksum>0</Checksum>', f'<Checksum>{checksum(xml)}</Checksum>', 1)


def checksum(xml):
    from monaco_checksum import checksum as _cs
    return _cs(xml)


def main():
    spec = open(sys.argv[1], encoding='utf-8').read()
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(sys.argv[1]))
    os.makedirs(out, exist_ok=True)
    for t in parse_spec(spec):
        xml = build_xml(t)
        path = os.path.join(out, t['name'] + '.xml')
        with open(path, 'w', encoding='utf-8', newline='') as fh:
            fh.write(xml)
        nG = sum(len(s['goals']) for s in t['structs'])
        print(f'{path}: {len(t["structs"])} estruturas, {nG} metas, checksum {checksum(xml)}')


if __name__ == '__main__':
    main()
