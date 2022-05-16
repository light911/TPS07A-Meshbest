from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtGui import QPixmap,QPainter,QPen,QImage
from PyQt5.QtWidgets import QApplication, QMainWindow,QGraphicsScene,QGraphicsItem,QGraphicsRectItem,QGraphicsTextItem,QWidget,QMessageBox,QGraphicsView
from TPS07A_showresult import Ui_MainWindow
import argparse,sys,os,signal,math,time,traceback,getpass,re

class MainUI(QMainWindow,Ui_MainWindow):
    def __init__(self) -> None:
        super(MainUI,self).__init__()
        signal.signal(signal.SIGINT, self.quit)
        signal.signal(signal.SIGTERM, self.quit)
        self.setupUi(self)
        self.pid = os.getpid()
        self.run()
    def run(self):
        #local crysal image
        self.Scene = {}
        for view in ['1','2']:
            imagepath = f"./crystalimage_{view}.jpg"
            image = QPixmap()
            image.load(imagepath)
            item = f'graphicsView_{view}'
            self.Scene[view] =  QGraphicsScene()
            self.Scene[view].addPixmap(image)
            graphicsView = getattr(self,item)
            # graphicsView = QGraphicsView()
            graphicsView.setScene(self.Scene[view])
        
        pass
    def quit(self,signum,frame):
        pass
if __name__ == "__main__":
    def run_app():         
        '''
        run main screen
        '''
        par = argparse.ArgumentParser()

        par.add_argument("-folder",type=str,help="Raw data folder")
        par.add_argument("-key",type=str,help="The string to  login bluice")
        par.add_argument("-user",type=str,help="Current user name")
        par.add_argument("-stra",type=str,help="The strategy for determine collect par.")
        par.add_argument("-beamline",type=str,help="Beamline")
        par.add_argument("-passwd",type=str,help="The string to  login bluice")
        par.add_argument("-base64passwd",type=str,help="The string to  login bluice")
        args=par.parse_args()
#        print args.folder
       #app = QtWidgets.QApplication(sys.argv)
        if not QtWidgets.QApplication.instance():
            print("new")
            app = QtWidgets.QApplication(sys.argv)
        else:
            print("has old")
            app = QtWidgets.QApplication.instance()
        #print "go"%tb
        
        window = MainUI()
        window.show()
        sys.exit(app.exec_())
        
        
        
        
    run_app()