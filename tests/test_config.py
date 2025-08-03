"""
Tests for configuration management utilities
"""

import pytest
import tempfile
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.config import save_config, load_config, get_default_config


class TestConfig:
    """Test configuration management functions"""
    
    def test_get_default_config(self):
        """Test getting default configuration"""
        config = get_default_config()
        
        assert isinstance(config, dict)
        assert 'calculation_name' in config
        assert 'workflow_type' in config
        assert config['workflow_type'] == 'MCTDH'
        assert config['quantics_executable'] == 'quantics'
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration"""
        test_config = {
            'calculation_name': 'test_calc',
            'workflow_type': 'vMCG',
            'inp_file': Path('/test/path/input.inp'),
            'analysis_tools': ['rdcheck etot', 'rdcheck spop']
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / 'test_config.json'
            
            # Test saving
            success = save_config(test_config, config_file)
            assert success
            assert config_file.exists()
            
            # Test loading
            loaded_config = load_config(config_file)
            assert loaded_config is not None
            assert loaded_config['calculation_name'] == 'test_calc'
            assert loaded_config['workflow_type'] == 'vMCG'
            assert isinstance(loaded_config['inp_file'], Path)
            assert loaded_config['analysis_tools'] == ['rdcheck etot', 'rdcheck spop']
    
    def test_load_nonexistent_config(self):
        """Test loading non-existent configuration file"""
        result = load_config(Path('/nonexistent/config.json'))
        assert result is None 