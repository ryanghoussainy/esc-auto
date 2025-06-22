import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import tkinterdnd2 as tkdnd
import os
import threading
import sys
import re

from leahify_qualifiers import leahify_qualifiers
from check_qualifiers import check_qualifiers
from check_finals import check_finals

class OutputCapture:
    """Context manager to capture print statements and user input"""
    def __init__(self, output_widget, input_callback=None):
        self.output_widget = output_widget
        self.input_callback = input_callback
        self.old_stdout = None
        self.old_stdin = None
        
    def __enter__(self):
        self.old_stdout = sys.stdout
        self.old_stdin = sys.stdin
        sys.stdout = self
        if self.input_callback:
            sys.stdin = self
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout
        sys.stdin = self.old_stdin
        
    def write(self, text):
        # Write all text, including newlines
        if self.output_widget.winfo_exists():
            try:
                self.output_widget.after_idle(lambda: self._write_to_widget(text))
            except tk.TclError:
                pass  # Widget destroyed
        return len(text)
        
    def _write_to_widget(self, text):
        try:
            if not self.output_widget.winfo_exists():
                return
                
            self.output_widget.config(state='normal')
            self._insert_colored_text(text)
            self.output_widget.see(tk.END)
            self.output_widget.config(state='disabled')
        except tk.TclError:
            pass  # Widget destroyed or not accessible
    
    def _insert_colored_text(self, text):
        """Insert text with color support by parsing ANSI escape codes"""
        # ANSI color code pattern
        ansi_pattern = r'\033\[(\d+)m'
        
        # Split text by ANSI codes
        parts = re.split(ansi_pattern, text)
        
        current_color = None
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Text part
                if current_color:
                    self.output_widget.insert(tk.END, part, current_color)
                else:
                    self.output_widget.insert(tk.END, part)
            else:  # Color code part
                color_code = int(part)
                if color_code == 91:  # Red
                    current_color = "red"
                elif color_code == 93:  # Yellow
                    current_color = "yellow"
                elif color_code == 92:  # Green
                    current_color = "green"
                elif color_code == 0:  # Reset
                    current_color = None
        
    def flush(self):
        pass
        
    def readline(self):
        if self.input_callback:
            return self.input_callback()
        return "\n"

class SwimmingResultsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("House Champs Times")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f8f9fa')

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
        
        # Variables for user input handling
        self.waiting_for_input = False
        self.input_result = None
        self.input_prompt = ""
        self.input_validation_attempts = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main title
        title_label = tk.Label(
            self.root, 
            text="House Champs Times", 
            font=("Segoe UI", 24, "bold"),
            bg='#f8f9fa',
            fg='#212529',
        )
        title_label.pack(pady=20)
        
        # Create main container with paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL, style="Modern.TFrame")
        main_paned.pack(expand=True, fill='both', padx=30, pady=20)
        
        # Left side - Controls
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Right side - Output
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        # Create notebook for tabs on left side
        self.notebook = ttk.Notebook(left_frame, style="Modern.TNotebook")
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
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
        
        # Configure modern button style
        style.configure(
            'Modern.TButton',
            font=('Segoe UI', 10),
            padding=(20, 10)
        )
        
        # Configure modern frame style
        style.configure(
            'Modern.TFrame',
            background='#ffffff',
            relief='flat'
        )
        
        # Configure modern notebook style
        style.configure(
            'Modern.TNotebook',
            background='#f8f9fa',
            borderwidth=0
        )
        style.configure(
            'Modern.TNotebook.Tab',
            padding=(20, 10),
            font=('Segoe UI', 10)
        )
    
    
    def create_output_panel(self, parent):
        # Output text area with modern styling
        self.output_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            width=50,
            height=20,
            font=("JetBrains Mono", 10),
            bg='#1e1e1e',
            fg='#d4d4d4',
            state='disabled',
            borderwidth=0,
            highlightthickness=1,
            highlightcolor='#0078d4',
            insertbackground='#d4d4d4',
            relief='flat'
        )
        self.output_text.pack(expand=True, fill='both', pady=(0, 20), padx=10)
        
        # Configure modern color tags
        self.output_text.tag_configure("red", foreground="#ff6b6b")
        self.output_text.tag_configure("yellow", foreground="#ffd93d")
        self.output_text.tag_configure("green", foreground="#6bcf7f")
        
        # Modern input frame
        self.input_frame = tk.Frame(parent, bg='#f8f9fa')
        
        input_container = tk.Frame(self.input_frame, bg='#f8f9fa')
        input_container.pack(fill=tk.X, pady=(0, 20), padx=10)
        
        self.input_entry = tk.Entry(
            input_container,
            font=("Segoe UI", 11),
            width=35,
            relief='flat',
            borderwidth=0,
            highlightthickness=2,
            highlightcolor='#0078d4',
            bg='#ffffff',
            fg='#212529'
        )
        self.input_entry.pack(side=tk.LEFT, padx=(0, 15), ipady=8)
        self.input_entry.bind('<Return>', self.handle_input_submit)
        
        self.input_submit_btn = ttk.Button(
            input_container,
            text="Submit",
            command=self.handle_input_submit,
            style='Modern.TButton'
        )
        self.input_submit_btn.pack(side=tk.LEFT)
    
    def clear_output(self):
        self.output_text.config(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state='disabled')
    
    def show_input_prompt(self, prompt):
        self.input_prompt = prompt
        self.input_frame.pack(fill=tk.X, pady=(0, 10))
        self.input_entry.focus_set()
        self.waiting_for_input = True
        self.input_validation_attempts = 0
    
    def hide_input_prompt(self):
        self.input_frame.pack_forget()
        self.waiting_for_input = False
        self.input_entry.delete(0, tk.END)
        self.input_validation_attempts = 0
    
    def handle_input_submit(self, event=None):
        if self.waiting_for_input:
            user_input = self.input_entry.get()
            self.input_result = user_input
            self.hide_input_prompt()
    
    def get_user_input(self):
        # Extract the prompt from the last few lines written to output
        all_text = self.output_text.get(1.0, tk.END).strip()
        lines = all_text.split('\n')
        
        # Look for the last line that contains a prompt pattern
        prompt = ""
        for line in reversed(lines):
            clean_line = re.sub(r'\033\[\d+m', '', line).strip()
            if clean_line and ("?" in clean_line or ":" in clean_line):
                prompt = clean_line
                break
        
        if not prompt and lines:
            # Fallback to last non-empty line
            for line in reversed(lines):
                clean_line = re.sub(r'\033\[\d+m', '', line).strip()
                if clean_line:
                    prompt = clean_line
                    break
        
        # Show the input prompt in GUI
        self.root.after(0, lambda: self.show_input_prompt(prompt))
        
        # Wait for user input
        while self.waiting_for_input and self.input_result is None:
            self.root.update()
            threading.Event().wait(0.1)

        result = self.input_result
        self.input_result = None

        # Don't echo the input - let the underlying logic handle all output
        return f"{result}\n" if result else "\n"
    
    def _write_to_output(self, text):
        self.output_text.config(state='normal')
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state='disabled')
    
    def create_leahify_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="1. Leahify Qualifiers")
        
        # Instructions
        instructions = tk.Label(
            frame,
            text="Convert Sammy's qualifier format to Leah's format",
            font=("Segoe UI", 12),
            bg="#ffffff",
            fg="#6c757d",
            wraplength=400
        )
        instructions.pack(pady=20)
        
        # File input areas
        self.create_file_input(frame, "Sammy's Qualifiers File (.xlsx)", 'sammy_qualifiers', [('Excel files', '*.xlsx')])
        self.create_file_input(frame, "Leah's Template File (.xls)", 'leah_template', [('Excel files', '*.xls *.xlsx')])

        # Output file selection
        self.create_output_file_input(frame, "Output File Location", 'output_file', [('Excel files', '*.xlsx')])
        
        # Process button
        process_btn = ttk.Button(
            frame,
            text="Process Files",
            command=self.run_leahify,
            style="Modern.TButton",
        )
        process_btn.pack(pady=30)
    
    def create_check_qualifiers_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="2. Check Qualifiers")
        
        # Instructions
        instructions = tk.Label(
            frame,
            text="Check the generated qualifiers against heat results PDF",
            font=("Segoe UI", 12),
            bg="#ffffff",
            fg="#6c757d",
            wraplength=400
        )
        instructions.pack(pady=20)
        
        # File input areas
        self.create_file_input(frame, "Generated Output File (output.xlsx)", 'output_excel', [('Excel files', '*.xlsx')])
        self.create_file_input(frame, "Heat Results PDF", 'heat_results_pdf', [('PDF files', '*.pdf')])
        
        # Process button
        process_btn = ttk.Button(
            frame,
            text="Check Files",
            command=self.run_check_qualifiers,
            style="Modern.TButton",
        )
        process_btn.pack(pady=30)
    
    def create_check_finals_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="3. Check Finals")
        
        # Instructions
        instructions = tk.Label(
            frame,
            text="Check finals results against full results PDF",
            font=("Segoe UI", 12),
            bg="#ffffff",
            fg="#6c757d",
            wraplength=400
        )
        instructions.pack(pady=20)
        
        # File input areas
        self.create_file_input(frame, "Finals Excel File", 'finals_excel', [('Excel files', '*.xlsx')])
        self.create_file_input(frame, "Full Results PDF", 'full_results_pdf', [('PDF files', '*.pdf')])
        
        # Process button
        process_btn = ttk.Button(
            frame,
            text="Check Finals",
            command=self.run_check_finals,
            style="Modern.TButton",
        )
        process_btn.pack(pady=30)
    
    def create_file_input(self, parent, label_text, key, filetypes):
        # Container frame
        container = tk.Frame(parent, bg='white', relief=tk.RAISED, bd=1)
        container.pack(fill=tk.X, padx=10, pady=10)
        
        # Label
        label = tk.Label(container, text=label_text, font=("Arial", 10, "bold"), bg='white')
        label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Drop area
        drop_frame = tk.Frame(container, bg='#ecf0f1', height=60, relief=tk.SUNKEN, bd=2)
        drop_frame.pack(fill=tk.X, padx=10, pady=5)
        drop_frame.pack_propagate(False)
        
        drop_label = tk.Label(
            drop_frame,
            text="Drag & Drop file here or click to browse",
            bg='#ecf0f1',
            fg='#7f8c8d',
            font=("Arial", 9)
        )
        drop_label.pack(expand=True)
        
        # File path display
        path_var = tk.StringVar()
        path_label = tk.Label(container, textvariable=path_var, bg='white', fg='#2c3e50', wraplength=400)
        path_label.pack(anchor=tk.W, padx=10, pady=(0, 10))
        
        # Store references
        setattr(self, f'{key}_var', path_var)
        setattr(self, f'{key}_frame', drop_frame)
        
        # Bind click event
        drop_frame.bind("<Button-1>", lambda e: self.browse_file(key, filetypes))
        drop_label.bind("<Button-1>", lambda e: self.browse_file(key, filetypes))
        
        # Enable drag and drop
        drop_frame.drop_target_register(tkdnd.DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', lambda e: self.handle_drop(e, key))

    def create_output_file_input(self, parent, label_text, key, filetypes):
        # Container frame
        container = tk.Frame(parent, bg='white', relief=tk.RAISED, bd=1)
        container.pack(fill=tk.X, padx=10, pady=10)
        
        # Label
        label = tk.Label(container, text=label_text, font=("Arial", 10, "bold"), bg='white')
        label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Browse button and path display in same row
        button_frame = tk.Frame(container, bg='white')
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        browse_btn = tk.Button(
            button_frame,
            text="Choose Location",
            command=lambda: self.browse_output_file(key, filetypes),
            bg='#3498db',
            fg='white',
            font=("Arial", 9)
        )
        browse_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # File path display
        path_var = tk.StringVar()
        path_var.set("No location selected (will use default: output.xlsx)")
        path_label = tk.Label(button_frame, textvariable=path_var, bg='white', fg='#2c3e50', wraplength=300)
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
    
    def handle_drop(self, event, key):
        files = self.root.tk.splitlist(event.data)
        if files:
            self.set_file_path(key, files[0])
    
    def set_file_path(self, key, path):
        self.file_paths[key] = path
        path_var = getattr(self, f'{key}_var')
        path_var.set(f"Selected: {os.path.basename(path)}")
        
        # Update drop area appearance
        drop_frame = getattr(self, f'{key}_frame')
        drop_frame.configure(bg='#d5f4e6')
        for child in drop_frame.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(bg='#d5f4e6', fg='#27ae60', text="✓ File loaded")
    
    def run_leahify(self):
        if not self.file_paths['sammy_qualifiers'] or not self.file_paths['leah_template']:
            messagebox.showerror("Error", "Please select both required files")
            return
        
        # Get output path or use default
        output_path = self.file_paths.get('output_file', 'output.xlsx')
        
        def process():
            try:
                self.clear_output()
                
                with OutputCapture(self.output_text, self.get_user_input):
                    leahify_qualifiers(
                        self.file_paths['sammy_qualifiers'],
                        self.file_paths['leah_template'],
                        output_path  # Pass the output path
                    )
                
                self._write_to_output(f"\n✅ FILES PROCESSED SUCCESSFULLY! Output saved as '{output_path}'\n")
            except Exception as e:
                self._write_to_output(f"\n❌ ERROR: {str(e)}\n")
        
        # Run in separate thread to prevent GUI freezing
        threading.Thread(target=process, daemon=True).start()
    
    def run_check_qualifiers(self):
        output_path = self.file_paths.get('output_excel') or 'output.xlsx'
        if not self.file_paths['heat_results_pdf']:
            messagebox.showerror("Error", "Please select the heat results PDF file")
            return
        
        def process():
            try:
                self.clear_output()
                
                with OutputCapture(self.output_text, self.get_user_input):
                    check_qualifiers(output_path, self.file_paths['heat_results_pdf'])
                
                self._write_to_output("\n✅ QUALIFIER CHECK COMPLETED!\n")
            except Exception as e:
                self._write_to_output(f"\n❌ ERROR: {str(e)}\n")
        
        threading.Thread(target=process, daemon=True).start()
    
    def run_check_finals(self):
        if not self.file_paths['finals_excel'] or not self.file_paths['full_results_pdf']:
            messagebox.showerror("Error", "Please select both required files")
            return
        
        def process():
            try:
                self.clear_output()
                
                with OutputCapture(self.output_text, self.get_user_input):
                    check_finals(
                        self.file_paths['finals_excel'],
                        self.file_paths['full_results_pdf']
                    )
                
                self._write_to_output("\n✅ FINALS CHECK COMPLETED!\n")
            except Exception as e:
                self._write_to_output(f"\n❌ ERROR: {str(e)}\n")
        
        threading.Thread(target=process, daemon=True).start()

def main():
    root = tkdnd.TkinterDnD.Tk()
    app = SwimmingResultsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()