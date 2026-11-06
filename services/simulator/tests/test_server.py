"""Integration tests: boot the real server via run(cfg), poke it over OPC-UA."""

import asyncio

import pytest
from asyncua import Client
from simulator.config import MachineConfig, SimulatorConfig
from simulator.main import run

ENDPOINT = "opc.tcp://127.0.0.1:48410/prognosiq/simulator/test"


def make_cfg() -> SimulatorConfig:
    return SimulatorConfig(
        endpoint=ENDPOINT,
        interval_s=0.01,
        machines=[
            MachineConfig(
                name="TestPump-01",
                org_id="org-1",
                asset_id="asset-101",
                asset_type="pump",
            ),
            MachineConfig(
                name="TestTurbofan-01", org_id="org-1", asset_id="asset-102", asset_type="turbofan"
            ),
        ],
    )


async def wait_until_accepting(url: str, attempts: int = 50) -> None:
    """run() runs as a background task, so the socket is not bound
    instantly -- poll with throwaway client connections until one lands."""
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            client = Client(url)
            await client.connect()
            await client.disconnect()
            return
        except Exception as exc:
            last_exc = exc
            await asyncio.sleep(0.02)
    raise RuntimeError(f"server never came up at {url}: {last_exc}")


@pytest.fixture
async def server_url() -> str:
    task = asyncio.create_task(run(make_cfg()))
    await wait_until_accepting(ENDPOINT)
    yield ENDPOINT
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


async def test_server_boots_and_fleet_is_browsable(server_url):
    async with Client(server_url) as client:
        fleet = await client.nodes.objects.get_child("2:Fleet")
        machines = await fleet.get_children()
        names = sorted([(await m.read_browse_name()).Name for m in machines])
        assert names == ["TestPump-01", "TestTurbofan-01"]
        for machine in machines:
            children = await machine.get_children()
            labels = sorted([(await c.read_browse_name()).Name for c in children])
            assert labels == [
                "AssetId",
                "AssetType",
                "Health",
                "OrgId",
                "rpm",
                "temperature_c",
                "vibration_mm_s",
            ]


async def test_identity_properties(server_url):
    async with Client(server_url) as client:
        fleet = await client.nodes.objects.get_child("2:Fleet")
        pump = await fleet.get_child("2:TestPump-01")
        assert await (await pump.get_child("2:OrgId")).read_value() == "org-1"
        assert await (await pump.get_child("2:AssetId")).read_value() == "asset-101"
        assert await (await pump.get_child("2:AssetType")).read_value() == "pump"


async def test_values_change_and_health_decays(server_url):
    async with Client(server_url) as client:
        fleet = await client.nodes.objects.get_child("2:Fleet")
        pump = await fleet.get_child("2:TestPump-01")
        rpm = await pump.get_child("2:rpm")
        health = await pump.get_child("2:Health")
        rpm_before = await rpm.read_value()
        health_before = await health.read_value()
        await asyncio.sleep(0.5)  # ~50 ticks at interval_s = 0.01
        rpm_after = await rpm.read_value()
        health_after = await health.read_value()
        assert rpm_after != rpm_before  # gauge is live
        assert health_after < health_before  # battery is draining
