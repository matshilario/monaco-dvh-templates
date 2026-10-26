# Formato do template e checksum

Tudo abaixo foi observado no **Monaco 6.1.3**. Outras versões não foram testadas.

## XML

Um template é um arquivo `NomeDoTemplate.xml` (UTF-8, fim de linha CRLF) na pasta
`MonacoDvhCriteriaTemplates`:

```xml
<?xml version="1.0"?>
<DvhCriteriaTemplateData xmlns:xsd="..." xmlns:xsi="...">
  <Version>1</Version>
  <Checksum>220693</Checksum>
  <Description>texto livre ou vazio</Description>
  <AnatomicalSite>All | Brain | HN | Thorax | Abdomen | Pelvis | Other</AnatomicalSite>
  <DoseStructureParameters>
    <DoseStructureParametersData>          <!-- uma por estrutura, em ordem alfabetica -->
      <StructName>COCLEA D</StructName>
      <Enabled>1</Enabled>                 <!-- 1 com metas, 0 sem metas, -1 tambem existe -->
      <HighDoseRef>5</HighDoseRef>
      <MinDoseRef>95</MinDoseRef>
      <PrescribedDose>-1</PrescribedDose>  <!-- cGy, ou -1 -->
      <RefDoses>
        <RefDoseData><RefType>0</RefType><RefValue>2200</RefValue></RefDoseData>
      </RefDoses>
      <DoseGoals>
        <DoseGoalData>                     <!-- uma por meta -->
          <GoalType>8</GoalType>
          <Dose>2200</Dose>                <!-- cGy -->
          <Volume>35</Volume>              <!-- % para tipos 5/7/9/11; mm3 para tipos 8/12; -1 sem volume -->
          <Tolerance>0</Tolerance>
          <isShiftRecovery>false</isShiftRecovery>
          <RecoveryTolerance>INF</RecoveryTolerance>
          <Index>0</Index>
          <MeanDoseMaximum>-1</MeanDoseMaximum>              <!-- tipo 3: dose media em cGy, Dose = INF -->
          <MeanDoseMaxTolerance>-1</MeanDoseMaxTolerance>
          <MeanDoseMaxRecoveryTolerance>-1</MeanDoseMaxRecoveryTolerance>
        </DoseGoalData>
      </DoseGoals>
      <IsUnmapped>false</IsUnmapped>
    </DoseStructureParametersData>
  </DoseStructureParameters>
</DvhCriteriaTemplateData>
```

Tipos de meta (`GoalType`): 1 Dmin, 2 Dmax, 3 Dmean, 5 D(V%) mínimo, 7 D(V%) máximo,
8 D(Vcc) máximo, 9 V(D) mínimo em %, 11 V(D) máximo em %, 12 V(D) máximo em cc.
Os tipos 1, 9 e 12 foram inferidos de templates antigos e ainda não foram conferidos na tela.

## Checksum

O Monaco só lista templates cujo `<Checksum>` bate com o calculado. A regra, implementada em
`monaco_checksum.py`:

```
checksum = 3320
         + 5240 × (nº de DoseStructureParametersData)
         + 2287 × (nº de RefDoseData)
         + 6467 × (nº de DoseGoalData)
         + soma dos valores das folhas abaixo
```

- Texto (`StructName`, `Description`, `AnatomicalSite`, `GoalType`, `Index`, `RefType`,
  `Version`): soma dos bytes em Windows-1252, cada byte como char **com sinal**
  (byte > 127 conta byte − 256; acentos são negativos).
- Números reais (`Dose`, `Volume`, `Tolerance`, `RecoveryTolerance`, `PrescribedDose`,
  `RefValue`, `HighDoseRef`, `MinDoseRef`): formatados com 6 algarismos significativos
  (`%g` do C) e somados como texto. `INF` vira `inf`; `RecoveryTolerance` igual a 0 vira `inf`.
- `Enabled`: entra o próprio valor numérico (−1, 0 ou 1).
- Não entram: `Checksum`, `MeanDoseMaximum`, `MeanDoseMaxTolerance`,
  `MeanDoseMaxRecoveryTolerance`, `IsUnmapped`, `isShiftRecovery`.

Como foi descoberta: 50 templates antigos do serviço mais 13 testes controlados criados no Monaco
mudando um fator por vez (dose, meta extra, description, site, Enabled, maiúsculas no nome).
A fórmula fecha nos 63. Validação final: dois templates gerados apareceram no Monaco e um controle
negativo com checksum errado não apareceu (Monaco 6.1.3, outubro de 2026).
