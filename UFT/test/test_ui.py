# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'test.ui'
#
# Created: Tue Dec 02 16:43:36 2014
#      by: PyQt4 UI code generator 4.9.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
import sys
import time

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class Ui_Form(QtGui.QWidget):
    def __init__(self):
        super(Ui_Form, self).__init__()
        self.setupUi(self)

    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(461, 326)
        self.verticalLayout_2 = QtGui.QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.textEdit = QtGui.QTextEdit(Form)
        self.textEdit.setObjectName(_fromUtf8("textEdit"))
        self.verticalLayout.addWidget(self.textEdit)
        self.pushButton = QtGui.QPushButton(Form)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.verticalLayout.addWidget(self.pushButton)
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

        self.pushButton.clicked.connect(self.start)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.pushButton.setText(_translate("Form", "START", None))

    def start(self):
        #self.add("start!")
        self.workThread = WorkThread()
        self.connect(self.workThread, QtCore.SIGNAL("update(QString)"), self.add)
        self.workThread.start()

    def add(self, text):
        self.textEdit.append("{0} \n".format(text))


class WorkThread(QtCore.QThread):
    def __init__(self):
        self.pb = ProgressBar()

        QtCore.QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        self.pb.start()
        self.emit(QtCore.SIGNAL('update(QString)'), "pb started.")

        while(self.pb.isAlive()):
        #for i in range(100):
            time.sleep(0.1)
            self.emit(QtCore.SIGNAL('update(QString)'), "progress " +
                      str(self.pb.progress))

        #for i in range(10000):
        #    time.sleep(0.1) # artificial time delay
        #    self.emit(QtCore.SIGNAL('update(QString)'), "from work thread " + str(i))

        #ch = Chan()
        #ch.
        #
        #while(ch.is):
        #    self.emit(, ch.dut_list.)
        #    time.sleep(1)

        self.emit(QtCore.SIGNAL('update(QString)'), "pb stopped.")
        self.terminate()


import threading

class ProgressBar(threading.Thread):
    def __init__(self):
        self.progress = 0
        super(ProgressBar, self).__init__()

    def run(self):
        while(self.progress < 100):
            time.sleep(0.1)
            self.progress += 1


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    app.setStyle("Plastique")
    widget = Ui_Form()
    widget.show()
    sys.exit(app.exec_())
