"""
WSGI entrypoint for running Data Formulator under a production server
(gunicorn), instead of Flask's single-threaded development server.

`app.run_app()` builds its config from `sys.argv` via argparse, which is
wrong here: under gunicorn, `sys.argv` holds gunicorn's own CLI arguments,
not ours. This module reproduces the same one-time startup sequence
`run_app()` performs, but sourcing every setting from environment variables
(matching each CLI flag's own env-var default) instead of argv, then hands
the resulting Flask `app` object to gunicorn.

Usage:
    gunicorn -c gunicorn.conf.py data_formulator.wsgi:app
"""
import os

from data_formulator.app import (
    app,
    configure_logging,
    configure_file_logging,
    _register_blueprints,
)

configure_logging()

app.config['CLI_ARGS'] = {
    'host': os.environ.get('HOST', '127.0.0.1'),
    'sandbox': os.environ.get('SANDBOX', 'local'),
    'disable_display_keys': os.environ.get('DISABLE_DISPLAY_KEYS', 'false').strip().lower() == 'true',
    'disable_data_connectors': os.environ.get('DISABLE_DATA_CONNECTORS', 'false').strip().lower() == 'true',
    'disable_custom_models': os.environ.get('DISABLE_CUSTOM_MODELS', 'false').strip().lower() == 'true',
    'max_display_rows': int(os.environ.get('MAX_DISPLAY_ROWS', '10000')),
    'scratch_max_bytes': int(os.environ.get('SCRATCH_MAX_SIZE_MB', '1024')) * 1024 * 1024,
    'scratch_max_file_bytes': int(os.environ.get('SCRATCH_MAX_FILE_SIZE_MB', '20')) * 1024 * 1024,
    'data_dir': os.environ.get('DATA_FORMULATOR_HOME'),
    'dev': False,
    'workspace_backend': os.environ.get('WORKSPACE_BACKEND', 'local'),
    'azure_blob_connection_string': os.environ.get('AZURE_BLOB_CONNECTION_STRING'),
    'azure_blob_account_url': os.environ.get('AZURE_BLOB_ACCOUNT_URL'),
    'azure_blob_container': os.environ.get('AZURE_BLOB_CONTAINER', 'data-formulator'),
    'available_languages': [
        lang.strip() for lang in os.environ.get('AVAILABLE_LANGUAGES', 'en,zh').split(',') if lang.strip()
    ],
}

configure_file_logging()
_register_blueprints()

print("Ready! (served by gunicorn)", flush=True)
