#! /bin/bash
htmldir=~/Desktop/chess_rating_test_coverage
pytest -v --cov=rating --cov-report=html:${htmldir}
