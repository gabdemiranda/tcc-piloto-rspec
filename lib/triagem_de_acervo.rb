module TriagemDeAcervo
  class JanelaDeAclimatacao
    def self.minutos(caixas, umidade)
      return 0 if caixas < 1
      espera = 12 + caixas * 4
      espera += 9 if umidade >= 70
      [espera, 45].min
    end
  end
end
