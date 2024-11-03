#!/usr/bin/env python3
"""This is the entrypoint for running the django site.

Use ``python ./manage.py help`` for more info.
"""

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "thaliawebsite.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        try:
            # If Django couldn't be found, we're probably not in the virtual
            # environment. This re-execs the file, but prefixed with `uv run`
            # so the script will be running in the venv.
            os.execvp("uv", ["uv", "run", *sys.argv])
        except FileNotFoundError:
            raise ImportError(
                "Can't find Django or uv. Make sure to install "
                "the required dependencies from README.md!"
            ) from exc
    execute_from_command_line(sys.argv)
