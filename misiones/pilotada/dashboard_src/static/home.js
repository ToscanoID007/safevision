(() => {
"use strict";

const byId = id => document.getElementById(id);
const state = {
  connected: false,
  toastTimer: null,
  statusTimer: null
};

function showToast(message) {
  const box = byId("toast");
  if (!box) return;
  box.textContent = message;
  box.classList.add("show");
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => box.classList.remove("show"), 1700);
}

function setConnection(connected, detail) {
  state.connected = Boolean(connected);

  const badge = byId("homeConnectionBadge");
  const text = byId("homeConnectionText");
  const connectionDetail = byId("homeConnectDetail");

  if (badge) {
    badge.classList.toggle("status-off", !state.connected);
  }

  if (text) {
    text.textContent = state.connected ? "CONECTADO" : "DESCONECTADO";
  }

  if (connectionDetail) {
    connectionDetail.classList.toggle("is-on", state.connected);
    connectionDetail.classList.toggle("is-off", !state.connected);

    const label = connectionDetail.querySelector("span:last-child");
    if (label) {
      label.textContent =
        detail ||
        (state.connected ? "Robot disponible" : "Esperando conexión");
    }
  }
}

function setDiag(name, value) {
  const item = document.querySelector(`[data-diag="${name}"]`);
  if (!item) return;

  item.classList.remove("diag-unknown", "diag-off");
  const valueNode = item.querySelector(".ok b");
  if (!valueNode) return;

  if (value === true) {
    valueNode.textContent = "OK";
  } else if (value === false) {
    item.classList.add("diag-off");
    valueNode.textContent = "OFF";
  } else {
    item.classList.add("diag-unknown");
    valueNode.textContent = "—";
  }
}

function resetDiag() {
  ["ros", "driver", "lidar", "camera", "navigation"]
    .forEach(name => setDiag(name, null));
}

function renderRobot(robot) {
  if (!robot || typeof robot !== "object") {
    resetDiag();
    return;
  }

  setDiag("ros", robot.ros_master === true);
  setDiag("driver", robot.driver === true);
  setDiag("lidar", robot.lidar === true);
  setDiag("camera", robot.camera === true);

  const ip = typeof robot.ip === "string" ? robot.ip.trim() : "";
  if (ip && byId("homeRobotIp")) {
    byId("homeRobotIp").value = ip;
  }
}

async function refreshNavigation() {
  if (!state.connected) {
    setDiag("navigation", null);
    return;
  }

  try {
    const response = await fetch("/nav/status", {cache: "no-store"});
    let data = {};
    try {
      data = await response.json();
    } catch (_) {}

    const ready =
      response.ok &&
      data &&
      data.ok !== false &&
      data.available !== false;

    setDiag("navigation", ready);
  } catch (_) {
    setDiag("navigation", false);
  }
}

async function refreshStatus() {
  try {
    const response = await fetch("/robot_status", {cache: "no-store"});

    if (!response.ok) {
      setConnection(false);
      resetDiag();
      return;
    }

    const data = await response.json();
    if (!data || !data.robot) {
      setConnection(false);
      resetDiag();
      return;
    }

    setConnection(true, "Robot disponible");
    renderRobot(data.robot);
    await refreshNavigation();
  } catch (_) {
    setConnection(false);
    resetDiag();
  }
}

async function connectRobot() {
  const input = byId("homeRobotIp");
  const button = byId("connectBtn");
  const ip = input ? input.value.trim() : "";

  if (!ip) {
    showToast("Escribe la IP de la Raspberry Pi.");
    return;
  }

  if (button) button.disabled = true;

  try {
    const response = await fetch("/connect", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ip})
    });

    let data = {};
    try {
      data = await response.json();
    } catch (_) {}

    if (!response.ok) {
      throw new Error(data.message || "No se pudo conectar.");
    }

    setConnection(true, "Robot disponible");
    renderRobot(data.robot || {});
    await refreshNavigation();
    showToast(`Conectado a ${ip}.`);
  } catch (error) {
    setConnection(false);
    resetDiag();
    showToast(error.message || "No se pudo conectar.");
  } finally {
    if (button) button.disabled = false;
  }
}

const routes = {
  "Misión Pilotada": "/pilotada",
  "Misión Automática": "/automatica",
  "Mapear": "/mapas/mapear",
  "Programar misión": "/programar",
  "Mapas": "/mapas",
  "Nodos": "/nodos"
};

