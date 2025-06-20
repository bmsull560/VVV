import os
import openai
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set and no API key provided.")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"OpenAIClient initialized with model: {self.model}")

    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            text_content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            cost_usd = self._calculate_cost(response.usage)

            return {
                "text": text_content,
                "tokens_used": tokens_used,
                "cost_usd": cost_usd
            }
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during OpenAI call: {e}")
            raise

    def _calculate_cost(self, usage: Any) -> float:
        # This is a simplified cost calculation. Real costs depend on model, input/output tokens, etc.
        # Refer to OpenAI pricing for accurate calculation.
        input_cost_per_token = 0.000005  # Example: gpt-4o input token cost
        output_cost_per_token = 0.000015 # Example: gpt-4o output token cost
        
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens

        cost = (prompt_tokens * input_cost_per_token) + (completion_tokens * output_cost_per_token)
        return cost

