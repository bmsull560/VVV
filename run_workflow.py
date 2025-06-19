print("DEBUG: run_workflow.py script is being executed by Python interpreter.")
import asyncio
import yaml
import logging
import sys

from orchestrator import Orchestrator

# --- Basic Setup (Logging) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Entry point for running the B2BValue workflow."""
    logger.info("--- Initializing B2BValue Workflow ---")
    orchestrator = Orchestrator(workflow_path='workflow.yaml')

    logger.info("Loading initial context from 'initial_context.yaml'")
    with open('initial_context.yaml', 'r') as f:
        initial_context = yaml.safe_load(f)

    logger.info("--- Starting Workflow Execution ---")
    final_context = await orchestrator.run_workflow(initial_context)

    logger.info("--- Workflow Execution Finished ---")
    logger.info("Final Workflow Context:")
    print(yaml.dump(final_context, indent=2))

if __name__ == "__main__":
    print("DEBUG: Inside __name__ == '__main__' block.")
    asyncio.run(main())
