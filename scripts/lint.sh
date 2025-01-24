#!/usr/bin/env bash

set -e
set -x

mypy nexify
ruff check nexify scripts
ruff format nexify scripts --check