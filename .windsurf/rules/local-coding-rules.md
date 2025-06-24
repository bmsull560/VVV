---
trigger: always_on
---

Local Rules (Code Generation & Modification)
These rules, derived from .windsurf/rules/local-coding-rules.md, apply specifically to any agent tasked with writing, modifying, or reviewing code. They ensure the quality, security, and maintainability of the codebase itself.

1. Code Quality and Maintainability

Style and Formatting: All Python code MUST be formatted with black and adhere to ruff linter standards, as enforced by the project's pre-commit hooks.
Type Safety: Code MUST include full type hinting and pass mypy static analysis to ensure type safety.
Documentation: All modules, functions, and complex logic MUST be documented according to the pydocstyle standard.
Modularity: Code MUST be modular and adhere to the single-responsibility principle. It must not introduce unnecessary dependencies or monolithic blocks.
2. Security and Vulnerability Prevention

Secure Coding Practices: Generated code MUST follow secure coding best practices to prevent common vulnerabilities (e.g., injection, XSS).
No Hardcoded Secrets: Sensitive configurations like API keys or credentials MUST NOT be hardcoded. They should be managed securely, for instance through environment variables.
Input Sanitization: All inputs processed by the generated code MUST be properly sanitized and validated.
3. Testability and Verification

Testable Code: All generated code MUST be inherently testable, with clear interfaces and predictable behavior.
Self-Correction: The coding agent SHOULD attempt to self-verify its code (e.g., syntax checks, running unit tests) before submitting it for review.
4. Error Handling and Logging

Robust Exception Handling: Code MUST implement appropriate exception handling to prevent crashes and ensure graceful degradation.
Logging: Generated code SHOULD incorporate appropriate logging to track its execution flow, providing insights for debugging and monitoring.

Do not checkin for most items instead continue to resolution or completion, then move on to the next items in the plan.md
