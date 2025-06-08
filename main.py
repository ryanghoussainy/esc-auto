from leahify_qualifiers import leahify_qualifiers
from check_qualifiers import check_qualifiers
import sys

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ['1', '2', '3']:
        print("Invalid input. Valid inputs are 1, 2, 3.")
        return

    input = int(sys.argv[1])
    if input == 1:
        leahify_qualifiers('examples/1_doc.xlsx', 'examples/2_docLeah.xls')
    elif input == 2:
        check_qualifiers("output.xlsx", "examples/3_docHeatResults.pdf")
    elif input == 3:
        # TODO
        pass
    else:
        print("Invalid input. Valid inputs are 1, 2, 3.")

if __name__ == "__main__":
    main()
