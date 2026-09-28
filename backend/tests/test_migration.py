import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from alembic.config import Config
from alembic import command

def test_migration_applies_cleanly():
    """
    Test that the Alembic migration applies cleanly.
    """
    # Path to alembic.ini should be absolute to avoid running issues from root
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_ini_path = os.path.join(backend_dir, "alembic.ini")
    
    alembic_cfg = Config(alembic_ini_path)
    # We also need to set the script location correctly
    alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    
    # In a real environment, we'd ensure this runs against a fresh regulens_test DB.
    # We run the upgrade command. If it fails, it will raise an exception.
    try:
        command.downgrade(alembic_cfg, "base")
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        pytest.fail(f"Alembic upgrade failed: {e}")
