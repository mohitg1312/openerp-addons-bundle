# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

import wizard
import pooler
import time
import tools
import os

view_form_company = '''<?xml version="1.0"?>
<form string="Setup">
    <notebook colspan="4">
    <page string="General Information">
    <image name="gtk-dialog-info" colspan="2"/>
    <group>
        <separator string="Define Main Company" colspan="4"/>
        <newline/>
        <field name="name" align="0.0" colspan="4" required="True"/>
        <newline/>
        <field name="street" align="0.0"/>
        <field name="street2" align="0.0"/>
        <field name="zip" align="0.0"/>
        <field name="city" align="0.0"/>
        <field name="country_id" align="0.0"/>
        <field name="state_id" align="0.0"/>
        <field name="email" align="0.0"/>
        <field name="phone" align="0.0"/>
        <field name="currency" align="0.0"/>
    </group>
    </page>
    <page string="Report Information">
        <separator string="Report header" colspan="4"/>
        <newline/>
        <field name="rml_header1" align="0.0" colspan="4"/>
        <field name="rml_footer1" align="0.0" colspan="4"/>
        <field name="rml_footer2" align="0.0" colspan="4"/>
        <separator colspan="4" string="Your Logo - Use a size of about 450x150 pixels."/>
        <field colspan="4" name="logo" widget="image"/>
    </page>
    </notebook>
</form>'''

view_form_finish = '''<?xml version="1.0"?>
<form string="Setup">
    <image name="gtk-dialog-info" colspan="2"/>
    <group colspan="2" col="4">
        <separator colspan="4" string="Installation Done"/>
        <label align="0.0" colspan="4" string="Your new database is now fully installed."/>
        <label align="0.0" colspan="4" string="You can start configuring the system or connect directly to the database using the default setup."/>
    </group>
</form>
'''

