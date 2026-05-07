from typing import Dict, List


def build_reporting_chain(relationships: Dict[str, str]) -> Dict[str, List[str]]:
    chain: Dict[str, List[str]] = {}
    for child, parent in relationships.items():
        chain.setdefault(parent, []).append(child)
    return chain
