from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QDialog,
                               QDateTimeEdit, QSpinBox, QGroupBox,
                               QTextEdit, QTableWidget, QAbstractScrollArea,
                               QComboBox, QTableWidgetItem, QCheckBox,
                               QHeaderView, QAbstractItemView)

from PySide6.QtCore import Qt, QThread, Slot, Signal, QDateTime
from PySide6.QtGui import QPixmap, QKeySequence, QShortcut
from typing import Dict, List, Union
from database.utils import get_public_names


class LabeledSetting(QWidget):

    def __init__(self, text: str, setting: QWidget):
        super().__init__()
        self.changed = False
        self.init_ui(text, setting)

    def init_ui(self, text, setting) -> None:
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.label = QLabel(text)
        self.setting = setting()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.setting)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def connect_changed_slots(self) -> None:
        if isinstance(self.setting, QDateTimeEdit):
            return self.setting.dateTimeChanged.connect(self.connect_changed)
        elif isinstance(self.setting, QSpinBox):
            return self.setting.valueChanged.connect(self.connect_changed)
        elif isinstance(self.setting, QTextEdit):
            return self.setting.textChanged.connect(self.connect_changed)
        else:
            return self.setting.changed.connect(self.connect_changed)

    def get_filters(self) -> Union[str, int]:
        if not self.changed:
            return
        if isinstance(self.setting, QDateTimeEdit):
            return self.setting.dateTime().toPython()
        elif isinstance(self.setting, QSpinBox):
            return self.setting.value()
        elif isinstance(self.setting, QTextEdit):
            return self.setting.toPlainText()
        else:
            return self.setting.text()

    @Slot()
    def connect_changed(self) -> None:
        self.changed = True


class PublicTable(QWidget):

    def __init__(self, publics):
        super().__init__()
        self.publics = publics

        # Qt widgets
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.table = QTableWidget()
        layout.addWidget(self.table)
        buttonLayout = QHBoxLayout()
        self.addButton = QPushButton('Add', self)
        self.deleteButton = QPushButton('Delete', self)
        buttonLayout.addWidget(self.addButton)
        buttonLayout.addWidget(self.deleteButton)
        layout.addLayout(buttonLayout)
        layout.addStretch()
        self.setLayout(layout)

        # Table column count
        self.table.setColumnCount(2)
        # Adding and filling rows
        self.set_rows()
        # Disabling row numbers
        self.table.verticalHeader().setVisible(False)
        # Setting column names
        self.table.setHorizontalHeaderLabels(['Public', ''])
        # Resizing to contents, stretching first column
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        # Disabling focus
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)

    def set_rows(self) -> None:
        for row, public in enumerate(self.publics):
            # Adding new row
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Setting item with public's domain name
            item = QTableWidgetItem(public)
            item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 0, item)

            # Setting include/exclude checkbox
            cellWidget = QWidget()
            layout = QHBoxLayout()
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            checkBox = QCheckBox()
            checkBox.setCheckState(Qt.Checked)
            layout.addWidget(checkBox)
            cellWidget.setLayout(layout)
            self.table.setCellWidget(row, 1, cellWidget)

    def get_filters(self) -> List[str]:
        checks = [
            self.table.cellWidget(i, 1) \
                      .layout() \
                      .itemAt(0) \
                      .widget() \
                      .isChecked()
            for i in range(self.table.rowCount())
        ]
        publics = [self.table.item(i, 0).text() for i in range(self.table.rowCount())]
        return list(map(lambda x: x[0], filter(lambda x: x[1], zip(publics, checks))))


class MixingSettings(QDialog):

    changed_params = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.publics = get_public_names()
        self.init_ui()
        self.finished.connect(self.emit_params)

    def init_ui(self) -> None:
        self.setWindowTitle('Change settings')
        self.setWindowModality(Qt.ApplicationModal)
        mainLayout = QVBoxLayout()

        publicsGroupBox = QGroupBox('Publics')
        publicsLayout = QHBoxLayout()
        self.publicsWidget = PublicTable(self.publics)
        self.publicsWidget.table.setMinimumSize(100, 200)
        publicsLayout.addWidget(self.publicsWidget)
        publicsGroupBox.setLayout(publicsLayout)
        mainLayout.addWidget(publicsGroupBox)

        cropsGroupBox = QGroupBox('Crops')
        cropsMainLayout = QVBoxLayout()
        cropsLayout = QHBoxLayout()
        self.cropsFrom = LabeledSetting('Minimum number', QSpinBox)
        self.cropsUntil = LabeledSetting('Maximum number', QSpinBox)
        cropsLayout.addWidget(self.cropsFrom)
        cropsLayout.addWidget(self.cropsUntil)
        cropsMainLayout.addLayout(cropsLayout)
        cropsLayout = QHBoxLayout()
        self.cropsTextInclude = LabeledSetting('Include text', QTextEdit)
        self.cropsTextExclude = LabeledSetting('Exclude text', QTextEdit)
        cropsLayout.addWidget(self.cropsTextInclude)
        cropsLayout.addWidget(self.cropsTextExclude)
        cropsMainLayout.addLayout(cropsLayout)
        cropsGroupBox.setLayout(cropsMainLayout)
        mainLayout.addWidget(cropsGroupBox)

        postsGroupBox = QGroupBox('Pictures')
        postsLayout = QHBoxLayout()
        self.postsFrom = LabeledSetting('Minimum number', QSpinBox)
        self.postsUntil = LabeledSetting('Maximum number', QSpinBox)
        postsLayout.addWidget(self.postsFrom)
        postsLayout.addWidget(self.postsUntil)
        postsGroupBox.setLayout(postsLayout)
        mainLayout.addWidget(postsGroupBox)

        dateGroupBox = QGroupBox('Date')
        dateLayout = QHBoxLayout()
        self.dateFrom = LabeledSetting('From', QDateTimeEdit)
        self.dateUntil = LabeledSetting('Until', QDateTimeEdit)
        dateLayout.addWidget(self.dateFrom)
        dateLayout.addWidget(self.dateUntil)
        dateGroupBox.setLayout(dateLayout)
        mainLayout.addWidget(dateGroupBox)

        self.setLayout(mainLayout)

    @Slot()
    def emit_params(self) -> None:
        from_publics = self.publicsWidget.get_filters()
        params = {
            'from_publics': from_publics,
            'exclude_publics': list(set(self.publics) - set(from_publics)),
            'from_date': self.dateFrom.get_filters(),
            'to_date': self.dateUntil.get_filters(),
            'include_text': self.cropsTextInclude.get_filters(),
            'exclude_text': self.cropsTextExclude.get_filters(),
            'min_pics': self.postsFrom.get_filters(),
            'max_pics': self.postsUntil.get_filters(),
            'min_crops': self.cropsFrom.get_filters(),
            'max_crops': self.cropsUntil.get_filters()
        }
        print(params)
        self.changed_params.emit(params)
