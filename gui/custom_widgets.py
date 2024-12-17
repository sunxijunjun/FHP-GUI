import time
import tkinter as tk
from datetime import datetime
from datetime import timedelta
from typing import Callable, Union
from PIL import Image, ImageTk
import ui_config
from database_manager import UserDetails
from data_analyst import DataAnalyst
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import SpanSelector
from matplotlib.patches import Rectangle
from matplotlib.axes import Axes
import random
from logger import Logger
from tkinter import ttk, messagebox
from sound_player import play_sound_in_thread


class TkCustomImage:
    """ Store 3 type of images:
    1. Original image as np.array
    2. Scaled image as np.array
    3. Tk image of scaled image
    """

    def __init__(self, file_path: str, w: int, h: int):
        self.original_image = Image.open(file_path)
        self.scaled_image = self.original_image.resize((w, h), resample=Image.LANCZOS)
        self.tk_image: tk.PhotoImage = ImageTk.PhotoImage(image=self.scaled_image)

    def attach_image(self, master, row: int, col: int) -> ttk.Label:
        image_label = ttk.Label(master)
        image_label.image = self.tk_image
        image_label.grid(row=row, column=col, padx=5, pady=5)
        return image_label


class Clock(ttk.Frame):
    """ The clock widget to show the time elapsed """

    def __init__(self, parent, app, start=True):
        super().__init__(parent)
        self.app = app
        self.is_started = start
        self.start_time = datetime.now()
        self.paused_time = None
        self.total_paused_duration = timedelta(0)
        self.time_label = ttk.Label(self, font=("Helvetica", 48))
        self.time_label.pack(pady=20)
        self.update_time()

    def update_time(self):
        if not self.app.is_paused:
            if self.paused_time:
                # Calculate the total paused duration
                self.total_paused_duration += datetime.now() - self.paused_time
                self.paused_time = None

            elapsed_time = datetime.now() - self.start_time - self.total_paused_duration
            time_str = str(timedelta(seconds=int(elapsed_time.total_seconds())))
            self.time_label.configure(text=time_str)
        else:
            if not self.paused_time:
                self.paused_time = datetime.now()
        
        self.after(1000, self.update_time)


