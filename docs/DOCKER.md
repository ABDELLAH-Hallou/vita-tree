# Docker

The image contains Vita Tree, Vita CV, Git, PDFLaTeX, XeLaTeX, LuaLaTeX,
latexmk, a selected TeX Live package set and redistributable fonts. Custom
classes/packages/fonts still need to be supplied by the project or an extended
image. For example, `fontawesome5.sty` is not part of this selected package set.
A project needing it can explicitly extend the image with Debian
`texlive-fonts-extra` (substantially increases image size); do not enable shell
escape or automatic package installation to bypass missing dependencies. Docker does not resolve existing application workflow limitations.

Use Docker Desktop with **Linux containers** on Windows/macOS, or Docker Engine
with Compose on Linux. A native Windows container is not supported. Start with
the published image tag you have explicitly pulled, or build this checkout:

```sh
docker compose build
docker compose up -d
```

Open <http://localhost:8765>. Set `VITA_IMAGE` to a versioned tag when using a manually published image;
the default `local` tag is for local builds. The default named volume creates a small starter
CV on first use. Replace it with your complete UTF-8 LaTeX CV project. No host
Python, Git, Node or LaTeX installation is needed for API-provider mode.

```sh
docker compose exec vita vita --help
docker compose exec vita vt --version
docker compose logs --tail 100 vita
docker compose stop
docker compose start
```

Project files, ignored Vita configuration, history, worktrees, checkpoints,
logs and exported PDFs persist in the workspace volume. `docker compose down`
keeps that volume; **`down -v` deletes it**. Back it up independently of Git.
UI-added API keys remain session-only. Configure the provider in the UI; image
layers do not contain provider or Git credentials.

## Existing projects

You can bind mount a complete repository at `/workspace` instead of the named
volume. Bind mounts are writable: changes affect the mounted project. Supply
all local classes, styles, includes, images and required fonts.

For Windows repositories with existing linked worktrees, use a **separate clone**
for Docker. Their Git metadata may contain absolute native paths that Linux
cannot resolve. Startup detects inaccessible registered worktrees and refuses
to repair/prune them. A linked worktree alone is not a complete repository.
Preserve uncommitted drafts and ignored configuration separately before moving
between native and container installations; a clone does not include them.
Do not run native Tree and container Tree against the same checkout concurrently.

Example using a separate existing clone (PowerShell):

```powershell
docker run --rm -p 127.0.0.1:8765:8765 --mount "type=bind,source=$PWD,target=/workspace" abdellahhallou/vita-tree:local
```

The container runs as UID 1000. On Linux, make the selected project writable by
that user or run with your UID/GID and a writable HOME. Do not fix permission
errors using privileged mode or by making unrelated host directories writable.
Set Git identity with `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`,
`GIT_COMMITTER_NAME` and `GIT_COMMITTER_EMAIL`, or configure it inside the
container. The Compose defaults are placeholders; replace them before syncing.

GitHub authentication is separate from AI authentication. Use a scoped runtime
credential helper or SSH setup for the intended remote. Do not embed tokens in
remote URLs, image builds or Compose files. `Save draft` remains usable without
a remote; `Save` requires a configured authenticated sync destination.

To choose another browser port, set `VITA_PORT` before starting Compose:

```powershell
$env:VITA_PORT="8875"
docker compose up -d
```

Keep the host publication on **127.0.0.1**. Container mode explicitly allows an
internal wildcard listener; Host, Origin and session-token checks remain active.
It is not a supported internet or shared-LAN deployment.

## Use the laptop's Codex installation

This optional mode uses an authenticated host helper and the existing native
Codex CLI contract, through Vita CV's `VITA_CODEX` executable hook. It creates
independent read-only CLI sessions against captured synthetic-or-user-approved
project snapshots; it does not attach to a desktop conversation. Codex remains
installed and signed in on the host. Its login files never enter the image.

