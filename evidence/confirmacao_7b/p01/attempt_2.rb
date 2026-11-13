require_relative '../lib/triagem_de_acervo'

RSpec.describe TriagemDeAcervo::JanelaDeAclimatacao do
  describe '.minutos' do
    it 'returns 0 with 0 boxes regardless of humidity' do
      expect(described_class.minutos(0, 0)).to eq(0)
      expect(described_class.minutos(0, 100)).to eq(0)
    end

    it 'returns 12 minutes with 1 box and 0% humidity' do
      expect(described_class.minutos(1, 0)).to eq(12)
    end

    it 'returns 16 minutes with 1 box and 70% humidity' do
      expect(described_class.minutos(1, 70)).to eq(16)
    end

    it 'returns 20 minutes with 1 box and 100% humidity' do
      expect(described_class.minutos(1, 100)).to eq(20)
    end

    it 'returns 24 minutes with 2 boxes and 0% humidity' do
      expect(described_class.minutos(2, 0)).to eq(24)
    end

    it 'returns 28 minutes with 2 boxes and 70% humidity' do
      expect(described_class.minutos(2, 70)).to eq(28)
    end

    it 'returns 32 minutes with 2 boxes and 100% humidity' do
      expect(described_class.minutos(2, 100)).to eq(32)
    end

    it 'returns 45 minutes with 11 boxes and 0% humidity' do
      expect(described_class.minutos(11, 0)).to eq(45)
    end

    it 'returns 45 minutes with 11 boxes and 70% humidity' do
      expect(described_class.minutos(11, 70)).to eq(45)
    end

    it 'returns 45 minutes with 11 boxes and 100% humidity' do
      expect(described_class.minutos(11, 100)).to eq(45)
    end
  end
end
