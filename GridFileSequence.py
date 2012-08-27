# This file contain GridFileSquence class which create grid for squence of frame

import numpy as np
import struct
import threading
import time
import multiprocessing

from Grid import *
from RasterGrid import Grid
from primitives import Vector2
from ThreadRasterization import *

# the thread that does the file output
def threadOutput( outFile, buffer, bufferLock, startTime ):
    """Reads grids from the buffer and writes them to the output file"""
    nextGrid = 0
    while ( buffer or ACTIVE_RASTER_THREADS ):
        # keep doing the work as long as the buffer has contents or there are active raster threads
        bufferLock.acquire()
        try:
            i = buffer.index( nextGrid )
            bg = buffer.pop( i )
            bufferLock.release()
            print "\t\tWriting buffer %d at time %f s" % ( nextGrid, time.clock() - startTime )
            outFile.write( bg.grid.binaryString() )
            nextGrid += 1
        except ValueError:
            bufferLock.release()
            time.sleep( 1.0 )

class RasterReport:
    """Simple class to return the results of rasterization"""
    def __init__( self ):
        self.maxVal = 0.0
        self.count = 0

    def incCount( self ):
        self.count += 1

    def setMax( self, val ):
        if ( val > self.maxVal ):
            self.maxVal = val

# A mapping of numpy array type to an int iterator for storing in the file
NP_TYPES = ( np.float32, np.float64, np.float96, np.int8, np.int16, np.int32, np.int64 )
TYPE_ID_MAP = dict( map( lambda x: ( x[1], x[0] ), enumerate( NP_TYPES ) ) )


class GridFileSequenceReader:
    '''A simple class for reading and iterating through a GridFileSequence'''
    def __init__( self, fileName, startGrid=0, maxGrids=-1, gridStep=1 ):
        '''Initializes the reader to a particular file.

        @param      fileName        A string.  The path to a grid file sequence file.
        @param      startGrid       An int.  The first grid to return in the sequence.
                                    (Defaults to 0, the first grid.)
        @param      maxGrids        An int.  The maximum number of grids to iterate through.
                                    If negative, all grids in the file will be used.  If
                                    non-negative, it iterates through min( maxGrids, count).
        @param      gridStep        An int.  The stride between accessible grids.
                                    The default is 1 (every grid.)
        @raises     IOError if the file doesn't exist.
        '''
        self.file = open( fileName, 'rb' )
        # read the header
        self.readHeader()
        self.currGridID = 0
        self.startGrid = startGrid
        if ( maxGrids == -1 ):
            self.maxGrids = self.count
        else:
            self.maxGrids = min( self.count, self.maxGrids )
        assert( gridStep > 0 )
        self.gridStride = self.gridSize() * ( gridStep - 1 )
        self.currGrid = np.empty( ( self.w, self.h ), dtype=self.arrayType )

    def summary( self ):
        '''Produces a string which summarizes the sequence'''
        s = "Grid file sequence"
        s += "\n\tMinimum corner: (%.2f, %.2f)" % ( self.corner[0], self.corner[1] )
        s += '\n\tSize:           (%.2f, %.2f)' % ( self.size[0], self.size[1] )
        s += '\n\tResolution:     (%d, %d )' % ( self.w, self.h )
        s += '\n\tGrid count:     %d' % self.count
        s += '\n\tData type:      %s' % str( self.arrayType )
        s += '\n\tData range:     (%s, %s)' % ( str( self.range[0] ), str( self.range[1] ) )
        return s

    def readHeader( self ):
        '''Reads the header of the open file.'''
        corner = struct.unpack( 'ff', self.file.read( 8 ) )
        self.corner = Vector2( corner[0], corner[1] )
        size = struct.unpack( 'ff', self.file.read( 8 ) )
        self.size = Vector2( size[0], size[1] )
        self.w, self.h = struct.unpack( 'ii', self.file.read( 8 ) )
        self.arrayType = np.dtype( NP_TYPES[ struct.unpack( 'i', self.file.read( 4 ) )[0] ] )
        self.count = struct.unpack( 'i', self.file.read( 4 ) )[0]
        self.range = struct.unpack( self.arrayType.char * 2, self.file.read( self.arrayType.itemsize * 2 ) )
        self.headerSize = 32 + self.arrayType.itemsize * 2

    def gridSize( self ):
        '''Returns the size of a grid in bytes.capitalize

        @returns    The number of bytes in a single frame
        '''
        return self.w * self.h * 4

    def gridCount( self ):
        '''Returns the number of grids in the sequence.

        @returns    An int.  The number of grids (not in the file, but the number
                    to be iterated across accounting for startGrid, maxGrids and gridStep.'''
        return self.maxGrids

    def __iter__( self ):
        '''Returns an iterator to the grids (it is itself).

        The iterator continues from the current state of the reader.  I.e. if it is currently on
        frame 5, the iterator will start on frame 5.  It is the responsibility of the caller to
        call setNext(0) on the sequence before using it as an interable if the caller wants to
        iterate over all values.
        '''
        return self

    def setNext( self, gridID ):
        '''Sets the reader so that the grid returned on the next invocaiton of "next" is gridID.

        @param      gridID      An int.  The index of the next next grid.  Should be in the range [0, self.count ).
        '''
        assert( gridID >= 0 and gridID <= self.maxGrids )
        if ( gridID > self.maxGrids ):
            self.currGridID = self.maxGrids
        else:
            self.currGridID = gridID - 1
            size = self.gridSize()
            byteAddr = self.headerSize + self.startGrid * size + ( gridID * self.gridStride )
            self.file.seek( byteAddr )
        
    def next( self ):
        '''Returns the next frame in the sequence.

        @returns        A 2-tuple ( grid, gridID ).  It returns a numpy array consisting of the
                        grid (with shape ( self.w, self.h )) and the index of that grid.  The
                        index value is with respect to the stride and starting grid.
        @raises         StopIteration when there are no more grids.
        '''
        if ( self.currGridID + 1 >= self.maxGrids ):
            raise StopIteration
        dataCount = self.w * self.h
        try:
            self.currGrid[:, :] = np.reshape( np.fromstring( self.file.read( self.gridSize() ), self.arrayType, dataCount), ( self.w, self.h ) )
        except ValueError:
            raise StopIteration
        self.currGridID += 1
        if ( self.gridStride ):
            self.file.seek( self.gridStride )
        return self.currGrid, self.currGridID
    
