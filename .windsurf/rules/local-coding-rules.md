---
trigger: always_on
---

1. Code Quality & Best Practices
Rule 1.1 - Readability & Maintainability: Generated code MUST prioritize readability, clarity, and maintainability. It SHOULD include comments for complex logic and adhere to established coding style guides (e.g., PEP 8 for Python).
Rule 1.2 - Efficiency: Code SHOULD be optimized for performance where applicable, considering computational complexity and resource usage.
Rule 1.3 - Modularity: Generated code SHOULD be modular, reusable, and adhere to single-responsibility principles. It MUST NOT introduce unnecessary dependencies or monolithic blocks.
Rule 1.4 - Idempotency (where applicable): If the code performs actions that modify state, it SHOULD be designed to be idempotent when executed multiple times (i.e., producing the same result).

2. Security & Vulnerability Prevention
Rule 2.1 - Secure Coding Practices: Generated code MUST follow secure coding best practices to prevent common vulnerabilities (e.g., SQL injection, cross-site scripting, arbitrary code execution, insecure deserialization).
Rule 2.2 - Input Sanitization: All inputs processed by generated code MUST be properly sanitized and validated to prevent malicious data injection.
Rule 2.3 - Dependency Vulnerability: The agent MUST prioritize using well-maintained, secure, and up-to-date libraries and dependencies, and SHOULD NOT introduce known vulnerable components.

3. Testing & Verification
Rule 3.1 - Testability: Generated code MUST be inherently testable, with clear interfaces and predictable behavior.
Rule 3.2 - Self-Correction/Verification: The Coder Agent SHOULD attempt to self-verify its generated code where possible (e.g., syntax checks, basic unit tests, static analysis) before offering it as a solution.
Rule 3.3 - Human Review Gateway: All generated code that impacts production systems or sensitive data MUST pass through a Human Review Agent (or similar human oversight) before deployment.

4. Integration & Environment Adherence
Rule 4.1 - Environment Compatibility: Generated code MUST be compatible with the target runtime environment and its constraints (e.g., Python version, available libraries, container environment).
Rule 4.2 - API Adherence: If interacting with existing APIs or internal services, generated code MUST strictly adhere to those API contracts and authentication mechanisms.
Rule 4.3 - Configuration Management: Sensitive configurations (e.g., API keys, database credentials) MUST NOT be hardcoded and SHOULD be managed via secure environment variables or a configuration management system.

5. Error Handling & Debugging
Rule 5.1 - Clear Error Messaging: Generated code SHOULD include clear and informative error messages to aid in debugging and troubleshooting.
Rule 5.2 - Robust Exception Handling: Code MUST implement appropriate exception handling to prevent crashes and ensure graceful degradation.
Rule 5.3 - Logging within Code: Generated code SHOULD incorporate appropriate logging to track its execution flow and provide insights into its behavior.

6. Scope & Constraint Adherence
Rule 6.1 - Task Focus: The Coder Agent MUST strictly adhere to the specific coding task assigned by the Orchestrator and MUST NOT attempt to perform actions outside its defined scope.
Rule 6.2 - Resource Limits: The Coder Agent MUST respect any allocated resource limits (e.g., execution time, memory) for code generation and compilation processes.