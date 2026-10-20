# AI workflow configuration

## Interaction design research

Reviewed the official product documentation on 20 October 2026:

- [n8n: create and edit credentials](https://docs.n8n.io/credentials/add-edit-credentials/): reusable credentials, with inline creation from a node's credential selector. Applied here as named connections that can be created next to a step's setup and reused by other steps.
- [n8n: OpenAI Chat Model](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatopenai/): model and optional controls belong to the model node, with suggestions based on account access. Vita Tree offers repository/local suggestions and editable model IDs; it does not claim that suggestions prove account access.
- [UiPath: connections](https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/connections): connection setup is separate from activities and reusable across automations. Applied here by separating the connection reference from a step's model and reasoning settings.
- [UiPath: organizing and sharing connections](https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/organizing-and-sharing-connections): a connection may serve multiple automations or a single automation. Applied here as a shared default, with optional independent connections for individual steps.

The resulting design uses progressive disclosure: a shared setup first, optional per-step configuration under Advanced, and an effective model summary on the workflow graph and each step. It retains Vita Tree's ordered CV workflow; it does not add arbitrary workflow graphs, scheduling, or third-party connectors.

## User flow

1. In **Job details & AI**, choose a provider in **Shared AI setup**.
2. Select a suggested model ID or type the exact ID accepted by the provider. Empty means the provider/Vita CV default. Suggestions are not an allowlist.
3. Choose a reasoning level where supported. Codex uses its CLI login and supports explicit reasoning through the source adapter. Other Vita CV transports currently offer Automatic.
4. Use existing local credentials, or **Add API key…** to create a named session connection. API connections can be reused by all steps with that same provider.
5. Optionally expand **Advanced · customize individual steps**, open a step, and enable **Use custom AI setup for this step**. This copies the shared setup as a starting point. The step then owns its configuration independently. Uncheck it to restore inheritance.
6. **Save AI setup** persists choices locally for this application. Runs use the current visible choices, including unsaved setup edits. **Use shared setup for every step** clears all overrides.

You can also click any AI component in the workflow graph, from any workspace tab, to open its settings popup. Choose **Use shared setup** or **Customize this step**, edit the provider/model/reasoning/connection, and select **Apply to step**. Apply saves the current AI setup locally and updates that component; Cancel, the close button, and Escape discard the popup's pending edits. API-key connections can be added directly from the popup. Selecting a component does not select it for execution or start an AI call.

When viewing a historical or running preparation, the popup displays the captured setup as read only. **Configure next run** opens the current draft when the application is editable and idle. Editing that draft never changes the recorded run. Final checks continue to use their local inspector because they have no AI setup.

The shared setup is a whole-route default. A custom step is a complete configuration, not a collection of field-by-field overrides. Changing its provider resets the model, reasoning, and connection to avoid mixing vendors. Non-custom steps always follow changes to the shared setup.

## Storage and execution

- Non-secret settings live under the repository's common Git directory at `vita-tree/ai-settings/<branch hash>.json`; they are not committed. Saved models also appear as suggestions.
- API keys live only in the running Workspace's memory. Lists and create responses contain connection ID, name, and provider, never the key. No key is stored in browser storage, settings files, generated extension files, run history, or diagnostics by this feature.
- Restarting the server expires session connections. Their saved references remain visible with instructions to add or select a connection again. Existing keys from the process environment or `.vita/.env` remain available as the local credentials option.
- Each submitted run captures the effective configuration and selected key for every selected step. Later setup edits or connection removal do not change a submitted run.
- Each step has its own subprocess environment, explicit provider, per-stage model routing, and temporary provider configuration. Two steps can use the same provider with different models and different API keys. The bridge gives process settings precedence over file settings.
- Run history retains the effective provider, model, reasoning, and connection ID/name for each executed step. The graph and inspector show this captured setup rather than the latest draft, including after a session connection expires. Validation uses no AI connection.
- Adding a connection checks its fields locally. It makes no provider request and does not verify model access or consume tokens. Provider authentication and model access are checked by the provider when the step runs.

## Validation

Unit and subprocess tests cover custom models, provider and reasoning validation, inheritance, persisted settings, session expiry, same-provider key isolation, mixed-provider execution, credential snapshots, secret-free outputs, and environment precedence. `tests/browser_ai_settings.py` checks the complete setup flow, graph popups from the CV tab, Apply/Cancel/Escape, validation errors, restored shared inheritance, API-key creation inside a popup, saved choices after reload, recorded settings, mixed-provider execution, expired connections, CSRF, and light/dark/mobile layouts using simulated AI processes.