class GridFileSequence:
    """Creates a grid sequence from a frame file and streams the resulting grids to
       a file"""
    # different ways of visualizing speed
    BLIT_SPEED = 0      # simply blit the agent to the cell center with his speed
    NORM_SPEED = 1      # distribute speed with a normalized gaussian
    UNNORM_SPEED = 2    # distribute speed with an unnormalized gaussian
    NORM_DENSE_SPEED = 3 # distribute speed with normalized gaussian and then divide by the density
    NORM_CONTRIB_SPEED = 4 # distribute speed with normalized gaussian and then divide by contribution matrix
    LAPLACE_SPEED = 5   # compute the magnitude of the laplacian of the velocity field
    
    def __init__( self, outFileName, obstacles=None, arrayType=np.float32 ):
        """Constructs a GridFileSequence which caches to the indicated file name.

        @param  outFileName     The name of the file to which the gridFileSequence writes.
        @param  obstacles       An optional obstacleHandler object.  Used for obstacle-dependent
                                computations.
        @param  arrayType       A numpy datatype.  Defaults to np.float32.
        """
        self.outFileName = outFileName
        # TODO: This currently doesn't have any effect.  Eventually, it can be used for object-aware convolution
        #   or other operations.
        self.obstacles = obstacles
        self.arrayType = np.dtype( arrayType )
        self.headerSize = 40    # this assumes that the arrayType is np.float32

    def header( self, corner, size, resolution ):
        '''Prepares a string for the header of the grid file sequence.

        It is assumed that some of the information is unknown (min/max vals, grid count) and zero
        place holders will be inserted for later replacement.

        @param      corner      A Vector2 instance.  The left-bottom corner of the grid's domain 
                                (i.e. the minimum x- and y-values).
        @param      size        A Vector2 instance.  The width and height of the grid's domain.
        @param      resolution  A 2-tuple of ints.  Indicates the (width, height) of the grid.
        @returns    A binary string which represents the header information for this file sequence.
        '''
        s = struct.pack( 'ff', corner[0], corner[1] )           # minimum corner of grid
        s += struct.pack( 'ff', size[0], size[1] )              # domain width and height
        s += struct.pack( 'ii', resolution[0], resolution[1] )  # size of grid (cell counts)
        s += struct.pack( 'i', TYPE_ID_MAP[ self.arrayType.type ] )  # the data type of the grids
        s += struct.pack( 'i', 0 )                              # grid count
        s += struct.pack( 2 * self.arrayType.char, 0, 0 )       # range of grid values
        self.headerSize = len( s )
        return s

    def fillInHeader( self, file, gridCount, minVal, maxVal ):
        '''Writes the final grid count, minimum and maximum values to the file's header section.

        This assumes that the original header had been already written and the sequence has been
        fully created and written to the file.  Now, the post hoc derived values must be set into
        the header.

        @param      file        An open file object.
        @param      gridCount   An int.  The number of grids in the file.
        @param      minVal      A value of type self.arrayType. The minimum value across all grids.
        @param      maxVal      A value of type self.arrayType. The maximum value across all grids.
        '''
        file.seek( 28 )
        file.write( struct.pack( 'i', gridCount ) )
        file.write( struct.pack( 2 * self.arrayType.char, minVal, maxVal ) )

    def renderTraces( self, minCorner, size, resolution, frameSet, preWindow, postWindow, fileBase ):
        """Creates a sequence of images of the traces of the agents.

        The trace extends temporally backwards preWindow frames.
        The trace extends temporally forwards postWindow frames.
        The dimensions of the rasterized grid are determined by: minCorner, size, resolution.
        The rendered colors are then output via the colorMap and fileBase name.
        """
        renderTraces( minCorner, size, resolution, frameSet, preWindow, postWindow, fileBase )

    def computeDensity( self, gridDomain, kernel, signal, frameSet ):
        '''Creates a binary file representing the density scalar fields of each frame of the
            pedestrian data.append

        @param      gridDomain      An instance of AbstractGrid, specifying the grid domain
                                    and resolution over which the density field is calculated.
        @param      kernel          The kernel to be used to create the scalar field.  It is
                                    convolved with the pedestrian data.
        @param      signal          An instance of the signal type to be convolved.  It includes the
                                    signal domain.  The data for the signal is set in each iteration
                                    by the data in frameSet.
        @param      frameSet        An instance of a pedestrian data sequence (could be simulated
                                    or real data.  It could be a sequence of voronoi diagrams.
        '''
        global ACTIVE_RASTER_THREADS

        THREAD_COUNT = multiprocessing.cpu_count()
        # file output
        outFile = open( self.outFileName + '.density', 'wb' )
        outFile.write( self.header( gridDomain.minCorner, gridDomain.size, gridDomain.resolution ) )
        buffer = []
        bufferLock = threading.Lock()
        saveThread = threading.Thread( target=threadOutput, args=(outFile, buffer, bufferLock, time.clock() ) )
        ACTIVE_RASTER_THREADS = THREAD_COUNT
        saveThread.start()

        # prepare rasterization        
        frameSet.setNext( 0 )
        frameLock = threading.Lock()
        rasterThreads = []
        rasterLogs = []
        for i in range( THREAD_COUNT ):
            rasterLogs.append( RasterReport() )
            # This has self.obstacles
            rasterThreads.append( threading.Thread( target=threadConvolve, args=( rasterLogs[-1], bufferLock, buffer, frameLock,
                                                                                   signal.copyEmpty(), frameSet, gridDomain, kernel )
                                                    )  )

        for i in range( THREAD_COUNT ):
            rasterThreads[i].start()
        for i in range( THREAD_COUNT ):
            rasterThreads[i].join()
            ACTIVE_RASTER_THREADS -= 1
        saveThread.join()

        gridCount = 0
        maxVal = 0.0
        for log in rasterLogs:
            gridCount += log.count
            if ( log.maxVal > maxVal ):
                maxVal = log.maxVal

        # add the additional information about grid count and maximum values
        self.fillInHeader( outFile, gridCount, 0.0, maxVal )
        outFile.close()
        
