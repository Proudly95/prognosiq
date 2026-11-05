import asyncio

from asyncua import Server

from simulator.degradation import MachineState, next_state, read_sensors


async def main() -> None:
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/prognosiq/simulator/")
    idx = await server.register_namespace("https://prognosiq.dev/simulator")

    fleet = await server.nodes.objects.add_object(idx, "Fleet")
    state = MachineState(name="Machine-01")
    machine = await fleet.add_object(idx, state.name)
    sensors = {
        name: await machine.add_variable(idx, name, value)
        for name, value in read_sensors(state).items()
    }

    print("Simulator serving at opc.tcp://localhost:4840 -Ctrl+c to stop")
    await server.start()
    try:
        while True:
            next_state(state)
            values = read_sensors(state)
            for name, node in sensors.items():
                await node.write_value(values[name])
            await asyncio.sleep(1.0)
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
