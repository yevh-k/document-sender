import { LitElement, css, html, nothing } from "./lit-core.min.js";

const COPY = {
  en: {
    title: "Document Sender",
    account: "SMTP account",
    send: "Send",
    test: "Send test",
    clear: "Clear",
    save: "Save defaults",
    attachments: "Attachments",
    history: "Send history",
    camera: "Camera snapshot",
    html: "Enable HTML",
    subject: "Subject",
    to: "To",
    cc: "CC",
    bcc: "BCC",
    text: "Plain text",
    htmlBody: "HTML",
    resend: "Resend",
    delete: "Delete",
    sender: "Sender",
    noAccounts: "No loaded Document Sender accounts.",
    noAttachments: "No managed attachments.",
    noHistory: "No messages have been sent yet.",
    chooseCamera: "Choose a camera",
    sent: "Message sent.",
    saved: "Defaults saved.",
    uploaded: "Attachment uploaded.",
    deleted: "Attachment deleted.",
    snapshotSaved: "Camera snapshot imported.",
    recipientsRequired: "Enter at least one To, CC, or BCC recipient.",
    loading: "Loading…",
  },
  pl: {
    title: "Document Sender",
    account: "Konto SMTP",
    send: "Wyślij",
    test: "Wyślij test",
    clear: "Wyczyść",
    save: "Zapisz domyślne",
    attachments: "Załączniki",
    history: "Historia wysyłki",
    camera: "Zdjęcie z kamery",
    html: "Włącz HTML",
    subject: "Temat",
    to: "Do",
    cc: "DW",
    bcc: "UDW",
    text: "Zwykły tekst",
    htmlBody: "HTML",
    resend: "Wyślij ponownie",
    delete: "Usuń",
    sender: "Nadawca",
    noAccounts: "Brak wczytanych kont Document Sender.",
    noAttachments: "Brak zarządzanych załączników.",
    noHistory: "Nie wysłano jeszcze żadnych wiadomości.",
    chooseCamera: "Wybierz kamerę",
    sent: "Wiadomość została wysłana.",
    saved: "Zapisano wartości domyślne.",
    uploaded: "Załącznik został przesłany.",
    deleted: "Załącznik został usunięty.",
    snapshotSaved: "Zaimportowano zdjęcie z kamery.",
    recipientsRequired: "Wpisz co najmniej jednego odbiorcę Do, DW lub UDW.",
    loading: "Ładowanie…",
  },
  uk: {
    title: "Document Sender",
    account: "Обліковий запис SMTP",
    send: "Надіслати",
    test: "Надіслати тест",
    clear: "Очистити",
    save: "Зберегти типові",
    attachments: "Вкладення",
    history: "Історія надсилань",
    camera: "Знімок камери",
    html: "Увімкнути HTML",
    subject: "Тема",
    to: "Кому",
    cc: "Копія",
    bcc: "Прихована копія",
    text: "Звичайний текст",
    htmlBody: "HTML",
    resend: "Повторити",
    delete: "Видалити",
    sender: "Відправник",
    noAccounts: "Немає завантажених облікових записів Document Sender.",
    noAttachments: "Немає керованих вкладень.",
    noHistory: "Повідомлення ще не надсилалися.",
    chooseCamera: "Виберіть камеру",
    sent: "Повідомлення надіслано.",
    saved: "Типові значення збережено.",
    uploaded: "Вкладення завантажено.",
    deleted: "Вкладення видалено.",
    snapshotSaved: "Знімок камери імпортовано.",
    recipientsRequired:
      "Вкажіть хоча б одного одержувача в Кому, Копія або Прихована копія.",
    loading: "Завантаження…",
  },
};

const emptyDraft = () => ({
  recipients: [],
  cc: [],
  bcc: [],
  subject: "",
  text: "",
  html: "",
});

class DocumentSenderPanel extends LitElement {
  static properties = {
    hass: { attribute: false },
    entries: { state: true },
    entryId: { state: true },
    draft: { state: true },
    attachments: { state: true },
    history: { state: true },
    cameras: { state: true },
    selected: { state: true },
    notice: { state: true },
    htmlEnabled: { state: true },
    busy: { state: true },
  };

