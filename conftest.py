# Conftest is at the root because it is needed by all plugins
from pathlib import Path

import pytest
import git
from termcolor import cprint

from time import time
from sitefab import __version__ as version
from sitefab import utils
from sitefab import files
from sitefab.SiteFab import SiteFab

# NOTE you don't need to import fixture explictly pytest do it for you. Avoid
# flake8 errors

PKG_ROOT_DIR = Path(__file__).parent

TEMPLATE_DATA_ROOT = PKG_ROOT_DIR / 'tests' / 'sitefab_template'
TEMPLATE_GIT_URL = 'https://github.com/ebursztein/sitefab-template'

# each excution have a new TEMPLATE_DATA_PATH to avoid cache
# and find git miss commit issues.
TEMPLATE_DATA_PATH = None
TEMPLATE_DATA_CONFIG_FILE_PATH = None


@pytest.fixture(scope="session")
def sitefab():
    "pull needed data and create a valid instance of sitefab"

    fname = TEMPLATE_DATA_PATH / "config" / "sitefab.yaml"
    print('SiteFab version: %s' % version)
    return SiteFab(fname)


@pytest.fixture(scope="function")
def empty_post():
    "mock a post"
    post = utils.create_objdict()
    post.md = ""
    post.html = ""
    post.meta = utils.create_objdict()
    post.meta.statistics = utils.create_objdict()
    post.meta.toc = utils.create_objdict()
    post.elements = utils.create_objdict()
    return post


def pytest_configure(config):
    global TEMPLATE_DATA_PATH
    global TEMPLATE_DATA_CONFIG_FILE_PATH
    global PLUGINS_DATA_PATH

    TEMPLATE_DATA_PATH = TEMPLATE_DATA_ROOT / str(int(time()))
    TEMPLATE_DATA_CONFIG_FILE_PATH = TEMPLATE_DATA_PATH / 'config' / 'sitefab.yaml'  # noqa

    cprint('[Cleanup]', 'magenta')
    cprint('|- deleting old site template: %s' % TEMPLATE_DATA_ROOT, 'cyan')
    try:
        files.clean_dir(TEMPLATE_DATA_ROOT)
    except:  # noqa
        cprint('Warning: part of directory not deleted - should be fine thus',
               'yellow')

    # recreate if correctly deleted
    if not TEMPLATE_DATA_ROOT.exists():
        TEMPLATE_DATA_ROOT.mkdir()

    cprint('[SiteFab Templates]', 'magenta')
    if TEMPLATE_DATA_PATH.exists():
        cprint('Pulling latest sitefab template', 'green')
        g = git.cmd.Git(TEMPLATE_DATA_PATH)
        g.pull()
    else:
        cprint('Cloning sitefab template', 'yellow')
        git.Repo().clone_from(TEMPLATE_GIT_URL, TEMPLATE_DATA_PATH)

    cprint('[Injecting Plugins config]', 'magenta')