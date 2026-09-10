import json
from typing import Dict, List, Any
from ..models.scheme import Scheme, UserProfile

class RuleEngine:
    def __init__(self, rules_file_path: str):
        with open(rules_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.schemes_data = data.get('schemes', [])
    
    def evaluate_rule(self, rule, user_value: Any) -> bool:
        op = rule.operator
        if op == "between":
            return rule.min <= user_value <= rule.max
        elif op == "<=":
            return user_value <= rule.value
        elif op == ">=":
            return user_value >= rule.value
        elif op == "==":
            return user_value == rule.value
        elif op == "!=":
            return user_value != rule.value
        elif op == "in":
            return user_value in rule.values
        return False
    
    def check_eligibility(self, scheme: Scheme, user: UserProfile) -> Dict:
        results = []
        all_passed = True
        
        for rule in scheme.rules:
            user_value = getattr(user, rule.field, None)
            if user_value is None:
                all_passed = False
                results.append({
                    "field": rule.field,
                    "passed": False,
                    "reason": "Field not provided",
                    "actual": None
                })
                continue
            
            passed = self.evaluate_rule(rule, user_value)
            all_passed = all_passed and passed
            
            results.append({
                "field": rule.field,
                "passed": passed,
                "condition": f"{rule.field} {rule.operator} {rule.value if rule.value else f'{rule.min}-{rule.max}'}",
                "actual": user_value
            })
        
        return {
            "scheme_id": scheme.scheme_id,
            "scheme_name": scheme.name,
            "eligible": all_passed,
            "match_percentage": 100 if all_passed else 0,
            "checks": results,
            "source": scheme.source_url,
            "documents_required": scheme.documents_required,
            "benefits": scheme.benefits
        }
    
    def find_eligible_schemes(self, user: UserProfile) -> List[Dict]:
        eligible = []
        for scheme_data in self.schemes_data:
            scheme = Scheme(**scheme_data)
            result = self.check_eligibility(scheme, user)
            if result["eligible"]:
                eligible.append(result)
        return eligible