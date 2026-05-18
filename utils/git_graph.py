# utils/git_graph.py
"""
Парсинг git log в структуру для отрисовки графа коммитов.
"""
import subprocess
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class CommitNode:
    sha:        str
    short_sha:  str
    message:    str
    author:     str
    date:       str
    branches:   List[str] = field(default_factory=list)  # имена веток/тегов
    parents:    List[str] = field(default_factory=list)  # sha родителей
    children:   List[str] = field(default_factory=list)  # sha детей
    # Позиция в графе
    col:        int = 0
    row:        int = 0


class GitGraph:

    # Цвета дорожек (по колонкам)
    LANE_COLORS = [
        "#1e66f5",  # синий
        "#40a02b",  # зелёный
        "#df8e1d",  # жёлтый
        "#d20f39",  # красный
        "#8839ef",  # фиолетовый
        "#04a5e5",  # голубой
        "#fe640b",  # оранжевый
        "#179299",  # бирюзовый
    ]

    @staticmethod
    def get_color(col: int) -> str:
        return GitGraph.LANE_COLORS[col % len(GitGraph.LANE_COLORS)]

    @staticmethod
    def load(path: str, max_commits: int = 200) -> List[CommitNode]:
        """
        Загружает историю коммитов через git log и возвращает список CommitNode
        с расставленными колонками (lane layout).
        """
        try:
            sep = "\x1f"
            fmt = sep.join(["%H", "%h", "%s", "%an", "%ad", "%P", "%D"])
            result = subprocess.run(
                ["git", "log",
                 f"--pretty=format:{fmt}",
                 "--date=format:%d %b %Y %H:%M",
                 "--all",
                 f"-{max_commits}"],
                cwd=path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if result.returncode != 0:
                return []

            commits: List[CommitNode] = []
            sha_index: Dict[str, int] = {}  # sha -> index in commits

            for row, line in enumerate(result.stdout.splitlines()):
                if not line.strip():
                    continue
                parts = line.split(sep)
                if len(parts) < 6:
                    continue

                sha, short, msg, author, date = parts[0], parts[1], parts[2], parts[3], parts[4]
                parents_str = parts[5] if len(parts) > 5 else ""
                refs_str    = parts[6] if len(parts) > 6 else ""

                parents = [p.strip() for p in parents_str.split() if p.strip()]

                # Разбираем ссылки (HEAD, ветки, теги)
                branches = []
                if refs_str.strip():
                    for ref in refs_str.split(","):
                        ref = ref.strip()
                        if not ref:
                            continue
                        ref = re.sub(r'^HEAD -> ', '', ref)
                        ref = re.sub(r'^tag: ', '🏷 ', ref)
                        branches.append(ref)

                node = CommitNode(
                    sha=sha, short_sha=short,
                    message=msg, author=author, date=date,
                    branches=branches, parents=parents,
                    row=row
                )
                commits.append(node)
                sha_index[sha] = row

            # Расставляем children
            for node in commits:
                for psha in node.parents:
                    if psha in sha_index:
                        commits[sha_index[psha]].children.append(node.sha)

            # Lane layout — простой жадный алгоритм
            GitGraph._assign_lanes(commits, sha_index)
            return commits

        except Exception as e:
            print(f"[git_graph] Error: {e}")
            return []

    @staticmethod
    def _assign_lanes(commits: List[CommitNode], sha_index: Dict[str, int]):
        """
        Расставляет col для каждого коммита.
        Алгоритм: каждая «живая» ветка занимает дорожку.
        """
        # lanes[col] = sha последнего коммита, который «ведёт» эту дорожку
        lanes: List[Optional[str]] = []

        def find_lane(sha: str) -> int:
            for i, s in enumerate(lanes):
                if s == sha:
                    return i
            return -1

        def free_lane() -> int:
            for i, s in enumerate(lanes):
                if s is None:
                    return i
            lanes.append(None)
            return len(lanes) - 1

        for node in commits:
            col = find_lane(node.sha)
            if col == -1:
                col = free_lane()
            node.col = col

            # Основной родитель продолжает эту дорожку
            if node.parents:
                lanes[col] = node.parents[0]
            else:
                lanes[col] = None  # конец ветки

            # Дополнительные родители (merge) открывают новые дорожки
            for extra_parent in node.parents[1:]:
                ecol = free_lane()
                lanes[ecol] = extra_parent
