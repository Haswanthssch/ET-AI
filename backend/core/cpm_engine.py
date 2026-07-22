"""
AURA-EPC NetworkX Critical Path Method (CPM) Engine
Builds and queries a directed acyclic graph representing the 24-month
datacenter EPC schedule. Identifies critical path, float, and the cascading
impact of supply chain delays.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd


@dataclass
class TaskNode:
    task_id: str
    name: str
    duration: int          # working days
    predecessors: list[str]
    es: int = 0            # Early Start
    ef: int = 0            # Early Finish
    ls: int = 0            # Late Start
    lf: int = 0            # Late Finish
    float_days: int = 0
    is_critical: bool = False
    phase: str = ""
    equipment_tag: str = ""


class CPMEngine:
    """
    Wraps a NetworkX DiGraph for Critical Path Method calculations.
    Loaded from master_schedule.csv.
    """

    def __init__(self, schedule_csv_path: str | Path):
        self.path = Path(schedule_csv_path)
        self.graph = nx.DiGraph()
        self._tasks: dict[str, TaskNode] = {}
        self._critical_path: list[str] = []
        self._loaded = False

    def load(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"Schedule CSV not found: {self.path}")
        df = pd.read_csv(self.path)
        for _, row in df.iterrows():
            predecessors = (
                [p.strip() for p in str(row["predecessors"]).split(",") if p.strip() and p.strip() != "nan"]
                if pd.notna(row.get("predecessors")) and str(row.get("predecessors")) != "nan"
                else []
            )
            task = TaskNode(
                task_id=str(row["task_id"]),
                name=str(row["task_name"]),
                duration=int(row["duration_days"]),
                predecessors=predecessors,
                phase=str(row.get("phase", "")),
                equipment_tag=str(row.get("equipment_tag", "")),
            )
            self._tasks[task.task_id] = task
            self.graph.add_node(task.task_id, **task.__dict__)

        for task in self._tasks.values():
            for pred in task.predecessors:
                if pred in self._tasks:
                    self.graph.add_edge(pred, task.task_id)

        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Schedule graph contains cycles — invalid CPM input.")

        self._forward_pass()
        self._backward_pass()
        self._compute_float_and_critical()
        self._loaded = True

    # ------------------------------------------------------------------
    # CPM Passes
    # ------------------------------------------------------------------
    def _forward_pass(self) -> None:
        for node_id in nx.topological_sort(self.graph):
            task = self._tasks[node_id]
            predecessors = list(self.graph.predecessors(node_id))
            if not predecessors:
                task.es = 0
            else:
                task.es = max(self._tasks[p].ef for p in predecessors)
            task.ef = task.es + task.duration

    def _backward_pass(self) -> None:
        project_end = max(t.ef for t in self._tasks.values())
        for node_id in reversed(list(nx.topological_sort(self.graph))):
            task = self._tasks[node_id]
            successors = list(self.graph.successors(node_id))
            if not successors:
                task.lf = project_end
            else:
                task.lf = min(self._tasks[s].ls for s in successors)
            task.ls = task.lf - task.duration

    def _compute_float_and_critical(self) -> None:
        self._critical_path = []
        for task in self._tasks.values():
            task.float_days = task.ls - task.es
            task.is_critical = task.float_days == 0
            if task.is_critical:
                self._critical_path.append(task.task_id)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_critical_path(self) -> list[str]:
        return self._critical_path

    def get_task(self, task_id: str) -> TaskNode | None:
        return self._tasks.get(task_id)

    def apply_delay(self, task_id: str, delay_days: int) -> dict[str, Any]:
        """
        Simulate the impact of a delay on a task. Returns cascade info.
        """
        task = self._tasks.get(task_id)
        if not task:
            return {"error": f"Task {task_id} not found"}

        impacted = list(nx.descendants(self.graph, task_id))
        critical_impact = [t for t in impacted if self._tasks[t].is_critical]
        project_slip = delay_days if task.is_critical else max(0, delay_days - task.float_days)

        return {
            "task_id": task_id,
            "task_name": task.name,
            "delay_days": delay_days,
            "project_slip_days": project_slip,
            "total_impacted_tasks": len(impacted),
            "critical_path_impacted_tasks": len(critical_impact),
            "is_on_critical_path": task.is_critical,
            "float_available": task.float_days,
            "sample_impacted": [
                {"id": t, "name": self._tasks[t].name} for t in critical_impact[:5]
            ],
        }

    def get_summary(self) -> dict[str, Any]:
        all_tasks = list(self._tasks.values())
        project_end = max(t.ef for t in all_tasks)
        return {
            "total_tasks": len(all_tasks),
            "critical_path_tasks": len(self._critical_path),
            "project_duration_days": project_end,
            "project_duration_months": round(project_end / 21, 1),
        }

    def to_dict(self) -> list[dict[str, Any]]:
        return [
            {
                "task_id": t.task_id,
                "name": t.name,
                "phase": t.phase,
                "duration": t.duration,
                "es": t.es,
                "ef": t.ef,
                "float": t.float_days,
                "is_critical": t.is_critical,
                "equipment_tag": t.equipment_tag,
            }
            for t in self._tasks.values()
        ]


# Module-level singleton — loaded lazily on first use
_engine: CPMEngine | None = None


def get_cpm_engine(csv_path: str = "./data/master_schedule.csv") -> CPMEngine:
    global _engine
    if _engine is None or not _engine._loaded:
        _engine = CPMEngine(csv_path)
        _engine.load()
    return _engine

