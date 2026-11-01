import { renderLatexSnippet } from "./vendor/editor.mjs";
export function initJobenu({ api, branches, openBranch, ready }) {
  const $ = (s) => document.querySelector(s),
    make = (tag, value) => {
      const e = document.createElement(tag);
      e.textContent = value;
      return e;
    };
  const statusLabel = (value) =>
    ({
      selecting: "Choose applications",
      planned: "Ready to start",
      running: "In progress",
      imported: "Branches created",
      awaiting_approval: "Waiting for review",
      awaiting_requirements_approval: "Review job requirements",
      failed: "Needs attention",
      rejected: "Changes rejected",
      interrupted: "Interrupted · preview to resume",
      complete: "AI stages complete",
      preparing: "Preparing workspace",
      extract: "Extract",
      analyze: "Analyze",
      adapt: "Adapt",
      review: "Review",
      cover: "Cover",
    })[value] ||
    value ||
    "";
  const entry = make("button", "Import jobs");
  entry.id = "open-jobenu";
  entry.className = "quiet";
  $(".board-nav").append(entry);
  const section = document.createElement("section");
  section.id = "jobenu-import";
  section.hidden = true;
  section.innerHTML = `<button id="jobenu-back" class="back">← All applications</button><div class="page-heading"><div><h1>Import jobs</h1><p class="subtitle">Bring opportunities from Jobenu into this CV collection.</p></div></div>
 <div role="tablist" aria-label="Import source" class="jobenu-tabs"><button role="tab" aria-selected="true">Jobenu</button></div>
 <p class="helper">Your export stays unchanged. Each selected application gets its own CV workspace. Importing never submits an application or pushes to Git.</p>
 <p id="jobenu-error" role="alert" class="form-error"></p><p id="jobenu-feedback" role="status"></p>
 <details id="jobenu-install"><summary>Vita installation</summary><label>Compatible Vita CV source folder<input id="jobenu-source" placeholder="Folder containing vita/__main__.py"></label><button id="jobenu-check">Check installation</button><p id="jobenu-capability" role="status"></p></details>
 <label id="jobenu-drop" class="jobenu-drop">Choose or drop a Jobenu JSON export<input id="jobenu-file" type="file" accept=".json,application/json"></label><p id="jobenu-file-info" role="status"></p>
 <div id="jobenu-date-filters" hidden><div class="jobenu-date-toolbar"><label>Date<select id="jobenu-date-field"><option value="createdAt">Added</option><option value="updatedAt">Updated</option><option value="appliedAt">Applied</option><option value="deadlineAt">Deadline</option><option value="nextActionAt">Next action</option></select></label><label>From<input id="jobenu-date-from" type="date" aria-describedby="jobenu-date-help jobenu-date-error"></label><label>To<input id="jobenu-date-to" type="date" aria-describedby="jobenu-date-help jobenu-date-error"></label><div class="actions"><button id="jobenu-today">Today</button><button id="jobenu-all-dates">All dates</button></div></div><p id="jobenu-date-help" class="helper">Dates follow the calendar day in your export. Today uses your device's date.</p><p id="jobenu-date-error" role="alert" class="form-error"></p><p id="jobenu-selection-summary" role="status"></p></div>
 <div class="jobenu-scroll" tabindex="0" role="region" aria-label="Applications to import"><table id="jobenu-selection"><caption>Select applications</caption><thead><tr><th><input id="jobenu-select-all" type="checkbox" aria-label="Select all matching jobs"></th><th>Company</th><th>Position</th><th>Status</th><th id="jobenu-date-heading">Added</th></tr></thead><tbody></tbody></table></div>
 <div class="jobenu-settings"><label>Starting CV<input id="jobenu-base" type="search" list="jobenu-bases" autocomplete="off" placeholder="Search local branches"><datalist id="jobenu-bases"></datalist></label><label>Approval mode<select id="jobenu-approval"><option value="human">Review changes before applying</option><option value="auto">Apply verified changes automatically</option></select></label></div>
 <label><input id="jobenu-run" type="checkbox" checked> Run the AI workflow</label><p class="helper">Automatic mode can still pause for factual or canonical-requirement confirmation. Complete means the configured AI stages finished; PDFs and submission are separate.</p>
 <details><summary>Advanced</summary><div class="jobenu-settings"><label>Language override<input id="jobenu-language" placeholder="Use saved language"></label><label>Provider override<input id="jobenu-provider" placeholder="Use saved AI settings"></label><label>Status filters<input id="jobenu-statuses" value="SAVED" aria-describedby="jobenu-status-help"></label></div><p id="jobenu-status-help" class="helper">Comma-separated statuses, or ALL. Uses saved stage providers/models and native Vita reasoning preferences. Tree-only reasoning overrides are not forwarded by this batch CLI.</p><label><input id="jobenu-demo" type="checkbox"> Include demo applications</label><label><input id="jobenu-revision" type="checkbox"> Create a new source revision when records changed</label><label><input id="jobenu-rerun" type="checkbox"> Reassess completed stages (additional AI calls)</label></details>
 <div class="actions"><button id="jobenu-preview" disabled>Preview branches</button><button id="jobenu-start" class="primary" disabled>Create branches</button></div>
 <div class="jobenu-scroll" tabindex="0" role="region" aria-label="Application preview"><table id="jobenu-plan"><caption>Branch preview</caption><thead><tr><th>Company</th><th>Position</th><th>Branch</th><th>Action</th></tr></thead><tbody></tbody></table></div><section id="jobenu-aliases" hidden aria-labelledby="jobenu-alias-title"></section>
 <h2>Batch activity</h2><p class="helper">You can leave this view while work continues. Retained sources stay private until you forget the batch; imported workspaces are preserved.</p><div id="jobenu-history"></div>
 <dialog id="jobenu-review" aria-labelledby="jobenu-review-title"><div class="dialog-heading"><h2 id="jobenu-review-title">Review imported application</h2><button id="jobenu-review-close" aria-label="Close import review">×</button></div><div id="jobenu-review-content" class="review-scroll"></div><p id="jobenu-review-error" role="alert" class="form-error"></p><footer class="dialog-footer"><button id="jobenu-reject">Reject changes</button><button id="jobenu-approve" class="primary">Approve exact revision</button></footer></dialog>`;
  $("#main-content").append(section);
  let session = null,
    plan = null,
    available = false,
    busy = false,
    review = null,
    polling = false,
    version = 0,
    uploadVersion = 0,
    historySignature = "";
  let selectedIds = new Set(),
    aliasSaving = false;
  const aliasDrafts = new Map();
  const error = (e) => ($("#jobenu-error").textContent = e?.message || e || "");
  function invalidate() {
    version++;
    plan = null;
    $("#jobenu-start").disabled = true;
    $("#jobenu-plan tbody").replaceChildren();
    $("#jobenu-aliases").replaceChildren();
    $("#jobenu-aliases").hidden = true;
  }
  function dateRange() {
    return {
      dateField: $("#jobenu-date-field").value,
      dateFrom: $("#jobenu-date-from").value,
      dateTo: $("#jobenu-date-to").value,
    };
  }
  function matchingApplications() {
    const { dateField, dateFrom, dateTo } = dateRange();
    return (session?.applications || []).filter((a) => {
      const day = a.dates?.[dateField];
      return (
        (!dateFrom && !dateTo) ||
        (day && (!dateFrom || day >= dateFrom) && (!dateTo || day <= dateTo))
      );
    });
  }
  function updateSelection() {
    const matches = matchingApplications(),
      count = matches.filter((a) => selectedIds.has(a.id)).length;
    const { dateField, dateFrom, dateTo } = dateRange();
    const invalid = !!(dateFrom && dateTo && dateFrom > dateTo);
    $("#jobenu-date-error").textContent = invalid
      ? "The end date must be on or after the start date."
      : "";
    for (const name of ["from", "to"])
      $("#jobenu-date-" + name).setAttribute("aria-invalid", String(invalid));
    const missing = (session?.applications || []).filter(
      (a) => !a.dates?.[dateField],
    ).length;
    $("#jobenu-selection-summary").textContent =
      `${matches.length ? `${count} selected · ${matches.length} matching` : "No jobs match these dates"} · ${session?.applications?.length || 0} in export${missing ? ` · ${missing} without a date${dateFrom || dateTo ? " (excluded)" : ""}` : ""}`;
    $("#jobenu-select-all").checked = count > 0 && count === matches.length;
    $("#jobenu-select-all").indeterminate = count > 0 && count < matches.length;
    $("#jobenu-select-all").disabled = !matches.length || invalid;
    $("#jobenu-preview").disabled =
      !available || busy || aliasSaving || invalid || !count;
  }
  function renderSelection() {
    $("#jobenu-date-filters").hidden = !session;
    $("#jobenu-date-heading").textContent =
      $("#jobenu-date-field").selectedOptions[0].textContent;
    const body = $("#jobenu-selection tbody");
    body.replaceChildren();
    for (const a of matchingApplications()) {
      const row = document.createElement("tr"),
        cell = document.createElement("td"),
        input = document.createElement("input");
      input.type = "checkbox";
      input.value = a.id;
      input.checked = selectedIds.has(a.id);
      input.setAttribute("aria-label", `Select ${a.company} · ${a.position}`);
      input.onchange = () => {
        input.checked ? selectedIds.add(a.id) : selectedIds.delete(a.id);
        invalidate();
        updateSelection();
      };
      cell.append(input);
      const dateCell = make(
        "td",
        a.dates?.[$("#jobenu-date-field").value] || "—",
      );
      dateCell.dataset.label = $("#jobenu-date-heading").textContent;
      row.append(
        cell,
        ...["company", "position", "status"].map((k) => make("td", a[k])),
        dateCell,
      );
      body.append(row);
    }
    updateSelection();
  }
  for (const id of ["field", "from", "to"])
    $("#jobenu-date-" + id).addEventListener("input", () => {
      invalidate();
      renderSelection();
    });
  $("#jobenu-select-all").onchange = (event) => {
    for (const a of matchingApplications())
      event.target.checked ? selectedIds.add(a.id) : selectedIds.delete(a.id);
    invalidate();
    renderSelection();
  };
  $("#jobenu-today").onclick = () => {
    const now = new Date(),
      today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
    $("#jobenu-date-from").value = $("#jobenu-date-to").value = today;
    invalidate();
    renderSelection();
  };
  $("#jobenu-all-dates").onclick = () => {
    $("#jobenu-date-from").value = $("#jobenu-date-to").value = "";
    invalidate();
    renderSelection();
  };
  function data() {
    return {
      id: session.id,
      ids: matchingApplications()
        .filter((a) => selectedIds.has(a.id))
        .map((a) => a.id),
      ...dateRange(),
      base: $("#jobenu-base").value,
      approval: $("#jobenu-approval").value,
      run: $("#jobenu-run").checked,
      source: $("#jobenu-source").value,
      language: $("#jobenu-language").value,
      provider: $("#jobenu-provider").value,
      statuses: $("#jobenu-statuses")
        .value.split(",")
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean),
      includeDemo: $("#jobenu-demo").checked,
      newRevision: $("#jobenu-revision").checked,
      rerun: $("#jobenu-rerun").checked,
    };
  }
  async function check() {
    await ready();
    available = false;
    $("#jobenu-preview").disabled = true;
    invalidate();
    const capability = await api("/api/jobenu/capability", {
      source: $("#jobenu-source").value,
    });
    available = capability.available;
    $("#jobenu-capability").textContent =
      capability.message || "Jobenu batch import is available.";
    $("#jobenu-install").open = !available;
    if (!$("#jobenu-base").value) $("#jobenu-base").value = capability.base;
    updateSelection();
  }
  async function show() {
    section.hidden = false;
    $("#board").hidden = true;
    $("#workspace").hidden = true;
    $("#jobenu-bases").replaceChildren(
      ...branches()
        .filter((b) => b.local)
        .map((b) => {
          const o = document.createElement("option");
          o.value = b.name;
          return o;
        }),
    );
    try {
      await ready();
      await check();
      await refresh();
    } catch (e) {
      error(e);
    }
    $("#jobenu-file").focus();
  }
  entry.onclick = show;
  $("#jobenu-back").onclick = () => {
    section.hidden = true;
    $("#board").hidden = false;
  };
  $("#jobenu-check").onclick = () => check().catch(error);
  async function upload(file) {
    if (!file) return;
    const ticket = ++uploadVersion;
    session = null;
    selectedIds.clear();
    aliasDrafts.clear();
    invalidate();
    renderSelection();
    $("#jobenu-file-info").textContent = "Reading export…";
    error("");
    if (file.size > 10 * 1024 * 1024) {
      error("Choose a JSON export smaller than 10 MiB.");
      return;
    }
    try {
      await ready();
      const uploaded = await api("/api/jobenu/upload", {
        filename: file.name,
        content: await file.text(),
      });
      if (ticket !== uploadVersion) return;
      session = uploaded;
      $("#jobenu-date-field").value = "createdAt";
      $("#jobenu-date-from").value = $("#jobenu-date-to").value = "";
      selectedIds = new Set(
        session.applications
          .filter((a) => a.status === "SAVED" && !a.isDemo)
          .map((a) => a.id),
      );
      $("#jobenu-file-info").textContent =
        `${session.filename} · ${session.applications.length} applications`;
      renderSelection();
    } catch (e) {
      error(e);
    }
  }
  $("#jobenu-file").onchange = (e) => upload(e.target.files[0]);
  $("#jobenu-drop").ondragover = (e) => e.preventDefault();
  $("#jobenu-drop").ondrop = (e) => {
    e.preventDefault();
    upload(e.dataTransfer.files[0]);
  };
  for (const id of [
    "base",
    "approval",
    "run",
    "source",
    "language",
    "provider",
    "statuses",
    "demo",
    "revision",
    "rerun",
  ])
    $("#jobenu-" + id).addEventListener("input", invalidate);
  async function preview() {
    if (busy || aliasSaving || !session || !available || !data().ids.length)
      return;
    busy = true;
    invalidate();
    const capturedVersion = version;
    error("");
    $("#jobenu-preview").disabled = true;
    try {
      const result = await api("/api/jobenu/preview", data());
      if (version !== capturedVersion) return;
      plan = result.plan;
      if (plan.error) error(plan.error);
      const body = $("#jobenu-plan tbody");
      body.replaceChildren();
      for (const e of plan.entries) {
        const row = document.createElement("tr");
        row.append(
          ...["company", "position", "branch", "action"].map((k) => {
            const cell = make("td", e[k]);
            cell.dataset.label = k === "branch" ? "Application" : k;
            return cell;
          }),
        );
        body.append(row);
      }
      renderAliases(plan.entries);
      const created = plan.entries.filter((e) => e.action === "create").length;
      $("#jobenu-start").textContent = created
        ? `Create ${created} branches${$("#jobenu-run").checked ? " and run" : ""}`
        : `Continue ${plan.entries.length} application${plan.entries.length === 1 ? "" : "s"}`;
      $("#jobenu-start").disabled =
        plan.entries.some((e) => !["create", "existing"].includes(e.action)) ||
        result.status !== "planned" ||
        !plan.entries.length;
    } catch (e) {
      error(e);
    } finally {
      busy = false;
      updateSelection();
    }
  }
  function renderAliases(entries) {
    const titles = [
      ...new Set(
        entries
          .filter((e) => e.role_resolution === "slug_fallback")
          .map((e) => e.position),
      ),
    ];
    const host = $("#jobenu-aliases");
    host.replaceChildren();
    host.hidden = !titles.length;
    if (!titles.length) return;
    const heading = make("h2", "Short role names"),
      help = make(
        "p",
        "Optional: give these roles shorter names for your application branches. Save all names together.",
      );
    heading.id = "jobenu-alias-title";
    help.className = "helper";
    const form = document.createElement("form"),
      fields = document.createElement("fieldset"),
      list = document.createElement("div");
    list.className = "jobenu-alias-fields";
    const inputs = titles.map((title) => {
      const label = make("label", title),
        input = document.createElement("input");
      input.value = aliasDrafts.get(title) || "";
      input.placeholder = "e.g. ml-engineer";
      input.pattern = "[a-z0-9][a-z0-9-]{0,63}";
      input.maxLength = 64;
      input.setAttribute("aria-describedby", "jobenu-alias-help");
      input.oninput = () => {
        aliasDrafts.set(title, input.value);
        save.disabled = !inputs.some((i) => i.value.trim());
      };
      label.append(input);
      list.append(label);
      return input;
    });
    const hint = make(
        "p",
        "Lowercase letters, numbers and hyphens, up to 64 characters. Leave any role blank to keep its current name.",
      ),
      failure = make("p", ""),
      save = make("button", "Save aliases & update preview");
    hint.id = "jobenu-alias-help";
    hint.className = "helper";
    failure.id = "jobenu-alias-error";
    failure.className = "form-error";
    failure.setAttribute("role", "alert");
    save.type = "submit";
    save.disabled = !inputs.some((i) => i.value.trim());
    fields.append(list, hint, failure, save);
    form.append(fields);
    form.onsubmit = async (event) => {
      event.preventDefault();
      if (busy || aliasSaving) return;
      const aliases = titles
        .map((title, i) => ({ title, alias: inputs[i].value.trim() }))
        .filter((a) => a.alias);
      if (!aliases.length) return;
      aliasSaving = true;
      fields.disabled = true;
      save.textContent = "Saving aliases…";
      failure.textContent = "";
      // A previous preview must not be started while its aliases are changing.
      version++;
      plan = null;
      $("#jobenu-start").disabled = true;
      updateSelection();
      try {
        await api("/api/jobenu/aliases", { aliases });
        for (const { title } of aliases) aliasDrafts.delete(title);
        $("#jobenu-feedback").textContent =
          `${aliases.length} role alias${aliases.length === 1 ? "" : "es"} saved. Updating preview…`;
        aliasSaving = false;
        await preview();
        $("#jobenu-preview").focus();
      } catch (err) {
        failure.textContent = err.message;
        if (!failure.isConnected) error(err);
      } finally {
        aliasSaving = false;
        fields.disabled = false;
        save.textContent = "Save aliases & update preview";
        updateSelection();
      }
    };
    host.append(heading, help, form);
  }
  $("#jobenu-preview").onclick = preview;
  $("#jobenu-start").onclick = async () => {
    if (busy || !plan) return;
    busy = true;
    updateSelection();
    const token = plan.plan_id;
    $("#jobenu-start").disabled = true;
    error("");
    try {
      await api("/api/jobenu/start", { id: session.id, planId: token });
      invalidate();
      await refresh();
    } catch (e) {
      error(e);
    } finally {
      busy = false;
      updateSelection();
    }
  };
  async function reviewEntry(batch, entry) {
    review = {
      batch,
      entry,
      ...(await api("/api/jobenu/review", { id: batch.id, key: entry.key })),
    };
    const content = $("#jobenu-review-content");
    content.replaceChildren();
    $("#jobenu-review-error").textContent = "";
    $("#jobenu-reject").hidden = review.kind !== "facts";
    const resolved =
      review.kind === "facts" &&
      ["approved", "applied", "rejected"].includes(review.report.status);
    $("#jobenu-approve").disabled = resolved;
    $("#jobenu-reject").disabled = resolved;
    $("#jobenu-approve").textContent = review.needsDraft
      ? "Generate requirement draft"
      : "Approve exact revision";
    if (review.kind === "facts") {
      const r = review.report;
      content.append(make("p", `Revision ${r.revision}`));
      for (const change of r.changes) {
        const article = document.createElement("article");
        article.className = "factual-change";
        article.append(
          make("h3", "Confirm the meaning of this change"),
          make("h4", "Original wording"),
          make("pre", change.original),
          make("h4", "Proposed wording"),
          make("pre", change.proposed),
        );
        const codes = article.querySelectorAll("pre");
        for (const [i, code] of [...codes].entries()) {
          code.className = i ? "wording-after" : "wording-before";
          renderLatexSnippet(
            code,
            i ? change.proposed : change.original,
            0,
            (i ? change.proposed : change.original).length,
          );
        }
        const sourceInfo = make(
          "p",
          `Category: ${change.kind || change.reason} · ${change.verification || "Requires review"} · Source facts: ${(change.source_fact_ids || []).join(", ")}`,
        );
        article.append(sourceInfo);
        for (const id of change.source_fact_ids || []) {
          const ref = review.report.source_facts?.find(
            (f) => f.id === id,
          )?.source_ref;
          if (!ref) continue;
          const path =
            review.report.candidate_sources?.sources?.find(
              (s) => s.id === ref.source_id,
            )?.path || "Captured source";
          const details = document.createElement("details");
          details.append(
            make(
              "summary",
              `${path} · lines ${ref.line_start}–${ref.line_end}`,
            ),
            make("pre", ref.quote),
          );
          article.append(details);
        }
        content.append(article);
      }
      content.append(
        make(
          "p",
          "Approve only after checking every factual interpretation against the captured sources.",
        ),
      );
    } else if (review.needsDraft)
      content.append(
        make(
          "p",
          "Canonical requirements need a separate draft and explicit approval. Generating a draft uses your configured AI provider.",
        ),
      );
    else {
      content.append(
        make(
          "p",
          "Review the immutable requirement definition, classifications and source references before approval.",
        ),
        make("p", `Revision ${review.report.revision.revision}`),
      );
      const definition = review.report.revision;
      for (const [key, label] of [
        ["requirements", "Requirements"],
        ["employment_conditions", "Employment conditions"],
      ]) {
        content.append(make("h3", label));
        for (const item of definition[key] || []) {
          const article = document.createElement("article");
          article.className = "factual-change";
          article.append(
            make("h4", item.criterion || item.text || item.label || item.key),
            make(
              "p",
              `${item.classification || item.kind || ""} · ${item.category || ""}`,
            ),
          );
          const refs = document.createElement("details");
          refs.append(
            make("summary", "Source references and definition"),
            make("pre", JSON.stringify(item, null, 2)),
          );
          article.append(refs);
          content.append(article);
        }
      }
    }
    if (!$("#jobenu-review").open) $("#jobenu-review").showModal();
  }
  $("#jobenu-review-close").onclick = () => $("#jobenu-review").close();
  async function decide(action) {
    const b = $("#jobenu-approve");
    b.disabled = true;
    $("#jobenu-reject").disabled = true;
    try {
      const revision =
        review.kind === "facts"
          ? review.report.revision
          : review.report?.revision?.revision;
      await api("/api/jobenu/decide", {
        id: review.batch.id,
        key: review.entry.key,
        action: review.needsDraft ? "draft" : action,
        revision,
      });
      if (review.needsDraft) await reviewEntry(review.batch, review.entry);
      else {
        $("#jobenu-review").close();
        $("#jobenu-feedback").textContent =
          "Decision saved. Use Preview resume to review the remaining work before continuing.";
        await refresh();
      }
    } catch (e) {
      $("#jobenu-review-error").textContent = e.message;
    } finally {
      b.disabled = false;
      $("#jobenu-reject").disabled = false;
    }
  }
  $("#jobenu-approve").onclick = () => decide("approve");
  $("#jobenu-reject").onclick = () => decide("reject");
  async function refresh() {
    if (polling) return;
    polling = true;
    try {
      const { batches } = await api("/api/jobenu");
      const signature = JSON.stringify(batches);
      if (signature === historySignature) return;
      historySignature = signature;
      const host = $("#jobenu-history");
      host.replaceChildren();
      for (const batch of batches) {
        const group = document.createElement("section");
        group.className = "jobenu-batch";
        group.append(
          make("h3", batch.filename),
          make(
            "p",
            batch.status === "complete"
              ? "AI stages complete · PDF generation and submission are separate"
              : statusLabel(batch.status),
          ),
        );
        if (batch.error) group.append(make("p", batch.error));
        const table = document.createElement("table");
        const heading = document.createElement("thead"),
          header = document.createElement("tr");
        for (const label of ["Company", "Position", "Progress", "Actions"])
          header.append(make("th", label));
        heading.append(header);
        table.append(heading);
        for (const e of batch.entries) {
          const row = document.createElement("tr");
          row.append(
            make("td", e.company),
            make("td", e.position),
            make(
              "td",
              [
                statusLabel(e.status || e.action),
                statusLabel(e.current_step),
                (e.completed_steps || []).map(statusLabel).join(" → "),
              ]
                .filter(Boolean)
                .join(" · "),
            ),
          );
          if (e.error) row.lastElementChild.append(make("p", e.error));
          const actions = document.createElement("td");
          if (e.workspace) {
            const open = make("button", "Open workspace");
            open.onclick = async () => {
              section.hidden = true;
              await openBranch(e.branch);
            };
            actions.append(open);
          }
          if (e.execution_log) {
            const log = make("button", "Application log");
            log.onclick = async () => {
              try {
                const r = await api("/api/jobenu/log", {
                  id: batch.id,
                  key: e.key,
                });
                group.append(make("pre", r.text));
              } catch (err) {
                error(err);
              }
            };
            actions.append(log);
          }
          if (e.pending || e.status === "awaiting_requirements_approval") {
            const button = make(
              "button",
              e.pending ? "Review changes" : "Review requirements",
            );
            button.onclick = () => reviewEntry(batch, e).catch(error);
            actions.append(button);
          }
          row.append(actions);
          table.append(row);
        }
        const scroll = document.createElement("div");
        scroll.className = "jobenu-scroll";
        scroll.tabIndex = 0;
        scroll.setAttribute("role", "region");
        scroll.setAttribute("aria-label", `Applications from ${batch.filename}`);
        scroll.append(table);
        group.append(scroll);
        const logs = make("button", "View logs");
        logs.onclick = async () => {
          try {
            const r = await api("/api/jobenu/log", { id: batch.id });
            const pre = make("pre", r.text);
            group.append(pre);
          } catch (e) {
            error(e);
          }
        };
        group.append(logs);
        if (batch.status !== "running") {
          const resume = make("button", "Preview resume");
          resume.onclick = async () => {
            invalidate();
            session = { id: batch.id };
            const opts = batch.options || {};
            $("#jobenu-base").value = opts.base || "";
            $("#jobenu-source").value = opts.source || "";
            $("#jobenu-approval").value = opts.approval || "human";
            $("#jobenu-run").checked = opts.run !== false;
            for (const k of ["language", "provider"])
              $("#jobenu-" + k).value = opts[k] || "";
            $("#jobenu-statuses").value = (opts.statuses || ["SAVED"]).join(
              ",",
            );
            $("#jobenu-demo").checked = !!opts.includeDemo;
            $("#jobenu-revision").checked = !!opts.newRevision;
            $("#jobenu-rerun").checked = false;
            const original = await api("/api/jobenu/selection", {
              id: batch.id,
            });
            session.applications = original.applications;
            selectedIds = new Set(opts.ids || []);
            aliasDrafts.clear();
            $("#jobenu-date-field").value = opts.dateField || "createdAt";
            $("#jobenu-date-from").value = opts.dateFrom || "";
            $("#jobenu-date-to").value = opts.dateTo || "";
            $("#jobenu-file-info").textContent =
              `${batch.filename} · ${original.applications.length} applications`;
            renderSelection();
            await check();
            await preview();
          };
          group.append(resume);
          const discard = make("button", "Forget batch");
          discard.onclick = async () => {
            if (
              confirm(
                "Forget this private export and batch history? Imported CV workspaces are kept.",
              )
            ) {
              await api("/api/jobenu/discard", { id: batch.id });
              await refresh();
            }
          };
          group.append(discard);
        }
        host.append(group);
      }
    } catch (e) {
      error(e);
    } finally {
      polling = false;
    }
  }
  setInterval(() => {
    if (!section.hidden) refresh();
  }, 1800);
  return { open: show };
}
