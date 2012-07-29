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

import xml
import copy
from operator import itemgetter
import time
import datetime
from report import report_sxw
from tools import config
from tools.translate import _

class account_balance(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(account_balance, self).__init__(cr, uid, name, context)
        self.sum_debit = 0.00
        self.sum_credit = 0.00
        self.sum_balance = 0.00
        self.sum_debit_fy = 0.00
        self.sum_credit_fy = 0.00
        self.sum_balance_fy = 0.00
        self.date_lst = []
        self.date_lst_string = ''
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'get_fiscalyear_text': self.get_fiscalyear_text,
            'get_periods_and_date_text': self.get_periods_and_date_text,
            'get_informe_text': self.get_informe_text,
            'get_month':self.get_month,
            'exchange_name':self.exchange_name,
        })
        self.context = context


    def get_fiscalyear_text(self, form):
        """
        Returns the fiscal year text used on the report.
        """
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        fiscalyear = None
        if form.get('fiscalyear'):
            fiscalyear = fiscalyear_obj.browse(self.cr, self.uid, form['fiscalyear'])
            return fiscalyear.name or fiscalyear.code
        else:
            fiscalyear = fiscalyear_obj.browse(self.cr, self.uid, fiscalyear_obj.find(self.cr, self.uid))
            return "%s*" % (fiscalyear.name or fiscalyear.code)

    def get_informe_text(self, form):
        """
        Returns the header text used on the report.
        """
        inf_type = {
            'bgen' : '               Balance General',
            'bcom' : '       Balance de Comprobacion',            
            'edogp': 'Estado de Ganancias y Perdidas',
            'bml': 'Libro Mayor Legal',
            'bdl'  : 'Diario Legal'
        }
        return inf_type[form['inf_type']]

    def get_month(self, form):
        '''
        return day, year and month
        '''
        if form['filter'] in ['bydate', 'all']:
            months=["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
            mes = months[time.strptime(form['date_to'],"%Y-%m-%d")[1]-1]
            ano = time.strptime(form['date_to'],"%Y-%m-%d")[0]
            dia = time.strptime(form['date_to'],"%Y-%m-%d")[2]
            return 'Período del '+self.formatLang(form['date_from'], date=True)+' al '+self.formatLang(form['date_to'], date=True)
        elif form['filter'] in ['byperiod', 'all']:
            aux=[]
            period_obj = self.pool.get('account.period')
            
            for period in period_obj.browse(self.cr, self.uid, form['periods']):
                aux.append(period.date_start)
                aux.append(period.date_stop)
            sorted(aux)
            return _('Período del ')+self.formatLang(aux[0], date=True)+_(' al ')+self.formatLang(aux[-1], date=True)

    def get_periods_and_date_text(self, form):
        """
        Returns the text with the periods/dates used on the report.
        """
        period_obj = self.pool.get('account.period')
        periods_str = None
        fiscalyear_id = form['fiscalyear'] or fiscalyear_obj.find(self.cr, self.uid)
        period_ids = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear_id),('special','=',False)])
        if form['filter'] in ['byperiod', 'all']:
            period_ids = form['periods']
        periods_str = ', '.join([period.name or period.code for period in period_obj.browse(self.cr, self.uid, period_ids)])

        dates_str = None
        if form['filter'] in ['bydate', 'all']:
            dates_str = self.formatLang(form['date_from'], date=True) + ' - ' + self.formatLang(form['date_to'], date=True) + ' '
        return {'periods':periods_str, 'date':dates_str}


    def special_period(self, periods):
        period_obj = self.pool.get('account.period')
        period_brw = period_obj.browse(self.cr, self.uid, periods)
        period_counter = [True for i in period_brw if not i.special]
        if not period_counter:
            return True
        return False
        
    def exchange_name(self, form):
        self.from_currency_id = self.get_company_currency(form['company_id'] and type(form['company_id']) in (list,tuple) and form['company_id'][0] or form['company_id'])
        if not form['currency_id']:
            self.to_currency_id = self.from_currency_id
        else:
            self.to_currency_id = form['currency_id'] and type(form['currency_id']) in (list, tuple) and form['currency_id'][0] or form['currency_id']
        return self.pool.get('res.currency').browse(self.cr, self.uid, self.to_currency_id).name

    def exchange(self, from_amount):
        if self.from_currency_id == self.to_currency_id:
            return from_amount
        curr_obj = self.pool.get('res.currency')
        return curr_obj.compute(self.cr, self.uid, self.from_currency_id, self.to_currency_id, from_amount)
    
    def get_company_currency(self, company_id):
        rc_obj = self.pool.get('res.company')
        return rc_obj.browse(self.cr, self.uid, company_id).currency_id.id
    
    def get_company_credit_accounts(self, company_id):
        rc_obj = self.pool.get('res.company')
        return [brw.id for brw in rc_obj.browse(self.cr, self.uid, company_id).credit_account_ids]
    
    def lines(self, form, level=0):
        """
        Returns all the data needed for the report lines
        (account info plus debit/credit/balance in the selected period
        and the full year)
        """
        account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        
        self.from_currency_id = self.get_company_currency(form['company_id'] and type(form['company_id']) in (list,tuple) and form['company_id'][0] or form['company_id'])
        if not form['currency_id']:
            self.to_currency_id = self.from_currency_id
        else:
            self.to_currency_id = form['currency_id'] and type(form['currency_id']) in (list, tuple) and form['currency_id'][0] or form['currency_id']
        tot_check = False
        tot_bin = 0.0
        tot_deb = 0.0
        tot_crd = 0.0
        tot_eje = 0.0

        if form.has_key('account_list') and form['account_list']:
            account_ids = form['account_list']
            del form['account_list']
        
        credit_account_ids = self.get_company_credit_accounts(form['company_id'] and type(form['company_id']) in (list,tuple) and form['company_id'][0] or form['company_id'])

        print 'Primer print de credit_account_ids ', credit_account_ids
        
        res = {}
        result_acc = []

        if form.get('fiscalyear'):
            if type(form.get('fiscalyear')) in (list,tuple):
                fiscalyear = form['fiscalyear'] and form['fiscalyear'][0]
            elif type(form.get('fiscalyear')) in (int,):
                fiscalyear = form['fiscalyear']
        fiscalyear = fiscalyear_obj.browse(self.cr, self.uid, fiscalyear)

        #
        # Get the accounts
        #

        def _get_children_and_consol(cr, uid, ids, level, context={},change_sign=False):
            aa_obj = self.pool.get('account.account')
            ids2=[]
            for aa_brw in aa_obj.browse(cr, uid, ids, context):
                if aa_brw.child_id and aa_brw.level < level and aa_brw.type !='consolidation':
                    if not change_sign:
                        ids2.append([aa_brw.id,True, False,aa_brw])
                    ids2 += _get_children_and_consol(cr, uid, [x.id for x in aa_brw.child_id], level, context,change_sign=change_sign)
                    if change_sign:
                        ids2.append(aa_brw.id) 
                    else:
                        ids2.append([aa_brw.id,False,True,aa_brw])
                else:
                    if change_sign:
                        ids2.append(aa_brw.id) 
                    else:
                        ids2.append([aa_brw.id,True,True,aa_brw])
            return ids2

        account_ids = _get_children_and_consol(self.cr, self.uid, account_ids, form['display_account_level'] and form['display_account_level'] or 100,self.context)
        
        credit_account_ids = _get_children_and_consol(self.cr, self.uid, credit_account_ids, 100,self.context,change_sign=True)
        
        print 'credit_account_ids ', credit_account_ids
        
        account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')
        fiscalyear_obj = self.pool.get('account.fiscalyear')

        #############################################################################
        # Calculate the period Debit/Credit                                         #
        # (from the selected period or all the non special periods in the fy)       #
        #############################################################################
        def _ctx_end(ctx):
            ctx_end = ctx
            ctx_end['filter'] = form.get('filter','all')
            ctx_end['fiscalyear'] = fiscalyear.id
            #~ ctx_end['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('special','=',False)])
            
            if ctx_end['filter'] not in ['bydate','none']:
                special = self.special_period(form['periods'])
            else:
                special = False
            
            if form['filter'] in ['byperiod', 'all']:
                if special:
                    ctx_end['periods'] = period_obj.search(self.cr, self.uid, [('id','in',form['periods'] or ctx_end.get('periods',False))])
                else:
                    ctx_end['periods'] = period_obj.search(self.cr, self.uid, [('id','in',form['periods'] or ctx_end.get('periods',False)),('special','=',False)])
                    
            if form['filter'] in ['bydate','all','none']:
                ctx_end['date_from'] = form['date_from']
                ctx_end['date_to'] = form['date_to']
            
            return ctx_end.copy()
        
        def missing_period():
            ctx_init['fiscalyear'] = fiscalyear_obj.search(self.cr, self.uid, [('date_stop','<',fiscalyear.date_start)],order='date_stop') and \
                                fiscalyear_obj.search(self.cr, self.uid, [('date_stop','<',fiscalyear.date_start)],order='date_stop')[-1] or []
            ctx_init['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',ctx_init['fiscalyear']),('date_stop','<',fiscalyear.date_start)])
        
        #############################################################################
        # Calculate the period initial Balance                                      #
        # (fy balance minus the balance from the start of the selected period       #
        #  to the end of the year)                                                  #
        #############################################################################
        
        def _ctx_init(ctx):
            ctx_init = self.context.copy()
            ctx_init['filter'] = form.get('filter','all')
            ctx_init['fiscalyear'] = fiscalyear.id

            if form['filter'] in ['byperiod', 'all']:
                ctx_init['periods'] = form['periods']
                date_start = min([period.date_start for period in period_obj.browse(self.cr, self.uid, ctx_init['periods'])])
                ctx_init['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('date_stop','<=',date_start)])
                if not ctx_init['periods']:
                    missing_period()
            elif form['filter'] in ['bydate']:
                ctx_init['date_from'] = fiscalyear.date_start
                ctx_init['date_to'] = form['date_from']
                ctx_init['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('date_stop','<=',ctx_init['date_to'])])
            elif form['filter'] == 'none':
                ctx_init['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('special','=',True)])
                date_start = min([period.date_start for period in period_obj.browse(self.cr, self.uid, ctx_init['periods'])])
                ctx_init['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('date_start','<=',date_start),('special','=',True)])
            
            return ctx_init.copy()
            
        def z(n):
            return abs(n) < 0.005 and 0.0 or n
                
        #
        # Generate the report lines (checking each account)
        #
        tot = {}        
        
        ctx_init = _ctx_init(self.context.copy())
        ctx_end = _ctx_end(self.context.copy())
        
        for aa_id in account_ids:
            id = aa_id[0]

            #
            # Check if we need to include this level
            #
            if not form['display_account_level'] or account['level'] <= form['display_account_level']:
                res = {
                'id'        : id,
                'type'      : aa_id[3].type,
                'code'      : aa_id[3].code,
                'name'      : (aa_id[2] and not aa_id[1]) and 'TOTAL %s'%(aa_id[3].name.upper()) or aa_id[3].name,
                'parent_id' : aa_id[3].parent_id and aa_id[3].parent_id.id,
                'level'     : aa_id[3].level,
                'label'     : aa_id[1],
                'total'     : aa_id[2],
                'change_sign' : credit_account_ids and (id  in credit_account_ids and -1 or 1) or 1
                }
                
                if form['columns'] != 'thirteen':

                    aa_brw_init = account_obj.browse(self.cr, self.uid, id, ctx_init)
                    aa_brw_end  = account_obj.browse(self.cr, self.uid, id, ctx_end)

                    i,d,c = map(z,[aa_brw_init.balance,aa_brw_end.debit,aa_brw_end.credit])
                    b = z(i+d-c)
                    res.update({
                        'balanceinit': self.exchange(i),
                        'debit': self.exchange(d),
                        'credit': self.exchange(c),
                        'balance': self.exchange(b),
                    })
                
                if form['columns'] == 'thirteen':
                    period_ids = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('special','=',False)],order='date_start asc')
                    print 'TODOS LOS PERIODS ',period_ids
                    pass
                    for i in range(12):
                        pass
                    
                    
                #
                # Check whether we must include this line in the report or not
                #

                if form['display_account'] == 'mov' and aa_id[3].parent_id:
                    # Include accounts with movements
                    if abs(d) >= 0.005 or abs(c) >= 0.005:
                        result_acc.append(res)
                elif form['display_account'] == 'bal' and aa_id[3].parent_id:
                    # Include accounts with balance
                    if abs(b) >= 0.005:
                        result_acc.append(res)
                elif form['display_account'] == 'bal_mov' and aa_id[3].parent_id:
                    # Include accounts with balance or movements
                    if abs(b) >= 0.005 or abs(d) >= 0.005 or abs(c) >= 0.005:
                        result_acc.append(res)
                else:
                    # Include all accounts
                    result_acc.append(res)
                if form['tot_check'] and res['type'] == 'view' and res['level'] == 1 and (res['id'] not in tot):
                    tot_check = True
                    tot[res['id']] = True
                    tot_bin += res['balanceinit']
                    tot_deb += res['debit']
                    tot_crd += res['credit']
                    tot_eje += res['balance']

        #if (form['tot_check'] and res['type']=='view' and res['level']==1 and (res['id'] not in tot)):
        if tot_check:
            str_label = form['lab_str']
            res2 = {
                    'type' : 'view',
                    'name': 'TOTAL %s'%(str_label),
                    'balanceinit': tot_bin,
                    'debit': tot_deb,
                    'credit': tot_crd,
                    'balance': tot_eje,
                    'label': False,
                    'total': True,
            }
            result_acc.append(res2)
        return result_acc

report_sxw.report_sxw('report.afr.1cols', 
                      'wizard.report', 
                      'account_financial_report/report/balance_full.rml',
                       parser=account_balance, 
                       header=False)

report_sxw.report_sxw('report.afr.2cols', 
                      'wizard.report', 
                      'account_financial_report/report/balance_full_2_cols.rml',
                       parser=account_balance, 
                       header=False)

report_sxw.report_sxw('report.afr.4cols', 
                      'wizard.report', 
                      'account_financial_report/report/balance_full_4_cols.rml',
                       parser=account_balance, 
                       header=False)
