# Widget Validation Agent

## Overview

The Widget Validation Agent validates that each feature in a ThetaRay solution has the optimal widget type assigned for data visualization in the investigation UI.

## Widget Types

The ThetaRay platform supports 4 widget types:

### 1. BEHAVIORAL (`ExplainabilityType.BEHAVIORAL`)
- **Visualization**: Stacked bar chart over time
- **Best for**: Multi-dimensional time-series data, geographic patterns over time
- **Required fields**: 
  - `time_range_value` and `time_range_unit`
  - `category_lbl` and `category_var` 
  - `json_column_reference`

### 2. CATEGORICAL (`ExplainabilityType.CATEGORICAL`)
- **Visualization**: Pie chart for category distribution
- **Best for**: One-to-many relationships, counterparty concentration, discrete categories
- **Required fields**:
  - `category_lbl` and `category_var`
  - `json_column_reference`

### 3. HISTORICAL (`ExplainabilityType.HISTORICAL`)
- **Visualization**: Line graph with historical trend comparison
- **Best for**: Z-score features, deviation from historical baseline
- **Required fields**:
  - `time_range_value` and `time_range_unit`
  - **`ExplainabilityValueType.POPULATION` (MANDATORY)**
- **Critical**: Population behavior data MUST be present for meaningful comparison

### 4. BINARY (`ExplainabilityType.BINARY`)
- **Visualization**: Text-only display
- **Best for**: True/false flags, yes/no indicators, binary states
- **Required fields**: Simple key-value pairs

## Validation Rules

The agent enforces these rules:

1. **Boolean features** (`DataType.BOOLEAN`) → MUST use BINARY widget
2. **Z-score features** (`z_score_*`) → MUST use HISTORICAL widget with population behavior
3. **HISTORICAL widgets** → MUST include `ExplainabilityValueType.POPULATION`
4. **Count distinct features** (`cnt_distinct_*`, `one_to_many`, etc.) → SHOULD use CATEGORICAL widget
5. **Aggregate features** (`sum_*`, `cnt_*`, `max_*`) → SHOULD use BEHAVIORAL or HISTORICAL

## Usage

### Quick Test
```bash
cd CrewAi
python3 test_widget_validation.py
```

This runs the validation tools directly without the full agent workflow.

### Full Agent Workflow
```bash
cd CrewAi
python3 widget_validation_main.py demo_fuib
```

### With Custom Output Directory
```bash
python3 widget_validation_main.py demo_fuib --output-dir custom_reports
```

## Output

The validation produces:

1. **widget_validation_report.md** - Human-readable markdown report with:
   - Executive summary
   - Quality score (0-100)
   - Critical issues (priority 1)
   - Recommended improvements (priority 2)
   - Detailed findings per feature

2. **widget_analysis_raw.json** - Machine-readable JSON with complete analysis data

### Quality Score Calculation

The quality score (0-100) is calculated as:

- **20 points**: Widget coverage (% of features with widgets defined)
- **40 points**: Optimal selection (% of features with optimal widget types)
- **40 points**: Population behavior (% of HISTORICAL widgets with population data)

### Example Output

```json
{
  "summary": {
    "total_features": 24,
    "with_widgets": 18,
    "without_widgets": 6,
    "optimal_widgets": 10,
    "suboptimal_widgets": 8,
    "missing_population_in_historical": 7
  }
}
```

**Quality Score**: 56.1/100
- Widget Coverage: 15.0/20
- Optimal Selection: 22.2/40
- Population Behavior: 18.9/40

## Common Issues Found

### Critical Issues (High Priority)

1. **HISTORICAL widgets missing population behavior**
   ```python
   # ❌ INCORRECT - Missing population
   Explainability(
       type=ExplainabilityType.HISTORICAL,
       values=[
           ExplainabilityValueProperties(
               key="zval",
               type=ExplainabilityValueType.TREND
           )
       ]
   )
   
   # ✅ CORRECT - With population
   Explainability(
       type=ExplainabilityType.HISTORICAL,
       values=[
           ExplainabilityValueProperties(
               key="zval",
               type=ExplainabilityValueType.TREND
           ),
           ExplainabilityValueProperties(
               key="st",
               type=ExplainabilityValueType.POPULATION,
               dynamic_value="pop_avg_sum_trx"
           )
       ]
   )
   ```

2. **Z-score features not using HISTORICAL widget**
   ```python
   # ❌ Feature: z_score_sum_trx using BEHAVIORAL
   # ✅ Should use HISTORICAL with population
   ```

3. **Boolean features not using BINARY widget**
   ```python
   # ❌ DataType.BOOLEAN using HISTORICAL
   # ✅ Should use BINARY for text display
   ```

### Medium Priority

4. **Categorical features using wrong widget**
   ```python
   # ⚠️  one_to_many using BEHAVIORAL
   # ✅ Should use CATEGORICAL for pie chart
   ```

5. **Missing widget definition**
   ```python
   # ⚠️  No explainabilities defined
   # ✅ Should have at least one widget type
   ```

## Integration with Other Agents

The widget validation can be integrated into the main validation workflow:

```python
# In main_unified.py or run_with_reuse.py
from agents.widget_validation_agents import create_widget_validator_agent
from tasks.widget_validation_tasks import create_widget_analysis_task

# Add to agent list
widget_agent = create_widget_validator_agent(widget_tools, llm)

# Add to task list  
widget_task = create_widget_analysis_task(widget_agent, domain)
```

## Files

- `tools/widget_validation_tools.py` - Core validation logic
- `agents/widget_validation_agents.py` - Agent definitions
- `tasks/widget_validation_tasks.py` - Task definitions
- `widget_validation_main.py` - Standalone execution script
- `test_widget_validation.py` - Unit tests for tools

## Developer Notes

### Adding New Widget Types

If new widget types are added to the platform, update:
1. Widget type detection in `analyze_single_feature()`
2. Validation rules in `validate_widget_type()`
3. Best practices in `GetWidgetBestPracticesTool`

### Custom Validation Rules

To add custom domain-specific validation rules, extend the `validate_widget_type()` function with additional checks based on feature identifier patterns or categories.

## Example Findings

From `demo_fuib` domain:

| Feature | Current Widget | Recommended | Has Population | Issue |
|---------|---------------|-------------|----------------|-------|
| `z_score_sum_hghrsk_cntry` | BEHAVIORAL | HISTORICAL | N/A | Z-score should use HISTORICAL |
| `sum_trx_cash_in` | HISTORICAL | HISTORICAL | ❌ | Missing population behavior |
| `cnt_trx_cash` | HISTORICAL | HISTORICAL | ✅ | Optimal |
| `one_to_many` | CATEGORICAL | CATEGORICAL | N/A | Optimal |
| `customer_name` | None | - | - | No widget defined |

## Quality Improvement Tips

1. **For all HISTORICAL widgets**: Add population behavior data
   - Include `ExplainabilityValueType.POPULATION`
   - Reference population fields like `pop_avg_*`, `pop_dstnct_*`

2. **For z-score features**: Switch to HISTORICAL widget type
   - These features compare to historical baselines
   - Line graphs show trend deviation best

3. **For boolean features**: Use BINARY widget
   - Simple text display is most appropriate
   - No need for time-series visualization

4. **For categorical features**: Use CATEGORICAL widget
   - Pie charts show distribution clearly
   - Better than stacked bars for snapshot view

## Contact

For questions or issues with widget validation, contact the solution quality team.
