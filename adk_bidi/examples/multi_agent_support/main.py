"""
Multi-Agent Support Example

A coordinated customer support team with multiple specialist
agents managed by a supervisor.

Usage:
    python -m adk_bidi.examples.multi_agent_support.main

Requirements:
    - GOOGLE_API_KEY environment variable
"""

import asyncio
import os
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.adk.tools import FunctionTool
from google.genai import types

from adk_bidi.orchestration.supervisor import MultiAgentSupervisor, SpecialistTeam
from adk_bidi.orchestration.router import IntentRouter, IntentPattern
from adk_bidi.memory.shared_memory import SharedMemory
from adk_bidi.memory.working_memory import WorkingMemory
from adk_bidi.core.streaming_config import StreamingPresets


# Native audio model
LIVE_MODEL = "gemini-live-2.5-flash-native-audio"


# Support tools for different specialists
def lookup_account(account_id: str) -> str:
    """Look up account information."""
    return f"Account {account_id}: Status=Active, Plan=Premium, Since=2023"


def check_billing_status(account_id: str) -> str:
    """Check billing status for an account."""
    return f"Billing for {account_id}: Last payment=Dec 2024, Balance=$0.00, Next due=Jan 2025"


def process_refund(account_id: str, amount: float, reason: str) -> str:
    """Process a refund request."""
    return f"Refund initiated: ${amount:.2f} for {account_id}. Reason: {reason}. Processing in 3-5 days."


def check_system_status() -> str:
    """Check system status."""
    return "All systems operational. No known issues."


def lookup_error_code(error_code: str) -> str:
    """Look up error code information."""
    error_db = {
        "E001": "Connection timeout - Check network settings",
        "E002": "Authentication failed - Reset password",
        "E003": "Service unavailable - Try again later",
    }
    return error_db.get(error_code, f"Unknown error code: {error_code}")


def create_support_ticket(issue: str, priority: str = "normal") -> str:
    """Create a support ticket."""
    ticket_id = f"TKT-{hash(issue) % 10000:04d}"
    return f"Ticket created: {ticket_id}, Priority: {priority}"


def create_support_team() -> MultiAgentSupervisor:
    """Create and configure the support team."""
    # Shared memory for team coordination
    shared_memory = SharedMemory()

    # Create specialist agents
    greeter = Agent(
        name="greeter",
        model=LIVE_MODEL,
        description="Initial contact and triage specialist",
        instruction="""You are the first point of contact for customers.

Your responsibilities:
- Welcome customers warmly
- Understand their issue
- Gather necessary information (account ID, issue description)
- Route to the appropriate specialist

Guidelines:
- Be friendly and professional
- Ask clarifying questions
- Never attempt to resolve complex issues yourself
- Always confirm the customer's needs before routing
""",
        tools=[FunctionTool(lookup_account)],
    )

    technical_support = Agent(
        name="technical_support",
        model=LIVE_MODEL,
        description="Technical issue resolution specialist",
        instruction="""You are a technical support specialist.

Your responsibilities:
- Diagnose technical issues
- Provide step-by-step solutions
- Explain technical concepts simply
- Escalate complex issues when needed

Guidelines:
- Ask about error messages and symptoms
- Guide users through troubleshooting
- Document all steps taken
- Be patient and thorough
""",
        tools=[
            FunctionTool(check_system_status),
            FunctionTool(lookup_error_code),
            FunctionTool(create_support_ticket),
        ],
    )

    billing_support = Agent(
        name="billing_support",
        model=LIVE_MODEL,
        description="Billing and account specialist",
        instruction="""You are a billing and account specialist.

Your responsibilities:
- Handle billing inquiries
- Process refunds when appropriate
- Explain charges and invoices
- Update account information

Guidelines:
- Verify account ownership before making changes
- Be transparent about billing policies
- Process refunds according to policy
- Document all billing changes
""",
        tools=[
            FunctionTool(lookup_account),
            FunctionTool(check_billing_status),
            FunctionTool(process_refund),
        ],
    )

    escalation = Agent(
        name="escalation",
        model=LIVE_MODEL,
        description="Escalation and complex issue handler",
        instruction="""You handle escalated and complex issues.

Your responsibilities:
- Handle escalated cases
- Resolve complex multi-faceted issues
- Provide compensation when appropriate
- Ensure customer satisfaction

Guidelines:
- Review all previous interactions
- Take ownership of the issue
- Have authority to make exceptions
- Follow up to ensure resolution
""",
        tools=[
            FunctionTool(lookup_account),
            FunctionTool(create_support_ticket),
            FunctionTool(process_refund),
        ],
    )

    # Create supervisor
    supervisor = MultiAgentSupervisor(
        agents=[greeter, technical_support, billing_support, escalation],
        shared_memory=shared_memory,
        working_memory=WorkingMemory(max_size=30),
        instruction="""You coordinate a customer support team.

Team members:
- Greeter: Initial contact and triage
- Technical Support: Technical issues
- Billing Support: Billing and account questions
- Escalation: Complex cases and complaints

Routing guidelines:
1. New customers always start with Greeter
2. Technical issues go to Technical Support
3. Billing questions go to Billing Support
4. Angry customers or unresolved issues go to Escalation
5. Share context between agents using shared memory

Quality standards:
- Ensure smooth handoffs between agents
- Monitor customer satisfaction
- Intervene if agents are struggling
- Track resolution metrics
""",
    )

    return supervisor