class CountDownClock:
    def __init__(self, parent, initial_time=60, close_callback=None, start_callback=None):
        self.parent = parent
        self.initial_time = initial_time
        self.time_remaining = initial_time
        self.close_callback = close_callback
        self.start_callback = start_callback
        self.label = ttk.Label(self.parent, font=ui_config.Fonts.title_font)
        self.label.pack(pady=20)
        self.display(new_time=(self.time_remaining - 1))

        self.is_running = False

        # Testing buttons
        self.start_button = self.add_button(text="Start", func=self.start)
        self.stop_button = self.add_button(text="Stop", func=self.stop)

    def add_button(self, text: str, func: Callable) -> ttk.Button:
        button = ttk.Button(self.parent, text=text, command=func)
        button.pack(pady=10)
        return button

    def start(self):
        if not self.is_running:
            if self.start_callback:
                self.start_callback()
                print("STARTED")
            self.is_running = True
            self.countdown()

    def stop(self):
        self.is_running = False

    def countdown(self):
        if self.is_running:
            self.display(new_time=(self.time_remaining - 1))
            if self.time_remaining > 0:
                self.time_remaining -= 1
                self.label.after(1000, self.countdown)
            else:
                self.stop()
                if self.close_callback:
                    self.close_callback()
                    print("ENDED")

    def display(self, new_time):
        minutes = int(new_time // 60)
        seconds = int(new_time % 60)
        self.label.config(text=f"{minutes:02d}:{seconds:02d}")


class AbstractWindow(tk.Toplevel):
    def __init__(self, parent, title: str):
        super().__init__()
        self.title(title)
        self.parent = parent
        self.submission_button = None
        self.button_nums = 0
        self.message_frame = None

    def close(self):
        self.destroy()

    def clear_messages(self):
        if self.message_frame:
            self.message_frame.destroy()

    def show_message_frame(self, subject: str, details: str, row=4, col=0):
        self.clear_messages()  # remove previous messages
        frame = ttk.LabelFrame(self, text=subject)
        frame.grid(row=row, column=col, padx=10, pady=10)
        details_label = ttk.Label(frame, text=details)
        details_label.pack()
        delay: int = ui_config.Measurements.pop_up_closing_delay.value
        self.message_frame = frame
        if subject != "Error":
            self.after(delay, func=self.close)

    def disable_submission_button(self):
        button: ttk.Button = self.submission_button
        button.config(command=self.do_nothing)

    def add_button(self, txt: str, func: Callable, row: int = 3):
        # Submit button
        submit_button = ttk.Button(self, text=txt, command=func)
        submit_button.grid(row=row, column=self.button_nums, padx=10, pady=10)
        self.submission_button = submit_button
        self.button_nums += 1

    @staticmethod
    def do_nothing():
        pass


class UserDetailsWindow(AbstractWindow):
    def __init__(self, parent, title: str, read_data: bool = True):
        super().__init__(parent, title)
        self.full_name_entry = None
        self.password_entry = None
        self.remember_name = str()
        self.remember_password = str()

        if read_data:
            #try to get data from user_account.txt
            try:
                with open('user_account.txt', 'r') as file:
                    # read the first line as user name
                    self.remember_name = file.readline().strip()
                    # read the first line as password
                    self.remember_password  = file.readline().strip()
            except FileNotFoundError:
                #defalt
                pass

        # Create the widgets
        self.create_widgets()

    def create_widgets(self):
        # Full name label and entry
        full_name_label = ttk.Label(self, text="Full Name (e.g. Zhang San):")
        full_name_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.full_name_entry = ttk.Entry(self)
        self.full_name_entry.grid(row=0, column=1, padx=10, pady=10)
        self.full_name_entry.insert(0, self.remember_name)

        # Password label and entry
        password_label = ttk.Label(self, text="Password:")
        password_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)
        self.password_entry.insert(0, self.remember_password)

        # "Remember me" checkbox
        self.remember_var = tk.BooleanVar(value=True)
        remember_check = ttk.Checkbutton(self, text="Remember me", variable=self.remember_var)
        remember_check.grid(row=2, columnspan=2, pady=5)

    def get_entered_details(self) -> UserDetails:
        """ Get the values from popupfields as str
        and return as UserDetails object
        """
        # Get the values from the entry fields
        full_name: str = self.full_name_entry.get()
        if(len(full_name.split())<2):
            messagebox.showwarning("Input Error", "Please enter your full name. Example: Jone Doe, Chan Tai Man")
        password: str = self.password_entry.get()
        if(not password):
            messagebox.showwarning("Input Error", "Please enter your password.")
        details = UserDetails(full_name, password)

        #save user_account
        if self.remember_var.get():
            with open("user_account.txt", "w") as f:
                f.write(f"{full_name}\n{password}")
        else:
            with open("user_account.txt", "w") as f:
                f.write("")

        return details

