import yaml
import os
from typing import Dict, Any

class IntakeAssistantAgent:
    """
    An agent responsible for gathering initial user input and extracting key business context.
    """

    def __init__(self, agent_definition_path: str):
        """
        Initializes the agent by loading its definition from a YAML file.

        Args:
            agent_definition_path (str): The path to the agent's YAML definition file.
        """
        self.definition = self._load_definition(agent_definition_path)
        self.agent_id = self.definition.get('agent_id')
        print(f"Successfully initialized agent: {self.agent_id}")

    def _load_definition(self, path: str) -> Dict[str, Any]:
        """
        Loads the YAML definition file.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Agent definition file not found at: {path}")
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def execute(self, user_raw_input: str) -> Dict[str, Any]:
        """
        Executes the agent's core logic.

        This function takes the raw user input, simulates a call to an LLM
        to process it, and returns the structured output.

        Args:
            user_raw_input (str): The unstructured text provided by the user.

        Returns:
            Dict[str, Any]: A dictionary containing the structured output,
                            such as company profile and pain points.
        """
        print(f"\nExecuting agent '{self.agent_id}' with user input...")
        
        # --- Placeholder for LLM Interaction ---
        # In a real implementation, this is where you would:
        # 1. Format the initial_prompt from the YAML definition.
        # 2. Add the user_raw_input to the prompt.
        # 3. Call the specified LLM (e.g., GPT-4) via its API.
        # 4. Parse the LLM's response into the structured output format.
        
        print("Simulating LLM call to process user input...")
        # This is a mock response for demonstration purposes.
        mock_llm_output = {
            "company_profile": {
                "company_name": "Global Tech Inc.",
                "industry": "Software as a Service (SaaS)",
                "annual_revenue_usd": 150000000,
                "employee_count": 800
            },
            "initial_pain_points": [
                "High customer churn rate",
                "Slow product development cycle",
                "Inefficient manual processes in marketing"
            ],
            "strategic_alignment": "The company aims to leverage AI to automate processes and improve customer retention, aligning perfectly with our solution's value proposition."
        }
        
        print("Agent execution complete.")
        return mock_llm_output

if __name__ == '__main__':
    # This demonstrates how to run the agent.
    # The orchestrator would typically manage this process.

    # Relative path to the agent's YAML definition
    # This assumes you run this script from the project root directory (e.g., /home/bmsul/B2BValue)
    definition_path = os.path.join('Agents', 'intake_assistant_agent.yaml')

    try:
        # 1. Initialize the agent
        intake_agent = IntakeAssistantAgent(definition_path)

        # 2. Define a sample user input
        sample_input = "We are Global Tech Inc., an 800-person SaaS company with $150M in revenue. We're struggling with customer churn and our marketing team is bogged down by manual work. We need to innovate faster."

        # 3. Execute the agent
        structured_output = intake_agent.execute(sample_input)

        # 4. Print the results
        print("\n--- Agent Output ---")
        print(yaml.dump(structured_output, indent=2))
        print("--------------------")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure you are running this script from the root of the B2BValue project directory.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
