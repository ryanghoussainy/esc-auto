__version__ = "1.0.4" # Major.Minor.Patch

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkmacosx import Button
import os
import platform
import threading
import sys
import json
from datetime import datetime
from PIL import Image, ImageTk

from leahify_qualifiers import leahify_qualifiers
from check_qualifiers import check_qualifiers
from check_finals import check_finals
from amindefy_timesheets import amindefy_timesheets
from check_timesheets import check_timesheets
from colours import *

# Get different path depending on Windows vs Mac
def get_rates_file_path():
    system = platform.system()
    if system == "Windows":
        return os.path.join(os.path.expanduser("~"), "AppData", "Local", "ESCAuto", "rates.json")
    elif system == "Darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "ESCAuto", "rates.json")
    else:
        raise NotImplementedError(f"Unsupported OS: {system}")

RATES_FILE = get_rates_file_path()

RATE_LEVELS = [
    "L1", "NQL2", "L2", "Enhanced L2", "Lower Enhanced L2",
    "Safeguarding", "Admin", "Gala Full Day", "Gala Half Day", "House Event"
]

# The months considered for timesheets. The swimming year is September-July
MONTHS = [
    "September", "October", "November", "December", "January",
    "February", "March", "April", "May", "June", "July"
]

class SwimmingResultsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ESC Auto")
        self.root.geometry("1200x1000")
        self.root.configure(bg=APP_BACKGROUND)

        # Setup styles
        self.setup_styles()
        
        # File paths storage
        self.file_paths = {
            'sammy_qualifiers': None,
            'leah_template': None,
            'heat_results_pdf': None,
            'finals_excel': None,
            'full_results_pdf': None,
            'timesheets_folder': None,
            'amindefied_excel': None,
            'sign_in_sheet': None,
            'amindefy_output_file': None,
            'leahify_output_file': None,
        }
        
        self.setup_ui()

    def resource_path(self, relative_path):
        """Get absolute path to resource, works for development and PyInstaller"""
        try:
            base_path = sys._MEIPASS  # For PyInstaller
        except AttributeError:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
        
    def setup_ui(self):
        # Main title with logo
        title_frame = tk.Frame(self.root, bg=APP_BACKGROUND)
        title_frame.pack(pady=(10, 0))

        # Try to load and display logo
        try:
            # Load logo
            logo_path = self.resource_path("images/esc-logo.png")
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                # Resize logo
                logo = logo.resize((48, 48), Image.Resampling.LANCZOS)
                self.title_image = ImageTk.PhotoImage(logo)

                # Image label
                image_label = tk.Label(
                    title_frame,
                    image=self.title_image,
                    bg=APP_BACKGROUND
                )
                image_label.pack(side=tk.LEFT, padx=(0, 15))
        except Exception as e:
            print(f"Could not load logo: {e}")

        # Add title label
        title_label = tk.Label(
            title_frame,
            text="ESC Auto",
            font=("Segoe UI", 16, "bold"),
            bg=APP_BACKGROUND,
            fg=APP_TITLE
        )
        title_label.pack(side=tk.LEFT, padx=(0, 15))

        # Add version label
        version_label = tk.Label(
            title_frame,
            text=f"Version {__version__}",
            font=("Segoe UI", 10),
            bg=APP_BACKGROUND,
            fg=APP_TITLE,
        )
        version_label.pack(side=tk.RIGHT, padx=(0, 20))
        
        # Create button frame for app switching
        button_frame = tk.Frame(self.root, bg=APP_BACKGROUND)
        button_frame.pack(pady=5)

        self.app1_btn = Button(
            button_frame,
            text="Timesheet Checker",
            command=lambda: self.switch_app(0),
            font=("Segoe UI", 10, "bold"),
            borderless=True,
            padx=15,
            pady=5
        )
        self.app1_btn.pack(side=tk.LEFT, padx=5)
        
        self.app2_btn = Button(
            button_frame,
            text="House Champs",
            command=lambda: self.switch_app(1),
            font=("Segoe UI", 10),
            borderless=True,
            padx=15,
            pady=5
        )
        self.app2_btn.pack(side=tk.LEFT, padx=5)
        
        # Container frame for the apps
        self.apps_container = tk.Frame(self.root, bg=APP_BACKGROUND)
        self.apps_container.pack(expand=True, fill='both', padx=30, pady=20)
        
        # Create both app frames
        self.timesheet_checker_frame = tk.Frame(self.apps_container, bg=APP_BACKGROUND)
        self.house_champs_frame = tk.Frame(self.apps_container, bg=APP_BACKGROUND)

        # Setup timesheet checker app (your current app)
        self.setup_timesheet_checker_app(self.timesheet_checker_frame)

        # Setup house champs app
        self.setup_house_champs_app(self.house_champs_frame)

        # Show timesheet checker app by default
        self.current_app = None # we initialise this to None to prevent early returning from switch_app(0)
        self.switch_app(0)
    
    def switch_app(self, app_index):
        """Switch between the two apps"""
        # If already on the selected app, do nothing
        if self.current_app == app_index:
            return
        
        self.current_app = app_index
        
        # Hide both frames
        self.timesheet_checker_frame.pack_forget()
        self.house_champs_frame.pack_forget()
        
        # Update button styles
        if app_index == 0:
            # Show timesheet checker app
            self.timesheet_checker_frame.pack(expand=True, fill='both')
            self.app1_btn.config(font=("Segoe UI", 10, "bold"))
            self.app2_btn.config(font=("Segoe UI", 10))
        else:
            # Show house champs app
            self.house_champs_frame.pack(expand=True, fill='both')
            self.app1_btn.config(font=("Segoe UI", 10))
            self.app2_btn.config(font=("Segoe UI", 10, "bold"))

    def setup_house_champs_app(self, parent):
        """Setup the Auto House Champs app"""
        # Create main container with paned window
        main_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL, style="TFrame")
        main_paned.pack(expand=True, fill='both')
        
        # Left side - Controls
        left_frame = tk.Frame(main_paned, bg=FRAME_BACKGROUND)
        main_paned.add(left_frame, weight=1)
        
        # Right side - Output
        right_frame = tk.Frame(main_paned, bg=FRAME_BACKGROUND)
        main_paned.add(right_frame, weight=1)
        
        # Create notebook for tabs on left side
        self.house_champs_notebook = ttk.Notebook(left_frame, style="TNotebook")
        self.house_champs_notebook.pack(expand=True, fill='both', padx=10)
        
        # Tab 1: Leahify Qualifiers
        self.create_leahify_tab()
        
        # Tab 2: Check Qualifiers
        self.create_check_qualifiers_tab()
        
        # Tab 3: Check Finals
        self.create_check_finals_tab()

        # Output panel on right side
        self.create_house_champs_output_panel(right_frame)

    def setup_timesheet_checker_app(self, parent):
        """Setup Auto Timesheet Checker app"""
        # Create main container with paned window
        main_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL, style="TFrame")
        main_paned.pack(expand=True, fill='both')
        
        # Left side - Controls
        left_frame = tk.Frame(main_paned, bg=FRAME_BACKGROUND)
        main_paned.add(left_frame, weight=1)
        
        # Right side - Output
        right_frame = tk.Frame(main_paned, bg=FRAME_BACKGROUND)
        main_paned.add(right_frame, weight=1)
        
        # Create notebook for tabs on left side
        self.timesheet_checker_notebook = ttk.Notebook(left_frame, style="TNotebook")
        self.timesheet_checker_notebook.pack(expand=True, fill='both', padx=10)

        # Tab 1: Folder Processing
        self.create_amindefy_tab()

        # Tab 2: Rates
        self.create_rates_tab()

        # Tab 3: Check Timesheets
        self.create_check_timesheets_tab()

        # Output panel on right side
        self.create_timesheet_output_panel(right_frame)

    def setup_styles(self):
        # Configure ttk styles
        style = ttk.Style()
        
        # Configure frame style
        style.configure(
            'TFrame',
            background=FRAME_BACKGROUND,
            relief='flat'
        )
        
        # Configure notebook style
        style.configure(
            'TNotebook'
        )
        style.configure(
            'TNotebook.Tab',
            padding=(20, 10),
            font=('Segoe UI', 12)
        )
    
    def create_house_champs_output_panel(self, parent):
        self.house_champs_output_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            width=50,
            height=20,
            font=("JetBrains Mono", 12),
            bg=OUTPUT_BACKGROUND,
            fg=OUTPUT_FOREGROUND,
            state='disabled',
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=OUTPUT_HIGHLIGHT,
            insertbackground=OUTPUT_CURSOR,
            relief='flat'
        )
        self.house_champs_output_text.pack(expand=True, fill='both', padx=10)
        
        # Configure colour tags
        self.house_champs_output_text.tag_configure("red", foreground=RED)
        self.house_champs_output_text.tag_configure("yellow", foreground=YELLOW)
        self.house_champs_output_text.tag_configure("green", foreground=GREEN)

    def create_timesheet_output_panel(self, parent):
        self.timesheet_output_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            width=50,
            height=20,
            font=("JetBrains Mono", 12),
            bg=OUTPUT_BACKGROUND,
            fg=OUTPUT_FOREGROUND,
            state='disabled',
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=OUTPUT_HIGHLIGHT,
            insertbackground=OUTPUT_CURSOR,
            relief='flat'
        )
        self.timesheet_output_text.pack(expand=True, fill='both', padx=10)
        
        # Configure colour tags
        self.timesheet_output_text.tag_configure("red", foreground=RED)
        self.timesheet_output_text.tag_configure("yellow", foreground=YELLOW)
        self.timesheet_output_text.tag_configure("green", foreground=GREEN)

    def get_current_output_widget(self):
        """Get the output widget for the currently active app"""
        if self.current_app == 0:  # Timesheet Checker
            return self.timesheet_output_text
        else:  # House Champs
            return self.house_champs_output_text

    def clear_output(self):
        output_widget = self.get_current_output_widget()
        output_widget.config(state='normal')
        output_widget.delete(1.0, tk.END)
        output_widget.config(state='disabled')

    def append_output(self, text, color=None):
        """Thread-safe method to append text to output"""
        def _append():
            output_widget = self.get_current_output_widget()
            if output_widget.winfo_exists():
                try:
                    output_widget.config(state='normal')
                    if color:
                        output_widget.insert(tk.END, text + "\n", color)
                    else:
                        output_widget.insert(tk.END, text + "\n")
                    output_widget.see(tk.END)
                    output_widget.config(state='disabled')
                except tk.TclError:
                    pass  # Widget destroyed
        
        # Ensure GUI updates happen on main thread
        self.root.after(0, _append)

    def _write_to_output(self, text):
        output_widget = self.get_current_output_widget()
        output_widget.config(state='normal')
        output_widget.insert(tk.END, text)
        output_widget.see(tk.END)
        output_widget.config(state='disabled')
    
    def show_confirmation_dialog(self, data: dict):
        """
        Show confirmation dialog and return user's choice

        Args:

        """
        # This will be called from a background thread, so we need to use a queue
        import queue
        result_queue = queue.Queue()
        
        def show_dialog():
            # Create custom dialog
            dialog = tk.Toplevel(self.root)
            
            dialog.title("Confirm Swimmer Match")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Dialog dimensions
            dialog_width = 500
            dialog_height = 250
            
            # Center the dialog
            self.root.update_idletasks()
            parent_x = self.root.winfo_x()
            parent_y = self.root.winfo_y()
            parent_width = self.root.winfo_width()
            parent_height = self.root.winfo_height()
            
            x = parent_x + (parent_width - dialog_width) // 2
            y = parent_y + (parent_height - dialog_height) // 2
            
            dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
            
            # Message display
            msg_frame = tk.Frame(dialog, padx=20, pady=20)
            msg_frame.pack(expand=True, fill='both')
            
            msg_label = tk.Label(
                msg_frame,
                text="Are these the same swimmer?",
                font=("Segoe UI", 14, "bold")
            )
            msg_label.pack(pady=(0, 15))
            
            # Sammy's swimmer info
            sammy_label = tk.Label(
                msg_frame,
                text=f"(Sammy) {data['sammy_name']}",
                font=("Segoe UI", 11, "bold"),
            )
            sammy_label.pack(anchor=tk.W, pady=(0, 5))
            
            # Leah's swimmer info
            leah_label = tk.Label(
                msg_frame,
                text=f"(Leah) {data['leah_name']}",
                font=("Segoe UI", 11, "bold"),
            )
            leah_label.pack(anchor=tk.W, pady=(0, 5))
            
            # Similarity score
            similarity = data['similarity']
            similarity_color = GREEN if similarity >= 80 else YELLOW if similarity >= 50 else RED
            similarity_label = tk.Label(
                msg_frame,
                text=f"Similarity Score: {similarity}%",
                font=("Segoe UI", 11, "bold"),
                fg=similarity_color
            )
            similarity_label.pack(anchor=tk.W, pady=(0, 15))
            
            # Buttons
            button_frame = tk.Frame(dialog)
            button_frame.pack(pady=(0, 20))
            
            def accept():
                result_queue.put("y")
                dialog.destroy()
            
            def deny():
                result_queue.put("n")
                dialog.destroy()
            
            def ignore():
                result_queue.put("ignore")
                dialog.destroy()
            
            def cancel():
                result_queue.put("exit")
                dialog.destroy()
            
            # Bind close event
            dialog.protocol("WM_DELETE_WINDOW", cancel)
            
            accept_btn = Button(
                button_frame,
                text="✓ Accept Match",
                command=accept,
                font=("Segoe UI", 10, "bold"),
                bg=GREEN,
                padx=20,
                pady=8
            )
            accept_btn.pack(side=tk.LEFT, padx=5)
            
            deny_btn = Button(
                button_frame,
                text="✗ Deny Match",
                command=deny,
                font=("Segoe UI", 10, "bold"),
                bg=RED,
                padx=20,
                pady=8
            )
            deny_btn.pack(side=tk.LEFT, padx=5)

            ignore_btn = Button(
                button_frame,
                text="Ignore",
                command=ignore,
                font=("Segoe UI", 10, "bold"),
                bg=YELLOW,
                padx=20,
                pady=8
            )
            ignore_btn.pack(side=tk.LEFT, padx=5)

            dialog.deiconify()
            dialog.lift()
            dialog.focus_force()
        
        # Show dialog on main thread
        self.root.after(0, show_dialog)
        
        # Wait for result
        while True:
            # we use a try-except block to avoid blocking. The timeout is convenient and allows us to check periodically.
            try:
                result = result_queue.get(timeout=0.1) # check for result every 100ms
                return result
            except queue.Empty:
                continue
    
    def create_leahify_tab(self):
        frame = tk.Frame(self.house_champs_notebook, bg=NOTEBOOK_TAB_BACKGROUND)
        self.house_champs_notebook.add(frame, text="1. Leahify Qualifiers")

        # Instructions
        instructions = tk.Label(
            frame,
            text="Convert Sammy's qualifier format to Leah's format",
            font=("Segoe UI", 12),
            fg=LABEL_FOREGROUND,
            bg=NOTEBOOK_TAB_BACKGROUND,
            wraplength=500
        )
        instructions.pack(pady=20)
        
        # File input areas
        self.create_file_input(frame, "Sammy's Qualifiers EXCEL", 'sammy_qualifiers', [('Excel files', '*.xls *.xlsx')])
        self.create_file_input(frame, "Leah's Template EXCEL", 'leah_template', [('Excel files', '*.xls *.xlsx')])

        # Output file selection
        self.create_output_file_input(frame, "Output EXCEL", 'leahify_output_file', [('Excel files', '*.xlsx')], 'output.xlsx')
        
        # Process button
        process_btn = Button(
            frame,
            text="Process Files",
            command=self.run_leahify,
            highlightbackground=NOTEBOOK_TAB_BACKGROUND,
            focusthickness=0,
        )
        process_btn.pack(pady=30)
    
    def create_check_qualifiers_tab(self):
        frame = tk.Frame(self.house_champs_notebook, bg=NOTEBOOK_TAB_BACKGROUND)
        self.house_champs_notebook.add(frame, text="2. Check Qualifiers")

        # Instructions
        instructions = tk.Label(
            frame,
            text="Check the generated qualifiers against heat results PDF",
            font=("Segoe UI", 12),
            fg=LABEL_FOREGROUND,
            bg=NOTEBOOK_TAB_BACKGROUND,
            wraplength=500
        )
        instructions.pack(pady=20)
        
        # File input areas
        self.create_file_input(frame, "Generated Output EXCEL", 'output_excel', [('Excel files', '*.xls *.xlsx')])
        self.create_file_input(frame, "Heat Results PDF", 'heat_results_pdf', [('PDF files', '*.pdf')])
        
        # Process button
        process_btn = Button(
            frame,
            text="Check Qualifiers",
            command=self.run_check_qualifiers,
            highlightbackground=NOTEBOOK_TAB_BACKGROUND,
            focusthickness=0,
        )
        process_btn.pack(pady=30)
    
    def create_check_finals_tab(self):
        frame = tk.Frame(self.house_champs_notebook, bg=NOTEBOOK_TAB_BACKGROUND)
        self.house_champs_notebook.add(frame, text="3. Check Finals")
        
        # Instructions
        instructions = tk.Label(
            frame,
            text="Check finals results against full results PDF",
            font=("Segoe UI", 12),
            fg=LABEL_FOREGROUND,
            bg=NOTEBOOK_TAB_BACKGROUND,
            wraplength=500
        )
        instructions.pack(pady=20)
        
        # File input areas
        self.create_file_input(frame, "Finals EXCEL", 'finals_excel', [('Excel files', '*.xlsx')])
        self.create_file_input(frame, "Full Results PDF", 'full_results_pdf', [('PDF files', '*.pdf')])
        
        # Process button
        process_btn = Button(
            frame,
            text="Check Finals",
            command=self.run_check_finals,
            highlightbackground=NOTEBOOK_TAB_BACKGROUND,
            focusthickness=0,
        )
        process_btn.pack(pady=30)
    
    def create_amindefy_tab(self):
        frame = tk.Frame(self.timesheet_checker_notebook, bg=NOTEBOOK_TAB_BACKGROUND)
        self.timesheet_checker_notebook.add(frame, text="1. Amindefy Timesheets")

        # Instructions
        instructions = tk.Label(
            frame,
            text="Combine all timesheets into a single Excel file.",
            font=("Segoe UI", 12),
            bg=NOTEBOOK_TAB_BACKGROUND,
            wraplength=400
        )
        instructions.pack(pady=20)
        
        # Folder input area
        self.create_folder_input(frame, "Timesheets Folder", 'timesheets_folder')

        # Output file selection
        self.create_output_file_input(frame, "Output Excel File", 'amindefy_output_file', [('Excel files', '*.xlsx')], 'all_timesheets.xlsx')
        
        # Process button
        process_btn = Button(
            frame,
            text="Create Amindefied Excel File",
            command=self.run_amindefy,
            highlightbackground=NOTEBOOK_TAB_BACKGROUND,
            focusthickness=0,
        )
        process_btn.pack(pady=30)
    
    def create_rates_tab(self):
        frame = tk.Frame(self.timesheet_checker_notebook, bg=NOTEBOOK_TAB_BACKGROUND)
        self.timesheet_checker_notebook.add(frame, text="2. Rates")

        instructions = tk.Label(
            frame,
            text="Review and edit rates for each level. Remember to SAVE.",
            font=("Segoe UI", 12),
            bg=NOTEBOOK_TAB_BACKGROUND,
            wraplength=400
        )
        instructions.pack(pady=20)

        # Rate change checkbox and date (UI only)
        self.rate_change_var = tk.BooleanVar(value=False)
        self.rate_change_date_var = tk.StringVar(value="")

        rate_change_frame = tk.Frame(frame)
        rate_change_frame.pack(padx=10, pady=5, anchor="w")

        rate_change_check = tk.Checkbutton(
            rate_change_frame,
            text="Rate change",
            variable=self.rate_change_var,
            command=self.toggle_rate_change,
            activeforeground=LABEL_FOREGROUND,
        )
        rate_change_check.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(rate_change_frame, text="Change date (DD/MM/YYYY):").pack(side=tk.LEFT)
        self.rate_change_date_entry = tk.Entry(rate_change_frame, textvariable=self.rate_change_date_var, state="disabled")
        self.rate_change_date_entry.pack(side=tk.LEFT, padx=(5, 0))

        # Load nested rates format (rates, rates_after, date)
        rates, rates_after, rate_change_date = self.load_rates()
        self.rates = rates
        # if rates_after is None, keep internal copy for editing but hide the table UI
        self.rates_after = {k: float(v) for k, v in rates.items()} if rates_after is None else {k: float(v) for k, v in rates_after.items()}

        # set date UI if present
        if rate_change_date:
            self.rate_change_date_var.set(rate_change_date)
            self.rate_change_var.set(True)
            self.rate_change_date_entry.config(state='normal')
        else:
            self.rate_change_var.set(False)
            self.rate_change_date_entry.config(state='disabled')

        self.rate_vars = {}
        self.rate_vars_after = {}

        # Parent container holding two table frames side-by-side
        tables_container = tk.Frame(frame)
        tables_container.pack(padx=10, pady=10, fill=tk.X)

        # Left table (current rates)
        self.table_frame = tk.Frame(tables_container)
        self.table_frame.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(self.table_frame, text="Level", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=10, pady=5)
        tk.Label(self.table_frame, text="Rate (£/hr)", font=("Arial", 11, "bold")).grid(row=0, column=1, padx=10, pady=5)

        for i, (level, rate) in enumerate(self.rates.items(), start=1):
            tk.Label(self.table_frame, text=level, font=("Arial", 11)).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            var = tk.StringVar(value=f"{float(rate):.2f}")
            entry = tk.Entry(self.table_frame, textvariable=var, width=10, font=("Arial", 11))
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.rate_vars[level] = var

        # Right table (rates after change) — create but may be hidden depending on rates_after
        self.table_frame_after = tk.Frame(tables_container)
        tk.Label(self.table_frame_after, text="Level", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=10, pady=5)
        tk.Label(self.table_frame_after, text="Rate (£/hr) (after)", font=("Arial", 11, "bold")).grid(row=0, column=1, padx=10, pady=5)

        for i, level in enumerate(self.rates.keys(), start=1):
            tk.Label(self.table_frame_after, text=level, font=("Arial", 11)).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            after_value = self.rates_after.get(level, 0.0)
            var_after = tk.StringVar(value=f"{float(after_value):.2f}")
            entry_after = tk.Entry(self.table_frame_after, textvariable=var_after, width=10, font=("Arial", 11))
            entry_after.grid(row=i, column=1, padx=10, pady=5)
            self.rate_vars_after[level] = var_after

        # Show after-table only if rates_after was present in file (not None) or checkbox is set
        if rates_after is not None:
            self.table_frame_after.pack(side=tk.LEFT)

        save_btn = Button(
            frame,
            text="Save",
            command=self.on_save_rates,
            highlightbackground=NOTEBOOK_TAB_BACKGROUND,
            focusthickness=0,
        )
        save_btn.pack(pady=10)
    
    def toggle_rate_change(self):
        """Show/hide the after-table. If turning on and rates_after was None, copy current rates into it."""
        if self.rate_change_var.get():
            # ensure internal rates_after exists and populate from current rates if it was None
            if getattr(self, "rates_after", None) is None:
                self.rates_after = {k: float(v) for k, v in self.rates.items()}
                # update UI entries to match
                for lvl, var in self.rate_vars_after.items():
                    var.set(f"{self.rates_after.get(lvl, 0.0):.2f}")
            self.table_frame_after.pack(side=tk.LEFT, padx=(0, 0))
            self.rate_change_date_entry.config(state='normal')
        else:
            # Hide it and mark internal as None (so save writes null)
            self.table_frame_after.pack_forget()
            self.rate_change_date_entry.config(state='disabled')
            self.rates_after = None

    def load_rates(self):
        """
        Load nested rates JSON:
        { "rate_change_date": "DD/MM/YYYY" | null,
            "rates": {...},
            "rates_after": {...} | null
        }
        Returns (rates_dict, rates_after_dict_or_None, rate_change_date_or_None)
        """
        try:
            with open(RATES_FILE, "r") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("rates.json must contain an object")
            rates = {str(k): float(v) for k, v in data.get("rates", {}).items()}
            rates_after_raw = data.get("rates_after", None)
            rates_after = None if rates_after_raw is None else {str(k): float(v) for k, v in rates_after_raw.items()}
            rate_change_date = data.get("rate_change_date", None)

            return rates, rates_after, rate_change_date
        except Exception:
            return {level: 0.0 for level in RATE_LEVELS}, None, None

    def save_rates(self):
        """
        Save nested structure:
        { "rate_change_date": <str or null>, "rates": {...}, "rates_after": {...} or null }
        If rate_change checkbox is unchecked, rates_after will be saved as null.
        """
        try:
            # choose which rates_after to persist: either dict or None
            rates_to_save = {k: float(v) for k, v in self.rates.items()}
            if getattr(self, "rate_change_var", None) and self.rate_change_var.get() and getattr(self, "rates_after", None) is not None:
                rates_after_to_save = {k: float(v) for k, v in self.rates_after.items()}
            else:
                rates_after_to_save = None

            data = {
                "rate_change_date": self.rate_change_date_var.get() if (getattr(self, "rate_change_var", None) and self.rate_change_var.get()) else None,
                "rates": rates_to_save,
                "rates_after": rates_after_to_save,
            }

            # Create intermediate directories if they don't exist
            os.makedirs(os.path.dirname(RATES_FILE), exist_ok=True)

            with open(RATES_FILE, "w") as f:
                json.dump(data, f, indent=2)

            messagebox.showinfo("Saved", "Rates saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save rates: {e}")

    def on_save_rates(self):
        """Validate both tables and then persist nested JSON (rates + optional rates_after + date)."""
        new_rates = {}
        new_rates_after = None

        # Validate left table (current rates)
        for level, var in self.rate_vars.items():
            try:
                value = float(var.get())
                new_rates[level] = value
            except ValueError:
                messagebox.showerror("Error", f"Invalid rate for {level}: {var.get()}")
                return

        # Validate right table only if visible (rate change checked)
        if getattr(self, 'rate_change_var', None) and self.rate_change_var.get():

            if not self.rate_change_date_var.get():
                messagebox.showerror("Error", "Please enter a valid rate change date (DD/MM/YYYY).")
                return

            new_rates_after = {}
            for level, var in self.rate_vars_after.items():
                try:
                    value = float(var.get())
                    new_rates_after[level] = value
                except ValueError:
                    messagebox.showerror("Error", f"Invalid rate for {level} (after change): {var.get()}")
                    return

        # assign to instance
        self.rates = new_rates
        self.rates_after = new_rates_after

        # Save nested structure (save_rates writes rates_after as null if None)
        self.save_rates()

    def create_check_timesheets_tab(self):
        frame = tk.Frame(self.timesheet_checker_notebook, bg=NOTEBOOK_TAB_BACKGROUND)
        self.timesheet_checker_notebook.add(frame, text="2. Check Timesheets")

        # Instructions
        instructions = tk.Label(
            frame,
            text="Check the timesheets against the sign in sheet.",
            font=("Segoe UI", 12),
            bg=NOTEBOOK_TAB_BACKGROUND,
            wraplength=400
        )
        instructions.pack(pady=20)
        
        # Month dropdown menu
        current_month = datetime.now().strftime("%B")
        self.month_var = tk.StringVar(value=current_month)
        self.month = current_month

        def on_month_change(*args):
            self.month = self.month_var.get()

        self.month_var.trace_add("write", on_month_change)

        month_label = tk.Label(
            frame,
            text="Select Month:",
            font=("Segoe UI", 11, "bold"),
            fg=LABEL_FOREGROUND
        )
        month_label.pack(pady=(15, 5))

        month_dropdown = ttk.Combobox(
            frame,
            textvariable=self.month_var,
            values=MONTHS,
            state="readonly",
            font=("Segoe UI", 11)
        )
        month_dropdown.pack(pady=(0, 15))
        
        # File input areas
        self.create_file_input(frame, "Timesheets Excel File", 'amindefied_excel', [('Excel files', '*.xls *.xlsx')])
        self.create_file_input(frame, "Sign In Sheet", 'sign_in_sheet', [('Excel files', '*.xls *.xlsx')])
        
        # Process button
        process_btn = Button(
            frame,
            text="Check Timesheets",
            command=self.run_check_timesheets,
            highlightbackground=NOTEBOOK_TAB_BACKGROUND,
            focusthickness=0,
        )
        process_btn.pack(pady=30)
    
    def create_folder_input(self, parent, label_text, key):
        # Container frame
        container = tk.Frame(parent, relief=tk.RAISED, bd=1)
        container.pack(fill=tk.X, padx=10, pady=10)
        
        # Label
        label = tk.Label(container, text=label_text, font=("Arial", 10, "bold"))
        label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Browse button
        browse_btn = Button(
            container,
            text="Browse",
            command=lambda: self.browse_folder(key),
            highlightbackground=NOTEBOOK_TAB_BACKGROUND,
            focusthickness=0,
        )
        browse_btn.pack(pady=10)
        
        # File path display
        path_var = tk.StringVar()
        path_label = tk.Label(container, textvariable=path_var, fg=FILE_PATH_FG, wraplength=400)
        path_label.pack(anchor=tk.W, padx=10, pady=(0, 10))
        
        # Store references
        setattr(self, f'{key}_var', path_var)
    
    def create_file_input(self, parent, label_text, key, filetypes):
        # Container frame
        container = tk.Frame(parent, relief=tk.RAISED, bd=1)
        container.pack(fill=tk.X, padx=10, pady=10)
        
        # Label
        label = tk.Label(container, text=label_text, font=("Arial", 10, "bold"))
        label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Browse button
        browse_btn = Button(
            container,
            text=f"Browse",
            command=lambda: self.browse_file(key, filetypes),
            highlightbackground=NOTEBOOK_TAB_BACKGROUND,
            focusthickness=0,
        )
        browse_btn.pack(pady=10)
        
        # File path display
        path_var = tk.StringVar()
        path_label = tk.Label(container, textvariable=path_var, fg=FILE_PATH_FG, wraplength=400, font=("Segoe UI", 10, 'italic'))
        path_label.pack(anchor=tk.W, padx=10, pady=(0, 10))
        
        # Store references
        setattr(self, f'{key}_var', path_var)

    def create_output_file_input(self, parent, label_text, key, filetypes, default_name):
        # Container frame
        container = tk.Frame(parent, relief=tk.RAISED, bd=1)
        container.pack(fill=tk.X, padx=10, pady=10)
        
        # Label
        label = tk.Label(container, text=label_text, font=("Arial", 10, "bold"))
        label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Browse button and path display in same row
        button_frame = tk.Frame(container)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        browse_btn = Button(
            button_frame,
            text="Choose Location",
            command=lambda: self.browse_output_file(key, filetypes),
            highlightbackground=NOTEBOOK_TAB_BACKGROUND,
            focusthickness=0,
        )
        browse_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # File path display
        path_var = tk.StringVar()
        path_var.set(f"No location selected (will use default: {default_name})")
        path_label = tk.Label(button_frame, textvariable=path_var, fg=LABEL_FOREGROUND, wraplength=400)
        path_label.pack(side=tk.LEFT, anchor=tk.W, pady=(0, 10))
        
        # Store references
        setattr(self, f'{key}_var', path_var)

    def browse_output_file(self, key, filetypes):
        filename = filedialog.asksaveasfilename(
            title=f"Choose output file location",
            defaultextension=".xlsx",
            filetypes=filetypes + [('All files', '*.*')]
        )
        if filename:
            self.file_paths[key] = filename
            path_var = getattr(self, f'{key}_var')
            path_var.set(f"Will save to: {os.path.basename(filename)}")
    
    def browse_folder(self, key):
        folder = filedialog.askdirectory(title="Select folder")
        if folder:
            self.set_file_path(key, folder)
    
    def browse_file(self, key, filetypes):
        filename = filedialog.askopenfilename(
            title=f"Select file for {key}",
            filetypes=filetypes + [('All files', '*.*')]
        )
        if filename:
            self.set_file_path(key, filename)
    
    def set_file_path(self, key, path):
        self.file_paths[key] = path
        path_var = getattr(self, f'{key}_var')
        path_var.set(f"Selected: {os.path.basename(path)}")
        
    def run_leahify(self):
        if not self.file_paths['sammy_qualifiers'] or not self.file_paths['leah_template']:
            messagebox.showerror("Error", "Please select both required files")
            return
        
        # Get output path or use default (use the Leahify-specific key)
        output_path = self.file_paths.get('leahify_output_file', 'output.xlsx')
        
        def process():
            try:
                self.clear_output()
                
                # Define callback functions
                def progress_callback(message, color=None):
                    self.append_output(message, color)
                
                def confirm_callback(data):
                    return self.show_confirmation_dialog(data)
                
                def error_callback(message, color=None):
                    self.append_output(message, color or "red")
                
                # Call the backend function with callbacks
                leahify_qualifiers(
                    self.file_paths['sammy_qualifiers'],
                    self.file_paths['leah_template'],
                    progress_callback=progress_callback,
                    confirm_callback=confirm_callback,
                    error_callback=error_callback,
                    output_path=output_path,
                )
                
            except KeyboardInterrupt:
                self.append_output("Operation cancelled by user", "red")
            except Exception as e:
                self.append_output(f"❌ ERROR: {str(e)}", "red")
        
        # Run in separate thread
        threading.Thread(target=process, daemon=True).start()
    
    def run_check_qualifiers(self):
        output_path = self.file_paths.get('output_excel') or 'output.xlsx'
        if not self.file_paths['heat_results_pdf']:
            messagebox.showerror("Error", "Please select the heat results PDF file")
            return
        
        def process():
            try:
                self.clear_output()
                
                def progress_callback(message, color=None):
                    self.append_output(message, color)

                def confirm_callback(data):
                    return self.show_confirmation_dialog(data)

                def error_callback(message, color=None):
                    self.append_output(message, color or "red")
                
                # You'll need to update check_qualifiers to accept callbacks too
                check_qualifiers(
                    output_path, 
                    self.file_paths['heat_results_pdf'],
                    progress_callback=progress_callback,
                    confirm_callback=confirm_callback,
                    error_callback=error_callback
                )
                
            except KeyboardInterrupt:
                self.append_output("Operation cancelled by user", "yellow")
            except Exception as e:
                self.append_output(f"❌ ERROR: {str(e)}", "red")
        
        threading.Thread(target=process, daemon=True).start()
    
    def run_check_finals(self):
        if not self.file_paths['finals_excel'] or not self.file_paths['full_results_pdf']:
            messagebox.showerror("Error", "Please select both required files")
            return
        
        def process():
            try:
                self.clear_output()
                
                def progress_callback(message, color=None):
                    self.append_output(message, color)
                
                def confirm_callback(data):
                    return self.show_confirmation_dialog(data)
                
                def error_callback(message, color=None):
                    self.append_output(message, color or "red")
                
                # You'll need to update check_finals to accept callbacks too
                check_finals(
                    self.file_paths['finals_excel'],
                    self.file_paths['full_results_pdf'],
                    progress_callback=progress_callback,
                    confirm_callback=confirm_callback,
                    error_callback=error_callback
                )
                
            except KeyboardInterrupt:
                self.append_output("Operation cancelled by user", "yellow")
            except Exception as e:
                self.append_output(f"❌ ERROR: {str(e)}", "red")
        
        threading.Thread(target=process, daemon=True).start()
    
    def run_amindefy(self):
        if not self.file_paths['timesheets_folder']:
            messagebox.showerror("Error", "Please select a folder")
            return
        
        def process():
            try:
                self.clear_output()

                # Define callback functions
                def progress_callback(message, color=None):
                    self.append_output(message, color)
                
                def error_callback(message, color=None):
                    self.append_output(message, color or "red")
                
                # Call backend
                amindefy_timesheets(
                    self.file_paths['timesheets_folder'],
                    self.file_paths.get('amindefy_output_file', 'all_timesheets.xlsx'),
                    progress_callback,
                    error_callback
                )
            
            except KeyboardInterrupt:
                self.append_output("Operation cancelled by user.", "red")
            except Exception as e:
                self.append_output(f"❌ ERROR: {str(e)}", "red")
        
        # Run in separate thread to prevent GUI freezing
        threading.Thread(target=process, daemon=True).start()
    
    def run_check_timesheets(self):
        if not self.file_paths['amindefied_excel'] or not self.file_paths['sign_in_sheet']:
            messagebox.showerror("Error", "Please select both Excel files")
            return

        def process():
            try:
                self.clear_output()
                
                # Define callback functions
                def progress_callback(message, color=None):
                    self.append_output(message, color)

                def error_callback(message, color=None):
                    self.append_output(message, color or "red")

                # Load nested rates triple and pass all three to check_timesheets
                rates, rates_after, rate_change_date = self.load_rates()

                # Call backend
                check_timesheets(
                    self.file_paths['amindefied_excel'],
                    self.file_paths['sign_in_sheet'],
                    rates,
                    rates_after,
                    rate_change_date,
                    self.month,
                    progress_callback,
                    error_callback
                )

                self._write_to_output(f"\n✅ TIMESHEET CHECK COMPLETED!\n")
            except Exception as e:
                self._write_to_output(f"\n❌ ERROR: {str(e)}\n")

        threading.Thread(target=process, daemon=True).start()

def main():
    root = tk.Tk()
    app = SwimmingResultsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
