class NumberingExtractor:
    """
    This class is used to compute numbering text for list items.
    For example: "1.", (i), "○"
    """
    def __init__(self) -> None:
        # Mapping according to the ST_TextAutonumberScheme
        # NOTE we ignore chinese, japanese, hindi, thai
        self.numbering_types = dict(
            arabic="1",  # 1, 2, 3, ..., 10, 11, 12, ...
            alphaLc="a",  # a, b, c, ..., y, z, aa, bb, cc, ..., yy, zz, aaa, bbb, ccc, ...
            alphaUc="A",  # A, B, C, ..., Y, Z, AA, BB, CC, ..., YY, ZZ, AAA, BBB, CCC, ...
            romanLc="i",  # i, ii, iii, iv, ..., xviii, xix, xx, xxi, ...
            romanUc="I"  # I, II, III, IV, ..., XVIII, XIX, XX, XXI, ...
        )

        self.numbering_formatting = dict(
            ParenBoth="({}) ",
            ParenR="{}) ",
            Period="{}. ",
            Plain="{} "
        )

        self.combined_types = {
            num_type + num_formatting: (num_type, num_formatting) for num_type in self.numbering_types for num_formatting in self.numbering_formatting
        }
        self.roman_mapping = [(1000, "m"), (500, "d"), (100, "c"), (50, "l"), (10, "x"), (5, "v"), (1, "i")]

    def get_text(self, numbering: str, shift: int) -> str:
        """
        Computes the next item of the list sequence.
        :param numbering: type of the numbering, e.g. "arabicPeriod"
        :param shift: shift from the beginning of list numbering
        :return: string representation of the next numbering item
        """
        num_type, num_formatting = self.combined_types.get(numbering, ("arabic", "Period"))

        if num_type in ("alphaLc", "alphaUc"):
            shift1, shift2 = shift % 26, shift // 26 + 1
            num_char = chr(ord(self.numbering_types[num_type]) + shift1) * shift2
        elif num_type in ("romanLc", "romanUc"):
            num_char = ""
            for number, letter in self.roman_mapping:
                cnt, shift = shift // number, shift % number
                if num_type == "romanUc":
                    letter = chr(ord(letter) + ord("A") - ord("a"))
                num_char += letter * cnt
        else:
            num_char = str(int(self.numbering_types["arabic"]) + shift)

        return self.numbering_formatting[num_formatting].format(num_char)
