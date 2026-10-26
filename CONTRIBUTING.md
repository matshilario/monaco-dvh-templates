# Contribuindo

O que mais ajuda, em ordem:

1. **Validar na tela do Monaco** os itens marcados como "só o checksum" no README (`Dmean`, tipos 1/9/12,
   `site` diferente de `All`, `description`). Abra uma issue com o modelo "Validei um item na tela do Monaco".
2. **Relatar se a fórmula do checksum vale na sua versão do Monaco.** Rode `python monaco_checksum.py` nos
   templates que o seu Monaco criou. Se algum der `DIFERENTE`, abra uma issue com o modelo
   "Checksum não bate no meu Monaco" e anexe o XML.
3. **Novos conjuntos de templates** (QUANTEC, HyTEC, protocolos de consenso). Envie o `.txt` de especificação
   em `templates/<nome>/` junto com os XML gerados e cite a fonte no README.
4. Correções e novos tipos de meta no `gerar_template.py`.

Antes de abrir um PR, rode:

```bash
python tests/test_reproducibilidade.py
```

Se você mudou um `.txt` ou o gerador, regere os XML correspondentes e inclua-os no PR, senão o teste falha.

Templates de DVH Criteria não contêm dados de paciente, mas confira o conteúdo antes de anexar qualquer
arquivo vindo do seu serviço.
