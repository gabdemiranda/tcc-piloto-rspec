"""Obtém o blob GGUF do distribuidor oficial e valida seu SHA-256."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('output',type=Path)
p.add_argument('--initial',action='store_true')
a=p.parse_args()
d=root/'config_inicial' if a.initial else root
config=json.loads((d/'model.json').read_text())
manifest=json.loads((d/'model-manifest.json').read_text())
layer=next(x for x in manifest['layers'] if x['mediaType'].endswith('.model'))
sha=layer['digest'].split(':')[1]
if sha!=config['sha256']: raise SystemExit('Manifesto diverge da configuração')
if a.output.exists():
    with a.output.open('rb') as file:
        if hashlib.file_digest(file,'sha256').hexdigest()==sha:
            print(a.output); raise SystemExit(0)
    raise SystemExit('Arquivo de destino já existe com hash diferente')
a.output.parent.mkdir(parents=True,exist_ok=True)
tmp=a.output.with_suffix(a.output.suffix+'.part')
h=hashlib.sha256()
url='https://registry.ollama.ai/v2/library/qwen2.5-coder/blobs/'+layer['digest']
with urllib.request.urlopen(url,timeout=60) as stream,tmp.open('xb') as out:
    while block:=stream.read(8*1024*1024):
        h.update(block)
        out.write(block)
if tmp.stat().st_size!=layer['size'] or h.hexdigest()!=sha:
    raise SystemExit('Arquivo baixado não corresponde ao manifesto')
tmp.rename(a.output)
print(a.output)
