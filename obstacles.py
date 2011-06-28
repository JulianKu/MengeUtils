from ObjSlice import AABB, Segment, Polygon
from primitives import Vector3
# sax parser for obstacles
from xml.sax import make_parser, handler

from OpenGL.GL import *

class GLPoly ( Polygon ):
    def __init__( self ):
        Polygon.__init__( self )
        self.vStart = 0         # the index at which select values for vertices starts
        self.eStart = 0         # the index at which select values for edges starts

    def drawGL( self, select=False, selectEdges=False, editable=False ):
        if ( editable ):
            glColor3f( 0.8, 0.0, 0.0 )
        else:
            glColor3f( 0.4, 0.0, 0.0 )

        if ( selectEdges or not select or editable ):        
            for i in range( self.vertCount() - 1):
                if ( selectEdges ):
                    glLoadName( self.eStart + i )
                v1 = self.vertices[i]
                v2 = self.vertices[i+1]
                glBegin( GL_LINES )
                glVertex3f( v1.x, v1.y, 0 )
                glVertex3f( v2.x, v2.y, 0 )
                glEnd()
            if ( self.closed ):
                if ( selectEdges ):
                    glLoadName( self.eStart + self.vertCount() - 1 )
                v1 = self.vertices[0]
                v2 = self.vertices[-1]
                glBegin( GL_LINES )
                glVertex3f( v1.x, v1.y, 0 )
                glVertex3f( v2.x, v2.y, 0 )
                glEnd()
        if ( editable or ( select and not selectEdges ) ):            
            glColor3f( 0.9, 0.9, 0.0 )
            for i in range( len( self.vertices ) ):
                if ( select ):
                    glLoadName( self.vStart + i )
                v = self.vertices[ i ]
                glBegin( GL_POINTS )
                glVertex3f( v.x, v.y, 0 )
                glEnd()   
        
class ObstacleSet:
    def __init__( self ):
        self.edgeCount = 0
        self.vertCount = 0
        self.polys = []
        self.activeVert = None
        self.activeEdge = None        

    def sjguy( self ):
        s = '%d\n' % ( self.edgeCount )
        for p in self.polys:
            s += '%s' % ( p.sjguy() )
        return s
    
    def __iter__( self ):
        return self.polys.__iter__()

    def __len__( self ):
        return len( self.polys )

    def selectVertex( self, i ):
        """Selects the ith vertex in the obstacle set"""
        count = 0
        for o in self.polys:
            tempSum = count + o.vertCount()
            if ( tempSum > i ):
                localI = i - count
                return o.vertices[ localI ]
            count = tempSum

    def selectEdge( self, i ):
        """Selects the ith edge in the obstacle set"""
        count = 0
        for o in self.polys:
            tempSum = count + o.edgeCount()
            if ( tempSum > i ):
                localI = i - count
                return ( o.vertices[ localI ], o.vertices[ localI + 1 ] )
            count = tempSum

    def append( self, poly ):
        poly.vStart = self.vertCount
        poly.eStart = self.edgeCount
        self.vertCount += poly.vertCount()
        self.edgeCount += poly.edgeCount()
        self.polys.append( poly )

    def drawGL( self, select=False, selectEdges = False, editable=False ):
        glPushAttrib( GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT )
        glDisable( GL_DEPTH_TEST )
        
        for o in self.polys:
            o.drawGL( select, selectEdges, editable )
        # now highlight selected elements
        if ( self.activeVert or self.activeEdge ):
            if ( self.activeVert ):
                glPointSize( 6.0 )
                glBegin( GL_POINTS )
                glColor3f( 0.9, 0.9, 0.0 )
                glVertex3f( self.activeVert.x, self.activeVert.y, 0 )
                glEnd()
                glPointSize( 3.0 )
            elif ( self.activeEdge ):
                glLineWidth( 3.0 )
                glBegin( GL_LINES )
                v1, v2 = self.activeEdge
                glVertex3f( v1.x, v1.y, 0 )
                glVertex3f( v2.x, v2.y, 0 )
                glEnd()
                glLineWidth( 1.0 )
        glPopAttrib()               

## TODO: Write this parser
##def sjguyObstParser( fileName ):
##    '''Create an obstacle set and bounding box based on the definition of sjguy for obstacles.activeEdge
##
##    definition is simple:
##    line 0:  number of line segments
##    line 1-N: each line segment is four floats: x0, y0, x1, y1
##    '''
##    obstacles = ObstacleSet()
##    bb = AABB()
##    f = open( fileName, 'r' )
##    obstCount = -1
##    for line in f.xreadlines():
##        if ( obstCount == -1 ):
##            obstCount = int( line )
##        else:
##            tokens = line.split()
##            
##                             
##    f.close()
    def obstacleBB( self ):
        '''Returns a list of 2-tuples: (obstacle, bb)'''
        return map( lambda x: (x, x.getBB()), self.polys )

    def inflate( self, amount ):
        '''Inflates all of the obstacles by the given amount'''
        for p in self.polys:
            p.inflate( amount )
    
class ObstXMLParser(handler.ContentHandler):
    def __init__(self):
        self.bb = AABB()
        self.obstacles = ObstacleSet()
        self.currObst = None        

    def startElement(self, name, attrs):
        if ( name == 'Obstacle' ):
            # assume all obstacles have a closed attribute
            self.currObst = GLPoly()
            if ( int( attrs[ 'closed' ] ) != 0 ):
                self.currObst.closed = True
        elif ( name == 'Vertex' and self.currObst != None ):
            x = float( attrs['p_x'] )
            y = float( attrs['p_y'] )
            self.currObst.vertices.append( Vector3( x, y, 0 ) )
            
    def endElement( self, name ):
        if ( name == "Obstacle" ):
            self.currObst.close()
            self.obstacles.append( self.currObst )
            self.bb.expand( self.currObst.vertices )
            self.currObst = None
            
    def endDocument(self):
        print "Found %d obstacles" % ( len( self.obstacles ) )
        print "Overal BB:", self.bb
        print

            
def readObstacles( fileName, yFlip=False ):
    print "READ OBSTACLES: ", fileName
    if ( fileName[-3:] == 'xml' ):
        parser = make_parser()
        obstHandler = ObstXMLParser()
        parser.setContentHandler( obstHandler )
        parser.parse( fileName )
        if ( yFlip ):
            for o in obstHandler.obstacles:
                o.flipY()
            obstHandler.bb.flipY()
    elif ( fileName[ -3: ] == 'txt' ):
        raise Exception, "Invalid obstacle extension: %s" % ( fileName )
    else:
        raise Exception, "Invalid obstacle extension: %s" % ( fileName )
    return obstHandler.obstacles, obstHandler.bb

if __name__ == '__main__':
    import sys
    obstacles, bb = readObstacles( sys[1] )
    for p in obstacles.polys:
        p.inflate(3.0)
    