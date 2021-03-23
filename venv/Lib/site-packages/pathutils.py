import os
import sys


def project_path(type='full', dirname='code'):
    """
    Parameters
    ----------
    type: str (full or relative defaults to full)
    dirname : str of dirname to break on

    Returns
    ---------
    paths
    """
    parts = os.getcwd().split(os.sep)
    return '/'.join(parts[parts.index(dirname):]) if type == 'relative' else '/'.join(parts[0:parts.index(dirname)])
