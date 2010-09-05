from copy import deepcopy
from struct import pack
from math import sqrt

class Vector2:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def asTuple( self ):
        return (self.x, self.y)

    def __sub__( self, v ):
        return Vector2( self.x - v.x, self.y - v.y )

    def __isub__( self, v ):
        self.x -= v.x
        self.y -= v.y
        return self

    def __add__( self, v ):
        return Vector2( self.x + v.x, self.y + v.y )

    def __iadd__( self, v ):
        self.x += v.x
        self.y += v.y
        return self

    def __div__( self, s ):
        return Vector2( self.x / s, self.y / s )

    def __mul__( self, s ):
        return Vector2( self.x * s, self.y * s )

    def normalize( self ):
        """Returns a normalized version of the vector"""
        mag = self.magnitude()
        if ( mag > 0.0 ):
            return Vector2( self.x / mag, self.y / mag )
        else:
            return Vector2( 0.0, 0.0 )

    def det( self, v ):
        """Computes the determinant of this vector with v"""
        return self.x * v.y - self.y * v.x

    def dot( self, v ):
        return self.x * v.x + self.y * v.y

    def magnitude( self ):
        return sqrt( self.x * self.x + self.y * self.y )

    def __getitem__( self, index ):
        if ( index == 0 ):
            return self.x
        elif (index == 1 ):
            return self.y
        else:
            raise IndexError, "list index out of range"

    def __setitem__( self, index, value ):
        if ( index == 0 ):
            self.x = value
        elif (index == 1 ):
            self.y = value
        else:
            raise IndexError, "list index out of range"

    def __str__(self):
        return "<%g, %g>" % (self.x, self.y )

    def __repr__( self ):
        return str(self)        

