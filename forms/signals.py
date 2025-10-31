from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from forms.models import Response as FormResponse, Answer

def _broadcast_form(form_id, report_type="summary"):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"form_{form_id}",
        {"type": "report.update", "form_id": str(form_id), "report_type": report_type},
    )

def _on_commit_broadcast(form_id):
    transaction.on_commit(lambda: _broadcast_form(form_id, "summary"))

@receiver(post_save, sender=FormResponse)
@receiver(post_delete, sender=FormResponse)
def response_changed(sender, instance, **kwargs):
    _on_commit_broadcast(instance.form_id)

@receiver(post_save, sender=Answer)
@receiver(post_delete, sender=Answer)
def answer_changed(sender, instance, **kwargs):
    _on_commit_broadcast(instance.response.form_id)