document.querySelectorAll("[data-name]").forEach(button => {
  button.addEventListener("click", () => {
    const name = button.dataset.name || "";

    if (name === "Modelos / IA") {
      window.location.href = "/redes";
      return;
    }

    if (routes[name]) {
      window.location.href = routes[name];
    }
  });
});

if (byId("connectBtn")) {
  byId("connectBtn").addEventListener("click", connectRobot);
}

if (byId("homeRobotIp")) {
  byId("homeRobotIp").addEventListener("keydown", event => {
    if (event.key === "Enter") connectRobot();
  });
}

resetDiag();
refreshStatus();
state.statusTimer = setInterval(refreshStatus, 5000);


// =========================================================
// ROSMASTER X3 · VISOR STL REAL EN WEBGL, SIN DEPENDENCIAS
// =========================================================

function parseBinarySTL(buffer) {
  if (buffer.byteLength < 84) return null;

  const view = new DataView(buffer);
  const triangleCount = view.getUint32(80, true);
  const expected = 84 + triangleCount * 50;

  if (expected > buffer.byteLength) return null;

  const positions = new Float32Array(triangleCount * 9);
  let src = 84;
  let dst = 0;

  for (let t = 0; t < triangleCount; t += 1) {
    src += 12;

    for (let v = 0; v < 3; v += 1) {
      positions[dst++] = view.getFloat32(src, true);
      positions[dst++] = view.getFloat32(src + 4, true);
      positions[dst++] = view.getFloat32(src + 8, true);
      src += 12;
    }

    src += 2;
  }

  return positions;
}

function parseAsciiSTL(buffer) {
  const text = new TextDecoder().decode(buffer);
  const regex = /\bvertex\s+([+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?)\s+([+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?)\s+([+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?)/ig;
  const values = [];
  let match;

  while ((match = regex.exec(text)) !== null) {
    values.push(Number(match[1]), Number(match[2]), Number(match[3]));
  }

  return values.length >= 9 ? new Float32Array(values) : null;
}

function parseSTL(buffer) {
  return parseBinarySTL(buffer) || parseAsciiSTL(buffer);
}

function transformPoint(matrix, scale, x, y, z) {
  x *= scale[0];
  y *= scale[1];
  z *= scale[2];

  return [
    matrix[0] * x + matrix[1] * y + matrix[2] * z + matrix[3],
    matrix[4] * x + matrix[5] * y + matrix[6] * z + matrix[7],
    matrix[8] * x + matrix[9] * y + matrix[10] * z + matrix[11]
  ];
}

function triangleNormal(a, b, c) {
  const ux = b[0] - a[0];
  const uy = b[1] - a[1];
  const uz = b[2] - a[2];
  const vx = c[0] - a[0];
  const vy = c[1] - a[1];
  const vz = c[2] - a[2];

  let nx = uy * vz - uz * vy;
  let ny = uz * vx - ux * vz;
  let nz = ux * vy - uy * vx;

  const len = Math.hypot(nx, ny, nz) || 1;
  return [nx / len, ny / len, nz / len];
}

function perspective(fovy, aspect, near, far) {
  const f = 1 / Math.tan(fovy / 2);
  const nf = 1 / (near - far);

  return new Float32Array([
    f / aspect, 0, 0, 0,
    0, f, 0, 0,
    0, 0, (far + near) * nf, -1,
    0, 0, (2 * far * near) * nf, 0
  ]);
}

function multiply(a, b) {
  const out = new Float32Array(16);

  for (let col = 0; col < 4; col += 1) {
    for (let row = 0; row < 4; row += 1) {
      out[col * 4 + row] =
        a[row] * b[col * 4] +
        a[4 + row] * b[col * 4 + 1] +
        a[8 + row] * b[col * 4 + 2] +
        a[12 + row] * b[col * 4 + 3];
    }
  }

  return out;
}

function rotationX(angle) {
  const c = Math.cos(angle);
  const s = Math.sin(angle);
  return new Float32Array([
    1,0,0,0,
    0,c,s,0,
    0,-s,c,0,
    0,0,0,1
  ]);
}

function rotationY(angle) {
  const c = Math.cos(angle);
  const s = Math.sin(angle);
  return new Float32Array([
    c,0,-s,0,
    0,1,0,0,
    s,0,c,0,
    0,0,0,1
  ]);
}

function rotationZ(angle) {
  const c = Math.cos(angle);
  const s = Math.sin(angle);
  return new Float32Array([
    c,s,0,0,
    -s,c,0,0,
    0,0,1,0,
    0,0,0,1
  ]);
}

function translation(x, y, z) {
  return new Float32Array([
    1,0,0,0,
    0,1,0,0,
    0,0,1,0,
    x,y,z,1
  ]);
}

function compileShader(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);

  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    throw new Error(gl.getShaderInfoLog(shader) || "Shader inválido.");
  }

  return shader;
}

function createProgram(gl, vertexSource, fragmentSource) {
  const program = gl.createProgram();
  gl.attachShader(program, compileShader(gl, gl.VERTEX_SHADER, vertexSource));
  gl.attachShader(program, compileShader(gl, gl.FRAGMENT_SHADER, fragmentSource));
  gl.linkProgram(program);

  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    throw new Error(gl.getProgramInfoLog(program) || "WebGL inválido.");
  }

  return program;
}

