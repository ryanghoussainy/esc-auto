'''
This file's purpose is to turn Sammy's version of qualifiers into Leah's version,
hence the name leahify.
First, read leah's version, then for each swimmer in that sheet, find the corresponding
time in Sammy's version and add it to the dictionary.
'''

from extract_tables import extract_tables, print_tables

def leahify_qualifiers(file: str, sheet_name: str) -> list[dict]:
    pass

if __name__ == '__main__':
    print_tables(extract_tables('examples/2_docLeah.xls', None, [("Lane", 0), ("Extra", 1)]))
