# Product

## Register

product

## Users

Three groups, one platform:

- **Analistas técnicos (Corregedoria PRODESP)** — Sidney, Renato e equipe. Usam o workspace completo: conectam bases (Excel, Oracle, MySQL, Postgres, etc.), montam gráficos, navegam Data Threads para comparar caminhos de análise. Contexto: apuração e acompanhamento de processos administrativos, com dados sensíveis.
- **Usuários leigos internos** — servidores da Corregedoria sem conhecimento técnico. Entram por `/simples`: perguntam em linguagem natural, leem uma resposta em texto. Nunca tocam em gráfico, conector ou Data Thread.
- **Futuros clientes externos** — organizações fora da Corregedoria, cada uma com suas próprias bases de dados, em regime multi-tenant.

## Product Purpose

Cortex Data (fork evoluído do Microsoft Data Formulator, sob o produto guarda-chuva "Cortex Binário") existe para tirar a fricção entre "ter uma pergunta" e "ter uma resposta a partir de dados reais" — para dois níveis de usuário ao mesmo tempo, sem forçar o leigo a aprender a ferramenta do analista nem empobrecer a ferramenta do analista para acomodar o leigo. Sucesso é: um analista técnico monta uma investigação de dados sem sair do fluxo (Data Thread) tão rápido quanto hoje ou mais; um usuário leigo faz uma pergunta em `/simples` e recebe uma resposta clara sem precisar entender o que há por trás.

## Brand Personality

Técnico e preciso, acessível e claro. A marca não decora — ela reduz a distância entre pergunta e resposta. Tom de instrumento de precisão (como um terminal profissional de investigação), nunca de "app de produtividade divertido". Onde o /simples fala com o leigo, a clareza vem de reduzir a interface, não de infantilizar a linguagem.

## Anti-references

Explicitamente NÃO deve parecer um SaaS genérico de IA de 2025/26: nada de cards com gradiente roxo/azul, "hero metric" (número grande + label pequeno + gradiente), eyebrows em caixa alta acima de cada seção, grids de cards idênticos, glassmorphism decorativo, gradient text. Esses são os "tells" que fazem uma interface parecer gerada por IA — e são justamente o padrão que o /simples já rompeu ao adotar um tema escuro carbono inspirado na ferramenta Oracle ANA em vez do dashboard-SaaS-claro genérico.

## Design Principles

1. **Duas superfícies, uma marca.** O workspace técnico e o `/simples` servem públicos opostos (complexidade total vs. zero complexidade) mas devem ser inconfundivelmente do mesmo produto — mesma paleta-base, mesma tipografia, mesmo logo, densidade de informação diferente.
2. **Precisão sem intimidação.** Dados de investigação são sensíveis; a interface nunca compete com a informação por atenção. Decoração é sempre subordinada à legibilidade do dado.
3. **Multi-tenant desde o desenho.** Cada cliente futuro precisa poder "morar" na interface sem parecer um template reaproveitado — tokens de tema devem suportar variação de marca sem redesenho.
4. **Recusar o clichê de SaaS-IA.** Qualquer elemento da lista de anti-referências é motivo de reescrita, não de ajuste fino.
5. **Acessibilidade é funcionalidade central.** Contraste alto e tipografia legível não são um checkbox de compliance — são o que faz um usuário leigo conseguir usar `/simples` sem ajuda.

## Accessibility & Inclusion

Prioridade explícita: baixa visão / alto contraste, especialmente na superfície `/simples`, onde o público inclui servidores não-técnicos que podem não ter familiaridade com interfaces densas. Corpo de texto ≥4.5:1 de contraste (texto grande ≥3:1), nunca depender só de cor para transmitir estado, tipografia com tamanho generoso no modo simples. Fora disso, seguir WCAG AA como piso geral do workspace técnico.