async function loadRobotGeometry(manifest) {
  const chunks = [];
  let totalFloats = 0;

  let minX = Infinity;
  let minY = Infinity;
  let minZ = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  let maxZ = -Infinity;

  for (const part of manifest.parts || []) {
    const response = await fetch(
      part.url,
      {
        cache: "no-store"
      }
    );

    if (!response.ok) {
      throw new Error(
        `No se pudo cargar ${part.name}.`
      );
    }

    const raw = parseSTL(
      await response.arrayBuffer()
    );

    if (!raw) {
      throw new Error(
        `STL inválido: ${part.name}.`
      );
    }

    const matrix = part.matrix;
    const scale =
      part.scale
      ||
      [1, 1, 1];

    const color =
      part.color
      ||
      [0.34, 0.72, 0.72, 1];

    const partPositions =
      new Float32Array(raw.length);

    const partNormals =
      new Float32Array(raw.length);

    const partColors =
      new Float32Array(raw.length);

    let out = 0;

    for (
      let i = 0;
      i + 8 < raw.length;
      i += 9
    ) {
      const a =
        transformPoint(
          matrix,
          scale,
          raw[i],
          raw[i + 1],
          raw[i + 2]
        );

      const b =
        transformPoint(
          matrix,
          scale,
          raw[i + 3],
          raw[i + 4],
          raw[i + 5]
        );

      const c =
        transformPoint(
          matrix,
          scale,
          raw[i + 6],
          raw[i + 7],
          raw[i + 8]
        );

      const n =
        triangleNormal(
          a,
          b,
          c
        );

      for (
        const point
        of [a, b, c]
      ) {
        partPositions[out] =
          point[0];

        partNormals[out] =
          n[0];

        partColors[out] =
          color[0];

        minX =
          Math.min(
            minX,
            point[0]
          );

        maxX =
          Math.max(
            maxX,
            point[0]
          );

        out += 1;

        partPositions[out] =
          point[1];

        partNormals[out] =
          n[1];

        partColors[out] =
          color[1];

        minY =
          Math.min(
            minY,
            point[1]
          );

        maxY =
          Math.max(
            maxY,
            point[1]
          );

        out += 1;

        partPositions[out] =
          point[2];

        partNormals[out] =
          n[2];

        partColors[out] =
          color[2];

        minZ =
          Math.min(
            minZ,
            point[2]
          );

        maxZ =
          Math.max(
            maxZ,
            point[2]
          );

        out += 1;
      }
    }

    chunks.push({
      positions:
        partPositions,
      normals:
        partNormals,
      colors:
        partColors
    });

    totalFloats +=
      partPositions.length;
  }

  if (!totalFloats) {
    throw new Error(
      "El modelo no contiene triángulos."
    );
  }

  const cx =
    (minX + maxX) / 2;

  const cy =
    (minY + maxY) / 2;

  const cz =
    (minZ + maxZ) / 2;

  const extent =
    Math.max(
      maxX - minX,
      maxY - minY,
      maxZ - minZ
    )
    ||
    1;

  const factor =
    1.65 / extent;

  const positions =
    new Float32Array(
      totalFloats
    );

  const normals =
    new Float32Array(
      totalFloats
    );

  const colors =
    new Float32Array(
      totalFloats
    );

  let offset = 0;

  for (
    const chunk
    of chunks
  ) {
    const source =
      chunk.positions;

    for (
      let i = 0;
      i < source.length;
      i += 3
    ) {
      positions[offset + i] =
        (source[i] - cx)
        *
        factor;

      positions[offset + i + 1] =
        (source[i + 1] - cy)
        *
        factor;

      positions[offset + i + 2] =
        (source[i + 2] - cz)
        *
        factor;
    }

    normals.set(
      chunk.normals,
      offset
    );

    colors.set(
      chunk.colors,
      offset
    );

    offset +=
      source.length;
  }

  return {
    positions,
    normals,
    colors,
    count:
      totalFloats / 3
  };
}

