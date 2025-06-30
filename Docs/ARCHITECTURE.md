# B2BValue System Architecture

## 1. Introduction & Vision

This document provides a comprehensive overview of the B2BValue system architecture. The platform is designed as a multi-agent system to automate and enhance the creation of complex business cases, transforming qualitative value propositions into quantifiable financial models.

Our vision is to create a Strategic Decision Intelligence Platform that empowers organizations to make faster, data-driven investment decisions with confidence.

## 2. Core Architectural Principles

- **Modularity & Single Responsibility**: Each agent is a self-contained unit with a specific, well-defined purpose (e.g., risk analysis, ROI calculation). This promotes reusability, testability, and independent development.
- **Scalability & Performance**: The system is built on an asynchronous architecture (FastAPI, asyncio) to handle concurrent requests and long-running agent tasks efficiently.
- **Security First**: Security is integrated at all levels, including secure credential management, access control policies (ACLs), and robust input validation.
- **Extensibility**: The architecture allows for the easy addition of new agents, data sources, and analytical capabilities without disrupting existing workflows.
- **Data-Driven & Stateful**: All agent interactions and generated artifacts are persisted in a centralized Memory Component (MCP), providing a complete audit trail and enabling complex, multi-step workflows.

## 3. High-Level Architecture

```mermaid
graph TD
    subgraph User Interface
        A[React Frontend]
    end

    subgraph API Layer
        B[FastAPI Server]
    end

    subgraph Agent Orchestration
        C[Workflow Coordinator]
    end

    subgraph Core Agents
        D[Intake Assistant]
        E[Value Driver Agent]
        F[ROI Calculator]
        G[Narrative Generator]
        H[... Other Agents]
    end

    subgraph Core Services
        I[Memory Component (MCP)]
        J[LLM Client]
        K[Database (PostgreSQL)]
    end

    A --> B
    B --> C
    C --> D
    C --> E
    C --> F
    C --> G
    C --> H
    D --> I
    E --> I
    F --> I
    G --> I
    H --> I
    I --> K
    D --> J
    E --> J
    G --> J
```

## 4. Key Components

### 4.1. Agents
Agents are the core business logic units. Each agent is a specialized Python class inheriting from a `BaseAgent`, which provides common functionalities like validation, error handling, and performance tracking. See `Agent_Inventory_Overview.csv` for a complete list.

### 4.2. Memory Component (MCP)
The Model Context Protocol (MCP) is the system's brain. It provides a secure, versioned, and auditable storage layer for all data artifacts (Entities) created by agents. It leverages a PostgreSQL backend for persistent storage.

### 4.3. API Layer
A FastAPI server exposes the agent capabilities as a set of secure, asynchronous RESTful endpoints. It handles user requests, orchestrates agent execution, and formats the final response.

## 5. Workflow Orchestration

The B2BValue platform follows a 4-phase workflow for business case creation:

1.  **Discovery**: The `IntakeAssistantAgent` captures initial project details, and the `ValueDriverAgent` identifies potential areas of business value.
2.  **Quantification**: The `ROICalculatorAgent` and `SensitivityAnalysisAgent` model the financial impact and risks associated with the project.
3.  **Narrative Generation**: The `NarrativeGeneratorAgent` creates a compelling story tailored to specific stakeholder personas (e.g., CFO, CIO).
4.  **Composition**: The `BusinessCaseComposerAgent` assembles all the generated artifacts into a final, structured business case document.

A `WorkflowCoordinator` manages the state transitions between these phases, ensuring data flows correctly from one agent to the next.

## 6. Data Flow

Data flows through the system in a structured manner:

1.  The user provides initial input via the UI.
2.  The API layer validates the request and invokes the appropriate agent.
3.  The agent processes the input, performs its analysis (potentially calling an LLM), and creates one or more `KnowledgeEntity` objects.
4.  These entities are stored securely in the MCP.
5.  Subsequent agents in the workflow retrieve data from the MCP using a `project_id` to continue the analysis.
6.  The final result is returned to the user through the API layer.

## 7. Security Model

- **Authentication**: A robust authentication system manages user identities and access.
- **Access Control**: The MCP enforces strict Access Control Lists (ACLs) on all data entities, ensuring agents and users can only access the data they are permitted to see.
- **Data Encryption**: Sensitive credentials for external data sources are encrypted both in transit and at rest.
- **Input Validation**: A centralized validation framework sanitizes and validates all inputs to prevent injection attacks and ensure data integrity.

## 8. Deployment

The application is designed to be deployed using containerization (e.g., Docker) and orchestrated with a system like Kubernetes for scalability and resilience. See `DEPLOYMENT.md` for detailed instructions.