class Vector3:
    def __init__( self, x, y, z ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __getitem__( self, index ):
        if ( index == 0 ):
            return self.x
        elif (index == 1 ):
            return self.y
        elif ( index == 2 ):
            return self.z
        else:
            raise IndexError, "list index out of range"

    def __setitem__( self, index, value ):
        if ( index == 0 ):
            self.x = value
        elif (index == 1 ):
            self.y = value
        elif (index == 2 ):
            self.z = value
        else:
            raise IndexError, "list index out of range"

    def __str__(self):
        return "<%6.3f, %6.3f, %6.3f>" % (self.x, self.y, self.z )

    def __repr__( self ):
        return str(self)

    def __eq__( self, v ):
        return self.x == v.x and self.y == v.y and self.z == v.z
    
    def __sub__( self, v ):
        return Vector3( self.x - v.x, self.y - v.y, self.z - v.z )

    def __mul__( self, s ):
        return Vector3( self.x * s, self.y * s, self.z * s )

    def asTuple( self ):
        return (self.x, self.y, self.z)

    def dot( self, v ):
        return self.x * v.x + self.y * v.y + self.z * v.z

    def cross( self, v ):
        x = self.y * v.z - self.z * v.y
        y = self.z * v.x - self.x * v.z
        z = self.x * v.y - self.y * v.x
        return Vector3( x, y, z )

    def lengthSquared( self ):
        return self.x * self.x + self.y * self.y + self.z * self.z

    def length( self ):
        return sqrt( self.lengthSquared() )

    def normalize_ip( self ):
        lenRecip = 1.0 / self.length()
        self.x *= lenRecip
        self.y *= lenRecip
        self.z *= lenRecip

    def minAxis( self ):
        """Returns the axis with the minimum value"""
        dir = 0
        minVal = self.x
        if ( self.y < minVal ):
            minVal = self.y
            dir = 1
        if ( self.z < minVal ):
            dir = 2
        return dir

    def minAbsAxis( self ):
        """Returns the axis with the minimum absolute magnitude"""
        dir = 0
        minVal = abs(self.x)
        if ( abs(self.y) < minVal ):
            minVal = sab(self.y)
            dir = 1
        if ( abs(self.z) < minVal ):
            dir = 2
        return dir
        
class Face:
    def __init__( self, v = None, vn = None, vt = None ):
        if ( v == None ):
            self.verts = []
        else:
            self.verts = v
        if ( vn == None ):
            self.norms = []
        else:
            self.norms = vn
        if ( vt == None ):
            self.uvs = []
        else:
            self.uvs = vt

    def triangulate( self ):
        """Triangulates the face - returns a list of faces"""
        if ( len(self.verts) == 3 ):
            return [deepcopy( self ), ]
        else:
            newFaces = []
            # blindly create a fan triangulation (v1, v2, v3), (v1, v3, v4), (v1, v4, v5), etc...
            for i in range(1, len(self.verts) - 1):
                verts = [self.verts[0], self.verts[i], self.verts[i+1]]
                norms = None
                if ( self.norms ):
                    norms = [self.norms[0], self.norms[i], self.norms[i+1]]
                uvs = None
                if ( self.uvs ):
                    uvs = [self.uvs[0], self.uvs[i], self.uvs[i+1]]
                newFaces.append( Face( verts, norms, uvs ) )
            return newFaces
                

    def OBJFormat( self ):
        """Writes face definition in OBJ format"""
        s = 'f '
        vIndex = 0
        for v in self.verts:
            s += '%d' % v
            if ( self.uvs ):
                s += '/%d' % self.uvs[vIndex]
            if ( self.norms ):
                if (not self.uvs ):
                    s += '/'
                s += '/%d' % self.norms[vIndex]
            s += ' '
            vIndex += 1
        return s

    def PLYAsciiFormat( self, useNorms = False, useUvs = False ):
        """Writes face definition in PLY format"""
        s = '%d ' % (len(self.verts))
        vIndex = 0
        for v in self.verts:
            s += '%d' % ( v - 1 )
##            if ( self.uvs ):
##                s += '/%d' % self.uvs[vIndex]
##            if ( self.norms ):
##                if (not self.uvs ):
##                    s += '/'
##                s += '/%d' % self.norms[vIndex]
            s += ' '
            vIndex += 1
        return s    

    def PLYBinaryFormat( self, useNorms = False, useUvs = False ):
        """Writes face definition in PLY format"""
        s = pack('>b', len(self.verts) )
##        vIndex = 0
        for v in self.verts:
            s += pack('>i', ( v - 1 ) )
##            if ( self.uvs ):
##                s += '/%d' % self.uvs[vIndex]
##            if ( self.norms ):
##                if (not self.uvs ):
##                    s += '/'
##                s += '/%d' % self.norms[vIndex]
##            vIndex += 1
        return s            

class Vertex:
    def __init__( self, x, y, z ):
        self.pos = (x, y, z)

    def formatOBJ( self ):
        """Returns a string that represents this vertex"""
        return "v %f %f %f" % ( self.pos[0], self.pos[1], self.pos[2] )

    def asciiPlyHeader( self, count ):
        """Returns the header for this element in ply format"""
        s = 'element vertex %d\n' % ( count )
        s += 'property float x\n'
        s += 'property float y\n'
        s += 'property float z\n'
        return s
    
    def formatPLYAscii( self ):
        """Returns a string that represents this vertex in ascii ply format"""
        return "%f %f %f" % ( self.pos[0], self.pos[1], self.pos[2] )

    def binPlyHeader( self, count ):
        """Returns the header for this element in binary ply format"""
        s = 'element vertex %d\x0a' % ( count )
        s += 'property float x\x0a'
        s += 'property float y\x0a'
        s += 'property float z\x0a'
        return s

    def formatPlyBinary( self ):
        """Returns a string that represents this vertex in binary PLY format"""
        return pack('>fff', v.x, v.y, v.z)

class ColoredVertex( Vertex ):
    DEF_COLOR = ( 0, 60, 120 )
    def __init__( self, color = None ):
        Vertex.__init__( self )
        if ( color == None ):
            self.color = ColoredVertex.DEF_COLOR
        else:
            self.color = color

    def asciiPlyHeader( self, count ):
        """Returns the header for this element in ply format"""
        s = Vertex.asciiPlyHeader( self, count )
        s += 'property uchar red\n'
        s += 'property uchar green\n'
        s += 'property uchar blue\n'
        return s
    
    def formatPLYAscii( self ):
        """Returns a string that represents this vertex in ascii ply format"""
        return "%f %f %f %d %d %d" % ( self.pos[0], self.pos[1], self.pos[2],
                                       self.color[0], self.color[1], self.color[2] )

    def binPlyHeader( self, count ):
        """Returns the header for this element in binary ply format"""
        s = Vertex.binPlyHeader( self, count )
        s += 'property uchar red\x0a'
        s += 'property uchar green\x0a'
        s += 'property uchar blue\x0a'
        return s

    def formatPlyBinary( self ):
        """Returns a string that represents this vertex in binary PLY format"""
        return Vertex.formatPlyBinary( self ) + pack('>BBB', color[0], color[1], color[2])    
            
        
if __name__ == "__main__":
    print "TESTING PRIMITIVES"
    v2 = Vector2( 0.3, 0.9 )
    print v2
    v3 = Vector3( 1.2, 15.3, 100.0 )
    print v3
        