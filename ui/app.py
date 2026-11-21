import platform
import customtkinter as ctk
from core.backup import export_snapshot, get_backup_dir, restore_snapshot
from core.system_actions import (
    apply_tweak_state,
    detect_tweak_state,
    execute_custom_action,
)
from core.tweaks_catalog import TWEAKS_BY_SECTION
from ui.widgets import DropdownCard, ToggleCard

NAV_ITEMS = [
    "Dashboard",
    "Tweaks",
    "Downloads",
    "Gaming Tweaks",
    "Updates",
    "Context Menu",
]


class MaquinadoBoostApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MaquinadoBoost — Windows 11 Performance & Debloat")
        self.geometry("1220x740")
        self.minsize(980, 620)
        self.configure(fg_color="#121216")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.current_section = "Tweaks"

        self._build_sidebar()
        self._build_main_container()
        self.select_section("Tweaks")

    def log(self, message: str) -> None:
        if hasattr(self, "log_box") and self.log_box.winfo_exists():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", message + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=220, fg_color="#17171c", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(10, weight=1)

        brand_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(20, 14))

        ctk.CTkLabel(
            brand_frame,
            text="⚡ MaquinadoBoost",
            font=("Segoe UI", 16, "bold"),
            text_color="#f5f5fa",
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand_frame,
            text="Win11 Latency & Debloat",
            font=("Segoe UI", 11),
            text_color="#8e8e9d",
        ).pack(anchor="w")

        for idx, name in enumerate(NAV_ITEMS, start=1):
            btn = ctk.CTkButton(
                sidebar,
                text=name,
                anchor="w",
                fg_color="transparent",
                hover_color="#23232c",
                text_color="#c4c4d0",
                font=("Segoe UI", 13),
                height=38,
                corner_radius=8,
                command=lambda n=name: self.select_section(n),
            )
            btn.grid(row=idx, column=0, sticky="ew", padx=10, pady=2)
            self.nav_buttons[name] = btn

        about_btn = ctk.CTkButton(
            sidebar,
            text="About",
            anchor="w",
            fg_color="transparent",
            hover_color="#23232c",
            text_color="#8e8e9d",
            font=("Segoe UI", 12),
            height=34,
            corner_radius=8,
            command=lambda: self.select_section("About"),
        )
        about_btn.grid(row=11, column=0, sticky="ew", padx=10, pady=(0, 16))
        self.nav_buttons["About"] = about_btn

    def _build_main_container(self) -> None:
        self.right_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=22, pady=18)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_rowconfigure(2, weight=0)

        self.header_lbl = ctk.CTkLabel(
            self.right_panel,
            text="Tweaks",
            font=("Segoe UI", 22, "bold"),
            text_color="#f5f5fa",
        )
        self.header_lbl.grid(row=0, column=0, sticky="w", pady=(0, 12))

        self.scroll_area = ctk.CTkScrollableFrame(
            self.right_panel,
            fg_color="transparent",
            scrollbar_button_color="#2b2b36",
            scrollbar_button_hover_color="#3b3b4a",
        )
        self.scroll_area.grid(row=1, column=0, sticky="nsew")
        self.scroll_area.grid_columnconfigure((0, 1), weight=1)

        log_frame = ctk.CTkFrame(
            self.right_panel,
            fg_color="#17171c",
            border_color="#272730",
            border_width=1,
            corner_radius=8,
            height=115,
        )
        log_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        log_frame.grid_propagate(False)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            log_frame,
            text="Console de Execução",
            font=("Segoe UI", 11, "bold"),
            text_color="#a2a2b2",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(6, 2))

        self.log_box = ctk.CTkTextbox(
            log_frame,
            fg_color="#121216",
            text_color="#b8d8be",
            font=("Consolas", 11),
            state="disabled",
        )
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))

    def select_section(self, section: str) -> None:
        self.current_section = section
        self.header_lbl.configure(text=section)

        for name, btn in self.nav_buttons.items():
            if name == section:
                btn.configure(fg_color="#24242e", text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color="#c4c4d0")

        for widget in self.scroll_area.winfo_children():
            widget.destroy()

        if section == "Dashboard":
            self._render_dashboard()
        elif section == "Gaming Tweaks":
            self._render_gaming_tweaks()
        elif section == "Downloads":
            self._render_placeholder(
                "Módulo de Downloads / Post-Install",
                "Aqui você pode adicionar scripts de instalação silenciosa via winget para navegadores, drivers e runtimes.",
            )
        elif section == "About":
            self._render_placeholder(
                "Sobre o MaquinadoBoost",
                f"Sistema: Windows {platform.release()} ({platform.version()})\nArquitetura: {platform.machine()}",
            )
        else:
            items = TWEAKS_BY_SECTION.get(section, [])
            self._render_toggle_grid(items)

    def _render_toggle_grid(self, items: list[dict], start_row: int = 0) -> int:
        row_idx = start_row
        for idx, item in enumerate(items):
            state = detect_tweak_state(item)
            card = ToggleCard(
                self.scroll_area,
                item=item,
                initial_state=state,
                on_change=self._on_toggle_change,
            )
            card.grid(
                row=row_idx + (idx // 2),
                column=idx % 2,
                sticky="ew",
                padx=6,
                pady=6,
            )
        return row_idx + ((len(items) + 1) // 2)

    def _render_gaming_tweaks(self) -> None:
        gaming_data = TWEAKS_BY_SECTION["Gaming Tweaks"]
        current_row = 0

        for group_name, group_items in gaming_data.items():
            section_box = ctk.CTkFrame(
                self.scroll_area,
                fg_color="#18181f",
                border_color="#272731",
                border_width=1,
                corner_radius=10,
            )
            section_box.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=6, pady=(4, 12))
            section_box.grid_columnconfigure((0, 1), weight=1)

            ctk.CTkLabel(
                section_box,
                text=group_name,
                font=("Segoe UI", 15, "bold"),
                text_color="#f3f3f7",
            ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 6))

            inner_idx = 0
            for item in group_items:
                kind = item.get("kind", "toggle")
                r = 1 + (inner_idx // 2)
                c = inner_idx % 2
                if kind == "dropdown":
                    card = DropdownCard(
                        section_box,
                        item=item,
                        on_select=self._on_dropdown_select,
                    )
                    card.grid(row=r, column=c, sticky="ew", padx=10, pady=6)
                else:
                    card = ToggleCard(
                        section_box,
                        item=item,
                        initial_state=detect_tweak_state(item),
                        on_change=self._on_toggle_change,
                    )
                    card.grid(row=r, column=c, sticky="ew", padx=10, pady=6)
                inner_idx += 1

            # Espaçador inferior dentro do grupo
            ctk.CTkLabel(section_box, text="", height=4).grid(row=99, column=0)
            current_row += 1

    def _render_dashboard(self) -> None:
        info_card = ctk.CTkFrame(
            self.scroll_area,
            fg_color="#1d1d23",
            border_color="#2a2a33",
            border_width=1,
            corner_radius=10,
        )
        info_card.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=6)

        ctk.CTkLabel(
            info_card,
            text="Segurança e Snapshots do Sistema",
            font=("Segoe UI", 15, "bold"),
            text_color="#f3f3f7",
        ).pack(anchor="w", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            info_card,
            text=f"Máquina: {platform.node()} | Processador: {platform.processor() or 'N/A'}",
            font=("Segoe UI", 12),
            text_color="#a2a2b2",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        btn_row = ctk.CTkFrame(info_card, fg_color="transparent")
        btn_row.pack(anchor="w", padx=16, pady=(0, 16))

        ctk.CTkButton(
            btn_row,
            text="Exportar Snapshot (.json)",
            fg_color="#6c5ce7",
            hover_color="#5b4bc4",
            command=self._export_all_snapshot,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row,
            text="Restaurar Último Snapshot",
            fg_color="#282834",
            hover_color="#353545",
            command=self._restore_latest_snapshot,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row,
            text="Criar Ponto de Restauração",
            fg_color="#282834",
            hover_color="#353545",
            command=lambda: execute_custom_action("create_restore_point", True, log_fn=self.log),
        ).pack(side="left")

    def _render_placeholder(self, title: str, subtitle: str) -> None:
        box = ctk.CTkFrame(
            self.scroll_area,
            fg_color="#1d1d23",
            border_color="#2a2a33",
            border_width=1,
            corner_radius=10,
        )
        box.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=6)
        ctk.CTkLabel(box, text=title, font=("Segoe UI", 15, "bold")).pack(
            anchor="w", padx=16, pady=(14, 4)
        )
        ctk.CTkLabel(box, text=subtitle, font=("Segoe UI", 12), text_color="#a2a2b2").pack(
            anchor="w", padx=16, pady=(0, 14)
        )

    def _export_all_snapshot(self) -> None:
        all_items = []
        for sec, val in TWEAKS_BY_SECTION.items():
            if isinstance(val, list):
                all_items.extend(val)
            elif isinstance(val, dict):
                for grp in val.values():
                    all_items.extend(grp)
        export_snapshot(all_items, log_fn=self.log)

    def _restore_latest_snapshot(self) -> None:
        backup_dir = get_backup_dir()
        files = sorted(backup_dir.glob("snapshot_*.json"), reverse=True)
        if not files:
            self.log("[INFO] Nenhum snapshot encontrado na pasta backups/.")
            return
        restore_snapshot(str(files[0]), log_fn=self.log)

    def _on_toggle_change(self, item: dict, state: bool) -> None:
        apply_tweak_state(item, state, log_fn=self.log)

    def _on_dropdown_select(self, item: dict, choice: str) -> None:
        action = item.get("action")
        if action:
            execute_custom_action(action, True, log_fn=self.log, value=choice)