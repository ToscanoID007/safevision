/*
 * SafeVision - genera el reporte final en Word a partir de docs/reporte-final.md.
 *
 *   cd scripts/reporte_docx && npm install && node generar_reporte.js [indice.json]
 *
 * Portada, indice, encabezado y numeracion de pagina; tablas, listas, notas,
 * figuras con pie y bloque de firmas. Los diagramas mermaid se sustituyen por
 * docs/entrega/img/diagrama-N.png y las capturas .webp por sus .png en esa
 * carpeta (Word no siempre muestra webp). El indice lleva numeros de pagina si
 * se le pasa un JSON {titulo: pagina} (lo calcula verificar_paginas.py).
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ExternalHyperlink, ImageRun, Table, TableRow,
  TableCell, WidthType, ShadingType, BorderStyle, AlignmentType, HeadingLevel,
  LevelFormat, Header, Footer, PageNumber, PageBreak, TabStopType, TabStopPosition,
  VerticalAlign, TableLayoutType,
} = require("docx");

const RAIZ = path.resolve(__dirname, "..", "..");
const MD = path.join(RAIZ, "docs", "reporte-final.md");
const SALIDA = path.join(RAIZ, "docs", "entrega", "reporte-final.docx");
const IMG = path.join(RAIZ, "docs", "entrega", "img");
const DIMS = JSON.parse(fs.readFileSync(path.join(IMG, "dimensiones.json"), "utf8"));
const PAGINAS = process.argv[2] && fs.existsSync(process.argv[2])
  ? JSON.parse(fs.readFileSync(process.argv[2], "utf8")) : {};

// Carta, margenes de 2,5 cm
const PAGINA = { width: 12240, height: 15840 };
const MARGEN = 1417;
const ANCHO = PAGINA.width - 2 * MARGEN;           // 9406 DXA
const AZUL = "1F3864", AZUL_CLARO = "D9E2F3", GRIS = "595959", FUENTE = "Arial";

// ---------------------------------------------------------------- texto en linea
const SIMBOLOS = [[/\\theta/g, "θ"], [/\\omega/g, "ω"]];
function limpiar(t) {
  t = t.replace(/✅\s*/g, "").replace(/❌\s*/g, "").replace(/⚠️\s*/g, "").replace(/📝\s*/g, "");
  return t;
}
function mayusInicial(t) { return t ? t.charAt(0).toUpperCase() + t.slice(1) : t; }

function enLinea(texto, base = {}) {
  texto = limpiar(texto);
  const runs = [];
  // tokens: **negrita**, *cursiva*, `codigo`, [t](u), <http..>, $math$
  const re = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|<https?:[^>]+>|\$[^$]+\$|~~[^~]+~~)/g;
  let ultimo = 0, m;
  const plano = (t) => { if (t) runs.push(new TextRun({ text: t, font: FUENTE, ...base })); };
  while ((m = re.exec(texto)) !== null) {
    plano(texto.slice(ultimo, m.index));
    const tok = m[0];
    if (tok.startsWith("**")) {
      enLinea(tok.slice(2, -2), { ...base, bold: true }).forEach((r) => runs.push(r));
    } else if (tok.startsWith("~~")) {
      runs.push(new TextRun({ text: tok.slice(2, -2), font: FUENTE, strike: true, ...base }));
    } else if (tok.startsWith("*")) {
      enLinea(tok.slice(1, -1), { ...base, italics: true }).forEach((r) => runs.push(r));
    } else if (tok.startsWith("`")) {
      runs.push(new TextRun({ text: tok.slice(1, -1), font: "Consolas", size: (base.size || 21) - 2, color: "333333", ...(base.bold ? { bold: true } : {}) }));
    } else if (tok.startsWith("$")) {
      let t = tok.slice(1, -1); SIMBOLOS.forEach(([a, b]) => { t = t.replace(a, b); });
      runs.push(new TextRun({ text: t, font: "Cambria Math", italics: true, ...base }));
    } else if (tok.startsWith("<")) {
      const url = tok.slice(1, -1);
      runs.push(new ExternalHyperlink({ link: url, children: [new TextRun({ text: url, font: FUENTE, style: "Hyperlink", ...base })] }));
    } else {
      const mm = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(tok);
      const etiqueta = mm[1], destino = mm[2];
      if (/^https?:/.test(destino)) {
        runs.push(new ExternalHyperlink({ link: destino, children: enLinea(etiqueta, { ...base, style: "Hyperlink" }) }));
      } else {
        // Enlace a otro documento del repositorio: texto plano con su ruta
        enLinea(etiqueta, base).forEach((r) => runs.push(r));
      }
    }
    ultimo = m.index + tok.length;
  }
  plano(texto.slice(ultimo));
  return runs;
}

