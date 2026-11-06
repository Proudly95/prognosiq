import asyncio

from asyncua import Client


async def main() -> None:
    async with Client("opc.tcp://localhost:4840/prognosiq/simulator/") as client:
        fleet = await client.nodes.objects.get_child("2:Fleet")
        for machine in await fleet.get_children():
            name = (await machine.read_browse_name()).Name
            print(f"{name}:")
            for child in await machine.get_children():
                label = (await child.read_browse_name()).Name
                print(f"  {label} = {await child.read_value()}")


asyncio.run(main())
