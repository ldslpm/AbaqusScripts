from __future__ import division
import math
from itertools import groupby
from random import uniform
from sympy import Ellipse as el
from sympy.geometry import intersection


"""
This module contains the classes defining the shapes of inclusions, as well
as a factory to create them. Creation of an object is:
myCircle = ShapeFactory.createShape(shapes.CIRCLE)
"""

def enum(**enums):
    return type('Enum', (), enums)

"""
This enum maintains a list of possible shapes that can be created. If a new
shape is added, it must be added to the list. The value is the name of the
class.
"""
shapes = enum(CIRCLE='Circle', ELLIPSE='Ellipse', RECTANGLE='Rectangle')


class ShapeFactory:
    """
    Factory class to encapsulate creation of shapes. Using **kwargs lets you
    pass values to the shape constructors,
    eg. for a circle createShape(shapes.CIRCLE, centre = 0.5, radius = 0.2)
    """

    factories = {}

    def addFactory(shape, shapeFactory):
        ShapeFactory.factories.put[shape] = shapeFactory

    def generateKwargs(shape):
        if not shape in ShapeFactory.factories:
            ShapeFactory.factories[shape] = eval(shape + '.Factory()')

    # A Template Method:
    def createShape(shape, **kwargs):
        if not shape in ShapeFactory.factories:
            ShapeFactory.factories[shape] = eval(shape + '.Factory()')
        return ShapeFactory.factories[shape].create(**kwargs)

    addFactory = staticmethod(addFactory)
    createShape = staticmethod(createShape)


class Shape(object):
    """
    The Shape base class
    """

    centre = ()
    material = None


    def __init__(self, material, centre):
        self.centre = centre
        self.material = material

    def Area(self):
        pass

    def Orientation(self):
        pass

    def GenerateSketch(self):
        pass

#    @staticmethod
#    def ExportInclusions(shapes, matrix_material):
#        output_str = ''
#        materials_used = []
#        for key, group in groupby(sorted(shapes, key=lambda shape: shape.material), lambda x: x.material):
#            materials_used.append(key)
#            output_str += 'Material: {0}:\n'.format(key.name)
#            for shape in group:
#                output_str += '\t{0}\n'.format(shape)

#           output_str += '\n'

#       output_str += 'Materials:\n'
#       for mat in materials_used:
#           output_str += '\t{0}\n'.format(mat)

#        output_str += '\nMatrix Material:\n'
#        output_str += '\t{0}'.format(matrix_material)

#        return output_str


class Ellipse(Shape):
    """
    Class representing an ellipse
    """

    short_axis = 0
    long_axis = 0
    angle = 0

    def __init__(self, material, centre=(0,0), short_axis=0.0, long_axis=0.0, angle=0.0):
        super(Ellipse, self).__init__(material, centre)
        self.short_axis = short_axis
        self.long_axis = long_axis
        self.angle = angle

    def Area(self):
        return math.pi * self.short_axis * self.long_axis

    def AspectRatio(self):
        return self.short_axis / self.long_axis

    def GenerateSketch(self):
        commands = []
        commands.append("t = p.MakeSketchTransform(sketchPlane=f[0], sketchPlaneSide=SIDE1, origin=({0}, {1}, 0.0))".format(self.centre[0], self.centre[1]))
        commands.append("s = myModel.ConstrainedSketch(name='__profile__', sheetSize=20.0, transform=t)")
        commands.append("s.setPrimaryObject(option=SUPERIMPOSE)")
        commands.append("s.EllipseByCenterPerimeter(center=(0.0, 0.0), axisPoint1=({0}, 0.0), axisPoint2=(0.0, {1}))".format(self.long_axis, self.short_axis)) # -> this gives long axis 15, short 2.5

        return commands

    @staticmethod
    def __GenerateSymPyEllipse(ellipse):
        return el(ellipse.centre, ellipse.long_axis, ellipse.short_axis)


    def check_intersect(self, ellipses):
        """
        Check if one ellipse either intersects with another ellipse, or is contained within it.
        Returns true if they intersect or one is within the other.
        Returns false if the ellipses do not touch
        """
        
        ellipse1 = Ellipse.__GenerateSymPyEllipse(self)

        for ellipse in ellipses:
            ellipse2 = Ellipse.__GenerateSymPyEllipse(ellipse)

            if len(intersection(ellipse1, ellipse2)) != 0 or ellipse1.encloses(ellipse2) or ellipse2.encloses(ellipse1): 
                return True

        return False

    def __str__(self):
        return '{0}, {1}, {2}, {3}, {4}, {5}, {6}'.format(self.centre[0], self.centre[1], self.long_axis, self.short_axis, self.AspectRatio(), self.Area(), self.angle)

    @staticmethod
    def ExportInclusions(shapes):
        output_str = '**Matrix:\n'
        output_str += '**Bottom left corner X, Bottom left corner Y, height, width\n'
        output_str += '0, 0, 1, 1\n\n'

        output_str += '**Ellipse distribution\n'
        output_str += '**Centre X, centre Y, long axis, short axis, aspect ratio, area, orientation(rad)\n'
        for shape in shapes:
            output_str += '{0}\n'.format(shape)

        return output_str


    class Factory:
        def create(self, **kwargs):
            return Ellipse(**kwargs)


