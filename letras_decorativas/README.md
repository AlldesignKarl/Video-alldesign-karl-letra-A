# Letras decorativas · Spot vertical

Anuncio vertical de **20,0 s** (1080×1920, 9:16, 30 fps, H.264 + AAC) para Instagram Reels y TikTok,
creado a partir de las tres fotografías de la letra «A» decorada.

**Archivo final:** [`../Letras_Decorativas_1080x1920.mp4`](../Letras_Decorativas_1080x1920.mp4)

<img src="../portada_letras_decorativas.jpg" width="270" alt="Portada del spot">

## Qué se ha hecho

| Petición | Resultado |
|---|---|
| Usar el producto real, sin inventar ni deformar | La letra se ha recortado de las tres fotos originales (`fotos_originales/`) y es la que se ve en todo momento: misma forma, flores, lunares, lazos de organza y zapatillas de ballet. No se ha generado ninguna parte del producto. Se han quitado el plato dorado, la pared y la mesa de la cocina; los huecos de la «A» (triángulo y abertura entre las patas) se han vaciado para que se vea el fondo nuevo a través de ellos, pero se conservan las flores que asoman por dentro. |
| Recorte de calidad | Segmentación interactiva (MediaPipe) con puntos marcados a mano, refinado con GrabCut y *matting* de forma cerrada (pymatting) en el borde. La organza conserva su transparencia y los bordes no tienen halo del fondo antiguo. Resultado en `recortes/` (PNG RGBA de 16 bits). |
| Cámara alrededor de la letra, lenta y continua | Una única cámara virtual con movimiento continuo (acercamiento tipo *dolly* y deriva lateral de órbita) con paralaje real por profundidad: la pared del fondo se desplaza más que la mesa. En cada vista la letra gira unos grados con perspectiva real (homografía). Entre las tres vistas hay transiciones de **enfoque/desenfoque** de ~1 s durante los planos cercanos, sin cortes ni saltos (verificado fotograma a fotograma). |
| Fondo elegante, cálido y desenfocado | Set de estudio renderizado en 3D (Blender Cycles): pared de estuco rosa empolvado con luz de ventana y sombras de hojas, mesa de travertino crema, jarrón de cerámica con pampas secas, libros en rosa palo y vela. Desenfoque óptico real (f/2,2). Hay dos renders con la altura de cámara de cada foto (la foto 2 está hecha desde más arriba), para que la letra apoye con la perspectiva correcta. |
| Integración | Sombra de contacto y sombra proyectada suave, ajuste de color cálido al set, ligero *light wrap* en los bordes, viñeta y grano fino. |
| Voz en español de España | Locución femenina (síntesis neuronal Kokoro‑82M, voz `ef_dora`, acento castellano: /θ/ en «Mercería» y «dieciséis»), frase a frase con pausas naturales, ecualización, compresión y una sala muy sutil. **Comprobada con reconocimiento de voz (Whisper):** la mezcla final se transcribe palabra por palabra. |
| Música | Composición original para este spot (Re mayor, ~96 bpm): piano suave en arpegios, cuerdas cálidas y arpa al principio y al final. Baja automáticamente bajo la voz y unos 2,5 dB más en la última frase (las tiendas). |
| Mezcla | -14 LUFS integrados, pico -1,1 dBFS (estándar de Instagram/TikTok). |
| Texto | Cormorant Garamond + Montserrat, en tonos rosa oscuro, siempre en la zona superior libre y sin tapar nunca la letra. |

## Guion de la locución (19,3 s de voz)

> Descubre nuestras letras decorativas: un toque especial y único para cualquier espacio.
> Ideales para dormitorios, habitaciones, salones y mucho más.
> Puedes encontrarlas en nuestras tiendas colaboradoras:
> Mercería El Siglo, en Cortes de Aragón, cuarenta y seis,
> y Papelería Casablanca, en calle La Vía, dieciséis.

