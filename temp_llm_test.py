import os
import sys

# Add the parent directory of agents to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'agents', 'core')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'agents')))


print("Attempting to import LLMClient...")
try:
    from llm_client import LLMClient
    print("LLMClient imported successfully.")

    print("Attempting to instantiate LLMClient...")
    # Mock config for testing purposes
    mock_config = {
        'provider': 'openai',
        'model': 'gpt-4o',
        'api_key': 'fake_key',
        'temperature': 0.1,
        'max_tokens': 4096,
        'timeout': 60,
        'retry_attempts': 3,
        'retry_delay': 1
    }
    # Set a fake API key environment variable, as LLMClient expects it.
    os.environ['LLM_API_KEY'] = 'sk-fake-api-key'
    os.environ['LLM_PROVIDER'] = 'openai'

    client = LLMClient(config=mock_config)
    print("LLMClient instantiated successfully.")

except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
