
import os
import sys
import json
import numpy as np
from compas.geometry import oriented_bounding_box_numpy


output = ""
arguments = sys.argv
if (len(arguments) < 2):
    print("Not enough arguments in "+str(arguments))
    sys.exit()
points = sys.argv[1]
try:
    points = json.loads(points)
    points = np.array(points)
    box = oriented_bounding_box_numpy(points)
    points = []
    for i in range(8):
        point = [float(box[i][0]), float(box[i][1]), float(box[i][2])]
        points.append(point)
    output += json.dumps(points)
except:
    output = ""
print(output)

