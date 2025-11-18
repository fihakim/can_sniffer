# Importing tkinter modules
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
# Importing serial library for serial monitor
import serial.tools.list_ports
from serial import Serial, SerialException
# Import threading for parallel execution
import threading
# Import datetime module for timestamping log entries
import datetime
# Import queue for thread-safe GUI updates
import queue

# Defining class for Serial Monitor
class SerialMonitor:
    # Constructor method to initialise class
    def __init__(self, master):
        self.master = master
        self.version = "v1.4"
        # Setting title and window size
        self.master.title("Serial Monitor")
        self.master.geometry("850x400")
        # Queue for serial data
        self.serial_queue = queue.Queue()
        self.reading = False # Control flag for thread
        self.timestamping = False # Control flag for timestamping
        self.start_time = None
        # Call create_widgets method: sets up GUI components
        self.create_widgets()
        # Handle window close event
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Dropdown Menu to select COM port
        self.port_ddmenu_label = ttk.Label(self.master, text="Select Port:")
        self.port_ddmenu_label.grid(row=0, column=0, padx=10, pady=10)
        # Port dropdown menu
        self.port_ddmenu = ttk.Combobox(self.master, values=self.get_ports(), state="readonly")
        self.port_ddmenu.grid(row=0, column=1, padx=10, pady=10)
        # Bind click event to update port list
        self.port_ddmenu.bind("<Button-1>", self.update_ports)#        # Dropdown Menu to select Baud Rate
        self.baud_ddmenu_label = ttk.Label(self.master, text="Select Baud Rate:")
        self.baud_ddmenu_label.grid(row=0, column=2, padx=10, pady=10)
        self.baud_ddmenu = ttk.Combobox(self.master, values=["2400", "4800", "9600", "14400", "115200"], state="readonly")
        self.baud_ddmenu.set("115200") # Default Baud Rate value
        self.baud_ddmenu.grid(row=0, column=3, padx=10, pady=10)
        # Connect Button
        self.connect_button = ttk.Button(self.master, text="Connect", command=self.connect)
        self.connect_button.grid(row=0, column=4, padx=10, pady=10)
        # Disconnect Button
        self.disconnect_button = ttk.Button(self.master, text="Disconnect", command=self.disconnect, state=tk.DISABLED)
        self.disconnect_button.grid(row=0, column=5, padx=10, pady=10)
        # Export button to export as LOG file
        self.export_button = ttk.Button(self.master, text="Export as LOG", command=self.export_log, state=tk.DISABLED)
        self.export_button.grid(row=0, column=6, padx=10, pady=10)
        # Serial Monitor box
        self.monitor = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, width=100, height=20)
        self.monitor.grid(row=1, column=0, columnspan=7, padx=10, pady=10)

    # Method to get available ports
    def get_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports

    # Method to update port list on click
    def update_ports(self, event=None):
        ports = self.get_ports()
        self.port_ddmenu['values'] = ports

    # Method to establish serial connection
    def connect(self):
        port = self.port_ddmenu.get()
        if not port:
            self.monitor.insert(tk.END, "Error: No port selected\n")
            return
        baud = int(self.baud_ddmenu.get())
        try:
            self.ser = Serial(port, baud, timeout=1)
            # Clearing monitor for new messages
            self.monitor.delete(1.0, tk.END)
            self.timestamping = False
            self.monitor.insert(tk.END, f"Software {self.version}\n")
            self.monitor.insert(tk.END, f"Connected to {port} at {baud} baud\n")
            self.connect_button["state"] = tk.DISABLED
            self.disconnect_button["state"] = tk.NORMAL
            self.export_button["state"] = tk.NORMAL
            # Start reading from serial port
            self.reading = True
            self.thread = threading.Thread(target=self.read_from_port)
            self.thread.daemon = True # Thread will close when main app closes
            self.thread.start()
            # Start processing the queue
            self.process_serial_queue()
        except Exception as e:
            # Handling any connection errors
            self.monitor.insert(tk.END, f"Error: {str(e)}\n")

    # Method to process items from the queue and update GUI
    def process_serial_queue(self):
        try:
            # Get all items from queue without blocking
            while True:
                item = self.serial_queue.get_nowait()
                line, signal_time = item
                if "##START" in line:
                    self.timestamping = True
                    self.start_time = signal_time # Get time of signal 
                    continue
                if "##VER:" in line: # Looking for version number
                    try:
                        version_number = line.split("##VER:")[1].strip() # Getting version number from arduino script
                        self.monitor.insert(tk.END, f"Firmware v{version_number}\n") # Printing version number onto serial monitor
                    except IndexError:
                        self.monitor.insert(tk.END, line)
                    continue
                if self.timestamping and self.start_time:
                    elapsed_time = signal_time - self.start_time # Get timestamp
                    # Maths for minutes seconds and milliseconds
                    mins = int(elapsed_time.total_seconds() // 60)
                    sec = int(elapsed_time.total_seconds() % 60)
                    millis = int(elapsed_time.microseconds / 1000)
                    time = f"{mins:02}:{sec:02}:{millis:03}" # Format timestamp correctly
                    self.monitor.insert(tk.END, f"[{time}] {line}") 
                else:
                    self.monitor.insert(tk.END, line)

                self.monitor.see(tk.END)
        except queue.Empty:
            pass # Do nothing if queue is empty
        finally:
            # Schedule this function to run again after 100ms
            if self.reading:
                self.master.after(100, self.process_serial_queue)

    # Method to disconnect serial connection
    def disconnect(self):
        self.reading = False # Signal thread to stop
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
        self.connect_button["state"] = tk.NORMAL
        self.disconnect_button["state"] = tk.DISABLED
        self.export_button["state"] = tk.DISABLED
        self.monitor.insert(tk.END, "Disconnected\n")

    # Method to read from the serial port in a separate thread
    def read_from_port(self):
        while self.reading:
            try:
                line = self.ser.readline().decode("utf-8")
                if line:
                    # Put data into queue instead of updating GUI directly
                    current_time = datetime.datetime.now()
                    self.serial_queue.put((line, current_time))
            except SerialException:
                # Port was closed, break loop
                break
            except Exception as e:
                # Handle other potential read errors
                print(f"Read error: {e}")
                break

    # Method to export log data as log file
    def export_log(self):
        data = self.monitor.get(1.0, tk.END)
        # Open file dialog to choose save location
        filename = filedialog.asksaveasfilename(
            initialfile=f"signals_log_{datetime.datetime.now().strftime('%d%m%Y%H%M%S')}.log",
            defaultextension=".log",
            filetypes=[("Log Files", "*.log"), ("Text Documents", "*.txt"), ("All Files", "*.*")]
        )
        # Write file only if a filename was provided
        if filename:
            with open(filename, "w") as file:
                file.write(data)
            self.monitor.insert(tk.END, f"Log exported to: {filename}\n")

    # Method to handle window closing
    def on_closing(self):
        # Check if connected and disconnect
        if self.reading:
            self.disconnect()
        # Close the main window
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialMonitor(root)
    root.mainloop()