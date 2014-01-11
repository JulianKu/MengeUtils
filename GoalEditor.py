import Goals
from OpenGL.GL import *
import numpy as np
import operator

# unit circle centered on radius
CIRCLE = np.column_stack( (np.cos( np.linspace( 0, np.pi * 2.0, 16, endpoint=False ) ),
                           np.sin( np.linspace( 0, np.pi * 2.0, 16, endpoint=False ) ) ) )

# square box with size 1, bottom-left corner positioned on origin
SQUARE = np.array( ( (0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0) ), dtype=np.float32 )

class GoalEditor:
    '''A class for managing multiple goal sets and drawing them.'''
    def __init__( self, goalSets ):
        '''Constructor.

        @param      goalSets        A list of Goals.GoalSet instances.
        '''
        self.goalSets = goalSets
        # The index of the goal set currently displayed for editing
        self.editSet = -1

    def __getitem__( self, i ):
        '''Returns the ith goalset'''
        return self.goalSets[ i ]
    
    def setCount( self ):
        '''Reports the total number of goal sets'''
        return len( self.goalSets )

    def goalCount( self ):
        '''Reports the total number of goals'''
        return reduce( operator.add, map( lambda x: len(x), self.goalSets ) )
        
    def drawGL( self, select=False ):
        '''Draws the list of goal sets to the OpenGL context.

        @param      select          Determines if the goals are being drawn for selection
                                    purposes.
        '''
        glPushAttrib( GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT | GL_POINT_BIT | GL_LINE_BIT )
        glDisable( GL_DEPTH_TEST )
        glPointSize( 5 )
        glLineWidth( 2 )
        gID = 0
        for i, gs in enumerate( self.goalSets ):
            if ( i == self.editSet ):
                glColor3f( 0.7, 0.3, 0.9 )
            else:
                glColor3f( 0.35, 0.15, 0.45 )
            for g in gs:
                if ( select ):
                    glLoadName( glID )
                    glID += 1
                drawGoal( g )
        glPopAttrib()

def drawGoal( goal ):
    '''Draws a goal instance to the OpenGL context.

    @param      goal            The instance of Goals.Goal subclass to draw.
    '''
    if ( isinstance( goal, Goals.PointGoal ) ):
        drawPointGoal( goal )
    if ( isinstance( goal, Goals.CircleGoal ) ):
        drawCircleGoal( goal )
    if ( isinstance( goal, Goals.AABBGoal ) ):
        drawAABBGoal( goal )
    if ( isinstance( goal, Goals.OBBGoal ) ):
        drawOBBGoal( goal )

def drawPointGoal( goal ):
    '''Draws a point goal instance to the OpenGL context.

    @param      goal            An instace of Goals.PointGoal.
    '''
    glBegin( GL_POINTS )
    glVertex3f( goal.p.x, goal.p.y, 0.0 )
    glEnd()
    
def drawCircleGoal( goal ):
    '''Draws a point goal instance to the OpenGL context.

    @param      goal            An instace of Goals.PointGoal.
    '''
    glPushMatrix()
    glTranslatef( goal.p.x, goal.p.y, 0.0 )
    glScalef( goal.r, goal.r, goal.r )
    glBegin( GL_LINE_LOOP )
    for x, y in CIRCLE:
        glVertex3f( x, y, 0.0 )
    glEnd()
    glPopMatrix()

def drawAABBGoal( goal ):
    '''Draws a point goal instance to the OpenGL context.

    @param      goal            An instace of Goals.PointGoal.
    '''
    size = goal.maxPt - goal.minPt
    glPushMatrix()
    glTranslatef( goal.minPt.x, goal.minPt.y, 0.0 )
    glScalef( size.x, size.y, 1.0 )
    glBegin( GL_LINE_LOOP )
    for x, y in SQUARE:
        glVertex3f( x, y, 0.0 )
    glEnd()
    glPopMatrix()

def drawOBBGoal( goal ):
    '''Draws a point goal instance to the OpenGL context.

    @param      goal            An instace of Goals.PointGoal.
    '''
    glPushMatrix()
    glTranslatef( goal.pivot.x, goal.pivot.y, 0.0 )
    glRotatef( goal.angle, 0.0, 0.0, 1.0 )
    glScalef( goal.size.x, goal.size.y, 1.0 )
    glBegin( GL_LINE_LOOP )
    for x, y in SQUARE:
        glVertex3f( x, y, 0.0 )
    glEnd()
    glPopMatrix()