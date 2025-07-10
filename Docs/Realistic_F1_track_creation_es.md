# Creación de mundos y circuitos personalizados en Blender

## Descarga e instalación del addon GIS

Lo primero será descargar e instalar el **GIS Addon** en Blender. Para ello:

1. Accede al repositorio oficial de GitHub del addon.
2. Dirígete al apartado **Releases** y descarga el archivo `.zip`.
3. **No descomprimas** el `.zip`.

En Blender:

1. Ve a `Edit -> Preferences -> Add-ons -> Install`.
2. Selecciona el archivo `.zip` descargado.

---

## Creación del plano

1. Abre el menú **GIS** (barra de herramientas del viewport).
2. Navega a: `GIS -> Web Geodata -> Basemap`.
3. Selecciona `Google` y luego `Satellite`, y haz clic en **OK**.
4. Aparecerá un mapa del mundo donde podrás ubicarte en la zona deseada.  
   > Se recomienda que el terreno no supere los **5 km** de largo y ancho.
5. Usa la tecla **B** para hacer una selección precisa del área.
6. Usa la tecla **E** para eliminar el resto del plano.

---

## Añadir elevación

1. Con el plano seleccionado, en el menú **GIS**, elige `Get elevation`.
2. Selecciona la fuente **Marine-geo.org GMRT**.
3. Esto aplicará elevación al plano mediante modificadores.

> Aplica los modificadores **de abajo hacia arriba** para convertir el plano en una malla.

Para mejorar la resolución (aumentar la cantidad de malla):

- Añade un modificador de **Subdivision**.
- Ajusta hasta que el tamaño de los bloques sea el doble del ancho de la carretera o menos.

---

## Creación de la carretera

1. Crea una **curva tipo Path** en el inicio del circuito.
2. Activa **Face Project** en el imán para que la curva se adapte al terreno acercando la curva a la carretera si es necesario.
3. Pasa a **Edit Mode** y comienza a añadir y ajustar los puntos de la curva siguiendo el trazado.
4. En el menú `Object Data Properties`:
   - Cambia `Twist Method` a **Z-Up**.
5. Desactiva el imán una vez finalices.

---

## Opción 1: Trazado por encima del plano

1. Crea un **bloque genérico** que represente el asfalto.  
   > Si quieres añadir guardarraíles, inclúyelos aquí.

   - El ancho del bloque debe coincidir con el del circuito.
   - La longitud puede ser aproximadamente la mitad del ancho.

2. Coloca este bloque en el primer punto del circuito.
3. Añade los siguientes **modificadores** al bloque:
   - **Array**: Para repetir el bloque.
   - **Curve**: Para seguir la curva del circuito.
   - **Solidify**: Para darle grosor.

   Asegúrate de:
   - Activar **Merge** en Array.
   - Asignar la curva en el modificador **Curve**.

4. Ajusta la curva para evitar zonas flotantes o sumergidas en el terreno.
5. Aplica los modificadores y texturiza a tu gusto.

---

## Opción 2: Trazado incluido en el plano

> Este método genera una malla única, pero puede introducir **N-gons** (caras con más de 4 lados).

1. Sigue los pasos iniciales de creación del bloque, **sin añadir Solidify**.
2. Guarda la **coordenada Z** del bloque del circuito.
3. Eleva levemente el circuito hasta que esté completamente por encima del terreno.
4. Selecciona el plano del terreno y entra en **Edit Mode**.
5. Desde la vista superior (`Top View`):
   - Haz clic sobre el objeto de la carretera.
   - En el menú `Mesh`, haz un **Knife Project**.

6. En `Vertex Groups`:
   - Crea un nuevo grupo y asigna la selección proyectada.
7. Deselecciona la carretera con `Ctrl + Click` y pulsa `Delete` para eliminar las caras.
8. Vuelve a **Object Mode** y devuelve el circuito a su coordenada Z original.

9. Añade un modificador **Shrinkwrap** al circuito:
   - `Target`: El plano del terreno.
   - `Vertex Group`: El grupo que creaste.
   - `Wrap Method`: **Nearest Vertex**.

10. Aplica los modificadores y texturiza el circuito a tu gusto.

---

## Notas Finales

- Guarda copias del proyecto antes de aplicar modificadores importantes.
- Puedes exportar el circuito para usarlo en motores como Unity o simuladores como Gazebo.

---

## Links útiles

- [Blender GIS Addon (GitHub)](https://github.com/domlysz/BlenderGIS)
- [Marine Geoscience Data System (GMRT)](https://www.marine-geo.org/tools/maps_grids.php)