# -*- coding: utf-8 -*-

import os
import sys
import urllib.request 

from utils import *
from nodefs import *
from dirlist import *
from consts import *
from providers import *

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QTreeWidgetItem, QApplication, QSpacerItem, QSizePolicy, QFrame
from PyQt5.QtGui import QIcon


class Mode():
    is_dirlist_loaded = False
    is_getting_dirlist = False
    is_downloading_file = False
    is_searching = False

    def starting_downloading(self):
        self.is_downloading_file = True

    def finished_downloading(self):
        self.is_downloading_file = False

    def starting_search(self):
        self.is_searching = True

    def finished_search(self):
        self.is_searching = False

    def starting_dirlist(self):
        self.is_dirlist_loaded = False
        self.is_getting_dirlist = True

    def finished_dirlist(self):
        self.is_dirlist_loaded = True
        self.is_getting_dirlist = False

    def no_dirlist(self):
        self.is_dirlist_loaded = False
        self.is_getting_dirlist = False

class Ui_MainWindow(QObject):
    def __init__(self):
        super().__init__()
        # Dirlist
        self.thread_dirlist = None
        self.worker_dirlist = None
        self.working_dir = None
        self.dirlist_path = None
        self.list_new_nodes_to_process = [] # Batch processing
        # Selected items
        self.selected_tree_item = None
        self.selected_tree_node = None
        self.node_processing = None
        # URL
        self.current_url = None
        self.current_provider = None
        # Mode
        self.mode = Mode()
        # Nodes
        self.nodes_stats = None
        self.root_node = None

    def setupUi(self, MainWindow):
        # Main windows
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle("Storage File Viewer")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        # Vertical layout
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        #####################################

        ### Horizontal Layout 1 - URL###
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout.addLayout(self.horizontalLayout)
        # Label url
        self.labelUrl = QtWidgets.QLabel(self.centralwidget)
        self.labelUrl.setObjectName("labelUrl")
        self.labelUrl.setText("Name / URL")
        self.horizontalLayout.addWidget(self.labelUrl)
        # Line edit url
        self.lineEditUrl = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEditUrl.setObjectName("lineEditUrl")
        self.lineEditUrl.setPlaceholderText("mybucket")
        self.horizontalLayout.addWidget(self.lineEditUrl)
        # Bucket get dirlist
        self.buttonGetDirlist = QtWidgets.QPushButton(self.centralwidget)
        self.buttonGetDirlist.setObjectName("buttonGetDirlist")
        self.buttonGetDirlist.setText("Get Dirlist")
        self.horizontalLayout.addWidget(self.buttonGetDirlist)
        #####################################

        ### Horizontal Layout 2 - Dirlist path###
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        # Label dirlist path
        self.labelDirlistPath = QtWidgets.QLabel(self.centralwidget)
        self.labelDirlistPath.setObjectName("labelDirlistPath")
        self.labelDirlistPath.setText("Dirlist File")
        self.horizontalLayout_2.addWidget(self.labelDirlistPath)
        # Label dirlist path
        self.lineEditDirlistPath = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEditDirlistPath.setObjectName("lineEditDirlistPath")
        self.horizontalLayout_2.addWidget(self.lineEditDirlistPath)
        # Button load dirlist offline
        self.buttonLoadDirlistOffline = QtWidgets.QPushButton(self.centralwidget)
        self.buttonLoadDirlistOffline.setObjectName("buttonLoadDirlistOffline")
        self.buttonLoadDirlistOffline.setText("Load Offline")
        self.horizontalLayout_2.addWidget(self.buttonLoadDirlistOffline)
        # Button open directory
        self.buttonOpenDir = QtWidgets.QPushButton(self.centralwidget)
        self.buttonOpenDir.setObjectName("buttonOpenDir")
        self.buttonOpenDir.setText("Open Dir")
        self.horizontalLayout_2.addWidget(self.buttonOpenDir)
        #####################################

        # Separator
        self.separatorLine = QFrame()
        self.separatorLine.setFrameShape(QFrame.HLine)
        self.verticalLayout.addWidget(self.separatorLine)
        #####################################

        ### Horizontal Layout 3 - ￿Search ###
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        # Label search
        self.labelSearch = QtWidgets.QLabel(self.centralwidget)
        self.labelSearch.setObjectName("labelSearch")
        self.labelSearch.setText("Search")
        self.horizontalLayout_3.addWidget(self.labelSearch)
        # Line edit search
        self.lineEditSearch = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEditSearch.setObjectName("lineEditSearch")
        self.lineEditSearch.setEnabled(False)
        self.horizontalLayout_3.addWidget(self.lineEditSearch)
        # Button search
        self.buttonSearchDo = QtWidgets.QPushButton(self.centralwidget)
        self.buttonSearchDo.setObjectName("buttonSearchDo")
        self.buttonSearchDo.setText("Search")
        self.buttonSearchDo.setEnabled(False)
        self.horizontalLayout_3.addWidget(self.buttonSearchDo)
        # Button clear search
        self.buttonSearchClear = QtWidgets.QPushButton(self.centralwidget)
        self.buttonSearchClear.setObjectName("buttonSearchClear")
        self.buttonSearchClear.setText("Clear")
        self.buttonSearchClear.setEnabled(False)
        self.horizontalLayout_3.addWidget(self.buttonSearchClear)
        #####################################

        ### Horizontal Layout 4 - Tree view ###
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        # Tree widget
        self.treeWidget = QtWidgets.QTreeWidget(self.centralwidget)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "Name")
        self.treeWidget.headerItem().setText(1, "Size")
        self.treeWidget.headerItem().setText(2, "Date Modified")
        self.treeWidget.headerItem().setText(3, "Downloaded")
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.horizontalLayout_4.addWidget(self.treeWidget)
        #####################################

        ### More items ###
        # Label statistics
        self.labelStatistics = QtWidgets.QLabel(self.centralwidget)
        self.labelStatistics.setObjectName("labelStatistics")
        self.labelStatistics.setText("Please load S3 bucket")
        self.verticalLayout.addWidget(self.labelStatistics)
        # Progress bar ￿
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        # Label status
        self.labelStatus = QtWidgets.QLabel(self.centralwidget)
        self.labelStatus.setText("")
        self.labelStatus.setObjectName("labelStatus")
        self.verticalLayout.addWidget(self.labelStatus)
        #####################################
        MainWindow.setCentralWidget(self.centralwidget)

        ### Connect functions ###
        self.buttonGetDirlist.clicked.connect(self.button_click_download_and_process_bucket_dirlist)
        self.buttonLoadDirlistOffline.clicked.connect(self.button_click_process_dirlist)
        self.buttonOpenDir.clicked.connect(self.button_click_open_working_dir)
        self.buttonSearchDo.clicked.connect(self.button_click_search_do)
        self.buttonSearchClear.clicked.connect(self.button_click_search_clear)
        self.treeWidget.doubleClicked['QModelIndex'].connect(self.tree_view_item_double_clicked)
        self.treeWidget.customContextMenuRequested.connect(self.menu_context_tree_view_widget)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        #####################################

    ################################################
    ######### Menu context in tree widget ##########
    ################################################
    # Menu when right-click on a tree view item
    def menu_context_tree_view_widget(self, point):
        index = self.treeWidget.indexAt(point)
        if not index.isValid():
            return
        self.selected_tree_item = self.treeWidget.itemAt(point)
        self.selected_tree_node = self.tree_item_to_node(self.selected_tree_item)
        # Sanity
        if not self.selected_tree_node:
            self.selected_tree_item = None
            self.selected_tree_node = None
            return 
        is_dir = self.selected_tree_node.is_directory
        is_downloaded = self.selected_tree_node.is_downloaded
        children_files_count = self.selected_tree_node.get_how_many_childern_are_files()

        # Building the menu
        menu = QtWidgets.QMenu()
        fake_action_node_desc = menu.addAction(str(self.selected_tree_node))
        menu.addSeparator()
        # Set actions
        download_title = "Download"
        if is_dir and children_files_count > 0:
            download_title = "Download ({} files)".format(children_files_count)
        action_download = menu.addAction(download_title)
        action_download.triggered.connect(self.tree_item_download)
        can_download = (not is_downloaded) and ((not is_dir) or (is_dir and children_files_count > 0))
        action_download.setEnabled(can_download)

        action_open_file = menu.addAction("Open File")
        action_open_file.triggered.connect(self.tree_item_open_file)
        action_open_file.setEnabled(not is_dir and is_downloaded)
        action_open_dir = menu.addAction("Open Directory")
        action_open_dir.triggered.connect(self.tree_item_open_directory)
        action_open_dir.setEnabled(is_dir or is_downloaded)
        menu.exec_(self.treeWidget.mapToGlobal(point))

    def tree_item_download(self):
        if self.selected_tree_node.is_file:
            self.download_node_with_gui_update(self.selected_tree_node)
        else:
            # Download all child-files
            real_selected_node = self.selected_tree_node
            real_selected_tree = self.selected_tree_item
            real_selected_tree_child_count = real_selected_tree.childCount()
            for i in range(real_selected_tree_child_count):
                tree_child_item = real_selected_tree.child(i)
                tree_child_node = self.tree_item_to_node(tree_child_item)
                if tree_child_node.is_file:
                    self.selected_tree_item = tree_child_item
                    self.selected_tree_node = tree_child_node
                    self.download_node_with_gui_update(tree_child_node)
            self.selected_tree_node = real_selected_node
            self.selected_tree_item = real_selected_tree

    def tree_item_open_file(self):
        open_file(self.selected_tree_node.download_path)

    def tree_item_open_directory(self):
        file_path = self.prepare_dirs_for_download(self.selected_tree_node)
        dir_path = os.path.dirname(file_path)
        open_dir(dir_path)

    ################################################
    ############# Tree item / nodes ################
    ################################################
    def setup_root_node(self):
        self.nodes_stats = FSNodeStats()
        self.root_node = FSNode("", None, 0)
        self.create_tree_view_item(self.root_node, self.treeWidget)

    # Get full path of a tree item
    def get_tree_item_full_path(self, item):
        out = item.text(0)
        parent = item.parent()
        if parent:
            out = self.get_tree_item_full_path(parent) + "/" + out
        return out

    # Node to tree item
    def create_tree_view_item(self, node, tree_parent):
        # Create tree item
        tree_item = QTreeWidgetItem(tree_parent, [node.basename, str(node.get_human_readable_size()), node.get_date_modified(), ""])
        # Set icon
        if node.is_directory:
            tree_item.setIcon(0, QIcon(get_asset_path('assets/folder.png')))
        else:
            tree_item.setIcon(0, QIcon(get_asset_path('assets/file.png')))
        node.item_view = tree_item
        return tree_item

    # Tree item to node
    def tree_item_to_node(self, tree_item):
        selected_node = None
        # Get full path from item
        item_full_path = self.get_tree_item_full_path(tree_item)
        item_full_path = item_full_path.lstrip("/")
        # Find node from path
        try:
            selected_node = self.root_node.get_sub_node(item_full_path)
        except Exception as e:
            show_message_box(str(e))
        return selected_node

    ################################################
    #################### Input #####################
    ################################################
    # Check url input and extract details
    def check_input_details(self):
        self.current_url = self.lineEditUrl.text().strip()
        if not self.current_url:
            show_message_box("Please fill url or bucket name")
            return False
        self.current_provider = find_provider_class_by_url(self.current_url)
        if not self.current_provider:
            show_message_box("Could not find provider for '{}'".format(self.current_url))
            return False
        if not self.current_provider.check():
            return False
        return True

    ################################################
    ############### Download files #################
    ################################################
    def update_progress_bar(self, blocknum, blocksize, totalsize):
        ## Calculate the progress
        readed_data = blocknum * blocksize 
        if totalsize > 0: 
            download_percentage = readed_data * 100 / totalsize 
            self.progressBar.setValue(download_percentage)
            # Finished downloading
            if self.progressBar.value() >= 100:
                pass
            QApplication.processEvents()

    def prepare_dirs_for_download(self, node):
        path_download = node.full_path.lstrip("/") # remove the first / if any
        # Make dirs
        path_save_to = os.path.join(self.working_dir, self.current_url, path_download)
        path_save_to_dir = os.path.dirname(path_save_to)
        try:
            os.makedirs(path_save_to_dir, exist_ok=True)
        except Exception as e:
            show_message_box(str(e))
            return None
        return path_save_to

    def download_node(self, node):
        # Sanity
        if not self.check_input_details():
            return False
        path_save_to = self.prepare_dirs_for_download(node)
        if not path_save_to:
            return False
        # Prepare download url
        path_download = node.full_path.lstrip("/") # remove the first / if any
        url_download = self.current_provider.get_download_url(path_download)
        url_download_encoded = urllib.parse.quote(url_download, safe=':/')
        try:
            # Download
            urllib.request.urlretrieve(url_download_encoded, path_save_to, self.update_progress_bar)
            # Update node
            self.node_processing = node
            self.node_processing.is_downloaded = True
            self.node_processing.download_path = path_save_to
        except Exception as e:
            show_message_box(url_download + ":\n" + str(e))
            return False
        return True

    def download_node_with_gui_update(self, node):
        if not self.selected_tree_node or not self.selected_tree_node.is_file:
            return
        # Update UI
        self.mode.starting_downloading()
        # Download
        if self.download_node(node):
            self.selected_tree_item.setText(3, "   V ")
        self.mode.finished_downloading()

    ################################################
    ################## Actions #####################
    ################################################
    @pyqtSlot( )
    def tree_view_item_double_clicked(self):
        # Get selected item
        selected_items = self.treeWidget.selectedItems()
        if len(selected_items) < 1:
            self.selected_tree_item = None
            self.selected_tree_node = None
            return 
        self.selected_tree_item = selected_items[0]
        self.selected_tree_node = self.tree_item_to_node(self.selected_tree_item)
        # Download node
        self.download_node_with_gui_update(self.selected_tree_node)
        
    @pyqtSlot( )
    def button_click_process_dirlist(self):
        file_dialog_options = QtWidgets.QFileDialog.Options()
        file_dialog_options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_dialog_title = "Select dirlist file"
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, file_dialog_title, "", "All Files (*)", options=file_dialog_options)
        # Update working dir
        self.dirlist_path = file_path
        self.working_dir = os.path.dirname(os.path.abspath(file_path))
        # Update UI
        self.populate_tree_view_with_gui(file_path)

    @pyqtSlot( )
    def button_click_download_and_process_bucket_dirlist(self):
        # Check bucket details
        if self.check_input_details():
            self.populate_tree_view_with_gui(self.dirlist_path)

    @pyqtSlot( )
    def button_click_open_working_dir(self):
        if self.working_dir:
            open_dir(self.working_dir)

    @pyqtSlot( )
    def button_click_search_do(self):
        # Hide all
        for item in self.treeWidget.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            item.setHidden(True)
            # Mark as search mode only if there are items
            self.mode.starting_search()
        if self.mode.is_searching:
            # Show only those that match the search
            search_query = self.lineEditSearch.text()
            flags = QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive
            #flags |= QtCore.Qt.MatchRegExp # use regex
            for item in self.treeWidget.findItems(search_query, flags):
                # Walk up the chain
                item_temp = item
                while item_temp:
                    item_temp.setHidden(False)
                    item_temp = item_temp.parent()
                    # If parent is not hidden, all the chain is visible so no need to redo
                    if item_temp and not item_temp.isHidden():
                        break
        self.update_ui()
    
    @pyqtSlot( )
    def button_click_search_clear(self):
        self.lineEditSearch.setText("")
        if self.mode.is_searching:
            self.mode.finished_search()
            # Show all
            for item in self.treeWidget.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
                item.setHidden(False)
        self.update_ui()

    ################################################
    ################## UI Updates ##################
    ################################################
    def update_ui(self):
        if self.dirlist_path:
            self.lineEditDirlistPath.setText(self.dirlist_path)
        if self.mode.is_searching:
            self.labelStatus.setText("Showing results for: '{}'".format(self.lineEditSearch.text()))
            self.progressBar.setValue(0)
        elif self.mode.is_getting_dirlist:
            if self.node_processing:
                self.labelStatus.setText("Currently processing: {}..".format(self.node_processing.full_path))
            self.progressBar.setValue(0)
            self.labelStatistics.setText("Showing {} items (dirs: {}, files: {}) | Accumulated size: {} | Dates: {} - {}".format(self.nodes_stats.count_total, self.nodes_stats.count_dirs, self.nodes_stats.count_files, self.nodes_stats.get_human_readable_size(), self.nodes_stats.date_oldest, self.nodes_stats.date_newest))
        elif self.mode.is_downloading_file:
            self.labelStatus.setText("Downloading {}...".format(self.node_processing.full_path))
        elif self.mode.is_dirlist_loaded:
            self.labelStatus.setText("Working dir: {}".format(self.working_dir))
            self.labelStatistics.setText("Showing items {} (dirs: {}, files: {}) | Accumulated size: {} | Dates: {} - {}".format(self.nodes_stats.count_total, self.nodes_stats.count_dirs, self.nodes_stats.count_files, self.nodes_stats.get_human_readable_size(), self.nodes_stats.date_oldest, self.nodes_stats.date_newest))
            self.progressBar.setValue(0)
            # Enable search
            self.buttonSearchDo.setEnabled(True)
            self.buttonSearchClear.setEnabled(True)
            self.lineEditSearch.setEnabled(True)


    ################################################
    ################## Dirlist #####################
    ################################################
    # Populate tree view with all items
    def populate_tree_view(self, node, tree):
        tree_item = self.create_tree_view_item(node, tree)
        # Populate children
        for child_node in node.children.values():
            self.populate_tree_view(child_node, tree_item)

    def dirlist_report_progress(self, node, force_update=False):
        if node:
            self.list_new_nodes_to_process.append(node)
        if force_update or len(self.list_new_nodes_to_process) % NODE_BATCH_UPDATE_COUNT:
            # Process batch
            for node in self.list_new_nodes_to_process:
                self.create_tree_view_item(node, node.parent.item_view)
            # Save last processed node and clear list
            if self.list_new_nodes_to_process:
                self.node_processing = self.list_new_nodes_to_process[-1]
                self.list_new_nodes_to_process.clear()

    def dirlist_thread_finished(self):
        # One last batch processing
        self.dirlist_report_progress(None, force_update=True)
        # Update status
        self.mode.finished_dirlist()
        self.update_ui()

    def populate_tree_view_with_gui(self, dirlist_path=None):
        # Clear all
        self.selected_tree_item = None
        self.selected_tree_node = None
        self.treeWidget.clear()
        # Init
        self.setup_root_node()
        self.thread_dirlist = QThread()
        self.worker_dirlist = DirlistWorker(nodes_stats=self.nodes_stats, root_node=self.root_node, provider=self.current_provider, pre_generated_dirlist_path=dirlist_path)
        # Get working dirs
        self.working_dir = self.worker_dirlist.working_dir
        self.dirlist_path = self.worker_dirlist.dirlist_path
        # Move worker to the thread
        self.worker_dirlist.moveToThread(self.thread_dirlist)
        # Connect signals and slots
        self.thread_dirlist.started.connect(self.worker_dirlist.run)
        self.thread_dirlist.finished.connect(self.thread_dirlist.deleteLater)
        self.thread_dirlist.finished.connect(self.dirlist_thread_finished)
        self.worker_dirlist.finished.connect(self.thread_dirlist.quit)
        self.worker_dirlist.finished.connect(self.worker_dirlist.deleteLater)
        self.worker_dirlist.progress.connect(self.dirlist_report_progress)
        # Start the thread
        self.thread_dirlist.start()
        # Update status
        self.mode.starting_dirlist()
        self.update_ui()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())