"""Mede cobertura SimpleCov e mutantes reais com limite de tempo por mutante."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from time import monotonic
from sandbox import run_ruby, ROOT

TARGETS=json.loads((ROOT/'targets.json').read_text())
RSPEC=['-rrspec/core','-e','exit RSpec::Core::Runner.run(ARGV)','--','--options','/dev/null',
       '--format','progress','/study/spec/candidate_spec.rb']
def dump(p,o):
    p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')

def measure(key, candidate, work, seed, cap, limit, task_limit, cli=False, reference=None, coverage_only=False):
    target=TARGETS[key]
    args=['/study/tools/mutant_bridge.rb']
    feature=Path(target['source']).stem
    isolation={'TCC_TARGET_SOURCE':target['source']}
    def run(args,work,candidate,**kwargs):
        return run_ruby(args,work,candidate,extra_env=isolation,**kwargs)
    work.mkdir(parents=True,exist_ok=False)
    for i in range(1,4):
        step=run(RSPEC,work,candidate,seconds=limit,coverage=(i==1))
        dump(work/f'rspec_{i}.json',step)
        if step['status']!=0 or not re.search(r'\b[1-9]\d* examples?, 0 failures?',step['log']):
            raise RuntimeError('Suíte de referência não passou no original: '+step['log'])
    cov=json.loads((work/'simplecov.json').read_text())
    if len(cov)!=1 or cov[0]['path']!=target['source']:
        raise RuntimeError('A cobertura não corresponde ao alvo isolado')
    if coverage_only:
        dump(work/'measurement.json',{'coverage':cov[0]})
        print(key,cov[0],flush=True)
        return {'coverage':cov[0]}
    if cli:
        result=run(args+['cli',feature,target['subject']],work,candidate,seconds=min(task_limit,60))
        dump(work/'mutant_cli.json',result)
    t=monotonic()
    res=run(args+['list',feature,target['subject']],work,candidate,seconds=limit)
    dump(work/'mutant_catalog_log.json',res)
    if res['status']!=0: raise RuntimeError(res['log'])
    items=json.loads((work/'catalog.json').read_text())
    eligible=[x for x in items if x['syntax_valid'] and x['kind']=='Evil' and x['source']!=x['original_source']]
    controls=[x for x in items if x['kind']!='Evil']
    picked=sorted(eligible,key=lambda x:hashlib.sha256(f"{seed}:{x['id']}".encode()).hexdigest())[:cap]
    ids=[x['id'] for x in picked]
    catalog={'available':items,'selected_ids':ids,'seed':seed,'cap':cap}
    dump(work/'mutant_manifest.json',catalog)
    if reference and ids!=json.loads(Path(reference).read_text())['selected_ids']:
        raise RuntimeError('Manifestos divergentes entre condições')
    if not eligible or not controls:
        raise RuntimeError('Catálogo vazio ou sem controle')
    def one(x):
        remaining=task_limit-(monotonic()-t)
        if remaining<=0: return {'id':x['id'],'status':'inconclusivo','detail':'teto por método','seconds':0}
        step=run(args+['one',feature,target['subject'],x['id']],work,candidate,seconds=min(limit,remaining))
        if step['timeout'] or step['status']!=0:
            raw={'status':'inconclusivo','detail':'timeout' if step['timeout'] else step['log']}
        else:
            raw=json.loads(step['log'].strip().splitlines()[-1])
        return {'id':x['id'],'seconds':step['seconds'],**raw}
    check=[one(c) for c in controls]
    if any(c['status']!='controle_ok' for c in check):
        dump(work/'mutant_controls.json',check)
        raise RuntimeError('Controle de mutação falhou')
    rows=[one(x) for x in picked]
    counts={k:sum(x['status']==k for x in rows) for k in ('eliminado','sobreviveu','inconclusivo')}
    out={'coverage':cov[0],'generated':len(items),'eligible':len(eligible),
         'selected':len(picked),'counts':counts,'controls':check,'mutant_seconds':monotonic()-t,
         'maximum_per_mutant_seconds':max((r['seconds'] for r in rows),default=0),
         'results':rows}
    dump(work/'measurement.json',out)
    print(key,{k:v for k,v in out.items() if k not in ('results','controls')},flush=True)
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('target')
    p.add_argument('--manifest',type=Path,default=ROOT/'targets.json')
    p.add_argument('--suite',type=Path)
    p.add_argument('--out',type=Path)
    p.add_argument('--reference',type=Path)
    p.add_argument('--coverage-only',action='store_true')
    p.add_argument('--seed',type=int,default=20261113)
    p.add_argument('--max-mutants',type=int,default=40)
    p.add_argument('--timeout',type=int,default=30)
    p.add_argument('--task-limit',type=int,default=1200)
    a=p.parse_args()
    TARGETS.update(json.loads(a.manifest.read_text()))
    if a.target!='pilot' and a.target not in TARGETS: p.error('Alvo ausente do manifesto')
    if min(a.max_mutants,a.timeout,a.task_limit)<1: p.error('Limites devem ser positivos')
    if a.target=='pilot':
        for key in TARGETS:
            measure(key,ROOT/'reviewed'/f'{key}_spec.rb',ROOT/'evidence'/key/'final_metrics',
                    a.seed,a.max_mutants,a.timeout,a.task_limit,cli=True)
    else:
        if a.suite is None or a.out is None: p.error('Informe --suite e --out')
        measure(a.target,a.suite,a.out,a.seed,a.max_mutants,a.timeout,a.task_limit,reference=a.reference,coverage_only=a.coverage_only)

if __name__=='__main__': main()
