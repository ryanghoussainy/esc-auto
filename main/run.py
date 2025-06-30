from leahify_qualifiers import leahify_qualifiers
from check_qualifiers import check_qualifiers
from check_finals import check_finals
import sys

def main():
    if len(sys.argv) == 1:
        # No arguments - launch GUI
        try:
            from gui_app import main as gui_main
            gui_main()
        except ImportError:
            print("GUI dependencies not installed. Install with: pip install -r requirements.txt")
            print("Or use command line with arguments 1, 2, or 3.")
        return
    
    if len(sys.argv) != 2 or sys.argv[1] not in ['1', '2', '3']:
        print("Invalid input. Valid inputs are 1, 2, 3, or no arguments for GUI.")
        return

    input = int(sys.argv[1])
    if input == 1:
        leahify_qualifiers('examples/1_doc.xlsx', 'examples/2_docLeah.xls')
    elif input == 2:
        check_qualifiers("output.xlsx", "examples/3_docHeatResults.pdf")
    elif input == 3:
        check_finals("examples/4_docFinalResultsLeah.xlsx", "examples/5_docFullResults.pdf")
    else:
        print("Invalid input. Valid inputs are 1, 2, 3.")

if __name__ == "__main__":
    main()
