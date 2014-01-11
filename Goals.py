# handles the definition of agent goals and goal sets

from primitives import Vector2
from xml.dom import minidom

# The accuracy with which the floats are pritned
DIGITS = 5

# Registration of goal types.  Used to parse goals
class GoalSet:
    '''A set of goals.  Maps integer identifiers to instances of goals.'''
    # The TagName that this will process
    TAG_NAME = 'GoalSet'

    class GoalIterator:
        '''An iterator through the goal set's goals.'''
        def __init__( self, goalSet ):
            '''Constructor.

            @param      goalSet     The goal set to iterate through.
            '''
            self.goalSet = goalSet
            self.goalCount = len( goalSet.goals )
            self.nextID = 0     # the next goal to return

        def __iter__( self ):
            '''To support the iterator interface, __iter__ returns itself.'''
            return self

        def next( self ):
            if ( self.nextID < self.goalCount ):
                g = self.goalSet[ self.nextID ]
                self.nextID += 1
                return g
            else:
                raise StopIteration
        
    def __init__( self, robustParse=True ):
        '''Constructor

        @param      robustParse         Indicates if, during parsing, unrecognized
                                        Tag types should simply be stored to be included
                                        in the output.
        '''
        self.id = -1
        self.goals = {}     # mapping from goals to ids
        self.keys = []      # ids of goals
        self.robust = robustParse
        if ( robustParse ):
            self.unknownTags = []   # tags encountered when parsing that should be saved
                                    # out blindly, verbatim

    def __iter__( self ):
        return self.GoalIterator( self )
    
    def __getitem__( self, i ):
        '''Returns the ith goal in the set'''
        assert( i > -len(self.goals) and i < len( self.goals ) )
        return self.goals[ self.keys[ i ] ]

    def __del__( self ):
        # This is XML DOM stuff to make sure it gets garbage collected properly.
        if ( self.robust and self.unknownTags ):
            for tag in self.unknownTags:
                tag.unlink()
    
    def parseXML( self, element ):
        '''Sets the goal set parameters based on the structure of an XML DOM tree.

        @param      element     The root element of a GoalSet tree.
        @raises     ValueError if there is a parsing error
        '''
        # extract its attributes
        try:
            self.id = int( element.getAttribute( 'id' ) )
        except ValueError:
            raise ValueError, 'Error extracting the "id" attribute for the GoalSet element' # on line ??

        # extract its goals
        for child in element.childNodes:
            if ( child.nodeType == minidom.Node.ELEMENT_NODE ):
                if ( child.tagName == 'Goal' ):
                    goal = getGoalFromXML( child, self.robust )
                    try:
                        self.addGoal( goal )
                    except KeyError as e:
                        raise ValueError, str(e)
                elif ( self.robust ):
                    print "Child tag of GoalSet unrecognized -- %s.  Tag stored for output." % ( child.tagName )
                    element.removeChild( child )
                    self.unknownTags.append( child )
                else:
                    raise ValueError, "Child tag of GoalSet unrecognized -- %s" % ( child.tagName )

    def addGoal( self, goal ):
        '''Adds a goal to the goal set.

        @param      goal    An instance of Goal.
        @raises     KeyError        If the id is not unique
        '''
        if ( self.goals.has_key( goal.id ) ):
            raise KeyError, "GoalSet already contains a goal with id %d" % ( goal.id )
        self.goals[ goal.id ] = goal
        self.keys.append( goal.id )
        self.keys.sort()

    def __len__( self ):
        '''Returns the number of goals'''
        return len( self.goals )

    def xmlElement( self ):
        '''Creates an XML Dom Element for this GoalSet.

        @returns        An instnace of minidom.Element containing this node's data.
                        If there are no goals or unknown tags, it returns None.
        '''
        root = None
        if ( len( self.goals ) or ( self.robust and len( self.unknownTags ) ) ):
            root = minidom.Element( 'GoalSet' )
            root.setAttribute( 'id', '%d' % ( self.id ) )
            ids = self.goals.keys()
            ids.sort()
            for id in ids:
                root.appendChild( self.goals[ id ].xmlElement() )
            if ( self.robust):
                for tag in self.unknownTags:
                    root.appendChild( tag )
        return root
        
    
    
