from django.utils import timezone
from celery import shared_task

from forms.models import Report
from forms.services.reporting import ReportService

@shared_task(name="forms.tasks.run_due_reports")
def run_due_reports():
    """Find all due scheduled reports and run them."""
    now = timezone.now()
    svc = ReportService(now)
    due = Report.objects.filter(is_active=True, next_run__isnull=False, next_run__lte=now)                             .select_related("form", "created_by")
    ran = 0
    for rep in due:
        svc.run_once(rep)
        ran += 1
    return {"ran": ran}
