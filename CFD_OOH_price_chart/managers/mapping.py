from __future__ import annotations
from typing import Callable, Sequence, List, Dict, NoReturn, Union, Tuple, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from timeseries.classes import TimeSeriesContainer, TimeSeries
    from instruments.classes import InstrumentContainer, PriceInstrument, SyntheticInstrument
    from managers.classes import SeriesManager
from dataclasses import dataclass, field, InitVar, replace



class ParentCollectiontoChild:
    def __init__(self):
        self._map: Dict[Tuple[float, ...], float] = {}

    def add(self, parent_id: List[float], child_id: float):
        key = tuple(sorted(p for p in parent_id))
        self._map[key] = child_id

    def get(self, parent_id: List[float]):
        key = tuple(sorted(p for p in parent_id))
        return self._map.get(key)


class MappingEngine:
    def __init__(self):
        self._id_map: Dict[Tuple[float, ...], List[float]] = {}
        self._child_metadata_map: Dict[float, Dict[str, Union[float, str]]] = {}
        self._timestamp_metric_index: Dict[Tuple[float, str], List[float]] = {}
        self._child_to_parents: Dict[float, List[float]] = {}
        self._full_lookup_index: Dict[Tuple[float, str, str], float] = {}

    def _key(self, parent_ids: List[float]) -> Tuple[float, ...]:
        return tuple(sorted(parent_ids))

    def add(self,
            parents: List[SeriesManager] | SeriesManager,
            child: SeriesManager):
        if isinstance(parents, list):
            parent_ids = [p.internal_name for p in parents]
        else:
            parent_ids = [parents.internal_name]
        print(f"\n{parent_ids}")
        child_id = child.internal_name

        key = self._key(parent_ids)
        self._id_map.setdefault(key, []).append(child_id)

        metadata = {
            "timestamp_filters": child.timestamp_filters,
            "metric_type": child.metric_type,
            "name": child.name
        }
        self._child_metadata_map[child_id] = metadata
        
        tm_key = (child.timestamp_filters, child.metric_type)
        print(f"tm_key{ tm_key}")
        self._timestamp_metric_index.setdefault(tm_key, []).append(child_id)

        self._child_to_parents[child_id] = parent_ids

        self._full_lookup_index[(child.timestamp_filters, child.metric_type, child.name)] = child_id

    def get_ids_by_params(
        self,
        timestamp: float = None,
        metric_type: str = None,
        name: str = None
    ) -> List[float]:
        """Return all internal_names matching any combination of parameters."""
        results = []
        for child_id, metadata in self._child_metadata_map.items():
            if timestamp is not None and metadata["timestamp_filters"] != timestamp:
                continue
            if metric_type is not None and metadata["metric_type"] != metric_type:
                continue
            if name is not None and metadata["name"] != name:
                continue
            results.append(child_id)
        return results

    def get_children_ids(self, parents: List) -> List[float]:
        parent_ids = [p.internal_name for p in parents]
        key = self._key(parent_ids)
        return self._id_map.get(key, [])

    def has_child(self, parents: List) -> bool:
        parent_ids = [p.internal_name for p in parents]
        return self._key(parent_ids) in self._id_map

    def get_ids_by_timestamp_metric(self, timestamp: float, metric_type: str) -> List[float]:
        return self._timestamp_metric_index.get((timestamp, metric_type), [])

    def get_child_metadata(self, child_id: float) -> Dict[str, Union[float, str]]:
        return self._child_metadata_map.get(child_id, {})

    def get_parents_of_child(self, child_id: float) -> List[float]:
        return self._child_to_parents.get(child_id, [])

    def get_all_children(self) -> List[float]:
        return list(self._child_metadata_map.keys())

    def get_id_by_all_params(
        self,
        timestamp: float = None,
        metric_type: str = None,
        name: str = None
    ) -> Union[float, None]:
        for child_id, metadata in self._child_metadata_map.items():
            if timestamp is not None and metadata["timestamp_filters"] != timestamp:
                continue
            if metric_type is not None and metadata["metric_type"] != metric_type:
                continue
            if name is not None and metadata["name"] != name:
                continue
            return child_id
        return None

    def get_metadata_by_all_params(
        self,
        timestamp: float = None,
        metric_type: str = None,
        name: str = None
    ) -> Dict[str, Union[float, str]]:
        obj_id = self.get_id_by_all_params(timestamp, metric_type, name)
        if obj_id is not None:
            return self.get_child_metadata(obj_id)
        return {}


#%%
"""

mapper = MappingEngine()

parent1 = Stock("AAPL_0", 1, datetime.now().timestamp_filters(), "price")
parent11 = Stock("AAPL", np.array([2.0, 3.0]), datetime.now().timestamp_filters(), "price ")
parent2 = Stock("MSFT_0", 1.5, datetime.now().timestamp_filters(), "price")
parent22 = Stock("MSFT", np.array([3.0, 4.0]), datetime.now().timestamp_filters(), "price")
parents1 = [parent1, parent11]
parents2 = [parent2, parent22]




child2 = Stock.from_parent(
                            parents=parents2,
                            name="MSFT",
                            timestamp=datetime.now().timestamp_filters(),
                            metric_type="pct_change",
                            operator=returns
)

child1 = Stock.from_parent(
    parents=parents1,
    name="AAPL",  # Corrected name
    timestamp=datetime.now().timestamp_filters(),
    metric_type="pct_change",
    operator=returns
)

child11 = Stock.from_parent(
    parents=parents1,
    name="AAPL",  # Corrected name
    timestamp=datetime.now().timestamp_filters()+1,
    metric_type="pct_change",
    operator=returns
)

mapper.add(parents1, child1)
mapper.add(parents2, child11)
mapper.add(parents2, child2)

theo_parents = [child1, child2]

theo = Stock.from_parent(
    parents=theo_parents,
    name="THEO",
    timestamp=datetime.now().timestamp_filters(),
    metric_type="diff",
    operator=Diff(child1.name, child2.name),
)

mapper.add(theo_parents, theo)
#%%
# All children with name = "AAPL"
ids = mapper.get_ids_by_params(name="AAPL")
print(ids)  # Expecting multiple IDs here

ids = mapper.get_ids_by_params(name="AAPL", metric_type="pct_change")
print(ids)

# All children with just timestamp filter
ids = mapper.get_ids_by_params(timestamp=child1.timestamp_filters)
print(ids)



"""