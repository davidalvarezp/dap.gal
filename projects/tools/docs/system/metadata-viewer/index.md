---
title: Metadata Viewer — visor de metadatos de archivos e imágenes
description: Inspecciona metadatos básicos de archivos e imágenes directamente en tu navegador sin subirlos a un servidor.
tags:
  - metadata
  - exif
  - images
  - privacy
  - local-first
---

# Metadata Viewer

Selecciona un archivo para inspeccionar **metadatos básicos localmente en tu navegador**.

<div class="tool-shell" id="metadata-viewer" markdown>

<div class="tool-badge">🔒 LOCAL-FIRST · EL ARCHIVO NO SE SUBE</div>

<label for="mv-file">Seleccionar archivo</label>
<input id="mv-file" class="tool-file" type="file">

<div class="metadata-grid" data-mv-results hidden></div>

<div class="tool-note" data-mv-status role="status" aria-live="polite"></div>

</div>

## Qué muestra

Para cualquier archivo:

- nombre
- tipo MIME
- tamaño
- última modificación

Para imágenes también muestra:

- dimensiones
- relación de aspecto
- información básica disponible en el navegador
- algunos metadatos EXIF de JPEG cuando están presentes
- chunks de texto básicos de PNG cuando están presentes

El archivo se lee localmente mediante las APIs del navegador.
