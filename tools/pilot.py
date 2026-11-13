"""Geração real, até dois reparos e medição automatizada do piloto."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from time import monotonic
from datetime import datetime, timezone
from sandbox import run_ruby

ROOT=Path(__file__).resolve().parents[1]
TARGETS=json.loads((ROOT/'targets.json').read_text())
MODEL=json.loads((ROOT/'model.json').read_text())
RSPEC=['-rrspec/core','-e','exit RSpec::Core::Runner.run(ARGV)','--','--options','/dev/null',
       '--format','progress','/study/spec/candidate_spec.rb']
def dump(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def extract(text):
    fenced=re.findall(r'```(?:ruby|rb)?[ \t]*\n(.*?)```',text,re.S|re.I)
    return (fenced[0] if fenced else text).strip()+'\n'

def initial(info):
    path=(ROOT/info['source'])
    return (
        "Write one RSpec 3 spec file for exactly the Ruby method below. Use require_relative "
        f"'../{info['source'].removesuffix('.rb')}'. Do not use mocks, external libraries, "
        "filesystem, network, time, random inputs or alter the class. Use describe/it and "
        "explicit expect(...).to eq(...). Test every rule, priority and relevant boundary with "
        "representative literal inputs. Return the full Ruby file only.\n\n"
        f"Contract (Portuguese):\n{(ROOT/info['specification']).read_text()}\nRuby source:\n{path.read_text()}"
    )

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=ROOT/'targets.json')
    parser.add_argument('--target')
    parser.add_argument('--out',type=Path,default=ROOT/'evidence')
    opts=parser.parse_args()
    targets=json.loads(opts.manifest.read_text())
    if opts.target:
        if opts.target not in targets: parser.error('Alvo ausente do manifesto')
        targets={opts.target:targets[opts.target]}
    model=Path(os.environ['TCC_MODEL']).resolve()
    with model.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
    if digest!=MODEL['sha256']: raise SystemExit('SHA-256 do modelo divergente')
    evidence=opts.out.resolve()
    evidence.mkdir(parents=True,exist_ok=False)
    results={}
    for key,info in targets.items():
        start=datetime.now(timezone.utc).isoformat()
        t=monotonic()
        out=evidence/key
        out.mkdir()
        attempts=[]
        context=initial(info)
        prompt=context
        for attempt in range(1,MODEL['max_repairs']+2):
            stem=out/f'attempt_{attempt}'
            ask, reply, candidate=[stem.with_suffix(ext) for ext in ('.prompt.txt','.raw.txt','.rb')]
            ask.write_text(prompt)
            try:
                step=subprocess.run(['node',str(ROOT/'tools/infer.mjs'),str(model),str(ask),str(reply)],
                                    timeout=180,capture_output=True,text=True,check=True)
            except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as err:
                detail=err.stderr or ''
                if isinstance(detail,bytes): detail=detail.decode('utf8',errors='replace')
                data={'attempt':attempt,'technical_failure':type(err).__name__,'error':detail[-4000:]}
                dump(stem.with_suffix('.json'),data)
                attempts.append(data)
                passed=False
                break
            candidate.write_text(extract(reply.read_text()))
            syntax=run_ruby(['-c','/study/spec/candidate_spec.rb'], out/'work',candidate,extra_env={'TCC_TARGET_SOURCE':info['source']})
            test=run_ruby(RSPEC,out/'work',candidate,extra_env={'TCC_TARGET_SOURCE':info['source']}) if syntax['status']==0 else None
            data={'attempt':attempt,'model':json.loads(step.stdout.strip().splitlines()[-1]),
                  'syntax':syntax,'rspec':test}
            dump(stem.with_suffix('.json'),data)
            attempts.append(data)
            passed=bool(test and test['status']==0 and re.search(r'\b[1-9]\d* examples?, 0 failures?',test['log']))
            if passed:
                final=out/'automatic_spec.rb'
                final.write_bytes(candidate.read_bytes())
                break
            previous=(test or syntax)['log'][-1800:]
            prompt=(context+"\nRepair the preceding proposed spec; return the entire Ruby spec.\n"+
                    f"Previous Ruby:\n{candidate.read_text()}\nRSpec/Ruby output:\n{previous}")
        results[key]={'subject':info['subject'],'started_utc':start,
                      'finished_utc':datetime.now(timezone.utc).isoformat(),
                      'automated_seconds':monotonic()-t,'attempts':len(attempts),'passed':passed}
        dump(evidence/'pilot.json',results)
        print(key,results[key],flush=True)
if __name__=='__main__': main()
