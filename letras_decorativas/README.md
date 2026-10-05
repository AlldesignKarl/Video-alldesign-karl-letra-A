# Letras decorativas · Spot vertical

Anuncio vertical de **20,0 s** (1080×1920, 9:16, 30 fps, H.264 + AAC) para Instagram Reels y TikTok,
creado a partir de las tres fotografías de la letra «A» decorada.

| Versión | Archivo |
|---|---|
| **Giro 360° (principal):** la letra gira sobre sí misma y se ve desde todos los ángulos | [`../Letras_Decorativas_1080x1920.mp4`](../Letras_Decorativas_1080x1920.mp4) |
| Solo fotos: las tres vistas reales con movimiento de cámara y transiciones de enfoque | [`../Letras_Decorativas_fotos_1080x1920.mp4`](../Letras_Decorativas_fotos_1080x1920.mp4) |

<img src="../portada_letras_decorativas.jpg" width="270" alt="Portada del spot">

## Versión 360° (modelo 3D con las fotos)

La letra se ha reconstruido en 3D y gira algo más de una vuelta completa (≈ 35°/s): frente → lado de las
zapatillas (4 s) → cara floral (6,5 s) → lado derecho (9 s) → frente (11,5 s) → zapatillas (14 s) → cierre en
la cara floral a tres cuartos (17,6–20 s). La cámara, la luz y el set son los mismos que en la versión de fotos.

| Parte | De dónde sale |
|---|---|
| Forma de la «A» | Contorno de la foto 1 enderezado (con el hueco triangular y la abertura entre las patas); 20 cm de alto y 4,5 cm de grosor, cantos ligeramente redondeados. |
| Cara frontal (lunares, rayas rojas, flores del travesaño) | **Textura directa de la foto 1**, proyectada sobre la cara. En el borde izquierdo la foto tenía trozos de la zapatilla encima de la raya roja; se ha completado la raya con su propia textura. |
| Cara floral | **Textura directa de la foto 3**, con un mapa de relieve para que las flores tengan volumen al verlas de lado; las flores sobresalen de los bordes como en la foto. |
| Laterales y parte de arriba | Rosa, con el color medido en la foto 2. |
| Paredes interiores de los huecos | Blanco, medido en las fotos. |
| Zapatillas de ballet y lazos de organza | **Modelados en 3D** (raso perlado y organza malva translúcida) para que se puedan ver desde cualquier ángulo, colocados donde están en las fotos. |
| Sombras | Reales del modelo sobre la mesa del set (*shadow catcher* de Cycles). |

**Qué es aproximado:** el lado derecho de la letra no aparece en ninguna foto y se ha supuesto rosa como el
izquierdo. Las zapatillas y los lazos son una recreación (forma, posición y material parecidos a las fotos,
no una copia exacta). El relieve de las flores visto de canto también es aproximado.

## Versión de fotos

| Petición | Resultado |
|---|---|
| Usar el producto real, sin inventar ni deformar | La letra se ha recortado de las tres fotos originales (`fotos_originales/`) y es la que se ve en todo momento: misma forma, flores, lunares, lazos de organza y zapatillas de ballet. No se ha generado ninguna parte del producto. Se han quitado el plato dorado, la pared y la mesa de la cocina; los huecos de la «A» (triángulo y abertura entre las patas) se han vaciado para que se vea el fondo nuevo a través de ellos, pero se conservan las flores que asoman por dentro. |
| Recorte de calidad | Segmentación interactiva (MediaPipe) con puntos marcados a mano, refinado con GrabCut y *matting* de forma cerrada (pymatting) en el borde. La organza conserva su transparencia y los bordes no tienen halo del fondo antiguo. Resultado en `recortes/` (PNG RGBA de 16 bits). |
| Cámara alrededor de la letra, lenta y continua | Una única cámara virtual con movimiento continuo (acercamiento tipo *dolly* y deriva lateral de órbita) con paralaje real por profundidad: la pared del fondo se desplaza más que la mesa. En cada vista la letra gira unos grados con perspectiva real (homografía). Entre las tres vistas hay transiciones de **enfoque/desenfoque** de ~1 s durante los planos cercanos, sin cortes ni saltos (verificado fotograma a fotograma). |
| Fondo elegante, cálido y desenfocado | Set de estudio renderizado en 3D (Blender Cycles): pared de estuco rosa empolvado con luz de ventana y sombras de hojas, mesa de travertino crema, jarrón de cerámica con pampas secas, libros en rosa palo y vela. Desenfoque óptico real (f/2,2). Hay dos renders con la altura de cámara de cada foto (la foto 2 está hecha desde más arriba), para que la letra apoye con la perspectiva correcta. |
| Integración | Sombra de contacto y sombra proyectada suave, ajuste de color cálido al set, ligero *light wrap* en los bordes, viñeta y grano fino. |
| Voz en español de España | Locución femenina (síntesis neuronal Kokoro‑82M, voz `ef_dora`, acento castellano), frase a frase con pausas naturales, ecualización, compresión y una sala muy sutil. La marca se pronuncia como se diría en España, «ol disáin Karl», y «online» como «onláin» (fonemas indicados a mano para que no se lea letra a letra). **Comprobada con reconocimiento de voz (Whisper):** se transcribe «…en nuestra tienda online, alldesignKarl» y «alldesignkarl.com». |
| Música | Composición original para este spot (Re mayor, ~96 bpm): piano suave en arpegios, cuerdas cálidas y arpa al principio y al final. Baja automáticamente bajo la voz y unos 2,5 dB más mientras se dice la web; en el cierre vuelve a subir. |
| Mezcla | -14 LUFS integrados, pico -1,1 dBFS (estándar de Instagram/TikTok). |
| Texto | Cormorant Garamond + Montserrat, en tonos rosa oscuro, siempre en la zona superior libre y sin tapar nunca la letra. |