// ---------------------------------------------------------------- bloques
const numeracionListas = [];
let listaId = 0;

function parrafo(texto, opciones = {}) {
  return new Paragraph({ children: enLinea(texto, opciones.run || {}), spacing: { after: 120, line: 276 }, ...opciones.p });
}

function figura(ruta, pie, anchoMaxCm = 15.5, altoMaxCm = 11) {
  const dims = DIMS[path.relative(RAIZ, ruta)] || DIMS[ruta];
  if (!dims) throw new Error("Sin dimensiones para " + ruta);
  const [w, h] = dims;
  const pxPorCm = 37.8;  // docx-js usa px a 96 ppp
  let ancho = anchoMaxCm * pxPorCm, alto = ancho * h / w;
  if (alto > altoMaxCm * pxPorCm) { alto = altoMaxCm * pxPorCm; ancho = alto * w / h; }
  const tipo = ruta.toLowerCase().endsWith(".png") ? "png" : "jpg";
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 }, keepNext: true,
      children: [new ImageRun({ type: tipo, data: fs.readFileSync(ruta), transformation: { width: Math.round(ancho), height: Math.round(alto) },
        altText: { title: pie, description: pie, name: path.basename(ruta) } })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: enLinea(pie, { italics: true, size: 19, color: GRIS }),
    }),
  ];
}

function rutaImagen(rel) {
  // rel es relativo a docs/. Los .webp se sustituyen por su .png en docs/entrega/img
  let r = path.join(RAIZ, "docs", rel);
  if (r.endsWith(".webp")) r = path.join(IMG, path.basename(r).replace(/\.webp$/, ".png"));
  return r;
}

function celdasDe(linea) {
  return linea.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
}