##    def computeDensityStandard( self, minCorner, size, resolution, defineRegionX,
##                                defineRegionY, frameSet, isVoronoi ):
##        '''Creates a binary file representing the density scalar fields of each frame
##        @param defineRegionX: a pair of minimum and maximum to define region in x axis
##        @param defineRegionY: a pair of center and width to define region in y axis'''
##        global ACTIVE_RASTER_THREADS
##
##        THREAD_COUNT = multiprocessing.cpu_count()
##        # file output
##        outFile = open( self.outFileName + '.density', 'wb' )
##        outFile.write( struct.pack( 'ii', resolution[0], resolution[1] ) )  # size of grid
##        outFile.write( struct.pack( 'i', 0 ) )                              # grid count
##        outFile.write( struct.pack( 'ff', 0.0, 0.0 ) )                      # range of grid values
##        buffer = []
##        bufferLock = threading.Lock()
##        saveThread = threading.Thread( target=threadOutput, args=(outFile, buffer, bufferLock, time.clock() ) )
##        ACTIVE_RASTER_THREADS = THREAD_COUNT
##        saveThread.start()
##
##        # prepare rasterization        
##        frameSet.setNext( 0 )
##        frameLock = threading.Lock()
##        rasterThreads = []
##        rasterLogs = []
##
##        for i in range( THREAD_COUNT ):
##            rasterLogs.append( RasterReport() )
##            if( isVoronoi ):
##                print "Voronoi Computation"
##                print defineRegionX
##                # Compute boundary in y-axis
##                left = defineRegionY[0] - defineRegionY[1] * 0.5
##                right = defineRegionY[0] + defineRegionY[1] * 0.5
##                area = (right-left) * ( defineRegionX[1] - defineRegionX[0] )
##                cellSize = Vector2( size.x/float( resolution[0] ),
##                                    size.y/float( resolution[1] ) )
##                print "\n defineRegionX %f %f" % ( defineRegionX[0], defineRegionX[1] )
##                print "\n defineRegionY %f %f" % ( left, right )
##                # Convert to grid space
##                offset0 = Vector2( defineRegionX[0], left ) - minCorner
##                offset1 = Vector2( defineRegionX[1], right ) - minCorner
##                ofX0 = offset0.x/cellSize.x
##                ofX1 = offset1.x/cellSize.x
##                ofY0 = offset0.y/cellSize.y
##                ofY1 = offset1.y/cellSize.y
##                # Grid space index
##                boundIndexX = ( ofX0, ofX1 )
##                boundIndexY = ( ofY0, ofY1 )
##                rasterThreads.append( threading.Thread( target=threadStandardVoronoiRasterize,
##                                                       args=( rasterLogs[-1], bufferLock,
##                                                              buffer, frameLock, frameSet,
##                                                              minCorner, size, resolution,
##                                                              boundIndexX, boundIndexY, area,
##                                                              self.domainX, self.domainY, self.obstacles ) ) )
##            else:
##                print "Standard computation"
##                rasterThreads.append( threading.Thread( target=threadStandardRasterize,
##                                                        args=( rasterLogs[-1],bufferLock,
##                                                               buffer, frameLock, frameSet,
##                                                               minCorner, size, resolution,
##                                                               defineRegionX, defineRegionY,
##                                                               self.domainX, self.domainY ) ) )
##            
##        for i in range( THREAD_COUNT ):
##            rasterThreads[i].start()
##        for i in range( THREAD_COUNT ):
##            rasterThreads[i].join()
##            ACTIVE_RASTER_THREADS -= 1
##        saveThread.join()
##
##        gridCount = 0
##        maxVal = 0.0
##        for log in rasterLogs:
##            gridCount += log.count
##            if ( log.maxVal > maxVal ):
##                maxVal = log.maxVal
##
##        # add the additional information about grid count and maximum values            
##        self.fillInHeader( outFile, gridCount, 0.0, maxVal )
##        outFile.close()

    def splatAgents( self, minCorner, size, resolution, radius, frameSet ):
        '''Simply splats the agents onto the grid'''
        print "Splatting agents:"
        print "\tminCorner:  ", minCorner
        print "\tsize:       ", size
        print "\tresolution: ", resolution
        print "\tradius:     ", radius
        outFile = open( self.outFileName + '.splat', 'wb' )
        outFile.write( self.header( minCorner, size, resolution ) )
        
        frameSet.setNext( 0 )

        # all of this together should make a function which draws filled-in circles
        #   at APPROXIMATELY the center of the agents.
        maxRad = radius / 3.0   # this makes it work with the kernel generation
        def inCircle( dispX, dispY, rSqd ):
            dispSqd = ( dispX * dispX + dispY * dispY )
            return ( dispSqd <= rSqd ) * 1.0
        dFunc = lambda x, y: inCircle( x, y, radius * radius )

        gridCount = 0        
        while ( True ):
            try:
                frame, index = frameSet.next()
            except StopIteration:
                break
            grid = Grid( minCorner, size, resolution, 0.0 )
            
            grid.rasterizePosition( frame, dFunc, maxRad )
            outFile.write( grid.binaryString() )
            gridCount += 1
            
        self.fillInHeader( outFile, gridCount, 0.0, 1.0 )
        outFile.close()
        
    def computeSpeeds( self, minCorner, size, resolution, maxRad, frameSet, timeStep, excludeStates, speedType=NORM_CONTRIB_SPEED, timeWindow=1 ):
        """Computes the displacements from one cell to the next"""
        print "Computing speeds:"
        print "\tminCorner:  ", minCorner
        print "\tsize:       ", size
        print "\tresolution: ", resolution
        print "\tmaxRad:     ", maxRad
        print "\ttime step:  ", timeStep
        print "\ttime window:", timeWindow
        outFile = open( self.outFileName + '.speed', 'wb' )
        outFile.write( self.header( minCorner, size, resolution ) )
        maxVal = -1e6
        minVal = 1e6
        gridCount = 0
        gridSize = resolution[0] * resolution[1]
        cellSize = Vector2( size.x / float( resolution[0] ), size.y / float( resolution[1] ) )
        frameSet.setNext( 0 )        
        data = [ frameSet.next() for i in range( timeWindow + 1 ) ]
        # continue while the index of the last frame on the queue is greater than the index of the first frame

        distFunc = lambda x, y: np.exp( -( (x * x + y *y) / ( maxRad * maxRad ) ) )
        print "Speedy type:", speedType
        if ( speedType == GridFileSequence.BLIT_SPEED ):
            speedFunc = Grid.rasterizeSpeedBlit
            kernel = None
            gridFunc = lambda: Grid( minCorner, size, resolution, -1.0 )
        elif ( speedType == GridFileSequence.NORM_SPEED ):
            speedFunc = Grid.rasterizeSpeedGauss
            kernel = Kernel( maxRad, distFunc, cellSize )
            gridFunc = lambda: Grid( minCorner, size, resolution )
        elif ( speedType == GridFileSequence.UNNORM_SPEED ):
            speedFunc = Grid.rasterizeSpeedGauss
            kernel = Kernel( maxRad, distFunc, cellSize )
            gridFunc = lambda: Grid( minCorner, size, resolution )
        elif ( speedType == GridFileSequence.NORM_DENSE_SPEED ):
