# Parecer científico consultivo — revisão cega do manuscrito

**Manuscrito:** *Do Synthetic Personas Predict Real Audience Response? A Headline-Ranking Study with a Generic-Reader Baseline*.

**Data:** 31 de outubro de 2026. **Fonte imutável declarada:** `9c6cfe78d3a50d80c7143c736a28dfecda3c7a33`. **SHA-256 do PDF conferido:** `5a765385cdafd3c5bbc34f1ad22755ad3c83578dff5f76861e93f6445dabd519`.

## Escopo e conclusão do parecer

Li as 13 páginas, o corpo LaTeX, tabelas, variáveis numéricas, apêndice e bibliografia do snapshot. Conferi os 30 hashes de `INPUT_IDENTITY.json`, todos coincidentes, e executei o verificador heurístico de referências: 15 labels referenciados e 25 entradas bibliográficas citadas, sem candidatos a referências quebradas. Inspecionei visualmente as páginas com as principais tabelas suplementares. Não consultei histórico Git, conversas, pareceres, planos ou diretórios de outros trabalhos. Usei apenas fontes primárias públicas para verificar pontos específicos. Não alterei o manuscrito nem executei experimentos com modelos.

O resultado exploratório central é plausível e está descrito com mais cuidado do que a pergunta ampla do título poderia sugerir: nesses registros, o leitor genérico supera o painel fixo em decisões top-1 e lift, e o texto não transforma isso em dano universal causado por personas. Não encontrei contradição aritmética demonstrada nas tabelas primárias nem erro nas fórmulas de gamma, tau-b e crédito esperado de empates. A distinção entre médias marginais e contrastes pareados é importante e foi feita corretamente.

**Recomendo revisão metodológica substancial antes de apresentar o trabalho como contribuição científica plenamente verificável.** Os principais pontos são: a parada adaptativa dos experimentos históricos não foi incorporada à discussão dos filtros; a unidade de reamostragem precisa de justificativa; o controle experimental não está suficientemente especificado no manuscrito; e as comparações entre datasets carecem de definições operacionais essenciais. A reprodução por respostas brutas é uma alegação ainda não verificável com o material recebido. Isso não demonstra que o efeito principal esteja errado.

Este é um parecer científico consultivo produzido por uma ferramenta de IA, não aprovação editorial humana nem gate de produto. “Importante” abaixo indica impacto sobre interpretação ou verificação; não significa fraude ou erro numérico provado.

## Achados principais

### 1. A triagem simultânea não discute a parada adaptativa dos experimentos históricos

**Prioridade:** importante. **Classificação:** omissão metodológica demonstrada; magnitude do impacto não demonstrada.

**Local:** p. 3, seção 5, “Simultaneous winner screen”; `sections/05-setup.tex:27–37`. Trecho: “The nominal bound is approximate and per package, conditional on independent binomial observations and adequate normal approximation.” A frase sobre ausência de parada dependente do resultado em `sections/05-setup.tex:79–80`, p. 4, descreve a nova coleta de LLMs, não o mecanismo de encerramento dos testes históricos.

