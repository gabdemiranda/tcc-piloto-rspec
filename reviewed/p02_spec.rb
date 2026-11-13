require_relative '../lib/remessa_de_cartazes'

RSpec.describe RemessaDeCartazes::Rota do
  describe '.classificar' do
    it('defers even protected shipments with no slots') do
      expect(described_class.classificar(8, true, 0)).to eq(:adiar)
    end

    it('protects glass regardless of distance when a slot is free') do
      expect(described_class.classificar(8, true, 1)).to eq(:protegida)
      expect(described_class.classificar(9, true, 1)).to eq(:protegida)
    end

    it('selects the neighborhood route up to and including 8 km') do
      expect(described_class.classificar(7, false, 1)).to eq(:bairro)
      expect(described_class.classificar(8, false, 1)).to eq(:bairro)
    end

    it('selects the regional route above 8 km') do
      expect(described_class.classificar(9, false, 1)).to eq(:regional)
    end
  end
end
