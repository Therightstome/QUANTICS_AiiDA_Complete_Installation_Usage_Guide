"""
Tests for command line argument parser
"""

import pytest
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.argument_parser import create_argument_parser, parse_args


class TestArgumentParser:
    """Test command line argument parsing"""
    
    def test_create_argument_parser(self):
        """Test creating argument parser"""
        parser = create_argument_parser()
        
        assert parser is not None
        assert parser.prog == 'argument_parser.py'
        
    def test_parse_help(self):
        """Test parsing help argument"""
        with pytest.raises(SystemExit):
            parse_args(['--help'])
    
    def test_parse_create_command(self):
        """Test parsing create command"""
        args = parse_args([
            'create', 'test_calc', 
            'input.inp', 'operator.op', 
            '--workflow', 'MCTDH'
        ])
        
        assert args.command == 'create'
        assert args.name == 'test_calc'
        assert args.inp_file == Path('input.inp')
        assert args.op_file == Path('operator.op')
        assert args.workflow == 'MCTDH'
    
    def test_parse_run_command(self):
        """Test parsing run command"""
        args = parse_args([
            'run', 'test_calc',
            '--quantics-exe', '/path/to/quantics'
        ])
        
        assert args.command == 'run'
        assert args.name == 'test_calc'
        assert args.quantics_exe == '/path/to/quantics'
    
    def test_parse_analyze_command(self):
        """Test parsing analyze command"""
        args = parse_args([
            'analyze', 'test_calc',
            'rdcheck etot', 'rdcheck spop'
        ])
        
        assert args.command == 'analyze'
        assert args.name == 'test_calc'
        assert args.tools == ['rdcheck etot', 'rdcheck spop']
    
    def test_parse_gui_command(self):
        """Test parsing GUI command"""
        args = parse_args(['gui', '--mode', 'local'])
        
        assert args.command == 'gui'
        assert args.mode == 'local'
    
    def test_parse_no_command(self):
        """Test parsing with no command (should default to GUI)"""
        args = parse_args([])
        
        assert args.command is None 