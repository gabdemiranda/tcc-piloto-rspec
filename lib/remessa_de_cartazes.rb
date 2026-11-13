module RemessaDeCartazes
  class Rota
    def self.classificar(distancia_km, vidro, pontos_livres)
      return :adiar if pontos_livres < 1
      return :protegida if vidro
      return :bairro if distancia_km <= 8
      :regional
    end
  end
end
