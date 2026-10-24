import asyncio

import pulumi
import pytest


class RecordingMocks(pulumi.runtime.Mocks):
    """Pulumi-Mocks, die alle registrierten Ressourcen für Assertions mitschreiben."""

    def __init__(self):
        self.resources: list[pulumi.runtime.MockResourceArgs] = []

    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        self.resources.append(args)
        outputs = dict(args.inputs)
        if args.typ == "random:index/randomPassword:RandomPassword":
            outputs["result"] = "mock-password"
        return [f"{args.name}_id", outputs]

    def call(self, args: pulumi.runtime.MockCallArgs):
        return {}, None

    def by_type(self, resource_type: str) -> list[pulumi.runtime.MockResourceArgs]:
        return [r for r in self.resources if r.typ == resource_type]


# Pulumi benötigt ab Python 3.14 einen explizit gesetzten Event-Loop.
asyncio.set_event_loop(asyncio.new_event_loop())

_mocks = RecordingMocks()
pulumi.runtime.set_mocks(_mocks, project="test", stack="test", preview=False)


@pytest.fixture
def mocks() -> RecordingMocks:
    """Liefert die Mocks und leert die aufgezeichneten Ressourcen vor jedem Test."""
    _mocks.resources.clear()
    return _mocks
