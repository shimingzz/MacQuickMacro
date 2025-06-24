import time
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread, Slot
from PySide6.QtGui import QDoubleValidator
from pynput import keyboard as pynput_keyboard # Renamed to avoid conflict

# Listener thread for capturing a single key press
class KeyListenerThread(QThread):
    key_captured = Signal(object) # Can emit either str or pynput.keyboard.Key or None for error

    def __init__(self, parent=None):
        super().__init__(parent)
        self.listener = None
        # self._stop_event = False # No longer explicitly used with 'with' statement logic

    def run(self):
        print("[KeyListenerThread] Thread started")
        try:
            def on_press(key):
                print(f"[KeyListenerThread] Key pressed: {key}")
                # Important: Emit the signal before trying to stop or join,
                # as stopping might terminate the thread context for the signal.
                self.key_captured.emit(key)
                return False # Stops the listener

            # Using 'with' statement for robust listener management
            with pynput_keyboard.Listener(on_press=on_press) as listener_instance:
                self.listener = listener_instance # Assign to self.listener if needed elsewhere, though 'with' manages it
                print("[KeyListenerThread] Listener created and started")
                self.listener.join() # Wait until listener stops (on_press returns False)

            print("[KeyListenerThread] Listener stopped and joined")

        except Exception as e:
            print(f"[KeyListenerThread] EXCEPTION in listener thread: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self.key_captured.emit(None) # Signal an error or no key
        finally:
            # self.listener = None # Listener is already out of scope or stopped
            print("[KeyListenerThread] Thread finished")


    def stop_listener(self): # This might be less critical if 'with' handles cleanup well
        print("[KeyListenerThread] stop_listener called (External request)")
        if self.listener and self.listener.is_alive(): # Check if listener is running
            try:
                print("[KeyListenerThread] Attempting to stop listener via internal stop method...")
                # For pynput, returning False from callback is the primary way to stop.
                # Direct self.listener.stop() can be problematic if called from a different thread
                # than the one running the listener, or if the listener is not fully initialized.
                # If the 'with' statement is used, this external stop might interfere or be redundant.
                # Consider if this method is truly needed or if relying on callback return is sufficient.
                # For now, we can try to call its stop method, but be cautious.
                self.listener.stop() # This can still be problematic.
                print("[KeyListenerThread] Listener explicitly stopped by stop_listener()")
            except Exception as e:
                print(f"[KeyListenerThread] Error stopping listener in stop_listener(): {e}")
        else:
            print("[KeyListenerThread] stop_listener: Listener was None or not alive.")


class AddKeyDialog(QDialog):
    # Signal to emit the captured key data: (display_name, key_code, key_special, interval)
    key_setting_accepted = Signal(str, object, object, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新增按鍵設定")
        self.setMinimumWidth(350)
        self.setModal(True) # Block parent window

        self.captured_key = None
        self.key_display_name = ""

        self.layout = QVBoxLayout(self)

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
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.key_listener_thread = None

    def _start_key_capture(self):
        self.capture_status_label.setText("請按下一個按鍵...")
        self.capture_button.setText("設定中...請按鍵")
        self.capture_button.setEnabled(False)
        self.captured_key = None # Reset
        self.key_display_name = ""

        # Important: Ensure pynput listener runs in a separate thread
        # to avoid freezing the GUI.
        if self.key_listener_thread and self.key_listener_thread.isRunning():
            # Should not happen if button is disabled, but as a safeguard
            print("Listener thread already running.")
            return

        self.key_listener_thread = KeyListenerThread(self)
        self.key_listener_thread.key_captured.connect(self._on_key_captured)
        self.key_listener_thread.finished.connect(self._on_listener_finished) # Clean up
        self.key_listener_thread.start()

    @Slot(object)
    def _on_key_captured(self, key):
        if key is None:
            self.capture_status_label.setText("錯誤: 無法擷取按鍵")
            QMessageBox.warning(self, "按鍵擷取失敗", "無法擷取按鍵，請確保沒有其他程式獨佔鍵盤，或檢查權限。")
            self.capture_button.setEnabled(True)
            return

        self.captured_key = key
        try:
            if isinstance(key, pynput_keyboard.KeyCode):
                self.key_display_name = key.char
            elif isinstance(key, pynput_keyboard.Key):
                self.key_display_name = str(key.name) # e.g., "space", "enter"
            else: # Should not happen with pynput
                self.key_display_name = str(key)
        except AttributeError:
            # For some special keys that might not have a 'char' or 'name' attribute directly
            # This is a fallback, might need more robust handling for all pynput Key types
            self.key_display_name = str(key).replace("Key.", "")


        if self.key_display_name:
             self.capture_status_label.setText(f"已擷取: <b>{self.key_display_name}</b>")
        else:
              # This case should ideally be rare if pynput gives good names/chars
              self.capture_status_label.setText(f"已擷取: <b>特殊鍵</b> (代碼: {self.captured_key})")


        # Listener thread will stop itself and emit finished signal.
        # Button re-enabling and text reset will be handled in _on_listener_finished

    @Slot()
    def _on_listener_finished(self):
        if self.key_listener_thread:
            self.key_listener_thread.deleteLater() # Schedule for deletion
            self.key_listener_thread = None
        self.capture_button.setText(self.original_capture_button_text) # Reset button text
        self.capture_button.setEnabled(True) # Ensure button is re-enabled

    def _on_accept(self):
        if not self.captured_key:
            QMessageBox.warning(self, "錯誤", "請先設定一個按鍵。")
            return

        interval_str = self.interval_input.text()
        try:
            interval = float(interval_str)
            if interval <= 0:
                raise ValueError("間隔必須是正數")
        except ValueError:
            QMessageBox.warning(self, "錯誤", f"無效的間隔時間: '{interval_str}'。\n請輸入一個正數 (例如 0.5)。")
            return

        key_code = None
        key_special = None

        if isinstance(self.captured_key, pynput_keyboard.KeyCode):
            key_code = self.captured_key.char # This might be None for some special keys if not handled well by pynput char mapping
            if key_code is None: # Fallback for things like numpad keys if char is None
                key_code = self.key_display_name # Use display name if char is None
        elif isinstance(self.captured_key, pynput_keyboard.Key):
            key_special = self.captured_key
            # key_code = self.key_display_name # Store a representation for pynput if needed, or rely on key_special

        # Ensure key_code or key_special is available
        if key_code is None and key_special is None:
             QMessageBox.warning(self, "錯誤", "擷取的按鍵資料不完整。")
             return


        # Emit the signal with the captured data
        # The key_code here is what pynput's Controller.press() expects for char keys
        # key_special is for pynput.keyboard.Key enum members
        actual_key_for_pynput = key_code if key_code else key_special

        # Emit: display_name, the actual key object for pynput, interval
        self.key_setting_accepted.emit(self.key_display_name, actual_key_for_pynput, interval)
        self.accept() # Close the dialog

    def done(self, result):
        # Ensure listener thread is stopped if dialog is closed prematurely
        if self.key_listener_thread and self.key_listener_thread.isRunning():
            print("Dialog closed, stopping listener thread...")
            self.key_listener_thread.stop_listener() # Request stop
            self.key_listener_thread.wait(1000) # Wait a bit for it to finish
        super().done(result)

    # Allow dialog to be closed with Escape key, even if a listener is active (might be tricky)
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
