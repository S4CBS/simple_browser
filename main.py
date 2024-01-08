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

        self.setWindowTitle("История")
        self.setGeometry(100, 100, 600, 400)

        # Установка иконки окна
        icon_path = os.path.join("_internal", "images", "browser_.png")
        self.setWindowIcon(QIcon(icon_path))

        # Сохранение ссылки на основной браузер
        self.main_browser = main_browser

        # Создание QVBoxLayout для диалогового окна
        layout = QVBoxLayout()

        # Создание QTextBrowser для отображения текста истории с кликабельными ссылками
        self.history_browser = QTextBrowser()
        self.history_browser.setOpenExternalLinks(False)  # Отключение внешних ссылок для их обработки вручную
        self.history_browser.setHtml(self.format_history_html(history_data))

        # Подключение сигнала anchorClicked к слоту для обработки кликов по ссылкам
        self.history_browser.anchorClicked.connect(self.handle_link_clicked)

        # Установка стилей из файла CSS
        self.setStyleSheet(open(os.path.join('styles', 'history_dialog_style.css')).read())

        # Создание области прокрутки для содержимого истории
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.history_browser)

        # Добавление области прокрутки в макет
        layout.addWidget(scroll_area)

        # Добавление кнопки для очистки истории
        clear_button = QPushButton("Очистить историю")
        clear_button.clicked.connect(self.clear_history)
        layout.addWidget(clear_button)

        # Установка макета для диалогового окна
        self.setLayout(layout)

    def format_history_html(self, history_data):
        # Форматирование данных истории в HTML-контент
        html_content = "<ul>"
        for entry in history_data:
            title = entry.get("title", "Без названия")
            url = entry.get("url", "")
            timestamp = entry.get("timestamp", "")
            html_content += f"<li><div><strong>{title}</strong></div><div><a href='{url}'>{url}</a></div><div>{timestamp}</div></li>"
        html_content += "</ul>"
        return html_content

    def handle_link_clicked(self, link):
        # Открытие кликнутой ссылки в основном браузере
        url = link.toString()

        # Проверка, что URL не начинается с 'javascript:void(0);'
        if not url.startswith("javascript:"):
            # Открытие URL в основном браузере
            self.main_browser.tab_widget.currentWidget().setUrl(QUrl(url))

            # Закрытие диалогового окна истории
            self.close()

    def clear_history(self):
        # Очистка файла истории (history.json)
        history_filename = os.path.join("_internal", "history.json")
        try:
            with open(history_filename, "w") as history_file:
                history_file.write("[]")  # Запись пустого списка для очистки истории

            # Обновление отображаемой истории в QTextBrowser
            self.history_browser.setHtml("<ul></ul>")
        except Exception as e:
            print(f"Ошибка при очистке истории: {e}")
        self.close()


