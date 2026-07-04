from odoo import models, fields, api


class HrmsAttendance(models.Model):
    _name = 'hrms.attendance'
    _description = 'Employee Attendance'
    _order = 'check_in desc'

    STANDARD_HOURS = 8.0

    employee_id = fields.Many2one('hrms.employee', string='Employee', required=True, ondelete='cascade')
    check_in = fields.Datetime(string='Check In', required=True, default=fields.Datetime.now)
    check_out = fields.Datetime(string='Check Out')
    date = fields.Date(string='Date', compute='_compute_date', store=True)
    work_hours = fields.Float(string='Work Hours', compute='_compute_hours', store=True)
    extra_hours = fields.Float(string='Extra Hours', compute='_compute_hours', store=True)

    @api.depends('check_in')
    def _compute_date(self):
        for rec in self:
            rec.date = rec.check_in.date() if rec.check_in else False

    @api.depends('check_in', 'check_out')
    def _compute_hours(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                delta = rec.check_out - rec.check_in
                hours = delta.total_seconds() / 3600.0
                rec.work_hours = hours
                rec.extra_hours = max(hours - self.STANDARD_HOURS, 0.0)
            else:
                rec.work_hours = 0.0
                rec.extra_hours = 0.0