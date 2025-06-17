# Semantic Kernel using Process Framework within Agent Handoffs

## Setup

1. Create a virtual environment
2. Install the requirements into the virtual environment

## Conceptual Overview

We aim to leverage the agent orchestration to handle a wide variety of potential patient/user requets and leverage on the Process Framework to streamline standardised unchanging processes.

## Architecture

The diagram below illustrates the architecture of the Agent Orchestration with Process Framework.

## Debugging Notes

### Semantic Kernel content filtering exception - jailbreaking

Agent names contain underscores. Eg. booking_agent is not allowed. Instead safe options are BookingAgent and the like.
