# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    activity_due_notification = fields.Boolean()
    ondue_date_notify = fields.Boolean()
    after_first_notify = fields.Boolean()
    after_second_notify = fields.Boolean()
    before_first_notify = fields.Boolean()
    before_second_notify = fields.Boolean()
    enter_after_first_notify = fields.Integer()
    enter_after_second_notify = fields.Integer()
    enter_before_first_notify = fields.Integer()
    enter_before_second_notify = fields.Integer()
    notify_create_user_due = fields.Boolean()
    notify_create_user_after_first = fields.Boolean()
    notify_create_user_after_second = fields.Boolean()
    notify_create_user_before_first = fields.Boolean()
    notify_create_user_before_second = fields.Boolean()
