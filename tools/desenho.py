#!/usr/bin/env python3
"""Congela a ordem experimental e audita o intervalo de sete dias."""
import argparse, csv, hashlib, json, random
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median, quantiles

GROUPS=("validacao","calculo","decisao")
CONDITIONS=("manual","assistida")
SEED=20261113

def write_new(path,data):
    with Path(path).open('x') as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
        f.write('\n')

def allocation(manifest, output):
    content=Path(manifest).read_bytes()
    targets=json.loads(content)
    if not isinstance(targets,dict) or len(targets)!=12:
        raise ValueError('O manifesto deve ter 12 alvos únicos.')
    if any('category' not in v or v['category'] not in GROUPS for v in targets.values()):
        raise ValueError('Categorias permitidas: validacao, calculo, decisao.')
    if len({v['source'] for v in targets.values()})!=12:
        raise ValueError('Atribua um arquivo independente por método.')
    rng=random.Random(SEED)
    out={}
    for group in GROUPS:
        keys=sorted(k for k,v in targets.items() if v['category']==group)
        if len(keys)!=4: raise ValueError(f'{group}: são necessários quatro alvos.')
        rng.shuffle(keys)
        selected=set(rng.sample(keys,2))
        for i,k in enumerate(keys):
            out[k]={'categoria':group,'ordem':list(CONDITIONS if i<2 else CONDITIONS[::-1]),
                    'mutacao':k in selected}
    write_new(output,{'seed':SEED,'manifest_sha256':hashlib.sha256(content).hexdigest(),
                      'targets':out})

def read_task(directory,key,condition):
    stem=Path(directory)/f'{key}_{condition}'
    if not stem.with_suffix('.csv').is_file():
        return None
    with stem.with_suffix('.csv').open() as f:
        rows=list(csv.DictReader(f))
    if not rows or any(r['alvo']!=key or r['condicao']!=condition for r in rows):
        raise ValueError(f'Identificador incorreto: {stem}')
    if any(a['fim_utc']!=b['inicio_utc'] for a,b in zip(rows,rows[1:])):
        raise ValueError(f'Intervalos descontínuos: {stem}')
    for r in rows:
        if float(r['segundos'])<0: raise ValueError(f'Intervalo negativo: {stem}')
        if datetime.fromisoformat(r['inicio_utc'])>datetime.fromisoformat(r['fim_utc']):
            raise ValueError(f'Horário inconsistente: {stem}')
    outcome=rows[-1]['desfecho']
    if outcome not in ('aceita','falha','censurada'): raise ValueError(f'Desfecho inválido: {stem}')
    excluded={'espera_modelo','espera_execucao','pausa_externa'}
    active=sum(float(r['segundos']) for r in rows if r['categoria'] not in excluded)
    elapsed=sum(float(r['segundos']) for r in rows if r['categoria']!='pausa_externa')
    if outcome=='aceita' and elapsed>=3600: raise ValueError(f'Tarefa fora do limite: {stem}')
    return {'inicio':rows[0]['inicio_utc'],'fim':rows[-1]['fim_utc'],'desfecho':outcome,
            'ativo_s':active,'decorrido_s':elapsed}

def audit(allocation_path,directory,output):
    plan=json.loads(Path(allocation_path).read_text())['targets']
    result={}
    rates=[]
    for key,meta in plan.items():
        c1,c2=meta['ordem']
        first=read_task(directory,key,c1)
        second=read_task(directory,key,c2)
        gap=None
        if first and second:
            gap=(datetime.fromisoformat(second['inicio'])-datetime.fromisoformat(first['fim'])).total_seconds()
            if gap<7*86400: raise ValueError(f'{key}: ordem ou intervalo mínimo de 168 h violado.')
            m,a=(first,second) if c1=='manual' else (second,first)
            if m['desfecho']==a['desfecho']=='aceita' and m['ativo_s']>0:
                rates.append(100*(m['ativo_s']-a['ativo_s'])/m['ativo_s'])
        if first is None and second is not None:
            raise ValueError(f'{key}: segunda condição sem primeira registrada.')
        result[key]={c1:first,c2:second,'intervalo_s':gap,'mutacao':meta['mutacao']}
    n_accepted=sum((r['assistida'] or {}).get('desfecho')=='aceita' for r in result.values())
    out={'alvos':result,'assistidas_aceitas':n_accepted,'pares_aceitos_com_tempo':len(rates),
         'mediana_reducao_pct':median(rates) if rates else None,
         'quartis_reducao_pct':quantiles(rates,n=4,method='inclusive') if len(rates)>=2 else None}
    write_new(output,out)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    s=p.add_subparsers(dest='action',required=True)
    a=s.add_parser('sortear'); a.add_argument('manifesto'); a.add_argument('saida')
    b=s.add_parser('auditar'); b.add_argument('ordem'); b.add_argument('tempos'); b.add_argument('saida')
    a=p.parse_args()
    try:
        if a.action=='sortear': allocation(a.manifesto,a.saida)
        else: audit(a.ordem,a.tempos,a.saida)
    except (ValueError,FileExistsError) as e: p.error(str(e))
if __name__=='__main__': main()
