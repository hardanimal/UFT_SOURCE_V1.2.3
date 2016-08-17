import sys
from PyQt4 import QtCore, QtGui
import logging
from UFT_GUI import UFT_Ui
import time
class QtHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
    def emit(self, record):
        record = self.format(record)
        if record: XStream.stdout().write('%s\n' % record)
        # originally: XStream.stdout().write("{}\n".format(record))


logger = logging.getLogger(__name__)
handler = QtHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class XStream(QtCore.QObject):
    _stdout = None
    _stderr = None
    messageWritten = QtCore.pyqtSignal(str)
    def flush(self):
        pass
    def fileno(self):
        return -1
    def write(self, msg):
        if (not self.signalsBlocked()):
            self.messageWritten.emit(unicode(msg))
    @staticmethod
    def stdout():
        if (not XStream._stdout):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout
    @staticmethod
    def stderr():
        if (not XStream._stderr):
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        return XStream._stderr

def test():
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warning message')
    logger.error('error message')
    print 'Old school hand made print message'
        
if (__name__ == '__main__'):
    app = None
    if (not QtGui.QApplication.instance()):
        app = QtGui.QApplication([])
        Form = QtGui.QWidget()
    ui = UFT_Ui.Ui_Form()
    ui.setupUi(Form)
    def append_formatData(data):
        ui.info_textBrowser.insertPlainText(time.strftime("%Y-%m-%d %X\t")+data)
        ui.info_textBrowser.moveCursor(QtGui.QTextCursor.End)
#     XStream.stdout().messageWritten.connect(ui.info_textBrowser.append)    
    XStream.stdout().messageWritten.connect(append_formatData)
    ui.start_pushButton.clicked.connect(test)
    Form.show()
    if (app):
        app.exec_()
