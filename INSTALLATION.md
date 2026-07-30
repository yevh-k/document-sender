# Installation guide

## Requirements

- Home Assistant Core 2025.12 or later
- Python 3.13 (provided by supported Core installations)
- An SMTP account. Gmail requires two-step verification and a Google App Password.

## Install with HACS

1. Push this repository to GitHub.
2. In Home Assistant, open **HACS → Integrations → ⋮ → Custom repositories**.
3. Add the GitHub repository URL and select **Integration** as the category.
4. Find **Document Sender** in HACS and select **Download**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration**, search for **Document Sender**, and complete the form.

When publishing under a GitHub account, add its real issue tracker/documentation links and code owner to `custom_components/document_sender/manifest.json` if desired. No source change is required for HACS installation.

## Manual installation

1. Copy the `custom_components/document_sender` directory into your Home Assistant configuration directory.
2. Restart Home Assistant.
3. Add **Document Sender** through **Settings → Devices & services**.

The final path should be:

```text
<config>/custom_components/document_sender/manifest.json
```

## Gmail App Password

1. Enable [2-Step Verification](https://myaccount.google.com/signinoptions/two-step-verification) for the Google account.
2. Create an [App Password](https://myaccount.google.com/apppasswords) for Mail.
3. In the integration setup enter:
   - SMTP host: `smtp.gmail.com`
   - SMTP port: `587`
   - SMTP username and sender: your Gmail address
   - SMTP password: the 16-character App Password
   - Use STARTTLS: enabled
4. Select **Test connection** in the Config Flow. It authenticates without sending mail and must succeed before configuration is saved.
5. Then use the **Send test message** button.

Google may hide App Passwords for some managed, Advanced Protection, or security-key-only accounts. In that case use another approved SMTP provider; Document Sender supports any server that accepts username/password authentication with optional STARTTLS.

## Upgrades and recovery

HACS upgrades preserve Home Assistant's `.storage` data and the copied files in `<config>/document_sender/<entry-id>`. Before a major upgrade, take a Home Assistant backup. To remove the integration cleanly, remove its config entry first; remove its attachment directory and `<entry-id>_document_sender.sqlite` from `.storage` only if you intentionally want to discard attachment and delivery-history data.
