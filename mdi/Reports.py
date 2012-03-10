#-*-coding=utf-8-*-

import os, sys
from PyQt4 import QtCore, QtGui, QtSql, QtWebKit
from helpers import tableFormat
from db import AttrDict
from helpers import makeHeaders
from helpers import dateDelim
from helpers import HeaderUtil
from helpers import humanable_bytes
from ebsWindow import ebsTableWindow
from ebsWindow import ebsTabs_n_TablesWindow
import itertools
from itertools import count, izip
import datetime
import socket 
from reports.bpreportedit import bpReportEdit
import thread
import time
from customwidget import CustomDateTimeWidget
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s
strftimeFormat = "%d.%m.%Y %H:%M:%S"
#TODO: заменить сообщение о пустой выборке пустой картинкой
_xmlpath = "reports/xml"
reppath  = "reports/genhtml"

_querydict = {\
              "get_nas"      : "SELECT name, type, ipaddress, id FROM nas_nas ORDER BY name;", \
	      "get_usernames": "SELECT username, id FROM billservice_account ORDER BY username;", \
              "get_classes"  : "SELECT name, weight, id FROM nas_trafficclass ORDER BY name;", \
              "get_groups"   : "SELECT name, id FROM billservice_group ORDER BY name;"}

_chartopts = {\
             "gstat_multi"  : [("portsTab",'groupsTab'), ('ggb_groups_checkBox',), {}],\
             "pie_gmulti"  : [("portsTab",'groupsTab'),('ggb_groups_checkBox',), {'pie':True}],\
             "gstat_globals"  : [("portsTab","classesTab", 'groupsTab'),('ggb_groups_checkBox','ggb_classes_checkBox'), {'ttype':'stat'}],\
             "groups"  : [("portsTab","classesTab", "serversTab"),('ggb_classes_checkBox', 'ggb_nas_checkBox','traffic_groupBox'), {'ttype':'group'}],\
             "sessions" : [("serversTab", "classesTab", "portsTab", 'groupsTab'), ('traffic_groupBox', 'data_groupBox', 'groupby_groupBox'), {}],\
             "trans_deb" : [("usersTab", "serversTab", "classesTab", "portsTab", 'groupsTab'), ('traffic_groupBox', 'data_groupBox', 'groupby_groupBox'), {'trtype':'deb'}],\
             "trans_crd" : [("usersTab", "serversTab", "classesTab", "portsTab", 'groupsTab'), ('traffic_groupBox', 'data_groupBox', 'groupby_groupBox'), {'trtype':'crd'}]
            }

_ports = [(25, "SMTP"), (53, "DNS"), (80, "HTTP"), (110, "POP3"), (143, "IMAP"), (443, "HTTPS"), (1080, "SOCKS"), (3128, "Web Cache"), (3306, "MySQL"), (3724, "WoW"), (5190, "ICQ"), (5222, "Jabber"), (5432, "Postgres"), (8080, "HTTP Proxy")]