class Goal:
    '''The goal base class'''
    TYPE = 'undefined'
    def __init__( self ):
        '''Constructor.
        '''
        self.weight = 1.0
        self.capacity = 1000000
        self.id = -1

    def xmlElement( self ):
        '''Creates an XML Dom Element for this Goal.

        Subclasses of Goal should call this to instantiate the node and then
        add their unique attributes.
        
        @returns        An instnace of xml.minidom.Element containing this node's data
        '''
        node = minidom.Element( 'Goal' )
        node.setAttribute( 'type', self.TYPE )
        node.setAttribute( 'id', '%d' % self.id )
        node.setAttribute( 'weight', '{0:.{1}f}'.format( self.weight, DIGITS ) )
        node.setAttribute( 'capacity', '%d' % self.capacity )
        return node
    
    def parseXML( self, element, robustParse ):
        '''Sets the goal parameters based on the structure of an XML DOM tree.

        Subclasses of Goal should call this to include the Goal attributes.
        
        @param      element     The element of a Goal tag.
        @param      robustParse     A boolean which controls how robust the parse is.
                                If true, the GoalSet will blindly include unrecognized child Tags,
                                if False, unrecognized tags will be treated as failure.
        @raises     ValueError if there is a parsing error
        '''
        # extract its attriutes
        try:
            self.id = int( element.getAttribute( 'id' ) )
        except ValueError:
            raise ValueError, 'Goal of type "%s" is missing "id" attribute.' % ( element.getAttribute( 'type' ) )

        try:
            self.weight = float( element.getAttribute( 'weight' ) )
        except ValueError:
            if ( robustParse ):
                print 'Goal of type "%s" is missing "weight" attribute.  Using default value of %.1f.' % ( self.TYPE, self.weight )
            else:
                raise ValueError, 'Goal of type "%s" is missing "weight" attribute.' % ( self.TYPE )

        try:
            self.capacity = int( element.getAttribute( 'capacity' ) )
        except ValueError:
            if ( robustParse ):
                print 'Goal of type "%s" is missing "capacity" attribute.  Using default value of %d.' % ( self.TYPE, self.capacity )        
            else:
                raise ValueError, 'Goal of type "%s" is missing "capacity" attribute.' % ( self.TYPE )

            
        

class PointGoal( Goal ):
    '''A simple point goal.  The agent's goal position is this point.'''
    # The goal type for xml
    TYPE = 'point'
    def __init__( self ):
        '''Constructor.'''
        Goal.__init__( self )
        self.p = Vector2( 0.0, 0.0 )

    def xmlElement( self ):
        '''Creates an XML Dom Element for this GoalSet.

        @returns        An instnace of xml.minidom.Element containing this node's data
        '''
        node = Goal.xmlElement( self )
        node.setAttribute( 'x', '{0:.{1}f}'.format( self.p.x, DIGITS ) )
        node.setAttribute( 'y', '{0:.{1}f}'.format( self.p.y, DIGITS ) )
        return node

    def parseXML( self, element, robustParse ):
        '''Sets the goal parameters based on the structure of an XML DOM tree.

        @param      element     The element of a Goal tag.
        @raises     ValueError if there is a parsing error
        '''
        Goal.parseXML( self, element, robustParse )
        # extract its attriutes
        try:
            self.p.x = float( element.getAttribute( 'x' ) )
        except ValueError:
            raise ValueError, 'Goal of type "%s" is missing "x" attribute.' % ( self.TYPE )        

        try:
            self.p.y = float( element.getAttribute( 'y' ) )
        except ValueError:
            raise ValueError, 'Goal of type "%s" is missing "y" attribute.' % ( self.TYPE )
          
class CircleGoal( PointGoal ):
    '''A circular goal which assignes positions with uniform probability'''
    # The goal type for xml
    TYPE = 'circle'
    def __init__( self ):
        '''Constructor.'''
        PointGoal.__init__( self )
        self.r = 0.0

    def xmlElement( self ):
        '''Creates an XML Dom Element for this GoalSet.

        @returns        An instnace of xml.minidom.Element containing this node's data
        '''
        node = PointGoal.xmlElement( self )
        node.setAttribute( 'radius', '{0:.{1}f}'.format( self.r, DIGITS ) )
        return node

    def parseXML( self, element, robustParse ):
        '''Sets the goal parameters based on the structure of an XML DOM tree.

        @param      element     The element of a Goal tag.
        @raises     ValueError if there is a parsing error
        '''
        PointGoal.parseXML( self, element, robustParse )
        # extract its attriutes
        try:
            self.r = float( element.getAttribute( 'radius' ) )
        except ValueError:
            raise ValueError, 'Goal of type "%s" is missing "radius" attribute.' % ( self.TYPE )  
    
