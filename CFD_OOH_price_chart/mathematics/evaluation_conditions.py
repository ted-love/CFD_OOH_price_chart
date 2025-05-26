
from dataclasses import dataclass, field
from typing import Dict, List




@dataclass(slots=True, kw_only=True)
class MetricLimitations:
    metric_type: str
    selected_price_types: List[str]
    allowed_metrics: List[str]
    all_price_types: List[str]
    children_allowed: Dict[str, str] = field(default_factory=dict)
    action: Dict[str, str]
    
    def __post_init__(self):
        self.children_allowed = {metric : {} for metric in self.allowed_metrics}
        
        unavailable = []
        
        for metric_type in self.allowed_metrics:
            for price_type in self.all_price_types:
                if metric_type == self.metric_type:
                    self.children_allowed[self.metric_type] = price_type
                else:
                    if price_type in self.selected_price_types:
                        self.children_allowed[self.metric_type] = price_type
                    else:
                        unavailable.append({"metric_type" : metric_type, "price_type" : price_type})
                        
        
        
    
    
price = {"name" : "price",
        "" : {"price_type" : "underlying_price_type"},
        "failure" : {"object" : "parent",
                    "class" : "SyntheticInstrument",
                    "type" : "proxy"},
                    }







def get_conditions(metric):
    percentage = {"name" : "percentange",
                  "requires" : {"price_type" : "underlying_price_type"},
                  "failure" : {"object" : "parent",
                                "class" : "SyntheticInstrument",
                                "type" : "proxy"},
                                }

    price = {"name" : "price",
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
    return {"percentage" : percentage, "price" : price, "theo" : theo}[metric]

@dataclass(slots=True, kw_only=True)
class MetricCalculationRequrement:
    name: str 
    requires: Dict[str, str]
    failure: Dict[str, str] 




#%%












from abc import ABC, abstractmethod
from typing import Dict, List


class DerivationRule(ABC):
    @abstractmethod
    def applies_to(self, parent: Dict[str, str]) -> bool:
        pass

    @abstractmethod
    def derive(self, parent: Dict[str, str]) -> Dict[str, List[Dict[str, str]]]:
        pass


class MidPriceFromBidAskRule(DerivationRule):
    def applies_to(self, parent: Dict[str, str]) -> bool:
        return parent.get("metric_type") == "price"

    def derive(self, parent: Dict[str, str]) -> Dict[str, List[Dict[str, str]]]:
        available_types = parent.get("selected_price_types", [])
        result = {"allowed": [], "missing": []}

        if "bid" in available_types and "ask" in available_types:
            result["allowed"].append({
                "metric_type": "price",
                "price_type": "mid",
                "source": "derived from bid+ask"
            })
        else:
            missing = [pt for pt in ["bid", "ask"] if pt not in available_types]
            result["missing"].append({
                "metric_type": "price",
                "price_type": "mid",
                "reason": "requires bid and ask",
                "missing": missing
            })

        return result


class PercentageRequiresPriceRule(DerivationRule):
    def applies_to(self, parent: Dict[str, str]) -> bool:
        return parent.get("metric_type") == "price"

    def derive(self, parent: Dict[str, str]) -> Dict[str, List[Dict[str, str]]]:
        available_types = parent.get("selected_price_types", [])
        result = {"allowed": [], "missing": []}

        for pt in parent.get("all_price_types", []):
            if pt in available_types:
                result["allowed"].append({
                    "metric_type": "percentage",
                    "underlying_price_type": pt,
                    "source": "direct"
                })
            else:
                result["missing"].append({
                    "metric_type": "percentage",
                    "underlying_price_type": pt,
                    "reason": "missing underlying_price_type"
                })

        return result


class TheoRequiresPercentageRule(DerivationRule):
    def applies_to(self, parent: Dict[str, str]) -> bool:
        return parent.get("metric_type") == "percentage"

    def derive(self, parent: Dict[str, str]) -> Dict[str, List[Dict[str, str]]]:
        result = {"allowed": [], "missing": []}

        for pt in parent.get("all_price_types", []):
            if pt in parent.get("selected_price_types", []):
                result["allowed"].append({
                    "metric_type": "theo",
                    "underlying_price_type": pt,
                    "source": "allowed"
                })
            else:
                result["missing"].append({
                    "metric_type": "theo",
                    "underlying_price_type": pt,
                    "reason": "missing underlying_price_type"
                })

        return result

class DerivationEngine:
    def __init__(self, rules: List[DerivationRule]):
        self.rules = rules

    def evaluate(self, parent_info: Dict[str, str]) -> Dict[str, List[Dict[str, str]]]:
        all_allowed = []
        all_missing = []

        for rule in self.rules:
            if rule.applies_to(parent_info):
                result = rule.derive(parent_info)
                all_allowed.extend(result["allowed"])
                all_missing.extend(result["missing"])

        return {"allowed": all_allowed, "missing": all_missing}



parent = {
    "metric_type": "percentage",
    "selected_price_types": ["bid", "ask"], 
    "all_price_types": ["mid", "bid", "ask"]
}

engine = DerivationEngine([
    MidPriceFromBidAskRule(),
    PercentageRequiresPriceRule(),
    TheoRequiresPercentageRule()
])

from pprint import pprint
pprint(engine.evaluate(parent))






#%%


# Fixing missing imports
from abc import ABC, abstractmethod

# Re-run the same logic now that ABC is imported
class DerivationRule(ABC):
    @abstractmethod
    def applies_to(self, parent: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def derive(self, parent: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        pass


class MidPriceFromBidAskRule(DerivationRule):
    def applies_to(self, parent: Dict[str, Any]) -> bool:
        return parent.get("metric_type") in {"price", "percentage"}

    def derive(self, parent: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        available_types = parent.get("selected_price_types", [])
        result = {"allowed": [], "missing": []}

        if "bid" in available_types and "ask" in available_types:
            result["allowed"].append({
                "metric_type": "price",
                "price_type": "mid",
                "source": "derived from bid+ask"
            })
        else:
            missing = [pt for pt in ["bid", "ask"] if pt not in available_types]
            result["missing"].append({
                "metric_type": "price",
                "price_type": "mid",
                "reason": "requires bid and ask",
                "missing": missing
            })

        return result


class PercentageRequiresPriceRule(DerivationRule):
    def applies_to(self, parent: Dict[str, Any]) -> bool:
        return parent.get("metric_type") == "price"

    def derive(self, parent: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        available_types = parent.get("selected_price_types", [])
        result = {"allowed": [], "missing": []}

        for pt in parent.get("all_price_types", []):
            if pt in available_types:
                result["allowed"].append({
                    "metric_type": "percentage",
                    "underlying_price_type": pt,
                    "source": "direct"
                })
            else:
                result["missing"].append({
                    "metric_type": "percentage",
                    "underlying_price_type": pt,
                    "reason": "missing underlying_price_type"
                })

        return result


class TheoRequiresPercentageRule(DerivationRule):
    def applies_to(self, parent: Dict[str, Any]) -> bool:
        return parent.get("metric_type") == "percentage"

    def derive(self, parent: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        result = {"allowed": [], "missing": []}
        for pt in parent.get("all_price_types", []):
            if pt in parent.get("selected_price_types", []):
                result["allowed"].append({
                    "metric_type": "theo",
                    "underlying_price_type": pt,
                    "source": "allowed"
                })
            else:
                result["missing"].append({
                    "metric_type": "theo",
                    "underlying_price_type": pt,
                    "reason": "missing underlying_price_type"
                })
        return result


class DerivationEngine:
    def __init__(self, rules: List[DerivationRule]):
        self.rules = rules

    def evaluate(self, parent_info: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        all_allowed = []
        all_missing = []

        for rule in self.rules:
            if rule.applies_to(parent_info):
                result = rule.derive(parent_info)
                all_allowed.extend(result["allowed"])
                all_missing.extend(result["missing"])

        return {"allowed": all_allowed, "missing": all_missing}



parent = {
    "metric_type": "percentage",
    "selected_price_types": ["bid", "ask"],
    "all_price_types": ["mid", "bid", "ask"]
}

engine = DerivationEngine([
    MidPriceFromBidAskRule(),
    PercentageRequiresPriceRule(),
    TheoRequiresPercentageRule()
])

initial_results = engine.evaluate(parent)

# Proxy logic: simulate if we can resolve missing 'theo + mid' by checking if percentage + mid is derivable
proxy_parent = {
    "metric_type": "price",
    "selected_price_types": ["bid", "ask"],
    "all_price_types": ["mid", "bid", "ask"]
}
proxy_result = engine.evaluate(proxy_parent)

# Can we resolve the missing "theo with mid"?
missing_theo_mid = {
    "metric_type": "theo",
    "underlying_price_type": "mid"
}

derived_percentage_mid = any(
    item for item in proxy_result["allowed"]
    if item.get("metric_type") == "percentage" and item.get("underlying_price_type") == "mid"
)

if derived_percentage_mid:
    resolution = {
        **missing_theo_mid,
        "resolution": "derive percentage with mid from bid/ask then derive theo",
        "proxy_steps": proxy_result["allowed"]
    }
else:
    resolution = missing_theo_mid

resolution, initial_results, proxy_result
#%%

metric_equation = "100 * (p2/p1 - 1)"
price_type_equation = "(b+a)/2"

metric_string = "percentage"
price_type = "mid"
epic="HK50"




stringyfied = ""
