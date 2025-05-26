#%%
from __future__ import annotations
from typing import List, Dict, Union, Any, Tuple, Callable, TYPE_CHECKING
from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass(slots=True, kw_only=True)
class MetricCalculationRequrement:
    name: str 
    requires: Dict[str, str]
    failure: Dict[str, str] 


p = MetricCalculationRequrement("percentange",
                                {"price_type" : "underlying_price_type"},
                                {"object" : "parent",
                                 "class" : "SyntheticInstrument",
                                 "type" : "proxy"},
                                )

def get_metric_requirements():
    percentage = {"name" : "percentange",
                  "requires" : {"price_type" : "underlying_price_type"},
                  "failure" : {"object" : "parent",
                                "class" : "SyntheticInstrument",
                                "type" : "proxy"},
                                }

    percentage = {"name" : "price",
                  "requires" : {"price_type" : "underlying_price_type"},
                  "failure" : {"object" : "parent",
                                "class" : "SyntheticInstrument",
                                "type" : "proxy"},
                                }

    theo = {"name" : "theo",
                  "requires" : {"metric_type" : "percentange"},
                  "failure" : {"object" : "parent",
                                "class" : "SyntheticInstrument",
                                "type" : "proxy"},
                                }


def synthetic_items_requirement_logic(child_information: Dict[str, str]) -> Dict[str, Any]:
    parent_requirements = {}

    child_metric = child_information["metric_type"]
    
    match child_metric:
        case "price":
            requirement = {"metric_type": "price", 
                           "price_type": child_information["price_type"]
                            }


    if child_information["metric_type"] == "price":
        requirement = {
            "metric_type": "price",
            "price_type": child_information["price_type"]
        }
        parent_requirements["price_requirement"] = {
            "requirement": requirement,
            "failure": [
                {
                    "object": "parent",
                    "reason": "Parent must be a price metric with matching price_type",
                    "expected_price_type": child_information["price_type"]
                }
            ]
        }

    elif child_information["metric_type"] == "percentage":
        requirement = {
            "metric_type": "price",
            "price_type": child_information["underlying_price_type"]
        }
        parent_requirements["percentage_requirement"] = {
            "requirement": requirement,
            "failure": [
                {
                    "object": "parent",
                    "reason": "Parent must be a price metric with price_type equal to underlying_price_type",
                    "expected_price_type": child_information["underlying_price_type"]
                }
            ]
        }

    elif child_information["metric_type"] == "theo":
        requirement = {
            "metric_type": "percentage",
            "price_type": child_information["underlying_price_type"]
        }
        parent_requirements["theo_requirement"] = {
            "requirement": requirement,
            "failure": [
                {
                    "object": "parent",
                    "reason": "Parent must be a percentage metric with price_type equal to the underlying price type",
                    "expected_price_type": child_information["underlying_price_type"]
                }
            ]
        }

    return parent_requirements
#%%


from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass(slots=True)
class MetricRequirement:
    name: str
    requires: Dict[str, str]  
    failure: Dict[str, str]   # What to report on failure


def check_requirements(child: Dict[str, str],
                       parent: Dict[str, str],
                       requirements: List[MetricRequirement]) -> Dict[str, Any]:

    unmet_requirements = {}

    for req in requirements:
        for key, required_key in req.requires.items():
            expected_value = child.get(required_key)

            if parent.get(key) != expected_value:
                unmet_requirements[req.name] = {
                    "requirement": {key: expected_value},
                    "failure": {
                        **req.failure,
                        "expected": expected_value,
                        "actual": parent.get(key)
                    }
                }

    return unmet_requirements


child_info = {
    "metric_type": "percentage",
    "underlying_price_type": "mid"
}

parent_info = {
    "metric_type": "price",
    "price_type": "bid"
}

requirements = [
    MetricRequirement(
        name="PercentageMetricNeedsPriceType",
        requires={"price_type": "underlying_price_type"},   
        failure={"object": "parent", "reason": "Child's underlying_price_type must match parent's price_type"}
    )
]

failures = check_requirements(child_info, parent_info, requirements)

from pprint import pprint
pprint(failures)
