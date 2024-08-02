def schedule_operations(df: pd.DataFrame) -> (pd.DataFrame, datetime, float):
    if df.empty:
        return pd.DataFrame(), datetime.now(), 0.0

    # Sort DataFrame by 'id' to maintain the sequence as stored in the database
    df_sorted = df.sort_values(by='id')

    schedule = []
    machine_end_times = {machine: df_sorted['start_time'].min() for machine in df_sorted["machine"].unique()}
    component_end_times = {component: df_sorted['start_time'].min() for component in df_sorted["component"].unique()}
    component_last_end_time = {component: df_sorted['start_time'].min() for component in df_sorted["component"].unique()}

    for component, component_df in df_sorted.groupby('component'):
        component_df = component_df.sort_values(by='id')  # Ensure operations within component are in order

        for _, row in component_df.iterrows():
            description, op_type, machine, time, start_time, quantity = row[
                ["description", "type", "machine", "time", "start_time", "quantity"]
            ]
            start_time = max(start_time, component_last_end_time[component])  # Use last end time for the component

            # Check machine availability
            if start_time < machine_end_times[machine]:
                start_time = machine_end_times[machine]

            # Calculate operation time considering quantity
            operation_time = time * quantity

            end_time = start_time + timedelta(minutes=operation_time)
            schedule.append(
                [
                    component,
                    description,
                    op_type,
                    machine,
                    start_time,
                    end_time,
                    quantity
                ]
            )
            component_last_end_time[component] = end_time
            machine_end_times[machine] = end_time
            component_end_times[component] = max(component_end_times[component], end_time)

    schedule_df = pd.DataFrame(
        schedule,
        columns=[
            "component",
            "description",
            "type",
            "machine",
            "start_time",
            "end_time",
            "quantity"
        ],
    )

    # Calculate total time
    overall_end_time = max(component_end_times.values())
    overall_time = (overall_end_time - df_sorted['start_time'].min()).total_seconds() / 60

    return schedule_df, overall_end_time, overall_time






"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
from datetime import datetime, timedelta, time as datetime_time


def schedule_operations(df: pd.DataFrame, component_quantities: dict) -> (pd.DataFrame, datetime, float, dict):
    if df.empty:
        return pd.DataFrame(), datetime.now(), 0.0, {}

    df_sorted = df.sort_values(by=['component', 'id'])

    start_date = df_sorted['start_time'].min()
    if pd.isnull(start_date):
        start_date = datetime.now()

    # Align start_date to the next 9 AM
    start_date = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
    if start_date.time() > datetime_time(9, 0):
        start_date += timedelta(days=1)

    schedule = []
    machine_end_times = {machine: start_date for machine in df_sorted["machine"].unique()}
    current_time = start_date
    daily_production = {}
    remaining_quantities = component_quantities.copy()

    def schedule_component(component, start_time):
        component_ops = df_sorted[df_sorted["component"] == component]
        unit_operations = []
        for _, row in component_ops.iterrows():
            description, op_type, machine, operation_time = row[["description", "type", "machine", "time"]]
            start_time = max(start_time, machine_end_times[machine])

            # Adjust start_time to next available shift start if necessary
            if start_time.time() < datetime_time(9, 0) or start_time.time() >= datetime_time(17, 0):
                start_time = (start_time + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

            end_time = start_time + timedelta(minutes=operation_time)

            # If operation can't be completed within shift, move to next day
            if end_time.time() > datetime_time(17, 0):
                start_time = start_time.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
                end_time = start_time + timedelta(minutes=operation_time)

            unit_operations.append([
                component,
                description,
                op_type,
                machine,
                start_time,
                end_time,
                f"{component_quantities[component] - remaining_quantities[component] + 1}/{component_quantities[component]}"
            ])
            machine_end_times[machine] = end_time
            start_time = end_time
        return unit_operations, start_time

    while any(remaining_quantities.values()):
        shift_start = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
        shift_end = shift_start.replace(hour=17, minute=0, second=0, microsecond=0)

        for component in list(remaining_quantities.keys()):
            if remaining_quantities[component] <= 0:
                continue

            while remaining_quantities[component] > 0:
                unit_start_time = max(min(machine_end_times.values()), shift_start)
                if unit_start_time >= shift_end:
                    break

                unit_operations, unit_end_time = schedule_component(component, unit_start_time)

                if unit_end_time <= shift_end:
                    schedule.extend(unit_operations)
                    remaining_quantities[component] -= 1

                    if component not in daily_production:
                        daily_production[component] = {}
                    day = unit_start_time.date()
                    if day not in daily_production[component]:
                        daily_production[component][day] = 0
                    daily_production[component][day] += 1
                else:
                    break

        current_time = shift_end + timedelta(days=1)

    schedule_df = pd.DataFrame(
        schedule,
        columns=[
            "component",
            "description",
            "type",
            "machine",
            "start_time",
            "end_time",
            "quantity"
        ],
    )

    overall_end_time = max(schedule_df['end_time'])
    overall_time = (overall_end_time - start_date).total_seconds() / 60

    return schedule_df, overall_end_time, overall_time, daily_production