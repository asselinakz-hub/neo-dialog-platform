# scoring.py
import json
from typing import Dict, Any, Tuple, List

def load_config(path: str = "neo_config.json") -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def ru(config: Dict[str, Any], pid: str) -> str:
    return config["potentials"].get(pid, {}).get("ru", pid)

def build_column_result(config: Dict[str, Any], sphere_id: str, type_id: str) -> Tuple[str, List[str]]:
    """
    Возвращает:
    main_potential, ordered_list_of_3_in_sphere
    ordered_list: main, second, third (внутри сферы)
    """
    mapping = config["sphere_type_to_potential"]
    main = mapping[sphere_id][type_id]

    sphere_pots = config["spheres"][sphere_id]["potentials"][:]  # 3 потенциала сферы
    # ставим main первым, остальные — как есть, без усложнений
    ordered = [main] + [p for p in sphere_pots if p != main]
    return main, ordered

def make_report(responses: Dict[str, Any], config_path: str = "neo_config.json") -> Dict[str, Any]:
    config = load_config(config_path)

    columns = [
        ("perception", "Восприятие"),
        ("motivation", "Мотивация"),
        ("instrument", "Инструмент")
    ]

    table = {
        "perception": {"row1": None, "row2": None, "row3": None},
        "motivation": {"row1": None, "row2": None, "row3": None},
        "instrument": {"row1": None, "row2": None, "row3": None},
    }

    # собираем по каждому столбцу сферу+тип
    for col_id, _ in columns:
        sphere_key = f"{col_id}_sphere"
        type_key = f"{col_id}_type"

        sphere_id = responses.get(sphere_key, {}).get("choice")
        type_id = responses.get(type_key, {}).get("choice")

        if not sphere_id or not type_id:
            # если человек не прошёл до конца
            continue

        main, ordered3 = build_column_result(config, sphere_id, type_id)
        table[col_id]["row1"] = ordered3[0]
        table[col_id]["row2"] = ordered3[1]
        table[col_id]["row3"] = ordered3[2]

    # итоговый “читаемый” вывод
    def pretty(col_id: str, col_ru: str) -> Dict[str, Any]:
        return {
            "column": col_id,
            "title": col_ru,
            "row1": ru(config, table[col_id]["row1"]) if table[col_id]["row1"] else "—",
            "row2": ru(config, table[col_id]["row2"]) if table[col_id]["row2"] else "—",
            "row3": ru(config, table[col_id]["row3"]) if table[col_id]["row3"] else "—",
        }

    pretty_out = [
        pretty("perception", "Восприятие"),
        pretty("motivation", "Мотивация"),
        pretty("instrument", "Инструмент"),
    ]

    return {
        "version": "dialog_v1",
        "table_raw": table,
        "table_pretty": pretty_out,
        "responses_used": responses
    }