class DateOfBirthEntry(ttk.Entry):
    def __init__(self, parent, row, column, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.day_var = tk.StringVar(self)
        self.month_var = tk.StringVar(self)
        self.year_var = tk.StringVar(self)
        self.date_var = tk.StringVar(self)

        self.days = [str(i) for i in range(1, 32)]
        self.months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        current_year = datetime.now().year
        default_year = 1990
        self.years = [str(i) for i in range(1900, current_year + 1)]

        # Set default values
        self.day_var.set(self.days[0])
        self.month_var.set(self.months[0])
        self.year_var.set(default_year)

        # Hide the parent Entry
        self.grid_remove()

        # Create a frame to hold the dropdowns
        self.dropdown_frame = ttk.Frame(parent)
        self.dropdown_frame.grid(row=row, column=column, padx=2, pady=10, sticky="w")

        # Place the dropdowns inside the frame
        self.day_dropdown = ttk.OptionMenu(self.dropdown_frame, self.day_var, self.days[0], *self.days, command=self.update_date)
        self.day_dropdown.grid(row=0, column=0, padx=2, pady=10, sticky="w")

        self.month_dropdown = ttk.OptionMenu(self.dropdown_frame, self.month_var, self.months[0], *self.months, command=self.update_date)
        self.month_dropdown.grid(row=0, column=1, padx=2, pady=10, sticky="w")

        self.year_dropdown = ttk.OptionMenu(self.dropdown_frame, self.year_var, default_year, *self.years, command=self.update_date)
        self.year_dropdown.grid(row=0, column=2, padx=2, pady=10, sticky="w")

        self.update_date()

    def update_date(self, *args):
        day = self.day_var.get()
        month = self.month_var.get()
        year = self.year_var.get()

        # Update the day dropdown based on the selected month and year
        days_in_month = self.get_days_in_month(month, year)
        self.update_day_dropdown(days_in_month)

        date_str = f"{day}-{month}-{year}"
        self.date_var.set(date_str)

    def get_days_in_month(self, month, year):
        month_days = {
            "Jan": 31, "Feb": 28, "Mar": 31, "Apr": 30, "May": 31, "Jun": 30,
            "Jul": 31, "Aug": 31, "Sep": 30, "Oct": 31, "Nov": 30, "Dec": 31
        }
        if month == "Feb" and self.is_leap_year(int(year)):
            return 29
        return month_days[month]

    def is_leap_year(self, year):
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    def update_day_dropdown(self, days_in_month):
        current_day = int(self.day_var.get())
        self.days = [str(i) for i in range(1, days_in_month + 1)]
        menu = self.day_dropdown["menu"]
        menu.delete(0, "end")
        for day in self.days:
            menu.add_command(label=day, command=lambda value=day: self.day_var.set(value))
        if current_day > days_in_month:
            self.day_var.set(str(days_in_month))
        else:
            self.day_var.set(str(current_day))

    def get(self):
        day = self.day_var.get()
        month_str = self.month_var.get()
        year = self.year_var.get()
        month = self.months.index(month_str) + 1
        date = datetime(int(year), month, int(day))
        return date.strftime("%d-%m-%Y")

class UserRegistrationWindow(UserDetailsWindow):
    def __init__(self, parent, title):
        super().__init__(parent, title, read_data = False)
        # Basic memory cells
        self.data_entries_num = 4  # minimum is 4, because other 4 [0-3] are taken for name, password, remember, and buttons
        self.message_location = (7, 3)
        self.category_selection = None
        # Add Shoulder Size categories
        shoulder_sizes: list[str] = ui_config.ElementNames.shoulder_options.value
        self.shoulder_size_var = self.add_category_selection(options=shoulder_sizes,
                                                             name=ui_config.ElementNames.shoulder_category_txt.value)
        # Add Gender categories
        gender_options: list[str] = ui_config.ElementNames.gender_options.value
        self.gender_var = self.add_category_selection(options=gender_options,
                                                      name=ui_config.ElementNames.gender_category_txt.value)
        # Add Date of Birth Selection
        self.date_entry = self.add_date_selection(label_name="Date of Birth")
        # Add numeral entry of data
        self.weight_var, self.weight_entry = self.add_numeral_selection(limit=(30, 300), name="Weight (KG)")
        self.height_var, self.height_entry = self.add_numeral_selection(limit=(100, 300), name="Height (CM)")

    def add_category_selection(self, options: list, name: str) -> tk.StringVar:
        """
        Add a dropdown selection for categories.
        :param options is a list of the categories
        :param name is the category name
        :returns address which will contain selected category for retrieval
        """
        category_label = ttk.Label(self, text=f"{name}:")
        category_label.grid(row=self.data_entries_num, column=0, padx=10, pady=10, sticky="e")

        selection_address = tk.StringVar(self)
        selection_address.set(options[0])  # Set the default value

        category_dropdown = ttk.OptionMenu(self, selection_address, options[0], *options)
        category_dropdown.grid(row=self.data_entries_num, column=1, padx=10, pady=10)
        self.data_entries_num += 1
        return selection_address

    def add_date_selection(self, label_name: str):
        date_label = ttk.Label(self, text=label_name)
        date_label.grid(row=self.data_entries_num, column=0, padx=10, pady=10, sticky="e")
        date_field = DateOfBirthEntry(self, row=self.data_entries_num, column=1)
        date_field.grid(row=self.data_entries_num, column=1, padx=10, pady=10)
        self.data_entries_num += 1
        return date_field

    def clear_date_placeholder(self, event=None):
        if self.date_entry.get() == "dd-mm-yyyy":
            self.date_entry.delete(0, tk.END)

    def validate_date(self, event=None):
        date_str = self.date_entry.get()
        try:
            date = datetime.strptime(date_str, "%d-%m-%Y")
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, date.strftime("%d-%m-%Y"))
        except ValueError:
            if date_str == "":
                self.date_entry.insert(0, "dd-mm-yyyy")
            else:
                self.show_message_frame("Error", "Please enter a valid date in the format dd-mm-yyyy.",
                                        row=self.message_location[0],
                                        col=self.message_location[1])

    def add_numeral_selection(self, limit: tuple, name: str) -> tuple[tk.IntVar, ttk.Entry]:
        num_label = ttk.Label(self, text=name)
        num_label.grid(row=self.data_entries_num, column=0, padx=10, pady=10, sticky="e")
        selection_variable = tk.IntVar()
        selection_variable.set(limit[0])
        selection_entry = ttk.Entry(self, textvariable=selection_variable, width=5)
        selection_entry.grid(row=self.data_entries_num, column=1, padx=10, pady=10)
        selection_entry.bind("<FocusOut>", lambda event: self.validate_number(limit, name, selection_variable))
        self.data_entries_num += 1
        return selection_variable, selection_entry

    def validate_number(self, limit: tuple, name: str, selection_variable: tk.IntVar, event=None):
        """
        Validates the numerical input entered by the user.

        Args:
            limit (tuple): A tuple containing the minimum and maximum values for the input.
            name (str): The name of the input field.
            selection_variable (int): it a num containing the selected value
            event: contains callback info
        """
        input_value = selection_variable.get()
        try:
            value = int(input_value)
            if limit[0] <= value <= limit[1]:
                return  # Valid input
            else:
                self.show_message_frame("Error", f"{name} must be between {limit[0]} and {limit[1]}.",
                                        row=self.message_location[0],
                                        col=self.message_location[1])
                selection_variable.set("")
        except ValueError:
            self.show_message_frame("Error", f"{name} must be a valid integer.",
                                    row=self.message_location[0],
                                    col=self.message_location[1])
            selection_variable.set("")

    def get_entered_details(self) -> UserDetails:
        details: UserDetails = super().get_entered_details()
        # get other details
        details.weight = self.weight_var.get()
        details.height = self.height_var.get()
        details.shoulder_size = self.shoulder_size_var.get()
        details.age = self.date_entry.get()
        details.gender = self.gender_var.get()
        return details


