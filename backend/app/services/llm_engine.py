"""
LLM engine service – sends user queries + RAG context to Groq (Llama-3)
and returns a concise answer.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from backend.app.core.config import settings

_TEMPLATE = """\
System: You are an expert Government Scheme Advisor for India.
Use the following pieces of context to answer the user's question.
If the answer is not in the context, say "I don't have enough information."
Keep the answer concise and helpful.
{language_instruction}

Context: {context}

User: {query}

Answer:"""


class LLMEngine:
    """Generate answers via Groq-hosted Llama-3 using a RAG prompt."""

    def __init__(self) -> None:
        self.llm = ChatGroq(
            temperature=0,
            model_name="llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY,
        )
        self.prompt = PromptTemplate(
            input_variables=["context", "query", "language_instruction"],
            template=_TEMPLATE,
        )
        self.parser = StrOutputParser()
        self.chain = self.prompt | self.llm | self.parser

    def generate_answer(
        self,
        query: str,
        context: str,
        language: str = "English",
        history: list | None = None,
    ) -> str:
        """Run the chain and return the LLM's answer as a plain string."""
        # Build language instruction
        if language and language != "English":
            lang_instruction = (
                f"\nAnswer the user's question in {language}. "
                f"Keep technical terms (like scheme names) in English if needed, "
                f"but explain in {language}."
            )
        else:
            lang_instruction = ""

        # Build conversation history context
        history_block = ""
        if history:
            turns = []
            for msg in history[-10:]:  # last 10 messages to avoid token overflow
                role = "User" if msg.get("role") == "user" else "AI"
                turns.append(f"{role}: {msg.get('content', '')}")
            if turns:
                history_block = (
                    "\n\nPrevious conversation:\n"
                    + "\n".join(turns)
                    + "\n\nNow answer the latest question below."
                )

        # Prepend history to the query so the LLM sees the conversation
        full_query = history_block + "\n" + query if history_block else query

        return self.chain.invoke({
            "query": full_query,
            "context": context,
            "language_instruction": lang_instruction,
        })

    def generate_raw(self, prompt: str) -> str:
        """Send a fully-formed prompt directly to the LLM (no template).

        Use this when the caller has already built the complete prompt
        (e.g., the recommendation service) and does not need the default
        RAG template wrapping it again.
        """
        response = self.llm.invoke(prompt)
        return self.parser.invoke(response)
