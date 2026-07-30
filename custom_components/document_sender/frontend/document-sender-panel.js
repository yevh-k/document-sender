import { LitElement, css, html, nothing } from "./lit-core.min.js";

const COPY = {
  en: {
    title: "Document Sender",
    compose: "Compose",
    templates: "Templates",
    automations: "Automations",
    attachments: "Attachments",
    history: "History",
    account: "SMTP account",
    send: "Send",
    test: "Send test",
    clear: "Clear",
    saveDefaults: "Save compose defaults",
    html: "Enable HTML",
    subject: "Subject",
    to: "To",
    cc: "CC",
    bcc: "BCC",
    text: "Plain text",
    htmlBody: "HTML",
    sender: "Sender",
    selectedAttachments: "Selected attachments",
    templateName: "Template name",
    saveTemplate: "Save template",
    newTemplate: "New template",
    edit: "Edit",
    delete: "Delete",
    noTemplates: "No templates saved.",
    variables: "Available monthly variables",
    attachmentNote:
      "Selected files stay attached to this template until you change them manually.",
    automationName: "Automation name",
    template: "Template",
    day: "Day of month",
    time: "Send time",
    enabled: "Enabled",
    saveAutomation: "Save automation",
    newAutomation: "New automation",
    runNow: "Run now",
    lastRun: "Last run",
    nextRun: "Next run",
    status: "Status",
    never: "Never",
    noAutomations: "No monthly automations.",
    camera: "Camera snapshot",
    chooseCamera: "Choose a camera",
    resend: "Resend last",
    noAccounts: "No loaded Document Sender accounts.",
    noAttachments: "No managed attachments.",
    noHistory: "No messages have been sent yet.",
    sent: "Message sent.",
    saved: "Saved.",
    uploaded: "Attachment uploaded.",
    deleted: "Deleted.",
    snapshotSaved: "Camera snapshot imported.",
    recipientsRequired: "Enter at least one To, CC, or BCC recipient.",
    templateRequired: "Create a template first.",
    confirmDelete: "Delete this item?",
    loading: "Loading…",
  },
  pl: {
    title: "Document Sender",
    compose: "Wiadomość",
    templates: "Szablony",
    automations: "Automatyzacje",
    attachments: "Załączniki",
    history: "Historia",
    account: "Konto SMTP",
    send: "Wyślij",
    test: "Wyślij test",
    clear: "Wyczyść",
    saveDefaults: "Zapisz domyślne wiadomości",
    html: "Włącz HTML",
    subject: "Temat",
    to: "Do",
    cc: "DW",
    bcc: "UDW",
    text: "Zwykły tekst",
    htmlBody: "HTML",
    sender: "Nadawca",
    selectedAttachments: "Wybrane załączniki",
    templateName: "Nazwa szablonu",
    saveTemplate: "Zapisz szablon",
    newTemplate: "Nowy szablon",
    edit: "Edytuj",
    delete: "Usuń",
    noTemplates: "Brak zapisanych szablonów.",
    variables: "Dostępne zmienne miesięczne",
    attachmentNote:
      "Wybrane pliki pozostają w szablonie, dopóki nie zmienisz ich ręcznie.",
    automationName: "Nazwa automatyzacji",
    template: "Szablon",
    day: "Dzień miesiąca",
    time: "Godzina wysyłki",
    enabled: "Włączona",
    saveAutomation: "Zapisz automatyzację",
    newAutomation: "Nowa automatyzacja",
    runNow: "Uruchom teraz",
    lastRun: "Ostatnie uruchomienie",
    nextRun: "Następne uruchomienie",
    status: "Status",
    never: "Nigdy",
    noAutomations: "Brak automatyzacji miesięcznych.",
    camera: "Zdjęcie z kamery",
    chooseCamera: "Wybierz kamerę",
    resend: "Wyślij ostatnią ponownie",
    noAccounts: "Brak wczytanych kont Document Sender.",
    noAttachments: "Brak zarządzanych załączników.",
    noHistory: "Nie wysłano jeszcze żadnych wiadomości.",
    sent: "Wiadomość została wysłana.",
    saved: "Zapisano.",
    uploaded: "Załącznik został przesłany.",
    deleted: "Usunięto.",
    snapshotSaved: "Zaimportowano zdjęcie z kamery.",
    recipientsRequired: "Wpisz co najmniej jednego odbiorcę Do, DW lub UDW.",
    templateRequired: "Najpierw utwórz szablon.",
    confirmDelete: "Usunąć ten element?",
    loading: "Ładowanie…",
  },
  uk: {
    title: "Document Sender",
    compose: "Повідомлення",
    templates: "Шаблони",
    automations: "Автоматизації",
    attachments: "Вкладення",
    history: "Історія",
    account: "Обліковий запис SMTP",
    send: "Надіслати",
    test: "Надіслати тест",
    clear: "Очистити",
    saveDefaults: "Зберегти типове повідомлення",
    html: "Увімкнути HTML",
    subject: "Тема",
    to: "Кому",
    cc: "Копія",
    bcc: "Прихована копія",
    text: "Звичайний текст",
    htmlBody: "HTML",
    sender: "Відправник",
    selectedAttachments: "Вибрані вкладення",
    templateName: "Назва шаблону",
    saveTemplate: "Зберегти шаблон",
    newTemplate: "Новий шаблон",
    edit: "Змінити",
    delete: "Видалити",
    noTemplates: "Збережених шаблонів немає.",
    variables: "Доступні місячні змінні",
    attachmentNote:
      "Вибрані файли залишаються в шаблоні, доки ви не зміните їх вручну.",
    automationName: "Назва автоматизації",
    template: "Шаблон",
    day: "День місяця",
    time: "Час надсилання",
    enabled: "Увімкнено",
    saveAutomation: "Зберегти автоматизацію",
    newAutomation: "Нова автоматизація",
    runNow: "Запустити зараз",
    lastRun: "Останній запуск",
    nextRun: "Наступний запуск",
    status: "Статус",
    never: "Ніколи",
    noAutomations: "Місячних автоматизацій немає.",
    camera: "Знімок камери",
    chooseCamera: "Виберіть камеру",
    resend: "Повторити останнє",
    noAccounts: "Немає завантажених облікових записів Document Sender.",
    noAttachments: "Немає керованих вкладень.",
    noHistory: "Повідомлення ще не надсилалися.",
    sent: "Повідомлення надіслано.",
    saved: "Збережено.",
    uploaded: "Вкладення завантажено.",
    deleted: "Видалено.",
    snapshotSaved: "Знімок камери імпортовано.",
    recipientsRequired:
      "Вкажіть хоча б одного одержувача в Кому, Копія або Прихована копія.",
    templateRequired: "Спочатку створіть шаблон.",
    confirmDelete: "Видалити цей елемент?",
    loading: "Завантаження…",
  },
};

