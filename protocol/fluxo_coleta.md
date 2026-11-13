# Coleta principal

1. Receber os 12 alvos, contratos e manifesto do autor independente. Verificar condições técnicas sem consultar as suítes de referência. Congelar commit, ferramentas e hardware.
2. Executar `python3 tools/desenho.py sortear targets_main.json ordem.json` antes de abrir os alvos para coleta. Rodada 1: primeira condição de cada alvo, segundo a ordem sorteada. Rodada 2: segunda condição, com início pelo menos 168 horas após o fim da primeira tarefa do mesmo alvo. Guardar datas UTC.
3. Antes de abrir o contrato: `python3 tools/tempo.py iniciar A01 manual` ou `assistida`. Ao mudar de atividade: `python3 tools/tempo.py marcar <categoria>`. Fechar em até 60 minutos sem as pausas externas: `python3 tools/tempo.py encerrar aceita`, `falha` ou `censurada`.
4. Na condição manual: escrever sem IA e sem ver testes da condição oposta. Na assistida: preservar a geração inicial, até dois reparos e os ajustes do avaliador. Usar o mesmo contrato nas duas condições.
5. Congelar as suítes aceitas; executar cobertura em cada condição. Aplicar mutação apenas aos seis alvos sorteados, reutilizando o manifesto por alvo e registrando inconclusivos. Preservar saídas e diferenças. Não retornar métricas de mutação ao modelo.
6. Executar `python3 tools/desenho.py auditar ordem.json tempos auditoria.json`. Apurar dados por par e preservar as falhas. Publicar apenas os dados e artefatos cuja divulgação foi autorizada.

Não misturar os ensaios de bancada com a coleta principal. Um intervalo inferior a sete dias entre as condições do mesmo alvo deve ser tratado como desvio de protocolo.
