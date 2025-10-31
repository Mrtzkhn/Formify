import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from forms.models import Response as FormResponse, Answer, FormView


@dataclass
class DeliveryResult:
    ok: bool
    channel: str
    detail: str


class ReportService:
    """
    Builds and (optionally) delivers reports for forms.
    Supports types: 'summary', 'detailed.
    Delivery: email (default).
    """

    def __init__(self, now=None):
        self.now = now or timezone.now()

    # ---------- Public API ----------

    def generate(self, report):
        if report.type == 'summary':
            return self._build_summary(report.form)
        elif report.type == 'detailed':
            return self._build_detailed(report.form)
        else:
            raise ValueError(f"Unknown report type: {report.type}")

    def deliver(self, report, payload):
        method = report.delivery_method

        if method == 'email':
            return self._deliver_email(report, payload)
        else:
            return DeliveryResult(False, method, f"Unsupported delivery method: {method}")

    def run_once(self, report):
        """
        Generate + deliver (if active). Returns execution metadata + payload.
        """
        data = self.generate(report)
        delivery = None
        if report.is_active:
            delivery = self.deliver(report, data)
        # Update next_run for scheduled reports
        self._bump_next_run(report)
        return {
            "report_id": report.id,
            "form_id": str(report.form_id),
            "type": report.type,
            "delivered": bool(delivery and delivery.ok),
            "delivery": delivery.__dict__ if delivery else None,
            "generated_at": self.now.isoformat(),
            "payload": data,
        }

    # ---------- Builders ----------

    def _build_summary(self, form):
        qs = FormResponse.objects.filter(form=form)
        total = qs.count()
        last = qs.order_by('-submitted_at').values_list('submitted_at', flat=True).first()

        # Responses per day (last 30 days)
        since = self.now - timedelta(days=30)
        daily = (
            qs.filter(submitted_at__gte=since)
              .annotate(day=TruncDate('submitted_at'))
              .values('day')
              .annotate(count=Count('id'))
              .order_by('day')
        )
        daily_series = [{"date": d["day"].isoformat(), "count": d["count"]} for d in daily]

        # Field-level aggregates
        field_stats = {}
        answers = Answer.objects.filter(response__form=form).select_related('field')

        # group answers by field
        by_field = defaultdict(list)
        for a in answers:
            by_field[str(a.field_id)].append(a)

        for field_id, items in by_field.items():
            # try to parse numeric values
            numeric_vals = []
            text_vals = []
            for it in items:
                v = (it.value or "").strip()
                if v == "":
                    continue
                try:
                    numeric_vals.append(float(v))
                except Exception:
                    text_vals.append(v)

            summary = {}
            if numeric_vals:
                summary["count"] = len(numeric_vals)
                summary["min"] = min(numeric_vals)
                summary["max"] = max(numeric_vals)
                try:
                    summary["mean"] = statistics.mean(numeric_vals)
                except Exception:
                    pass
                try:
                    summary["median"] = statistics.median(numeric_vals)
                except Exception:
                    pass
            if text_vals:
                top = Counter(text_vals).most_common(10)
                summary["top_values"] = [{"value": v, "count": c} for v, c in top]

            field_stats[field_id] = summary

        # Getting the total form view
        total_viewers = FormView.objects.filter(form=form).count()

        return {
            "form": {"id": str(form.id), "title": form.title},
            "totals": {
                "responses": total,
                "viewers": total_viewers,
                "last_response_at": last.isoformat() if last else None,
            },
            "responses_per_day": daily_series,
            "fields": field_stats,
        }

    def _build_detailed(self, form):
        latest = (
            FormResponse.objects.filter(form=form)
            .order_by('-submitted_at')
            .select_related('submitted_by')
        )
        data = []
        for r in latest:
            answers = Answer.objects.filter(response=r).select_related('field')
            data.append({
                "response_id": str(r.id),
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
                "submitted_by": getattr(r.submitted_by, 'email', None),
                "answers": [
                    {
                        "field_id": str(ans.field_id),
                        "field_label": getattr(ans.field, 'label', None),
                        "value": ans.value,
                    } for ans in answers
                ],
            })
        return {
            "form": {"id": str(form.id), "title": form.title},
            "responses": data,
        }

    # ---------- Delivery helpers ----------

    def _deliver_email(self, report, payload):
        subject = f"[Formify] {report.form.title} – {report.type.capitalize()} report"

        to_email = getattr(report.created_by, 'email', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        if not to_email:
            return DeliveryResult(False, "email",
                                  "No recipient email configured (report.created_by.email or DEFAULT_FROM_EMAIL).")

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)

        if report.type == 'summary':
            body_lines = [
                f"Report Type: {report.type}",
                f"Form: {report.form.title}",
                "",
                "Summary:",
                f"Total responses: {payload.get('totals', {}).get('responses')}",
                f"Last response at: {payload.get('totals', {}).get('last_response_at')}",
                "",
                "This is an automated message."
            ]
            message = "\n".join(body_lines)

        elif report.type == 'detailed':
            body_lines = [
                f"Report Type: {report.type}",
                f"Form: {report.form.title}",
                "",
                "detailed:",
                f"People Answered:\n{'\n'.join([person.get('submitted_by') for person in payload.get('responses')])}",
                "",
                "This is an automated message."
            ]
            message = "\n".join(body_lines)

        try:
            send_mail(subject, message, from_email, [to_email], fail_silently=False)
            return DeliveryResult(True, "email", f"Email sent to {to_email}")
        except Exception as e:
            return DeliveryResult(False, "email", f"Email send failed: {e}")

    # ---------- Scheduling ----------

    def compute_initial_next_run(self, report):
        """Compute next_run based on schedule_type, if not manual."""
        if report.schedule_type == 'manual':
            return None
        base = self.now
        if report.schedule_type == 'weekly':
            return base + timedelta(days=7)
            # return base + timedelta(seconds=30)
        if report.schedule_type == 'monthly':
            return base + timedelta(days=30)
        return None

    def _bump_next_run(self, report):
        if report.schedule_type == 'manual':
            return
        nxt = self.compute_initial_next_run(report)
        if nxt:
            report.next_run = nxt
            report.save(update_fields=['next_run'])


# Convenience singleton
report_service = ReportService()