class FileUploadWindow(AbstractWindow):
    def __init__(self, parent, title: str):
        super().__init__(parent, title)
        # Remember the fields
        self.file_path_entry = None
        # Create the widgets
        self.create_widgets()

    def create_widgets(self):
        # File path label and entry
        file_path_label = ttk.Label(self, text="File Path:")
        file_path_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.file_path_entry = ttk.Entry(self)
        self.file_path_entry.grid(row=0, column=1, padx=10, pady=10)

    def get_file_path(self) -> str:
        return self.file_path_entry.get()


class NotesEntryFrame(ttk.Frame):
    def __init__(self, parent, title=""):
        super().__init__(parent)
        self.add_header_text(title)
        self.paragraph_entry = tk.Text(self, height=5, width=50, wrap="word")
        self.paragraph_entry.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        self.control_button_frame = ttk.Frame(self)
        self.control_button_frame.pack(side=tk.BOTTOM, fill='x')
        self.add_scroll_bar()

    def add_header_text(self, title: str) -> None:
        header_label = ttk.Label(self, text=title, font=ui_config.Fonts.title_font.value)
        header_label.pack(side=tk.TOP, padx=10, pady=10)

    def add_scroll_bar(self) -> None:
        scrollbar = tk.Scrollbar(self, command=self.paragraph_entry.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.paragraph_entry.config(yscrollcommand=scrollbar.set)

    def add_button(self, text: str, func: Callable) -> None:
        save_button = ttk.Button(self.control_button_frame, text=text, command=func)
        save_button.pack(side=tk.LEFT, fill='x')

    def get_notes(self) -> str:
        return self.paragraph_entry.get("1.0", tk.END).strip()


class GraphScrollBar(tk.Scrollbar):
    def __init__(self, parent, options: list[int], figure_func: Callable):
        super().__init__(parent)
        self.config(orient=tk.HORIZONTAL)
        self.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.list_box = self.add_listbox(parent, options)
        self.config(command=self.list_box.xview)
        self.bind('<Motion>', self.scroll_callback)
        self.update_figure_func = figure_func
        self.move_cursor_end()

    def add_listbox(self, parent, options: list[int]):
        box = tk.Listbox(parent, xscrollcommand=self.set, selectmode=tk.EXTENDED, height=1)
        item_string = " ".join([str(option) for option in range(len(options))])
        box.insert(tk.END, item_string)
        box.config(background='#f0f0f0', bd=0, highlightthickness=0)
        box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        return box

    def scroll_callback(self, event=None):
        # Get the visible range of the Listbox
        first, last = self.list_box.xview()
        lower, upper = self.get_visible_range(lower_range=first,
                                              upper_range=last)
        self.update_figure_func(lower_range=lower, upper_range=upper)

    def get_visible_range(self, lower_range: float, upper_range: float) -> tuple:
        """ The function determine which of the listbox elements are visible for the user
        and figure to be updated
        :returns range as a tuple(from_int, to_int)
        """
        string_options: str = self.list_box.get(0)
        options: list[int] = [int(option) for option in string_options.split()]
        first_el = options[int(lower_range * len(options))]
        last_el = options[int(upper_range * len(options)) - 1]
        # print(f"X_first: {lower_range}, X_last: {upper_range}")
        # print(f"First: {first_el}, Last: {last_el}")
        return first_el, last_el

    def move_cursor_end(self):
        # Scroll to the end of the Listbox
        self.list_box.xview_moveto(1.0)

    def destroy(self):
        super().destroy()
        # self.list_box.destroy()


class TimeIntervalSelectorFrame(ttk.Frame):
    pad_x = ui_config.Measurements.widgets_padding.value
    pad_y = 5

    def __init__(self, parent, row: int, col: int, txt: str, func: Callable):
        super().__init__(parent)
        self.parent = parent
        self.row = row
        self.col = col
        self.time_format = "MM:SS"  # minutes:seconds, which acts as placeholder
        self.interval_field = ttk.Entry()
        self.add_button(txt, func)
        self.add_timer_selection_field()

    def add_button(self, text: str, func: Callable) -> None:
        button = ttk.Button(self.parent, text=text, command=func)
        button.grid(row=self.row, column=self.col, pady=5, padx=(10, 5), columnspan=2, sticky="n")

    def add_timer_selection_field(self) -> None:
        field = ttk.Entry(self.parent)
        # set placeholder
        field.insert(0, self.time_format)
        field.bind(sequence="<FocusIn>", func=self.remove_placeholder)
        field.grid(row=self.row, column=self.col + 2, pady=5, padx=(10, 5), sticky="n")
        self.interval_field = field

    def remove_placeholder(self, event=None) -> None:
        if self.interval_field.get() == self.time_format:
            self.interval_field.delete(0, tk.END)

    def get_interval(self) -> int:
        value = self.interval_field.get()
        values: list[str] = value.split(":")
        minutes = int(values[0])
        seconds = int(values[1])
        total_seconds = minutes * 60 + seconds
        return total_seconds


class CheckBoxesFrame(ttk.Frame):
    """ Frame contain the list of the checkboxes the user would like to select
    this allows to set some of the options, such as:
    1. I want to be notified if I maintained a bad posture for X minutes
    2. Enable or disable alarm sound

    Attributes:
        check_boxes is a dictionary with key as a specific name of the checkbox
        check_boxes values are (tk.Checkbutton, tk.BooleanVar)
    """
    check_boxes: dict[str,
                      tuple[tk.Checkbutton,
                            tk.BooleanVar,
                            Union[None, ttk.Entry]
                            ]
                      ]
    pad_x = ui_config.Measurements.widgets_padding.value
    pad_y = 5

    def __init__(self, parent, row: int, col: int):
        super().__init__(parent)
        self.check_boxes = dict()
        self.grid(row=row, column=col, padx=self.pad_x, pady=self.pad_y)
        self.add_check_box(text="Notify Bad Posture After",
                           access_key=ui_config.CheckBoxesKeys.notification_bad_posture.value,
                           add_input=True)
        self.add_check_box(text="Enable Sound",
                           access_key=ui_config.CheckBoxesKeys.enable_sound.value)
        self.add_check_box("Enable Light", access_key=ui_config.CheckBoxesKeys.enable_light.value)
        self.grid_remove()

    def add_check_box(self, text: str, access_key: str, add_input=False) -> None:
        var = tk.BooleanVar(value=False)
        row, col = len(self.check_boxes), 0
        label = ttk.Label(self, text=text, wraplength=100)
        box = ttk.Checkbutton(self, variable=var)
        box.grid(row=row, column=col, sticky="w", padx=5)
        label.grid(row=row, column=col+1, sticky="w", padx=5)
        entry_field = None
        if add_input:
            entry_field = self.add_entry_field(row=row, col=col)
        zipped_value = (box, var, entry_field)
        self.check_boxes[access_key] = zipped_value

    def add_entry_field(self, row: int, col: int) -> ttk.Entry:
        """ The function add the input field to the right of the created checkbox """
        entry = ttk.Entry(self)
        entry.grid(row=row, column=col + 2, padx=5)
        entry.config(width=5)
        return entry

    def is_true(self, access_key: str) -> bool:
        return self.check_boxes[access_key][1].get()

    def get_input_value(self, access_key: str) -> str:
        input_field = self.check_boxes[access_key][2]
        value = ""
        if input_field and input_field.winfo_exists():  # 检查输入框是否仍然存在
            value = input_field.get()
        if value == "":
            return "0.0"
        return value

    def get_check_box(self, access_key: str) -> tk.Checkbutton:
        return self.check_boxes[access_key][0]


class NotificationBar(ttk.LabelFrame):
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent, text=title)
        self.content = self.add_message(message=message)

    def show(self, x: int, y: int, callback: Union[None, Callable],
             delay=ui_config.Measurements.notification_delay.value):
        # Calculate the screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Ensure the notification is within the screen boundaries
        x = max(0, min(x, screen_width - self.winfo_width()))
        y = max(0, min(y, screen_height - self.winfo_height()))

        # Position the notification
        self.place(x=x, y=y)

        if callback:
            self.after(delay, func=callback)

    def add_message(self, message: str) -> tk.Text:
        text_box = tk.Text(self, height=20)
        text_box.insert(tk.INSERT, message)
        text_box.pack(side=tk.TOP, expand=False, fill=tk.X)
        return text_box

    def destroy(self):
        self.content.destroy()
        super().destroy()

    def set_notification_style(self, bg_color: str):
        self.content.configure(height=10, padx=5, pady=10)