function anchosColumnas(filas) {
  // Proporcional al contenido, pero ninguna columna mas estrecha que su palabra
  // mas larga (a 9,5 pt Arial, ~110 DXA por caracter + margenes): sin palabras partidas.
  const n = filas[0].length;
  const texto = (c) => limpiar(c).replace(/[*`]|\[([^\]]*)\]\([^)]*\)/g, "$1");
  const largos = Array(n).fill(4), minimos = Array(n).fill(700);
  filas.forEach((f, fi) => f.forEach((c, i) => {
    const t = texto(c);
    largos[i] = Math.max(largos[i], Math.min(t.length, 70));
    const palabra = Math.max(...t.split(/\s+/).map((w) => w.length), 1);
    minimos[i] = Math.max(minimos[i], Math.min(palabra, 28) * (fi === 0 ? 120 : 110) + 230);
  }));
  const total = largos.reduce((a, b) => a + b, 0);
  let anchos = largos.map((l, i) => Math.max(minimos[i], Math.round(ANCHO * l / total)));
  // Si los minimos desbordan, se recorta de las columnas que tienen holgura
  let exceso = anchos.reduce((a, b) => a + b, 0) - ANCHO;
  while (exceso > 0) {
    const holgura = anchos.map((a, i) => a - minimos[i]);
    const k = holgura.indexOf(Math.max(...holgura));
    if (holgura[k] <= 0) break;
    const quita = Math.min(exceso, holgura[k]);
    anchos[k] -= quita; exceso -= quita;
  }
  const suma = anchos.reduce((a, b) => a + b, 0);
  if (suma !== ANCHO) {
    const ancha = anchos.indexOf(Math.max(...anchos));
    anchos[ancha] += ANCHO - suma;
  }
  return anchos;
}

function tabla(filas) {
  const anchos = anchosColumnas(filas);
  const borde = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
  const bordes = { top: borde, bottom: borde, left: borde, right: borde };
  return new Table({
    width: { size: ANCHO, type: WidthType.DXA }, columnWidths: anchos, layout: TableLayoutType.FIXED,
    rows: filas.map((fila, i) => new TableRow({
      tableHeader: i === 0, cantSplit: true,
      children: fila.map((c, j) => new TableCell({
        width: { size: anchos[j], type: WidthType.DXA }, borders: bordes, verticalAlign: VerticalAlign.CENTER,
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        shading: i === 0 ? { fill: AZUL_CLARO, type: ShadingType.CLEAR, color: "auto" } : undefined,
        children: [new Paragraph({ spacing: { after: 0, line: 252 },
          children: enLinea(i > 0 && /^(✅|❌)/.test(c) ? mayusInicial(limpiar(c)) : c, { size: 19, ...(i === 0 ? { bold: true } : {}) }) })],
      })),
    })),
  });
}

function nota(lineas) {
  return new Paragraph({
    children: enLinea(lineas.join(" "), { size: 20 }),
    spacing: { before: 120, after: 160, line: 264 }, indent: { left: 284, right: 284 },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color: "C9A227", space: 8 } },
    shading: { fill: "FBF6E7", type: ShadingType.CLEAR, color: "auto" },
  });
}

function firmas() {
  const linea = (nombre, cargo) => new TableCell({
    width: { size: ANCHO / 2, type: WidthType.DXA },
    borders: { top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" } },
    margins: { top: 900, bottom: 200, left: 300, right: 300 },
    children: nombre ? [
      new Paragraph({ alignment: AlignmentType.CENTER, border: { top: { style: BorderStyle.SINGLE, size: 6, color: "000000", space: 4 } },
        children: [new TextRun({ text: nombre, font: FUENTE, bold: true, size: 20 })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: cargo, font: FUENTE, size: 19, color: GRIS })] }),
    ] : [new Paragraph("")],
  });
  return new Table({
    width: { size: ANCHO, type: WidthType.DXA }, columnWidths: [ANCHO / 2, ANCHO / 2],
    rows: [
      new TableRow({ cantSplit: true, children: [linea("Luis Adrian Flores Bueno", "Prestador · No. de control 22460736"),
        linea("Andros Jair Toscano Farias", "Prestador · No. de control 22460548")] }),
      new TableRow({ cantSplit: true, children: [linea("Armando Gaytan Godinez", "Asesor responsable"), linea("", "")] }),
    ],
  });
}

// ---------------------------------------------------------------- conversion
function convertir(md) {
  const lineas = md.split("\n");
  const inicio = lineas.findIndex((l) => l.startsWith("## 1. Datos generales"));
  const salida = [];
  const titulos = [];
  let i = inicio, diagrama = 0;
  while (i < lineas.length) {
    const l = lineas[i];
    if (/^\s*$/.test(l) || /^---\s*$/.test(l)) { i++; continue; }
    // Encabezados
    let m = /^(#{2,4})\s+(.*)$/.exec(l);
    if (m) {
      const nivel = m[1].length, texto = limpiar(m[2]).replace(/`/g, "");
      if (texto === "Firmas") {
        salida.push(new Paragraph({ children: [new PageBreak()] }));
      }
      const heading = nivel === 2 ? HeadingLevel.HEADING_1 : nivel === 3 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3;
      if (nivel === 2 && !texto.startsWith("1.") && texto !== "Firmas") {
        salida.push(new Paragraph({ children: [new PageBreak()] }));
      }
      salida.push(new Paragraph({ heading, children: [new TextRun({ text: texto, font: FUENTE })], keepNext: true }));
      if (nivel <= 3) titulos.push({ nivel, texto });
      if (texto === "Firmas") {
        i++;
        while (i < lineas.length && !lineas[i].startsWith("|")) {
          if (lineas[i].trim()) salida.push(parrafo(lineas[i].trim(), { p: { spacing: { before: 240, after: 240 } } }));
          i++;
        }
        while (i < lineas.length && lineas[i].startsWith("|")) i++;
        salida.push(firmas());
        continue;
      }
      i++; continue;
    }
    // Bloque de codigo (mermaid -> imagen)
    if (l.startsWith("```")) {
      const lenguaje = l.slice(3).trim();
      let j = i + 1; while (j < lineas.length && !lineas[j].startsWith("```")) j++;
      if (lenguaje === "mermaid") {
        diagrama++;
        const pies = { 1: "Diagrama 1. Arquitectura en tres capas: la PC y el robot, con el Robot Server como única frontera HTTP ↔ ROS.",
                       2: "Diagrama 2. Opción A: la profundidad de la Astra Pro como segunda fuente del costmap, sin tocar /scan." };
        figura(path.join(IMG, "diagrama-" + diagrama + ".png"), pies[diagrama], diagrama === 1 ? 10 : 15.5, 11).forEach((p) => salida.push(p));
      } else {
        lineas.slice(i + 1, j).forEach((c) => salida.push(new Paragraph({ children: [new TextRun({ text: c, font: "Consolas", size: 18 })], spacing: { after: 0 } })));
      }
      i = j + 1; continue;
    }
    // Tabla
    if (l.startsWith("|")) {
      const bloque = [];
      while (i < lineas.length && lineas[i].startsWith("|")) { bloque.push(lineas[i]); i++; }
      const filas = bloque.filter((b) => !/^\|\s*:?-{2,}/.test(b)).map(celdasDe);
      if (bloque.some((b) => b.includes("!["))) {
        // Tabla de figuras: imagen en una fila, pie en la siguiente
        let n = 0;
        for (let f = 0; f < filas.length; f++) {
          filas[f].forEach((c, k) => {
            const im = /!\[[^\]]*\]\(([^)]+)\)/.exec(c);
            if (im) {
              const pie = (filas[f + 1] && filas[f + 1][k] || "").replace(/^\*|\*$/g, "");
              figura(rutaImagen(im[1]), pie).forEach((p) => salida.push(p));
              n++;
            }
          });
        }
        continue;
      }
      if (filas.length && filas[0].every((c) => c === "")) filas.shift();
      salida.push(tabla(filas));
      salida.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
      continue;
    }
    // Nota (blockquote)
    if (l.startsWith(">")) {
      const bloque = [];
      while (i < lineas.length && lineas[i].startsWith(">")) { bloque.push(lineas[i].replace(/^>\s?/, "")); i++; }
      salida.push(nota(bloque));
      continue;
    }
    // Listas
    m = /^(\s*)(-|\d+\.)\s+(.*)$/.exec(l);
    if (m) {
      const numerada = m[2] !== "-";
      listaId++;
      const ref = numerada ? "numerada" : "vinetas";
      while (i < lineas.length) {
        const mm = /^(\s*)(-|\d+\.)\s+(.*)$/.exec(lineas[i]);
        if (!mm) break;
        let texto = mm[3]; i++;
        while (i < lineas.length && /^\s{2,}\S/.test(lineas[i]) && !/^\s*(-|\d+\.)\s/.test(lineas[i])) { texto += " " + lineas[i].trim(); i++; }
        salida.push(new Paragraph({ children: enLinea(texto), numbering: { reference: ref, level: 0, instance: listaId },
          spacing: { after: 80, line: 276 } }));
      }
      salida.push(new Paragraph({ spacing: { after: 60 }, children: [] }));
      continue;
    }
    // Parrafo
    const texto = [];
    while (i < lineas.length && lineas[i].trim() && !/^(#|```|\||>|\s*(-|\d+\.)\s)/.test(lineas[i]) && !/^---\s*$/.test(lineas[i])) {
      texto.push(lineas[i].trim()); i++;
    }
    const unido = texto.join(" ");
    // Un parrafo que presenta lo siguiente (termina en ':') no se queda solo al pie de pagina
    salida.push(parrafo(unido, /:\**\s*$/.test(unido) ? { p: { keepNext: true } } : {}));
  }
  return { salida, titulos };
}

