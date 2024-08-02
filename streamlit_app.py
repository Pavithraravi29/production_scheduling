import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
from app.main2 import fetch_operations, insert_operations, schedule_operations, OperationIn


st.title("Production Schedule Gantt Chart")

# Fetch operations data from the database
df = fetch_operations()

# Schedule the operations
schedule_df, overall_end_time, overall_time = schedule_operations(df)

# Sidebar for adding operations
st.sidebar.title("Add New Operation")
component_options = df['component'].unique().tolist() + ['Other']
component = st.sidebar.selectbox("Component", component_options)
if component == 'Other':
    custom_component = st.sidebar.text_input("Enter Custom Component")
    if custom_component:
        component = custom_component

description = st.sidebar.text_input("Description")
type_options = df['type'].unique().tolist() + ['Other']
op_type = st.sidebar.selectbox("Type", type_options)
if op_type == 'Other':
    custom_type = st.sidebar.text_input("Enter Custom Type")
    if custom_type:
        # Insert the custom type into the database
        # insert_operations([OperationIn(component='', description='', type=custom_type, machine='', time=0, quantity='')])
        # st.sidebar.success(f"Custom Type '{custom_type}' Added Successfully!")
        op_type = custom_type

machine_options = df['machine'].unique().tolist() + ['Other']
machine = st.sidebar.selectbox("Machine", machine_options)
if machine == 'Other':
    custom_machine = st.sidebar.text_input("Enter Custom Machine")
    if custom_machine:
        machine = custom_machine

time = st.sidebar.number_input("Time (minutes)", min_value=0, value=0)
quantity = st.sidebar.text_input("quantity")  # Add quantity field

if st.sidebar.button("Add Operation"):
    insert_operations([OperationIn(component=component, description=description, type=op_type, machine=machine, time=time, quantity=quantity)])
    st.sidebar.success("Operation Added Successfully!")

    # Update operations and schedule after adding the operation
    df = fetch_operations()
    schedule_df, overall_end_time, overall_time = schedule_operations(df)

# Print the schedule
st.write("Scheduled Operations:")
st.write(schedule_df)


# Function to format overall time and end time
def format_time(minutes):
    delta = timedelta(minutes=minutes)
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days} days, {hours:02}:{minutes:02}:{seconds:02}"


# Print overall time
formatted_time = format_time(overall_time)
st.write(f"Overall Time to Complete All Components: {formatted_time}")
st.write(f"Completion Time: {overall_end_time.strftime('%Y-%m-%d %H:%M:%S')}")

# Gantt chart visualization using Streamlit and Plotly
def plot_gantt_chart(schedule_df, overall_end_time):
    fig = px.timeline(
        schedule_df,
        x_start="start_time",
        x_end="end_time",
        y="machine",
        color="component",
        hover_data={"quantity": True,  "description": True},
        labels={"component": "Component", "description": "Operation", "quantity": "quantity"}
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_layout(xaxis_title="Time", yaxis_title="Machine", showlegend=True)
    return fig

# Render the Gantt chart
st.plotly_chart(plot_gantt_chart(schedule_df, overall_end_time))


# To Run
# streamlit run streamlit_app.py
