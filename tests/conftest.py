import pytest

from tracemedic.config import Settings
from tracemedic.engine import Engine
from tracemedic.testing import ScriptedProvider


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path, provider="scripted", model="deterministic-test-double")


@pytest.fixture
def engine(settings):
    return Engine(settings, ScriptedProvider())
