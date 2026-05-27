"""Loop workflow: tool definitions."""

from google.adk.tools.tool_context import ToolContext


def build_exit_loop_tool():
    """Quality gate tool — call when output meets requirements to exit the loop."""

    def exit_loop(tool_context: ToolContext):
        """Signal that the current output meets quality requirements.

        Call this ONLY when the content is good enough to exit the refinement loop.
        This escalates the event, causing LoopAgent to stop iterating.
        """
        tool_context.actions.escalate = True
        return {"status": "quality_gate_passed"}

    return exit_loop


def build_quality_score_tool(min_score: float = 0.8):
    """Tool that checks a quality score against a threshold."""

    def check_quality(score: float, tool_context: ToolContext):
        """Check if quality score meets the threshold. Escalates if passed.

        Args:
            score: Quality score between 0.0 and 1.0.
        """
        if score >= min_score:
            tool_context.actions.escalate = True
            return {"passed": True, "score": score, "threshold": min_score}
        return {"passed": False, "score": score, "threshold": min_score}

    return check_quality
