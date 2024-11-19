# import streamlit as st
# import pandas as pd
# import plotly.express as px
# from datetime import datetime, timedelta
# from app.algorithms.scheduling import schedule_operations
# from app.crud.component_quantities import fetch_component_quantities, insert_component_quantities
# from app.crud.leadtime import fetch_lead_times, insert_lead_times
# from app.crud.operations import fetch_operations, insert_operations
# from app.database.models import db
# from app.schemas.operations import OperationIn
# from app.schemas.component_quantities import ComponentQuantityIn
# from app.schemas.leadtime import LeadTimeIn
#
# # Initialize session state
# if 'page' not in st.session_state:
#     st.session_state.page = "Production Schedule"
# if 'show_success' not in st.session_state:
#     st.session_state.show_success = False
#
#
# def configure_database():
#     if not db.provider:
#         db.bind(provider='postgres', user='postgres', password='password', host='172.18.101.47', database='schedulingalgo')
#         db.generate_mapping(create_tables=True)
#
#
# configure_database()
#
# # Set up Streamlit page configuration
# st.set_page_config(layout="wide", page_title="Smart Production scheduling")
#
# # Custom CSS for improved styling
# st.markdown("""
# <style>
#     .reportview-container .main .block-container {
#         max-width: 1200px;
#         padding-top: 2rem;
#         padding-bottom: 2rem;
#     }
#     .stat-box {
#         background-color: #f0f2f6;
#         border-radius: 5px;
#         padding: 20px;
#         text-align: center;
#         box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
#         transition: all 0.3s ease;
#     }
#     .stat-box:hover {
#         transform: translateY(-5px);
#         box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
#     }
#     .stat-box h3 {
#         margin-bottom: 10px;
#         color: #2c3e50;
#     }
#     .success-message {
#         padding: 10px;
#         border-radius: 5px;
#         background-color: #d4edda;
#         border: 1px solid #c3e6cb;
#         color: #155724;
#         margin-bottom: 10px;
#     }
# </style>
# """, unsafe_allow_html=True)
#
#
# # Function to format time
# def format_time(minutes):
#     delta = timedelta(minutes=minutes)
#     days, seconds = delta.days, delta.seconds
#     hours, minutes = divmod(seconds, 3600)
#     minutes, seconds = divmod(minutes, 60)
#     return f"{days}d {hours:02d}h {minutes:02d}m"
#
#
# # Sidebar for navigation
# st.sidebar.title("Production Scheduling")
# page = st.sidebar.radio("Navigate", ["Production Schedule", "Component & Lead Time"])
#
# # Update session state
# st.session_state.page = page
#
# if st.session_state.page == "Production Schedule":
#     st.title("SCHEDULING DASHBOARD")
#
#     # Fetch and schedule operations
#     df = fetch_operations()
#     component_quantities = fetch_component_quantities()
#     lead_times = fetch_lead_times()
#     schedule_df, overall_end_time, overall_time, daily_production, component_status = schedule_operations(df,
#                                                                                                           component_quantities,
#                                                                                                           lead_times)
#
#     # Dashboard layout
#     col1, col2, col3 = st.columns(3)
#
#     with col1:
#         st.markdown('<div class="stat-box">', unsafe_allow_html=True)
#         st.subheader("Total Components")
#         st.markdown(f"<h2>{len(component_quantities)}</h2>", unsafe_allow_html=True)
#         st.markdown('</div>', unsafe_allow_html=True)
#
#     with col2:
#         st.markdown('<div class="stat-box">', unsafe_allow_html=True)
#         st.subheader("Total Production Time")
#         st.markdown(f"<h2>{format_time(overall_time)}</h2>", unsafe_allow_html=True)
#         st.markdown('</div>', unsafe_allow_html=True)
#
#     with col3:
#         st.markdown('<div class="stat-box">', unsafe_allow_html=True)
#         st.subheader("Estimated Completion")
#         st.markdown(f"<h2>{overall_end_time.strftime('%Y-%m-%d %H:%M')}</h2>", unsafe_allow_html=True)
#         st.markdown('</div>', unsafe_allow_html=True)
#
#     # Tabs for detailed views
#     tab1, tab2, tab3 = st.tabs(["📊 Production Timeline", "📋 Scheduling Details", "🏭 Daily Analytics"])
#
#     with tab1:
#         st.header("Production Timeline Visualizer")
#
#         # Filter controls
#         col1, col2 = st.columns(2)
#         with col1:
#             selected_components = st.multiselect("Component Filter", options=schedule_df['component'].unique(),
#                                                  default=schedule_df['component'].unique())
#         with col2:
#             selected_machines = st.multiselect("Machine Filter", options=schedule_df['machine'].unique(),
#                                                default=schedule_df['machine'].unique())
#
#         # Filter the dataframe
#         filtered_df = schedule_df[
#             schedule_df['component'].isin(selected_components) & schedule_df['machine'].isin(selected_machines)]
#
#         # Create Gantt chart
#         fig = px.timeline(filtered_df, x_start="start_time", x_end="end_time", y="machine", color="component",
#                           hover_data={"quantity": True, "description": True},
#                           labels={"component": "Component", "description": "Operation", "quantity": "Quantity"})
#         fig.update_yaxes(categoryorder="total ascending")
#         fig.update_layout(height=600, xaxis_title="Timeline", yaxis_title="Machine", showlegend=True)
#         st.plotly_chart(fig, use_container_width=True)
#
#     with tab2:
#         st.header("Scheduling details")
#         st.dataframe(schedule_df)
#
#     with tab3:
#         st.header("Daily production Analytics")
#
#         # Convert daily production to a more suitable format for visualization
#         daily_prod_data = []
#         for component, production in daily_production.items():
#             for date, quantity in production.items():
#                 daily_prod_data.append(
#                     {"Date": date.strftime('%Y-%m-%d'), "Component": component, "Quantity": quantity})
#
#         daily_prod_df = pd.DataFrame(daily_prod_data)
#         daily_prod_df['Date'] = pd.to_datetime(daily_prod_df['Date'])
#         daily_prod_df = daily_prod_df.sort_values('Date')
#
#         # Create a stacked bar chart
#         fig = px.bar(daily_prod_df, x='Date', y='Quantity', color='Component', barmode='stack')
#         fig.update_layout(
#             title="Daily Component Production Breakdown",
#             xaxis_title="Date",
#             yaxis_title="Units Produced",
#             xaxis=dict(tickformat="%Y-%m-%d")
#         )
#         st.plotly_chart(fig, use_container_width=True)
#
#         # Show the data in a table format as well
#         st.subheader("Detailed Daily Production Log")
#         daily_prod_df['Date'] = daily_prod_df['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
#         st.dataframe(daily_prod_df)
#
#     # Sidebar for adding new operations
#     with st.sidebar:
#         st.header("Operation Architect")
#         component_options = df['component'].unique().tolist() + ['Other']
#         component = st.selectbox("Select Component", component_options)
#         if component == 'Other':
#             component = st.text_input("Specify New Component")
#
#         description = st.text_input("Operation Description")
#
#         type_options = df['type'].unique().tolist() + ['Other']
#         op_type = st.selectbox("Operation Type", type_options)
#         if op_type == 'Other':
#             op_type = st.text_input("Specify New Type")
#
#         machine_options = df['machine'].unique().tolist() + ['Other']
#         machine = st.selectbox("Assign Machine", machine_options)
#         if machine == 'Other':
#             machine = st.text_input("Specify New Machine")
#
#         time = st.number_input("Duration (minutes)", min_value=0, value=0)
#
#         if st.button("Create Operation"):
#             operation_in = OperationIn(
#                 component=component,
#                 description=description,
#                 type=op_type,
#                 machine=machine,
#                 time=time
#             )
#
#             insert_operations([operation_in])
#             st.session_state.show_success = True
#             st.rerun()
#
#     # Show success message if applicable
#     if st.session_state.show_success:
#         st.sidebar.markdown('<div class="success-message">Operation Added Successfully!</div>', unsafe_allow_html=True)
#         st.session_state.show_success = False
#
# elif st.session_state.page == "Component & Lead Time":
#     st.title("Component & Lead Time Manager")
#
#     tab1, tab2 = st.tabs(["📝 Add/Update", "👁️ Current Inventory"])
#
#     with tab1:
#         st.header("Component and Lead Time Editor")
#
#         col1, col2 = st.columns(2)
#
#         with col1:
#             st.subheader("Quantity Adjuster")
#             component = st.text_input("Component Identifier")
#             quantity = st.number_input("Stock Quantity", min_value=0, value=0)
#
#             if st.button("Update Inventory"):
#                 component_quantity = ComponentQuantityIn(component=component, quantity=quantity)
#                 insert_component_quantities([component_quantity])
#                 st.success(f"Inventory updated for {component}")
#
#         with col2:
#             st.subheader("Lead Time Configurator")
#             lead_time_component = st.text_input("Component for Lead Time")
#             due_date = st.date_input("Target Date")
#             due_time = st.time_input("Target Time")
#
#             if st.button("Set Lead Time"):
#                 due_datetime = datetime.combine(due_date, due_time)
#                 lead_time = LeadTimeIn(component=lead_time_component, due_date=due_datetime)
#                 insert_lead_times([lead_time])
#                 st.success(f"Lead time configured for {lead_time_component}")
#
#     with tab2:
#         st.header("Inventory & Lead Time Overview")
#
#         col1, col2 = st.columns(2)
#
#         with col1:
#             st.subheader("Current Inventory Levels")
#             quantities = fetch_component_quantities()
#             quantities_df = pd.DataFrame(list(quantities.items()), columns=['Component', 'Stock'])
#             st.dataframe(quantities_df)
#
#         with col2:
#             st.subheader("Component Lead Times")
#             lead_times = fetch_lead_times()
#             lead_times_df = pd.DataFrame([(k, v.strftime('%Y-%m-%d %H:%M')) for k, v in lead_times.items()],
#                                          columns=['Component', 'Target Completion'])
#             st.dataframe(lead_times_df)
#
# # Add a footer
# st.markdown("""
# <style>
# .footer {
#     position: fixed;
#     left: 0;
#     bottom: 0;
#     width: 100%;
#     background-color: #f0f2f6;
#     color: #2c3e50;
#     text-align: center;
#     padding: 10px 0;
#     font-size: 14px;
# }
# </style>
# <div class="footer">
#     © 2024 Smart Production Hub | Empowering Efficient Manufacturing
# </div>
# """, unsafe_allow_html=True)


