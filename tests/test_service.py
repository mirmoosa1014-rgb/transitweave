import json
import threading
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import numpy as np
import pytest
from transitweave.server import make_server,ROOT
from transitweave.search import analyze
from transitweave.simulation import simulate

@pytest.fixture(scope='module')
def url():
    server=make_server(0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown();server.server_close();thread.join()


def test_live_api_matches_core(url):
    payload=dict(seed=3001,family='quiet',depth_ppm=1200)
    request=Request(url+'/api/run',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urlopen(request) as response:result=json.load(response)
    lc=simulate(**payload)
    assert result['truth']==lc.truth
    fit=analyze(lc.time,lc.flux,lc.sigma)
    assert result['methods']['raw']['scores']==fit['scores']
    with urlopen(url+'/api/meta') as response:assert len(json.load(response)['summary'])==6

@pytest.mark.parametrize('body',[b'{}x',b'[]',b'{"seed":true}',b'{"seed":1.5}',b'{"family":"nope"}',b'{"extra":1}',b'x'*513])
def test_bad_requests(url,body):
    with pytest.raises(HTTPError) as error:urlopen(Request(url+'/api/run',data=body))
    assert error.value.code==400


def test_unknown_path_and_cross_origin(url):
    for path in ['/../results/config.json','/results/config.json','/not-found']:
        with pytest.raises(HTTPError) as error:urlopen(url+path)
        assert error.value.code==404
    with pytest.raises(HTTPError) as error:urlopen(Request(url+'/api/run',data=b'{}',headers={'Origin':'https://example.com'}))
    assert error.value.code==403


def test_saved_artifacts_and_summary_agree():
    result=json.loads((ROOT/'results/benchmark.json').read_text())
    rows=result['rows'];config=result['config']
    assert len(rows)==672 and not config['quick']
    assert config['selected_window_days']==max(config['tuning'],key=lambda x:(x['recovery_rate'],-x['window_days']))['window_days']
    for summary in result['summary']:
        a=[r for r in rows if r['family']==summary['family'] and r['method']==summary['method'] and r['split']=='test']
        b=[r for r in rows if r['family']==summary['family'] and r['method']==summary['method'] and r['split']=='null_test']
        assert summary['recovered']==sum(r['recovered'] for r in a)
        assert summary['false_alarms']==sum(r['alarm'] for r in b)
        assert len(a)==summary['signals'] and len(b)==summary['nulls']
    calibration=json.loads((ROOT/'results/calibration.json').read_text())
    for method,window in [('raw',0),('detrended',config['selected_window_days'])]:
        values=[r['score'] for r in calibration if r['window_days']==window]
        assert len(values)==120
        assert config['thresholds'][method]==np.quantile(values,.95,method='higher')


def test_committed_demo_reproduces_search():
    demo=json.loads((ROOT/'results/demos.json').read_text())[0]
    for method in ('raw','detrended'):
        fit=demo['methods'][method]
        current=analyze(demo['time'],demo['flux'],.0008,fit['window_days'])
        np.testing.assert_allclose(current['scores'],fit['scores'],rtol=1e-10,atol=1e-10)
