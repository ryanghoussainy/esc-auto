__version__ = "1.0.0" # Major.Minor.Patch

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkmacosx import Button
import os
import threading
import sys
from PIL import Image, ImageTk

from leahify_qualifiers import leahify_qualifiers
from check_qualifiers import check_qualifiers
from check_finals import check_finals
from colours import *

class SwimmingResultsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto House Champs")
        self.root.geometry("1200x800")
        self.root.configure(bg=APP_BACKGROUND)

        # Setup modern styles
        self.setup_modern_styles()
        
        # File paths storage
        self.file_paths = {
            'sammy_qualifiers': None,
            'leah_template': None,
            'heat_results_pdf': None,
            'finals_excel': None,
            'full_results_pdf': None
        }

        self.current_confirmation = None
        
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

        # Title label
        title_label = tk.Label(
            title_frame, 
            text="Auto House Champs", 
            font=("Segoe UI", 18, "bold"),
            bg=APP_BACKGROUND,
            fg=APP_TITLE,
        )
        title_label.pack(side=tk.LEFT)

        # Add version label
        version_label = tk.Label(
            title_frame,
            text=f"Version {__version__}",
            font=("Segoe UI", 10),
            bg=APP_BACKGROUND,
            fg=APP_TITLE,
        )
        version_label.pack(side=tk.RIGHT, padx=(0, 20))
        
        # Create main container with paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL, style="Modern.TFrame")
        main_paned.pack(expand=True, fill='both', padx=30, pady=20)
        
        # Left side - Controls
        left_frame = tk.Frame(main_paned, bg=FRAME_BACKGROUND)
        main_paned.add(left_frame, weight=1)
        
        # Right side - Output
        right_frame = tk.Frame(main_paned, bg=FRAME_BACKGROUND)
        main_paned.add(right_frame, weight=1)
        
        # Create notebook for tabs on left side
        self.notebook = ttk.Notebook(left_frame, style="Modern.TNotebook")
        self.notebook.pack(expand=True, fill='both', padx=10, pady=20)
        
        # Tab 1: Leahify Qualifiers
        self.create_leahify_tab()
        
        # Tab 2: Check Qualifiers
        self.create_check_qualifiers_tab()
        
        # Tab 3: Check Finals
        self.create_check_finals_tab()
        
        # Output panel on right side
        self.create_output_panel(right_frame)


    def setup_modern_styles(self):
        # Configure modern ttk styles
        style = ttk.Style()
        
        # Configure modern frame style
        style.configure(
            'Modern.TFrame',
            background=FRAME_BACKGROUND,
            relief='flat'
        )
        
        # Configure modern notebook style
        style.configure(
            'Modern.TNotebook'
        )
        style.configure(
            'Modern.TNotebook.Tab',
            padding=(20, 10),
            font=('Segoe UI', 12)
        )
    
    
    def create_output_panel(self, parent):
        # Output text area with modern styling
        self.output_text = scrolledtext.ScrolledText(
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
        self.output_text.pack(expand=True, fill='both', pady=(0, 20), padx=10)
        
        # Configure modern colour tags
        self.output_text.tag_configure("red", foreground=RED)
        self.output_text.tag_configure("yellow", foreground=YELLOW)
        self.output_text.tag_configure("green", foreground=GREEN)
    
    def clear_output(self):
        self.output_text.config(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state='disabled')
    
    def append_output(self, text, color=None):
        """Thread-safe method to append text to output"""
        def _append():
            if self.output_text.winfo_exists():
                try:
                    self.output_text.config(state='normal')
                    if color:
                        self.output_text.insert(tk.END, text + "\n", color)
                    else:
                        self.output_text.insert(tk.END, text + "\n")
                    self.output_text.see(tk.END)
                    self.output_text.config(state='disabled')
                except tk.TclError:
                    pass  # Widget destroyed
        
        # Ensure GUI updates happen on main thread
        self.root.after(0, _append)

    def show_confirmation_dialog(self, data: dict):
        """
        Show confirmation dialog and return user's choice

        Args:

        """
        # This will be called from a background thread, so we need to use a queue
        import queue
        result_queue = queue.Queue()
        
        def show_dialog():
            if self.current_confirmation:
                # If there's already a dialog, wait for it
                result_queue.put("wait")
                return
            
            # Create custom dialog
            dialog = tk.Toplevel(self.root)
            self.current_confirmation = dialog
            
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
                self.current_confirmation = None
                dialog.destroy()
            
            def deny():
                result_queue.put("n")
                self.current_confirmation = None
                dialog.destroy()
            
            def cancel():
                result_queue.put("exit")
                self.current_confirmation = None
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
            
            dialog.deiconify()
            dialog.lift()
            dialog.focus_force()
        
        # Show dialog on main thread
        self.root.after(0, show_dialog)
        
        # Wait for result
        while True:
            try:
                result = result_queue.get(timeout=0.1)
                if result == "wait":
                    continue
                return result
            except queue.Empty:
                # Keep the main thread responsive
                continue
    
    def _write_to_output(self, text):
        self.output_text.config(state='normal')
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state='disabled')
    
    def create_leahify_tab(self):
        frame = tk.Frame(self.notebook, bg=NOTEBOOK_TAB_BACKGROUND)
        self.notebook.add(frame, text="1. Leahify Qualifiers")
        
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
        self.create_output_file_input(frame, "Output EXCEL", 'output_file', [('Excel files', '*.xlsx')])
        
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
        frame = tk.Frame(self.notebook, bg=NOTEBOOK_TAB_BACKGROUND)
        self.notebook.add(frame, text="2. Check Qualifiers")
        
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
        frame = tk.Frame(self.notebook, bg=NOTEBOOK_TAB_BACKGROUND)
        self.notebook.add(frame, text="3. Check Finals")
        
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

    def create_output_file_input(self, parent, label_text, key, filetypes):
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
        path_var.set("No location selected (will use default: output.xlsx)")
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
        
        # Get output path or use default
        output_path = self.file_paths.get('output_file', 'output.xlsx')
        
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

def main():
    root = tk.Tk()
    app = SwimmingResultsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()