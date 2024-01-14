
import bpy
import sys
import bmesh
import logging
import functools
import traceback
import subprocess


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


def get_skin(args, obj):
    print(obj.name)
    target = args[0]
    limit = -1
    mesh = obj.data
    groups = obj.vertex_groups
    vertices = mesh.vertices
    names = []
    skin = {}
    for i, group in enumerate(groups):
        name = group.name
        #print(str(name))
        names.append(name)
        weighting = list(get_weighting(vertices, group))
        for j in range(len(weighting)):
            if not (weighting[j][0] in skin):
                skin[weighting[j][0]] = {}
            skin[weighting[j][0]][i] = weighting[j][1]
    vertices = get_sorting(list(enumerate(vertices)))
    descriptor = open(target+".obj.vw.txt", "w")
    for vertex, _ in vertices:
        if not (vertex in skin):
            continue
        weights = skin[vertex]
        if ((limit > -1) and (len(weights) > limit)):
            temp = []
            for key in weights:
                temp.append(tuple([weights[key], key]))
            temp = list(reversed(get_sorting(temp)))[:limit]
            #print(str(temp))
            weights = {}
            for i in range(len(temp)):
                weights[temp[i][1]] = temp[i][0]
        descriptor.write("vw "+str(vertex))
        for key in weights:
            descriptor.write(" "+str(key)+" "+str(weights[key]))
        descriptor.write("\n")
    descriptor.close()
    return True


args = sys.argv
args = args[(args.index("--")+1):]
if (len(args) < 1):
    print("Not enough arguments in "+str(args))
    sys.exit()
target = args[0]
if not ((target.endswith(".gltf")) or (target.endswith(".glb"))):
    print("\""+target+"\" does not have the proper extension")
    sys.exit()
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.object.select_by_type(type="MESH")
bpy.ops.object.delete()
bpy.ops.import_scene.gltf(filepath=target)
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.object.select_by_type(type="MESH")
for obj in bpy.context.selected_objects:
    res = get_skin(args, obj)
    print(str(res))
    break
bpy.ops.export_scene.obj(filepath=target+".obj")
bpy.ops.export_anim.bvh(filepath=target+".bvh")
bpy.ops.wm.quit_blender()


