import asyncio
import sys
from pathlib import Path

from asyncua import Server

from simulator.config import SimulatorConfig, load_config
from simulator.degradation import next_state, read_sensors
from simulator.fleet import build_fleet

NAMESPACE_URI = "https://prognosiq.dev/simulator"


async def run(cfg: SimulatorConfig) -> None:
    """Serve the configured fleet over OPC-UA until cancelled."""
    server = Server()
    await server.init()
    server.set_endpoint(cfg.endpoint)
    idx = await server.register_namespace(NAMESPACE_URI)

    fleet = await server.nodes.objects.add_object(idx, "Fleet")
    states = build_fleet(cfg)
    sensor_nodes = {}
    health_nodes = {}
    for st in states:
        obj = await fleet.add_object(idx, st.name)
        sensor_nodes[st.name] = {
            s: await obj.add_variable(idx, s, v) for s, v in read_sensors(st).items()
        }
        # identity properties: the #12 collector reads these to build
        # MQTT topics (prognosiq/orgs/{org}/assets/{asset}/telemetry)
        health_nodes[st.name] = await obj.add_property(idx, "Health", st.health)
        await obj.add_property(idx, "OrgId", st.org_id)
        await obj.add_property(idx, "AssetId", st.asset_id)
        await obj.add_property(idx, "AssetType", st.profile.asset_type)

    print(f"Simulator serving {len(states)} machines at {cfg.endpoint} - Ctrl+c to stop")
    await server.start()
    try:
        while True:
            for st in states:
                next_state(st)
                values = read_sensors(st)
                for s, node in sensor_nodes[st.name].items():
                    await node.write_value(values[s])
                await health_nodes[st.name].write_value(st.health)
            await asyncio.sleep(cfg.interval_s)
    finally:
        await server.stop()


async def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("config.toml")
    await run(load_config(path))


if __name__ == "__main__":
    asyncio.run(main())
