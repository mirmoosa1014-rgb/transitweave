import numpy as np
import pytest
from transitweave.simulation import simulate
from transitweave.search import analyze,detrend,search,recovered,BINS,WIDTHS
from transitweave.experiment import SPLITS


def test_replay_and_depth_pairing():
    a=simulate(101,'gapped',0);b=simulate(101,'gapped',1200);c=simulate(101,'gapped',1200)
    assert np.array_equal(b.flux,c.flux)
    assert np.array_equal(a.time,b.time)
    np.testing.assert_allclose(b.flux-a.flux,b.transit,atol=3e-16)
    assert b.time.max()<27 and b.time.min()>=0
    assert not np.any((b.time>11)&(b.time<14))

@pytest.mark.parametrize('kwargs',[{'seed':True},{'seed':-1},{'seed':2.5},{'seed':1000001},{'family':'missing'}, {'depth_ppm':float('nan')},{'depth_ppm':True},{'depth_ppm':-1},{'depth_ppm':6000}])
def test_simulation_rejects_invalid_inputs(kwargs):
    with pytest.raises(ValueError):simulate(**kwargs)


def test_all_split_seed_sets_disjoint():
    sets=[set(s) for s in SPLITS.values()]
    assert sum(map(len,sets))==len(set.union(*sets))


def test_constant_flux_has_no_detection():
    fit=search(np.arange(100)/10,np.ones(100),.001)
    assert fit['score']==0 and fit['depth_ppm']==0
    assert fit['baseline_flux']==1


def test_known_period_and_wrapped_box():
    t=np.arange(0,27,.03);p=2.7
    y=1-.005*(np.abs((t+.05+p/2)%p-p/2)<.09)
    fit=search(t,y,.0008)
    assert abs(fit['period_days']-p)<.011
    assert fit['score']>20 and fit['depth_ppm']>4000


def test_binned_score_equals_exhaustive_least_squares():
    lc=simulate(42,'quiet',2000);p=lc.truth['period_days']
    t,y=lc.time,lc.flux
    phase=((t-t[0])%p/p*BINS).astype(int)
    best=0.;base=np.sum((y-y.mean())**2)
    for width in WIDTHS:
        for start in range(BINS):
            mask=(phase-start)%BINS<width
            if mask.sum()<4 or (~mask).sum()<20 or y[mask].mean()>=y[~mask].mean():continue
            residual=np.sum((y[mask]-y[mask].mean())**2)+np.sum((y[~mask]-y[~mask].mean())**2)
            best=max(best,(base-residual)/lc.sigma**2)
    fit=search(t,y,lc.sigma,[p])
    assert fit['score']**2==pytest.approx(best,rel=1e-10)


def test_offset_and_time_translation_invariance():
    lc=simulate(23,'quiet',2000)
    a=search(lc.time,lc.flux,lc.sigma)
    b=search(lc.time+37.25,lc.flux+7,lc.sigma)
    assert a['period_days']==b['period_days']
    np.testing.assert_allclose(a['scores'],b['scores'],atol=1e-10)


def test_detrending_uses_elapsed_time_and_preserves_input():
    t=np.r_[np.arange(20)*.01,10+np.arange(20)*.01]
    y=np.r_[np.ones(20),np.full(20,2.)];before=y.copy()
    cleaned,trend=detrend(t,y,.6)
    np.testing.assert_array_equal(cleaned,np.ones(40))
    np.testing.assert_array_equal(y,before)
    np.testing.assert_array_equal(trend,y)


def test_search_never_receives_truth():
    lc=simulate(44,'quiet',2400)
    before=analyze(lc.time,lc.flux,lc.sigma,.6)
    lc.truth.update(period_days=99,depth_ppm=0)
    assert analyze(lc.time,lc.flux,lc.sigma,.6)==before

@pytest.mark.parametrize('time,flux,sigma',[(np.arange(10),np.ones(10),1), (np.zeros(30),np.ones(30),1),(np.arange(30),np.full(30,np.nan),1),(np.arange(30),np.ones(30),0),(np.arange(30),np.ones(30),True)])
def test_bad_observations_rejected(time,flux,sigma):
    with pytest.raises(ValueError):search(time,flux,sigma)


def test_aliases_and_null_are_not_recoveries():
    truth={'period_days':3.,'depth_ppm':1000}
    assert recovered({'period_days':3.01},truth)
    assert not recovered({'period_days':6.},truth)
    assert not recovered({'period_days':1.5},truth)
    assert not recovered({'period_days':3.},{**truth,'depth_ppm':0})
