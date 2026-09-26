import re
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = None


class NLPParser:
    def __init__(self):
        self.state_list = [
            "Maharashtra", "UP", "Uttar Pradesh", "Bihar", "Rajasthan",
            "MP", "Madhya Pradesh", "Delhi", "Gujarat", "Karnataka",
            "Tamil Nadu", "Kerala", "West Bengal", "Punjab", "Haryana"
        ]
        self.occupation_list = [
            "Farmer", "Student", "Business", "Vendor", "Street Vendor",
            "Artisan", "Craftsman", "Carpenter", "Blacksmith", "Potter",
            "Teacher", "Driver", "Worker", "Self-employed"
        ]
    
    def parse(self, text: str) -> dict:
        """Extract user profile from natural language"""
        text_lower = text.lower()
        profile = {}
        
        # ---------- Extract Age ----------
        age_patterns = [
            r'(\d{1,3})\s*(?:year|yr|years|yrs)\s*(?:old)?',
            r'age\s*(?:is\s*)?(\d{1,3})',
            r'i\s*am\s*(\d{1,3})',
        ]
        for pattern in age_patterns:
            age_match = re.search(pattern, text_lower)
            if age_match:
                age = int(age_match.group(1))
                if 1 <= age <= 100:
                    profile["age"] = age
                    break
        
        # ---------- Extract Income (improved) ----------
        income_patterns = [
            r'income\s+(?:of\s+)?(?:rs\.?\s*)?(\d+(?:\.\d+)?)\s*(lakh|lac|lakhs|lacs|k|thousand)?',
            r'(\d+(?:\.\d+)?)\s*(lakh|lac|lakhs|lacs)',
            r'earning\s+(?:rs\.?\s*)?(\d+(?:\.\d+)?)\s*(lakh|lac|lakhs|lacs|k|thousand)?',
            r'(?:rs\.?|₹)\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        ]
        for pattern in income_patterns:
            income_match = re.search(pattern, text_lower)
            if income_match:
                amount_str = income_match.group(1).replace(',', '')
                amount = float(amount_str)
                unit = income_match.group(2) if len(income_match.groups()) > 1 else None
                
                if unit in ["lakh", "lac", "lakhs", "lacs"]:
                    amount = amount * 100000
                elif unit in ["k", "thousand"]:
                    amount = amount * 1000
                
                if amount >= 10000:
                    profile["annual_income"] = amount
                    break
        
        # ---------- Extract State ----------
        for state in self.state_list:
            if state.lower() in text_lower:
                if state == "UP":
                    profile["state"] = "Uttar Pradesh"
                elif state == "MP":
                    profile["state"] = "Madhya Pradesh"
                else:
                    profile["state"] = state
                break
        
        # ---------- Extract Gender ----------
        if "female" in text_lower or "woman" in text_lower or "girl" in text_lower:
            profile["gender"] = "Female"
        elif "male" in text_lower or "man" in text_lower or "boy" in text_lower:
            profile["gender"] = "Male"
        
        # ---------- Extract Occupation ----------
        for occ in self.occupation_list:
            if occ.lower() in text_lower:
                profile["occupation"] = occ
                break
        
        # ---------- Extract Land Owner ----------
        if "land owner" in text_lower or "landowner" in text_lower or "own land" in text_lower:
            profile["land_owner"] = True
        elif "no land" in text_lower or "don't own land" in text_lower:
            profile["land_owner"] = False
        
        return profile