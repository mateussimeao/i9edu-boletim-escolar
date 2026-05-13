# Gerador de Boletins e Relatórios SMED

Ferramenta para geração automatizada de boletins escolares e relatórios de indicadores educacionais em PDF, consolidando dados de avaliações externas, rendimento, fluência leitora e metas por escola, regional e rede municipal.

---

## Conceitos

### Formatos de saída

| Formato | Descrição |
|---|---|
| **Boletim** | Um único PDF por unidade (escola, regional ou rede), com todas as páginas de indicadores encadernadas em sequência |
| **Relatório** | Um PDF separado por indicador dentro de uma pasta por unidade (escola, regional ou rede) |

### Níveis de agregação

| Nível | Descrição |
|---|---|
| `escola` | Dados filtrados por escola. Inclui páginas de Introdução e Formação de Classe |
| `regional` | Dados agregados por média das escolas da regional |
| `rede` | Dados de toda a rede municipal (usa `IDEB_REDE.xlsx` como fonte de IDEB) |

A combinação **nível × formato** define o que é gerado e onde é salvo:

```
BOLETIM DAS ESCOLAS/          ← boletins
├── REDE/
│   └── boletim_rede.pdf
├── SUBURBIO I/
│   ├── boletim_regional_SUBURBIO_I.pdf
│   ├── boletim_escolar_SUBURBIO_I_EM_Exemplo.pdf
│   └── ...

RELATORIOS SMED/              ← relatórios
├── REDE/
│   ├── IDEB_REDE.pdf
│   ├── Taxa_Rendimento_REDE.pdf
│   └── ...
├── SUBURBIO I/
│   ├── MEDIA_REGIONAL/
│   │   ├── IDEB_SUBURBIO_I.pdf
│   │   └── ...
│   ├── EM Exemplo/
│   │   ├── IDEB_EM_Exemplo.pdf
│   │   ├── Prosa_Padrao_Desempenho_EM_Exemplo.pdf
│   │   └── ...
```

---

## Estrutura do projeto

```
├── main.py              # Ponto de entrada — argumentos CLI
├── config.py            # Caminhos de saída, arquivos de dados, constantes
├── data_loader.py       # Carregamento e normalização unificada dos dados
│
├── generator/
│   ├── boletim.py       # Geração de PDFs no formato boletim
│   ├── relatorio.py     # Geração de PDFs no formato relatório
│   └── _utils.py        # Funções auxiliares compartilhadas
│
├── pages/               # Módulos de renderização por indicador
│   ├── capa.py
│   ├── introducao.py
│   ├── formacao_classe.py
│   ├── ideb.py / ideb_vista.py
│   ├── prosa.py / prosa_proficiencia.py
│   ├── fluencia_leitora.py / fluencia_leitora_vista.py
│   ├── taxa_rendimento.py / taxa_rendimento_vista.py
│   ├── distorcao.py / distorcao_vista.py
│   ├── sabe.py
│   └── metas.py
│
├── data/                # Arquivos de dados (Excel, Parquet)
├── assets/              # Imagens, fontes, QR codes
├── fonts.py             # Registro de fontes customizadas
└── pdf_engine.py        # Header e footer padrão dos PDFs
```

---

## Uso

### Pré-requisitos

```bash
pip install -r requirements.txt
```

### Executar tudo em sequência

```bash
python main.py --all
```

Roda todas as combinações definidas em `config.ALL_MODES`. Por padrão:

```
rede/boletim → rede/relatorio → regional/boletim → regional/relatorio → escola/boletim → escola/relatorio
```

### Executar uma combinação específica

```bash
# Boletim de toda a rede
python main.py --nivel rede --formato boletim

# Relatórios individuais por regional
python main.py --nivel regional --formato relatorio

# Boletins por escola
python main.py --nivel escola --formato boletim
```

### Filtros opcionais

```bash
# Apenas uma regional
python main.py --nivel regional --formato boletim --regional "SUBURBIO I"

# Apenas escolas de uma regional
python main.py --nivel escola --formato relatorio --regional "CENTRO"

# Uma escola específica
python main.py --nivel escola --formato boletim --escola "ESCOLA MUNICIPAL XAVIER MARQUES"
```

---

## Configuração (`config.py`)

### Diretórios de saída

```python
OUTPUT_BOLETIM   = r'G:\Shared drives\...\BOLETIM DAS ESCOLAS'
OUTPUT_RELATORIO = r'G:\Shared drives\...\RELATORIOS SMED'
```

### Modos do `--all`

Para habilitar ou desabilitar combinações no modo `--all`, edite a lista `ALL_MODES`:

```python
ALL_MODES = [
    ('rede',     'boletim'),
    ('rede',     'relatorio'),
    ('regional', 'boletim'),
    ('regional', 'relatorio'),
    ('escola',   'boletim'),
    ('escola',   'relatorio'),
]
```

### Arquivos de dados

Todos os caminhos de entrada ficam em `config.py`. Os arquivos devem estar na pasta `data/`:

| Constante | Arquivo | Uso |
|---|---|---|
| `PROSA_BOLETIM` | `prosa_boletim.parquet` | Padrões de desempenho PROSA |
| `PROSA_ESCOLAS` | `prosa_escolas.parquet` | Referência de escolas e regionais |
| `PROSA_MEDIA` | `prosa_media_alunos.parquet` | Proficiência média dos alunos |
| `IDEB` | `IDEB.xlsx` | IDEB por escola (usado em escola e regional) |
| `IDEB_REDE` | `IDEB_REDE.xlsx` | IDEB agregado da rede municipal |
| `MATRICULAS` | `MATRICULAS.xlsx` | Formação de classe e matrículas |
| `TAXA_RENDIMENTO` | `TAXA_RENDIMENTO.xlsx` | Aprovação, reprovação, abandono |
| `TAXA_DISTORCAO` | `TAXA_DISTORCAO.xlsx` | Distorção idade-série |
| `SABE` | `sabe.xlsx` | Avaliação SABE |
| `METAS` | `METAS.xlsx` | Metas de proficiência por escola/série |
| `FLUENCIA_2025` | `leitura_diag_2025.xlsx` | Fluência Leitora 2025 |
| `FLUENCIA_2026` | `leitura_diag_2026.xlsx` | Fluência Leitora 2026 |

---

## Fluxo de execução

```
main.py (argparse)
    │
    ├── data_loader.load_data(formato)
    │       └── Carrega e normaliza todos os DataFrames
    │           (nomes de escolas, regionais, IDEB, SABE, Metas...)
    │
    └── generator/boletim.py  ou  generator/relatorio.py
            ├── gerar_rede(data)
            ├── gerar_regional(data, regional_filter)
            └── gerar_escola(data, regional_filter, escola_filter)
                    └── pages/*.py  →  ReportLab Canvas  →  PDF
```

No modo `--all`, os dados são carregados **uma vez por formato** (boletim e relatório) e reutilizados para todos os níveis daquele formato, evitando releituras desnecessárias dos arquivos.

---

## Adicionando um novo indicador

1. Crie o módulo em `pages/novo_indicador.py` com a função `render(c, width, height, df)`.
2. Se o relatório precisar de uma versão separada por gráfico, crie também `pages/novo_indicador_vista.py`.
3. Adicione a chamada `novo_indicador.render(...)` em `generator/boletim.py` e/ou `generator/relatorio.py` nos métodos `_render_*` correspondentes.
4. Carregue os dados do novo indicador em `data_loader.py` e inclua a chave no dicionário retornado por `load_data`.
