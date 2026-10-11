"""Preview/build local patches through the official Retro Trans release API."""
import argparse,json,sys,time,subprocess
from tools.common import ROOT


def main():
    from tools.game_build import VERSION
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',default=VERSION);p.add_argument('--apply',action='store_true');a=p.parse_args()
    folder=ROOT/'work/output/releases'/a.version;cfg=folder/'release-local.json';data=json.loads(cfg.read_text(encoding='utf8'))
    if data['version']!=a.version:raise ValueError('Mixed local release versions')
    for route in data['patches']:print(route['source_version'],'=>',a.version,route['patch'],flush=True)
    print('Local output:',folder/'artifacts',flush=True)
    if not a.apply:print('DRY RUN: no patch assets written.');return
    tool=ROOT/'work/output/release-tools-v0.5.4'
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=tool,text=True).strip()
    if commit!='8edfb2e1c0d0c74df67107d80803177cc5939079':raise ValueError('Retro Trans 0.5.4 source changed')
    sys.path.insert(0,str(tool))
    from retro_trans.release import build_release,validate_directory
    last=['',0.0]
    def progress(message,fraction=None):
        now=time.monotonic()
        if message!=last[0]or now-last[1]>=25:
            print(message,''if fraction is None else f'{fraction:.0%}',flush=True);last[:]=[message,now]
    result=build_release(cfg,folder/'artifacts',progress=progress)
    if validate_directory(folder/'artifacts')!=result:raise ValueError('Official release protocol verification differs')
    print('Verified both complete ISO patch round trips and all release protocol assets.',flush=True)

if __name__=='__main__':main()
