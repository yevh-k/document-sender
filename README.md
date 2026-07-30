# Document Sender

Document Sender is a Home Assistant custom integration for reliable SMTP email delivery. It is built for Home Assistant Core **2025.12+** and Python **3.13**, with an async runtime, Config Flow setup, persistent delivery history, and HACS packaging.

## Highlights

- Gmail SMTP with a Google App Password, or any STARTTLS-capable SMTP server
- Multiple recipients, unlimited managed attachments, and automatic image processing
- Reusable plain-text and HTML/Jinja templates
- Daily, weekly, monthly (last valid day is used), and one-time schedules
- `Send`, `Send test message`, and `Resend last message` button entities
- Persistent Home Assistant and Mobile App delivery notifications
- SQLite audit log and durable attachment/template/schedule storage
- English, Polish, and Ukrainian UI translations
- Native **Document Sender** sidebar panel for message composition, managed
  uploads, camera snapshots, saved drafts, and masked delivery history

## Management panel

After an account loads, select **Document Sender** in the Home Assistant
sidebar. The panel is a native Lit module, not an iframe. It communicates over
authenticated WebSocket commands and never receives SMTP credentials. Browser
uploads are copied into the private integration attachment directory, so the
browser cannot supply arbitrary filesystem paths.

## Installation

See [INSTALLATION.md](INSTALLATION.md) for HACS and manual installation instructions.

## First setup

1. In Home Assistant, open **Settings → Devices & services → Add integration**.
2. Select **Document Sender**.
3. For Gmail enter `smtp.gmail.com`, port `587`, your Gmail address, and a [Google App Password](https://myaccount.google.com/apppasswords). Do not use your normal Google password.
4. Enter the sender display name, default sender email, and one or more default recipients.
5. Select the **Test connection** action. Document Sender authenticates with SMTP without sending an email; the integration is saved only when that test succeeds.
6. Press the **Send test message** button on the created device.

Settings are stored by Home Assistant's internal config-entry storage, so the SMTP password is never written to YAML or this repository. Use the integration's **Reconfigure** action to change SMTP credentials; the regular **Configure** action opens delivery and notification options.

## Managers and services

The integration uses native Home Assistant services as its attachment, template, and schedule manager. The `list_*` services return data in the Developer Tools service-response panel; use the returned IDs in automation YAML or subsequent service calls. Add `entry_id` to any call when more than one Document Sender entry is configured.

| Service | Purpose |
| --- | --- |
| `document_sender.add_attachment` / `remove_attachment` / `list_attachments` | Copy files into, remove from, and inspect managed attachment storage. |
| `document_sender.save_template` / `remove_template` / `list_templates` | Create, update, delete, and inspect reusable templates. |
| `document_sender.save_schedule` / `remove_schedule` / `list_schedules` | Create, update, delete, and inspect schedules. |
| `document_sender.send` | Send a one-off message. |
| `document_sender.test_send` | Verify SMTP delivery. |
| `document_sender.resend_last` | Re-send the last successful logged message. |

### Add an attachment

`path` is copied at the time of the service call. The original file can then change or be removed without affecting the message.

```yaml
service: document_sender.add_attachment
data:
  path: /config/www/monthly-report.pdf
  name: report.pdf
response_variable: attachment_result
```

Use `attachment_result.attachment.id` in a send call. JPEG, PNG, and WEBP images are resized before SMTP submission while preserving aspect ratio. HEIC/HEIF images are converted to JPEG for broad mail-client compatibility. Configure output quality and the maximum attachment size in the integration's **Configure** screen; oversized non-images and images that cannot be reduced to the selected size are rejected before SMTP submission.

### Save and use a template

```yaml
service: document_sender.save_template
data:
  name: Daily report
  subject: "Daily report — {{ now().strftime('%Y-%m-%d') }}"
  text: "The current temperature is {{ states('sensor.temperature') }} °C."
  html: "<h1>Daily report</h1><p>Temperature: <b>{{ states('sensor.temperature') }} °C</b></p>"
response_variable: template_result
```

Templates use Home Assistant's normal Jinja environment, so states, helpers, and functions such as `now()` are available at send time.

```yaml
service: document_sender.send
data:
  template_id: "{{ template_result.template.id }}"
  recipients:
    - to@example.com
  cc:
    - copy@example.com
  bcc:
    - audit@example.com
  attachments:
    - "abc123"
```

`bcc` addresses are used only in the SMTP envelope and are never added to the
message headers. Every value in `attachments` must be a managed attachment ID.
The legacy `attachment_ids` send field remains accepted for backward
compatibility. You can override a template's subject, text, HTML, recipients,
or attachments in `document_sender.send`.

### Create schedules

All schedules run in Home Assistant's configured local time zone. `weekday` uses ISO-style zero-based numbers: `0` Monday through `6` Sunday. Monthly schedules requested for the 29th–31st run on the last day in shorter months. A one-time schedule is disabled after its delivery attempt.

```yaml
# Every weekday at 08:30
service: document_sender.save_schedule
data:
  name: Weekday summary
  schedule_type: weekly
  weekday: 0
  time: "08:30"
  template_id: "daily_report_template_id"
  attachment_ids:
    - "report_attachment_id"

# On the last valid day of each month at 09:00
service: document_sender.save_schedule
data:
  name: Monthly statement
  schedule_type: monthly
  day: 31
  time: "09:00"
  subject: Monthly statement
  text: Your statement is attached.

# Once at the stated local date and time
service: document_sender.save_schedule
data:
  name: Renewal reminder
  schedule_type: once
  date: "2026-12-01"
  time: "10:00"
  subject: Renewal reminder
  text: Your document renewal is due today.
```

## Notifications and logs

By default, every delivery result creates a persistent notification and is sent to every configured `notify.mobile_app_*` service. Both behaviors can be disabled in the integration's **Configure** screen.

Delivery attempts are logged in a per-entry SQLite database under Home Assistant's `.storage` directory. The log stores recipient addresses, message bodies, attachment IDs/names, timestamp, source, and SMTP outcome. It intentionally never stores SMTP credentials. Treat your Home Assistant backup as sensitive because it contains this audit history and copied attachments.

## Development

```bash
python -m pip install black ruff mypy
ruff check .
black --check .
mypy custom_components/document_sender
```

The component follows Home Assistant's async rules: network I/O uses `aiosmtplib`, while SQLite, Pillow, and filesystem work run through the executor.

## License

MIT. See [LICENSE](LICENSE).
