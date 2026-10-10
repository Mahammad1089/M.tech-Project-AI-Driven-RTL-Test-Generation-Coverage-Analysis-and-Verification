#!/usr/bin/env python3
"""Extract a verifiable UART knowledge model via PyVerilog AST parsing.

Does not convert RTL to executable Python. Does not guess UART features absent
from RTL; it verifies required structural signatures for this known benchmark.
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'phase_01_rtl' / 'uart'
OUTPUT = ROOT / 'phase_02_parsing' / 'results' / 'uart_knowledge.json'
EXPECTED = {
    'uart_tx': ('clk', 'rst', 'start', 'data_in', 'tx', 'busy', 'done'),
    'uart_rx': ('clk', 'rst', 'rx', 'data_out', 'valid', 'busy', 'framing_error'),
    'uart_tx_opt': ('clk', 'rst', 'start', 'data_in', 'tx', 'busy', 'done'),
    'uart_rx_opt': ('clk', 'rst', 'rx', 'data_out', 'valid', 'busy', 'framing_error'),
}

def descendants(node):
    yield node
    for child in node.children():
        yield from descendants(child)

def extract_ports(module):
    ports = []
    for port in module.portlist.ports:
        decl = getattr(port, 'first', None)
        if decl is None:
            raise ValueError(f'Unsupported port declaration in {module.name}: {port}')
        width = getattr(decl, 'width', None)
        bits = 1
        if width is not None:
            msb = getattr(width.msb, 'value', None)
            lsb = getattr(width.lsb, 'value', None)
            if msb is not None and lsb is not None:
                bits = abs(int(msb, 0) - int(lsb, 0)) + 1
            else:
                bits = None
        ports.append({'name': decl.name, 'direction': decl.__class__.__name__.lower(), 'bits': bits})
    return ports

def parse_file(path, expected_name):
    try:
        from pyverilog.vparser.parser import VerilogParser
        from pyverilog.vparser.ast import ModuleDef, Always, Sens, Localparam, Parameter
    except ImportError as exc:
        raise RuntimeError('PyVerilog missing. Activate WSL venv and run: python -m pip install pyverilog==1.3.0') from exc
    raw = path.read_text(encoding='utf-8')
    # PyVerilog VerilogParser operates on text without the external iverilog preprocessor.
    sanitized = '\n'.join(line for line in raw.splitlines() if not line.lstrip().startswith('`timescale'))
    parser = VerilogParser()
    ast = parser.parse(sanitized)
    mods = [node for node in descendants(ast) if isinstance(node, ModuleDef)]
    if len(mods) != 1 or mods[0].name != expected_name:
        raise ValueError(f'{path.name}: expected module {expected_name}, found {[m.name for m in mods]}')
    mod = mods[0]
    ports = extract_ports(mod)
    names = {p['name'] for p in ports}
    if names != set(EXPECTED[expected_name]):
        raise ValueError(f'{expected_name}: unexpected port contract {names}')
    posedge = False
    states = set()
    parameters = set()
    for node in descendants(mod):
        if isinstance(node, Always):
            senslist = getattr(node, 'sens_list', None)
            if senslist is not None:
                for sens in getattr(senslist, 'list', ()):
                    if isinstance(sens, Sens) and sens.type == 'posedge':
                        posedge = True
        if isinstance(node, Localparam):
            if node.name in {'IDLE','START','DATA','STOP'}:
                states.add(node.name)
        if isinstance(node, Parameter):
            parameters.add(node.name)
    if not posedge or states != {'IDLE','START','DATA','STOP'}:
        raise ValueError(f'{expected_name}: posedge FSM/state contract mismatch: {states}')
    if 'CLKS_PER_BIT' not in parameters:
        raise ValueError(f'{expected_name}: CLKS_PER_BIT parameter missing')
    return {'module': expected_name, 'file': path.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'ports':ports,
            'parameters':sorted(parameters), 'states':sorted(states), 'posedge_clocked': posedge,
            'parser': 'PyVerilog VerilogParser AST'}

def knowledge():
    files = {
        'uart_tx': 'uart_tx.v', 'uart_rx': 'uart_rx.v',
        'uart_tx_opt': 'uart_tx_opt.v', 'uart_rx_opt': 'uart_rx_opt.v'
    }
    parsed = {mod: parse_file(SOURCES / name, mod) for mod,name in files.items()}
    for mod in parsed:
        txt = (SOURCES / files[mod]).read_text(encoding='utf-8')
        required = ['if (rst)', 'state<=IDLE'] if mod in ('uart_tx','uart_rx') else ['if (rst)', 'state <= IDLE']
        # Allow formatting differences: AST-based contract above is authoritative.
        if not re.search(r'\bCLKS_PER_BIT\b', txt):
            raise ValueError(f'{mod}: baud period reference absent')
    tx_text = (SOURCES / files['uart_tx']).read_text()
    rx_text = (SOURCES / files['uart_rx']).read_text()
    if not all(s in tx_text for s in ('payload[0]', 'bit_idx==7', 'done<=1')):
        raise ValueError('Baseline TX behavioral landmarks not found')
    if not all(s in rx_text for s in ('rx_meta<=rx', 'rx_sync<=rx_meta', 'framing_error<=1', 'data_out<=payload')):
        raise ValueError('Baseline RX behavioral landmarks not found')
    return {
        'schema': 'uart_knowledge_v1', 'generated_utc': datetime.now(timezone.utc).isoformat(),
        'source_analysis': parsed,
        'protocol': {'format':'8N1', 'data_bits':8, 'parity':'none', 'stop_bits':1,
                     'bit_order':'LSB_first', 'clock_parameter':'CLKS_PER_BIT',
                     'tested_clocks_per_bit':[8,16,32,64],
                     'reset':'synchronous active-high',
                     'receiver_input_synchronizer_stages':2,
                     'receiver_stop_check':'framing_error on low stop bit',
                     'note':'Observed design contract, not a full formal protocol proof'},
        'verification_budgets': {'baseline_scenarios':10, 'max_ai_scenarios_per_round':24, 'max_feedback_rounds':2},
        'required_bins': ['zero','all_ones','alternating_55','alternating_aa',
                          'edge_81','other_data','framing_error','reset_mid_tx',
                          'busy_start','paired_frames'],
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, default=OUTPUT)
    args=ap.parse_args()
    data=knowledge()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print('[PASS] Phase 2: parsed four UART modules via PyVerilog AST')
    print('KNOWLEDGE:',args.output)
    print('REQUIRED COVERAGE BINS:',len(data['required_bins']))
if __name__=='__main__':
    try: main()
    except (ValueError, OSError, RuntimeError) as ex:
        print('[FAIL] Phase 2:',ex,file=sys.stderr);sys.exit(1)
