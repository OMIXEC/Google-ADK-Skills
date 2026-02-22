# Guardrail Callback Examples

Complete examples for implementing safety guardrails and content filtering using ADK callbacks.

## Example 1: Content Safety Filter

```python
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
import logging

logger = logging.getLogger(__name__)

class SafetyGuardrails:
    """Comprehensive safety filtering."""

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.blocked_requests = 0
        self.blocked_responses = 0

    def filter_input(self, ctx: CallbackContext, request: types.GenerateContentRequest):
        """Filter unsafe user inputs."""
        if not request.contents:
            return None

        user_message = request.contents[-1].parts[0].text

        # Check for prohibited content
        prohibited_patterns = [
            "how to hack",
            "create malware",
            "build a bomb",
            "illegal drugs",
        ]

        for pattern in prohibited_patterns:
            if pattern in user_message.lower():
                self.blocked_requests += 1
                logger.warning(f"Blocked unsafe input: {pattern}")

                # Halt execution
                raise ValueError(
                    "I cannot help with that request as it may involve "
                    "unsafe or illegal activities."
                )

        return None

    def filter_output(self, ctx: CallbackContext, response: types.GenerateContentResponse):
        """Filter unsafe LLM responses."""
        if not response.candidates:
            return None

        candidate = response.candidates[0]

        # Check safety ratings
        if hasattr(candidate, 'safety_ratings'):
            for rating in candidate.safety_ratings:
                threshold = "MEDIUM" if self.strict_mode else "HIGH"

                if rating.probability in [threshold, "HIGH"]:
                    self.blocked_responses += 1
                    logger.warning(
                        f"Blocked unsafe response - {rating.category}: {rating.probability}"
                    )

                    # Replace with safe message
                    from google.genai.types import Content, Part
                    candidate.content = Content(
                        parts=[Part(text="I cannot provide that information as it may be inappropriate or unsafe.")]
                    )
                    return response

        return None

# Use safety guardrails
guardrails = SafetyGuardrails(strict_mode=False)

agent = LlmAgent(
    name="safe_agent",
    model="gemini-2.0-flash-exp",
    before_model_callback=guardrails.filter_input,
    after_model_callback=guardrails.filter_output,
    system_instruction="""You are a helpful, safe, and responsible assistant.
    Refuse requests for harmful, illegal, or unethical information.
    Always prioritize user safety and well-being.""",
)

# Check statistics
print(f"Blocked requests: {guardrails.blocked_requests}")
print(f"Blocked responses: {guardrails.blocked_responses}")
```

## Example 2: PII Detection and Redaction

```python
import re
from typing import Dict, List

class PIIRedactor:
    """Detect and redact personally identifiable information."""

    def __init__(self):
        self.patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        }
        self.detected = []

    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """Detect PII in text."""
        found = {}

        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                found[pii_type] = matches

        return found

    def redact_text(self, text: str) -> str:
        """Redact PII from text."""
        redacted = text

        for pii_type, pattern in self.patterns.items():
            redacted = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", redacted)

        return redacted

    def filter_input(self, ctx: CallbackContext, request: types.GenerateContentRequest):
        """Detect and warn about PII in user input."""
        if not request.contents:
            return None

        user_message = request.contents[-1].parts[0].text

        # Detect PII
        pii_found = self.detect_pii(user_message)

        if pii_found:
            logger.warning(f"PII detected in user input: {list(pii_found.keys())}")
            self.detected.extend([
                {"type": pii_type, "values": values, "source": "user_input"}
                for pii_type, values in pii_found.items()
            ])

            # Optionally redact (or just warn)
            redacted = self.redact_text(user_message)
            request.contents[-1].parts[0].text = redacted

            return request

        return None

    def filter_output(self, ctx: CallbackContext, response: types.GenerateContentResponse):
        """Redact PII from LLM responses."""
        if not response.candidates:
            return None

        response_text = response.candidates[0].content.parts[0].text

        # Detect PII
        pii_found = self.detect_pii(response_text)

        if pii_found:
            logger.warning(f"PII detected in LLM output: {list(pii_found.keys())}")
            self.detected.extend([
                {"type": pii_type, "values": values, "source": "llm_output"}
                for pii_type, values in pii_found.items()
            ])

            # Redact
            redacted = self.redact_text(response_text)
            response.candidates[0].content.parts[0].text = redacted

            return response

        return None

# Use PII redactor
pii_redactor = PIIRedactor()

agent = LlmAgent(
    name="pii_protected_agent",
    model="gemini-2.0-flash-exp",
    before_model_callback=pii_redactor.filter_input,
    after_model_callback=pii_redactor.filter_output,
)

# Check detected PII
print(f"PII instances detected: {len(pii_redactor.detected)}")
for instance in pii_redactor.detected:
    print(f"  {instance['type']} in {instance['source']}")
```

