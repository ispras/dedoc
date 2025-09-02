class TableTypeAdditionalOptions:
    """
    Setting up the table recognizer. The value of the parameter specifies the type of tables recognized when processed by
    class :class:`~dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_recognizer.TableRecognizer`.

    * Parameter `table_type=wo_external_bounds` - recognize tables without external bounds;

    Example of a table of type `wo_external_bounds`::

       text   | text | text
      --------+------+------
       text   | text | text
      --------+------+------
       text   | text | text
      --------+------+------
       text   | text | text


    * Parameter `table_type=one_cell_table` - if a document contains a bounding box with text, it will be considered a table;

    Example of a page with a table of type `one_cell_table`::

         _________________________
         Header of document
         text text text +------+
         text           | text |  <--- it is a table
                        +------+
         ________________________

    * Parameter `table_type=split_last_column` - specified parameter for the merged last column of the table;

    Example of a table of type `split_last_column`::

         +--------+------+-------+
         | text   | text | text1 |
         +--------+------+       |
         | text0  | text | text2 |
         |        | -----|       |
         |        | text | text3 |
         +--------+------+       |
         | text   | text | text4 |
         +--------+------+-------+
                     |
                 Recognition
                    |
                    V
         +--------+------+-------+
         | text   | text | text1 |
         +--------+------+-------|
         | text0  | text | text2 |
         |--------+ -----+------ |
         | text0  | text | text3 |
         +--------+------+------ |
         | text   | text | text4 |
         +--------+------+-------+

    """

    def __init__(self) -> None:
        self.table_wo_external_bounds = "wo_external_bounds"
        self.detect_one_cell_table = "one_cell_table"
        self.split_last_column = "split_last_column"
