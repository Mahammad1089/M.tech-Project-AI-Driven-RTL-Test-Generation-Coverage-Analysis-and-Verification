#!/usr/bin/env python3
"""Create a clean phase-labelled reviewer ZIP without changing historic experiment paths."""
import hashlib
import json
import re
import zipfile
from pathlib import Path
from datetime import datetime, timezone

WF=Path(__file__).resolve().parents[1]
OUT=Path.home()/'MTech_Phase_Based_Review_Package.zip'
PREFIXES=('phase_01_rtl/', 'phase_02_parsing/', 'phase_03_ai_verification/',
          'phase_04_uart_novelty/', 'evaluation/figures/', 'docs/', 'tools/')
REQUIRED=('phase_01_rtl/uart/uart_tx.v','phase_01_rtl/uart/uart_rx.v',
          'phase_04_uart_novelty/UART_ARCHITECTURE_RESULTS.md',
          'evaluation/PHASE_REVIEW_SUMMARY.md','README.md')

def included(relative):
    if relative=='README.md':return True
    if not relative.startswith(PREFIXES) and relative!='evaluation/PHASE_REVIEW_SUMMARY.md':return False
    if any(x in relative for x in ('/__pycache__/','/.legacy_file_map.json','/results/','/reference/')):return False
    if relative.endswith(('.pyc','.out','.vcd','.log')):return False
    return True

def main():
    files=[]
    for p in sorted(WF.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(WF).as_posix()
        if included(rel):files.append((rel,p))
    included_set={r for r,_ in files}
    missing=set(REQUIRED)-included_set
    if missing:raise RuntimeError('Run organizer and summary builders first: '+str(sorted(missing)))
    for rel,_ in files:
        if re.search(r'(?i)(?:day[_-]?\d+|extension_day[_-]?\d+)',rel):
            raise RuntimeError('Chronological filename in review package: '+rel)
    manifest={'generated_utc':datetime.now(timezone.utc).isoformat(),
              'status':'REVIEW_VIEW_NOT_COMPLETE_REPRODUCTION',
              'file_count':len(files),'paths_sha256':{rel:hashlib.sha256(p.read_bytes()).hexdigest() for rel,p in files},
              'note':'Historical source/evidence is in original Git repository; private path map intentionally omitted.'}
    with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for rel,path in files:z.write(path,arcname='phase_workflow/'+rel)
        z.writestr('phase_workflow/REVIEW_MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(OUT) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(files)+1
    print('REVIEW PACKAGE:',OUT)
    print('FILES:',len(files))
    print('[PASS] No chronological filenames; raw historic experiment files excluded')
    print('[PASS] ZIP integrity')
if __name__=='__main__':main()
