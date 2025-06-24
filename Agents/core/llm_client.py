import os
import openai
import logging
import time
import yaml
from openai import OpenAI, AzureOpenAI, RateLimitError, APIError
from openai.types.chat import ChatCompletionMessageParam
import anthropic
from cryptography.fernet import Fernet
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

from enum import Enum
from typing import Optional, Dict, Any, List, Tuple

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    AZURE_OPENAI = "azure_openai"
    MOCK = "mock"

class LLMClient:
    """Production-ready LLM client with security, retry logic, and synchronous calls"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.provider = LLMProvider(self.config.get('provider', 'openai'))
        self.api_key = self._get_secure_api_key()
        self.model = self.config.get('model', 'gpt-4')
        self.temperature = self.config.get('temperature', 0.1)
        self.max_tokens = self.config.get('max_tokens', 4096)
        self.timeout = self.config.get('timeout', 60)
        self.retry_attempts = self.config.get('retry_attempts', 3)
        self.retry_delay = self.config.get('retry_delay', 1)
        
        # Thread pool for sync calls
        self._executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="llm_client")
        self._lock = threading.Lock()
        
        # Initialize provider client
        self._init_provider_client()
        
        logger.info(f"LLMClient initialized with provider: {self.provider.value}, model: {self.model}")

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file or environment variables"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                return config_data.get('globals', {}).get('llm', {})
        
        # Fallback to environment variables
        provider_str = os.getenv('LLM_PROVIDER', 'openai').lower()
        if provider_str == 'mock':
            provider = LLMProvider.MOCK
        else:
            provider = LLMProvider(provider_str)
        return {
            'provider': provider.value,
            'model': os.getenv('LLM_MODEL', 'gpt-4'),
            'temperature': float(os.getenv('LLM_TEMPERATURE', '0.1')),
            'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '4096')),
            'timeout': int(os.getenv('LLM_TIMEOUT', '60')),
            'retry_attempts': int(os.getenv('LLM_RETRY_ATTEMPTS', '3')),
            'retry_delay': int(os.getenv('LLM_RETRY_DELAY', '1'))
        }

    def _get_secure_api_key(self) -> str:
        """Securely retrieve API key with encryption support"""
        api_key = os.getenv('LLM_API_KEY')
        if not api_key:
            raise ValueError(f"LLM_API_KEY environment variable not set for provider {self.provider.value}")
        
        # Check if key is encrypted
        encryption_key = os.getenv('LLM_KEY_ENCRYPTION_KEY')
        if encryption_key and api_key.startswith('gAAAAAA'):  # Fernet token prefix
            try:
                fernet = Fernet(encryption_key.encode())
                api_key = fernet.decrypt(api_key.encode()).decode()
                logger.debug("API key decrypted successfully")
            except Exception as e:
                logger.error(f"Failed to decrypt API key: {e}")
                raise ValueError("Invalid encrypted API key")
        
        return api_key

    def _init_provider_client(self):
        """Initialize the appropriate provider client"""
        if self.provider == LLMProvider.OPENAI:
            self.client = openai.OpenAI(
                api_key=self.api_key,
                timeout=self.timeout
            )
        elif self.provider == LLMProvider.AZURE_OPENAI:
            self.client = AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01'),
                timeout=self.timeout
            )
        elif self.provider == LLMProvider.ANTHROPIC:
            self.client = anthropic.Anthropic(api_key=self.api_key, timeout=self.timeout)
        elif self.provider == LLMProvider.MOCK:
            self.client = MockLLMClient(config_path=None) # Mock client doesn't need external API key
        else:
            raise ValueError(f"Unsupported provider: {self.provider.value}")

    def generate_text_sync(self, prompt: str, system_message: Optional[str] = None, stop_sequences: Optional[List[str]] = None) -> Dict[str, Any]:
        """Synchronous text generation with retry logic"""
        with self._lock:
            for attempt in range(self.retry_attempts):
                try:
                    start_time = time.time()
                    generated_text, tokens_used, cost_usd = "", 0, 0.0

                    if self.provider == LLMProvider.OPENAI or self.provider == LLMProvider.AZURE_OPENAI:
                        generated_text, tokens_used, cost_usd = self._generate_text_openai_internal(prompt, system_message, stop_sequences)
                    elif self.provider == LLMProvider.ANTHROPIC:
                        generated_text, tokens_used, cost_usd = self._generate_text_anthropic_internal(prompt, system_message, stop_sequences)
                    elif self.provider == LLMProvider.MOCK:
                        result = self.client.generate_text_sync(prompt, system_message=system_message, stop_sequences=stop_sequences)
                        generated_text = result["text"]
                        tokens_used = result["tokens_used"]
                        cost_usd = result["cost_usd"]
                    else:
                        raise ValueError(f"Unsupported provider: {self.provider.value}")

                    execution_time = time.time() - start_time
                    logger.info(f"LLM call successful - Tokens: {tokens_used}, Cost: ${cost_usd:.4f}, Time: {execution_time:.2f}s")

                    return {
                        "text": generated_text,
                        "tokens_used": tokens_used,
                        "cost_usd": cost_usd,
                        "execution_time_seconds": execution_time,
                        "model": self.model,
                        "provider": self.provider.value
                    }

                except (openai.RateLimitError, openai.APIError, anthropic.APIError) as e:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"API error ({type(e).__name__}) on attempt {attempt + 1}/{self.retry_attempts}, waiting {wait_time}s")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(wait_time)
                    else:
                        logger.error(f"API error ({type(e).__name__}) after {self.retry_attempts} attempts")
                        raise
                except Exception as e:
                    logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                    else:
                        raise

    async def generate_text_async(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Asynchronous text generation wrapper"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, 
            self.generate_text_sync, 
            prompt, 
            **kwargs
        )

    def _generate_text_openai_internal(self, prompt: str, system_message: Optional[str] = None, stop_sequences: Optional[List[str]] = None) -> Tuple[str, int, float]:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            seed=self.seed,
            stop=stop_sequences
        )
        generated_text = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens
        cost_usd = self._calculate_openai_cost(response.usage.prompt_tokens, response.usage.completion_tokens)
        return generated_text, tokens_used, cost_usd

    def _generate_text_anthropic_internal(self, prompt: str, system_message: Optional[str] = None, stop_sequences: Optional[List[str]] = None) -> Tuple[str, int, float]:
        messages = []
        if system_message:
            messages.append({"role": "user", "content": system_message}) # Anthropic uses user role for system messages in some models
        messages.append({"role": "user", "content": prompt})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=messages,
            stop_sequences=stop_sequences
        )
        generated_text = response.content[0].text.strip()
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        cost_usd = self._calculate_anthropic_cost(response.usage.input_tokens, response.usage.output_tokens)
        return generated_text, tokens_used, cost_usd

    def _calculate_openai_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        # Pricing as of 2024-05-15, for gpt-4o. Prices are per 1M tokens.
        # This should be updated as models and pricing change.
        input_cost_per_million = 5.00
        output_cost_per_million = 15.00

        cost = (prompt_tokens / 1_000_000) * input_cost_per_million + \
               (completion_tokens / 1_000_000) * output_cost_per_million
        return cost

    def _calculate_anthropic_cost(self, input_tokens: int, output_tokens: int) -> float:
        # Pricing for Claude 3 Opus as of 2024-05-15. Prices are per 1M tokens.
        # This should be updated as models and pricing change.
        input_cost_per_million = 15.00
        output_cost_per_million = 75.00

        cost = (input_tokens / 1_000_000) * input_cost_per_million + \
               (output_tokens / 1_000_000) * output_cost_per_million
        return cost

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model configuration"""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on LLM service"""
        try:
            start_time = time.time()
            result = self.generate_text_sync("Test connection. Respond with 'OK'.")
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_seconds": response_time,
                "tokens_used": result.get("tokens_used", 0),
                "model": self.model,
                "provider": self.provider.value
            }
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.model,
                "provider": self.provider.value
            }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._executor.shutdown(wait=True)

# Legacy support - maintains backward compatibility
class MockLLMClient(LLMClient):
    """Mock LLM client for testing and offline mode"""
    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        logger.info("MockLLMClient initialized. Responses will be simulated.")

    def generate_text_sync(self, prompt: str, **kwargs) -> Dict[str, Any]:
        logger.info(f"MockLLMClient received prompt: {prompt[:50]}...")
        # Simulate a response
        simulated_text = f"Mock response for: {prompt}"
        tokens_used = len(simulated_text.split()) # Basic token count
        cost_usd = 0.0 # No cost for mock
        execution_time = 0.1 # Simulate quick response

        return {
            "text": simulated_text,
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
            "execution_time_seconds": execution_time,
            "model": self.model,
            "provider": self.provider.value
        }

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "response_time_seconds": 0.01,
            "model": self.model,
            "provider": self.provider.value
        }


class OpenAIClient(LLMClient):
    """Legacy OpenAI client - redirects to new LLMClient"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        if api_key:
            os.environ['LLM_API_KEY'] = api_key
        config = {
            'provider': 'openai',
            'model': model
        }
        super().__init__()
        
    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Legacy async method"""
        return await self.generate_text_async(prompt, **kwargs)
