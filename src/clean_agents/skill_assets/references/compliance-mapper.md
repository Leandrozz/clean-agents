# Compliance Mapper Module

Map regulatory requirements to the designed agentic system.
Generates checklists, data flow diagrams, and gap analysis.

---

## 1. Regulation Overview

### Applicable Regulations by Domain

| Domain | Primary Regulations | Key Deadline |
|--------|-------------------|-------------|
| General (EU) | EU AI Act + GDPR | Aug 2, 2026 (high-risk) |
| General (US) | NIST AI RMF | Voluntary framework |
| Healthcare | HIPAA + EU AI Act | Active (HIPAA), Aug 2026 (AI Act) |
| Financial Services | SEC/FINRA + SOX | Active |
| Legal Practice | ABA Opinion 512 + state bars | Active |
| Enterprise SaaS | SOC 2 Type II | Active |
| All with EU data | GDPR | Active |

### Quick Classifier

```
FOR the designed system, ask:
  1. Does it process EU personal data? → GDPR applies
  2. Does it make autonomous decisions affecting people? → EU AI Act high-risk
  3. Does it handle health information? → HIPAA applies
  4. Is it in financial services? → SEC/FINRA applies
  5. Is it for legal work? → ABA guidelines apply
  6. Does it need enterprise trust? → SOC 2 relevant
  7. Is it a US-based AI system? → NIST AI RMF recommended
```

---

## 2. EU AI Act Requirements

### Risk Classification for Agent Systems

| Agent Characteristic | Risk Level | Requirements |
|---------------------|-----------|-------------|
| Autonomous decisions in HR, legal, financial | HIGH-RISK | Full compliance (Art. 6, Annex III) |
| User-facing chatbot | LIMITED | Transparency only (Art. 50) |
| Internal tool with human oversight | MINIMAL | No specific requirements |
| Biometric, law enforcement, education grading | HIGH-RISK | Full compliance + conformity assessment |

### High-Risk Compliance Checklist (deadline: August 2, 2026)

```
Technical Documentation (Art. 11, Annex IV):
  [ ] System architecture description
  [ ] Data requirements and sources
  [ ] Performance testing results
  [ ] Risk management documentation
  [ ] Lifecycle management plan
  [ ] Post-market monitoring plan

Transparency (Art. 13):
  [ ] Instructions for use
  [ ] Performance characteristics
  [ ] Known limitations
  [ ] Human oversight procedures

Human Oversight:
  [ ] Intervention points defined
  [ ] Override mechanisms implemented
  [ ] Audit trail: timestamp, input, output, reasoning
  [ ] Tamper-evident logging

Post-Market:
  [ ] Continuous monitoring plan
  [ ] Incident logging procedure
  [ ] Update/versioning documentation
```

---

## 3. GDPR Requirements

### Agent-Specific Compliance

| Requirement | Agent Component Affected | Implementation |
|------------|------------------------|----------------|
| Legal basis (Art. 6) | All data processing | Consent management or legitimate interest documentation |
| Data minimization (Art. 5) | Memory, context, RAG | PII stripping, de-identification, minimal context |
| Right to explanation (Art. 22) | Autonomous decisions | Decision logging, explainable reasoning traces |
| Right to deletion (Art. 17) | Memory, conversation history | Auto-delete policies, user-triggered purge |
| Data transfer (Art. 46) | API calls to non-EU providers | SCCs with providers, Transfer Impact Assessment |
| DPIA (Art. 35) | High-risk automated processing | Document risks, mitigations, DPO review |

### PII Handling in Agent Systems

```
BEFORE agent sees data:
  1. Strip unnecessary PII (names → "User_001")
  2. Mask sensitive fields (SSN → "***-**-1234")
  3. Classify data sensitivity level

IN agent memory:
  1. Encrypt at rest (AES-256)
  2. Encrypt in transit (TLS 1.2+)
  3. Access control per agent role
  4. No PII in system prompts or few-shot examples

AFTER agent processes:
  1. Scan output for PII leakage
  2. Apply retention policy (auto-delete after N days)
  3. Log data access for audit trail
```

### Vector DB Security (RAG/GraphRAG)

| Risk | Mitigation |
|------|-----------|
| Embeddings can reconstruct PII | Encrypt embedding storage |
| Access controls stripped during vectorization | Implement document-level RBAC on retrieval |
| No audit trail on vector queries | Log all retrieval queries with user context |
| Cross-document contamination | Namespace isolation per data sensitivity level |

---

## 4. SOC 2 Requirements

### Trust Service Criteria for Agents

| TSC | Agent Requirement | Implementation |
|-----|-------------------|----------------|
| CC6.1 Logical Access | Restrict agent tool access | Least-privilege, tool whitelisting, RBAC |
| CC6.2 Access Monitoring | Detect unauthorized access | Real-time alerting, anomaly detection |
| CC7.2 Security Monitoring | Detect security events | SIEM integration, centralized logging |
| PI1.1 Processing Objectives | Accurate agent outputs | Validation, accuracy monitoring, rollback |
| PI1.2 Requirements | Prevent unauthorized changes | API key rotation (90 days), service isolation |
| A1.1 Availability | Meet uptime SLA | Health checks, failover, graceful degradation |
| C1.1 Confidentiality | Protect sensitive data | Encrypted memory, no plaintext logs |
| P2 Authorization | User consent for data use | Consent management, privacy-by-design |

### SOC 2 Audit Evidence for Agents

| Evidence Type | What to Provide | Retention |
|--------------|----------------|-----------|
| Access logs | All agent tool invocations | 1 year |
| Configuration change logs | Prompt/model version changes | 1 year |
| Incident response records | Agent failure investigations | 3 years |
| Testing evidence | Eval suite results, red team findings | 1 year |
| Policy documents | Agent governance policies | Current + 1 prior |

