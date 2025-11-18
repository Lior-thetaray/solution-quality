# ThetaRay Solution Quality - Copilot Instructions

## Architecture Overview

This is a **QA validation agent** for ThetaRay AML/fraud detection solutions built on the ThetaRay platform. The codebase validates that solutions contain required components for production readiness.

### Core Structure
- **`Sonar/`** - Reference ThetaRay solution implementation (data ingestion → ML training → alert generation)
- **`agent_instructions/agent_sdlc.md`** - Canonical QA validation spec defining all required solution components
- **`CrewAI/`** - Multi-agent orchestration for automated validation

### Domain-Driven Design
Each solution lives under `Sonar/domains/<domain_name>/` with standardized folders:
- **`features/`** - Feature engineering logic (PySpark transformations)
- **`datasets/`** - Dataset metadata definitions using `thetaray.api.solution.DataSet`
- **`evaluation_flows/`** - ML pipeline configuration (model refs, trace queries, customer insights)
- **`config/core/`** - YAML configs defining active features and parameters
- **`notebooks/`** - Jupyter notebooks for full pipeline: data upload, enrichment, wrangling, training, evaluation, drift monitoring
- **`libs/`** - Domain-specific utilities (drift testing, data generators)
- **`graphs/`** - Graph entity metadata for network visualization
- **`risks/`** - Alert risk definitions and decisioning logic

Shared code in `Sonar/domains/common/` includes feature engineering base classes, config loaders, and trace query collectors.

## Critical Workflows

### Feature Development Pattern
Features inherit from `AggFeature` in `common/libs/feature_engineering.py`:
1. Define `identifier`, `version`, `description`, `required_columns`, `group_by_keys`
2. Implement `get_agg_exprs()` returning PySpark aggregation expressions
3. Add `trace_query()` to filter transactions in UI (or return empty string for global trace)
4. Declare `output_fields` with `Field` metadata including `category` for UI grouping and `dynamic_description` for alert narratives

Example: `Sonar/domains/demo_fuib/features/core/customer/sum_trx_cash_in.py`

### Configuration-Driven Features
Features are activated via YAML (`config/core/<entity>/<cadence>/wrangling.yaml`):
- `active: true` - Include in wrangling/evaluation
- `train: true` - Use for ML model training (features with `train: false` are forensic-only)

Feature discovery happens via `common/libs/features_discovery.py` which loads instances from YAML config.

### Trace Queries
**Every trained feature** must either:
1. Define a `trace_query()` method filtering transactions for that feature, OR
2. Be included in the global trace query via `EvaluationFlow.global_trace_query`

Trace queries map features to filterable transaction sets in the investigation UI. See `common/libs/trace_query_collector.py` for assembly logic.

### Evaluation Flow Structure
`evaluation_flows/<name>_ef.py` defines the ML pipeline:
```python
EvaluationFlow(
    identifier="cust_month_ef",
    input_dataset="customer_monthly",  # wrangled dataset
    evaluation_steps=[AlgoEvaluationStep(
        feature_extraction_model=ModelReference('customer_monthly_fe'),
        detection_model=ModelReference('customer_monthly_ad'),
    )],
    global_trace_query=TraceQuery(...),  # Base transaction query
    trace_queries=_trace_queries(),      # Feature-specific filters
    customer_insights=CustomerInsights(...),  # KYC widget config
)
```

### Dataset Ingestion Modes
- **`IngestionMode.APPEND`** - For transactional datasets (add new records)
- **`IngestionMode.UPDATE`** - For dimensional data with updates (e.g., customer insights)
- **`IngestionMode.OVERWRITE`** - Full refresh (auxiliary datasets)

Transactional datasets should use `upload_by_execution_date` for incremental loads.

## Airflow DAG Patterns

DAGs use `thetaray.api.airflow.RunNotebookOperator` to execute notebooks:
```python
from thetaray.api.airflow import RunNotebookOperator, ExecutionDateMode

RunNotebookOperator(
    task_id="wrangling",
    domain="demo_fuib",
    notebook_name="wrangling",
    dag=dag,
)
```

Standard E2E task flow:
```
copy_data_to_s3 >> upload_data >> entity_resolution >> wrangling >> 
training >> detecting >> publishing_activities >> publishing_dataset >> 
decisioning >> distributing >> graph_netviz
```

See `Sonar/dags/default/end_to_end.py` for reference implementation.

## QA Validation Requirements

The agent validates solutions against `agent_instructions/agent_sdlc.md`:

### Must-Have Components
1. **Trace Queries** - Every `train: true` feature needs trace query or global mapping
2. **Unit Tests** - Each feature should have I/O tests (though `tests/` directory currently absent)
3. **E2E DAG** - Full pipeline from data upload to distribution
4. **Drift Monitoring** - Notebook with PSI/Z-score tests (see `demo_fuib/libs/drift_lib.py`)
5. **Algo Validation** - Model performance validation notebook
6. **Dataset Metadata** - All datasets with mandatory fields, correct ingestion modes
7. **Risk Definitions** - Decisioning logic with valid metadata references
8. **Customer Insights** - KYC and activity widgets in evaluation flow
9. **Distribution** - Alert distribution to investigation console

### Data Upload Best Practices
- Use `upload_by_execution_date` for transactional datasets
- Set `IngestionMode.APPEND` for transactions
- Auxiliary datasets use `UPDATE` or `OVERWRITE`

## Development Conventions

### Import Patterns
External platform APIs:
```python
from thetaray.api.solution import DataSet, Field, DataType, IngestionMode
from thetaray.api.airflow import RunNotebookOperator, ExecutionDateMode
from thetaray.common import Settings, Constants
```

Internal utilities:
```python
from common.libs.feature_engineering import AggFeature, FeatureDescriptor
from common.libs.config.loader import load_config
from common.libs.features_discovery import get_features
```

### YAML Configuration
Global params in `config/core/global.yaml`:
```yaml
bau: False
monthly_features_look_back_in_months: 6
global_features_params:
    round_digits: 2
```

Feature-specific params in wrangling YAML under each feature version.

### PySpark Style
- Use `pyspark.sql.functions as f` (not `F`)
- Keep feature logic in pure functions (DataFrame in, DataFrame out)
- Use `OrderedDict` for maintaining column order in aggregations
- Prefer `.withColumn()` chains over complex `select()` statements

## Tech Stack
- **Python 3.x** with PySpark for distributed processing
- **Apache Airflow** for workflow orchestration
- **MLflow** for model tracking (via `thetaray.api.mlflow`)
- **Jupyter** notebooks for interactive development/validation
- **YAML** for declarative configuration
- Platform APIs via `thetaray.*` packages

## Key Files to Reference
- `agent_instructions/agent_sdlc.md` - QA validation specification (authoritative source)
- `Sonar/domains/common/libs/feature_engineering.py` - Feature base classes
- `Sonar/domains/demo_fuib/evaluation_flows/customer_monthly_ef.py` - Full evaluation flow example
- `Sonar/domains/demo_fuib/config/core/customer/monthly/wrangling.yaml` - Feature activation config
- `Sonar/dags/default/end_to_end.py` - Reference DAG structure

## Agent Operating Principles
Per `agent_sdlc.md`:
- **Do NOT write or modify code** - Only validate and report
- Output must be JSON with checks, pass/fail status, and final quality score (0-100)
- Trust the SDLC spec as authoritative for all validations
- Validate both general best practices AND custom rules in agent_sdlc.md Section 3
