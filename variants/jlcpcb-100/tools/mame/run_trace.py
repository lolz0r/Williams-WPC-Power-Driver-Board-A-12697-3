"""Run reproducible STTNG input scenarios and record unsmoothed CPU writes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil

ROOT = Path(__file__).resolve().parents[2]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rompath', required=True, type=Path, help='Parent containing sttng_l7 directory/zip')
    p.add_argument('--scenario', choices=['boot', 'game', 'diagnostics'], default='boot')
    p.add_argument('--seconds', type=int, default=240)
    args = p.parse_args()
    out = ROOT / 'output/verification/mame' / args.scenario
    out.mkdir(parents=True, exist_ok=True)
    # These directories contain only this runner's generated emulator state.
    for name in ('nvram', 'cfg'):
        if (out / name).exists():
            shutil.rmtree(out / name)
    actions = []
    def pulse(t, name, duration=.2):
        actions.extend([(t, name, 1), (t + duration, name, 0)])
    if args.scenario == 'game':
        for t in [35,36,37,38,39]:
            pulse(t, 'Coin 1')
        pulse(45, 'P1 Start', 1.)
        for t in range(55, 120, 2):
            pulse(t, 'INP' + str([31, 32, 41, 42, 51, 52, 71, 72][(t // 2) % 8]))
            pulse(t + .3, 'L Flipper Button')
            pulse(t + .6, 'R Flipper Button')
        pulse(180, 'Tilt', .6)
        pulse(210, 'Slam Tilt', .5)
    elif args.scenario == 'diagnostics':
        for t in range(35, 47, 3):
            pulse(t, 'Begin test/Enter')
        pulse(47, 'Volume Up/Up')
        pulse(50, 'Volume Up/Up')
        pulse(53, 'Begin test/Enter')
        for t in (56,59,62):
            pulse(t, 'Volume Up/Up')
        pulse(68, 'Begin test/Enter')
        for t in range(74, 168, 3):
            pulse(t, 'Volume Up/Up')
        pulse(170, 'Service credit/Escape')
        pulse(173, 'Volume Down/Down')
        pulse(176, 'Begin test/Enter')
        pulse(210, 'Service credit/Escape')
        pulse(213, 'Volume Up/Up')
        pulse(216, 'Volume Up/Up')
        pulse(219, 'Begin test/Enter')
        for t in range(225, 252, 3):
            pulse(t, 'Volume Up/Up')
        pulse(255, 'Service credit/Escape')
        pulse(258, 'Volume Up/Up')
        pulse(261, 'Begin test/Enter')
        for t in range(270, 312, 6):
            pulse(t, 'Volume Up/Up')
    (out / 'actions.csv').write_text(''.join(f'{t},{n},{v}\n' for t, n, v in sorted(actions)))
    env = dict(os.environ, WPC_TRACE_DIR=str(out), WPC_SCENARIO=args.scenario)
    fallback = Path('/home/lolz0r/repros/allied_mpu/.scratch/rev_b/mame/usr')
    binary = os.environ.get('MAME_BIN') or shutil.which('mame') or str(fallback/'games/mame')
    if fallback.exists():
        env['LD_LIBRARY_PATH'] = str(fallback/'lib/x86_64-linux-gnu')
    env.update(SDL_VIDEODRIVER='x11',SDL_AUDIODRIVER='dummy')
    for key in ('DISPLAY','WAYLAND_DISPLAY','SDL_WINDOWID'):env.pop(key,None)
    command = ['xvfb-run','-a','--server-args=-screen 0 640x480x24 -nolisten tcp',binary, 'sttng_l7', '-rompath', str(args.rompath), '-pluginspath',
               str(ROOT / 'tools/mame/plugins') + ';' + '/home/lolz0r/repros/gottlieb_ma766/.scratch/mame-source/plugins',
               '-plugins', '-plugin', 'wpcverify', '-video', 'none', '-sound', 'none', '-nothrottle',
               '-seconds_to_run', str(args.seconds), '-skip_gameinfo',
               '-nvram_directory', str(out / 'nvram'), '-cfg_directory', str(out / 'cfg'),
               '-inipath',str(out/'cfg'),'-window','-keyboardprovider','none',
               '-mouseprovider','none','-lightgunprovider','none','-joystickprovider','none']
    roms = args.rompath / 'sttng_l7'
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in roms.iterdir() if p.is_file()} if roms.is_dir() else {}
    if (args.rompath/'sttng_l7.zip').exists():
        hashes['sttng_l7.zip']=hashlib.sha256((args.rompath/'sttng_l7.zip').read_bytes()).hexdigest()
    metadata = {'command': command, 'binary_sha256':hashlib.sha256(Path(binary).read_bytes()).hexdigest(), 'rom_sha256': hashes, 'scenario': args.scenario,
                'seconds': args.seconds, 'limitations': 'Input script exercises firmware but is not a full physical playfield model. Scenario success requires screen/trace review.'}
    (out / 'manifest.json').write_text(json.dumps(metadata, indent=2) + '\n')
    with (out / 'run.log').open('w') as log:
        result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
    text = (out / 'run.log').read_text()
    if result.returncode or 'Error running plugin' in text or 'WPC recorder attached at 0.0' not in text:
        raise RuntimeError(text)
    print(out)


if __name__ == '__main__':
    main()
