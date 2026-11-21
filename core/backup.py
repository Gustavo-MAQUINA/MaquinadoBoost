import json
import os
import winreg
from datetime import datetime
from pathlib import Path

ROOT_MAP = {
    "HKLM": winreg.HKEY_LOCAL_MACHINE,
    "HKCU": winreg.HKEY_CURRENT_USER,
}


def get_backup_dir() -> Path:
    base_dir = Path(__file__).resolve().parent.parent / "backups"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def read_registry_value(root: str, subkey: str, value_name: str):
    hive = ROOT_MAP.get(root)
    if hive is None:
        return None
    try:
        with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ) as key:
            val, reg_type = winreg.QueryValueEx(key, value_name)
            return {"value": val, "type": reg_type}
    except FileNotFoundError:
        return None
    except OSError:
        return None


def export_snapshot(entries: list[dict], log_fn=None) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = get_backup_dir() / f"snapshot_{timestamp}.json"

    payload = {
        "created_at": datetime.now().isoformat(),
        "entries": [],
    }

    for item in entries:
        reg_cfg = item.get("reg")
        if reg_cfg:
            current = read_registry_value(
                reg_cfg["root"], reg_cfg["path"], reg_cfg["name"]
            )
            payload["entries"].append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "reg": reg_cfg,
                    "snapshot": current,
                }
            )

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    if log_fn:
        log_fn(f"[BACKUP] Snapshot salvo em: {filepath}")
    return str(filepath)


def restore_snapshot(filepath: str, log_fn=None) -> int:
    if not os.path.exists(filepath):
        if log_fn:
            log_fn(f"[ERRO] Arquivo de backup não encontrado: {filepath}")
        return 0

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    restored = 0
    for entry in data.get("entries", []):
        reg_cfg = entry.get("reg")
        snap = entry.get("snapshot")
        if not reg_cfg:
            continue
        hive = ROOT_MAP.get(reg_cfg["root"])
        if not hive:
            continue
        try:
            with winreg.CreateKeyEx(
                hive, reg_cfg["path"], 0, winreg.KEY_SET_VALUE
            ) as key:
                if snap is None:
                    try:
                        winreg.DeleteValue(key, reg_cfg["name"])
                        restored += 1
                    except FileNotFoundError:
                        pass
                else:
                    winreg.SetValueEx(
                        key, reg_cfg["name"], 0, snap["type"], snap["value"]
                    )
                    restored += 1
        except OSError as exc:
            if log_fn:
                log_fn(f"[AVISO] Falha ao restaurar {entry.get('title')}: {exc}")

    if log_fn:
        log_fn(f"[BACKUP] {restored} chaves restauradas de {filepath}")
    return restored