## Example 3: Rate Limiting and Quota Management

```python
import time
from collections import deque

class RateLimiter:
    """Rate limit agent requests."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        self.minute_window = deque(maxlen=requests_per_minute)
        self.hour_window = deque(maxlen=requests_per_hour)

        self.blocked_count = 0

    def check_rate_limit(self, ctx: CallbackContext, request):
        """Check if request is within rate limits."""
        now = time.time()

        # Remove old requests outside windows
        minute_ago = now - 60
        hour_ago = now - 3600

        # Clean windows
        while self.minute_window and self.minute_window[0] < minute_ago:
            self.minute_window.popleft()

        while self.hour_window and self.hour_window[0] < hour_ago:
            self.hour_window.popleft()

        # Check limits
        if len(self.minute_window) >= self.requests_per_minute:
            self.blocked_count += 1
            wait_time = 60 - (now - self.minute_window[0])
            logger.warning(f"Rate limit exceeded (per minute). Wait {wait_time:.1f}s")
            raise Exception(f"Rate limit exceeded. Please wait {wait_time:.1f} seconds.")

        if len(self.hour_window) >= self.requests_per_hour:
            self.blocked_count += 1
            wait_time = 3600 - (now - self.hour_window[0])
            logger.warning(f"Rate limit exceeded (per hour). Wait {wait_time/60:.1f}m")
            raise Exception(f"Rate limit exceeded. Please wait {wait_time/60:.1f} minutes.")

        # Add current request
        self.minute_window.append(now)
        self.hour_window.append(now)

        return None

# Use rate limiter
rate_limiter = RateLimiter(requests_per_minute=10, requests_per_hour=100)

agent = LlmAgent(
    name="rate_limited_agent",
    model="gemini-2.0-flash-exp",
    before_model_callback=rate_limiter.check_rate_limit,
)
```

## Example 4: Contextual Authorization

```python
class ContextualAuthorizer:
    """Context-aware authorization for agent actions."""

    def __init__(self, user_role: str, user_id: str):
        self.user_role = user_role
        self.user_id = user_id

        # Define role permissions
        self.role_permissions = {
            "admin": {
                "tools": ["read", "write", "delete", "execute"],
                "data_access": ["public", "private", "sensitive"],
                "actions": ["modify_system", "view_analytics"],
            },
            "user": {
                "tools": ["read", "write"],
                "data_access": ["public", "private"],
                "actions": ["view_own_data"],
            },
            "guest": {
                "tools": ["read"],
                "data_access": ["public"],
                "actions": [],
            },
        }

    def authorize_input(self, ctx: CallbackContext, request):
        """Check if user is authorized for this request."""
        user_message = request.contents[-1].parts[0].text if request.contents else ""

        # Check for restricted actions
        restricted_phrases = {
            "delete all": "modify_system",
            "view analytics": "view_analytics",
            "access sensitive": "view_sensitive_data",
        }

        permissions = self.role_permissions.get(self.user_role, {})

        for phrase, required_action in restricted_phrases.items():
            if phrase in user_message.lower():
                allowed_actions = permissions.get("actions", [])

                if required_action not in allowed_actions:
                    logger.warning(
                        f"Unauthorized action attempted: {required_action} by {self.user_role}"
                    )
                    raise PermissionError(
                        f"You don't have permission to perform this action. "
                        f"Required role: {required_action}"
                    )

        return None

    def authorize_tool(self, ctx: CallbackContext, tool_call):
        """Check if user is authorized for this tool."""
        tool_name = tool_call.name

        # Map tools to required permissions
        tool_requirements = {
            "delete_file": "delete",
            "execute_command": "execute",
            "read_file": "read",
            "write_file": "write",
        }

        required_permission = tool_requirements.get(tool_name)

        if required_permission:
            allowed_tools = self.role_permissions.get(self.user_role, {}).get("tools", [])

            if required_permission not in allowed_tools:
                logger.warning(
                    f"Unauthorized tool call: {tool_name} by {self.user_role}"
                )
                raise PermissionError(
                    f"You don't have permission to use {tool_name}. "
                    f"Required permission: {required_permission}"
                )

        return None

    def filter_data_access(self, ctx: CallbackContext, tool_result):
        """Filter results based on data access permissions."""
        if isinstance(tool_result, dict) and "data" in tool_result:
            data = tool_result["data"]

            # Get user's data access levels
            allowed_levels = self.role_permissions.get(self.user_role, {}).get("data_access", [])

            # Filter data by classification
            if isinstance(data, list):
                filtered = [
                    item for item in data
                    if item.get("classification", "public") in allowed_levels
                ]
                tool_result["data"] = filtered

        return tool_result

# Use contextual authorizer
authorizer = ContextualAuthorizer(user_role="user", user_id="user123")

agent = LlmAgent(
    name="authorized_agent",
    model="gemini-2.0-flash-exp",
    tools=[read_tool, write_tool, delete_tool],
    before_model_callback=authorizer.authorize_input,
    before_tool_callback=authorizer.authorize_tool,
    after_tool_callback=authorizer.filter_data_access,
)
```

