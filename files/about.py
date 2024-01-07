import os
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtCore import Qt, QUrl, QStandardPaths
from PyQt5.QtWidgets import QApplication, QDialogButtonBox, QDialog, QVBoxLayout, QLabel


class AboutDialog(QDialog):
    def __init__(self, parent=None, *args, **kwargs):
        super(AboutDialog, self).__init__(*args, **kwargs)

        self.layout = QVBoxLayout()

        ok_btn = QDialogButtonBox.Ok
        self.button_box = QDialogButtonBox(ok_btn)

        self.init_ui()

    def init_ui(self):
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        with open(os.path.join("styles", "about_style.css")) as f:
            self.button_box.button(QDialogButtonBox.Ok).setStyleSheet(f.read())

        logo = QLabel()
        pixmap = QPixmap(os.path.join("_internal", "images", "browser_.png"))
        pixmap = pixmap.scaled(80, 80)
        logo.setPixmap(pixmap)
        self.layout.addWidget(logo)

        title = QLabel("Browser")
        title.setFont(QFont("Times", 20))
        self.layout.addWidget(title)

        lbl1 = QLabel(
        '<center><a href="https://github.com/S4CBS/simple_browser" style="text-decoration: none; color: #0000FF;">Version 1.5<br>Created by Alexey Panov, Maksim Lobinsev.</a></center>'
        )
        lbl1.setFont(QFont("Times", 10))
        lbl1.setOpenExternalLinks(True)  # Открывать ссылки во внешнем браузере
        lbl1.linkActivated.connect(self.open_github_link)  # Подключение к событию активации ссылки
        self.layout.addWidget(lbl1)

        self.layout.addWidget(self.button_box)

        for i in range(0, self.layout.count()):
            self.layout.itemAt(i).setAlignment(Qt.AlignHCenter)

        self.setLayout(self.layout)

        self.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint)
        self.resize(400, 250)
        self.setMaximumHeight(300)
        self.setMaximumWidth(500)
        self.setWindowTitle("About")

        self.setWindowIcon(QIcon(os.path.join("_internal", "images", "browser_.png")))

    def open_github_link(self, link):
        # Открываем ссылку во внешнем браузере
        QStandardPaths.openUrl(QUrl(link))

# Пример использования
if __name__ == '__main__':
    app = QApplication([])
    window = AboutDialog()
    window.exec_()
