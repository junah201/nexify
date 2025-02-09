import importlib

import nexify.templates.basic.main
import pytest
from nexify import Nexify


@pytest.fixture(scope="function")
def app():
    app_instance = Nexify()
    return app_instance


@pytest.fixture(scope="function")
def basic_app():
    importlib.reload(nexify.templates.basic.main)
    return nexify.templates.basic.main.app