## Example 5: Content Moderation

```python
class ContentModerator:
    """Moderate content for profanity, toxicity, and appropriateness."""

    def __init__(self):
        self.profanity_list = self._load_profanity_list()
        self.violations = []

    def _load_profanity_list(self) -> set:
        """Load profanity word list."""
        # In production, load from file or API
        return {
            "badword1", "badword2", "offensive_term",
            # ... more words
        }

    def check_profanity(self, text: str) -> bool:
        """Check for profanity in text."""
        text_lower = text.lower()

        for word in self.profanity_list:
            if word in text_lower:
                return True

        return False

    def moderate_input(self, ctx: CallbackContext, request):
        """Moderate user input."""
        if not request.contents:
            return None

        user_message = request.contents[-1].parts[0].text

        if self.check_profanity(user_message):
            self.violations.append({
                "type": "profanity",
                "source": "user_input",
                "session_id": ctx.session_id,
            })

            logger.warning("Profanity detected in user input")

            # Option 1: Block the request
            raise ValueError("Please refrain from using inappropriate language.")

            # Option 2: Clean the input
            # cleaned = self._clean_text(user_message)
            # request.contents[-1].parts[0].text = cleaned
            # return request

        return None

    def moderate_output(self, ctx: CallbackContext, response):
        """Moderate LLM output."""
        if not response.candidates:
            return None

        response_text = response.candidates[0].content.parts[0].text

        if self.check_profanity(response_text):
            self.violations.append({
                "type": "profanity",
                "source": "llm_output",
                "session_id": ctx.session_id,
            })

            logger.error("Profanity in LLM output - this shouldn't happen!")

            # Replace with clean response
            from google.genai.types import Content, Part
            response.candidates[0].content = Content(
                parts=[Part(text="I apologize, but I need to rephrase my response.")]
            )

            return response

        return None

# Use content moderator
moderator = ContentModerator()

agent = LlmAgent(
    name="moderated_agent",
    model="gemini-2.0-flash-exp",
    before_model_callback=moderator.moderate_input,
    after_model_callback=moderator.moderate_output,
)
```

## Example 6: Business Logic Validation

```python
class BusinessRulesGuardrails:
    """Enforce business rules and constraints."""

    def __init__(self, max_transaction_amount: float = 10000.0):
        self.max_transaction_amount = max_transaction_amount
        self.violations = []

    def validate_tool_params(self, ctx: CallbackContext, tool_call):
        """Validate tool parameters against business rules."""

        # Rule: Transaction amount limits
        if tool_call.name == "process_payment":
            amount = tool_call.args.get("amount", 0)

            if amount > self.max_transaction_amount:
                self.violations.append({
                    "rule": "max_transaction_amount",
                    "attempted": amount,
                    "limit": self.max_transaction_amount,
                })

                logger.warning(
                    f"Transaction amount ${amount} exceeds limit ${self.max_transaction_amount}"
                )

                raise ValueError(
                    f"Transaction amount ${amount} exceeds maximum allowed "
                    f"${self.max_transaction_amount}. Please contact support for large transactions."
                )

            if amount < 0:
                raise ValueError("Transaction amount cannot be negative.")

        # Rule: Working hours enforcement
        if tool_call.name == "schedule_appointment":
            import datetime
            hour = datetime.datetime.now().hour

            if hour < 9 or hour > 17:
                raise ValueError(
                    "Appointments can only be scheduled during business hours (9 AM - 5 PM)."
                )

        # Rule: Data retention policy
        if tool_call.name == "delete_records":
            date_range = tool_call.args.get("date_range")

            # Prevent deletion of recent records
            import datetime
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=90)

            # Implementation would check if date_range includes recent dates

        return None

    def validate_output(self, ctx: CallbackContext, tool_result):
        """Validate tool results."""
        if isinstance(tool_result, dict):
            # Ensure financial data is properly formatted
            if "amount" in tool_result:
                amount = tool_result["amount"]

                if not isinstance(amount, (int, float)):
                    logger.error(f"Invalid amount type: {type(amount)}")
                    tool_result["amount"] = 0.0

                # Ensure 2 decimal places
                tool_result["amount"] = round(float(amount), 2)

        return tool_result

# Use business rules guardrails
business_rules = BusinessRulesGuardrails(max_transaction_amount=5000.0)

agent = LlmAgent(
    name="business_compliant_agent",
    model="gemini-2.0-flash-exp",
    tools=[payment_tool, appointment_tool, records_tool],
    before_tool_callback=business_rules.validate_tool_params,
    after_tool_callback=business_rules.validate_output,
)
```