class wizard_base_setup(wizard.interface):

    def _get_company(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        company_obj = pool.get('res.company')
        ids=company_obj.search(cr, uid, [])
        if not ids:
            return {}
        company = company_obj.browse(cr, uid, ids)[0]

        res = {'currency': company.currency_id.id}

        for field in 'name logo rml_header1 rml_footer1 rml_footer2'.split():
            res[field] = company[field]

        if company.partner_id.address:
            address = company.partner_id.address[0]
            for field in 'street street2 zip city email phone'.split():
                res[field] = address[field]

            for field in 'country_id state_id'.split():
                if address[field]:
                    res[field] = address[field].id

        return res

    def _get_all(self, cr, uid, context, model):
        pool = pooler.get_pool(cr.dbname)
        obj = pool.get(model)
        ids = obj.search(cr, uid, [])
        res = [(o.id, o.name) for o in obj.browse(cr, uid, ids, context=context)]
        res.append((-1, ''))
        res.sort(key=lambda x: x[1])
        return res

    def _get_states(self, cr, uid, context):
        return self._get_all(cr, uid, context, 'res.country.state')

    def _get_countries(self, cr, uid, context):
        return self._get_all(cr, uid, context, 'res.country')

    def _get_currency(self, cr, uid, context):
        return self._get_all(cr, uid, context, 'res.currency')

    def _update(self, cr, uid, data, context):
        pool=pooler.get_pool(cr.dbname)
        form=data['form']

        company_obj=pool.get('res.company')
        partner_obj=pool.get('res.partner')
        address_obj=pool.get('res.partner.address')
        ids=company_obj.search(cr, uid, [])
        company=company_obj.browse(cr, uid, ids)[0]
        company_obj.write(cr, uid, [company.id], {
                'name': form['name'],
                'rml_header1': form['rml_header1'],
                'rml_footer1': form['rml_footer1'],
                'rml_footer2': form['rml_footer2'],
                'currency_id': form['currency'],
                'logo': form['logo'],
            })
        partner_obj.write(cr, uid, [company.partner_id.id], {
                'name': form['name'],
            })
        values={
                    'name': form['name'],
                    'street': form['street'],
                    'street2': form['street2'],
                    'zip': form['zip'],
                    'city': form['city'],
                    'email': form['email'],
                    'phone': form['phone'],
                }
        # we can do this, or set res.append((False, '')) in _get_all()
        if form['country_id'] > 0:
            values['country_id'] = form['country_id']
        if form['state_id'] > 0:
            values['state_id'] = form['state_id']
        if company.partner_id.address:
            address=company.partner_id.address[0]
            address_obj.write(cr, uid, [address.id], values)
        else:
            values['partner_id']=company.partner_id.id
            add_id=address_obj.create(cr, uid, values)

        cr.commit()
        (db, pool)=pooler.restart_pool(cr.dbname, update_module=True)

        return {}

    def _menu(self, cr, uid, data, context):
        users_obj=pooler.get_pool(cr.dbname).get('res.users')
        action_obj=pooler.get_pool(cr.dbname).get('ir.actions.act_window')

        ids=action_obj.search(cr, uid, [('name', '=', 'Menu')])
        menu=action_obj.browse(cr, uid, ids)[0]

        ids=users_obj.search(cr, uid, [('action_id', '=', 'Setup')])
        users_obj.write(cr, uid, ids, {'action_id': menu.id})
        ids=users_obj.search(cr, uid, [('menu_id', '=', 'Setup')])
        users_obj.write(cr, uid, ids, {'menu_id': menu.id})

        return {
            'name': menu.name,
            'type': menu.type,
            'view_id': (menu.view_id and\
                    (menu.view_id.id, menu.view_id.name)) or False,
            'domain': menu.domain,
            'res_model': menu.res_model,
            'src_model': menu.src_model,
            'view_type': menu.view_type,
            'view_mode': menu.view_mode,
            'views': menu.views,
        }

    def _config(self, cr, uid, data, context=None):
        pool = pooler.get_pool(cr.dbname)
        users_obj=pool.get('res.users')
        action_obj=pool.get('ir.actions.act_window')

        ids=action_obj.search(cr, uid, [('name', '=', 'Menu')])
        menu=action_obj.browse(cr, uid, ids)[0]

        ids=users_obj.search(cr, uid, [('action_id', '=', 'Setup')])
        users_obj.write(cr, uid, ids, {'action_id': menu.id})
        ids=users_obj.search(cr, uid, [('menu_id', '=', 'Setup')])
        users_obj.write(cr, uid, ids, {'menu_id': menu.id})

        return pool.get('res.config').next(cr, uid, [], context=context)

    fields={
        'name':{
            'string': 'Company Name',
            'type': 'char',
            'size': 64,
        },
        'street':{
            'string': 'Street',
            'type': 'char',
            'size': 128,
        },
        'street2':{
            'string': 'Street2',
            'type': 'char',
            'size': 128,
        },
        'zip':{
            'string': 'Zip code',
            'type': 'char',
            'size': 24,
        },
        'city':{
            'string': 'City',
            'type': 'char',
            'size': 128,
        },
        'state_id':{
            'string': 'State',
            'type': 'selection',
            'selection':_get_states,
        },
        'country_id':{
            'string': 'Country',
            'type': 'selection',
            'selection':_get_countries,
        },
        'email':{
            'string': 'E-mail',
            'type': 'char',
            'size': 64,
        },
        'phone':{
            'string': 'Phone',
            'type': 'char',
            'size': 64,
        },
        'currency': {
            'string': 'Currency',
            'type': 'selection',
            'selection':_get_currency,
            'required': True,
        },
        'rml_header1':{
            'string': 'Report Header',
            'type': 'char',
            'help': """This sentence will appear at the top right corner of your reports.
We suggest you to put a slogan here:
"Open Source Business Solutions".""",
            'size': 200,
        },
        'rml_footer1':{
            'string': 'Report Footer 1',
            'type': 'char',
            'help': """This sentence will appear at the bottom of your reports.
We suggest you to write legal sentences here:
Web: http://openerp.com - Fax: +32.81.73.35.01 - Fortis Bank: 126-2013269-07""",
            'size': 200,
        },
        'rml_footer2':{
            'string': 'Report Footer 2',
            'help': """This sentence will appear at the bottom of your reports.
We suggest you to put bank information here:
IBAN: BE74 1262 0121 6907 - SWIFT: CPDF BE71 - VAT: BE0477.472.701""",
            'type': 'char',
            'size': 200,
        },
        'logo':{
            'string': 'Logo',
            'type': 'binary',
        },
    }
    states={
        'init':{
            'actions': [_get_company],
            'result': {'type': 'form', 'arch': view_form_company, 'fields': fields,
                'state': [
                    ('menu', 'Cancel', 'gtk-cancel'),
                    ('finish', 'Next', 'gtk-go-forward', True)
                ]
            }
        },
        'finish':{
            'actions': [_update],
            'result': {'type': 'form', 'arch': view_form_finish, 'fields': {},
                'state': [
                    ('menu', 'Use Directly', 'gtk-ok'),
                    ('config', 'Start Configuration', 'gtk-go-forward', True)
                ]
            }
        },
        'config': {
            'result': {
                'type': 'action',
                'action': _config,
                'state': 'end',
            },
        },
        'menu': {
            'actions': [],
            'result': {'type': 'action', 'action': _menu, 'state': 'end'}
        },
    }

wizard_base_setup('base_setup.base_setup')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