**Evidência e mecanismo:** a fonte do próprio arquivo relata que editores acompanhavam resultados e decidiam quando interromper o teste. Relata também que podiam iniciar outro teste após insatisfação com os resultados. Isso consta de Methods e Technical Validation de [Matias et al., descrição primária do Upworthy](https://pmc.ncbi.nlm.nih.gov/articles/PMC8329003/). Os testes z usuais não adquirem validade sob parada arbitrária dependente dos resultados apenas por haver observações Bernoulli e aproximação normal. Bonferroni trata a família de comparações especificada; não corrige automaticamente inspeções e decisões de parada anteriores.

**Impacto:** o filtro continua sendo uma regra reprodutível de seleção dos 190 pacotes, mas sua interpretação como triagem com controle nominal aproximado de erro precisa reconhecer mais uma hipótese não assegurada. Excluir a janela de problemas de randomização não elimina esse problema. Não há, no material fornecido, trajetória temporal suficiente para calcular a inflação efetiva ou concluir que algum vencedor específico esteja errado.

**Correção mínima:** explicitar a parada editorial e restringir o papel da triagem a uma regra operacional de separação dos resultados observados, sem insinuar que as condições do controle nominal foram verificadas no arquivo. Se o trabalho quiser sustentar essa propriedade inferencial para os testes históricos, será necessária evidência da regra de parada ou análise válida para o desenho sequencial pertinente. Não é necessário recolher respostas de LLM para corrigir a interpretação.

### 2. O bootstrap assume uma unidade independente cuja adequação não foi documentada

**Prioridade:** importante. **Classificação:** hipótese não verificada; não é demonstração de intervalos incorretos.

**Local:** p. 4, seção 5, “Estimation and denominators”, `sections/05-setup.tex:82–90`; tabelas 1–3, pp. 5–6. Trecho: “Percentile bootstrap CIs use 10,000 package resamples”.

**Evidência e mecanismo:** a descrição primária informa que testes subsequentes recebem novos IDs e podem compartilhar conteúdo com testes anteriores. [Matias et al., Technical Validation](https://pmc.ncbi.nlm.nih.gov/articles/PMC8329003/). Portanto, IDs de experimento distintos não certificam unidades independentes. O manuscrito não informa quantas matérias, famílias de testes ou conteúdos repetidos existem nos 190 pacotes, nem uma verificação de dependência entre pacotes. O problema potencial é entre experimentos; a reamostragem por pacote já preserva corretamente a dependência das variantes dentro de cada experimento.

Há ainda uma definição inferencial a explicitar: se o alvo é estritamente a média destes pacotes e destes resultados fixos, ela é uma descrição conhecida; se os intervalos representam variação entre pacotes de uma população selecionada, é preciso declarar essa população e a hipótese de intercambialidade. Dizer apenas que os intervalos “condition on this cohort” não resolve essa distinção.

**Impacto:** conteúdo repetido pode alterar a ponderação substantiva e a precisão; a extensão disso na amostra é desconhecida. O limite inferior de lift de Gemini fora da janela de risco é apenas 0,001, tornando especialmente relevante não pressupor robustez de sua exclusão de zero a outras unidades de reamostragem.

**Correção mínima:** definir o estimando e relatar um diagnóstico de repetição de conteúdo/famílias entre IDs, com a regra de identificação. Se houver grupos relevantes, mostrar sensibilidade com reamostragem por grupo ou outra abordagem justificada. Se não for possível reconstruir a relação, declarar que os intervalos dependem de independência entre pacotes não verificada. Não se deve afirmar que necessariamente haverá inversão do resultado.

### 3. O prompt do controle central não está reproduzido

**Prioridade:** importante. **Classificação:** lacuna documental demonstrada.

**Local:** p. 11, apêndice A, `sections/09-appendix.tex:8–21`; p. 13, tabela 11. Trecho: “The exact templates, including quotation marks and the first-person, third-person, and baseline variants, are authoritative in the versioned collector.”

**Problema:** o apêndice mostra apenas um template de persona em primeira pessoa. O texto exato do leitor genérico não está no snapshot. Também não se identifica explicitamente, em uma especificação compacta, qual dos templates nomeados constitui cada condição primária. A tabela 11 omite o campo de engajamento noticioso, embora esse campo entre no prompt mostrado. O coletor e o JSON completo apontados pelo texto não estão entre os arquivos recebidos.

**Mecanismo e impacto:** a intervenção comparada é um pacote de instruções. Sem o controle, o leitor não pode verificar se “generic reader” recebe a mesma tarefa, enquadramento temporal/plataforma, papel de mensagem e restrição de saída, ou se há diferenças adicionais de instrução. Isso é essencial mesmo que o estudo corretamente renuncie a atribuir um mecanismo causal à demografia.

**Correção mínima:** acrescentar os dois templates primários integrais, papéis de mensagem e campos efetivamente interpolados, além da identificação inequívoca da condição usada. Disponibilizar os dez registros completos do painel ou incorporar os campos faltantes no apêndice. É uma correção de especificação, sem exigência automática de novo experimento.

### 4. A alegação de reprodução por respostas brutas não pôde ser testada neste material

**Prioridade:** importante para verificabilidade. **Classificação:** limitação de disponibilidade explicitamente declarada; não é contradição nem prova de ausência do bundle.

**Local:** p. 1, resumo, “A raw-replay artifact supports offline reproduction”; p. 9, Data and Code Availability, `main.tex:63–76`; p. 11, apêndice A, `sections/09-appendix.tex:31–39`.

**Problema:** o manuscrito informa honestamente que o bundle está preparado localmente e ainda não está no endereço público. O snapshot desta revisão contém PDF, fontes e exports, mas não o CSV, respostas brutas, plano de requisições, parser, relatórios por pacote ou scripts de análise. Assim, conferir os hashes e a concordância entre tabela e texto não verifica a ligação entre observações e resultados. O comentário “AUTO-GENERATED” de uma tabela também não a demonstra.

**Impacto:** não pude reproduzir seleção dos 190 casos, exclusões, médias, tratamento de empates, interseções válidas, bootstrap ou sensibilidade temporal. A seção de métodos diz ainda que resumos com observações disponíveis são apresentados separadamente (`sections/05-setup.tex:70–71`), mas esses resultados não têm tabela ou referência verificável no manuscrito fornecido.

**Correção mínima:** disponibilizar aos revisores, mesmo que inicialmente de modo privado, o bundle imutável e uma entrada de execução que regenere as tabelas 1–3 e seus denominadores a partir das respostas brutas e outcomes. Indicar seu hash/versão e apontar precisamente a sensibilidade com observações disponíveis. Para divulgação pública da contribuição de reprodutibilidade, completar o depósito e atualizar o endereço. Não afirmo que o bundle local não existe, apenas que esta revisão não o verificou.

### 5. MIND e Reddit não têm outcomes suficientemente definidos; a interpretação entre datasets vai além do que os agregados isolam

**Prioridade:** importante para RQ3. **Classificação:** falta de definição demonstrada e limitações de procedência já declaradas.

**Local:** p. 2, seção 3, `sections/03-framework.tex:2–10`; pp. 6–7, “Dataset comparisons”, `sections/06-results.tex:85–94`, e tabela 5; resumo, `sections/00-abstract.tex:16–18`. Trecho: “The direction of the contrast therefore depends on dataset and metric.”

**Problema:** explica-se o agrupamento aproximado, mas não a taxa observada usada em MIND e Reddit: faltam numerador, denominador, janela de agregação, condições de inclusão e interpretação da unidade de exposição. “Reddit voting” e “outcome-rate range” não especificam se o alvo é proporção de votos positivos, votos normalizados ou outra grandeza. Não é possível julgar o teste de proporções ou o significado do lift sem essa definição. Tampouco são mostrados os CIs de gamma de Reddit mencionados no texto, ou um contraste pareado com incerteza para seus resultados top-1/lift.

O próprio manuscrito reconhece que o subconjunto Reddit tem seleção não documentada e que contagens de draws e IDs avaliados não estão preservados nesses resumos. A linha Upworthy exploratory da tabela 5 apresenta gamma do painel 0,079, enquanto a tabela 4 apresenta 0,084; a divergência é avisada, mas sua origem permanece desconhecida. Assim, a mudança de sinal entre resumos é observável; atribuir a diferença ao dataset é uma interpretação que não separa população, amostra e protocolo.

**Impacto:** a análise suplementar não identifica uma moderação por dataset e não constitui replicação controlada. Isso importa porque o contraste Reddit é elevado ao resumo e à conclusão, e não aparece apenas como registro histórico em apêndice.

**Correção mínima:** definir integralmente cada outcome e a transformação/seleção aplicada; vincular cada linha a uma versão e protocolo. Se isso não puder ser recuperado, apresentar esses números como comparações históricas não reconciliadas e reformular a conclusão para “os resumos disponíveis exibem sinais diferentes, sem permitir atribuir a diferença ao dataset”. Remover de RQ3 qualquer pretensão de teste de heterogeneidade. Uma nova coleta comum em outros datasets seria desejável, mas não é necessária para publicar uma conclusão exploratória mais estreita sobre Upworthy.

### 6. RQ2 não especifica a variável correlacionada com top-1 nem explica o denominador

**Prioridade:** moderada. **Classificação:** ambiguidade e omissão demonstradas; erro de sinal não demonstrado.

**Local:** p. 5, “Signal strength (RQ2)”, `sections/06-results.tex:78–83`; figura 3, p. 7; `variables.tex`, comandos `hThreeN` e `hThreeTopOne`. Trecho: “The association between the supplementary screening statistic and top-1 is Spearman 0.059 … over 1678 packages.”

**Problema:** o filtro suplementar e a figura 3 são definidos por um valor-p, mas o parágrafo não fornece a fórmula da variável usada nessa correlação. Se foi o próprio p, a correlação positiva tem direção diferente de uma correlação com 1−p ou com −log(p). O valor-p também mistura separação, tamanho amostral e número/composição das variantes: não é uma medida pura de força do sinal. Não se explica por que a amostra cai de 1695 para 1678, nem quais braços, falhas ou regras de validade determinam esses 17 casos ausentes.

**Impacto:** o leitor não consegue interpretar o sinal nem reproduzir a estimativa. Além disso, o número de variantes influencia a probabilidade casual de top-1; uma associação não ajustada pode refletir dificuldade combinatória e exposição, não maior previsibilidade do conteúdo.

**Correção mínima:** fornecer definição exata da variável, braço avaliado, tratamento de empates, critério dos 1678 casos e interpretação direcional. Se o agregado não permitir recuperar isso, retirar a estimativa como resposta a RQ2 e mantê-la apenas como resultado não interpretável do relatório antigo. Análise estratificada por número de variantes/exposição seria um refinamento útil, não condição para a comparação primária.

## Melhorias delimitadas, sem exigir novos experimentos

1. **Adicionar referência casual à análise primária.** As tabelas 1–3, pp. 5–6, não mostram distribuição do número de variantes nem top-1 casual do próprio conjunto; os 30,4% da tabela 4 pertencem a outro conjunto. Para vencedor único, a referência é a média de `1/k` dos pacotes utilizados. Para lift, a seleção uniforme tem referência `(média das taxas − mínimo)/(máximo − mínimo)`, que não é universalmente 0,5. Isso ajuda a responder à pergunta de capacidade preditiva absoluta; a falta dessa referência não invalida o contraste pareado baseline versus painel.

2. **Dar mais visibilidade à degeneração do baseline Gemini.** Já está corretamente declarada em `sections/06-results.tex:21–24`, p. 4: 51/188 pacotes têm ranking constante no baseline, contra 3/188 no painel. Os 136 pares válidos representam 72,3% dos pacotes completos. O gap de tau-b é, portanto, condicionado a produzir ordenações utilizáveis nos dois braços. Não substituir indefinidos por zero. Uma breve descrição por número de variantes e desempenho decisório dos pacotes constantes ajudaria a entender o sistema; o top-1 esperado já evita excluí-los da decisão principal.

3. **Completar a descrição da coorte.** `sections/05-setup.tex:2–9`, p. 3, dá o corpus filtrado, mas faltam o fluxo desde o split de origem e distribuições básicas de variantes, impressões e datas. Isso informa a população efetivamente examinada e ajuda a avaliar aproximação normal e dificuldade. A exigência mínima de 3000 impressões não é, sozinha, uma verificação de contagens esperadas suficientes em todos os testes z.

4. **Melhorar legibilidade e foco.** A tabela 6, p. 7, fica muito reduzida; pode ocupar duas colunas ou ir ao apêndice. O conjunto suplementar ocupa espaço considerável apesar das limitações de procedência. Concentrar o argumento principal nas tabelas 1–3 tornaria mais clara a contribuição verificável pretendida. Os nomes dos splits “holdout” e “confirmatory” na tabela 5 devem continuar explicitamente tratados como nomes do arquivo, sem sugerir avaliação prospectiva do presente estudo.

## Verificações que não geraram achados adversos

- As fórmulas de gamma e tau-b da p. 2 distinguem corretamente pares empatados. O crédito esperado `|S_pred ∩ S_real| / |S_pred|` tem interpretação válida como sucesso de uma escolha uniforme entre os máximos previstos. O lift descrito é normalizado pelo intervalo observado; não equivale a ganho comercial ou CTR calibrado, e o texto não afirma essa equivalência.
- Usar todas as comparações não ordenadas na família Bonferroni evita tratar o vencedor observado como se tivesse sido escolhido antes dos dados. A crítica do achado 1 concerne à calibração histórica dos p-valores, não a um erro algébrico nessa família.
- As médias marginais Gemini não precisam subtrair para o gap pareado, pois têm conjuntos válidos distintos. O manuscrito explica isso. Diferenças de uma unidade na última casa em outras tabelas são compatíveis com arredondamento; não as classifiquei como erro.
- Os totais temporais são compatíveis entre si: 42 pacotes selecionados estão na janela de risco; excluir 40 dos 188 completos Gemini deixa 148, e excluir 41 dos 188 GPT deixa 147. Isso é compatível com localizações diferentes das duas exclusões operacionais em cada modelo.
- As duas exclusões operacionais por modelo, isoladamente, não poderiam inverter o sinal da média top-1 de todos os 190 pacotes. Usando os gaps arredondados e o limite de −1 a +1 para a diferença de cada pacote ausente, a média completa ficaria aproximadamente entre +14,5 e +16,6 pontos percentuais para Gemini e entre +18,4 e +20,5 para GPT. É um limite algébrico descritivo, não um novo IC nem prova de ausência de outros vieses.
- A sensibilidade temporal é apresentada como pós-hoc, e a perda de exclusão de zero para tau-b e Spearman Gemini não é ocultada. Não há alegação de equivalência derivada de ICs sobrepostos ou de não significância.
- A alegação de aproximadamente 85% da consistência teste–reteste em Park et al. corresponde ao resumo da [versão v1 especificamente citada](https://arxiv.org/abs/2411.10109v1). A janela temporal usada corresponde à descrição corrigida do [arquivo Upworthy](https://d-nb.info/1343524792/34). Não realizei certificação completa, entrada por entrada, de todos os metadados bibliográficos; o teste automático verifica chaves e referências, não a veracidade de cada citação.

## Limitações já declaradas e pesquisas futuras

A ausência de holdout novo, a seleção por resultados, o painel não representativo, o enquadramento social/2014, a omissão de imagem, a diferença entre intenção e clique, a falta de incerteza entre novas gerações, a heterogeneidade de transporte entre provedores e a possibilidade de contaminação são limitações reais já reconhecidas. Não as apresento como descobertas ocultas nem como evidência de que a média observada esteja errada.

Para ampliar a conclusão, seriam úteis um estudo prospectivo com protocolo e população novos, manipulações separadas de demografia/role-play/enquadramento e repetições independentes de geração. Esses estudos responderiam a perguntas mais ambiciosas; não são a correção mínima necessária para manter uma conclusão exploratória estrita sobre o painel e a coorte atuais.

A sequência mais econômica é: completar a especificação do controle e dos outcomes; ajustar a interpretação da triagem histórica; explicitar o estimando e verificar dependência entre pacotes; disponibilizar o bundle para reprodução; e reduzir as inferências feitas a partir dos agregados suplementares não reconciliados. Essas medidas permitem avaliar a contribuição atual sem transformar a revisão em uma demanda indeterminada por novos experimentos.
