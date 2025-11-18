"""
Alert Quality Validator
Extracts alert consolidation, duplicate detection, and monthly distribution metrics
from tr_alert_table, activity_risk_table, and evaluated_activities CSV files.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class AlertValidator:
    """Validates alert quality from CSV datasets"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.alerts_df = None
        self.risks_df = None
        self.activities_df = None
        
    def load_data(self) -> bool:
        """Load all three CSV files"""
        try:
            alerts_path = self.data_dir / "tr_alert_table.csv"
            risks_path = self.data_dir / "activity_risk_table.csv"
            activities_path = self.data_dir / "evaluated_activities.csv"
            
            if not alerts_path.exists():
                print(f"❌ Missing: {alerts_path}")
                return False
            if not risks_path.exists():
                print(f"❌ Missing: {risks_path}")
                return False
            if not activities_path.exists():
                print(f"❌ Missing: {activities_path}")
                return False
                
            self.alerts_df = pd.read_csv(alerts_path)
            self.risks_df = pd.read_csv(risks_path)
            self.activities_df = pd.read_csv(activities_path)
            
            print(f"✅ Loaded {len(self.alerts_df)} alerts")
            print(f"   Columns: {list(self.alerts_df.columns)}")
            print(f"✅ Loaded {len(self.risks_df)} risk records")
            print(f"   Columns: {list(self.risks_df.columns)}")
            print(f"✅ Loaded {len(self.activities_df)} activities")
            print(f"   Columns: {list(self.activities_df.columns)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def parse_triggers(self, triggers_json: str) -> List[str]:
        """Parse triggers JSON field to extract triggerID list"""
        try:
            if pd.isna(triggers_json):
                return []
            
            # Handle if already a list
            if isinstance(triggers_json, list):
                return triggers_json
                
            # Parse JSON string
            triggers = json.loads(triggers_json)
            
            # Extract triggerID from list of dicts or direct list
            if isinstance(triggers, list):
                if len(triggers) > 0 and isinstance(triggers[0], dict):
                    return [t.get('triggerID') or t.get('tr_id') for t in triggers if t.get('triggerID') or t.get('tr_id')]
                else:
                    return triggers
            
            return []
            
        except json.JSONDecodeError:
            # Try eval as fallback for Python-style lists
            try:
                triggers = eval(triggers_json)
                if isinstance(triggers, list):
                    return triggers
            except:
                pass
            return []
        except Exception as e:
            print(f"⚠️ Error parsing triggers: {e}")
            return []
    
    def validate_alert_counts(self) -> Dict[str, Any]:
        """
        Validation A: Alert Count Analysis
        Calculates total alerts, consolidated vs non-consolidated
        """
        print("\n📊 Validation A: Alert Count Analysis")
        
        # Parse triggers for each alert
        self.alerts_df['trigger_list'] = self.alerts_df['triggers'].apply(self.parse_triggers)
        self.alerts_df['trigger_count'] = self.alerts_df['trigger_list'].apply(len)
        
        total_alerts = len(self.alerts_df)
        consolidated_alerts = len(self.alerts_df[self.alerts_df['trigger_count'] > 1])
        non_consolidated_alerts = len(self.alerts_df[self.alerts_df['trigger_count'] == 1])
        consolidation_rate = (consolidated_alerts / total_alerts * 100) if total_alerts > 0 else 0
        
        # Statistics
        avg_triggers_per_alert = self.alerts_df['trigger_count'].mean()
        max_triggers = self.alerts_df['trigger_count'].max()
        min_triggers = self.alerts_df['trigger_count'].min()
        
        result = {
            "total_alerts": int(total_alerts),
            "consolidated_alerts": int(consolidated_alerts),
            "non_consolidated_alerts": int(non_consolidated_alerts),
            "consolidation_rate_percent": round(consolidation_rate, 2),
            "statistics": {
                "avg_triggers_per_alert": round(avg_triggers_per_alert, 2),
                "max_triggers_in_alert": int(max_triggers),
                "min_triggers_in_alert": int(min_triggers)
            }
        }
        
        print(f"  Total Alerts: {total_alerts}")
        print(f"  Consolidated (>1 trigger): {consolidated_alerts} ({consolidation_rate:.1f}%)")
        print(f"  Non-Consolidated (1 trigger): {non_consolidated_alerts}")
        
        return result
    
    def detect_duplicates(self) -> Dict[str, Any]:
        """
        Validation B: Duplicate Detection
        Finds triggerIDs appearing in multiple alert IDs (suppression failures)
        """
        print("\n🔍 Validation B: Duplicate Detection")
        
        # Flatten all triggers with their alert IDs
        trigger_alert_map = []
        for _, row in self.alerts_df.iterrows():
            alert_id = row.get('alert_id') or row.get('id')
            triggers = row['trigger_list']
            for trigger_id in triggers:
                trigger_alert_map.append({
                    'trigger_id': trigger_id,
                    'alert_id': alert_id
                })
        
        # Handle case when no triggers found
        if not trigger_alert_map:
            print("  ⚠️ No triggers found in alerts table")
            return {
                "total_triggers_checked": 0,
                "duplicate_triggers_found": 0,
                "duplicate_rate_percent": 0.0,
                "duplicate_details": [],
                "warning": "No triggers parsed from alerts"
            }
        
        trigger_df = pd.DataFrame(trigger_alert_map)
        
        # Find duplicates: triggerIDs in multiple alerts
        trigger_counts = trigger_df.groupby('trigger_id')['alert_id'].agg(['count', list]).reset_index()
        trigger_counts.columns = ['trigger_id', 'alert_count', 'alert_ids']
        
        duplicates = trigger_counts[trigger_counts['alert_count'] > 1]
        
        total_duplicates = len(duplicates)
        total_triggers = len(trigger_counts)
        duplicate_rate = (total_duplicates / total_triggers * 100) if total_triggers > 0 else 0
        
        # Format duplicate details
        duplicate_details = []
        for _, dup in duplicates.iterrows():
            duplicate_details.append({
                "trigger_id": str(dup['trigger_id']),
                "appears_in_alerts": dup['alert_ids'],
                "occurrence_count": int(dup['alert_count'])
            })
        
        result = {
            "total_triggers_checked": int(total_triggers),
            "duplicate_triggers_found": int(total_duplicates),
            "duplicate_rate_percent": round(duplicate_rate, 2),
            "duplicate_details": duplicate_details[:50]  # Limit to 50 for readability
        }
        
        print(f"  Total Unique Triggers: {total_triggers}")
        print(f"  Duplicate Triggers: {total_duplicates} ({duplicate_rate:.1f}%)")
        if total_duplicates > 0:
            print(f"  ⚠️ Suppression failures detected!")
        
        return result
    
    def calculate_monthly_distribution(self) -> Dict[str, Any]:
        """
        Validation C: Monthly Distribution
        Calculates alert distribution by month with percentages
        """
        print("\n📅 Validation C: Monthly Distribution")
        
        # Identify date column
        date_col = None
        for col in ['createdate', 'alert_date', 'created_at', 'date', 'timestamp']:
            if col in self.alerts_df.columns:
                date_col = col
                break
        
        if not date_col:
            print("  ⚠️ No date column found in alerts table")
            return {
                "error": "No date column found",
                "monthly_breakdown": []
            }
        
        # Parse dates and extract year-month
        self.alerts_df['date_parsed'] = pd.to_datetime(self.alerts_df[date_col], errors='coerce')
        self.alerts_df['year_month'] = self.alerts_df['date_parsed'].dt.to_period('M')
        
        # Count by month
        monthly_counts = self.alerts_df.groupby('year_month').size().reset_index(name='alert_count')
        monthly_counts = monthly_counts.sort_values('year_month')
        
        total_alerts = len(self.alerts_df)
        
        # Calculate percentages
        monthly_breakdown = []
        for _, row in monthly_counts.iterrows():
            month_str = str(row['year_month'])
            count = int(row['alert_count'])
            percentage = (count / total_alerts * 100) if total_alerts > 0 else 0
            
            monthly_breakdown.append({
                "month": month_str,
                "alert_count": count,
                "percentage": round(percentage, 2)
            })
        
        result = {
            "total_alerts": int(total_alerts),
            "months_covered": len(monthly_breakdown),
            "monthly_breakdown": monthly_breakdown
        }
        
        print(f"  Total Alerts: {total_alerts}")
        print(f"  Months Covered: {len(monthly_breakdown)}")
        for item in monthly_breakdown[:6]:  # Show first 6 months
            print(f"    {item['month']}: {item['alert_count']} alerts ({item['percentage']:.1f}%)")
        
        return result
    
    def check_data_quality(self) -> Dict[str, Any]:
        """
        Cross-table consistency checks
        Ensures all triggerIDs exist in all 3 tables
        """
        print("\n🔬 Data Quality Checks")
        
        # Extract all trigger IDs from alerts
        all_triggers_from_alerts = set()
        for triggers in self.alerts_df['trigger_list']:
            all_triggers_from_alerts.update(triggers)
        
        # Get trigger IDs from other tables
        risk_trigger_col = 'tr_id' if 'tr_id' in self.risks_df.columns else 'trigger_id'
        activity_trigger_col = 'tr_id' if 'tr_id' in self.activities_df.columns else 'trigger_id'
        
        triggers_in_risks = set(self.risks_df[risk_trigger_col].unique())
        triggers_in_activities = set(self.activities_df[activity_trigger_col].unique())
        
        # Find orphans
        orphan_in_risks = all_triggers_from_alerts - triggers_in_risks
        orphan_in_activities = all_triggers_from_alerts - triggers_in_activities
        extra_in_risks = triggers_in_risks - all_triggers_from_alerts
        extra_in_activities = triggers_in_activities - all_triggers_from_alerts
        
        checks = {
            "triggers_in_alerts": len(all_triggers_from_alerts),
            "triggers_in_risks": len(triggers_in_risks),
            "triggers_in_activities": len(triggers_in_activities),
            "orphan_alerts_missing_risks": len(orphan_in_risks),
            "orphan_alerts_missing_activities": len(orphan_in_activities),
            "extra_risks_not_in_alerts": len(extra_in_risks),
            "extra_activities_not_in_alerts": len(extra_in_activities),
            "consistency_status": "PASS" if len(orphan_in_risks) == 0 and len(orphan_in_activities) == 0 else "FAIL"
        }
        
        print(f"  Triggers in Alerts: {checks['triggers_in_alerts']}")
        print(f"  Triggers in Risks: {checks['triggers_in_risks']}")
        print(f"  Triggers in Activities: {checks['triggers_in_activities']}")
        
        if checks['orphan_alerts_missing_risks'] > 0:
            print(f"  ⚠️ {checks['orphan_alerts_missing_risks']} triggers in alerts missing from risks table")
        if checks['orphan_alerts_missing_activities'] > 0:
            print(f"  ⚠️ {checks['orphan_alerts_missing_activities']} triggers in alerts missing from activities table")
        
        if checks['consistency_status'] == "PASS":
            print(f"  ✅ Data consistency: PASS")
        else:
            print(f"  ❌ Data consistency: FAIL")
        
        return checks
    
    def validate_alert_metadata(self) -> Dict[str, Any]:
        """
        Validation D: Alert Metadata Quality
        Checks severity, status, assignment, and other metadata fields
        """
        print("\n📋 Validation D: Alert Metadata Quality")
        
        results = {}
        
        # Severity distribution
        if 'severity' in self.alerts_df.columns:
            severity_dist = self.alerts_df['severity'].value_counts().to_dict()
            results['severity_distribution'] = {str(k): int(v) for k, v in severity_dist.items()}
            print(f"  Severity Distribution: {dict(list(severity_dist.items())[:5])}")
        
        # Alert status/state
        if 'stateid' in self.alerts_df.columns:
            state_dist = self.alerts_df['stateid'].value_counts().to_dict()
            results['state_distribution'] = {str(k): int(v) for k, v in state_dist.items()}
            closed = len(self.alerts_df[self.alerts_df.get('isclosed', False) == True])
            open_alerts = len(self.alerts_df) - closed
            results['closed_alerts'] = closed
            results['open_alerts'] = open_alerts
            print(f"  Open: {open_alerts}, Closed: {closed}")
        
        # Assignment
        if 'assignee' in self.alerts_df.columns:
            assigned = self.alerts_df['assignee'].notna().sum()
            unassigned = self.alerts_df['assignee'].isna().sum()
            results['assigned_alerts'] = int(assigned)
            results['unassigned_alerts'] = int(unassigned)
            results['assignment_rate_percent'] = round((assigned / len(self.alerts_df) * 100), 2)
            print(f"  Assigned: {assigned}, Unassigned: {unassigned} ({results['assignment_rate_percent']:.1f}% assigned)")
        
        # Suppression count
        if 'suppressioncount' in self.alerts_df.columns:
            suppressed = len(self.alerts_df[self.alerts_df['suppressioncount'] > 0])
            avg_suppression = self.alerts_df['suppressioncount'].mean()
            results['alerts_with_suppression'] = int(suppressed)
            results['avg_suppression_count'] = round(avg_suppression, 2)
            print(f"  Alerts with Suppression: {suppressed}, Avg Count: {avg_suppression:.2f}")
        
        # Consolidation metadata check
        if 'isconsolidated' in self.alerts_df.columns:
            consolidated_flag = len(self.alerts_df[self.alerts_df['isconsolidated'] == True])
            results['consolidated_by_flag'] = int(consolidated_flag)
            
            # Compare with trigger count
            if 'trigger_count' in self.alerts_df.columns:
                consolidated_by_triggers = len(self.alerts_df[self.alerts_df['trigger_count'] > 1])
                mismatch = abs(consolidated_flag - consolidated_by_triggers)
                results['consolidation_flag_vs_triggers_mismatch'] = int(mismatch)
                if mismatch > 0:
                    print(f"  ⚠️ Consolidation mismatch: {mismatch} alerts (flag={consolidated_flag}, triggers={consolidated_by_triggers})")
        
        return results
    
    def validate_risk_quality(self) -> Dict[str, Any]:
        """
        Validation E: Risk Metadata Quality
        Analyzes risk severity, categories, and coverage
        """
        print("\n⚡ Validation E: Risk Metadata Quality")
        
        results = {}
        
        # Risk severity distribution
        if 'risk_severity' in self.risks_df.columns:
            severity_dist = self.risks_df['risk_severity'].value_counts().to_dict()
            results['risk_severity_distribution'] = {str(k): int(v) for k, v in severity_dist.items()}
            print(f"  Risk Severity: {dict(list(severity_dist.items())[:5])}")
        
        # Risk category distribution
        if 'risk_category' in self.risks_df.columns:
            category_dist = self.risks_df['risk_category'].value_counts().to_dict()
            results['risk_category_distribution'] = {str(k): int(v) for k, v in category_dist.items()}
            print(f"  Risk Categories: {len(category_dist)} unique")
        
        # Analysis method
        if 'risk_analysis_method' in self.risks_df.columns:
            method_dist = self.risks_df['risk_analysis_method'].value_counts().to_dict()
            results['analysis_method_distribution'] = {str(k): int(v) for k, v in method_dist.items()}
        
        # Suppression configuration
        if 'suppression_identifier' in self.risks_df.columns:
            with_suppression = self.risks_df['suppression_identifier'].notna().sum()
            results['risks_with_suppression_config'] = int(with_suppression)
            results['suppression_coverage_percent'] = round((with_suppression / len(self.risks_df) * 100), 2)
            print(f"  Suppression Configured: {with_suppression}/{len(self.risks_df)} ({results['suppression_coverage_percent']:.1f}%)")
        
        return results
    
    def validate_activity_scores(self) -> Dict[str, Any]:
        """
        Validation F: Activity Score Distribution
        Analyzes algo_score distribution and patterns
        """
        print("\n🎯 Validation F: Activity Score Distribution")
        
        results = {}
        
        if 'algo_score' not in self.activities_df.columns:
            print("  ⚠️ No algo_score column found")
            return {"error": "No algo_score column"}
        
        scores = self.activities_df['algo_score'].dropna()
        
        results['total_activities'] = len(self.activities_df)
        results['activities_with_scores'] = int(len(scores))
        results['score_statistics'] = {
            'min': float(scores.min()),
            'max': float(scores.max()),
            'mean': round(float(scores.mean()), 4),
            'median': round(float(scores.median()), 4),
            'std': round(float(scores.std()), 4)
        }
        
        # Score percentiles
        percentiles = [50, 75, 90, 95, 99]
        score_percentiles = {}
        for p in percentiles:
            score_percentiles[f'p{p}'] = round(float(scores.quantile(p/100)), 4)
        results['score_percentiles'] = score_percentiles
        
        print(f"  Activities: {results['total_activities']}, With Scores: {results['activities_with_scores']}")
        print(f"  Score Range: [{results['score_statistics']['min']:.4f}, {results['score_statistics']['max']:.4f}]")
        print(f"  Mean: {results['score_statistics']['mean']:.4f}, Median: {results['score_statistics']['median']:.4f}")
        print(f"  Percentiles: P90={score_percentiles['p90']:.4f}, P95={score_percentiles['p95']:.4f}, P99={score_percentiles['p99']:.4f}")
        
        # High score activities (potential alerts)
        if len(scores) > 0:
            high_score_threshold = scores.quantile(0.95)
            high_score_count = len(scores[scores >= high_score_threshold])
            results['high_score_activities'] = int(high_score_count)
            results['high_score_threshold_p95'] = round(float(high_score_threshold), 4)
            
            # Compare with actual alerts
            if hasattr(self, 'alerts_df') and len(self.alerts_df) > 0:
                alert_to_activity_ratio = len(self.alerts_df) / len(self.activities_df) * 100
                results['alert_to_activity_ratio_percent'] = round(alert_to_activity_ratio, 2)
                print(f"  High Score Activities (P95+): {high_score_count}")
                print(f"  Alert/Activity Ratio: {alert_to_activity_ratio:.2f}%")
        
        return results
    
    def validate_temporal_patterns(self) -> Dict[str, Any]:
        """
        Validation G: Temporal Pattern Analysis
        Checks for unusual time patterns in alerts and activities
        """
        print("\n⏰ Validation G: Temporal Pattern Analysis")
        
        results = {}
        
        # Alert temporal patterns
        date_col = None
        for col in ['createdate', 'alert_date', 'created_at']:
            if col in self.alerts_df.columns:
                date_col = col
                break
        
        if date_col:
            self.alerts_df['date_parsed'] = pd.to_datetime(self.alerts_df[date_col], errors='coerce')
            self.alerts_df['day_of_week'] = self.alerts_df['date_parsed'].dt.dayofweek
            self.alerts_df['hour'] = self.alerts_df['date_parsed'].dt.hour
            
            # Day of week distribution
            dow_dist = self.alerts_df['day_of_week'].value_counts().sort_index().to_dict()
            dow_names = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
            results['alerts_by_day_of_week'] = {dow_names.get(int(k), str(k)): int(v) for k, v in dow_dist.items()}
            
            # Hour distribution (check for batch processing patterns)
            hour_dist = self.alerts_df['hour'].value_counts().sort_index().to_dict()
            results['alerts_by_hour'] = {int(k): int(v) for k, v in hour_dist.items()}
            
            # Detect batch patterns (>50% in single hour)
            max_hour_pct = max(hour_dist.values()) / len(self.alerts_df) * 100 if hour_dist else 0
            results['max_hour_concentration_percent'] = round(max_hour_pct, 2)
            if max_hour_pct > 50:
                max_hour = max(hour_dist, key=hour_dist.get)
                print(f"  ⚠️ Batch pattern detected: {max_hour_pct:.1f}% alerts at hour {max_hour}")
            
            print(f"  Day of Week Distribution: {results['alerts_by_day_of_week']}")
        
        # Activity year_month validation
        if 'year_month' in self.activities_df.columns:
            month_dist = self.activities_df['year_month'].value_counts().to_dict()
            results['activities_by_month'] = {str(k): int(v) for k, v in sorted(month_dist.items())[:12]}
            print(f"  Activity Months: {len(month_dist)} unique periods")
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate complete validation report"""
        print("\n" + "="*60)
        print("ALERT QUALITY VALIDATION REPORT")
        print("="*60)
        
        if not self.load_data():
            return {
                "status": "ERROR",
                "message": "Failed to load CSV files",
                "timestamp": datetime.now().isoformat()
            }
        
        # Run all validations
        alert_counts = self.validate_alert_counts()
        duplicates = self.detect_duplicates()
        monthly_dist = self.calculate_monthly_distribution()
        data_quality = self.check_data_quality()
        metadata_quality = self.validate_alert_metadata()
        risk_quality = self.validate_risk_quality()
        activity_scores = self.validate_activity_scores()
        temporal_patterns = self.validate_temporal_patterns()
        
        # Generate recommendations
        recommendations = []
        
        if alert_counts['consolidation_rate_percent'] < 30:
            recommendations.append("Low consolidation rate - consider reviewing alert grouping logic")
        
        if duplicates['duplicate_triggers_found'] > 0:
            recommendations.append(f"Found {duplicates['duplicate_triggers_found']} duplicate triggers - review suppression mechanism")
        
        if data_quality['consistency_status'] == "FAIL":
            recommendations.append("Data consistency issues detected - investigate missing trigger references")
        
        if data_quality['orphan_alerts_missing_risks'] > 0:
            recommendations.append(f"{data_quality['orphan_alerts_missing_risks']} triggers missing risk metadata")
        
        if metadata_quality.get('assignment_rate_percent', 100) < 50:
            recommendations.append(f"Low assignment rate ({metadata_quality.get('assignment_rate_percent')}%) - consider alert routing improvements")
        
        if risk_quality.get('suppression_coverage_percent', 100) < 80:
            recommendations.append(f"Low suppression configuration coverage ({risk_quality.get('suppression_coverage_percent')}%)")
        
        if activity_scores.get('alert_to_activity_ratio_percent', 0) > 5:
            recommendations.append(f"High alert rate ({activity_scores.get('alert_to_activity_ratio_percent')}%) - consider tuning detection thresholds")
        
        if temporal_patterns.get('max_hour_concentration_percent', 0) > 80:
            recommendations.append(f"Batch processing pattern detected - {temporal_patterns.get('max_hour_concentration_percent')}% alerts in single hour")
        
        if not recommendations:
            recommendations.append("All validations passed - alert quality looks good")
        
        # Compile full report
        report = {
            "validation_type": "alert_quality",
            "timestamp": datetime.now().isoformat(),
            "status": "FAIL" if data_quality['consistency_status'] == "FAIL" or duplicates['duplicate_triggers_found'] > 0 else "PASS",
            "validations": {
                "alert_count_analysis": alert_counts,
                "duplicate_detection": duplicates,
                "monthly_distribution": monthly_dist,
                "data_quality": data_quality,
                "metadata_quality": metadata_quality,
                "risk_quality": risk_quality,
                "activity_scores": activity_scores,
                "temporal_patterns": temporal_patterns
            },
            "recommendations": recommendations,
            "summary": {
                "total_alerts": alert_counts['total_alerts'],
                "consolidation_rate": alert_counts['consolidation_rate_percent'],
                "duplicate_triggers": duplicates['duplicate_triggers_found'],
                "data_consistency": data_quality['consistency_status'],
                "assignment_rate": metadata_quality.get('assignment_rate_percent', 0),
                "alert_to_activity_ratio": activity_scores.get('alert_to_activity_ratio_percent', 0)
            }
        }
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Status: {report['status']}")
        print(f"Total Alerts: {report['summary']['total_alerts']}")
        print(f"Consolidation Rate: {report['summary']['consolidation_rate']}%")
        print(f"Duplicate Triggers: {report['summary']['duplicate_triggers']}")
        print(f"Data Consistency: {report['summary']['data_consistency']}")
        print("\nRecommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_dir: str = "reports") -> str:
        """Save report to JSON file"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"alert_validation_{timestamp}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Report saved: {filepath}")
        return str(filepath)


def main():
    """Main execution"""
    validator = AlertValidator()
    report = validator.generate_report()
    validator.save_report(report)


if __name__ == "__main__":
    main()
