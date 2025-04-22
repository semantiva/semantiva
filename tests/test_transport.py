# tests/test_transport.py

from semantiva.execution_tools.transport.in_memory import InMemorySemantivaTransport
from semantiva.execution_tools.transport.base import Message


def extract_data_context(messages):
    """Helper to extract (data, context) from Message objects."""
    return [(msg.data, msg.context) for msg in messages]


def test_publish_and_subscribe_order():
    transport = InMemorySemantivaTransport()
    transport.connect()

    transport.publish("subjA", 100, {"x": 1})
    transport.publish("subjA", 200, {"y": 2})

    subscription = transport.subscribe("subjA")
    items = extract_data_context(subscription)
    subscription.close()

    assert items == [(100, {"x": 1}), (200, {"y": 2})]

    subscription2 = transport.subscribe("subjA")
    assert extract_data_context(subscription2) == []
    subscription2.close()

    transport.close()


def test_multiple_subjects_isolated():
    transport = InMemorySemantivaTransport()
    transport.connect()

    transport.publish("s1", "foo", {})
    transport.publish("s2", "bar", {})

    assert extract_data_context(transport.subscribe("s1")) == [("foo", {})]
    assert extract_data_context(transport.subscribe("s2")) == [("bar", {})]
    # s1 remains empty
    assert extract_data_context(transport.subscribe("s1")) == []

    transport.close()