El guion original duraba unos 22 s con pausas, así que se ha acortado ligeramente sin perder información:
«creadas para dar un toque especial y único a cualquier espacio» → «un toque especial y único para cualquier
espacio»; «Ideales para decorar dormitorios…» → «Ideales para dormitorios…»; «en Calle Cortes de Aragón 46» →
«en Cortes de Aragón, cuarenta y seis». En pantalla la dirección aparece completa.

## Estructura

| Tiempo | Imagen | Texto en pantalla | Voz |
|---|---|---|---|
| 0,0–3,0 s | Letra completa (vista frontal), giro lento y acercamiento suave | LETRAS DECORATIVAS | «Descubre nuestras letras decorativas…» |
| 3,0–5,0 s | Acercamiento a los lunares y a las flores del travesaño; transición de enfoque hacia las zapatillas y los lazos | — | |
| 5,0–9,0 s | Primer plano de zapatillas y organza; la cámara se retira y muestra el volumen y el grosor de la letra en vista lateral | *Artesanales* · *Un detalle único para tu hogar* | «Ideales para dormitorios, habitaciones, salones y mucho más.» |
| 9,0–12,0 s | Transición de enfoque a la cara trasera; recorrido lento por las flores secas | — | «Puedes encontrarlas en nuestras tiendas colaboradoras:» |
| 12,0–14,0 s | La cámara se retira a una vista general de la cara floral | DISPONIBLES EN: · Mercería El Siglo · C. Cortes de Aragón, 46 | «Mercería El Siglo…» |
| 14,0–20,0 s | Plano final limpio, la letra sigue girando muy despacio | + Papelería Casablanca · C. La Vía, 16 | «…y Papelería Casablanca, en calle La Vía, dieciséis.» |

## Notas importantes

- **Voz:** es una voz sintética de alta calidad, no una locutora real. Es la más natural que se podía
  generar en este entorno (los servicios de voz comerciales no estaban accesibles). Si se quiere una voz
  100 % humana, basta con grabar el guion de arriba (dura unos 19 s, empezando en 0,3 s) y sustituir
  `audio/locucion_voz.flac`: la música y la mezcla están separadas y preparadas para ello.
- **Giro alrededor de la letra:** con tres fotos no existe la información de los ángulos intermedios
  (por ejemplo, el lado derecho de la letra no aparece en ninguna foto). Para no inventarlos, cada vista
  real gira solo unos grados y el paso de una vista a otra se hace con una transición de enfoque en los
  planos cercanos, como en los anuncios de producto. Si se graba un vídeo dando una vuelta completa a la
  letra, se puede hacer una órbita continua de 360° real.
- **Música:** composición original creada para este spot, sin derechos de terceros.
- **Fondo:** render 3D fotorrealista, no es una foto de stock.

## Contenido de esta carpeta

- `fotos_originales/`: las tres fotografías de referencia.
- `recortes/`: la letra recortada de cada foto (PNG RGBA 16 bits) y sus coordenadas en la foto original.
- `audio/`: voz procesada, música original (FLAC y MIDI) y mezcla final, todo a 48 kHz.
- `pipeline/`: scripts utilizados (ver abajo).

### Pipeline

1. `mt.py` + `pts.json`: segmentación interactiva por puntos (MediaPipe *magic touch*).
2. `matte.py` + `holes.json`: trimapa (huecos de la «A» marcados como fondo) y *matting* de forma cerrada.
3. `scene2.py`: set 3D en Blender (`python3 scene2.py -- 1685 2304 64 bg14.png 14 beauty`; también a 30° y pases `depth`).
4. `comp.py` + `overlay2.py`: cámara virtual, giro 2.5D, sombras, transiciones, etalonaje y rótulos (`python3 comp.py 0 600`).
5. `voice.py` + `lines.json`: locución (Kokoro‑82M, `ef_dora`). `music2.py`: música (MIDI → FluidSynth, FluidR3_GM). `mix.py`: mezcla a -14 LUFS.
6. `asr.mjs`: comprobación de la locución con Whisper (transformers.js).
