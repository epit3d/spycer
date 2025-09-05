#!/usr/bin/env bash
set -e
python -m unittest discover -s test -p '*_test.py'
