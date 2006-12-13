##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################


from osv import osv, fields
import time

class account_v11(osv.osv):
	_name ='account.v11'
	_columns = {
		'name': fields.char('Date', size=64), # pe mettre une sequence
		'file': fields.binary('V11 file'),
		'state': fields.selection([('new','New'),         # completely new file
								   ('partial','Partial'), # file with unknown lines
								   ('error','Error'),     # file completely wrong
								   ('done','Done')],      # file ok even if some lines were ignored
								  'State',readonly= True),
		'note': fields.text('Import log'),
		}

	_defaults= {
		'name': lambda *a : time.strftime('%Y-%m-%d'),
		'state': lambda *a : 'new',
		}
account_v11()

