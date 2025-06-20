# Security Model & Threat Analysis for B2BValue

## Threat Model
- **Actors:** Internal agents, system users, external API integrations, PostgreSQL database access
- **Assets:** Business context, workflow history, semantic knowledge, relationship graph, user credentials, encrypted agent data
- **Threats:**
  - Unauthorized access to sensitive memory tiers
  - Tampering with workflow history or context
  - Injection of malicious or malformed data via agent inputs
  - Data leakage via logs or error messages
  - Credential theft from external system connections
  - SQL injection through database interactions
  - Privilege escalation via agent role manipulation

## RBAC Matrix
| Role   | Working | Episodic | Semantic | Graph | PostgreSQL |
|--------|---------|----------|----------|-------|------------|
| admin  | RWX     | RWX      | RWX      | RWX   | RWX        |
| agent  | R       |          | R        |       | R (limited)|
| system | RWX     | RWX      | RWX      | RWX   | RWX        |
| user   | R       | R        |          |       | R (own)    |

- **R**: Read, **W**: Write, **X**: Delete

## Security Controls

### **Memory & Database Security**
- All memory access mediated by `MemoryManager` with role-based access control
- PostgreSQL connections use encrypted credentials and connection pooling
- EpisodicMemory backend implements SQLAlchemy ORM with parameterized queries
- Default access: agents get read-only to working/semantic, admin/system get full access
- User authentication uses bcrypt password hashing with secure salts

### **Agent Security Framework**
- **Centralized Input Validation**: All agent inputs validated through BaseAgent framework
- **Credential Encryption**: External system credentials encrypted at rest using industry standards
- **Data Sensitivity Handling**: High-sensitivity data marked and handled with enhanced security
- **Audit Logging**: Comprehensive logging of all agent actions and data access
- **Type Safety**: Full type validation prevents injection through malformed inputs

### **Data Protection**
- All entity writes validated for type, required fields, and sensitivity levels
- External (untrusted) JSON schema-validated before processing
- Agent communication secured through MCP protocol with access control
- Workflow state protected through transactional updates and rollback capabilities

## Implemented Security Features

### **Authentication & Authorization**
- PostgreSQL-backed user management with hashed credentials
- Session-based authentication with secure cookie handling
- Role-based permissions enforced at agent and memory tier levels
- Service account isolation for agent-to-database communications

### **Data Validation & Sanitization**
- Centralized validation framework prevents malicious input injection
- Schema validation for all external data sources
- Input sanitization for all user-provided content
- Output validation before data storage in memory tiers

### **Monitoring & Audit**
- All memory mutations logged with timestamps and actor identification
- Access attempt logging for security event analysis
- Critical error logging to dedicated security log files
- Agent execution tracking for performance and security monitoring

## Security Recommendations

### **Operational Security**
- Periodically audit access logs for suspicious patterns
- Rotate admin/system credentials quarterly
- Review and update access control policies when adding new agents
- Monitor credential encryption key rotation schedules

### **Development Security**
- Follow secure coding practices per local-coding-rules.md
- Implement additional custom validations for domain-specific security needs
- Regular security testing of agent input validation frameworks
- Code review all external system integration patterns

### **Infrastructure Security**
- Secure PostgreSQL configuration with restricted network access
- Regular backup and disaster recovery testing
- Monitor database connection pooling for anomalous patterns
- Implement database-level audit logging for compliance requirements

---
**See also:** `local-coding-rules.md`, `entity_schemas.md`, and agent implementation examples in `/agents/examples/`
