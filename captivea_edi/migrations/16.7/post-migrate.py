# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("\n" + " ------- Odoo Post-Migration Started -------")

    _logger.info(" ------- Post-Migration Ended -------" + "\n")
