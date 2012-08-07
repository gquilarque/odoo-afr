# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
###############Credits######################################################
#    Coded by:   Humberto Arocha humberto@openerp.com.ve
#                Angelica Barrios angelicaisabelb@gmail.com
#               Jordi Esteve <jesteve@zikzakmedia.com>
#               Javier Duran <javieredm@gmail.com>
#    Planified by: Humberto Arocha
#    Finance by: LUBCAN COL S.A.S http://www.lubcancol.com
#    Audited by: Humberto Arocha humberto@openerp.com.ve
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

from osv import osv,fields
import pooler
import time
from tools.translate import _

class account_financial_report(osv.osv):
    _name = "afr"

    _columns = {
        'name': fields.char('Name', size= 128, required=True),
        'company_id': fields.many2one('res.company','Company',required=True),
        'currency_id': fields.many2one('res.currency', 'Currency', help="Currency at which this report will be expressed. If not selected will be used the one set in the company"),
        'inf_type': fields.selection([('BS','Balance Sheet'),('IS','Income Statement')],'Type',required=True),
        'columns': fields.selection([('one','End. Balance'),('two','Debit | Credit'), ('four','Initial | Debit | Credit | YTD'), ('five','Initial | Debit | Credit | Period | YTD'),('qtr',"4 QTR's | YTD"), ('thirteen','12 Months | YTD')],'Columns',required=True),
        'display_account': fields.selection([('all','All Accounts'),('bal', 'With Balance'),('mov','With movements'),('bal_mov','With Balance / Movements')],'Display accounts'),
        'display_account_level': fields.integer('Up to level',help='Display accounts up to this level (0 to show all)'),
        'account_ids': fields.many2many ('account.account','afr_account_rel','afr_id','account_id','Root accounts',required=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear','Fiscal year',help='Fiscal Year for this report',required=True),
        'period_ids': fields.many2many('account.period','afr_period_rel','afr_id','period_id','Periods',help='All periods in the fiscal year if empty'),
        
        'tot_check': fields.boolean('Summarize?', help='Checking will add a new line at the end of the Report which will Summarize Columns in Report'),
        'lab_str': fields.char('Description', help='Description for the Summary', size= 128),
        
        #~ Deprecated fields
        'filter': fields.selection([('bydate','By Date'),('byperiod','By Period'),('all','By Date and Period'),('none','No Filter')],'Date/Period Filter'),
        'date_to': fields.date('End date'),
        'date_from': fields.date('Start date'),
    }
    
    _defaults = {
        'display_account_level': lambda *a: 0,
        'inf_type': lambda *a:'BS',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
        'fiscalyear_id': lambda self, cr, uid, c: self.pool.get('account.fiscalyear').find(cr, uid),
        'display_account': lambda *a:'bal_mov',
        'columns': lambda *a:'five',
        
        'date_from': lambda *a: time.strftime('%Y-%m-%d'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'filter': lambda *a:'byperiod',
    }
    
    def copy(self, cr, uid, id, defaults, context=None):
        if context is None:
            context = {}
        previous_name = self.browse(cr, uid, id, context=context).name
        new_name = _('Copy of %s')%previous_name
        lst = self.search(cr, uid, [('name','like',new_name)], context=context)
        if lst:
            new_name = '%s (%s)' % (new_name, len(lst)+1)
        defaults['name'] = new_name
        return super(account_financial_report,self).copy(cr, uid, id, defaults, context=context)

account_financial_report()