## Guion de la locución (0,3–16,3 s)

> Descubre nuestras letras decorativas: un toque especial y único para cualquier espacio.
> Ideales para dormitorios, habitaciones, salones y mucho más.
> Puedes encontrarlas en nuestra tienda online, alldesignKarl:
> alldesignkarl punto com.

Las dos primeras frases se acortaron ligeramente respecto al guion original para que el spot no pasara de
20 s («creadas para dar un toque especial y único a cualquier espacio» → «un toque especial y único para
cualquier espacio»; «Ideales para decorar dormitorios…» → «Ideales para dormitorios…»).

## Estructura (versión de fotos)

En la versión 360° la voz, la música y los textos son los mismos y en los mismos tiempos; la imagen es el giro
descrito arriba.

| Tiempo | Imagen | Texto en pantalla | Voz |
|---|---|---|---|
| 0,0–3,0 s | Letra completa (vista frontal), giro lento y acercamiento suave | LETRAS DECORATIVAS | «Descubre nuestras letras decorativas…» |
| 3,0–5,0 s | Acercamiento a los lunares y a las flores del travesaño; transición de enfoque hacia las zapatillas y los lazos | — | |
| 5,0–9,0 s | Primer plano de zapatillas y organza; la cámara se retira y muestra el volumen y el grosor de la letra en vista lateral | *Artesanales* · *Un detalle único para tu hogar* | «Ideales para dormitorios, habitaciones, salones y mucho más.» |
| 9,0–12,0 s | Transición de enfoque a la cara trasera; recorrido lento por las flores secas | — | «Puedes encontrarlas en nuestra tienda online, alldesignKarl:» |
| 12,0–14,0 s | La cámara se retira a una vista general de la cara floral | DISPONIBLES EN: · **alldesignKarl** · TIENDA ONLINE | |
| 14,0–20,0 s | Plano final limpio, la letra sigue girando muy despacio | + **alldesignkarl.com** | «alldesignkarl punto com.» y cierre con música |

## Notas importantes

- **Voz:** es una voz sintética de alta calidad, no una locutora real. Es la más natural que se podía
  generar en este entorno (los servicios de voz comerciales no estaban accesibles). Si se quiere una voz
  100 % humana, basta con grabar el guion de arriba (unos 16 s, empezando en 0,3 s) y sustituir
  `audio/locucion_voz.flac`: la música y la mezcla están separadas y preparadas para ello.
- **Giro 360°:** con tres fotos no existen los ángulos intermedios, así que la versión 360° usa un modelo
  3D con las texturas de las fotos (ver arriba lo que es aproximado). Si se graba un vídeo de la letra dando
  una vuelta completa, se puede hacer un giro con la letra 100 % real en todos los ángulos.
- **Música:** composición original creada para este spot, sin derechos de terceros.
- **Fondo:** render 3D fotorrealista, no es una foto de stock.

## Contenido de esta carpeta

- `fotos_originales/`: las tres fotografías de referencia.
- `recortes/`: la letra recortada de cada foto (PNG RGBA 16 bits) y sus coordenadas en la foto original.
- `audio/`: voz procesada, música original (FLAC y MIDI) y mezcla final, todo a 48 kHz.
- `pipeline/`: scripts utilizados (ver abajo).
- `modelo_3d/`: escena 3D de la letra (`product.py`), contorno (`shape.py`), giro y cámara (`timeline.py`) y texturas sacadas de las fotos.

### Pipeline

1. `mt.py` + `pts.json`: segmentación interactiva por puntos (MediaPipe *magic touch*).
2. `matte.py` + `holes.json`: trimapa (huecos de la «A» marcados como fondo) y *matting* de forma cerrada.
3. `scene2.py`: set 3D en Blender (`python3 scene2.py -- 1685 2304 64 bg14.png 14 beauty`; también a 30° y pases `depth`).
4. `comp.py` + `overlay2.py`: cámara virtual, giro 2.5D, sombras, transiciones, etalonaje y rótulos (`python3 comp.py 0 600`).
5. `voice.py` + `lines.json`: locución (Kokoro‑82M, `ef_dora`). `music2.py`: música (MIDI → FluidSynth, FluidR3_GM). `mix.py`: mezcla a -14 LUFS.
6. `asr.mjs`: comprobación de la locución con Whisper (transformers.js).
7. Versión 360°: `modelo_3d/timeline.py` (ángulo por fotograma y cámara), `modelo_3d/product.py` (render de la letra con Cycles:
   `python3 product.py -- 0 600 8 frames_prod 0.85`) y `pipeline/comp2.py` (composición sobre el set con los mismos rótulos).
