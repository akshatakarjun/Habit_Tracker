#import all the libs & packages reqd
import streamlit as st
import pandas as pd
import os
from datetime import date


#Initiating the path to the data file to write 
DATA_FILE = "Personal_Habit_Tracker.csv"

#predefined metrics used as examples in the csv file
METRICS = [
    "Up before 7 AM?", "3L_Water?", "Job_Apps?", "2_Healthy_Meals?", 
    "Journal?", "Mindfulness?", "Side_Hustle?", "Veggie_Fruits?", 
    "Protein _Lentils_Pulses?", "Courses_Certs?","Self_Love?"
]

#Alternative when data file does not exist
if not os.path.exists(DATA_FILE) or (os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) == 0):
    df = pd.DataFrame(columns=["Date"] + METRICS)
    df.to_csv(DATA_FILE, index=False)

#creating page congifuration for dashboard and viewing
st.set_page_config(page_title="Habit Tracker Dashboard", layout="wide")
st.title("📊 Personal Habit Tracker & Analytics")

#frontend for user inputs 
st.subheader("📝 Log Daily Habits")

selected_date = st.date_input("Select Date:", date.today())
date_str = str(selected_date)

user_inputs = {"Date": date_str}
input_cols = st.columns(2)

for i, metric in enumerate(METRICS):
    with input_cols[i % 2]:
        #options to answer the metrics
        response = st.selectbox(f"{metric}", ["Yes", "No"], index=1, key=f"input_{metric}")
        #convert Yes/No to 1/0 for Excel/Graph calculations plotting
        user_inputs[metric] = 1 if response == "Yes" else 0

#save and reload data button
if st.button("Save & Update Dashboard", type="primary"):
    try:
        current_df = pd.read_csv(DATA_FILE)
    except pd.errors.EmptyDataError:
        current_df = pd.DataFrame(columns=["Date"] + METRICS)
    #prevent duplicating the date input
    current_df = current_df[current_df["Date"] != date_str]
    
    #add the recent input
    new_row = pd.DataFrame([user_inputs])
    updated_df = pd.concat([current_df, new_row], ignore_index=True)
    
    #sort the date in ascending order
    updated_df['Date'] = pd.to_datetime(updated_df['Date'])
    updated_df = updated_df.sort_values("Date")
    
    #load the updated/written inputs from the frontend to the excel file
    updated_df.to_csv(DATA_FILE, index=False)
    st.success(f"Data saved successfully for {selected_date}!")
    st.rerun()  #forces Streamlit to instantly redraw the updated charts below

st.divider()


#FRONTEND ANALYTICS & DASHBOARD KPIs

st.subheader("📈 Real-Time KPIs & Progress Chart")

#load recently updated data
display_df = pd.read_csv(DATA_FILE)

if not display_df.empty and len(display_df) > 0:
    #prepare date columns for indexing
    display_df["Date"] = pd.to_datetime(display_df["Date"])
    display_df = display_df.sort_values("Date")
    
    #KPI Segment Calculations (Last 7 tracked days)
    recent_entries = display_df.tail(7)
    days_tracked = len(recent_entries)
    
    #category1 Productivity Score
    prod_habits = ["Job_Apps?", "Side_Hustle?", "Up before 7 AM?"]
    prod_pct = int(recent_entries[prod_habits].sum().sum() / (days_tracked * len(prod_habits)) * 100)
    
    #category2 Health & Nutrition Score
    health_habits = ["3L_Water?", "2_Healthy_Meals?", "Veggie_Fruits?", "Protein _Lentils_Pulses?"]
    health_pct = int(recent_entries[health_habits].sum().sum() / (days_tracked * len(health_habits)) * 100)
    
    #category3 Wellness Score
    well_habits = ["Journal?", "Mindfulness?", "Self_Love?"]
    well_pct = int(recent_entries[well_habits].sum().sum() / (days_tracked * len(well_habits)) * 100)

    #Render KPI Dashboard Blocks
    st.markdown("##### 🗓️ 7-Day Rolling Success Metrics")
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    
    with kpi_col1:
        st.metric(label="💼 Productivity Alignment", value=f"{prod_pct}%")
    with kpi_col2:
        st.metric(label="🥗 Nutritional Consistency", value=f"{health_pct}%")
    with kpi_col3:
        st.metric(label="🧠 Mindfulness & Care", value=f"{well_pct}%")
        
    st.write("") #Padding space

    # --- Render Interactive Line Graph ---
    display_df.set_index("Date", inplace=True)
    
    #interactive multiselect allows user to toggle lines on/off dynamically
    view_selections = st.multiselect(
        "Choose which habits to trace on the line chart:", 
        METRICS, 
        default=METRICS[:3]
    )
    
    if view_selections:
        #Renders interactive chart timeline natively
        st.line_chart(display_df[view_selections])
    else:
        st.warning("Please select at least one habit metric from the list above to render the timeline.")
else:
    st.info("No habit records discovered yet. Fill out the questions above and submit your first entry!")

