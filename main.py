import tkinter as tk
from tkinter import ttk
import sqlite3
import feedparser
from datetime import datetime
from tkinter import messagebox

DB_NAME = "world.db"

# --- Database setup ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            slno INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT,
            state TEXT,
            city TEXT,
            location TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS headlines (
            slno INTEGER PRIMARY KEY AUTOINCREMENT,
            headline TEXT,
            country TEXT,
            city TEXT,
            datetime TEXT
        )
    """)
    conn.commit()
    conn.close()

# --- Add location entry ---
def add_location(country, state, city, location):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO locations (country, state, city, location) VALUES (?, ?, ?, ?)",
                   (country, state, city, location))
    conn.commit()
    conn.close()
    load_locations()

# --- Load locations into table ---
def load_locations(keyword=""):
    for item in loc_tree.get_children():
        loc_tree.delete(item)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if keyword.strip() == "":
        cursor.execute("SELECT * FROM locations")
    else:
        cursor.execute("""
            SELECT * FROM locations
            WHERE country LIKE ? OR state LIKE ? OR city LIKE ? OR location LIKE ?
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        loc_tree.insert("", "end", values=row)

# --- Fetch headlines from Google News ---
def fetch_city_headlines(city, limit=10):
    country = "India"

    feed_url = (
        f"https://news.google.com/rss/search?"
        f"q={city}+{country}"
        f"&hl=en-IN&gl=IN&ceid=IN:en"
    )

    feed = feedparser.parse(feed_url)

    headlines = []
    for entry in feed.entries[:limit]:
        headlines.append(
            (entry.title, country, city,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )

    return headlines
    

def delete_selected_location():
    selected = loc_tree.selection()

    if not selected:
        messagebox.showwarning(
            "Warning",
            "Please select a location row."
        )
        return

    item = loc_tree.item(selected[0])
    slno = item["values"][0]

    if not messagebox.askyesno(
        "Confirm Delete",
        "Are you sure you want to delete the selected location?"
    ):
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM locations WHERE id=?",
        (slno,)
    )

    conn.commit()
    conn.close()

    load_locations()

    messagebox.showinfo(
        "Success",
        "Location deleted successfully."
    )
    
        
def delete_selected_headline():
    selected = head_tree.selection()

    if not selected:
        messagebox.showwarning(
            "Warning",
            "Please select a headline row."
        )
        return

    item = head_tree.item(selected[0])
    slno = item["values"][0]

    if not messagebox.askyesno(
        "Confirm Delete",
        "Are you sure you want to delete the selected headline?"
    ):
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM headlines WHERE slno=?",
        (slno,)
    )

    conn.commit()
    conn.close()

    if search_var.get():
        load_headlines_from_db(search_var.get())

    messagebox.showinfo(
        "Success",
        "Headline deleted successfully."
    )
    
    
# --- Search headlines: fetch + store + display ---
def search_and_store_headlines(city):
    if not city.strip():
        return
    headlines = fetch_city_headlines(city)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for h in headlines:
        cursor.execute("INSERT INTO headlines (headline, country, city, datetime) VALUES (?, ?, ?, ?)", h)
    conn.commit()
    conn.close()
    load_headlines_from_db(city)

# --- Load headlines from DB for a city ---
def load_headlines_from_db(city=""):
    # Clear Treeview
    for item in head_tree.get_children():
        head_tree.delete(item)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if city.strip():
        cursor.execute("""
            SELECT
                MIN(slno),
                headline,
                country,
                city,
                MAX(datetime)
            FROM headlines
            WHERE city=?
            GROUP BY headline
            ORDER BY MAX(datetime) DESC
        """, (city,))
    else:
        cursor.execute("""
            SELECT
                MIN(slno),
                headline,
                country,
                city,
                MAX(datetime)
            FROM headlines
            GROUP BY headline
            ORDER BY MAX(datetime) DESC
        """)

    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        head_tree.insert("", "end", values=row)
        
