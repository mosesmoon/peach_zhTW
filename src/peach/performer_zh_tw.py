"""女优名的繁体写法：取自 JavDB 演员页现名栏，只用于「女优名称」选繁体中文时的显示与搜索（ADR-0203）。

一条写法落两处，同一个事务里写：

- `entity_alias`：来源 `auto:performer-zh-tw-name@<批次>`，让繁体输入搜得到人（搜索、建议、FTS
  都读别名）。这个来源不算艺名来源：页头、可选艺名与两个后继的名字链都跳过它。
- JavDB 演员 id 那一行 `entity_external_ref.metadata_json`：`zh_tw`（空串表示查过、没有可用的写法）、
  `zh_tw_for`（写入时的规范名）、`zh_tw_rule`。繁体写法属于 JavDB 现名那个艺名，用户之后改选别的
  艺名当规范名，它就不再显示，别名仍可搜。

`scripts/revert_auto_landing.py --source auto:performer-zh-tw-name` 整批撤回：删别名，并清掉对应实体上的这几项。
"""
from __future__ import annotations

import json
import sqlite3

from .entities import normalize_entity_name

SOURCE = "auto:performer-zh-tw-name"
#: 判据版本；换了判据就加一，查过的 id 按新判据再查一次。
RULE = 1
_KEYS = ("zh_tw", "zh_tw_for", "zh_tw_rule")
_REF = "provider='javdb' AND external_kind='performer'"


def is_ours(source: str) -> bool:
    return source == SOURCE or source.startswith(SOURCE + "@")


def _metadata(raw) -> dict:
    try:
        value = json.loads(raw or "{}")
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _taken(connection: sqlite3.Connection, entity_id: int, key: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM entity WHERE kind='performer' AND normalized_name=? AND id<>?"
        " UNION SELECT 1 FROM entity_alias a JOIN entity e ON e.id=a.entity_id"
        " WHERE e.kind='performer' AND a.normalized_alias=? AND a.entity_id<>? LIMIT 1",
        (key, int(entity_id), key, int(entity_id))).fetchone() is not None


def checked(connection: sqlite3.Connection, entity_id: int) -> bool:
    """她名下的 JavDB 演员 id 里有没有按现行判据查过的。"""
    return any(_metadata(raw).get("zh_tw_rule") == RULE for (raw,) in connection.execute(
        f"SELECT metadata_json FROM entity_external_ref WHERE entity_id=? AND {_REF}", (int(entity_id),)))


def record(connection: sqlite3.Connection, entity_id: int, actor_id: str, writing: str,
           canonical: str, batch: str) -> str:
    """记下这个演员 id 查过了；`writing` 非空时同时登记繁体别名。返回写入的繁体写法（没写返回空串）。

    别名已被另一条女优占用时不写，按「查过、没有」记。调用方负责事务。
    """
    row = connection.execute(
        f"SELECT metadata_json FROM entity_external_ref WHERE entity_id=? AND external_id=? AND {_REF}",
        (int(entity_id), str(actor_id))).fetchone()
    if row is None:
        return ""
    key = normalize_entity_name(writing) if writing else ""
    if key and _taken(connection, entity_id, key):
        writing, key = "", ""
    metadata = {name: value for name, value in _metadata(row[0]).items() if name not in _KEYS}
    metadata.update({"zh_tw": writing, "zh_tw_rule": RULE, **({"zh_tw_for": canonical} if writing else {})})
    connection.execute(
        f"UPDATE entity_external_ref SET metadata_json=? WHERE entity_id=? AND external_id=? AND {_REF}",
        (json.dumps(metadata, ensure_ascii=False), int(entity_id), str(actor_id)))
    if writing:
        connection.execute(
            "INSERT OR IGNORE INTO entity_alias(entity_id,alias,normalized_alias,source,confidence)"
            " VALUES(?,?,?,?,0.9)", (int(entity_id), writing, key, f"{SOURCE}@{batch}"))
    return writing


def writings(connection: sqlite3.Connection, entity_id: int | None = None) -> dict[int, tuple[str, str]]:
    """{实体: (繁体写法, 写入时的规范名)}，只含查到了的；一位有几条 id 时取第一条。`entity_id` 只取这一位。"""
    found: dict[int, tuple[str, str]] = {}
    where, values = ("", ()) if entity_id is None else (" AND entity_id=?", (int(entity_id),))
    for entity_id, raw in connection.execute(
            f"SELECT entity_id,metadata_json FROM entity_external_ref WHERE {_REF}{where}"
            " ORDER BY entity_id,external_id", values):
        metadata = _metadata(raw)
        if metadata.get("zh_tw") and int(entity_id) not in found:
            found[int(entity_id)] = (str(metadata["zh_tw"]), str(metadata.get("zh_tw_for") or ""))
    return found


def shown(entry: tuple[str, str] | None, canonical: str) -> str | None:
    """要显示的繁体写法：只在规范名仍是写入时那一个时给。"""
    if entry and normalize_entity_name(entry[1]) == normalize_entity_name(canonical):
        return entry[0]
    return None


def withdraw(connection: sqlite3.Connection, entity_ids) -> int:
    """清掉这些实体 JavDB 演员 id 上记的繁体项（撤回别名时一起做），返回改了几行。"""
    changed = 0
    for entity_id in set(entity_ids):
        for external_id, raw in connection.execute(
                f"SELECT external_id,metadata_json FROM entity_external_ref WHERE entity_id=? AND {_REF}",
                (int(entity_id),)).fetchall():
            metadata = _metadata(raw)
            if not any(name in metadata for name in _KEYS):
                continue
            for name in _KEYS:
                metadata.pop(name, None)
            connection.execute(
                f"UPDATE entity_external_ref SET metadata_json=? WHERE external_id=? AND {_REF}",
                (json.dumps(metadata, ensure_ascii=False), external_id))
            changed += 1
    return changed
