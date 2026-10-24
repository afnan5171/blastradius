from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .db import get_db
from .auth import current_user
from .models import User
from .routes import profile, owned
from .graph import build_graph, calculate_shortest_attack_paths, calculate_blast_radius_score, calculate_account_risk_scores, risk_level
router=APIRouter()
@router.post('/simulate/{account_id}')
def simulate(account_id: str, db: Session=Depends(get_db), user: User=Depends(current_user)):
    owned(db,user,account_id)
    graph=build_graph(*profile(db,user))
    paths=calculate_shortest_attack_paths(graph,account_id)
    return {'source_account_id':account_id,'directly_reachable':[p['target_account_id'] for p in paths if p['direct']],
            'indirectly_reachable':[p['target_account_id'] for p in paths if not p['direct']],
            'paths':paths,'affected_count':len(paths), 'score':calculate_blast_radius_score(graph,account_id), 'level':risk_level(calculate_blast_radius_score(graph,account_id)),
            'high_value_count':sum(graph.nodes[p['target_account_id']]['account'].importance in {'High','Critical'} for p in paths)}

@router.get('/risk-scores')
def risk_scores(db: Session=Depends(get_db), user: User=Depends(current_user)):
    return calculate_account_risk_scores(build_graph(*profile(db,user)))
