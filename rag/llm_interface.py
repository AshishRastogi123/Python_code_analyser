"""
Abstract LLM interface for pluggable LLM backends.
"""

class LLMInterface:
    """Abstract base class for LLM interactions."""

    def generate_answer(self, query, context):
        """
        Generate an answer based on query and context.

        Args:
            query (str): User query.
            context (str): Retrieved context.

        Returns:
            str: Generated answer.
        """
        raise NotImplementedError("Subclasses must implement generate_answer")

class DummyLLM(LLMInterface):
    """Dummy LLM for testing (returns a simple response)."""

    def generate_answer(self, query, context):
        return f"Based on the context: {context[:100]}..., the answer to '{query}' is not implemented yet. Plug in a real LLM."

# Example: To plug in OpenAI, you could create OpenAILLM(LLMInterface) with API calls.