// ---------------------------------------------------------------- portada e indice
function portada(subtitulo) {
  const c = (t, o = {}) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: o.after ?? 80, before: o.before ?? 0 },
    children: [new TextRun({ text: t, font: FUENTE, size: o.size || 24, bold: o.bold, color: o.color || "000000", italics: o.italics })] });
  return [
    c("Tecnológico Nacional de México", { size: 28, bold: true, color: AZUL, before: 600 }),
    c("Instituto Tecnológico de Colima", { size: 26, bold: true, color: AZUL }),
    c("Departamento de Ingeniería Eléctrica y Electrónica", { size: 22 }),
    c("Ingeniería Mecatrónica · Especialidad en Sistemas Mecatrónicos Inteligentes", { size: 22, after: 1400 }),
    c("REPORTE TÉCNICO FINAL", { size: 30, bold: true, color: AZUL, after: 120 }),
    c("Servicio Social en Investigación Tecnológica", { size: 24, italics: true, after: 600 }),
    c(subtitulo, { size: 30, bold: true, after: 1400 }),
    c("Prestadores", { size: 20, bold: true, color: GRIS, after: 40 }),
    c("Luis Adrian Flores Bueno · No. de control 22460736", { size: 24 }),
    c("Andros Jair Toscano Farias · No. de control 22460548", { size: 24, after: 360 }),
    c("Asesor responsable", { size: 20, bold: true, color: GRIS, after: 40 }),
    c("Armando Gaytan Godinez", { size: 24, after: 360 }),
    c("Periodo: marzo a septiembre de 2026", { size: 22, after: 1000 }),
    c("Colima, Colima · octubre de 2026", { size: 22 }),
  ];
}

