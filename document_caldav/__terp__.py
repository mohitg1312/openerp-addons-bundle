# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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


{
    'name': 'Support for caldav based on Document Management System',
    'version': '1.0',
    'category': 'Generic Modules/Others',
    'description': """Allows to synchronise calendars with others applications.""",
    'author': 'Tiny',
    'website': 'http://www.openerp.com',
    'depends': ['caldav','document_webdav', 'crm'],
    'init_xml': ['document_data.xml'],
    'update_xml': ['document_view.xml'],
    'demo_xml': ['document_demo.xml'],
    'installable': True,
    'active': False,
    'certificate': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
