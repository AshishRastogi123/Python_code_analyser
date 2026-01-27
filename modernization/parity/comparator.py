"""
Parity Comparator for Python vs Go Migration Testing.

Compares test results between Python and Go implementations
to determine behavioral parity.
"""

import json
import os
from typing import Dict, Any, List
from pathlib import Path


class ParityComparator:
    """Compares Python and Go test results for parity analysis."""

    def __init__(self, artifacts_dir: str = None):
        if artifacts_dir is None:
            # Default to tests/artifacts relative to this file
            current_dir = Path(__file__).parent
            self.artifacts_dir = current_dir.parent.parent / "tests" / "artifacts"
        else:
            self.artifacts_dir = Path(artifacts_dir)

    def load_python_results(self, function_name: str) -> Dict[str, Any]:
        """Load Python test results from JSON file."""
        python_file = self.artifacts_dir / f"python_{function_name}.json"
        if not python_file.exists():
            raise FileNotFoundError(f"Python results file not found: {python_file}")

        with open(python_file, 'r') as f:
            return json.load(f)

    def load_go_results(self, function_name: str) -> Dict[str, Any]:
        """Load Go test results from JSON file."""
        go_file = self.artifacts_dir / f"go_{function_name}.json"
        if not go_file.exists():
            raise FileNotFoundError(f"Go results file not found: {go_file}")

        with open(go_file, 'r') as f:
            return json.load(f)

    def compare_results(self, function_name: str) -> Dict[str, Any]:
        """Compare Python and Go test results."""
        python_results = self.load_python_results(function_name)
        go_results = self.load_go_results(function_name)

        # Create lookup dictionaries for Go results
        go_results_lookup = {result['test_case']: result for result in go_results['test_results']}

        comparison_results = []
        total_tests = len(python_results['test_results'])
        passed_tests = 0
        failed_tests = 0

        for python_result in python_results['test_results']:
            test_case = python_result['test_case']
            go_result = go_results_lookup.get(test_case)

            if go_result is None:
                # Go test case not found
                comparison = {
                    'test_case': test_case,
                    'python_result': python_result['status'],
                    'go_result': 'NOT_FOUND',
                    'status': 'FAIL',
                    'reason': 'Go test case not found'
                }
                failed_tests += 1
            else:
                # Compare statuses
                python_status = python_result['status']
                go_status = go_result['status']

                if python_status == go_status:
                    comparison = {
                        'test_case': test_case,
                        'python_result': python_status,
                        'go_result': go_status,
                        'status': 'PASS'
                    }
                    passed_tests += 1
                else:
                    comparison = {
                        'test_case': test_case,
                        'python_result': python_status,
                        'go_result': go_status,
                        'status': 'FAIL',
                        'reason': f'Status mismatch: Python={python_status}, Go={go_status}'
                    }
                    failed_tests += 1

            comparison_results.append(comparison)

        # Generate summary
        summary = {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'pass_rate': round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0
        }

        report = {
            'function': function_name,
            'test_cases': comparison_results,
            'summary': summary,
            'metadata': {
                'python_tests_file': f"python_{function_name}.json",
                'go_tests_file': f"go_{function_name}.json",
                'generated_at': str(Path(__file__).parent.parent.parent / "utils" / "logger.py")  # Placeholder for timestamp
            }
        }

        return report

    def save_report(self, report: Dict[str, Any], function_name: str):
        """Save parity report to JSON file."""
        report_file = self.artifacts_dir.parent / "parity" / f"report_{function_name}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Parity report saved to: {report_file}")

    def run_comparison(self, function_name: str) -> Dict[str, Any]:
        """Run full comparison and save report."""
        print(f"🔍 Comparing parity for function: {function_name}")

        try:
            report = self.compare_results(function_name)
            self.save_report(report, function_name)

            print("✅ Parity comparison complete")
            print(f"📊 RESULT:\nTotal Tests: {report['summary']['total']}\nPassed: {report['summary']['passed']}\nFailed: {report['summary']['failed']}")

            return report

        except Exception as e:
            print(f"❌ Error during parity comparison: {e}")
            raise


def main():
    """CLI entry point for parity comparison."""
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m modernization.parity.comparator <function_name>")
        sys.exit(1)

    function_name = sys.argv[1]
    comparator = ParityComparator()
    comparator.run_comparison(function_name)


if __name__ == '__main__':
    main()
