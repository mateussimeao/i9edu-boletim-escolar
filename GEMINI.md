# Documentação de Contexto do Projeto SMED (Relatórios Automáticos)

Este documento centraliza as informações arquiteturais, lógicas de funcionamento, estrutura e regras gerais do projeto `relatorios-auto` para acelerar o entendimento e onboarding de agentes IAs (como o próprio Gemini).

## 1. Visão Geral
Este é um sistema desenvolvido em **Python** que gera relatórios escolares em formato PDF. Ele atende a dois fluxos principais:
*   **Pipeline SMED (Original)**: Relatórios individuais por escola focados em Formação de Classe e Distorção (`main.py`).
*   **Painel Educação à Vista**: Relatórios modulares por indicadores (IDEB, Prosa, Fluência, Taxa de Rendimento, Distorção) gerados em três níveis:
    *   **Escola Individual**: `main_vista.py`.
    *   **Média Regional**: `main_regional_vista.py` (Agregado por Regional).
    *   **Média Rede**: `main_rede_vista.py` (Agregado total da rede municipal).
*   **Novos Scripts de Geração**:
    *   `main_smed_formacao_classe.py`: Gera relatórios de Formação de Classe para o SMED.
    *   `main_smed_distorcao.py`: Gera relatórios de Distorção para o SMED.
    *   `main_smed_geral.py`: Orquestra a execução dos relatórios de Formação de Classe e Distorção para o SMED.

## 2. Ambiente e Instalação
* **Gerenciador de Ambiente**: `uv`.
* **Virtual Environment**: Existe a pasta `.venv` na raiz. Os scripts e módulos devem ser executados através desse `.venv` (`.venv\Scripts\python.exe` no Windows ou ativando o terminal).
* **Dependências Principais**: `pandas`, `matplotlib`, `reportlab`, `openpyxl`, `pyarrow` (para arquivos `.parquet`).

## 3. Arquitetura e Estrutura de Diretórios
* `main.py`: Ponto de entrada do fluxo SMED original.
* `main_vista.py`: Ponto de entrada para relatórios individuais do painel Educação à Vista.
* `main_regional_vista.py`: Gera médias regionais agregadas, salvando em `[Regional]/MEDIA_REGIONAL/`.
* `main_rede_vista.py`: Gera a média total da rede, salvando na pasta `REDE/`.
* `generate_reports.py`: Versão "antiga/monolítica" que antes gerava tudo num arquivo só. Atualmente a arquitetura adotada é a **Modular** via a pasta `pages/`.
* `pdf_engine.py`: Funções utilitárias reaproveitáveis do ReportLab (header, footer, QR Codes dinâmicos).
* `fonts.py`: Módulo responsável pelo registro e injeção do pacote de fontes customizadas (Montserrat, Open Sans, Roboto). Define constantes (`FONT_TITULO`, etc).
* `data/`: Diretório que engloba as bases de dados nos formatos `.parquet` e `.xlsx`. (Ex: `IDEB.xlsx`, `MATRICULAS.xlsx`, `TAXA_RENDIMENTO.xlsx`, `TAXA_DISTORCAO.xlsx`, `fluencia_leitora.xlsx`).
* `assets/`: Arquivos de imagens estáticas, como logos e capas (ex: `capa_background.png`, `logo_escola.png`, cabeçalhos customizados).
* `pages/`: Onde cada página temática do PDF mora. 
  * Estrutura Vista: Arquivos com sufixo `_vista.py` são otimizados para o novo painel (ex: `fluencia_leitora_vista.py`).
  * Toda classe de página exporta uma função padrão `render(c, width, height, df_respectivo_modulo)`. 
* `relatorios/`: Pasta output de geração, que subdivide as escolas nas sub-pastas das respectivas **Regionais**.

## 4. Padrões de Layout e Design
* Cada script em `pages/` deve obrigatoriamente invocar `draw_header` e, no final, invocar `draw_footer` antes do `c.showPage()`.
* **Gráficos**: São gerados através do `matplotlib` salvos em `tmp_nome.png`, impressos via `c.drawImage` do canvas e obrigatoriamente **apagados do disco** em seguida com `os.remove`.
* **Cores**: A aplicação usa tons pastéis bem definidos para componentes específicos:
  * Verde, Amarelo, Laranja, Vermelho são usados em KPIs como Condicionais dependendo de aprovações/reprovações ou notas de distorção.
  * O "Tema" central da Secretária usa variações de azul (`#056cad`, `#1565C0`, etc).
* As fontes devem **sempre** ser puxadas do `fonts.py` para garantir a customização (que foi requisitada pelo usuário no histórico do projeto).
* **Posicionamento**: Como o Reportlab funciona com coordenadas matemáticas XY partindo do Bottom-Left (0,0), normalmente a construção ocorre descendo subtraindo alturas e centímetros: `y = height - X*cm`.

## 5. Lógica de Componentes (Recorrentes)
* **Gráficos com Labels (Bar_label)**: Os gráficos frequentemente requerem exibição do valor (`%` ou absoluto) da barra em cima dela (se vertical) ou ao lado (se horizontal) usando `.bar_label(container, labels)`. Fontes de legendas de gráficos sempre pequenas (`fontsize=8` a `10`) e em negrito.
* **Tabelas de KPI**: Tabelas não usam a abstração Table do Reportlab geralmente; as funções desenham linhas (usando divisórias verticais `c.line(x, bottom_y, x, top_y)`) e desenham Strings centralizadas. O background costuma ser limpo, sem gridlines horizontais (conforme o pedido expresso para paineis limpos).
* **Estrutura "Anos Iniciais e Anos Finais"**: Muitos dados são particionados por essas duas Etapas Escolares. Se um dataframe para àquela Etapa estiver vazio, a página é abortada (`if df_etapa.empty: continue`).
* **Lógica de Agregação (Médias)**: Ao gerar relatórios Regionais ou de Rede, as porcentagens são recalculadas a partir das quantidades absolutas (`QTD_ALUNOS` ou `QTD`). **Regra**: Somar as quantidades e dividir pelo total do grupo para garantir que a média seja ponderada e não ultrapasse 100%.

## 6. Fluxo de Execução Simplificado (Para Adicionar Novas Funcionalidades)
Sempre que uma nova métrica for incluída, siga estes passos:
1. Inspecione o formato de dados correspondente em `.xlsx` ou `.parquet` (crie scripts provisórios tipo `inspect_xxx.py` para não estourar tokens da IA).
2. Crie um arquivo em `pages/nova_medida.py` com a assinatura `render(c, width, height, df_nova_medida_escola)`.
3. Adicione lógica de carregamento de base (read_excel) dentro do `main.py` antes do loop de escolas (`escolas = df...`).
4. Dentro do loop de escolas em `main.py`, filtre os dados referentes exatos daquela escola (ex: `df_nova_medida_escola = df_nova_medida[df_nova_medida['ESCOLA'] == escola]`).
5. Repasse como argumento ao `generate_school_report()` e inclua a chamada `nova_medida.render(c, w, h, df_escola)` na lista sequencial de páginas.

## 7. Padronização de Dados e Regionais
* **Unificação**: "CIDADE BAIXA" e "LIBERDADE" são unificadas como **CIDADE BAIXA LIBERDADE** em todos os fluxos.
* **Merges**: Bases que não possuem a coluna `REGIONAL` devem fazer merge com `df_escolas` via coluna `ESCOLA` para herdar o vínculo geográfico.
* **Filtros**: No `main_vista.py`, a geração de um indicador deve ser pulada (`if df.empty: continue`) caso a escola não possua dados para aquele módulo específico.
