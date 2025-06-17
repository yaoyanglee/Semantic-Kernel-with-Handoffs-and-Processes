import os
import asyncio
import configparser
from enum import Enum
from typing import ClassVar

from pydantic import Field

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from semantic_kernel.processes.process_builder import ProcessBuilder

# Setting up environment variables
# --- Load all configuration settings ---
config = configparser.ConfigParser()
# config.read(
#     r'./config.prop')
config_path = os.path.join(os.path.dirname(__file__), "config.prop")
config.read(config_path)

os.environ["AZURE_OPENAI_ENDPOINT"] = config['azure_openai_gpt4o-mini']['endpoint']
os.environ["AZURE_OPENAI_API_KEY"] = config['azure_openai_gpt4o-mini']['api_key']
DEPLOYMENT_NAME = config['azure_openai_gpt4o-mini']['deployment']
ENDPOINT = config['azure_openai_gpt4o-mini']['endpoint']
API_KEY = config['azure_openai_gpt4o-mini']['api_key']
API_VERSION = config['azure_openai_gpt4o-mini']['api_version']

model = AzureChatCompletion(
    service_id="default",
    api_key=API_KEY,
    endpoint=ENDPOINT,
    deployment_name=DEPLOYMENT_NAME
)


class PatientInfoStep(KernelProcessStep):
    @kernel_function
    async def handle_patient_info(self):
        # user_query = self.get_patient_info()
        print("Get user info")

    def get_patient_info(self):
        '''
        Asks for the users' age and gender and returns it

        Parameters:
            None

        Returns:
            user_input (str): A string containing the users' age and gender
        '''

        user_input = input("Please let me know your age and gender")

        return user_input


class RetrieveVaccineInfoStep(KernelProcessStep):
    @kernel_function
    async def retrieve_vaccine_info(self):
        print("Get vaccine info")


class BookingStep(KernelProcessStep):
    @kernel_function
    async def handle_booking(self):
        print("Perform booking")


kernel = Kernel()


async def booking_process():
    kernel.add_service(model)

    process = ProcessBuilder(name="VaccinationBooking")

    # Defining all steps in the process
    patient_info_step = process.add_step(PatientInfoStep)
    retrieve_vaccine_info_step = process.add_step(RetrieveVaccineInfoStep)
    booking_step = process.add_step(BookingStep)

    # Defining entry point for the process
    process.on_input_event(
        # id should be the same as 'initial_event' in start
        event_id="Start appointment booking").send_event_to(target=patient_info_step)

    # Defining the sequential steps after the entry point
    patient_info_step.on_function_result(
        "handle_patient_info").send_event_to(retrieve_vaccine_info_step)
    retrieve_vaccine_info_step.on_function_result(
        "retrieve_vaccine_info").send_event_to(booking_step)
    booking_step.on_function_result("handle_booking").stop_process()

    # Build the kernel process
    kernel_process = process.build()

    # Start the process
    await start(
        process=kernel_process,
        kernel=kernel,
        initial_event=KernelProcessEvent(
            # id here should be the same as the if in 'on_input_event'
            id="Start appointment booking", data="I want to book a flu vaccine"),
    )

if __name__ == "__main__":
    # if you want to run this sample with your won input, set the below parameter to False
    asyncio.run(booking_process())
