eng = "".join(list(map(chr, range(ord("a"), ord("z") + 1))))
rus = "".join([chr(i) for i in range(ord("а"), ord("а") + 32)] + ["ё"])
lower_letters = eng + rus
upper_letters = lower_letters.upper()
letters = upper_letters + lower_letters
digits = "".join([str(i) for i in range(10)])
special_symbols = "<>~!@#$%^&*_+-/\"|?.,:;'`= "
brackets = "{}[]()"
symbols = letters + digits + brackets + special_symbols
not_chars = digits + brackets + special_symbols

prohibited_symbols = {s: i for i, s in enumerate("[]<")}


def count_symbols(text: str, symbol_list: str) -> int:
    return sum(1 for symbol in text if symbol in symbol_list)
