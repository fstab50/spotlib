"""
Local logging and configuration variables for build scripts
    - Python3 only
"""
import os
import subprocess


enable_logging = True
log_filename = ''
log_path = ''
log_mode = 'STREAM'


def _root():
    """Returns root directory of git project repository"""
    cmd = 'git rev-parse --show-toplevel 2>/dev/null'
    return subprocess.getoutput(cmd).strip()


def package_name(artifact):
    with open(artifact) as f1:
        f2 = f1.readlines()
    for line in f2:
        if line.startswith('PACKAGE'):
            return line.split(':')[1]
    return None


script_config = {
    "PROJECT": {
        "PACKAGE": package_name(os.path.join(_root(), 'DESCRIPTION.rst')),
    },
    "LOGGING": {
        "ENABLE_LOGGING": enable_logging,
        "LOG_FILENAME": log_filename,
        "LOG_PATH": log_path,
        "LOG_MODE": log_mode,
        "SYSLOG_FILE": False
    }
}
