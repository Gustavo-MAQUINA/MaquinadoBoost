import subprocess
import winreg
from core.backup import ROOT_MAP, export_snapshot


def run_cmd(cmd: list[str] | str, log_fn=None) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            capture_output=True,
            text=True,
            timeout=25,
        )
        out = (proc.stdout or proc.stderr or "").strip()
        ok = proc.returncode == 0
        if log_fn:
            status = "OK" if ok else f"RC={proc.returncode}"
            msg = f" -> {out}" if out else ""
            log_fn(f"[CMD {status}] {cmd}{msg}")
        return ok, out
    except Exception as exc:
        if log_fn:
            log_fn(f"[ERRO CMD] {cmd}: {exc}")
        return False, str(exc)


def get_reg_dword(root: str, path: str, name: str, default=None):
    hive = ROOT_MAP.get(root)
    if not hive:
        return default
    try:
        with winreg.OpenKey(hive, path, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, name)
            return val
    except FileNotFoundError:
        return default
    except OSError:
        return default


def set_reg_dword(root: str, path: str, name: str, value: int, log_fn=None) -> bool:
    hive = ROOT_MAP.get(root)
    if not hive:
        return False
    try:
        with winreg.CreateKeyEx(hive, path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, int(value))
        if log_fn:
            log_fn(f"[REG] {root}\\{path}\\{name} = {value}")
        return True
    except OSError as exc:
        if log_fn:
            log_fn(f"[ERRO REG] {root}\\{path}\\{name}: {exc}")
        return False


def set_service_start(service_name: str, start_type: str, log_fn=None) -> bool:
    """
    start_type: 'disabled', 'demand' (manual), 'auto'
    """
    ok, _ = run_cmd(["sc.exe", "config", service_name, f"start={start_type}"], log_fn=log_fn)
    if start_type == "disabled":
        run_cmd(["sc.exe", "stop", service_name], log_fn=log_fn)
    return ok


def get_service_disabled(service_name: str) -> bool:
    ok, out = subprocess.run(
        ["sc.exe", "qc", service_name], capture_output=True, text=True
    ).returncode == 0, ""
    if not ok:
        return False
    proc = subprocess.run(["sc.exe", "qc", service_name], capture_output=True, text=True)
    return "DISABLED" in (proc.stdout or "").upper()


def _find_nvidia_class_keys() -> list[str]:
    base = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    found = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base, 0, winreg.KEY_READ) as root_key:
            sub_count, _, _ = winreg.QueryInfoKey(root_key)
            for idx in range(sub_count):
                sub_name = winreg.EnumKey(root_key, idx)
                if not sub_name.isdigit():
                    continue
                sub_path = f"{base}\\{sub_name}"
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_path, 0, winreg.KEY_READ) as k:
                        desc, _ = winreg.QueryValueEx(k, "DriverDesc")
                        if "NVIDIA" in str(desc).upper():
                            found.append(sub_path)
                except OSError:
                    continue
    except OSError:
        pass
    return found


