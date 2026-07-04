from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrmsEmployee(models.Model):
    _name = 'hrms.employee'
    _description = 'HRMS Employee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    # Basic Info
    name = fields.Char(string='Full Name', required=True, tracking=True)
    login_id = fields.Char(string='Login ID', copy=False, readonly=True, index=True)
    email = fields.Char(string='Email')
    mobile = fields.Char(string='Mobile')
    image_1920 = fields.Image(string='Profile Picture', max_width=1024, max_height=1024)

    # Org Info
    company_name = fields.Char(string='Company', default=lambda self: self.env.company.name)
    department = fields.Char(string='Department')
    manager_id = fields.Many2one('hrms.employee', string='Manager')
    location = fields.Char(string='Location')
    date_of_joining = fields.Date(string='Date of Joining', default=fields.Date.today)

    # Status
    status = fields.Selection([
        ('present', 'Present'),
        ('leave', 'On Leave'),
        ('absent', 'Absent'),
    ], string='Status', default='absent')

    # Profile content
    about = fields.Html(string='About')
    job_description = fields.Html(string='What I love about my job')
    interests_hobbies = fields.Html(string='My interests and hobbies')
    skill_ids = fields.Many2many('hrms.skill', string='Skills')
    certification_ids = fields.Many2many('hrms.certification', string='Certifications')

    # Private Info
    date_of_birth = fields.Date(string='Date of Birth')
    permanent_address = fields.Text(string='Permanent Address')
    nationality = fields.Char(string='Nationality')
    personal_email = fields.Char(string='Personal Email')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    marital_status = fields.Selection([
        ('single', 'Single'), ('married', 'Married'), ('other', 'Other')
    ])
    bank_details = fields.Char(string='Bank Details')
    aadhaar_no = fields.Char(string='Aadhaar Number')
    pan_no = fields.Char(string='PAN')
    uan_no = fields.Char(string='UAN')

    # Salary Info
    monthly_wage = fields.Float(string='Monthly Wage')
    yearly_wage = fields.Float(string='Yearly Wage', compute='_compute_yearly_wage', store=True)
    working_days_per_week = fields.Integer(string='Working Days per Week', default=5)
    break_time_hours = fields.Float(string='Break Time (hrs)', default=1.0)
    pf_employee_rate = fields.Float(string='PF Employee %', default=12.0)
    pf_employer_rate = fields.Float(string='PF Employer %', default=12.0)
    professional_tax = fields.Float(string='Professional Tax (Monthly)', default=200.0)
    salary_component_ids = fields.One2many('hrms.salary.component', 'employee_id', string='Salary Components')
    total_salary_components = fields.Float(string='Total of Components', compute='_compute_total_components')

    # Attendance
    attendance_ids = fields.One2many('hrms.attendance', 'employee_id', string='Attendance Records')
    is_checked_in = fields.Boolean(string='Checked In', compute='_compute_is_checked_in')
    last_check_in = fields.Datetime(string='Last Check In', compute='_compute_is_checked_in')

    # Leave / Time Off
    leave_ids = fields.One2many('hrms.leave', 'employee_id', string='Leave Requests')
    paid_leave_allocated = fields.Float(string='Paid Time Off Allocated', default=24.0)
    sick_leave_allocated = fields.Float(string='Sick Leave Allocated', default=7.0)
    paid_leave_taken = fields.Float(string='Paid Time Off Taken', compute='_compute_leave_balances')
    sick_leave_taken = fields.Float(string='Sick Leave Taken', compute='_compute_leave_balances')
    paid_leave_available = fields.Float(string='Paid Time Off Available', compute='_compute_leave_balances')
    sick_leave_available = fields.Float(string='Sick Leave Available', compute='_compute_leave_balances')

    # Linked Odoo user
    user_id = fields.Many2one('res.users', string='Related User')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('login_id'):
                vals['login_id'] = self._generate_login_id(vals)
        return super().create(vals_list)

    def _generate_login_id(self, vals):
        company = self.env.company
        company_code = ''.join([w[0] for w in (company.name or 'OI').split()])[:2].upper()

        full_name = vals.get('name', '')
        parts = full_name.strip().split()
        first = parts[0][:2].upper() if parts else 'XX'
        last = parts[-1][:2].upper() if len(parts) > 1 else 'XX'
        name_code = first + last

        joining_date = vals.get('date_of_joining') or fields.Date.today()
        if isinstance(joining_date, str):
            year = joining_date[:4]
        else:
            year = str(joining_date.year)

        count = self.search_count([
            ('date_of_joining', '>=', f'{year}-01-01'),
            ('date_of_joining', '<=', f'{year}-12-31'),
        ]) + 1
        serial = str(count).zfill(4)

        return f'{company_code}{name_code}{year}{serial}'

    @api.depends('monthly_wage')
    def _compute_yearly_wage(self):
        for emp in self:
            emp.yearly_wage = (emp.monthly_wage or 0.0) * 12

    @api.depends('salary_component_ids.computed_amount')
    def _compute_total_components(self):
        for emp in self:
            emp.total_salary_components = sum(emp.salary_component_ids.mapped('computed_amount'))

    @api.constrains('salary_component_ids', 'monthly_wage')
    def _check_components_not_exceed_wage(self):
        for emp in self:
            total = sum(emp.salary_component_ids.mapped('computed_amount'))
            if emp.monthly_wage and total > emp.monthly_wage + 0.01:
                raise ValidationError(
                    'Total of salary components (%.2f) cannot exceed the defined Wage (%.2f).'
                    % (total, emp.monthly_wage))

    @api.depends('attendance_ids.check_in', 'attendance_ids.check_out')
    def _compute_is_checked_in(self):
        for emp in self:
            open_att = emp.attendance_ids.filtered(lambda a: not a.check_out)
            emp.is_checked_in = bool(open_att)
            emp.last_check_in = open_att[0].check_in if open_att else False

    def action_check_in(self):
        self.ensure_one()
        if self.is_checked_in:
            return
        self.env['hrms.attendance'].create({
            'employee_id': self.id,
            'check_in': fields.Datetime.now(),
        })
        self.status = 'present'

    def action_check_out(self):
        self.ensure_one()
        open_att = self.attendance_ids.filtered(lambda a: not a.check_out)
        if open_att:
            open_att[0].check_out = fields.Datetime.now()

    @api.depends('leave_ids.state', 'leave_ids.number_of_days', 'leave_ids.leave_type',
                 'paid_leave_allocated', 'sick_leave_allocated')
    def _compute_leave_balances(self):
        for emp in self:
            approved = emp.leave_ids.filtered(lambda l: l.state == 'approved')
            paid_taken = sum(approved.filtered(lambda l: l.leave_type == 'paid').mapped('number_of_days'))
            sick_taken = sum(approved.filtered(lambda l: l.leave_type == 'sick').mapped('number_of_days'))
            emp.paid_leave_taken = paid_taken
            emp.sick_leave_taken = sick_taken
            emp.paid_leave_available = emp.paid_leave_allocated - paid_taken
            emp.sick_leave_available = emp.sick_leave_allocated - sick_taken


