def main():
    # Launch GUI
    try:
        from gui_app import main as gui_main
        gui_main()
    except ImportError as e:
        print("Dependencies not installed. Install with: pip install -r requirements.txt")
        print(e)

if __name__ == "__main__":
    main()
