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

from osv import osv, fields
from tools.translate import _
import pooler
import tools
import time
from document import nodes
import StringIO

class node_database(nodes.node_database):
    def _child_get(self, cr, name=False, parent_id=False, domain=None):
        dirobj = self.context._dirobj
        uid = self.context.uid
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        if not domain:
            domain = []
        domain2 = domain + [('calendar_collection','=', False)]
        res = super(node_database, self)._child_get(cr, name=name, parent_id=parent_id, domain=domain2)
        where = [('parent_id','=',parent_id)]
        domain2 = domain + [('calendar_collection','=', True)]
        if name:
            where.append(('name','=',name))
        if domain2:
            where += domain2

        where2 = where + [('type', '=', 'directory')]
        ids = dirobj.search(cr, uid, where2, context=ctx)
        for dirr in dirobj.browse(cr,uid,ids,context=ctx):
            res.append(node_calendar_collection(dirr.name,self,self.context,dirr))
        return res

class node_calendar_collection(nodes.node_dir):
    DAV_PROPS = {
            "http://calendarserver.org/ns/" : ('getctag',),
            }
    DAV_M_NS = {
           "http://calendarserver.org/ns/" : '_get_dav',
           }

    http_options = { 'DAV': ['calendar-access'] }

    def _file_get(self,cr, nodename=False):
        return []

    def _child_get(self, cr, name=False, parent_id=False, domain=None):
        dirobj = self.context._dirobj
        uid = self.context.uid
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        where = [('collection_id','=',self.dir_id)]
        ext = False
        if name and name.endswith('.ics'):
            name = name[:-4]
            ext = True
        if name:
            where.append(('name','=',name))
        if not domain:
            domain = []
        where = where + domain
        fil_obj = dirobj.pool.get('basic.calendar')
        ids = fil_obj.search(cr,uid,where,context=ctx)
        res = []
        for cal in fil_obj.browse(cr, uid, ids, context=ctx):
            if (not name) or not ext:
                res.append(node_calendar(cal.name, self, self.context, cal))
            if (not name) or ext:
                res.append(res_node_calendar(cal.name+'.ics', self, self.context, cal))
            # May be both of them!
        return res

    def _get_dav_owner(self, cr):
        # Todo?
        return False

    def _get_ttag(self, cr):
        return 'calen-dir-%d' % self.dir_id

    def _get_dav_getctag(self, cr):
        result = self.get_etag(cr)
        return str(result)