class HrmsSkill(models.Model):
    _name = 'hrms.skill'
    _description = 'Employee Skill'
    name = fields.Char(required=True)


class HrmsCertification(models.Model):
    _name = 'hrms.certification'
    _description = 'Employee Certification'
    name = fields.Char(required=True)


class HrmsSalaryComponent(models.Model):
    _name = 'hrms.salary.component'
    _description = 'Employee Salary Component'
    _order = 'sequence, id'

    employee_id = fields.Many2one('hrms.employee', string='Employee', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Selection([
        ('basic', 'Basic Salary'),
        ('hra', 'House Rent Allowance'),
        ('standard_allowance', 'Standard Allowance'),
        ('performance_bonus', 'Performance Bonus'),
        ('leave_travel_allowance', 'Leave Travel Allowance'),
        ('fixed_allowance', 'Fixed Allowance'),
    ], string='Component', required=True)
    computation_type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage of Wage'),
    ], string='Computation Type', default='percentage', required=True)
    percentage_of_basic = fields.Boolean(string='% of Basic (instead of Wage)')
    value = fields.Float(string='Value (% or Amount)', required=True)
    computed_amount = fields.Float(string='Monthly Amount', compute='_compute_amount', store=True)

    @api.depends('computation_type', 'value', 'percentage_of_basic',
                 'employee_id.monthly_wage', 'employee_id.salary_component_ids.computed_amount')
    def _compute_amount(self):
        for line in self:
            wage = line.employee_id.monthly_wage or 0.0
            if line.computation_type == 'fixed':
                line.computed_amount = line.value
            else:
                if line.percentage_of_basic:
                    basic_line = line.employee_id.salary_component_ids.filtered(
                        lambda l: l.name == 'basic' and l.id != line.id)
                    base = basic_line[0].computed_amount if basic_line else 0.0
                else:
                    base = wage
                line.computed_amount = base * (line.value / 100.0)