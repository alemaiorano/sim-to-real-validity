# DoesItStand — rodada FINAL e adjudicação

Alvo25a8b2c47f0090852abbc9ad23412e91ea3bffaf; PDFSHA256
03d0a905d62521fd32a70d796556562df91790f6a4bd2ec2e70bb468c8127c02.
Toolb3e35a36218697fe32cc0bb82c5d8165e9b924d3, review-promptv3, manuscriptv2.
Saída nativa completaexit0: WeakAccept, overall6/10, confiança4/5. Nenhum reviewer ausente.
A primeira rodada é preservada; a segunda foi necessária porque o exemplo JSON doPDF mudou
para glyphs literais, não para buscar uma nota melhor. Ambos os pareceres permanecem intactos.
Nenhuma alteração de paper/código depois desta rodada final.

## Achados estatísticos readjudicados

- O review fala em52pacotes constantes no baselineGemini. O artefato primário mostra51no
baseline e3no painel, com interseção2: união52, portanto188-52=136pares válidos. Isso já é
explicitado em06-results e nas tabelas. O n136não é um erro aritmético ou52constantes baseline.
- Condicionar a ranks definidos pode selecionar uma população diferente; é limitação real,
explicitada. A recomendação de imputar0não corrige Kendalltau-b: para um vetor constante,
seu denominador é0e a correlação é indefinida. Imputar0define outro estimando e não foi feito.
Top1e lift já abrangem188pacotes completos, com crédito esperado por empates. Não se vende o
contraste de136pares como estimativa sobre188ranks definidos.
- A assimetria Azure n3/Gemini single-choice é real e descrita. Dentro de cada modelo, os dois
braços usam o mesmo número de scores e o mesmo transporte. O paper diz que não iguala tokens /
custo entre provedores, não presume independência de choices e não identifica efeito causal
da família. O review extrapola ao chamar isso de controle de compute ou ao supor dependência
autoregressiva entre completions sem evidência. Ablation de transporte seria novo experimento.
- Variações de prompts, tamanho do painel e personas são extensões legítimas. O artigo restringe
seu resultado ao painel/coorte/protocolo e não afirma dano universal nem mecanismo isolado.
Não houve nova coleta científica para responder a sugestões de ampliação.

## Transparência/reprodução

Alega-se ausência de temperatura/seeds/link/statement. OPDFtem temperatura0.8em05-setup,
seeds e condições de request em05/09, e seçãoDataandCodeAvailability com URLGitHub emmain.tex.
Os prompts exatos e requests estão no código e bundle. O exemplo do apêndice é ilustrativo.
Top-p/penalties não foram enviados; REPLICATIONexplicita isso sem inventar defaults numéricos.
O bundle desta versão ainda é local preparado para depósito: falta de depósito público atual
é limitação real, declarada, e não foi resolvida fingindo publicação. IDs históricos ausentes
continuam ausentes; os novos resultados retêm IDs, raws e denominadores.

## Sinais do pacote que não são prova sobre o paper

Guard com encodingONapontou6itenshigh emfigures/protocol.tex, todos nas opçõesTikZ
>=Stealth e\draw[->]. São comandos para gerar setas, não texto onde '>'seria impresso como'¿'.
Estrutura, imagens, logs e policy signals não têm outros apontamentos. Não se alterou sintaxeTikZ
válida nem se editou o relatório para fabricar PASS. A checagem estrutural nativa anterior sem
scanner tinha passado; oPDFfoi inspecionado e o JSON literal atual é confirmado por extração e
rebuild byte a byte. O guard final bruto permanecepassed=false/exit1por esses6falsos positivos;
o e2e nativo termina0porque esse guard é reportado separadamente.

Claim checkerfinal:3supported,1unsupported,0uncertain sobre4paráfrases. A unsupported é a
paráfrase de dependência de dataset/métrica/janela. O código do pacote, em
integrity/claim_verification.py, passa somente title/summary/keywords e3resumos externos ao juiz:
não passa o texto completo, tabelas, resultados numéricos ou acknowledged_limitations. Logo,
ausência de suporte nesse resumo não é refutação dos dados do artigo. O próprio juiz usa como
'evidence_quote'uma frase de resumo que não é citação literal doPDF. Nenhuma dessas paráfrases
substitui as claims reais. O artigo relata diferenças de estimativa/ICe direção em algumas
comparações; não declara interação formal entre coortes/modelos com base em significância.

Resolver:23/25,author_mismatch0. Pew eNIST, os2não resolvidos, foram conferidos nas fontes
primárias e correspondem às referências:
https://www.pewresearch.org/journalism/2013/11/14/news-use-across-social-media-platforms/
https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm
LOLApossibly_fused é causada por um IDarXiv semversão e seu v3no mesmo registro; é uma obra,
não fusão. Nenhuma referência foi removida ou adulterada para acomodar heurísticas.

Decisão de implementação: nenhuma nova divergência de fórmula ou valor foi demonstrada pelo
review. O readerCSVreal e o defeito de glyphs foram reparados antes desta rodada. Os sinais
nativos e seus limites são preservados; WeakAcceptadvisory não é aprovação editorial humana.
