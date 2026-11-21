import customtkinter as ctk


class ToggleCard(ctk.CTkFrame):
    def __init__(self, master, item: dict, initial_state: bool, on_change):
        super().__init__(
            master,
            fg_color="#1d1d23",
            border_color="#2a2a33",
            border_width=1,
            corner_radius=8,
            height=70,
        )
        self.item = item
        self.on_change = on_change
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(
            self,
            text=item["title"],
            font=("Segoe UI", 13, "bold"),
            text_color="#f3f3f7",
        )
        title_lbl.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 0))

        desc_lbl = ctk.CTkLabel(
            self,
            text=item["desc"],
            font=("Segoe UI", 11),
            text_color="#9898a6",
        )
        desc_lbl.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

        self.var = ctk.BooleanVar(value=initial_state)
        self.switch = ctk.CTkSwitch(
            self,
            text="Enabled" if initial_state else "Disabled",
            variable=self.var,
            command=self._handle_toggle,
            progress_color="#6c5ce7",
            button_color="#ffffff",
            button_hover_color="#e4e4ec",
            font=("Segoe UI", 11),
            text_color="#c8c8d4",
        )
        self.switch.grid(row=0, column=1, rowspan=2, padx=16)

    def _handle_toggle(self) -> None:
        state = self.var.get()
        self.switch.configure(text="Enabled" if state else "Disabled")
        self.on_change(self.item, state)


class DropdownCard(ctk.CTkFrame):
    def __init__(self, master, item: dict, on_select):
        super().__init__(
            master,
            fg_color="#1d1d23",
            border_color="#2a2a33",
            border_width=1,
            corner_radius=8,
            height=96,
        )
        self.item = item
        self.on_select = on_select
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(
            self,
            text=item["title"],
            font=("Segoe UI", 13, "bold"),
            text_color="#f3f3f7",
        )
        title_lbl.grid(row=0, column=0, sticky="w", padx=16, pady=(10, 0))

        desc_lbl = ctk.CTkLabel(
            self,
            text=item["desc"],
            font=("Segoe UI", 11),
            text_color="#9898a6",
        )
        desc_lbl.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 6))

        default_val = item.get("default_option", item["options"][0])
        self.option_menu = ctk.CTkOptionMenu(
            self,
            values=item["options"],
            command=self._handle_select,
            fg_color="#26262f",
            button_color="#32323e",
            button_hover_color="#3f3f4e",
            dropdown_fg_color="#22222a",
            dropdown_hover_color="#323240",
            text_color="#e8e8f0",
            font=("Segoe UI", 12),
            height=30,
        )
        self.option_menu.set(default_val)
        self.option_menu.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))

    def _handle_select(self, choice: str) -> None:
        self.on_select(self.item, choice)