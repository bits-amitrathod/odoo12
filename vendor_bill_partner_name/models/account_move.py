
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import format_date,get_lang


class hide_state_code(models.Model):
    _inherit = 'res.country.state'

    #@api.multi
    def name_get(self):
        # super(hide_state_code,self).name_get()
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result


class AccountMoveVendorBill(models.Model):
    _inherit = "account.move"

    due_date_note = fields.Text(string="Due Dates", compute="due_date_note_cal")
    def create(self, vals_list):
        data = super(AccountMoveVendorBill, self).create(vals_list)
        if self.env.context.get('create_bill'):
            res_partner = data.partner_id
            for obj in res_partner:
                if obj.is_parent:
                    for child_id in obj.child_ids:
                        if child_id.type == "other":
                            data.partner_id = child_id.id
                else:
                    for child_id in obj.parent_id.child_ids:
                        if child_id.type == "other":
                            data.partner_id = child_id.id
        return data

    # TODO: UPG_ODOO16_NOTE line.option == ['day_current_month',day_after_invoice_date,day_before_invoice_date]
    # Line.option is Not Available in the parent , we need to find new Solutions
    @api.onchange('invoice_payment_term_id')
    @api.depends('invoice_payment_term_id')
    def due_date_note_cal(self):
        for rec in self:
            lista = list(rec.invoice_payment_term_id.line_ids)
            date_ref = rec.invoice_date or fields.Date.context_today(rec)
            rec.due_date_note = False
            due_str = ""
            # for line in lista:
            #     next_date = fields.Date.from_string(date_ref)
            #     if line.option == 'day_after_invoice_date':
            #         next_date += relativedelta(days=line.days)
            #         if line.day_of_the_month > 0:
            #             months_delta = (line.day_of_the_month < next_date.day) and 1 or 0
            #             next_date += relativedelta(day=line.day_of_the_month, months=months_delta)
            #     elif line.option == 'after_invoice_month':
            #         next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
            #         next_date = next_first_date + relativedelta(days=line.days - 1)
            #     elif line.option == 'day_following_month':
            #         next_date += relativedelta(day=line.days, months=1)
            #     elif line.option == 'day_current_month':
            #         next_date += relativedelta(day=line.days, months=0)
            #     due_str += "Due Date :- " + str(format_date(rec.env, next_date, date_format="MM/dd/yyyy")) + "\n"

            if due_str == "":
                rec.due_date_note = "Due Date :- " + str(
                    format_date(rec.env, rec.invoice_date_due, date_format="MM/dd/yyyy"))
            else:
                rec.due_date_note = due_str

    def action_invoice_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('vendor_bill_partner_name.email_template_edi_invoice_custom', raise_if_not_found=False)
        lang = False
        if template:
            lang = template._render_lang(self.ids)[self.id]
        if not lang:
            lang = get_lang(self.env).code
        compose_form = self.env.ref('account.account_invoice_send_wizard_form', raise_if_not_found=False)
        email_from = 'accounting@shopsps.com'
        ctx = dict(
            default_model='account.move',
            default_res_id=self.id,
            # For the sake of consistency we need a default_res_model if
            # default_res_id is set. Not renaming default_model as it can
            # create many side-effects.
            default_res_model='account.move',
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            custom_layout="mail.mail_notification_paynow",
            model_description=self.with_context(lang=lang).type_name,
            force_email=True,
            email_from=email_from
        )
        return {
            'name': _('Send Invoice'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.send',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

