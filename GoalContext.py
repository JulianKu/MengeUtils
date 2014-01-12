# The interactive context for editing goals

from RoadContext import PGContext, MouseEnabled, PGMouse
from Context import BaseContext, ContextResult
import pygame
from OpenGL.GL import *
import GoalEditor
import Goals
import paths
import xml.dom as dom
from math import sqrt

class GoalContext( PGContext, MouseEnabled ):
    '''A context for drawing goal regions (for now just AABB)'''
    #TODO: Add other goal types
    HELP_TEXT = 'Goal Context' + \
                '\n\tWork with Goals and GoalSets' + \
                '\n' + \
                '\n\tLeft arrow         Select previous goal set' + \
                '\n\tRight arrow        Select next goal set' + \
                '\n\tCtrl-s             Save goal sets to "goals.xml"' + \
                '\n\tCtrl-n             Create new goal set' + \
                '\n\tCtrl-delete        Delete current goal set (and all goals)' + \
                '\n\tCtrl-x             Delete highlighted goal' + \
                '\n\tLeft click         Begin editing active goal' + \
                '\n\tp                  Create point goals' + \
                '\n\t\tLeft click       In empty space to create a point goal' +\
                '\n\t\tLeft drag        To move highlighted point goal' +\
                '\n\tc                  Create circle goals' + \
                '\n\t\tLeft click       In empty space to create a circle goal' + \
                '\n\t\tLeft click       On highlighted circle goal to begin editing' + \
                '\n\t\tLeft drag        On circle center to move' + \
                '\n\t\tLeft drag        On circle permiter to change radius' + \
                '\n\t\tLeft click       In empty space to stop editing' + \
                '\n\t\tRight click      To cancel move/radius operation or end editing' + \
                '\n\ta                  Create AABB goals' + \
                '\n\t\tLeft drag        In empty space to draw a new AABB goal' + \
                '\n\t\tLeft click       On highlighted AABB to edit' + \
                '\n\t\tLeft click       On highlighted corner to reshape AABB' + \
                '\n\t\tLeft click       In empty space to stop editing' + \
                '\n\t\tRight click      To cancel movement of AABB corner or end editing' + \
                '\n\to                 Create OBB goals' + \
                ''
    # state for acting on goal sets
    POINT = 1
    CIRCLE = 2
    AABB = 4
    OBB = 8
    CREATE = 0xf
    EDIT_POINT = 0x10
    EDIT_CIRCLE = 0xE0
    MOVE_CIRCLE = 0xA0
    SIZE_CIRCLE = 0xC0
    EDIT_AABB = 0x700
    MOVE_AABB = 0x600
    SIZE_AABB = 0x500
    EDIT_OBB = 0x800

    STATE_NAMES = { POINT:'point', CIRCLE:'circle', AABB:'AABB', OBB:'OBB',
                    EDIT_POINT:'point', EDIT_CIRCLE:'circle', EDIT_AABB:'AABB', EDIT_OBB:'OBB',
                    MOVE_CIRCLE:'circle', SIZE_CIRCLE:'circle',
                    MOVE_AABB:'AABB', SIZE_AABB:'AABB',
                    }    
    
    def __init__( self, goalEditor ):
        '''Constructor.

        @param      goalEditor       The GoalEditor instance
        '''
        PGContext.__init__( self )
        MouseEnabled.__init__( self )

        self.goalEditor = goalEditor
        self.state = self.POINT
        self.editGoal = None

        self.lastActive = 0
        
    def activate( self ):
        '''Called when the set gets activated'''
        self.goalEditor.editSet = self.lastActive
        self.goal = None
        
    def deactivate( self ):
        '''Called when the set gets activated'''
        self.lastActive = self.goalEditor.editSet
        self.goalEditor.editSet = -1
        
    def setState( self, newState ):
        '''Sets the contexts new activity state'''
        if ( self.state != newState ):
            self.state = newState
        
    def handleKeyboard( self, event, view ):
        """The context handles the keyboard event as it sees fit and reports it's status with a ContextResult"""
        result = PGContext.handleKeyboard( self, event, view )
        
        if ( not result.isHandled() ):
            mods = pygame.key.get_mods()
            hasCtrl = mods & pygame.KMOD_CTRL
            hasAlt = mods & pygame.KMOD_ALT
            hasShift = mods & pygame.KMOD_SHIFT
            noMods = not( hasShift or hasCtrl or hasAlt )

            if ( event.type == pygame.KEYDOWN ):
                if ( event.key == pygame.K_RIGHT and noMods ):
                    oldActive = self.goalEditor.editSet
                    self.goalEditor.editSet = ( self.goalEditor.editSet + 1 ) % self.goalEditor.setCount()
                    result.set( True, oldActive != self.goalEditor.editSet )
                elif ( event.key == pygame.K_LEFT and noMods ):
                    oldActive = self.goalEditor.editSet
                    self.goalEditor.editSet = ( self.goalEditor.editSet -  1 ) % self.goalEditor.setCount()
                    result.set( True, oldActive != self.goalEditor.editSet )
                elif ( event.key == pygame.K_s and hasCtrl ):
                    self.saveGoals()
                    result.set( True, False )
                elif ( event.key == pygame.K_n and hasCtrl ):
                    self.goalEditor.editSet = self.goalEditor.newSet()
                    result.set( True, True )
                elif ( event.key == pygame.K_DELETE and hasCtrl ):
                    self.goalEditor.deleteSet( self.goalEditor.editSet )
                    self.goalEditor.editSet = self.goalEditor.editSet % self.goalEditor.setCount()
                    result.set( True, True )
                elif ( event.key == pygame.K_x and hasCtrl ):
                    if ( self.goalEditor.activeGoal > -1 ):
                        self.goalEditor.deleteGoal( self.goalEditor.editSet, self.goalEditor.activeGoal )
                        if ( not self.state & self.CREATE ):
                            if ( self.state & self.EDIT_AABB ):
                                self.state = self.AABB
                            elif ( self.state & self.EDIT_CIRCLE ):
                                self.state = self.CIRCLE
                            elif ( self.state & self.EDIT_POINT ):
                                self.state = self.POINT
                            elif ( self.state & self.EDIT_OBB ):
                                self.state = self.OBB
                        self.goalEditor.activeGoal = -1
                        result.set( True, True )
                elif ( event.key == pygame.K_p and noMods ):
                    result.set( True, self.state != self.POINT )
                    self.setState( self.POINT )
                elif ( event.key == pygame.K_c and noMods ):
                    result.set( True, self.state != self.CIRCLE )
                    self.setState( self.CIRCLE )
                elif ( event.key == pygame.K_a and noMods ):
                    result.set( True, self.state != self.AABB )
                    self.setState( self.AABB )
                elif ( event.key == pygame.K_o and noMods ):
                    result.set( True, self.state != self.OBB )
                    self.setState( self.OBB )
                # TODO:
                #   Set goal weight
                #   Set goal capacity
        return result        

    def saveGoals( self, fileName='goals.txt' ):
        '''Saves the goals to the specified file.

        @param      fileName        The name to write the goals to.
        '''
        Goals.DIGITS = 2
        path = paths.getPath( fileName, False )
        print "Writing goals to:", path
        f = open( path, 'w' )
        f.write ('''<?xml version="1.0"?>
<Population >
''')
        for gs in self.goalEditor:
            node = gs.xmlElement()
            if ( node ):
                node.writexml( f, indent='    ', addindent='    ', newl='\n' )
        f.write( '\n</Population>' )
        f.close()

    def handleMouse( self, event, view ):
        """The context handles the mouse event as it sees fit and reports it's status with a ContextResult"""
        result = ContextResult()
        
        mods = pygame.key.get_mods()
        hasCtrl = mods & pygame.KMOD_CTRL
        hasAlt = mods & pygame.KMOD_ALT
        hasShift = mods & pygame.KMOD_SHIFT
        noMods = not( hasShift or hasCtrl or hasAlt )

        if ( noMods ):
            if ( event.type == pygame.MOUSEMOTION ):
                if ( self.state & self.CREATE ):
                    result.setHandled( True )
                    pX, pY = event.pos
                    selID = view.select( pX, pY, self.goalEditor )
                    result.setNeedsRedraw( selID != self.goalEditor.activeGoal )
                    self.goalEditor.activeGoal = selID
                elif ( self.state == self.EDIT_POINT ):
                    pX, pY = view.screenToWorld( event.pos )
                    self.editGoal.set( pX, pY )
                    result.set( True, True )
                elif ( self.state & self.EDIT_CIRCLE ):
                    result.setHandled( True )
                    if ( self.dragging ):
                        dX, dY = view.screenToWorld( event.pos )
                        if ( self.state == self.MOVE_CIRCLE ):
                            self.editGoal.setPos( dX, dY )
                        elif ( self.state == self.SIZE_CIRCLE ):
                            dX -= self.editGoal.p.x
                            dY -= self.editGoal.p.y
                            r = sqrt( dX * dX + dY * dY )
                            self.editGoal.setRadius( r )
                        result.set( True, True )
                    else:
                        result.setNeedsRedraw( self.setCircleEdit( event.pos, view ) )
                elif ( self.state & self.EDIT_AABB ):
                    result.setHandled( True )
                    if ( self.dragging ):
                        dX, dY = view.screenToWorld( event.pos )
                        if ( self.state == self.MOVE_AABB ):
                            self.editGoal.setMin( dX, dY )
                        elif ( self.state == self.SIZE_AABB ):
                            self.editGoal.setMax( dX, dY )
                        result.set( True, True )
                    else:
                        result.setNeedsRedraw( self.setAABBEdit( event.pos, view ) )
            elif ( event.type == pygame.MOUSEBUTTONDOWN ):
                if ( event.button == PGMouse.LEFT ):
                    self.cacheDownClick( event.pos, view.screenToWorld( event.pos ) )
                    if ( self.goalEditor.activeGoal > -1 ):
                        self.startEdit( view )
                        result.set( True, True )
                    else:
                        self.startCreate( view )
                        result.set( True, True )
                elif ( event.button == PGMouse.RIGHT ):
                    if ( self.state == self.EDIT_POINT ):
                        self.editGoal.set( self.tempValue[0], self.tempValue[1] )
                        self.editGoal = None
                        self.goalEditor.activeGoal = -1
                        self.state = self.POINT
                        result.set( True, True )
                    elif ( self.state & self.EDIT_CIRCLE ):
                        if ( self.state == self.EDIT_CIRCLE ):
                            self.editGoal = None
                            self.goalEditor.activeGoal = -1
                            self.state = self.CIRCLE
                        elif ( self.state != self.EDIT_CIRCLE ):
                            self.editGoal.set( self.tempValue[0], self.tempValue[1], self.tempValue[2] )
                            self.state = self.EDIT_CIRCLE
                            self.dragging = False
                        result.set( True, True )
                    elif ( self.state & self.EDIT_AABB ):
                        if ( self.state == self.EDIT_AABB ):
                            self.editGoal = None
                            self.goalEditor.activeGoal = -1
                            self.state = self.AABB
                        elif ( self.state != self.EDIT_AABB ):
                            self.editGoal.set( self.tempValue[0], self.tempValue[1], self.tempValue[2], self.tempValue[3] )
                            self.state = self.EDIT_AABB
                            self.dragging = False
                        result.set( True, True )
            elif ( event.type == pygame.MOUSEBUTTONUP ):
                if ( event.button == PGMouse.LEFT ):
                    if ( self.state == self.EDIT_POINT ):
                        self.state = self.POINT
                        result.set( True, True )
                    elif ( self.state & self.EDIT_CIRCLE and self.state != self.EDIT_CIRCLE ):
                        self.state = self.EDIT_CIRCLE
                        self.dragging = False
                        result.set( True, True )
                    elif ( self.state & self.EDIT_AABB and self.state != self.EDIT_AABB ):
                        self.editGoal.fixPoints()
                        self.state = self.EDIT_AABB
                        self.dragging = False
                        result.set( True, True )
        return result

    def cacheDownClick( self, screenPos, worldPos ):
        '''Caches the down click position.

        @param      screenPos       A 2-tuple of ints.  The screenspace position of the mouse.
        @param      worldPos        A 2-tuple of flaots.  The worldspace position of the mouse.
        '''
        self.downX, self.downY = screenPos
        self.downWorld = worldPos
        
    def startCreate( self, view ):
        '''Sets the state of the context to begin editing the active goal.

        @param      view        A pointer to the OpenGL viewer.
        '''
        if ( self.state == self.POINT ):
            self.editGoal = Goals.PointGoal()
            self.editGoal.set( self.downWorld[0], self.downWorld[1] )
            self.goalEditor.activeGoal = self.goalEditor.addGoal( self.goalEditor.editSet, self.editGoal )
            self.startEdit( view )
        elif ( self.state == self.CIRCLE ):
            self.editGoal = Goals.CircleGoal()
            self.editGoal.set( self.downWorld[0], self.downWorld[1], 1.0 )
            self.goalEditor.activeGoal = self.goalEditor.addGoal( self.goalEditor.editSet, self.editGoal )
            self.startEdit( view )
        elif ( self.state == self.AABB ):
            self.editGoal = Goals.AABBGoal()
            self.editGoal.set( self.downWorld[0], self.downWorld[1], self.downWorld[0], self.downWorld[1] )
            self.goalEditor.activeGoal = self.goalEditor.addGoal( self.goalEditor.editSet, self.editGoal )
            self.state = self.AABB
            self.startEdit( view )
        elif ( self.state == self.OBB ):
            pass

    def startEdit( self, view ):
        '''Sets the state of the context to begin editing the active goal.

        @param      view        A pointer to the OpenGL viewer.
        '''
        self.editGoal = self.goalEditor.getGoal( self.goalEditor.editSet, self.goalEditor.activeGoal )
        if ( isinstance( self.editGoal, Goals.CircleGoal ) ):
            self.setCircleEdit( (self.downX, self.downY ), view, True )
            if ( self.state & self.EDIT_CIRCLE and self.state != self.EDIT_CIRCLE ):
                self.tempValue = ( self.editGoal.p.x, self.editGoal.p.y, self.editGoal.r )
                self.dragging = True
        elif ( isinstance( self.editGoal, Goals.PointGoal ) ):
            self.tempValue = ( self.editGoal.p.x, self.editGoal.p.y )
            self.state = self.EDIT_POINT
        elif ( isinstance( self.editGoal, Goals.AABBGoal ) ):
            self.setAABBEdit( (self.downX, self.downY ), view, self.state == self.EDIT_AABB )
            if ( self.state & self.EDIT_AABB and self.state != self.EDIT_AABB ):
                self.tempValue = ( self.editGoal.minPt.x, self.editGoal.minPt.y, self.editGoal.maxPt.x, self.editGoal.maxPt.y )
                self.dragging = True
        elif ( isinstance( self.editGoal, Goals.OBBGoal ) ):
            self.state = self.EDIT_OBB

    def setCircleEdit( self, mousePos, view, missDeselect=False ):
        '''Sets the circle state based on the current mouse position.

        @param      mousePos        A 2-tuple of ints. The screen space coordinates of the mouse.
        @param      view            A pointer to the OpenGL viewer.
        @param      missDeselect    If the mouse isn't near the center or radius, then it deselects
                                    the active object.
        @returns    A boolean if the edit state changed.
        '''
        cX, cY = view.worldToScreen( ( self.editGoal.p.x, self.editGoal.p.y ) )
        dX = mousePos[0] - cX
        dY = mousePos[1] - cY
        distSqd = dX * dX + dY * dY
        changed = False
        if ( distSqd < 49 ):
            changed = self.state != self.MOVE_CIRCLE
            self.state = self.MOVE_CIRCLE
        else:
            rX, rY = view.worldToScreen( ( self.editGoal.r + self.editGoal.p.x, self.editGoal.p.y ) )
            radS = rX - cX
            dist = sqrt( distSqd )
            delta = abs( dist - radS )
            if ( delta < 7 ):
                changed = self.state != self.SIZE_CIRCLE
                self.state = self.SIZE_CIRCLE
            else:
                if ( missDeselect ):
                    changed = True
                    self.state = self.CIRCLE
                    self.editGoal = None
                    self.goalEditor.activeGoal = -1
                else:
                    changed =  self.state != self.EDIT_CIRCLE 
                    self.state = self.EDIT_CIRCLE
        return changed

    def setAABBEdit( self, mousePos, view, missDeselect=False ):
        '''Sets the AABB state based on the current mouse position.

        @param      mousePos        A 2-tuple of ints. The screen space coordinates of the mouse.
        @param      view            A pointer to the OpenGL viewer.
        @param      missDeselect    If True and the mouse isn't near the min or max corners, 
                                    then it deselects the active object.
        @returns    A boolean if the edit state changed.
        '''
        cX, cY = view.worldToScreen( ( self.editGoal.minPt.x, self.editGoal.minPt.y ) )
        dX = mousePos[0] - cX
        dY = mousePos[1] - cY
        distSqd = dX * dX + dY * dY
        changed = False
        if ( distSqd < 49 ):
            changed = self.state != self.MOVE_AABB
            self.state = self.MOVE_AABB
        else:
            cX, cY = view.worldToScreen( ( self.editGoal.maxPt.x, self.editGoal.maxPt.y ) )
            dX = mousePos[0] - cX
            dY = mousePos[1] - cY
            distSqd = dX * dX + dY * dY
            if ( distSqd < 49 ):
                changed = self.state != self.SIZE_AABB
                self.state = self.SIZE_AABB
            else:
                if ( missDeselect ):
                    changed = True
                    self.state = self.AABB
                    self.editGoal = None
                    self.goalEditor.activeGoal = -1
                else:
                    changed =  self.state != self.EDIT_AABB
                    self.state = self.EDIT_AABB
        return changed    
   
    def drawGL( self, view ):
        '''Draws the current rectangle to the open gl context'''
        PGContext.drawGL( self, view )

        view.printText( 'Creating %s goals' % self.STATE_NAMES[ self.state ], ( 10, 45 ) )        
        view.printText( "%d goals in %d sets" % ( self.goalEditor.goalCount(), self.goalEditor.setCount() ), (20,30) )
        gs = self.goalEditor[ self.goalEditor.editSet ]
        msg = 'Goal set %d with %d goals' % ( gs.id, len(gs) )
        view.printText( msg, (20, 15) )

        # special display for editing
        if ( self.editGoal ):
            glPushAttrib( GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT | GL_POINT_BIT | GL_LINE_BIT )
            glDisable( GL_DEPTH_TEST )
            glPointSize( 5 )
            glLineWidth( 2 )
            glColor3f( 0.7, 0.7, 0.1 )
            if ( self.state & self.EDIT_CIRCLE ):
                if ( self.state == self.MOVE_CIRCLE ):
                    glPointSize( 7 )
                elif ( self.state == self.SIZE_CIRCLE ):
                    glLineWidth( 4 )
                    GoalEditor.drawCircleGoal( self.editGoal )
                glBegin( GL_POINTS )
                glVertex3f( self.editGoal.p.x, self.editGoal.p.y, 0.0 )
                glEnd()
            elif ( self.state & self.EDIT_AABB ):
                if ( self.state == self.MOVE_AABB ):
                    glPointSize( 7 )
                else:
                    glPointSize( 4 )
                glBegin( GL_POINTS )
                glVertex3f( self.editGoal.minPt.x, self.editGoal.minPt.y, 0.0 )
                glEnd()
                if ( self.state == self.SIZE_AABB ):
                    glPointSize( 7 )
                else:
                    glPointSize( 4 )
                glBegin( GL_POINTS )
                glVertex3f( self.editGoal.maxPt.x, self.editGoal.maxPt.y, 0.0 )
                glEnd()
            glPopAttrib()

