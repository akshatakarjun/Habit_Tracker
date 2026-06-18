#import all the libs & packages reqd
import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import date

#Initiating the paths to files
DATA_FILE = "Personal_Habit_Tracker.csv"
CONFIG_FILE = "Tracked_Habits_Config.txt"

# ----------------------------------------------------
# DYNAMIC METRICS CONFIGURATION ENGINE (READ/WRITE)
# ----------------------------------------------------
# 1. READ: Load existing custom items, or fall back to standard defaults if empty
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config_lines = [line.strip() for line in f.readlines() if line.strip()]
else:
    # Default configuration layout if the app runs for the very first time
    config_lines = [
        "Productivity: Up before 7 AM?",
        "Health: 3L_Water?",
        "Productivity: Job_Apps?",
        "Health: 2_Healthy_Meals?",
        "Wellness: Journal?",
        "Wellness: Mindfulness?",
        "Productivity: Side_Hustle?",
        "Health: Veggie_Fruits?",
        "Health: Protein _Lentils_Pulses?",
        "Productivity: Courses_Certs?",
        "Wellness: Self_Love?"
    ]

# 2. WRITE: Display instructions and text area configuration box inside Sidebar
st.sidebar.subheader("⚙️ Custom Habit Configuration")
st.sidebar.info("Modify your tracklist here. Write each category as CategoryName: exactly one habit per line.")

user_defined_text = st.sidebar.text_area(
    label="Edit Categories & Questions:",
    value="\n".join(config_lines),
    height=320,
    help="Example structure: CategoryName: Your Habit"
)

# Parse raw multiline string back into individual line strings
current_config_lines = [line.strip() for line in user_defined_text.split("\n") if line.strip()]

# Save user adjustments instantly to the text configuration file
if current_config_lines != config_lines and len(current_config_lines) > 0:
    with open(CONFIG_FILE, "w") as f:
        for line in current_config_lines:
            f.write(f"{line}\n")
    config_lines = current_config_lines
    st.rerun()

# 3. PARSER: Separate category names from habit names via the colon syntax
METRICS = []
CATEGORY_MAP = {} # Maps Category Names -> List of relative habits

for line in config_lines:
    line_clean = line.strip()
    if not line_clean:
        continue # Skip empty rows completely
    if ":" in line_clean:
        parts = line_clean.split(":", 1)
        cat_name = parts[0].strip()   # Text BEFORE the colon (Category)
        habit_name = parts[1].strip()  # Text AFTER the colon (Habit Name)
    else:
        cat_name = "General"
        habit_name = line_clean
        
    if habit_name and habit_name != "":
        METRICS.append(habit_name)
        if cat_name not in CATEGORY_MAP:
            CATEGORY_MAP[cat_name] = []
        if habit_name not in CATEGORY_MAP[cat_name]:
            CATEGORY_MAP[cat_name].append(habit_name)


# --- Safety check for structural spreadsheet allocation ---
if not os.path.exists(DATA_FILE) or (os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) == 0):
    df = pd.DataFrame(columns=["Date"] + METRICS)
    df.to_csv(DATA_FILE, index=False)

# Load existing database memory 
try:
    current_df = pd.read_csv(DATA_FILE)
except pd.errors.EmptyDataError:
    current_df = pd.DataFrame(columns=["Date"] + METRICS)
current_df["Date"] = current_df["Date"].astype(str)


# ----------------------------------------------------
# CONTROLLER: FRONTEND USER INPUTS
# ----------------------------------------------------
# creating page configuration for dashboard and viewing
st.set_page_config(page_title="Habit Tracker Dashboard", layout="wide")
st.title("📊 Personal Habit Tracker & Analytics")

st.subheader("📝 Log Daily Habits")

# Updated format sets visual screen layout to DD/MM/YYYY, preserving standard backend string data
selected_date = st.date_input("Select Date:", date.today(), format="DD/MM/YYYY")
date_str = str(selected_date)

# Check if data already exists for this SPECIFIC date
date_row = current_df[current_df["Date"] == date_str]
has_existing_data = not date_row.empty

user_inputs = {"Date": date_str}
input_cols = st.columns(2)
options_list = ["Yes", "No", "Clear"]

for i, metric in enumerate(METRICS):
    with input_cols[i % 2]:
        # Determine the dynamic default layout index based on historical entries for THIS date
        default_index = 1  # Standard fallback is "No"
        if has_existing_data and metric in date_row.columns:
            past_val = date_row.iloc[0][metric] if len(date_row) > 0 else None
            if pd.isna(past_val) or past_val == "":
                default_index = 2  # Clear
            elif past_val == 1 or past_val == 1.0:
                default_index = 0  # Yes
            else:
                default_index = 1  # No
            
        # Display BOTH the category and metric together in the dropdown label dynamically
        metric_category = "General"
        for cat_name, habit_list in CATEGORY_MAP.items():
            if metric in habit_list:
                metric_category = cat_name
                break
                
        response = st.selectbox(
            f"[{metric_category}] {metric}", 
            options_list, 
            index=default_index, 
            key=f"input_{metric}_{date_str}" 
        )
        
        if response == "Yes":
            user_inputs[metric] = 1
        elif response == "No":
            user_inputs[metric] = 0
        else:
            user_inputs[metric] = None 


