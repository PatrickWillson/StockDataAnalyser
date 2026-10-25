"""
Unit tests for Dossier file saving functionality.
"""

import os
import pytest
import tempfile
import shutil
from stock_data_analyser import save_dossier


def test_save_dossier_creates_directory():
    """
    Test that save_dossier creates the data/ directory if it doesn't exist.
    Validates: Requirements 9.12, 9.13
    """
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Ensure data directory doesn't exist
            assert not os.path.exists('data')
            
            # Save dossier
            save_dossier('TEST.US', 'Test content')
            
            # Verify directory was created
            assert os.path.exists('data')
            assert os.path.isdir('data')
        finally:
            os.chdir(original_cwd)


def test_save_dossier_filename_format():
    """
    Test that save_dossier saves file with correct naming format.
    Validates: Requirements 9.8, 9.9
    """
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Test with ticker containing dots
            save_dossier('AAPL.US', 'Test content for AAPL')
            
            # Verify file was created with correct name (dots replaced with underscores)
            expected_filename = 'data/AAPL_US_DOSSIER.md'
            assert os.path.exists(expected_filename)
            
            # Verify it's a .md file
            assert expected_filename.endswith('.md')
            
            # Verify content
            with open(expected_filename, 'r', encoding='utf-8') as f:
                content = f.read()
                assert content == 'Test content for AAPL'
        finally:
            os.chdir(original_cwd)


def test_save_dossier_multiple_tickers():
    """
    Test that save_dossier handles multiple tickers correctly.
    """
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Save multiple dossiers
            save_dossier('VOD.L', 'Vodafone content')
            save_dossier('RY.TO', 'Royal Bank content')
            save_dossier('BMW.DE', 'BMW content')
            
            # Verify all files were created
            assert os.path.exists('data/VOD_L_DOSSIER.md')
            assert os.path.exists('data/RY_TO_DOSSIER.md')
            assert os.path.exists('data/BMW_DE_DOSSIER.md')
            
            # Verify contents
            with open('data/VOD_L_DOSSIER.md', 'r', encoding='utf-8') as f:
                assert f.read() == 'Vodafone content'
            
            with open('data/RY_TO_DOSSIER.md', 'r', encoding='utf-8') as f:
                assert f.read() == 'Royal Bank content'
            
            with open('data/BMW_DE_DOSSIER.md', 'r', encoding='utf-8') as f:
                assert f.read() == 'BMW content'
        finally:
            os.chdir(original_cwd)
