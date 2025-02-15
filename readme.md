# @aemet-avisa.bot.azeria.dev

Este es el código fuente con el cual está construido este bot para [BlueSky](https://bsky.app/). Puedes encontrar su cuenta en [@aemet-avisa.bot.azeria.dev](https://bsky.app/profile/did:plc:74vcrrzbpvefn46bocozy527).

Esta es la segunda versión del bot, completamente reconstruida en Python, puedes encontrar
el código original, mayormente escrito en TypeScript, en [este repositorio](https://github.com/ArtfulAzeria/aemet-avisa).

## ¿Qué diferencias hay con la versión original?
El repositorio de aemet-avisa-v2 es el resultado de un cambio importante en la aplicación: la construcción del mapa
programáticamente. Mientras que anteriormente se extraían los datos y solo se construía una respuesta en texto con ellos,
en esta versión esos datos son usados también para crear un mapa.

Anteriormente, el mapa era extraído en paralelo a la lectura de los datos haciendo web-scrapping a la web de [AEMET](https://www.aemet.es/es/eltiempo/prediccion/avisos).
Esto daba lugar a un error relativamente inusual, donde había una ligera desincronización en la página de AEMET entre la actualización
de su RSS y de su mapa, llevando con ello a que los posts tuviesen en ocasiones discordancia entre lo escrito en el texto y mostrado en la imagen.

Con esta nueva versión, al construir el mapa programáticamente se evita esa desincronización molesta.

Además, se resuelve otro gran problema, que era la ausencia de las Islas Canarias. Y es que al obtener el mapa
por web-scrapping, y al tener la AEMET en su página los mapas de la peninsula y canarias por separado, se estaba omitiendo
la susodicha parte del territorio español en las imágenes. Esto sucedía a pesar de que los datos meteorológicos eran igualmente recibidos y procesados de forma correcta.

Al crear el mapa en base puramente a los datos y sin scrapping, se puede manipular la imagen tanto como sea necesario. Cambios de colores, texto en el mapa,
recortar la imagen, picture-in-picture... con ello podemos crear el típico mapa de España con un recorte de las islas canarias abajo a la izquierda.

## ¿Cómo funciona?
La aplicación realiza las siguientes tareas, en este orden:
1. Obtiene el XML del Feed RSS oficial de avisos meteorológicos AEMET.
2. Extrae y trata los datos relevantes, creando el texto y la imagen para el post.
3. Publica el resultado en Bluesky.

## ¿Cuál es el formato del mensaje?
El texto siempre se formatea de la siguiente forma:

```md
🔴 Avisos rojos en:
Comunidades, Autónomas, En, Aviso y Rojo.

🟠 Avisos naranjas en:
Comunidades, Autónomas, En, Aviso y Naranja.

🟡 Avisos amarillos en:
Comunidades, Autónomas, En, Aviso y Amarillo.

Para más información acude a aemet.es
```

Si no existen avisos de un tipo (rojo/naranja/amarillo) se salta por completo esa línea.
```md
🟠 Avisos naranjas en:
Comunidades, Autónomas, En, Aviso y Naranja.

🟡 Avisos amarillos en:
Comunidades, Autónomas, En, Aviso y Amarillo.

Para más información acude a aemet.es
```
En caso de que no haya aviso alguno de ningún tipo, el texto dictará:
```md
🟢 Actualmente no hay ningún aviso activo.

Para más información acude a aemet.es
```

Al final del mensaje, siempre se escribe la línea indicando que se puede obtener más información en la web oficial de avisos de la AEMET, con un [enlace a la misma](https://www.aemet.es/es/eltiempo/prediccion/avisos).

## ¿Cómo se extraen los datos?
Se llama al Feed RSS de avisos usando la URI (almacenada en `src/Constant.py`, en `AEMET_RSS`).
Se usa el Feed RSS simplificado, con tan solo la información de las zonas y avisos. 

## ¿Cómo lo ejecuto?
1. Clona el proyecto.
2. Instala las dependencias necesarias (`pip install -r requirements.txt`) 
3. Crea tu archivo `.env` (ver [sample.env](sample.env)).
4. Finalmente ejecuta `src/Main.ts`

## Archivos .geojson
Bajo el directorio `resources/` tenemos los archivos `aemet_zones.geojson` y `spain_communities.geojson`.
Estos contienen respectivamente los `.geojson` para las zonas de avisos de aemet, y para las comunidades
autónomas de España.

- `spain_communities.geojson` es únicamente usado para dibujar las comunidades autónomas sobre el mapa.
- `aemet_zones.geojson` es usado para todo lo demás. Contiene los datos de cuáles son las zonas de aviso, sus
coordenadas, nombres, comunidad autónoma, provincia...