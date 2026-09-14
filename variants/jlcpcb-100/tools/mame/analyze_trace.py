"""Measure commanded solenoid pulses/duty from raw CPU writes (not physical blanking)."""
import argparse
import bisect
import csv
import json
from pathlib import Path

REGS = {0x3fe0: (25, 4), 0x3fe1: (1, 8), 0x3fe2: (17, 8), 0x3fe3: (9, 8)}


def analyze(path):
    edges = {i: [(0., 0)] for i in range(1, 29)}
    registers, counts, first, last, multi_columns = {}, {}, None, 0., 0
    for row in csv.DictReader(path.open()):
        t, a, value = float(row['time']), int(row['address'], 16), int(row['data'], 16)
        first = t if first is None else first
        last = t
        if row['kind'] != 'W':
            continue
        counts[hex(a)] = counts.get(hex(a), 0) + 1
        if a == 0x3fe5 and value & (value - 1):
            multi_columns += 1
        if a in REGS:
            base, bits = REGS[a]
            for bit in range(bits):
                seq = edges[base + bit]
                state = (value >> bit) & 1
                if state != seq[-1][1]:
                    seq.append((t, state))
        registers[a] = value
    results = {}
    concurrency = [(0., 0)]
    for channel, sequence in edges.items():
        sequence = sequence + [(last, 0)]
        times = [t for t, _ in sequence]
        areas = [0.]
        for (t, state), (end, _) in zip(sequence, sequence[1:]):
            areas.append(areas[-1] + (end - t) * state)
        def integral(t):
            if t <= 0:
                return 0.
            i = min(bisect.bisect_right(times, t) - 1, len(times) - 1)
            return areas[i] + (t - times[i]) * sequence[i][1]
        pulses = [(t, end - t) for (t, state), (end, _) in zip(sequence, sequence[1:]) if state]
        duty = {}
        for window in (1., 10.):
            ends = {min(last, max(window, t + shift)) for t in times for shift in (0., window)}
            duty[str(int(window)) + 's'] = max((integral(t) - integral(t - window)) / window for t in ends)
        results[str(channel)] = {'pulses': len(pulses), 'longest_s': max((d for _, d in pulses), default=0.),
                                 'duty': duty, 'total_commanded_on_s': areas[-1],
                                 'active_at_end': bool(edges[channel][-1][1])}
        previous = 0
        for t, state in sequence:
            concurrency.append((t, state - previous))
            previous = state
    concurrent, peak = 0, 0
    for _, delta in sorted(concurrency):
        concurrent += delta
        peak = max(peak, concurrent)
    return {'first_event_s': first, 'last_event_s': last, 'writes_by_register': counts,
            'multi_column_writes': multi_columns, 'max_commanded_simultaneous_solenoids': peak,
            'channels': results, 'limitations': 'Registers represent commands, not current or hardware BLANKING. Initial state assumed off before first write; pulses active at trace end are censored.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    args = parser.parse_args()
    result = analyze(args.trace)
    args.trace.with_name('analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
