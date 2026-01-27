"""
Python behavior tests for make_gl_entries function.

Tests the original ERPNext make_gl_entries function with mocked dependencies
to capture behavior for parity testing.
"""

import json
import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from types import SimpleNamespace

def simple_namespace_to_dict(obj):
    """Convert SimpleNamespace object to dict recursively."""
    if isinstance(obj, SimpleNamespace):
        return {k: simple_namespace_to_dict(v) for k, v in vars(obj).items()}
    elif isinstance(obj, list):
        return [simple_namespace_to_dict(item) for item in obj]
    else:
        return obj

# ------------------------------------------------------------

# 🔥 CRITICAL FIX: Mock frappe BEFORE importing legacy code

# ------------------------------------------------------------

sys.modules['frappe'] = MagicMock()
sys.modules['frappe.model'] = MagicMock()
sys.modules['frappe.model.meta'] = MagicMock()
sys.modules['frappe.utils'] = MagicMock()
sys.modules['frappe.utils.caching'] = MagicMock()
sys.modules['erpnext'] = MagicMock()
sys.modules['erpnext.accounts'] = MagicMock()
sys.modules['erpnext.accounts.doctype'] = MagicMock()
sys.modules['erpnext.accounts.doctype.accounting_dimension'] = MagicMock()
sys.modules['erpnext.accounts.doctype.accounting_dimension.accounting_dimension'] = MagicMock()
sys.modules['erpnext.accounts.doctype.accounting_dimension_filter'] = MagicMock()
sys.modules['erpnext.accounts.doctype.accounting_dimension_filter.accounting_dimension_filter'] = MagicMock()
sys.modules['erpnext.accounts.doctype.accounting_period'] = MagicMock()
sys.modules['erpnext.accounts.doctype.accounting_period.accounting_period'] = MagicMock()
sys.modules['erpnext.accounts.doctype.budget'] = MagicMock()
sys.modules['erpnext.accounts.doctype.budget.budget'] = MagicMock()
sys.modules['erpnext.accounts.utils'] = MagicMock()
sys.modules['erpnext.controllers'] = MagicMock()
sys.modules['erpnext.controllers.budget_controller'] = MagicMock()
sys.modules['erpnext.exceptions'] = MagicMock()

# Add the legacy_code path to sys.path
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), '..', '..', 'legacy_code')
)

from accounts.general_ledger import make_gl_entries