##            try:
##                denseFile = open( self.outFileName + ".density", "rb" )
##            except:
##                print "Can't open desnity file: %.density" % ( self.outFileName )
##                raise
##            else:
##                w, h, count, minVal, maxVal = struct.unpack( 'iiiff', denseFile.read( self.headerSize ) )
##                assert( w == resolution[0] and h == resolution[1] )
##            speedFunc = lambda g, k, f2, f1, dist, rad, step: Grid.rasterizeDenseSpeed( g, denseFile, k, f2, f1, dist, rad, step )
##            kernel = Kernel( maxRad, distFunc, cellSize )
##            gridFunc = lambda: Grid( minCorner, size, resolution )
            raise ValueError, "This currently unsupported."
        elif ( speedType == GridFileSequence.NORM_CONTRIB_SPEED ):
            speedFunc = Grid.rasterizeContribSpeed
            kernel = Kernel( maxRad, distFunc, cellSize )
            gridFunc = lambda: Grid( minCorner, size, resolution )
        elif ( speedType == GridFileSequence.LAPLACE_SPEED ):
            distFunc = lambda x, y: 1.0 / ( np.pi * maxRad * maxRad ) * ((x * x + y * y - maxRad * maxRad) / (0.25 * maxRad ** 4 ) ) * np.exp( -( (x * x + y *y) / ( maxRad * maxRad ) ) )
            gridFunc = lambda: Grid( minCorner, size, resolution )
            X = np.zeros( resolution, dtype=np.float32 )
            Y = np.zeros( resolution, dtype=np.float32 )
            speedFunc = lambda g, k, f2, f1, dist, rad, step: Grid.rasterizeVelocity( g, X, Y, k, f2, f1, dist, rad, step )
            kernel = Kernel( maxRad, distFunc, cellSize )

        # TODO: This will probably break for some other speed vis method
        stats = StatRecord( frameSet.agentCount() )              
        while ( data[ -1 ][0] != None ):
            f1, i1 = data.pop(0)
            f2, i2 = data[ -1 ]
            g = gridFunc() 
            speedFunc( g, kernel, f2, f1, distFunc, maxRad, timeStep * timeWindow, excludeStates, stats )
            M = g.maxVal()
            if ( M > maxVal ):
                maxVal = M
            m = g.minVal()
            if ( m < minVal ):
                minVal = m
            outFile.write( g.binaryString() )
            gridCount += 1
            data.append( frameSet.next() )
            stats.nextFrame()

        if ( speedType != GridFileSequence.LAPLACE_SPEED ):
            minVal = 0
        # add the additional information about grid count and maximum values            
        self.fillInHeader( outFile, gridCount, minVal, maxVal )
        outFile.close()
        return stats


    def initProgress( self, frame ):
        '''A helper function for the progress compuation.  Creates an N x 3 array.ArrayType
        Columns 0 & 1 are normalized vectors pointing to the direction of the agents and
        column2 is the best progress.'''
        agtCount = len( frame.agents )
        progress = np.zeros( ( agtCount, 3 ), dtype=np.float32 )
        for i in range( agtCount ):
            agt = frame.agents[ i ]
            dir = agt.pos.normalize()
            progress[ i, 0] = dir.x
            progress[ i, 1] = dir.y
        return progress
    
    def computeProgress( self, minCorner, size, resolution, maxRad, frameSet, timeStep, excludeStates, timeWindow=1 ):
        """Computes the progress from one frame to the next - progress is measured in the fraction
        of the circle traversed from the initial position"""
        print "Computing progress:"
        print "\tminCorner:  ", minCorner
        print "\tsize:       ", size
        print "\tresolution: ", resolution
        print "\tmaxRad:     ", maxRad
        print "\ttime step:  ", timeStep
        print "\ttime window:", timeWindow
        outFile = open( self.outFileName + '.progress', 'wb' )
        outFile.write( self.header( minCorner, size, resolution ) )
        maxVal = -1e6
        minVal = 1e6
        gridCount = 0
        gridSize = resolution[0] * resolution[1]
        cellSize = Vector2( size.x / float( resolution[0] ), size.y / float( resolution[1] ) )
        frameSet.setNext( 0 )        
        data = [ frameSet.next() for i in range( timeWindow + 1 ) ]

        stats = StatRecord( frameSet.agentCount() )
        initFrame, initIndex = data[0]
        progress = self.initProgress( initFrame )
        while ( data[ -1 ][0] ):
            print '.',
            f1, i1 = data.pop(0)
            f2, i2 = data[ -1 ]
            g = Grid( minCorner, size, resolution, 100.0 ) 
            g.rasterizeProgress( f2, initFrame, progress, excludeStates, stats )

            m = g.minVal()
            if ( m < minVal ):
                minVal = m
            g.swapValues( 100.0, -100.0 )
            M = g.maxVal()
            if ( M > maxVal ):
                maxVal = M            
            
            outFile.write( g.binaryString() )
            gridCount += 1
            data.append( frameSet.next() )
            stats.nextFrame()
        print
        # add the additional information about grid count and maximum values            
        self.fillInHeader( outFile, gridCount, minVal, maxVal )
        outFile.close()
        return stats

    def computeAngularSpeeds( self, minCorner, size, resolution, maxRad, frameSet, timeStep, excludeStates, speedType=BLIT_SPEED, timeWindow=1 ):
        """Computes the displacements from one cell to the next"""
        print "Computing angular speed:"
        print "\tminCorner:  ", minCorner
        print "\tsize:       ", size
        print "\tresolution: ", resolution
        print "\tmaxRad:     ", maxRad
        print "\ttime step:  ", timeStep
        print "\ttime window:", timeWindow
        outFile = open( self.outFileName + '.omega', 'wb' )
        outFile.write( self.header( minCorner, size, resolution ) )
        maxVal = -1e6
        minVal = 1e6
        gridCount = 0
        gridSize = resolution[0] * resolution[1]
        cellSize = Vector2( size.x / float( resolution[0] ), size.y / float( resolution[1] ) )
        frameSet.setNext( 0 )        
        data = [ frameSet.next() for i in range( timeWindow + 1 ) ]
        # continue while the index of the last frame on the queue is greater than the index of the first frame

        distFunc = lambda x, y: np.exp( -( (x * x + y *y) / ( maxRad * maxRad ) ) )
        print "Speedy type:", speedType
        if ( speedType == GridFileSequence.BLIT_SPEED ):
            speedFunc = Grid.rasterizeOmegaBlit
            kernel = None
            gridFunc = lambda: Grid( minCorner, size, resolution, 720.0 )
        elif ( speedType == GridFileSequence.NORM_SPEED ):
            raise ValueError, "Compute Angular speed doesn't support normalized angular speed"
