# Orientação para autoria independente dos alvos principais

Prepare 12 classes de serviço Ruby inéditas e suas especificações, com um método público por arquivo. Os dois métodos do piloto não entram na amostra. Use Ruby puro e operações determinísticas, sem rede, banco de dados, sistema de arquivos, relógio ou aleatoriedade. O projeto não depende de Rails. Mantenha o código e os contratos privados até o congelamento das suítes do estudo.

Use estes temas como ponto de partida. Defina de forma independente nomes, entradas, valores exatos, prioridades e casos de borda. Os temas não são os contratos a serem entregues a quem escreverá os testes.

| IDs | Categoria | Temas de regras |
|---|---|---|
| A01 a A04 | Validação | Admissão de cadastro; admissibilidade de reserva; consistência de intervalos; restrições de lote |
| A05 a A08 | Cálculo | Tarifa com teto; pontuação com bônus; rateio com arredondamento; custo com faixa de desconto |
| A09 a A12 | Decisão | Prioridade de atendimento; elegibilidade para remessa; classificação de categoria; decisão sobre substituição |

Para cada alvo, entregue: (1) classe e método Ruby em um arquivo de `lib/`; (2) contrato em Markdown com assinatura, domínio, retorno, regras, prioridades e tratamento de entradas inválidas; (3) categoria predominante; e (4) testes privados de referência, em pacote separado. Os contratos devem permitir que o avaliador deduza expectativas sem executar o método para copiá-las. Evite depender de sintaxe Ruby posterior à 2.5, pois o analisador do Mutant 0.8.24 tem esse limite. Confirme com os testes de referência que o comportamento coincide com cada contrato.

Gere um manifesto JSON no formato abaixo e faça um commit antes de entregar o material ao avaliador. Preserve as suítes de referência fora do repositório de trabalho e dos prompts. Para garantir independência, não deixe o avaliador escrever, revisar previamente ou alterar os alvos depois do congelamento. Se houver incompatibilidade técnica, documente e corrija antes da coleta.

```json
{
  "A01": {
    "source": "lib/a01.rb",
    "specification": "specifications/a01.md",
    "subject": "ServicoA01.validar",
    "category": "validacao"
  }
}
```

O avaliador recebe apenas o código-alvo e o contrato correspondentes no início de cada tarefa. A autoria e a data do congelamento devem ser registradas. Qualquer divulgação posterior depende da concordância de quem contribuiu com o código.
