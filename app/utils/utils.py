def recalc_order_status(order):
    active_items = [
        item for item in order.items
        if item.status != "CANCELLED"
    ]

    if not active_items:
        order.status = "CANCELLED"
    elif len(active_items) < len(order.items):
        order.status = "PARTIALLY_CANCELLED"
    else:
        order.status = "PLACED"


def recalc_order_total(order):
    order.total_amount = sum(
        item.subtotal
        for item in order.items
        if item.status != "CANCELLED"
    )