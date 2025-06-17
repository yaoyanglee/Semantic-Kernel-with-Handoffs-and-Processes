import os
import configparser
import asyncio

from openai import AzureOpenAI

from semantic_kernel.agents import Agent, ChatCompletionAgent, HandoffOrchestration, OrchestrationHandoffs
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.functions import kernel_function

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

# Initialising the model
model = AzureChatCompletion(
    deployment_name=DEPLOYMENT_NAME,
    api_key=API_KEY,
    endpoint=ENDPOINT,
    api_version=API_VERSION)


# Creating the different plugins
# A kernel function in each plugin will be a process and the plugin will be a collection of processes

# Workflows:
# 1. Make a vaccination booking
# 2. Check what vaccines I am eligible for


class VaccinationBookingPlugIn:
    def __init__(self):
        pass

    @kernel_function
    def vaccination_process(self):
        print("Vaccination Process")


# Defining the agents
# In this case triage agent and the process agent
triage_agent = ChatCompletionAgent(
    name='TriageAgent',
    description='Triages user requests.',
    instructions='Handle user requests.',
    service=model
)

booking_agent = ChatCompletionAgent(
    name='BookingAgent',
    description='A patient support agent that handles appointment booking',
    instructions='Handle booking requests.',
    service=model,
    plugins=[VaccinationBookingPlugIn()]
)

handoffs = (
    OrchestrationHandoffs().add(
        source_agent='TriageAgent',
        target_agent='BookingAgent',
        description='=Transfer to this agent is the issue is appointment booking related.'
    ).add(
        source_agent='BookingAgent',
        target_agent='TriageAgent',
        description='Return to the triage agent if the issue is not appointment booking related.'
    )
)


def agent_response_callback(message: ChatMessageContent) -> None:
    """Observer function to print the messages from the agents."""
    print(f"{message.name}: {message.content}")


def human_response_function() -> ChatMessageContent:
    """Observer function to print the messages from the agents."""
    user_input = input("User: ")
    return ChatMessageContent(role=AuthorRole.ASSISTANT, content=user_input)


async def main():
    handoff_orchestration = HandoffOrchestration(
        members=[triage_agent, booking_agent],
        handoffs=handoffs,
        agent_response_callback=agent_response_callback,
        human_response_function=human_response_function,
    )

    # 2. Create a runtime and start it
    runtime = InProcessRuntime()
    runtime.start()

    # 3. Invoke the orchestration with a task and the runtime
    orchestration_result = await handoff_orchestration.invoke(
        task="I would like to book an influenza vaccine at 10am today",
        runtime=runtime,
    )

    # 4. Wait for the results
    value = await orchestration_result.get()
    print(value)

    # 5. Stop the runtime after the invocation is complete
    await runtime.stop_when_idle()

if __name__ == "__main__":
    asyncio.run(main())