class AABBGoal( Goal ):
    '''A axis-aligned bounding box goal region with uniform probability'''
    # The goal type for xml
    TYPE = 'AABB'
    def __init__( self):
        '''Constructor.'''
        Goal.__init__( self )
        self.minPt = Vector2( 0.0, 0.0 )
        self.maxPt = Vector2( 0.0, 0.0 )

    def xmlElement( self ):
        '''Creates an XML Dom Element for this GoalSet.

        @returns        An instnace of xml.minidom.Element containing this node's data
        '''
        node = Goal.xmlElement( self )
        node.setAttribute( 'xmin', '{0:.{1}f}'.format( self.minPt.x, DIGITS ) )
        node.setAttribute( 'ymin', '{0:.{1}f}'.format( self.minPt.y, DIGITS ) )
        node.setAttribute( 'xmax', '{0:.{1}f}'.format( self.maxPt.x, DIGITS ) )
        node.setAttribute( 'ymax', '{0:.{1}f}'.format( self.maxPt.y, DIGITS ) )
        return node

    def parseXML( self, element, robustParse ):
        '''Sets the goal parameters based on the structure of an XML DOM tree.

        @param      element     The element of a Goal tag.
        @raises     ValueError if there is a parsing error
        '''
        Goal.parseXML( self, element, robustParse )
        # extract its attriutes
        try:
            self.minPt.x = float( element.getAttribute( 'xmin' ) )
        except ValueError:
            raise ValueError, 'Goal of type "%s" is missing "xmin" attribute.' % ( self.TYPE )
        try:
            self.minPt.y = float( element.getAttribute( 'ymin' ) )
        except ValueError:
            raise ValueError, 'Goal of type "%s" is missing "ymin" attribute.' % ( self.TYPE )
        try:
            self.maxPt.x = float( element.getAttribute( 'xmax' ) )
        except ValueError:
            raise ValueError, 'Goal of type "%s" is missing "xmax" attribute.' % ( self.TYPE )
        try:
            self.maxPt.y = float( element.getAttribute( 'ymax' ) )
        except ValueError:
            raise ValueError, 'Goal of type "%s" is missing "ymax" attribute.' % ( self.TYPE )
    
class OBBGoal( Goal ):
    '''An oriented bounding box goal region with uniform probability'''
    
    # The goal type for xml
    TYPE = 'OBB'
    def __init__( self ):
        '''Constructor.'''
        Goal.__init__( self )
        self.pivot = Vector2( 0.0, 0.0 )  
        self.size = Vector2( 0.0, 0.0 )
        self.angle = 0.0

    def xmlElement( self ):
        '''Creates an XML Dom Element for this GoalSet.

        @returns        An instnace of xml.minidom.Element containing this node's data
        '''
        node = Goal.xmlElement( self )
        node.setAttribute( 'x', '{0:.{1}f}'.format( self.pivot.x, DIGITS ) )
        node.setAttribute( 'y', '{0:.{1}f}'.format( self.pivot.y, DIGITS ) )
        node.setAttribute( 'width', '{0:.{1}f}'.format( self.size.x, DIGITS ) )
        node.setAttribute( 'height', '{0:.{1}f}'.format( self.size.y, DIGITS ) )
        node.setAttribute( 'angle', '{0:.{1}f}'.format( self.angle, DIGITS ) )
        return node

    def parseXML( self, element, robustParse ):
        '''Sets the goal parameters based on the structure of an XML DOM tree.

        @param      element     The element of a Goal tag.
        @raises     ValueError if there is a parsing error
        '''
        Goal.parseXML( self, element, robustParse )
        # extract its attriutes
        try:
            self.pivot.x = float( element.getAttribute( 'x' ) )
        except ValueError:
            raise ValueError, 'Goal of type "%s" is missing "x" attribute.' % ( self.TYPE )
        try:
            self.pivot.y = float( element.getAttribute( 'y' ) )
        except ValueError:
            raise ValueError, 'Goal of type "%s" is missing "y" attribute.' % ( self.TYPE )
        try:
            self.size.x = float( element.getAttribute( 'width' ) )
        except ValueError:
            raise ValueError, 'Goal of type "%s" is missing "width" attribute.' % ( self.TYPE )
        try:
            self.size.y = float( element.getAttribute( 'height' ) )
        except ValueError:
            raise ValueError, 'Goal of type "%s" is missing "height" attribute.' % ( self.TYPE )
        try:
            self.angle = float( element.getAttribute( 'angle' ) )
        except ValueError:
            raise ValueError, 'Goal of type "%s" is missing "angle" attribute.' % ( self.TYPE )


