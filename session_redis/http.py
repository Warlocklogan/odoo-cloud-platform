# -*- coding: utf-8 -*-
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
import os

from distutils.util import strtobool

import redis

import openerp
from openerp import http
from openerp.tools.func import lazy_property

from .session import RedisSessionStore

_logger = logging.getLogger(__name__)


def is_true(strval):
    return bool(strtobool(strval or '0'.lower()))


@lazy_property
def session_store(self):
    host = os.environ.get('ODOO_SESSION_REDIS_HOST') or 'localhost'
    port = int(os.environ.get('ODOO_SESSION_REDIS_PORT') or 6379)
    prefix = os.environ.get('ODOO_SESSION_REDIS_PREFIX')
    password = os.environ.get('ODOO_SESSION_REDIS_PASSWORD')
    expiration = os.environ.get('ODOO_SESSION_REDIS_EXPIRATION')
    _logger.debug("HTTP sessions stored in Redis %s:%s with prefix '%s'",
                  host, port, prefix or '')
    redis_client = redis.Redis(host=host, port=port, password=password)
    return RedisSessionStore(redis=redis_client, prefix=prefix,
                             expiration=expiration,
                             session_class=http.OpenERPSession)


def session_gc(session_store):
    """ Do not garbage collect the sessions

    Redis keys are automatically cleaned at the end of their
    expiration.
    """
    return


def purge_fs_sessions(path):
    for fname in os.listdir(path):
        path = os.path.join(path, fname)
        try:
            os.unlink(path)
        except OSError:
            pass


if is_true(os.environ.get('ODOO_SESSION_REDIS')):
    http.Root.session_store = session_store
    http.session_gc = session_gc
    # clean the existing sessions on the file system
    purge_fs_sessions(openerp.tools.config.session_dir)