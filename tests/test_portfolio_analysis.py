"""Check that a portfolio-conditional empirical bound has the stated meaning."""
import pytest
from experiments.analyze_portfolio import paired_floors, summarise_portfolio


def pair():
    return [dict(n='128',motif='example',rhs='same',shift=str(i),accepted=True,stable=True,
                 winner=winner,jacobi_total=j,amg0_total=a,rs025_total=r)
            for i,winner,j,a,r in [(0,'jacobi',1.,2.,.5),(1,'amg0',2.,1.,.5)]]


def test_enlarging_portfolio_can_remove_fixed_choice_cost_floor():
    data=pair()
    assert paired_floors(data,['jacobi','amg0'])[0]['empirical_minimum_mean_excess']==pytest.approx(.5)
    for row in data:row['winner']='rs025'
    result=paired_floors(data,['jacobi','amg0','rs025'])[0]
    assert result['empirical_minimum_mean_excess']==0
    assert not result['stable_reversal']
    assert result['best_invariant_only_method']=='rs025'


def test_floor_is_time_unit_invariant_and_rejects_incomplete_acceptance():
    data=pair();expected=paired_floors(data,['jacobi','amg0'])[0]['empirical_minimum_mean_excess']
    for row in data:
        for m in ['jacobi','amg0','rs025']:row[m+'_total']*=1000
    assert paired_floors(data,['jacobi','amg0'])[0]['empirical_minimum_mean_excess']==pytest.approx(expected)
    data[0]['accepted']=False;data[0]['stable']=False
    result=paired_floors(data,['jacobi','amg0'])[0]
    assert result['empirical_minimum_mean_excess'] is None
    assert not result['stable_reversal']


def test_duplicate_repeat_cannot_masquerade_as_complete_block():
    row=dict(cell='a',method='jacobi',repeat=0,accepted=True,residual=0,
             setup=0,solve=1,total=1,iterations=1)
    with pytest.raises(AssertionError):
        summarise_portfolio([row,row],['cell'],['jacobi'],2)
