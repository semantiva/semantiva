import pytest
from semantiva.context_processors.context_types import (
    ContextType,
    ContextCollectionType,
)


def test_context_type():
    context = ContextType()
    assert context.get_value("key") is None

    context.set_value("key", "value")
    assert context.get_value("key") == "value"

    context.delete_value("key")
    assert context.get_value("key") is None

    with pytest.raises(KeyError):
        context.delete_value("nonexistent_key")

    context.set_value("key1", "value1")
    context.set_value("key2", "value2")
    assert context.keys() == ["key1", "key2"]
    assert context.values() == ["value1", "value2"]
    assert context.items() == [("key1", "value1"), ("key2", "value2")]

    context.clear()
    assert context.keys() == []


def test_context_collection_type():
    context1 = ContextType({"key1": "value1"})
    context2 = ContextType({"key2": "value2"})
    collection = ContextCollectionType(context_list=[context1, context2])

    assert len(collection) == 2
    assert collection[0] == context1
    assert collection[1] == context2

    context3 = ContextType({"key3": "value3"})
    collection.append(context3)
    assert len(collection) == 3
    assert collection[2] == context3

    with pytest.raises(TypeError):
        collection.append("not a ContextType")

    items = [item for item in collection]
    assert items == [context1, context2, context3]


if __name__ == "__main__":
    pytest.main()
