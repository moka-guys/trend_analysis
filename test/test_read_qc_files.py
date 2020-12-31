import pytest, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from read_qc_files import arg_parse
import argparse
try:
    from unittest import mock  # python 3.3+
except ImportError:
    import mock  # python 2.6-3.2

def test_arg_parse_dev():
    """
    Test that the argument parser works with and without the --dev command line argument.
    """
    # without command line argument
    prod_args = arg_parse()
    assert prod_args.dev == False
    # with command line argument
    with mock.patch('sys.argv', ['read_qc_files', "--dev"]):
        dev_args = arg_parse()
        assert dev_args.dev == True