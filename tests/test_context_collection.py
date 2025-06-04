# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
from semantiva.context_processors.context_types import (
    ContextType,
    ContextCollectionType,
)


def test_empty_collection():
    collection = ContextCollectionType(context_list=[])
    assert len(collection) == 0
    with pytest.raises(IndexError):
        _ = collection[0]


def test_collection_indexing_and_iteration():
    # Create two individual contexts with unique keys.
    ctx1 = ContextType({"key1": "value1"})
    ctx2 = ContextType({"key2": "value2"})
    collection = ContextCollectionType(context_list=[ctx1, ctx2])

    # Since the global context is empty, the merged view should equal the individual context.
    merged1 = collection[0]
    merged2 = collection[1]
    assert merged1.get_value("key1") == "value1"
    assert merged2.get_value("key2") == "value2"

    # Test iteration over the collection.
    items = [item for item in collection]
    assert len(items) == 2


def test_collection_with_global_context():
    # Define a global context and an individual context with non-overlapping keys.
    global_context = {"global_key": "global_value"}
    item_context = ContextType({"item_key": "item_value"})
    collection = ContextCollectionType(
        global_context=global_context, context_list=[item_context]
    )

    merged = collection[0]
    # Global keys should be available alongside the individual context keys.
    assert merged.get_value("global_key") == "global_value"
    assert merged.get_value("item_key") == "item_value"


def test_overlapping_keys_raise_error():
    # Define a global context and an individual context with an overlapping key.
    global_context = {"overlap": "global_value"}
    item_context = ContextType({"overlap": "item_value", "other": "value"})
    collection = ContextCollectionType(
        global_context=global_context, context_list=[item_context]
    )

    with pytest.raises(ValueError):
        _ = collection.get_item(0)


def test_append_and_type_validation():
    ctx1 = ContextType({"a": 1})
    collection = ContextCollectionType(context_list=[ctx1])
    assert len(collection) == 1

    ctx2 = ContextType({"b": 2})
    collection.append(ctx2)
    assert len(collection) == 2

    # Verify that appending a non-ContextType raises a TypeError.
    with pytest.raises(TypeError):
        collection.append("not a ContextType")


def test_get_value_demonstration():
    # Global context with some scientific metadata.
    global_context = {"global_info": "Earth Science", "unit": "meters"}
    # Individual contexts with measurement data.
    measurement1 = ContextType({"local_info": 42, "precision": 0.01})
    measurement2 = ContextType(
        {
            "local_info": 100,
            "precision": 0.02,
            "key_unique_for_item_2": "This is measurement 2",
        }
    )

    collection = ContextCollectionType(
        global_context=global_context, context_list=[measurement1, measurement2]
    )

    # a. Retrieving keys defined only in the global context returns single values.
    assert collection.get_value("global_info") == "Earth Science"
    assert collection.get_value("unit") == "meters"

    # b. Retrieving an individual key ('local_info') returns a list of values.
    local_info_val = collection.get_value("local_info")
    assert isinstance(local_info_val, list)
    assert local_info_val == [42, 100]

    # c. Retrieving a key defined only in one individual context returns a list with None for missing values.
    unique_val = collection.get_value("key_unique_for_item_2")
    assert isinstance(unique_val, list)
    assert unique_val == [None, "This is measurement 2"]

    # d. Retrieving a non-existent key returns None.
    assert collection.get_value("unknown") is None


def test_set_value_demonstration():
    # Global context with metadata.
    global_context = {"global_info": "Earth Science", "unit": "meters"}
    # Individual contexts with measurement values.
    measurement1 = ContextType({"local_info": 42, "precision": 0.01})
    measurement2 = ContextType({"local_info": 100, "precision": 0.02})

    collection = ContextCollectionType(
        global_context=global_context, context_list=[measurement1, measurement2]
    )

    # a. Update the global key in the collection.
    collection.set_value("global_info", "Atmospheric Science")
    assert collection.get_value("global_info") == "Atmospheric Science"

    # b. Set a new global key in the collection.
    collection.set_value("planet", "Venus")
    assert collection.get_value("planet") == "Venus"

    # c. Update an individual key for the first context using set_item_value.
    collection.set_item_value(0, "local_info", 123)
    local_val = collection.get_value("local_info")
    assert local_val == [123, 100]

    # d. Update an individual key for all contexts using set_value.
    collection.set_value("local_info", 84)
    local_val_updated = collection.get_value("local_info")
    assert local_val_updated == [84, 84]
