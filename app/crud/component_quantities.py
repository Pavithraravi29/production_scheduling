from typing import List, Dict
from app.database.models import ComponentQuantity
from app.schemas.component_quantities import ComponentQuantityIn, ComponentQuantityOut
from pony.orm import db_session, select, commit

@db_session
def fetch_component_quantities() -> Dict[str, int]:
    quantities = select(cq for cq in ComponentQuantity)[:]
    return {cq.component: cq.quantity for cq in quantities}

@db_session
def insert_component_quantities(quantities: List[ComponentQuantityIn]) -> List[ComponentQuantityOut]:
    results = []
    for qty in quantities:
        component = qty.component
        quantity = qty.quantity
        existing = ComponentQuantity.get(component=component)
        if existing:
            existing.quantity = quantity
        else:
            ComponentQuantity(component=component, quantity=quantity)
        results.append(ComponentQuantityOut(component=component, quantity=quantity))
    commit()
    return results
