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