# --- Search headlines by city + date ---
def search_headlines_by_date(city, date_str):
    for item in head_tree.get_children():
        head_tree.delete(item)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT slno, headline, country, city, datetime FROM headlines WHERE city=? AND datetime LIKE ?",
                   (city, f"{date_str}%"))
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        head_tree.insert("", "end", values=row)


# --- Scrollable Frame Helper ---
class DragScrollableFrame(tk.Frame):
    def __init__(self, parent, height=60, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.canvas = tk.Canvas(
            self,
            bg="#0a0a0a",
            height=height,
            highlightthickness=0
        )

        self.hbar = tk.Scrollbar(
            self,
            orient="horizontal",
            command=self.canvas.xview
        )

        self.canvas.configure(xscrollcommand=self.hbar.set)

        self.scrollable_frame = tk.Frame(
            self.canvas,
            bg="#0a0a0a"
        )

        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )

        self.scrollable_frame.bind(
            "<Configure>",
            self.on_frame_configure
        )

        self.canvas.pack(fill="both", expand=True)
        self.hbar.pack(fill="x")

        # Drag-scroll support
        self.canvas.bind("<ButtonPress-1>", self.start_scroll)
        self.canvas.bind("<B1-Motion>", self.drag_scroll)

        # Mouse wheel horizontal
        self.canvas.bind_all(
            "<Shift-MouseWheel>",
            self.mouse_scroll
        )

    def on_frame_configure(self, event=None):
        self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        )

    def start_scroll(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def drag_scroll(self, event):
        self.canvas.scan_dragto(
            event.x,
            event.y,
            gain=1
        )

    def mouse_scroll(self, event):
        self.canvas.xview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )

# --- Tkinter UI ---
root = tk.Tk()
root.title("World Locations & Headlines")
root.geometry("1200x750")
root.configure(bg="#0a0a0a")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background="#121212", foreground="#00ffff", fieldbackground="#121212", font=("Consolas", 12))
style.configure("Treeview.Heading", background="#00ffff", foreground="#0a0a0a", font=("Consolas", 12, "bold"))

# --- Locations Frame ---
loc_frame = tk.LabelFrame(root, text="Locations Table", bg="#0a0a0a", fg="#00ffff", font=("Consolas", 14, "bold"))
loc_frame.pack(fill="both", expand=True, padx=10, pady=10)

loc_columns = ("SlNo", "Country", "State", "City", "Location")
loc_tree = ttk.Treeview(loc_frame, columns=loc_columns, show="headings", height=8)
for col in loc_columns:
    loc_tree.heading(col, text=col)
    loc_tree.column(col, width=150)
loc_tree.pack(fill="both", expand=True)

# --- Scrollable Entry + Buttons for Locations ---
loc_button_scroll = DragScrollableFrame(
    loc_frame,
    height=70,
    bg="#0a0a0a"
)
loc_button_scroll.pack(
    fill="x",
    padx=5,
    pady=5
)
country_var = tk.StringVar()
state_var = tk.StringVar()
city_var = tk.StringVar()
location_var = tk.StringVar()

