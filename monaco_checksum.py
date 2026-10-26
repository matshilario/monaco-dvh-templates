"""Checksum dos templates de DVH Criteria do Monaco (engenharia reversa, 2026-10-23).

Fecha nos 13 testes controlados e nos 50 templates antigos (63/63).

Regra:
  checksum = soma dos valores abaixo + 3320 + 5240*nEstruturas + 2287*nRefDoseData + 6467*nMetas
  - texto (StructName, Description, AnatomicalSite, GoalType, Index, RefType, Version):
      soma dos bytes Windows-1252, como char COM SINAL (acento: byte - 256)
  - numeros reais (Dose, Volume, Tolerance, RecoveryTolerance, PrescribedDose, RefValue,
      HighDoseRef, MinDoseRef): formatados com 6 algarismos significativos (%g), somados como texto;
      INF vira "inf"; RecoveryTolerance 0 vira "inf"
  - Enabled: entra o proprio valor numerico (-1, 0, 1)
  - nao entram: MeanDoseMaximum, MeanDoseMaxTolerance, MeanDoseMaxRecoveryTolerance,
      IsUnmapped, isShiftRecovery, Checksum

Uso:
  python monaco_checksum.py arquivo.xml [...]     -> mostra checksum calculado e o gravado
  python monaco_checksum.py arquivo.xml --fix     -> regrava o arquivo com o checksum calculado
"""
import io
import re
import sys
import xml.etree.ElementTree as ET

BASE, K_STRUCT, K_REF, K_GOAL = 3320, 5240, 2287, 6467
DOUBLES = {'Dose', 'Volume', 'Tolerance', 'RecoveryTolerance', 'PrescribedDose', 'RefValue', 'HighDoseRef', 'MinDoseRef'}
IGNORE = {'Checksum', 'MeanDoseMaximum', 'MeanDoseMaxTolerance', 'MeanDoseMaxRecoveryTolerance', 'IsUnmapped', 'isShiftRecovery'}


def _fmt_double(tag, txt):
    if txt == 'INF':
        return 'inf'
    v = float(txt)
    if tag == 'RecoveryTolerance' and v == 0:
        return 'inf'
    return '%g' % v


def _signed_bytes(s):
    return sum(b - 256 if b > 127 else b for b in s.encode('cp1252'))


def checksum(xml_text: str) -> int:
    root = ET.fromstring(xml_text)
    total = BASE
    for e in root.iter():
        if len(e):
            if e.tag == 'DoseStructureParametersData':
                total += K_STRUCT
            elif e.tag == 'RefDoseData':
                total += K_REF
            elif e.tag == 'DoseGoalData':
                total += K_GOAL
            continue
        if e.tag in IGNORE:
            continue
        txt = e.text or ''
        if e.tag == 'Enabled':
            total += int(txt)
        elif e.tag in DOUBLES:
            total += _signed_bytes(_fmt_double(e.tag, txt))
        else:
            total += _signed_bytes(txt)
    return total


def main():
    fix = '--fix' in sys.argv
    for path in [a for a in sys.argv[1:] if a != '--fix']:
        raw = io.open(path, encoding='utf-8-sig', newline='').read()
        calc = checksum(raw)
        m = re.search(r'<Checksum>(\d+)</Checksum>', raw)
        stored = int(m.group(1)) if m else None
        print(f'{path}: calculado={calc} gravado={stored} {"OK" if calc == stored else "DIFERENTE"}')
        if fix and calc != stored:
            new = raw.replace(m.group(0), f'<Checksum>{calc}</Checksum>', 1)
            io.open(path, 'w', encoding='utf-8', newline='').write(new)
            print('  arquivo regravado')


if __name__ == '__main__':
    main()
