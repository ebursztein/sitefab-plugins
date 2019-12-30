import shutil
from tqdm import tqdm
from pathlib import Path

from sitefab.plugins import SitePreparsing
from sitefab.SiteFab import SiteFab

PROGBAR = None


def _logprogress(path, names):
    """"log shutil progress
    see here: https://docs.python.org/2/library/shutil.html#shutil.Error
    """
    PROGBAR.update()
    return []   # nothing will be ignore


class CopyDir(SitePreparsing):
    """
    Copy directories
    """

    def process(self, unused, site, config):
        """ Process the content of the site once
        :param FabSite site: the site object
        """
        global PROGBAR
        log = ""
        errors = False
        targets = config.targets

        for target in targets:
            if '>' not in target:
                errors = True
                log += ("[Error] target '%s' is not properly formated<br/>" %
                        target)
                continue

            src, dst = target.split('>')
            src = src.strip()
            dst = dst.strip()

            PROGBAR = tqdm(desc='%s -> %s' % (src, dst), unit='files',
                           leave=False)

            src = site.config.root_dir / src
            dst = site.config.root_dir / dst

            try:
                shutil.copytree(src, dst, ignore=_logprogress)
            except:  # noqa
                errors += 1
                log += "[Failed] failed to copy '%s' to '%s' <br/>" % (src,
                                                                       dst)
                PROGBAR.close()
                continue

            log += "[OK]copied: '%s' to '%s'<br>" % (src, dst)
            PROGBAR.close()

        if errors:
            return (SiteFab.ERROR, "CopyDir", log)
        else:
            return (SiteFab.OK, "CopyDir", log)
