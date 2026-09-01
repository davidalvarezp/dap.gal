---
title: Generador de contraseñas seguras
description: Genera contraseñas aleatorias y seguras directamente en tu navegador. Sin subir ni almacenar tus contraseñas.
tags:
  - passwords
  - security
  - local-first
  - ciberseguridad
---

# Generador de contraseñas

Genera contraseñas aleatorias **directamente en tu navegador**.

<div class="tool-shell" id="password-generator" markdown>

<div class="tool-badge">🔒 LOCAL-FIRST · SIN SUBIDA DE DATOS</div>

<div class="tool-output">
  <label for="pg-output">Contraseña generada</label>
  <div class="tool-output-row">
    <input id="pg-output" class="tool-input tool-input--mono" type="text" readonly autocomplete="off" spellcheck="false" aria-label="Contraseña generada">
    <button class="tool-button tool-button--secondary" type="button" data-pg-copy>Copiar</button>
    <button class="tool-button" type="button" data-pg-generate>Generar</button>
  </div>
  <div class="tool-strength"><span data-pg-strength>—</span><span data-pg-entropy>—</span></div>
</div>

<div class="tool-controls">
  <div class="tool-control">
    <label for="pg-length">Longitud <output id="pg-length-value">24</output></label>
    <input id="pg-length" type="range" min="8" max="128" value="24">
  </div>

  <label class="tool-check"><input id="pg-upper" type="checkbox" checked> Mayúsculas</label>
  <label class="tool-check"><input id="pg-lower" type="checkbox" checked> Minúsculas</label>
  <label class="tool-check"><input id="pg-numbers" type="checkbox" checked> Números</label>
  <label class="tool-check"><input id="pg-symbols" type="checkbox" checked> Símbolos</label>
  <label class="tool-check"><input id="pg-ambiguous" type="checkbox"> Excluir caracteres ambiguos</label>
</div>

<div class="tool-note" data-pg-error role="status" aria-live="polite"></div>

</div>

## Seguridad

La generación utiliza la API criptográfica del navegador (`crypto.getRandomValues`) para obtener valores aleatorios de alta calidad. La contraseña se genera en memoria en tu navegador y esta página no necesita enviarla a un servidor.

> **Consejo:** una contraseña generada aquí no debe reutilizarse entre servicios. Para credenciales críticas, considera además utilizar un gestor de contraseñas.
