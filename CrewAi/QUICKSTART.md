# Quick Start Guide - CrewAI SDLC Validation

## 🚀 Quick Setup (5 minutes)

### 1. Install Dependencies
```bash
cd CrewAi
pip install -r requirements.txt
```

### 2. Configure API Key
```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### 3. Test the Tools
```bash
# Verify tools are working
python test_tools.py
```

### 4. Run SDLC Validation
```bash
# Run the validation
python main.py

# When prompted, enter domain name (e.g., demo_fuib)
```

## 📊 Example Output

The validation will:
1. ✅ Analyze all features in the domain
2. ✅ Check YAML configurations
3. ✅ Validate trace query coverage
4. ✅ Check unit test presence
5. ✅ Verify DAG structure
6. ✅ Validate datasets
7. ✅ Check evaluation flows
8. ✅ Validate risk definitions
9. ✅ Verify drift monitoring
10. ✅ Generate comprehensive JSON report with quality score

## 📁 Report Location

Reports are saved to `CrewAi/reports/` with timestamp:
```
reports/sdlc_report_demo_fuib_20251118_143022.json
```

## 🔍 Understanding the Report

The JSON report includes:

```json
{
  "domain": "demo_fuib",
  "timestamp": "2025-11-18T14:30:22",
  "validations": [
    {
      "name": "Trace Query Coverage",
      "pass": true,
      "issues": []
    },
    ...
  ],
  "summary": {
    "total_checks": 9,
    "passed": 7,
    "failed": 2
  },
  "quality_score": 78,
  "recommendations": [
    "Add unit tests for features: sum_trx_cash, cnt_trx_n_day",
    "Create drift monitoring notebook"
  ]
}
```

## 🎯 Quality Score Interpretation

- **90-100**: ✅ Excellent - Production ready
- **75-89**: ✅ Good - Minor improvements needed  
- **60-74**: ⚠️ Acceptable - Several issues to address
- **< 60**: ❌ Needs work - Major issues found

## 🛠️ Troubleshooting

### "OPENAI_API_KEY not found"
Edit `.env` file and add your OpenAI API key

### "Domain 'xyz' not found"
Check domain exists in `Sonar/domains/xyz/`
Run without arguments to see available domains

### Tool errors
Run `python test_tools.py` to diagnose which tool is failing

## 🔧 Advanced Usage

### Validate Specific Domain
```python
# Edit main.py or pass domain as argument
python main.py --domain demo_fuib
```

### Custom Validation Rules
Edit `agent_instructions/agent_sdlc.md` to modify validation criteria and agent behavior

### Add New Checks
1. Add task definition to Section 6 in `agent_instructions/agent_sdlc.md`
2. Create new task function in `tasks/sdlc_tasks.py`
3. Add task to crew in `main.py`

## 📚 Next Steps

1. Review generated report in `reports/`
2. Address failing validations
3. Re-run validation to verify improvements
4. Integrate into CI/CD pipeline for automated checks
