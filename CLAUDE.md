# CLAUDE.md — SafeVision / Rosmaster X3

Read this fully before touching anything. The authoritative background is
`docs/handoff-2026-09.md` (Spanish, ~80 sections). Section numbers below
refer to that document.

## What this project is

A Yahboom Rosmaster X3 mobile robot (Raspberry Pi, ROS Melodic, RPLIDAR, IMU,
USB RGB camera) plus a PC dashboard. Three layers:

- **Robot** (`misiones/pilotada/robot/`): Flask "Robot Server" on `:8091` is
  the HTTP↔ROS boundary. ROS nodes handle driver, AMCL, `move_base`, mapping,
  a `cmd_vel` selector with watchdog, and a navigation queue.
- **Dashboard** (`misiones/pilotada/dashboard_src/`): Flask on
  `127.0.0.1:5000`. UI, proxy to the Robot Server, YOLO inference (runs on the
  PC), map editor, mission editor/simulator.
- **Missions** (`misiones/automatica/robot/`): a restricted Python-like DSL
  (`ir`, `esperar`, `orientar`, `girar`, `relocalizar`) → validate → simulate
  → execution plan → `sf_nav_queue` → `move_base`.

Identifiers, DSL keywords, commit messages and comments are in Spanish. Keep
them that way; do not "translate" code.

## Repo map — what is current, what is legacy

| Path | Status |
|---|---|
| `misiones/pilotada/robot/` | **Current runtime.** Primary refactor target. |
| `misiones/pilotada/dashboard_src/` | **Current dashboard.** Templates and static are complete and tracked. |
| `misiones/automatica/robot/` | **Current** automatic-mission runtime. |
| `misiones/pilotada/systemd/` + `sf_*_service.sh` | **Current.** Runtime now runs as systemd services on the Pi. |
| `mapping/maps/`, `modelos/`, `misiones/programadas/` | Data. Keep, review names later. |
| `api/` | **Previous generation** (SSH/Paramiko dashboard, terminal menus). Some utilities may still be referenced. Classify before removing — see "Deleting code". |
| `grafo/`, `generar_arbol.py`, `escanear_proyecto.sh`, `api/exportar_codigo.sh` | Tools. |
| `mapeo_denso.sh`, `auto_mapeo.sh`, `emisor_sensores.sh`, Astra/RTAB-Map scripts | 3D/depth experiments. Not integrated. Do not build on them. |
| `yahboomcar_ws` (outside this repo, on the Pi) | Hard dependency. Copy of `src/` lives at `~/yahboomcar_ws-src` on the dev laptop. |

## Known drift: the handoff doc is behind the code

The doc audited tag `safevision-return-2026-08-19-73b187d`. Since then
(see `git diff --stat safevision-return-2026-08-19-73b187d wip-handoff`):

- `sf_runtime_manager.py` (~1,600 lines) is **new** and not described in the
  doc. It likely supersedes parts of `sf_operacion_pilotada.sh` (section 11).
  Establish which one actually boots the runtime before refactoring either.
- `sf_runtime_core.launch` and `sf_runtime_lidar.launch` are new.
- `sf_robot_server.py` grew by ~476 lines (now ~4,800).
- systemd units `safevision-roscore.service` and
  `safevision-robot-server.service` exist. Anything they reference is live.
- `sf_model_manager.py` exists in `robot/` and is not covered by the doc.

Treat the doc as an audited baseline, not as ground truth for these files.

## Hard rules

1. **Do not delete anything in `api/`** until the criteria in "Deleting code"
   are met and documented. "Old" is not "dead".
2. **One axis at a time** (section 75): never change ROS, Python version,
   containers, dashboard, navigation params and depth in the same change.
3. **Preserve these decisions** (section 57): Dashboard/robot separation;
   Robot Server as the only HTTP↔ROS boundary; single shared camera capture;
   manual/navigation `cmd_vel` selector with watchdog; explicit cancel;
   map bound to nav queue; `make_plan` pre-validation; mapping rollback;
   validate → simulate → execute for missions; `/health` endpoint.
4. **Critical loops stay on the robot** (section 79): `cmd_vel`, watchdog,
   `move_base`, cancel, e-stop, drivers, sensors. Nothing remote may close
   the motion loop.
5. **Never expose `:8091` or `:11311` to the Internet** (sections 50, 64).
   Remote access goes through Tailscale/VPN only.
