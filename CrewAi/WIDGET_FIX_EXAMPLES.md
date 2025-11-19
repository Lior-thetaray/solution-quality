# Widget Validation - Example Fixes

This document shows how to fix common widget validation issues found by the agent.

## Issue 1: HISTORICAL Widget Missing Population Behavior (CRITICAL)

### ❌ Before (Incorrect)
```python
@property
def output_fields(self) -> Set[Field]:
    return {
        Field(
            identifier='sum_trx_cash_in',
            display_name='Total Cash Deposit Activity',
            data_type=DataType.DOUBLE,
            explainabilities=[
                Explainability(
                    identifier="hist_expl",
                    type=ExplainabilityType.HISTORICAL,
                    time_range_value=12,
                    time_range_unit=TimeRangeUnit.MONTH,
                    values=[
                        ExplainabilityValueProperties(
                            key="zval",
                            name="Total Cash Amount",
                            dynamic_value="sum_trx_cash_in",
                            type=ExplainabilityValueType.TREND
                        )
                        # ❌ MISSING: Population behavior!
                    ]
                )
            ]
        )
    }
```

### ✅ After (Fixed)
```python
@property
def output_fields(self) -> Set[Field]:
    return {
        Field(
            identifier='sum_trx_cash_in',
            display_name='Total Cash Deposit Activity',
            data_type=DataType.DOUBLE,
            explainabilities=[
                Explainability(
                    identifier="hist_expl",
                    type=ExplainabilityType.HISTORICAL,
                    time_range_value=12,
                    time_range_unit=TimeRangeUnit.MONTH,
                    values=[
                        ExplainabilityValueProperties(
                            key="zval",
                            name="Total Cash Amount",
                            dynamic_value="sum_trx_cash_in",
                            type=ExplainabilityValueType.TREND
                        ),
                        # ✅ ADDED: Population behavior for comparison
                        ExplainabilityValueProperties(
                            key='st',
                            name="Population Average",
                            dynamic_value="pop_avg_sum_trx_cash",
                            type=ExplainabilityValueType.POPULATION
                        )
                    ]
                )
            ]
        )
    }
```

**What changed**:
- Added `ExplainabilityValueType.POPULATION` entry
- References `pop_avg_sum_trx_cash` field from wrangled dataset
- Now shows customer value vs. population average in UI

---

## Issue 2: Z-Score Feature Using Wrong Widget Type

### ❌ Before (Incorrect)
```python
class SumHghrskCntry(AggFeature, FeatureDescriptor):
    @property
    def identifier(self) -> str:
        return 'z_score_sum_hghrsk_cntry'  # ← Note: z_score feature!
    
    @property
    def output_fields(self) -> Set[Field]:
        return {
            Field(
                identifier="z_score_sum_hghrsk_cntry",
                explainabilities=[
                    Explainability(
                        type=ExplainabilityType.BEHAVIORAL,  # ❌ Wrong for z-score!
                        time_range_value=12,
                        time_range_unit=TimeRangeUnit.MONTH,
                        category_lbl="ct",
                        category_var="s",
                        json_column_reference="high_risk_country_explainability"
                    )
                ]
            )
        }
```

### ✅ After (Fixed)
```python
class SumHghrskCntry(AggFeature, FeatureDescriptor):
    @property
    def identifier(self) -> str:
        return 'z_score_sum_hghrsk_cntry'
    
    @property
    def output_fields(self) -> Set[Field]:
        return {
            Field(
                identifier="z_score_sum_hghrsk_cntry",
                explainabilities=[
                    Explainability(
                        type=ExplainabilityType.HISTORICAL,  # ✅ Correct for z-score
                        time_range_value=12,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="zval",
                                name="High Risk Country Value",
                                dynamic_value="sum_hghrsk_cntry",
                                type=ExplainabilityValueType.TREND
                            ),
                            ExplainabilityValueProperties(
                                key='st',
                                name="Historical Average",
                                dynamic_value="pop_avg_sum_hghrsk_cntry",
                                type=ExplainabilityValueType.POPULATION  # ✅ Required!
                            )
                        ]
                    )
                ]
            )
        }
```

**What changed**:
- Changed from `BEHAVIORAL` to `HISTORICAL`
- Added population baseline for comparison
- Z-scores show deviation - line graph with baseline is appropriate

---

## Issue 3: Boolean Feature Using Wrong Widget

### ❌ Before (Incorrect)
```python
Field(
    identifier='has_card',
    display_name='Has Card',
    data_type=DataType.BOOLEAN,  # ← Boolean type
    explainabilities=[
        Explainability(
            type=ExplainabilityType.HISTORICAL,  # ❌ Overkill for boolean!
            time_range_value=12,
            time_range_unit=TimeRangeUnit.MONTH,
            values=[...]
        )
    ]
)
```

### ✅ After (Fixed)
```python
Field(
    identifier='has_card',
    display_name='Has Card',
    data_type=DataType.BOOLEAN,
    explainabilities=[
        Explainability(
            type=ExplainabilityType.BINARY,  # ✅ Simple text display
            values=[
                ExplainabilityValueProperties(
                    key="hc",
                    name="Customer has card",
                    dynamic_value="has_card",
                ),
            ]
        )
    ]
)
```

**What changed**:
- Changed from `HISTORICAL` to `BINARY`
- Removed unnecessary time_range fields
- Boolean values don't need trend analysis

---

