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
        except:
            continue
            ##
        if glyph_name == -1:
            continue
        char_save_path = str(save_path.joinpath(str(uni), f"{font.fontname}_{index}.png"))

        try:
            font[int(uni)].export(char_save_path, image_size)
            save_paths.append(char_save_path)
        except:
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
        if "superior" in name:
            continue
        if not font[name].isWorthOutputting() and name != "space":
            continue

        filename = None
        if name == ".notdef":
            continue

        try:
            unicode_val = ord(name)
        except TypeError:
            try:
                unicode_val = font[name].encoding
            except AttributeError:
                unicode_val = fontforge.unicodeFromName(name)

        if unicode_val == -1:
            filename = name
        else:
            filename = str(unicode_val)

        if not font[name].isWorthOutputting() or font[name].width == 0:

            all_empty = True
            for i in range(len(font[name].layers)):
                if font[name].layers[i] != 1:
                    all_empty = False
                    break

            if all_empty:
                continue

            name_whitespace = ""
            try:
                name_whitespace = chr(int(filename)) if filename.isdigit() else filename
            except (ValueError, TypeError):
                name_whitespace = filename

            font_white_spaces[name_whitespace] = " "
            not_worth_outputting.append(filename)
            continue

        if filename == -1:
            continue

        char_save_path = f"{save_path}/{filename}.png"

        try:
            font[name].export(char_save_path, image_size)
            save_paths.append(char_save_path)
            names.append(name)
            codes.append(unicode_val)
        except OSError:
            continue
    return [save_paths, font_white_spaces, names, codes]


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if args[0] == "True":
        print(generate_images(Path(args[1]), Path(args[2]), int(args[3]), args[4:]))
    elif args[0] == "False":
        print(generate_all_images(Path(args[1]), Path(args[2])))
