import os
import openai
import logging
import time
import yaml
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from cryptography.fernet import Fernet
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    AZURE_OPENAI = "azure_openai"

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
        return {
            'provider': os.getenv('LLM_PROVIDER', 'openai'),
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
            self.client = openai.AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01'),
                timeout=self.timeout
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider.value}")

    def generate_text_sync(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Synchronous text generation with retry logic"""
        with self._lock:
            for attempt in range(self.retry_attempts):
                try:
                    start_time = time.time()
                    
                    # Prepare parameters
                    params = {
                        'model': kwargs.get('model', self.model),
                        'messages': [{"role": "user", "content": prompt}],
                        'temperature': kwargs.get('temperature', self.temperature),
                        'max_tokens': kwargs.get('max_tokens', self.max_tokens),
                        'timeout': kwargs.get('timeout', self.timeout)
                    }
                    
                    # Make API call
                    response = self.client.chat.completions.create(**params)
                    
                    execution_time = time.time() - start_time
                    
                    # Extract response data
                    text_content = response.choices[0].message.content
                    tokens_used = response.usage.total_tokens if response.usage else 0
                    cost_usd = self._calculate_cost(response.usage) if response.usage else 0.0
                    
                    logger.info(f"LLM call successful - Tokens: {tokens_used}, Cost: ${cost_usd:.4f}, Time: {execution_time:.2f}s")
                    
                    return {
                        "text": text_content,
                        "tokens_used": tokens_used,
                        "cost_usd": cost_usd,
                        "execution_time_seconds": execution_time,
                        "model": params['model'],
                        "provider": self.provider.value
                    }
                    
                except openai.RateLimitError as e:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Rate limit hit, attempt {attempt + 1}/{self.retry_attempts}, waiting {wait_time}s")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Rate limit exceeded after {self.retry_attempts} attempts")
                        raise
                        
                except openai.APIError as e:
                    logger.error(f"OpenAI API error on attempt {attempt + 1}: {e}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
                    else:
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

    def _calculate_cost(self, usage: Any) -> float:
        """Calculate cost based on token usage and model"""
        if not usage:
            return 0.0
            
        # Model-specific pricing (per 1K tokens)
        pricing = {
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002}
        }
        
        model_pricing = pricing.get(self.model, pricing['gpt-4'])
        
        prompt_tokens = usage.prompt_tokens if hasattr(usage, 'prompt_tokens') else 0
        completion_tokens = usage.completion_tokens if hasattr(usage, 'completion_tokens') else 0
        
        input_cost = (prompt_tokens / 1000) * model_pricing['input']
        output_cost = (completion_tokens / 1000) * model_pricing['output']
        
        return input_cost + output_cost

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
