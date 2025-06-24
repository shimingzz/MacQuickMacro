import sys
import os
from PySide6.QtWidgets import QApplication

# When running with "python -m src.main", 'src' is treated as a package.
# The import ".gui.main_window" means "from the current package (src),
# import the 'gui' subpackage, and from it, import AutoClickerMainWindow".
from .gui.main_window import AutoClickerMainWindow

def main():
    app = QApplication(sys.argv)
    # app.setQuitOnLastWindowClosed(True) # Default behavior

    # For a more native macOS menu bar experience, especially if you add menus later
    # app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, True) # Example

    window = AutoClickerMainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    # This special variable `__package__` is set when Python loads a module
    # as part of a package. If it's None or empty, it means the file was
    # run as a top-level script, which can break relative imports.
    # print(f"Running main.py: __name__ = {__name__}, __package__ = {__package__}")
    main()
