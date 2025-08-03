"""
Configuration Management Utilities
=================================

This module provides configuration saving/loading functionality
for QUANTICS GUI applications.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def save_config(config: Dict[str, Any], file_path: Optional[Path] = None) -> bool:
    """
    Save configuration to JSON file

    Args:
        config: Configuration dictionary to save
        file_path: Path to save configuration. If None, generates timestamp-based name

    Returns:
        bool: True if successful, False otherwise
    """
    if file_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = Path(f"quantics_config_{timestamp}.json")

    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert Path objects to strings for JSON serialization
        json_config = _serialize_config(config)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(json_config, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False


def load_config(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load configuration from JSON file

    Args:
        file_path: Path to configuration file

    Returns:
        Dict with configuration or None if failed
    """
    try:
        if not file_path.exists():
            print(f"Configuration file not found: {file_path}")
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Convert string paths back to Path objects
        return _deserialize_config(config)

    except Exception as e:
        print(f"Error loading configuration: {e}")
        return None


def _serialize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Path objects to strings for JSON serialization"""
    json_config = {}

    for key, value in config.items():
        if isinstance(value, Path):
            json_config[key] = str(value)
        elif isinstance(value, dict):
            json_config[key] = _serialize_config(value)
        elif isinstance(value, list):
            json_config[key] = [str(item) if isinstance(item, Path) else item for item in value]
        else:
            json_config[key] = value

    return json_config


def _deserialize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Convert string paths back to Path objects"""
    # Define which keys should be converted to Path objects
    path_keys = {
        "inp_file",
        "op_file",
        "db_folder",
        "working_directory",
        "quantics_executable",
        "base_directory",
    }

    result_config = {}

    for key, value in config.items():
        if key in path_keys and value:
            result_config[key] = Path(value)
        elif isinstance(value, dict):
            result_config[key] = _deserialize_config(value)
        else:
            result_config[key] = value

    return result_config


def get_default_config() -> Dict[str, Any]:
    """Get default configuration values"""
    return {
        "calculation_name": "my_quantics_run",
        "workflow_type": "MCTDH",
        "quantics_executable": "quantics",
        "working_directory": None,
        "inp_file": None,
        "op_file": None,
        "db_folder": None,
        "save_inputs": True,
        "cleanup_on_success": False,
        "analysis_tools": [],
        "rdgpop_nz": "2",
        "rdgpop_dof": "1",
        "show_cmdline": True,
        "execution_mode": "local",  # 'local' or 'aiida'
        "aiida_resources": 1,
        "aiida_walltime": 3600,
        "aiida_queue": None,
    }
