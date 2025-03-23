
import sounddevice as sd
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox,QHBoxLayout

"""
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")

        # Query available input devices
        self.input_devices = [device['name'] for device in sd.query_devices() if device['max_input_channels'] > 0]

        # Main layout
        layout = QVBoxLayout()

        # Input device selection
        layout.addWidget(QLabel("Select Input Device:"))
        self.device_combo = QComboBox()
        self.device_combo.addItems(self.input_devices)
        layout.addWidget(self.device_combo)

        # Buttons for confirmation
        buttons = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        buttons.addWidget(self.ok_button)
        buttons.addWidget(self.cancel_button)

        layout.addLayout(buttons)
        self.setLayout(layout)

        # Connect the buttons
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_selected_device(self):
        return self.device_combo.currentText()
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")

        # Query available input devices
        self.devices = [(device['name'], index) for index, device in enumerate(sd.query_devices()) if device['max_input_channels'] > 0]

        # Main layout
        layout = QVBoxLayout()

        # Input device selection
        layout.addWidget(QLabel("Select Input Device:"))
        self.device_combo = QComboBox()
        self.device_names = [device[0] for device in self.devices]
        self.device_combo.addItems(self.device_names)
        layout.addWidget(self.device_combo)

        # Buttons for confirmation
        buttons = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        buttons.addWidget(self.ok_button)
        buttons.addWidget(self.cancel_button)

        layout.addLayout(buttons)
        self.setLayout(layout)

        # Connect the buttons
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_selected_device_info(self):
        selected_device_name = self.device_combo.currentText()
        # Find the device ID using the selected device name
        selected_device_id = next((device_id for name, device_id in self.devices if name == selected_device_name), None)
        return selected_device_name, selected_device_id
"""
import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QComboBox, QHBoxLayout, QPushButton
import sounddevice as sd

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")

        # Query available input devices; store the complete device info
        self.device_list = [device for device in sd.query_devices() if device['max_input_channels'] > 0]
        self.device_names = [device['name'] for device in self.device_list]

        # Main layout
        layout = QVBoxLayout()

        # Input device selection
        layout.addWidget(QLabel("Select Input Device:"))
        self.device_combo = QComboBox()
        self.device_combo.addItems(self.device_names)
        layout.addWidget(self.device_combo)

        # Buttons for confirmation
        buttons = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        buttons.addWidget(self.ok_button)
        buttons.addWidget(self.cancel_button)

        layout.addLayout(buttons)
        self.setLayout(layout)

        # Connect the buttons
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_selected_device_object(self):
        selected_index = self.device_combo.currentIndex()
        # Return the selected device object from the list
        return self.device_list[selected_index]

def main():
    app = QApplication(sys.argv)
    dialog = SettingsDialog()

    if dialog.exec_() == QDialog.Accepted:
        selected_device_object = dialog.get_selected_device_object()
        print(f"Selected Device Object: {selected_device_object}")

if __name__ == "__main__":
    main()
