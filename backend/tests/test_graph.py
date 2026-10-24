from types import SimpleNamespace as Obj
from app.graph import *
def account(id, **kw):
    return Obj(id=id,service_name=id,importance='High',category='Email',has_mfa=False,has_passkey=False,**kw)
def relation(a,b,id='r',type='PASSWORD_RESET',weight=10):
    return Obj(id=id,source_account_id=a,target_account_id=b,relationship_type=type,risk_weight=weight)
def sample(): return build_graph([account(x) for x in 'abcd'],[relation('a','b'),relation('b','c','s')])
def test_traversal():
    g=sample()
    assert calculate_reachable_accounts(g,'a')==['b','c']
    assert calculate_reachable_accounts(g,'c')==[]
    assert 'd' in g
    assert calculate_shortest_attack_paths(g,'a')[1]['account_ids']==['a','b','c']
def test_parallel_relationships():
    g=build_graph([account(x) for x in 'ab'],[relation('a','b'),relation('a','b','s','OAUTH_READ_ACCESS',6)])
    assert g.number_of_edges()==2
    assert calculate_shortest_attack_paths(g,'a')[0]['relationship_ids']==['r']
def test_cycles_and_chokepoints():
    g=sample();g.add_edge('b','a',id='back',relationship_type='RECOVERY_EMAIL',risk_weight=9)
    assert find_circular_dependencies(g)==[['a','b']]
    assert find_security_chokepoints(g)[0]['dependent_accounts']==2
    assert find_circular_dependencies(sample())==[]
