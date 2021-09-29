+ ### mayaApi: 
utils to use OpenMaya api easier , this is one of the building blocks of the builder api, it allows to have live connections with the builded modules.  
In order to use it, it can be initialized with the a node name or use the createNode method

``` python
from om2_wrapper.mNode import MNode
cube = cmds.polyCube()[0]
node = MNode(cube) #init from string
print node.name() # Result: u'pCube2' # 
#the node it self is saved not the name so even if the name change, it still working
cmds.rename(cube, "test") 
print node.name() # Result: u'test' # 
# has a wrapper to get and set attributes
print node.ty.get() # Result: 0.0 # 
node.ty.set(5)
print node.ty.get() # Result: 5.0 # 
# It identify the function set form the node type
baseFn = node.getBaseFn() #MFnDagNode
bestFn = node.getBestFn() #MFnTransform
shape = MNode(cmds.listRelatives("test", s=1)[0])
shape.getBaseFn() #MFnDagNode
shape.getBestFn() #MFnMesh
#at its core Mnode is an expanded maya object handle, so it is compatible with OpenMaya api 2.0
from maya.api import OpenMaya as om
trf_obj = om.MFnTransform(node.object())
#and becasue the str representation is overwrite, ir the obje works with maya comands as well
print cmds.listRelatives(node, s=1)
```
Main methods are:  
&nbsp;&nbsp;&nbsp;&nbsp;**createNode** create a node and return a MNode object  
&nbsp;&nbsp;&nbsp;&nbsp;**getBaseFn** get the basic maya api MFnDependencyNode, but MFnDagNode if is a Dag node  
&nbsp;&nbsp;&nbsp;&nbsp;**getBestFn** get maya api that best match the node type  
&nbsp;&nbsp;&nbsp;&nbsp;**getDagPath** get full dag path maya object (objet that hadle hierarchy)  
&nbsp;&nbsp;&nbsp;&nbsp;**addAttribute** add atrribute to the node, it the main arguments are attrName (mandatory), attrType (default "float"), keyable (default True) and limits (default None)  
&nbsp;&nbsp;&nbsp;&nbsp;**lockAndHideAttr** lock and hide (remove from the channel box) attributes  
&nbsp;&nbsp;&nbsp;&nbsp;**getShape** return the node shape, if the node is a shape it will return itself  
&nbsp;&nbsp;&nbsp;&nbsp;**replaceShape** replace the node shape for a specified target shape  
&nbsp;&nbsp;&nbsp;&nbsp;**setColor** set the shape color  
&nbsp;&nbsp;&nbsp;&nbsp;**getColor** get the shape color  
&nbsp;&nbsp;&nbsp;&nbsp;**getParent** get node current parent or None if it does not have parent  
&nbsp;&nbsp;&nbsp;&nbsp;**setParent** reparent node to a new parent  
&nbsp;&nbsp;&nbsp;&nbsp;**getMatrix** if the node is a DAG node, it return the matrix  
&nbsp;&nbsp;&nbsp;&nbsp;**setMatrix** set current node transformation matrix  
&nbsp;&nbsp;&nbsp;&nbsp;**getPosition** if the node is DAG, return the node position in the spacified space (world by default)  
&nbsp;&nbsp;&nbsp;&nbsp;**setPosition** set the node position  
&nbsp;&nbsp;&nbsp;&nbsp;**getRotation** if the node is DAG, return the node rotation in the spacified space (world by default)  
&nbsp;&nbsp;&nbsp;&nbsp;**setRotation** set the node rotation  
&nbsp;&nbsp;&nbsp;&nbsp;**getScale** if the node is DAG, return the node scale in the spacified space (world by default)  
&nbsp;&nbsp;&nbsp;&nbsp;**setScale** set the node scale  
&nbsp;&nbsp;&nbsp;&nbsp;**snapTo** snap current node to a target node in world space  
