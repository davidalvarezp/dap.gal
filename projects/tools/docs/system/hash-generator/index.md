---
title: Hash Generator — SHA-256, SHA-384 y SHA-512
description: Calcula hashes SHA-256, SHA-384 y SHA-512 de texto o archivos directamente en tu navegador.
tags:
  - hashes
  - sha256
  - sha512
  - sysadmin
  - local-first
---

# Hash Generator

Calcula hashes criptográficos de **texto o archivos** sin subir los datos a un servidor.

<div class="tool-shell" id="hash-generator" markdown>

<div class="tool-badge">🔒 LOCAL-FIRST · PROCESAMIENTO EN TU NAVEGADOR</div>

<div class="tool-tabs" role="tablist">
  <button class="tool-tab is-active" type="button" data-hash-mode="text">Texto</button>
  <button class="tool-tab" type="button" data-hash-mode="file">Archivo</button>
</div>

<div data-hash-panel="text">
  <label for="hash-text">Texto</label>
  <textarea id="hash-text" class="tool-input tool-input--textarea" rows="7" placeholder="Introduce el texto que quieres resumir..."></textarea>
</div>

<div data-hash-panel="file" hidden>
  <label for="hash-file">Archivo</label>
  <input id="hash-file" class="tool-file" type="file">
  <div class="tool-file-info" data-hash-file-info></div>
</div>

<div class="tool-controls">
  <label for="hash-algorithm">Algoritmo</label>
  <select id="hash-algorithm" class="tool-select">
    <option value="SHA-256">SHA-256</option>
    <option value="SHA-384">SHA-384</option>
    <option value="SHA-512">SHA-512</option>
  </select>
  <button class="tool-button" type="button" data-hash-calculate>Calcular hash</button>
</div>

<div class="tool-output">
  <label for="hash-output">Resultado</label>
  <div class="tool-output-row">
    <input id="hash-output" class="tool-input tool-input--mono" type="text" readonly spellcheck="false">
    <button class="tool-button tool-button--secondary" type="button" data-hash-copy>Copiar</button>
  </div>
</div>

<div class="tool-note" data-hash-status role="status" aria-live="polite"></div>

</div>

## Uso

- **SHA-256** es una opción general para integridad y comprobaciones de archivos.
- **SHA-384** y **SHA-512** ofrecen hashes más largos.
- El cálculo se realiza con la API Web Crypto del navegador.

> Esta herramienta no implementa MD5. MD5 no debe utilizarse para nuevos diseños criptográficos.
