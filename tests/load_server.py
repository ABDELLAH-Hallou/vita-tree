"""Private load-test host. No production test endpoints or live providers."""
import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time
import uuid
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from vita_tree.server import VitaTreeServer
from vita_tree.pdf import compile_document


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--port',type=int,default=0);parser.add_argument('--pdf',choices=['simulated','real'],default='simulated')
    args=parser.parse_args();root=args.root
    def simulated(folder, entry, engine='auto', output=None):
        time.sleep(.04)
        output=output or folder/'__vt_output';output.mkdir(parents=True,exist_ok=True)
        pdf=output/Path(entry).with_suffix('.pdf');pdf.write_bytes(b'%PDF-1.7\nsynthetic load timing stub')
        return dict(pdf=pdf,engine='pdflatex',warnings=[])
    def measured(folder,entry,engine='auto',output=None):
        started=time.monotonic();stamp=time.time();success=False
        try:
            result=(simulated if args.pdf=='simulated' else compile_document)(folder,entry,engine,output)
            success=True
            return result
        finally:
            job=folder/'job.md'
            label=json.loads(job.read_text(encoding='utf-8')).get('label') if job.is_file() else None
            (root/'.git/load-control'/(uuid.uuid4().hex+'.pdf.json')).write_text(json.dumps(dict(
                label=label,startedAt=stamp,ms=(time.monotonic()-started)*1000,success=success,engine=engine,entry=entry,mode=args.pdf)))
    server=VitaTreeServer(('127.0.0.1',args.port),root,'main.tex',root/'.git/fake-vita',log_dir=root/'.git/test-logs')
    command=[sys.executable,str(ROOT/'tests/load_provider.py')]
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    with patch.object(server.workspace,'vita_command',return_value=command):
        context=patch('vita_tree.pdf.compile_document',side_effect=measured)
        with context:
            thread.start()
            (root/'.git/load-control/ready.json').write_text(json.dumps(dict(port=server.server_port,pid=os.getpid())))
            try:
                while not (root/'.git/load-control/stop').exists():time.sleep(.1)
            finally:
                server.shutdown();server.server_close();thread.join(timeout=5)


if __name__=='__main__':main()
