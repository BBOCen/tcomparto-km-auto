# main_gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
from io import StringIO
from process_events import start_program

class ConsoleRedirector(StringIO):
    """
    Redirects stdout to a Tkinter Text widget.
    """
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)  # Auto-scroll to the end
        self.text_widget.update()  # Update GUI

    def flush(self):
        pass

class KilometerReportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kilometer Report Generator")
        self.root.configure(bg="#f0f2f5")

        # Maximize the window to fill the screen
        self.root.state('zoomed')  # Maximizes window (keeps borders and taskbar)

        # Alternative: True full-screen mode (uncomment to use instead)
        # self.root.attributes('-fullscreen', True)
        # # Bind Esc key to exit full-screen mode
        # self.root.bind('<Escape>', lambda event: self.root.attributes('-fullscreen', False))

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TLabel", background="#f0f2f5", font=("Helvetica", 12))
        self.style.configure("TButton", font=("Helvetica", 12, "bold"))
        self.style.configure("TCombobox", font=("Helvetica", 12))
        self.style.configure(
            "Custom.TButton",
            background="#4CAF50",
            foreground="white",
            borderwidth=0,
            padding=12,
        )
        self.style.map(
            "Custom.TButton",
            background=[("active", "#45a049")],
        )

        # Main frame
        self.main_frame = ttk.Frame(self.root, padding=30)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=1)  # Make text area row expandable
        self.main_frame.grid_columnconfigure(0, weight=1)  # Make columns expandable
        self.main_frame.grid_columnconfigure(1, weight=1)

        # Title
        self.title_label = ttk.Label(
            self.main_frame,
            text="Kilometer Report Generator",
            font=("Helvetica", 20, "bold"),
            foreground="#333"
        )
        self.title_label.grid(row=0, column=0, columnspan=2, pady=20)

        # Month selection
        self.month_label = ttk.Label(self.main_frame, text="Select Month:")
        self.month_label.grid(row=1, column=0, sticky="e", padx=10, pady=10)

        self.month_var = tk.StringVar()
        self.month_combobox = ttk.Combobox(
            self.main_frame,
            textvariable=self.month_var,
            values=[f"{i:02}" for i in range(1, 13)],
            width=5,
            state="readonly"
        )
        self.month_combobox.grid(row=1, column=1, sticky="w", padx=10, pady=10)
        self.month_combobox.set("01")  # Default to January

        # Run button
        self.run_button = ttk.Button(
            self.main_frame,
            text="Generate Report",
            style="Custom.TButton",
            command=self.start_processing
        )
        self.run_button.grid(row=2, column=0, columnspan=2, pady=20)

        # Status label
        self.status_var = tk.StringVar(value="Ready to start")
        self.status_label = ttk.Label(
            self.main_frame,
            textvariable=self.status_var,
            foreground="#555",
            font=("Helvetica", 12, "italic")
        )
        self.status_label.grid(row=3, column=0, columnspan=2, pady=10)

        # Output text area
        self.output_text = tk.Text(
            self.main_frame,
            height=20,  # Increased height for larger screens
            width=80,   # Increased width for larger screens
            font=("Consolas", 12),
            wrap=tk.WORD,
            state="normal",
            bg="#ffffff",
            fg="#333",
            borderwidth=1,
            relief="solid"
        )
        self.output_text.grid(row=4, column=0, columnspan=2, pady=10, padx=10, sticky="nsew")

        # Scrollbar for text area
        self.scrollbar = ttk.Scrollbar(
            self.main_frame,
            orient="vertical",
            command=self.output_text.yview
        )
        self.scrollbar.grid(row=4, column=2, sticky="ns")
        self.output_text["yscrollcommand"] = self.scrollbar.set

        # Redirect stdout to text area
        self.console_redirector = ConsoleRedirector(self.output_text)
        sys.stdout = self.console_redirector

        # Thread lock for status updates
        self.lock = threading.Lock()

    def update_status(self, message, status_type):
        """
        Update the status label with a message and color based on status_type.
        status_type: 'info', 'error', 'success'
        """
        colors = {"info": "#555", "error": "#d32f2f", "success": "#388e3c"}
        with self.lock:
            self.root.after(0, lambda: (
                self.status_var.set(message),
                self.status_label.configure(foreground=colors.get(status_type, "#555"))
            ))

    def start_processing(self):
        """Start the processing in a separate thread."""
        month = self.month_var.get()
        if not month:
            messagebox.showerror("Error", "Please select a month.")
            return

        # Disable inputs
        self.run_button.configure(state="disabled")
        self.month_combobox.configure(state="disabled")
        self.update_status("Starting program...", "info")
        self.output_text.delete(1.0, tk.END)  # Clear previous output

        # Start processing in a new thread
        def run():
            try:
                start_program(month, self.update_status)
            except Exception as e:
                import traceback
                self.update_status(f"Error: {e}", "error")
                print("Exception in background thread:")
                traceback.print_exc()
            finally:
                self.root.after(0, self.enable_inputs)

        threading.Thread(target=run, daemon=True).start()

    def enable_inputs(self):
        """Re-enable inputs after processing."""
        self.run_button.configure(state="normal")
        self.month_combobox.configure(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = KilometerReportApp(root)
    root.mainloop()