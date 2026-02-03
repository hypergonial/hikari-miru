import arc
import hikari
import pytest

import miru

bot = hikari.GatewayBot("MzA4MjkzNjAzNTMxMjkyNjcy.DN9r_A.amogus", banner=None)
client = miru.Client(bot)


class Dummy:
    def __init__(self, val: int):
        self.val = val


client.set_type_dependency(Dummy, Dummy(0))


@client.inject_dependencies
def dummy_callback(dummy: Dummy = miru.inject()) -> int:
    dummy.val += 1
    return dummy.val


@client.inject_dependencies
async def async_dummy_callback(dummy: Dummy = miru.inject()) -> int:
    dummy.val += 1
    return dummy.val


@client.inject_dependencies
def injects_client(client: miru.Client = miru.inject()) -> miru.Client:
    return client


injector = miru.Injector()
injector.set_type_dependency(Dummy, Dummy(0))

manually_injected_client = miru.Client(bot, injector=injector)


@manually_injected_client.inject_dependencies
def manual_dummy_callback(dummy: Dummy = miru.inject()) -> int:
    dummy.val += 1
    return dummy.val


arc_c = arc.GatewayClient(bot)
arc_c.set_type_dependency(Dummy, Dummy(0))
arc_miru_c = miru.Client.from_arc(arc_c)


@arc_miru_c.inject_dependencies
def arc_miru_c_callback(dummy: Dummy = miru.inject()) -> int:
    dummy.val += 1
    return dummy.val


@pytest.mark.asyncio
async def test_inject() -> None:
    assert dummy_callback() == 1
    assert await async_dummy_callback() == 2
    assert dummy_callback() == 3
    assert injects_client() is client

    assert manual_dummy_callback() == 1
    assert manual_dummy_callback() == 2

    assert arc_miru_c_callback() == 1
    assert arc_miru_c_callback() == 2