class Circle(Ellipse):
    """
    A circle is just an ellipse with equal axes, so it extends ellipse
    """

    def __init__(self, material, centre=(0, 0), radius=0.0):
        super(Circle, self).__init__(material, centre, radius, radius)

    @property
    def radius(self):
        return self.short_axis

    @radius.setter
    def radius(self, value):
        self.short_axis = value
        self.long_axis = value

    def perimeter_location(self):
        """
        Get a coordinate that lies on the perimeter of the circle
        """

        return self.centre[0] + self.radius, self.centre[0]

    @staticmethod
    def determine_max_radius(buffersize, numcircles, scalefactor):
        """
        Determines the Maximum radius of circles to fit into a unit square.
        The fit is based on all fitting across in a row, so that they will
        always be able to fit.
        buffersize - the buffer space to leave between circles and the edge of
            the container, as well as between circles.
        numcircles - the number of circles to fit into the container
        scalefactor - a factor to multiply the final radius by. It is provided
            to allow for easier fitting of circles, since if the maximum
            radius is used, it can be difficult to fit all the circles in if
            the first is in a bad location. 0.5 will halve the radius, 2
            will double it.
        """

        if buffersize*2 + (numcircles-1)*buffersize > 1:
            raise ArithmeticError('Cannot fit {} circles with {} buffer size'
                                  .format(numcircles, buffersize))

        return (((1 - buffersize - buffersize * numcircles) / numcircles)
                / 2) * scalefactor

    @staticmethod
    def determine_radius(max_radius, equalsize):
        if equalsize:
            return max_radius
        else:
            return uniform(0.01, max_radius)

    def is_location_inside_square(self, buffersize=0):
        """
        Ensure that the circle will sit completely within the buffer zone of
        the container
        """

        if self.centre[0] - self.radius < buffersize or self.centre[0] + self.radius > (1 - buffersize):
            return False
        if self.centre[1] - self.radius < buffersize or self.centre[1] + self.radius > (1 - buffersize):
            return False

        return True

    def check_intersect(self, circles):
        """
        The circles intesect if the distance between the centrepoints is less
        than the sum of the radii. Also check to make sure one circle isn't
        wholly within another circle. It returns True if they do intersect,
        and False if they do not.
        """

        for circle in circles:
            centre_distance = math.sqrt((self.centre[0] -
                                         circle.centre[0])**2 +
                                        (self.centre[1] -
                                         circle.centre[1])**2)

            if centre_distance > self.radius + circle.radius:
                continue
            elif centre_distance <= math.fabs(self.radius - circle.radius):
                return True
            else:
                return True

        return False

    def __str__(self):
        return '{0}, {1}, {2}, {3}'.format(self.centre[0], self.centre[1], self.radius, self.Area())

    @staticmethod
    def ExportInclusions(shapes):
        #TODO: Refector this, and the same code in ellipse, and change it from being hard coded
        output_str = '**Matrix:\n'
        output_str += '**Bottom left corner X, Bottom left corner Y, height, width\n'
        output_str += '0, 0, 1, 1\n\n'

        output_str += '**Circle distribution\n'
        output_str += '**Centre X, centre Y, radius, area\n'
        for shape in shapes:
            output_str += '{0}\n'.format(shape)

        return output_str

    class Factory:
        def create(self, **kwargs):
            return Circle(**kwargs)


class Rectangle(Shape):
    """
    Class representing a rectangle
    """

    class Factory:
        def create(self):
            return Rectangle()
