from semantiva.context_processors.context_types import (
    ContextType,
    ContextCollectionType,
)
from semantiva.context_processors.context_observer import ContextObserver


def test_initialize_with_predefined_local_contexts():
    """Ensure ContextCollectionType initializes correctly with predefined local contexts."""
    global_context = {"key_global": "global_value"}
    local_contexts = [
        ContextType({"key1": "value1"}),
        ContextType({"key2": "value2"}),
        ContextType({"key3": "value3"}),
    ]

    collection_context = ContextCollectionType(global_context, local_contexts)

    assert len(collection_context) == 3
    assert collection_context.to_dict()["global"] == {"key_global": "global_value"}
    assert collection_context.to_dict()["locals"] == [
        {"key1": "value1"},
        {"key2": "value2"},
        {"key3": "value3"},
    ]


def test_append_local_context():
    """Ensure new local contexts can be appended after initialization."""
    collection_context = ContextCollectionType({"key_global": "global_value"})

    collection_context.append(ContextType({"key1": "value1"}))
    collection_context.append(ContextType({"key1": "value2"}))

    assert len(collection_context) == 2
    assert collection_context.to_dict()["locals"] == [
        {"key1": "value1"},
        {"key1": "value2"},
    ]


def test_get_value():
    """Ensure get_value correctly retrieves values from global and local contexts."""
    collection_context = ContextCollectionType(
        {"global_key": "global_value"},
        [
            ContextType({"local_key_1": "value1"}),
            ContextType({"local_key_2": "value2"}),
        ],
    )

    assert collection_context.get_value("global_key") == "global_value"
    assert collection_context.get_value("local_key_1")[1] is None


def test_update_single_slice():
    """Ensure updates to a specific slice do not affect global context."""
    collection_context = ContextCollectionType(
        {"global_key": "global_value"},
        [ContextType({"local_key": "initial_value"}), ContextType({})],
    )

    ContextObserver.update_context(
        collection_context, "local_key", "updated_value", index=0
    )

    assert collection_context.to_dict()["locals"][0]["local_key"] == "updated_value"
    assert collection_context.get_value("local_key")[1] is None
