# app/services/states_service.py

INDIAN_STATES = {
    "01": "Jammu and Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "25": "Daman and Diu",
    "26": "Dadra and Nagar Haveli and Daman and Diu",
    "27": "Maharashtra",
    "28": "Andhra Pradesh",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman and Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh",
}


# ============================================================
# STATE ABBREVIATIONS
# ============================================================

STATE_ALIASES = {
    "jk": "Jammu and Kashmir",
    "j&k": "Jammu and Kashmir",

    "hp": "Himachal Pradesh",
    "pb": "Punjab",
    "ch": "Chandigarh",
    "uk": "Uttarakhand",
    "ua": "Uttarakhand",
    "hr": "Haryana",
    "dl": "Delhi",
    "rj": "Rajasthan",
    "up": "Uttar Pradesh",
    "br": "Bihar",
    "sk": "Sikkim",
    "ar": "Arunachal Pradesh",
    "nl": "Nagaland",
    "mn": "Manipur",
    "mz": "Mizoram",
    "tr": "Tripura",
    "ml": "Meghalaya",
    "as": "Assam",
    "wb": "West Bengal",
    "jh": "Jharkhand",
    "od": "Odisha",
    "or": "Odisha",
    "cg": "Chhattisgarh",
    "mp": "Madhya Pradesh",
    "gj": "Gujarat",
    "guj": "Gujarat",
    "mh": "Maharashtra",
    "ap": "Andhra Pradesh",
    "ka": "Karnataka",
    "ga": "Goa",
    "kl": "Kerala",
    "tn": "Tamil Nadu",
    "py": "Puducherry",
    "ts": "Telangana",
    "tg": "Telangana",
    "ld": "Lakshadweep",
    "la": "Ladakh",
    "an": "Andaman and Nicobar Islands",
    "dn": "Dadra and Nagar Haveli and Daman and Diu",
}


# ============================================================
# MAJOR CITY → STATE MAP
# ============================================================

CITY_TO_STATE = {
    # Maharashtra
    "mumbai": "Maharashtra",
    "pune": "Maharashtra",
    "nagpur": "Maharashtra",
    "nashik": "Maharashtra",
    "navi mumbai": "Maharashtra",
    "thane": "Maharashtra",
    "aurangabad": "Maharashtra",
    "chhatrapati sambhajinagar": "Maharashtra",
    "kolhapur": "Maharashtra",
    "solapur": "Maharashtra",
    "satara": "Maharashtra",
    "sangli": "Maharashtra",
    "ahmednagar": "Maharashtra",
    "jalgaon": "Maharashtra",
    "amravati": "Maharashtra",

    # Karnataka
    "bengaluru": "Karnataka",
    "bangalore": "Karnataka",
    "mysore": "Karnataka",
    "mysuru": "Karnataka",
    "mangalore": "Karnataka",
    "hubli": "Karnataka",
    "belgaum": "Karnataka",
    "belagavi": "Karnataka",

    # Gujarat
    "ahmedabad": "Gujarat",
    "surat": "Gujarat",
    "vadodara": "Gujarat",
    "baroda": "Gujarat",
    "rajkot": "Gujarat",
    "gandhinagar": "Gujarat",
    "bhavnagar": "Gujarat",

    # Tamil Nadu
    "chennai": "Tamil Nadu",
    "coimbatore": "Tamil Nadu",
    "madurai": "Tamil Nadu",
    "salem": "Tamil Nadu",
    "tiruchirappalli": "Tamil Nadu",
    "trichy": "Tamil Nadu",
    "tiruppur": "Tamil Nadu",

    # Telangana
    "hyderabad": "Telangana",
    "warangal": "Telangana",

    # Andhra Pradesh
    "visakhapatnam": "Andhra Pradesh",
    "vizag": "Andhra Pradesh",
    "vijayawada": "Andhra Pradesh",
    "tirupati": "Andhra Pradesh",
    "guntur": "Andhra Pradesh",

    # Delhi
    "new delhi": "Delhi",
    "delhi": "Delhi",

    # Haryana
    "gurgaon": "Haryana",
    "gurugram": "Haryana",
    "faridabad": "Haryana",
    "panipat": "Haryana",
    "ambala": "Haryana",

    # Uttar Pradesh
    "lucknow": "Uttar Pradesh",
    "kanpur": "Uttar Pradesh",
    "noida": "Uttar Pradesh",
    "greater noida": "Uttar Pradesh",
    "agra": "Uttar Pradesh",
    "varanasi": "Uttar Pradesh",
    "prayagraj": "Uttar Pradesh",
    "allahabad": "Uttar Pradesh",
    "meerut": "Uttar Pradesh",

    # Rajasthan
    "jaipur": "Rajasthan",
    "jodhpur": "Rajasthan",
    "udaipur": "Rajasthan",
    "kota": "Rajasthan",
    "ajmer": "Rajasthan",

    # Madhya Pradesh
    "bhopal": "Madhya Pradesh",
    "indore": "Madhya Pradesh",
    "gwalior": "Madhya Pradesh",
    "jabalpur": "Madhya Pradesh",

    # West Bengal
    "kolkata": "West Bengal",
    "howrah": "West Bengal",
    "siliguri": "West Bengal",

    # Kerala
    "kochi": "Kerala",
    "cochin": "Kerala",
    "thiruvananthapuram": "Kerala",
    "trivandrum": "Kerala",
    "kozhikode": "Kerala",

    # Punjab
    "amritsar": "Punjab",
    "ludhiana": "Punjab",
    "jalandhar": "Punjab",
    "patiala": "Punjab",

    # Bihar
    "patna": "Bihar",
    "gaya": "Bihar",
    "muzaffarpur": "Bihar",

    # Odisha
    "bhubaneswar": "Odisha",
    "cuttack": "Odisha",
    "rourkela": "Odisha",

    # Jharkhand
    "ranchi": "Jharkhand",
    "jamshedpur": "Jharkhand",
    "dhanbad": "Jharkhand",

    # Assam
    "guwahati": "Assam",

    # Goa
    "panaji": "Goa",
    "panjim": "Goa",

    # Chhattisgarh
    "raipur": "Chhattisgarh",
    "bilaspur": "Chhattisgarh",

    # Uttarakhand
    "dehradun": "Uttarakhand",
    "haridwar": "Uttarakhand",

    # Himachal Pradesh
    "shimla": "Himachal Pradesh",
    "manali": "Himachal Pradesh",

    # Jammu and Kashmir
    "srinagar": "Jammu and Kashmir",
    "jammu": "Jammu and Kashmir",

    # Puducherry
    "pondicherry": "Puducherry",
    "puducherry": "Puducherry",

    # Sikkim
    "gangtok": "Sikkim",
}


