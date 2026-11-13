# Piloto de geração assistida de testes RSpec

Piloto técnico executado em 13/11/2026, separado dos 12 métodos do estudo principal. Os alvos P01 e P02 estão em `lib/` e os contratos em `specifications/`. `reviewed/` contém as correções de bancada. `evidence/` preserva prompts, saídas brutas, testes extraídos, resultados, coberturas, manifestos e tempos. `protocol/` traz o roteiro da coleta, a ficha de revisão e o pedido de autoria independente.

## Resultados observados

A primeira rodada, com 1,5B, não produziu uma suíte aprovada automaticamente para nenhum dos dois alvos, mesmo após dois reparos. As suítes corrigidas em bancada eliminaram 40/40 mutantes em cada alvo. Na confirmação com 7B, P02 passou sem correção, atingiu 7/7 linhas e 6/6 ramificações e eliminou 39/40 mutantes em 19,11 s. P01 continuou com falhas. A rodada de mutação das suítes corrigidas levou 19,86 s em P01 e 18,65 s em P02. Esses resultados são do piloto técnico, sem comparação de esforço humano.

O histórico mantém os dois commits de congelamento: `db27205` para os alvos e a configuração inicial, e `e098739` para a confirmação com 7B. Somente os dois métodos do piloto e seus artefatos são publicados neste repositório.

## Configuração congelada

- Qwen2.5-Coder-7B-Instruct, GGUF Q4_K_M, inferência local em CPU; SHA-256 em `model.json`.
- node-llama-cpp 3.22.3, llama.cpp v0.9.0, Node 24.22.1; quatro threads, temperatura 0, semente 20261113, contexto de 4.096, até 700 tokens por resposta, até dois reparos.
- Ruby 3.3.8, RSpec Core 3.13.0, SimpleCov 0.22.0, Mutant e mutant-rspec 0.8.24.
- Linux x86-64; o piloto usou Debian 13. Para executar testes gerados, são necessários bubblewrap com namespaces de usuário e libseccomp 2. O executor não roda código gerado se o isolamento falhar.
- O modelo de 1,5B é a configuração da primeira rodada e está registrado em `config_inicial/`. O 7B é o modelo selecionado para a coleta.

## Preparar e executar

Instale Ruby 3.3 e Node em Linux. Use Ruby em `/usr/bin` ou configure `TCC_RUBY_ROOT` para uma árvore Debian extraída com Ruby 3.3. Instale as gems em um diretório local e deixe o restante do sistema fora do contexto dos testes. A gem antiga Morpher 0.2.6 é obtida do código-fonte publicado na tag `v0.2.6` de https://github.com/mbj/morpher. Ela pode ser construída a partir de um checkout da tag com `gem build morpher.gemspec`; o gemspec lê a lista de arquivos do Git. Instale essa gem primeiro. A origem, as versões e os hashes do piloto estão em `protocol/dependencias.txt`.

```bash
npm ci --ignore-scripts
export TCC_GEM_HOME="$PWD/gems"
export GEM_HOME="$TCC_GEM_HOME"
gem install --local /caminho/morpher-0.2.6.gem --no-document
gem install 'rspec:3.13.0' 'rspec-core:3.13.0' 'rspec-support:3.13.1' 'simplecov:0.22.0' 'mutant:0.8.24' 'mutant-rspec:0.8.24' --no-document
python3 tools/model_download.py pesos/qwen-7b.gguf
export TCC_MODEL="$PWD/pesos/qwen-7b.gguf"
python3 tools/pilot.py --out novas_medicoes/geracao
python3 tools/measure.py p01 --suite reviewed/p01_spec.rb --out novas_medicoes/p01
python3 tools/measure.py p02 --suite reviewed/p02_spec.rb --out novas_medicoes/p02
```

Em Ruby instalado em outro caminho sob `/usr`, defina `TCC_RUBY_BIN`. Os testes são executados apenas sobre o arquivo do alvo e em um ambiente limpo, sem sockets. Não tente abrir nem executar as saídas brutas fora do isolamento. Não misture o código piloto com os 12 alvos principais.

Para a coleta principal, siga `protocol/fluxo_coleta.md`. Com o manifesto principal, use `tools/pilot.py --manifest targets_main.json --target A01 --out <pasta>` na condição assistida e `tools/measure.py A01 --manifest targets_main.json --suite <spec> --out <pasta>` nos alvos sorteados. Para os demais, use a opção `--coverage-only`. Para a segunda condição, forneça `--reference <mutant_manifest.json da primeira condição>`. As pastas de saída devem ser novas.

## Licenças

Código original do pacote sob MIT. Mutant, mutant-rspec e Morpher usados no piloto possuem licença MIT nas versões indicadas. Pesos e bibliotecas de terceiros não são distribuídos neste pacote.
