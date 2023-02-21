
import bpy
import sys
import json
import math
import bmesh
import logging
import functools
import traceback


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


def get_center(vertices):
    center = []
    center.append(0.0)
    center.append(0.0)
    center.append(0.0)
    for vertex in vertices:
        if ("list" in str(type(vertex))):
            for i in range(len(center)):
                center[i] += vertex[i]
            continue
        for i in range(len(center)):
            center[i] += vertex.co[i]
    for i in range(len(center)):
        center[i] /= float(len(vertices))
    return center


def get_subtraction(left, right):
    subtraction = []
    subtraction.append(left[0]-right[0])
    subtraction.append(left[1]-right[1])
    subtraction.append(left[2]-right[2])
    return subtraction


def get_magnitude(vector):
    magnitude = 0.0
    magnitude += vector[0]**2.0
    magnitude += vector[1]**2.0
    magnitude += vector[2]**2.0
    return magnitude**0.5


def get_normalized(vector):
    normalized = []
    magnitude = get_magnitude(vector)
    try:
        normalized.append(vector[0]/magnitude)
        normalized.append(vector[1]/magnitude)
        normalized.append(vector[2]/magnitude)
    except:
        normalized = []
        for i in range(len(vector)):
            normalized.append(vector[i])
    return normalized


def get_cross(left, right):
    cross = []
    cross.append((left[1]*right[2])-(left[2]*right[1]))
    cross.append((left[2]*right[0])-(left[0]*right[2]))
    cross.append((left[0]*right[1])-(left[1]*right[0]))
    return cross


def get_dot(left, right):
    dot = 0.0
    dot += left[0]*right[0]
    dot += left[1]*right[1]
    dot += left[2]*right[2]
    return dot


def get_normal(point, center, pivot):
    return get_cross(get_subtraction(point, center), get_subtraction(point, pivot))


def get_projection(point, center, pivot):
    projection = []
    normal = get_normalized(get_normal(point, center, pivot))
    axis = get_normalized(get_subtraction(pivot, center))
    axisOther = get_normalized(get_cross(normal, axis))
    displacement = get_subtraction(point, center)
    projection.append(get_dot(axis, displacement))
    projection.append(get_dot(axisOther, displacement))
    #displacement = get_dot(normal, displacement)
    #projection.append(displacement)
    return projection


def get_bounded(angle):
    bounded = angle
    bound = math.pi*2.0
    while (bounded >= bound):
        bounded -= bound
    while (bounded <= 0.0):
        bounded += bound
    return bounded


def get_direction(source, destination):
    return math.atan2(source[1]-destination[1], source[0]-destination[0])


def get_distance(left, right):
    distance = 0.0
    for i in range(min(len(left), len(right))):
        distance += (left[i]-right[i])**2.0
    return distance**0.5


def get_angle(point, center, pivot, origin):
    position = get_projection(point, center, pivot)
    angle = get_direction(origin, position)
    return get_bounded(angle)


def get_supports(vertices, left, right, direction):
    pairs = []
    paired = {}
    positions = []
    positions += vertices[left]
    positions += vertices[right]
    for i in range(len(vertices[left])):
        if (i in paired):
            continue
        position = positions[i]
        pair = []
        pair.append(i)
        other = (i+len(vertices[left]))%len(positions)
        while ((other in paired) or (other < len(vertices[left]))):
            other += 1
            if (other == len(positions)):
                other -= other
        distance = get_dot(direction, get_normalized(get_subtraction(positions[i][1], positions[other][1])))
        for j in range(len(positions)):
            if (i == j):
                continue
            if (j == other):
                continue
            if (j < len(vertices[left])):
                continue
            if (j in paired):
                continue
            temp = get_dot(direction, get_normalized(get_subtraction(positions[i][1], positions[j][1])))
            if (temp < distance):
                continue
            distance = temp
            other = j
        if not (other in paired):
            pair.append(other)
        if (len(pair) < 2):
            continue
        for j in range(len(pair)):
            paired[pair[j]] = len(pairs)
            if (pair[j] < len(vertices[left])):
                pair[j] = vertices[left][pair[j]][0]
            else:
                pair[j] = vertices[right][pair[j]-len(vertices[left])][0]
        pairs.append(pair)
    #print(str(pairs))
    return pairs


