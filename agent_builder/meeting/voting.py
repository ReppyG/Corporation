from dataclasses import dataclass
from typing import Dict, List


@dataclass
class VotingResult:
    question: str
    tally: Dict[str, int]
    winner: str


def conduct_vote(question: str, options: List[str], ballots: List[str]) -> VotingResult:
    tally = {o: 0 for o in options}
    for vote in ballots:
        if vote in tally:
            tally[vote] += 1
    winner = max(tally, key=tally.get)
    return VotingResult(question=question, tally=tally, winner=winner)
