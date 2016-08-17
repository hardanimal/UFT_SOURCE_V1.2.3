import sys
from numpy import linspace
from PyQt4 import QtCore, QtGui
import random
from UFT_GUI import UFT_Ui
from numpy import arange, sin, pi
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

def plot(axes):
    x = linspace(-10, 10)
    axes.plot(x, x**2)
    axes.plot(x, x**3)

def plot_2(axes):
    t = arange(0.0, 3.0, 0.01)
    s = sin(2*pi*t)
    axes.plot(t, s)

def plot_3(axes):
    axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')
    l = [random.randint(0, 10) for i in range(4)]
    axes.plot([0, 1, 2, 3], l, 'r')
#===============================================================================
#   Example
#===============================================================================
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    Form = QtGui.QWidget()
    ui = UFT_Ui.Ui_Form()
    ui.setupUi(Form)

    ui.mplwidget.setFocus()
    ui.mplwidget_2.setFocus()
    ui.mplwidget_3.setFocus()
    ui.mplwidget_4.setFocus()
    
    plot(ui.mplwidget.axes)
    plot_2(ui.mplwidget_2.axes)
    def update_mpl_3():
        plot_3(ui.mplwidget_3.axes)
        ui.mplwidget_3.draw()
    ui.mplwidget.timer = QtCore.QTimer()
    ui.mplwidget.timer.timeout.connect(update_mpl_3)
    ui.mplwidget.timer.start(1000)
    
    ui.mplwidget_3.draw()
    
    
    
    Form.show()
    sys.exit(app.exec_())
