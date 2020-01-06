# coding: utf-8
# Part of CAPTIVEA. Odoo 12 EE.

from odoo import fields, models, api


class AccountAccount(models.Model):
	_inherit = 'account.invoice'
	
	date_invoice = fields.Date(readonly = false)
	
	