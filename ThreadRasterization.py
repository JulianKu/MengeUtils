# This file contains a function which perform thread rasterization functionality.
# It is imported into GridFileSequence file

from Grid import *
from Voronoi import *
import drawVoronoi

class BufferGrid:
    """Entry into a buffer for a grid"""
    def __init__( self, id, grid ):
        self.id = id
        self.grid = grid

    def __eq__( self, id ):
        return self.id == id

    def __str__( self ):
        return "BufferGrid %d, %f" % ( self.id, self.grid.maxVal() )

# The   that does the rasterization work
ACTIVE_RASTER_THREADS = 0
def threadRasterize( log, bufferLock, buffer, frameLock, frameSet,
                     minCorner, size, resolution, distFunc, maxRad,
                     domainX, domainY, obstacles=None  ):
    while ( True ):
        # create grid and rasterize
        # acquire frame
        frameLock.acquire()
        try:
            frame, index = frameSet.next()
        except StopIteration:
            break
        finally:            
            frameLock.release()
        g = Grid( minCorner, size, resolution, domainX, domainY )
        g.rasterizePosition( frame, distFunc, maxRad, obstacles )
        # update log
        log.setMax( g.maxVal() )
        log.incCount()
        # put into buffer
        bufferLock.acquire()
        buffer.append( BufferGrid(index, g ) )
        bufferLock.release()
##        # acquire next frame
##        frameLock.acquire()
##        frame, index = frameSet.next()
##        frameLock.release()

def threadVoronoiRasterize( log, bufferLock, buffer, frameLock, frameSet,
                            minCorner, size, resolution, distFunc, maxRad,
                            domainX, domainY, obstacles=None ):
    while ( True ):
        vxCell = float(size.x)/resolution.x
        vyCell = float(size.y)/resolution.y
        PADDING_RAD = 1.0
        PADDING_SIZE = Vector2( PADDING_RAD * 1./vxCell, PADDING_RAD * 1./vyCell )
        # create grid and rasterize
        # acquire frame
        frameLock.acquire()
        try:
            frame, index = frameSet.next()
        except StopIteration:
            break
        finally:            
            frameLock.release()

        # Calculate new size for Voronoi with padding
        vDomainX = Vector2( domainX[0] - PADDING_RAD, domainX[1] + PADDING_RAD)
        vDomainY = Vector2( domainY[0] - PADDING_RAD, domainY[1] + PADDING_RAD )
        vMinCorner = Vector2( vDomainX[0], vDomainY[0])
        vSize = Vector2( vDomainX[1], vDomainY[1]) - vMinCorner
        vRes = Vector2( int(vSize.x/vxCell), int(vSize.y/vyCell) )
##        g = Grid( minCorner, size, resolution, domainX, domainY )
##        vRegion = Voronoi( minCorner, size, resolution, obstacles )
        g = Grid( vMinCorner, vSize, vRes, vDomainX, vDomainY )
        vRegion = Voronoi( vMinCorner, vSize, vRes, obstacles)
        # Compute density based on Voronoi region
        densityRegion = vRegion.computeVoronoiDensity( g, frame, minCorner, size,
                                                       resolution, domainX, domainY, PADDING_SIZE, maxRad ) # Default agent radius is 1
        # TESTING : draw Voronoi diagram as image file
##        import os
##        filePath = r'\Users\ksuvee\Documents\Density_project\VoronoiRegion'
##        if ( not os.path.exists( filePath ) ):
##            os.makedirs( filePath  )
##        fileName = os.path.join( filePath, 'vRegion%s.png' % (index))
##        drawVoronoi.drawVoronoi( vRegion.ownerGrid.cells, fileName, obstacles, vRegion.ownerGrid)

        # Perform Function convolution
        densityGrid = densityRegion.rasterizeVoronoiDensity( frame, distFunc, maxRad )
##                                 
        # update log
        # print densityGrid.maxVal()
        log.setMax( densityGrid.maxVal() )
        log.incCount()
        # put into buffer
        bufferLock.acquire()
        buffer.append( BufferGrid( index, densityGrid ) )
        bufferLock.release()
        # acquire next frame ALWAYS GET COMMENT
##        frameLock.acquire()
##        frame, index = frameSet.next()
        #frameLock.release()