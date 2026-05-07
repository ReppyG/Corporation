from agent_builder.core.communication import MessageBus


def test_message_send_and_get_inbox():
    bus = MessageBus()
    bus.send_message("a", "b", "hello")
    inbox = bus.get_inbox("b")
    assert len(inbox) == 1
    assert inbox[0].message == "hello"
