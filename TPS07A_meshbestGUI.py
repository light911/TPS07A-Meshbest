# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'TPS07A_meshbestGUI.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1525, 1055)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_2.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.LastInfo = QtWidgets.QLabel(self.centralwidget)
        self.LastInfo.setMinimumSize(QtCore.QSize(300, 0))
        self.LastInfo.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.LastInfo.setTextFormat(QtCore.Qt.AutoText)
        self.LastInfo.setObjectName("LastInfo")
        self.horizontalLayout.addWidget(self.LastInfo)
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.TPSStateText = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.TPSStateText.setFont(font)
        self.TPSStateText.setObjectName("TPSStateText")
        self.horizontalLayout.addWidget(self.TPSStateText)
        self.Current = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.Current.setMinimumSize(QtCore.QSize(0, 0))
        self.Current.setAutoFillBackground(False)
        self.Current.setFrame(True)
        self.Current.setAlignment(QtCore.Qt.AlignCenter)
        self.Current.setReadOnly(True)
        self.Current.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.Current.setSpecialValueText("")
        self.Current.setAccelerated(False)
        self.Current.setKeyboardTracking(True)
        self.Current.setPrefix("")
        self.Current.setDecimals(1)
        self.Current.setMaximum(1000.0)
        self.Current.setProperty("value", 500.0)
        self.Current.setObjectName("Current")
        self.horizontalLayout.addWidget(self.Current)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.Energy = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.Energy.setAlignment(QtCore.Qt.AlignCenter)
        self.Energy.setReadOnly(True)
        self.Energy.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.Energy.setPrefix("")
        self.Energy.setDecimals(3)
        self.Energy.setMinimum(4.0)
        self.Energy.setMaximum(20.0)
        self.Energy.setObjectName("Energy")
        self.horizontalLayout.addWidget(self.Energy)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.Active = QtWidgets.QPushButton(self.centralwidget)
        self.Active.setMinimumSize(QtCore.QSize(140, 30))
        self.Active.setCheckable(True)
        self.Active.setChecked(False)
        self.Active.setAutoRepeat(False)
        self.Active.setAutoExclusive(False)
        self.Active.setAutoDefault(False)
        self.Active.setDefault(True)
        self.Active.setObjectName("Active")
        self.horizontalLayout.addWidget(self.Active)
        self.gridLayout_2.addLayout(self.horizontalLayout, 2, 0, 1, 3)
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_1 = QtWidgets.QWidget()
        self.tab_1.setObjectName("tab_1")
        self.gridLayout = QtWidgets.QGridLayout(self.tab_1)
        self.gridLayout.setObjectName("gridLayout")
        self.comboBox = QtWidgets.QComboBox(self.tab_1)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.gridLayout.addWidget(self.comboBox, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_1, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.Autocenter = QtWidgets.QPushButton(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Autocenter.sizePolicy().hasHeightForWidth())
        self.Autocenter.setSizePolicy(sizePolicy)
        self.Autocenter.setObjectName("Autocenter")
        self.gridLayout_4.addWidget(self.Autocenter, 5, 0, 1, 1)
        self.Zoom1 = QtWidgets.QPushButton(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Zoom1.sizePolicy().hasHeightForWidth())
        self.Zoom1.setSizePolicy(sizePolicy)
        self.Zoom1.setObjectName("Zoom1")
        self.gridLayout_4.addWidget(self.Zoom1, 3, 0, 1, 1)
        self.pos_10deg = QtWidgets.QPushButton(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pos_10deg.sizePolicy().hasHeightForWidth())
        self.pos_10deg.setSizePolicy(sizePolicy)
        self.pos_10deg.setObjectName("pos_10deg")
        self.gridLayout_4.addWidget(self.pos_10deg, 4, 2, 1, 1)
        self.pos_90deg = QtWidgets.QPushButton(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pos_90deg.sizePolicy().hasHeightForWidth())
        self.pos_90deg.setSizePolicy(sizePolicy)
        self.pos_90deg.setObjectName("pos_90deg")
        self.gridLayout_4.addWidget(self.pos_90deg, 4, 3, 1, 1)
        self.Centermode = QtWidgets.QPushButton(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Centermode.sizePolicy().hasHeightForWidth())
        self.Centermode.setSizePolicy(sizePolicy)
        self.Centermode.setObjectName("Centermode")
        self.gridLayout_4.addWidget(self.Centermode, 5, 2, 1, 1)
        self.Zoom2 = QtWidgets.QPushButton(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Zoom2.sizePolicy().hasHeightForWidth())
        self.Zoom2.setSizePolicy(sizePolicy)
        self.Zoom2.setObjectName("Zoom2")
        self.gridLayout_4.addWidget(self.Zoom2, 3, 1, 1, 1)
        self.neg_90deg = QtWidgets.QPushButton(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.neg_90deg.sizePolicy().hasHeightForWidth())
        self.neg_90deg.setSizePolicy(sizePolicy)
        self.neg_90deg.setObjectName("neg_90deg")
        self.gridLayout_4.addWidget(self.neg_90deg, 4, 0, 1, 1)
        self.neg_10deg = QtWidgets.QPushButton(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.neg_10deg.sizePolicy().hasHeightForWidth())
        self.neg_10deg.setSizePolicy(sizePolicy)
        self.neg_10deg.setObjectName("neg_10deg")
        self.gridLayout_4.addWidget(self.neg_10deg, 4, 1, 1, 1)
        self.Zoom3 = QtWidgets.QPushButton(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Zoom3.sizePolicy().hasHeightForWidth())
        self.Zoom3.setSizePolicy(sizePolicy)
        self.Zoom3.setObjectName("Zoom3")
        self.gridLayout_4.addWidget(self.Zoom3, 3, 2, 1, 1)
        self.Zoom4 = QtWidgets.QPushButton(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Zoom4.sizePolicy().hasHeightForWidth())
        self.Zoom4.setSizePolicy(sizePolicy)
        self.Zoom4.setObjectName("Zoom4")
        self.gridLayout_4.addWidget(self.Zoom4, 3, 3, 1, 1)
        self.Transfermode = QtWidgets.QPushButton(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Transfermode.sizePolicy().hasHeightForWidth())
        self.Transfermode.setSizePolicy(sizePolicy)
        self.Transfermode.setObjectName("Transfermode")
        self.gridLayout_4.addWidget(self.Transfermode, 5, 3, 1, 1)
        self.SampleViedo = QtWidgets.QGraphicsView(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.SampleViedo.sizePolicy().hasHeightForWidth())
        self.SampleViedo.setSizePolicy(sizePolicy)
        self.SampleViedo.setMinimumSize(QtCore.QSize(320, 256))
        self.SampleViedo.setMaximumSize(QtCore.QSize(1280, 1024))
        self.SampleViedo.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.SampleViedo.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.SampleViedo.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.SampleViedo.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.SampleViedo.setObjectName("SampleViedo")
        self.gridLayout_4.addWidget(self.SampleViedo, 0, 0, 1, 4)
        self.Raster = QtWidgets.QPushButton(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Raster.sizePolicy().hasHeightForWidth())
        self.Raster.setSizePolicy(sizePolicy)
        self.Raster.setMinimumSize(QtCore.QSize(0, 30))
        self.Raster.setIconSize(QtCore.QSize(16, 16))
        self.Raster.setObjectName("Raster")
        self.gridLayout_4.addWidget(self.Raster, 1, 0, 1, 2)
        self.StartRaster = QtWidgets.QPushButton(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.StartRaster.sizePolicy().hasHeightForWidth())
        self.StartRaster.setSizePolicy(sizePolicy)
        self.StartRaster.setMinimumSize(QtCore.QSize(0, 30))
        self.StartRaster.setIconSize(QtCore.QSize(16, 16))
        self.StartRaster.setObjectName("StartRaster")
        self.gridLayout_4.addWidget(self.StartRaster, 1, 2, 1, 2)
        self.gridLayout_5.addLayout(self.gridLayout_4, 0, 0, 2, 1)
        self.toolBox = QtWidgets.QToolBox(self.tab_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolBox.sizePolicy().hasHeightForWidth())
        self.toolBox.setSizePolicy(sizePolicy)
        self.toolBox.setMinimumSize(QtCore.QSize(0, 0))
        self.toolBox.setMaximumSize(QtCore.QSize(16777215, 130))
        self.toolBox.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.toolBox.setAutoFillBackground(False)
        self.toolBox.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.toolBox.setFrameShadow(QtWidgets.QFrame.Plain)
        self.toolBox.setLineWidth(1)
        self.toolBox.setMidLineWidth(0)
        self.toolBox.setObjectName("toolBox")
        self.page_3 = QtWidgets.QWidget()
        self.page_3.setGeometry(QtCore.QRect(0, 0, 86, 41))
        self.page_3.setObjectName("page_3")
        self.gridLayout_12 = QtWidgets.QGridLayout(self.page_3)
        self.gridLayout_12.setObjectName("gridLayout_12")
        self.RootPath = QtWidgets.QLineEdit(self.page_3)
        self.RootPath.setObjectName("RootPath")
        self.gridLayout_12.addWidget(self.RootPath, 0, 0, 1, 1)
        self.toolBox.addItem(self.page_3, "")
        self.page_5 = QtWidgets.QWidget()
        self.page_5.setGeometry(QtCore.QRect(0, 0, 1056, 73))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.page_5.sizePolicy().hasHeightForWidth())
        self.page_5.setSizePolicy(sizePolicy)
        self.page_5.setObjectName("page_5")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.page_5)
        self.verticalLayout_7.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.gridLayout_10 = QtWidgets.QGridLayout()
        self.gridLayout_10.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.gridLayout_10.setObjectName("gridLayout_10")
        self.label_14 = QtWidgets.QLabel(self.page_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_14.sizePolicy().hasHeightForWidth())
        self.label_14.setSizePolicy(sizePolicy)
        self.label_14.setObjectName("label_14")
        self.gridLayout_10.addWidget(self.label_14, 0, 0, 1, 1)
        self.Distance = QtWidgets.QDoubleSpinBox(self.page_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Distance.sizePolicy().hasHeightForWidth())
        self.Distance.setSizePolicy(sizePolicy)
        self.Distance.setMinimum(150.0)
        self.Distance.setMaximum(1000.0)
        self.Distance.setObjectName("Distance")
        self.gridLayout_10.addWidget(self.Distance, 1, 0, 1, 1)
        self.Beamsize = QtWidgets.QComboBox(self.page_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Beamsize.sizePolicy().hasHeightForWidth())
        self.Beamsize.setSizePolicy(sizePolicy)
        self.Beamsize.setObjectName("Beamsize")
        self.Beamsize.addItem("")
        self.Beamsize.addItem("")
        self.Beamsize.addItem("")
        self.Beamsize.addItem("")
        self.Beamsize.addItem("")
        self.Beamsize.addItem("")
        self.Beamsize.addItem("")
        self.gridLayout_10.addWidget(self.Beamsize, 1, 3, 1, 1)
        self.Attenuation = QtWidgets.QDoubleSpinBox(self.page_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Attenuation.sizePolicy().hasHeightForWidth())
        self.Attenuation.setSizePolicy(sizePolicy)
        self.Attenuation.setObjectName("Attenuation")
        self.gridLayout_10.addWidget(self.Attenuation, 1, 1, 1, 1)
        self.ExpouseValue = QtWidgets.QDoubleSpinBox(self.page_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ExpouseValue.sizePolicy().hasHeightForWidth())
        self.ExpouseValue.setSizePolicy(sizePolicy)
        self.ExpouseValue.setDecimals(3)
        self.ExpouseValue.setMaximum(100.0)
        self.ExpouseValue.setProperty("value", 0.01)
        self.ExpouseValue.setObjectName("ExpouseValue")
        self.gridLayout_10.addWidget(self.ExpouseValue, 1, 2, 1, 1)
        self.ExpousetimeType = QtWidgets.QComboBox(self.page_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ExpousetimeType.sizePolicy().hasHeightForWidth())
        self.ExpousetimeType.setSizePolicy(sizePolicy)
        self.ExpousetimeType.setMinimumSize(QtCore.QSize(110, 0))
        self.ExpousetimeType.setObjectName("ExpousetimeType")
        self.ExpousetimeType.addItem("")
        self.ExpousetimeType.addItem("")
        self.gridLayout_10.addWidget(self.ExpousetimeType, 0, 2, 1, 1)
        self.label_15 = QtWidgets.QLabel(self.page_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_15.sizePolicy().hasHeightForWidth())
        self.label_15.setSizePolicy(sizePolicy)
        self.label_15.setObjectName("label_15")
        self.gridLayout_10.addWidget(self.label_15, 0, 4, 1, 1)
        self.label_12 = QtWidgets.QLabel(self.page_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_12.sizePolicy().hasHeightForWidth())
        self.label_12.setSizePolicy(sizePolicy)
        self.label_12.setObjectName("label_12")
        self.gridLayout_10.addWidget(self.label_12, 0, 3, 1, 1)
        self.label_13 = QtWidgets.QLabel(self.page_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_13.sizePolicy().hasHeightForWidth())
        self.label_13.setSizePolicy(sizePolicy)
        self.label_13.setObjectName("label_13")
        self.gridLayout_10.addWidget(self.label_13, 0, 1, 1, 1)
        self.doubleSpinBox_12 = QtWidgets.QDoubleSpinBox(self.page_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.doubleSpinBox_12.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_12.setSizePolicy(sizePolicy)
        self.doubleSpinBox_12.setMinimumSize(QtCore.QSize(0, 0))
        self.doubleSpinBox_12.setAlignment(QtCore.Qt.AlignCenter)
        self.doubleSpinBox_12.setReadOnly(True)
        self.doubleSpinBox_12.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.doubleSpinBox_12.setDecimals(3)
        self.doubleSpinBox_12.setObjectName("doubleSpinBox_12")
        self.gridLayout_10.addWidget(self.doubleSpinBox_12, 1, 4, 1, 1)
        self.verticalLayout_7.addLayout(self.gridLayout_10)
        self.toolBox.addItem(self.page_5, "")
        self.gridLayout_5.addWidget(self.toolBox, 0, 2, 1, 2)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.RasterView1 = QtWidgets.QGraphicsView(self.tab_2)
        self.RasterView1.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.RasterView1.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.RasterView1.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.RasterView1.setViewportUpdateMode(QtWidgets.QGraphicsView.SmartViewportUpdate)
        self.RasterView1.setObjectName("RasterView1")
        self.verticalLayout.addWidget(self.RasterView1)
        self.Overlap_Select_1 = QtWidgets.QComboBox(self.tab_2)
        self.Overlap_Select_1.setObjectName("Overlap_Select_1")
        self.Overlap_Select_1.addItem("")
        self.Overlap_Select_1.addItem("")
        self.Overlap_Select_1.addItem("")
        self.Overlap_Select_1.addItem("")
        self.Overlap_Select_1.addItem("")
        self.Overlap_Select_1.addItem("")
        self.Overlap_Select_1.addItem("")
        self.verticalLayout.addWidget(self.Overlap_Select_1)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_8 = QtWidgets.QLabel(self.tab_2)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout_7.addWidget(self.label_8)
        self.view1_opacity = QtWidgets.QSlider(self.tab_2)
        self.view1_opacity.setMaximum(100)
        self.view1_opacity.setProperty("value", 80)
        self.view1_opacity.setOrientation(QtCore.Qt.Horizontal)
        self.view1_opacity.setObjectName("view1_opacity")
        self.horizontalLayout_7.addWidget(self.view1_opacity)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_4 = QtWidgets.QLabel(self.tab_2)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_3.addWidget(self.label_4)
        self.List_number_1 = QtWidgets.QSpinBox(self.tab_2)
        self.List_number_1.setProperty("value", 10)
        self.List_number_1.setObjectName("List_number_1")
        self.horizontalLayout_3.addWidget(self.List_number_1)
        self.horizontalSlider_3 = QtWidgets.QSlider(self.tab_2)
        self.horizontalSlider_3.setMaximum(100)
        self.horizontalSlider_3.setProperty("value", 100)
        self.horizontalSlider_3.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_3.setObjectName("horizontalSlider_3")
        self.horizontalLayout_3.addWidget(self.horizontalSlider_3)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.gridLayout_3 = QtWidgets.QGridLayout()
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.pushButton_4 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_4.setAutoRepeat(False)
        self.pushButton_4.setObjectName("pushButton_4")
        self.gridLayout_3.addWidget(self.pushButton_4, 1, 2, 1, 1)
        self.pushButton_3 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_3.setObjectName("pushButton_3")
        self.gridLayout_3.addWidget(self.pushButton_3, 0, 1, 1, 1)
        self.pushButton = QtWidgets.QPushButton(self.tab_2)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout_3.addWidget(self.pushButton, 1, 0, 1, 1)
        self.pushButton_2 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout_3.addWidget(self.pushButton_2, 2, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_3)
        self.gridLayout_5.addLayout(self.verticalLayout, 1, 2, 3, 1)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.RasterView2 = QtWidgets.QGraphicsView(self.tab_2)
        self.RasterView2.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.RasterView2.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.RasterView2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.RasterView2.setViewportUpdateMode(QtWidgets.QGraphicsView.SmartViewportUpdate)
        self.RasterView2.setObjectName("RasterView2")
        self.verticalLayout_3.addWidget(self.RasterView2)
        self.Overlap_Select_2 = QtWidgets.QComboBox(self.tab_2)
        self.Overlap_Select_2.setObjectName("Overlap_Select_2")
        self.Overlap_Select_2.addItem("")
        self.Overlap_Select_2.addItem("")
        self.Overlap_Select_2.addItem("")
        self.Overlap_Select_2.addItem("")
        self.Overlap_Select_2.addItem("")
        self.Overlap_Select_2.addItem("")
        self.Overlap_Select_2.addItem("")
        self.verticalLayout_3.addWidget(self.Overlap_Select_2)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_9 = QtWidgets.QLabel(self.tab_2)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_8.addWidget(self.label_9)
        self.view2_opacity = QtWidgets.QSlider(self.tab_2)
        self.view2_opacity.setMaximum(100)
        self.view2_opacity.setProperty("value", 80)
        self.view2_opacity.setOrientation(QtCore.Qt.Horizontal)
        self.view2_opacity.setObjectName("view2_opacity")
        self.horizontalLayout_8.addWidget(self.view2_opacity)
        self.verticalLayout_3.addLayout(self.horizontalLayout_8)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_5 = QtWidgets.QLabel(self.tab_2)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_4.addWidget(self.label_5)
        self.List_number_2 = QtWidgets.QSpinBox(self.tab_2)
        self.List_number_2.setProperty("value", 10)
        self.List_number_2.setObjectName("List_number_2")
        self.horizontalLayout_4.addWidget(self.List_number_2)
        self.horizontalSlider_7 = QtWidgets.QSlider(self.tab_2)
        self.horizontalSlider_7.setMaximum(100)
        self.horizontalSlider_7.setProperty("value", 100)
        self.horizontalSlider_7.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_7.setObjectName("horizontalSlider_7")
        self.horizontalLayout_4.addWidget(self.horizontalSlider_7)
        self.verticalLayout_3.addLayout(self.horizontalLayout_4)
        self.gridLayout_11 = QtWidgets.QGridLayout()
        self.gridLayout_11.setObjectName("gridLayout_11")
        self.pushButton_5 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_5.setObjectName("pushButton_5")
        self.gridLayout_11.addWidget(self.pushButton_5, 1, 0, 1, 1)
        self.pushButton_11 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_11.setObjectName("pushButton_11")
        self.gridLayout_11.addWidget(self.pushButton_11, 1, 2, 1, 1)
        self.pushButton_12 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_12.setObjectName("pushButton_12")
        self.gridLayout_11.addWidget(self.pushButton_12, 0, 1, 1, 1)
        self.pushButton_13 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_13.setObjectName("pushButton_13")
        self.gridLayout_11.addWidget(self.pushButton_13, 2, 1, 1, 1)
        self.verticalLayout_3.addLayout(self.gridLayout_11)
        self.gridLayout_5.addLayout(self.verticalLayout_3, 1, 3, 3, 1)
        self.label_3 = QtWidgets.QLabel(self.tab_2)
        self.label_3.setObjectName("label_3")
        self.gridLayout_5.addWidget(self.label_3, 2, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_5.addItem(spacerItem1, 2, 1, 1, 1)
        self.verticalLayout_6 = QtWidgets.QVBoxLayout()
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.graphicsView_5 = QtWidgets.QGraphicsView(self.tab_2)
        self.graphicsView_5.setObjectName("graphicsView_5")
        self.verticalLayout_6.addWidget(self.graphicsView_5)
        self.gridLayout_13 = QtWidgets.QGridLayout()
        self.gridLayout_13.setObjectName("gridLayout_13")
        self.tabWidget_2 = QtWidgets.QTabWidget(self.tab_2)
        self.tabWidget_2.setObjectName("tabWidget_2")
        self.tab_5 = QtWidgets.QWidget()
        self.tab_5.setObjectName("tab_5")
        self.tabWidget_2.addTab(self.tab_5, "")
        self.tab_6 = QtWidgets.QWidget()
        self.tab_6.setObjectName("tab_6")
        self.tabWidget_2.addTab(self.tab_6, "")
        self.gridLayout_13.addWidget(self.tabWidget_2, 0, 0, 1, 1)
        self.verticalLayout_6.addLayout(self.gridLayout_13)
        self.verticalLayout_6.setStretch(0, 100)
        self.gridLayout_5.addLayout(self.verticalLayout_6, 3, 0, 1, 1)
        self.gridLayout_5.setColumnStretch(2, 50)
        self.gridLayout_5.setColumnStretch(3, 50)
        self.tabWidget.addTab(self.tab_2, "")
        self.Collect = QtWidgets.QWidget()
        self.Collect.setObjectName("Collect")
        self.tabWidget.addTab(self.Collect, "")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout_9 = QtWidgets.QGridLayout(self.tab)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.gridLayout_8 = QtWidgets.QGridLayout()
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.debug_string = QtWidgets.QPushButton(self.tab)
        self.debug_string.setObjectName("debug_string")
        self.gridLayout_8.addWidget(self.debug_string, 0, 1, 1, 1)
        self.debug_motor = QtWidgets.QPushButton(self.tab)
        self.debug_motor.setObjectName("debug_motor")
        self.gridLayout_8.addWidget(self.debug_motor, 0, 0, 1, 1)
        self.debug_operation = QtWidgets.QPushButton(self.tab)
        self.debug_operation.setObjectName("debug_operation")
        self.gridLayout_8.addWidget(self.debug_operation, 1, 0, 1, 1)
        self.debug_shutter = QtWidgets.QPushButton(self.tab)
        self.debug_shutter.setObjectName("debug_shutter")
        self.gridLayout_8.addWidget(self.debug_shutter, 1, 1, 1, 1)
        self.debug_raster = QtWidgets.QPushButton(self.tab)
        self.debug_raster.setObjectName("debug_raster")
        self.gridLayout_8.addWidget(self.debug_raster, 2, 0, 1, 1)
        self.debug_Debug = QtWidgets.QPushButton(self.tab)
        self.debug_Debug.setObjectName("debug_Debug")
        self.gridLayout_8.addWidget(self.debug_Debug, 2, 1, 1, 1)
        self.gridLayout_9.addLayout(self.gridLayout_8, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab, "")
        self.gridLayout_2.addWidget(self.tabWidget, 0, 0, 1, 3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1525, 20))
        self.menubar.setObjectName("menubar")
        self.menuMeshBestGUI = QtWidgets.QMenu(self.menubar)
        self.menuMeshBestGUI.setObjectName("menuMeshBestGUI")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setEnabled(True)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menuMeshBestGUI.addSeparator()
        self.menubar.addAction(self.menuMeshBestGUI.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(1)
        self.toolBox.setCurrentIndex(1)
        self.Overlap_Select_1.setCurrentIndex(1)
        self.Overlap_Select_2.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Mesh and Collect"))
        self.LastInfo.setText(_translate("MainWindow", "LastInfo"))
        self.label.setText(_translate("MainWindow", "TPS State:"))
        self.TPSStateText.setText(_translate("MainWindow", "Open"))
        self.Current.setSuffix(_translate("MainWindow", " mA"))
        self.label_2.setText(_translate("MainWindow", "Energy:"))
        self.Energy.setSuffix(_translate("MainWindow", "Kev"))
        self.Active.setText(_translate("MainWindow", "Unknow"))
        self.comboBox.setItemText(0, _translate("MainWindow", "I has no idea....."))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1), _translate("MainWindow", "Project Setup"))
        self.Autocenter.setText(_translate("MainWindow", "Auto Center"))
        self.Zoom1.setText(_translate("MainWindow", "Zoom1"))
        self.pos_10deg.setText(_translate("MainWindow", "+10deg"))
        self.pos_90deg.setText(_translate("MainWindow", "+90deg"))
        self.Centermode.setText(_translate("MainWindow", "Center mode"))
        self.Zoom2.setText(_translate("MainWindow", "Zoom2"))
        self.neg_90deg.setText(_translate("MainWindow", "-90deg"))
        self.neg_10deg.setText(_translate("MainWindow", "-10deg"))
        self.Zoom3.setText(_translate("MainWindow", "Zoom3"))
        self.Zoom4.setText(_translate("MainWindow", "Zoom4"))
        self.Transfermode.setText(_translate("MainWindow", "Transfer mode"))
        self.Raster.setText(_translate("MainWindow", "Take Raster Image"))
        self.StartRaster.setText(_translate("MainWindow", "Start Raster"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_3), _translate("MainWindow", "File Setup"))
        self.label_14.setText(_translate("MainWindow", "Detector Distance"))
        self.Beamsize.setItemText(0, _translate("MainWindow", "50"))
        self.Beamsize.setItemText(1, _translate("MainWindow", "40"))
        self.Beamsize.setItemText(2, _translate("MainWindow", "30"))
        self.Beamsize.setItemText(3, _translate("MainWindow", "20"))
        self.Beamsize.setItemText(4, _translate("MainWindow", "10"))
        self.Beamsize.setItemText(5, _translate("MainWindow", "5"))
        self.Beamsize.setItemText(6, _translate("MainWindow", "1"))
        self.ExpousetimeType.setItemText(0, _translate("MainWindow", "Exposed time"))
        self.ExpousetimeType.setItemText(1, _translate("MainWindow", "Rate"))
        self.label_15.setText(_translate("MainWindow", "Dose"))
        self.label_12.setText(_translate("MainWindow", "BeamSize"))
        self.label_13.setText(_translate("MainWindow", "Attenuation"))
        self.doubleSpinBox_12.setSuffix(_translate("MainWindow", "Mgy"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_5), _translate("MainWindow", "Raster scan Par"))
        self.Overlap_Select_1.setItemText(0, _translate("MainWindow", "None"))
        self.Overlap_Select_1.setItemText(1, _translate("MainWindow", "Grid"))
        self.Overlap_Select_1.setItemText(2, _translate("MainWindow", "Dozor score"))
        self.Overlap_Select_1.setItemText(3, _translate("MainWindow", "Number of Peaks"))
        self.Overlap_Select_1.setItemText(4, _translate("MainWindow", "Visible resolution"))
        self.Overlap_Select_1.setItemText(5, _translate("MainWindow", "Crystal Map"))
        self.Overlap_Select_1.setItemText(6, _translate("MainWindow", "Crystal Map with Dozor score"))
        self.label_8.setText(_translate("MainWindow", "Opacity(%)"))
        self.label_4.setText(_translate("MainWindow", "Listnumber"))
        self.pushButton_4.setText(_translate("MainWindow", ">"))
        self.pushButton_3.setText(_translate("MainWindow", "^"))
        self.pushButton.setText(_translate("MainWindow", "<"))
        self.pushButton_2.setText(_translate("MainWindow", "v"))
        self.Overlap_Select_2.setItemText(0, _translate("MainWindow", "None"))
        self.Overlap_Select_2.setItemText(1, _translate("MainWindow", "Grid"))
        self.Overlap_Select_2.setItemText(2, _translate("MainWindow", "Dozor score"))
        self.Overlap_Select_2.setItemText(3, _translate("MainWindow", "Number of Peaks"))
        self.Overlap_Select_2.setItemText(4, _translate("MainWindow", "Visible resolution"))
        self.Overlap_Select_2.setItemText(5, _translate("MainWindow", "Crystal Map"))
        self.Overlap_Select_2.setItemText(6, _translate("MainWindow", "Crystal Map with Dozor score"))
        self.label_9.setText(_translate("MainWindow", "Opacity(%)"))
        self.label_5.setText(_translate("MainWindow", "Listnumber"))
        self.pushButton_5.setText(_translate("MainWindow", "<"))
        self.pushButton_11.setText(_translate("MainWindow", ">"))
        self.pushButton_12.setText(_translate("MainWindow", "^"))
        self.pushButton_13.setText(_translate("MainWindow", "v"))
        self.label_3.setText(_translate("MainWindow", "Diffraction"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_5), _translate("MainWindow", "Tab 1"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_6), _translate("MainWindow", "Tab 2"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Crystal Center&Raster"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Collect), _translate("MainWindow", "Collect"))
        self.debug_string.setText(_translate("MainWindow", "string"))
        self.debug_motor.setText(_translate("MainWindow", "Motor"))
        self.debug_operation.setText(_translate("MainWindow", "operation"))
        self.debug_shutter.setText(_translate("MainWindow", "shutter"))
        self.debug_raster.setText(_translate("MainWindow", "Raster"))
        self.debug_Debug.setText(_translate("MainWindow", "Debug"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Debug"))
        self.menuMeshBestGUI.setTitle(_translate("MainWindow", "Experiment"))