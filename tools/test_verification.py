"""Regression tests for verification gates, including deliberately faulty inputs.

Run: python3 -m unittest discover -s tools -p test_verification.py
"""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from verify_artifacts import audit
from spice import run_all
from spice.replay_rom import worst_window, read_edges, command_points
from sexp import parse, dump


class ArtifactTests(unittest.TestCase):
    def test_value_and_connectivity_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            pcb, xml = Path(directory) / 'board.kicad_pcb', Path(directory) / 'board.xml'
            pcb.write_text('(kicad_pcb (footprint "R" (property "Reference" "R1") '
                           '(property "Value" "2K") (pad "1" smd rect (net 1 "GND"))))')
            xml.write_text('<export><components><comp ref="R1"><value>1K</value>'
                           '<footprint>R</footprint></comp></components><nets>'
                           '<net name="VCC"><node ref="R1" pin="1"/></net></nets></export>')
            result = audit(pcb, xml)
            self.assertFalse(result['passed'])
            self.assertEqual(len(result['net_mismatches']), 1)
            self.assertEqual(len(result['component_field_mismatches']), 1)
            pcb.write_text(pcb.read_text().replace('2K', '1K').replace('GND', 'VCC'))
            self.assertTrue(audit(pcb, xml)['passed'])

    def test_mpn_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            pcb, xml = Path(directory)/'board.kicad_pcb', Path(directory)/'board.xml'
            pcb.write_text('(kicad_pcb (footprint "FP" (property "Reference" "D1") '
                           '(property "Value" "Diode") (property "MPN" "WRONG")))')
            xml.write_text('<export><components><comp ref="D1"><value>Diode</value>'
                           '<footprint>FP</footprint><fields><field name="MPN">RIGHT</field>'
                           '</fields></comp></components><nets/></export>')
            result=audit(pcb,xml)
            self.assertFalse(result['passed'])
            self.assertEqual(result['component_field_mismatches'][0]['field'],'MPN')
            pcb.write_text(pcb.read_text().replace('WRONG','RIGHT'))
            self.assertTrue(audit(pcb,xml)['passed'])

    def test_header_catalog_typo(self):
        from verify_interface import audit as interface_audit
        import xml.etree.ElementTree as ET
        source=Path(__file__).resolve().parents[1]/'output/release-candidate/reports/netlist.xml'
        tree=ET.parse(source)
        component=next(c for c in tree.findall('.//components/comp') if c.attrib['ref']=='J101')
        field=next(f for f in component.findall('fields/field') if f.attrib['name']=='MPN')
        field.text='0026604007'
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.xml';tree.write(path)
            result=interface_audit(path)
            self.assertIn('J101 Molex KK396 catalog MPN',result['failures'])


class SpiceGateTests(unittest.TestCase):
    def run_fixture(self, log, missing_deck=False):
        class FakeSpice:
            def cmd(self, command):
                return 0

            def run_deck(self, deck):
                return log

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'decks').mkdir()
            if not missing_deck:
                (root / 'decks' / 'sample.cir').write_text('Sample\n.end\n')
            (root / 'models.lib').write_text('* fixture\n')
            original_cwd = Path.cwd()
            try:
                with patch.object(run_all, 'HERE', directory), patch.object(run_all, 'OUT', str(root / 'out')), \
                     patch.object(run_all, 'CHECKS', {'sample': [('v', 4.9, 5.1, 'rail')]}), \
                     patch.object(run_all, 'NgSpice', FakeSpice), patch('sys.argv', ['run_all.py']), \
                     contextlib.redirect_stdout(io.StringIO()):
                    return run_all.main()
            finally:
                import os
                os.chdir(original_cwd)

    def test_passing_measurement(self):
        self.assertEqual(self.run_fixture(['stdout v = 5']), 0)

    def test_failed_or_missing_measurement(self):
        for log in (['stdout v = 6'], [], ['stdout v = nan']):
            with self.subTest(log=log):
                self.assertEqual(self.run_fixture(log), 1)

    def test_simulator_error_fails_even_with_valid_measurement(self):
        self.assertEqual(self.run_fixture(['stdout v = 5', 'stderr simulation failed']), 1)

    def test_missing_deck_cannot_pass(self):
        with self.assertRaises(RuntimeError):
            self.run_fixture([], missing_deck=True)


class TraceTests(unittest.TestCase):
    def test_worst_window_spans_separate_pulses(self):
        start, end, duty = worst_window([(0,0),(2,1),(5,0),(8,1),(12,0)],20)
        self.assertAlmostEqual(duty,.7)
        self.assertAlmostEqual(end-start,10)

    def test_short_trace_and_end_censoring(self):
        self.assertAlmostEqual(worst_window([(0,0),(2,1)],5)[2],.3)
        self.assertAlmostEqual(worst_window([(0,0),(12,1)],20)[2],.8)

    def test_nonmonotonic_trace_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'trace.csv'
            p.write_text('time,kind,address,data\n2,W,3fe1,01\n1,W,3fe1,00\n')
            with self.assertRaises(AssertionError):read_edges(p)

    def test_kicad_escaped_text_roundtrip(self):
        text='line one\nline two "quoted" \\ literal'
        self.assertEqual(parse(dump(['text',text]))[0][1],text)


if __name__ == '__main__':
    unittest.main()

class ReplayWaveformTests(unittest.TestCase):
    def test_end_event_has_no_duplicate_pwl_time(self):
        points=command_points([(0.,0),(1.,1),(2.,0)],0.,2.,2.03)
        self.assertTrue(all(b[0]>a[0] for a,b in zip(points,points[1:])))
        self.assertEqual(sum(t==2. for t,v in points),1)
        self.assertEqual(next(v for t,v in points if t==1.),4.5)

    def test_close_edges_preserve_command_order(self):
        points=command_points([(0.,0),(1e-9,1),(2e-9,0)],0.,1e-6,.03)
        self.assertTrue(all(b[0]>a[0] for a,b in zip(points,points[1:])))
        self.assertIn((1e-9,4.5),points)
        self.assertIn((2e-9,0.),points)