tk.Label(loc_button_scroll.scrollable_frame, text="Country:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=country_var, width=15).pack(side="left", padx=5)

tk.Label(loc_button_scroll.scrollable_frame, text="State:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=state_var, width=15).pack(side="left", padx=5)

tk.Label(loc_button_scroll.scrollable_frame, text="City:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=city_var, width=15).pack(side="left", padx=5)

tk.Label(loc_button_scroll.scrollable_frame, text="Location:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=location_var, width=15).pack(side="left", padx=5)

tk.Button(loc_button_scroll.scrollable_frame, text="Add Location",
          command=lambda: add_location(country_var.get(),
                                       state_var.get(),
                                       city_var.get(),
                                       location_var.get())).pack(side="left", padx=10)

# --- Search bar for Locations ---
search_loc_var = tk.StringVar()
tk.Label(loc_button_scroll.scrollable_frame, text="Search Locations:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=search_loc_var, width=30).pack(side="left", padx=5)
tk.Button(loc_button_scroll.scrollable_frame, text="Search", command=lambda: load_locations(search_loc_var.get())).pack(side="left", padx=10)
tk.Button(loc_button_scroll.scrollable_frame, text="Reset", command=lambda: load_locations("")).pack(side="left", padx=10)
tk.Button(
    loc_button_scroll.scrollable_frame,
    text="Delete Selected",
    bg="red",
    fg="white",
    command=delete_selected_location
).pack(side="left", padx=5)

# --- Headlines Frame ---
head_frame = tk.LabelFrame(root, text="City Headlines", bg="#0a0a0a", fg="#00ffff", font=("Consolas", 14, "bold"))
head_frame.pack(fill="both", expand=True, padx=10, pady=10)

head_columns = ("SlNo", "Headlines", "Country", "City", "DateTime")
head_tree = ttk.Treeview(head_frame, columns=head_columns, show="headings", height=8)
for col in head_columns:
    head_tree.heading(col, text=col)
    head_tree.column(col, width=220)
head_tree.pack(fill="both", expand=True)

# --- Scrollable Search + Buttons for Headlines ---
head_button_scroll = DragScrollableFrame(
    head_frame,
    height=70,
    bg="#0a0a0a"
)

head_button_scroll.pack(
    fill="x",
    padx=5,
    pady=5
)
search_var = tk.StringVar()
date_var = tk.StringVar()

tk.Label(head_button_scroll.scrollable_frame, text="Enter City:", fg="#00ffff", bg="#0a0a0a",
         font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(head_button_scroll.scrollable_frame, textvariable=search_var, width=20).pack(side="left", padx=5)

tk.Label(head_button_scroll.scrollable_frame, text="Enter Date (YYYY-MM-DD):", fg="#00ffff", bg="#0a0a0a",
         font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(head_button_scroll.scrollable_frame, textvariable=date_var, width=15).pack(side="left", padx=5)

tk.Button(head_button_scroll.scrollable_frame, text="Search & Store Headlines",
          command=lambda: search_and_store_headlines(search_var.get())).pack(side="left", padx=10)

tk.Button(head_button_scroll.scrollable_frame, text="Search by Date",
          command=lambda: search_headlines_by_date(search_var.get(), date_var.get())).pack(side="left", padx=10)

tk.Button(head_button_scroll.scrollable_frame, text="Load Stored Headlines",
          command=lambda: load_headlines_from_db(search_var.get())).pack(side="left", padx=10)
          
tk.Button(
    head_button_scroll.scrollable_frame,
    text="Delete Selected",
    bg="red",
    fg="white",
    command=delete_selected_headline
).pack(side="left", padx=5)

# --- Initialize ---
init_db()
load_locations()

root.mainloop()


# --- Tkinter UI ---
root = tk.Tk()
root.title("World Locations & Headlines")
root.geometry("1200x750")
root.configure(bg="#0a0a0a")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background="#121212", foreground="#00ffff", fieldbackground="#121212", font=("Consolas", 12))
style.configure("Treeview.Heading", background="#00ffff", foreground="#0a0a0a", font=("Consolas", 12, "bold"))

# --- Locations Frame ---
loc_frame = tk.LabelFrame(root, text="Locations Table", bg="#0a0a0a", fg="#00ffff", font=("Consolas", 14, "bold"))
loc_frame.pack(fill="both", expand=True, padx=10, pady=10)

loc_columns = ("SlNo", "Country", "State", "City", "Location")
loc_tree = ttk.Treeview(loc_frame, columns=loc_columns, show="headings", height=8)
for col in loc_columns:
    loc_tree.heading(col, text=col)
    loc_tree.column(col, width=150)
loc_tree.pack(fill="both", expand=True)

# --- Scrollable Entry + Buttons for Locations ---
loc_frame = tk.LabelFrame(root, text="Locations")
loc_frame.pack(fill="both", expand=True, padx=10, pady=10)

loc_tree.pack(fill="both", expand=True)

loc_button_scroll = DragScrollableFrame(loc_frame, height=70)
loc_button_scroll.pack(fill="x", pady=5)

country_var = tk.StringVar()
state_var = tk.StringVar()
city_var = tk.StringVar()
location_var = tk.StringVar()

tk.Label(loc_button_scroll.scrollable_frame, text="Country:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=country_var, width=15).pack(side="left", padx=5)

tk.Label(loc_button_scroll.scrollable_frame, text="State:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=state_var, width=15).pack(side="left", padx=5)

tk.Label(loc_button_scroll.scrollable_frame, text="City:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=city_var, width=15).pack(side="left", padx=5)

tk.Label(loc_button_scroll.scrollable_frame, text="Location:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=location_var, width=15).pack(side="left", padx=5)

tk.Button(loc_button_scroll.scrollable_frame, text="Add Location",
          command=lambda: add_location(country_var.get(),
                                       state_var.get(),
                                       city_var.get(),
                                       location_var.get())).pack(side="left", padx=10)

# --- Search bar for Locations ---
search_loc_var = tk.StringVar()
tk.Label(loc_button_scroll.scrollable_frame, text="Search Locations:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=search_loc_var, width=30).pack(side="left", padx=5)
tk.Button(loc_button_scroll.scrollable_frame, text="Search", command=lambda: load_locations(search_loc_var.get())).pack(side="left", padx=10)
tk.Button(loc_button_scroll.scrollable_frame, text="Reset", command=lambda: load_locations("")).pack(side="left", padx=10)

# --- Headlines Frame ---
head_frame = tk.LabelFrame(root, text="City Headlines", bg="#0a0a0a", fg="#00ffff", font=("Consolas", 14, "bold"))
head_frame.pack(fill="both", expand=True, padx=10, pady=10)

head_columns = ("SlNo", "Headlines", "Country", "City", "DateTime")
head_tree = ttk.Treeview(head_frame, columns=head_columns, show="headings", height=8)
for col in head_columns:
    head_tree.heading(col, text=col)
    head_tree.column(col, width=220)
head_tree.pack(fill="both", expand=True)

# --- Scrollable Search + Buttons for Headlines ---
head_button_scroll = DragScrollableFrame(head_frame, orient="horizontal", height=60)
head_button_scroll.pack(fill="x", pady=5)
make_draggable(head_button_scroll)

search_var = tk.StringVar()
date_var = tk.StringVar()

tk.Label(head_button_scroll.scrollable_frame, text="Enter City:", fg="#00ffff", bg="#0a0a0a",
         font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(head_button_scroll.scrollable_frame, textvariable=search_var, width=20).pack(side="left", padx=5)

tk.Label(head_button_scroll.scrollable_frame, text="Enter Date (YYYY-MM-DD):", fg="#00ffff", bg="#0a0a0a",
         font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(head_button_scroll.scrollable_frame, textvariable=date_var, width=15).pack(side="left", padx=5)

tk.Button(head_button_scroll.scrollable_frame, text="Search & Store Headlines",
          command=lambda: search_and_store_headlines(search_var.get())).pack(side="left", padx=10)

tk.Button(head_button_scroll.scrollable_frame, text="Search by Date",
          command=lambda: search_headlines_by_date(search_var.get(), date_var.get())).pack(side="left", padx=10)

tk.Button(head_button_scroll.scrollable_frame, text="Load Stored Headlines",
          command=lambda: load_headlines_from_db(search_var.get())).pack(side="left", padx=10)

# --- Initialize ---
init_db()
load_locations()

root.mainloop()


# --- Tkinter UI ---
root = tk.Tk()
root.title("World Locations & Headlines")
root.geometry("1200x750")
root.configure(bg="#0a0a0a")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background="#121212", foreground="#00ffff", fieldbackground="#121212", font=("Consolas", 12))
style.configure("Treeview.Heading", background="#00ffff", foreground="#0a0a0a", font=("Consolas", 12, "bold"))

# --- Locations Frame ---
loc_frame = tk.LabelFrame(root, text="Locations Table", bg="#0a0a0a", fg="#00ffff", font=("Consolas", 14, "bold"))
loc_frame.pack(fill="both", expand=True, padx=10, pady=10)

loc_columns = ("SlNo", "Country", "State", "City", "Location")
loc_tree = ttk.Treeview(loc_frame, columns=loc_columns, show="headings", height=8)
for col in loc_columns:
    loc_tree.heading(col, text=col)
    loc_tree.column(col, width=150)
loc_tree.pack(fill="both", expand=True)

# --- Scrollable Entry + Buttons for Locations ---
loc_button_scroll = ScrollableFrame(loc_frame, orient="horizontal", height=60)
loc_button_scroll.pack(fill="x", pady=5)
make_draggable(loc_button_scroll)

country_var = tk.StringVar()
state_var = tk.StringVar()
city_var = tk.StringVar()
location_var = tk.StringVar()

tk.Label(loc_button_scroll.scrollable_frame, text="Country:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=country_var, width=15).pack(side="left", padx=5)

tk.Label(loc_button_scroll.scrollable_frame, text="State:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=state_var, width=15).pack(side="left", padx=5)

tk.Label(loc_button_scroll.scrollable_frame, text="City:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=city_var, width=15).pack(side="left", padx=5)

tk.Label(loc_button_scroll.scrollable_frame, text="Location:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=location_var, width=15).pack(side="left", padx=5)

tk.Button(loc_button_scroll.scrollable_frame, text="Add Location",
          command=lambda: add_location(country_var.get(),
                                       state_var.get(),
                                       city_var.get(),
                                       location_var.get())).pack(side="left", padx=10)

# --- Search bar for Locations ---
search_loc_var = tk.StringVar()
tk.Label(loc_button_scroll.scrollable_frame, text="Search Locations:", fg="#00ffff", bg="#0a0a0a", font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(loc_button_scroll.scrollable_frame, textvariable=search_loc_var, width=30).pack(side="left", padx=5)
tk.Button(loc_button_scroll.scrollable_frame, text="Search", command=lambda: load_locations(search_loc_var.get())).pack(side="left", padx=10)
tk.Button(loc_button_scroll.scrollable_frame, text="Reset", command=lambda: load_locations("")).pack(side="left", padx=10)

# --- Headlines Frame ---
head_frame = tk.LabelFrame(root, text="City Headlines", bg="#0a0a0a", fg="#00ffff", font=("Consolas", 14, "bold"))
head_frame.pack(fill="both", expand=True, padx=10, pady=10)

head_columns = ("SlNo", "Headlines", "Country", "City", "DateTime")
head_tree = ttk.Treeview(head_frame, columns=head_columns, show="headings", height=8)
for col in head_columns:
    head_tree.heading(col, text=col)
    head_tree.column(col, width=220)
head_tree.pack(fill="both", expand=True)

# --- Scrollable Search + Buttons for Headlines ---
head_button_scroll = ScrollableFrame(head_frame, orient="horizontal", height=60)
head_button_scroll.pack(fill="x", pady=5)
make_draggable(head_button_scroll)

search_var = tk.StringVar()
date_var = tk.StringVar()

tk.Label(head_button_scroll.scrollable_frame, text="Enter City:", fg="#00ffff", bg="#0a0a0a",
         font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(head_button_scroll.scrollable_frame, textvariable=search_var, width=20).pack(side="left", padx=5)

tk.Label(head_button_scroll.scrollable_frame, text="Enter Date (YYYY-MM-DD):", fg="#00ffff", bg="#0a0a0a",
         font=("Consolas", 12, "bold")).pack(side="left", padx=5)
tk.Entry(head_button_scroll.scrollable_frame, textvariable=date_var, width=15).pack(side="left", padx=5)

tk.Button(head_button_scroll.scrollable_frame, text="Search & Store Headlines",
          command=lambda: search_and_store_headlines(search_var.get())).pack(side="left", padx=10)

tk.Button(head_button_scroll.scrollable_frame, text="Search by Date",
          command=lambda: search_headlines_by_date(search_var.get(), date_var.get())).pack(side="left", padx=10)

tk.Button(
    head_button_scroll.scrollable_frame,
    text="All Headlines",
    command=load_headlines_from_db
).pack(side="left", padx=10)


# --- Initialize ---
init_db()
load_locations()

root.mainloop()