const emptyMessage = () => ({
  recipients: [],
  cc: [],
  bcc: [],
  subject: "",
  text: "",
  html: "",
});

const emptyTemplate = () => ({
  id: "",
  name: "",
  ...emptyMessage(),
  attachment_ids: [],
});

const emptyAutomation = () => ({
  id: "",
  name: "",
  template_id: "",
  day: 1,
  time: "09:00",
  enabled: true,
});

class DocumentSenderPanel extends LitElement {
  static properties = {
    hass: { attribute: false },
    entries: { state: true },
    entryId: { state: true },
    activeSection: { state: true },
    draft: { state: true },
    attachments: { state: true },
    history: { state: true },
    cameras: { state: true },
    templates: { state: true },
    automations: { state: true },
    selected: { state: true },
    templateDraft: { state: true },
    automationDraft: { state: true },
    notice: { state: true },
    htmlEnabled: { state: true },
    templateHtmlEnabled: { state: true },
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
    h1,
    h2,
    h3 {
      margin-top: 0;
    }
    h2 {
      font-size: 1.25rem;
    }
    h3 {
      margin-bottom: 4px;
      font-size: 1rem;
    }
    ha-card {
      display: block;
      padding: 20px;
    }
    .toolbar,
    .tabs,
    .row,
    .actions {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }
    .toolbar {
      justify-content: space-between;
      margin-bottom: 16px;
    }
    .toolbar label {
      min-width: min(100%, 340px);
    }
    .tabs {
      margin-bottom: 16px;
      border-bottom: 1px solid var(--divider-color);
    }
    .tabs button {
      border-radius: 4px 4px 0 0;
      background: transparent;
      color: var(--primary-text-color);
    }
    .tabs button.active {
      border-bottom: 3px solid var(--primary-color);
      color: var(--primary-color);
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
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
    button.secondary,
    button.tab {
      background: var(--secondary-background-color);
      color: var(--primary-text-color);
    }
    button.danger {
      background: var(--error-color);
    }
    button:disabled {
      cursor: default;
      opacity: 0.5;
    }
    .notice {
      min-height: 24px;
      margin-bottom: 8px;
      color: var(--primary-color);
    }
    .muted {
      color: var(--secondary-text-color);
    }
    .variables {
      padding: 10px;
      border-radius: 4px;
      background: var(--secondary-background-color);
      line-height: 1.8;
      overflow-wrap: anywhere;
    }
    ul {
      padding: 0;
      list-style: none;
    }
    li {
      display: flex;
      gap: 12px;
      align-items: center;
      justify-content: space-between;
      padding: 10px 0;
      border-bottom: 1px solid var(--divider-color);
    }
    li label,
    li span {
      overflow-wrap: anywhere;
    }
    .item-main {
      flex: 1;
    }
    .status-success {
      color: var(--success-color);
    }
    .status-failed {
      color: var(--error-color);
    }
    @media (max-width: 600px) {
      :host {
        padding: 12px;
      }
      li {
        align-items: flex-start;
        flex-direction: column;
      }
    }
  `;

  constructor() {
    super();
    this.entries = [];
    this.entryId = "";
    this.activeSection = "compose";
    this.draft = emptyMessage();
    this.attachments = [];
    this.history = [];
    this.cameras = [];
    this.templates = [];
    this.automations = [];
    this.selected = [];
    this.templateDraft = emptyTemplate();
    this.automationDraft = emptyAutomation();
    this.notice = "";
    this.htmlEnabled = false;
    this.templateHtmlEnabled = false;
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
      this.notice =
        error?.message || error?.body?.message || String(error);
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
    const [draft, attachments, history, cameras, templates, automations] =
      await Promise.all([
        this.ws("document_sender/template/get", { entry_id: this.entryId }),
        this.ws("document_sender/attachments/list", {
          entry_id: this.entryId,
        }),
        this.ws("document_sender/history/list", { entry_id: this.entryId }),
        this.ws("document_sender/camera/list"),
        this.ws("document_sender/templates/list", { entry_id: this.entryId }),
        this.ws("document_sender/automations/list", {
          entry_id: this.entryId,
        }),
      ]);
    this.draft = { ...emptyMessage(), ...(draft || {}) };
    this.htmlEnabled = Boolean(this.draft.html);
    this.attachments = attachments || [];
    this.history = history || [];
    this.cameras = cameras || [];
    this.templates = templates || [];
    this.automations = automations || [];
    const validIds = new Set(this.attachments.map((item) => item.id));
    this.selected = this.selected.filter((id) => validIds.has(id));
    this.templateDraft = {
      ...this.templateDraft,
      attachment_ids: this.templateDraft.attachment_ids.filter((id) =>
        validIds.has(id),
      ),
    };
  }

  parseRecipients(value) {
    return value
      .split(/[;,\n]/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  setDraft(key, value) {
    this.draft = { ...this.draft, [key]: value };
  }

  setTemplate(key, value) {
    this.templateDraft = { ...this.templateDraft, [key]: value };
  }

  setAutomation(key, value) {
    this.automationDraft = { ...this.automationDraft, [key]: value };
  }

  hasRecipients(message) {
    return Boolean(
      message.recipients.length || message.cc.length || message.bcc.length,
    );
  }

  composeMessage() {
    return {
      ...this.draft,
      html: this.htmlEnabled ? this.draft.html : "",
      attachments: this.selected,
    };
  }

  async send(test = false) {
    if (!this.hasRecipients(this.draft)) {
      this.notice = this.t.recipientsRequired;
      return;
    }
    await this.run(async () => {
      const message = test
        ? {
            ...this.composeMessage(),
            subject: "Document Sender test",
            text: "Document Sender panel test",
            html: "",
          }
        : this.composeMessage();
      await this.ws("document_sender/send", {
        entry_id: this.entryId,
        message,
      });
      this.notice = this.t.sent;
      await this.loadEntry();
    });
  }

  async saveDefaults() {
    await this.run(async () => {
      await this.ws("document_sender/template/save", {
        entry_id: this.entryId,
        template: this.composeMessage(),
      });
      this.notice = this.t.saved;
    });
  }

  clearCompose() {
    this.draft = emptyMessage();
    this.selected = [];
    this.htmlEnabled = false;
    this.notice = "";
  }

  async saveTemplate() {
    if (!this.hasRecipients(this.templateDraft)) {
      this.notice = this.t.recipientsRequired;
      return;
    }
    await this.run(async () => {
      await this.ws("document_sender/templates/save", {
        entry_id: this.entryId,
        template: {
          ...this.templateDraft,
          html: this.templateHtmlEnabled ? this.templateDraft.html : "",
        },
      });
      this.templateDraft = emptyTemplate();
      this.templateHtmlEnabled = false;
      await this.loadEntry();
      this.notice = this.t.saved;
    });
  }

  editTemplate(template) {
    this.templateDraft = {
      ...emptyTemplate(),
      ...template,
      recipients: [...template.recipients],
      cc: [...template.cc],
      bcc: [...template.bcc],
      attachment_ids: [...template.attachment_ids],
    };
    this.templateHtmlEnabled = Boolean(template.html);
  }

  async deleteTemplate(templateId) {
    if (!window.confirm(this.t.confirmDelete)) {
      return;
    }
    await this.run(async () => {
      await this.ws("document_sender/templates/delete", {
        entry_id: this.entryId,
        template_id: templateId,
      });
      await this.loadEntry();
      this.notice = this.t.deleted;
    });
  }

  async saveAutomation(automation = this.automationDraft) {
    if (!automation.template_id) {
      this.notice = this.t.templateRequired;
      return;
    }
    await this.run(async () => {
      await this.ws("document_sender/automations/save", {
        entry_id: this.entryId,
        automation,
      });
      this.automationDraft = emptyAutomation();
      await this.loadEntry();
      this.notice = this.t.saved;
    });
  }

  editAutomation(automation) {
    this.automationDraft = {
      id: automation.id,
      name: automation.name,
      template_id: automation.template_id,
      day: automation.day,
      time: automation.time.slice(0, 5),
      enabled: automation.enabled,
    };
  }

  async deleteAutomation(automationId) {
    if (!window.confirm(this.t.confirmDelete)) {
      return;
    }
    await this.run(async () => {
      await this.ws("document_sender/automations/delete", {
        entry_id: this.entryId,
        automation_id: automationId,
      });
      await this.loadEntry();
      this.notice = this.t.deleted;
    });
  }

  async runAutomation(automationId) {
    await this.run(async () => {
      const result = await this.ws("document_sender/automations/run", {
        entry_id: this.entryId,
        automation_id: automationId,
      });
      await this.loadEntry();
      this.notice =
        result.last_status === "success"
          ? this.t.sent
          : result.last_error || result.last_status;
    });
  }

  async upload(event) {
    const files = [...(event.target.files || [])];
    if (!files.length) {
      return;
    }
    await this.run(async () => {
      for (const file of files) {
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
      }
      event.target.value = "";
      await this.loadEntry();
      this.notice = this.t.uploaded;
    });
  }

  async removeAttachment(attachmentId) {
    if (!window.confirm(this.t.confirmDelete)) {
      return;
    }
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

  toggleId(list, identifier, checked) {
    return checked
      ? [...new Set([...list, identifier])]
      : list.filter((item) => item !== identifier);
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

  recipientField(message, key, label, setter) {
    return html`
      <label class="field">
        <span>${label}</span>
        <input
          type="text"
          .value=${(message[key] || []).join(", ")}
          @input=${(event) =>
            setter(key, this.parseRecipients(event.target.value))}
        />
      </label>
    `;
  }

  textField(message, key, label, setter, type = "text") {
    return html`
      <label class="field">
        <span>${label}</span>
        <input
          type=${type}
          .value=${String(message[key] ?? "")}
          @input=${(event) => setter(key, event.target.value)}
        />
      </label>
    `;
  }

  textArea(message, key, label, setter) {
    return html`
      <label class="field">
        <span>${label}</span>
        <textarea
          .value=${message[key] || ""}
          @input=${(event) => setter(key, event.target.value)}
        ></textarea>
      </label>
    `;
  }

  attachmentPicker(selected, changed) {
    const t = this.t;
    return html`
      <h3>${t.selectedAttachments}</h3>
      ${this.attachments.length
        ? html`
            <ul>
              ${this.attachments.map(
                (attachment) => html`
                  <li>
                    <label class="item-main">
                      <input
                        type="checkbox"
                        .checked=${selected.includes(attachment.id)}
                        @change=${(event) =>
                          changed(
                            this.toggleId(
                              selected,
                              attachment.id,
                              event.target.checked,
                            ),
                          )}
                      />
                      ${attachment.name} (${attachment.size} B)
                    </label>
                  </li>
                `,
              )}
            </ul>
          `
        : html`<p class="muted">${t.noAttachments}</p>`}
    `;
  }

  renderCompose() {
    const t = this.t;
    const sender = this.entries.find((entry) => entry.entry_id === this.entryId);
    const setter = (key, value) => this.setDraft(key, value);
    return html`
      <div class="grid">
        <ha-card>
          ${this.recipientField(this.draft, "recipients", t.to, setter)}
          ${this.recipientField(this.draft, "cc", t.cc, setter)}
          ${this.recipientField(this.draft, "bcc", t.bcc, setter)}
          ${this.textField(this.draft, "subject", t.subject, setter)}
          ${this.textArea(this.draft, "text", t.text, setter)}
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
          ${this.htmlEnabled
            ? this.textArea(this.draft, "html", t.htmlBody, setter)
            : nothing}
          <p class="muted">
            ${t.sender}: ${sender?.sender_name || ""}
            &lt;${sender?.sender_email || ""}&gt;
          </p>
          <div class="actions">
            <button ?disabled=${this.busy} @click=${() => this.send(false)}>
              ${t.send}
            </button>
            <button ?disabled=${this.busy} @click=${() => this.send(true)}>
              ${t.test}
            </button>
            <button
              class="secondary"
              ?disabled=${this.busy}
              @click=${() => this.saveDefaults()}
            >
              ${t.saveDefaults}
            </button>
            <button
              class="secondary"
              ?disabled=${this.busy}
              @click=${() => this.clearCompose()}
            >
              ${t.clear}
            </button>
          </div>
        </ha-card>
        <ha-card>
          ${this.attachmentPicker(this.selected, (selected) => {
            this.selected = selected;
          })}
        </ha-card>
      </div>
    `;
  }

  renderTemplates() {
    const t = this.t;
    const setter = (key, value) => this.setTemplate(key, value);
    const variables = [
      "month_name",
      "month_name_genitive",
      "previous_month_name",
      "previous_month_name_genitive",
      "year",
      "previous_month_year",
      "date",
    ];
    return html`
      <div class="grid">
        <ha-card>
          <h2>
            ${this.templateDraft.id ? t.edit : t.newTemplate}
          </h2>
          ${this.textField(
            this.templateDraft,
            "name",
            t.templateName,
            setter,
          )}
          ${this.recipientField(
            this.templateDraft,
            "recipients",
            t.to,
            setter,
          )}
          ${this.recipientField(this.templateDraft, "cc", t.cc, setter)}
          ${this.recipientField(this.templateDraft, "bcc", t.bcc, setter)}
          ${this.textField(
            this.templateDraft,
            "subject",
            t.subject,
            setter,
          )}
          ${this.textArea(this.templateDraft, "text", t.text, setter)}
          <label class="field row">
            <input
              type="checkbox"
              .checked=${this.templateHtmlEnabled}
              @change=${(event) => {
                this.templateHtmlEnabled = event.target.checked;
              }}
            />
            <span>${t.html}</span>
          </label>
          ${this.templateHtmlEnabled
            ? this.textArea(this.templateDraft, "html", t.htmlBody, setter)
            : nothing}
          <p class="muted">${t.attachmentNote}</p>
          ${this.attachmentPicker(
            this.templateDraft.attachment_ids,
            (attachment_ids) => this.setTemplate("attachment_ids", attachment_ids),
          )}
          <div class="actions">
            <button
              ?disabled=${this.busy}
              @click=${() => this.saveTemplate()}
            >
              ${t.saveTemplate}
            </button>
            <button
              class="secondary"
              ?disabled=${this.busy}
              @click=${() => {
                this.templateDraft = emptyTemplate();
                this.templateHtmlEnabled = false;
              }}
            >
              ${t.clear}
            </button>
          </div>
          <p class="variables">
            <strong>${t.variables}:</strong><br />
            ${variables.map((name) => html`<code>{{ ${name} }}</code> `)}
          </p>
        </ha-card>
        <ha-card>
          <h2>${t.templates}</h2>
          ${this.templates.length
            ? html`
                <ul>
                  ${this.templates.map(
                    (template) => html`
                      <li>
                        <span class="item-main">
                          <strong>${template.name}</strong><br />
                          ${template.subject}<br />
                          <span class="muted"
                            >${template.attachment_ids.length}
                            ${t.attachments.toLowerCase()}</span
                          >
                        </span>
                        <span>
                          <button
                            class="secondary"
                            @click=${() => this.editTemplate(template)}
                          >
                            ${t.edit}
                          </button>
                          <button
                            class="danger"
                            @click=${() => this.deleteTemplate(template.id)}
                          >
                            ${t.delete}
                          </button>
                        </span>
                      </li>
                    `,
                  )}
                </ul>
              `
            : html`<p class="muted">${t.noTemplates}</p>`}
        </ha-card>
      </div>
    `;
  }

  renderAutomations() {
    const t = this.t;
    return html`
      <div class="grid">
        <ha-card>
          <h2>
            ${this.automationDraft.id ? t.edit : t.newAutomation}
          </h2>
          ${this.textField(
            this.automationDraft,
            "name",
            t.automationName,
            (key, value) => this.setAutomation(key, value),
          )}
          <label class="field">
            <span>${t.template}</span>
            <select
              .value=${this.automationDraft.template_id}
              @change=${(event) =>
                this.setAutomation("template_id", event.target.value)}
            >
              <option value="">${t.template}</option>
              ${this.templates.map(
                (template) =>
                  html`<option value=${template.id}>${template.name}</option>`,
              )}
            </select>
          </label>
          <label class="field">
            <span>${t.day}</span>
            <input
              type="number"
              min="1"
              max="31"
              .value=${String(this.automationDraft.day)}
              @input=${(event) =>
                this.setAutomation("day", Number(event.target.value))}
            />
          </label>
          ${this.textField(
            this.automationDraft,
            "time",
            t.time,
            (key, value) => this.setAutomation(key, value),
            "time",
          )}
          <label class="field row">
            <input
              type="checkbox"
              .checked=${this.automationDraft.enabled}
              @change=${(event) =>
                this.setAutomation("enabled", event.target.checked)}
            />
            <span>${t.enabled}</span>
          </label>
          <div class="actions">
            <button
              ?disabled=${this.busy || !this.templates.length}
              @click=${() => this.saveAutomation()}
            >
              ${t.saveAutomation}
            </button>
            <button
              class="secondary"
              @click=${() => {
                this.automationDraft = emptyAutomation();
              }}
            >
              ${t.clear}
            </button>
          </div>
        </ha-card>
        <ha-card>
          <h2>${t.automations}</h2>
          ${this.automations.length
            ? html`
                <ul>
                  ${this.automations.map(
                    (automation) => html`
                      <li>
                        <span class="item-main">
                          <strong>${automation.name}</strong><br />
                          ${t.day}: ${automation.day}, ${t.time}<br />
                          ${t.lastRun}:
                          ${this.formatDateTime(automation.last_run)}<br />
                          ${t.nextRun}:
                          ${this.formatDateTime(automation.next_run)}<br />
                          ${t.status}:
                          <span
                            class=${`status-${automation.last_status || ""}`}
                          >
                            ${automation.last_status || t.never}
                          </span>
                          ${automation.last_error || ""}
                        </span>
                        <span>
                          <label>
                            <input
                              type="checkbox"
                              .checked=${automation.enabled}
                              @change=${(event) =>
                                this.saveAutomation({
                                  id: automation.id,
                                  name: automation.name,
                                  template_id: automation.template_id,
                                  day: automation.day,
                                  time: automation.time,
                                  enabled: event.target.checked,
                                })}
                            />
                            ${t.enabled}
                          </label>
                          <button
                            @click=${() => this.runAutomation(automation.id)}
                          >
                            ${t.runNow}
                          </button>
                          <button
                            class="secondary"
                            @click=${() => this.editAutomation(automation)}
                          >
                            ${t.edit}
                          </button>
                          <button
                            class="danger"
                            @click=${() =>
                              this.deleteAutomation(automation.id)}
                          >
                            ${t.delete}
                          </button>
                        </span>
                      </li>
                    `,
                  )}
                </ul>
              `
            : html`<p class="muted">${t.noAutomations}</p>`}
        </ha-card>
      </div>
    `;
  }

  renderAttachments() {
    const t = this.t;
    return html`
      <ha-card>
        <h2>${t.attachments}</h2>
        <input
          type="file"
          multiple
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
                      <span class="item-main">
                        <strong>${attachment.name}</strong><br />
                        ID: ${attachment.id}<br />
                        ${attachment.content_type} · ${attachment.size} B ·
                        ${this.formatDateTime(attachment.created_at)}
                      </span>
                      <button
                        class="danger"
                        ?disabled=${this.busy}
                        @click=${() => this.removeAttachment(attachment.id)}
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
                      <span class="item-main">
                        ${this.formatDateTime(item.created_at)}<br />
                        <strong>${item.subject}</strong><br />
                        <span
                          class=${item.success
                            ? "status-success"
                            : "status-failed"}
                        >
                          ${item.success ? "✓" : "✕"}
                        </span>
                        · ${item.attachment_count} ${t.attachments.toLowerCase()}
                        · ${item.recipients.join(", ")} ${item.error || ""}
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

  formatDateTime(value) {
    if (!value) {
      return this.t.never;
    }
    const date = new Date(value);
    return Number.isNaN(date.getTime())
      ? value
      : date.toLocaleString(this.hass?.language || "en");
  }

  renderSection() {
    if (this.activeSection === "templates") {
      return this.renderTemplates();
    }
    if (this.activeSection === "automations") {
      return this.renderAutomations();
    }
    if (this.activeSection === "attachments") {
      return this.renderAttachments();
    }
    if (this.activeSection === "history") {
      return this.renderHistory();
    }
    return this.renderCompose();
  }

  render() {
    const t = this.t;
    const sections = [
      ["compose", t.compose],
      ["templates", t.templates],
      ["automations", t.automations],
      ["attachments", t.attachments],
      ["history", t.history],
    ];
    return html`
      <div class="toolbar">
        <h1>${t.title}</h1>
        ${this.entries.length
          ? html`
              <label>
                <span class="muted">${t.account}</span>
                <select
                  ?disabled=${this.busy || this.entries.length < 2}
                  @change=${(event) => {
                    this.entryId = event.target.value;
                    this.selected = [];
                    this.templateDraft = emptyTemplate();
                    this.automationDraft = emptyAutomation();
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
            `
          : nothing}
      </div>
      <div class="notice">${this.busy ? t.loading : this.notice}</div>
      ${this.entries.length
        ? html`
            <nav class="tabs">
              ${sections.map(
                ([id, label]) => html`
                  <button
                    class=${this.activeSection === id ? "active" : "tab"}
                    @click=${() => {
                      this.activeSection = id;
                      this.notice = "";
                    }}
                  >
                    ${label}
                  </button>
                `,
              )}
            </nav>
            ${this.renderSection()}
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
