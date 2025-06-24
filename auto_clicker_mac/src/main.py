import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import AutoClickerMainWindow

def main():
    app = QApplication(sys.argv)
    # app.setQuitOnLastWindowClosed(True) # Default behavior

    # For a more native macOS menu bar experience, especially if you add menus later
    # app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, True) # Example

    window = AutoClickerMainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