def create_intent_router(supervisor: MultiAgentSupervisor) -> IntentRouter:
    """Create intent router for direct routing."""
    router = IntentRouter(
        shared_memory=supervisor.shared_memory,
        enable_llm_routing=True,
    )

    # Define intent patterns
    router.add_route(
        agent=supervisor.agents["greeter"],
        intents=[
            IntentPattern(
                name="greeting",
                patterns=[r"^(hi|hello|hey)", r"need help$"],
                keywords=["help", "support", "question"],
            ),
        ],
    )

    router.add_route(
        agent=supervisor.agents["technical_support"],
        intents=[
            IntentPattern(
                name="technical_issue",
                patterns=[r"error", r"not working", r"broken"],
                keywords=["error", "bug", "crash", "slow", "fix", "broken", "issue"],
            ),
        ],
    )

    router.add_route(
        agent=supervisor.agents["billing_support"],
        intents=[
            IntentPattern(
                name="billing_inquiry",
                patterns=[r"bill", r"charge", r"payment"],
                keywords=["bill", "charge", "payment", "refund", "invoice", "subscription"],
            ),
        ],
    )

    router.add_route(
        agent=supervisor.agents["escalation"],
        intents=[
            IntentPattern(
                name="escalation",
                patterns=[r"manager", r"supervisor", r"complaint"],
                keywords=["manager", "supervisor", "complaint", "escalate", "unacceptable"],
            ),
        ],
        is_fallback=True,
    )

    return router


async def run_support_session():
    """Run an interactive support session."""
    print("Initializing Multi-Agent Support Team...")
    print("Using model: gemini-live-2.5-flash-native-audio")
    print("-" * 50)

    # Create the support team
    supervisor = create_support_team()
    router = create_intent_router(supervisor)

    # Create runner with supervisor agent
    runner = Runner(
        agent=supervisor.get_supervisor_agent(),
        app_name="multi_agent_support_example",
    )

    # Create live request queue
    live_queue = LiveRequestQueue()

    # Get streaming configuration
    run_config = StreamingPresets.text_and_audio()

    print("\nSupport Team is ready!")
    print("Team members: Greeter, Technical Support, Billing Support, Escalation")
    print("\nCommands:")
    print("  <message>    - Send a support request")
    print("  status       - Show team status")
    print("  history      - Show delegation history")
    print("  quit         - Exit")
    print("-" * 50)
    print("\nExample messages:")
    print("  'Hi, I need help with my account'")
    print("  'I got error E001 when logging in'")
    print("  'Why was I charged twice?'")
    print("-" * 50)

    async def process_responses():
        """Process responses from the support team."""
        async for event in runner.run_live(
            user_id="demo_customer",
            session_id="demo_session",
            live_request_queue=live_queue,
            run_config=run_config,
        ):
            # Handle response content
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            print(f"\nSupport: {part.text}")

            if hasattr(event, 'turn_complete') and event.turn_complete:
                print("\nCustomer> ", end="", flush=True)

    async def handle_input():
        """Handle customer input."""
        while True:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, "Customer> "
                )

                user_input = user_input.strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Thank you for contacting support. Goodbye!")
                    live_queue.close()
                    break

                if user_input.lower() == 'status':
                    status = supervisor.get_agent_status()
                    print(f"\n{status}\n")
                    continue

                if user_input.lower() == 'history':
                    history = supervisor.get_delegation_history()
                    print(f"\n{history}\n")
                    continue

                if user_input:
                    # Route the request
                    agent, decision = await router.route(user_input)
                    print(f"[Routing to: {decision.agent_name} ({decision.intent})]")

                    # Share context
                    await supervisor.shared_memory.write(
                        key="customer_message",
                        value=user_input,
                        agent_id="router",
                    )

                    # Send to supervisor
                    content = types.Content(
                        parts=[types.Part(text=user_input)]
                    )
                    live_queue.send_content(content)

            except EOFError:
                live_queue.close()
                break

    # Run both tasks concurrently
    try:
        await asyncio.gather(
            process_responses(),
            handle_input(),
            return_exceptions=True,
        )
    except Exception as e:
        print(f"Session ended: {e}")
    finally:
        # Session summary
        stats = supervisor.get_stats()
        router_stats = router.get_stats()
        print("\n" + "=" * 50)
        print("SUPPORT SESSION SUMMARY")
        print("=" * 50)
        print(f"Team size: {stats['agent_count']} agents")
        print(f"Delegations: {stats['delegations']}")
        print(f"Successful: {stats['successful_delegations']}")
        print(f"Router decisions: {router_stats['total_decisions']}")
        print(f"Route distribution: {router_stats['route_distribution']}")


def main():
    """Main entry point."""
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable not set")
        print("Please set your API key:")
        print("  export GOOGLE_API_KEY=your_api_key")
        return

    try:
        asyncio.run(run_support_session())
    except KeyboardInterrupt:
        print("\nSupport session ended.")


if __name__ == "__main__":
    main()
