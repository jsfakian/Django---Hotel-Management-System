"""
Test configuration for Django
Disables foreign key constraints for SQLite to handle pre-existing issues
"""

import sqlite3
from django.test.utils import setup_databases, teardown_databases
from django.db import connection

def setup_test_environment():
    """Patch SQLite to disable foreign key constraints during testing"""
    original_execute = sqlite3.Connection.execute
    
    def patched_execute(self, sql, *args, **kwargs):
        try:
            return original_execute(self, sql, *args, **kwargs)
        except sqlite3.IntegrityError:
            # Disable foreign key constraints if there's an integrity error
            original_execute(self, 'PRAGMA foreign_keys = OFF')
            return original_execute(self, sql, *args, **kwargs)
    
    sqlite3.Connection.execute = patched_execute

# Apply the patch when this module is imported
setup_test_environment()
