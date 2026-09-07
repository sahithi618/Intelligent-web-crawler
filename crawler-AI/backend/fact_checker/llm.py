from typing import cast
from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings
import os 
from dotenv import load_dotenv

load_dotenv(override=True)

def build_model() -> Model:

    model_name = "groq:llama-3.1-8b-instant"
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Warning: GROQ_API_KEY environment variable is not set. Falling back to TestModel for mock initialization.")
        from pydantic_ai.models.test import TestModel
        return TestModel()
    base_url = ""
    temperature = 0.0
    max_tokens = 1024
    model_settings = ModelSettings(
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if model_name.startswith("openai:"):
        from pydantic_ai.models.openai import OpenAIModel, OpenAIModelName
        from pydantic_ai.providers.openai import OpenAIProvider

        return OpenAIModel(
            cast(OpenAIModelName, model_name[7:]),
            provider=OpenAIProvider(api_key=api_key),
            model_settings=model_settings,
        )

    elif model_name.startswith("anthropic:"):
        from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelName

        return AnthropicModel(
            cast(AnthropicModelName, model_name[10:]),
            api_key=api_key,
            model_settings=model_settings,
        )

    elif model_name.startswith("google-gla:"):
        from pydantic_ai.models.gemini import GeminiModel, GeminiModelName
        from pydantic_ai.providers.google_gla import GoogleGLAProvider

        return GeminiModel(
            cast(GeminiModelName, model_name[11:]),
            provider=GoogleGLAProvider(api_key=api_key),
            model_settings=model_settings,
        )

    elif model_name.startswith("groq:"):
        from pydantic_ai.models.groq import GroqModel, GroqModelName
        from pydantic_ai.providers.groq import GroqProvider

        return GroqModel(
            cast(GroqModelName, model_name[5:]), provider=GroqProvider(api_key=api_key),
            settings = model_settings,  
        )

    elif model_name.startswith("mistral:"):
        from pydantic_ai.models.mistral import MistralModel, MistralModelName
        from pydantic_ai.providers.mistral import MistralProvider

        return MistralModel(
            cast(MistralModelName, model_name[8:]),
            provider=MistralProvider(api_key=api_key),
            model_settings=model_settings,
        )

    elif model_name.startswith("ollama:"):
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider

        return OpenAIModel(
            model_name[7:],
            provider=OpenAIProvider(base_url=base_url),
            model_settings=model_settings,
        )

    else:
        raise ValueError(f"Unsupported model name: {model_name}")


async def run_agent_with_retry(agent, prompt: str, max_retries: int = 3, initial_delay: float = 3.0):
    import asyncio
    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            result = await agent.run(prompt)
            return result
        except Exception as e:
            err_str = str(e).lower()
            if any(term in err_str for term in ["429", "rate limit", "tpm", "rate_limit"]):
                if attempt < max_retries:
                    print(f"[LLM] Rate limit hit. Retrying in {delay}s... (Attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                    delay *= 2.0  # exponential backoff
                    continue
            raise e


def parse_json_robust(text: str) -> dict:
    import json
    text = text.strip()
    # Strip leading/trailing markdown code block tags if present
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part_clean = part.strip()
            if part_clean.startswith("json"):
                part_clean = part_clean[4:].strip()
            if part_clean.startswith("{") or part_clean.startswith("["):
                try:
                    return json.loads(part_clean, strict=False)
                except Exception:
                    continue
    # Try parsing the whole text directly
    try:
        return json.loads(text, strict=False)
    except Exception as e:
        # Fallback: search for first '{' and last '}'
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1], strict=False)
            except Exception:
                pass
        raise e




if __name__ == "__main__":
    model = build_model()
    print(model)
