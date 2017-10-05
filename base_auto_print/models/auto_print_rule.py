from odoo import models, fields, api
from odoo.addons.queue_job.job import job
from odoo.tools.safe_eval import safe_eval


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    domain_rule_ids = fields.One2many(
        comodel_name='printing.domain.rule',
        inverse_name='action_id',
        string='Automated Printing Rules',
    )

    @job
    @api.model
    def _print_document_automatically(self, report_name, records):
        report = self.sudo()._get_report_from_name(report_name)
        for record in records:
            record_domain = [('id', '=', record.id)]
            matched_rule = False
            for rule in report.domain_rule_ids:
                if record.search(record_domain +
                                 safe_eval(rule.filter_domain)):
                    matched_rule = rule
                    break
            sudo_uid = matched_rule.user_id.id if matched_rule else self._uid
            self.sudo(sudo_uid).print_document([record.id], report_name)
        return True

    @api.model
    def print_document_automatically(self, report_name, records, delay=True):
        if delay:
            self.with_delay()._print_document_automatically(
                report_name, records)
        else:
            self._print_document_automatically(report_name, records)


class PrintingDomainRule(models.Model):
    _name = 'printing.domain.rule'
    _order = 'sequence asc'

    action_id = fields.Many2one(
        comodel_name='ir.actions.report', required=True)
    user_id = fields.Many2one(
        comodel_name='res.users', required=True)
    sequence = fields.Integer(default=5, required=True)
    filter_domain = fields.Char(
        string='Apply on',
        default='[]',
        required=True,
        help="If present, this condition must be satisfied before "
             "executing the action rule.")
