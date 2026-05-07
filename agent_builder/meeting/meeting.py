from typing import List

from agent_builder.meeting.agenda import Agenda, AgendaItem
from agent_builder.meeting.transcript import MeetingTranscript
from agent_builder.meeting.voting import VotingResult, conduct_vote


class Meeting:
    def __init__(self, meeting_id: str, agenda: Agenda, participants: List):
        self.meeting_id = meeting_id
        self.agenda = agenda
        self.participants = participants

    def add_agenda_item(self, item: AgendaItem):
        self.agenda.add_item(item)

    def run(self) -> MeetingTranscript:
        transcript = MeetingTranscript(meeting_id=self.meeting_id)
        for item in self.agenda.items:
            transcript.add_record(
                {
                    "agenda_item": item.title,
                    "participants": [p.agent_id for p in self.participants],
                    "status": "discussed",
                }
            )
        return transcript

    def vote(self, question: str, options: List[str]) -> VotingResult:
        ballots = []
        for participant in self.participants:
            vote_fn = getattr(participant, "vote", None)
            if callable(vote_fn):
                choice = vote_fn(question, options)
                ballots.append(choice if choice in options else options[0])
            else:
                ballots.append(options[0])
        return conduct_vote(question=question, options=options, ballots=ballots)
