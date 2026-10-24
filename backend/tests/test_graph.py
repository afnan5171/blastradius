from types import SimpleNamespace as Obj
from app.graph import *


def account(id, **kw):
    return Obj(
        id=id,
        service_name=id,
        importance="High",
        category="Email",
        has_mfa=False,
        has_passkey=False,
        **kw
    )


def relation(a, b, id="r", type="PASSWORD_RESET", weight=10):
    return Obj(
        id=id,
        source_account_id=a,
        target_account_id=b,
        relationship_type=type,
        risk_weight=weight,
    )


def sample():
    return build_graph(
        [account(x) for x in "abcd"], [relation("a", "b"), relation("b", "c", "s")]
    )


def test_traversal():
    g = sample()
    assert calculate_reachable_accounts(g, "a") == ["b", "c"]
    assert calculate_reachable_accounts(g, "c") == []
    assert "d" in g
    assert calculate_shortest_attack_paths(g, "a")[1]["account_ids"] == ["a", "b", "c"]


def test_parallel_relationships():
    g = build_graph(
        [account(x) for x in "ab"],
        [relation("a", "b"), relation("a", "b", "s", "OAUTH_READ_ACCESS", 6)],
    )
    assert g.number_of_edges() == 2
    assert calculate_shortest_attack_paths(g, "a")[0]["relationship_ids"] == ["r"]


def test_cycles_and_chokepoints():
    g = sample()
    g.add_edge("b", "a", id="back", relationship_type="RECOVERY_EMAIL", risk_weight=9)
    assert find_circular_dependencies(g) == [["a", "b"]]
    assert find_security_chokepoints(g)[0]["dependent_accounts"] == 2
    assert find_circular_dependencies(sample()) == []


def test_scoring_and_protection():
    g = sample()
    base = calculate_blast_radius_score(g, "a")
    assert 0 < base <= 100
    g.nodes["a"]["account"].has_mfa = True
    mfa = calculate_blast_radius_score(g, "a")
    assert mfa < base
    g.nodes["a"]["account"].has_passkey = True
    assert calculate_blast_radius_score(g, "a") < mfa
    assert calculate_blast_radius_score(g, "d") == 0
    assert (
        calculate_account_risk_scores(g)[0]["score"]
        >= calculate_account_risk_scores(g)[-1]["score"]
    )


def test_destination_protection_and_weights():
    g = sample()
    base = calculate_blast_radius_score(g, "a")
    g.nodes["b"]["account"].has_passkey = True
    assert calculate_blast_radius_score(g, "a") < base
    g["a"]["b"]["r"]["risk_weight"] = 1
    assert calculate_blast_radius_score(g, "a") < base
    assert [risk_level(v) for v in [20, 21, 40, 41, 60, 61, 80, 81]] == [
        "Low",
        "Moderate",
        "Moderate",
        "Elevated",
        "Elevated",
        "High",
        "High",
        "Critical",
    ]


def test_recommendations():
    g = sample()
    recs = generate_recommendations(g, "a")
    assert len(recs) == 3 and recs == generate_recommendations(g, "a")
    assert any(r["kind"] == "single_recovery" for r in recs)
    g.add_edge("b", "a", id="back", relationship_type="RECOVERY_EMAIL", risk_weight=9)
    assert generate_recommendations(g, "a")[0]["kind"] == "recovery_loop"


def test_shared_password_recommendation():
    g = build_graph(
        [account(x) for x in "ab"], [relation("a", "b", type="SHARED_PASSWORD")]
    )
    assert generate_recommendations(g, "a")[0]["kind"] == "shared_password"