class NotificationIncorrectPosture(NotificationBar):

    def __init__(self, parent, interval: float):
        text = self.get_content(interval)
        super().__init__(parent, title="Warning!", message=text)
        self.set_notification_style(bg_color='yellow')
        self.content.config(height=4)

    @staticmethod
    def get_content(interval: float) -> str:
        val_formatted = DataAnalyst.convert_to_specific_format(interval).split(':')
        hours, minutes, seconds, ms = val_formatted[0], val_formatted[1], val_formatted[2], val_formatted[3]
        content = (f"The incorrect posture has been detected for over "
                   f"{hours} hours.\n{minutes} minutes\n{seconds} seconds\n{ms} milliseconds")
        return content


class NotificationSuccessSave(NotificationBar):
    def __init__(self, parent, subject: str, details=None):
        text = f"{subject.title()} has been successfully saved!"
        if details:
            text += "\n" + details
        super().__init__(parent, title="Success!", message=text)
        self.set_notification_style(bg_color='green')


class ErrorNotification(NotificationBar):
    def __init__(self, parent, error_message: str):
        text = error_message
        super().__init__(parent, title="Warning!", message=text)
        self.set_notification_style(bg_color='yellow')
        self.content.config(height=2)

#
# class RandomSideQuestNotification(NotificationBar):
#     """ Show pop up notification to make incorrect posture """
#     title = "Side Quest!"
#     instructions = ("Please move your chin closer to the sensor until bad posture is detected!\n"
#                     "Keep your posture until the time below is over!\n\n"
#                     "Press START once the participant is ready!")
#     rand_range: list[int] = ui_config.Measurements.rand_quest_duration.value  # seconds
#     functions: dict[str, ttk.Button]
#     logger_callback: Union[None, Callable]
#     close_callback: Union[None, Callable]
#     timer: CountDownClock
#     time_interval: int  # seconds to maintain posture
#
#     def __init__(self, parent, logger_callback=None, end_callback=None):
#         super().__init__(parent, self.title, message=self.instructions)
#         self.logger_callback = logger_callback
#         self.close_callback = end_callback
#
#         self.set_notification_style(bg_color='yellow')
#         self.time_interval = random.randint(self.rand_range[0],
#                                             self.rand_range[1])
#         self.timer = CountDownClock(parent=self,
#                                     initial_time=self.time_interval,
#                                     close_callback=self.close,
#                                     start_callback=self.timer_started_callback)
#         self.content.config(height=5)
#
#     def show(self, x: int, y: int, callback: Union[None, Callable],
#              delay=ui_config.Measurements.notification_delay.value):  # self.update_time_interval()
#         # Calculate the screen width and height
#         screen_width = self.winfo_screenwidth()
#         screen_height = self.winfo_screenheight()
#
#         # Ensure the notification is within the screen boundaries
#         x = max(0, min(x, screen_width - self.winfo_width()))
#         y = max(0, min(y, screen_height - self.winfo_height()))
#
#         # Position the notification
#         self.place(x=x, y=y)
#
#     def timer_started_callback(self):
#         if self.logger_callback:
#             self.logger_callback('started')
#
#     def close(self):
#         if self.logger_callback:
#             self.logger_callback("ended")
#         self.close_callback()
#         self.destroy()
#
#     def update_time_interval(self):
#         self.time_interval = random.randint(self.rand_range[0],
#                                             self.rand_range[1])
#         self.timer.time_remaining = self.time_interval
#
#
# class XRangeSelectorFrame(ttk.LabelFrame):
#     title = "X Scale"
#     button_text = "Update"
#     placeholder = str(ui_config.Measurements.graph_x_limit.value)
#     entry: ttk.Entry
#     button: ttk.Button
#     update_graph_callback: Callable
#     pad_x = ui_config.Measurements.widgets_padding.value
#     pad_y = 5
#
#     def __init__(self, parent, row: int, col: int, func: Callable):
#         super().__init__(parent, text=self.title)
#         self.entry = self.add_num_entry_field()
#         self.button = self.add_button()
#         self.grid(row=row, column=col, padx=self.pad_x, pady=self.pad_y)
#         self.update_graph_callback = func
#
#     def add_num_entry_field(self) -> ttk.Entry:
#         field = ttk.Entry(self)
#         # Add placeholder
#         field.insert(0, self.placeholder)
#         field.bind(sequence="<FocusIn>", func=self.remove_placeholder)
#         # Adjust style
#         field.config(width=10)
#         field.pack(side=tk.TOP, padx=5, pady=5)
#         return field
#
#     def get_val(self) -> int:
#         default_value = ""
#         value = self.entry.get()
#         if value == default_value:
#             return ui_config.Measurements.graph_x_limit.value
#         return int(value)
#
#     def remove_placeholder(self, event=None) -> None:
#         if self.entry.get() == self.placeholder:
#             self.entry.delete(0, tk.END)
#
#     def add_button(self) -> ttk.Button:
#         button = ttk.Button(self, text=self.button_text, command=self.update_graph_scale)
#         button.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X, expand=True)
#         return button
#
#     def update_graph_scale(self) -> None:
#         new_range = self.get_val()
#         self.update_graph_callback(new_range)
#

