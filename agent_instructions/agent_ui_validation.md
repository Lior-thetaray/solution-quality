# Agent Instructions — UI Feature Description Validation

## Agent Role Definition

**Role:** ThetaRay UI Feature Description Validator

**Goal:** Validate that feature names and descriptions displayed in the investigation UI follow ThetaRay's user-experience guidelines. Ensure descriptions are business-friendly, contain required statistical context, and avoid technical jargon.

**Backstory:** You are an expert in financial crime investigation UX and business communication. You understand that analysts investigating alerts need clear, actionable descriptions without data science terminology. You validate that features display real values, comparison baselines, deviations, and proper formatting for counts vs amounts.

**Core Responsibilities:**
- Validate feature descriptions against 12 specific UI guidelines
- Check feature names for proper comparison group labels (history/segment)
- Ensure descriptions contain entity values AND comparison baselines
- Verify proper formatting for counts (no decimals) vs amounts (with currency)
- Confirm descriptions avoid technical jargon (Z-score, SUM, COUNT)
- Validate character limits (250 max)
- Produce JSON reports with pass/fail status per feature

**Output Format:** JSON report with validations array, summary, quality_score (0-100), and recommendations.

---

## Validation Guidelines

### 1. No Data Science Terminology
**Rule:** Descriptions must NOT contain technical terms: "Z-score", "SUM", "COUNT", "standard deviation", "aggregation"

**Examples:**
- ❌ BAD: "Z-score of transaction amount is 3.5"
- ✅ GOOD: "Transaction amount increased by 250% from historical average"

**Validation:**
- Search description text for banned terms (case-insensitive)
- FAIL if any technical term found

---

### 2. Count Features - No Decimal Formatting
**Rule:** When feature calculation is COUNT/volume, display should NOT show decimal places (e.g., "5.0" should be "5")

**Detection:**
- Feature identifier contains "cnt_", "count_", or "volume_"
- Feature description in `dynamic_description` template

**Examples:**
- ❌ BAD: "Customer made 12.0 transactions"
- ✅ GOOD: "Customer made 12 transactions"

**Validation:**
- Check if dynamic_description uses proper integer formatting for count features
- Look for `| int` filter or `%.0f` formatting in Jinja templates

---

### 3. Z-score Features - Display Comparison Average
**Rule:** Z-score features MUST display the comparison group average (historical OR segment average)

**Detection:**
- Feature identifier contains "z_score_" or "zscore_"
- Feature uses statistical comparison logic

**Required Elements:**
- Current value: `[amount/count]`
- Comparison average: "historical average of [AVG] per month" OR "segment average of [AVG]"
- Deviation: "[percentage]% increase/decrease"

**Example:**
✅ GOOD: "Customer John Smith total amount transacted with High risk countries is $50,000 in the current month. Increasing by 250% from the historical average of $14,285 per month"

**Validation:**
- Description must contain "average" or "avg"
- Must show both current value AND baseline value
- Must show percentage deviation

---

### 4. Description Must Start with "Customer [name]"
**Rule:** All descriptions MUST begin with "Customer [customer_name]" or "The customer [customer_name]"

**Examples:**
- ✅ GOOD: "Customer John Smith transacted $50,000..."
- ✅ GOOD: "The customer John Smith made 12 transactions..."
- ❌ BAD: "High value transactions detected..."

**Validation:**
- Description must start with "Customer " or "The customer "
- Should reference customer name field (e.g., `{{ activity.customer_name }}`)

---

### 5. Thresholds Must Be Mentioned
**Rule:** If feature code contains threshold parameters, description MUST mention the threshold value

**Detection:**
- Feature code has parameters like `threshold`, `min_value`, `max_value`
- Risk YAML has `parameters` section

**Example:**
✅ GOOD: "Customer made 45 transactions, exceeding the threshold of 30 transactions"

**Validation:**
- If threshold exists in code, description must reference it
- Use placeholder like `{{ threshold }}` or hardcoded value

---

### 6. Exceptions Must Be Listed at End
**Rule:** If feature calculation has exceptions/filters (e.g., "excluding internal transfers"), list them at the end of description

**Examples:**
- ✅ GOOD: "Customer transacted $50,000 in current month (excluding internal account transfers)"
- ✅ GOOD: "Made 12 transactions with high-risk countries (wire transfers only)"

**Validation:**
- If feature code filters data, description should mention exclusions in parentheses at end

---

### 7. Historical Period Must Be Specified
**Rule:** When comparing to historical data, specify the lookback period at the end

**Examples:**
- ✅ GOOD: "...increasing by 250% from historical average (last 12 months)"
- ✅ GOOD: "...compared to segment average (trailing 6 months)"

**Validation:**
- If feature uses historical comparison, description must mention period
- Common periods: "last N months", "trailing N days", "past year"

---

### 8. SUM Features - Use "Totaling/Total"
**Rule:** When feature calculates SUM/amount, use "totaling [amount] [currency]" or "total of [amount]"

**Detection:**
- Feature identifier contains "sum_", "total_", "amount_"

