Cat mesh and animations from "Animal Pack Vol.2" by Quaternius,
https://opengameart.org/content/animated-animales-low-poly, released as CC0
(public domain).

Exported from Cat.blend with Blender 3.3: the IK driven legs were baked onto
the deform bones and the IK helper bones removed, because gz cannot load
animation channels of bones that are not in the skin. gz ignores the actor
skin scale, so the files declare `<unit meter="0.11"/>` to bring the cat to
about 0.6 m long with the tail.
