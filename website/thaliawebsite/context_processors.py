"""
These context processors can be used to expand the context provided
tos views.
"""
import os


def source_commit(_):
    return {'SOURCE_COMMIT': os.environ.get('SOURCE_COMMIT', 'unknown')}
