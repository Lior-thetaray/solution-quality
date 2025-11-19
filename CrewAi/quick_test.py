#!/usr/bin/env python3
"""
Quick test script to run only alert validation + manager using existing SDLC report
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
DOMAIN = "demo_fuib"
SOURCE_RUN = "run_20251119_104618_demo_fuib"  # Latest run with successful SDLC

# Paths
reports_dir = Path("reports")
source_run_dir = reports_dir / SOURCE_RUN
new_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
new_run_dir = reports_dir / f"run_{new_timestamp}_{DOMAIN}"

print("=" * 80)
print("QUICK TEST: Alert Validation + Manager (Reusing SDLC Report)")
print("=" * 80)

# Create new run directory
new_run_dir.mkdir(parents=True, exist_ok=True)
print(f"\n📁 Created new run directory: {new_run_dir}")

# Copy SDLC report from previous run
sdlc_json = source_run_dir / f"sdlc_report_{DOMAIN}.json"
sdlc_txt = source_run_dir / f"sdlc_report_{DOMAIN}.txt"

if sdlc_json.exists():
    shutil.copy2(sdlc_json, new_run_dir)
    print(f"✓ Copied SDLC report: {sdlc_json.name}")
elif sdlc_txt.exists():
    shutil.copy2(sdlc_txt, new_run_dir)
    print(f"✓ Copied SDLC report: {sdlc_txt.name}")
else:
    print(f"❌ No SDLC report found in {SOURCE_RUN}")
    exit(1)

print(f"\n📂 Run directory ready: {new_run_dir}")
print("\nNow run:")
print(f"  cd /Users/lior.yariv/solution-quality/CrewAi")
print(f"  echo -e 'alert_validation\\n{DOMAIN}\\ny' | python3 main_unified.py")
print()
print("Then manually run manager mode and it will pick up both reports!")
print(f"  echo -e 'manager\\n{DOMAIN}\\ny' | python3 main_unified.py")
print("\nOr just use the reuse feature:")
print(f"  echo -e 'manager\\n{DOMAIN}\\ny' | python3 main_unified.py")
print("  (When prompted about reusing reports, answer 'y')")
