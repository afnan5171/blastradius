"""Pure NetworkX analysis. Reachability expresses possibility, never proof of takeover."""
import networkx as nx

def build_graph(accounts, relationships):
    graph = nx.MultiDiGraph()
    for a in accounts:
        graph.add_node(a.id, account=a)
    for r in sorted(relationships, key=lambda r: r.id):
        if r.source_account_id in graph and r.target_account_id in graph:
            graph.add_edge(r.source_account_id, r.target_account_id, key=r.id,
                           id=r.id, relationship_type=r.relationship_type, risk_weight=r.risk_weight)
    return graph

def calculate_reachable_accounts(graph, source):
    return sorted(nx.descendants(graph, source))

def calculate_shortest_attack_paths(graph, source):
    paths = nx.single_source_shortest_path(graph, source)
    result = []
    for target in sorted(paths):
        if target == source: continue
        path = paths[target]
        edges = []
        for u, v in zip(path, path[1:]):
            # A shortest path by hop count; choose the highest-risk parallel edge.
            edges.append(max(graph[u][v].values(), key=lambda e: (e['risk_weight'], e['id'])))
        result.append({'target_account_id': target, 'account_ids': path,
                       'relationship_ids': [e['id'] for e in edges],
                       'relationship_types': [e['relationship_type'] for e in edges],
                       'direct': len(path) == 2})
    return result

def find_circular_dependencies(graph):
    # Strongly connected recovery groups avoid exponential enumeration of cycles.
    recovery = nx.DiGraph()
    recovery.add_nodes_from(graph.nodes)
    recovery.add_edges_from((u,v) for u,v,d in graph.edges(data=True)
                           if d['relationship_type'] in {'PASSWORD_RESET','RECOVERY_EMAIL','PHONE_RECOVERY'})
    return sorted([sorted(c) for c in nx.strongly_connected_components(recovery) if len(c)>1])

def find_security_chokepoints(graph):
    centrality = nx.out_degree_centrality(nx.DiGraph(graph))
    result = [{'account_id': n, 'dependent_accounts': len(nx.descendants(graph,n)),
               'out_degree': len(set(graph.successors(n))), 'centrality': round(centrality[n],3)} for n in graph]
    return sorted([r for r in result if r['dependent_accounts'] >= 2],
                  key=lambda r: (-r['dependent_accounts'],-r['centrality'],r['account_id']))

IMPORTANCE = {'Low':1, 'Medium':2, 'High':3, 'Critical':4}
CATEGORY = {'Financial':1.5, 'Cloud Storage':1.25, 'Password Manager':1.75}
def protection(account):
    return (0.75 if account.has_mfa else 1.0) * (0.5 if account.has_passkey else 1.0)
def risk_level(score):
    return 'Low' if score<=20 else 'Moderate' if score<=40 else 'Elevated' if score<=60 else 'High' if score<=80 else 'Critical'
def calculate_blast_radius_score(graph, source):
    """Heuristic exposure-priority score, NOT a breach probability.

    For each reachable destination: importance(1..4) * sensitive-category multiplier
    * destination protection * strongest edge product over ANY simple path.
    Compute strongest products via Dijkstra on -log(weight/10) costs.
    Map total impact to 0..85 with 85*(1-exp(-impact/14)), then add up to 15
    for source out-degree centrality. Apply source protection, round and clamp.
    MFA multiplies by .75; passkeys by .5. Both multiply together.
    The starting account is excluded from affected counts. Protection changes
    priority, never removes a possible path. Other path intermediates do not
    reduce risk in this deliberately conservative V1 model.
    """
    import math
    paths=calculate_shortest_attack_paths(graph,source)
    if not paths: return 0
    weighted=nx.DiGraph()
    weighted.add_nodes_from(graph.nodes)
    for u,v,d in graph.edges(data=True):
        cost=-math.log(d['risk_weight']/10)
        if not weighted.has_edge(u,v) or cost<weighted[u][v]['cost']:
            weighted.add_edge(u,v,cost=cost)
    distances=nx.single_source_dijkstra_path_length(weighted,source,weight='cost')
    impact=sum(IMPORTANCE[graph.nodes[n]['account'].importance]*CATEGORY.get(graph.nodes[n]['account'].category,1)
               *protection(graph.nodes[n]['account'])*math.exp(-distances[n]) for n in distances if n!=source)
    centrality=len(set(graph.successors(source)))/max(1,len(graph)-1)
    score=(85*(1-math.exp(-impact/14))+15*centrality)*protection(graph.nodes[source]['account'])
    return max(0,min(100,round(score)))
