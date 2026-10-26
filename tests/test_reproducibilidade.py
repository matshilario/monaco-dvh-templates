"""Regera os templates do repositorio em pasta temporaria e compara com os arquivos commitados.

Uso: python tests/test_reproducibilidade.py   (tambem roda com pytest)
"""
import glob
import io
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from monaco_checksum import checksum  # noqa: E402

CASOS = [('templates/timmerman/timmerman2021.txt', 'templates/timmerman'),
         ('exemplos/prostata_70Gy_28fx.txt', 'exemplos')]


def _regera(spec, out):
    subprocess.run([sys.executable, os.path.join(ROOT, 'gerar_template.py'), os.path.join(ROOT, spec), out],
                   check=True, capture_output=True)


def test_xml_reproduzem():
    for spec, pasta in CASOS:
        with tempfile.TemporaryDirectory() as tmp:
            _regera(spec, tmp)
            gerados = sorted(glob.glob(os.path.join(tmp, '*.xml')))
            assert gerados, f'nada gerado para {spec}'
            for g in gerados:
                ref = os.path.join(ROOT, pasta, os.path.basename(g))
                assert os.path.exists(ref), f'{ref} nao esta no repositorio'
                a = io.open(g, encoding='utf-8', newline='').read()
                b = io.open(ref, encoding='utf-8', newline='').read()
                assert a == b, f'{ref} difere do regerado'


def test_checksums_batem():
    xmls = glob.glob(os.path.join(ROOT, 'templates', '**', '*.xml'), recursive=True) + \
        glob.glob(os.path.join(ROOT, 'exemplos', '*.xml'))
    assert xmls
    for p in xmls:
        raw = io.open(p, encoding='utf-8-sig', newline='').read()
        gravado = int(re.search(r'<Checksum>(\d+)</Checksum>', raw).group(1))
        assert checksum(raw) == gravado, f'{p}: calculado {checksum(raw)} x gravado {gravado}'


if __name__ == '__main__':
    test_xml_reproduzem()
    test_checksums_batem()
    print('OK: templates reproduzem e checksums batem')