---

## 5. HIPAA Requirements

### When HIPAA Applies to Agent Systems

```
IF agent accesses, processes, or transmits Protected Health Information (PHI)
  → Even transiently during inference
  → AI vendor becomes a Business Associate
  → BAA required before any PHI processing
```

### PHI Handling Rules for Agents

| Rule | Implementation |
|------|---------------|
| BAA with every AI vendor | Execute before deployment |
| Zero data retention | Configure API for zero-retention mode |
| Encryption mandatory (2025 update) | AES-256 at rest, TLS 1.2+ in transit |
| Audit trail | Log: agent ID, human authorizer, operation, PHI accessed, timestamp |
| Breach notification | Within 60 days, document all suspected breaches |
| Minimum necessary | Agents receive only PHI needed for specific task |
| No training data reuse | PHI never used for model fine-tuning |

### HIPAA-Compatible Agent Patterns

```
COMPLIANT:
  Doctor → HIPAA-compliant API (zero retention) → Agent processes → Auto-delete

NON-COMPLIANT:
  Doctor → Consumer ChatGPT → Data retained for training → PHI exposure
```

---

## 6. Financial Services (SEC/FINRA)

### Key Principle

"FINRA rules are technologically neutral. Securities laws apply to AI agents
just as they apply to any other business tool."

### Agent Compliance Requirements

| Application | Regulatory Constraint | Required Control |
|------------|----------------------|-----------------|
| Trading agent | Market manipulation (Reg SHO) | Human approval for all trades, kill switches |
| Advisory chatbot | Suitability, fiduciary duties | Disclose AI, human supervisor sign-off |
| Compliance monitor | Pattern-based surveillance | Audit trail, supervised review |
| Account opening | KYC accuracy | Human final review, identity verification |
| Risk management | Decision transparency | Explainability logs per decision |

---

## 7. Legal Practice (ABA)

### Six Core Obligations (ABA Opinion 512)

| Obligation | Rule | Agent Requirement |
|-----------|------|-------------------|
| Competence | 1.1 | Understand AI limitations before use |
| Confidentiality | 1.6 | BAA-compliant vendors only, client consent |
| Communication | 1.4 | Disclose AI use, explain limitations |
| Candor | 3.3 | Verify AI-generated research and citations |
| Supervision | 5.1/5.3 | Review all AI output before delivery |
| Fee Reasonableness | 1.5 | Adjust fees for AI efficiency |

---

## 8. Regulation-to-Component Mapping Matrix

Use this matrix to quickly identify which regulations affect which agent components:

| Component | EU AI Act | GDPR | SOC 2 | HIPAA | FINRA | ABA |
|-----------|----------|------|-------|-------|-------|-----|
| Tool Access Control | Art. 13 | Art. 5 | CC6 | 164.312 | Suitability | 5.1 |
| Decision Logging | Art. 11 | Art. 15 | PI1.2 | 164.312(b) | Reg SHO | 3.3 |
| User Notification | Art. 50 | Art. 13 | P2 | Privacy notice | Communications | 1.4 |
| Data Retention | Art. 5(1)(e) | Art. 5(1)(e) | A1.1 | 164.312(b) | — | 1.6 |
| Multi-Agent Coordination | Art. 13 | Art. 6 | PI1.1 | 164.500 | Scope auth | 1.1 |
| Human Oversight | Art. 13 | — | PI1.3 | Minimum necessary | Rule 4512 | 5.3 |
| Cross-Border Data | Art. 5(1)(f) | Art. 46 | C1.1 | — | Privacy | — |
| Output Accuracy | Art. 11 | Art. 22 | PI1.1-5 | BAA quality | Suitability | 3.3 |

---

## 9. Gap Analysis Template

### How to Generate

For the designed system:

```
1. Identify applicable regulations (use Quick Classifier from Section 1)
2. For each regulation, check each component against the checklist
3. Mark status: COMPLIANT / GAP / NOT_APPLICABLE
4. For each GAP, specify:
   - What's missing
   - Effort to remediate (hours)
   - Priority (Critical / High / Medium / Low)
   - Recommended fix
```

### Gap Report Format

```json
{
  "regulation": "GDPR",
  "component": "Memory System",
  "status": "GAP",
  "finding": "No PII stripping before agent context injection",
  "priority": "Critical",
  "remediation": "Add PII detection + masking layer before agent input",
  "effort_hours": 40,
  "deadline": "Before production deployment"
}
```

---

## 10. Output in HTML Blueprint

Add a "Compliance" tab showing:

1. **Applicable Regulations** — which apply to this system and why
2. **Component Mapping** — matrix showing regulation × component
3. **Gap Analysis** — findings with severity and remediation
4. **Checklists** — per-regulation checklists with status
5. **Data Flow Diagram** — Mermaid showing data paths + compliance controls
6. **Timeline** — compliance deadlines

### Mermaid: Compliance Data Flow

```
graph TB
    USER["User Input"] --> PII["PII Detector<br/>GDPR Art. 5"]
    PII --> AGENT["Agent System<br/>EU AI Act Art. 13"]
    AGENT --> TOOLS["Tools<br/>SOC 2 CC6"]
    AGENT --> MEMORY["Memory<br/>Encrypted AES256"]
    AGENT --> LOG["Audit Trail<br/>All regulations"]
    AGENT --> OUTPUT["Output Filter<br/>GDPR Art. 22"]
    OUTPUT --> USER2["User Response<br/>Art. 50 Disclosure"]

    style PII fill:#ef4444,color:#fff
    style LOG fill:#f59e0b,color:#000
    style OUTPUT fill:#10b981,color:#000
```
