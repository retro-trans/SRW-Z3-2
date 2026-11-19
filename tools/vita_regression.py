"""Run font regressions with the historical Pillow version before PIL loads."""
import argparse
import sys
import unittest
from tools import vita
from PIL import __version__


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--full',action='store_true');args=parser.parse_args()
    if __version__!='12.3.0':raise ValueError('Run in a fresh interpreter with the pinned Pillow 12.3.0 workset')
    loader=unittest.defaultTestLoader
    suite=loader.discover('tests') if args.full else loader.loadTestsFromNames([
        'tests.test_latin_font','tests.test_review38_fonts','tests.test_ui_build','tests.test_vita_port'])
    print('Pinned Pillow',__version__,flush=True)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    raise SystemExit(not result.wasSuccessful())


if __name__=='__main__':main()