import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests

# Set up Streamlit page configuration
st.set_page_config(layout="wide", page_title="Smart Production Scheduling")

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
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    .stat-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
    }
    .stat-box h3 {
        margin-bottom: 10px;
        color: #2c3e50;
    }
    .success-message {
        padding: 10px;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin-bottom: 10px;
    }
    .stSelectbox, .stTextInput, .stNumberInput {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = "Production Schedule"
if 'show_success' not in st.session_state:
    st.session_state.show_success = False


# Function to format time
def format_time(minutes):
    delta = timedelta(minutes=minutes)
    days, seconds = delta.days, delta.seconds
    hours, minutes = divmod(seconds, 3600)
    minutes, seconds = divmod(minutes, 60)
    return f"{days}d {hours:02d}h {minutes:02d}m"


# Sidebar for navigation
st.sidebar.title("Production Scheduling")
page = st.sidebar.radio("Navigate", ["Production Schedule", "Component & Lead Time", "Analytics"])

# Update session state
st.session_state.page = page

if st.session_state.page == "Production Schedule":
    st.title("Scheduling Dashboard")

    # Fetch data from API endpoints
    schedule_response = requests.get("http://172.18.7.85:5609/schedule/")
    daily_production_response = requests.get("http://172.18.7.85:5609/daily_production/")

    if schedule_response.status_code == 200 and daily_production_response.status_code == 200:
        schedule_data = schedule_response.json()
        daily_production_data = daily_production_response.json()

        # Dashboard layout
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown('<div class="stat-box">', unsafe_allow_html=True)
            st.subheader("Total Components")
            st.markdown(f"<h2>{daily_production_data['total_components']}</h2>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="stat-box">', unsafe_allow_html=True)
            st.subheader("Total Production Time")
            st.markdown(f"<h2>{daily_production_data['overall_time']}</h2>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="stat-box">', unsafe_allow_html=True)
            st.subheader("Estimated Completion")
            st.markdown(f"<h2>{daily_production_data['overall_end_time']}</h2>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Tabs for detailed views
        tab1, tab2, tab3 = st.tabs(["📊 Production Timeline", "📋 Scheduling Details", "🏭 Daily Analytics"])

        with tab1:
            st.header("Production Timeline Visualizer")

            # Convert schedule data to DataFrame
            schedule_df = pd.DataFrame(schedule_data)
            schedule_df['start_time'] = pd.to_datetime(schedule_df['start_time'], format='ISO8601')
            schedule_df['end_time'] = pd.to_datetime(schedule_df['end_time'], format='ISO8601')

            # Filter controls
            col1, col2 = st.columns(2)
            with col1:
                selected_components = st.multiselect("Component Filter", options=schedule_df['component'].unique(),
                                                     default=schedule_df['component'].unique())
            with col2:
                selected_machines = st.multiselect("Machine Filter", options=schedule_df['machine'].unique(),
                                                   default=schedule_df['machine'].unique())

            # Filter the dataframe
            filtered_df = schedule_df[
                schedule_df['component'].isin(selected_components) & schedule_df['machine'].isin(selected_machines)]

            # Create Gantt chart
            fig = px.timeline(filtered_df, x_start="start_time", x_end="end_time", y="machine", color="component",
                              hover_data={"description": True},
                              labels={"component": "Component", "description": "Operation"})
            fig.update_yaxes(categoryorder="total ascending")
            fig.update_layout(height=600, xaxis_title="Timeline", yaxis_title="Machine", showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.header("Scheduling Details")
            st.dataframe(schedule_df)

        with tab3:
            st.header("Daily Production Analytics")

            # Convert daily production to a DataFrame
            daily_prod_data = []
            for component, production in daily_production_data['daily_production'].items():
                for date, quantity in production.items():
                    daily_prod_data.append(
                        {"Date": date, "Component": component, "Quantity": quantity})

            daily_prod_df = pd.DataFrame(daily_prod_data)
            daily_prod_df['Date'] = pd.to_datetime(daily_prod_df['Date'], format='ISO8601')
            daily_prod_df = daily_prod_df.sort_values('Date')

            # Create a stacked bar chart
            fig = px.bar(daily_prod_df, x='Date', y='Quantity', color='Component', barmode='stack')
            fig.update_layout(
                title="Daily Component Production Breakdown",
                xaxis_title="Date",
                yaxis_title="Units Produced",
                xaxis=dict(tickformat="%Y-%m-%d")
            )
            st.plotly_chart(fig, use_container_width=True)

            # Show the data in a table format as well
            st.subheader("Detailed Daily Production Log")
            st.dataframe(daily_prod_df)

    else:
        st.error("Failed to fetch data from the API. Please check if the backend server is running.")

    # Sidebar for adding new operations
    with st.sidebar:
        st.header("Operation Architect")
        with st.form("new_operation"):
            component = st.text_input("Component")
            description = st.text_input("Operation Description")
            op_type = st.text_input("Operation Type")
            machine = st.text_input("Assign Machine")
            time = st.number_input("Duration (minutes)", min_value=0, value=0)

            submitted = st.form_submit_button("Create Operation")
            if submitted:
                operation_data = {
                    "operations": [{
                        "component": component,
                        "description": description,
                        "type": op_type,
                        "machine": machine,
                        "time": time
                    }]
                }
                response = requests.post("http://172.18.7.85:5609/post_operations/", json=operation_data)
                if response.status_code == 200:
                    st.success("Operation added successfully!")
                else:
                    st.error("Failed to add operation. Please try again.")

elif st.session_state.page == "Component & Lead Time":
    st.title("Component & Lead Time Manager")

    tab1, tab2 = st.tabs(["📝 Add/Update", "👁️ Current Inventory"])

    with tab1:
        st.header("Component and Lead Time Editor")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Quantity Adjuster")
            with st.form("update_inventory"):
                component = st.text_input("Component Identifier")
                quantity = st.number_input("Stock Quantity", min_value=0, value=0)
                submitted = st.form_submit_button("Update Inventory")
                if submitted:
                    data = [{"component": component, "quantity": quantity}]
                    response = requests.post("http://172.18.7.85:5609/insert_component_quantities/", json=data)
                    if response.status_code == 200:
                        st.success(f"Inventory updated for {component}")
                    else:
                        st.error("Failed to update inventory. Please try again.")

        with col2:
            st.subheader("Lead Time Configurator")
            with st.form("set_lead_time"):
                lead_time_component = st.text_input("Component for Lead Time")
                due_date = st.date_input("Target Date")
                due_time = st.time_input("Target Time")
                submitted = st.form_submit_button("Set Lead Time")
                if submitted:
                    due_datetime = datetime.combine(due_date, due_time)
                    data = [{"component": lead_time_component, "due_date": due_datetime.isoformat()}]
                    response = requests.post("http://172.18.7.85:5609/insert_lead_times/", json=data)
                    if response.status_code == 200:
                        st.success(f"Lead time configured for {lead_time_component}")
                    else:
                        st.error("Failed to set lead time. Please try again.")

    with tab2:
        st.header("Inventory & Lead Time Overview")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Current Inventory Levels")
            quantities_response = requests.get("http://172.18.7.85:5609/fetch_component_quantities/")
            if quantities_response.status_code == 200:
                quantities = quantities_response.json()
                quantities_df = pd.DataFrame(list(quantities.items()), columns=['Component', 'Stock'])
                st.dataframe(quantities_df)
            else:
                st.error("Failed to fetch inventory data.")

        with col2:
            st.subheader("Component Lead Times")
            lead_times_response = requests.get("http://172.18.7.85:5609/lead-time-table")
            if lead_times_response.status_code == 200:
                lead_times = lead_times_response.json()
                lead_times_df = pd.DataFrame(lead_times)
                lead_times_df['due_date'] = pd.to_datetime(lead_times_df['due_date'])
                st.dataframe(lead_times_df)
            else:
                st.error("Failed to fetch lead time data.")

elif st.session_state.page == "Analytics":
    st.title("Production Analytics")

    # Fetch component status data
    component_status_response = requests.get("http://172.18.7.85:5609/component_status/")
    if component_status_response.status_code == 200:
        component_status = component_status_response.json()

        # Prepare data for visualization
        status_data = []
        for category in ['early_complete', 'on_time_complete', 'delayed_complete']:
            for item in component_status[category]:
                status_data.append({
                    'Component': item['component'],
                    'Scheduled End Time': item['scheduled_end_time'],
                    'Lead Time': item['lead_time'],
                    'Status': category.replace('_', ' ').title(),
                    'Completed Quantity': item['completed_quantity'],
                    'Total Quantity': item['total_quantity'],
                    'Delay': item['delay'] if item['delay'] is not None else 0
                })

        status_df = pd.DataFrame(status_data)
        status_df['Scheduled End Time'] = pd.to_datetime(status_df['Scheduled End Time'])
        status_df['Lead Time'] = pd.to_datetime(status_df['Lead Time'])

        # Create a mixed graph (bar + line) for lead time vs. scheduled time
        fig = go.Figure()

        # Add bar chart for scheduled end time
        fig.add_trace(go.Bar(
            x=status_df['Component'],
            y=status_df['Scheduled End Time'],
            name='Scheduled End Time',
            marker_color='blue'
        ))

        # Add line chart for lead time
        fig.add_trace(go.Scatter(
            x=status_df['Component'],
            y=status_df['Lead Time'],
            mode='lines+markers',
            name='Lead Time',
            line=dict(color='red', width=2)
        ))

        fig.update_layout(
            title='Lead Time vs. Scheduled Time',
            xaxis_title='Component',
            yaxis_title='Time',
            barmode='group',
            legend_title='Metric',
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

        # Component Status Breakdown
        st.subheader("Component Status Breakdown")
        status_counts = status_df['Status'].value_counts()
        fig_pie = px.pie(values=status_counts.values, names=status_counts.index, title='Component Status Distribution')
        st.plotly_chart(fig_pie, use_container_width=True)

        # Detailed Component Status Table
        st.subheader("Detailed Component Status")
        st.dataframe(status_df)

    else:
        st.error("Failed to fetch component status data. Please check if the backend server is running.")

# Add a footer
st.markdown("""
<div style="position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f0f2f6; color: #2c3e50; text-align: center; padding: 10px 0; font-size: 14px;">
    © 2024 Smart Production Hub | Empowering Efficient Manufacturing
</div>
""", unsafe_allow_html=True)