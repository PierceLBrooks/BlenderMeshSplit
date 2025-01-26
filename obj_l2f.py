
import os

def get_distance(left, right):
    if not (len(left) == len(right)):
        return float("inf")
    result = 0.0
    for i in range(len(left)):
        result += (left[i]-right[i])**2.0
    return result**0.5

def run(path, dump):
    print(path)
    handle = open(path, "r")
    lines = handle.readlines()
    handle.close()
    maximum = []
    minimum = []
    vertices = []
    output = []
    face = []
    output.append("vn 0 1 0")
    output.append("vt 0 0")
    for line in lines:
        if (line.startswith("v ")):
            vertex = line.split(" ")[1:]
            if (len(vertex) < 2):
                continue
            for i in range(len(vertex)):
                vertex[i] = float(vertex[i])
            index = 0
            while (index < len(vertex)):
                if (abs(vertex[index]) < 0.00001):
                    if (index == 0):
                        vertex = vertex[1:]
                    elif (index == len(vertex)-1):
                        vertex = vertex[:index]
                    else:
                        vertex = vertex[:index]+vertex[(index+1):]
                    index -= 1
                index += 1
            #print(str(vertex))
            if not (len(vertex) == 2):
                continue
            if (len(maximum) == 0):
                for i in range(len(vertex)):
                    maximum.append(float("-inf"))
            if (len(minimum) == 0):
                for i in range(len(vertex)):
                    minimum.append(float("inf"))
            for i in range(len(vertex)):
                maximum[i] = max(maximum[i], vertex[i])
                minimum[i] = min(minimum[i], vertex[i])
            vertices.append(vertex)
    distance = 0.0
    count = 0
    for line in lines:
        line = line.strip()
        if (line.startswith("v ")):
            continue
        if (line.startswith("l ")):
            splits = line.split(" ")[1:]
            if not (len(splits) == 2):
                continue
            head = int(splits[0])-1
            if ((head < 0) or (head >= len(vertices))):
                continue
            tail = int(splits[1])-1
            if ((tail < 0) or (tail >= len(vertices))):
                continue
            distance += get_distance(vertices[head], vertices[tail])
            count += 1
    if (count > 0):
        distance /= float(count)
    else:
        distance = 0.0
    #distance *= 2.0
    for line in lines:
        line = line.strip()
        if (line.startswith("v ")):
            continue
        if (line.startswith("l ")):
            splits = line.split(" ")[1:]
            if not (len(splits) == 2):
                continue
            if (len(face) > 0):
                last = face[len(face)-1]
                last = last[:last.index("/")]
                next = int(splits[0])-1
                other = int(splits[1])-1
                if ((splits[0] == last) or ((int(last)-1 < len(vertices)*2) and (next < len(vertices)*2) and (get_distance(vertices[next%len(vertices)], vertices[(int(last)-1)%len(vertices)]) <= distance))):
                    #face.append(splits[1]+"/1/1")
                    if (len(face) > 3):
                        output.append(" ".join(face))
                        face = ["f"]+list(reversed(face[(len(face)-2):]))
                        face.append(str(int(splits[1])+len(vertices))+"/1/1")
                        face.append(splits[1]+"/1/1")
                        #output.append(" ".join(face))
                        #face = []
                    continue
                """
                elif ((splits[1] == last) or ((int(last)-1 < len(vertices)*2) and (other < len(vertices)*2) and (get_distance(vertices[other%len(vertices)], vertices[(int(last)-1)%len(vertices)]) <= distance))):
                    #face.append(splits[1]+"/1/1")
                    if (len(face) > 3):
                        output.append(" ".join(face))
                        face = ["f"]+face[(len(face)-2):]
                        face.append(str(int(splits[0])+len(vertices))+"/1/1")
                        face.append(splits[0]+"/1/1")
                        #output.append(" ".join(face))
                        #face = []
                    continue
                """
                output.append(" ".join(face))
                face = []
            face.append("f")
            face.append(splits[1]+"/1/1")
            face.append(str(int(splits[1])+len(vertices))+"/1/1")
            face.append(str(int(splits[0])+len(vertices))+"/1/1")
            face.append(splits[0]+"/1/1")
            continue
        output.append(line)
    #"""
    if (len(face) > 0):
        output.append(" ".join(face))
    #"""
    print(str(minimum))
    print(str(maximum))
    if ((len(minimum) == 0) or (len(maximum) == 0)):
        return
    depth = float("inf")
    handle = open(dump, "w")
    for i in range(len(vertices)):
        for j in range(len(vertices[i])):
            depth = min(depth, abs(maximum[j]-minimum[j]))
            vertices[i][j] = vertices[i][j]-((maximum[j]-minimum[j])*0.5)
        handle.write("v "+str(vertices[i][0])+" 0.0 "+str(vertices[i][1])+"\n")
    depth = depth**0.5
    for i in range(len(vertices)):
        handle.write("v "+str(vertices[i][0])+" "+str(-depth)+" "+str(vertices[i][1])+"\n")
    handle.write("v "+str(minimum[0])+" 0.0 "+str(minimum[1])+"\n")
    handle.write("v "+str(minimum[0])+" 0.0 "+str(maximum[1])+"\n")
    handle.write("v "+str(maximum[0])+" 0.0 "+str(maximum[1])+"\n")
    handle.write("v "+str(maximum[0])+" 0.0 "+str(minimum[1])+"\n")
    for i in range(len(output)):
        handle.write(output[i].strip()+"\n")
    handle.close()

extension = ".obj"
for root, folders, files in os.walk(os.getcwd()):
    for name in files:
        if (name.endswith(extension)):
            run(os.path.join(root, name), os.path.join(root, name[:(len(name)-len(extension))]+".obj.obj"))

