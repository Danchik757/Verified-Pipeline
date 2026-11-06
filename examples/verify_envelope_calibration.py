"""Reproduce the 12 archived calibration sizes using this standalone checkout."""
import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--blender',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();repo=Path(__file__).resolve().parents[1];out=a.out.resolve()
if out.exists():raise SystemExit('Use a new output directory')
out.mkdir(parents=True)
expected=json.loads((repo/'docs/evidence/envelope_calibration/calibration_comparison.json').read_text())['records']
checks=[]
for kind in ('sphere','cube'):
 for mode in ('reference','turn_max'):
  output=out/f'{kind}_{mode}.json'
  command=[str(a.blender),'-b','--factory-startup','--python',str(repo/f'scripts/calibrate_{kind}_projection_height.py'),'--','--target','50','70','90','--mode',mode,'--output',str(output)]
  with (out/f'{kind}_{mode}.log').open('w') as log:r=subprocess.run(command,cwd=repo,stdout=log,stderr=subprocess.STDOUT)
  if r.returncode or not output.exists():raise SystemExit(f'Failed {kind} {mode}; inspect log')
  records=json.loads(output.read_text())['results']
  for item in records:
   old=next(x for x in expected if x['kind']==kind and x['mode']==mode and x['target_percent']==item['target_percent'])
   error=abs(item['physical_size_m']-old['physical_size_m'])
   assert error<1e-9 and abs(item['achieved_percent']-item['target_percent'])<1e-5
   checks.append({'kind':kind,'mode':mode,'target_percent':item['target_percent'],'size_delta_m':error})
  print(kind,mode,'passed',flush=True)
(out/'verification.json').write_text(json.dumps(checks,indent=2)+'\n')