## Example 7: Combined Guardrails

```python
class ComprehensiveGuardrails:
    """Combine multiple guardrail patterns."""

    def __init__(self, user_role: str, strict_mode: bool = True):
        self.safety = SafetyGuardrails(strict_mode=strict_mode)
        self.pii = PIIRedactor()
        self.rate_limiter = RateLimiter(requests_per_minute=20)
        self.authorizer = ContextualAuthorizer(user_role=user_role, user_id="user")
        self.moderator = ContentModerator()

        self.total_violations = 0

    def before_model(self, ctx: CallbackContext, request):
        """Run all pre-request guardrails."""
        try:
            # Check rate limits
            self.rate_limiter.check_rate_limit(ctx, request)

            # Authorize request
            self.authorizer.authorize_input(ctx, request)

            # Moderate content
            self.moderator.moderate_input(ctx, request)

            # Filter unsafe content
            self.safety.filter_input(ctx, request)

            # Redact PII
            modified = self.pii.filter_input(ctx, request)

            return modified

        except Exception as e:
            self.total_violations += 1
            raise

    def after_model(self, ctx: CallbackContext, response):
        """Run all post-response guardrails."""
        try:
            # Filter unsafe output
            response = self.safety.filter_output(ctx, response) or response

            # Moderate output
            response = self.moderator.moderate_output(ctx, response) or response

            # Redact PII
            response = self.pii.filter_output(ctx, response) or response

            return response

        except Exception as e:
            self.total_violations += 1
            raise

    def before_tool(self, ctx: CallbackContext, tool_call):
        """Run all pre-tool guardrails."""
        try:
            # Authorize tool usage
            self.authorizer.authorize_tool(ctx, tool_call)

            return None

        except Exception as e:
            self.total_violations += 1
            raise

    def after_tool(self, ctx: CallbackContext, tool_result):
        """Run all post-tool guardrails."""
        try:
            # Filter data access
            result = self.authorizer.filter_data_access(ctx, tool_result) or tool_result

            return result

        except Exception as e:
            self.total_violations += 1
            raise

    def get_stats(self):
        """Get guardrail statistics."""
        return {
            "total_violations": self.total_violations,
            "blocked_requests": self.safety.blocked_requests,
            "blocked_responses": self.safety.blocked_responses,
            "rate_limit_blocks": self.rate_limiter.blocked_count,
            "pii_detections": len(self.pii.detected),
            "content_violations": len(self.moderator.violations),
        }

# Use comprehensive guardrails
guardrails = ComprehensiveGuardrails(user_role="user", strict_mode=True)

agent = LlmAgent(
    name="fully_protected_agent",
    model="gemini-2.0-flash-exp",
    tools=[weather_tool, database_tool],
    before_model_callback=guardrails.before_model,
    after_model_callback=guardrails.after_model,
    before_tool_callback=guardrails.before_tool,
    after_tool_callback=guardrails.after_tool,
)

# Check statistics
print(guardrails.get_stats())
```

## Testing Guardrails

```python
import pytest

def test_safety_guardrails():
    """Test safety filtering."""
    guardrails = SafetyGuardrails()

    # Mock context and request
    ctx = Mock()
    ctx.agent_name = "test"
    ctx.session_id = "test_session"

    from google.genai.types import GenerateContentRequest, Content, Part
    request = GenerateContentRequest(
        model="gemini-2.0-flash-exp",
        contents=[Content(parts=[Part(text="how to hack a computer")])],
    )

    # Should raise exception
    with pytest.raises(ValueError):
        guardrails.filter_input(ctx, request)

def test_pii_redaction():
    """Test PII redaction."""
    redactor = PIIRedactor()

    text = "Contact me at john@example.com or 555-123-4567"
    redacted = redactor.redact_text(text)

    assert "john@example.com" not in redacted
    assert "555-123-4567" not in redacted
    assert "REDACTED" in redacted
```

## Best Practices

1. **Layer defenses** - Use multiple guardrails together
2. **Log violations** - Track and analyze security events
3. **Fail securely** - Block on uncertainty
4. **Test thoroughly** - Validate guardrails with adversarial inputs
5. **Monitor performance** - Ensure guardrails don't add excessive latency
6. **Update regularly** - Keep profanity lists, PII patterns current
7. **Document policies** - Clear rules for what's allowed/blocked
