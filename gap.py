
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


def get_length(vertices):
    length = 0.0
    for i in range(len(vertices)):
        if (i == 0):
            continue
        left = vertices[i-1]
        right = vertices[i]
        if not ("list" in str(type(left))):
            left = left.co
        if not ("list" in str(type(right))):
            right = right.co
        length += get_distance(left, right)
    return length


def get_angle(point, center, pivot, origin):
    position = get_projection(point, center, pivot)
    angle = get_direction(origin, position)
    return get_bounded(angle)


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


def get_indices(indices):
    result = {}
    for index in indices:
        result[index.index] = index
    return result


def gaps(args, obj):
    subject = obj.type

    if not (bpy.context.mode == "OBJECT"):
        return False
    
    bm = None
    mesh = None
    edges = []
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
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type="EDGE")
            bpy.ops.mesh.select_non_manifold(use_non_contiguous=False)
            #bpy.ops.mesh.select_all(action="INVERT")
            #bpy.ops.object.mode_set(mode="OBJECT")
            for edge in bm.edges:
                if (edge.select):
                    edges.append(edge)
            #bpy.ops.object.mode_set(mode="EDIT")
    
    if (bm == None):
        return False
    if (len(edges) < 2):
        bm.free()
        return False
    """
    bmesh.ops.delete(bm, geom=edges, context="EDGES")
    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode="OBJECT")
    return True
    """
    
    while (True):
        print(obj.name)
        edge = None
        reverse = {}
        vertices = {}
        lengths = []
        centers = []
        totals = []
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
                totals.append([])
                positions = []
                for j in range(len(group)):
                    positions.append(get_center(group[j].verts))
                    if not (group[j].index in vertices):
                        vertices[group[j].index] = []
                    for vertex in group[j].verts:
                        if not (vertex.index in totals[len(groups)]):
                            totals[len(groups)].append(vertex.index)
                        reverse[vertex.index] = len(groups)
                        vertices[group[j].index].append([vertex.index, vertex.co])
                center = get_center(positions)
                origin = get_projection(center, center, positions[0])
                for j in range(len(group)):
                    angle = get_angle(positions[j], center, positions[0], origin)
                    group[j] = [angle, group[j].index, positions[j], get_length(group[j].verts)]
                #group = list(get_sorting(group))
                for j in range(len(group)):
                    angle = group[j][0]
                    group[j][0] = group[j][len(group[j])-1]
                    group[j][len(group[j])-1] = angle
                    #print(str(angle)+" @ "+str(j)+" = "+str(group[j][0]))
                print(str(len(groups))+" = "+str(len(group)))
                groups.append(group)
                centers.append(center)
                lengths.append(list(reversed(list(get_sorting(group)))))
                #print(str(lengths[len(lengths)-1]))
            group = []
        past = []
        frontier = []
        edges = len(bm.edges)
        edge = None
        print(str(len(groups)))
        
        if (len(groups) < 2):
            bm.free()
            return False
        
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
        print(str(pairs))
        
        mapping = {}
        distances = {}
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
                    if not (pair[0] in distances):
                        distances[pair[0]] = {}
                    for i in range(len(pair)):
                        if (i == 0):
                            continue
                        #print(str(pair[0])+" @ "+str(left)+" -> "+str(pair[i])+" @ "+str(right)+" = "+str(distance))
                        mapping[pair[0]].append(pair[i])
                        distances[pair[0]][pair[i]] = distance
                        if not (pair[i] in mapping):
                            mapping[pair[i]] = []
                        if not (pair[i] in distances):
                            distances[pair[i]] = {}
                        mapping[pair[i]].append(pair[0])
                        distances[pair[i]][pair[0]] = distance
        print(str(len(list(mapping.keys())))+" | "+str(edges))
        
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
                        if not (pair[0] in distances):
                            distances[pair[0]] = {}
                        for k in range(len(pair)):
                            if (k == 0):
                                continue
                            #print(str(pair[0])+" @ "+str(left)+" -> "+str(pair[k])+" @ "+str(right)+" = "+str(distance))
                            mapping[pair[0]].append(pair[k])
                            distances[pair[0]][pair[k]] = distance
                            if not (pair[k] in mapping):
                                mapping[pair[k]] = []
                            if not (pair[k] in distances):
                                distances[pair[k]] = {}
                            mapping[pair[k]].append(pair[0])
                            distances[pair[k]][pair[0]] = distance
                    else:
                        fail += 1
        temp = {}
        for key in mapping:
            if (key in vertices):
                for vertex in vertices[key]:
                    vertex = vertex[0]
                    for i in range(len(pairs)):
                        pair = pairs[i]
                        left = pair[0][0]
                        right = pair[0][1]
                        if ((left == reverse[vertex]) or (right == reverse[vertex])):
                            if not (i in temp):
                                temp[i] = []
                            temp[i].append(vertex)
                            break
            length = len(mapping[key])
            if not (length in stats):
                stats[length] = 0
            stats[length] += 1
        reverse = temp
        print(str(fix)+" | "+str(fail)+" | "+str(count)+" | "+str(total)+" | "+str(stats))
        
        edits = []
        edges = get_indices(list(bm.edges))
        vertices = get_indices(list(bm.verts))
        big = []
        for i in range(len(pairs)):
            pair = pairs[i]
            left = pair[0][0]
            right = pair[0][1]
            small = None
            cuts = {}
            if (len(lengths[left]) == len(lengths[right])):
                continue
            if (len(lengths[left]) < len(lengths[right])):
                small = left
                big.append(right)
            else:
                small = right
                big.append(left)
            for i in range(abs(len(lengths[small])-len(lengths[big[len(big)-1]]))):
                long = i%len(lengths[small])
                if not (long in cuts):
                    cuts[long] = 0
                cuts[long] += 1
            for cut in cuts:
                length = len(edges)
                #print(str(cut)+" | "+str(lengths[small][cut][0]))
                #bpy.ops.mesh.select_all(action="DESELECT")
                edge = edges[lengths[small][cut][1]]
                cut = cuts[cut]
                bmesh.ops.subdivide_edges(bm, edges=[edge], cuts=cut)
                edges = get_indices(list(bm.edges))
                vertices = get_indices(list(bm.verts))
                for i in range(abs(length-len(edges))):
                    for face in edges[length+i].link_faces:
                        bmesh.ops.triangulate(bm, faces=[face])
                edges = get_indices(list(bm.edges))
                vertices = get_indices(list(bm.verts))
                #print(str(cut)+" | "+str(length)+" | "+str(len(edges)))
            edges = get_indices(list(bm.edges))
            vertices = get_indices(list(bm.verts))
        if (len(big) > 0):
            print(str(big))
            continue
        edges = get_indices(list(bm.edges))
        vertices = get_indices(list(bm.verts))
        for i in range(len(pairs)):
            pair = pairs[i]
            left = pair[0][0]
            right = pair[0][1]
            short = []
            for j in range(len(groups[left])):
                edge = groups[left][j]
                for other in mapping[edge[1]]:
                    for k in range(len(groups[right])):
                        if (groups[right][k][1] == other):
                            short.append([distances[edge[1]][groups[right][k][1]], j, k])
                            break
            short = list(sorted(short))
            edge = short[0][1]
            other = short[0][2]
            if not (edge == 0):
                if (edge == len(groups[left])-1):
                    groups[left] = [groups[left][edge]]+groups[left][:edge]
                else:
                    groups[left] = groups[left][edge:]+groups[left][:edge]
            if not (other == 0):
                if (other == len(groups[right])-1):
                    groups[right] = [groups[right][other]]+groups[right][:other]
                else:
                    groups[right] = groups[right][other:]+groups[right][:other]
        for i in range(len(groups)):
            group = [0]
            indices = list(range(len(groups[i])))[1:]
            while (len(group) < len(groups[i])):
                length = len(group)
                edge = edges[groups[i][group[length-1]][1]]
                for j in range(len(indices)):
                    other = edges[groups[i][indices[j]][1]]
                    for vertex in other.verts:
                        for k in range(len(vertex.link_edges)):
                            if (vertex.link_edges[k].index == edge.index):
                                group.append(indices[j])
                                if (j == 0):
                                    indices = indices[1:]
                                else:
                                    if (j == len(indices)-1):
                                        indices = indices[:(len(indices)-1)]
                                    else:
                                        indices = indices[:j]+indices[(j+1):]
                                break
                        if not (length == len(group)):
                            break
                    if not (length == len(group)):
                        break
                if (length == len(group)):
                    if (len(indices) == 1):
                        group.append(indices[0])
                    else:
                        print(str(indices))
                        print(str(len(indices))+" | "+str(len(groups[i])))
                        group = None
                    break
            if (group == None):
                continue
            print(str(len(group)))
            for j in range(len(group)):
                group[j] = groups[i][group[j]]
            groups[i] = group
        for i in range(len(groups)):
            group = list(edges[groups[i][0][1]].verts)
            indices = list(range(len(groups[i])))[1:]
            while (len(group) < len(totals[i])):
                length = len(group)
                for j in range(len(indices)):
                    edge = edges[groups[i][indices[j]][1]]
                    for vertex in edge.verts:
                        for k in range(len(vertex.link_edges)):
                            for other in vertex.link_edges[k].verts:
                                if ((other == group[len(group)-1]) and not (other == vertex)):
                                    group.append(vertex)
                                    if (j == 0):
                                        indices = indices[1:]
                                    else:
                                        if (j == len(indices)-1):
                                            indices = indices[:(len(indices)-1)]
                                        else:
                                            indices = indices[:j]+indices[(j+1):]
                                    break
                            if not (length == len(group)):
                                break
                        if not (length == len(group)):
                            break
                    if not (length == len(group)):
                        break
                if (length == len(group)):
                    if (len(indices) == 1):
                        group.append(indices[0])
                    else:
                        print(str(indices))
                        print(str(len(indices))+" | "+str(len(totals[i])))
                        group = None
                    break
            if (group == None):
                continue
            print(str(len(group)))
            for j in range(len(group)):
                group[j] = group[j].index
            groups[i] = group
        for i in range(len(pairs)):
            pair = pairs[i]
            for j in range(len(groups[pair[0][0]])):
                left = pair[0][0]
                right = pair[0][1]
                for k in range(2):
                    edit = []
                    if not (k == 0):
                        temp = left
                        left = right
                        right = temp
                    vertex = vertices[groups[left][j]]
                    other = vertices[groups[right][(j+k)%len(groups[right])]]
                    edit.append(vertex)
                    edit.append(other)
                    edit.append(vertices[groups[left][(j+1)%len(groups[left])]])
                    if (len(edit) < 3):
                        continue
                    if (len(edit) > 3):
                        triangulation = get_triangulation(edit)
                        for l in range(len(triangulation)):
                            edits.append(triangulation[l])
                    else:
                        edits.append(edit)
        for edit in edits:
            bm.faces.ensure_lookup_table()
            try:
                bm.faces.new(tuple(edit))
            except:
                logging.error(traceback.format_exc())
                print(str(edit))
        bm.faces.ensure_lookup_table()
        #bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bmesh.update_edit_mesh(mesh)
        bpy.ops.object.mode_set(mode="OBJECT")
        
        bm.free()
        
        break
    
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