##            speedFunc = Grid.rasterizeSpeedGauss
##            kernel = Kernel( maxRad, distFunc, cellSize )
##            gridFunc = lambda: Grid( minCorner, size, resolution )
        elif ( speedType == GridFileSequence.UNNORM_SPEED ):
            raise ValueError, "Compute Angular speed doesn't support unnormalized angular speed"
##            speedFunc = Grid.rasterizeSpeedGauss
##            kernel = Kernel( maxRad, distFunc, cellSize )
##            gridFunc = lambda: Grid( minCorner, size, resolution )
        elif ( speedType == GridFileSequence.NORM_DENSE_SPEED ):
            raise ValueError, "Compute Angular speed doesn't support normalized density angular speed"
##            try:
##                denseFile = open( self.outFileName + ".density", "rb" )
##            except:
##                print "Can't open desnity file: %.density" % ( self.outFileName )
##                raise
##            else:
##                w, h, count, minVal, maxVal = struct.unpack( 'iiiff', denseFile.read( self.headerSize ) )
##                assert( w == resolution[0] and h == resolution[1] )
##            speedFunc = lambda g, k, f2, f1, dist, rad, step: Grid.rasterizeDenseSpeed( g, denseFile, k, f2, f1, dist, rad, step )
##            kernel = Kernel( maxRad, distFunc, cellSize )
##            gridFunc = lambda: Grid( minCorner, size, resolution )
        elif ( speedType == GridFileSequence.NORM_CONTRIB_SPEED ):
            raise ValueError, "Compute Angular speed doesn't support normalized contribution angular speed"
