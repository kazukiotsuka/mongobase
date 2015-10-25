#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# logger.py
# mongobase

from logging import getLogger, StreamHandler, Formatter, DEBUG, basicConfig

def configure_log(level=DEBUG, name=__name__):
    basicConfig(stream=sys.stderr)
    handler = StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(
        Formatter(
            '%(asctime)s[%(levelname)s]%(filename)s:%(lineno)d: %(message)s')
        )
    logger = getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger.debug

logger = configure_log(level=logging.DEBUG)


