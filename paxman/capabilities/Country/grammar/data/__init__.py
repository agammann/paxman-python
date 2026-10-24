"""Country grammar recognition key sets.

Each module exports a frozenset of syntax-normalized name representation
keys for recognition. The key sets contain no token-to-country mappings —
validation rules own every token-to-country decision.

Locales: english_names.py (ISO 3166-1 English), historical_names.py
(ISO 3166-3 former names), chinese_names.py (CLDR zh), localized_names.py
(CLDR zh/es/fr — the full current CLDR spelling catalog).

Code locales: alpha2_codes.py (ISO 3166-1 alpha-2 plus the ISO 3166-3
former codes), alpha3_codes.py (ISO 3166-1 alpha-3), numeric_codes.py
(ISO 3166-1 M49 numeric plus the retired M49 codes).

New locale files can be added here and imported in name_recognition.py.
"""