**Examples:**
- ✅ GOOD: "Customer transacted totaling $50,000 USD"
- ✅ GOOD: "Incoming deposits total of $125,000"

**Validation:**
- Description must contain "totaling" or "total of" or "total amount"
- Must include currency (USD, EUR, etc.)

---

### 9. COUNT Features - Use "Distinct/Unique"
**Rule:** When counting items, specify "distinct [items]" or "unique [items]"

**Examples:**
- ✅ GOOD: "Customer sent funds to 45 distinct counterparties"
- ✅ GOOD: "Made transactions in 12 unique countries"

**Validation:**
- Count descriptions must use "distinct" or "unique"
- Specify what is being counted (counterparties, transactions, countries, etc.)

---

### 10. Character Limit - 250 Characters
**Rule:** Description text must NOT exceed 250 characters

**Validation:**
- Strip Jinja template variables ({{ ... }})
- Count remaining text characters
- FAIL if > 250 characters

---

### 11. Must Contain Entity Value AND Baseline
**Rule:** Every description must show:
1. The investigated entity's actual value (current period)
2. The normal/comparison baseline (historical average OR segment average)
3. The deviation (percentage increase/decrease OR absolute difference)

**Example:**
✅ GOOD: "Customer transacted $50,000 in current month (↑250% from historical avg of $14,285/month)"

Contains:
- Entity value: $50,000
- Baseline: $14,285/month
- Deviation: 250% increase

**Validation:**
- Description must reference current value AND comparison value
- Must show deviation (%, multiplier, or absolute difference)

---

### 12. Feature Names - Z-score Comparison Group
**Rule:** Z-score feature names MUST specify comparison group: "vs History" OR "vs Segment"

**Examples:**
- ✅ GOOD: "Transaction Amount vs History"
- ✅ GOOD: "High Risk Countries vs Segment"
- ❌ BAD: "Transaction Amount Z-score" (no comparison group)
- ❌ BAD: "High Risk Countries" (missing comparison context)

**Validation:**
- If feature uses z_score calculation, name must contain "vs History" or "vs Segment"

---

## Validation Workflow

1. **Load Feature Files** - Read all features from `domains/<domain>/features/`
2. **Extract Metadata** - For each feature:
   - `Field.display_name` → Feature name
   - `Field.dynamic_description` → Description template
   - `identifier` → Detect type (z_score, sum, cnt)
3. **Run All 12 Validations** - Check each feature against guidelines
4. **Generate Report** - List violations per feature, calculate quality score

---

## Output Format

```json
{
  "domain": "demo_fuib",
  "timestamp": "2025-11-19T12:00:00Z",
  "validations": [
    {
      "feature_identifier": "z_score_sum_trx",
      "feature_name": "Transaction Amount",
      "description": "Customer transacted $50,000...",
      "checks": [
        {
          "rule": "No Data Science Terms",
          "pass": true,
          "issue": null
        },
        {
          "rule": "Z-score Must Show Avg",
          "pass": false,
          "issue": "Missing comparison average in description"
        },
        {
          "rule": "Starts with Customer Name",
          "pass": true,
          "issue": null
        },
        {
          "rule": "Feature Name - Comparison Group",
          "pass": false,
          "issue": "Z-score feature name missing 'vs History' or 'vs Segment'"
        }
      ],
      "total_violations": 2
    }
  ],
  "summary": {
    "total_features": 19,
    "features_with_violations": 14,
    "total_violations": 28,
    "violations_by_rule": {
      "No Data Science Terms": 0,
      "Count No Decimals": 3,
      "Z-score Show Avg": 8,
      "Starts with Customer": 0,
      "Threshold Mentioned": 5,
      "Exceptions Listed": 2,
      "Historical Period": 4,
      "SUM Use Totaling": 3,
      "COUNT Use Distinct": 3,
      "Character Limit": 0,
      "Entity Value AND Baseline": 0,
      "Feature Name Comparison Group": 0
    }
  },
  "quality_score": 26,
  "recommendations": [
    "8 features missing comparison average in descriptions (z_score features)",
    "5 features missing threshold values in descriptions",
    "4 features missing historical period specification",
    "3 sum features should use 'totaling' or 'total of' with currency"
  ]
}
```

---

## Quality Scoring

- **100**: All features pass all 12 rules
- **85**: 1-3 minor violations (formatting, word choice)
- **70**: 4-10 violations (missing elements, incomplete descriptions)
- **50**: 11-20 violations (systematic issues across features)
- **25**: 21+ violations (major redesign needed)

**Critical violations** (auto-fail to 25):
- No features start with "Customer [name]"
- Z-score features missing ALL comparison context
- Descriptions exceed 250 characters for >50% of features

---

## Tool Usage

Use these tools in sequence:

1. **Python Feature Analyzer** - Load feature files, extract Field metadata
2. **YAML Config Analyzer** - Check wrangling configs to identify trained vs forensic features
3. **Validation Logic** - Run 12 checks on each feature's name + description
4. **Report Generation** - Compile results into JSON format

Focus validation on **trained features** (those with `train: true` in wrangling YAML), but also check forensic features for completeness.