def get_state_by_code(code: str) -> str | None:
    """
    Return state/UT name for a GST state code.
    """
    if not code:
        return None

    code = str(code).strip().zfill(2)

    return INDIAN_STATES.get(code)


def get_code_by_state(state_name: str) -> str | None:
    """
    Return GST state code for a state/UT name.
    """
    if not state_name:
        return None

    normalized = state_name.strip().lower()

    for code, name in INDIAN_STATES.items():
        if name.lower() == normalized:
            return code

    return None


def get_state_by_alias(value: str) -> str | None:
    """
    Convert a state abbreviation/alias into a full state name.

    Examples:
        MH -> Maharashtra
        mh -> Maharashtra
        KA -> Karnataka
        TS -> Telangana
    """
    if not value:
        return None

    normalized = str(value).strip().casefold()

    return STATE_ALIASES.get(normalized)


def get_state_by_city(city: str) -> str | None:
    """
    Return the state for a known Indian city.

    Matching is case-insensitive.
    """
    if not city:
        return None

    normalized = str(city).strip().casefold()

    return CITY_TO_STATE.get(normalized)


def resolve_state(value: str) -> str | None:
    """
    Resolve a user-entered state value.

    Supports:
        - Full state name
        - State abbreviation
        - Common alias

    Examples:
        MH -> Maharashtra
        mh -> Maharashtra
        Maharashtra -> Maharashtra
    """
    if not value:
        return None

    normalized = str(value).strip()

    # Check abbreviation/alias first.
    alias_result = get_state_by_alias(normalized)
    if alias_result:
        return alias_result

    # Check complete state names.
    normalized_lower = normalized.casefold()

    for name in INDIAN_STATES.values():
        if name.casefold() == normalized_lower:
            return name

    return None


def is_valid(state_name: str) -> bool:
    """
    Check whether a state/UT name exists in the state list.
    """
    return resolve_state(state_name) is not None


def state_from_gstin(gstin: str) -> str | None:
    """
    Extract the state/UT from a GSTIN.

    The first two characters of a GSTIN represent
    the GST state code.
    """
    if not gstin:
        return None

    gstin = str(gstin).strip().upper()

    if len(gstin) < 2:
        return None

    state_code = gstin[:2]

    return get_state_by_code(state_code)