  static styles = css`
    :host {
      display: block;
      max-width: 1200px;
      margin: auto;
      padding: 24px;
      color: var(--primary-text-color);
    }
    h1 {
      margin-top: 0;
    }
    h2 {
      margin-top: 0;
      font-size: 1.25rem;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
    }
    ha-card {
      display: block;
      padding: 20px;
    }
    .field {
      display: block;
      margin: 12px 0;
    }
    .field > span {
      display: block;
      margin-bottom: 5px;
      color: var(--secondary-text-color);
      font-size: 0.9rem;
    }
    input,
    textarea,
    select {
      width: 100%;
      box-sizing: border-box;
      padding: 10px;
      border: 1px solid var(--divider-color);
      border-radius: 4px;
      background: var(--card-background-color);
      color: var(--primary-text-color);
      font: inherit;
    }
    input[type="checkbox"] {
      width: auto;
    }
    textarea {
      min-height: 120px;
      resize: vertical;
    }
    button {
      margin: 4px 4px 4px 0;
      padding: 9px 14px;
      border: 0;
      border-radius: 4px;
      background: var(--primary-color);
      color: var(--text-primary-color);
      cursor: pointer;
    }
    button.secondary {
      background: var(--secondary-background-color);
      color: var(--primary-text-color);
    }
    button:disabled {
      cursor: default;
      opacity: 0.5;
    }
    .row {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }
    .row select {
      flex: 1;
      min-width: 200px;
    }
    .notice {
      min-height: 24px;
      margin-bottom: 8px;
      color: var(--primary-color);
    }
    .muted {
      color: var(--secondary-text-color);
    }
    ul {
      padding: 0;
      list-style: none;
    }
    li {
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid var(--divider-color);
    }
    li label,
    li span {
      overflow-wrap: anywhere;
    }
  `;

  constructor() {
    super();
    this.entries = [];
    this.entryId = "";
    this.draft = emptyDraft();
    this.attachments = [];
    this.history = [];
    this.cameras = [];
    this.selected = [];
    this.notice = "";
    this.htmlEnabled = false;
    this.busy = false;
    this._initialized = false;
  }

  get t() {
    return COPY[(this.hass?.language || "en").slice(0, 2)] || COPY.en;
  }

  updated(changedProperties) {
    if (
      changedProperties.has("hass") &&
      this.hass?.connection &&
      !this._initialized
    ) {
      this._initialized = true;
      void this.loadConfig();
    }
  }

  async ws(type, data = {}) {
    if (!this.hass?.connection) {
      throw new Error("Home Assistant connection is not ready");
    }
    return this.hass.connection.sendMessagePromise({ type, ...data });
  }

  async run(action) {
    this.busy = true;
    try {
      await action();
    } catch (error) {
      this.notice = error instanceof Error ? error.message : String(error);
    } finally {
      this.busy = false;
    }
  }

  async loadConfig() {
    await this.run(async () => {
      const result = await this.ws("document_sender/config");
      this.entries = result.entries || [];
      if (!this.entries.some((entry) => entry.entry_id === this.entryId)) {
        this.entryId = this.entries[0]?.entry_id || "";
      }
      await this.loadEntry();
    });
  }

  async loadEntry() {
    if (!this.entryId) {
      return;
    }
    const [savedDraft, attachments, history, cameras] = await Promise.all([
      this.ws("document_sender/template/get", { entry_id: this.entryId }),
      this.ws("document_sender/attachments/list", { entry_id: this.entryId }),
      this.ws("document_sender/history/list", { entry_id: this.entryId }),
      this.ws("document_sender/camera/list"),
    ]);
    this.draft = { ...emptyDraft(), ...(savedDraft || {}) };
    this.htmlEnabled = Boolean(this.draft.html);
    this.attachments = attachments || [];
    this.history = history || [];
    this.cameras = cameras || [];
    const validIds = new Set(this.attachments.map((item) => item.id));
    this.selected = this.selected.filter((id) => validIds.has(id));
  }