def get_triangulation(vertices):
    triangles = []
    triangle = []
    triangle.append(vertices[0])
    triangle.append(vertices[1])
    triangle.append(vertices[2])
    triangles.append(triangle)
    triangle = []
    triangle.append(vertices[3])
    triangle.append(vertices[2])
    triangle.append(vertices[1])
    triangles.append(triangle)
    return triangles


def gaps(args, obj):
    print(obj.name)
    subject = obj.type
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    edges = list(bm.edges)
    edge = None
    vertices = {}
    centers = []
    groups = []
    group = []
    past = []
    for i in range(len(edges)):
        edge = edges[i]
        frontier = []
        if (edge in past):
            continue
        frontier.append(edge)
        while (len(frontier) > 0):
            edge = frontier[0]
            frontier = frontier[1:]
            if not (edge.index in past):
                past.append(edge.index)
            if not (edge.is_manifold):
                group.append(edge)
                for vertex in edge.verts:
                    for other in vertex.link_edges:
                        if not (other == edge):
                            if not (other.index in past):
                                frontier.append(other)
        if (len(group) > 1):
            positions = []
            for j in range(len(group)):
                positions.append(get_center(group[j].verts))
                if not (group[j].index in vertices):
                    vertices[group[j].index] = []
                for vertex in group[j].verts:
                    vertices[group[j].index].append([vertex.index, vertex.co])
            center = get_center(positions)
            origin = get_projection(center, center, positions[0])
            for j in range(len(group)):
                angle = get_angle(positions[j], center, positions[0], origin)
                group[j] = [angle, group[j].index, positions[j]]
            group = list(get_sorting(group))
            """
            for j in range(len(group)):
                angle = group[j][0]
                print(str(angle)+" @ "+str(j))
            """
            #print(str(len(groups))+" = "+str(len(group)))
            groups.append(group)
            centers.append(center)
        group = []
    past = []
    frontier = []
    edges = len(bm.edges)
    edge = None
    bm.to_mesh(mesh)
    bm.free()
    
    if (len(groups) < 2):
        return False
    print(str(len(groups)))
    pairs = []
    paired = {}
    for i in range(len(groups)):
        if (i in paired):
            continue
        group = groups[i]
        center = centers[i]
        pair = []
        pair.append(i)
        other = (i+1)%len(groups)
        while (other in paired):
            other += 1
            if (other == len(groups)):
                other -= other
        distance = get_distance(center, centers[other])
        for j in range(len(groups)):
            if (i == j):
                continue
            if (j == other):
                continue
            if (j in paired):
                continue
            temp = get_distance(center, centers[j])
            if (temp > distance):
                continue
            distance = temp
            other = j
        if not (other in paired):
            pair.append(other)
        if (len(pair) < 2):
            continue
        for j in range(len(pair)):
            paired[pair[j]] = len(pairs)
        center = get_center([center, centers[pair[len(pair)-1]]])
        pairs.append([pair, distance, center])
    #print(str(pairs))
    
    mapping = {}
    for pair in pairs:
        left = pair[0][0]
        right = pair[0][1]
        for edge in groups[left]:
            pair = []
            pair.append(edge[1])
            distance = None
            for other in groups[right]:
                temp = get_distance(edge[2], other[2])
                if (distance == None):
                    distance = temp
                    pair.append(other[1])
                    continue
                if (temp > distance):
                    continue
                distance = temp
                pair[len(pair)-1] = other[1]
            if (len(pair) > 1):
                if not (pair[0] in mapping):
                    mapping[pair[0]] = []
                for i in range(len(pair)):
                    if (i == 0):
                        continue
                    #print(str(pair[0])+" @ "+str(left)+" -> "+str(pair[i])+" @ "+str(right)+" = "+str(distance))
                    mapping[pair[0]].append(pair[i])
                    if not (pair[i] in mapping):
                        mapping[pair[i]] = []
                    mapping[pair[i]].append(pair[0])
    #print(str(len(list(mapping.keys())))+" | "+str(edges))
    
    count = 0
    total = 0
    fail = 0
    fix = 0
    stats = {}
    for i in range(len(groups)):
        group = groups[i]
        total += len(group)
        for j in range(len(group)):
            edge = group[j]
            if not (edge[1] in mapping):
                count += 1
                if not (i in paired):
                    continue
                pair = pairs[paired[i]]
                left = pair[0][0]
                right = pair[0][1]
                if not (left == i):
                    temp = left
                    left = right
                    right = temp
                pair = []
                pair.append(edge[1])
                distance = None
                for other in groups[right]:
                    temp = get_distance(edge[2], other[2])
                    if (distance == None):
                        distance = temp
                        pair.append(other[1])
                        continue
                    if (temp > distance):
                        continue
                    distance = temp
                    pair[len(pair)-1] = other[1]
                if (len(pair) > 1):
                    fix += 1
                    if not (pair[0] in mapping):
                        mapping[pair[0]] = []
                    for k in range(len(pair)):
                        if (k == 0):
                            continue
                        #print(str(pair[0])+" @ "+str(left)+" -> "+str(pair[k])+" @ "+str(right)+" = "+str(distance))
                        mapping[pair[0]].append(pair[k])
                        if not (pair[k] in mapping):
                            mapping[pair[k]] = []
                        mapping[pair[k]].append(pair[0])
                else:
                    fail += 1
    """
    for key in mapping:
        length = len(mapping[key])
        if not (length in stats):
            stats[length] = 0
        stats[length] += 1
    """
    #print(str(fix)+" | "+str(fail)+" | "+str(count)+" | "+str(total)+" | "+str(stats))
    
    news = []
    faces = []
    for pair in pairs:
        left = pair[0][0]
        right = pair[0][1]
        direction = get_normalized(get_subtraction(centers[left], centers[right]))
        for edge in groups[left]:
            if not (edge[1] in mapping):
                continue
            others = mapping[edge[1]]
            if (len(others) == 1):
                supports = get_supports(vertices, edge[1], others[0], direction)
                face = []
                for support in supports:
                    support = json.dumps(support)
                    if not (support in news):
                        face.append(edges+len(news))
                        news.append(support)
                    else:
                        face.append(news.index(support))
                face.append(edge[1])
                face.append(others[0])
                faces.append(face)
                continue
    """
    for i in range(len(faces)):
        face = faces[i]
        print(str(face)+" @ "+str(i))
    print(str(len(news)))
    """
    
    #"""
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
                """
                for new in news:
                    bm.edges.ensure_lookup_table()
                    bm.verts.ensure_lookup_table()
                    new = json.loads(new)
                    for i in range(len(new)):
                        new[i] = bm.verts[new[i]]
                    try:
                        bm.edges.new(tuple(new))
                    except:
                        logging.error(traceback.format_exc())
                        print(str(new))
                """
                for face in faces:
                    bm.edges.ensure_lookup_table()
                    bm.verts.ensure_lookup_table()
                    bm.faces.ensure_lookup_table()
                    vertices = []
                    for edge in face:
                        if (edge < edges):
                            edge = bm.edges[edge]
                            for vertex in edge.verts:
                                #vertices.append(vertex.index)
                                vertex = bm.verts[vertex.index]
                                if (vertex in vertices):
                                    continue
                                vertices.append(vertex)
                        else:
                            new = json.loads(news[edge-edges])
                            for i in range(len(new)):
                                vertex = bm.verts[new[i]]
                                if (vertex in vertices):
                                    continue
                                vertices.append(vertex)
                    """
                    triangles = get_triangulation(vertices)
                    for triangle in triangles:
                        bm.faces.new(tuple(triangle))
                    """
                    try:
                        bm.faces.new(tuple(vertices))
                    except:
                        logging.error(traceback.format_exc())
                        print(str(vertices))
                bmesh.ops.triangulate(bm, faces=bm.faces[:])
                bmesh.update_edit_mesh(mesh)
                bm.free()
                bpy.ops.object.mode_set(mode="OBJECT")
                break
    #"""
    
    return True


args = sys.argv
args = args[(args.index("--")+1):]
if (len(args) < 1):
    print("Not enough arguments in "+str(args))
    sys.exit()
target = args[0]
if not (target.endswith(".obj")):
    print("\""+target+"\" does not have the proper extension")
    sys.exit()
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.object.select_by_type(type="MESH")
bpy.ops.object.delete()
bpy.ops.import_scene.obj(filepath=target)
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.object.select_by_type(type="MESH")
for obj in bpy.context.selected_objects:
    res = gaps(args, obj)
    print(str(res))
    break
bpy.ops.export_scene.obj(filepath=target+".obj")
bpy.ops.wm.quit_blender()