class FeedbackCollector(tk.Toplevel):
    title_text = "Feedback"
    content = "Please indicate if the alarm generated at:\n %local_time!\nX-axis: %position"
    confirmation_content = "Thank you for your response!"
    buttons_num = 0
    logger: Logger
    callback: Callable  # call function upon timer is over
    response_callback: Callable  # call function when any response has been received
    content_field: tk.Text
    timestamp: str
    content_row = 0
    button_row = 1
    buttons_frame: ttk.Frame

    def __init__(self, parent, logger: Logger, closing_callback: Callable, response_callback: Callable):
        super().__init__(parent)
        self.title(self.title_text)
        self.logger = logger
        self.callback = closing_callback
        self.response_callback = response_callback
        self.timestamp = ""
        self.content_field = self.add_content_field()
        self.buttons_frame = self.add_buttons_field()
        self.add_button(text="True", func=self.receive_true)
        self.add_button(text="False", func=self.receive_false)

    def show(self, x: int, y: int, timestamp: str, local_time: str, x_position: int):
        self.timestamp = timestamp
        self.content = self.content.replace('%local_time', local_time)
        self.content = self.content.replace('%position', str(x_position))
        self.update_content(new_text=self.content)
        # Calculate the screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Ensure the notification is within the screen boundaries
        x = max(0, min(x, screen_width - self.winfo_width()))
        y = max(0, min(y, screen_height - self.winfo_height()))

        # Position the notification
        self.geometry(f"+{x}+{y}")
        play_sound_in_thread()

    def add_content_field(self) -> tk.Text:
        text_field = tk.Text(self, height=5, width=45)
        text_field.insert(tk.INSERT, self.content)
        text_field.grid(row=self.content_row, column=0, padx=10, pady=10)
        return text_field

    def add_buttons_field(self) -> ttk.Frame:
        frame = ttk.Frame(self, height=5)
        frame.grid(row=self.content_row + 1, column=0, padx=10, pady=10)
        return frame

    def add_button(self, text: str, func: Callable) -> ttk.Button:
        button = ttk.Button(self.buttons_frame, text=text, command=func)
        button.grid(row=self.button_row, column=self.buttons_num, pady=0, padx=15)
        self.buttons_num += 1
        return button

    def receive_true(self):
        self.response_callback(response=True)
        self.logger.update_user_feedback(1, self.timestamp)
        self.update_content(new_text=self.confirmation_content)
        self.callback()

    def receive_false(self):
        self.response_callback(response=False)
        self.logger.update_user_feedback(0, self.timestamp)
        self.update_content(new_text=self.confirmation_content)
        self.callback()

    def update_content(self, new_text: str):
        self.content_field.delete(1.0, tk.END)
        self.content_field.insert(tk.END, new_text)

