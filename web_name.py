import ast
import base64
import csv
import glob
import itertools
import logging
import operator
import datetime
import hashlib
import os
import re
import simplejson
import time
import urllib
import urllib2
import urlparse
import xmlrpclib
import zlib
from xml.etree import ElementTree
from cStringIO import StringIO

import babel.messages.pofile
import werkzeug.utils
import werkzeug.wrappers
try:
    import xlwt
except ImportError:
    xlwt = None

import openerp
import openerp.modules.registry
from openerp.tools.translate import _
from openerp.tools import config

from .. import http
openerpweb = http

from openerp import pooler, sql_db

#----------------------------------------------------------
# OpenERP Web helpers
#-


class MyReports(openerpweb.Controller):
    _cp_path = "/web/report"
    POLLING_DELAY = 0.25
    TYPES_MAPPING = {
        'doc': 'application/vnd.ms-word',
        'html': 'text/html',
        'odt': 'application/vnd.oasis.opendocument.text',
        'pdf': 'application/pdf',
        'sxw': 'application/vnd.sun.xml.writer',
        'xls': 'application/vnd.ms-excel',
    }
@openerpweb.httprequest
def index(self, req, action, token):
        action = simplejson.loads(action)

        report_srv = req.session.proxy("report")
        context = dict(req.context)
        context.update(action["context"])

        report_data = {}
        report_ids = context["active_ids"]
        if 'report_type' in action:
            report_data['report_type'] = action['report_type']
        if 'datas' in action:
            if 'ids' in action['datas']:
                report_ids = action['datas'].pop('ids')
            report_data.update(action['datas'])

        report_id = report_srv.report(
            req.session._db, req.session._uid, req.session._password,
            action["report_name"], report_ids,
            report_data, context)

        report_struct = None
        while True:
            report_struct = report_srv.report_get(
                req.session._db, req.session._uid, req.session._password, report_id)
            if report_struct["state"]:
                break

            time.sleep(self.POLLING_DELAY)

        report = base64.b64decode(report_struct['result'])
        if report_struct.get('code') == 'zlib':
            report = zlib.decompress(report)
        report_mimetype = self.TYPES_MAPPING.get(
            report_struct['format'], 'octet-stream')
        file_name = action.get('name', 'report')
        if 'name' not in action:
            reports = req.session.model('ir.actions.report.xml')
            res_id = reports.search([('report_name', '=', action['report_name']),],
                                    0, False, False, context)
            if len(res_id) > 0:
                file_name = reports.read(res_id[0], ['name'], context)['name']
            else:
                file_name = action['report_name']
                
        # This is to get the reference name of the purchase order
        purchase_order_name = context["active_id"]
        purchase_uid = context["uid"]        
        if file_name == 'Purchase Order':
            dbname = req.session._db
            db = sql_db.db_connect(dbname) 
            cr = db.cursor()            
            pool =  pooler.get_pool(cr.dbname)
            purchase_order_obj = pool['purchase.order'].browse(cr,purchase_uid, purchase_order_name, context)            
            print purchase_order_obj.name
            sql_db.close_db(dbname)  
            file_name = dbname+'_'+purchase_order_obj.name 
       
        # This is to get the reference name of the request for quotation
        purchase_order_name = context["active_id"]
        purchase_uid = context["uid"]        
        if file_name == 'Request for Quotation':
            dbname = req.session._db
            db = sql_db.db_connect(dbname) 
            cr = db.cursor()            
            pool =  pooler.get_pool(cr.dbname)
            purchase_order_obj = pool['purchase.order'].browse(cr,purchase_uid, purchase_order_name, context)            
            print purchase_order_obj.name
            sql_db.close_db(dbname)  
            file_name = dbname+ purchase_order_obj.name 

        # This is to get the reference name of the sale quotation
        sale_order_name = context["active_id"]
        sale_uid = context["uid"]        
        if file_name == 'Quotation / Order':
            dbname = req.session._db
            db = sql_db.db_connect(dbname) 
            cr = db.cursor()            
            pool =  pooler.get_pool(cr.dbname)
            sale_order_obj = pool['sale.order'].browse(cr,sale_uid, sale_order_name, context)            
            so_name=sale_order_obj.name
            sql_db.close_db(dbname)  
            file_name = dbname+'_QO-'+ so_name[3:] 

        # This is to get the reference name of the sale quotation
        sale_order_name = context["active_id"]
        sale_uid = context["uid"]        
        if file_name == 'Sale Quotation':
            dbname = req.session._db
            db = sql_db.db_connect(dbname) 
            cr = db.cursor()            
            pool =  pooler.get_pool(cr.dbname)
            sale_order_obj = pool['sale.order'].browse(cr,sale_uid, sale_order_name, context)            
            print sale_order_obj.name
            sql_db.close_db(dbname)  
            file_name = dbname+'_'+sale_order_obj.name

        # This is to get the reference name of the sale quotation with logo
        sale_order_name = context["active_id"]
        sale_uid = context["uid"]        
        if file_name == 'Sale Quotation With Logo':
            dbname = req.session._db
            db = sql_db.db_connect(dbname) 
            cr = db.cursor()            
            pool =  pooler.get_pool(cr.dbname)
            sale_order_obj = pool['sale.order'].browse(cr,sale_uid, sale_order_name, context)            
            print sale_order_obj.name
            sql_db.close_db(dbname)  
            file_name = dbname+'_'+sale_order_obj.name 

        
        file_name = '%s.%s' % (file_name , report_struct['format'])

        return req.make_response(report,
             headers=[
                 ('Content-Disposition', content_disposition(file_name, req)),
                 ('Content-Type', report_mimetype),
                 ('Content-Length', len(report))],
             cookies={'fileToken': token})            

# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:
