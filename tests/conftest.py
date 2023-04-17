"""
Pytest fixtures.

https://docs.pytest.org/en/6.2.x/fixture.html
"""
import pytest

from django.db.models.signals import post_save

from taxonomy.models import Job
from taxonomy.signals.handlers import handle_generate_job_description


@pytest.fixture(autouse=True)
def disconnect_signals(request):
    """
    Pytest fixture to disable post_save signal for Job model only if `use_signal` marker is not set on test function.
    """
    if 'use_signals' in request.keywords:
        return

    post_save.disconnect(handle_generate_job_description, sender=Job)

    def reconnect_signals():
        post_save.connect(handle_generate_job_description, sender=Job)

    request.addfinalizer(reconnect_signals)
