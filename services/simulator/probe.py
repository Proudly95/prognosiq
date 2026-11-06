import asyncio

from asyncua import Client


async def main() -> None:
    # host port 4841: the container publishes 4841 because an OPC-UA Local
    # Discovery Server (opcualds.exe) owns 4840 on the Windows side
    async with Client("opc.tcp://localhost:4841/prognosiq/simulator/") as client:
        fleet = await client.nodes.objects.get_child("2:Fleet")
        for machine in await fleet.get_children():
            name = (await machine.read_browse_name()).Name
            print(f"{name}:")
            for child in await machine.get_children():
                label = (await child.read_browse_name()).Name
                print(f"  {label} = {await child.read_value()}")


asyncio.run(main())
