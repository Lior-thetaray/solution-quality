"""
Test Risk Assessment Validation
Quick test of the risk assessment alignment validation
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.risk_assessment_tools import (
    ExcelReaderTool,
    RiskAssessmentAlignmentReportTool
)


def test_excel_reader():
    """Test reading the risk assessment Excel"""
    print("\n" + "=" * 80)
    print("TEST: Excel Reader Tool")
    print("=" * 80)
    
    tool = ExcelReaderTool()
    result = tool._run(
        excel_path="Sonar/domains/demo_fuib/risk_assessment.xlsx"
    )
    
    print(result)
    print("\n✅ Excel reader test complete\n")


def test_alignment_report():
    """Test generating alignment report"""
    print("\n" + "=" * 80)
    print("TEST: Risk Assessment Alignment Report")
    print("=" * 80)
    
    tool = RiskAssessmentAlignmentReportTool()
    result = tool._run(
        domain="demo_fuib",
        excel_path="Sonar/domains/demo_fuib/risk_assessment.xlsx"
    )
    
    print(result)
    print("\n✅ Alignment report test complete\n")


if __name__ == "__main__":
    print("\n🧪 Testing Risk Assessment Tools\n")
    
    test_excel_reader()
    test_alignment_report()
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 80)
    print("\nTo run full validation with agents:")
    print("  python3 risk_assessment_main.py demo_fuib")
    print("=" * 80 + "\n")
