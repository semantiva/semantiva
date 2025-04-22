from semantiva.execution_tools.transport import InMemorySemantivaTransport


def test_publish_and_subscribe_order():
    transport = InMemorySemantivaTransport()
    # Publish two messages under the same subject
    transport.publish("subjA", 100, {"x": 1})
    transport.publish("subjA", 200, {"y": 2})

    # Subscribe drains in FIFO order
    items = list(transport.subscribe("subjA"))
    assert items == [(100, {"x": 1}), (200, {"y": 2})]

    # Subsequent subscribe yields nothing
    assert list(transport.subscribe("subjA")) == []


def test_multiple_subjects_isolated():
    transport = InMemorySemantivaTransport()
    transport.publish("s1", "foo", {})
    transport.publish("s2", "bar", {})

    assert list(transport.subscribe("s1")) == [("foo", {})]
    assert list(transport.subscribe("s2")) == [("bar", {})]
    # s1 remains empty
    assert list(transport.subscribe("s1")) == []
