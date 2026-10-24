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
