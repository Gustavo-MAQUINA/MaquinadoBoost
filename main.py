import sys
import customtkinter as ctk
from core.admin import ensure_admin
from ui.app import MaquinadoBoostApp


def main() -> None:
    ensure_admin()
    ctk.set_appearance_mode("dark")
    app = MaquinadoBoostApp()
    app.mainloop()


if __name__ == "__main__":
    sys.exit(main() or 0)