## Issue 4: Categorical Feature Using Wrong Widget

### ❌ Before (Incorrect)
```python
Field(
    identifier='one_to_many',
    display_name='One to Many',
    description="Distinct counterparties customer sends funds to",
    explainabilities=[
        Explainability(
            type=ExplainabilityType.BEHAVIORAL,  # ❌ Not ideal for distribution
            time_range_value=12,
            time_range_unit=TimeRangeUnit.MONTH,
            category_lbl="cn",
            category_var="c",
            json_column_reference="one_to_many_explainability"
        )
    ]
)
```

### ✅ After (Fixed)
```python
Field(
    identifier='one_to_many',
    display_name='One to Many',
    description="Distinct counterparties customer sends funds to",
    explainabilities=[
        Explainability(
            type=ExplainabilityType.CATEGORICAL,  # ✅ Pie chart for distribution
            category_lbl="cn",
            category_var="c",
            json_column_reference="one_to_many_explainability",
            values=[
                ExplainabilityValueProperties(
                    key="cn",
                    name="Counterparty Name",
                ),
                ExplainabilityValueProperties(
                    key="s",
                    name="Sum of Transactions",
                    type=ExplainabilityValueType.SUM,
                ),
                ExplainabilityValueProperties(
                    key="c",
                    name="Transaction Count",
                    type=ExplainabilityValueType.COUNT,
                )
            ]
        )
    ]
)
```

**What changed**:
- Changed from `BEHAVIORAL` to `CATEGORICAL`
- Removed `time_range` (not needed for snapshot)
- Added proper value properties for pie chart

---

## Issue 5: Missing Widget Definition

### ❌ Before (Incorrect)
```python
class CustomerName(AggFeature, FeatureDescriptor):
    @property
    def output_fields(self) -> Set[Field]:
        return {
            Field(
                identifier='customer_name',
                display_name='Customer Name',
                data_type=DataType.STRING,
                category="KYC"
                # ❌ No explainabilities defined!
            )
        }
```

### ✅ After (Fixed - Option 1: Simple Binary)
```python
class CustomerName(AggFeature, FeatureDescriptor):
    @property
    def output_fields(self) -> Set[Field]:
        return {
            Field(
                identifier='customer_name',
                display_name='Customer Name',
                data_type=DataType.STRING,
                category="KYC",
                # ✅ Added simple text display
                explainabilities=[
                    Explainability(
                        type=ExplainabilityType.BINARY,
                        values=[
                            ExplainabilityValueProperties(
                                key="cn",
                                name="Customer Name",
                                dynamic_value="customer_name",
                            )
                        ]
                    )
                ]
            )
        }
```

### ✅ After (Fixed - Option 2: If used forensically only)
```python
# If this is purely a forensic field (not displayed as widget),
# you can leave without explainability but add a comment:

class CustomerName(AggFeature, FeatureDescriptor):
    @property
    def output_fields(self) -> Set[Field]:
        return {
            Field(
                identifier='customer_name',
                display_name='Customer Name',
                data_type=DataType.STRING,
                category="KYC"
                # Forensic field only - no widget display needed
            )
        }
```

---

## Dataset Changes Required

When adding population behavior, ensure the wrangled dataset includes the population fields:

```python
# In datasets/customer_monthly.py

def customer_monthly_dataset():
    return DataSet(
        identifier='customer_monthly',
        field_list=[
            # ... existing fields ...
            
            # ✅ Add population fields for HISTORICAL widgets
            Field(
                identifier="pop_avg_sum_trx_cash", 
                display_name="Population Avg Cash Transactions",
                data_type=DataType.DOUBLE
            ),
            Field(
                identifier="pop_avg_sum_hghrsk_cntry",
                display_name="Population Avg High Risk Country",
                data_type=DataType.DOUBLE
            ),
            # ... more population fields as needed ...
        ]
    )
```

And ensure population enrichment in wrangling notebook:

```python
# In notebooks/wrangling.ipynb

# Calculate population statistics
df_with_pop = df.withColumn(
    "pop_avg_sum_trx_cash",
    f.avg("sum_trx_cash_in").over(Window.partitionBy("month_offset"))
)
```

---

## Quick Reference

| Issue | Current | Recommended | Fix |
|-------|---------|-------------|-----|
| HISTORICAL without population | HISTORICAL | HISTORICAL + POPULATION | Add ExplainabilityValueType.POPULATION |
| Z-score with BEHAVIORAL | BEHAVIORAL | HISTORICAL | Change type, add population |
| Boolean with HISTORICAL | HISTORICAL | BINARY | Change to BINARY, remove time_range |
| Categorical with BEHAVIORAL | BEHAVIORAL | CATEGORICAL | Change to CATEGORICAL |
| No widget | None | BINARY/CATEGORICAL/etc | Add appropriate explainability |

---

## Validation Checklist

After fixing, verify:

- [ ] All HISTORICAL widgets have `ExplainabilityValueType.POPULATION`
- [ ] All z-score features use HISTORICAL widget type
- [ ] All boolean features use BINARY widget type
- [ ] Categorical features use CATEGORICAL widget type
- [ ] Population fields exist in wrangled dataset
- [ ] Population fields are calculated in wrangling notebook
- [ ] Dynamic descriptions reference population fields correctly

Run validation again:
```bash
python3 widget_validation_main.py demo_fuib
```

Target score: 80+/100 (with all HISTORICAL widgets having population behavior)
