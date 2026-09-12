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

## Known drift: the handoff doc is behind the code — RESOLVED 2026-09-10

The doc audited tag `safevision-return-2026-08-19-73b187d`. The drift it left
open has now been traced in the code and **verified on the robot itself**. See
`docs/runtime-boot.md` and `docs/estado-actual.md`.

- **`sf_runtime_manager.py` (1,610 lines) supersedes `sf_operacion_pilotada.sh`
  entirely**, and adds capabilities the script never had (profiles, selective
  teardown, LiDAR silent-failure recovery, the mapping handoff). It is an
  imported module, not an executable — no `__main__`.
- **The live boot path is systemd**: `safevision-roscore.service` →
  `safevision-robot-server.service` → `sf_robot_server.py --control mando`.
  Both units are installed, `enabled`, and byte-identical to the repo copies
  (verified). `sf_operacion_pilotada.sh` is a secondary path, still reachable
  from `api/main_menu.py`, and the two are mutually exclusive.
- **After boot only `roscore` + Robot Server run.** Everything that moves the
  robot is started on demand by `POST /runtime/profile`. Confirmed on a real
  cold boot: 1 h 55 min of uptime with `profile.requested` still `null`.
- `sf_runtime_core.launch` and `sf_runtime_lidar.launch` are new: together with
  `sf_localizacion_mapa.launch` they decompose the old `sf_localizacion.launch`.
- `sf_robot_server.py` is **5,060 lines** (the doc said ~4,300).
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
10. **Python is mixed, but not the way you would expect** (verified on the
    robot, 2026-09-10). Three interpreters coexist:
    `/usr/local/bin/python3` = **3.7.3**, a local build, runs the Robot Server
    and every SafeVision node; `/usr/bin/python` = 2.7.17 runs `roscore` and
    **`sf_pose_exporter.py`**; `/usr/bin/python3` = 3.6.9 is unused.
    `rospy` is installed **only** in the Python 2 tree and 3.7 imports it via
    `PYTHONPATH` — that works because `rospy` is pure Python.
    **`sf_pose_exporter.py` is the one file that MUST stay on Python 2**: it is
    the only one importing `tf`, whose `_tf2.so` is a Python-2 C extension
    (`ImportError: ... PyInit__tf2` under 3.7). Porting it breaks the robot's
    pose on the map. See `docs/anexo-dependencias-robot.md` §2.

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
- Raw copy of the Pi's **`robot_custom` directory** (incl. untracked weights
  and logs): `~/safevision-raw/`. Read-only reference. Note it is *not* a copy
  of the Pi's filesystem — it holds no `/etc`, `crontab` or `.bashrc`.
- The robot is reachable at `pi@yahboom.local`. SSH needs a password; there is
  no key installed for non-interactive access. The Robot Server answers
  read-only HTTP GETs on `:8091` without any credential.

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

## Current priority: the social-service deliverable

**The refactor roadmap above is NOT the current goal.** The professor who owns
the robot asked for three things: everything working, a documented and
easy-to-install repo, and a structured final report. **No cloud, no containers,
no refactor.** Work on branch `docs/entrega`; see `docs/README.md` for the map
of what exists.

What is still open, in priority order (details in `docs/analisis-alcance.md` §6):

1. **Version the working dashboard.** `~/SafeVision_Dashboard_dev/` on the dev
   laptop is a day newer than the committed one and is the only thing that can
   apply a runtime profile from the UI (71 routes vs 66, a strict superset).
   Until it is committed, the robot is only operable via `curl`.
   Run test V-1 of `docs/validacion.md` first.
2. **Execute `docs/validacion.md`** (87 tests) and record the results.
3. ~~Rotate the exposed credentials~~ — **decided 2026-09-12: not rotated, history
   not rewritten, everything stays as is.** `docs/security-scan.md` remains as analysis.
4. Optional, recommended: RGB-D fusion, option A (`docs/analisis-alcance.md` §4).
   The Astra Pro is already mounted and `depthimage_to_laserscan` is installed.

## Earlier agent tasks — done 2026-09-10

1. Read `docs/handoff-2026-09.md` sections 0–1, 11–14, 43–45, 57, 62, 75–78.
2. Read `sf_runtime_manager.py`, `sf_operacion_pilotada.sh` and both systemd
   units; write `docs/runtime-boot.md` describing how the runtime actually
   starts today and which of the two launchers is live.
3. Produce `docs/inventory.md`: every file under `api/` classified as
   *used by current runtime / used only by legacy path / tool / unreferenced*,
   with the `git grep` evidence for each.
4. ~~Propose a Phase 1 directory layout as `docs/phase1-plan.md`~~ —
   **not done, and deliberately so.** The repo-cleanup phase was superseded by
   the deliverable above: structure now comes from documentation, not from
   moving files. Do not start it without the professor asking.
5. ~~Start Phase 1 moves~~ — same: out of scope.

> One correction worth carrying forward: `docs/inventory.md` classified several
> files as "unreferenced" using `git grep` alone. Verification on the robot found
> the invoker lives **outside the repo** — 13 aliases in `/home/pi/.bashrc`.
> **No file under `api/` or at the repo root meets the deletion criteria.**
> See `docs/estado-actual.md` §6.
