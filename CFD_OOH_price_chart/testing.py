#%%

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
import sys
app = QApplication(sys.argv)
w = QWidget()
layout = QVBoxLayout(w)
hbox = QHBoxLayout()
layout.addLayout(hbox)

print(layout.count())
print(hbox.count())