# Define reuseable save function pipeline
def save_data_to_csv(dataframe, date_string, input_data):
    # Ensure current DataFrame columns adapt dynamically if headers changed or columns were added
    for m in METRICS:
        if m not in dataframe.columns:
            dataframe[m] = None # Append empty column safely
            
    cleaned_df = dataframe[dataframe["Date"] != date_string]
    new_row = pd.DataFrame([input_data])
    updated_df = pd.concat([cleaned_df, new_row], ignore_index=True)
    
    updated_df['Date'] = pd.to_datetime(updated_df['Date'])
    updated_df = updated_df.sort_values("Date")
    updated_df['Date'] = updated_df['Date'].dt.date.astype(str)
    
    # Force alignment of columns to current metrics schema to avoid trailing pollution
    cols_to_save = ["Date"] + [m for m in METRICS if m in updated_df.columns]
    updated_df[cols_to_save].to_csv(DATA_FILE, index=False)
    st.success(f"Data saved successfully for {date_string}!")
    st.rerun()

# Confirmation workflow routing buttons with safety prompts
if has_existing_data:
    if st.button("Save & Update Dashboard", type="secondary"):
        st.session_state.show_confirmation = True

    if st.session_state.get("show_confirmation", False):
        st.warning(f"⚠️ You already have data saved for **{selected_date}**. Saving will permanently overwrite your previous answers in Excel. Do you want to proceed?")
        conf_col1, conf_col2, _ = st.columns(3)
        with conf_col1:
            if st.button("Yes, Overwrite", type="primary"):
                st.session_state.show_confirmation = False
                save_data_to_csv(current_df, date_str, user_inputs)
        with conf_col2:
            if st.button("Cancel"):
                st.session_state.show_confirmation = False
                st.info("Overwrite cancelled. Data unchanged.")
                st.rerun()
else:
    if st.button("Save & Update Dashboard", type="primary"):
        save_data_to_csv(current_df, date_str, user_inputs)

st.divider()


# ----------------------------------------------------
# CONTROLLER: FRONTEND ANALYTICS & DYNAMIC DASHBOARD KPIs
# ----------------------------------------------------
st.subheader("📈 Real-Time KPIs & Progress Chart")

try:
    display_df = pd.read_csv(DATA_FILE)
except pd.errors.EmptyDataError:
    display_df = pd.DataFrame(columns=["Date"] + METRICS)

if not display_df.empty and len(display_df) > 0:
    display_df["Date"] = pd.to_datetime(display_df["Date"])
    display_df = display_df.sort_values("Date")
    
    recent_entries = display_df.tail(7)
    
    st.markdown("##### 🗓️ 7-Day Rolling Success Metrics")
    
    # Restrict grid footprint to maximum 4 dashboard blocks side-by-side
    num_categories = min(max(len(CATEGORY_MAP), 1), 4)
    kpi_columns = st.columns(num_categories)
    
    for idx, (category, relative_habits) in enumerate(list(CATEGORY_MAP.items())[:4]):
        # Match configured options against existing dataset tracking column headers
        valid_habits = [h for h in relative_habits if h in recent_entries.columns]
        
        if valid_habits:
            cat_mean = recent_entries[valid_habits].mean().mean()
            cat_pct = int(cat_mean * 100) if not pd.isna(cat_mean) else 0
        else:
            cat_pct = 0
            
        with kpi_columns[idx % num_categories]:
            st.metric(label=f"🎯 {category} Score", value=f"{cat_pct}%")
        
    st.write("") # Padding space

    # Interactive multiselect traces
    view_selections = st.multiselect("Choose which habits to trace on the line chart:", METRICS, default=METRICS[:3] if len(METRICS) >=3 else METRICS)
    
    if view_selections:
        valid_selections = [v for v in view_selections if v in display_df.columns]
        
        if valid_selections:
            # Reshape layout architecture from wide rows to long key-value pairings for Altair scroll engine
            chart_data = display_df.melt(id_vars=["Date"], value_vars=valid_selections, var_name="Habit", value_name="Status")
            
            scrollable_chart = (
                alt.Chart(chart_data)
                .mark_line(point=True, interpolate='monotone')
                .encode(
                    x=alt.X("Date:T", title="Timeline (Click and drag chart sideways to scroll continuously)"),
                    y=alt.Y("Status:Q", title="Completed (1=Yes, 0=No)", scale=alt.Scale(domain=[-0.1, 1.1])),
                    color="Habit:N",
                    tooltip=["Date:T", "Habit:N", "Status:Q"]
                )
                .properties(width="container", height=400)
                .interactive(bind_y=False) # Free scroll bar horizontal operations
            )
            st.altair_chart(scrollable_chart, use_container_width=True)
        else:
            st.warning("Selected habits do not match columns inside the current CSV data file.")
    else:
            st.warning("Please select at least one habit metric from the list above to render the timeline.")
else:
    st.info("No habit records discovered yet. Fill out the questions above and submit your first entry!")