##            speedFunc = Grid.rasterizeContribSpeed
##            kernel = Kernel( maxRad, distFunc, cellSize )
##            gridFunc = lambda: Grid( minCorner, size, resolution )
        elif ( speedType == GridFileSequence.LAPLACE_SPEED ):
            raise ValueError, "Compute Angular speed doesn't support laplacian angular speed"
##            distFunc = lambda x, y: 1.0 / ( np.pi * maxRad * maxRad ) * ((x * x + y * y - maxRad * maxRad) / (0.25 * maxRad ** 4 ) ) * np.exp( -( (x * x + y *y) / ( maxRad * maxRad ) ) )
##            gridFunc = lambda: Grid( minCorner, size, resolution )
##            X = np.zeros( resolution, dtype=np.float32 )
##            Y = np.zeros( resolution, dtype=np.float32 )
##            speedFunc = lambda g, k, f2, f1, dist, rad, step: Grid.rasterizeVelocity( g, X, Y, k, f2, f1, dist, rad, step )
##            kernel = Kernel( maxRad, distFunc, cellSize )

        stats = StatRecord( frameSet.agentCount() )            
        while ( data[ -1 ][0] ): 
            f1, i1 = data.pop(0)
            f2, i2 = data[ -1 ]
            g = gridFunc() 
            speedFunc( g, kernel, f2, f1, distFunc, maxRad, timeStep * timeWindow, excludeStates, stats )
            m = g.minVal()
            if ( m < minVal ):
                minVal = m
            # swap out 720.0 value for -720
            g.swapValues( 720.0, -720.0 )
            M = g.maxVal()
            if ( M > maxVal ):
                maxVal = M
            outFile.write( g.binaryString() )
            gridCount += 1
            data.append( frameSet.next() )
            stats.nextFrame()

