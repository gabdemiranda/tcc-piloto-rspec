require_relative '../lib/triagem_de_acervo'

RSpec.describe TriagemDeAcervo::JanelaDeAclimatacao do
  describe '.minutos' do
    it('returns zero for no boxes even in high humidity') do
      expect(described_class.minutos(0, 70)).to eq(0)
    end

    it('computes the wait below the humidity boundary') do
      expect(described_class.minutos(1, 69)).to eq(16)
      expect(described_class.minutos(2, 69)).to eq(20)
    end

    it('adds the surcharge from the boundary onwards') do
      expect(described_class.minutos(1, 70)).to eq(25)
      expect(described_class.minutos(2, 71)).to eq(29)
    end

    it('caps only values above the limit') do
      expect(described_class.minutos(6, 70)).to eq(45)
      expect(described_class.minutos(7, 70)).to eq(45)
    end
  end
end
