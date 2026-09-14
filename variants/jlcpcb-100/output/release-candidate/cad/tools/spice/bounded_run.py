"""Isolate ngspice runs with explicit wall-time limits and retained live logs.

Timeout is INCOMPLETE, never a circuit failure or pass. No solver/model changes.
This separate wrapper leaves the hash-bound baseline NgSpice driver unchanged.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from corners import measurements
from ngspice_lib import NgSpice


def run_bounded(deck, wall_seconds=180, pspice=False):
    deck = Path(deck).resolve()
    result_path = deck.with_suffix('.run.json')
    if result_path.exists():
        raise FileExistsError(f'Preserve previous result before rerunning: {result_path}')
    command = [sys.executable, str(Path(__file__).resolve()), str(deck), '--worker']
    if pspice:
        command.append('--pspice')
    start = time.monotonic()
    timed_out = False
    with deck.with_suffix('.worker.log').open('w') as stream:
        process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT)
        try:
            process.wait(timeout=wall_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    log_path = deck.with_suffix('.log')
    log = log_path.read_text().splitlines() if log_path.exists() else []
    values = measurements(log)
    errors = [x for x in log if x.startswith('stderr')
              and not x.startswith('stderr Note:') and 'Warning' not in x]
    result = dict(deck=str(deck), deck_sha256=hashlib.sha256(deck.read_bytes()).hexdigest(),
                  elapsed_s=time.monotonic()-start, wall_limit_s=wall_seconds,
                  timed_out=timed_out, worker_returncode=process.returncode,
                  execution_completed=not timed_out and process.returncode == 0,
                  errors=errors, measurements=values,
                  timeout_meaning='Runtime limit; no electrical or numerical-convergence conclusion')
    result_path.write_text(json.dumps(result, indent=2) + '\n')
    return result


def worker(deck, pspice):
    with deck.with_suffix('.log').open('w', buffering=1) as stream:
        class LiveSpice(NgSpice):
            def _send_char(self, value, ident, user):
                line = value.decode(errors='replace')
                if 'Reference value' in line:
                    deck.with_suffix('.progress').write_text(line + '\n')
                else:
                    stream.write(line + '\n')
                return 0
        ng = LiveSpice()
        if pspice:
            ng.cmd('set ngbehavior=ps')
        ng.run_deck(str(deck))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('deck', type=Path)
    parser.add_argument('--wall-seconds', type=float, default=180)
    parser.add_argument('--pspice', action='store_true')
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.worker:
        worker(args.deck.resolve(), args.pspice)
    else:
        result = run_bounded(args.deck, args.wall_seconds, args.pspice)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result['execution_completed'] and not result['errors'] else 1)