# Определение класса Browser, который является основным окном браузера
class Browser(QMainWindow):
    def __init__(self):
        super().__init__()

        # Создание виджета вкладок и настройка его параметров
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_current_tab)
        self.setCentralWidget(self.tab_widget)

        # Установка стилей для виджета вкладок
        self.tab_widget.setStyleSheet(open(os.path.join("styles", "tab_wiget.css")).read())

        # Создание и настройка панели инструментов
        qtoolbar = QToolBar("Навигация")
        qtoolbar.setIconSize(QSize(30, 30))
        qtoolbar.setAllowedAreas(Qt.TopToolBarArea)
        qtoolbar.setFloatable(False)
        qtoolbar.setMovable(False)
        self.addToolBar(qtoolbar)

        # Установка стилей для панели инструментов
        qtoolbar.setStyleSheet(open(os.path.join("styles", "toolbar.css")).read())

        # Добавление кнопок навигации на панель инструментов
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

        # Иконка для отображения протокола HTTPS
        self.https_icon = QLabel()
        self.https_icon.setPixmap(QPixmap(os.path.join("_internal","images", "lock.png")))
        qtoolbar.addWidget(self.https_icon)

        # Строка ввода URL
        self.url_line = QLineEdit()
        self.url_line.returnPressed.connect(self.nav_to_url)
        qtoolbar.addWidget(self.url_line)

        # Кнопка для открытия новой вкладки
        new_tab_btn = QAction(QIcon(os.path.join("_internal","images", "add-icon.png")), "Новая вкладка", self)
        new_tab_btn.setStatusTip("Открыть новую вкладку")
        new_tab_btn.triggered.connect(lambda: self.add_new_tab())
        qtoolbar.addAction(new_tab_btn)

        # Кнопка для отображения информации
        info_btn = QAction(QIcon(os.path.join("_internal","images", "info.png")), "Информация", self)
        info_btn.triggered.connect(self.info)
        qtoolbar.addAction(info_btn)

        # Настройка стилей для строки ввода URL
        self.url_line.setStyleSheet(open(os.path.join("styles", "url_line.css")).read())

        # Кнопка для открытия истории
        history_btn = QAction(QIcon(os.path.join("_internal","images", "history.png")), "История", self)
        history_btn.triggered.connect(self.show_history)
        qtoolbar.addAction(history_btn)

        # Подключение сигнала downloadRequested при создании новой вкладки
        self.tab_widget.currentChanged.connect(self.connect_download_signal)

        # Создание экземпляра QTimer
        self.history_timer = QTimer(self)
        self.history_timer.setSingleShot(True)
        self.history_timer.timeout.connect(self.append_history_delayed)

        # Открытие новой вкладки с домашней страницей Google при запуске
        self.add_new_tab(QUrl("https://google.com"), "Домашняя страница")

        # Настройка горячей клавиши F5 для обновления страницы
        self.shortcut = QShortcut(QKeySequence("F5"), self)
        self.shortcut.activated.connect(lambda: self.tab_widget.currentWidget().reload())

        # Отображение окна
        self.show()
        self.setWindowIcon(QIcon(os.path.join("_internal","images", "browser_.png")))

        # Загрузка сохранённых вкладок при запуске
        self.load_tabs_from_file()

        # Установка обработчика события закрытия окна
        self.closeEvent = self.save_tabs_before_close

    # Метод для добавления новой вкладки
    def add_new_tab(self, qurl=QUrl("https://google.com"), label="Пусто"):
        # Создание нового профиля и страницы для каждой вкладки
        profile = QWebEngineProfile(self)
        webpage = QWebEnginePage(profile, self)

        # Создание нового виджета QWebEngineView с использованием созданного профиля и страницы
        browser = QWebEngineView()
        browser.setPage(webpage)  # Установка созданной страницы в виджет

        # Настройка параметров прокрутки и полноэкранного режима
        browser.settings().setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        browser.settings().setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        browser.page().fullScreenRequested.connect(lambda request: request.accept())

        # Загрузка указанного URL
        browser.setUrl(qurl)

        # Добавление новой вкладки с виджетом в QTabWidget
        tab = self.tab_widget.addTab(browser, label)
        self.tab_widget.setCurrentIndex(tab)

        # Подключение сигналов изменения URL и завершения загрузки страницы
        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_urlbar(qurl, browser))
        browser.loadFinished.connect(lambda _, i=tab, browser=browser:
                                      self.tab_widget.setTabText(tab, browser.page().title()))

    # Метод для обработки двойного щелчка на вкладке
    def tab_open_doubleclick(self, i):
        if i == -1:
            self.add_new_tab()

    # Метод для изменения текущей вкладки
    def current_tab_changed(self, i):
        qurl = self.tab_widget.currentWidget().url()
        self.update_urlbar(qurl, self.tab_widget.currentWidget())
        self.update_title(self.tab_widget.currentWidget())

    # Метод для закрытия текущей вкладки
    def close_current_tab(self, i):
        if self.tab_widget.count() < 2:
            return

        self.tab_widget.removeTab(i)

    # Метод для обновления заголовка окна
    def update_title(self, browser):
        if browser != self.tab_widget.currentWidget():
            return
        title = self.tab_widget.current().page().title()
        self.setWindowTitle(f"{title} - Browser")

    # Метод для отображения диалога с информацией о браузере
    def info(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec_()

    # Метод для перехода на домашнюю страницу (Google)
    def nav_home(self):
        self.tab_widget.currentWidget().setUrl(QUrl("https://google.com"))

    # Метод для перехода по введённому URL
    def nav_to_url(self):
        qurl = QUrl(self.url_line.text())
        if qurl.scheme() == "":
            qurl.setScheme("http")

        self.tab_widget.currentWidget().setUrl(qurl)

    # Метод для обновления строки URL и отображения иконки протокола HTTPS
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

            # Запуск таймера для отложенного обновления истории через 5 секунд
            self.history_timer.start(5000)

    # Метод для загрузки сохранённых вкладок из файла
    def load_tabs_from_file(self):
        filename = os.path.join("_internal","saved_tabs.json")

        # Проверка наличия файла перед попыткой загрузки вкладок
        if os.path.exists(filename):
            try:
                with open(filename, "r") as json_file:
                    tabs_info = json.load(json_file)

                    # Проверка наличия хотя бы одной вкладки в файле
                    if tabs_info and isinstance(tabs_info, list) and any(tabs_info):
                        # Очистка текущих вкладок перед загрузкой из файла
                        self.tab_widget.clear()

                        # Итерация по сохранённым вкладкам и их добавление в браузер
                        for tab_info in tabs_info:
                            url = tab_info.get("url")
                            title = tab_info.get("title", "Untitled")
                            self.add_new_tab(QUrl(url), title)
                    else:
                        pass

            except Exception as e:
                # Обработка исключений, например, если есть проблемы с чтением файла
                print(f"Ошибка при загрузке вкладок из файла: {e}")
        else:
            pass

    # Метод для сохранения вкладок перед закрытием
    def save_tabs_before_close(self, event):
        # Создание словаря для хранения информации о открытых вкладках
        tabs_info = []

        # Итерация по каждой вкладке и сбор необходимой информации
        for index in range(self.tab_widget.count()):
            browser = self.tab_widget.widget(index)
            url = browser.url().toString()
            title = self.tab_widget.tabText(index)
            tabs_info.append({"url": url, "title": title})

        # Сохранение информации в JSON-файл
        filename = os.path.join("_internal","saved_tabs.json")
        with open(filename, "w") as json_file:
            json.dump(tabs_info, json_file, indent=2)

        # Вызов стандартного события closeEvent для закрытия приложения
        event.accept()

    # Метод для отображения диалога истории
    def show_history(self):
        # Загрузка данных истории
        history_filename = os.path.join("_internal","history.json")
        if os.path.exists(history_filename):
            with open(history_filename, "r") as history_file:
                history_data = json.load(history_file)
        else:
            history_data = []

        # Открытие диалога истории и передача данных истории и экземпляра основного браузера
        history_dialog = HistoryDialog(history_data, self)
        history_dialog.exec_()

    # Метод для добавления записи в историю
    def append_to_history(self, url, title):
        history_filename = os.path.join("_internal","history.json")

        try:
            # Загрузка существующей истории, если она есть
            if os.path.exists(history_filename):
                with open(history_filename, "r") as history_file:
                    history_data = json.load(history_file)
            else:
                history_data = []

            # Добавление новой записи в данные истории
            history_data.append({"url": url, "title": title, "timestamp": QDateTime.currentDateTime().toString()})

            # Сохранение обновленных данных истории в файл
            with open(history_filename, "w") as history_file:
                json.dump(history_data, history_file, indent=2)

        except Exception as e:
            print(f"Ошибка при обновлении истории: {e}")

    # Метод для отложенного добавления записи в историю
    def append_history_delayed(self):
        # Этот метод будет вызван после того, как таймер QTimer истечет (через 5 секунд)
        url = self.tab_widget.currentWidget().url().toString()
        title = self.tab_widget.currentWidget().page().title()
        self.append_to_history(url, title)

    # Метод для загрузки текущей страницы
    def download_current_page(self):
        # Получение текущего виджета вкладки
        current_tab_widget = self.tab_widget.currentWidget()

        # Создание объекта загрузки
        download = current_tab_widget.page().profile().download(current_tab_widget.page().url())
        # Метод для загрузки текущей страницы
    def download_current_page(self):
        # Получаем текущий виджет вкладки
        current_tab_widget = self.tab_widget.currentWidget()

        # Создаем объект загрузки
        download = current_tab_widget.page().profile().download(current_tab_widget.page().url())

        # Подключаем сигнал завершения загрузки к методу on_download_finished
        download.finished.connect(self.on_download_finished)

    # Метод, вызываемый при запросе на загрузку
    def download_requested(self, download):
        # Открываем диалог сохранения файла для выбора пути назначения

        # Извлекаем предложенное имя файла из элемента загрузки
        suggested_file_name = download.suggestedFileName()

        # Устанавливаем каталог по умолчанию в "Загрузки"
        default_directory = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        
        # Используем стандартный диалог сохранения файла
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", default_directory + '/' + suggested_file_name, "Все файлы (*);")

        if file_path:
            # Устанавливаем местоположение загрузки
            download.setPath(file_path)

            # Принимаем загрузку
            download.accept()

            # Подключаем сигнал завершения загрузки к пользовательскому методу
            download.finished.connect(self.on_download_finished)

    # Метод, вызываемый при завершении загрузки
    def on_download_finished(self):
        # Обработка завершения загрузки, например, вывод сообщения
        print("Загрузка завершена.")

    # Метод для подключения сигнала downloadRequested при смене вкладки
    def connect_download_signal(self, index):
        # Отключаем предыдущее соединение, если оно есть
        current_widget = self.tab_widget.currentWidget()
        if current_widget is not None:
            try:
                download_signal = current_widget.page().profile().downloadRequested
                if download_signal.count() > 0:
                    download_signal.disconnect()
            except AttributeError:
                pass

        # Подключаем сигнал downloadRequested к методу download_requested
        if index != -1:  # Убеждаемся, что есть допустимый индекс
            current_widget = self.tab_widget.widget(index)
            if isinstance(current_widget, QWebEngineView) and current_widget.page() is not None:
                current_widget.page().profile().downloadRequested.connect(self.download_requested)

if __name__ == '__main__':
    # Создание экземпляра QApplication
    app = QApplication([])
    QApplication.setApplicationName("Browser")
    app.setOrganizationName("""
                            Школа 1573, Алексей Панов 10А (ИТ),\n
                            Школа 1573, Максим Лобинцев 10И (ИТ).
                            """)
    
    # Создание экземпляра основного окна браузера
    window = Browser()
    window.showMaximized()  # Отображение окна в максимальном размере
    app.exec_()  # Запуск главного цикла приложения

       
