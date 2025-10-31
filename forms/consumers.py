from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from uuid import UUID

from forms.models import Form
from forms.services.reporting import ReportService

class FormReportConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        raw = self.scope["url_route"]["kwargs"]["form_id"]
        try:
            self.form_id = UUID(raw)          # accepts both 32-char and hyphenated
        except ValueError:
            await self.close(code=4404)       # invalid ID
            return

        qs = parse_qs(self.scope.get("query_string", b"").decode())
        self.report_type = (qs.get("type", ["summary"])[0] or "summary").lower()

        can_view = await self._can_view_form(self.form_id)
        if not can_view:
            await self.close(code=4403)
            return

        self.group_name = f"form_{self.form_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        payload = await self._build_payload(self.form_id, self.report_type)
        await self.send_json({"type": "init", "report_type": self.report_type, "payload": payload})

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("action") == "refresh":
            payload = await self._build_payload(self.form_id, self.report_type)
            await self.send_json({"type": "refresh", "payload": payload})

    async def report_update(self, event):
        payload = await self._build_payload(event["form_id"], event["report_type"])
        await self.send_json({"type": "update", "payload": payload})

    @database_sync_to_async
    def _can_view_form(self, form_id):
        try:
            form = Form.objects.get(id=form_id)
        except Form.DoesNotExist:
            return False
        # Allow public forms or staff/owner; adjust to your needs.
        user = getattr(self.scope, "user", None)
        if getattr(form, "is_public", True):
            return True
        return bool(user and user.is_authenticated and (user.is_staff or form.created_by_id == user.id))

    @database_sync_to_async
    def _build_payload(self, form_id, report_type):
        svc = ReportService()
        # Build a tiny shim object to reuse the service
        class _R: pass
        r = _R()
        r.type = report_type
        r.form = Form.objects.get(id=form_id)
        return svc.generate(r)