function indice(titulos) {
  const out = [new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: "Índice", font: FUENTE })] })];
  titulos.forEach((t) => {
    const pagina = PAGINAS[t.texto];
    out.push(new Paragraph({
      spacing: { after: t.nivel === 2 ? 60 : 20, before: t.nivel === 2 ? 100 : 0 },
      indent: { left: t.nivel === 2 ? 0 : 440 },
      tabStops: [{ type: TabStopType.RIGHT, position: ANCHO, leader: "dot" }],
      children: [new TextRun({ text: t.texto, font: FUENTE, size: t.nivel === 2 ? 21 : 20, bold: t.nivel === 2 }),
        ...(pagina ? [new TextRun({ text: "\t" + pagina, font: FUENTE, size: 20 })] : [])],
    }));
  });
  return out;
}

// ---------------------------------------------------------------- documento
const md = fs.readFileSync(MD, "utf8");
const subtitulo = (/^###\s+(.*)$/m.exec(md) || [, ""])[1];
const { salida, titulos } = convertir(md);

const doc = new Document({
  creator: "Luis Adrian Flores Bueno; Andros Jair Toscano Farias",
  title: "Reporte técnico final — SafeVision",
  description: subtitulo,
  styles: {
    default: { document: { run: { font: FUENTE, size: 21 } } },
    paragraphStyles: [
      { id: "PiePagina", name: "Pie de pagina SafeVision", basedOn: "Normal", run: { size: 17, color: GRIS, font: FUENTE } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: FUENTE, color: AZUL }, paragraph: { spacing: { before: 240, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 25, bold: true, font: FUENTE, color: AZUL }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: FUENTE, color: "2F5496" }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: "vinetas", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 567, hanging: 283 } } } }] },
    { reference: "numerada", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 567, hanging: 340 } } } }] },
  ] },
  sections: [
    { properties: { page: { size: PAGINA, margin: { top: MARGEN, bottom: MARGEN, left: MARGEN, right: MARGEN } } },
      children: portada(subtitulo) },
    { properties: { page: { size: PAGINA, margin: { top: MARGEN, bottom: MARGEN, left: MARGEN, right: MARGEN },
        pageNumbers: { start: 1 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF", space: 4 } },
        children: [new TextRun({ text: "SafeVision · Reporte técnico final de Servicio Social", font: FUENTE, size: 17, color: GRIS })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, style: "PiePagina",
        children: [new TextRun({ children: ["Página ", PageNumber.CURRENT], font: FUENTE, size: 17, color: GRIS })] })] }) },
      children: [...indice(titulos), new Paragraph({ children: [new PageBreak()] }), ...salida] },
  ],
});

fs.mkdirSync(path.dirname(SALIDA), { recursive: true });
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(SALIDA, buf);
  fs.writeFileSync(path.join(__dirname, "titulos.json"), JSON.stringify(titulos.map((t) => t.texto), null, 1));
  console.log("Escrito", path.relative(RAIZ, SALIDA), "-", titulos.length, "titulos en el indice");
});
