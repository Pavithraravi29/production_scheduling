from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Tuple

def schedule_operations(df: pd.DataFrame, component_quantities: Dict[str, int], lead_times: Dict[str, datetime]) -> Tuple[pd.DataFrame, datetime, float, Dict, Dict]:
    if df.empty:
        return pd.DataFrame(), datetime.now(), 0.0, {}, {}

    df_sorted = df.sort_values(by=['component', 'id'])
    start_date = df_sorted['start_time'].min()
    if pd.isnull(start_date):
        start_date = datetime.now()

    # Adjust start_date to the next 9 AM if it's not within shift hours
    if start_date.hour < 9 or start_date.hour >= 17:
        start_date = (start_date + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

    schedule = []
    machine_end_times = {machine: start_date for machine in df_sorted["machine"].unique()}
    current_time = start_date
    daily_production = {}
    remaining_quantities = component_quantities.copy()
    component_status = {}

    def schedule_component(component: str, start_time: datetime) -> Tuple[list, datetime]:
        component_ops = df_sorted[df_sorted["component"] == component]
        unit_operations = []
        end_time = start_time

        for _, row in component_ops.iterrows():
            description, op_type, machine, time = row[["description", "type", "machine", "time"]]
            start_time = max(start_time, machine_end_times[machine])

            # Adjust start_time to next shift if it's outside shift hours
            if start_time.hour < 9 or start_time.hour >= 17:
                start_time = (start_time + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

            end_time = start_time + timedelta(minutes=time)

            # If operation ends after shift, split it
            if end_time.hour >= 17:
                remaining_time = (end_time - start_time).total_seconds() / 60
                today_end = start_time.replace(hour=17, minute=0, second=0, microsecond=0)
                today_duration = (today_end - start_time).total_seconds() / 60

                # Add operation for today
                unit_operations.append([
                    component, description, op_type, machine, start_time, today_end,
                    f"{component_quantities[component] - remaining_quantities[component] + 1}/{component_quantities[component]}"
                ])
                machine_end_times[machine] = today_end

                # Schedule remaining time for next day
                next_day_start = (today_end + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
                next_day_end = next_day_start + timedelta(minutes=remaining_time - today_duration)
                unit_operations.append([
                    component, description, op_type, machine, next_day_start, next_day_end,
                    f"{component_quantities[component] - remaining_quantities[component] + 1}/{component_quantities[component]}"
                ])
                machine_end_times[machine] = next_day_end
                end_time = next_day_end
            else:
                unit_operations.append([
                    component, description, op_type, machine, start_time, end_time,
                    f"{component_quantities[component] - remaining_quantities[component] + 1}/{component_quantities[component]}"
                ])
                machine_end_times[machine] = end_time

            start_time = end_time

        lead_time = lead_times.get(component)
        component_status[component] = {
            'scheduled_end_time': end_time,
            'lead_time': lead_time,
            'on_time': lead_time is None or end_time <= lead_time,
            'completed_quantity': component_quantities[component] - remaining_quantities[component] + 1,
            'total_quantity': component_quantities[component],
            'lead_time_provided': lead_time is not None
        }

        return unit_operations, end_time

    # Sort components by lead time, putting components without lead time at the end
    sorted_components = sorted(
        component_quantities.keys(),
        key=lambda x: (lead_times.get(x, datetime.max), x)
    )

    while any(remaining_quantities.values()):
        day_start = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
        day_end = day_start.replace(hour=17, minute=0, second=0, microsecond=0)

        for component in sorted_components:
            if remaining_quantities[component] <= 0:
                continue

            while remaining_quantities[component] > 0:
                unit_start_time = max(min(machine_end_times.values()), day_start)
                if unit_start_time >= day_end:
                    break

                unit_operations, unit_end_time = schedule_component(component, unit_start_time)
                schedule.extend(unit_operations)
                remaining_quantities[component] -= 1

                # Update daily production
                if unit_operations:
                    completion_day = unit_operations[-1][5].date()
                    if component not in daily_production:
                        daily_production[component] = {}
                    if completion_day not in daily_production[component]:
                        daily_production[component][completion_day] = 0
                    daily_production[component][completion_day] += 1

        current_time = (day_end + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

    schedule_df = pd.DataFrame(
        schedule,
        columns=[
            "component", "description", "type", "machine", "start_time", "end_time", "quantity"
        ],
    )
    overall_end_time = max(schedule_df['end_time'])
    overall_time = (overall_end_time - start_date).total_seconds() / 60

    return schedule_df, overall_end_time, overall_time, daily_production, component_status