class Graph:
    frame: ttk.Frame
    figure: Figure
    ax: Axes
    canvas: FigureCanvasTkAgg
    lines: list
    spans_storage: list[Rectangle]
    span_selector: Union[None, SpanSelector]
    selected_span: tuple
    is_paused: bool
    span_rect: Union[None, Rectangle]
    x_label = "Time"
    y_label = "Distance"
    title = "Sensors Data"
    padx = 10
    pady = 5
    dpi = 100
    graph_size: tuple[int, int] = ui_config.Measurements.graph_size.value
    limit: int = ui_config.Measurements.graph_x_limit.value
    sensor_names: list[str] = ui_config.ElementNames.sensor_names.value
    refresh_rate: int = ui_config.Measurements.graph_refresh_rate.value

    def __init__(self, parent, row: int, col: int,
                 values: dict[str, list[int]],
                 times: list[tuple[str]],
                 paused=False):
        self.values = values
        self.timestamps = times
        self.frame = self.create_frame(parent, row, col)
        self.figure, self.ax, self.canvas, self.lines = self.create_figure()
        self.span_rect = None
        self.selected_span = (0, 0)
        self.spans_storage = list()  # list[span]
        self.is_paused = paused
        if self.is_paused:
            self.span_selector = self.add_values_selector()

    def resume(self):
        self.is_paused = False
        if not self.is_paused:
            self.span_selector = None

    def pause(self):
        self.is_paused = True
        if self.is_paused:
            self.span_selector = self.add_values_selector()

    def add_values_selector(self) -> SpanSelector:
        def on_select_span(vertical_min: float, vertical_max: float):
            self.selected_span = (vertical_min, vertical_max)
            if self.span_rect:
                self.span_rect.remove()
            self.span_rect = self.ax.add_patch(Rectangle((vertical_min, self.ax.get_ylim()[0]),
                                                         vertical_max - vertical_min,
                                                         self.ax.get_ylim()[1] - self.ax.get_ylim()[0],
                                                         color='green', alpha=0.3))
            self.canvas.draw()

        return SpanSelector(self.ax, on_select_span, "horizontal", useblit=True, minspan=0.1)

    def create_frame(self, parent, row: int, col: int) -> ttk.Frame:
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=col, padx=self.padx, pady=self.pady)
        return frame

    def create_figure(self) -> tuple[Figure, Axes, FigureCanvasTkAgg, list]:
        fig = Figure(figsize=self.graph_size, dpi=self.dpi)
        ax = fig.add_subplot(111)
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        ax.set_title(self.title)
        graph_lns = []
        for sensor_name in self.sensor_names:
            x, y = DataAnalyst.get_axes_values(sensor_values=self.values,
                                               sensor_timestamps=self.timestamps,
                                               sensor=sensor_name,
                                               upper_limit=self.limit,
                                               lower_limit=None)
            line, = ax.plot(x, y, label=sensor_name)
            graph_lns.append(line)
        ax.legend()
        canvas = FigureCanvasTkAgg(fig, master=self.frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        result = fig, ax, canvas, graph_lns
        return result

    def get_subplot_title(self) -> Union[None, str]:
        if self.ax:
            title = self.ax.get_title()
            return title
        else:
            return None

    def draw_vert_span(self, x: int, width=1):
        # Add a vertical span to the background
        span: Rectangle = self.ax.axvspan(x - width / 2, x + width / 2, facecolor='red', alpha=1.0, zorder=1)
        self.spans_storage.append(span)

    def draw_graph_arrow(self, x: int, height: int, values: dict[str, list[int]]):
        # Draw the arrow
        y_min = min(min(y) for y in values.values())
        self.ax.annotate('',
                         xy=(x, y_min),
                         xytext=(x, y_min + height),
                         arrowprops=dict(arrowstyle='->',
                                         color='r',
                                         linewidth=2))

    def redraw_vert_spans(self, visible_range: Union[None, int]) -> None:
        if len(self.spans_storage) == 0:
            return None
        if visible_range is not None:
            selected_spans = self.spans_storage[-visible_range:]  # select latest N number
        else:
            selected_spans = self.spans_storage  # select all
        for span in selected_spans:
            self.ax.add_artist(span)
        time.sleep(0.01)
