"""LLM router — routes requests to DeepSeek V3 or R1 based on task type."""

import json
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.config import settings

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# Model mapping
MODELS = {
    "standard": "deepseek-chat",       # DeepSeek V3 — fast, general tasks
    "reasoning": "deepseek-reasoner",  # DeepSeek R1 — complex reasoning
}

CONCEPT_EXTRACTION_PROMPT = """\
Extract educational concepts from the following text. Return a JSON array of objects,
each with keys: "name" (concise concept name), "description" (one-sentence summary),
"estimated_weight" (0.0-1.0 relative importance in the course).

Only return the JSON array, no other text.

Course context: {course_name}

Text:
{text}
"""


class LLMRouter:
    def __init__(self, api_key: str | None = None):
        self.client = AsyncOpenAI(
            api_key=api_key or settings.deepseek_api_key,
            base_url=DEEPSEEK_BASE_URL,
        )

    def _get_model(self, task_type: str) -> str:
        return MODELS.get(task_type, MODELS["standard"])

    async def complete(
        self,
        prompt: str,
        task_type: str = "standard",
        system_prompt: str | None = None,
        max_tokens: int = 2048,
    ) -> dict:
        """Send a completion request to the appropriate DeepSeek model."""
        model = self._get_model(task_type)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        return {
            "content": choice.message.content or "",
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            } if response.usage else None,
        }

    async def stream(
        self,
        prompt: str,
        task_type: str = "standard",
        system_prompt: str | None = None,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Stream a completion response token by token."""
        model = self._get_model(task_type)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def extract_concepts(
        self, text: str, course_name: str | None = None
    ) -> list[dict]:
        """Extract educational concepts from text using DeepSeek V3."""
        prompt = CONCEPT_EXTRACTION_PROMPT.format(
            course_name=course_name or "General",
            text=text,
        )
        result = await self.complete(prompt, task_type="standard", max_tokens=4096)
        content = result["content"].strip()

        # Strip markdown code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            content = "\n".join(lines)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return []

    async def analyze(
        self,
        prompt: str,
        context: dict | None = None,
        max_tokens: int = 4096,
    ) -> dict:
        """Deep analysis using DeepSeek R1 (reasoning model)."""
        system_prompt = (
            "You are an educational analytics expert. Provide thorough, "
            "well-reasoned analysis."
        )
        if context:
            prompt = f"Context:\n{json.dumps(context, indent=2)}\n\n{prompt}"

        return await self.complete(
            prompt,
            task_type="reasoning",
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )
