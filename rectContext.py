# This is an OpenGL context for drawing rectangular regions
from Context import *
from primitives import Vector2
from OpenGL.GL import *
from domains import RectDomain

class GLRectDomain( RectDomain ):
    '''The GL representation of a rectangular domain'''
    def __init__( self, minCorner, size ):
        '''Constructor.

        @param  minCorner       A 2-tuple-like instance of floats.  The position, in world space,
                                of the "bottom-left" corner of the domain.  (Minimum x- and y-
                                values.
        @param  size            A 2-tuple-like instace of floats.  The span of the domain (in world
                                space.)  The maximum values of the domain are minCorner[0] + size[0]
                                and minCorner[1] + size[1], respectively.
        '''
        RectDomain.__init__( self, minCorner, size )

    def __str__( self ):
        return 'GLRectDomain ( %.2f, %.2f ) to ( %.2f, %.2f )' % ( self.minCorner[0], self.minCorner[1],
                                                                      self.minCorner[0] + self.size[0], self.minCorner[1] + self.size[1] )

    def drawGL( self, color=(0.1, 1.0, 0.1) ):
        '''Draw the rectangluar region into a GL context.

        @param      A 3-tuple of floats.  The color of the rect.
                    All values should lie in the range [0, 1], to be
                    interpreted as r, g, b color values.
        '''
        glPushAttrib( GL_COLOR_BUFFER_BIT )
        glColor3fv( color )
        glBegin( GL_LINE_STRIP )
        glVertex2f( self.minCorner[0], self.minCorner[1] )
        glVertex2f( self.minCorner[0] + self.size[0], self.minCorner[1] )
        glVertex2f( self.minCorner[0] + self.size[0], self.minCorner[1] + self.size[1] )
        glVertex2f( self.minCorner[0], self.minCorner[1] + self.size[1] )
        glVertex2f( self.minCorner[0], self.minCorner[1] )
        glEnd()
        glPopAttrib()


class RectContext( BaseContext ):
    '''Context for drawing and editing rectangular regions'''
    MIN_DRAG_DIST = 2 # the minimum drag distance (manhattan distance ) required to draw a rect
    # edit state - used for knowing what to do with the active rect and cancellation
    NO_EDIT = 0
    EDIT = 1
    ADD = 2
    def __init__( self, cancelCB=None ):
        '''Constructor.

        @param      cancelCB        A callable.  An optional callback object
                                    for when rect drawing is canceled.
        '''
        BaseContext.__init__( self )
        self.rects = []
        self.names = []

        self.activeID = -1  # the rect currently affected by modifications
        self.editState = self.NO_EDIT
        self.cancelCB = cancelCB
        
        self.active = None
        self.canDraw = False
        self.dragging = False
        # position (in screen space) of where the mouse was when the mouse button was pressed
        self.downPos = None
        self.downWorld = None

    def clear( self ):
        '''Clears out all of the rects'''
        self.rects = []
        self.names = []
        self.activeID = -1
        self.editState = self.NO_EDIT
        self.active = None
        self.canDraw = False
        self.dragging = False
        self.downPos = None

    def rectCount( self ):
        return len( self.rects )
    
    def getName( self, id ):
        '''Returns the name associated with the rect. region index, id.

        @param      id      An integer.  The index into the stored set of rects.
        @return     A string.  The stored name.
        '''
        return self.names[ id ]
    
    def getRect( self, id ):
        '''Returns the RectDomain associated with the rect index, id.

        @param      id      An integer.  The index into the stored set of rects.
        @return     An instance of a RectDomain.
        '''
        return self.rects[ id ]
    
    def addRect( self ):
        '''Causes the context to go into new RectDomain mode'''
        self.canDraw = True
        self.editState = self.ADD
        self.activeID = -1
        self.names.append( 'Rect %d' % len( self.names ) )

    def editRect( self, idx ):
        '''Edits the indicated RectDomain'''
        if ( self.editState == self.ADD): return
        if ( idx < 0 ):
            self.editState = self.NO_EDIT
            self.canDraw = False
            self.activeID = -1
        else:
            self.editState = self.EDIT
            self.canDraw = True
            self.activeID = idx

    def setName( self, idx, name ):
        '''Sets the name for the RectDomain with the given index'''
        self.names[ idx ] = name

    def deleteRect( self, idx ):
        '''Removes a RectDomain from the set'''
        assert( idx >= 0 and idx < len( self.rects ) )
        self.rects.pop( idx )
        self.names.pop( idx )
        self.activeID = -1

    def setActive( self, idx ):
        '''Sets the active rect'''
        self.activeID = idx

    def stopEdit( self ):
        '''Stops the ability to edit'''
        self.editState = self.NO_EDIT
        self.canDraw = False
        
    def toConfigString( self ):
        """Creates a parseable config string so that the context can be reconsituted"""
        s = ''
        names = self.names
        while ( len( names ) > len( self.rects ) ):
            assert( self.editState == self.ADD )
            names = names[:-1]
        s = ','.join( names ) + "~"
        for i, rect in enumerate( self.rects ):
            s += ' %.5f %.5f %.5f %.5f' % ( rect.minCorner[0], rect.minCorner[1], rect.size[0], rect.size[1] )
        return s

    def setFromString( self, s ):
        '''Parses the string created by toConfigString into a set of rects'''
        self.names = []
        self.rects = []
        self.activeID = -1
        self.editState = self.NO_EDIT
        tokens = s.split( '~' )
        assert( len( tokens ) == 2 )
        self.names = tokens[0].split( ',' )
        tokens = tokens[1].split()
        assert( len( tokens ) == len( self.names ) * 4 )
        while ( tokens ):
            minX, minY, w, h = map( lambda x: float(x), tokens[:4] )
            tokens = tokens[4:]
            self.rects.append( GLRectDomain( ( minX, minY ), ( w, h ) ) )

    def handleMouse ( self, evt, view ):
        """Detects click, drag, release and creates a rect"""
        result = ContextResult()
        try:
            event = self.canonicalEvent( evt )
        except ValueError as e:
            return result
            
        if ( not self.canDraw ):
            return result
        if ( event.noModifiers() ):
            btn = event.button
            eX = event.x
            eY = event.y
            if ( event.type == MouseEvent.DOWN ): #QtCore.QEvent.MouseButtonPress ):
                if ( btn == MouseEvent.LEFT ):
                    self.downPos = Vector2( eX, eY )
                    x, y = view.screenToWorld( ( eX, eY ) )
                    self.downWorld = ( x, y )
                    self.active = GLRectDomain( ( x, y ), ( 0, 0 ) )
                    result.set( True, True, False )
                    self.dragging = True
                elif ( btn == MouseEvent.RIGHT and self.dragging ):
                    # cancel the edit
                    if ( self.editState == self.ADD ):
                        self.editState = self.NO_EDIT
                        if ( not self.cancelCB is None ):
                            self.cancelCB()
                    canceled = self.active != None
                    self.active = None
                    self.dragging = False
                    result.set( canceled, canceled, False )
            elif ( event.type == MouseEvent.UP ):
                if ( btn == MouseEvent.LEFT and self.dragging ):
                    endPos = Vector2( eX, eY )
                    if ( (endPos - self.downPos).magnitude() >= self.MIN_DRAG_DIST  ):
                        if ( self.editState == self.ADD ):
                            self.rects.append( self.active )
                            self.editState = self.EDIT
                            self.activeID = len( self.rects ) - 1
                        elif ( self.editState == self.EDIT ):
                            assert( self.activeID > -1 )
                            self.rects[ self.activeID ] = self.active
                        self.active = None
                    self.active = None  
                    self.dragging = False
                    result.set( True, True, False )
            elif ( event.type == MouseEvent.MOVE ):
                if ( self.dragging ):
                    x, y = view.screenToWorld( ( eX, eY ) )
                    dX = x - self.downWorld[0]
                    dY = y - self.downWorld[1]
                    if ( dX < 0.0 ):
                        dX = -dX
                    else:
                        x = self.downWorld[0]
                    if ( dY < 0.0 ):
                        dY = -dY
                    else:
                        y = self.downWorld[1]
                    self.active.minCorner = ( x, y )
                    self.active.size = ( dX, dY )
                    result.set( True, True, False )
        return result

    def drawGL( self ):
        '''Basic rects are drawn in default (green), the active rect is drawn in yellow,
        and when it is being edited, the original disappears and the new rect is drawn in
        cyan.'''
        if ( self.active ):
            self.active.drawGL( ( 0.1, 1.0, 1.0 ) )
        elif ( self.activeID > -1 and self.editState != self.ADD ):
            self.rects[ self.activeID ].drawGL( ( 1.0, 1.0, 0.1 ) )
            
        for i, rect in enumerate( self.rects ):
            if ( i == self.activeID ): continue
            rect.drawGL()