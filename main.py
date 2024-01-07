from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from files.about import AboutDialog

import json
import os

class HistoryDialog(QDialog):
    def __init__(self, history_data, main_browser):
        super().__init__()

        self.setWindowTitle("History")
        self.setGeometry(100, 100, 600, 400)

        # Set the window icon
        icon_path = os.path.join("_internal","images", "browser_.png")
        self.setWindowIcon(QIcon(icon_path))

        # Store a reference to the main browser
        self.main_browser = main_browser

        # Create a QVBoxLayout for the dialog
        layout = QVBoxLayout()

        # Create a QTextBrowser to display the history text with clickable links
        self.history_browser = QTextBrowser()
        self.history_browser.setOpenExternalLinks(False)  # Disable external links to handle them manually
        self.history_browser.setHtml(self.format_history_html(history_data))

        # Connect the anchorClicked signal to a slot for handling link clicks
        self.history_browser.anchorClicked.connect(self.handle_link_clicked)

        self.setStyleSheet(open(os.path.join('styles','history_dialog_style.css')).read())

        # Create a scroll area for the history content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.history_browser)

        # Add the scroll area to the layout
        layout.addWidget(scroll_area)

        # Add a button to clear history
        clear_button = QPushButton("Очистить историю")
        clear_button.clicked.connect(self.clear_history)
        layout.addWidget(clear_button)

        # Set the layout for the dialog
        self.setLayout(layout)

    def format_history_html(self, history_data):
        # Format history data as HTML content
        html_content = "<ul>"
        for entry in history_data:
            title = entry.get("title", "Untitled")
            url = entry.get("url", "")
            timestamp = entry.get("timestamp", "")
            html_content += f"<li><div><strong>{title}</strong></div><div><a href='{url}'>{url}</a></div><div>{timestamp}</div></li>"
        html_content += "</ul>"
        return html_content

    def handle_link_clicked(self, link):
        # Open the clicked link in the main browser
        url = link.toString()

        # Ensure the URL is not 'javascript:void(0);'
        if not url.startswith("javascript:"):
            # Open the URL in the main browser
            self.main_browser.tab_widget.currentWidget().setUrl(QUrl(url))

            # Close the HistoryDialog
            self.close()

    def clear_history(self):
        # Clear the history file (history.json)
        history_filename = os.path.join("_internal","history.json")
        try:
            with open(history_filename, "w") as history_file:
                history_file.write("[]")  # Write an empty list to clear the history

            # Update the displayed history in the QTextBrowser
            self.history_browser.setHtml("<ul></ul>")
        except Exception as e:
            print(f"Error clearing history: {e}")
        self.close()

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_current_tab)
        self.setCentralWidget(self.tab_widget)

        self.tab_widget.setStyleSheet(open(os.path.join("styles", "tab_wiget.css")).read())

        qtoolbar = QToolBar("Nav")
        qtoolbar.setIconSize(QSize(30, 30))
        qtoolbar.setAllowedAreas(Qt.TopToolBarArea)
        qtoolbar.setFloatable(False)
        qtoolbar.setMovable(False)
        self.addToolBar(qtoolbar)

        qtoolbar.setStyleSheet(open(os.path.join("styles", "toolbar.css")).read())

        back_btn = QAction(QIcon(os.path.join("_internal","images", "back.png")), "Назад", self)
        back_btn.setStatusTip("Вернуться на предыдущую страницу")
        back_btn.triggered.connect(lambda: self.tab_widget.currentWidget().back())
        qtoolbar.addAction(back_btn)

        next_btn = QAction(QIcon(os.path.join("_internal","images", "forward.png")), "Вперёд", self)
        next_btn.setStatusTip("Перейти на страницу вперёд")
        next_btn.triggered.connect(lambda: self.tab_widget.currentWidget().forward())
        qtoolbar.addAction(next_btn)

        reload_btn = QAction(QIcon(os.path.join("_internal","images", "reload.png")), "Обновить страницу", self)
        reload_btn.setStatusTip("Перезагрузить страницу")
        reload_btn.triggered.connect(lambda: self.tab_widget.currentWidget().reload())
        qtoolbar.addAction(reload_btn)

        home_btn = QAction(QIcon(os.path.join("_internal","images", "home.png")), "Домой", self)
        home_btn.setStatusTip("Домой")
        home_btn.triggered.connect(lambda: self.nav_home())
        qtoolbar.addAction(home_btn)

        qtoolbar.addSeparator()

        self.https_icon = QLabel()
        self.https_icon.setPixmap(QPixmap(os.path.join("_internal","images", "lock.png")))
        qtoolbar.addWidget(self.https_icon)

        self.url_line = QLineEdit()
        self.url_line.returnPressed.connect(self.nav_to_url)
        qtoolbar.addWidget(self.url_line)

        new_tab_btn = QAction(QIcon(os.path.join("_internal","images", "add-icon.png")), "Новая вкладка", self)
        new_tab_btn.setStatusTip("Открыть новую вкладку")
        new_tab_btn.triggered.connect(lambda: self.add_new_tab())
        qtoolbar.addAction(new_tab_btn)

        info_btn = QAction(QIcon(os.path.join("_internal","images", "info.png")), "Информация", self)
        info_btn.triggered.connect(self.info)
        qtoolbar.addAction(info_btn)

        self.url_line.setStyleSheet(open(os.path.join("styles", "url_line.css")).read())

        history_btn = QAction(QIcon(os.path.join("_internal","images", "history.png")), "История", self)
        history_btn.triggered.connect(self.show_history)
        qtoolbar.addAction(history_btn)

        # Connect the downloadRequested signal when a new tab is created
        self.tab_widget.currentChanged.connect(self.connect_download_signal)

        # Add a QTimer instance
        self.history_timer = QTimer(self)
        self.history_timer.setSingleShot(True)
        self.history_timer.timeout.connect(self.append_history_delayed)

        self.add_new_tab(QUrl("https://google.com"), "Домашняя страница")

        self.shortcut = QShortcut(QKeySequence("F5"), self)
        self.shortcut.activated.connect(lambda: self.tab_widget.currentWidget().reload())

        self.show()
        self.setWindowIcon(QIcon(os.path.join("_internal","images", "browser_.png")))

        self.load_tabs_from_file()

        self.closeEvent = self.save_tabs_before_close

    def add_new_tab(self, qurl=QUrl("https://google.com"), label="blank"):
        # Создаем новый профиль и страницу для каждой вкладки
        profile = QWebEngineProfile(self)
        webpage = QWebEnginePage(profile, self)
        
        # Создаем новый виджет QWebEngineView с использованием созданного профиля и страницы
        browser = QWebEngineView()
        browser.setPage(webpage)  # Устанавливаем созданную страницу в виджет
        
        browser.settings().setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        browser.settings().setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        browser.page().fullScreenRequested.connect(lambda request: request.accept())
        
        # Загружаем указанный URL
        browser.setUrl(qurl)

        # Добавляем новую вкладку с виджетом в QTabWidget
        tab = self.tab_widget.addTab(browser, label)
        self.tab_widget.setCurrentIndex(tab)

        # Подключаем сигналы изменения URL и завершения загрузки страницы
        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_urlbar(qurl, browser))
        browser.loadFinished.connect(lambda _, i=tab, browser=browser:
                                    self.tab_widget.setTabText(tab, browser.page().title()))

    def tab_open_doubleclick(self, i):
        if i == -1:
            self.add_new_tab()

    def current_tab_changed(self, i):
        qurl = self.tab_widget.currentWidget().url()
        self.update_urlbar(qurl, self.tab_widget.currentWidget())
        self.update_title(self.tab_widget.currentWidget())

    def close_current_tab(self, i):
        if self.tab_widget.count() < 2:
            return

        self.tab_widget.removeTab(i)

    def update_title(self, browser):
        if browser != self.tab_widget.currentWidget():
            return
        title = self.tab_widget.current().page().title()
        self.setWindowTitle(f"{title} - Browser")

    def info(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec_()

    def nav_home(self):
        self.tab_widget.currentWidget().setUrl(QUrl("https://google.com"))

    def nav_to_url(self):
        qurl = QUrl(self.url_line.text())
        if qurl.scheme() == "":
            qurl.setScheme("http")

        self.tab_widget.currentWidget().setUrl(qurl)

    def update_urlbar(self, url, browser=None):
        if browser != self.tab_widget.currentWidget():
            return

        current_url = self.url_line.text()

        if current_url != url.toString():
            if url.scheme() == "https":
                self.https_icon.setPixmap(QPixmap(os.path.join("_internal","images", "lock.png")))
            else:
                self.https_icon.setPixmap(QPixmap(os.path.join("_internal","images", "unlock.png")))

            self.url_line.setText(url.toString())
            self.url_line.setCursorPosition(999)

            # Start the QTimer to delay the history update by 5 seconds
            self.history_timer.start(1500)

    def load_tabs_from_file(self):
        filename = os.path.join("_internal","saved_tabs.json")

        # Check if the file exists before attempting to load tabs
        if os.path.exists(filename):
            try:
                with open(filename, "r") as json_file:
                    tabs_info = json.load(json_file)

                    # Check if there is at least one tab in the file
                    if tabs_info and isinstance(tabs_info, list) and any(tabs_info):
                        # Clear existing tabs before loading from the file
                        self.tab_widget.clear()

                        # Iterate through the saved tabs and add them to the browser
                        for tab_info in tabs_info:
                            url = tab_info.get("url")
                            title = tab_info.get("title", "Untitled")
                            self.add_new_tab(QUrl(url), title)
                    else:
                        pass

            except Exception as e:
                # Handle exceptions, e.g., if there's an issue reading the file
                print(f"Error loading tabs from file: {e}")
        else:
            pass

    def save_tabs_before_close(self, event):
        # Create a dictionary to store information about open tabs
        tabs_info = []

        # Iterate through each tab and gather necessary information
        for index in range(self.tab_widget.count()):
            browser = self.tab_widget.widget(index)
            url = browser.url().toString()
            title = self.tab_widget.tabText(index)
            tabs_info.append({"url": url, "title": title})

        # Save the information to a JSON file
        filename = os.path.join("_internal","saved_tabs.json")
        with open(filename, "w") as json_file:
            json.dump(tabs_info, json_file, indent=2)

        # Call the default closeEvent to close the application
        event.accept()

    def show_history(self):
        # Load history data
        history_filename = os.path.join("_internal","history.json")
        if os.path.exists(history_filename):
            with open(history_filename, "r") as history_file:
                history_data = json.load(history_file)
        else:
            history_data = []

        # Open the history dialog and pass the history data and the main browser instance
        history_dialog = HistoryDialog(history_data, self)
        history_dialog.exec_()

    def append_to_history(self, url, title):
        history_filename = os.path.join("_internal","history.json")

        try:
            # Load existing history if available
            if os.path.exists(history_filename):
                with open(history_filename, "r") as history_file:
                    history_data = json.load(history_file)
            else:
                history_data = []

            # Append the new entry to the history data
            history_data.append({"url": url, "title": title, "timestamp": QDateTime.currentDateTime().toString()})

            # Save the updated history data to the file
            with open(history_filename, "w") as history_file:
                json.dump(history_data, history_file, indent=2)

        except Exception as e:
            print(f"Error updating history: {e}")

    def append_history_delayed(self):
        # This method will be called after the QTimer times out (after 5 seconds)
        url = self.tab_widget.currentWidget().url().toString()
        title = self.tab_widget.currentWidget().page().title()
        self.append_to_history(url, title)

    def download_current_page(self):
        # Получаем текущий виджет вкладки
        current_tab_widget = self.tab_widget.currentWidget()

        # Создаем объект загрузки
        download = current_tab_widget.page().profile().download(current_tab_widget.page().url())

        # Подключаем сигнал завершения загрузки к методу on_download_finished
        download.finished.connect(self.on_download_finished)

    def download_requested(self, download):
        # Открываем диалог выбора директории для сохранения файла
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        # Извлекаем предложенное имя файла из элемента загрузки
        suggested_file_name = download.suggestedFileName()

        # Устанавливаем директорию по умолчанию в "Downloads"
        default_directory = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", default_directory + '/' + suggested_file_name, "All Files (*);;Text Files (*.txt)", options=options)

        if file_path:
            # Устанавливаем местоположение загрузки
            download.setPath(file_path)

            # Принимаем загрузку
            download.accept()

            # Подключаем сигнал завершения к пользовательскому слоту
            download.finished.connect(self.on_download_finished)

    def on_download_finished(self):
        # Обработка завершения загрузки, например, вывод сообщения
        print("Download completed.")

    def connect_download_signal(self, index):
        # Disconnect the previous connection, if any
        current_widget = self.tab_widget.currentWidget()
        if current_widget is not None:
            try:
                download_signal = current_widget.page().profile().downloadRequested
                if download_signal.count() > 0:
                    download_signal.disconnect()
            except AttributeError:
                pass

        # Connect the downloadRequested signal to the download_requested method
        if index != -1:  # Ensure that there is a valid index
            current_widget = self.tab_widget.widget(index)
            if isinstance(current_widget, QWebEngineView) and current_widget.page() is not None:
                current_widget.page().profile().downloadRequested.connect(self.download_requested)

if __name__ == '__main__':
    app = QApplication([])
    QApplication.setApplicationName("Browser")
    app.setOrganizationName("""
                            School 1573, Alexey Panov 10A (IT),\n
                            School 1573, Maksim Lobinsev 10I (IT).
                            """)
    window = Browser()
    window.showMaximized()
    app.exec_()