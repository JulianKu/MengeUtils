# This file contain Abstract Grida and Grid which is used in computing density

import numpy as np
import math
import random
from Kernels import *
from primitives import Vector2

BUFFER_DIST = 0.46  # Based on Proxemics for Close Perosnal Distance

class AbstractGrid:
    '''A class to index into an abstract grid'''
    def __init__( self, minCorner, size, resolution ):
        self.minCorner = minCorner          # tuple (x, y)  - float
        self.size = size                    # tuple (x, y)  - float
        self.resolution = resolution        # tuple (x, y)  - int
        # size of each cell in the world grid (not the kernel)
        self.cellSize = Vector2( size.x / float( resolution[0] ), size.y / float( resolution[1] ) )  

    def getCenter( self, position ):
        """Returns the closest cell center to this position"""
        # offset in euclidian space
        offset = position - self.minCorner
        # offset in cell sizes
        ofX = offset.x / self.cellSize.x
        ofY = offset.y / self.cellSize.y
        x = int( ofX )
        y = int( ofY )
        return x, y

class DataGrid( AbstractGrid) :
    """A Class to stroe information in grid based structure (i.e the one in Voronoi class ) """
    def __init__( self, minCorner, size, resolution, initVal=0.0 ):
        AbstractGrid.__init__( self, minCorner, size, resolution )
        self.initVal = initVal
        self.clear()

    def getCenters( self ):
        '''Return NxNx2 array of the world positions of each cell center'''
        firstCenter = self.minCorner + self.cellSize * 0.5
        x = np.arange( self.resolution.x ) * self.cellSize.x + firstCenter.x
        y = np.arange( self.resolution.y ) * self.cellSize.y + firstCenter.y
        X, Y = np.meshgrid( x, y )
        return np.dstack( (X,Y) )
           
    def __str__( self ):
        s = 'Grid'
        for row in range( self.resolution[1] - 1, -1, -1 ):
            s += '\n'
            for col in range( self.resolution[0] ):
                s += '%7.2f' % ( self.cells[ col ][ row ] )
        return s

    def clear( self ):
        # Cells are a 2D array accessible with (x, y) values
        #   x = column, y = row
        if ( self.initVal == 0 ):
            self.cells = np.zeros( ( self.resolution[0], self.resolution[1] ), dtype=np.float32 )
        else:
            self.cells = np.zeros( ( self.resolution[0], self.resolution[1] ), dtype=np.float32 ) + self.initVal

class Grid( AbstractGrid ):
    """Class to discretize scalar field computation"""
    def __init__( self, minCorner, size, resolution, domainX, domainY, initVal=0.0  ):
        """Initializes the grid to span the space starting at minCorner,
        extending size amount in each direction with resolution cells
        domainX is a Vector2 storing range of value x from user.
        domainX[0] stores min value and domainX[1] stores max value.
        domainY is a similar to domainX but in y-axis"""
        AbstractGrid.__init__( self, minCorner, size, resolution )
        self.initVal = initVal
        self.clear()
        self.domainX = domainX
        self.domainY = domainY

    def getCenters( self ):
        '''Return NxNx2 array of the world positions of each cell center'''
        firstCenter = self.minCorner + self.cellSize * 0.5
        x = np.arange( self.resolution.x ) * self.cellSize.x + firstCenter.x
        y = np.arange( self.resolution.y ) * self.cellSize.y + firstCenter.y
        X, Y = np.meshgrid( x, y )
        return np.dstack( (X,Y) )
        
       
    def __str__( self ):
        s = 'Grid'
        for row in range( self.resolution[1] - 1, -1, -1 ):
            s += '\n'
            for col in range( self.resolution[0] ):
                s += '%7.2f' % ( self.cells[ col ][ row ] )
        return s

    def binaryString( self ):
        """Produces a binary string for the data"""
        return self.cells.tostring()

    def setFromBinary( self, binary ):
        """Populates the grid values from a binary string"""
        self.cells = np.fromstring( binary, np.float32 )
        self.cells = self.cells.reshape( self.resolution )

    def __idiv__( self, scalar ):
        self.cells /= scalar
        return self

    def __imul__( self, scalar ):
        self.cells *= scalar
        return self

    def maxVal( self ):
        """Returns the maximum value of the grid"""
