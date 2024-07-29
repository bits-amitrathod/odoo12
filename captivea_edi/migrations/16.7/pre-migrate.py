# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("\n" + " ------- Pri-Migration Started -------")
    # TODO: ODOO16_UPG At time upgrations scheduler should not execute
    cr.execute("""update setu_sftp set instance_active = false;""")
    _logger.info(" ------- Pri-Migration Ended -------" + "\n")
