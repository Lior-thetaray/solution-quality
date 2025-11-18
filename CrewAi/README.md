# CrewAI Solution Quality Framework

This CrewAI framework orchestrates multiple AI agents to validate ThetaRay solution quality against SDLC requirements.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. Run the SDLC validation:
```bash
python main.py
```

## Structure

- `agents/` - AI agent definitions
- `tasks/` - Task definitions for each agent
- `tools/` - Custom tools for code analysis
- `config/` - YAML configurations for agents and tasks
- `main.py` - Main orchestration script
- `reports/` - Generated validation reports (auto-created)

## Agents

### SDLC Validator Agent
Validates solution components against SDLC requirements defined in `agent_instructions/agent_sdlc.md`.

**Responsibilities:**
- Feature validation (trace queries, unit tests)
- DAG structure validation
- Dataset ingestion mode verification
- Evaluation flow completeness
- Risk and decisioning validation
- Drift monitoring checks

**Output:** JSON report with quality score (0-100)
