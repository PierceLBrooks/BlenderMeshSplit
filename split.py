
import bpy
import sys
import json
import bmesh
import logging
import functools


def get_children(obj, subject = None):
    if (obj == None):
        if not (subject == None):
            return []
        return None
    children = []
    print(obj.type)
    if (obj.type == subject):
        children.append(obj)
    for o in bpy.data.objects:
        if (o.parent == obj):
            if (subject == None):
                children.append(o)
            else:
                grandchildren = get_children(o, subject)
                if (o.type == subject):
                    children.append(o)
                for child in grandchildren:
                    print(child.type)
                    if (child.type == subject):
                        children.append(child)
    return children


def get_comparison(left, right):
    if (left[0] > right[0]):
        return 1
    if (left[0] < right[0]):
        return -1
    return 0


def get_sorting(array):
    sorting = sorted(array, key=functools.cmp_to_key(get_comparison))
    return list(sorting)


def get_total(array):
    total = 0.0
    for i in range(len(array)):
        total += array[i]
    return total


def get_weighting(vertices, group):
    index = group.index
    for i, v in enumerate(vertices):
        for g in v.groups:
            if (g.group == index):
                yield (i, g.weight)
                break


def get_split(args, obj):
    print(obj.name)
    subject = obj.type
    groups = obj.vertex_groups
    mesh = obj.data
    bm = bmesh.new()
    vertices = mesh.vertices
    faces = mesh.polygons
    reverse = {}
    mapping = {}
    weights = {}
    names = []
    neighbors = {}
    bm.from_mesh(mesh)
    for face in bm.faces:
        if not (face.index in neighbors):
            neighbors[face.index] = []
        for edge in face.edges:
            for other in edge.link_faces:
                if not (other.index == face.index):
                    if not (other.index in neighbors[face.index]):
                        neighbors[face.index].append(other.index)
    bm.to_mesh(mesh)
    bm.free()
    for i, f in enumerate(faces):
        f.select = False
        if not (i in mapping):
            mapping[i] = []
        for vertex in f.vertices:
            if not (vertex in reverse):
                reverse[vertex] = []
            if not (i in reverse[vertex]):
                reverse[vertex].append(i)
            if not (vertex in mapping[i]):
                mapping[i].append(vertex)
    for group in groups:
        name = group.name
        names.append(name)
        weighting = list(get_weighting(vertices, group))
        for v, w in weighting:
            for i in reverse[v]:
                if not (i in weights):
                    weights[i] = {}
                for vertex in mapping[i]:
                    if (vertex == v):
                        if not (name in weights[i]):
                            weights[i][name] = {}
                        weights[i][name][v] = w
    groups = {}
    for face in weights:
        temp = {}
        for name in weights[face]:
            if not (name in temp):
                temp[name] = []
            for vertex in weights[face][name]:
                weight = weights[face][name][vertex]
                temp[name].append(weight)
        vertices = []
        for name in temp:
            vertices.append([len(temp[name]), name])
        vertices = list(reversed(get_sorting(vertices)))
        for i in range(len(vertices)):
            vertices[i][0] = get_total(temp[vertices[i][1]])
        vertices = list(reversed(get_sorting(vertices)))
        name = vertices[0][1]
        weights[face] = name
        if not (name in groups):
            groups[name] = []
        if not (face in groups[name]):
            groups[name].append(face)
    borders = {}
    for name in groups:
        for face in groups[name]:
            if not (face in neighbors):
                continue
            for other in neighbors[face]:
                if not (other in weights):
                    continue
                if not (name == weights[other]):
                    if not (name in borders):
                        borders[name] = []
                    borders[name].append(face)
    border = []
    for name in borders:
        for face in borders[name]:
            border.append(face)
    print(subject)
    if (bpy.context.mode == "OBJECT"):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        for o in bpy.context.selected_objects:
            print(o.name)
            print(o.type)
            if not (o.type == subject):
                continue
            mesh = o.data
            if not (mesh == None):
                bm = bmesh.from_edit_mesh(mesh)
                selection = [f for f in bm.faces if f.index in border]
                bmesh.ops.delete(bm, geom=selection, context="FACES")
                bmesh.update_edit_mesh(mesh)
                bm.free()
                bpy.ops.object.mode_set(mode="OBJECT")
                break
    return True


args = sys.argv[(sys.argv.index("--")+1):]
if (len(args) < 1):
    sys.exit()
target = args[0]
if not ((target.endswith(".gltf")) or (target.endswith(".glb"))):
    sys.exit()
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.object.select_by_type(type="MESH")
bpy.ops.object.delete()
bpy.ops.import_scene.gltf(filepath=target)
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.object.select_by_type(type="MESH")
for obj in bpy.context.selected_objects:
    result = get_split(args, obj)
bpy.ops.export_scene.gltf(filepath=target+".glb")
bpy.ops.wm.quit_blender()

