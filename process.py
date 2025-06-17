import asyncio
from enum import Enum
from typing import ClassVar

from pydantic import Field

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
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

'''
Initialising some dataclasses for the process steps
'''


class CommonEvents(Enum):
    UserInputReceived = "UserInputReceived"
    AssistantResponseGenerated = "AssistantResponseGenerated"


class ChatBotEvents(Enum):
    StartProcess = "startProcess"
    IntroComplete = "introComplete"
    AssistantResponseGenerated = "assistantResponseGenerated"
    Exit = "exit"


'''
Defining a class to maintain the state for the user inputs
'''


class UserInputState(KernelBaseModel):
    user_inputs: list[str] = []
    current_input_index: int = 0


class UserInputStep(KernelProcessStep[UserInputState]):
    GET_USER_INPUT: ClassVar[str] = "get_user_input"

    def populate_user_inputs(self):
        """Method to be overridden by the user to populate with custom user messages."""
        pass

    async def activate(self, state: KernelProcessStepState[UserInputState]):
        """Activates the step and sets the state."""
        state.state = state.state or self.create_default_state()
        self.state = state.state
        self.populate_user_inputs()

    @kernel_function(name=GET_USER_INPUT)
    async def get_user_input(self, context: KernelProcessStepContext):
        """Gets the user input."""
        if not self.state:
            raise ValueError("State has not been initialized")

        user_message = input("USER: ")

        # print(f"USER: {user_message}")

        if "exit" in user_message:
            await context.emit_event(process_event=ChatBotEvents.Exit, data=None)
            return

        self.state.current_input_index += 1

        # Emit the user input event
        await context.emit_event(process_event=CommonEvents.UserInputReceived, data=user_message)