class node_calendar(nodes.node_class):
    our_type = 'collection'
    DAV_PROPS = {
            "DAV:": ('principal-collection-set'),
            "http://cal.me.com/_namespace/" : ('user-state'),
            "http://calendarserver.org/ns/" : (
                    'dropbox-home-URL',
                    'notification-URL',
                    'getctag',),
            'http://groupdav.org/': ('resourcetype',),
            "urn:ietf:params:xml:ns:caldav" : (
                    'calendar-description',
                    'calendar-data',
                    'calendar-home-set',
                    'calendar-user-address-set',
                    'schedule-inbox-URL',
                    'schedule-outbox-URL',)}
    DAV_M_NS = {
           "DAV:" : '_get_dav',
           "http://cal.me.com/_namespace/": '_get_dav', 
           'http://groupdav.org/': '_get_gdav',
           "http://calendarserver.org/ns/" : '_get_dav',
           "urn:ietf:params:xml:ns:caldav" : '_get_caldav'}

    http_options = { 'DAV': ['calendar-access'] }

    def __init__(self,path, parent, context, calendar):
        super(node_calendar,self).__init__(path, parent,context)
        self.calendar_id = calendar.id
        self.mimetype = 'application/x-directory'
        self.create_date = calendar.create_date
        self.write_date = calendar.write_date or calendar.create_date
        self.content_length = 0
        self.displayname = calendar.name
        self.cal_type = calendar.type

    def _get_dav_getctag(self, cr):
        result = self._get_ttag(cr) + ':' + str(time.time())
        return str(result)

    def _get_dav_dropbox_home_URL(self, cr):
        import xml.dom.minidom
        import urllib
        uid = self.context.uid
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        calendar_obj = self.context._dirobj.pool.get('basic.calendar')
        calendar = calendar_obj.browse(cr, uid, self.calendar_id, context=ctx)
        res = '%s/%s' %(calendar.collection_id.name, calendar.name)
        url = urllib.quote('/%s/%s' % (cr.dbname, res))
        return url
    
    def _get_dav_notification_URL(self, cr):
        import xml.dom.minidom
        import urllib
        uid = self.context.uid
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        calendar_obj = self.context._dirobj.pool.get('basic.calendar')
        calendar = calendar_obj.browse(cr, uid, self.calendar_id, context=ctx)
        res = '%s/%s' %(calendar.collection_id.name, calendar.name)
        url = urllib.quote('/%s/%s' % (cr.dbname, res))
        return url

    def _get_dav_user_state(self, cr):
        #TODO
        return True


    def get_dav_resourcetype(self, cr):
        res = [ ('collection', 'DAV:'),
                (str(self.cal_type + '-collection'), 'http://groupdav.org/'),
                ('calendar', 'urn:ietf:params:xml:ns:caldav') ]
        return res

    def get_domain(self, cr, filters):
        # TODO: doc.
        res = []
        if not filters:
            return res
        if filters.localName == 'calendar-query':
            res = []
            for filter_child in filters.childNodes:
                if filter_child.nodeType == filter_child.TEXT_NODE:
                    continue
                if filter_child.localName == 'filter':
                    for vcalendar_filter in filter_child.childNodes:
                        if vcalendar_filter.nodeType == vcalendar_filter.TEXT_NODE:
                            continue
                        if vcalendar_filter.localName == 'comp-filter':
                            if vcalendar_filter.getAttribute('name') == 'VCALENDAR':
                                for vevent_filter in vcalendar_filter.childNodes:
                                    if vevent_filter.nodeType == vevent_filter.TEXT_NODE:
                                        continue
                                    if vevent_filter.localName == 'comp-filter':
                                        if vevent_filter.getAttribute('name') == 'VEVENT':
                                            res = [('type','=','vevent')]
                                        if vevent_filter.getAttribute('name') == 'VTODO':
                                            res = [('type','=','vtodo')]
            return res
        elif filters.localName == 'calendar-multiget':
            names = []
            for filter_child in filters.childNodes:
                if filter_child.nodeType == filter_child.TEXT_NODE:
                    continue
                if filter_child.localName == 'href':
                    if not filter_child.firstChild:
                        continue
                    uri = filter_child.firstChild.data
                    caluri = uri.split('/')
                    if len(caluri):
                        caluri = caluri[-2]
                        if caluri not in names : names.append(caluri)
            res = [('name','in',names)]
            return res
        return res

    def children(self, cr, domain=None):
        return self._child_get(cr, domain=domain)

    def child(self,cr, name, domain=None):
        res = self._child_get(cr, name, domain=domain)
        if res:
            return res[0]
        return None


    def _child_get(self, cr, name=False, parent_id=False, domain=None):
        dirobj = self.context._dirobj
        uid = self.context.uid
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        where = []
        if name:
            if name.endswith('.ics'):
                name = name[:-4]
            try:
                where.append(('id','=',int(name)))
            except ValueError:
                # if somebody requests any other name than the ones we
                # generate (non-numeric), it just won't exist
                # FIXME: however, this confuses Evolution (at least), which
                # thinks the .ics node hadn't been saved.
                return []

        if not domain:
            domain = []

        fil_obj = dirobj.pool.get('basic.calendar')
        ids = fil_obj.search(cr, uid, domain)
        res = []
        if self.calendar_id in ids:
            res = fil_obj.get_calendar_objects(cr, uid, [self.calendar_id], self, domain=where, context=ctx)
        return res

    def create_child(self, cr, path, data):
        """ API function to create a child file object and node
            Return the node_* created
        """
        # we ignore the path, it will be re-generated automatically
        fil_obj = self.context._dirobj.pool.get('basic.calendar')
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        uid = self.context.uid

        res = self.set_data(cr, data)

        if res and len(res):
            # We arbitrarily construct only the first node of the data
            # that have been imported. ICS may have had more elements,
            # but only one node can be returned here.
            assert isinstance(res[0], (int, long))
            fnodes = fil_obj.get_calendar_objects(cr, uid, [self.calendar_id], self,
                    domain=[('id','=',res[0])], context=ctx)
            return fnodes[0]
        return None


    def set_data(self, cr, data, fil_obj = None):
        uid = self.context.uid
        calendar_obj = self.context._dirobj.pool.get('basic.calendar')
        res = calendar_obj.import_cal(cr, uid, data, self.calendar_id)
        return res

    def get_data_len(self, cr, fil_obj = None):
        return self.content_length

    def _get_ttag(self,cr):
        return 'calendar-%d' % (self.calendar_id,)

    def rmcol(self, cr):
        return False

    
    def _get_caldav_calendar_data(self, cr):
        res = []
        for child in self.children(cr):
            res.append(child._get_caldav_calendar_data(cr))
        return res

    def _get_caldav_calendar_description(self, cr):
        uid = self.context.uid
        calendar_obj = self.context._dirobj.pool.get('basic.calendar')
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        calendar = calendar_obj.browse(cr, uid, self.calendar_id, context=ctx)
        return calendar.description

    def _get_dav_principal_collection_set(self, uri):
        import urllib
        uid = self.context.uid
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        calendar_obj = self.context._dirobj.pool.get('basic.calendar')
        calendar = calendar_obj.browse(cr, uid, self.calendar_id, context=ctx)
        res = '%s/%s' %(calendar.collection_id.name, calendar.name)
        doc = xml.dom.minidom.getDOMImplementation().createDocument(None, 'href', None)
        href = doc.documentElement
        href.tagName = 'D:href'
        huri = doc.createTextNode(urllib.quote('/%s/%s' % (cr.dbname, res)))
        href.appendChild(huri)
        return href

    def _get_caldav_calendar_home_set(self, cr):
        import xml.dom.minidom
        import urllib
        uid = self.context.uid
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        doc = xml.dom.minidom.getDOMImplementation().createDocument(None, 'href', None)

        calendar_obj = self.context._dirobj.pool.get('basic.calendar')
        calendar = calendar_obj.browse(cr, uid, self.calendar_id, context=ctx)
        huri = doc.createTextNode(urllib.quote('/%s/%s' % (cr.dbname, calendar.collection_id.name)))
        href = doc.documentElement
        href.tagName = 'D:href'
        href.appendChild(huri)
        return href

    def _get_caldav_calendar_user_address_set(self, cr):
        import xml.dom.minidom
        dirobj = self.context._dirobj
        uid = self.context.uid
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        user_obj = self.context._dirobj.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=ctx)
        doc = xml.dom.minidom.getDOMImplementation().createDocument(None, 'href', None)
        href = doc.documentElement
        href.tagName = 'D:href'
        huri = doc.createTextNode('MAILTO:' + str(user.email) or str(user.name))
        href.appendChild(huri)
        return href

    def _get_caldav_schedule_outbox_URL(self, cr):
        return self._get_caldav_schedule_inbox_URL(cr)

    def _get_caldav_schedule_inbox_URL(self, cr):
        import xml.dom.minidom
        import urllib
        uid = self.context.uid
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        calendar_obj = self.context._dirobj.pool.get('basic.calendar')
        calendar = calendar_obj.browse(cr, uid, self.calendar_id, context=ctx)
        res = '%s/%s' %(calendar.collection_id.name, calendar.name)
        doc = xml.dom.minidom.getDOMImplementation().createDocument(None, 'href', None)
        href = doc.documentElement
        href.tagName = 'D:href'
        huri = doc.createTextNode(urllib.quote('/%s/%s' % (cr.dbname, res)))
        href.appendChild(huri)
        return href


