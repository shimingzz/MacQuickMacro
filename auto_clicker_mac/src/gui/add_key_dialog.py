import time
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QDoubleValidator
from pynput import keyboard as pynput_keyboard


class AddKeyDialog(QDialog):
    # Signal to emit the captured key data: (display_name, actual_key_for_pynput, interval)
    key_setting_accepted = Signal(str, object, float)

    # Signal to pass key captured by pynput listener back to the main Qt thread
    _qt_key_captured_signal = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新增按鍵設定")
        self.setMinimumWidth(350)
        self.setModal(True) # Block parent window

        self.captured_key_value = None # Renamed from self.captured_key to avoid potential QObject name clash
        self.key_display_name = ""
        self.pynput_listener = None # To store the pynput listener instance

        self.layout = QVBoxLayout(self)
        self._qt_key_captured_signal.connect(self._on_key_captured_from_signal) # Connect internal signal

        # Key capture section
        key_capture_layout = QHBoxLayout()
        self.capture_status_label = QLabel("按鍵: 尚未設定")
        self.capture_status_label.setStyleSheet("min-width: 150px;") # Give it some space
        self.capture_button = QPushButton("點此設定按鍵")
        self.capture_button.clicked.connect(self._start_key_capture)
        self.original_capture_button_text = self.capture_button.text()
        key_capture_layout.addWidget(self.capture_status_label, 1)
        key_capture_layout.addWidget(self.capture_button)
        self.layout.addLayout(key_capture_layout)

        # Interval section
        interval_layout = QHBoxLayout()
        interval_label = QLabel("重複間隔 (秒):")
        self.interval_input = QLineEdit("0.5")
        self.interval_input.setPlaceholderText("例如: 0.1, 1, 2.5")
        # Validator for float numbers (e.g., 0.001 to 999.999)
        # Adjust precision and range as needed
        double_validator = QDoubleValidator(0.001, 999.999, 3, self)
        double_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.interval_input.setValidator(double_validator)
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_input)
        self.layout.addLayout(interval_layout)

        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject) # self.reject calls done() implicitly
        self.layout.addWidget(self.button_box)

    def _pynput_on_press(self, key):
        """This method is called by the pynput listener in its own thread."""
        print(f"[AddKeyDialog_pynput_callback] Key pressed: {key}")
        try:
            # Stop the listener IMMEDIATELY in its own thread to prevent multiple captures.
            # This is safer than trying to stop it from the Qt thread after a signal.
            if self.pynput_listener:
                self.pynput_listener.stop() # Stop the listener

            # Emit a Qt signal to pass the key to the Qt main thread for processing.
            self._qt_key_captured_signal.emit(key)
        except Exception as e:
            print(f"[AddKeyDialog_pynput_callback] Error: {e}")
            self._qt_key_captured_signal.emit(None) # Emit None on error
        return False # Returning False also asks the listener to stop.

    def _start_key_capture(self):
        print("[AddKeyDialog] _start_key_capture called")
        self.capture_status_label.setText("請按下一個按鍵...")
        self.capture_button.setText("設定中...請按鍵")
        self.capture_button.setEnabled(False)
        self.captured_key_value = None # Reset
        self.key_display_name = ""

        if self.pynput_listener: # Should not happen if logic is correct
            print("[AddKeyDialog] Warning: Existing pynput_listener found. Stopping it.")
            self.pynput_listener.stop()
            self.pynput_listener = None

        try:
            print("[AddKeyDialog] Creating pynput.Listener instance.")
            self.pynput_listener = pynput_keyboard.Listener(on_press=self._pynput_on_press)
            self.pynput_listener.start() # Starts the listener in a new thread (managed by pynput)
            print("[AddKeyDialog] pynput.Listener started.")
        except Exception as e:
            print(f"[AddKeyDialog] Failed to start pynput.Listener: {type(e).__name__}: {e}")
            QMessageBox.warning(self, "監聽器錯誤", f"無法啟動按鍵監聽器: {e}\n請檢查權限設定。")
            self.capture_status_label.setText("錯誤: 無法啟動監聽")
            self.capture_button.setText(self.original_capture_button_text)
            self.capture_button.setEnabled(True)
            if self.pynput_listener:
                self.pynput_listener.stop()
                self.pynput_listener = None


    @Slot(object)
    def _on_key_captured_from_signal(self, key_obj):
        """This slot is executed in the Qt main thread."""
        print(f"[AddKeyDialog_qt_slot] _on_key_captured_from_signal received: {key_obj}")

        # Reset button state regardless of outcome
        self.capture_button.setText(self.original_capture_button_text)
        self.capture_button.setEnabled(True)

        if key_obj is None:
            self.capture_status_label.setText("錯誤: 無法擷取按鍵")
            # QMessageBox.warning(self, "按鍵擷取失敗", "無法擷取按鍵。") # Already shown or implied by listener error
            return

        self.captured_key_value = key_obj
        try:
            if isinstance(self.captured_key_value, pynput_keyboard.KeyCode):
                self.key_display_name = self.captured_key_value.char
            elif isinstance(self.captured_key_value, pynput_keyboard.Key):
                self.key_display_name = str(self.captured_key_value.name)
            else:
                self.key_display_name = str(self.captured_key_value) # Fallback

            if self.key_display_name is None: # e.g. for some dead keys or unmapped chars
                self.key_display_name = f"特殊鍵代碼: {self.captured_key_value.vk}" if hasattr(self.captured_key_value, 'vk') else "未知按鍵"


        except AttributeError:
            self.key_display_name = str(self.captured_key_value).replace("Key.", "")

        if self.key_display_name:
             self.capture_status_label.setText(f"已擷取: <b>{self.key_display_name}</b>")
        else:
             self.capture_status_label.setText(f"已擷取: <b>特殊鍵</b> (代碼: {self.captured_key_value})")

        # The pynput listener should have already stopped itself.
        # We can nullify our reference to it.
        if self.pynput_listener:
            # self.pynput_listener.stop() # Should already be stopped by the callback
            self.pynput_listener = None
            print("[AddKeyDialog_qt_slot] pynput_listener reference cleared.")


    def _on_accept(self):
        print("[AddKeyDialog] _on_accept called")
        if not self.captured_key_value:
            QMessageBox.warning(self, "錯誤", "請先設定一個按鍵。")
            return

        interval_str = self.interval_input.text().strip()
        try:
            interval = float(interval_str)
            if interval <= 0:
                raise ValueError("間隔必須是正數")
        except ValueError:
            QMessageBox.warning(self, "錯誤", f"無效的間隔時間: '{interval_str}'。\n請輸入一個正數 (例如 0.5)。")
            return

        # self.captured_key_value is already the correct object for pynput (char or Key object)
        # self.key_display_name is for display

        # Emit: display_name, the actual key object for pynput, interval
        print(f"[AddKeyDialog] Emitting key_setting_accepted: name='{self.key_display_name}', key='{self.captured_key_value}', interval={interval}")
        self.key_setting_accepted.emit(self.key_display_name, self.captured_key_value, interval)
        self.accept() # Close the dialog, which will also call done()

    def done(self, result):
        # This method is called when the dialog is closed, accepted, or rejected.
        print(f"[AddKeyDialog] done() called with result: {result}")
        if self.pynput_listener:
            print("[AddKeyDialog] Dialog closing, ensuring pynput_listener is stopped.")
            self.pynput_listener.stop() # Request pynput listener to stop
            # No need to join pynput listener here, it manages its own thread.
            # Stopping it should be enough to prevent further callbacks.
            self.pynput_listener = None
            print("[AddKeyDialog] pynput_listener reference cleared in done().")
        super().done(result)

    # Allow dialog to be closed with Escape key (default behavior for QDialog usually)
    # def keyPressEvent(self, event):
    #     if event.key() == Qt.Key.Key_Escape:
    #         self.reject()
    #     else:
    #         super().keyPressEvent(event)

if __name__ == '__main__':
    # This is for testing the dialog independently
    # Remember macOS Accessibility permissions for pynput to capture keys!
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    dialog = AddKeyDialog()

    # Connect to the signal for testing
    def handle_key_setting(display, key_obj, interval_val):
        print(f"Dialog accepted: Display='{display}', KeyObj='{key_obj}' (Type: {type(key_obj)}), Interval='{interval_val}'")

    dialog.key_setting_accepted.connect(handle_key_setting)

    if dialog.exec():
        print("Dialog accepted by user.")
    else:
        print("Dialog cancelled by user.")
    sys.exit()