async function initRobotViewer() {
  const canvas = byId("homeRobotCanvas");
  const stage = byId("robotStage");
  const fallback = byId("robot");
  const badge = document.querySelector(".stage-label");

  if (!canvas || !stage) return;

  const gl = canvas.getContext("webgl", {
    antialias: true,
    alpha: true,
    depth: true
  });

  if (!gl) {
    if (badge) badge.textContent = "VISTA 3D NO DISPONIBLE";
    return;
  }

  try {
    const response = await fetch("/static/robot_x3/manifest.json", {
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error("Manifiesto STL no disponible.");
    }

    const manifest = await response.json();
    const geometry = await loadRobotGeometry(manifest);

    const vertexShader = `
      attribute vec3 aPosition;
      attribute vec3 aNormal;
      attribute vec3 aColor;
      uniform mat4 uMVP;
      uniform mat4 uModel;
      varying vec3 vNormal;
      varying vec3 vColor;
      void main() {
        gl_Position = uMVP * vec4(aPosition, 1.0);
        vNormal = normalize(mat3(uModel) * aNormal);
        vColor = aColor;
      }
    `;

    const fragmentShader = `
      precision mediump float;
      varying vec3 vNormal;
      varying vec3 vColor;
      void main() {
        vec3 n = normalize(vNormal);
        vec3 key = normalize(vec3(0.45, 0.72, 0.82));
        vec3 fillDir = normalize(vec3(-0.55, -0.25, 0.40));
        float diffuse = abs(dot(n, key));
        float fill = abs(dot(n, fillDir)) * 0.16;
        float rim = pow(1.0 - abs(n.z), 2.0) * 0.12;
        vec3 color = vColor * (0.34 + diffuse * 0.64 + fill);
        color += vec3(0.06, 0.18, 0.19) * rim;
        gl_FragColor = vec4(color, 1.0);
      }
    `;

    const program = createProgram(gl, vertexShader, fragmentShader);
    gl.useProgram(program);

    function bind(name, data) {
      const location = gl.getAttribLocation(program, name);
      const buffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
      gl.enableVertexAttribArray(location);
      gl.vertexAttribPointer(location, 3, gl.FLOAT, false, 0, 0);
    }

    bind("aPosition", geometry.positions);
    bind("aNormal", geometry.normals);
    bind("aColor", geometry.colors);

    const uMVP = gl.getUniformLocation(program, "uMVP");
    const uModel = gl.getUniformLocation(program, "uModel");

    gl.enable(gl.DEPTH_TEST);

    // SAFEVISION HOME STL V3.1
    // STL CAD Yahboom: render de doble cara.
    gl.disable(gl.CULL_FACE);

    gl.clearColor(0, 0, 0, 0);

    let yaw = -0.62;
    let pitch = -0.38;
    let roll = -0.08;
    let distance = 3.2;
    let dragging = false;
    let lastX = 0;
    let lastY = 0;

    function resize() {
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      const width = Math.max(1, Math.round(stage.clientWidth * ratio));
      const height = Math.max(1, Math.round(stage.clientHeight * ratio));

      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      gl.viewport(0, 0, width, height);
    }

    function draw() {
      resize();
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

      const projection = perspective(
        Math.PI / 4,
        canvas.width / Math.max(canvas.height, 1),
        0.1,
        100
      );

      let model = multiply(rotationY(yaw), rotationX(pitch));
      model = multiply(rotationZ(roll), model);

      const view = translation(0, 0, -distance);
      const mvp = multiply(projection, multiply(view, model));

      gl.uniformMatrix4fv(uModel, false, model);
      gl.uniformMatrix4fv(uMVP, false, mvp);
      gl.drawArrays(gl.TRIANGLES, 0, geometry.count);
    }

    stage.addEventListener("pointerdown", event => {
      dragging = true;
      lastX = event.clientX;
      lastY = event.clientY;
      stage.setPointerCapture(event.pointerId);
    });

    stage.addEventListener("pointermove", event => {
      if (!dragging) return;

      yaw += (event.clientX - lastX) * 0.009;
      pitch += (event.clientY - lastY) * 0.007;
      pitch = Math.max(-1.35, Math.min(1.35, pitch));

      lastX = event.clientX;
      lastY = event.clientY;
      draw();
    });

    stage.addEventListener("pointerup", () => {
      dragging = false;
    });

    stage.addEventListener("pointercancel", () => {
      dragging = false;
    });

    stage.addEventListener("wheel", event => {
      event.preventDefault();
      distance += Math.sign(event.deltaY) * 0.20;
      distance = Math.max(2.15, Math.min(5.6, distance));
      draw();
    }, {passive: false});

    if (byId("resetView")) {
      byId("resetView").addEventListener("click", () => {
        yaw = -0.62;
        pitch = -0.38;
        roll = -0.08;
        distance = 3.2;
        draw();
      });
    }

    window.addEventListener("resize", draw);

    if (fallback) fallback.classList.add("stl-active");
    if (badge) {
      const count = Array.isArray(manifest.parts) ? manifest.parts.length : 0;
      badge.textContent = `STL REAL · ${count} PIEZAS`;
    }

    draw();
  } catch (error) {
    console.warn("[SafeVision Home] STL:", error);
    if (badge) badge.textContent = "STL · FALLBACK";
  }
}

initRobotViewer();

})();