class res_node_calendar(nodes.node_class):
    our_type = 'file'
    DAV_PROPS = {
            "http://calendarserver.org/ns/" : ('getctag'),
            "urn:ietf:params:xml:ns:caldav" : (
                    'calendar-description',
                    'calendar-data',
                    'calendar-home-set',
                    'calendar-user-address-set',
                    'schedule-inbox-URL',
                    'schedule-outbox-URL',)}
    DAV_M_NS = {
           "http://calendarserver.org/ns/" : '_get_dav',
           "urn:ietf:params:xml:ns:caldav" : '_get_caldav'}

    http_options = { 'DAV': ['calendar-access'] }

    def __init__(self,path, parent, context, res_obj, res_model=None, res_id=None):
        super(res_node_calendar,self).__init__(path, parent, context)
        self.mimetype = 'text/calendar'
        self.create_date = parent.create_date
        self.write_date = parent.write_date or parent.create_date
        self.calendar_id = hasattr(parent, 'calendar_id') and parent.calendar_id or False
        if res_obj:
            if not self.calendar_id: self.calendar_id = res_obj.id
            pr = res_obj.perm_read(context=context, details=False)[0]
            self.create_date = pr.get('create_date')
            self.write_date = pr.get('write_date') or pr.get('create_date')
            self.displayname = res_obj.name

        self.content_length = 0

        self.model = res_model
        self.res_id = res_id

    def open(self, cr, mode=False):
        uid = self.context.uid
        if self.type in ('collection','database'):
            return False
        s = StringIO.StringIO(self.get_data(cr))
        s.name = self
        return s

    def get_data(self, cr, fil_obj = None):
        uid = self.context.uid
        calendar_obj = self.context._dirobj.pool.get('basic.calendar')
        context = self.context.context.copy()
        context.update({'model': self.model, 'res_id':self.res_id})
        res = calendar_obj.export_cal(cr, uid, [self.calendar_id], context=context)
        return res
  
    def _get_caldav_calendar_data(self, cr):
        return self.get_data(cr)

    def get_data_len(self, cr, fil_obj = None):
        return self.content_length

    def set_data(self, cr, data, fil_obj = None):
        uid = self.context.uid
        calendar_obj = self.context._dirobj.pool.get('basic.calendar')
        res =  calendar_obj.import_cal(cr, uid, data, self.calendar_id)
        return res

    def _get_ttag(self,cr):
        res = False
        if self.model and self.res_id:
            res = '%s_%d' % (self.model, self.res_id)
        elif self.calendar_id:
            res = '%d' % (self.calendar_id)
        return res


    def rm(self, cr):
        uid = self.context.uid
        res = False
        if self.type in ('collection','database'):
            return False
        if self.model and self.res_id:
            document_obj = self.context._dirobj.pool.get(self.model)
            if document_obj:
                res =  document_obj.unlink(cr, uid, [self.res_id])

        return res

   

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4
