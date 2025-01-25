#!/usr/bin/env bash

set -e
set -x

pytest --cov=nexify --cov-fail-under=100 --cov-report=term-missing --cov-report=xml "${@}"