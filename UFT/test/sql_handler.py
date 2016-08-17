# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore, QtSql
import sys 
from UFT_GUI import UFT_Ui

def createConnection(): 
    db = QtSql.QSqlDatabase.addDatabase("QSQLITE") 
    db.setDatabaseName("./../UFT/pgem.db") 
    db.open() 

def createTable(): 
    q = QtSql.QSqlQuery() 
    q.exec_("create table if not exists t1 (f1 integer primary key,f2 varchar(20))") 
    q.exec_("delete from t1") 
    q.exec_(u"insert into t1 values(1,'mzfa')") 
    q.exec_(u"insert into t1 values(2,'qibo')") 
    q.exec_("commit") 


class Model(QtSql.QSqlTableModel):   
    def __init__(self,parent):   
        QtSql.QSqlTableModel.__init__(self,parent)   
        self.setTable("cycle")   
        self.select()   
        self.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)


if __name__=="__main__":
    a=QtGui.QApplication(sys.argv)
    createConnection()
#     createTable()
    Form = QtGui.QWidget()
    
    w=UFT_Ui.Ui_Form()
    w.setupUi(Form)
    view = w.tableView
    model = Model(view)
    view.setModel(model)
    
    def update():
        for i in range(model.rowCount()):
            record = model.record(i) 
            model.setRecord(i, record)
        model.submitAll()
    w.submit_pushButton.clicked.connect(update)
    
    Form.show()   
    sys.exit(a.exec_())  
