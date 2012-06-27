# This file contains a function which perform thread rasterization functionality.
# It is imported into GridFileSequence file

from Grid import *

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
def threadRasterize( log, bufferLock, buffer, frameLock, frameSet, minCorner, size, resolution, distFunc, maxRad, domainX, domainY ):
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
        g.rasterizePosition( frame, distFunc, maxRad )
        # update log
        log.setMax( g.maxVal() )  # TODO :: FIX THIS PROBLEM
        log.incCount()
        # put into buffer
##        if (index == 42):
        bufferLock.acquire()
        buffer.append( BufferGrid(index, g ) )
        bufferLock.release()
##            print "INTHREAD"
##            print g.cells[g.cells > 0].sum()
##            print len(buffer)
##            gg = buffer[0]
##            print type(gg)
##            print gg.grid.cells[g.cells > 0].sum()
##        # acquire next frame
##        frameLock.acquire()
##        frame, index = frameSet.next()
##        frameLock.release()
