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
from semantiva.data_types.data_types import BaseDataType, DataCollectionType


# Mock Classes for Testing
class MockBaseData(BaseDataType[float]):
    def validate(self, data: float) -> bool:
        return isinstance(data, float)


class MockCollection(DataCollectionType[MockBaseData, list]):
    @classmethod
    def _initialize_empty(cls) -> list:
        return []

    def validate(self, data: list) -> bool:
        return all(isinstance(item, MockBaseData) for item in data)

    def __iter__(self):
        return iter(self._data)

    def append(self, item: MockBaseData) -> None:
        if not isinstance(item, MockBaseData):
            raise TypeError("Item must be of type MockBaseData")
        self._data.append(item)

    def __len__(self) -> int:
        return len(self._data)


# Test Cases
def test_base_data_type_initialization():
    data = 5.0
    base_data = MockBaseData(data)
    assert base_data.data == data


def test_data_collection_initialization():
    collection = MockCollection()
    assert len(collection) == 0


def test_data_collection_append():
    collection = MockCollection()
    item = MockBaseData(1.0)
    collection.append(item)
    assert len(collection) == 1
    assert collection._data[0] == item


def test_data_collection_append_invalid_type():
    collection = MockCollection()
    with pytest.raises(TypeError):
        collection.append("invalid_item")


def test_data_collection_iteration():
    collection = MockCollection()
    items = [MockBaseData(1.0), MockBaseData(2.0), MockBaseData(3.0)]
    for item in items:
        collection.append(item)
    assert list(collection) == items


def test_data_collection_from_list():
    items = [MockBaseData(1.0), MockBaseData(2.0), MockBaseData(3.0)]
    collection = MockCollection.from_list(items)
    assert len(collection) == len(items)
    assert list(collection) == items


if __name__ == "__main__":
    pytest.main()