def calculate_account_risk_scores(graph):
    result=[]
    for n in graph:
        score=calculate_blast_radius_score(graph,n)
        result.append({'account_id':n,'score':score,'level':risk_level(score),'dependent_accounts':len(nx.descendants(graph,n))})
    return sorted(result,key=lambda r:(-r['score'],r['account_id']))

def generate_recommendations(graph, source):
    relevant={source,*nx.descendants(graph,source)}
    candidates=[]
    def add(kind,account_id,title,detail,priority):
        candidates.append(dict(kind=kind,account_id=account_id,title=title,detail=detail,priority=priority))
    for n in sorted(relevant):
        a=graph.nodes[n]['account']; reach=len(nx.descendants(graph,n)); importance=IMPORTANCE[a.importance]
        if not a.has_passkey:
            add('passkey',n,f'Enable a passkey on {a.service_name}',f'Adds strong sign-in protection to an account that influences {reach} other accounts. Existing recovery paths still need review.',50+reach*4+importance)
        if not a.has_mfa:
            add('mfa',n,f'Enable MFA on {a.service_name}',f'Adds a second sign-in check'+(' to protect financial access.' if a.category=='Financial' else f' for this {a.importance.lower()}-importance account.'),45+reach*2+importance+(15 if a.category=='Financial' else 0))
        recovery={u for u,_,d in graph.in_edges(n,data=True) if d['relationship_type'] in {'PASSWORD_RESET','RECOVERY_EMAIL','PHONE_RECOVERY'}}
        if len(recovery)==1 and a.importance in {'High','Critical'}:
            parent=next(iter(recovery));p=graph.nodes[parent]['account']
            add('single_recovery',n,f'Review recovery for {a.service_name}',f'{p.service_name} is its only mapped recovery account. Add an independent recovery option and protect both accounts.',70+importance)
        for u,_,d in graph.in_edges(n,data=True):
            parent=graph.nodes[u]['account']
            if d['relationship_type']=='SHARED_PASSWORD':
                add('shared_password',n,f'Use unique passwords for {parent.service_name} and {a.service_name}','Replace the reused passwords directly in those services, then remove this connection from your map.',90)
            if d['relationship_type'] in {'OAUTH_WRITE_ACCESS','OAUTH_READ_ACCESS'}:
                add('oauth',n,f'Review {parent.service_name} access to {a.service_name}','Remove unnecessary connected-app permissions in the service, then update this map.',55+d['risk_weight'])
            if a.importance=='Critical' and not parent.has_mfa and not parent.has_passkey:
                add('weak_dependency',u,f'Protect {parent.service_name} to safeguard {a.service_name}','A critical account depends on an account without MFA or a passkey. Strengthen that account or separate this dependency.',80)
    for group in find_circular_dependencies(graph):
        if relevant.intersection(group):
            names=' and '.join(graph.nodes[n]['account'].service_name for n in group)
            add('recovery_loop',group[0],'Break a circular recovery dependency',f'{names} are in a recovery loop. Set up an independent recovery method before removing a dependency.',95)
    # Stable rank, deduplicate identical advice; return the three highest priorities.
    unique={(r['kind'],r['account_id'],r['title']):r for r in candidates}
    return sorted(unique.values(),key=lambda r:(-r['priority'],r['title'],r['account_id']))[:3]