  parseRecipients(value) {
    return value
      .split(/[;,\n]/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  updateText(key, event) {
    this.draft = { ...this.draft, [key]: event.target.value };
  }

  updateRecipients(key, event) {
    this.draft = {
      ...this.draft,
      [key]: this.parseRecipients(event.target.value),
    };
  }

  message() {
    return {
      recipients: this.draft.recipients,
      cc: this.draft.cc,
      bcc: this.draft.bcc,
      subject: this.draft.subject,
      text: this.draft.text,
      html: this.htmlEnabled ? this.draft.html : "",
      attachments: this.selected,
    };
  }

  hasRecipients() {
    return Boolean(
      this.draft.recipients.length ||
        this.draft.cc.length ||
        this.draft.bcc.length,
    );
  }

  async send(test = false) {
    if (!this.hasRecipients()) {
      this.notice = this.t.recipientsRequired;
      return;
    }
    await this.run(async () => {
      const message = test
        ? {
            ...this.message(),
            subject: "Document Sender test",
            text: "Document Sender panel test",
            html: "",
          }
        : this.message();
      await this.ws("document_sender/send", {
        entry_id: this.entryId,
        message,
      });
      this.notice = this.t.sent;
      await this.loadEntry();
    });
  }

  async save() {
    await this.run(async () => {
      await this.ws("document_sender/template/save", {
        entry_id: this.entryId,
        template: this.message(),
      });
      this.notice = this.t.saved;
    });
  }

  clear() {
    this.draft = emptyDraft();
    this.selected = [];
    this.htmlEnabled = false;
    this.notice = "";
  }

  async upload(event) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    await this.run(async () => {
      const content = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () =>
          resolve(String(reader.result).split(",", 2)[1] || "");
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
      });
      await this.ws("document_sender/attachments/upload", {
        entry_id: this.entryId,
        name: file.name,
        content_type: file.type || "application/octet-stream",
        content,
      });
      await this.loadEntry();
      this.notice = this.t.uploaded;
      event.target.value = "";
    });
  }

  async remove(attachmentId) {
    await this.run(async () => {
      await this.ws("document_sender/attachments/delete", {
        entry_id: this.entryId,
        attachment_id: attachmentId,
      });
      this.selected = this.selected.filter((id) => id !== attachmentId);
      await this.loadEntry();
      this.notice = this.t.deleted;
    });
  }

  toggleAttachment(attachmentId, checked) {
    this.selected = checked
      ? [...new Set([...this.selected, attachmentId])]
      : this.selected.filter((id) => id !== attachmentId);
  }

  async snapshot() {
    const camera = this.renderRoot.querySelector("#camera")?.value;
    if (!camera) {
      return;
    }
    await this.run(async () => {
      await this.ws("document_sender/camera/snapshot", {
        entry_id: this.entryId,
        entity_id: camera,
      });
      await this.loadEntry();
      this.notice = this.t.snapshotSaved;
    });
  }

  async resend() {
    await this.run(async () => {
      await this.ws("document_sender/resend", { entry_id: this.entryId });
      await this.loadEntry();
      this.notice = this.t.sent;
    });
  }

  renderEditor() {
    const t = this.t;
    const sender = this.entries.find((entry) => entry.entry_id === this.entryId);
    return html`
      <ha-card>
        <label class="field">
          <span>${t.account}</span>
          <select
            ?disabled=${this.busy || this.entries.length < 2}
            @change=${(event) => {
              this.entryId = event.target.value;
              void this.run(() => this.loadEntry());
            }}
          >
            ${this.entries.map(
              (entry) => html`
                <option
                  value=${entry.entry_id}
                  ?selected=${entry.entry_id === this.entryId}
                >
                  ${entry.title} — ${entry.sender_email}
                </option>
              `,
            )}
          </select>
        </label>
        ${this.recipientField("recipients", t.to)}
        ${this.recipientField("cc", t.cc)}
        ${this.recipientField("bcc", t.bcc)}
        ${this.textField("subject", t.subject)}
        ${this.textArea("text", t.text)}
        <label class="field row">
          <input
            type="checkbox"
            .checked=${this.htmlEnabled}
            @change=${(event) => {
              this.htmlEnabled = event.target.checked;
            }}
          />
          <span>${t.html}</span>
        </label>
        ${this.htmlEnabled ? this.textArea("html", t.htmlBody) : nothing}
        <p class="muted">
          ${t.sender}: ${sender?.sender_name || ""}
          &lt;${sender?.sender_email || ""}&gt;
        </p>
        <div class="row">
          <button ?disabled=${this.busy} @click=${() => this.send(false)}>
            ${t.send}
          </button>
          <button ?disabled=${this.busy} @click=${() => this.send(true)}>
            ${t.test}
          </button>
          <button ?disabled=${this.busy} @click=${() => this.save()}>
            ${t.save}
          </button>
          <button
            class="secondary"
            ?disabled=${this.busy}
            @click=${() => this.clear()}
          >
            ${t.clear}
          </button>
        </div>
      </ha-card>
    `;
  }

  recipientField(key, label) {
    return html`
      <label class="field">
        <span>${label}</span>
        <input
          type="text"
          .value=${(this.draft[key] || []).join(", ")}
          @input=${(event) => this.updateRecipients(key, event)}
        />
      </label>
    `;
  }

  textField(key, label) {
    return html`
      <label class="field">
        <span>${label}</span>
        <input
          type="text"
          .value=${this.draft[key] || ""}
          @input=${(event) => this.updateText(key, event)}
        />
      </label>
    `;
  }

  textArea(key, label) {
    return html`
      <label class="field">
        <span>${label}</span>
        <textarea
          .value=${this.draft[key] || ""}
          @input=${(event) => this.updateText(key, event)}
        ></textarea>
      </label>
    `;
  }

  renderAttachments() {
    const t = this.t;
    return html`
      <ha-card>
        <h2>${t.attachments}</h2>
        <input
          type="file"
          ?disabled=${this.busy}
          @change=${(event) => this.upload(event)}
        />
        <div class="row field">
          <select id="camera" ?disabled=${this.busy}>
            <option value="">${t.chooseCamera}</option>
            ${this.cameras.map(
              (camera) =>
                html`<option value=${camera.entity_id}>${camera.name}</option>`,
            )}
          </select>
          <button ?disabled=${this.busy} @click=${() => this.snapshot()}>
            ${t.camera}
          </button>
        </div>
        ${this.attachments.length
          ? html`
              <ul>
                ${this.attachments.map(
                  (attachment) => html`
                    <li>
                      <label>
                        <input
                          type="checkbox"
                          .checked=${this.selected.includes(attachment.id)}
                          @change=${(event) =>
                            this.toggleAttachment(
                              attachment.id,
                              event.target.checked,
                            )}
                        />
                        ${attachment.name} (${attachment.content_type},
                        ${attachment.size} B)
                      </label>
                      <button
                        class="secondary"
                        ?disabled=${this.busy}
                        @click=${() => this.remove(attachment.id)}
                      >
                        ${t.delete}
                      </button>
                    </li>
                  `,
                )}
              </ul>
            `
          : html`<p class="muted">${t.noAttachments}</p>`}
      </ha-card>
    `;
  }

  renderHistory() {
    const t = this.t;
    return html`
      <ha-card>
        <h2>${t.history}</h2>
        ${this.history.length
          ? html`
              <ul>
                ${this.history.map(
                  (item) => html`
                    <li>
                      <span>
                        ${item.created_at}<br />
                        ${item.subject}<br />
                        ${item.success ? "✓" : "✕"} ${item.attachment_count}
                        ${item.error || ""}
                      </span>
                      <button
                        class="secondary"
                        ?disabled=${this.busy}
                        @click=${() => this.resend()}
                      >
                        ${t.resend}
                      </button>
                    </li>
                  `,
                )}
              </ul>
            `
          : html`<p class="muted">${t.noHistory}</p>`}
      </ha-card>
    `;
  }

  render() {
    const t = this.t;
    return html`
      <h1>${t.title}</h1>
      <div class="notice">${this.busy ? t.loading : this.notice}</div>
      ${this.entries.length
        ? html`
            <div class="grid">
              ${this.renderEditor()} ${this.renderAttachments()}
              ${this.renderHistory()}
            </div>
          `
        : html`<ha-card><p>${t.noAccounts}</p></ha-card>`}
    `;
  }
}

const PANEL_ELEMENT = "ha-panel-document-sender-panel";
const LEGACY_PANEL_ELEMENT = "document-sender-panel";

if (!customElements.get(PANEL_ELEMENT)) {
  customElements.define(PANEL_ELEMENT, DocumentSenderPanel);
}

if (!customElements.get(LEGACY_PANEL_ELEMENT)) {
  customElements.define(
    LEGACY_PANEL_ELEMENT,
    class extends DocumentSenderPanel {},
  );
}