##        print "Max" + str(self.cells.max())
        return self.cells.max()

    def minVal( self ):
        """Returns the maximum value of the grid"""
        return self.cells.min()

    def clear( self ):
        # Cells are a 2D array accessible with (x, y) values
        #   x = column, y = row
        if ( self.initVal == 0 ):
            self.cells = np.zeros( ( self.resolution[0], self.resolution[1] ), dtype=np.float32 )
        else:
            self.cells = np.zeros( ( self.resolution[0], self.resolution[1] ), dtype=np.float32 ) + self.initVal

    def computeDistanceToWall( self, agent):
        agentPos = agent[:2,]
        # calculate the distance to wall
        distMinY = math.fabs(agentPos[1] - self.domainY[0])
        distMaxY = math.fabs(agentPos[1] - self.domainY[1])
        distMinX = math.fabs(agentPos[0] - self.domainX[0])
        distMaxX = math.fabs(agentPos[0] - self.domainX[1])
        return np.min([distMinX,distMaxX])

    def computeClosestNeighbor( self, agent, frame ):
        '''compute distance from current agent to every other. Running in O(n^2) as
            we checking one against all others'''
        agentPos = agent[:2,]
        minDist = 1000.
        distWall = self.computeDistanceToWall(agent)
        if (frame.shape[0] == 1):
            # Distance to the closet boundary
            return distWall
        for agt in frame:
            agtPos = agt[:2,]
            if (agentPos[0] == agtPos[0] and  agentPos[1] == agtPos[1]):
                # Agent and agt is the same
                continue
            # get position of the agent the world grid
            agtCenter = self.getCenter( Vector2(agtPos[0], agtPos[1]) )
            diff = agtPos - agentPos
            localMin = np.sum(diff * diff, axis=0)
            if (localMin < minDist):
                minDist = localMin
        minDist = math.sqrt(minDist)
        return np.min([distWall, minDist])

    def rasterizePosition( self, frame, distFunc, maxRad ):
        """Given a frame of agents, rasterizes the whole frame"""
        # splat the kernel centered at the grid which contain agents
        if ((distFunc != FUNC_MAPS['variable-gaussian'])):
            kernel = Kernel( maxRad, distFunc, self.cellSize )
            # This assumes the kernel dimensions are ODD-sized
            w, h = kernel.data.shape
            w /= 2
            h /= 2
            
        for agt in frame:
            print type(frame)
            print frame.shape[0]
            print frame[0,:]
            pos = agt[:2,]
            if (distFunc == FUNC_MAPS['variable-gaussian']):
##                distWall = self.computeDistanceToWall(agt)
##                print "distWall " + str(distWall)
                minRadius = self.computeClosestNeighbor(agt, frame)
                if (minRadius < BUFFER_DIST):
                    minRadius = BUFFER_DIST
                kernel = Kernel( minRadius, distFunc, self.cellSize )
                w, h = kernel.data.shape
                w /= 2
                h /= 2
            # END IF
            
            # get position of the agent the world grid
            center = self.getCenter( Vector2(pos[0], pos[1]) )
            l = center[0] - w
            r = center[0] + w + 1
            b = center[1] - h
            t = center[1] + h + 1
            kl = 0
            kb = 0
            kr, kt = kernel.data.shape
            if ( l < 0 ):
                kl -= l
                l = 0
            if ( b < 0 ):
                kb -= b
                b = 0
            if ( r >= self.resolution[0] ):
                kr -= r - self.resolution[0]
                r = self.resolution[0]
            if ( t >= self.resolution[1] ):
                kt -= t - self.resolution[1]
                t = self.resolution[1]
            try:
                if ( l < r and b < t and kl < kr and kb < kt ):
                    self.cells[ l:r, b:t ] += kernel.data[ kl:kr, kb:kt ]
            except ValueError, e:
                print "Value error!"
                print "\tAgent at", center
                print "\tGrid resolution:", self.resolution
                print "\tKernel size:", kernel.data.shape
                print "\tTrying rasterize [ %d:%d, %d:%d ] to [ %d:%d, %d:%d ]" % ( kl, kr, kb, kt, l, r, b, t)
                raise e
