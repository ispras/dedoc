import re

# item parse \d
regexps_item = re.compile(r"^\s*\d+\.\s")
regexps_foiv_item = re.compile(r"^\s*(\d+\.)+\s*")
regexps_item_with_bracket = re.compile(r"^\s*(\d*\.)*\d+[)}]")
regexps_digits_with_dots = re.compile(r"^\s*(\d+\.)+(\d+)?\s*")

# subitem parse [а-яё]
regexps_subitem_with_dots = re.compile(r"^\s*((\d+\.((\d+|[а-яё])\.)+)|[а-яё][.)])\s")
regexps_subitem_extended = re.compile(r"^\s*[A-ZА-Яa-zа-яё][)}.]")
regexps_subitem = re.compile(r"^\s*[а-яё][)}]")

# number
regexps_number = re.compile(r"(^\s*\d{1,2}(\.\d{1,2})*)(\s|$|\)|\}|\.([A-ZА-Яa-zа-яё]|\s))")
regexps_ends_of_number = re.compile(r"([A-ZА-Яa-zа-яё]|\s|( )*)$")

# others
regexps_year = re.compile(r"(19\d\d|20\d\d)")
