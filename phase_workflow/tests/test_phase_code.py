#!/usr/bin/env python3
"""Fast unit tests; not a substitute for live Verilog/Hermes execution."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'phase_03_ai_verification'))
from testbench_generator import make_tb, validate_scenarios, payload_bin, BINS
from uart_ai_pipeline import prompt, parse_hermes_response, directed, randomized, aggregate

class Tests(unittest.TestCase):
    def test_scenario_schema(self):
        good=validate_scenarios({'scenarios':[{'id':'x','kind':'loopback','value':255},
                                              {'id':'y','kind':'bad_stop'}]})
        self.assertEqual(len(good),2)
        with self.assertRaises(ValueError): validate_scenarios([{'id':'x','kind':'raw_verilog','value':17}])
        with self.assertRaises(ValueError): validate_scenarios([{'id':'x','kind':'loopback','value':999}])
        with self.assertRaises(ValueError): validate_scenarios([{'id':'x','kind':'bad_stop'},{'id':'x','kind':'bad_stop'}])
        with self.assertRaises(ValueError): validate_scenarios([{'id':'x','kind':'loopback','value':'85'}])
    def test_generator(self):
        cases=[{'id':'one','kind':'loopback','value':0},
               {'id':'two','kind':'bad_stop'},
               {'id':'three','kind':'reset_mid_tx'},
               {'id':'four','kind':'busy_start','value':18},
               {'id':'five','kind':'paired_frames','value':23}]
        code=make_tb(cases,16)
        self.assertIn('module tb_uart_phase;',code)
        self.assertIn("one_loopback(8'd0,0);",code)
        self.assertIn('bad_stop();',code)
        self.assertIn('reset_mid();',code)
        self.assertIn("start_while_busy(8'd18);",code)
        self.assertIn('VERDICT=PASS',code)
        self.assertNotIn('__CPB__',code)
        self.assertNotIn('__SCENARIO_CALLS__',code)
        with self.assertRaises(ValueError): make_tb(cases,4)
    def test_hermes_json(self):
        res=parse_hermes_response('```json\n{"scenarios":[{"id":"x1","kind":"loopback","value":85}]}\n```')
        self.assertEqual(res[0]['value'],85)
        with self.assertRaises(ValueError): parse_hermes_response({'scenarios':[{'kind':'eval','id':'x'}]})
    def test_baselines_deterministic(self):
        self.assertEqual(len(directed()),10)
        self.assertEqual(randomized(4),randomized(4))
        self.assertEqual(payload_bin(129),'edge_81')
        self.assertEqual(len(BINS),10)
    def test_aggregator(self):
        rows=[{'cpb':8,'checks':3,'failed':0,'cycles':60,'wall_seconds':0.2,'coverage_pct':20.0,
               'status':'PASS','coverage':dict.fromkeys(BINS,0)},
              {'cpb':16,'checks':5,'failed':0,'cycles':120,'wall_seconds':0.3,'coverage_pct':30.0,
               'status':'PASS','coverage':dict.fromkeys(BINS,0)}]
        a=aggregate(rows)
        self.assertEqual(a['cycles'],180)
        self.assertEqual(a['checks'],8)
        self.assertEqual(a['min_coverage_pct'],20)
    def test_prompt_does_not_contain_executable_instructions(self):
        k={'protocol':{'data_bits':8}}
        s=prompt(k)
        self.assertIn('scenarios',s)
        self.assertIn('Allowed kind values',s)

if __name__=='__main__': unittest.main(verbosity=2)
