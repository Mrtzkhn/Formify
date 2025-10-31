# Formify – Reporting

* **ReportService** (`forms/services/reporting.py`): builds **summary** and **detailed** reports and delivers them via **email**.

* **API endpoints** (`/api/v1/forms/reports/`):

  * `GET /api/v1/forms/reports/` – list reports (owner only)
  * `POST /api/v1/forms/reports/` – create a report
  * `GET /api/v1/forms/reports/{id}/` – retrieve a report
  * `PUT /api/v1/forms/reports/{id}/` – replace a report
  * `PATCH /api/v1/forms/reports/{id}/` – update a report
  * `DELETE /api/v1/forms/reports/{id}/` – delete a report
  * `GET /api/v1/forms/reports/{id}/preview/` – generate and return report data (no delivery)
  * `POST /api/v1/forms/reports/{id}/run/` – generate + deliver via email (if `is_active=True`)

* **Admin registration**: `Report` appears in Django admin.

* **Scheduler command**: `python manage.py run_reports` executes due scheduled reports (based on `next_run`).

* **Requirements**: no extra packages required for email delivery (uses Django’s `send_mail`).

---

## Report types

### `summary` (default analytics)

* Totals:

  * **responses**: total number of submissions
  * **viewers**: total number of recorded form views (`FormView` count)
  * **last_response_at**: timestamp of the most recent submission (or `null`)

* Trend:

  * **responses_per_day** for the last 30 days

* Per-field aggregates:

  * Numeric answers → `count`, `min`, `max`, `mean`, `median`
  * Text answers → `top_values` (top 10 by frequency)

### `detailed`

* A full list of responses (most recent first), including:

  * `response_id`, `submitted_at`, `submitted_by` (email if available)
  * Each answer: `field_id`, `field_label`, `value`

---

## Delivery

* **email** – sends a plain-text email to `report.created_by.email`.
  Fallbacks to `settings.DEFAULT_FROM_EMAIL` if the creator has no email.

> Configure email in `config/settings.py` (e.g., Gmail SMTP or console backend).

---

## Quick start

1. **Migrate**

   ```bash
   python manage.py migrate
   ```

2. **Create a report (example)**

   ```http
   POST /api/v1/forms/reports/
   Content-Type: application/json
   Authorization: Bearer <token>

   {
     "form": "FORM_UUID_HERE",
     "type": "summary",            // or "detailed"
     "schedule_type": "manual",    // or "weekly" / "monthly"
     "delivery_method": "email",
     "is_active": true
   }
   ```

3. **Preview payload (no email)**

   ```http
   GET /api/v1/forms/reports/{id}/preview/
   ```

4. **Run and deliver now**

   ```http
   POST /api/v1/forms/reports/{id}/run/
   ```

5. **Scheduled runs**

   * Set `schedule_type` to `weekly` or `monthly`.
   * `next_run` is computed and bumped after each run.
   * Process due reports:

     ```bash
     python manage.py run_reports
     ```

---

## Payload shapes

### Summary

```jsonc
{
  "form": { "id": "uuid", "title": "My Form" },
  "totals": {
    "responses": 123,
    "viewers": 456,
    "last_response_at": "2025-10-30T12:34:56Z"
  },
  "responses_per_day": [
    { "date": "2025-10-01", "count": 3 },
    { "date": "2025-10-02", "count": 5 }
  ],
  "fields": {
    "FIELD_UUID": {
      // numeric fields
      "count": 42, "min": 1, "max": 99, "mean": 53.2, "median": 52
      // or for text fields
      // "top_values": [ { "value": "Yes", "count": 87 }, { "value": "No", "count": 36 } ]
    }
  }
}
```

### Detailed

```jsonc
{
  "form": { "id": "uuid", "title": "My Form" },
  "responses": [
    {
      "response_id": "resp-uuid",
      "submitted_at": "2025-10-30T10:00:00Z",
      "submitted_by": "user@example.com",
      "answers": [
        { "field_id": "f1", "field_label": "Name", "value": "Ada" },
        { "field_id": "f2", "field_label": "Age", "value": "28" }
      ]
    }
  ]
}
```