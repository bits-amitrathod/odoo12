# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class InvoicePrintBankChequeWizard(models.TransientModel):
    _name = 'invoice.print.bank.cheque.wizard'
    _description = "Invoice Print Bank Cheque Wizard"

    @api.model
    def _get_partner_id(self):
        customer = False
        if self._context.get("active_id"):
            if self._context.get("active_model") == "account.invoice":
                active_obj = self.env["account.invoice"].browse(self._context.get("active_id"))
                customer = active_obj.partner_id.id
            if self._context.get("active_model") == "account.payment":
                active_obj = self.env["account.payment"].browse(
                    self._context.get("active_id"))
                customer = active_obj.partner_id.id
        return customer

    @api.model
    def _get_pay_name(self):
        customer_name = ""
        if self._context.get("active_id"):
            if self._context.get("active_model") == "account.invoice":
                active_obj = self.env["account.invoice"].browse(
                    self._context.get("active_id"))
                customer_name = active_obj.partner_id.name
            if self._context.get("active_model") == "account.payment":
                active_obj = self.env["account.payment"].browse(
                    self._context.get("active_id"))
                customer_name = active_obj.partner_id.name
        return customer_name

    @api.model
    def _get_currency(self):
        amount = self.env.user.company_id.currency_id.id
        if self._context.get("active_id"):
            if self._context.get("active_model") == "account.invoice":
                active_obj = self.env["account.invoice"].browse(
                    self._context.get("active_id"))
                amount = active_obj.currency_id.id
            if self._context.get("active_model") == "account.payment":
                active_obj = self.env["account.payment"].browse(
                    self._context.get("active_id"))
                amount = active_obj.currency_id.id
        return amount

    @api.model
    def _get_amount(self):
        amount = 0.0
        if self._context.get("active_id"):
            if self._context.get("active_model") == "account.invoice":
                active_obj = self.env["account.invoice"].browse(self._context.get("active_id"))
                amount = active_obj.amount_total
            if self._context.get("active_model") == "account.payment":
                active_obj = self.env["account.payment"].browse(
                    self._context.get("active_id"))
                amount = active_obj.amount
        return amount

    @api.model
    def _get_amount_in_words(self):
        amount_total_words = ""
        if self._context.get("active_id"):
            if self._context.get("active_model") == "account.invoice":
                active_obj = self.env["account.invoice"].browse(
                    self._context.get("active_id"))
                amount_total_words = active_obj.currency_id.amount_to_text(
                        active_obj.amount_total)
            if self._context.get("active_model") == "account.payment":
                active_obj = self.env["account.payment"].browse(
                    self._context.get("active_id"))
                amount_total_words = active_obj.currency_id.amount_to_text(
                    active_obj.amount)
        return amount_total_words

    name = fields.Char(related="partner_id.name", string="Name")
    partner_id = fields.Many2one("res.partner", "Customer", default=_get_partner_id)
    pay_name_line1 = fields.Char("Pay To", default=_get_pay_name)
    pay_name_line2 = fields.Char("Pay To Line2")
    currency_id = fields.Many2one("res.currency", default=_get_currency)
    amount = fields.Float("Amount", default=_get_amount)
    amount_in_words = fields.Char(
        "Amount In Words", default=_get_amount_in_words)
    amount_in_words_line2 = fields.Char("Amount In Words Line 2",)
    date = fields.Date("Date On Cheque", default=fields.Date.today())
    cheque_book_id = fields.Many2one("bank.cheque.book", "Cheque Book")
    cheque_history_id = fields.Many2one(
        "issued.bank.cheque.history", "Cheque Number", domain='[("issued", "=", False), ("state", "=", "cancelled")]')
    cheque_has_pay_line2 = fields.Boolean(compute="_check_cheque_attributes")
    cheque_has_amount_line2 = fields.Boolean(compute="_check_cheque_attributes")
    is_preview = fields.Boolean("Preview")

    @api.one
    @api.depends("cheque_book_id")
    def _check_cheque_attributes(self):
        if self.cheque_book_id:
            for bank_cheque_attr in self.cheque_book_id.bank_cheque_id.cheque_attribute_line_ids.filtered(lambda o: o.name.attribute in ['pay_line2', 'amount_line_2']):
                if bank_cheque_attr.name.attribute == "pay_line2":
                    self.cheque_has_pay_line2 = True
                if bank_cheque_attr.name.attribute == "amount_line_2":
                    self.cheque_has_amount_line2 = True

    @api.onchange("amount")
    def onchange_amount(self):
        if self.currency_id:
            self.amount_in_words_line2 = False
            self.amount_in_words = self.currency_id.amount_to_text(
                self.amount)
            self.set_amount_lines_in_word()

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id:
            self.pay_name_line1 = self.partner_id.name

    @api.onchange("cheque_book_id")
    def onchange_cheque_book_id(self):
        if self.cheque_book_id:
            self.onchange_amount()
            x = self.env["issued.bank.cheque.history"].search(
                [("bank_cheque_book_id", "=", self.cheque_book_id.id), ("issued", "=", False)], order="cheque_number asc", limit=1)
            if x:
                self.cheque_history_id = x.id
            return {
                'domain': {
                    'cheque_history_id': [('bank_cheque_book_id', '=', self.cheque_book_id.id)]
                }
            }
        return {}

    @api.multi
    def set_amount_lines_in_word(self):
        self.ensure_one()
        if self.amount_in_words:
            if self.cheque_book_id.bank_cheque_id.max_char_in_line1:
                # char_count = len(self.amount_in_words)
                raw_str = self.amount_in_words
                # max_char = self.cheque_book_id.max_char_in_line1
                line1 = ""
                line2 = ""
                total_word = 0
                for word in raw_str.split(" "):
                    if total_word + len(word) <= self.cheque_book_id.bank_cheque_id.max_char_in_line1:
                        total_word += len(word) + 1
                        line1 += word
                        line1 += " "
                    else:
                        line2 = raw_str[total_word:]
                        break
                self.amount_in_words = line1
                self.amount_in_words_line2 = line2
    @api.multi
    def print_cheque_preview(self):
        self.ensure_one()
        self.is_preview = True
        return self.env.ref('odoo_cheque_management.bank_cheque_leaf_print_report').report_action(self)

    @api.multi
    def print_cheque(self):
        self.ensure_one()
        self.is_preview = False
        if self.cheque_history_id.issued:
            raise UserError(_("Cheque has been already printed with Cheque number %s" %
                              self.cheque_history_id.cheque_number))
        self.cheque_history_id.write({
            "customer_id": self.partner_id.id if self.partner_id else False,
            "issue_date": fields.Date.today(),
            "amount": self.amount,
            "currency_id": self.currency_id.id,
            "issued": True,
            "paid_to": self.pay_name_line1,
            "state": "printed"
        })
        return self.env.ref('odoo_cheque_management.bank_cheque_leaf_print_report').report_action(self)