##        print self.cells[self.cells > 0].sum()
##        print " "

    def rasterizePosition2( self, frame, distFunc, maxRad ):
        """Given a frame of agents, rasterizes the whole frame"""
        kernel = Kernel2( maxRad, self.cellSize )
        w, h = kernel.data.shape
        w /= 2
        h /= 2
        for agt in frame.agents:
            center = self.getCenter( agt.pos )
            centerWorld = Vector2( center[0] * self.cellSize.x + self.minCorner.x,
                                   center[1] * self.cellSize.y + self.minCorner.y )
            kernel.instance( distFunc, centerWorld, agt.pos )
            l = center[0] - w
            r = center[0] + w + 1
            b = center[1] - h
            t = center[1] + h + 1
            kl = 0
            kb = 0
            kr, kt = kernel.data.shape
            if ( l < 0 ):
                kl -= l
                l = 0
            if ( b < 0 ):
                kb -= b
                b = 0
            if ( r >= self.resolution[0] ):
                kr -= r - self.resolution[0]
                r = self.resolution[0]
            if ( t >= self.resolution[1] ):
                kt -= t - self.resolution[1]
                t = self.resolution[1]
            self.cells[ l:r, b:t ] += kernel.data[ kl:kr, kb:kt ]            

    def rasterizeValue( self, frame, distFunc, maxRad ):
        """Given a frame of agents, rasterizes the whole frame"""
        kernel = Kernel( maxRad, distFunc, self.cellSize )
        w, h = kernel.data.shape
        w /= 2
        h /= 2
        for agt in frame.agents:
            center = self.getCenter( agt.pos )
            l = center[0] - w
            r = center[0] + w + 1
            b = center[1] - h
            t = center[1] + h + 1
            kl = 0
            kb = 0
            kr, kt = kernel.data.shape
            if ( l < 0 ):
                kl -= l
                l = 0
            if ( b < 0 ):
                kb -= b
                b = 0
            if ( r >= self.resolution[0] ):
                kr -= r - self.resolution[0]
                r = self.resolution[0]
            if ( t >= self.resolution[1] ):
                kt -= t - self.resolution[1]
                t = self.resolution[1]
            self.cells[ l:r, b:t ] += kernel.data[ kl:kr, kb:kt ] * agt.value        

    

    def rasterizeContribSpeed( self, kernel, f2, f1, distFunc, maxRad, timeStep ):
        """Given two frames of agents, computes per-agent displacement and rasterizes the whole frame"""
        w, h = kernel.data.shape
        w /= 2
        h /= 2
        invDT = 1.0 / timeStep
        countCells = np.zeros_like( self.cells )
        maxSpd = 0
        for i in range( len ( f2.agents ) ):
            ag2 = f2.agents[ i ]
            ag1 = f1.agents[ i ]
            disp = ( ag2.pos - ag1.pos ).magnitude()
            disp *= invDT
            if ( disp > maxSpd ): maxSpd = disp
            center = self.getCenter( ag2.pos )
            l = center[0] - w
            r = center[0] + w + 1
            b = center[1] - h
            t = center[1] + h + 1
            kl = 0
            kb = 0
            kr, kt = kernel.data.shape
            if ( l < 0 ):
                kl -= l
                l = 0
            if ( b < 0 ):
                kb -= b
                b = 0
            if ( r >= self.resolution[0] ):
                kr -= r - self.resolution[0]
                r = self.resolution[0]
            if ( t >= self.resolution[1] ):
                kt -= t - self.resolution[1]
                t = self.resolution[1]
            self.cells[ l:r, b:t ] += kernel.data[ kl:kr, kb:kt ] * disp
            countCells[ l:r, b:t ] += kernel.data[ kl:kr, kb:kt ]
        countMask = countCells == 0
        countCells[ countMask ] = 1
        print "Counts: max", countCells.max(), "min:", countCells.min(),
        print "Accum max:", self.cells.max(), 
        self.cells /= countCells
        print "Max speed:", maxSpd, "max cell", self.cells.max()

    def rasterizeProgress( self, f2, initFrame, prevProgress, excludeStates=(), callBack=None ):
        '''Given the current frame and the initial frame, computes the fraction of the circle that
        each agent has travelled around the kaabah.'''
        # TODO: don't let this be periodic.
        TWO_PI = 2.0 * np.pi
        for i in range( len( f2.agents ) ):
            # first compute progress based on angle between start and current position
            ag2 = f2.agents[ i ]
            if ( ag2.state in excludeStates ): continue
            ag1 = initFrame.agents[ i ]
            dir2 = ag2.pos.normalize()
            dir1 = ag1.pos.normalize()
            angle = np.arccos( dir2.dot( dir1 ) )
            cross = dir1.det( dir2 )
            if ( cross < 0 ):
                angle = TWO_PI - angle
            progress = angle / TWO_PI

            # now determine direction from best progress so far
            
            if ( progress > prevProgress[i,2] ):
                best = Vector2( prevProgress[i,0], prevProgress[i,1] )
                cross = best.det( dir2 )
                if ( cross < 0 ):
                    # if I'm moving backwards from best progress BUT I'm apparently improving progress
                    #   I've backed over the 100% line.
                    progress = 0.0
                else:
                    prevProgress[ i, 2 ] = progress
                    prevProgress[ i, 0 ] = dir2.x
                    prevProgress[ i, 1 ] = dir2.y

            center = self.getCenter( ag2.pos )
            INFLATE = True # causes the agents to inflate more than a single cell
            if ( INFLATE ):
                l = center[0] - 1
                r = l + 3
                b = center[1] - 1
                t = b + 3
            else:
                l = center[0]
                r = l + 1
                b = center[1]
                t = b + 1
            
            if ( l < 0 ):
                l = 0
            if ( b < 0 ):
                b = 0
            if ( r >= self.resolution[0] ):
                r = self.resolution[0]
            if ( t >= self.resolution[1] ):
                t = self.resolution[1]
            self.cells[ l:r, b:t ] =  progress
            if ( callBack ):
                callBack( progress )            

    def rasterizeSpeedBlit( self, kernel, f2, f1, distFunc, maxRad, timeStep, excludeStates=(), callBack=None ):
        """Given two frames of agents, computes per-agent displacement and rasterizes the whole frame"""
        invDT = 1.0 / timeStep
        for i in range( len ( f2.agents ) ):
            ag2 = f2.agents[ i ]
            if ( ag2.state in excludeStates ): continue
            ag1 = f1.agents[ i ]
            disp = ( ag2.pos - ag1.pos ).magnitude()
            disp *= invDT
            if ( disp > 3.0 ): continue
            center = self.getCenter( ag2.pos )

            INFLATE = True # causes the agents to inflate more than a single cell
            if ( INFLATE ):
                l = center[0] - 1
                r = l + 3
                b = center[1] - 1
                t = b + 3
            else:
                l = center[0]
                r = l + 1
                b = center[1]
                t = b + 1
            
            if ( l < 0 ):
                l = 0
            if ( b < 0 ):
                b = 0
            if ( r >= self.resolution[0] ):
                r = self.resolution[0]
            if ( t >= self.resolution[1] ):
                t = self.resolution[1]
            self.cells[ l:r, b:t ] =  disp
            if ( callBack ):
                callBack( disp )

    def rasterizeOmegaBlit( self, kernel, f2, f1, distFunc, maxRad, timeStep, excludeStates=(), callBack=None ):
        """Given two frames of agents, computes per-agent angular speed and rasterizes the whole frame"""
        invDT = 1.0 / timeStep
        RAD_TO_ANGLE = 180.0 / np.pi * invDT
        for i in range( len ( f2.agents ) ):
            # compute the angle around the origin
            ag2 = f2.agents[ i ]
            if ( ag2.state in excludeStates ): continue
            ag1 = f1.agents[ i ]
            dir2 = ag2.pos.normalize()
            dir1 = ag1.pos.normalize()
            angle = np.arccos( dir2.dot( dir1 ) ) * RAD_TO_ANGLE
            cross = dir1.det( dir2 )
            if ( cross < 0 ):
                angle = -angle
                
            center = self.getCenter( ag2.pos )
            INFLATE = True # causes the agents to inflate more than a single cell
            if ( INFLATE ):
                l = center[0] - 1
                r = l + 3
                b = center[1] - 1
                t = b + 3
            else:
                l = center[0]
                r = l + 1
                b = center[1]
                t = b + 1
            
            if ( l < 0 ):
                l = 0
            if ( b < 0 ):
                b = 0
            if ( r >= self.resolution[0] ):
                r = self.resolution[0]
            if ( t >= self.resolution[1] ):
                t = self.resolution[1]
            self.cells[ l:r, b:t ] =  angle
            if ( callBack ):
                callBack( angle )


    def rasterizeDenseSpeed( self, denseFile, kernel, f2, f1, distFunc, maxRad, timeStep ):
        '''GIven two frames of agents, computes per-agent speed and rasterizes the whole frame.agents
        Divides the rasterized speeds by density from the denseFile'''
        w, h = kernel.data.shape
        w /= 2
        h /= 2
        invDT = 1.0 / timeStep
        countCells = np.zeros_like( self.cells )
        maxSpd = 0
        for i in range( len ( f2.agents ) ):
            ag2 = f2.agents[ i ]
            ag1 = f1.agents[ i ]
            disp = ( ag2.pos - ag1.pos ).magnitude()
            disp *= invDT
            if ( disp > maxSpd ): maxSpd = disp
            center = self.getCenter( ag2.pos )
            l = center[0] - w
            r = center[0] + w + 1
            b = center[1] - h
            t = center[1] + h + 1
            kl = 0
            kb = 0
            kr, kt = kernel.data.shape
            if ( l < 0 ):
                kl -= l
                l = 0
            if ( b < 0 ):
                kb -= b
                b = 0
            if ( r >= self.resolution[0] ):
                kr -= r - self.resolution[0]
                r = self.resolution[0]
            if ( t >= self.resolution[1] ):
                kt -= t - self.resolution[1]
                t = self.resolution[1]
            self.cells[ l:r, b:t ] += kernel.data[ kl:kr, kb:kt ] * disp
        dataStr = denseFile.read( self.resolution[0] * self.resolution[1] * 4 ) # total floats X 4 bytes per float
        density = np.fromstring( dataStr, dtype=np.float32 )
