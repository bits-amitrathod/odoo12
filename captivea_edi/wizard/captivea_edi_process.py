# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import csv
import re
import datetime
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import pysftp

GHX_GLOBAL = {}
DOC_PREFIX_PO = '850'  # Prefix for Purchase Order Document
DOC_PREFIX_POC = '860'  # Prefix for Purchase Order Change Document
DOC_PREFIX_POA = '855'  # Prefix for Purchase Order Aknowledgment Document
DOC_PREFIX_ASN = '856'  # Prefix for Advanced Ship Notice Document
DOC_PREFIX_BIL = '810'  # Prefix for Invoice Document
DOC_PREFIX_INV = '846'  # Prefix for Inventory Document
CURRENT_ORDERS = list()  # Current Processed Orders REMOVE THIS LATER NOT NEEDED ANYMORE
POA_FIELDS = ['TRANSACTION ID', 'ACCOUNTING ID', 'PURPOSE', 'TYPE STATUS',
              'PO #', 'PO DATE', 'RELEASE NUMBER', 'REQUEST REFERENCE NUMBER',
              'CONTRACT NUMBER', 'SELLING PARTY NAME',
              'SELLING PARTY ADDRESS 1', 'SELLING PARTY ADDRESS 2',
              'SELLING PARTY CITY', 'SELLING PARTY STATE', 'SELLING PARTY ZIP',
              'ACCOUNT NUMBER - VENDOR NUMBER', 'WAREHOUSE ID', 'LINE #',
              'PO LINE #', 'VENDOR PART #', 'UPC', 'SKU', 'QTY', 'UOM',
              'PRICE', 'SCHEDULED DELIVERY DATE', 'SCHEDULED DELIVERY TIME',
              'ESTIMATED DELIVERY DATE', 'ESTIMATED DELIVERY TIME',
              'PROMISED DATE', 'PROMISED TIME', 'STATUS', 'STATUS QTY',
              'STATUS UOM']
ASN_FIELDS = ['TRANSACTION TYPE', 'ACCOUNTING ID', 'SHIPMENT ID', 'SCAC',
              'CARRIER PRO NUMBER', 'BILL OF LADING', 'SCHEDULED DELIVERY',
              'SHIP DATE', 'SHIP TO NAME', 'SHIP TO ADDRESS - LINE ONE',
              'SHIP TO ADDRESS - LINE TWO', 'SHIP TO CITY', 'SHIP TO STATE',
              'SHIP TO ZIP', 'SHIP TO COUNTRY', 'SHIP TO ADDRESS CODE',
              'SHIP VIA', 'SHIP TO TYPE', 'PACKAGING TYPE', 'GROSS WEIGHT',
              'GROSS WEIGHT UOM', 'NUMBER OF CARTONS SHIPPED',
              'CARRIER TRAILER NUMBER', 'TRAILER INITIAL', 'SHIP FROM NAME',
              'SHIP FROM ADDRESS - LINE ONE', 'SHIP FROM ADDRESS - LINE TWO',
              'SHIP FROM CITY', 'SHIP FROM STATE', 'SHIP FROM ZIP',
              'SHIP FROM COUNTRY', 'SHIP FROM ADDRESS CODE', 'VENDOR NUMBER',
              'DC CODE', 'TRANSPORTATION METHOD', 'PRODUCT GROUP', 'STATUS',
              'TIME SHIPPED', 'PO NUMBER', 'PO DATE', 'INVOICE NUMBER',
              'ORDER WEIGHT', 'STORE NAME', 'STORE NUMBER', 'MARK FOR CODE',
              'DEPARTMENT NUMBER', 'ORDER LADING QUANTITY', 'PACKAGING TYPE',
              'UCC-128', 'PACK SIZE', 'INNER PACK PER OUTER PACK',
              'PACK HEIGHT', 'PACK WIDTH', 'PACK WEIGHT',
              'QTY OF UPCS WITHIN PACK', 'UOM OF UPCS', 'STORE NAME',
              'STORE NUMBER', 'LINE NUMBER', 'VENDOR PART NUMBER',
              'BUYER PART NUMBER', 'UPC NUMBER', 'ITEM DESCRIPTION',
              'QUANTITY SHIPPED', 'UOM', 'QUANTITY ORDERED', 'UNIT PRICE',
              'PACK SIZE', 'PACK UOM', 'INNER PACKS PER OUTER PACK']


