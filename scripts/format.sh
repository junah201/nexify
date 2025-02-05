#!/usr/bin/env bash
set -x

ruff check nexify scripts tests docs_src --fix
ruff format nexify scripts tests docs_src