class SelMunObrMolel(QtCore.QAbstractListModel):
    
    def __init__(self, parent):
        super(SelMunObrMolel, self).__init__(parent)
        self.objects = []
        
    def flags(self, index):
        ret = super(SelMunObrMolel, self).flags(index)
        
        if ret != QtCore.Qt.ItemFlags():
          return ret | QtCore.Qt.ItemIsUserCheckable
    
    def rowCount(self,e):

        return len(self.objects)
    
    def data (self, index, role):
        return self.objects[index.row()][0]
    
    def get_selected(self):
        res = []
        for item in self.objects:
            if item[2]==2:
                res.append(item[1])
                
        return res
    
    def data(self,index,role):
        if not index.isValid: return QtCore.QVariant()
        myname, internal_name, mystate = self.objects[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(myname)
        if role == QtCore.Qt.CheckStateRole:
            if mystate == 0:
                return QtCore.QVariant(QtCore.Qt.Unchecked)
            elif mystate == 1:
                return QtCore.QVariant(QtCore.Qt.PartiallyChecked)
            elif mystate == 2:
                return QtCore.QVariant(QtCore.Qt.Checked)
        return QtCore.QVariant()

    
    def setData(self,index,value,role=QtCore.Qt.EditRole):
        if index.isValid():
            if index.row()==0 and self.objects[0][1]=='all':
                for x in xrange(len(self.objects)):
                    self.objects[x][2] = value.toInt()[0]     
                self.emit(QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                          index, index)
                return True
            self.objects[index.row()][2] = value.toInt()[0]            
            self.emit(QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                      index, index)
            #print self.objects
            return True
        return False

    def flags(self,index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEditable
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable |     QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsTristate


class TransactionsReportEbs(ebsTableWindow):
    def __init__(self, connection,account=None, parent=None, cassa=False):
        self.account = account
        self.cassa=cassa
        columns=[u'#', u'Аккаунт', u"ФИО", u'Дата', u'Платёжный документ', u'Вид проводки', u"Выполнено", u'Тариф', u'Сумма', u'Комментарий', u"В долг", u"До числа"]
        initargs = {"setname":"transrep_frame_header", "objname":"TransactionReportEbsMDI", "winsize":(0,0,903,483), "wintitle":"История операций над лицевым счётом пользователя", "tablecolumns":columns}
        self.transactions_types = []#[u"Периодические услуги", u"Разовые услуги", u"За трафик", u"За время", u"Подключаемые услуги", u"Платежи QIWI"]
        self.transactions_types={
        "PS_GRADUAL":"billservice_periodicalservicehistory",
        "PS_AT_END":"billservice_periodicalservicehistory",
        "PS_AT_START":"billservice_periodicalservicehistory",
        "TIME_ACCESS":"billservice_timeaccesstransaction",
        "NETFLOW_BILL":"billservice_traffictransaction",
        "END_PS_MONEY_RESET":"billservice_transaction",
        "MANUAL_TRANSACTION":"billservice_transaction",
        "ACTIVATION_CARD":"billservice_transaction",
        "ONETIME_SERVICE":"billservice_onetimeservicehistory",
        "OSMP_BILL":"billservice_transaction",
        "ADDONSERVICE_WYTE_PAY":"billservice_billservice",
        "ADDONSERVICE_PERIODICAL_GRADUAL":"billservice_addonservicetransaction",
        "ADDONSERVICE_PERIODICAL_AT_START":"billservice_addonservicetransaction",
        "ADDONSERVICE_PERIODICAL_AT_END":"billservice_addonservicetransaction",
        "ADDONSERVICE_ONETIME":"billservice_onetimeservicehistory",
        "PAY_CARD":"billservice_transaction",
        "CASSA_TRANSACTION":"billservice_transaction",
        "PAYMENTGATEWAY_BILL":"billservice_transaction",
        "WEBMONEY_PAYMENT_IMPORT":"webmoney_payment",
        "QIWI_PAYMENT":"qiwi_invoice",
        "TOTAL_TRANSACTIONS":"totaltransactions"
        }
        
        #self.transactions_tables = [u"billservice_periodicalservicehistory",u"billservice_onetimeservicehistory",u"billservice_traffictransaction",u"billservice_timetransaction","billservice_addonservicetransaction", "qiwi_invoice"]
        super(TransactionsReportEbs, self).__init__(connection, initargs, parent)
        
    def ebsInterInit(self, initargs):
        self.user_edit = QtGui.QComboBox(self)
        self.user_edit.setGeometry(QtCore.QRect(100,12,201,20))
        self.user_edit.setObjectName("user_edit")    
        
        dt_now = datetime.datetime.now()
        
        self.date_start = CustomDateTimeWidget()
        #self.date_start.setGeometry(QtCore.QRect(420,9,161,20))
        #self.date_start.setCalendarPopup(True)
        self.date_start.setObjectName("date_start")
        #self.date_start.calendarWidget().setFirstDayOfWeek(QtCore.Qt.Monday)

        self.date_end = CustomDateTimeWidget()
        #self.date_end.setGeometry(QtCore.QRect(420,42,161,20))
        self.date_end.setDate(QtCore.QDate(dt_now.year, dt_now.month, dt_now.day))
        #self.date_end.setButtonSymbols(QtGui.QAbstractSpinBox.PlusMinus)
        #self.date_end.setCalendarPopup(True)
        self.date_end.setObjectName("date_end")
        #self.date_end.calendarWidget().setFirstDayOfWeek(QtCore.Qt.Monday)
        
        try:
            settings = QtCore.QSettings("Expert Billing", "Expert Billing Client")
            self.date_start.setDateTime(settings.value("trans_date_start", QtCore.QVariant(QtCore.QDateTime(2000,1,1,0,0))).toDateTime())
            self.date_end.setDateTime(settings.value("trans_date_end", QtCore.QVariant(QtCore.QDateTime(2000,1,1,0,0))).toDateTime())
        except Exception, ex:
            print "Transactions settings error: ", ex

        self.date_start_label = QtGui.QLabel(self)
        self.date_start_label.setMargin(10)
        self.date_start_label.setObjectName("date_start_label")

        self.date_end_label = QtGui.QLabel(self)
        self.date_end_label.setMargin(10)
        self.date_end_label.setObjectName("date_end_label")

        self.user_label = QtGui.QLabel(self)
        self.user_label.setMargin(10)
        self.user_label.setObjectName("user_label")

        self.label_transactions_type = QtGui.QLabel(self)
        self.label_transactions_type.setMargin(10)

        self.label_cashier = QtGui.QLabel(self)
        self.label_cashier.setMargin(10)
           
        self.comboBox_transactions_type = QtGui.QComboBox(self)
        self.comboBox_cashier = QtGui.QComboBox(self)
        
        
        self.go_pushButton = QtGui.QPushButton(self)
        self.go_pushButton.setGeometry(QtCore.QRect(590,40,101,25))
        self.go_pushButton.setObjectName("go_pushButton")        
        #self.system_transactions_checkbox = QtGui.QCheckBox(self)
        #self.system_transactions_checkbox.setObjectName("system_transactions_checkbox")

        self.toolBar = QtGui.QToolBar(self)      
        
        self.toolBar.addWidget(self.user_label)
        self.toolBar.addWidget(self.user_edit)
        
        self.toolBar.addWidget(self.label_transactions_type)
        self.toolBar.addWidget(self.comboBox_transactions_type)
        self.toolBar.addWidget(self.label_cashier)
        self.toolBar.addWidget(self.comboBox_cashier)
        self.toolBar.addWidget(self.date_start_label)
        self.toolBar.addWidget(self.date_start)
        self.toolBar.addWidget(self.date_end_label)
        self.toolBar.addWidget(self.date_end)
        #self.toolBar.addWidget(self.system_transactions_checkbox)
        self.toolBar.addWidget(self.go_pushButton)
        self.toolBar.addSeparator()        
        
        self.toolBar.setMovable(False)
        self.toolBar.setFloatable(False)
        self.addToolBar(QtCore.Qt.TopToolBarArea,self.toolBar)
        self.columns = {}

        self.columns["billservice_periodicalservicehistory"]=['#', u'Аккаунт', u"ФИО", u'Тарифный план', u'Услуга', u'Тип', u"Сумма", u"Дата"]
        self.columns["billservice_onetimeservicehistory"]=['#', u'Аккаунт', u"ФИО", u'Тарифный план', u'Услуга', u'Тип', u"Сумма", u"Дата"]
        self.columns["billservice_traffictransaction"] = ["#", u'Аккаунт', u"ФИО", u'Тарифный план', u'Сумма', u'Дата']
        self.columns["billservice_timetransaction"] = ["#", u'Аккаунт', u"ФИО", u'Тарифный план', u'Сумма', u'Дата']
        self.columns["totaltransactions"] = ["#", u'Аккаунт', u"ФИО", u'Тарифный план', u'Тип списания', u'Услуга/Документ', u'Сумма', u'Дата', u"Описание", u"Обещанный платёж", u"Кассир"]
        self.columns["billservice_addonservicetransaction"] = ["#", u'Аккаунт', u"ФИО", u'Услуга', u'Тип услуги', u'Сумма', u'Дата']
        self.columns["billservice_transaction"] = [u'#', u'Аккаунт', u"ФИО", u'Дата', u'Платёжный документ', u'Вид проводки', u"Выполнено", u'Тариф', u'Сумма', u'Комментарий', u"В долг", u"До числа"]
        self.columns["qiwi_invoice"] = [u'#', u'Аккаунт', u"ФИО", u"№ инвойса", u'Создан', u"Автозачисление", u'Оплачен', u"Сумма"]
        self.columns["webmoney_payment"] = [u'#', u'Аккаунт', u"ФИО", u"№ инвойса", u'Создан', u"Автозачисление", u'Оплачен', u"Сумма"]
       
    def ebsPostInit(self, initargs):
        self.tableWidget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.tableWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        QtCore.QObject.connect(self.go_pushButton,QtCore.SIGNAL("clicked()"),self.refresh_table)
        QtCore.QObject.connect(self.comboBox_transactions_type,QtCore.SIGNAL("currentIndexChanged(int)"),self.setTableColumns)
        
        actList=[("actionDeleteTransaction", "Отменить проводку", "images/del.png", self.delete_transaction),]
        objDict = {self.tableWidget:["actionDeleteTransaction", ]}
        if not self.cassa:
            self.actionCreator(actList, objDict)
        self.setTableColumns()
        
    def retranslateUI(self, initargs):
        super(TransactionsReportEbs, self).retranslateUI(initargs)
        self.date_start_label.setText(QtGui.QApplication.translate("Dialog", "С", None, QtGui.QApplication.UnicodeUTF8))
        self.date_end_label.setText(QtGui.QApplication.translate("Dialog", "По", None, QtGui.QApplication.UnicodeUTF8))
        self.user_label.setText(QtGui.QApplication.translate("Dialog", "Пользователь", None, QtGui.QApplication.UnicodeUTF8))
        self.go_pushButton.setText(QtGui.QApplication.translate("Dialog", "Показать", None, QtGui.QApplication.UnicodeUTF8))
        self.date_end.setDisplayFormat(QtGui.QApplication.translate("Dialog", self.datetimeFormat, None, QtGui.QApplication.UnicodeUTF8))
        self.date_start.setDisplayFormat(QtGui.QApplication.translate("Dialog", self.datetimeFormat, None, QtGui.QApplication.UnicodeUTF8))
        #self.system_transactions_checkbox.setText(QtGui.QApplication.translate("Dialog", "Включить в отчёт системные проводки", None, QtGui.QApplication.UnicodeUTF8))        
        self.label_transactions_type.setText(QtGui.QApplication.translate("Dialog", "Тип", None, QtGui.QApplication.UnicodeUTF8))
        self.label_cashier.setText(QtGui.QApplication.translate("Dialog", "Кассир", None, QtGui.QApplication.UnicodeUTF8))
    
    def refresh(self):
        systemusers = self.connection.get_systemusers()
        self.connection.commit()
        self.comboBox_cashier.addItem(unicode(u'--Все--'))
        self.comboBox_cashier.setItemData(0, QtCore.QVariant(None))
        

        i=1
        for systemuser in systemusers:
           self.comboBox_cashier.addItem(unicode(systemuser.username))
           self.comboBox_cashier.setItemData(i, QtCore.QVariant(systemuser.id))
           i+=1
           
        accounts = self.connection.get_account(fields=['id', 'username'])
        self.connection.commit()
        self.user_edit.addItem(u"-Все клиенты-")
        self.user_edit.setItemData(0, QtCore.QVariant(None))
        i=1
        for account in accounts:
            self.user_edit.addItem(account.username)
            self.user_edit.setItemData(i, QtCore.QVariant(account.id))
            i+=1
        
        if self.account:
            self.user_edit.setCurrentIndex(self.user_edit.findText(self.account.username, QtCore.Qt.MatchCaseSensitive))
            self.setWindowTitle(u"История операций над лицевым счётом пользователя %s" % self.account.username)


        items = self.connection.get_transactiontypes()
        self.connection.commit()
        
        sm=SelMunObrMolel(self)
        self.comboBox_transactions_type.setModel(sm)
        #self.comboBox_transactions_type.addItem(u"Общий отчёт", QtCore.QVariant("TOTAL_TRANSACTIONS"))
        i=1
        sm.objects.append([u'Все', 'all',  0])
        for item in items:
            sm.objects.append([item.name, item.internal_name,  0])
            #self.transactions_tables.insert(0, "billservice_transaction")
            #self.comboBox_transactions_type.addItem(item.name, QtCore.QVariant(item.internal_name))
            #if item.internal_name==u'MANUAL_TRANSACTION':
            #    self.comboBox_transactions_type.setCurrentIndex(i)
            i+=1 
            
        #for tr_type in self.transactions_types:
        #    self.comboBox_transactions_type.addItem(tr_type,QtCore.QVariant(i))
            
    def addrow(self, value, x, y, id=None, promise=False, date = None, table=None):
        headerItem = QtGui.QTableWidgetItem()
        if value==None:
            value=""
        if y==1:
            headerItem.setIcon(QtGui.QIcon("images/user.png"))
        
        if promise:
            headerItem.setBackgroundColor(QtGui.QColor("lightblue"))
            
        if isinstance(value, basestring):            
            headerItem.setText(unicode(value))     
        elif type(value)==datetime.datetime:
            #.strftime(self.strftimeFormat)   

            headerItem.setData(QtCore.Qt.DisplayRole, QtCore.QDateTime(value))      
 
        else:            
            headerItem.setData(0, QtCore.QVariant(float(value))) 
            
        if id:
            headerItem.id = id
            headerItem.date = date
            headerItem.table = table
        self.tableWidget.setItem(x,y,headerItem)
             
    def setTableColumns(self):
        self.tableWidget.clear()
        self.tableWidget.setRowCount(0)
        makeHeaders(self.columns[self.transactions_types.get(unicode(self.comboBox_transactions_type.itemData(self.comboBox_transactions_type.currentIndex()).toString())) or "billservice_transaction"], self.tableWidget)   
           
    def refresh_table(self):

        self.tableWidget.setSortingEnabled(False)
        self.setWindowTitle(u"История операций над лицевым счётом пользователя %s" % unicode(self.user_edit.currentText()))
        self.tableWidget.clearContents()
        start_date = self.date_start.currentDate()
        end_date = self.date_end.currentDate()

        account_id = self.user_edit.itemData(self.user_edit.currentIndex()).toInt()[0]
        print 'self.comboBox_transactions_type.model().get_selected()', self.comboBox_transactions_type.model().get_selected()
        transaction_type=unicode(self.comboBox_transactions_type.itemData(self.comboBox_transactions_type.currentIndex()).toString())
        #print transaction_type
        self.statusBar().showMessage(u"Выполняется обработка запроса. Подождите.")
        if self.transactions_types.get(transaction_type, None) in ["billservice_transaction",None]:
            sql = """SELECT transaction.*, transactiontype.name as transaction_type_name, tariff.name as tariff_name, (SELECT username FROM billservice_account WHERE id=transaction.account_id) as username, (SELECT fullname FROM billservice_account WHERE id=transaction.account_id) as fullname, (SELECT username FROM billservice_systemuser WHERE id=transaction.systemuser_id) as systemuser
                                            FROM billservice_transaction as transaction
                                            JOIN billservice_transactiontype as transactiontype ON transactiontype.internal_name = transaction.type_id
                                            LEFT JOIN billservice_tariff as tariff ON tariff.id = transaction.tarif_id   
                                            WHERE transaction.created between '%s' and '%s' %%s and transaction.type_id='%s' ORDER BY transaction.created DESC""" %  (start_date, end_date,transaction_type)

            if account_id:
                sql = sql % " and transaction.account_id=%s %%s" % account_id
            else:
                sql = sql % " %s"

            systemuser_id = self.comboBox_cashier.itemData(self.comboBox_cashier.currentIndex()).toInt()[0]
            #print sql
            if systemuser_id!=0:
                sql = sql % " and transaction.systemuser_id=%s " % systemuser_id
            else:
                sql = sql % " "

            items = self.connection.sql(sql)
            self.connection.commit()
            self.tableWidget.setRowCount(len(items))
            i=0
            sum = 0
            for item in items:
                self.addrow(i, i, 0, id=item.id, promise = item.promise, date = item.created, table="billservice_transaction")
                self.addrow(item.username, i, 1, promise = item.promise)
                self.addrow(item.fullname, i, 2, promise = item.promise)
                self.addrow(item.created, i, 3, promise = item.promise)
                self.addrow(item.bill, i, 4, promise = item.promise)
                self.addrow(item.transaction_type_name, i, 5, promise = item.promise)
                self.addrow(item.systemuser, i, 6, promise = item.promise)
                self.addrow(item.tariff_name, i, 7, promise = item.promise)
                self.addrow(item.summ*(-1), i, 8, promise = item.promise)
                self.addrow(item.description, i, 9, promise = item.promise)
                self.addrow(item.promise, i, 10, promise = item.promise)
                sum+=float(item.summ)*(-1)
                if item.promise:
                    try:
                        self.addrow(item.end_promise.strftime(self.strftimeFormat), i, 11, promise = item.promise)
                    except Exception, e:
                        print e
                i+=1
            self.statusBar().showMessage(u"Всего записей:%s. Итоговая сумма %.3f" % (i,sum))
        if self.transactions_types.get(transaction_type)=="billservice_periodicalservicehistory":
            services = self.connection.get_models("billservice_periodicalservice")
            s = {}
            for x in services:
                s[x.id] = x.name

            tariffs = self.connection.get_models("billservice_tariff")
            t = {}
            for x in tariffs:
                t[x.id] = x.name
                               
            sql = """
            SELECT psh.id, psh.service_id, psh.created, psh.accounttarif_id, (SELECT tarif_id FROM billservice_accounttarif WHERE id=psh.accounttarif_id) as tarif_id, psh.summ, (SELECT username FROM billservice_account WHERE id=psh.account_id) as username, (SELECT fullname FROM billservice_account WHERE id=psh.account_id) as fullname, psh.type_id 
            FROM billservice_periodicalservicehistory as psh 
            WHERE psh.created between '%s' and '%s' %%s and type_id='%s' ORDER BY psh.created DESC
            """ % (start_date, end_date,transaction_type)
            
            if account_id:
                sql = sql % " and psh.account_id=%s " % account_id
            else:
                sql = sql % " "  
        
            items = self.connection.sql(sql)
            self.connection.commit()
            self.tableWidget.setRowCount(len(items))
            i=0
            
            ['#', u'Аккаунт', u'Тарифный план', u'Услуга', u'Тип', u"Сумма", u"Дата"]
            sum = 0
            for item in items:
                self.addrow(i, i, 0, id = item.id, date = item.created, table="billservice_periodicalservicehistory")
                self.addrow(item.username, i, 1)
                self.addrow(item.fullname, i, 2)
                self.addrow(t.get(item.tarif_id), i, 3)
                self.addrow(s.get(item.service_id), i, 4)
                self.addrow(item.type_id, i, 5)
                self.addrow(item.summ, i, 6)
                self.addrow(item.created, i, 7)
                i+=1
                sum+=item.summ
            self.statusBar().showMessage(u"Всего записей:%s. Итоговая сумма %.3f" % (i,sum))
            
        if self.transactions_types.get(transaction_type)=="billservice_onetimeservicehistory":
            services = self.connection.get_models("billservice_onetimeservice")
            s = {}
            for x in services:
                s[x.id] = x.name
 
            tariffs = self.connection.get_models("billservice_tariff")
            t = {}
            for x in tariffs:
                t[x.id] = x.name
                               
            sql = """
            SELECT osh.id, osh.onetimeservice_id, osh.created, osh.accounttarif_id, (SELECT tarif_id FROM billservice_accounttarif WHERE id=osh.accounttarif_id) as tarif_id, osh.summ, (SELECT username FROM billservice_account WHERE id=osh.account_id) as username, (SELECT fullname FROM billservice_account WHERE id=osh.account_id) as fullname 
            FROM billservice_onetimeservicehistory as osh 
            WHERE osh.created between '%s' and '%s' %%s ORDER BY osh.created DESC
            """ % (start_date, end_date,)
            
            if account_id:
                sql = sql % " and osh.account_id=%s " % account_id
            else:
                sql = sql % " "  
        
            items = self.connection.sql(sql)
            self.connection.commit()
            self.tableWidget.setRowCount(len(items))
            i=0
            
            ['#', u'Аккаунт', u'Тарифный план', u'Услуга', u"Сумма", u"Дата"]
            sum = 0
            for item in items:
                self.addrow(i, i, 0, id = item.id, date = item.created, table="billservice_onetimeservicehistory")
                self.addrow(item.username, i, 1)
                self.addrow(item.fullname, i, 2)
                self.addrow(t.get(item.tarif_id), i, 3)
                self.addrow(s.get(item.onetimeservice_id), i, 4)
                self.addrow(item.summ, i, 5)
                self.addrow(item.created, i, 6)
                i+=1
                sum += item.summ
            self.statusBar().showMessage(u"Всего записей:%s. Итоговая сумма %.3f" % (i,sum))
                        
        if self.transactions_types.get(transaction_type)=="billservice_traffictransaction":
            tariffs = self.connection.get_models("billservice_tariff")
            t = {}
            for x in tariffs:
                t[x.id] = x.name
                               
            sql = """
            SELECT tr.id, tr.created, tr.accounttarif_id, (SELECT tarif_id FROM billservice_accounttarif WHERE id=tr.accounttarif_id) as tarif_id, tr.summ, (SELECT username FROM billservice_account WHERE id=tr.account_id) as username , (SELECT fullname FROM billservice_account WHERE id=tr.account_id) as fullname
            FROM billservice_traffictransaction as tr 
            WHERE tr.created between '%s' and '%s' %%s ORDER BY tr.created DESC
            """ % (start_date, end_date,)
            
            if account_id:
                sql = sql % " and tr.account_id=%s " % account_id
            else:
                sql = sql % " "  
        
            items = self.connection.sql(sql)
            self.connection.commit()
            self.tableWidget.setRowCount(len(items))
            i=0
            
            ["#", u'Аккаунт', u'Тарифный план', u'Сумма', u'Дата']
            sum = 0
            for item in items:
                self.addrow(i, i, 0, id = item.id, date = item.created, table="billservice_traffictransaction")
                self.addrow(item.username, i, 1)
                self.addrow(item.fullname, i, 2)
                self.addrow(t.get(item.tarif_id), i, 3)
                self.addrow(item.summ, i, 4)
                self.addrow(item.created, i, 5)
                i+=1
                sum+=item.summ
                
            self.statusBar().showMessage(u"Всего записей:%s. Итоговая сумма %.3f" % (i,sum))
            
        if self.transactions_types.get(transaction_type)=="billservice_timetransaction":
            #print 111
            tariffs = self.connection.get_models("billservice_tariff")
            t = {}
            for x in tariffs:
                t[x.id] = x.name
                               
            sql = """
            SELECT tr.id, tr.created, tr.accounttarif_id, (SELECT tarif_id FROM billservice_accounttarif WHERE id=tr.accounttarif_id) as tarif_id, tr.summ, (SELECT username FROM billservice_account WHERE id=tr.account_id) as username, (SELECT fullname FROM billservice_account WHERE id=tr.account_id) as fullname
            FROM billservice_timetransaction as tr 
            WHERE tr.created between '%s' and '%s' %%s ORDER BY tr.created DESC
            """ % (start_date, end_date,)
            
            if account_id:
                sql = sql % " and tr.account_id=%s " % account_id
            else:
                sql = sql % " "  
        
            items = self.connection.sql(sql)
            self.connection.commit()
            self.tableWidget.setRowCount(len(items))
            i=0
            sum = 0
            for item in items:
                self.addrow(i, i, 0, id = item.id, date = item.created, table="billservice_timetransaction")
                self.addrow(item.username, i, 1)
                self.addrow(item.fullname, i, 2)
                self.addrow(t.get(item.tarif_id), i, 3)
                self.addrow(item.summ, i, 4)
                self.addrow(item.created, i, 5)
                i+=1
                sum +=item.summ
            self.statusBar().showMessage(u"Всего записей:%s. Итоговая сумма %.3f" % (i,sum))                                
        self.tableWidget.setColumnHidden(0, False)
        
        if self.transactions_types.get(transaction_type)=="billservice_addonservicetransaction":
            #print 111
            tr_types = self.connection.get_models("billservice_transactiontype")
            t = {}
            for x in tr_types:
                t[x.internal_name] = x.name

            sql = """
            select addst.id, (SELECT name FROM billservice_addonservice WHERE id=addst.service_id) as service_name, addst.summ, addst.created, addst.type_id, (SELECT username FROM billservice_account WHERE id=addst.account_id) as username, (SELECT fullname FROM billservice_account WHERE id=addst.account_id) as fullname
            FROM billservice_addonservicetransaction as addst
            WHERE addst.created>='%s' and addst.created<='%s' %%s ORDER BY created ASC
            """ % (start_date, end_date,)
            
            if account_id:
                sql = sql % " and addst.account_id=%s " % account_id
            else:
                sql = sql % " "  
        
            items = self.connection.sql(sql)
            self.connection.commit()
            self.tableWidget.setRowCount(len(items))
            i=0
            sum = 0
            ["#", u'Аккаунт', u'Услуга', u'Тип услуги', u'Сумма', u'Дата']
            for item in items:
                self.addrow(i, i, 0, id = item.id, date = item.created, table="billservice_addonservicetransaction")
                self.addrow(item.username, i, 1)
                self.addrow(item.fullname, i, 2)
                self.addrow(item.service_name, i, 3)
                self.addrow(t[item.type_id], i, 4)
                self.addrow(item.summ, i, 5)
                self.addrow(item.created, i, 6)
                i+=1
                sum +=item.summ
            self.statusBar().showMessage(u"Всего записей:%s. Итоговая сумма %.3f" % (i,sum))                               
        self.tableWidget.setColumnHidden(0, False)

        if self.transactions_types.get(transaction_type)=="qiwi_invoice":
            #print 111
            #tr_types = self.connection.get_models("billservice_transactiontype")
            #t = {}
            #for x in tr_types:
            #    t[x.internal_name] = x.name
                               
            #print (start_date, end_date,)
            [u'#', u'Аккаунт', u"ФИО",  u"№ инвойса", u'Создан', u"Автозачисление", u'Оплачен', u"Сумма"]
            sql = """
            SELECT qi.id as id, (SELECT username FROM billservice_account WHERE id=qi.account_id) as username,(SELECT fullname FROM billservice_account WHERE id=qi.account_id) as fullname,qi,created as created, qi.autoaccept, qi.date_accepted, qi.summ
            FROM qiwi_invoice as qi
            WHERE qi.created>='%s' and qi.created<='%s' %%s ORDER BY created ASC
            """ % (start_date, end_date,)
            
            if account_id:
                sql = sql % " and qi.account_id=%s " % account_id
            else:
                sql = sql % " "  
        
            items = self.connection.sql(sql)
            self.connection.commit()
            self.tableWidget.setRowCount(len(items))
            i=0
            sum = 0
            allsumm=0
            for item in items:
                self.addrow(i, i, 0, id = item.id, date = item.created, table="qiwi_invoice")
                self.addrow(item.username, i, 1)
                self.addrow(item.fullname, i, 2)
                self.addrow(item.id, i, 3)
                self.addrow(item.created, i, 4)
                self.addrow(item.autoaccept, i, 5)
                try:
                    self.addrow(item.date_accepted.strftime(self.strftimeFormat), i, 6)
                except:
                    self.addrow('', i, 6)
                self.addrow(item.summ, i, 7)
                i+=1
                allsumm +=item.summ
                if item.date_accepted:
                    sum +=item.summ
            self.addrow(u"Инвойсов на сумму", i, 6)
            self.addrow(allsumm, i, 7)
            self.addrow(u"Оплачено на сумму", i+1, 6)
            self.addrow(sum, i+1, 7)
            self.statusBar().showMessage(u"Всего записей:%s.Инвойсов на сумму %.3f, оплачено %.3f" % (i,allsumm, sum))
                                             
        self.tableWidget.setColumnHidden(0, False)

        if self.transactions_types.get(transaction_type)=="totaltransactions":
            
            sql = """
            SELECT qi.id as id, (SELECT username FROM billservice_account WHERE id=qi.account_id) as username,(SELECT fullname FROM billservice_account WHERE id=qi.account_id) as fullname,qi,created as created, qi.autoaccept, qi.date_accepted, qi.summ, get_tarif_name(qi.account_id, qi.date_accepted) as tarif_name
            FROM qiwi_invoice as qi
            WHERE qi.date_accepted is not Null and qi.created>='%s' and qi.created<='%s' %%s ORDER BY created ASC
            """ % (start_date, end_date,)
            
            if account_id:
                sql = sql % " and qi.account_id=%s " % account_id
            else:
                sql = sql % " "  
        
            qiwi_items = self.connection.sql(sql)

#####################
            tr_types = self.connection.get_models("billservice_transactiontype",fields=['id','name', 'internal_name'])
            tr_type = {}
            for x in tr_types:
                tr_type[x.internal_name] = x.name

            tariffs = self.connection.get_models("billservice_tariff", fields=['id', "name"])
            tariff = {}
            for x in tariffs:
                tariff[x.id] = x.name

            services = self.connection.get_models("billservice_onetimeservice", fields=['id', 'name'])
            ot_service = {}
            for x in services:
                ot_service[x.id] = x.name

            services = self.connection.get_models("billservice_periodicalservice", fields=['id', 'name'])
            p_service = {}
            for x in services:
                p_service[x.id] = x.name
                
            sql = """
            select addst.id, (SELECT name FROM billservice_addonservice WHERE id=addst.service_id) as service_name, addst.summ, addst.created, addst.type_id, (SELECT username FROM billservice_account WHERE id=addst.account_id) as username, (SELECT fullname FROM billservice_account WHERE id=addst.account_id) as fullname, get_tarif_name(addst.account_id,addst.created) as tarif_name
            FROM billservice_addonservicetransaction as addst
            WHERE addst.created>='%s' and addst.created<='%s' %%s ORDER BY created ASC
            """ % (start_date, end_date,)
            
            if account_id:
                sql = sql % " and addst.account_id=%s " % account_id
            else:
                sql = sql % " "  
        
            addonservice_items = self.connection.sql(sql)
            
            ##
            

                               
            sql = """
            SELECT tr.id, tr.created, tr.accounttarif_id, (SELECT tarif_id FROM billservice_accounttarif WHERE id=tr.accounttarif_id) as tarif_id, tr.summ, (SELECT username FROM billservice_account WHERE id=tr.account_id) as username, (SELECT fullname FROM billservice_account WHERE id=tr.account_id) as fullname
            FROM billservice_timetransaction as tr 
            WHERE tr.created between '%s' and '%s' %%s ORDER BY tr.created DESC
            """ % (start_date, end_date,)
            
            if account_id:
                sql = sql % " and tr.account_id=%s " % account_id
            else:
                sql = sql % " "  
        
            timetransaction_items = self.connection.sql(sql)
            
            ##
            
                               
            sql = """
            SELECT tr.id, tr.created, tr.accounttarif_id, (SELECT tarif_id FROM billservice_accounttarif WHERE id=tr.accounttarif_id) as tarif_id, tr.summ, (SELECT username FROM billservice_account WHERE id=tr.account_id) as username , (SELECT fullname FROM billservice_account WHERE id=tr.account_id) as fullname, tr.radiustraffictransmitservice_id
            FROM billservice_traffictransaction as tr 
            WHERE tr.created between '%s' and '%s' %%s ORDER BY tr.created DESC
            """ % (start_date, end_date,)
            
            if account_id:
                sql = sql % " and tr.account_id=%s " % account_id
            else:
                sql = sql % " "  
        
            traffictransaction_items = self.connection.sql(sql)
            
            ##
            

 
                               
            sql = """
            SELECT osh.id, osh.onetimeservice_id, osh.created, osh.accounttarif_id, (SELECT tarif_id FROM billservice_accounttarif WHERE id=osh.accounttarif_id) as tarif_id, osh.summ, (SELECT username FROM billservice_account WHERE id=osh.account_id) as username, (SELECT fullname FROM billservice_account WHERE id=osh.account_id) as fullname 
            FROM billservice_onetimeservicehistory as osh 
            WHERE osh.created between '%s' and '%s' %%s ORDER BY osh.created DESC
            """ % (start_date, end_date,)
            
            if account_id:
                sql = sql % " and osh.account_id=%s " % account_id
            else:
                sql = sql % " "  
        
            otsh_items = self.connection.sql(sql)
            
            ##


                               
            sql = """
            SELECT psh.id, psh.service_id, psh.created, psh.accounttarif_id, (SELECT tarif_id FROM billservice_accounttarif WHERE id=psh.accounttarif_id) as tarif_id, psh.summ, (SELECT username FROM billservice_account WHERE id=psh.account_id) as username, (SELECT fullname FROM billservice_account WHERE id=psh.account_id) as fullname, psh.type_id 
            FROM billservice_periodicalservicehistory as psh 
            WHERE psh.created between '%s' and '%s' %%s  ORDER BY psh.created DESC
            """ % (start_date, end_date)
            
            if account_id:
                sql = sql % " and psh.account_id=%s " % account_id
            else:
                sql = sql % " "  
        
            period_items = self.connection.sql(sql)
            ##
            
            
            sql = """SELECT transaction.*, transactiontype.name as transaction_type_name, tariff.name as tariff_name, (SELECT username FROM billservice_account WHERE id=transaction.account_id) as username, (SELECT fullname FROM billservice_account WHERE id=transaction.account_id) as fullname, (SELECT username FROM billservice_systemuser WHERE id=transaction.systemuser_id) as systemuser
                                            FROM billservice_transaction as transaction
                                            JOIN billservice_transactiontype as transactiontype ON transactiontype.internal_name = transaction.type_id
                                            LEFT JOIN billservice_tariff as tariff ON tariff.id = transaction.tarif_id   
                                            WHERE transaction.created between '%s' and '%s' %%s ORDER BY transaction.created DESC""" %  (start_date, end_date,)

            if account_id:
                sql = sql % " and transaction.account_id=%s %%s" % account_id
            else:
                sql = sql % " %s"

            systemuser_id = self.comboBox_cashier.itemData(self.comboBox_cashier.currentIndex()).toInt()[0]
            #print sql
            if systemuser_id!=0:
                sql = sql % " and transaction.systemuser_id=%s " % systemuser_id
            else:
                sql = sql % " "

            transaction_items = self.connection.sql(sql)
            
            
#####################
            self.tableWidget.setSortingEnabled(False)
            self.connection.commit()
            self.tableWidget.setRowCount(len(qiwi_items)+len(addonservice_items)+len(timetransaction_items)+len(traffictransaction_items)+len(period_items)+len(otsh_items)+len(transaction_items))
            i=0
            pos_sum = 0
            neg_sum=0
            for item in qiwi_items:
                self.addrow(i, i, 0, id = item.id, date = item.created, table="qiwi_invoice")
                self.addrow(item.username, i, 1)
                self.addrow(item.fullname, i, 2)
                self.addrow(item.tarif_name, i, 3)
                self.addrow(u"QIWI инвойс", i, 4)
                self.addrow(item.id, i, 5)
                self.addrow(item.summ, i, 6)
                self.addrow(item.created, i, 7)
                i+=1
                if item.summ>0:
                    pos_sum +=item.summ
                else:
                    neg_sum +=item.summ

            for item in addonservice_items:
                self.addrow(i, i, 0, id = item.id, date = item.created, table="billservice_addonservicetransaction")
                self.addrow(item.username, i, 1)
                self.addrow(item.fullname, i, 2)
                self.addrow(item.tarif_name, i, 3)
                self.addrow(item.service_name, i, 4)
                self.addrow(tr_type[item.type_id], i, 5)
                self.addrow(item.summ, i, 6)
                self.addrow(item.created, i,7)
                i+=1
                if item.summ>0:
                    pos_sum +=item.summ
                else:
                    neg_sum +=item.summ
                
            for item in timetransaction_items:
                self.addrow(i, i, 0, id = item.id, date = item.created, table="billservice_timetransaction")
                self.addrow(item.username, i, 1)
                self.addrow(item.fullname, i, 2)
                self.addrow(tariffs.get(item.tarif_id), i, 3) #!!!
                self.addrow(u"Списание денег за время", i, 4) #!!!
                self.addrow(item.summ, i, 6)
                self.addrow(item.created, i, 7)
                i+=1           
                if item.summ>0:
                    pos_sum +=item.summ
                else:
                    neg_sum +=item.summ
                
            for item in traffictransaction_items:
                self.addrow(i, i, 0, id = item.id, date = item.created, table="billservice_traffictransaction")
                self.addrow(item.username, i, 1)
                self.addrow(item.fullname, i, 2)
                self.addrow(tariff.get(item.tarif_id), i, 3)
                self.addrow(u"Списание денег за трафик", i, 4)
                if item.radiustraffictransmitservice_id:
                    self.addrow(u"Тарификация по RADIUS", i, 5)
                else:
                    self.addrow(u"Тарификация по NetFlow", i, 5)
                self.addrow(item.summ, i, 6)
                self.addrow(item.created, i, 7)
                i+=1                
                if item.summ>0:
                    pos_sum +=item.summ
                else:
                    neg_sum +=item.summ
                
            for item in period_items:
                self.addrow(i, i, 0, id = item.id, date = item.created, table="billservice_periodicalservicehistory")
                self.addrow(item.username, i, 1)
                self.addrow(item.fullname, i, 2)
                self.addrow(tariff.get(item.tarif_id), i, 3)
                self.addrow(p_service.get(item.service_id), i, 4)
                self.addrow(item.type_id, i, 5)
                self.addrow(item.summ, i, 6)
                self.addrow(item.created, i, 7)
                i+=1
                if item.summ>0:
                    pos_sum +=item.summ
                else:
                    neg_sum +=item.summ
                
            for item in otsh_items:
                self.addrow(i, i, 0, id = item.id, date = item.created, table="billservice_onetimeservicehistory")
                self.addrow(item.username, i, 1)
                self.addrow(item.fullname, i, 2)
                self.addrow(tariff.get(item.tarif_id), i, 3)
                self.addrow(ot_service.get(item.onetimeservice_id), i, 4)
                self.addrow(item.summ, i, 6)
                self.addrow(item.created, i, 7)
                if item.summ>0:
                    pos_sum +=item.summ
                else:
                    neg_sum +=item.summ
                i+=1
                
            for item in transaction_items:
                self.addrow(i, i, 0, id=item.id, promise = item.promise, date = item.created, table="billservice_transaction")
                self.addrow(item.username, i, 1, promise = item.promise)
                self.addrow(item.fullname, i, 2, promise = item.promise)
                self.addrow(item.tariff_name, i, 3, promise = item.promise)
                
                self.addrow(item.transaction_type_name, i, 4, promise = item.promise)
                self.addrow(item.bill, i, 5, promise = item.promise)
                self.addrow(item.summ*(-1), i, 6, promise = item.promise)
                self.addrow(item.created, i, 7, promise = item.promise)
                
                self.addrow(item.description, i, 8, promise = item.promise)
                self.addrow(item.promise, i, 9, promise = item.promise)
                self.addrow(item.systemuser, i, 10, promise = item.promise)
                #sum+=item.summ*(-1)
                if item.summ>0:
                    pos_sum +=item.summ*(-1)
                else:
                    neg_sum +=item.summ*(-1)              
                i+=1
            #self.addrow(u"Начислено на сумму", i+1, 6)
            #self.addrow(pos_sum, i+1, 7)
            #i+=1
            #self.addrow(u"Списано на сумму", i+1, 6)
            #self.addrow(neg_sum, i+1, 7)
            self.statusBar().showMessage(u"Всего записей:%s. Начислено:%.3f. Списано:%.3f" % (i, neg_sum,pos_sum))
            
        self.tableWidget.setSortingEnabled(True)        
        self.tableWidget.setColumnHidden(0, False)
        
                
        try:
            settings = QtCore.QSettings("Expert Billing", "Expert Billing Client")
            settings.setValue("trans_date_start", QtCore.QVariant(self.date_start.dateTime()))
            settings.setValue("trans_date_end", QtCore.QVariant(self.date_end.dateTime()))
        except Exception, ex:
            print "Transactions settings save error: ", ex
        #self.tableWidget.setSortingEnabled(True)
        

    def get_selected_ids(self):
        ids = []
        for r in self.tableWidget.selectedItems():
            #print r.column()
            if r.column()==0:
                ids.append((r.id, r.date, r.table))
        return ids
    
   
    def delete_transaction(self):
        ids = self.get_selected_ids()
        #print ids
        #table=self.transactions_types.get(unicode(self.comboBox_transactions_type.itemData(self.comboBox_transactions_type.currentIndex()).toString()))
        if not ids:return
        
        for id,date,table in ids:
            #print id,date,table
            if table=="billservice_transaction":
                self.connection.transaction_delete(ids=[(id,date)])       
            elif  table=="billservice_periodicalservicehistory":

                self.connection.command("DELETE FROM billservice_periodicalservicehistory WHERE id=%s and created='%s'" % (id, date,))
                self.connection.commit()
            elif  table=="billservice_onetimeservicehistory":
                self.connection.command("DELETE FROM billservice_onetimeservicehistory WHERE id=%s and created='%s'" % (id, date,))
                self.connection.commit()
            elif  table=="billservice_addonservicetransaction":
                self.connection.command("DELETE FROM billservice_addonservicetransaction WHERE id=%s and created='%s'" % (id, date,))
                self.connection.commit()
            elif  table=="billservice_traffictransaction":
                self.connection.command("DELETE FROM billservice_traffictransaction WHERE id=%s and created='%s'" % (id, date,))
                self.connection.commit()
            elif  table=="billservice_timetransaction":
                self.connection.command("DELETE FROM billservice_timetransaction WHERE id=%s and created='%s'" % (id, date,))
                self.connection.commit()         
            elif  table=="qiwi_invoice":
                self.connection.command("DELETE FROM qiwi_invoice WHERE id=%s and created='%s'" % (id, date,))
                self.connection.commit()                            
        if ids:
            self.refresh_table()
     

        
class ReportPropertiesDialog(QtGui.QDialog):
    def __init__(self, connection):
        super(ReportPropertiesDialog, self).__init__()
        self.connection = connection
        self.datetimeFormat = "dd" + dateDelim + "MM" + dateDelim + "yyyy hh:mm:ss"
        self.strftimeFormat = "%d" + dateDelim + "%m" + dateDelim + "%Y %H:%M:%S"
        self.users = []
        self.classes = []
        self.nas = None
        self.start_date = datetime.datetime.now()
        self.end_date = datetime.datetime.now()
        
        self.resize(452, 465)
        self.gridLayout = QtGui.QGridLayout(self)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tabWidget = QtGui.QTabWidget(self)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.gridLayout_6 = QtGui.QGridLayout(self.tab)
        self.gridLayout_6.setObjectName(_fromUtf8("gridLayout_6"))
        self.groupBox_timeperiod = QtGui.QGroupBox(self.tab)
        self.groupBox_timeperiod.setObjectName(_fromUtf8("groupBox_timeperiod"))
        self.gridLayout_4 = QtGui.QGridLayout(self.groupBox_timeperiod)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.label_date_start = QtGui.QLabel(self.groupBox_timeperiod)
        self.label_date_start.setObjectName(_fromUtf8("label_date_start"))
        self.gridLayout_4.addWidget(self.label_date_start, 0, 0, 1, 1)
        self.dateTimeEdit_date_start = CustomDateTimeWidget()
        #self.dateTimeEdit_date_start.setCalendarPopup(True)
        self.dateTimeEdit_date_start.setObjectName(_fromUtf8("dateTimeEdit_date_start"))
        self.gridLayout_4.addWidget(self.dateTimeEdit_date_start, 0, 1, 1, 1)
        self.label_date_end = QtGui.QLabel(self.groupBox_timeperiod)
        self.label_date_end.setObjectName(_fromUtf8("label_date_end"))
        self.gridLayout_4.addWidget(self.label_date_end, 1, 0, 1, 1)
        self.dateTimeEdit_date_end = CustomDateTimeWidget()
        #self.dateTimeEdit_date_end.setCalendarPopup(True)
        self.dateTimeEdit_date_end.setObjectName(_fromUtf8("dateTimeEdit_date_end"))
        self.gridLayout_4.addWidget(self.dateTimeEdit_date_end, 1, 1, 1, 1)
        self.gridLayout_6.addWidget(self.groupBox_timeperiod, 0, 0, 1, 1)

        try:
            settings = QtCore.QSettings("Expert Billing", "Expert Billing Client")
            self.dateTimeEdit_date_start.setDateTime(settings.value("reportprop_date_start", QtCore.QVariant(QtCore.QDateTime(2011,1,1,0,0))).toDateTime())
            self.dateTimeEdit_date_end.setDateTime(settings.value("reportprop_date_end", QtCore.QVariant(QtCore.QDateTime(2012,1,1,0,0))).toDateTime())
        except Exception, ex:
            print "Transactions settings error: ", ex
            
        self.groupBox_accounts = QtGui.QGroupBox(self.tab)
        self.groupBox_accounts.setObjectName(_fromUtf8("groupBox_accounts"))
        self.gridLayout_5 = QtGui.QGridLayout(self.groupBox_accounts)
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.listWidget_accounts_all = QtGui.QListWidget(self.groupBox_accounts)
        self.listWidget_accounts_all.setObjectName(_fromUtf8("listWidget_accounts_all"))
        self.gridLayout_5.addWidget(self.listWidget_accounts_all, 1, 0, 4, 1)
        spacerItem = QtGui.QSpacerItem(20, 69, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_5.addItem(spacerItem, 1, 1, 1, 1)
        self.listWidget_accounts_selected = QtGui.QListWidget(self.groupBox_accounts)
        self.listWidget_accounts_selected.setObjectName(_fromUtf8("listWidget_accounts_selected"))
        self.gridLayout_5.addWidget(self.listWidget_accounts_selected, 1, 2, 4, 1)
        self.toolButton_to_accounts_selected = QtGui.QToolButton(self.groupBox_accounts)
        self.toolButton_to_accounts_selected.setObjectName(_fromUtf8("toolButton_to_accounts_selected"))
        self.gridLayout_5.addWidget(self.toolButton_to_accounts_selected, 2, 1, 1, 1)
        self.toolButton_from_accounts_selected = QtGui.QToolButton(self.groupBox_accounts)
        self.toolButton_from_accounts_selected.setObjectName(_fromUtf8("toolButton_from_accounts_selected"))
        self.gridLayout_5.addWidget(self.toolButton_from_accounts_selected, 3, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 69, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_5.addItem(spacerItem1, 4, 1, 1, 1)
        self.label_accounts_all = QtGui.QLabel(self.groupBox_accounts)
        self.label_accounts_all.setObjectName(_fromUtf8("label_accounts_all"))
        self.gridLayout_5.addWidget(self.label_accounts_all, 0, 0, 1, 1)
        self.label_accounts_selected = QtGui.QLabel(self.groupBox_accounts)
        self.label_accounts_selected.setObjectName(_fromUtf8("label_accounts_selected"))
        self.gridLayout_5.addWidget(self.label_accounts_selected, 0, 2, 1, 1)
        self.gridLayout_6.addWidget(self.groupBox_accounts, 1, 0, 1, 1)
        self.tabWidget.addTab(self.tab, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.gridLayout_2 = QtGui.QGridLayout(self.tab_2)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.listWidget_groups_all = QtGui.QListWidget(self.tab_2)
        self.listWidget_groups_all.setObjectName(_fromUtf8("listWidget_groups_all"))
        self.gridLayout_2.addWidget(self.listWidget_groups_all, 1, 0, 4, 1)
        self.toolButton_to_groups_selected = QtGui.QToolButton(self.tab_2)
        self.toolButton_to_groups_selected.setObjectName(_fromUtf8("toolButton_to_groups_selected"))
        self.gridLayout_2.addWidget(self.toolButton_to_groups_selected, 2, 1, 1, 1)
        self.listWidget_groups_selected = QtGui.QListWidget(self.tab_2)
        self.listWidget_groups_selected.setObjectName(_fromUtf8("listWidget_groups_selected"))
        self.gridLayout_2.addWidget(self.listWidget_groups_selected, 1, 2, 4, 1)
        self.toolButton_from_groups_selected = QtGui.QToolButton(self.tab_2)
        self.toolButton_from_groups_selected.setObjectName(_fromUtf8("toolButton_from_groups_selected"))
        self.gridLayout_2.addWidget(self.toolButton_from_groups_selected, 3, 1, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem2, 1, 1, 1, 1)
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem3, 4, 1, 1, 1)
        self.label_groups_all = QtGui.QLabel(self.tab_2)
        self.label_groups_all.setObjectName(_fromUtf8("label_groups_all"))
        self.gridLayout_2.addWidget(self.label_groups_all, 0, 0, 1, 1)
        self.label_groups_selected = QtGui.QLabel(self.tab_2)
        self.label_groups_selected.setObjectName(_fromUtf8("label_groups_selected"))
        self.gridLayout_2.addWidget(self.label_groups_selected, 0, 2, 1, 1)
        self.tabWidget.addTab(self.tab_2, _fromUtf8(""))
        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName(_fromUtf8("tab_3"))
        self.gridLayout_3 = QtGui.QGridLayout(self.tab_3)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.listWidget_classes_all = QtGui.QListWidget(self.tab_3)
        self.listWidget_classes_all.setObjectName(_fromUtf8("listWidget_classes_all"))
        self.gridLayout_3.addWidget(self.listWidget_classes_all, 1, 0, 4, 1)
        #self.tab_3.setHidden(True)
        spacerItem4 = QtGui.QSpacerItem(20, 137, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_3.addItem(spacerItem4, 1, 1, 1, 1)
        self.listWidget_classes_selected = QtGui.QListWidget(self.tab_3)
        self.listWidget_classes_selected.setObjectName(_fromUtf8("listWidget_classes_selected"))
        self.gridLayout_3.addWidget(self.listWidget_classes_selected, 1, 2, 4, 1)
        self.toolButton_to_classes_selected = QtGui.QToolButton(self.tab_3)
        self.toolButton_to_classes_selected.setObjectName(_fromUtf8("toolButton_to_classes_selected"))
        self.gridLayout_3.addWidget(self.toolButton_to_classes_selected, 2, 1, 1, 1)
        self.toolButton_from_classes_selected = QtGui.QToolButton(self.tab_3)
        self.toolButton_from_classes_selected.setObjectName(_fromUtf8("toolButton_from_classes_selected"))
        self.gridLayout_3.addWidget(self.toolButton_from_classes_selected, 3, 1, 1, 1)
        spacerItem5 = QtGui.QSpacerItem(20, 137, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_3.addItem(spacerItem5, 4, 1, 1, 1)
        self.label_classes_all = QtGui.QLabel(self.tab_3)
        self.label_classes_all.setObjectName(_fromUtf8("label_classes_all"))
        self.gridLayout_3.addWidget(self.label_classes_all, 0, 0, 1, 1)
        self.label_classes_selected = QtGui.QLabel(self.tab_3)
        self.label_classes_selected.setObjectName(_fromUtf8("label_classes_selected"))
        self.gridLayout_3.addWidget(self.label_classes_selected, 0, 2, 1, 1)
        #self.tabWidget.addTab(self.tab_3, _fromUtf8(""))
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)
        
        self.listWidget_accounts_all.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listWidget_accounts_selected.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listWidget_classes_all.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listWidget_classes_selected.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listWidget_groups_all.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listWidget_groups_selected.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.retranslateUi()
        
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"),self.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"),self.reject)
        
        QtCore.QObject.connect(self.toolButton_to_accounts_selected, QtCore.SIGNAL("clicked()"),self.addUser)
        QtCore.QObject.connect(self.toolButton_from_accounts_selected, QtCore.SIGNAL("clicked()"),self.delUser)

        QtCore.QObject.connect(self.listWidget_accounts_all, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"),self.addUser)
        QtCore.QObject.connect(self.listWidget_accounts_selected, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"),self.delUser)        
        

        QtCore.QObject.connect(self.toolButton_to_classes_selected, QtCore.SIGNAL("clicked()"), self.addClass)
        QtCore.QObject.connect(self.toolButton_from_classes_selected, QtCore.SIGNAL("clicked()"), self.delClass)
        
        QtCore.QObject.connect(self.listWidget_classes_all, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.addClass)
        QtCore.QObject.connect(self.listWidget_classes_selected, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.delClass)
        
        QtCore.QObject.connect(self.toolButton_to_groups_selected, QtCore.SIGNAL("clicked()"), self.addGroup)
        QtCore.QObject.connect(self.toolButton_from_groups_selected, QtCore.SIGNAL("clicked()"), self.delGroup)
        
        QtCore.QObject.connect(self.listWidget_groups_all, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.addGroup)
        QtCore.QObject.connect(self.listWidget_groups_selected, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.delGroup)
        
        
        self.setTabOrder(self.tabWidget, self.dateTimeEdit_date_start)
        self.setTabOrder(self.dateTimeEdit_date_start, self.dateTimeEdit_date_end)
        self.setTabOrder(self.dateTimeEdit_date_end, self.listWidget_accounts_all)
        self.setTabOrder(self.listWidget_accounts_all, self.toolButton_to_accounts_selected)
        self.setTabOrder(self.toolButton_to_accounts_selected, self.toolButton_from_accounts_selected)
        self.setTabOrder(self.toolButton_from_accounts_selected, self.listWidget_accounts_selected)
        self.setTabOrder(self.listWidget_accounts_selected, self.buttonBox)
        self.setTabOrder(self.buttonBox, self.listWidget_groups_all)
        self.setTabOrder(self.listWidget_groups_all, self.toolButton_to_groups_selected)
        self.setTabOrder(self.toolButton_to_groups_selected, self.toolButton_from_groups_selected)
        self.setTabOrder(self.toolButton_from_groups_selected, self.listWidget_groups_selected)
        self.setTabOrder(self.listWidget_groups_selected, self.listWidget_classes_all)
        self.setTabOrder(self.listWidget_classes_all, self.toolButton_to_classes_selected)
        self.setTabOrder(self.toolButton_to_classes_selected, self.toolButton_from_classes_selected)
        self.setTabOrder(self.toolButton_from_classes_selected, self.listWidget_classes_selected)
        
        self.fixtures()
        #QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self):
        self.setWindowTitle(QtGui.QApplication.translate("Dialog", "Настройки отчёта", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_timeperiod.setTitle(QtGui.QApplication.translate("Dialog", "Период", None, QtGui.QApplication.UnicodeUTF8))
        self.label_date_start.setText(QtGui.QApplication.translate("Dialog", "с", None, QtGui.QApplication.UnicodeUTF8))
        self.dateTimeEdit_date_start.setDisplayFormat(QtGui.QApplication.translate("Dialog", "dd.MM.yy HH:mm:ss", None, QtGui.QApplication.UnicodeUTF8))
        self.label_date_end.setText(QtGui.QApplication.translate("Dialog", "по", None, QtGui.QApplication.UnicodeUTF8))
        self.dateTimeEdit_date_end.setDisplayFormat(QtGui.QApplication.translate("Dialog", "dd.MM.yy HH:mm:ss", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_accounts.setTitle(QtGui.QApplication.translate("Dialog", "Пользователи", None, QtGui.QApplication.UnicodeUTF8))
        self.toolButton_to_accounts_selected.setText(QtGui.QApplication.translate("Dialog", ">", None, QtGui.QApplication.UnicodeUTF8))
        self.toolButton_from_accounts_selected.setText(QtGui.QApplication.translate("Dialog", "<", None, QtGui.QApplication.UnicodeUTF8))
        self.label_accounts_all.setText(QtGui.QApplication.translate("Dialog", "Все", None, QtGui.QApplication.UnicodeUTF8))
        self.label_accounts_selected.setText(QtGui.QApplication.translate("Dialog", "Выбранные", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("Dialog", "Общее", None, QtGui.QApplication.UnicodeUTF8))
        self.toolButton_to_groups_selected.setText(QtGui.QApplication.translate("Dialog", ">", None, QtGui.QApplication.UnicodeUTF8))
        self.toolButton_from_groups_selected.setText(QtGui.QApplication.translate("Dialog", "<", None, QtGui.QApplication.UnicodeUTF8))
        self.label_groups_all.setText(QtGui.QApplication.translate("Dialog", "Все", None, QtGui.QApplication.UnicodeUTF8))
        self.label_groups_selected.setText(QtGui.QApplication.translate("Dialog", "Выбранные", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("Dialog", "Группы", None, QtGui.QApplication.UnicodeUTF8))
        self.toolButton_to_classes_selected.setText(QtGui.QApplication.translate("Dialog", ">", None, QtGui.QApplication.UnicodeUTF8))
        self.toolButton_from_classes_selected.setText(QtGui.QApplication.translate("Dialog", "<", None, QtGui.QApplication.UnicodeUTF8))
        self.label_classes_all.setText(QtGui.QApplication.translate("Dialog", "Все", None, QtGui.QApplication.UnicodeUTF8))
        self.label_classes_selected.setText(QtGui.QApplication.translate("Dialog", "Выбранные", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QtGui.QApplication.translate("Dialog", "Классы", None, QtGui.QApplication.UnicodeUTF8))

        
    def fixtures(self):
        accounts = self.connection.get_models("billservice_account", fields=['id', 'username'], order={'username':'ASC'})
        self.connection.commit()
        for account in accounts:
            item = QtGui.QListWidgetItem()
            item.setText(account.username)
            item.id = account.id
            self.listWidget_accounts_all.addItem(item)
            
        
        groups = self.connection.get_models("billservice_group", fields=['id', 'name'], order={'name':'ASC'})
        self.connection.commit()
        for group in groups:
            item = QtGui.QListWidgetItem()
            item.setText(group.name)
            item.id = group.id
            self.listWidget_groups_all.addItem(item)

        #classes = self.connection.get_models("nas_trafficclass", fields=['id', 'name'], order={'name':'ASC'})
        #self.connection.commit()
        #for tclass in classes:
        #    item = QtGui.QListWidgetItem()
        #    item.setText(tclass.name)
        #    item.id = tclass.id
        #    self.listWidget_classes_all.addItem(item)

            
        #nasses = self.connection.sql("SELECT * FROM nas_nas")
        #self.connection.commit()
        #self.nas_comboBox.addItem('')
        #for nas in nasses:
        #    self.nas_comboBox.addItem(nas.name)
        
    def addUser(self):
        selected_items = self.listWidget_accounts_all.selectedItems()
        
        for item in selected_items:
            self.listWidget_accounts_all.takeItem(self.listWidget_accounts_all.row(item))
            self.listWidget_accounts_selected.addItem(item)
            
        self.listWidget_accounts_selected.sortItems()
        
    def delUser(self):
        selected_items = self.listWidget_accounts_selected.selectedItems()
        
        for item in selected_items:
            self.listWidget_accounts_selected.takeItem(self.listWidget_accounts_selected.row(item))
            self.listWidget_accounts_all.addItem(item)
        self.listWidget_accounts_all.sortItems()
        
    def addClass(self):
        selected_items = self.listWidget_classes_all.selectedItems()
        #print 1
        for item in selected_items:
            self.listWidget_classes_all.takeItem(self.listWidget_classes_all.row(item))
            self.listWidget_classes_selected.addItem(item)
        self.listWidget_classes_selected.sortItems()
        
    def delClass(self):
        selected_items = self.listWidget_classes_selected.selectedItems()
        #print 2
        for item in selected_items:
            self.listWidget_classes_selected.takeItem(self.listWidget_classes_selected.row(item))
            self.listWidget_classes_all.addItem(item)
        self.listWidget_classes_all.sortItems()
        
    def addGroup(self):
        selected_items = self.listWidget_groups_all.selectedItems()
        #print 1
        for item in selected_items:
            self.listWidget_groups_all.takeItem(self.listWidget_groups_all.row(item))
            self.listWidget_groups_selected.addItem(item)
        self.listWidget_groups_selected.sortItems()
        
    def delGroup(self):
        selected_items = self.listWidget_groups_selected.selectedItems()
        #print 2
        for item in selected_items:
            self.listWidget_groups_selected.takeItem(self.listWidget_groups_selected.row(item))
            self.listWidget_groups_all.addItem(item)
        self.listWidget_groups_all.sortItems()
            
    def accept(self):
        self.accounts = []
        self.classes = []
        self.groups = []
        self.nas = None
        for x in xrange(0, self.listWidget_accounts_selected.count()):
            self.accounts.append(self.listWidget_accounts_selected.item(x).id)
            
        for x in xrange(0, self.listWidget_groups_selected.count()):
            self.groups.append(self.listWidget_groups_selected.item(x).id)
            
        if self.accounts==[] or self.groups==[]:
            QtGui.QMessageBox.warning(self, u"Внимание!", u"Вы не указали аккаунты или группы")
            return               

        self.start_date = self.dateTimeEdit_date_start.currentDate()
        self.end_date = self.dateTimeEdit_date_end.currentDate()
        
        try:
            settings = QtCore.QSettings("Expert Billing", "Expert Billing Client")
            settings.setValue("reportprop_date_start", QtCore.QVariant(self.dateTimeEdit_date_start.dateTime()))
            settings.setValue("reportprop_date_end", QtCore.QVariant(self.dateTimeEdit_date_end.dateTime()))
        except Exception, ex:
            print "Transactions settings save error: ", ex
            
        QtGui.QDialog.accept(self)
        
        
class NetFlowReportEbs(ebsTabs_n_TablesWindow):
    def __init__(self, connection, parent):
        #columns_t0=['#', u'Аккаунт', u'Класс трафика', u'Протокол', u'Источник',  u'Получатель', u'Передано', u'Дата']
        columns_t0=['#', u'Аккаунт', u'Источник', u'Получатель', u'Передано',u'Дата']
        columns_t1=[u'Аккаунт', u'Группа', u'Количество'] 
        #columns_t2=[u'Аккаунт', u'Класс', u'Входящий', u'Исходящий']
        initargs = {"setname":"netflow_frame_header", "objname":"NetFlowReportEbsMDI", "winsize":(0,0,800,587), "wintitle":"Сетевая статистика"}
        tabargs= [["tab1", columns_t1, "Тарифицированный трафик"], ["tab0", columns_t0, "Детальная статистика"], ]
        self.child = ReportPropertiesDialog(connection = connection)
        self.used = False
        super(NetFlowReportEbs, self).__init__(connection, initargs, tabargs)
        
    def ebsPreInit(self, initargs, tabargs):
        self.current_page=0
        self.protocols_reverse = {
          '0':'',
          '37': 'ddp',
          '98': 'encap',
          '3': 'ggp',
          '47': 'gre',
          '20': 'hmp',
          '1' : 'ICMP',
          '38':'idpr-cmtp',
          '2': 'igmp',
          '4': 'ipencap',
          '94': 'ipip',
          '89': 'ospf',
          '27': 'rdp',
          '6' : 'TCP',
          '17': 'UDP'
          }
        
        
    def ebsInterInit(self, initargs, tabargs):
        self.label = QtGui.QLabel(u"Навигатор")
        self.button_start = QtGui.QPushButton()
        self.button_start.setText(u"|<<")
        self.button_start.setMaximumHeight(19)
        self.button_start.setMaximumWidth(28)
        
        self.button_back = QtGui.QPushButton()
        self.button_back.setText(u"<")
        self.button_back.setMaximumHeight(19)
        self.button_back.setMaximumWidth(28)

        self.button_forward = QtGui.QPushButton()
        self.button_forward.setText(u">")
        self.button_forward.setMaximumHeight(19)
        self.button_forward.setMaximumWidth(28)
        self.status_label= QtGui.QLabel()
        
        self.statusbar = QtGui.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

        self.toolBar = QtGui.QToolBar(self)
        self.toolBar.setObjectName("toolBar")
        self.toolBar.setMovable(False)
        self.toolBar.setFloatable(False)
        self.toolBar.setIconSize(QtCore.QSize(18,18))
        
        self.statusBar().addWidget(self.label)
        self.statusBar().addWidget(self.button_start)
        self.statusBar().addWidget(self.button_back)
        self.statusBar().addWidget(self.button_forward)
        self.statusBar().addWidget(self.status_label)
        self.addToolBar(QtCore.Qt.TopToolBarArea,self.toolBar)
        self.tab0_tableWidget.setColumnHidden(0, False)
        self.tab1_tableWidget.setColumnHidden(0, False)
        
    def ebsPostInit(self, initargs, tabargs):
        QtCore.QObject.connect(self.button_start, QtCore.SIGNAL("clicked()"), self.startPage)
        QtCore.QObject.connect(self.button_forward, QtCore.SIGNAL("clicked()"), self.addPage)
        QtCore.QObject.connect(self.button_back, QtCore.SIGNAL("clicked()"), self.delPage)
        
        actList=[("configureAction", "Конфигурировать", "images/configure.png", self.configure)]
        objDict = {self.toolBar:["configureAction"]}
        self.actionCreator(actList, objDict)
        
        self.tableWidget = self.tab0_tableWidget
        self.tableWidget_summary = self.tab1_tableWidget
        self.tableWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tableWidget_summary.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        
    def retranslateUI(self, initargs, tabargs):
        super(NetFlowReportEbs, self).retranslateUI(initargs, tabargs)
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("MainWindow", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
    
    def addrow(self, value, x, y, color=None):
        headerItem = QtGui.QTableWidgetItem()
        if value==None:
            value=''
        if color:
            headerItem.setBackgroundColor(QtGui.QColor(color))
        if y==1:
            headerItem.setIcon(QtGui.QIcon("images/user.png"))
        headerItem.setText(unicode(value))
        self.tableWidget.setItem(x,y,headerItem)
 
    def startPage(self):
        #self.current_page=0
        self.refresh('home')
         
    def addPage(self):
        #self.current_page+=1
        self.refresh('next')
        
    def delPage(self):
        #if self.current_page-1>=0:
        #    self.current_page-=1
        self.refresh('prev')
        
    def getProtocol(self, value):
        if str(value) in self.protocols_reverse:
            return self.protocols_reverse['%s' % value]
        return value
        
    def configure(self):

        if self.tabWidget.currentIndex()==1:
            self.child.tabWidget.setTabEnabled(1, False)
            if self.child.exec_()!=1:
                return            
            #self.current_page=0
            self.used = True
            self.refresh('start')
        elif self.tabWidget.currentIndex()==0:
            self.child.tabWidget.setTabEnabled(1, True)
            if self.child.exec_()!=1:
                return            
            self.refresh_summary()
        
    def addRowSummary(self, value, x, y, color=None, user=False):
        headerItem = QtGui.QTableWidgetItem()
        if value==None:
            value=''
        if color:
            headerItem.setBackgroundColor(QtGui.QColor(color))

        if user==True:
            headerItem.setIcon(QtGui.QIcon("images/user.png"))

        headerItem.setText(unicode(value))
        self.tableWidget_summary.setItem(x,y,headerItem)

    def summ(self, x,y):
        if x==None:
            x=0
        if y==None:
            y=0
        return x+y
                
    def refresh_summary(self):            
        sql_acc = ""
        sql_groups = ""
        users = {}
        for x in xrange(len(self.child.accounts)):
                users[self.child.listWidget_accounts_selected.item(x).id] = unicode(self.child.listWidget_accounts_selected.item(x).text())

        groups = {}
        for x in xrange(len(self.child.groups)):
                groups[self.child.listWidget_groups_selected.item(x).id] = unicode(self.child.listWidget_groups_selected.item(x).text())


        if len(self.child.accounts)>0:
            sql_acc= """ AND gpst.account_id IN (%s) """ % ','.join(map(str, self.child.accounts))

        if len(self.child.groups)>0:
            sql_groups= """ AND gpst.group_id IN (%s) """ % ','.join(map(str, self.child.groups))

  
        sql="""SELECT gpst.account_id, gpst.group_id, sum(gpst.bytes) as bytes 
                      FROM billservice_groupstat AS gpst
                      WHERE gpst.datetime BETWEEN '%s' AND '%s' %s %s
            """ % (self.child.start_date, self.child.end_date, sql_acc, sql_groups)

                    
        sql+="GROUP BY gpst.account_id,gpst.group_id;"
        
        #print sql
        items = self.connection.sql(sql)
        self.connection.commit()
        i=0
        self.tableWidget_summary.clearContents()
        classes_count = len(items)+1
        #self.tableWidget_summary.setRowCount(classes_count)
        #self.tableWidget_summary.setSpan(i,0,0,5)
        #self.addRowSummary(u"Общая статистика по группам", i, 0, color='#ffffff')
        #i+=1
        group_bytes = {}
        bytes = 0
        for item in items:
            self.tableWidget_summary.insertRow(i)
            self.addRowSummary(users.get(item.account_id), i, 0, user=True)
            self.addRowSummary(groups.get(item.group_id), i, 1)
            #self.tableWidget_summary.setSpan(i,0,0,5)
            self.addRowSummary(humanable_bytes(item.bytes), i, 2)
            
            i+=1
            if not group_bytes.get(item.group_id):
                group_bytes[item.group_id]=0
            
            group_bytes[item.group_id]+= item.bytes
            bytes+= item.bytes
            
        self.tableWidget_summary.insertRow(i)
        i+=1
        
        for key in group_bytes:
            self.tableWidget_summary.insertRow(i)
            self.tableWidget_summary.setSpan(i,0,0,2)
            
            self.addRowSummary(u"Итого по группе %s" % groups.get(key), i, 0)
            self.addRowSummary(humanable_bytes(group_bytes.get(key)), i, 2)
            i+=1
                
        self.tableWidget_summary.insertRow(i)
        self.tableWidget_summary.setSpan(i,0,0,2)
        
        self.addRowSummary(u"Итого", i, 0, color='#ffffff')
        self.addRowSummary(humanable_bytes(bytes), i, 2, color='#ffffff')
        HeaderUtil.getHeader(self.setname+"_tab_1", self.tableWidget_summary)

                    
    def refresh(self, rep_command):        
        self.status_label.setText(u"Подождите, идёт обработка.")
        self.repaint()
        i = 0
        c = 0
        users = {}
        for x in xrange(len(self.child.accounts)):
                users[self.child.listWidget_accounts_selected.item(x).id] = unicode(self.child.listWidget_accounts_selected.item(x).text())
        if rep_command == 'start':
            
            
            icount = 0
            users_str = ''
            if len(self.child.users) > 0:
                users_str = ','.join(map(str, self.child.accounts))                
            if not users_str:
                flows = self.connection.text_report(['start', self.child.start_date, self.child.end_date, ['none']])
            else:
                flows = self.connection.text_report(['start', self.child.start_date, self.child.end_date, ['accounts', users_str]])
        else:
            flows = self.connection.text_report([rep_command]) 
        
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(len(flows))
        
        #['#', u'Аккаунт', u'Источник', u'Получатель', u'Передано',u'Дата']
        for flowstr in flows:                   
            flow = flowstr.split(' ')
            self.addrow(c, i, 0)
            self.addrow(users.get(int(flow[0]), ""), i, 1)   #acc_id      
            self.addrow("%s:%s" % (flow[1], flow[2]), i, 2) #src ip, port
            self.addrow("%s:%s" % (flow[3], flow[4]), i, 3) #dst
            self.addrow(humanable_bytes(int(flow[5])), i, 4) #octets
            self.addrow(datetime.datetime.fromtimestamp(float(flow[6])).strftime(self.strftimeFormat), i, 5)  #date        
            i+=1
            c+=1
        
        #self.tableWidget.resizeColumnsToContents()
        HeaderUtil.getHeader(self.setname+"_tab_0", self.tableWidget)
        self.status_label.setText(u"Готово")
  
    def closeEvent(self, event):
        if self.used:
            self.connection.text_report(['finish'])
        settings = QtCore.QSettings("Expert Billing", "Expert Billing Client")
        settings.setValue("window-geometry-%s" % unicode(self.objectName()), QtCore.QVariant(self.saveGeometry()))
        event.accept()    
        




class StatReport(QtGui.QMainWindow):
    def __init__(self, connection, chartinfo):
        super(StatReport, self).__init__()
        self.connection = connection
        self.chartinfo = chartinfo
        self.child = ReportOptionsDialog(self.connection, self.chartinfo[1][0])
        self.resize(QtCore.QSize(QtCore.QRect(0,0,1050,700).size()).expandedTo(self.minimumSizeHint()))
        self.textedit = QtGui.QTextEdit(self)
        
        self.setCentralWidget(self.textedit)
        self.statusbar = QtGui.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

        self.toolBar = QtGui.QToolBar(self)
        self.toolBar.setObjectName("toolBar")
        self.toolBar.setMovable(False)
        self.toolBar.setFloatable(False)
        self.toolBar.setIconSize(QtCore.QSize(18,18))

        
        self.addToolBar(QtCore.Qt.TopToolBarArea,self.toolBar)

        self.configureAction = QtGui.QAction(self)
        self.configureAction.setIcon(QtGui.QIcon("images/configure.png"))
        self.configureAction.setObjectName("configureAction")
        self.toolBar.addAction(self.configureAction)
        
        self.printAction = QtGui.QAction(self)
        self.printAction.setIcon(QtGui.QIcon("images/document-print.png"))
        self.printAction.setObjectName("printAction")
        self.toolBar.addAction(self.printAction)
        
        QtCore.QObject.connect(self.configureAction, QtCore.SIGNAL("triggered()"), self.configure)
        QtCore.QObject.connect(self.printAction, QtCore.SIGNAL("triggered()"), self.printDocument)
        
        self.retranslateUi()
        #QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self):
        self.setWindowTitle(QtGui.QApplication.translate("MainWindow", self.chartinfo[2], None, QtGui.QApplication.UnicodeUTF8))
    
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("MainWindow", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.configureAction.setText(QtGui.QApplication.translate("MainWindow", "configureAction", None, QtGui.QApplication.UnicodeUTF8))

        
    def configure(self):        
        if self.child.exec_()!=1:
            return
        
        self.refresh()
                
    def refresh(self):
        kwargs = {}
        kwargs['options'] = {}
        if self.child.lgb_antialias_checkBox.checkState() == 0:
            kwargs['options']['antialias'] = False
        else:
            kwargs['options']['antialias'] = True
            
        if self.child.lgb_grid_checkBox.checkState() == 0:
            kwargs['options']['autoticks'] = True
        else:
            kwargs['options']['autoticks'] = False
          
        if self.child.users:
            kwargs['users']   = self.child.users
            
        if self.child.classes:
            kwargs['classes'] = self.child.classes
            
        if self.child.servers:
            kwargs['servers'] = self.child.servers
        if self.child.groups:
            kwargs['groups']   = self.child.groups
        if self.child.ports:
            kwargs['ports']   = self.child.ports
        
        kwargs['type'] = self.chartinfo[1][0]
        chOpts = _chartopts[kwargs['type']]
        kwargs.update(chOpts[2])
        kwargs.update(self.child.opts)
        brep = bpReportEdit()
        editor  = brep.createreport(_xmlpath+"/" +self.chartinfo[0], [(self.child.start_date, self.child.end_date)], [kwargs], connection=self.connection)
        self.textedit = None
        #print editor.physicalDpiX()
        #print editor.logicalDpiX()
        fname = reppath + "/" +self.chartinfo[1][0] + str(time.time()) + ".html"
        f = open(fname, "wb")
        f.write(editor.document().toHtml("utf-8").toUtf8())
        f.close()
        webv = QtWebKit.QWebView()
        #webv.setHtml(sht)
        lfurl = QtCore.QUrl.fromLocalFile(os.path.abspath(fname))
        #print lfurl.toString()
        webv.load(lfurl)

        self.setCentralWidget(webv)
            
    def printDocument(self):
        document = self.centralWidget()
        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        printer.setPageSize(QtGui.QPrinter.A4)
        dialog = QtGui.QPrintDialog(printer, self)
        dialog.setWindowTitle(self.tr("Print Document"))
        if dialog.exec_() != QtGui.QDialog.Accepted:
            return
        printer.setFullPage(True)
        document.print_(printer)
        

    

class ReportOptionsDialog(QtGui.QDialog):
    def __init__(self, connection, chartclass):
        super(ReportOptionsDialog, self).__init__()
        self.connection = connection
        self.chartclass = chartclass
        self.users   = []
        self.classes = []
        self.servers = []
        self.groups  = []
        self.ports   = []
        self.opts    = {}
        self.start_date = datetime.datetime.now()
        self.end_date   = datetime.datetime.now()
        self.datetimeFormat = "dd" + dateDelim + "MM" + dateDelim + "yyyy hh:mm:ss"
        self.resize(475, 535)
        self.gridLayout_4 = QtGui.QGridLayout(self)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.NoButton|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.tabWidget = QtGui.QTabWidget(self)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setTabPosition(QtGui.QTabWidget.North)
        self.tabWidget.setTabShape(QtGui.QTabWidget.Rounded)
        self.mainTab = QtGui.QWidget()
        self.mainTab.setObjectName("mainTab")
        self.gridLayout_3 = QtGui.QGridLayout(self.mainTab)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.inter_groupBox = QtGui.QGroupBox(self.mainTab)
        self.inter_groupBox.setMaximumSize(QtCore.QSize(16777215, 100))
        self.inter_groupBox.setObjectName("inter_groupBox")
        self.gridLayout_2 = QtGui.QGridLayout(self.inter_groupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.from_label = QtGui.QLabel(self.inter_groupBox)
        self.from_label.setObjectName("from_label")
        self.gridLayout_2.addWidget(self.from_label, 0, 0, 1, 1)        
        self.to_label = QtGui.QLabel(self.inter_groupBox)
        self.to_label.setObjectName("to_label")
        self.gridLayout_2.addWidget(self.to_label, 1, 0, 1, 1)
        self.from_dateTimeEdit = CustomDateTimeWidget()
        #self.from_dateTimeEdit.setMinimumDate(QtCore.QDate(2008, 1, 1))
        #self.from_dateTimeEdit.setCalendarPopup(True)
        #self.from_dateTimeEdit.setDisplayFormat(self.datetimeFormat)
        #self.from_dateTimeEdit.calendarWidget().setFirstDayOfWeek(QtCore.Qt.Monday)
        dt_now = datetime.datetime.now()
        self.from_dateTimeEdit.setDate(QtCore.QDate(dt_now.year, dt_now.month, dt_now.day))
        self.from_dateTimeEdit.setObjectName("from_dateTimeEdit")
        self.gridLayout_2.addWidget(self.from_dateTimeEdit, 0, 1, 1, 1)
        self.to_dateTimeEdit = CustomDateTimeWidget()
        #self.to_dateTimeEdit.setMinimumDate(QtCore.QDate(2008, 1, 1))
        #self.to_dateTimeEdit.setCalendarPopup(True)
        #self.to_dateTimeEdit.setDisplayFormat(self.datetimeFormat)
        self.to_dateTimeEdit.setObjectName("to_dateTimeEdit")
        #self.to_dateTimeEdit.calendarWidget().setFirstDayOfWeek(QtCore.Qt.Monday)
        self.gridLayout_2.addWidget(self.to_dateTimeEdit, 1, 1, 1, 1)
        self.gridLayout.addWidget(self.inter_groupBox, 0, 0, 1, 2)

        try:
            settings = QtCore.QSettings("Expert Billing", "Expert Billing Client")
            self.from_dateTimeEdit.setDateTime(settings.value("chrep_date_start", QtCore.QVariant(QtCore.QDateTime(2000,1,1,0,0))).toDateTime())
            self.to_dateTimeEdit.setDateTime(settings.value("chrep_date_end", QtCore.QVariant(QtCore.QDateTime(2000,1,1,0,0))).toDateTime())
        except Exception, ex:
            print "Chart reports settings error: ", ex
        
        self.data_groupBox = QtGui.QGroupBox(self.mainTab)
        self.data_groupBox.setMaximumSize(QtCore.QSize(1000, 120))
        self.data_groupBox.setObjectName("data_groupBox")
        self.gridLayout_6 = QtGui.QGridLayout(self.data_groupBox)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.dgb_traffic_radioButton = QtGui.QRadioButton(self.data_groupBox)
        self.dgb_traffic_radioButton.setObjectName("dgb_traffic_radioButton")
        self.dgb_traffic_radioButton.setChecked(True)
        self.gridLayout_6.addWidget(self.dgb_traffic_radioButton, 0, 0, 1, 1)
        self.dgb_speed_radioButton = QtGui.QRadioButton(self.data_groupBox)
        self.dgb_speed_radioButton.setObjectName("dgb_speed_radioButton")
        self.gridLayout_6.addWidget(self.dgb_speed_radioButton, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.data_groupBox, 1, 0, 1, 1)
        self.layout_groupBox = QtGui.QGroupBox(self.mainTab)
        self.layout_groupBox.setMaximumSize(QtCore.QSize(1000, 120))
        self.layout_groupBox.setObjectName("layout_groupBox")
        self.gridLayout_5 = QtGui.QGridLayout(self.layout_groupBox)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.lgb_grid_checkBox = QtGui.QCheckBox(self.layout_groupBox)
        self.lgb_grid_checkBox.setObjectName("lgb_grid_checkBox")
        self.gridLayout_5.addWidget(self.lgb_grid_checkBox, 0, 0, 1, 1)
        self.lgb_antialias_checkBox = QtGui.QCheckBox(self.layout_groupBox)
        self.lgb_antialias_checkBox.setObjectName("lgb_antialias_checkBox")
        self.gridLayout_5.addWidget(self.lgb_antialias_checkBox, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.layout_groupBox, 1, 1, 1, 1)
        self.groupby_groupBox = QtGui.QGroupBox(self.mainTab)
        self.groupby_groupBox.setMaximumSize(QtCore.QSize(1000, 200))
        self.groupby_groupBox.setObjectName("groupby_groupBox")
        self.gridLayout_8 = QtGui.QGridLayout(self.groupby_groupBox)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.ggb_accounts_checkBox = QtGui.QCheckBox(self.groupby_groupBox)
        self.ggb_accounts_checkBox.setObjectName("ggb_accounts_checkBox")
        self.gridLayout_8.addWidget(self.ggb_accounts_checkBox, 0, 0, 1, 1)
        self.ggb_groups_checkBox = QtGui.QCheckBox(self.groupby_groupBox)
        self.ggb_groups_checkBox.setObjectName("ggb_groups_checkBox")
        self.gridLayout_8.addWidget(self.ggb_groups_checkBox, 1, 0, 1, 1)
        self.ggb_nas_checkBox = QtGui.QCheckBox(self.groupby_groupBox)
        self.ggb_nas_checkBox.setObjectName("ggb_nas_checkBox")
        self.gridLayout_8.addWidget(self.ggb_nas_checkBox, 2, 0, 1, 1)
        self.ggb_classes_checkBox = QtGui.QCheckBox(self.groupby_groupBox)
        self.ggb_classes_checkBox.setObjectName("ggb_classes_checkBox")
        self.gridLayout_8.addWidget(self.ggb_classes_checkBox, 3, 0, 1, 1)
        self.gridLayout.addWidget(self.groupby_groupBox, 2, 0, 1, 1)
        self.traffic_groupBox = QtGui.QGroupBox(self.mainTab)
        self.traffic_groupBox.setMaximumSize(QtCore.QSize(16777215, 200))
        self.traffic_groupBox.setObjectName("traffic_groupBox")
        self.gridLayout_7 = QtGui.QGridLayout(self.traffic_groupBox)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.gbt_input_radioButton = QtGui.QRadioButton(self.traffic_groupBox)
        self.gbt_input_radioButton.setObjectName("gbt_input_radioButton")
        self.gridLayout_7.addWidget(self.gbt_input_radioButton, 0, 0, 1, 1)
        self.tgb_output_radioButton = QtGui.QRadioButton(self.traffic_groupBox)
        self.tgb_output_radioButton.setObjectName("tgb_output_radioButton")
        self.gridLayout_7.addWidget(self.tgb_output_radioButton, 1, 0, 1, 1)
        self.tgb_sum_radioButton = QtGui.QRadioButton(self.traffic_groupBox)
        self.tgb_sum_radioButton.setObjectName("tgb_sum_radioButton")
        self.tgb_sum_radioButton.setChecked(True)
        self.gridLayout_7.addWidget(self.tgb_sum_radioButton, 2, 0, 1, 1)
        self.tgb_max_radioButton = QtGui.QRadioButton(self.traffic_groupBox)
        self.tgb_max_radioButton.setObjectName("tgb_max_radioButton")
        self.gridLayout_7.addWidget(self.tgb_max_radioButton, 3, 0, 1, 1)
        self.gridLayout.addWidget(self.traffic_groupBox, 2, 1, 1, 1)
        self.gridLayout_3.addLayout(self.gridLayout, 1, 0, 1, 1)
        self.tmp_groupBox_2 = QtGui.QGroupBox(self.mainTab)
        self.tmp_groupBox_2.setVisible(False)
        self.tmp_groupBox_2.setMaximumSize(QtCore.QSize(16777215, 40))
        self.tmp_groupBox_2.setObjectName("tmp_groupBox_2")
        self.gridLayout_3.addWidget(self.tmp_groupBox_2, 3, 0, 1, 1)
        self.tmp_groupBox_3 = QtGui.QGroupBox(self.mainTab)
        self.tmp_groupBox_3.setVisible(False)
        self.tmp_groupBox_3.setMaximumSize(QtCore.QSize(16777215, 20))
        self.tmp_groupBox_3.setObjectName("tmp_groupBox_3")
        self.gridLayout_3.addWidget(self.tmp_groupBox_3, 0, 0, 1, 1)

        self.tabWidget.addTab(self.mainTab,"")

        self.usersTab = QtGui.QWidget()
        self.usersTab.setObjectName("usersTab")

        self.all_users_listWidget = QtGui.QListWidget(self.usersTab)
        self.all_users_listWidget.setGeometry(QtCore.QRect(10,30,181,401))
        self.all_users_listWidget.setObjectName("all_users_listWidget")
        self.all_users_listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.all_users_listWidget.setSelectionRectVisible(True)

        self.selected_users_listWidget = QtGui.QListWidget(self.usersTab)
        self.selected_users_listWidget.setGeometry(QtCore.QRect(240,30,191,401))
        self.selected_users_listWidget.setObjectName("selected_users_listWidget")
        self.selected_users_listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.selected_users_listWidget.setSelectionRectVisible(True)

        self.add_user_toolButton = QtGui.QToolButton(self.usersTab)
        self.add_user_toolButton.setGeometry(QtCore.QRect(200,160,27,23))
        self.add_user_toolButton.setObjectName("add_user_toolButton")

        self.del_user_toolButton = QtGui.QToolButton(self.usersTab)
        self.del_user_toolButton.setGeometry(QtCore.QRect(200,200,27,23))
        self.del_user_toolButton.setObjectName("del_user_toolButton")

        self.all_users_label = QtGui.QLabel(self.usersTab)
        self.all_users_label.setGeometry(QtCore.QRect(10,10,171,18))
        self.all_users_label.setObjectName("all_users_label")

        self.selected_users_label = QtGui.QLabel(self.usersTab)
        self.selected_users_label.setGeometry(QtCore.QRect(240,10,191,18))
        self.selected_users_label.setObjectName("selected_users_label")
        self.tabWidget.addTab(self.usersTab,"")

        self.serversTab = QtGui.QWidget()
        self.serversTab.setObjectName("serversTab")

        self.selected_servers_listWidget = QtGui.QListWidget(self.serversTab)
        self.selected_servers_listWidget.setGeometry(QtCore.QRect(240,30,191,401))
        self.selected_servers_listWidget.setObjectName("selected_servers_listWidget")
        self.selected_servers_listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.selected_servers_listWidget.setSelectionRectVisible(True)

        self.all_servers_listWidget = QtGui.QListWidget(self.serversTab)
        self.all_servers_listWidget.setGeometry(QtCore.QRect(10,30,181,401))
        self.all_servers_listWidget.setObjectName("all_servers_listWidget")
        self.all_servers_listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.all_servers_listWidget.setSelectionRectVisible(True)

        self.del_server_toolButton = QtGui.QToolButton(self.serversTab)
        self.del_server_toolButton.setGeometry(QtCore.QRect(200,200,27,23))
        self.del_server_toolButton.setObjectName("del_server_toolButton")

        self.add_server_toolButton = QtGui.QToolButton(self.serversTab)
        self.add_server_toolButton.setGeometry(QtCore.QRect(200,160,27,23))
        self.add_server_toolButton.setObjectName("add_server_toolButton")

        self.all_servers_label = QtGui.QLabel(self.serversTab)
        self.all_servers_label.setGeometry(QtCore.QRect(10,10,151,18))
        self.all_servers_label.setObjectName("all_servers_label")

        self.selected_servers_label = QtGui.QLabel(self.serversTab)
        self.selected_servers_label.setGeometry(QtCore.QRect(240,10,151,18))
        self.selected_servers_label.setObjectName("selected_servers_label")
        self.tabWidget.addTab(self.serversTab,"")

        self.classesTab = QtGui.QWidget()
        self.classesTab.setObjectName("classesTab")

        self.all_classes_label = QtGui.QLabel(self.classesTab)
        self.all_classes_label.setGeometry(QtCore.QRect(10,10,151,18))
        self.all_classes_label.setObjectName("all_classes_label")

        self.all_classes_listWidget = QtGui.QListWidget(self.classesTab)
        self.all_classes_listWidget.setGeometry(QtCore.QRect(10,30,181,401))
        self.all_classes_listWidget.setObjectName("all_classes_listWidget")
        self.all_classes_listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.all_classes_listWidget.setSelectionRectVisible(True)

        self.del_class_toolButton = QtGui.QToolButton(self.classesTab)
        self.del_class_toolButton.setGeometry(QtCore.QRect(200,200,27,23))
        self.del_class_toolButton.setObjectName("del_class_toolButton")

        self.add_class_toolButton = QtGui.QToolButton(self.classesTab)
        self.add_class_toolButton.setGeometry(QtCore.QRect(200,160,27,23))
        self.add_class_toolButton.setObjectName("add_class_toolButton")

        self.selected_classes_label = QtGui.QLabel(self.classesTab)
        self.selected_classes_label.setGeometry(QtCore.QRect(240,10,191,18))
        self.selected_classes_label.setObjectName("selected_classes_label")

        self.selected_classes_listWidget = QtGui.QListWidget(self.classesTab)
        self.selected_classes_listWidget.setGeometry(QtCore.QRect(240,30,191,401))
        self.selected_classes_listWidget.setObjectName("selected_classes_listWidget")
        self.selected_classes_listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.selected_classes_listWidget.setSelectionRectVisible(True)
        self.tabWidget.addTab(self.classesTab,"")
        
        
        self.groupsTab = QtGui.QWidget()
        self.groupsTab.setObjectName("groupsTab")

        self.all_groups_label = QtGui.QLabel(self.groupsTab)
        self.all_groups_label.setGeometry(QtCore.QRect(10,10,151,18))
        self.all_groups_label.setObjectName("all_groups_label")

        self.all_groups_listWidget = QtGui.QListWidget(self.groupsTab)
        self.all_groups_listWidget.setGeometry(QtCore.QRect(10,30,181,401))
        self.all_groups_listWidget.setObjectName("all_groups_listWidget")
        self.all_groups_listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.all_groups_listWidget.setSelectionRectVisible(True)

        self.del_group_toolButton = QtGui.QToolButton(self.groupsTab)
        self.del_group_toolButton.setGeometry(QtCore.QRect(200,200,27,23))
        self.del_group_toolButton.setObjectName("del_group_toolButton")

        self.add_group_toolButton = QtGui.QToolButton(self.groupsTab)
        self.add_group_toolButton.setGeometry(QtCore.QRect(200,160,27,23))
        self.add_group_toolButton.setObjectName("add_group_toolButton")

        self.selected_groups_label = QtGui.QLabel(self.groupsTab)
        self.selected_groups_label.setGeometry(QtCore.QRect(240,10,191,18))
        self.selected_groups_label.setObjectName("selected_groups_label")

        self.selected_groups_listWidget = QtGui.QListWidget(self.groupsTab)
        self.selected_groups_listWidget.setGeometry(QtCore.QRect(240,30,191,401))
        self.selected_groups_listWidget.setObjectName("selected_groups_listWidget")
        self.selected_groups_listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.selected_groups_listWidget.setSelectionRectVisible(True)
        self.tabWidget.addTab(self.groupsTab,"")

        self.portsTab = QtGui.QWidget()
        self.portsTab.setObjectName("portsTab")

        self.ports_groupBox = QtGui.QGroupBox(self.portsTab)
        self.ports_groupBox.setGeometry(QtCore.QRect(10,10,421,361))
        self.ports_groupBox.setObjectName("ports_groupBox")

        self.ports_listWidget = QtGui.QListWidget(self.ports_groupBox)
        self.ports_listWidget.setGeometry(QtCore.QRect(10,20,251,331))
        self.ports_listWidget.setObjectName("ports_listWidget")

        self.ports_description_label = QtGui.QLabel(self.ports_groupBox)
        self.ports_description_label.setGeometry(QtCore.QRect(270,20,141,331))
        self.ports_description_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.ports_description_label.setWordWrap(True)
        self.ports_description_label.setObjectName("ports_description_label")

        self.extra_ports_lineEdit = QtGui.QLineEdit(self.portsTab)
        self.extra_ports_lineEdit.setGeometry(QtCore.QRect(10,400,391,23))
        self.extra_ports_lineEdit.setObjectName("extra_ports_lineEdit")

        self.extra_ports_label = QtGui.QLabel(self.portsTab)
        self.extra_ports_label.setGeometry(QtCore.QRect(10,380,287,18))
        self.extra_ports_label.setObjectName("extra_ports_label")
        self.tabWidget.addTab(self.portsTab,"")
        self.to_label.setBuddy(self.to_dateTimeEdit)
        self.from_label.setBuddy(self.from_dateTimeEdit)
        
        self.gridLayout_4.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.gridLayout_4.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi()
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox,QtCore.SIGNAL("accepted()"),self.accept)
        QtCore.QObject.connect(self.buttonBox,QtCore.SIGNAL("rejected()"),self.reject)
        
        QtCore.QObject.connect(self.add_user_toolButton, QtCore.SIGNAL("clicked()"),self.addUser)
        QtCore.QObject.connect(self.del_user_toolButton, QtCore.SIGNAL("clicked()"),self.delUser)

        QtCore.QObject.connect(self.all_users_listWidget, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"),self.addUser)
        QtCore.QObject.connect(self.selected_users_listWidget, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"),self.delUser)        
        

        QtCore.QObject.connect(self.add_class_toolButton, QtCore.SIGNAL("clicked()"), self.addClass)
        QtCore.QObject.connect(self.del_class_toolButton, QtCore.SIGNAL("clicked()"), self.delClass)
        
        QtCore.QObject.connect(self.all_classes_listWidget, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.addClass)
        QtCore.QObject.connect(self.selected_classes_listWidget, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.delClass)
        
        QtCore.QObject.connect(self.add_group_toolButton, QtCore.SIGNAL("clicked()"), self.addGroup)
        QtCore.QObject.connect(self.del_group_toolButton, QtCore.SIGNAL("clicked()"), self.delGroup)
        
        QtCore.QObject.connect(self.all_groups_listWidget, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.addGroup)
        QtCore.QObject.connect(self.selected_groups_listWidget, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.delGroup)
        
        QtCore.QObject.connect(self.add_server_toolButton, QtCore.SIGNAL("clicked()"), self.addServer)
        QtCore.QObject.connect(self.del_server_toolButton, QtCore.SIGNAL("clicked()"), self.delServer)
        
        QtCore.QObject.connect(self.all_servers_listWidget, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.addServer)
        QtCore.QObject.connect(self.selected_servers_listWidget, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.delServer)
        
        self.chkButtons = [self.ggb_accounts_checkBox, self.ggb_groups_checkBox, self.ggb_nas_checkBox, self.ggb_classes_checkBox]
        self.chkLambdas = [lambda bl: self.chbToggled(bl, 0), lambda bl: self.chbToggled(bl,1), lambda bl: self.chbToggled(bl,2), lambda bl: self.chbToggled(bl, 3)]
        counter = itertools.count()
        for btn in self.chkButtons:
            QtCore.QObject.connect(btn, QtCore.SIGNAL("clicked(bool)"), self.chkLambdas[counter.next()])
        if 1:
            self.setTabOrder(self.tabWidget, self.from_dateTimeEdit)
            self.setTabOrder(self.from_dateTimeEdit, self.to_dateTimeEdit)
            self.setTabOrder(self.to_dateTimeEdit, self.dgb_traffic_radioButton)
            self.setTabOrder(self.dgb_traffic_radioButton, self.dgb_speed_radioButton)
            self.setTabOrder(self.dgb_speed_radioButton, self.lgb_grid_checkBox)
            self.setTabOrder(self.lgb_grid_checkBox, self.lgb_antialias_checkBox)
            self.setTabOrder(self.lgb_antialias_checkBox, self.ggb_accounts_checkBox)
            self.setTabOrder(self.ggb_accounts_checkBox, self.ggb_groups_checkBox)
            self.setTabOrder(self.ggb_groups_checkBox, self.ggb_nas_checkBox)
            self.setTabOrder(self.ggb_nas_checkBox, self.ggb_classes_checkBox)
            self.setTabOrder(self.ggb_classes_checkBox, self.gbt_input_radioButton)
            self.setTabOrder(self.gbt_input_radioButton, self.tgb_output_radioButton)
            self.setTabOrder(self.tgb_output_radioButton, self.tgb_sum_radioButton)
            self.setTabOrder(self.tgb_sum_radioButton, self.tgb_max_radioButton)
            self.setTabOrder(self.tgb_max_radioButton, self.add_user_toolButton)
            self.setTabOrder(self.all_users_listWidget,self.add_user_toolButton)
            self.setTabOrder(self.add_user_toolButton,self.del_user_toolButton)
            self.setTabOrder(self.del_user_toolButton,self.selected_users_listWidget)
            self.setTabOrder(self.selected_users_listWidget,self.all_servers_listWidget)
            self.setTabOrder(self.all_servers_listWidget,self.add_server_toolButton)
            self.setTabOrder(self.add_server_toolButton,self.del_server_toolButton)
            self.setTabOrder(self.del_server_toolButton,self.selected_servers_listWidget)
            self.setTabOrder(self.selected_servers_listWidget,self.all_classes_listWidget)
            self.setTabOrder(self.all_classes_listWidget,self.add_class_toolButton)
            self.setTabOrder(self.add_class_toolButton,self.del_class_toolButton)
            self.setTabOrder(self.del_class_toolButton,self.selected_classes_listWidget)
            self.setTabOrder(self.selected_classes_listWidget,self.all_groups_listWidget)
            self.setTabOrder(self.all_groups_listWidget,self.add_group_toolButton)
            self.setTabOrder(self.add_group_toolButton,self.del_group_toolButton)
            self.setTabOrder(self.del_group_toolButton,self.selected_groups_listWidget)
            self.setTabOrder(self.selected_groups_listWidget,self.ports_listWidget)
            self.setTabOrder(self.ports_listWidget,self.extra_ports_lineEdit)
            self.setTabOrder(self.extra_ports_lineEdit,self.buttonBox)
        self.fixtures()

    def retranslateUi(self):
        self.setWindowTitle(QtGui.QApplication.translate("Dialog", "Настройки отчёта", None, QtGui.QApplication.UnicodeUTF8))
        self.data_groupBox.setTitle(QtGui.QApplication.translate("Dialog", "Данные", None, QtGui.QApplication.UnicodeUTF8))
        self.dgb_traffic_radioButton.setText(QtGui.QApplication.translate("Dialog", "Трафик", None, QtGui.QApplication.UnicodeUTF8))
        self.dgb_speed_radioButton.setText(QtGui.QApplication.translate("Dialog", "Скорость", None, QtGui.QApplication.UnicodeUTF8))
        self.layout_groupBox.setTitle(QtGui.QApplication.translate("Dialog", "Внешний вид", None, QtGui.QApplication.UnicodeUTF8))
        self.lgb_grid_checkBox.setText(QtGui.QApplication.translate("Dialog", "Сетка", None, QtGui.QApplication.UnicodeUTF8))
        self.lgb_antialias_checkBox.setText(QtGui.QApplication.translate("Dialog", "Сглаживание", None, QtGui.QApplication.UnicodeUTF8))
        self.groupby_groupBox.setTitle(QtGui.QApplication.translate("Dialog", "Группировать по...", None, QtGui.QApplication.UnicodeUTF8))
        self.ggb_accounts_checkBox.setText(QtGui.QApplication.translate("Dialog", "Клиенты", None, QtGui.QApplication.UnicodeUTF8))
        self.ggb_groups_checkBox.setText(QtGui.QApplication.translate("Dialog", "Группы", None, QtGui.QApplication.UnicodeUTF8))
        self.ggb_nas_checkBox.setText(QtGui.QApplication.translate("Dialog", "NAS", None, QtGui.QApplication.UnicodeUTF8))
        self.ggb_classes_checkBox.setText(QtGui.QApplication.translate("Dialog", "Классы", None, QtGui.QApplication.UnicodeUTF8))
        self.traffic_groupBox.setTitle(QtGui.QApplication.translate("Dialog", "Трафик", None, QtGui.QApplication.UnicodeUTF8))
        self.gbt_input_radioButton.setText(QtGui.QApplication.translate("Dialog", "Только входящий", None, QtGui.QApplication.UnicodeUTF8))
        self.tgb_output_radioButton.setText(QtGui.QApplication.translate("Dialog", "Только исходящий", None, QtGui.QApplication.UnicodeUTF8))
        self.tgb_sum_radioButton.setText(QtGui.QApplication.translate("Dialog", "Сумма", None, QtGui.QApplication.UnicodeUTF8))
        self.tgb_max_radioButton.setText(QtGui.QApplication.translate("Dialog", "Наибольший", None, QtGui.QApplication.UnicodeUTF8))
        self.inter_groupBox.setTitle(QtGui.QApplication.translate("Dialog", "Интервал", None, QtGui.QApplication.UnicodeUTF8))
        self.from_label.setText(QtGui.QApplication.translate("Dialog", "Начало:", None, QtGui.QApplication.UnicodeUTF8))
        self.from_dateTimeEdit.setDisplayFormat(QtGui.QApplication.translate("Dialog", "yyyy-MM-dd H:mm:ss", None, QtGui.QApplication.UnicodeUTF8))
        self.to_dateTimeEdit.setDisplayFormat(QtGui.QApplication.translate("Dialog", "yyyy-MM-dd H:mm:ss", None, QtGui.QApplication.UnicodeUTF8))
        self.to_label.setText(QtGui.QApplication.translate("Dialog", "Конец:", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.mainTab), QtGui.QApplication.translate("Dialog", "Общее", None, QtGui.QApplication.UnicodeUTF8))
        self.add_user_toolButton.setText(QtGui.QApplication.translate("Dialog", ">", None, QtGui.QApplication.UnicodeUTF8))
        self.del_user_toolButton.setText(QtGui.QApplication.translate("Dialog", "<", None, QtGui.QApplication.UnicodeUTF8))
        self.all_users_label.setText(QtGui.QApplication.translate("Dialog", "Доступные пользователи", None, QtGui.QApplication.UnicodeUTF8))
        self.selected_users_label.setText(QtGui.QApplication.translate("Dialog", "Выбранные пользователи", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.usersTab), QtGui.QApplication.translate("Dialog", "Пользователи", None, QtGui.QApplication.UnicodeUTF8))
        self.del_server_toolButton.setText(QtGui.QApplication.translate("Dialog", "<", None, QtGui.QApplication.UnicodeUTF8))
        self.add_server_toolButton.setText(QtGui.QApplication.translate("Dialog", ">", None, QtGui.QApplication.UnicodeUTF8))
        self.all_servers_label.setText(QtGui.QApplication.translate("Dialog", "Доступные серверы", None, QtGui.QApplication.UnicodeUTF8))
        self.selected_servers_label.setText(QtGui.QApplication.translate("Dialog", "Выбранные серверы", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.serversTab), QtGui.QApplication.translate("Dialog", "Серверы доступа", None, QtGui.QApplication.UnicodeUTF8))
        self.all_classes_label.setText(QtGui.QApplication.translate("Dialog", "Доступные классы", None, QtGui.QApplication.UnicodeUTF8))
        self.del_class_toolButton.setText(QtGui.QApplication.translate("Dialog", "<", None, QtGui.QApplication.UnicodeUTF8))
        self.add_class_toolButton.setText(QtGui.QApplication.translate("Dialog", ">", None, QtGui.QApplication.UnicodeUTF8))
        self.selected_classes_label.setText(QtGui.QApplication.translate("Dialog", "Выбранные классы", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.classesTab), QtGui.QApplication.translate("Dialog", "Классы", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.groupsTab), QtGui.QApplication.translate("Dialog", "Группы", None, QtGui.QApplication.UnicodeUTF8))
        self.all_groups_label.setText(QtGui.QApplication.translate("Dialog", "Доступные группы", None, QtGui.QApplication.UnicodeUTF8))
        self.del_group_toolButton.setText(QtGui.QApplication.translate("Dialog", "<", None, QtGui.QApplication.UnicodeUTF8))
        self.add_group_toolButton.setText(QtGui.QApplication.translate("Dialog", ">", None, QtGui.QApplication.UnicodeUTF8))
        self.selected_groups_label.setText(QtGui.QApplication.translate("Dialog", "Выбранные группы", None, QtGui.QApplication.UnicodeUTF8))
        self.ports_groupBox.setTitle(QtGui.QApplication.translate("Dialog", "Выберите порты", None, QtGui.QApplication.UnicodeUTF8))
        self.ports_description_label.setText(QtGui.QApplication.translate("Dialog", "Отметьте флажками нужные порты", None, QtGui.QApplication.UnicodeUTF8))
        self.extra_ports_label.setText(QtGui.QApplication.translate("Dialog", "Введите дополнительные порты через запятую:", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.portsTab), QtGui.QApplication.translate("Dialog", "Порты", None, QtGui.QApplication.UnicodeUTF8))

    def fixtures(self):
        
        chOpts = _chartopts[self.chartclass]
        hidetabs  = chOpts[0]
        hideelems = chOpts[1]
        #self.data_groupBox.setEnabled(False)
        for hidetab in hidetabs:
            htObj = getattr(self, hidetab, None)
            self.tabWidget.removeTab(self.tabWidget.indexOf(htObj))
            
        for hideelem in hideelems:
            heObj = getattr(self, hideelem, None)
            if heObj:
                heObj.setEnabled(False)
            
            
        if "usersTab" not in hidetabs:
            users = self.connection.sql(_querydict['get_usernames'])
            
            for user in users:
                item = QtGui.QListWidgetItem()
                item.setText(user.username)
                item.id = user.id
                self.all_users_listWidget.addItem(item)
            
        if "classesTab" not in hidetabs:
            classes = self.connection.sql(_querydict['get_classes'])
            
            for clas in classes:
                item = QtGui.QListWidgetItem()
                item.setText(clas.name)
                item.id = clas.id
                self.all_classes_listWidget.addItem(item)
          
        if "serversTab" not in hidetabs:        
            servers = self.connection.sql(_querydict['get_nas'])
            
            for serv in servers:
                item = QtGui.QListWidgetItem()
                item.setText(serv.name)
                item.id = serv.id
                self.all_servers_listWidget.addItem(item)
                
        if "groupsTab" not in hidetabs:
            groups = self.connection.sql(_querydict['get_groups'])
            for grp in groups:
                item = QtGui.QListWidgetItem()
                item.setText(grp.name)
                item.id = grp.id
                self.all_groups_listWidget.addItem(item)
                
        if "portsTab" not in hidetabs:  
            for port in _ports:
                item = QtGui.QListWidgetItem()
                item.setText(port[1])
                item.id = port[0]
                item.setCheckState(QtCore.Qt.Unchecked)
                self.ports_listWidget.addItem(item)
        
    def addUser(self):
        selected_items = self.all_users_listWidget.selectedItems()        
        for item in selected_items:
            self.all_users_listWidget.takeItem(self.all_users_listWidget.row(item))
            self.selected_users_listWidget.addItem(item)
            
        self.selected_users_listWidget.sortItems()
        
    def delUser(self):
        selected_items = self.selected_users_listWidget.selectedItems()        
        for item in selected_items:
            self.selected_users_listWidget.takeItem(self.selected_users_listWidget.row(item))
            self.all_users_listWidget.addItem(item)
        self.all_users_listWidget.sortItems()
        
    def addServer(self):
        selected_items = self.all_servers_listWidget.selectedItems()        
        for item in selected_items:
            self.all_servers_listWidget.takeItem(self.all_servers_listWidget.row(item))
            self.selected_servers_listWidget.addItem(item)
            
        self.selected_servers_listWidget.sortItems()
        
    def delServer(self):
        selected_items = self.selected_servers_listWidget.selectedItems()        
        for item in selected_items:
            self.selected_servers_listWidget.takeItem(self.selected_servers_listWidget.row(item))
            self.all_servers_listWidget.addItem(item)
        self.all_servers_listWidget.sortItems()
        
    def addClass(self):       
        selected_items = self.all_classes_listWidget.selectedItems()
        for item in selected_items:
            self.all_classes_listWidget.takeItem(self.all_classes_listWidget.row(item))
            self.selected_classes_listWidget.addItem(item)
        self.selected_classes_listWidget.sortItems()
        
    def delClass(self):
        selected_items = self.selected_classes_listWidget.selectedItems()
        for item in selected_items:
            self.selected_classes_listWidget.takeItem(self.selected_classes_listWidget.row(item))
            self.all_classes_listWidget.addItem(item)
        self.all_classes_listWidget.sortItems()
        
    def addGroup(self):                
        selected_items = self.all_groups_listWidget.selectedItems()        
        for item in selected_items:
            self.all_groups_listWidget.takeItem(self.all_groups_listWidget.row(item))
            self.selected_groups_listWidget.addItem(item)            
        self.selected_groups_listWidget.sortItems()      
        
    def delGroup(self):
        selected_items = self.selected_groups_listWidget.selectedItems()        
        for item in selected_items:
            self.selected_groups_listWidget.takeItem(self.selected_groups_listWidget.row(item))
            self.all_groups_listWidget.addItem(item)
        self.all_groups_listWidget.sortItems()
        
    def chbToggled(self, toggled, btn_id):
        if toggled:
            for counter, btn in izip(count(), self.chkButtons):
                if btn.isChecked() and (btn_id != counter):
                    btn.setChecked(False)
                    
    def accept(self):
        #check the buttons!
        self.users   = []
        self.classes = []
        self.servers = []
        self.ports   = []
        self.groups  = []
        self.opts    = {}
        
        buttons ={'speed' :{self.dgb_traffic_radioButton:False, self.dgb_speed_radioButton:True}, \
                  'by_col':{self.ggb_accounts_checkBox:'users', self.ggb_groups_checkBox:'groups', self.ggb_nas_checkBox:'servers', self.ggb_classes_checkBox:'classes'}, \
                  'gtype' :{self.gbt_input_radioButton:1, self.tgb_output_radioButton:2, self.tgb_sum_radioButton:3, self.tgb_max_radioButton:4}}
        
        for ckey, vdct in buttons.iteritems():
            for bkey, bval in vdct.iteritems():
                if bkey.isChecked():
                    self.opts[ckey] = bval
                    break

        for x in xrange(0, self.selected_users_listWidget.count()):
            self.users.append(self.selected_users_listWidget.item(x).id)
            
        for x in xrange(0, self.selected_classes_listWidget.count()):
            self.classes.append(self.selected_classes_listWidget.item(x).id)
            
        for x in xrange(0, self.selected_servers_listWidget.count()):
            self.servers.append(self.selected_servers_listWidget.item(x).id)
            
        for x in xrange(0, self.selected_groups_listWidget.count()):
            self.groups.append(self.selected_groups_listWidget.item(x).id)
            
        for x in xrange(0, self.ports_listWidget.count()):
            if self.ports_listWidget.item(x).checkState() == 2:
                self.ports.append(self.ports_listWidget.item(x).id)
                
        if self.extra_ports_lineEdit.text():
            try:
                extra_ports_str = self.extra_ports_lineEdit.text().split(',')
            except Exception, ex:
                raise ex
            extra_ports = []
            for eps in extra_ports_str:
                try:
                    extra_ports.append(int(eps))
                except Exception, ex:
                    print ex
            for eport in extra_ports:
                if eport not in self.ports: self.ports.append(eport)
                
            
                    
        try:
            settings = QtCore.QSettings("Expert Billing", "Expert Billing Client")
            settings.setValue("chrep_date_start", QtCore.QVariant(self.from_dateTimeEdit.dateTime()))
            settings.setValue("chrep_date_end", QtCore.QVariant(self.to_dateTimeEdit.dateTime()))
        except Exception, ex:
            print "Chart reports settings save error: ", ex
            
        self.start_date = self.from_dateTimeEdit.currentDate()
        self.end_date   = self.to_dateTimeEdit.currentDate()

        QtGui.QDialog.accept(self)
        
        
class LogViewWindow(QtGui.QMainWindow):
    def __init__(self, connection):
        super(LogViewWindow, self).__init__()
        self.connection = connection
        self.setObjectName("LogViewWindow")
        self.resize(800, 600)
        self.centralwidget = QtGui.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.plainTextEdit = QtGui.QPlainTextEdit(self.centralwidget)
        self.plainTextEdit.setReadOnly(True)
        self.plainTextEdit.setBackgroundVisible(False)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.gridLayout.addWidget(self.plainTextEdit, 1, 0, 1, 2)
        self.groupBox = QtGui.QGroupBox(self.centralwidget)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)
        self.comboBox = QtGui.QComboBox(self.groupBox)
        self.comboBox.setObjectName("comboBox")
        self.gridLayout_2.addWidget(self.comboBox, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout_2.addWidget(self.label_2, 0, 2, 1, 1)
        self.spinBox = QtGui.QSpinBox(self.groupBox)
        self.spinBox.setMinimumSize(QtCore.QSize(100, 0))
        self.spinBox.setObjectName("spinBox")
        self.spinBox.setMaximum(10000000)
        self.spinBox.setValue(100)
        self.gridLayout_2.addWidget(self.spinBox, 0, 3, 1, 1)
        self.checkBox = QtGui.QCheckBox(self.groupBox)
        self.checkBox.setObjectName("checkBox")
        self.gridLayout_2.addWidget(self.checkBox, 0, 4, 1, 1)
        self.pushButton = QtGui.QPushButton(self.groupBox)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout_2.addWidget(self.pushButton, 0, 6, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 5, 1, 1)
        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 2)
        self.setCentralWidget(self.centralwidget)
        
        self.connect(self.pushButton, QtCore.SIGNAL("clicked()"), self.get_tail)
        self.connect(self.checkBox, QtCore.SIGNAL("stateChanged(int)"), self.checkbox_action)
        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)
        self.fixtures()

    def retranslateUi(self):
        self.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Просмотр лог-файлов", None, QtGui.QApplication.UnicodeUTF8))
        #self.plainTextEdit.setPlainText(QtGui.QApplication.translate("MainWindow", "цукцукцук", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("MainWindow", "Параметры", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MainWindow", "Имя лог-файла", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("MainWindow", "Количество последних строк", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox.setText(QtGui.QApplication.translate("MainWindow", "Всё", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("MainWindow", "Получить с сервера", None, QtGui.QApplication.UnicodeUTF8))


    def checkbox_action(self):
        if self.checkBox.isChecked():
            self.spinBox.setDisabled(True)
        else:
            self.spinBox.setDisabled(False)
    def fixtures(self):
        #self.connection
        
        logs = self.connection.list_logfiles()
        #print logs
        i=0
        for log in logs:
           self.comboBox.addItem(unicode(log))
           self.comboBox.setItemData(i, QtCore.QVariant(log))
           i+=1

    def get_tail(self):
        
        log_name = unicode(self.comboBox.itemData(self.comboBox.currentIndex()).toString())

        log_count = int(self.spinBox.value())

        if self.checkBox.isChecked()==True:
            a = self.connection.get_tail_log(log_name, log_count, all_file = True)
        else:
            a = self.connection.get_tail_log(log_name, log_count)
        #print a
        u = a[1]
        self.plainTextEdit.setPlainText(u)
        #self.plainTextEdit.setPla
        
        
class SimpleReportEbs(ebsTableWindow):
    def __init__(self, connection, report_type='radius_authlog', account_id=None, subaccount_id=None, nas_id=None):
        self.report_type=report_type
        self.connection=connection
        self.account_id = account_id
        if self.report_type=='radius_authlog':
            columns=[u'#', u'Аккаунт', u"Субаккаунт", u'Сервер доступа', u'Способ доступа', u'Тип события', u"Событие", u'Дата']
            initargs = {"setname":"%s_frame_header" % self.report_type, "objname":"%sSimpleReportEbs" % self.report_type, "winsize":(0,0,903,483), "wintitle":"История авторизаций пользователя пользователя", "tablecolumns":columns}
            #self.transactions_types = [u"Другие операции", u"Периодические услуги", u"Разовые услуги", u"За трафик", u"За время", u"Подключаемые услуги"]
            #self.transactions_tables = [u"billservice_transaction",u"billservice_periodicalservicehistory",u"billservice_onetimeservicehistory",u"billservice_traffictransaction",u"billservice_timetransaction","billservice_addonservicetransaction"]
        elif  self.report_type=='balance_log':
            columns=[u'#', u'Аккаунт', u"Новый баланс", u'Дата']
            initargs = {"setname":"%s_frame_header" % self.report_type, "objname":"%sSimpleReportEbs" % self.report_type, "winsize":(0,0,903,483), "wintitle":"История изменения баланса", "tablecolumns":columns}
            
        super(SimpleReportEbs, self).__init__(connection, initargs)
        
    def ebsInterInit(self, initargs):
        
        self.comboBox_account = QtGui.QComboBox(self)
        self.comboBox_account.setGeometry(QtCore.QRect(100,12,201,20))
        self.comboBox_account.setObjectName("comboBox_account")    
        
        dt_now = datetime.datetime.now()
        
        self.dateTimeEdit_date_start = CustomDateTimeWidget()
        self.dateTimeEdit_date_start.setGeometry(QtCore.QRect(420,9,161,20))
        #self.dateTimeEdit_date_start.setCalendarPopup(True)
        self.dateTimeEdit_date_start.setObjectName("dateTimeEdit_date_start")
        #self.dateTimeEdit_date_start.calendarWidget().setFirstDayOfWeek(QtCore.Qt.Monday)

        self.dateTimeEdit_date_end = CustomDateTimeWidget()
        self.dateTimeEdit_date_end.setGeometry(QtCore.QRect(420,42,161,20))
        self.dateTimeEdit_date_end.setDate(QtCore.QDate(dt_now.year, dt_now.month, dt_now.day))
        #self.dateTimeEdit_date_end.setButtonSymbols(QtGui.QAbstractSpinBox.PlusMinus)
        #self.dateTimeEdit_date_end.setCalendarPopup(True)
        self.dateTimeEdit_date_end.setObjectName("dateTimeEdit_date_end")
        #self.dateTimeEdit_date_end.calendarWidget().setFirstDayOfWeek(QtCore.Qt.Monday)
        
        try:
            settings = QtCore.QSettings("Expert Billing", "Expert Billing Client")
            self.dateTimeEdit_date_start.setDateTime(settings.value("%strans_date_start" % self.report_type, QtCore.QVariant(QtCore.QDateTime(2010,1,1,0,0))).toDateTime())
            self.dateTimeEdit_date_end.setDateTime(settings.value("%strans_date_end" % self.report_type, QtCore.QVariant(QtCore.QDateTime(2010,1,1,0,0))).toDateTime())
        except Exception, ex:
            print "Transactions settings error: ", ex
        
        self.label_date_start = QtGui.QLabel(self)
        self.label_date_start.setMargin(10)
        self.label_date_start.setObjectName("label_date_start")

        self.label_date_end = QtGui.QLabel(self)
        self.label_date_end.setMargin(10)
        self.label_date_end.setObjectName("label_date_end")

        self.label_account = QtGui.QLabel(self)
        self.label_account.setMargin(10)
        self.label_account.setObjectName("user_label")
        """
        self.label_transactions_type = QtGui.QLabel(self)
        self.label_transactions_type.setMargin(10)

        self.label_cashier = QtGui.QLabel(self)
        self.label_cashier.setMargin(10)
           
        self.comboBox_transactions_type = QtGui.QComboBox(self)
        self.comboBox_cashier = QtGui.QComboBox(self)
        """
        
        self.go_pushButton = QtGui.QPushButton(self)
        self.go_pushButton.setGeometry(QtCore.QRect(590,40,101,25))
        self.go_pushButton.setObjectName("go_pushButton")        
        #self.system_transactions_checkbox = QtGui.QCheckBox(self)
        #self.system_transactions_checkbox.setObjectName("system_transactions_checkbox")

        self.toolBar = QtGui.QToolBar(self)      
        
        self.toolBar.addWidget(self.label_account)
        self.toolBar.addWidget(self.comboBox_account)
        
        #self.toolBar.addWidget(self.label_transactions_type)
        #self.toolBar.addWidget(self.comboBox_transactions_type)
        #self.toolBar.addWidget(self.label_cashier)
        #self.toolBar.addWidget(self.comboBox_cashier)
        self.toolBar.addWidget(self.label_date_start)
        self.toolBar.addWidget(self.dateTimeEdit_date_start)
        self.toolBar.addWidget(self.label_date_end)
        self.toolBar.addWidget(self.dateTimeEdit_date_end)
        #self.toolBar.addWidget(self.system_transactions_checkbox)
        
        self.toolBar.addWidget(self.go_pushButton)
        self.toolBar.addSeparator()        
        
        self.toolBar.setMovable(False)
        self.toolBar.setFloatable(False)
        self.addToolBar(QtCore.Qt.TopToolBarArea,self.toolBar)
        
        self.columns = {}
       
        #if self.report_type=='radius_authlog':
        #    self.radius_auth_fixtures()   
                
    def ebsPostInit(self, initargs):
        self.tableWidget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.tableWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        if self.report_type=='radius_authlog':
            QtCore.QObject.connect(self.go_pushButton,QtCore.SIGNAL("clicked()"),self.radius_auth_fixtures)
        if self.report_type=='balance_log':
            QtCore.QObject.connect(self.go_pushButton,QtCore.SIGNAL("clicked()"),self.balance_log_fixtures)

        #QtCore.QObject.connect(self.comboBox_transactions_type,QtCore.SIGNAL("currentIndexChanged(int)"),self.setTableColumns)
        
        #actList=[("actionDeleteTransaction", "Удалить", "images/del.png", self.delete_transaction),]
        #objDict = {self.tableWidget:["actionDeleteTransaction", ]}
        #self.actionCreator(actList, objDict)
        #self.setTableColumns()
        self.fixtures()
        
    def retranslateUI(self, initargs):
        super(SimpleReportEbs, self).retranslateUI(initargs)
        
        self.label_date_start.setText(QtGui.QApplication.translate("Dialog", "С", None, QtGui.QApplication.UnicodeUTF8))
        self.label_date_end.setText(QtGui.QApplication.translate("Dialog", "По", None, QtGui.QApplication.UnicodeUTF8))
        self.label_account.setText(QtGui.QApplication.translate("Dialog", "Пользователь", None, QtGui.QApplication.UnicodeUTF8))
        self.dateTimeEdit_date_end.setDisplayFormat(QtGui.QApplication.translate("Dialog", self.datetimeFormat, None, QtGui.QApplication.UnicodeUTF8))
        self.dateTimeEdit_date_start.setDisplayFormat(QtGui.QApplication.translate("Dialog", self.datetimeFormat, None, QtGui.QApplication.UnicodeUTF8))
        #self.system_transactions_checkbox.setText(QtGui.QApplication.translate("Dialog", "Включить в отчёт системные проводки", None, QtGui.QApplication.UnicodeUTF8))        
        #self.label_transactions_type.setText(QtGui.QApplication.translate("Dialog", "Тип", None, QtGui.QApplication.UnicodeUTF8))
        #self.label_cashier.setText(QtGui.QApplication.translate("Dialog", "Кассир", None, QtGui.QApplication.UnicodeUTF8))
        
        self.go_pushButton.setText(QtGui.QApplication.translate("Dialog", "Показать", None, QtGui.QApplication.UnicodeUTF8))


    def addrow(self, value, x, y, id=None, promise=False, date = None):
        headerItem = QtGui.QTableWidgetItem()
        if value==None:
            value=""
        if y==1:
            headerItem.setIcon(QtGui.QIcon("images/user.png"))
        
        if y==5 and value not in ['AUTH_OK','DHCP_AUTH_OK']:
            headerItem.setBackgroundColor(QtGui.QColor("red"))
        elif y==5 and value in ['AUTH_OK','DHCP_AUTH_OK']:
            headerItem.setBackgroundColor(QtGui.QColor("lightgreen"))
            
        
        if isinstance(value, basestring):            
            headerItem.setText(unicode(value))     
        elif type(value)==datetime.datetime:
            #.strftime(self.strftimeFormat)   

            headerItem.setData(QtCore.Qt.DisplayRole, QtCore.QDateTime(value))      
 
        else:            
            headerItem.setData(0, QtCore.QVariant(float(value)))     
 
            
        if id:
            headerItem.id = id
            headerItem.date = date
        self.tableWidget.setItem(x,y,headerItem)
             
    def radius_auth_fixtures(self):
        self.tableWidget.setSortingEnabled(False)
        self.statusBar().showMessage(u"Ожидание ответа")
        self.tableWidget.clearContents()
        account_id = self.comboBox_account.itemData(self.comboBox_account.currentIndex()).toInt()[0]
        acc_str = ''
        if account_id:
            acc_str = " and account_id=%s" % account_id
        start_date = self.dateTimeEdit_date_start.currentDate()
        end_date = self.dateTimeEdit_date_end.currentDate()
        items = self.connection.sql("""SELECT ra.id as id, ra.account_id as account_id,(SELECT username FROM billservice_account WHERE id=ra.account_id) as account_username,
        ra.type as type, ra.service as service, (SELECT username FROM billservice_subaccount WHERE id=ra.subaccount_id) as subaccount_username, (SELECT name FROM nas_nas WHERE id=ra.nas_id) as nas_name, ra.cause as cause, ra.datetime as datetime FROM radius_authlog as ra 
        WHERE datetime between '%s' and '%s' %s
        ORDER BY datetime DESC""" % (start_date, end_date, acc_str))
        
        [u'#', u'Аккаунт', u"Субаккаунт", u'Сервер доступа', u'Способ доступа', u'Тип события', u"Событие", u'Дата']
        self.connection.commit()
        self.tableWidget.setRowCount(len(items)+1)
        i=0
        for item in items:
            self.addrow(i, i, 0, id=item.id, )
            self.addrow(item.account_username, i, 1)
            self.addrow(item.subaccount_username, i, 2)
            self.addrow(item.nas_name, i, 3)
            self.addrow(item.service, i, 4)
            self.addrow(item.type, i, 5)
            self.addrow(item.cause, i, 6)
            self.addrow(item.datetime, i, 7)
            i+=1

        try:
            settings = QtCore.QSettings("Expert Billing", "Expert Billing Client")
            settings.setValue("%strans_date_start" % self.report_type, QtCore.QVariant(self.dateTimeEdit_date_start.dateTime()))
            settings.setValue("%strans_date_end" % self.report_type, QtCore.QVariant(self.dateTimeEdit_date_end.dateTime()))
        except Exception, ex:
            print "Transactions settings save error: ", ex
        self.tableWidget.setSortingEnabled(True)
        self.statusBar().showMessage(u"Готово")
            
    def balance_log_fixtures(self):
        self.tableWidget.setSortingEnabled(False)
        self.statusBar().showMessage(u"Ожидание ответа")
        self.tableWidget.clearContents()
        account_id = self.comboBox_account.itemData(self.comboBox_account.currentIndex()).toInt()[0]
        acc_str = ''
        if account_id:
            acc_str = " and account_id=%s" % account_id
        start_date = self.dateTimeEdit_date_start.currentDate()
        end_date = self.dateTimeEdit_date_end.currentDate()
        items = self.connection.sql("""SELECT bah.id,(SELECT username FROM billservice_account WHERE id=bah.account_id) as account_username, bah.balance as balance, bah.datetime as datetime FROM billservice_balancehistory as bah 
        WHERE datetime between '%s' and '%s' %s
        ORDER BY datetime DESC""" % (start_date, end_date, acc_str))
        
        [u'#', u'Аккаунт', u"Баланс", u'Дата']
        self.connection.commit()
        self.tableWidget.setRowCount(len(items)+1)
        i=0
        for item in items:
            self.addrow(i, i, 0, id=item.id, )
            self.addrow(item.account_username, i, 1)
            self.addrow(item.balance, float(i), 2)
            self.addrow(item.datetime, i, 3)
            i+=1

        try:
            settings = QtCore.QSettings("Expert Billing", "Expert Billing Client")
            settings.setValue("%strans_date_start" % self.report_type, QtCore.QVariant(self.dateTimeEdit_date_start.dateTime()))
            settings.setValue("%strans_date_end" % self.report_type, QtCore.QVariant(self.dateTimeEdit_date_end.dateTime()))
        except Exception, ex:
            print "Transactions settings save error: ", ex
        self.tableWidget.setSortingEnabled(True)
            
        self.statusBar().showMessage(u"Готово")
    def fixtures(self):            
        accounts = self.connection.sql("SELECT id, username FROM billservice_account ORDER BY username ASC")
        self.connection.commit()
        self.comboBox_account.addItem(u"-Все клиенты-")
        self.comboBox_account.setItemData(0, QtCore.QVariant(0))
        i=1
        for account in accounts:
            self.comboBox_account.addItem(account.username)
            self.comboBox_account.setItemData(i, QtCore.QVariant(account.id))
            if self.account_id==account.id:
                self.comboBox_account.setCurrentIndex(i)
            i+=1
        
            