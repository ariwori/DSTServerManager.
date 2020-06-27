# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QRadioButton, QCheckBox, QComboBox, QStyledItemDelegate, QButtonGroup, QTabWidget, QScrollArea, QTableWidget, QAbstractItemView, QHeaderView, QFrame, QGroupBox, QMessageBox,  QTableWidgetItem, QTextBrowser
from PyQt5.QtCore import Qt
from globalvar import CONFIG_DIR, CLUSTER_DIR, TEMP_FILE
import os
import sys
import json
import random
import shutil
from LuaTableParser import LuaTableParser
from config import GlobalConfig
from newsharddialog import NewShardDialog
from settingswindow import SettingsWidget
from clustertab import ClusterWidget
from lupa import LuaRuntime
from modconfigdialog import ModConfigDialog


class ModWidget(QWidget):

    def __init__(self, parent=None):
        super(ModWidget, self).__init__(parent)

        modlayout = QHBoxLayout()

        allmodtablelayout = QVBoxLayout()
        modlayout.setContentsMargins(5, 0, 5, 0)
        self.allmodtable = QTableWidget()
        self.allmodtable.setFixedWidth(350)
        self.allmodtable.setColumnCount(4)
        # 禁止编辑
        self.allmodtable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 设置选择整行
        self.allmodtable.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 只选中单行
        self.allmodtable.setSelectionMode(QAbstractItemView.SingleSelection)
        # 自动列宽，随内容
        self.allmodtable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.allmodtable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.allmodtable.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.allmodtable.horizontalHeader().setDefaultSectionSize(0)

        self.allmodtable.clicked.connect(self.modSelect)

        btn = QPushButton()
        btn.setText("刷新列表")
        allmodtablelayout.addWidget(self.allmodtable)
        allmodtablelayout.addWidget(btn)
        btn.clicked.connect(self.initData)

        modlayout.addLayout(allmodtablelayout)

        # MOD 详情
        detaillayout = QVBoxLayout()
        self.modname = QLabel()
        self.modname.setStyleSheet("QLabel { font-size: 30px; }")
        self.modname.setWordWrap(True)
        detaillayout.addWidget(self.modname)
        self.modav = QLabel()
        self.modav.setWordWrap(True)
        detaillayout.addWidget(self.modav)
        self.moddesciption = QTextBrowser()
        detaillayout.addWidget(self.moddesciption)

        btnl = QHBoxLayout()
        self.btn1 = QPushButton()
        self.btn1.setText("更改MOD配置")
        btn2 = QPushButton()
        btn2.setText("打开MOD文件夹")
        btn2.clicked.connect(self.openModDir)
        self.btn1.clicked.connect(self.modConfig)
        btnl.addWidget(self.btn1)
        btnl.addWidget(btn2)
        detaillayout.addLayout(btnl)

        modlayout.addLayout(detaillayout)

        self.setLayout(modlayout)

        self.currentSelectMod = ""
        self.currentSelectModChecked = False
        self.currentModOptions = {}

    def initData(self):
        self.loadAllLoaclMod()
        self.loadSaveMod()

    def getCurrentCluster(self):
        tc = GlobalConfig(TEMP_FILE)
        return tc.get("TEMP", "cluster_index")

    def getModDir(self):
        dirstr = SettingsWidget().getClientPath()
        if dirstr != "" and os.path.exists(dirstr):
            if sys.platform == "darwin":
                dirstr = os.path.join(dirstr, "Contents")
            self.modrootdir = os.path.join(dirstr, "mods")
            return True
        else:
            return False

    # 取出MOD基本信息
    def getModInfo(self, root, moddir, t):
        modinfo = {}
        olddir = os.getcwd()
        os.chdir(self.modrootdir)
        if not os.path.exists(os.path.join(root, "json.lua")):
            shutil.copyfile(os.path.join(CONFIG_DIR, "json.lua"), os.path.join(root, "json.lua"))
        if os.path.exists(os.path.join(root, moddir, "modinfo.lua")):
            lua = LuaRuntime(unpack_returned_tuples=True)
            lua.require(os.path.join(moddir, "modinfo"))
            if os.path.exists(os.path.join(root, moddir, "modinfo_chs.lua")):
                lua.require(os.path.join(moddir, "modinfo_chs"))
            modinfo["name"] = lua.eval('name').strip()
            modinfo["server_only_mod"] = lua.eval('server_only_mod')
            modinfo["all_clients_require_mod"] = lua.eval('all_clients_require_mod')
            modinfo["client_only_mod"] = lua.eval('client_only_mod')
            if t != "basic":
                modinfo["description"] = lua.eval('description').strip()
                modinfo["author"] = lua.eval('author').strip()
                modinfo["version"] = lua.eval('version').strip()
                lua.require("json")
                config_json_str = lua.eval('encode_compliant(configuration_options)')
                modinfo["configuration_options"] = json.loads(config_json_str)

        os.chdir(olddir)
        return modinfo

    def getDictValue(self, d, k):
        if k in d:
            return d[k]
        else:
            return False

    def modConfig(self):
        if self.currentSelectMod == "":
            QMessageBox.warning(self, "警告", "未选择MOD！", QMessageBox.Yes)
        elif not self.currentSelectModChecked:
            QMessageBox.warning(self, "警告", "选中MOD未启用！", QMessageBox.Yes)
        else:
            self.modConfigDialog = ModConfigDialog(self)
            self.modConfigDialog.setWindowTitle("修改MOD "+self.modname.text()+" 配置")
            self.modConfigDialog.moddir = self.currentSelectMod
            self.modConfigDialog.initData(self.currentModOptions)
            self.modConfigDialog.exec()

    def loadSaveMod(self):
        self.savemod = {}
        file = ""
        rootdir = os.path.join(CLUSTER_DIR, "Cluster_" + self.getCurrentCluster())
        for sdir in os.listdir(rootdir):
            if os.path.isdir(os.path.join(rootdir, sdir)):
                if os.path.exists(os.path.join(rootdir, sdir, "modoverrides.lua")):
                    file = os.path.join(rootdir, sdir, "modoverrides.lua")
                    break
        if file != "":
            f = open(file, 'r', encoding='utf-8')
            data = f.read()
            f.close()
            data = data.replace("return", "")
            p1 = LuaTableParser()
            p1.load(data)
            self.savemod = p1.dumpDict()
        rowcount = self.allmodtable.rowCount()
        for i in range(rowcount):
            w = self.allmodtable.cellWidget(i, 0)
            if w.moddir in self.savemod and self.savemod[w.moddir]['enabled']:
                w.setChecked(True)

    def modCheck(self):
        w = self.sender()
        if w.moddir == self.currentSelectMod:
            self.currentSelectModChecked = w.isChecked()
        if w.isChecked():
            if not w.moddir not in self.savemod:
                self.savemod[w.moddir]['enabled'] = True
            else:
                self.savemod[w.moddir] = {}
                self.savemod[w.moddir]["configuration_options"] = {}
                self.savemod[w.moddir]['enabled'] = True
        else:
            if w.moddir in self.savemod:
                self.savemod[w.moddir]['enabled'] = False
        rootdir = os.path.join(CLUSTER_DIR, "Cluster_" + self.getCurrentCluster())
        for sdir in os.listdir(rootdir):
            if os.path.isdir(os.path.join(rootdir, sdir)):
                file = os.path.join(rootdir, sdir, "modoverrides.lua")
                p1 = LuaTableParser()
                p1.loadDict(self.savemod)
                data = "return" + p1.dump()
                with open(file, 'w', encoding='utf-8') as f:
                    f.write(data)
                    f.close()

    def openModDir(self):
        if self.currentSelectMod == "":
            path = self.modrootdir
        else:
            path = os.path.join(self.modrootdir, self.currentSelectMod)
        if os.path.exists(path):
            if sys.platform == "darwin":
                os.system("open \"%s\"" % path)
            elif sys.platform == "":
                os.system("start explorer %s" % path)
            else:
                QMessageBox.warning(self, "警告", "当前系统不支持该操作", QMessageBox.Yes)
        else:
            QMessageBox.warning(self, "警告", "存档文件夹不存在", QMessageBox.Yes)

    def modSelect(self):
        row = self.allmodtable.selectedItems()[0].row()
        self.currentSelectModChecked = self.allmodtable.cellWidget(row, 0).isChecked()
        moddir = self.allmodtable.selectedItems()[2].text()
        self.currentSelectMod = moddir
        info = self.getModInfo(self.modrootdir, moddir, "detail")
        name = self.getDictValue(info, 'name')
        self.modname.setText(name)
        a = self.getDictValue(info, 'author')
        v = self.getDictValue(info, 'version')
        self.modav.setText("作者：%s    版本：%s" % (a, v))
        des = self.getDictValue(info, 'description')
        self.moddesciption.setText(des)
        self.currentModOptions = self.getDictValue(info, "configuration_options")
        if self.currentModOptions and len(self.currentModOptions) > 0:
            self.btn1.setEnabled(True)
        else:
            self.btn1.setEnabled(False)

    # 加载本地所有MOD进入列表
    def loadAllLoaclMod(self):
        self.allmodtable.clear()
        if self.getModDir():
            row = 0
            # 设置标题
            self.allmodtable.setHorizontalHeaderLabels(['启用', '名称', '加载类型', ''])
            for modir in os.listdir(self.modrootdir):
                modpath = os.path.join(self.modrootdir, modir)
                if os.path.isdir(modpath):
                    info = self.getModInfo(self.modrootdir, modir, "basic")
                    self.allmodtable.setRowCount(row + 1)
                    check = QCheckBox()
                    check.moddir = modir
                    check.stateChanged.connect(self.modCheck)
                    self.allmodtable.setCellWidget(row, 0, check)
                    self.allmodtable.setItem(row, 1, QTableWidgetItem(self.getDictValue(info, 'name') and self.getDictValue(info, 'name') or modir))
                    if self.getDictValue(info, 'server_only_mod'):
                        mt = "服务端"
                    if self.getDictValue(info, 'all_clients_require_mod'):
                        mt = "所有人"
                    if self.getDictValue(info, 'client_only_mod'):
                        mt = "客户端"
                    self.allmodtable.setItem(row, 2, QTableWidgetItem(mt))
                    self.allmodtable.setItem(row, 3, QTableWidgetItem(modir))
                    row += 1
        else:
            QMessageBox.warning(self, "错误警告", "客户端路径未设置或不正确，\n无法读取MOD，请到设置面板确认！", QMessageBox.Yes)