// =========================================================
// SAFEVISION HOME V3.2 · TEMA PLANO
// Alinea el Home con la estética existente de las misiones.
// Solo presentación: no cambia rutas, Runtime ni visor 3D.
// =========================================================
(() => {
  "use strict";

  if (
    document.getElementById(
      "safeVisionHomeFlatThemeV32"
    )
  ) {
    return;
  }

  const style =
    document.createElement(
      "style"
    );

  style.id =
    "safeVisionHomeFlatThemeV32";

  style.textContent = `
    body.sv-home-body {
      background:
        #07111b
        !important;
    }

    .glass {
      background:
        linear-gradient(
          180deg,
          #101c29,
          #0b1722
        )
        !important;

      box-shadow:
        none
        !important;

      backdrop-filter:
        none
        !important;
    }

    .topbar::before {
      display:
        none
        !important;
    }

    .logo {
      background:
        #0d2131
        !important;

      box-shadow:
        none
        !important;
    }

    .status .dot,
    .conn-state .dot,
    .diag-item .ok i {
      box-shadow:
        none
        !important;
    }

    .sidebar::after {
      display:
        none
        !important;
    }

    .btn {
      box-shadow:
        none
        !important;
    }

    .btn:hover {
      filter:
        none
        !important;
    }

    .menu-item:hover {
      background:
        #0d2130
        !important;
    }

    .menu-item:hover::before {
      box-shadow:
        none
        !important;
    }

    .robot-stage {
      background:
        linear-gradient(
          rgba(94,161,255,.022)
          1px,
          transparent
          1px
        ),
        linear-gradient(
          90deg,
          rgba(94,161,255,.022)
          1px,
          transparent
          1px
        ),
        #07131e
        !important;

      background-size:
        30px 30px,
        30px 30px,
        auto
        !important;
    }

    .robot-stage::before {
      display:
        none
        !important;
    }

    .robot-stage::after {
      background:
        linear-gradient(
          90deg,
          transparent,
          rgba(142,178,208,.10),
          transparent
        )
        !important;

      box-shadow:
        none
        !important;
    }

    .chassis,
    .lidar,
    .camera,
    .deck,
    .robot-wrap {
      filter:
        none
        !important;
    }

    .diag-item {
      box-shadow:
        none
        !important;
    }

    .diag-item::after {
      background:
        linear-gradient(
          90deg,
          transparent,
          rgba(142,178,208,.08),
          transparent
        )
        !important;
    }
  `;

  document.head.appendChild(
    style
  );
})();
