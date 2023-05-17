import logging

from somesy.core.config import VERBOSE
from somesy.core.utils import set_logger

logger = logging.getLogger("somesy")


def test_set_logger_debug():
    # test debug mode
    set_logger(debug=True)
    assert logger.getEffectiveLevel() == logging.DEBUG


def test_set_logger_verbose():
    # test debug mode
    set_logger(verbose=True)
    assert logger.getEffectiveLevel() == VERBOSE


def test_set_logger_info():
    # test debug mode
    set_logger()
    assert logger.getEffectiveLevel() == logging.INFO
