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

"""
Test suite for Semantiva's in-memory transport implementation.

Semantiva's transport layer is responsible for moving (data, context) tuples
between pipeline stages or across distributed workers. The core transport API
defines `publish()` and `subscribe()` methods on a `SemantivaTransport`, and
messages are represented by the `Message` namedtuple (data, context, metadata, ack).

This file tests the `InMemorySemantivaTransport`, which is:
  - A simple, dependency-free transport for local development and unit tests.
  - FIFO-ordered per subject (channel) queueing.
  - Wildcard-free, exact subject matching.
  - No-op connect()/close() and ack() semantics.
"""

from semantiva.execution.transport.in_memory import InMemorySemantivaTransport


def extract_data_context(messages):
    """
    Helper to pull out just the (data, context) tuples from an iterator
    of Message objects returned by transport.subscribe().

    Semantiva workers/orchestrators expect each Message to carry:
      - .data:    the main payload
      - .context: the semantic context dict
    """
    return [(msg.data, msg.context) for msg in messages]


def test_publish_and_subscribe_order():
    """
    Verify that InMemorySemantivaTransport:
      - Delivers messages in FIFO order for a single subject.
      - Drains the queue so subsequent subscriptions yield no data.
    """
    transport = InMemorySemantivaTransport()
    transport.connect()  # No-op for in-memory, but part of the API

    # Publish two messages under the same subject/channel
    transport.publish("subjA", 100, {"x": 1})
    transport.publish("subjA", 200, {"y": 2})

    # Subscribe returns a Subscription (iterator over Message)
    subscription = transport.subscribe("subjA")
    # Extract just the (data, context) tuples for assertion
    items = extract_data_context(subscription)
    subscription.close()  # Clean up the subscription

    # Messages must come back in the same order they were published
    assert items == [(100, {"x": 1}), (200, {"y": 2})]

    # After draining, the same subject should yield an empty list
    subscription2 = transport.subscribe("subjA")
    assert extract_data_context(subscription2) == []
    subscription2.close()

    transport.close()  # No-op for in-memory


def test_multiple_subjects_isolated():
    """
    Verify that subjects (channels) are isolated:
      - Publishing to 's1' does not affect 's2' and vice versa.
      - Each subject has its own independent FIFO queue.
    """
    transport = InMemorySemantivaTransport()
    transport.connect()

    # Publish to two different subjects
    transport.publish("s1", "foo", {})
    transport.publish("s2", "bar", {})

    # Subscribe to each and verify isolation
    assert extract_data_context(transport.subscribe("s1")) == [("foo", {})]
    assert extract_data_context(transport.subscribe("s2")) == [("bar", {})]

    # Re-subscribing to 's1' after draining should yield empty again
    assert extract_data_context(transport.subscribe("s1")) == []

    transport.close()
