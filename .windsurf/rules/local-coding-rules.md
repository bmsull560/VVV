---
trigger: always_on
---

Local Rules (Specific to Modules, Agents, or Components)
These rules provide granular guidance relevant to specific parts of the codebase, often reflecting design patterns or domain-specific best practices.

AI Agent Specific Conventions (Agents/global_config.yaml):

Rule: Each agent should have its own main.py and configuration (.yaml) file under its dedicated directory (e.g., agents/intake_assistant/main.py, Agents/intake_assistant_agent.yaml).

Implementation for AI Agents: When an AI agent generates new agent code or modifies existing ones, it would follow this directory and file structure.

Rule: Agents must inherit from a common AgentBase class (agents/core/agent_base.py) to ensure consistent interface and core functionalities.

Implementation for AI Agents: AI agents generating new agent code would be trained to adhere to this inheritance model.

Memory Interaction Patterns:

Rule: Agents interacting with specific memory tiers (e.g., memory/episodic.py, memory/semantic.py) should use the prescribed patterns for writing and retrieving data, including proper entity schemas (docs/entity_schemas.md).

Implementation for AI Agents: AI agents would be guided to generate code that correctly structures data according to defined entity schemas before writing to memory and to interpret data according to these schemas upon retrieval.

UI Component Standards (temp_ui_project):

Rule: React/TypeScript components must follow established patterns (e.g., functional components, proper use of hooks useModelBuilder.ts, useFinancialCalculations.ts).

Configuration Source: Implied by existing UI component code and tsconfig.json.

Implementation for AI Agents: AI agents generating UI code would be specifically trained on the React/TypeScript best practices and component architecture used in temp_ui_project/src/components/workflow/ and temp_ui_project/src/components/model-builder/.

Local Coding Rules (.windsurf/rules/local-coding-rules.md):

Rule: Adherence to any specific coding best practices or anti-patterns documented in local-coding-rules.md (e.g., specific naming conventions, avoidance of certain library functions, preferred design patterns for domain-specific logic).

Implementation for AI Agents: These would serve as direct guidelines for agent code generation, either through fine-tuning, prompt engineering, or post-generation linting against these specific rules.