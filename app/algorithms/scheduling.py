from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Tuple, List
from app.crud.dynamic_scheduling import fetch_raw_materials, fetch_machine_statuses


def adjust_to_shift_hours(time: datetime) -> datetime:
    if time.hour < 9:
        return time.replace(hour=9, minute=0, second=0, microsecond=0)
    elif time.hour >= 17:
        return (time + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    return time


def schedule_operations(df: pd.DataFrame, component_quantities: Dict[str, int], lead_times: Dict[str, datetime]) -> \
        Tuple[pd.DataFrame, datetime, float, Dict, Dict, List[str]]:
    if df.empty:
        return pd.DataFrame(), datetime.now(), 0.0, {}, {}, []

    # Fetch raw materials and machine statuses
    raw_materials = {rm.name: (rm.available, rm.available_from) for rm in fetch_raw_materials()}
    machine_statuses = {ms.machine: (ms.status, ms.available_from) for ms in fetch_machine_statuses()}

    # Pre-process the dataframe to group by component and get operation sequences
    df_sorted = df.sort_values(by=['component', 'id'])
    component_operations = {
        component: group.to_dict('records')
        for component, group in df_sorted.groupby('component')
    }

    start_date = df_sorted['start_time'].min()
    if pd.isnull(start_date):
        start_date = datetime.now()

    start_date = adjust_to_shift_hours(start_date)

    schedule = []
    machine_end_times = {machine: start_date for machine in df_sorted["machine"].unique()}
    daily_production = {}
    component_status = {}
    partially_completed = []

    def check_machine_status(machine: str, time: datetime) -> Tuple[bool, datetime]:
        status, available_from = machine_statuses.get(machine, ('OFF', None))
        if status == 'OFF':
            return False, None
        if available_from and time < available_from:
            return False, available_from
        return True, time

    def find_last_available_operation(operations: List[dict], current_time: datetime) -> int:
        """Returns the index of the last available operation in the sequence."""
        last_available = -1
        current_op_time = current_time

        for idx, op in enumerate(operations):
            machine = op['machine']
            machine_available, available_time = check_machine_status(machine, current_op_time)

            if not machine_available and available_time is None:
                break

            if available_time:
                current_op_time = available_time

            last_available = idx
            current_op_time += timedelta(minutes=op['time'])

        return last_available

    def schedule_batch_operations(component: str, operations: List[dict], quantity: int, start_time: datetime) -> Tuple[
        List[list], int, Dict[int, datetime]]:
        batch_schedule = []
        operation_time = start_time
        unit_completion_times = {}  # Track when each unit completes all its operations

        # Check raw material availability
        raw_available, raw_time = raw_materials.get(component, (False, None))
        if not raw_available:
            return [], 0, {}  # Added empty dict for unit_completion_times

        if raw_time and operation_time < raw_time:
            operation_time = raw_time

        # Find the last available operation in the sequence
        last_available_idx = find_last_available_operation(operations, operation_time)

        if last_available_idx < 0:
            return [], 0, {}  # Added empty dict for unit_completion_times

        # Get the subset of operations that can be performed
        available_operations = operations[:last_available_idx + 1]

        # Process each unit through available operations
        for batch_num in range(quantity):
            current_time = operation_time
            unit_number = batch_num + 1

            # Process each available operation in sequence
            for op_idx, op in enumerate(available_operations):
                machine = op['machine']
                time_required = op['time']

                # Adjust for machine availability
                _, available_time = check_machine_status(machine, current_time)
                if available_time:
                    current_time = available_time

                current_time = adjust_to_shift_hours(current_time)
                current_time = max(current_time, machine_end_times.get(machine, current_time))
                operation_start = current_time
                operation_end = operation_start + timedelta(minutes=time_required)

                # Handle shift boundary crossing
                if operation_end.hour >= 17:
                    shift_end = operation_start.replace(hour=17, minute=0, second=0, microsecond=0)
                    remaining_time = (operation_end - shift_end).total_seconds() / 60

                    # Today's portion
                    batch_schedule.append([
                        component, op['description'], op['type'], machine,
                        operation_start, shift_end, f"{unit_number}/{quantity}"
                    ])
                    machine_end_times[machine] = shift_end

                    # Next day portion
                    next_day = (shift_end + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
                    next_day_end = next_day + timedelta(minutes=remaining_time)
                    batch_schedule.append([
                        component, op['description'], op['type'], machine,
                        next_day, next_day_end, f"{unit_number}/{quantity}"
                    ])
                    current_time = next_day_end
                    machine_end_times[machine] = next_day_end

                    # If this is the last operation for this unit, record completion time
                    if op_idx == len(available_operations) - 1:
                        unit_completion_times[unit_number] = next_day_end
                else:
                    batch_schedule.append([
                        component, op['description'], op['type'], machine,
                        operation_start, operation_end, f"{unit_number}/{quantity}"
                    ])
                    current_time = operation_end
                    machine_end_times[machine] = operation_end

                    # If this is the last operation for this unit, record completion time
                    if op_idx == len(available_operations) - 1:
                        unit_completion_times[unit_number] = operation_end

        return batch_schedule, len(
            available_operations), unit_completion_times  # Now returning all three values consistently

    # Sort components by lead time
    sorted_components = sorted(
        component_quantities.keys(),
        key=lambda x: (lead_times.get(x, datetime.max), x)
    )

    # Schedule batches for each component
    for component in sorted_components:
        if component not in component_operations:
            continue

        operations = component_operations[component]
        quantity = component_quantities[component]
        lead_time = lead_times.get(component)

        batch_schedule, completed_ops, unit_completion_times = schedule_batch_operations(
            component, operations, quantity, start_date
        )

        if batch_schedule:
            schedule.extend(batch_schedule)

            # Calculate the latest completion time for this component
            latest_completion_time = max(unit_completion_times.values()) if unit_completion_times else None

            # Create status dictionary matching your ComponentStatus model
            component_status[component] = {
                'component': component,
                'scheduled_end_time': latest_completion_time,
                'lead_time': lead_time,
                'on_time': latest_completion_time <= lead_time if lead_time and latest_completion_time else None,
                'completed_quantity': len(unit_completion_times),
                'total_quantity': quantity,
                'lead_time_provided': lead_time is not None
            }

            # Update daily production
            for unit_num, completion_time in unit_completion_times.items():
                completion_day = completion_time.date()
                if component not in daily_production:
                    daily_production[component] = {}
                if completion_day not in daily_production[component]:
                    daily_production[component][completion_day] = 0
                daily_production[component][completion_day] += 1

            if completed_ops < len(operations):
                partially_completed.append(
                    f"{component}: Completed {completed_ops}/{len(operations)} operation types for {quantity} units")

    schedule_df = pd.DataFrame(
        schedule,
        columns=["component", "description", "type", "machine", "start_time", "end_time", "quantity"]
    )

    if schedule_df.empty:
        return schedule_df, start_date, 0.0, daily_production, {}, partially_completed

    overall_end_time = max(schedule_df['end_time'])
    overall_time = (overall_end_time - start_date).total_seconds() / 60

    return schedule_df, overall_end_time, overall_time, daily_production, component_status, partially_completed