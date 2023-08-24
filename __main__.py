import asyncio

from equipment import Equipment

# Configure logging
# logging.basicConfig(filename="equipment.log", level=logging.ERROR)


async def main():
    equipment = Equipment()
    modbus_task = asyncio.create_task(equipment.startModbusServer())

    try:
        while True:
            equipment.cycle()
            print(equipment.battery.current)
            await asyncio.sleep(
                1
            )  # Add a sleep to yield control to other tasks
    except KeyboardInterrupt:
        print("Simulation terminated.")
    finally:
        modbus_task.cancel()  # Stop the Modbus server task when the main loop exits


if __name__ == "__main__":
    asyncio.run(main())
