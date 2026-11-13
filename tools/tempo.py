#!/usr/bin/env python3
"""Registro contínuo e auditável de uma tarefa manual ou assistida por vez."""
import argparse
import csv
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import re
import sys
import time

ACTIVE={
    'manual':('leitura','planejamento','escrita','depuracao','validacao'),
    'assistida':('leitura','preparacao','revisao','reparo_ativo','edicao','validacao')
}
OTHER=('espera_modelo','espera_execucao','pausa_externa')
FIELDS=('alvo','condicao','categoria','inicio_utc','fim_utc','segundos','desfecho')

def save(path,state):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    tmp.replace(path)

def now():
    return {'utc':datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
            'ns':time.monotonic_ns()}

def duration(a,b):
    return max(0, b['ns']-a['ns']) / 1e9

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dir', type=Path, default=Path('tempos'))
    subs=p.add_subparsers(dest='cmd',required=True)
    start=subs.add_parser('iniciar')
    start.add_argument('alvo'); start.add_argument('condicao',choices=ACTIVE)
    mark=subs.add_parser('marcar')
    mark.add_argument('categoria',choices=sorted(set(sum(ACTIVE.values(),OTHER))))
    end=subs.add_parser('encerrar')
    end.add_argument('desfecho',choices=['aceita','falha','censurada'])
    subs.add_parser('status')
    a=p.parse_args()
    a.dir.mkdir(parents=True,exist_ok=True)
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    current=a.dir/'em_andamento.json'
    with (a.dir/'.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if a.cmd=='iniciar':
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',a.alvo): p.error('ID de alvo inválido')
            if current.exists(): p.error('Já há uma tarefa em andamento')
            dest=a.dir/f'{a.alvo}_{a.condicao}.csv'
            if dest.exists(): p.error('Já existe registro para esse par alvo/condição')
            t=now()
            save(current,{'alvo':a.alvo,'condicao':a.condicao,'boot':boot,
                          'inicio':t,'categoria':'leitura','intervalos':[]})
            print('Tarefa iniciada em leitura.')
            return
        if not current.exists(): p.error('Nenhuma tarefa em andamento')
        s=json.loads(current.read_text())
        if s['boot']!=boot: p.error('Reinício detectado: preserve o estado e registre a interrupção como falha técnica')
        t=now()
        if a.cmd=='status':
            print(f'{s["alvo"]} {s["condicao"]} {s["categoria"]}: {duration(s["inicio"],t):.3f} s neste intervalo')
            return
        if a.cmd=='marcar':
            if a.categoria not in (*ACTIVE[s['condicao']],*OTHER) or (a.categoria=='espera_modelo' and s['condicao']=='manual'):
                p.error('Categoria incompatível com a condição')
            if a.categoria==s['categoria']: p.error('A categoria já está ativa')
        row={'alvo':s['alvo'],'condicao':s['condicao'],'categoria':s['categoria'],
             'inicio_utc':s['inicio']['utc'],'fim_utc':t['utc'],
             'segundos':round(duration(s['inicio'],t),6),'desfecho':''}
        s['intervalos'].append(row)
        if a.cmd=='marcar':
            s.update(inicio=t,categoria=a.categoria)
            save(current,s)
            print(f'{a.categoria} iniciada.')
            return
        totals={k:sum(r['segundos'] for r in s['intervalos'] if r['categoria']==k)
                for k in (*ACTIVE[s['condicao']],*OTHER)}
        elapsed=sum(v for k,v in totals.items() if k!='pausa_externa')
        active=sum(totals[k] for k in ACTIVE[s['condicao']])
        outcome='censurada' if elapsed>=3600 else a.desfecho
        row['desfecho']=outcome
        dest=a.dir/f"{s['alvo']}_{s['condicao']}.csv"
        with dest.open('x',newline='') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS)
            w.writeheader()
            w.writerows(s['intervalos'])
        save(dest.with_suffix('.json'),{'alvo':s['alvo'],'condicao':s['condicao'],
            'tempo_ativo_s':round(active,6),'tempo_decorrido_s':round(elapsed,6),
            'totais_s':totals,'desfecho':outcome,'limite_s':3600})
        current.unlink()
        print(dest)
        print(f'Tempo ativo: {active:.3f} s. Tempo decorrido sem pausas: {elapsed:.3f} s. Desfecho: {outcome}.')

if __name__=='__main__':
    main()
