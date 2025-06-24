import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QCheckBox, QSpacerItem, QSizePolicy, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QKeySequence # For displaying shortcuts nicely

from .add_key_dialog import AddKeyDialog
from ..core.key_event import press_and_release_key
import uuid # For unique IDs

class AutoClickerMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("macOS 自動按鍵程式")
        self.setGeometry(100, 100, 650, 450) # x, y, width, height

        self.key_configs = [] # List to store key configuration dictionaries
        self.is_globally_running = False # Flag to track overall state

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._init_ui()
        self._update_key_list_widget() # Initially populate if any data (though it's empty now)

    def _init_ui(self):
        # 1. 按鍵設定列表區域
        list_area_label = QLabel("自動按鍵列表:")
        self.main_layout.addWidget(list_area_label)

        self.key_list_widget = QListWidget()
        self.key_list_widget.setAlternatingRowColors(True)
        self.key_list_widget.setStyleSheet(
            "QListWidget::item { padding: 5px; }"
            "QListWidget::item:hover { background-color: #f0f0f0; }"
        )
        self.main_layout.addWidget(self.key_list_widget, 1) # Stretch factor 1

        # 2. 新增按鍵區域
        add_key_layout = QHBoxLayout()
        self.add_key_button = QPushButton("➕ 新增按鍵設定") # Using heavy plus sign emoji
        self.add_key_button.setStyleSheet(
            "QPushButton { padding: 6px 10px; border-radius: 5px; background-color: #5cb85c; color: white; }"
            "QPushButton:hover { background-color: #4cae4c; }"
            "QPushButton:pressed { background-color: #449d44; }"
        )
        self.add_key_button.clicked.connect(self._show_add_key_dialog)
        add_key_layout.addWidget(self.add_key_button)
        add_key_layout.addSpacerItem(QSpacerItem(10, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.main_layout.addLayout(add_key_layout)

        # 分隔線
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(line)

        # 3. 全域控制區域
        control_layout = QHBoxLayout()
        self.start_all_button = QPushButton("▶️ 全部開始")
        self.start_all_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; border-radius: 5px;")
        self.start_all_button.clicked.connect(self._start_all_macros)

        self.stop_all_button = QPushButton("⏹️ 全部停止")
        self.stop_all_button.setStyleSheet("background-color: #f44336; color: white; padding: 8px; border-radius: 5px;")
        self.stop_all_button.clicked.connect(self._stop_all_macros)
        self.stop_all_button.setEnabled(False) # Initially disabled

        control_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        control_layout.addWidget(self.start_all_button)
        control_layout.addWidget(self.stop_all_button)
        control_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.main_layout.addLayout(control_layout)

    def _update_key_list_widget(self):
        """根據 self.key_configs 重新整理 QListWidget"""
        self.key_list_widget.clear()
        for config in self.key_configs:
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(8, 5, 8, 5) # top, bottom, left, right

            checkbox = QCheckBox()
            checkbox.setChecked(config["enabled"])
            checkbox.stateChanged.connect(lambda state, cfg_id=config["id"]: self._toggle_key_config_enabled(cfg_id, state))
            item_layout.addWidget(checkbox)

            key_display_str = config["display_name"]
            # Attempt to make common special keys more readable
            if "key." in key_display_str: # pynput special keys often come as "Key.something"
                key_display_str = key_display_str.replace("key.", "").capitalize()

            key_display_str = config["display_name"]
            if "key." in key_display_str:
                key_display_str = key_display_str.replace("key.", "").capitalize()

            status_indicator = "▶️" if config.get("is_running") else "⏸️" # Play/Pause emoji as indicator
            key_text = f"{status_indicator} 按鍵: <b>{key_display_str}</b>"
            if config.get("is_running"):
                 key_text = f"<font color='green'>{key_text}</font>"

            key_label = QLabel(key_text)
            key_label.setToolTip(f"內部按鍵碼: {config['key_actual_for_pynput']}\nID: {config['id']}")
            item_layout.addWidget(key_label)

            interval_label = QLabel(f"間隔: {config['interval']:.2f} 秒")
            if config.get("is_running"):
                interval_label.setStyleSheet("color: green;")
            item_layout.addWidget(interval_label)

            item_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

            remove_button = QPushButton("🗑️ 移除") # Trash can emoji
            remove_button.setFixedSize(80, 28)
            remove_button.setStyleSheet(
                "QPushButton { background-color: #d9534f; color: white; border-radius: 3px; padding: 4px; }"
                "QPushButton:hover { background-color: #c9302c; }"
                "QPushButton:pressed { background-color: #ac2925; }"
            )
            remove_button.setToolTip("移除此項設定")
            remove_button.clicked.connect(lambda checked=False, cfg_id=config["id"]: self._remove_key_config(cfg_id)) # Added checked=False for lambda with PySide signal
            item_layout.addWidget(remove_button)

            list_item = QListWidgetItem(self.key_list_widget)
            list_item.setSizeHint(item_widget.sizeHint()) # Important for custom widget
            self.key_list_widget.addItem(list_item)
            self.key_list_widget.setItemWidget(list_item, item_widget)
            # Store config_id in the item itself for easier access if needed, though not strictly necessary here
            list_item.setData(Qt.ItemDataRole.UserRole, config["id"])


    @Slot()
    def _show_add_key_dialog(self):
        dialog = AddKeyDialog(self)
        # Pass existing key display names to avoid duplicates if necessary (optional)
        # current_display_names = [cfg['display_name'] for cfg in self.key_configs]
        # dialog.set_existing_names(current_display_names)

        dialog.key_setting_accepted.connect(self._add_new_key_config)
        dialog.exec() # exec_() for older Qt versions, exec() is fine in PySide6

    @Slot(str, object, float)
    def _add_new_key_config(self, display_name, key_actual_for_pynput, interval):
        # key_actual_for_pynput is what pynput's Controller.press() expects
        # (either a character string or a pynput.keyboard.Key object)

        new_config = {
            "id": str(uuid.uuid4()),
            "display_name": display_name,
            "key_actual_for_pynput": key_actual_for_pynput,
            "interval": interval,
            "enabled": True, # Default to enabled
            "timer": None, # Placeholder for QTimer or thread
            "is_running": False
        }
        self.key_configs.append(new_config)
        self._update_key_list_widget()
        # print(f"Added new key config: {new_config}")

    def _find_config_by_id(self, config_id):
        for config in self.key_configs:
            if config["id"] == config_id:
                return config
        return None

    @Slot(str)
    def _remove_key_config(self, config_id_to_remove):
        # Find and remove the item from self.key_configs
        # Also stop its timer/thread if it's running (to be implemented later)
        config_to_remove = self._find_config_by_id(config_id_to_remove)
        if config_to_remove:
            if config_to_remove.get("is_running", False):
                self._stop_single_macro(config_to_remove) # Stop before removing

            self.key_configs = [cfg for cfg in self.key_configs if cfg["id"] != config_id_to_remove]
            self._update_key_list_widget()
            # print(f"Removed key config: {config_id_to_remove}")
        else:
            QMessageBox.warning(self, "錯誤", f"找不到要移除的設定 (ID: {config_id_to_remove})")


    @Slot(str, int)
    def _toggle_key_config_enabled(self, config_id, state):
        config = self._find_config_by_id(config_id)
        if config:
            new_enabled_state = (state == Qt.CheckState.Checked.value)
            if config["enabled"] == new_enabled_state: # No change
                return

            config["enabled"] = new_enabled_state
            # print(f"Config '{config['display_name']}' enabled: {config['enabled']}")

            # If the macros are globally running, and this one was just enabled, start it.
            # If it was just disabled while globally running, stop it.
            # This interacts with the global start/stop state.
            # For now, let's assume if we toggle, and it was running, it should stop.
            # And if it's enabled, it will be picked up by a "Start All".
            # The logic here will be refined when _start_all_macros is implemented.
            if not config["enabled"] and config.get("is_running", False):
                self._stop_single_macro(config)

            # If global state is "running" and config is now enabled, we might want to start it.
            # This depends on the desired behavior for toggling while active.
            # For now, toggling 'enabled' primarily sets the flag.
            # Global start/stop will iterate through 'enabled' configs.

        self._update_key_list_widget() # Refresh to reflect state.

    @Slot(str) # config_id
    def _trigger_key_action(self, config_id):
        config = self._find_config_by_id(config_id)
        if config and config.get("is_running", False) and config.get("enabled", False):
            # print(f"Executing key: {config['display_name']}")
            press_and_release_key(config['key_actual_for_pynput'])
        elif config and config.get("timer"): # If timer exists but shouldn't run, stop it
            # This case might happen if it was disabled/stopped but timer fired one last time.
            self._stop_single_macro(config)


    def _start_single_macro(self, config):
        if not config or not config.get("enabled", False) or config.get("is_running", False):
            return

        if config.get("timer") and config["timer"].isActive(): # Already running with a timer
            return

        if not config.get("timer"): # Create timer if it doesn't exist
            config["timer"] = QTimer(self) # Parent it to self for auto-cleanup (maybe)
            # Using lambda to pass config_id. functools.partial is another option.
            config["timer"].timeout.connect(lambda cid=config["id"]: self._trigger_key_action(cid))

        config["timer"].setInterval(int(config["interval"] * 1000)) # ms
        config["timer"].start()
        config["is_running"] = True
        # print(f"Started macro: {config['display_name']}")
        self._update_key_list_widget() # Reflect running state (e.g. change icon, not implemented yet)

    def _stop_single_macro(self, config):
        if not config or not config.get("is_running", False):
            return

        if config.get("timer"):
            config["timer"].stop()
            # We can choose to delete the timer or reuse it. For simplicity, let's keep it.
            # If we delete:
            # config["timer"].deleteLater()
            # config["timer"] = None
        config["is_running"] = False
        # print(f"Stopped macro: {config['display_name']}")
        self._update_key_list_widget() # Reflect running state

    @Slot()
    def _start_all_macros(self):
        if not self.key_configs:
            QMessageBox.information(self, "提示", "請先新增至少一個按鍵設定。")
            return

        self.is_globally_running = True
        one_started = False
        for config in self.key_configs:
            if config.get("enabled", False):
                self._start_single_macro(config)
                one_started = True

        if one_started:
            self.start_all_button.setEnabled(False)
            self.stop_all_button.setEnabled(True)
            # print("All enabled macros started.")
        else:
            self.is_globally_running = False # No enabled macros were actually started
            QMessageBox.information(self, "提示", "沒有已啟用的按鍵設定可以開始。")


    @Slot()
    def _stop_all_macros(self):
        self.is_globally_running = False
        any_stopped = False
        for config in self.key_configs:
            if config.get("is_running", False):
                self._stop_single_macro(config)
                any_stopped = True

        # Always update button state after stop all, even if nothing was technically running
        # This handles cases where user might have manually disabled all items then hits stop.
        self.start_all_button.setEnabled(True)
        self.stop_all_button.setEnabled(False)
        # if any_stopped:
            # print("All active macros stopped.")
        # else:
            # print("No macros were running to stop.")

    def closeEvent(self, event):
        """Ensure all macros are stopped when the window is closed."""
        # print("Close event triggered. Stopping all macros.")
        self._stop_all_macros() # Attempt to stop all running macros

        # Clean up timers explicitly, though being parented might handle some of this.
        # for config in self.key_configs:
        #     if config.get("timer"):
        #         config["timer"].stop()
        #         config["timer"].deleteLater() # Request Qt to delete when safe
        #         config["timer"] = None

        event.accept() # Proceed with closing the window


if __name__ == '__main__':
    # This is for testing the main window independently
    # Remember macOS Accessibility permissions for pynput to capture keys!
    app = QApplication(sys.argv)
    # app.setStyle("Fusion") # Uncomment to try Fusion style
    window = AutoClickerMainWindow()
    window.show()
    sys.exit(app.exec())
