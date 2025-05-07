from pathlib import Path

image_size = 80


def generate_images(save_path: Path, font_path: Path, index: int, uni_char_pool: list) -> list:
    import fontforge
    font = fontforge.open(str(font_path), 1)
    save_paths = []
    for uni in uni_char_pool:
        uni = int(uni)
        glyph_name = fontforge.nameFromUnicode(uni)
        char = chr(uni)
        try:
            if char.isalpha() and char.isupper():
                char_low = char.lower()
                if font[ord(char)] == font[ord(char_low)]:
                    continue
        except Exception:
            continue
            ##
        if glyph_name == -1:
            continue
        char_save_path = str(save_path.joinpath(str(uni), f"{font.fontname}_{index}.png"))

        try:
            font[int(uni)].export(char_save_path, image_size)
            save_paths.append(char_save_path)
        except Exception:
            continue

    return save_paths


def generate_all_images(save_path: Path, font_path: Path) -> list:
    import fontforge

    font = fontforge.open(str(font_path))
    save_paths = []
    not_worth_outputting = []
    font_white_spaces = {}
    names = []
    codes = []

    for name in font:
        process_glyph(
            name, font, save_path,
            save_paths, font_white_spaces,
            names, codes, not_worth_outputting
        )

    return [save_paths, font_white_spaces, names, codes]


def process_glyph(
        name: str,
        font,
        save_path: Path,
        save_paths: list,
        font_white_spaces: dict,
        names: list,
        codes: list,
        not_worth_outputting: list
) -> None:
    if should_skip_glyph(name, font):
        return

    unicode_val = get_unicode_value(name, font)
    filename = get_filename(name, unicode_val)

    if is_empty_glyph(font, name, filename):
        handle_empty_glyph(name, filename, font_white_spaces, not_worth_outputting)
        return

    if filename == -1:
        return

    export_glyph(name, font, save_path, filename, save_paths, names, codes, unicode_val)


def should_skip_glyph(name: str, font) -> bool:
    if "superior" in name:
        return True
    if name == ".notdef":
        return True
    if not font[name].isWorthOutputting() and name != "space":
        return True
    return False


def get_unicode_value(name: str, font) -> int:
    import fontforge
    try:
        return ord(name)
    except TypeError:
        try:
            return font[name].encoding
        except AttributeError:
            return fontforge.unicodeFromName(name)


def get_filename(name: str, unicode_val: int) -> str:
    return str(unicode_val) if unicode_val != -1 else name


def is_empty_glyph(font, name: str, filename: str) -> bool:
    if not font[name].isWorthOutputting() or font[name].width == 0:
        for i in range(len(font[name].layers)):
            if font[name].layers[i] != 1:
                return False
        return True
    return False


def handle_empty_glyph(
        name: str,
        filename: str,
        font_white_spaces: dict,
        not_worth_outputting: list
) -> None:
    name_whitespace = ""
    try:
        name_whitespace = chr(int(filename)) if filename.isdigit() else filename
    except (ValueError, TypeError):
        name_whitespace = filename

    font_white_spaces[name_whitespace] = " "
    not_worth_outputting.append(filename)


def export_glyph(
        name: str,
        font,
        save_path: Path,
        filename: str,
        save_paths: list,
        names: list,
        codes: list,
        unicode_val: int
) -> None:
    char_save_path = f"{save_path}/{filename}.png"
    try:
        font[name].export(char_save_path, image_size)
        save_paths.append(char_save_path)
        names.append(name)
        codes.append(unicode_val)
    except OSError:
        pass


if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    if args[0] == "True":
        print(generate_images(Path(args[1]), Path(args[2]), int(args[3]), args[4:]))
    elif args[0] == "False":
        print(generate_all_images(Path(args[1]), Path(args[2])))
