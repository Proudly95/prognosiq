import asyncio

from asyncua import Client


async def main() -> None:
    async with Client("opc.tcp://localhost:4840/prognosiq/simulator/") as client:
        fleet = await client.nodes.objects.get_child(["2:Fleet"])
        machine = await fleet.get_child(["2:Machine-01"])
        for name in ("rpm", "temperature_c", "vibration_mm_s"):
            node = await machine.get_child([f"2:{name}"])
            print(name, await node.read_value())


asyncio.run(main())
