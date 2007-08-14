# -*-encoding: iso8859-1 -*-
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

import sql_db
from osv.osv import osv_pools
from report.interface import report_rml
from tools.amount_to_text import amount_to_text


def toxml(val):
	return val.replace('&', '&amp;').replace('<','&lt;').replace('>','&gt;').decode('utf8').encode('iso-8859-1')

terms_dict = {
	'fr': {
		'retir�': 'retir�'
	},
	'nl': {
		'retir�': 'NLretir�NL'
	}
}

class report_custom(report_rml):
	def __init__(self, name, table, tmpl, xsl):
		report_rml.__init__(self, name, table, tmpl, xsl)

	def create_xml(self, uid, ids, datas, context={}):
		if len(ids) != 1:
			return ''

		cr = sql_db.db.cursor()
		tax_obj = osv_pools.get('account.tax')
		
		dossier_id = ids[0]
		dossier = osv_pools.get('huissier.dossier').browse(cr, uid, dossier_id)
		lots = dossier.lot_id
		lang = dossier.lang 
		terms = terms_dict[dossier.lang]
		context.update({'lang':lang})
		
		adj = dossier.amount_adj
		costs = dossier.amount_costs
		total = dossier.amount_total
		vat_num = dossier.debiteur and dossier.debiteur.vat or ''
		
		xml = '''<?xml version="1.0" encoding="iso-8859-1"?>
<report>
	<dossier>
		<lang>%s</lang>
		<amount_obj>%d</amount_obj>
		<amount_adj>%f</amount_adj>
		<amount_adj_letters>%s</amount_adj_letters>
		<percent_costs>%f</percent_costs>
		<amount_costs>%f</amount_costs>
		<amount_costs_letters>%s</amount_costs_letters>
		<amount_total>%f</amount_total>
		<amount_total_letters>%s</amount_total_letters>
		<vat_number>%s</vat_number>
	</dossier>''' % (
			lang,
			len(lots),
			adj,
			amount_to_text(adj, dossier.lang, 'euro'),
			dossier.cost_id.amount*100,
			costs,
			amount_to_text(costs, dossier.lang, 'euro'),
			total,
			amount_to_text(total, dossier.lang, 'euro'),
			vat_num)

		vats = {}
		i = 1
		for l in lots:
			vid = l.vat.id
			if not vid in vats:
				vats[vid] = {
					'value': l.vat.amount,
					'lots_numbers': str(i),
					'amount_adj': l.adj_price,
				}
			else:
				vats[vid]['lots_numbers'] += ','+str(i)
				vats[vid]['amount_adj'] += l.adj_price
			tax_res = tax_obj.compute(cr, uid, [vid], l.adj_price, 1)
			tax_amount = reduce(lambda x, y: x+y['amount'], tax_res, 0.0)
			vat6 = (l.vat.amount==0.06) and tax_amount or 0.0
			vat21 = (l.vat.amount==0.21) and tax_amount or 0.0
				
			if l.adj_price==0:
				price_letters = terms['retir�']
			else:
				price_letters = amount_to_text(l.adj_price, dossier.lang, 'euro')
			xml += '''	<object>
		<number>%d</number>
		<desc>%s</desc>
		<price_letters>%s</price_letters>
		<buyer_name>%s</buyer_name>
		<buyer_address>%s</buyer_address>
		<buyer_zip>%s</buyer_zip>
		<buyer_city>%s</buyer_city>
		<price>%f</price>
		<vat6>%f</vat6>
		<vat21>%f</vat21>
	</object>''' % (
				i,
				toxml(l.name or ''),
				price_letters,
				toxml(l.buyer_name or ''),
				toxml(l.buyer_address or ''),
				l.buyer_zip or '',
				toxml(l.buyer_city or ''),
				l.adj_price or 0.0,
				vat6,
				vat21)
				
			i+=1
			
		# use each list of object in turn
		for v in vats.itervalues():
			xml += '''	<vat>
		<procent>%f</procent>
		<lots_numbers>%s</lots_numbers>
		<amount_adj>%f</amount_adj>
		<amount_vat>%f</amount_vat>
	</vat>''' % (v['value']*100, v['lots_numbers'], v['amount_adj'], v['amount_adj']*v['value'])
			
		xml += '</report>'
		cr.close()
		
#		file('/tmp/terp.xml','wb+').write(xml)
		return xml

report_custom('report.huissier.pv', 'huissier.lots', '', 'addons/huissier/report/pv.xsl')


