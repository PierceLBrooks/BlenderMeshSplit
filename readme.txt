
Windows:

 * python -m pip install -r ./requirements.txt

 * set BLENDER_HOME=C:\Blender\3.0

 * echo "%BLENDER_HOME%"

 * split.bat ./skeletal.gltf

 * gap.bat ./mesh.obj

Unix:

 * python3 -m pip install -r ./requirements.txt

 * export BLENDER_HOME=~/Blender/3.0

 * echo "$BLENDER_HOME"

 * ./split.sh ./skeletal.gltf

 * ./gap.sh ./mesh.obj