Install this version of Vita Tree on the host (Python 3.10+ and host Git are
required for this helper). For a development checkout:

```sh
python -m pip install .
codex login status
vita-codex-host --host 0.0.0.0 --auth-file /path/to/private/codex-host-auth
```

On Windows, supply a Windows path for the authentication file. A new file gets
a random token. Keep this process running. Permit access only from your trusted
local Docker network using the host firewall; **do not expose port 8766 to the
internet or an untrusted LAN**. This local connector uses HTTP bearer
authentication, not TLS. Do not put it behind a public forwarding service.

In another PowerShell window:

```powershell
$env:CODEX_HOST_AUTH_FILE="C:\private\codex-host-auth"
docker compose -f compose.yaml -f compose.codex.yaml up -d
docker compose exec vita vita-codex-client --check
```

Set `CODEX_HOST_URL` if the helper uses a different trusted address/port.
Select Codex and the desired model in the UI. The helper forwards model,
reasoning and structured-output schema to the host's Codex; the normal Vita CV
validation/factual-change contracts remain in charge of generated artifacts.
The native CLI writes its response in the host scratch area; only that response
is returned and written to the container's requested output file.

Snapshots include bounded text source files, job text, selected skills and
reports. They exclude `.git`, `.env`, credentials, symlinks and binary files.
Images and arbitrary host paths are not transferred. Codex itself runs with
its native read-only sandbox and the host's existing trusted configuration;
the helper is not an OS sandbox against malicious local users or TeX.

Each session has its own directory and owned process tree. Requests are not
queued. Up to 32 retained sessions are accepted; excess requests fail explicitly.
Disconnected clients expire after 15 seconds without polling; shutdown cancels
owned process trees. Native generation has a ten-minute timeout. Backend schema
and installed Codex/model capabilities still determine what requests succeed.

Docker Desktop uses `host.docker.internal`. Linux Compose adds a host-gateway
mapping. Firewalls, Docker network configuration and managed host policies may
require adjustment. `--check` verifies transport/authentication only, not a paid
generation call or account/model access. API mode works without the helper.

## Build and publish manually

```sh
docker build -t abdellahhallou/vita-tree:local .
```

The base Python image digest and Vita CV version are pinned in the Dockerfile.
Debian packages/security updates are resolved at build time; repeat builds are
not promised to be byte-identical. Record the tested image ID and reuse the
same image when tagging. No automatic Docker Hub publication is configured.

After testing, the owner can manually tag and push the image:

```sh
docker tag abdellahhallou/vita-tree:local abdellahhallou/vita-tree:YOUR_VERSION
docker login
docker push abdellahhallou/vita-tree:YOUR_VERSION
```

Only assign `latest` deliberately after the versioned image is verified. Keep
the previous version for rollback. `docker compose pull` updates a published
tag; recreate the service while retaining its volume. An update/restart does
not automatically resume interrupted AI work.

For a multi-architecture release, build and test `linux/amd64` and `linux/arm64`
separately. Local tags are `local` and `local-arm64`; classic Docker image stores
cannot load a combined multi-platform image under one local tag. After the owner
pushes both versioned architecture tags, create their shared registry manifest:

```sh
docker buildx imagetools create --tag abdellahhallou/vita-tree:YOUR_VERSION \
  abdellahhallou/vita-tree:YOUR_VERSION-amd64 \
  abdellahhallou/vita-tree:YOUR_VERSION-arm64
```

The manifest lets Docker select the host-compatible image. Emulated ARM tests
do not replace native Apple Silicon/Linux ARM hardware testing. Mac host
integration and managed corporate firewall policies require their own checks.

## Verification boundaries

Use `tests/docker_smoke.py` against the built image and the focused container
and host-transport tests. These use synthetic data and no live AI provider.
Record the tested OS, architecture, Docker version, image ID and PDF engines.
Do not claim a platform is verified from an image build alone, or claim that
container packaging closes the application's unrelated workflow audit items.
