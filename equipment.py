import datetime
import logging

import pybamm
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.server import ModbusTcpServer

from battery import Battery


class Equipment:
    def __init__(self):
        # Initialize the Battery
        self.battery = Battery()
        self.start_date = (
            datetime.datetime.timestamp(datetime.datetime.now()) * 1000
        )

        # Initialize the Battery simulation model
        self.battery_model = pybamm.lithium_ion.DFN()
        self.simulation = pybamm.Simulation(self.battery_model)

        # Initialize Modbus server
        self.init_modbus_server()

    def init_modbus_server(self):
        # Create a context for the Modbus server
        store = ModbusSlaveContext(
            hr=ModbusSequentialDataBlock(0, [0] * 100),  # Holding registers
            ir=ModbusSequentialDataBlock(4000, [0] * 100),  # Input registers
        )
        self.context = ModbusServerContext(slaves=store, single=True)

        # Start the Modbus server in a separate thread
        self.server = ModbusTcpServer(
            context=self.context,
            address=(
                "0.0.0.0",
                5020,
            ),  # Listen on all available network interfaces, port 5020
        )

    def cycle(self):
        try:
            current_timestamp = (
                datetime.datetime.timestamp(datetime.datetime.now()) * 1000
            )
            timestamp = current_timestamp - self.start_date
            self.update_battery(timestamp)
            self.update_input_registers()
        except pybamm.SolverError as e:
            logging.error(f"Error updating battery - SolverError: {str(e)}")
        except ValueError as e:
            logging.error(f"Error updating battery - ValueError: {str(e)}")
        except Exception as e:
            logging.error(f"Error in cycle: {str(e)}")

    def update_battery(self, timestamp):
        try:
            solution = self.simulation.solve([timestamp, timestamp + 1])
            self.battery.voltage = solution["Terminal voltage [V]"].data[-1]
            self.battery.current = solution["Current [A]"].data[-1]
            self.battery.temperature = solution["Cell temperature [K]"].data[
                -1
            ]
            self.battery.soc = (
                100.0
                * solution["Discharge capacity [A.h]"].data[-1]
                / solution["Total lithium capacity [A.h]"].data[-1]
            )

        except pybamm.SolverError as e:
            logging.error(f"Error updating battery - SolverError: {str(e)}")
        except ValueError as e:
            logging.error(f"Error updating battery - ValueError: {str(e)}")
        except Exception as e:
            logging.error(f"Error updating battery: {str(e)}")

    def update_input_registers(self):
        try:
            # Expose battery values to Modbus input registers

            # Define the addresses of the registers you want to update
            register_addresses = [4001, 4002, 4003]

            # Define the corresponding values
            values = [
                int(self.battery.voltage * 100),
                int(self.battery.current * 100),
                int(self.battery.soc),
            ]

            # Update Modbus input registers with the battery values
            for i in range(len(register_addresses)):
                self.context[0].setValues(
                    4, register_addresses[i], [values[i]]
                )

        except Exception as e:
            logging.error(f"Error updating input registers: {str(e)}")

    async def startModbusServer(self):
        try:
            await self.server.serve_forever()
        except Exception as e:
            logging.error(f"Error starting Modbus server: {str(e)}")
            raise  # Re-raise the exception to propagate it
