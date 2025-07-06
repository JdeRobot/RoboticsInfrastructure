# Creating Custom Worlds and Circuits in Blender

## Download and Install the GIS Addon

First, you need to download and install the **GIS Addon** in Blender. To do so:

1. Go to the official GitHub repository of the addon.
2. Navigate to the **Releases** section and download the `.zip` file.
3. **Do not unzip** the `.zip` file.

In Blender:

1. Go to `Edit -> Preferences -> Add-ons -> Install`.
2. Select the downloaded `.zip` file.

---

## Creating the Terrain

1. Open the **GIS** menu (toolbar in the viewport).
2. Go to: `GIS -> Web Geodata -> Basemap`.
3. Choose `Google`, then `Satellite`, and click **OK**.
4. A world map will appear, where you can select the desired area.  
   > It's recommended to keep the terrain under **5 km** in both width and height.
5. Press **B** to make a precise selection of the area.
6. Press **E** to delete the rest of the terrain.

---

## Adding Elevation

1. With the terrain selected, go to the **GIS** menu and choose `Get elevation`.
2. Select the source **Marine-geo.org GMRT**.
3. This will apply elevation to the terrain using modifiers.

> Apply the modifiers **from bottom to top** to convert the terrain into a mesh.

To increase mesh resolution:

- Add a **Subdivision** modifier.
- Adjust it until the size of the terrain blocks is about twice the width of the road or less.

---

## Creating the Road

1. Create a **Path-type curve** at the starting point of the track.
2. Enable **Face Project** in the snapping tool so the curve conforms to the terrain. Move the curve closer to the terrain if needed.
3. Switch to **Edit Mode** and start adding and adjusting curve points to follow the desired track layout.
4. In the `Object Data Properties` panel:
   - Set `Twist Method` to **Z-Up**.
5. Disable snapping once you're done.

---

## Option 1: Road on Top of Terrain

1. Create a **generic block** to represent the asphalt.  
   > If you want guardrails along the track, include them in this block.

   - The block width should match the road width.
   - The length can be roughly half the width.

2. Place this block at the starting point of the track.
3. Add the following **modifiers** to the block:
   - **Array**: To duplicate the block along the path.
   - **Curve**: To make the block follow the curve.
   - **Solidify**: To give thickness to the asphalt.

   Make sure to:
   - Enable **Merge** in the Array modifier.
   - Assign the curve to the **Curve** modifier.

4. Adjust the curve to avoid floating or sunken areas.
5. Apply the modifiers and texture the road as desired.

---

## Option 2: Road Included in the Terrain

> This method creates a single mesh but may result in **N-gons** (polygons with more than 4 sides).

1. Follow the initial block creation steps, **without adding Solidify**.
2. Save the **Z-coordinate** of the road block.
3. Slightly elevate the road so it sits completely above the terrain.
4. Select the terrain and enter **Edit Mode**.
5. In **Top View**:
   - Click on the road object.
   - In the `Mesh` menu, use **Knife Project**.

6. In the `Vertex Groups` section:
   - Create a new group and assign the projected selection to it.
7. Deselect the road using `Ctrl + Click` and press `Delete` to remove the faces.
8. Return to **Object Mode** and move the road back to its original Z-coordinate.

9. Add a **Shrinkwrap** modifier to the road:
   - `Target`: The terrain mesh.
   - `Vertex Group`: The group you created.
   - `Wrap Method`: **Nearest Vertex**.

10. Apply the modifiers and texture the road as desired.

---

## Final Notes

- Save copies of your project before applying important modifiers.
- You can export the track for use in engines like Unity or simulators like Gazebo.

---

## Useful Links

- [Blender GIS Addon (GitHub)](https://github.com/domlysz/BlenderGIS)
- [Marine Geoscience Data System (GMRT)](https://www.marine-geo.org/tools/maps_grids.php)