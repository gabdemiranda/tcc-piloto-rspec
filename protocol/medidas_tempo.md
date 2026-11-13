# Como interpretar os tempos

Os tempos de máquina das rodadas piloto estão em `evidence/rodada_1_5b/pilot.json` e `evidence/confirmacao_7b/pilot.json`. Cada tentativa registra tempo de carregamento, inferência, sintaxe e RSpec. `automated_seconds` mede a tarefa automatizada por alvo, incluindo invocação do executor e validações efetuadas pela versão do script usada no piloto. O hash dos pesos foi verificado antes da tarefa, fora desse tempo.

Os CSV e JSON com prefixo `ensaio_assistida` nesta pasta são um teste de funcionamento do cronômetro, não medições de esforço humano. As suítes corrigidas para validar SimpleCov e Mutant são ajustes de bancada produzidos durante a preparação deste material; não foram cronometradas como revisão humana. O experimento principal deverá registrar o tempo humano real do avaliador.

Em cada pasta de medição, `mutant_cli.json`, quando presente, guarda a demonstração completa da CLI histórica, cuja contagem inclui o controle. O escore comparável é calculado a partir de `measurement.json`, sem controles e com o mesmo manifesto. `mutant_seconds` inclui catálogo, controle e execuções isoladas; cada tempo por mutante inclui a inicialização do processo. As coberturas são do arquivo isolado que contém um único método.
