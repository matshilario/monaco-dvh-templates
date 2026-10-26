# monaco-dvh-templates

[![tests](https://github.com/matshilario/monaco-dvh-templates/actions/workflows/tests.yml/badge.svg)](https://github.com/matshilario/monaco-dvh-templates/actions/workflows/tests.yml)
![python](https://img.shields.io/badge/python-3.8%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![monaco](https://img.shields.io/badge/validado%20no-Monaco%206.1.3-orange)

Gere templates de **DVH Criteria** do TPS Elekta Monaco a partir de um arquivo de texto simples,
sem passar pela interface gráfica. Inclui 30 templates prontos baseados nas tabelas de
Timmerman (2021) para 1 a 30 frações.

> **Aviso.** O formato do XML e o checksum foram obtidos por engenharia reversa no **Monaco 6.1.3**,
> sem qualquer relação com a Elekta. Outras versões podem gravar o checksum de outra forma
> (veja [como conferir](#conferir-ou-corrigir-o-checksum-de-um-xml)). Um template com checksum errado simplesmente não aparece na lista do
> Monaco; um template com checksum certo e **valores errados aparece e pode ser usado**.
> Confira cada template na tela do Monaco antes de qualquer uso clínico. Use por sua conta e risco.

## Índice

- [Requisitos](#requisitos)
- [Uso rápido](#uso-rápido)
- [Formato da especificação](#formato-da-especificação)
- [Templates Timmerman](#templates-timmerman)
- [Conferir ou corrigir o checksum de um XML](#conferir-ou-corrigir-o-checksum-de-um-xml)
- [Como o checksum funciona](#como-o-checksum-funciona)
- [Testes](#testes)
- [Contribuindo](#contribuindo)
- [English summary](#english-summary)

## Requisitos

- Python 3.8 ou superior. Nenhuma biblioteca extra.
- Acesso à pasta de templates do seu Monaco (`MonacoDvhCriteriaTemplates`). No nosso serviço ela
  fica num compartilhamento de rede; o caminho muda de instalação para instalação.

## Uso rápido

```bash
git clone https://github.com/matshilario/monaco-dvh-templates.git
cd monaco-dvh-templates
python gerar_template.py exemplos/prostata_70Gy_28fx.txt saida
```

Sai um `.xml` por template em `saida/`, com o checksum já calculado. Copie o arquivo para a pasta
`MonacoDvhCriteriaTemplates` do seu Monaco, abra o DVH Criteria e confira se ele aparece na lista.

Os templates Timmerman já gerados estão em [`templates/timmerman/`](templates/timmerman) e podem
ser copiados direto, mas leia a seção sobre eles antes.

## Formato da especificação

Um arquivo `.txt` (UTF-8) pode conter vários templates. Cada um começa com `template:`.
Estruturas começam na coluna 0; metas ficam indentadas abaixo da estrutura. Doses em **cGy**.
`#` inicia comentário.

```
template: PTTA_70Gy_56Gy_28fx      # nome do arquivo .xml gerado
site: Pelvis                        # opcional: All, Brain, HN, Thorax, Abdomen, Pelvis, Other
description: Prostata 28 x 250 cGy  # opcional

PTV_70Gy@28Fr  PD=7000              # PD = dose de prescricao em cGy (opcional)
  D95% >= 7000  tol 350
  D0.027cc <= 7700  tol 350
Reto
  Dmax <= 8200
  V7000 <= 15%
  V5000 <= 45%  tol 5
Bexiga
  Dmean <= 2600  tol 100
Femur D                             # estrutura sem metas: entra desabilitada
```

O nome da estrutura precisa ser **idêntico** ao usado no seu Monaco. `tol N` é a tolerância
(opcional). Exemplo completo em [`exemplos/prostata_70Gy_28fx.txt`](exemplos/prostata_70Gy_28fx.txt).

### Metas aceitas

| Sintaxe | Significado | Tipo no XML | Validado na tela do Monaco |
|---|---|---|---|
| `Dmax <= 8200` | dose máxima | 2 | sim |
| `D95% >= 7000` | dose mínima em 95 % do volume | 5 | sim |
| `D1% <= 2000` | dose máxima em 1 % do volume | 7 | sim |
| `D0.5cc <= 2000` | dose máxima em 0,5 cc | 8 | sim |
| `V6500 <= 25%` | volume máximo que recebe 6500 cGy | 11 | sim |
| `Dmean <= 2600` | dose média máxima | 3 | só o checksum |
| `V1600 <= 15cc` | volume máximo em cc que recebe 1600 cGy | 12 | só o checksum |
| `V3800 >= 95%` | volume mínimo que recebe 3800 cGy | 9 | só o checksum |
| `Dmin >= 5000` | dose mínima | 1 | só o checksum |

"Só o checksum" significa que o template aparece no Monaco, mas ainda não conferimos se os valores
são exibidos exatamente como pretendido. `site` diferente de `All` e `description` estão na mesma
situação. Se você validar algum desses, abra uma issue ou PR.

## Templates Timmerman

[`templates/timmerman/`](templates/timmerman) contém 30 templates (Brain, Torax, Pelve × 1, 2, 3,
4, 5, 8, 10, 15, 20 e 30 frações) gerados a partir das tabelas de:

> Timmerman R. *A Story of Hypofractionation and the Table on the Wall.*
> Int J Radiat Oncol Biol Phys. 2022;112(1):4-21.

Como foram montados:

- Órgãos seriais: `D(volume)cc <= limite de volume` e `D0.035cc <= dose máxima pontual`
  ("ponto" = 0,035 cc, como no artigo).
- Pulmões: `V(dose) <= 37 %` (pneumonite). A regra de volume crítico (1500 cc) não cabe num
  template fixo e ficou de fora.
- **A dose do PTV é uma suposição** de prescrição típica por sítio e fracionamento
  (`D95% >= Rx`, tolerância 5 %). Ajuste conforme o seu caso.
- **Os nomes das estruturas seguem a convenção do nosso serviço** (`MEDULA`, `COCLEA D`,
  `Femur E`, `patient(Unsp.Tiss.)` etc.). Se o seu serviço usa outros nomes, edite
  `templates/timmerman/timmerman2021.txt` (ou o dicionário em `gerar_spec_timmerman.py`) e regere.
- Esses templates usam `site`, `description` e, de 10 a 30 frações, `Dmean` para os olhos. Esses
  três itens ainda estão na categoria "só o checksum" da tabela acima.

Para regerar tudo a partir das tabelas:

```bash
python templates/timmerman/gerar_spec_timmerman.py
python gerar_template.py templates/timmerman/timmerman2021.txt templates/timmerman
```

## Conferir ou corrigir o checksum de um XML

```bash
python monaco_checksum.py arquivo.xml            # mostra calculado x gravado
python monaco_checksum.py arquivo.xml --fix      # regrava com o checksum calculado
```

Útil para quem prefere editar um template existente na mão: edite o XML, rode `--fix` e copie para
o Monaco. Também serve para checar se a fórmula vale no seu Monaco: rode nos templates que o seu
próprio Monaco criou. Se algum der `DIFERENTE`, a sua versão grava o checksum de outro jeito e a
ferramenta não vai funcionar aí (abra uma issue informando a versão).

Versões em que a fórmula foi confirmada:

| Monaco | Resultado | Fonte |
|---|---|---|
| 6.1.3 | 63/63 templates batem; templates gerados aparecem na lista | autor, out/2026 |

Se funcionou na sua versão, abra uma issue para entrar nesta tabela.

## Como o checksum funciona

Resumo em [`docs/FORMATO_XML.md`](docs/FORMATO_XML.md). A fórmula fechou em 63 de 63 arquivos
(50 templates antigos do serviço mais 13 testes controlados criados no Monaco) e foi validada no
**Monaco 6.1.3** em outubro de 2026 copiando templates gerados e um controle negativo com checksum errado.

## Testes

```bash
python tests/test_reproducibilidade.py
```

Regera os templates Timmerman e o exemplo em uma pasta temporária, compara byte a byte com os
arquivos do repositório e confere o checksum de todos os XML.

## Contribuindo

Veja [`CONTRIBUTING.md`](CONTRIBUTING.md). As contribuições mais úteis são validações na tela do Monaco
e relatos de versões do Monaco em que o checksum não bate.

## English summary

Generate Elekta Monaco **DVH Criteria templates** from a plain-text spec instead of clicking through the
GUI. Monaco only lists templates whose `<Checksum>` matches; the formula was reverse-engineered
(63/63 files, validated on **Monaco 6.1.3** in October 2026; other versions untested) and is documented in
[`docs/FORMATO_XML.md`](docs/FORMATO_XML.md). Ships with 30 ready-made templates from Timmerman's 2021
hypofractionation tables (1 to 30 fractions, brain / thorax / pelvis), using our department's
Portuguese structure names; edit `templates/timmerman/timmerman2021.txt` and regenerate to adapt.
Not affiliated with Elekta. Check every template on screen before clinical use.

```bash
python gerar_template.py exemplos/prostata_70Gy_28fx.txt output
python monaco_checksum.py file.xml --fix     # recompute the checksum of a hand-edited template
```

## Licença

MIT. Veja [`LICENSE`](LICENSE).
