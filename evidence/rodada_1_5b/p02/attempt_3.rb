require_relative '../lib/remessa_de_cartazes'

RSpec.describe RemessaDeCartazes::Rota do
  describe '.classificar' do
    it 'returns :adiar if pontos_livres < 1' do
      expect(RemessaDeCartazes::Rota.classificar(0, true, 0)).to eq(:adiar)
      expect(RemessaDeCartazes::Rota.classificar(0, false, 0)).to eq(:adiar)
      expect(RemessaDeCartazes::Rota.classificar(0, true, 1)).to eq(:adiar)
      expect(RemessaDeCartazes::Rota.classificar(0, false, 1)).to eq(:adiar)
    end

    it 'returns :protegida if vidro' do
      expect(RemessaDeCartazes::Rota.classificar(0, true, 0)).to eq(:protegida)
      expect(RemessaDeCartazes::Rota.classificar(0, false, 0)).to eq(:protegida)
      expect(RemessaDeCartazes::Rota.classificar(0, true, 1)).to eq(:protegida)
      expect(RemessaDeCartazes::Rota.classificar(0, false, 1)).to eq(:protegida)
    end

    it 'returns :bairro if distancia_km <= 8' do
      expect(RemessaDeCartazes::Rota.classificar(0, true, 0)).to eq(:bairro)
      expect(RemessaDeCartazes::Rota.classificar(0, false, 0)).to eq(:bairro)
      expect(RemessaDeCartazes::Rota.classificar(0, true, 1)).to eq(:bairro)
      expect(RemessaDeCartazes::Rota.classificar(0, false, 1)).to eq(:bairro)
    end

    it 'returns :regional if distancia_km > 8' do
      expect(RemessaDeCartazes::Rota.classificar(9, true, 0)).to eq(:regional)
      expect(RemessaDeCartazes::Rota.classificar(9, false, 0)).to eq(:regional)
      expect(RemessaDeCartazes::Rota.classificar(9, true, 1)).to eq(:regional)
      expect(RemessaDeCartazes::Rota.classificar(9, false, 1)).to eq(:regional)
    end
  end
end
