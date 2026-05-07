from agent_builder.hierarchy.reporting import build_reporting_chain


def test_reporting_chain_builder():
    chain = build_reporting_chain({"coder1": "eng-head", "coder2": "eng-head"})
    assert chain["eng-head"] == ["coder1", "coder2"]