def execute_custom_action(action_key: str, enable: bool, log_fn=None, value=None) -> bool:
    if action_key == "boot_menu_standard":
        mode = "standard" if enable else "legacy"
        ok, _ = run_cmd(["bcdedit", "/set", "{current}", "bootmenupolicy", mode], log_fn=log_fn)
        return ok

    if action_key == "hyperv_toggle":
        val = "off" if enable else "auto"
        ok, _ = run_cmd(["bcdedit", "/set", "hypervisorlaunchtype", val], log_fn=log_fn)
        return ok

    if action_key == "dep_toggle":
        policy = "AlwaysOff" if enable else "OptIn"
        ok, _ = run_cmd(["bcdedit", "/set", "{current}", "nx", policy], log_fn=log_fn)
        return ok

    if action_key == "nvidia_preemption":
        keys = _find_nvidia_class_keys()
        if not keys:
            if log_fn:
                log_fn("[INFO] Chave de driver NVIDIA não encontrada neste sistema.")
            return False
        target = 0 if enable else 1
        ok_all = True
        for path in keys:
            ok_all = set_reg_dword("HKLM", path, "EnableMidGfxPreemption", target, log_fn) and ok_all
            ok_all = set_reg_dword("HKLM", path, "EnableMidBufferPreemption", target, log_fn) and ok_all
        return ok_all

    if action_key == "nvidia_hdcp":
        keys = _find_nvidia_class_keys()
        if not keys:
            if log_fn:
                log_fn("[INFO] Chave de driver NVIDIA não encontrada neste sistema.")
            return False
        target = 1 if enable else 0
        ok_all = True
        for path in keys:
            ok_all = set_reg_dword("HKLM", path, "RMHdcpKeyglobZero", target, log_fn) and ok_all
        return ok_all

    if action_key == "network_optimization":
        if enable:
            run_cmd("netsh int tcp set global autotuninglevel=normal", log_fn)
            run_cmd("netsh int tcp set global ecncapability=disabled", log_fn)
            run_cmd("netsh int tcp set global timestamps=disabled", log_fn)
            if log_fn:
                log_fn("[NET] Perfil de otimização TCP aplicado.")
            return True
        else:
            run_cmd("netsh int tcp set global autotuninglevel=normal", log_fn)
            run_cmd("netsh int tcp set global ecncapability=default", log_fn)
            if log_fn:
                log_fn("[NET] Configurações TCP padrão restauradas.")
            return True

    if action_key == "services_profile":
        profile = str(value or "Default")
        if log_fn:
            log_fn(f"[SERVICES] Aplicando perfil de serviços: {profile}")
        if profile == "SapphireOS":
            for svc in ["DiagTrack", "dmwappushservice", "Fax", "MapsBroker"]:
                set_service_start(svc, "disabled", log_fn)
        elif profile == "Minimal":
            for svc in ["DiagTrack", "Fax", "MapsBroker"]:
                set_service_start(svc, "disabled", log_fn)
        else:
            for svc in ["DiagTrack", "Fax", "MapsBroker"]:
                set_service_start(svc, "demand", log_fn)
        return True

    if action_key == "svchost_split":
        ram_map = {
            "4GB RAM": 4194304,
            "8GB RAM": 8388608,
            "16GB RAM": 16777216,
            "32GB RAM": 33554432,
            "64GB RAM": 67108864,
        }
        kb = ram_map.get(str(value), 16777216)
        return set_reg_dword(
            "HKLM",
            r"SYSTEM\CurrentControlSet\Control",
            "SvcHostSplitThresholdInKB",
            kb,
            log_fn,
        )

    if action_key == "win32_priority":
        hex_map = {
            "2A (Hex)": 0x2A,
            "26 (Hex)": 0x26,
            "28 (Hex)": 0x28,
            "18 (Hex)": 0x18,
            "02 (Hex)": 0x02,
        }
        val = hex_map.get(str(value), 0x2A)
        return set_reg_dword(
            "HKLM",
            r"SYSTEM\CurrentControlSet\Control\PriorityControl",
            "Win32PrioritySeparation",
            val,
            log_fn,
        )

    if action_key == "context_classic_menu":
        clsid = r"Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32"
        hive = winreg.HKEY_CURRENT_USER
        try:
            if enable:
                with winreg.CreateKeyEx(hive, clsid, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "")
                if log_fn:
                    log_fn("[CTX] Menu de contexto clássico do Windows ativado.")
            else:
                try:
                    winreg.DeleteKey(hive, clsid)
                except OSError:
                    pass
                if log_fn:
                    log_fn("[CTX] Menu de contexto padrão do Windows restaurado.")
            return True
        except OSError as exc:
            if log_fn:
                log_fn(f"[ERRO CTX] {exc}")
            return False

    if action_key == "windows_update_pause":
        days = "365" if enable else "0"
        return set_reg_dword(
            "HKLM",
            r"SOFTWARE\Microsoft\WindowsUpdate\UX\Settings",
            "PauseUpdatesExpiryDays",
            365 if enable else 0,
            log_fn,
        )

    if action_key == "create_restore_point":
        cmd = (
            'powershell -NoProfile -Command "Checkpoint-Computer '
            '-Description \'MaquinadoBoost Snapshot\' -RestorePointType \'MODIFY_SETTINGS\'"'
        )
        ok, _ = run_cmd(cmd, log_fn=log_fn)
        return ok

    return False


def apply_tweak_state(item: dict, enabled: bool, log_fn=None) -> bool:
    if item.get("backup_before", False):
        export_snapshot([item], log_fn=log_fn)

    reg_cfg = item.get("reg")
    if reg_cfg:
        target = reg_cfg["on_value"] if enabled else reg_cfg["off_value"]
        return set_reg_dword(
            reg_cfg["root"], reg_cfg["path"], reg_cfg["name"], target, log_fn=log_fn
        )

    svc_cfg = item.get("service")
    if svc_cfg:
        mode = svc_cfg["on_start"] if enabled else svc_cfg["off_start"]
        return set_service_start(svc_cfg["name"], mode, log_fn=log_fn)

    action_key = item.get("action")
    if action_key:
        return execute_custom_action(action_key, enabled, log_fn=log_fn)

    return False


def detect_tweak_state(item: dict) -> bool:
    reg_cfg = item.get("reg")
    if reg_cfg:
        current = get_reg_dword(reg_cfg["root"], reg_cfg["path"], reg_cfg["name"], None)
        return current == reg_cfg["on_value"]

    svc_cfg = item.get("service")
    if svc_cfg:
        if svc_cfg["on_start"] == "disabled":
            return get_service_disabled(svc_cfg["name"])
        return False

    return bool(item.get("default_state", False))