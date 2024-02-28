import abc


class LinePrefix(abc.ABC):
    """
    Class for line prefix typical for lists items.
    For example for line

    1) Bla bla bla
    prefix is Prefix( 1) )

    For line a) some item with letter
    prefix is Prefix( a) )

    For line
    1.2.1 Dotted line
    prefix is Prefix( 1.2.1 )

    Can be used to define if one prefix is valid predecessor for this prefix.

    For example

    >>> LinePrefix("1.2.1").predecessor(LinePrefix("1.1.1"))
    True

    >>> LinePrefix("1.2.3").predecessor(LinePrefix("1.1.1"))
    False
    """
    name = ""
    regexp = None

    def __init__(self, prefix: str, indent: float) -> None:
        assert self.is_valid(prefix), f"`{prefix}` is invalid prefix for this {self.name} type"
        self.prefix = prefix
        self.indent = indent

    def __eq__(self, o: object) -> bool:
        return isinstance(o, LinePrefix) and self.prefix == o.prefix and self.name == o.name

    @abc.abstractmethod
    def predecessor(self, other: "LinePrefix") -> bool:
        """
        Compare this and other prefix and define if other is valid predecessor for this one.
        >>> this_one = LinePrefix("2.")
        >>> other_one = LinePrefix("1.")
        >>> this_one.predecessor(other_one)
        True

        >>> this_one = LinePrefix("b)")
        >>> other_one = LinePrefix("a)")
        >>> this_one.predecessor(other_one)
        True

        >>> this_one = LinePrefix("1.2.1")
        >>> other_one = LinePrefix("1.1.1")
        >>> this_one.predecessor(other_one)
        True

        :param other: prefix of other line
        :return: true if other is valid predecessor for this one, false otherwise
        """
        pass

    def successor(self, other: "LinePrefix") -> bool:
        return other.predecessor(self)

    @staticmethod
    @abc.abstractmethod
    def is_valid(prefix_str: str) -> bool:
        """
        :param prefix_str: the string representation of the prefix. For example "1." is valid for DottedPrefix
        :return: true if prefix_str is valid for this type of prefix, false otherwise.
        """
        pass

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.prefix})"

    def __repr__(self) -> str:
        return self.__str__()