##        density[ density == 0 ] = 1
        density = density.reshape( self.cells.shape )
##        density[ density == 0 ] = 1
        print "Density: max", density.max(), "min:", density.min(),
        print "Accum max:", self.cells.max(), 
##        self.cells /= density
        print "Max speed:", maxSpd, "max cell", self.cells.max()
        
    def rasterizeSpeedGauss( self, kernel, f2, f1, distFunc, maxRad, timeStep ):
        """Given two frames of agents, computes per-agent displacement and rasterizes the whole frame"""
        w, h = kernel.data.shape
        w /= 2
        h /= 2
        invDT = 1.0 / timeStep
        for i in range( len ( f2.agents ) ):
            ag2 = f2.agents[ i ]
            ag1 = f1.agents[ i ]
            disp = ( ag2.pos - ag1.pos ).magnitude()
            disp *= invDT
            center = self.getCenter( ag2.pos )
            l = center[0] - w
            r = center[0] + w + 1
            b = center[1] - h
            t = center[1] + h + 1
            kl = 0
            kb = 0
            kr, kt = kernel.data.shape
            if ( l < 0 ):
                kl -= l
                l = 0
            if ( b < 0 ):
                kb -= b
                b = 0
            if ( r >= self.resolution[0] ):
                kr -= r - self.resolution[0]
                r = self.resolution[0]
            if ( t >= self.resolution[1] ):
                kt -= t - self.resolution[1]
                t = self.resolution[1]
            self.cells[ l:r, b:t ] += kernel.data[ kl:kr, kb:kt ] * disp

    def rasterizeVelocity( self, X, Y, kernel, f2, f1, distFunc, maxRad, timeStep ):
        """Given two frames of agents, computes per-agent displacement and rasterizes the whole frame"""
        w, h = kernel.data.shape
        w /= 2
        h /= 2
        invDT = 1.0 / timeStep
        X.fill( 0.0 )
        Y.fill( 0.0 )
        for i in range( len ( f2.agents ) ):
            ag2 = f2.agents[ i ]
            ag1 = f1.agents[ i ]
            disp = ag2.pos - ag1.pos
            disp *= invDT
            center = self.getCenter( ag2.pos )
            l = center[0] - w
            r = center[0] + w + 1
            b = center[1] - h
            t = center[1] + h + 1
            kl = 0
            kb = 0
            kr, kt = kernel.data.shape
            if ( l < 0 ):
                kl -= l
                l = 0
            if ( b < 0 ):
                kb -= b
                b = 0
            if ( r >= self.resolution[0] ):
                kr -= r - self.resolution[0]
                r = self.resolution[0]
            if ( t >= self.resolution[1] ):
                kt -= t - self.resolution[1]
                t = self.resolution[1]
            X[ l:r, b:t ] += kernel.data[ kl:kr, kb:kt ] * disp.x
            Y[ l:r, b:t ] += kernel.data[ kl:kr, kb:kt ] * disp.y
        self.cells = X + Y
        #self.cells = np.sqrt( X * X + Y * Y )

    def surface( self, map, minVal, maxVal ):
        """Creates a pygame surface"""
        return map.colorOnSurface( (minVal, maxVal ), self.cells )

    def swapValues( self, oldVal, newVal ):
        """Replaces all cells with the value oldVal with newVal"""
        self.cells[ self.cells == oldVal ] = newVal

    def clampMax( self, maxValue ):
        '''Makes sure that the grid contains no value greater than maxValue'''
        self.cells[ self.cells > maxValue ] = maxValue