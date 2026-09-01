/* dap.gal/tools — local-first tools */
(() => {
  const enc = new TextEncoder();

  const escapeHtml = (value) =>
    String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");

  const setStatus = (el, text, type = "") => {
    if (!el) return;
    el.textContent = text;
    el.classList.remove("is-error", "is-success");
    if (type) el.classList.add(`is-${type}`);
  };

  const copyText = async (text) => {
    if (!text) return false;
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
    return false;
  };

  function initPasswordGenerator() {
    const root = document.querySelector("#password-generator");
    if (!root || root.dataset.initialized) return;
    root.dataset.initialized = "1";

    const output = root.querySelector("#pg-output");
    const length = root.querySelector("#pg-length");
    const lengthValue = root.querySelector("#pg-length-value");
    const upper = root.querySelector("#pg-upper");
    const lower = root.querySelector("#pg-lower");
    const numbers = root.querySelector("#pg-numbers");
    const symbols = root.querySelector("#pg-symbols");
    const ambiguous = root.querySelector("#pg-ambiguous");
    const strength = root.querySelector("[data-pg-strength]");
    const entropy = root.querySelector("[data-pg-entropy]");
    const error = root.querySelector("[data-pg-error]");

    const sets = {
      upper: "ABCDEFGHJKLMNPQRSTUVWXYZ",
      lower: "abcdefghijkmnopqrstuvwxyz",
      numbers: "23456789",
      symbols: "!#$%&()*+,-./:;=?@[]^_{|}~"
    };

    const randomInt = (max) => {
      const limit = Math.floor(0x100000000 / max) * max;
      const buf = new Uint32Array(1);
      let n;
      do {
        crypto.getRandomValues(buf);
        n = buf[0];
      } while (n >= limit);
      return n % max;
    };

    const generate = () => {
      const selected = [];
      if (upper.checked) selected.push(sets.upper);
      if (lower.checked) selected.push(sets.lower);
      if (numbers.checked) selected.push(sets.numbers);
      if (symbols.checked) selected.push(sets.symbols);

      if (!selected.length) {
        output.value = "";
        setStatus(error, "Selecciona al menos un conjunto de caracteres.", "error");
        return;
      }

      const all = selected.join("");
      const targetLength = Number(length.value);
      const chars = [];

      selected.forEach((set) => chars.push(set[randomInt(set.length)]));
      while (chars.length < targetLength) {
        chars.push(all[randomInt(all.length)]);
      }

      // Fisher-Yates con fuente criptográfica.
      for (let i = chars.length - 1; i > 0; i--) {
        const j = randomInt(i + 1);
        [chars[i], chars[j]] = [chars[j], chars[i]];
      }

      output.value = chars.join("");
      const bits = Math.floor(targetLength * Math.log2(all.length));
      entropy.textContent = `~${bits} bits de entropía`;
      strength.textContent =
        bits >= 100 ? "Muy fuerte" :
        bits >= 70 ? "Fuerte" :
        bits >= 50 ? "Moderada" : "Débil";
      setStatus(error, "", "");
    };

    const updateLength = () => {
      lengthValue.textContent = length.value;
      generate();
    };

    length.addEventListener("input", updateLength);
    [upper, lower, numbers, symbols, ambiguous].forEach((el) =>
      el.addEventListener("change", generate)
    );

    root.querySelector("[data-pg-generate]")?.addEventListener("click", generate);
    root.querySelector("[data-pg-copy]")?.addEventListener("click", async (event) => {
      try {
        await copyText(output.value);
        const button = event.currentTarget;
        const original = button.textContent;
        button.textContent = "Copiado";
        setTimeout(() => (button.textContent = original), 1200);
      } catch {
        setStatus(error, "No se pudo copiar. Copia el valor manualmente.", "error");
      }
    });

    // Reaplica la opción de ambiguos sin penalizar la legibilidad del código.
    ambiguous.addEventListener("change", () => {
      const remove = "0O1Il|`'\"";
      Object.keys(sets).forEach((key) => {
        if (!sets[key].__original) sets[key].__original = sets[key];
        sets[key] = ambiguous.checked
          ? sets[key].replaceAll(/[0O1Il|`'"]/g, "")
          : sets[key].__original;
      });
      generate();
    });

    generate();
  }

  async function digestFile(file, algorithm) {
    const buffer = await file.arrayBuffer();
    const digest = await crypto.subtle.digest(algorithm, buffer);
    return [...new Uint8Array(digest)]
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }

  function initHashGenerator() {
    const root = document.querySelector("#hash-generator");
    if (!root || root.dataset.initialized) return;
    root.dataset.initialized = "1";

    const textPanel = root.querySelector('[data-hash-panel="text"]');
    const filePanel = root.querySelector('[data-hash-panel="file"]');
    const text = root.querySelector("#hash-text");
    const file = root.querySelector("#hash-file");
    const algorithm = root.querySelector("#hash-algorithm");
    const output = root.querySelector("#hash-output");
    const status = root.querySelector("[data-hash-status]");
    const fileInfo = root.querySelector("[data-hash-file-info]");
    const calculate = root.querySelector("[data-hash-calculate]");
    let mode = "text";

    root.querySelectorAll("[data-hash-mode]").forEach((button) => {
      button.addEventListener("click", () => {
        mode = button.dataset.hashMode;
        root.querySelectorAll("[data-hash-mode]").forEach((b) =>
          b.classList.toggle("is-active", b === button)
        );
        textPanel.hidden = mode !== "text";
        filePanel.hidden = mode !== "file";
        output.value = "";
        setStatus(status, "");
      });
    });

    file.addEventListener("change", () => {
      const selected = file.files?.[0];
      fileInfo.textContent = selected
        ? `${selected.name} · ${selected.type || "tipo desconocido"} · ${selected.size.toLocaleString("es-ES")} bytes`
        : "";
    });

    calculate.addEventListener("click", async () => {
      try {
        setStatus(status, "Calculando...");
        calculate.disabled = true;

        let data;
        if (mode === "text") {
          data = enc.encode(text.value);
        } else {
          const selected = file.files?.[0];
          if (!selected) throw new Error("Selecciona un archivo.");
          data = await selected.arrayBuffer();
        }

        const digest = await crypto.subtle.digest(algorithm.value, data);
        output.value = [...new Uint8Array(digest)]
          .map((b) => b.toString(16).padStart(2, "0"))
          .join("");

        setStatus(status, `${algorithm.value} calculado localmente.`, "success");
      } catch (err) {
        output.value = "";
        setStatus(status, err.message || "No se pudo calcular el hash.", "error");
      } finally {
        calculate.disabled = false;
      }
    });

    root.querySelector("[data-hash-copy]")?.addEventListener("click", async (event) => {
      try {
        await copyText(output.value);
        const button = event.currentTarget;
        const original = button.textContent;
        button.textContent = "Copiado";
        setTimeout(() => (button.textContent = original), 1200);
      } catch {
        setStatus(status, "No se pudo copiar el resultado.", "error");
      }
    });
  }

  const formatBytes = (bytes) => {
    if (!Number.isFinite(bytes)) return "—";
    if (bytes < 1024) return `${bytes} B`;
    const units = ["KiB", "MiB", "GiB", "TiB"];
    let value = bytes;
    let i = -1;
    do {
      value /= 1024;
      i++;
    } while (value >= 1024 && i < units.length - 1);
    return `${value.toFixed(value >= 10 ? 1 : 2)} ${units[i]}`;
  };

  const jpegExif = async (file) => {
    const buffer = await file.arrayBuffer();
    const view = new DataView(buffer);
    if (view.byteLength < 4 || view.getUint16(0) !== 0xffd8) return {};

    let offset = 2;
    while (offset + 4 <= view.byteLength) {
      if (view.getUint8(offset) !== 0xff) break;
      const marker = view.getUint8(offset + 1);
      const size = view.getUint16(offset + 2);
      if (marker === 0xe1 && size >= 8) {
        const exifStart = offset + 4;
        const header = new TextDecoder().decode(
          new Uint8Array(buffer, exifStart, 6)
        );
        if (header !== "Exif\u0000\u0000") return {};
        const tiff = exifStart + 6;
        const endian = view.getUint16(tiff);
        const little = endian === 0x4949;
        const u16 = (p) => view.getUint16(p, little);
        const u32 = (p) => view.getUint32(p, little);
        const ifdOffset = tiff + u32(tiff + 4);
        if (ifdOffset + 2 > view.byteLength) return {};

        const tags = {
          0x010f: "Make",
          0x0110: "Model",
          0x0131: "Software",
          0x0132: "DateTime",
          0x0112: "Orientation"
        };

        const values = {};
        const count = u16(ifdOffset);
        for (let i = 0; i < count; i++) {
          const p = ifdOffset + 2 + i * 12;
          if (p + 12 > view.byteLength) break;
          const tag = u16(p);
          if (!tags[tag]) continue;
          const type = u16(p + 2);
          const n = u32(p + 4);
          const bytes = type === 2 ? n : type === 3 ? 2 * n : type === 4 ? 4 * n : 0;
          let dataOffset = bytes <= 4 ? p + 8 : tiff + u32(p + 8);
          if (dataOffset + Math.min(bytes || 2, 256) > view.byteLength) continue;

          if (type === 2) {
            values[tags[tag]] = new TextDecoder()
              .decode(new Uint8Array(buffer, dataOffset, Math.max(0, n - 1)))
              .replace(/\0/g, "");
          } else if (type === 3 && n === 1) {
            values[tags[tag]] = u16(dataOffset);
          } else if (type === 4 && n === 1) {
            values[tags[tag]] = u32(dataOffset);
          }
        }
        return values;
      }
      if (marker === 0xda || marker === 0xd9) break;
      offset += 2 + size;
    }
    return {};
  };

  const pngText = async (file) => {
    const buffer = await file.arrayBuffer();
    const view = new DataView(buffer);
    const signature = [137, 80, 78, 71, 13, 10, 26, 10];
    if (view.byteLength < 33 || !signature.every((v, i) => view.getUint8(i) === v)) return {};
    let offset = 8;
    const result = {};
    const decoder = new TextDecoder();
    while (offset + 12 <= view.byteLength) {
      const length = view.getUint32(offset);
      const type = decoder.decode(new Uint8Array(buffer, offset + 4, 4));
      if (offset + 12 + length > view.byteLength) break;
      if (type === "tEXt" || type === "iTXt") {
        const data = new Uint8Array(buffer, offset + 8, length);
        const text = decoder.decode(data);
        result[type] = (result[type] || []);
        result[type].push(text.slice(0, 500));
      }
      offset += 12 + length;
      if (type === "IEND") break;
    }
    return result;
  };

  function initMetadataViewer() {
    const root = document.querySelector("#metadata-viewer");
    if (!root || root.dataset.initialized) return;
    root.dataset.initialized = "1";

    const fileInput = root.querySelector("#mv-file");
    const results = root.querySelector("[data-mv-results]");
    const status = root.querySelector("[data-mv-status]");

    const addRow = (key, value) =>
      `<div class="metadata-key">${escapeHtml(key)}</div><div class="metadata-value">${escapeHtml(value)}</div>`;

    fileInput.addEventListener("change", async () => {
      const file = fileInput.files?.[0];
      if (!file) return;

      setStatus(status, "Leyendo archivo...");
      results.hidden = true;

      const rows = [
        ["Nombre", file.name],
        ["Tipo", file.type || "Desconocido"],
        ["Tamaño", formatBytes(file.size)],
        ["Última modificación", new Date(file.lastModified).toLocaleString("es-ES")]
      ];

      if (file.type.startsWith("image/")) {
        try {
          const bitmap = await createImageBitmap(file);
          rows.push(
            ["Dimensiones", `${bitmap.width} × ${bitmap.height} px`],
            ["Relación de aspecto", (bitmap.width / bitmap.height).toFixed(4)]
          );
          bitmap.close();
        } catch {
          // No todas las imágenes necesitan ser decodificables por createImageBitmap.
        }

        if (file.type === "image/jpeg") {
          const exif = await jpegExif(file);
          Object.entries(exif).forEach(([key, value]) => rows.push([`EXIF · ${key}`, value]));
        }

        if (file.type === "image/png") {
          const text = await pngText(file);
          Object.entries(text).forEach(([key, value]) =>
            rows.push([`PNG · ${key}`, Array.isArray(value) ? value.join(" | ") : value])
          );
        }
      }

      results.innerHTML = rows.map(([k, v]) => addRow(k, v)).join("");
      results.hidden = false;
      setStatus(status, "Procesado localmente en tu navegador.", "success");
    });
  }

  function init() {
    initPasswordGenerator();
    initHashGenerator();
    initMetadataViewer();
  }

  if (window.document$) {
    document$.subscribe(init);
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
