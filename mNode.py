import math
import logging
import numbers
from six import string_types

from maya.api import OpenMaya as om
from maya.api import OpenMayaAnim as oma
from maya import cmds
from .xPlug import XPlug
_logger = logging.getLogger(__name__)


def exception_handler(func):
    """decorator to mask false maya error to using classes as comand argument
    """
    def inner_function(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except:
            pass
    return inner_function


class MNode(om.MObjectHandle):
    """Wrapper of OpenMaya objects to easier use of Maya Api
    Inheritance:
        MObjectHandle : inherit form MObjectHandle to check the validity of the object
    """

    def __init__(self, node):
        self._mObject = None
        self.path = None
        self._mFn = None
        self._bestFn = None
        if isinstance(node, string_types):
            if not cmds.objExists(node):
                raise BaseException("{} does not exists". format(node))
            sel = om.MSelectionList()
            sel.add(node)
            self._mObject = sel.getDependNode(0)
            if self._mObject.hasFn(om.MFn.kDagNode):
                self.path = sel.getDagPath(0)
        elif isinstance(node, om.MObject):
            self._mObject = node
        elif isinstance(node, om.MDagPath):
            self._mObject = node.node()
            self.path = node
        elif isinstance(node, om.MObjectHandle):
            self._mObject = node.object()
        elif isinstance(node, MNode):
            self._mObject = MNode.object()
        if self._mObject.hasFn(om.MFn.kDagNode):
            self.path = om.MDagPath.getAPathTo(self._mObject)
        super(MNode, self).__init__()
        self.assign(self._mObject)
        _logger.debug("{} initiated".format(self))

    @classmethod
    def createNode(cls, node_type, name_str=None):
        """create a node and return a MNode object
        Args:
            name_str (str): Name of the node
            node_type (str): type of the node
        Returns:
            MNode: MNode object with the created node
        """
        flags = dict()
        if name_str:
            flags["n"] = name_str
        node = cmds.createNode(node_type, **flags)
        if "shape" in cmds.nodeType(node, i=1):
            trf = cmds.listRelatives(node, p=1)[0]
            if name_str:
                cmds.rename(node, "{}Shape".format(name_str))
                node = cmds.rename(trf, name_str)
            else:
                node = trf
        _logger.debug("{} created".format(node))
        return cls(node)

    def checkValidity(self):
        """Check that the object still exist in memory and on the maya scene
        Raises:
            BaseException: the mObject is not alive or valid
        """
        if not self.isValid():
            raise RuntimeError("{} is not Valid". format(self.name()))
        if not self.isAlive():
            raise RuntimeError("{} is not Alive". format(self.name()))

    def getBestFn(self):
        """get maya api best MFn object form a node name, 
        geting the best Function method (mFn) using maya inheritance
        Raises:
            BaseException: the mObject is not alive or valid
            ValueError: if is unable to get the mFn
        Returns:
            variable maya.api.MFtype
        """
        self.checkValidity()
        if self._bestFn:
            return self._bestFn
        fnList = om.MGlobal.getFunctionSetList(self.object())
        input = self.object()
        if self.path:
            input = self.path
        for fn in fnList[::-1]:
            class_name = 'MFn{}'.format(fn[1:])
            if hasattr(om, class_name):
                try:
                    class_ = getattr(om, class_name)
                    self._bestFn = class_(input)
                    return self._bestFn
                except Exception as e:
                    _logger.debug(e)
            if hasattr(oma, class_name):
                try:
                    class_ = getattr(om, class_name)
                    self._bestFn = class_(input)
                    return self._bestFn
                except Exception as e:
                    _logger.debug(e)
        raise ValueError('Unable to find MFn for {}'.format(fnList[::-1]))

    def getBaseFn(self):
        """get maya api best MFn object form a node name, geting the base function method
        Returns:
            variable maya.api.MFnDagNode or maya.api.MFnDependencyNode
        """
        if not self._mFn:
            if self.path:
                self._mFn = om.MFnDagNode(self.path)
            else:
                self._mFn = om.MFnDependencyNode(self.object())
        return self._mFn

    def name(self):
        """return current name of the node
        Returns:
            str: name of the object
        """
        fn = self.getBaseFn()
        if hasattr(fn, "partialPathName"):
            return fn.partialPathName()
        return fn.name()

    def __str__(self):
        """override string operator to return node name
        Returns:
            str: node name
        """
        return self.name()

    def __unicode__(self):
        return self.name()

    @exception_handler
    def __apiobject__(self):
        "get the MObject for this node if it is valid"
        self.checkValidity()
        raise self.object()

    def __getattr__(self, name):
        """get the attribute as XPlug
        Raises:
            BaseException: the mObject is not alive or valid
        Returns:
            mPlug.XPlug
        """
        self.checkValidity()
        fn = self.getBaseFn()
        if fn.hasAttribute(name):
            return XPlug(fn.findPlug(name, True))
        raise AttributeError("MNode {} doesn't have property called {}".format(self.name(), name))

    def addAttribute(self, attrName, attrType="float", keyable=True, limits=None, default_value=0.0):
        fAttr = None
        attrName = attrName.replace(" ", "_")
        if attrType.lower() == "bool":
            attrType = "boolean"
        if attrType.lower() in ["float", "int", "boolean"]:
            fAttr = om.MFnNumericAttribute()
            data_type = getattr(om.MFnNumericData,
                                "k{}".format(attrType.capitalize()))
            new_attr = fAttr.create(attrName, attrName,
                                    data_type, default_value)
            fAttr.keyable = keyable
            if limits:
                fAttr.setMin(limits[0])
                fAttr.setMax(limits[1])
        elif attrType.lower() == "enum":
            fAttr = om.MFnEnumAttribute()
            new_attr = fAttr.create(attrName, attrName)
            if isinstance(default_value, basestring):
                fAttr.addField(default_value, 0)
            elif isinstance(default_value, list):
                for i, each in enumerate(default_value):
                    fAttr.addField(each, i)
                fAttr.hidden = False
                fAttr.keyable = False
                fAttr.channelBox = True
        fn = self.getBaseFn()
        fn.addAttribute(new_attr)
        return getattr(self, attrName)

    def lockAndHideAttr(self, attrName, value=True):
        if not hasattr(self, attrName):
            raise BaseException("{} has not attribute {}".format(self, attrName))
        plug = getattr(self, attrName)
        plug.isLocked = value
        plug.isKeyable = not value

    def lockAttr(self, attrName, value=True):
        if not hasattr(self, attrName):
            raise BaseException("{} has not attribute {}".format(self, attrName))
        plug = getattr(self, attrName)
        plug.isLocked = value
    
    def hideAttr(self, attrName, value=True):
        if not hasattr(self, attrName):
            raise BaseException("{} has not attribute {}".format(self, attrName))
        plug = getattr(self, attrName)
        plug.isKeyable = not value

    def getShape(self, index=0):
        self.checkValidity()
        if not self.path:
            raise RuntimeError("{} is not DAG node". format(self.name()))
        return MNode(self.path.extendToShape(index))

    def replaceShape(self, target, delete_transform=True):
        self.checkValidity()
        if not self.path:
            raise RuntimeError("{} is not DAG node". format(self.name()))
        MDagMod = om.MDagModifier()
        shape = self.getShape()
        targ_node = MNode(target)
        current_color = self.getColor()
        if shape:
            MDagMod.deleteNode(self.getShape().object(), includeParents=False)
        if targ_node.object().hasFn(om.MFn.kShape):
            target_shape = targ_node.object()
            targ_trf = target.getBaseFn().parent(0)
        else:
            target_shape = targ_node.getShape().object()
            targ_trf = targ_node.object()
        MDagMod.reparentNode(target_shape, self.object())
        MDagMod.doIt()
        self._mFn = om.MFnDagNode(self.object())
        self._bestFn = None
        self.path = self._mFn.getPath()
        if delete_transform:
            MDagMod.deleteNode(targ_trf)
        MDagMod.renameNode(self.getShape().object(), "{}Shape".format(self))
        MDagMod.doIt()
        if current_color:
            self.setColor(current_color)

    def setColor(self, color):
        shape = self.getShape()
        getattr(shape, 'overrideEnabled').set(1)
        getattr(shape, 'overrideRGBColors').set(1)
        for ch, col in zip(['R', 'G', 'B'], color):
            getattr(shape, 'overrideColor{}'.format(ch)).set(col)

    def getColor(self):
        shape = self.getShape()
        overrideEnabled = getattr(shape, 'overrideEnabled').get()
        if not overrideEnabled:
            return None
        overrideRGBColors = getattr(shape, 'overrideRGBColors').get()
        if not overrideRGBColors:
            return None
        overrideColor = list()
        for ch, in zip(['R', 'G', 'B']):
            overrideColor.append(getattr(shape, 'overrideColor{}'.format(ch)).get())
        return overrideColor

    def isTransform(self):
        self.checkValidity()
        return self.object().hasFn(om.MFn.kTransform)

    def _checkTransform(self):
        if not self.isTransform():
            raise RuntimeError(
                "{} has not transformation info". format(self.name()))

    def getParent(self):
        parent = self.getBaseFn().parent(0)
        if parent.hasFn(om.MFn.kWorld):
            return None
        return MNode(parent)

    def setParent(self, parent, stay_in_place=True):
        self._checkTransform()
        parent_node = None
        if isinstance(parent, MNode):
            parent_node = parent
        elif isinstance(parent, basestring):
            parent_node = MNode(parent)
        parent_node._checkTransform()
        if self.getBaseFn().parent(0) == parent_node.object():
            _logger.info("{} is already a child of {}, parenting skipped".format(self, parent_node))
            return
        if self.object() == parent_node.object():
            _logger.info("Unable to parent {} to itself, parenting skipped".format(self))
            return
        current_mtx = self.getMatrix("world")
        # using dagmodifier instead of MFnDag.addChild, becasue if the
        # node is a grandchild of parent, addChild it will fail
        dagMod = om.MDagModifier()
        dagMod.reparentNode(self.object(), parent_node.object())
        dagMod.doIt()
        if stay_in_place:
            self.setMatrix(current_mtx)

    def getMatrix(self, space='world'):
        """if the node is a DAG node, it return the matrix
        Args:
            space (str, optional): space to querry, world or object. Defaults to 'world'.
        Raises:
            RuntimeError: if the node is not alive or is not a DAG node
        Returns:
            MMatrix: current transformation matrix
        """
        self._checkTransform()
        if space.lower() == 'world':
            return self.path.inclusiveMatrix()
        return self.path.exclusiveMatrix()

    def setMatrix(self, matrix, space="world", translation=True, rotation=True, scale=True):
        self._checkTransform()
        mtx = om.MTransformationMatrix(matrix)
        k_space = self.getSpaceConstant(space)
        if scale:
            self.getBestFn().setScale(mtx.scale(k_space))
        if rotation:
            # for some reason the rotation it wont set properlly at world space
            rot_mtx = om.MTransformationMatrix(matrix * self.parentInverseMatrix[0].get())
            self.getBestFn().setRotation(rot_mtx.rotation(asQuaternion=True), self.getSpaceConstant("local"))
        if translation:
            self.getBestFn().setTranslation(mtx.translation(k_space), k_space)

    def getSpaceConstant(self, space):
        if space.lower() == 'world':
            return om.MSpace.kWorld
        elif space.lower() == 'local':
            return om.MSpace.kObject

    def getPosition(self, space='world'):
        """if the node is DAG, return the node position
        Args:
            space (str, optional): space to querry, world or object. Defaults to 'world'.
        Raises:
            RuntimeError: if the node is not alive or is not a DAG node
        Returns:
            MPoint: current position
        """
        mTrfMtx = om.MTransformationMatrix(self.getMatrix(space))

        return mTrfMtx.translation(self.getSpaceConstant(space))

    def setPosition(self, pos, space="world"):
        self._checkTransform()
        self.getBestFn().setTranslation(om.MVector(pos), self.getSpaceConstant(space))

    def getRotation(self, space='world'):
        """if the node is DAG, return the node position
        Args:
            space (str, optional): space to querry, world or object. Defaults to 'world'.
        Raises:
            RuntimeError: if the node is not alive or is not a DAG node
        Returns:
            MPoint: current position
        """
        mTrfMtx = om.MTransformationMatrix(self.getMatrix(space))
        return mTrfMtx.rotation(self.getSpaceConstant(space))

    def setRotation(self, rotation, space="world"):
        """set node rotation
        Args:
            rotation (list): rotations on degrees
            space (str, optional): transformation space. Defaults to "world".
        """
        self._checkTransform()
        rot = [math.radians(a) for a in rotation]
        self.getBestFn().setRotation(om.MEulerRotation(
            rot).asQuaternion(), self.getSpaceConstant(space))

    def getScale(self, space):
        """set node scale
        Args:
            space (str, optional): transformation space. Defaults to "world".
        Returns:
            MVector: current scale
        """
        mTrfMtx = om.MTransformationMatrix(self.getMatrix(space))
        return mTrfMtx.scale(self.getSpaceConstant(space))

    def setScale(self, scale):
        """set node scale
        Args:
            scale (float, list): scale value, if is float, it will apply uniform scale
            space (str, optional): transformation space. Defaults to "world".
        """
        self._checkTransform()
        if isinstance(scale, numbers.Number):
            scale = (scale, scale, scale)
        self.getBestFn().scaleBy(scale)

    def snapTo(self, target, translation=True, rotation=True, scale=True):
        """snap current node to a target node in world space
        Args:
            target (str, MNode): target node
            translation (bool, optional): transform translation. Defaults to True.
            rotation (bool, optional): transform rotation. Defaults to True.
            scale (bool, optional): transform scale. Defaults to True.
        """
        node = MNode(target)
        self.setMatrix(node.getMatrix(), "world", translation, rotation, scale)
