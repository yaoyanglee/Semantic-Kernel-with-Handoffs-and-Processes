import os
import configparser
import asyncio

from process import booking_process

from openai import AzureOpenAI

from semantic_kernel.agents import Agent, ChatCompletionAgent, HandoffOrchestration, OrchestrationHandoffs
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.functions import kernel_function

# Setting up environment variables
# --- Load all configuration settings ---
config = configparser.ConfigParser()
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
# 2. Handling general queries

class VaccinationBookingPlugIn:
    def __init__(self):
        pass

    @kernel_function
    async def vaccination_process(self):
        await booking_process()


# Defining the agents
# In this case triage agent and the process agent
triage_agent = ChatCompletionAgent(
    name='TriageAgent',
    description='Triages user requests.',
    instructions='Handle user requests.',
    service=model,
)

booking_agent = ChatCompletionAgent(
    name='BookingAgent',
    description='A patient support agent that handles appointment booking',
    instructions='Handle booking requests.',
    service=model,
    plugins=[VaccinationBookingPlugIn()]
)

general_questions_agent = ChatCompletionAgent(
    name='GeneralAgent',
    description='A patient support agent that handles answering any questions that the patients may have',
    instructions='Handle general patient questions.',
    service=model,
)

handoffs = (
    OrchestrationHandoffs().add_many(
        source_agent='TriageAgent',
        target_agents={
            'BookingAgent': 'Transfer to this agent is the issue is appointment booking related.',
            'GeneralAgent': 'Transfer to this agent if the goal is to answer user queries unrelated to appointment booking'
        }
    ).add(
        source_agent='BookingAgent',
        target_agent='TriageAgent',
        description='Return to the triage agent once done with appointment booking.'
    ).add(
        source_agent='GeneralAgent',
        target_agent='TriageAgent',
        description='Return to the triage agent once done with answering user queries.'
    )
)


def agent_response_callback(message: ChatMessageContent) -> None:
    """
    Observer function to print the messages from the agents.

    Parameters:
        None

    Returns:
        None
    """
    print(f"{message.name}: {message.content}")


def human_response_function() -> ChatMessageContent:
    """
    Observer function to print the messages from the agents. Additionally provides graceful exit for users to end the agent orchestration

    Parameters:
        None

    Returns:
        None
    """
    try:
        user_input = input("User (type 'exit' to quit): ")

        if user_input.strip().lower() == 'exit':
            print("Exiting agentic flow...")
            # This will signal the runtime to stop
            raise KeyboardInterrupt()

        return ChatMessageContent(role=AuthorRole.ASSISTANT, content=user_input)
    except KeyboardInterrupt:
        print("Orchestration interrupted by user. Exiting...")
        return ChatMessageContent(role=AuthorRole.ASSISTANT, content="Exiting agent orchestration")


async def main():
    '''
    Entry point for starting the entire agent workflow.
    - Defines the agent handoff orchestration
    - Creates a runtime for the handoffs
    - Invokes the handoff orchestration

    Parameters:
        None

    Returns:
        None
    '''

    try:
        # Ask user for task
        user_input = input("What would you like to do? (Type 'exit' to quit) ")

        if user_input.strip().lower() == 'exit':
            print("Exiting before starting orchestration.")
            return

        handoff_orchestration = HandoffOrchestration(
            members=[triage_agent, booking_agent, general_questions_agent],
            handoffs=handoffs,
            agent_response_callback=agent_response_callback,
            human_response_function=human_response_function,
        )

        # 2. Create a runtime and start it
        runtime = InProcessRuntime()
        runtime.start()

        # 3. Invoke the orchestration with a task and the runtime
        orchestration_result = await handoff_orchestration.invoke(
            task=user_input,
            runtime=runtime,
        )

        # 4. Wait for the results
        value = await orchestration_result.get()
        print(value)

        # 5. Stop the runtime after the invocation is complete
        await runtime.stop_when_idle()

    except KeyboardInterrupt:
        print("Orchestration interrupted by user. Exiting...")

if __name__ == "__main__":
    asyncio.run(main())