class CaptiveaEdiProcess(models.TransientModel):
    _name = 'captivea.ediprocess'
    _description = 'EDI Manual Handler Model'

    sftp_instance = fields.Many2one('setu.sftp', 'Instance', domain=[('instance_active', '=', True)])
    active = fields.Boolean('Active?', default=True)
    state = fields.Selection([('init', 'init'), ('done', 'done')],
                             string='State', readonly=True, default='init')
    notification = fields.Text()
    import_850 = fields.Boolean()
    export_855 = fields.Boolean()
    export_856 = fields.Boolean()
    export_810 = fields.Boolean()

    @api.model
    def default_get(self, fields):
        res = super(CaptiveaEdiProcess, self).default_get(fields)
        default_sftp = self.env['setu.sftp'].search([('default_instance', '=', True), ('instance_active', '=', True)])
        if default_sftp:
            res.update({
                'sftp_instance': default_sftp.id
            })
        return res

    def reload(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def get_display_notification(self, docs, doc_type):
        """
        Will return display notification based on document type.
        @param docs: total and failed docs.
        @param doc_type: transaction_id from 850 PO import.
        @return:
        """
        if type(docs) != str:
            total_doc, total_failed_doc = docs[0], docs[1]
            if total_failed_doc:
                names = " ,".join(total_failed_doc.mapped('name'))
            if not total_doc:
                if doc_type == '855':
                    self.notification = "No sale orders to be acknowledged."
                if doc_type == '856':
                    self.notification = "No delivery orders to be notified."
                if doc_type == '810':
                    self.notification = "No invoices to be notified."
            elif total_doc and not total_failed_doc:
                if doc_type == '855':
                    self.notification = "All sale orders are acknowledged."
                if doc_type == '856':
                    self.notification = "All delivery orders notified."
                if doc_type == '810':
                    self.notification = "All invoices notified."
            elif len(total_failed_doc) == len(total_doc) and total_failed_doc:
                if doc_type == '855':
                    self.notification = "Failed sending acknowledgement for all sale orders. " + names
                if doc_type == '856':
                    self.notification = "Failed sending notification for all delivery orders. " + names
                if doc_type == '810':
                    self.notification = "Failed sending notification for all invoices. " + names
            elif len(total_doc) != len(total_failed_doc) and total_failed_doc:
                if doc_type == '855':
                    self.notification = "Acknowledgements sent successfully but some of the acknowledgements could not be sent." \
                                        " Check these sale orders.  " + names
                if doc_type == '855':
                    self.notification = "Notifications sent successfully but some of notifications could not be sent." \
                                        " Check these delivery orders.  " + names
                if doc_type == '810':
                    self.notification = "Notifications sent successfully but some of notifications could not be sent." \
                                        " Check these invoices. " + names
        elif docs == 'no_connection':
            self.notification = "Invalid server details or Connection to server failed."

    def button_execute(self):

        if self.import_850:
            res = self.run_edi_process()
        else:
            res = {
                'name': _('EDI Process Completed'),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'captivea.ediprocess',
                'domain': [],
                'context': dict(self._context, active_ids=self.ids),
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': self.id,
            }
            if self.export_855:
                docs = self.manual_export_poack(self.sftp_instance)
                doc_type = '855'

            elif self.export_856:
                docs = self.manual_export_asn(self.sftp_instance)
                doc_type = '856'
            else:
                docs = self.manual_export_invn(self.sftp_instance)
                doc_type = '810'

            self.get_display_notification(docs, doc_type)

        return res

    def manual_export_poack(self, sftp):
        if sftp.instance_of == 'true':
            return self.manual_export_poack_true(sftp)
        if sftp.instance_of == 'ghx':
            return self.manual_export_poack_ghx(sftp)

    def manual_export_asn(self, sftp_conf):
        if sftp_conf.instance_of == 'true':
            return self.manual_export_asn_true(sftp_conf)
        else:
            return self.manual_export_asn_ghx(sftp_conf)

    def manual_export_invn(self, sftp_conf):
        """
        Manually export invoice notifications from wizard.
        @param sftp_conf: sftp instance
        @return:
        """
        invoices = self.env['account.move'].sudo().search(
            [('invn_sent', '=', False), ('sale_order_of', '=', sftp_conf.instance_of),
             ('company_id', '=', sftp_conf.company_id.id),
             ('partner_id.edi_810', '=', True),
             ('partner_id.x_edi_flag', '=', True),
             ('state', '=', 'posted')
             ])

        log_ids = invoices.create_and_export_invn()
        if log_ids:
            log_ids.log_created_from = 'manual'
        failed_inv_ids = invoices.filtered(lambda inv: inv.invn_sent != True)
        if not failed_inv_ids.edi_log_id.mapped('exception'):
            return invoices, failed_inv_ids
        else:
            return 'no_connection'

    def manual_export_asn_true(self, sftp_conf):
        """
        manually export shipping notifications from wizard.
        @param sftp_conf: sftp instance
        @return:
        """
        pickings = self.env['stock.picking'].sudo().search(
            [('asn_created', '=', False), ('sale_order_of', '=', 'true'),
             ('partner_id.edi_856', '=', True),
             ('partner_id.parent_id.x_edi_flag', '=', True),
             ('state', '=', 'done'),
             ('picking_type_id.code', '=', 'outgoing'),
             ('company_id', '=', sftp_conf.company_id.id)])
        bill_ship_picks_dict = {}
        for pick in pickings:
            bill_ship = str(pick.sale_id.partner_id.id) + ',' + str(pick.partner_id.id)
            if bill_ship in bill_ship_picks_dict.keys():
                bill_ship_picks_dict[bill_ship] |= pick
            else:
                bill_ship_picks_dict.update({
                    bill_ship: pick
                })

        log_ids = pickings.with_context(bill_ship_picks_dict=bill_ship_picks_dict).create_asn_log_and_asn_export()
        if log_ids:
            log_ids.log_created_from = 'manual'
        failed_asn_pickings = pickings.filtered(lambda pick: pick.asn_created != True)
        if not failed_asn_pickings.edi_log_ref.mapped('exception'):
            return pickings, failed_asn_pickings

        else:
            return 'no_connection'

    def manual_export_asn_ghx(self, sftp_conf):
        """
        manually export shipping notifications from wizard.
        @param sftp_conf: sftp instance
        @return:
        """
        pickings = self.env['stock.picking'].sudo().search(
            [('asn_created', '=', False), ('sale_order_of', '=', 'ghx'),
             ('partner_id.edi_856', '=', True),
             ('partner_id.parent_id.x_edi_flag', '=', True),
             ('state', '=', 'done'),
             ('picking_type_id.code', '=', 'outgoing'),
             ('company_id', '=', sftp_conf.company_id.id)])

        log_ids = pickings.create_asn_log_and_asn_export_ghx()
        if log_ids:
            log_ids.log_created_from = 'manual'
        failed_asn_pickings = pickings.filtered(lambda pick: pick.asn_created != True)
        if not failed_asn_pickings.edi_log_ref.mapped('exception'):
            return pickings, failed_asn_pickings

        else:
            return 'no_connection'

    def manual_export_poack_true(self, sftp_conf):
        """
        Manually export POACK from wizard.
        @param sftp_conf: sftp instance
        @return:
        """
        sales = self.env['sale.order'].sudo().search(
            [('poack_created', '!=', True), ('order_of', '=', 'true'),
             ('company_id', '=', sftp_conf.company_id.id),
             ('x_edi_accounting_id', '!=', False),
             ('partner_shipping_id.edi_855', '=', True),
             ('partner_id.x_edi_flag', '=', True),
             ('state', 'in', ['sale', 'done'])])
        log_ids = sales.with_context(manual_process=True).creat_poack_log_and_poack_export()
        if log_ids:
            log_ids.log_created_from = 'manual'
        failed_poack_sales = sales.filtered(lambda sale: sale.poack_created != True)
        if not failed_poack_sales.poack_ref.mapped('exception'):
            return sales, failed_poack_sales

        else:
            return 'no_connection'

    def manual_export_poack_ghx(self, sftp_conf):
        """
        Manually export POACK from wizard.
        @param sftp_conf: sftp instance
        @return:
        """
        sales = self.env['sale.order'].sudo().search(
            [('poack_created', '!=', True), ('order_of', '=', 'ghx'),
             ('company_id', '=', sftp_conf.company_id.id),
             ('x_edi_accounting_id', '!=', False),
             ('partner_shipping_id.edi_855', '=', True),
             ('partner_id.x_edi_flag', '=', True),
             ('state', 'in', ['sale', 'done'])])
        log_ids = sales.with_context(manual_process=True).creat_poack_log_and_poack_export()
        if log_ids:
            log_ids.log_created_from = 'manual'
        failed_poack_sales = sales.filtered(lambda sale: sale.poack_created != True)
        if not failed_poack_sales.poack_ref.mapped('exception'):
            return sales, failed_poack_sales

        else:
            return 'no_connection'

    @api.model
    def _write_edi_doclog(self, vals, log_id):
        """
        Create log lines.
        @param vals: log line vals dict.
        @param log_id: parent log id.
        @return:
        """
        try:
            doclog = self.env['captivea.edidocumentlog']
            log = doclog.sudo().create_and_add(vals, log_id)
            return log
        except:
            pass

    def _validate_order(self, vals):
        """
        850 Import validation.
        Decides weather create sale order or not.
        @param vals:
        @return:
        """
        """
        Function validate the request qty, product, customer, etc.
        :param vals:
        :return: status / validation msg
        """
        # Partner Validation

        if not self.env['res.partner'].sudo().search(
                [('x_edi_accounting_id', '=', vals['accounting_id']),
                 ('x_edi_flag', '=', True)]):
            validation_msg = "Failed! Customer does not exists."
        else:
            if not self.env['product.product'].sudo().search(
                    [('default_code', '=', vals['vendor_part_num'].strip())]):
                validation_msg = "Failed! Product does not exists."
            else:
                vals.update({
                    'log_type': 'success'
                })
                if not vals['store_number']:
                    validation_msg = "Success with Warning! There is no Store Number on the file, the default Delivery Address has been used"
                else:
                    validation_msg = "Pass"
        return validation_msg

    def _grab_ftp_files(self, sftp_conf):
        """
        This function check the connection and check for any new file if exist
        it will read and create log entry based on data. and if data is proper
        from log create funtion SO will also be created.
        :return:
        """
        file_ref = False
        all_failed_log_ids = self.env['setu.edi.log']
        all_success_log_ids = self.env['setu.edi.log']
        files_to_remove = list()
        ftpserver = sftp_conf['ftp_server']
        ftpport = sftp_conf['ftp_port']
        ftpuser = sftp_conf['ftp_user']
        ftpsecret = sftp_conf['ftp_secret']
        ftpgpath = sftp_conf['ftp_gpath']
        ftpdpath = sftp_conf['ftp_poack_dpath']
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        try:
            sftp = pysftp.Connection(host=ftpserver, username=ftpuser, password=ftpsecret, port=ftpport, cnopts=cnopts)
            if sftp:
                sftp.cwd(ftpgpath)
                directory_structure = sftp.listdir_attr()
                for attr in directory_structure:
                    try:
                        file_path = ftpgpath + '/' + attr.filename
                        file_ref = attr.filename
                        file_ref_with_time = attr.filename + str(datetime.now())
                        if sftp.isfile(file_path):
                            csvfile = sftp.open(file_path)
                            csvdata = csv.DictReader(csvfile)
                            log_id = False
                            log_ids = self.env['setu.edi.log']
                            for row in csvdata:  # Processing file begins here.
                                vals = {'create_date': datetime.now(),
                                        'transaction_id': row["TRANSACTION ID"].strip(),
                                        'accounting_id': row["ACCOUNTING ID"].strip(),
                                        'po_number': row["PURCHASE ORDER NUMBER"].strip(),
                                        'po_date': row["PO DATE"].strip(),
                                        'ship_to_name': row["SHIP TO NAME"].strip(),
                                        'ship_to_address_1': row["SHIP TO ADDRESS 1"].strip(),
                                        'ship_to_address_2': row["SHIP TO ADDRESS 2"].strip(),
                                        'ship_to_city': row["SHIP TO CITY"].strip(),
                                        'ship_to_state': row["SHIP TO STATE"].strip(),
                                        'ship_to_zip': row["SHIP TO ZIP"].strip(),
                                        'ship_to_country': row["SHIP TO COUNTRY"].strip(),
                                        'store_number': row["STORE NUMBER"].strip(),
                                        'bill_to_name': row["BILL TO NAME"].strip(),
                                        'bill_to_address_1': row["BILL TO ADDRESS 1"].strip(),
                                        'bill_to_address_2': row["BILL TO ADDRESS 2"].strip(),
                                        'bill_to_city': row["BILL TO CITY"].strip(),
                                        'bill_to_state': row["BILL TO STATE"].strip(),
                                        'bill_to_zip': row["BILL TO ZIP"].strip(),
                                        'bill_to_country': row["BILL TO COUNTRY"].strip(),
                                        'bill_to_code': row["BILL TO CODE"].strip(),
                                        'ship_via': row["SHIP VIA"].strip(),
                                        'ship_date': row["SHIP DATE"].strip(),
                                        'terms': row["TERMS"].strip(),
                                        'note': row["NOTE"].strip(),
                                        'department_number': row["DEPARTMENT NUMBER"].strip(),
                                        'cancel_date': row["CANCEL DATE"].strip(),
                                        'do_not_ship_before': row[
                                            "DO NOT SHIP BEFORE"].strip(),
                                        'do_not_ship_after': row["DO NOT SHIP AFTER"].strip(),
                                        'allowance_percent_1': row[
                                            "ALLOWANCE PERCENT 1"].strip(),
                                        'allowance_amount_1': row[
                                            "ALLOWANCE AMOUNT 1"].strip(),
                                        'allowance_percent_2': row[
                                            "ALLOWANCE PERCENT 2"].strip(),
                                        'allowance_amount_2': row[
                                            "ALLOWANCE AMOUNT 2"].strip(),
                                        'line_num': row["LINE #"].strip(),
                                        'vendor_part_num': row["VENDOR PART #"].strip(),
                                        'buyers_part_num': row["BUYERS PART #"].strip(),
                                        'upc_num': row["UPC #"].strip(),
                                        'description': row["DESCRIPTION"].strip(),
                                        'quantity': row["QUANTITY"].strip(),
                                        'uom': row["UOM"].strip(),
                                        'unit_price': row["UNIT PRICE"].strip(),
                                        'pack_size': row["PACK SIZE"].strip(),
                                        'num_of_inner_packs': row["# OF INNER PACKS"].strip(),
                                        'item_allowance_percent': row[
                                            "ITEM ALLOWANCE PERCENT"].strip(),
                                        'item_allowance_amount': row[
                                            "ITEM ALLOWANCE AMOUNT"].strip(),
                                        'state': "Testing",
                                        }
                                # DO VALIDATIONS
                                if not log_id or log_id and log_id.po_number != vals['po_number']:
                                    log_id = self.env['setu.edi.log'].create({
                                        'po_number': vals['po_number'],
                                        'type': 'import',
                                        'document_type': '850',
                                        'po_date': vals['po_date'],
                                        'file_ref': attr.filename,
                                        'log_created_from': 'manual',
                                        'company_id': sftp_conf.company_id.id
                                    })
                                log_ids |= log_id

                                STATE = self.env['captivea.ediprocess']._validate_order(vals)
                                vals['state'] = STATE
                                self.env['captivea.ediprocess']._write_edi_doclog(vals, log_id)
                                log_id._compute_log_status()

                            for log in log_ids:
                                if log.status == 'success':
                                    order = self.env['captivea.edidocumentlog']._create_sale_order(log,
                                                                                                   file_ref_with_time)
                                    if order:
                                        log.sale_id = order
                                        order.order_of = 'true'
                                    file_path = ftpgpath + '/' + attr.filename
                                    all_success_log_ids |= log
                                    if file_path not in files_to_remove:
                                        files_to_remove.append(file_path)
                                else:
                                    log.sale_id.unlink()
                                    all_failed_log_ids |= log
                    except Exception as e:
                        log_id = self.env['setu.edi.log'].create({
                            'po_number': False,
                            'type': 'import',
                            'document_type': '850',
                            'status': 'fail',
                            'log_created_from': 'manual',
                            'file_ref': file_ref,
                            'exception': 'Corrupt file or Invalid headers.'
                        })
                        all_failed_log_ids |= log_id
                        continue
                sftp.close()
            if files_to_remove:
                sftp = pysftp.Connection(host=ftpserver, username=ftpuser, password=ftpsecret, port=ftpport,
                                         cnopts=cnopts)
                if sftp:
                    for file_path in files_to_remove:
                        if sftp.isfile(file_path):
                            try:
                                sftp.remove(file_path)
                            except Exception as e:
                                continue
            return all_success_log_ids, all_failed_log_ids
        except Exception as e:
            log_id = self.env['setu.edi.log'].create({
                'po_number': False,
                'type': 'import',
                'document_type': '850',
                'status': 'fail',
                'log_created_from': 'manual',
            })
            if len(e.args) > 1:
                if e.args[1] == 22:
                    log_id.exception = 'Invalid Server Details or Connection Lost.'
            else:
                log_id.exception = e.args[0]
            return log_id, 'Fail'

    def run_edi_process(self):
        sftp = self.sftp_instance
        if sftp.instance_of == 'true':
            res = self._grab_ftp_files(sftp)
        else:
            res = self._grab_ghx_ftp_files(sftp)
        if res[1] != 'Fail':
            current_orders, failed_log_ids = res[0], res[1]
            if failed_log_ids:
                seq_list = failed_log_ids.mapped('seq')
                if False not in seq_list:
                    log_names = " ,".join(seq_list)
                else:
                    log_names = 'UNKNOWN'
            if current_orders and not failed_log_ids:
                self.notification = 'All files processed successfully.'
            elif current_orders and failed_log_ids:
                self.notification = 'Operation completed successfully but some of the files could not process. Please ' \
                                    'check log of ' + log_names
            elif failed_log_ids and not current_orders:
                self.notification = 'All files failed processing. Please check log of ' + log_names

            else:
                self.notification = 'No files found to process'
        else:
            self.notification = 'Server Connection Failed. Check latest log for that'
        return {
            'name': _('EDI Process Completed'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'captivea.ediprocess',
            'domain': [],
            'context': dict(self._context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    def edi_process_scheduler(self):
        sftp_confs = self.env['setu.sftp'].search([('instance_active', '=', True), ('enable_cron', '=', True)])
        true_sftp_confs = sftp_confs.filtered(lambda s: s.instance_of == 'true')
        ghx_sftp_confs = sftp_confs.filtered(lambda s: s.instance_of == 'ghx')
        for sftp_conf in true_sftp_confs:
            logs = self._grab_ftp_files(sftp_conf)
            if logs and logs[0] or logs and logs[1]:
                logs[0].log_created_from = 'scheduler'
                logs[1].log_created_from = 'scheduler'

            self._cr.commit()

            res = self.manual_export_poack_true(sftp_conf)
            if type(res) != str:
                sale_orders = res[0]
                if sale_orders:
                    sale_orders.poack_ref.log_created_from = 'scheduler'

            self._cr.commit()

            res = self.manual_export_asn_true(sftp_conf)
            if type(res) != str:
                picks = res[0]
                if picks:
                    picks.edi_log_ref.log_created_from = 'scheduler'

            self._cr.commit()

            res = self.manual_export_invn(sftp_conf)
            if type(res) != str:
                invoices = res[0]
                if invoices:
                    invoices.edi_log_id.log_created_from = 'scheduler'
        for sftp_conf in ghx_sftp_confs:
            logs = self._grab_ghx_ftp_files(sftp_conf)
            if logs and logs[0] or logs and logs[1]:
                logs[0].log_created_from = 'scheduler'
                logs[1].log_created_from = 'scheduler'

            self._cr.commit()

            res = self.manual_export_poack_ghx(sftp_conf)
            if type(res) != str:
                sale_orders = res[0]
                if sale_orders:
                    sale_orders.poack_ref.log_created_from = 'scheduler'

            self._cr.commit()

            res = self.manual_export_asn_ghx(sftp_conf)
            if type(res) != str:
                picks = res[0]
                if picks:
                    picks.edi_log_ref.log_created_from = 'scheduler'

            self._cr.commit()

            res = self.manual_export_invn(sftp_conf)
            if type(res) != str:
                invoices = res[0]
                if invoices:
                    invoices.edi_log_id.log_created_from = 'scheduler'
            self._cr.commit()

    def _grab_ghx_ftp_files(self, sftp_conf):
        file_ref = False
        all_failed_log_ids = self.env['setu.edi.log']
        all_success_log_ids = self.env['setu.edi.log']
        files_to_remove = list()
        ftpserver = sftp_conf['ftp_server']
        ftpport = sftp_conf['ftp_port']
        ftpuser = sftp_conf['ftp_user']
        ftpsecret = sftp_conf['ftp_secret']
        ftpgpath = sftp_conf['ftp_gpath']
        ftpdpath = sftp_conf['ftp_poack_dpath']
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        try:
            sftp = pysftp.Connection(host=ftpserver, username=ftpuser, password=ftpsecret, port=ftpport, cnopts=cnopts)
            if sftp:
                sftp.cwd(ftpgpath)
                directory_structure = sftp.listdir_attr()
                for attr in directory_structure:
                    file_status = True
                    try:
                        file_path = ftpgpath + '/' + attr.filename
                        file_ref = attr.filename
                        file_ref_with_time = attr.filename + str(datetime.now())
                        if sftp.isfile(file_path):
                            file = sftp.open(file_path)
                            # sftp.get(file_path, '/tmp/test.txt')
                            # csvdata = csv.DictReader(csvfile)
                            # file = open('/tmp/test.txt','r')
                            log_id = False
                            log_ids = self.env['setu.edi.log']
                            # txt_file = file.xreadlines()
                            txt_file = file.readlines()
                            lines = []
                            # lines = [x for x in txt_file]
                            for line in txt_file:
                                line = line.split('~')
                                for l in line:
                                    if '^' in l:
                                        lines.append(l)

                            row_count = 0
                            po_lines = {}
                            isa_id = False
                            headers = list(map(lambda x: x.replace('~', '').split('^')[0], lines))
                            sender_id = False
                            receiver_id = False
                            isa_id = False
                            ISA_ID = False
                            accounting_id = False
                            x_hdr_ref1 = False
                            x_hdr_ref2 = False
                            po_number = False
                            po_date = False
                            store_num = False
                            x_hdr_ref3 = False
                            x_hdr_ref4 = False
                            x_hdr_ref5 = False
                            vendor_id = False
                            vendor_ref = False
                            customer_number = False
                            for row in lines:  # Processing file begins here.
                                row_count += 1
                                fields = [field.strip() for field in row.replace('~', '').split('^')]

                                # GHX_GLOBAL.update({
                                #     row_count: {fields[0]: fields[1:]}
                                if len(fields) > 1:
                                    if fields[0] == 'ISA' or fields[0] == '\ufeffISA':
                                        sender_id = fields[6]
                                        receiver_id = fields[8]
                                        isa_id = fields[13]
                                    elif fields[0] == 'GS' and fields[1] == 'PO':
                                        accounting_id = fields[2]
                                    elif fields[0] == 'BEG' and fields[1] == '00':
                                        po_number = fields[3]
                                        po_date = fields[5]
                                        if len(po_date) != 8:
                                            po_date = False
                                    elif fields[0] == 'REF' and fields[1] == 'OQ':
                                        x_hdr_ref1 = fields[2]
                                    elif fields[0] == 'N1' and fields[1] == 'ST':
                                        customer_number = fields[4]
                                        store_num = fields[4]
                                        x_hdr_ref3 = fields[4]
                                    elif fields[0] == 'N1' and fields[1] == 'BT':
                                        x_hdr_ref4 = fields[4]
                                    elif fields[0] == 'N1' and fields[1] == 'SN':
                                        x_hdr_ref5 = fields[4]
                                    elif fields[0] == 'N1' and fields[1] == 'VN':
                                        if len(fields) == 3:
                                            vendor_id = receiver_id
                                            vendor_ref = fields[2]
                                        else:
                                            vendor_id = fields[4]
                                            vendor_ref = fields[2]
                                    elif fields[0] == 'AMT' and len(fields) > 3 and fields[1] == '1':
                                        x_hdr_ref2 = fields[3]
                                    elif fields[0] == 'IEA':
                                        ISA_ID = fields[2]
                                        if isa_id != ISA_ID:
                                            file_status = False
                                    elif fields[0] == 'PO1':
                                        if fields[1] and fields[1] not in po_lines.keys():
                                            po_lines.update({
                                                fields[1]: {
                                                    'qty': float(fields[2])
                                                    # 'uom': fields[3],
                                                    # 'unit_price': float(fields[4]),
                                                    # 'vendor_part': fields[7],
                                                    # 'buyer_part': fields[9]

                                                }
                                            })
                                            po_lines[fields[1]].update({
                                                'has_exceptions': False
                                            })
                                            if len(fields) > 3:
                                                po_lines[fields[1]].update({
                                                    'uom': fields[3]
                                                })
                                            if len(fields) > 4:
                                                po_lines[fields[1]].update({
                                                    'unit_price': float(fields[4])
                                                })
                                            if len(fields) > 7:
                                                product_seg = 7
                                                if fields[6] != 'VC':
                                                    product_seg = 9
                                                po_lines[fields[1]].update({
                                                    'vendor_part': fields[product_seg]
                                                })
                                            if len(fields) > 9:
                                                po_lines[fields[1]].update({
                                                    'buyer_part': fields[9]
                                                })

                                        else:
                                            file_status = False
                            log_id = self.env['setu.edi.log'].create({
                                'po_number': po_number,
                                'type': 'import',
                                'document_type': '850',
                                'po_date': po_date,
                                'file_ref': attr.filename,
                                'log_created_from': 'manual',
                                'company_id': sftp_conf.company_id.id
                            })
                            log_ids |= log_id
                            if po_lines and accounting_id and sender_id and receiver_id and store_num and po_number and file_status:
                                STATE = self._validate_gxh_file(po_lines, accounting_id, customer_number, sender_id,
                                                                receiver_id,
                                                                sftp_conf,
                                                                store_num)
                            else:
                                error_vals = []
                                if not po_lines:
                                    error_vals.append("PO Lines")
                                if not accounting_id:
                                    error_vals.append("Accounting ID")
                                if not receiver_id:
                                    error_vals.append("Receiver ID")
                                if not store_num:
                                    error_vals.append("Store Number")
                                if not po_number:
                                    error_vals.append("PO Number")

                                if error_vals and file_status:
                                    error_str = ", ".join(error_vals)
                                    if len(error_vals) == 1:
                                        error_str += " is"
                                    else:
                                        error_str += " are"
                                    STATE = error_str + " not available in EDI file."
                                else:
                                    STATE = 'Invalid Data in file'
                            if file_status and STATE == 'pass':
                                for line, product in po_lines.items():
                                    vals = {'create_date': datetime.now(),
                                            'x_hdr_ref1': x_hdr_ref1,
                                            'x_hdr_ref2': x_hdr_ref2,
                                            'accounting_id': accounting_id,
                                            'customer_number': customer_number,
                                            'po_number': po_number,
                                            'po_date': po_date,
                                            'store_number': store_num,
                                            'line_num': line,
                                            'vendor_part_num': product['vendor_part'],
                                            'buyers_part_num': 'buyer_part' in product and product['buyer_part'] or '',
                                            'quantity': product['qty'],
                                            'uom': product['uom'],
                                            'unit_price': product['unit_price'],
                                            'x_lin_ref1': product['unit_price'],
                                            'edi_log_id': log_id.id,
                                            'has_exceptions': product['has_exceptions']
                                            }
                                    self.env['captivea.edidocumentlog'].create(vals)
                                    log_id.x_hdr_ref1 = x_hdr_ref1

                                log_id.x_hdr_ref3 = x_hdr_ref3
                                log_id.x_hdr_ref4 = x_hdr_ref4
                                log_id.x_hdr_ref5 = x_hdr_ref5
                                log_id.vendor_id = vendor_id
                                log_id.vendor_ref = vendor_ref

                                order = self.env['captivea.edidocumentlog']._create_sale_order(log_id,
                                                                                               file_ref_with_time)
                                order.x_hdr_ref1 = x_hdr_ref1
                                order.order_of = 'ghx'
                                log_id.sale_id = order
                                file_path = ftpgpath + '/' + attr.filename
                                all_success_log_ids |= log_id
                                log_id.status = 'success'
                                if file_path not in files_to_remove:
                                    files_to_remove.append(file_path)
                            else:
                                log_id.status = 'fail'
                                log_id.exception = STATE
                                all_failed_log_ids |= log_id

                    except Exception as e:
                        log_id = self.env['setu.edi.log'].create({
                            'po_number': False,
                            'type': 'import',
                            'document_type': '850',
                            'status': 'fail',
                            'log_created_from': 'manual',
                            'file_ref': file_ref,
                            'exception': 'Corrupt file or Invalid headers.'
                        })
                        all_failed_log_ids |= log_id
                        continue
                sftp.close()
            if files_to_remove:
                sftp = pysftp.Connection(host=ftpserver, username=ftpuser, password=ftpsecret, port=ftpport,
                                         cnopts=cnopts)
                if sftp:
                    for file_path in files_to_remove:
                        if sftp.isfile(file_path):
                            try:
                                sftp.remove(file_path)
                            except Exception as e:
                                continue
            return all_success_log_ids, all_failed_log_ids
        except Exception as e:
            log_id = self.env['setu.edi.log'].create({
                'po_number': False,
                'type': 'import',
                'document_type': '850',
                'status': 'fail',
                'log_created_from': 'manual',
            })
            if len(e.args) > 1:
                if e.args[1] == 22:
                    log_id.exception = 'Invalid Server Details or Connection Lost.'
            else:
                log_id.exception = e.args[0]
            return log_id, 'Fail'

    def _get_partner(self, accounting_id):
        partner = self.env['res.partner'].search([('x_edi_accounting_id', '=', accounting_id)])
        if partner:
            return partner
        return 'No partner found for this accounting_id'

    def _validate_gxh_file(self, po_lines, accounting_id,
                           customer_number, sender_id,
                           receiver_id, sftp_conf,
                           store_num):
        if not (sender_id == sftp_conf.sender_id_850 and receiver_id == sftp_conf.receiver_id_850):
            return 'Sender ID or Receiver ID is invalid.'
        partner_id = self.env['res.partner'].sudo().search(
            [('x_edi_accounting_id', '=', accounting_id),
             ('edi_vendor_number', '=', customer_number)])

        if len(partner_id) > 1:
            partner_id = partner_id[0].commercial_partner_id

        if not partner_id:
            validation_error = 'Partner is not available.'
            return validation_error
        partner_uom_conf = False
        if partner_id:
            partner_uom_conf = self.env['customer.uom.conf'].search([('name', '=', partner_id.edi_vendor_number)],
                                                                    limit=1)

        for num, product in po_lines.items():
            if not self.env['product.product'].search(
                    [('default_code', '=', product['vendor_part'])]):
                # validation_error = 'Product(s) not available.'
                # return validation_error
                product['has_exceptions'] = True
            if product['uom'] and partner_uom_conf and not partner_uom_conf.line_ids.filtered(
                    lambda l: l.edi_uom.lower() == product['uom'].lower()):
                product['has_exceptions'] = True
            else:
                product['has_exceptions'] = True

        if not self.env['res.partner'].sudo().search(
                [('x_edi_store_number', '=', store_num)], limit=1):
            validation_error = 'Delivery Partner is not available.'
            return validation_error
        return 'pass'