6. **No secrets in the repo.** The legacy SSH layer had embedded credentials
   and `AutoAddPolicy`; do not reintroduce either.
7. **Do not commit**: model weights (`*.pt`, `*.torchscript`), logs,
   payload tarballs/zips, generated exports. Maps (`*.yaml` + `*.pgm`) are
   tracked and versioned as a pair.
8. **Nav params are frozen** (`robot/nav/*.yaml`, footprint ±0.117/±0.100 m)
   until a hardware baseline exists (section 30).
9. **`girar()` and `relocalizar()` are not physically implemented** in the
   automatic runtime (section 38). Do not document them as working.
10. Python is mixed: ROS-side code runs under Melodic's Python (2.7-era
    `rospy`), dashboard code under Python 3. Check the shebang and the
    launcher before assuming which interpreter runs a file.

## Deleting code (section 77)

A file may be removed only after `git grep` and tracing confirm it is not:
imported; run via `subprocess`; run from a shell script; referenced in any
`.launch`; used by a menu (`api/main_menu.py`, `api/menu_operacion.py`);
referenced by a systemd unit or cron; documented as a fallback; required by
tests. Record the evidence in the commit message. The acceptance test
(section 59) must pass before and after.

## Development environment

- Dev laptop: Ubuntu 18.04 host (kept deliberately — ROS Melodic and the
  Ubuntu18 dashboard build). Claude Code and Orca run inside a Distrobox
  Ubuntu 22.04 container; the home directory is shared.
- **ROS is not available inside the container.** You cannot run nodes,
  `roslaunch`, or the Robot Server here. Unit tests for pure-Python parts
  (mission DSL, validation, schemas) are the only tests that run locally.
- Nothing you do here moves the robot. Hardware validation is a separate,
  human-run step on the Pi (`pi@yahboom.local`).
- Remotes: `origin` = GitHub (hub), `pi` = the robot's working copy.
  Never push to `pi`; the Pi pulls from GitHub.
- Baseline: tag `pre-refactor-baseline` on branch `wip-handoff`.
- Raw filesystem copy of the Pi (incl. untracked weights/logs):
  `~/safevision-raw/`. Read-only reference.

## Workflow

- Branch per task from `wip-handoff`, named like the existing ones
  (`refactor/…`, `feature/…`). Commit messages follow the existing style:
  `feat:`, `chore:`, `fix:` + Spanish description.
- Small, reviewable changes. Each refactor commit cites the handoff section
  it implements.
- When in doubt about whether something is used, trace it and write down
  what you found instead of guessing.
- Do not rewrite a monolith wholesale. Extract one domain at a time behind
  the existing entry points so the acceptance test stays runnable.

## Refactor phases (section 62) and where we are

0. Freeze baseline — **done** (`pre-refactor-baseline`).
1. Repo cleanup: separate current / legacy / tools / tests / deploy — **now**.
2. Contracts: `safevision_protocol` package (Pydantic/JSON Schema for
   Mission, MissionPoint, NavigationCommand, RobotHealth, MapMetadata,
   ModelMetadata).
3. Split monoliths by domain (`sf_robot_server.py`, `sf_app_dashboard.py`,
   `sf_mission_lang.py`, `sf_mapping_manager.py`, `sf_runtime_manager.py`).
4. Centralize hard-coded config (paths, ports, devices).
5. Tests (unit → integration → hardware).
6. Edge containerization on the Pi (functional equivalence first; must
   wrap/replace the systemd units; watch `/proc` inspection in the mapping
   manager, section 24).
7. Decouple dashboard frontend.
8. Cloud control plane (auth, fleet, registries, telemetry).
9. Depth camera integration.

## First tasks for the agent

1. Read `docs/handoff-2026-09.md` sections 0–1, 11–14, 43–45, 57, 62, 75–78.
2. Read `sf_runtime_manager.py`, `sf_operacion_pilotada.sh` and both systemd
   units; write `docs/runtime-boot.md` describing how the runtime actually
   starts today and which of the two launchers is live.
3. Produce `docs/inventory.md`: every file under `api/` classified as
   *used by current runtime / used only by legacy path / tool / unreferenced*,
   with the `git grep` evidence for each.
4. Propose (do not execute) a Phase 1 directory layout, mapping each current
   file to its new location, as `docs/phase1-plan.md`.
5. Only after 2–4 are reviewed by a human: start Phase 1 moves, one directory
   per commit.