class TestMakeGlEntries(unittest.TestCase):
    """Test cases for make_gl_entries function behavior."""

    def setUp(self):
        """Setup test fixtures."""
        self.test_results = []

    def tearDown(self):
        """Save test results to JSON file."""
        output_file = os.path.join(
            os.path.dirname(__file__),
            '..',
            'artifacts',
            'python_make_gl_entries.json'
        )
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Convert SimpleNamespace objects to dicts for JSON serialization
        serializable_results = []
        for result in self.test_results:
            serializable_result = {
                'test_case': result['test_case'],
                'input': simple_namespace_to_dict(result['input']),
                'output': result['output'],
                'status': result['status'],
                'error': result['error']
            }
            serializable_results.append(serializable_result)

        with open(output_file, 'w') as f:
            json.dump(
                {
                    'function': 'make_gl_entries',
                    'test_results': serializable_results
                },
                f,
                indent=2
            )

    @patch('accounts.general_ledger.frappe')
    @patch('accounts.general_ledger.create_payment_ledger_entry')
    @patch('accounts.general_ledger.save_entries')
    @patch('accounts.general_ledger.make_entry')
    @patch('accounts.general_ledger.validate_accounting_period')
    @patch('accounts.general_ledger.validate_disabled_accounts')
    @patch('accounts.general_ledger.process_gl_map')
    def test_basic_gl_entries(
        self,
        mock_process_gl_map,
        mock_validate_disabled_accounts,
        mock_validate_accounting_period,
        mock_make_entry,
        mock_save_entries,
        mock_create_payment_ledger,
        mock_frappe
    ):
        """Test basic GL entries creation."""
        mock_frappe.get_single_value.return_value = 0

        # Balanced GL map: debit and credit sum to 0
        gl_map = [
            SimpleNamespace(
                account='Test Account Debit',
                debit=100.0,
                credit=0.0,
                posting_date='2023-01-01',
                company='Test Company',
                voucher_type='Journal Entry',
                voucher_no='JE-001'
            ),
            SimpleNamespace(
                account='Test Account Credit',
                debit=0.0,
                credit=100.0,
                posting_date='2023-01-01',
                company='Test Company',
                voucher_type='Journal Entry',
                voucher_no='JE-001'
            )
        ]
        mock_process_gl_map.return_value = gl_map

        try:
            result = make_gl_entries(gl_map)
            status = 'success'
            error = None
        except Exception as e:
            result = None
            status = 'error'
            error = str(e)

        self.test_results.append({
            'test_case': 'basic_gl_entries',
            'input': {'gl_map': simple_namespace_to_dict(gl_map)},
            'output': result,
            'status': status,
            'error': error
        })

        self.assertEqual(status, 'success')

    @patch('accounts.general_ledger.frappe')
    @patch('accounts.general_ledger.create_payment_ledger_entry')
    @patch('accounts.general_ledger.save_entries')
    def test_empty_gl_map(
        self,
        mock_save_entries,
        mock_create_payment_ledger,
        mock_frappe
    ):
        """Test with empty GL map."""
        mock_frappe.get_single_value.return_value = 0

        gl_map = []

        try:
            result = make_gl_entries(gl_map)
            status = 'success'
            error = None
        except Exception as e:
            result = None
            status = 'error'
            error = str(e)

        self.test_results.append({
            'test_case': 'empty_gl_map',
            'input': {'gl_map': gl_map},
            'output': result,
            'status': status,
            'error': error
        })

        self.assertEqual(status, 'success')

    @patch('accounts.general_ledger.frappe')
    @patch('accounts.general_ledger.create_payment_ledger_entry')
    @patch('accounts.general_ledger.save_entries')
    @patch('accounts.general_ledger.make_reverse_gl_entries')
    def test_cancel_operation(
        self,
        mock_make_reverse_gl_entries,
        mock_save_entries,
        mock_create_payment_ledger,
        mock_frappe
    ):
        """Test cancel operation."""
        mock_frappe.get_single_value.return_value = 0

        # Balanced GL map: debit and credit sum to 0
        gl_map = [
            SimpleNamespace(
                account='Test Account Debit',
                debit=50.0,
                credit=0.0,
                posting_date='2023-01-01',
                company='Test Company',
                voucher_type='Journal Entry',
                voucher_no='JE-001'
            ),
            SimpleNamespace(
                account='Test Account Credit',
                debit=0.0,
                credit=50.0,
                posting_date='2023-01-01',
                company='Test Company',
                voucher_type='Journal Entry',
                voucher_no='JE-001'
            )
        ]

        try:
            result = make_gl_entries(gl_map, cancel=True)
            status = 'success'
            error = None
        except Exception as e:
            result = None
            status = 'error'
            error = str(e)

        self.test_results.append({
            'test_case': 'cancel_operation',
            'input': {'gl_map': simple_namespace_to_dict(gl_map), 'cancel': True},
            'output': result,
            'status': status,
            'error': error
        })

        self.assertEqual(status, 'success')

    @patch('accounts.general_ledger.frappe')
    @patch('accounts.general_ledger.create_payment_ledger_entry')
    @patch('accounts.general_ledger.save_entries')
    @patch('accounts.general_ledger.make_entry')
    @patch('accounts.general_ledger.validate_accounting_period')
    @patch('accounts.general_ledger.validate_disabled_accounts')
    @patch('accounts.general_ledger.process_gl_map')
    def test_with_merge_entries_false(
        self,
        mock_process_gl_map,
        mock_validate_disabled_accounts,
        mock_validate_accounting_period,
        mock_make_entry,
        mock_save_entries,
        mock_create_payment_ledger,
        mock_frappe
    ):
        """Test with merge_entries=False."""
        mock_frappe.get_single_value.return_value = 0

        gl_map = [
            SimpleNamespace(
                account='Test Account 1',
                debit=100.0,
                credit=0.0,
                posting_date='2023-01-01',
                company='Test Company',
                voucher_type='Journal Entry',
                voucher_no='JE-001'
            ),
            SimpleNamespace(
                account='Test Account 2',
                debit=0.0,
                credit=100.0,
                posting_date='2023-01-01',
                company='Test Company',
                voucher_type='Journal Entry',
                voucher_no='JE-001'
            )
        ]
        mock_process_gl_map.return_value = gl_map

        try:
            result = make_gl_entries(gl_map, merge_entries=False)
            status = 'success'
            error = None
        except Exception as e:
            result = None
            status = 'error'
            error = str(e)

        self.test_results.append({
            'test_case': 'with_merge_entries_false',
            'input': {'gl_map': simple_namespace_to_dict(gl_map), 'merge_entries': False},
            'output': result,
            'status': status,
            'error': error
        })

        self.assertEqual(status, 'success')

    @patch('accounts.general_ledger.frappe')
    @patch('accounts.general_ledger.create_payment_ledger_entry')
    @patch('accounts.general_ledger.save_entries')
    @patch('accounts.general_ledger.make_entry')
    @patch('accounts.general_ledger.validate_accounting_period')
    @patch('accounts.general_ledger.validate_disabled_accounts')
    @patch('accounts.general_ledger.process_gl_map')
    def test_with_adv_adj_true(
        self,
        mock_process_gl_map,
        mock_validate_disabled_accounts,
        mock_validate_accounting_period,
        mock_make_entry,
        mock_save_entries,
        mock_create_payment_ledger,
        mock_frappe
    ):
        """Test with adv_adj=True."""
        mock_frappe.get_single_value.return_value = 0

        # Balanced GL map: debit and credit sum to 0
        gl_map = [
            SimpleNamespace(
                account='Test Account Debit',
                debit=200.0,
                credit=0.0,
                posting_date='2023-01-01',
                company='Test Company',
                voucher_type='Journal Entry',
                voucher_no='JE-001'
            ),
            SimpleNamespace(
                account='Test Account Credit',
                debit=0.0,
                credit=200.0,
                posting_date='2023-01-01',
                company='Test Company',
                voucher_type='Journal Entry',
                voucher_no='JE-001'
            )
        ]
        mock_process_gl_map.return_value = gl_map

        try:
            result = make_gl_entries(gl_map, adv_adj=True)
            status = 'success'
            error = None
        except Exception as e:
            result = None
            status = 'error'
            error = str(e)

        self.test_results.append({
            'test_case': 'with_adv_adj_true',
            'input': {'gl_map': simple_namespace_to_dict(gl_map), 'adv_adj': True},
            'output': result,
            'status': status,
            'error': error
        })

        self.assertEqual(status, 'success')


if __name__ == '__main__':
    unittest.main()
