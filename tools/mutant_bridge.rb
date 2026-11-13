# Seleciona mutantes do próprio Mutant e executa cada caso separadamente.
require 'mutant'
require 'mutant/integration/rspec'
require 'json'
require 'digest'

mode, feature, subject, wanted = ARGV
args = ['--use', 'rspec', '-I', '/study/lib', '-r', feature, '-j', '1', subject]
if mode == 'cli'
  exit(Mutant::CLI.run(args) ? 0 : 1)
end
env = Mutant::Env::Bootstrap.call(Mutant::CLI.call(args))
abort 'Expected exactly one subject' unless env.subjects.size == 1
abort 'No associated RSpec examples' if env.selections.values.flatten.empty?
index = {}
env.mutations.each do |m|
  id = Digest::SHA256.hexdigest([m.class.name, subject, m.source].join("\0"))
  index[id] ||= m
end
if mode == 'list'
  manifest = index.map do |id, m|
    { id: id, native_id: m.identification, kind: m.class.name.split('::').last,
      source: m.source, original_source: m.original_source,
      syntax_valid: (begin; RubyVM::InstructionSequence.compile(m.monkeypatch); true; rescue SyntaxError; false; end) }
  end
  File.write("/work/catalog.json", JSON.generate(manifest))
  puts "catalogued #{manifest.length} candidates"
elsif mode == 'one'
  m = index.fetch(wanted)
  result = env.kill(m)
  isolated = result.isolation_result
  if isolated.success?
    status = if m.is_a?(Mutant::Mutation::Evil)
               isolated.value.passed ? 'sobreviveu' : 'eliminado'
             else
               isolated.value.passed ? 'controle_ok' : 'controle_falhou'
             end
    puts JSON.generate(status: status, seconds_internal: result.runtime)
  else
    puts JSON.generate(status: 'inconclusivo', seconds_internal: result.runtime,
                       detail: isolated.class.name)
  end
else
  abort 'Invalid mode'
end
