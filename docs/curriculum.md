# Gen AI Curriculum

Canonical topic vocabulary for the CoE wiki. Concept stubs, synthesis prompts, and domain indexes use these exact titles as the authoritative node names.

Each sub-topic slug is derived by lower-casing the title and replacing spaces with hyphens (e.g. "Chunking Strategies" → `chunking-strategies`).

---

## Gen AI Fundamentals

- LLM Functional Mental Model
- Prompting and Context Discipline
- Structured Output and Schema Contracts
- Sampling and Decoding Controls
- Tokens, Cost and Caching
- When Not to Use AI, and Scoping a Client Ask
- Scoping and Estimating an AI Engagement
- What AI Solution Is a Fit to This Problem
- Evaluation, First Pass
- Security Baseline: Injection, Lethal Trifecta, PHI
- Shipping an LLM Feature
- Human Review and Escalation Design

## Retrieval and Knowledge

- Embeddings and Vector Search
- Lexical Retrieval and BM25
- Chunking Strategies
- The Retrieval Pipeline End to End
- Hybrid Search and Fusion
- Reranking
- Document Processing: OCR, Layout, Tables
- Ingestion and Incremental Updates
- Metadata and Access-Scoped Retrieval
- Query Understanding and Rewriting
- RAG Failure Diagnosis
- Groundedness and Citation Verification
- Late Interaction Retrieval
- GraphRAG and Structured Knowledge
- Structured Data and Text-to-SQL
- Long Context versus Retrieval, and CAG

## Agents and Autonomy

- Agent, Workflow, or Pipeline
- The Agent Loop
- Tool Calling and Tool Design
- MCP and Tool Interoperability
- Context Engineering
- Agent Memory
- Choosing a Framework, or Writing the Loop Yourself
- Build the Same Agent Twice
- Agentic Retrieval
- Planning and Task Decomposition
- Long-Horizon Reliability
- Sandboxed Code Execution
- Multi-Agent Systems
- Agent to Agent Interoperability

## Evaluation and Quality

- Error Analysis and Failure Taxonomy
- Golden Datasets and Labelling
- Deterministic and Property-Based Testing
- LLM as Judge and Rubric Design
- Judge Bias and Mitigation
- Builder and Grader Separation
- Retrieval and RAG Metrics
- Agent Trajectory Evaluation
- Regression Testing for Non-Deterministic Systems
- Knowing When Not to Answer
- Observability and Tracing
- Online Experimentation
- Feedback Capture and the Data Flywheel
- The Eval Harness as Infrastructure

## Models: Capability and Adaptation

- Model and Provider Selection Under Constraints
- Reasoning Models and Test-Time Compute
- Multimodal Understanding and Generation
- Provider and Model Migration
- Gate: Prove Prompting and Retrieval Have Run Out
- Fine-Tuning and PEFT
- Training Data Curation
- Post-Training and Preference Optimisation
- Distillation and Small Models
- Prompt and Model Release Engineering

## Security and Governance

- Threat Modelling for AI Systems
- Prompt Injection, Direct and Indirect
- Tool Permissions and Least Privilege
- Guardrails and Filtering Layers
- Data Leakage and Exfiltration
- Supply Chain and Provenance
- Healthcare Delivery: PHI, HIPAA, BAA Scope
- Privacy, Residency and Regional Handling
- Fairness and Bias Auditing
- Regulatory Landscape

## Platform and Operations

- Model Packaging and Serving
- Inference and Serving Economics
- Model Routing and Cascades
- Latency Engineering
- Caching Strategies
- Scaling and Load Behaviour
- Gateway Patterns: Keys, Budgets, Quotas
- Generative Endpoint Contracts
- Queues and Background Jobs
- Long-Running and Asynchronous Work
- Idempotency and Safe Retries
- Error and Degradation Contracts
- Cloud Fundamentals and IAM
- Containers and Infrastructure as Code
- CI/CD for AI Systems
- Canary, Shadow and Blue-Green Releases
- The AWS AI Stack
- Multi-Tenancy and Isolation
- Data Modelling, Relational and Vector
- Ingestion and Pipeline Orchestration
- Data Validation and Contracts
- Monitoring and Drift Detection
- Cost Governance and Attribution
- Incident Response for AI Systems

## Classical ML and Deep Learning

- Supervised Learning Workflow
- Train, Validation, Test and Leakage
- Metrics and Imbalanced Data
- Linear Models, Bias, Variance and Regularisation
- Feature Engineering
- Tree Ensembles and Gradient Boosting
- Clustering, Dimensionality Reduction and Anomaly Detection
- Time Series and Forecasting
- Recommender Systems
- Interpretability and Attribution
- Neural Network Fundamentals and the Training Loop
- Optimisation, Regularisation and Debugging Training
- Transfer Learning and Fine-Tuning
- Text Preprocessing and Tokenisation
- Sequence Models and the Transformer Architecture
- Text Classification and Information Extraction
- Speech and ASR Pipelines
- Image Fundamentals and Convolutional Networks
- Image Classification and Transfer Learning
- Object Detection and Segmentation
- Vision-Language Models and Document Understanding
- Data Literacy, EDA and Experiment Design
- Annotation and Labelling Operations
- When Classical Beats Generative
