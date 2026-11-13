require 'simplecov'
require 'json'
SimpleCov.coverage_dir('/work/coverage')
SimpleCov.enable_coverage(:branch)
SimpleCov.command_name('piloto')
SimpleCov.root('/study')
SimpleCov.add_filter { |source_file| !source_file.filename.start_with?('/study/lib/') }

class StudyCoverageFormatter
  def format(result)
    report = result.files.map do |file|
      {
        path: file.filename.delete_prefix('/study/'),
        lines_hit: file.covered_lines.size,
        lines_total: file.lines_of_code,
        branches_hit: file.covered_branches.size,
        branches_total: file.total_branches.size
      }
    end
    File.write('/work/simplecov.json', JSON.pretty_generate(report))
    report.each do |file|
      puts "SimpleCov #{file[:path]}: linhas #{file[:lines_hit]}/#{file[:lines_total]}; " \
           "ramificações #{file[:branches_hit]}/#{file[:branches_total]}"
    end
  end
end

SimpleCov.formatter = StudyCoverageFormatter
SimpleCov.start