##        if ( speedType != GridFileSequence.LAPLACE_SPEED ):
##            minVal = 0
        # add the additional information about grid count and maximum values            
        self.fillInHeader( outFile, gridCount, minVal, maxVal )
        outFile.close()
        return stats

    def readGrid( self, g, file, gridSize, index ):
        """Returns the index grid from the given file"""
        gridSize = resolution[0] * resolution[1]
        file.seek( self.headerSize + index * gridSize )
        data = file.read( gridSize )
        g.setFromBinary( data )


    def computeAdvecFlow( self,  minCorner, size, resolution, distFunc, maxDist, kernelSize, frameSet, lines ):
        """Performs a visualization of marking agents according to their intial position w.r.t. a line"""
        # initialization
        #   Iterate through the agents on the first frame
        frameSet.setNext( 0 )
        f, i = frameSet.next()
        for agt in f.agents:
            pos = agt.pos
            minDist = 1e6
            for line in lines:
                dist = line.pointDistance( pos )
                if ( dist < minDist ):
                    minDist = dist
            agt.value = max( maxDist - minDist, 0 )

        # now iterate through each frame and rasterize it
        outFile = open( self.outFileName + '.advec', 'wb' )
        outFile.write( struct.pack( 'ii', resolution[0], resolution[1] ) )  # size of grid
        outFile.write( struct.pack( 'i', 0 ) )                              # grid count
        outFile.write( struct.pack( 'ff', 0.0, 0.0 ) )                      # range of grid values
        maxVal = 0        
        gridCount = 0
        gridSize = resolution[0] * resolution[1]
        while ( True ):
            g = Grid( minCorner, size, resolution )
            g.rasterizeValue( f, distFunc, kernelSize )
            M = g.maxVal()
            if ( M > maxVal ):
                maxVal = M
            outFile.write( g.binaryString() )
            gridCount += 1
            try:
                f, i = frameSet.next( True )
            except StopIteration:
                break

        # add the additional information about grid count and maximum values            
        self.fillInHeader( outFile, gridCount, 0.0, maxVal )
        outFile.close()               
    def computeRegionSpeed( self, frameSet, polygons, timeStep, excludeStates, timeWindow=1 ):
        '''Given an ordered set of polygons, computes the average speed for all agents in each polygon
        per time step.'''
        # NOTE: This only really applies to the tawaf.
        print "Computing regional speed:"
        print "\ttime step:       ", timeStep
        print "Number of polygons:", len(polygons)

        frameSet.setNext( 0 )        
        data = [ frameSet.next() for i in range( timeWindow + 1 ) ]

        regions = None
        speeds = []
        while ( data[ -1 ][0] ):
            f1, i1 = data.pop(0)
            f2, i2 = data[ -1 ]
            frameSpeeds, regions = findRegionSpeed( f1, f2, timeStep * timeWindow, polygons, excludeStates, regions )
            speeds.append( frameSpeeds )
            data.append( frameSet.next() )
        data = np.array( speeds )
        np.savetxt( self.outFileName + ".region", data, fmt='%.5f' )