def getGoalFromXML( element, robustParse ):
    '''Given an XML Dome Element, instantiate the appropriate, intialized goal.

    @param      element         An instance of Dom.Element
    @param      robustParse     A boolean which controls how robust the parse is.
                                If true, the GoalSet will blindly include unrecognized child Tags,
                                if False, unrecognized tags will be treated as failure.
    @returns    An instance of the corresopnding goal type.
    @raises     ValueError if no goal type matches the element.
    '''
    GoalTypes = { PointGoal.TYPE:PointGoal,
                  CircleGoal.TYPE:CircleGoal,
                  AABBGoal.TYPE:AABBGoal,
                  OBBGoal.TYPE:OBBGoal
                  }
    goalType = element.getAttribute( 'type' )
    if ( goalType ):
        try:
            goal = GoalTypes[ goalType ]()
        except KeyError:
            raise ValueError, "Unrecognized goal type: %s" % ( goalType )

        # this may throw an exception that is propagated upwards
        goal.parseXML( element, robustParse )                                        
        return goal
    
    else:
        raise ValueError, 'Goal tag has no "type" attribute'


def searchGoalSets( root, robustParse ):
    '''Searches the XML DOM tree with the given root for instances of GoalSet.

    @param      root        An instance of minidom.Element.  The root of the tree.
    @param      robustParse     A boolean which controls how robust the parse is.
                                If true, the GoalSet will blindly include unrecognized child Tags,
                                if False, unrecognized tags will be treated as failure.
    @returns    A list of all GoalSets found in the tree.
    @raises     ValueError if GoalSet definitions are found, but have errors.
    '''
    goalSets = []
    for child in root.childNodes:
        if ( child.nodeType == minidom.Node.ELEMENT_NODE ):
            if ( child.tagName == GoalSet.TAG_NAME ):
                gs = GoalSet( robustParse )
                gs.parseXML( child )
                goalSets.append( gs )
            else:
                goalSets.extend( searchGoalSets( child, robustParse ) )
    return goalSets

def readGoals( fileName, robustParse=True ):
    '''Given a valid xml file that contains one or more GoalSet definitions, returns a list of
    goal sets.

    @param      fileName        The path to the file.
    @param      robustParse     A boolean which controls how robust the parse is.
                                If true, the GoalSet will blindly include unrecognized child Tags,
                                if False, unrecognized tags will be treated as failure.
    @returns    A list containing the valid goal sets in the file.
    @raises     ValueError if there is error parsing the GoalSet
    '''
    try:
        doc = minidom.parse( fileName )
    except Exception as e:
        raise ValueError, str(e)

    goalSets = []
    try:        
        goalSets = searchGoalSets( doc.documentElement, robustParse )
    except ValueError as e:
        print "Error parsing:", e

    doc.unlink()

    return goalSets

if __name__ == '__main__':
    import optparse, sys
    parser = optparse.OptionParser()
    parser.set_description( 'Prints summary information of the goals defined in the file' )
    parser.add_option( '-i', '--input', help='The XML file containing goal set definitions',
                       action='store', dest='inFileName', default='' )
    parser.add_option( '-s', '--strict', help='Sets the parser to be strict.  All Goal tags must be explicitly correct.',
                       action='store_false', dest='robust', default=True )
    parser.add_option( '-d', '--digits', help='The number of digits after the decimal point for output.  Defaults to %d.' % DIGITS,
                       action='store', type='int', dest='digits', default=5 )
    options, args = parser.parse_args()

    if ( not options.inFileName ):
        parser.print_help()
        print '\n!!! You must specify the input file (-i/--input)'
        sys.exit(1)

    goalSets = readGoals( options.inFileName, options.robust )

    DIGITS = options.digits
    
    print '\nFound %d goal sets' % ( len( goalSets ) )
    for i, set in enumerate( goalSets ):
        print '\tgoal set %d has %d goals' % ( i, len( set ) )


    print '\n===============================================\n'
    nodes = [ set.xmlElement() for set in goalSets ]
    for node in nodes:
        if node:
            node.writexml(sys.stdout, addindent='    ', newl='\n')
            print
    
    

    