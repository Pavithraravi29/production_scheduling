import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Assuming these are correctly imported from your app.main3
from app.main1 import fetch_operations, insert_operations, schedule_operations, OperationIn, fetch_component_quantities

st.set_page_config(layout="wide", page_title="Production Schedule Dashboard")

# Custom CSS for improved styling
st.markdown("""
<style>
    .reportview-container .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stat-box {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 20px;
        text-align: center;
    }
    .stat-box h3 {
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Breadcrumbs
# st.markdown("🏠 Home / 🏭 Production / 📅 Schedule")

st.title("Production Schedule Dashboard")

# Fetch and schedule operations
df = fetch_operations()
# component_quantities = {'Component1': 10, 'Component2': 10, 'Component3': 10, "Component 4": 10, "Component 5": 10,"Component 6": 10, "Component 7": 10, "Component 8": 10}
component_quantities = fetch_component_quantities()
schedule_df, overall_end_time, overall_time, daily_production = schedule_operations(df, component_quantities)


# Function to format time
def format_time(minutes):
    delta = timedelta(minutes=minutes)
    days, seconds = delta.days, delta.seconds
    hours, minutes = divmod(seconds, 3600)
    minutes, seconds = divmod(minutes, 60)
    return f"{days}d {hours:02d}h {minutes:02d}m"


# Dashboard layout
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="stat-box">', unsafe_allow_html=True)
    st.subheader("Total Components")
    st.markdown(f"<h2>{len(component_quantities)}</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="stat-box">', unsafe_allow_html=True)
    st.subheader("Total Production Time")
    st.markdown(f"<h2>{format_time(overall_time)}</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="stat-box">', unsafe_allow_html=True)
    st.subheader("Estimated Completion")
    st.markdown(f"<h2>{overall_end_time.strftime('%Y-%m-%d %H:%M')}</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Tabs for detailed views
tab1, tab2, tab3 = st.tabs(["📊 Gantt Chart", "📋 Schedule Details", "🏭 Production "])

with tab1:
    st.header("Production Gantt Chart")

    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        selected_components = st.multiselect("Filter by Component", options=schedule_df['component'].unique(),
                                             default=schedule_df['component'].unique())
    with col2:
        selected_machines = st.multiselect("Filter by Machine", options=schedule_df['machine'].unique(),
                                           default=schedule_df['machine'].unique())

    # Filter the dataframe
    filtered_df = schedule_df[
        schedule_df['component'].isin(selected_components) & schedule_df['machine'].isin(selected_machines)]

    # Create Gantt chart
    fig = px.timeline(filtered_df, x_start="start_time", x_end="end_time", y="machine", color="component",
                      hover_data={"quantity": True, "description": True},
                      labels={"component": "Component", "description": "Operation", "quantity": "Quantity"})
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_layout(height=600, xaxis_title="Time", yaxis_title="Machine", showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Scheduled Operations")
    st.dataframe(schedule_df)

with tab3:
    st.header("Daily Production Overview")

    # Convert daily production to a more suitable format for visualization
    daily_prod_data = []
    for component, production in daily_production.items():
        for date, quantity in production.items():
            daily_prod_data.append({"Date": date.strftime('%Y-%m-%d'), "Component": component, "Quantity": quantity})

    daily_prod_df = pd.DataFrame(daily_prod_data)
    daily_prod_df['Date'] = pd.to_datetime(daily_prod_df['Date'])
    daily_prod_df = daily_prod_df.sort_values('Date')

    # Create a stacked bar chart
    fig = px.bar(daily_prod_df, x='Date', y='Quantity', color='Component', barmode='stack')
    fig.update_layout(
        title="Daily Production by Component",
        xaxis_title="Date",
        yaxis_title="Quantity Produced",
        xaxis=dict(tickformat="%Y-%m-%d")
    )
    st.plotly_chart(fig, use_container_width=True)

    # Show the data in a table format as well
    st.subheader("Daily Production Details")
    daily_prod_df['Date'] = daily_prod_df['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
    st.dataframe(daily_prod_df)


# Sidebar for adding new operations
with st.sidebar:
    st.header("Add New Operation")
    component_options = df['component'].unique().tolist() + ['Other']
    component = st.selectbox("Component", component_options)
    if component == 'Other':
        component = st.text_input("Enter Custom Component")

    description = st.text_input("Description")

    type_options = df['type'].unique().tolist() + ['Other']
    op_type = st.selectbox("Type", type_options)
    if op_type == 'Other':
        op_type = st.text_input("Enter Custom Type")

    machine_options = df['machine'].unique().tolist() + ['Other']
    machine = st.selectbox("Machine", machine_options)
    if machine == 'Other':
        machine = st.text_input("Enter Custom Machine")

    time = st.number_input("Time (minutes)", min_value=0, value=0)
    # quantity = st.text_input("Quantity")

    if st.button("Add Operation"):
        insert_operations([OperationIn(component=component, description=description, type=op_type, machine=machine,
                                       time=time, quantity=quantity)])
        st.success("Operation Added Successfully!")
        st.experimental_rerun()

