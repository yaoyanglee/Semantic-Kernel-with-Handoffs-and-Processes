# Semantic Kernel using Process Framework within Agent Handoffs

## Setup

1. Create a virtual environment `uv venv`
2. Install the requirements into the virtual environment `uv pip install -r requirements.txt`

## Conceptual Overview

We aim to leverage the agent orchestration to handle a wide variety of potential patient/user requets and leverage on the Process Framework to streamline standardised unchanging processes.

#### Plugins

_Plugins_ are a collection of functions that are available to the agents in Semantic Kernel. The agents can choose from the functions with the decorator, `@kernel _function`

The Process Framework is essentially invoked within a `@kernel_function` within an agent which the `triage_agent` has handed off to.

#### Process Framework

It is an ordered collection of steps that works sequentially, completing the process.

_Steps_ are classes that can be defined. Somewhat similar to plugins, if a step only has 1 `@kernel_function` the step defaults to that function. If there are multiple `@kernel_function`, then we would have to explicitly define which step we want to occue next at the end of the current step.

Instead of maintaining a global state, parameters required are passed from the preceding step to the current step. Maintenance of a process wide state is not elegantly supported in the docs or in the library. Although states for each step can be maintained.

## Architecture

The diagram below illustrates the architecture of the Agent Orchestration with Process Framework.

![Orchestration Diagram](./assets/sk%20handoff%20process.png)

## Debugging Notes

### Semantic Kernel content filtering exception - jailbreaking

Agent names contain underscores. Eg. booking_agent is not allowed. Instead safe options are BookingAgent and the like.
