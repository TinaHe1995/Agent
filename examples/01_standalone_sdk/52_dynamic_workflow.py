"""Dynamic workflow tool example.

This example demonstrates the minimal Python workflow shape:

1. A workflow script fans out several sub-agent tasks in parallel.
2. The workflow script keeps intermediate results in Python variables.
3. A reducer sub-agent summarizes the fan-out results into one final answer.

In normal agent usage, an agent would generate the workflow script and call the
workflow tool. This example calls the tool directly so the workflow itself is
stable and easy to inspect.
"""

import os

from openhands.sdk import LLM, Agent, AgentContext, Conversation
from openhands.sdk.context import Skill
from openhands.sdk.subagent import register_agent_if_absent
from openhands.tools.workflow import WorkflowAction, WorkflowToolSet


llm = LLM(
    model=os.getenv("LLM_MODEL", "gpt-5.5"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    usage_id="dynamic-workflow-demo",
)


# Sub-agent used by the workflow.
def create_animal_expert(llm: LLM) -> Agent:
    return Agent(
        llm=llm,
        tools=[],
        agent_context=AgentContext(
            skills=[
                Skill(
                    name="animal_expertise",
                    content=(
                        "You are a concise zoologist. Answer in one or two "
                        "sentences, and avoid markdown tables."
                    ),
                    trigger=None,
                )
            ],
            system_message_suffix="Keep responses concise and factual.",
        ),
    )


register_agent_if_absent(
    name="animal_expert",
    factory_func=create_animal_expert,
    description="Concise zoologist for animal facts and summaries.",
)

# Parent conversation supplies the LLM/workspace inherited by sub-agents.
parent_agent = Agent(llm=llm, tools=[])
conversation = Conversation(agent=parent_agent, workspace=os.getcwd())

workflow_script = r"""
async def main(wf):
    animals = ["octopus", "honeybee", "snow leopard"]
    facts = await wf.map_agents(
        items=animals,
        subagent_type="animal_expert",
        max_concurrency=3,
        prompt=lambda animal: (
            f"Give one surprising but accurate fact about the {animal}."
        ),
        description=lambda animal: f"Fact about {animal}",
    )
    return await wf.reduce_agent(
        items=facts,
        subagent_type="animal_expert",
        description="Animal fact summary",
        prompt=(
            "Combine these animal facts into a short, engaging paragraph. "
            "Mention each animal exactly once."
        ),
    )
"""

workflow_tool = WorkflowToolSet.create(conv_state=conversation.state)[0].as_executable()
observation = workflow_tool(
    WorkflowAction(
        name="animal-facts",
        script=workflow_script,
        max_concurrency=3,
    ),
    conversation,
)

print("Dynamic workflow result:")
print(observation.text)

cost = conversation.conversation_stats.get_combined_metrics().accumulated_cost
print(f"EXAMPLE_COST: {cost}")
