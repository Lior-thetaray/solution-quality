#!/usr/bin/env python3
"""
Simple script to run alert validation + manager using existing SDLC report.
Just copies the latest SDLC report to a new run and executes alert + manager.
"""

import shutil
from pathlib import Path
from datetime import datetime

# Config
DOMAIN = "demo_fuib"

def main():
    print("=" * 80)
    print("ALERT + MANAGER TEST (Reusing Latest SDLC)")
    print("=" * 80)
    
    # Find latest run with SDLC report
    reports_dir = Path("reports")
    runs = sorted(
        [d for d in reports_dir.iterdir() 
         if d.is_dir() and DOMAIN in d.name and d.name.startswith("run_")],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    source_run = None
    for run in runs:
        sdlc_json = run / f"sdlc_report_{DOMAIN}.json"
        sdlc_txt = run / f"sdlc_report_{DOMAIN}.txt"
        if sdlc_json.exists() or sdlc_txt.exists():
            source_run = run
            break
    
    if not source_run:
        print(f"\n❌ No existing SDLC report found for {DOMAIN}")
        return 1
    
    print(f"\n📁 Found SDLC report in: {source_run.name}")
    
    # Create new run directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_run = reports_dir / f"run_{timestamp}_{DOMAIN}"
    new_run.mkdir(parents=True, exist_ok=True)
    
    # Copy SDLC report
    for ext in ['.json', '.txt']:
        sdlc_file = source_run / f"sdlc_report_{DOMAIN}{ext}"
        if sdlc_file.exists():
            shutil.copy2(sdlc_file, new_run)
            print(f"✓ Copied: {sdlc_file.name}")
            break
    
    print(f"\n📂 New run directory: {new_run}")
    print("\n" + "=" * 80)
    print("Now run main_unified.py in manager mode.")
    print("It will detect the existing SDLC report and ask to reuse it.")
    print("=" * 80)
    print(f"\nCommands:")
    print(f"  cd {new_run.parent.parent / 'CrewAi'}")
    print(f"  python3 main_unified.py")
    print(f"  Choose: 4 (manager)")
    print(f"  Domain: {DOMAIN}")
    print(f"  Reuse? y")
    print()
    
    return 0


if __name__ == "__main__":
    exit(main())
