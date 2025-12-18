from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Order, AuditLog


# def audit_log(action, object_type, object_id, old_value, new_value, actor):
#     AuditLog.objects.create(
#         actor=actor,
#         action=action,
#         object_type=object_type,
#         object_id=object_id,
#         old_value=old_value,
#         new_value=new_value,
#     )


@transaction.atomic
def transition_order(*, order: Order, new_status: str, actor):
    if not order.can_transition_to(new_status):
        raise ValidationError(
            f"Invalid transition from {order.status} to {new_status}"
        )

    old_status = order.status
    order.status = new_status
    order.save(update_fields=["status"])

    AuditLog.objects.create(
        actor=actor,
        action="status_changed",
        object_type="Order",
        object_id=order.pk,
        old_value={"status": old_status},
        new_value={"status": new_status},
    )
