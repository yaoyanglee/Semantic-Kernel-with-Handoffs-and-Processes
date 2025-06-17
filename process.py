import os
import asyncio
import configparser
from enum import Enum
from typing import ClassVar
import pandas as pd

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
    service_id="AppointmentBooking",
    api_key=API_KEY,
    endpoint=ENDPOINT,
    deployment_name=DEPLOYMENT_NAME
)


class PatientInfoStep(KernelProcessStep):
    @kernel_function
    async def handle_patient_info(self):
        name = self.get_patient_name()
        appt_time = self.get_appt_time()

        patient_info = self.get_patient_info(name)
        patient_info['appointment_time'] = appt_time

        return patient_info

    def get_patient_name(self):
        '''
        Asks for the users' age and gender and returns it

        Parameters:
            None

        Returns:
            user_input (str): A string containing the users' age and gender
        '''

        user_input = input("What is your name? ")

        return user_input

    def get_appt_time(self):
        '''
        Asks for the users' appointment time

        Parameters:
            None

        Returns:
            user_input (str): A string containing the users' age and gender
        '''

        user_input = input(
            "What time would you like to schedule the appointment? ")

        return user_input

    def get_patient_info(self, name):
        patient_filepath = r"C:\Users\yylee\OneDrive\Desktop\synapxe\playground\agent_evaluation\patient_data_information.xlsx"

        try:
            df = pd.read_excel(patient_filepath, engine='openpyxl')
            print
            # Check if necessary columns exist
            required_columns = {"patient_name",
                                "age", "gender", "is_vaccinated"}
            if not required_columns.issubset(df.columns):
                return {"error": "Missing required columns in the dataset."}

            # Search for patient
            patient_row = df[df["patient_name"].str.lower() ==
                             name.lower()]

            if patient_row.empty:
                return {"error": f"No data found for patient '{name}'."}

            # Extract required details
            age = patient_row["age"].values[0]
            gender = patient_row["gender"].values[0]
            is_vaccinated = patient_row["is_vaccinated"].values[0]

            result = {
                "patient_name": name,
                "age": age,
                "gender": gender,
                "is_vaccinated": is_vaccinated
            }

            return result

        except Exception as e:
            print("Error: ", e)

            return None


class RetrieveVaccineInfoStep(KernelProcessStep):
    @kernel_function
    async def retrieve_vaccine_info(self, patient_info):
        if patient_info is not None:
            vaccine_path = r"C:\Users\yylee\OneDrive\Desktop\synapxe\playground\agent_evaluation\vaccine_list.xlsx"

            print(patient_info)

            try:
                df = pd.read_excel(vaccine_path, engine='openpyxl')

                # Filter based on age range and gender
                filtered_df = df[(df['age_floor'] <= patient_info['age']) & (df['age_ceiling'] > patient_info['age']) & (
                    df['gender'].str.lower() == patient_info['gender'].lower())]

                # Extract and return the list of vaccines
                if not filtered_df.empty:
                    vaccines = filtered_df['vaccine_list'].values[0]
                    vaccines = vaccines.split(', ')

                    result = {
                        'vaccines': vaccines,
                        'appointment_time': patient_info['appointment_time']
                    }

                    return result

                else:
                    result = "There are no vaccines eligible for the current patient."
                    return None

            except Exception as e:
                print(f"Error reading the file: {e}")
                result = "There are no vaccines eligible for the current patient, due to an error when reading the file."
                return None

        else:
            print(
                "No vaccine information found for the current patient. Please check the patient name")
            return None


class BookingStep(KernelProcessStep):
    @kernel_function
    async def handle_booking(self, vaccine_info):
        # print(vaccine_info)

        vaccines_list = vaccine_info['vaccines']
        appt_time = vaccine_info['appointment_time']

        booking_slots = self.retrieve_booking_slots()

        user_vaccine_request = self.retrieve_desired_vaccine()

        if user_vaccine_request in vaccines_list:
            if appt_time in booking_slots:
                result = f"Successfully booked vaccination slot at {appt_time} for the vaccine, {user_vaccine_request}"
                print(result)
                return {'status': 'Success'}
            else:
                print(
                    f"The appointment time: {appt_time} is not available please give another time or check that the formating is similar to, 9am")
                print(f"Available time slots: {booking_slots}")
                return {'status': 'Failure'}

        else:
            print(
                f"You are not eligible for the vaccine. {user_vaccine_request}")
            return {'status': 'Failure'}

    def retrieve_booking_slots(self):
        """Retrieve available vaccination booking slots.

        This function provides a list of time slots currently open for booking.

        Returns:
            list: A list of available booking time slots.
        """
        booking_slots = ['2pm', '4pm', '5pm', '9am', '3pm']

        return booking_slots

    def retrieve_desired_vaccine(self):
        '''
        Asks for the users' appointment time

        Parameters:
            None

        Returns:
            user_input (str): A string containing the users' age and gender
        '''

        user_input = input(
            "What vaccine would you like to book a vaccination for? ")

        return user_input


kernel = Kernel()
kernel.add_service(model)


async def booking_process():
    '''
    Creates the appointment booking process. Key steps:
    - Create and add steps to the process object
    - Define transition conditions, i.e. End of the current step and when to transition to the next step in the process
    - Building the process
    - Running the entire process

    Parameters:
        None

    Returns:
        None
    '''

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
        "handle_patient_info").send_event_to(target=retrieve_vaccine_info_step, parameter_name="patient_info",)

    retrieve_vaccine_info_step.on_function_result(
        "retrieve_vaccine_info").send_event_to(target=booking_step, parameter_name="vaccine_info")

    booking_step.on_function_result("handle_booking").stop_process()

    # Build the kernel process with the process state initialized
    kernel_process = process.build()

    # Start the process
    await start(
        process=kernel_process,
        kernel=kernel,
        initial_event=KernelProcessEvent(
            # id here should be the same as the if in 'on_input_event'
            id="Start appointment booking", task='Make a vaccination appointment booking'),
    )

# if __name__ == "__main__":
#     asyncio.run(booking_process())
