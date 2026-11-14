"""Loopback-only laboratory server; no uploads, accounts or external services."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import urlsplit
from .simulation import simulate
from .search import analyze

ROOT = Path(__file__).resolve().parents[1]


def run_case(payload, config):
    if not isinstance(payload, dict) or set(payload)-{'seed','family','depth_ppm'}:
        raise ValueError('provide seed, family and depth_ppm only')
    lc = simulate(payload.get('seed',3001),payload.get('family','variable'),payload.get('depth_ppm',1200))
    methods={}
    for method,window in [('raw',0),('detrended',config['selected_window_days'])]:
        fit=analyze(lc.time,lc.flux,lc.sigma,window)
        fit['threshold']=config['thresholds'][method]
        fit['alarm']=fit['score']>fit['threshold']
        methods[method]=fit
    return dict(truth=lc.truth,time=lc.time.tolist(),flux=lc.flux.tolist(),
                stellar=lc.stellar.tolist(),transit=lc.transit.tolist(),methods=methods,
                note='Synthetic observations; injected truth is for evaluation, never search input.')


class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT/'web'),**kwargs)

    def reply(self,status,value):
        body=json.dumps(value,allow_nan=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json')
        self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)))
        self.end_headers();self.wfile.write(body)

    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/meta':
            return self.reply(200,dict(config=self.server.config,summary=self.server.summary))
        if path not in ('/','/index.html','/app.js','/style.css'):
            return self.reply(404,{'error':'not found'})
        super().do_GET()

    def do_POST(self):
        if self.path!='/api/run':return self.reply(404,{'error':'not found'})
        # Browser cross-origin requests are not accepted, even for this local-only app.
        origin=self.headers.get('Origin')
        allowed={f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}
        if origin and origin not in allowed:return self.reply(403,{'error':'cross-origin requests are not supported'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=512:raise ValueError('request must be 1–512 bytes')
            payload=json.loads(self.rfile.read(length))
            if not self.server.gate.acquire(blocking=False):return self.reply(429,{'error':'another simulation is running; retry shortly'})
            try:result=run_case(payload,self.server.config)
            finally:self.server.gate.release()
            self.reply(200,result)
        except (ValueError,TypeError) as exc:
            self.reply(400,{'error':str(exc)})


def make_server(port=8766):
    benchmark=json.loads((ROOT/'results/benchmark.json').read_text())
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.config=benchmark['config'];server.summary=benchmark['summary']
    server.gate=threading.BoundedSemaphore(1)
    return server

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8766)
    args=parser.parse_args()
    with make_server(args.port) as server:
        print(f'TransitWeave: http://127.0.0.1:{server.server_port}',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
