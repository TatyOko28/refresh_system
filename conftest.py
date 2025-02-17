import pytest
from django.db import connections
from django.test.utils import setup_databases, teardown_databases

@pytest.fixture(scope="session")
def django_db_setup(
    request,
    django_test_environment,
    django_db_blocker,
    django_db_use_migrations,
    django_db_keepdb,
    django_db_createdb,
    django_db_modify_db_settings,
):
    setup_databases_args = {}

    if not django_db_use_migrations:
        from pytest_django.compat import _disable_migrations

        _disable_migrations()

    if django_db_keepdb and not django_db_createdb:
        setup_databases_args["keepdb"] = True

    with django_db_blocker.unblock():
        db_cfg = setup_databases(
            verbosity=request.config.option.verbose,
            interactive=False,
            **setup_databases_args,
        )

    
    for conn in connections.all():
        conn.inc_thread_sharing()

    yield  

   
    with django_db_blocker.unblock():
        teardown_databases(db_cfg, verbosity=request.config.option.verbose)

    for conn in connections.all():
        conn.dec_thread_sharing()