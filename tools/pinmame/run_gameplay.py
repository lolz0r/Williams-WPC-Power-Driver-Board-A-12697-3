"""Build/run the deterministic STTNG PinMAME harness; preserve provenance, never bundle ROMs."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--rom-parent',type=Path,default=Path('/Users/mc/Downloads'));p.add_argument('--output',type=Path,default=ROOT/'output/verification/pinmame/gameplay-reproduced');p.add_argument('--seconds',type=int,default=240);p.add_argument('--build-only',action='store_true');a=p.parse_args()
checkout=ROOT/'.scratch/pinmame';lib=checkout/'build/libpinmame.dylib';source=ROOT/'tools/pinmame/play.cpp';exe=source.with_suffix('')
assert lib.exists(),'Build the pinned PinMAME checkout first; see docs/VERIFICATION.md'
header=next(checkout.rglob('libpinmame.h'));command=['clang++','-std=c++17','-O2','-I'+str(header.parent),str(source),'-L'+str(lib.parent),'-lpinmame','-Wl,-rpath,'+str(lib.parent),'-o',str(exe)]
subprocess.run(command,check=True)
if a.build_only:raise SystemExit(0)
out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);assert not (out/'bus.csv').exists(),'Choose a fresh output directory to preserve evidence'
roms=a.rom_parent.resolve()/'sttng_l7';assert roms.is_dir()
manifest={'harness_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'library_sha256':hashlib.sha256(lib.read_bytes()).hexdigest(),'commit':subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip(),'rom_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in roms.iterdir() if f.is_file()},'seconds':a.seconds,'build_command':command,'completed':False}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
env=dict(os.environ,PINMAME_WPC_TRACE=str(out/'bus.csv'))
with (out/'emulator.log').open('w') as log:r=subprocess.run([str(exe),str(a.rom_parent.resolve()),str(out),str(a.seconds)],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=a.seconds*3+90)
manifest.update(completed=r.returncode==0,returncode=r.returncode,bus_sha256=hashlib.sha256((out/'bus.csv').read_bytes()).hexdigest())
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');raise SystemExit(r.returncode)
