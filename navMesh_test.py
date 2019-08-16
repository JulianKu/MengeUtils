import StringIO
import unittest

from navMesh import NavMesh

SIMPLE_NAV_SPEC = '''13
-5.0 6.0
-1.0 6.0
1.0 6.0
3.0 6.0
-5.0 3.0
-1.0 3.0
1.0 3.0
3.0 3.0
-1.0 0.0
1.0 0.0
-1.0 -3.0
1.0 -3.0
0.0 1.5

7
	1 5 0 1
	2 6 1 2
	5 6 1 3
	8 9 6 7
	5 12 3 5
	6 12 3 4
	9 12 4 6

13
	0 1 0 1
	1 2 1 2
	2 3 2 3
	3 7 2 4
	7 6 2 5
	6 9 4 6
	9 11 7 7
	11 10 7 8
	10 8 7 9
	8 5 5 10
	5 4 0 11
	4 0 0 0
	8 12 5 -1

nodeGroup
8
	-3.0 4.50
	4 4 5 1 0
	0 0 1.0
	1 0
	5 0 1 11 10 9
	
	0.0 4.50
	4 5 6 2 1
	0 0 1.0
	3 0 1 2
	7 0 1 2 4 5 9 10
	
	2.00 4.50
	4 6 7 3 2
	0 0 1.0
	1 1
	5 1 2 3 4 5
	
	0.0 2.50
	3 12 6 5
	0.0 0.33333 0.0
	3 2 4 5
	5 4 5 9 10 12 
	
	0.5 1.50
	3 12 9 6
	0.0 0.33333 0.0
	2 5 6 
	4 4 5 6 12 
	
	-0.5 1.50
	3 12 5 8
	0.0 0.33333 0.0
	1 4 
	3 9 10 12 
	
	0.0 0.75
	3 12 8 9
	0.0 0.33333 0.0
	2 3 6 
	4 5 6 8 12 
	
	0.0 -1.50
	4 10 11 9 8
	0.0 0.0 0.0
	1 3
	5 5 6 7 8 9
	'''

COMPLEX_NAV_SPEC = '''88
	-1.00 0.00
	1.00 0.00
	1.00 7.50
	-1.00 7.50
	-10.00 0.00
	-10.00 -10.00
	10.00 -10.00
	10.00 0.00
	-10.00 0.35
	-1.00 0.35
	-1.00 0.85
	-10.00 0.85
	10.00 0.85
	1.00 0.85
	1.00 0.35
	10.00 0.35
	-10.00 1.05
	-1.00 1.05
	-1.00 1.55
	-10.00 1.55
	10.00 1.55
	1.00 1.55
	1.00 1.05
	10.00 1.05
	-10.00 1.75
	-1.00 1.75
	-1.00 2.25
	-10.00 2.25
	10.00 2.25
	1.00 2.25
	1.00 1.75
	10.00 1.75
	-10.00 2.45
	-1.00 2.45
	-1.00 2.95
	-10.00 2.95
	10.00 2.95
	1.00 2.95
	1.00 2.45
	10.00 2.45
	-10.00 3.15
	-1.00 3.15
	-1.00 3.65
	-10.00 3.65
	10.00 3.65
	1.00 3.65
	1.00 3.15
	10.00 3.15
	-10.00 3.85
	-1.00 3.85
	-1.00 4.35
	-10.00 4.35
	10.00 4.35
	1.00 4.35
	1.00 3.85
	10.00 3.85
	-10.00 4.55
	-1.00 4.55
	-1.00 5.05
	-10.00 5.05
	10.00 5.05
	1.00 5.05
	1.00 4.55
	10.00 4.55
	-10.00 5.25
	-1.00 5.25
	-1.00 5.75
	-10.00 5.75
	10.00 5.75
	1.00 5.75
	1.00 5.25
	10.00 5.25
	-10.00 5.95
	-1.00 5.95
	-1.00 6.45
	-10.00 6.45
	10.00 6.45
	1.00 6.45
	1.00 5.95
	10.00 5.95
	-10.00 6.65
	-1.00 6.65
	-1.00 7.15
	-10.00 7.15
	10.00 7.15
	1.00 7.15
	1.00 6.65
	10.00 6.65

21
	0 1 0 1
	9 10 0 2
	13 14 0 3
	17 18 0 4
	21 22 0 5
	25 26 0 6
	29 30 0 7
	33 34 0 8
	37 38 0 9
	41 42 0 10
	45 46 0 11
	49 50 0 12
	53 54 0 13
	57 58 0 14
	61 62 0 15
	65 66 0 16
	69 70 0 17
	73 74 0 18
	77 78 0 19
	81 82 0 20
	85 86 0 21

88
	1 7 1 1
	7 6 1 2
	6 5 1 3
	5 4 1 4
	4 0 1 5
	0 9 0 6
	9 8 2 7
	8 11 2 8
	11 10 2 13
	14 1 0 0
	15 14 3 9
	12 15 3 10
	13 12 3 11
	10 17 0 14
	17 16 4 15
	16 19 4 16
	19 18 4 21
	22 13 0 12
	23 22 5 17
	20 23 5 18
	21 20 5 19
	18 25 0 22
	25 24 6 23
	24 27 6 24
	27 26 6 29
	30 21 0 20
	31 30 7 25
	28 31 7 26
	29 28 7 27
	26 33 0 30
	33 32 8 31
	32 35 8 32
	35 34 8 37
	38 29 0 28
	39 38 9 33
	36 39 9 34
	37 36 9 35
	34 41 0 38
	41 40 10 39
	40 43 10 40
	43 42 10 45
	46 37 0 36
	47 46 11 41
	44 47 11 42
	45 44 11 43
	42 49 0 46
	49 48 12 47
	48 51 12 48
	51 50 12 53
	54 45 0 44
	55 54 13 49
	52 55 13 50
	53 52 13 51
	50 57 0 54
	57 56 14 55
	56 59 14 56
	59 58 14 61
	62 53 0 52
	63 62 15 57
	60 63 15 58
	61 60 15 59
	58 65 0 62
	65 64 16 63
	64 67 16 64
	67 66 16 69
	70 61 0 60
	71 70 17 65
	68 71 17 66
	69 68 17 67
	66 73 0 70
	73 72 18 71
	72 75 18 72
	75 74 18 77
	78 69 0 68
	79 78 19 73
	76 79 19 74
	77 76 19 75
	74 81 0 78
	81 80 20 79
	80 83 20 80
	83 82 20 85
	86 77 0 76
	87 86 21 81
	84 87 21 82
	85 84 21 83
	82 3 0 86
	3 2 0 87
	2 85 0 84

stairGrp
1
	0.0000 3.7500
	4 0 1 2 3
	0.0000 0.6745 0.0000
	21 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20
	68 0 1 2 3 4 5 6 8 9 10 12 13 14 16 17 18 20 21 22 24 25 26 28 29 30 32 33 34 36 37 38 40 41 42 44 45 46 48 49 50 52 53 54 56 57 58 60 61 62 64 65 66 68 69 70 72 73 74 76 77 78 80 81 82 84 85 86 87


floorGrp
1
	0.0000 -5.0000
	4 4 5 6 7
	0.0000 0.0000 0.0000
	1 0
	7 0 1 2 3 4 5 9


rowsGrp
20
	-5.5000 0.6000
	4 8 9 10 11
	0.0000 0.0000 0.4047
	1 1
	5 5 6 7 8 13

	5.5000 0.6000
	4 12 13 14 15
	0.0000 0.0000 0.4047
	1 2
	5 9 10 11 12 17

	-5.5000 1.3000
	4 16 17 18 19
	0.0000 0.0000 0.8769
	1 3
	5 13 14 15 16 21

	5.5000 1.3000
	4 20 21 22 23
	0.0000 0.0000 0.8769
	1 4
	5 17 18 19 20 25

	-5.5000 2.0000
	4 24 25 26 27
	0.0000 0.0000 1.3490
	1 5
	5 21 22 23 24 29

	5.5000 2.0000
	4 28 29 30 31
	0.0000 0.0000 1.3490
	1 6
	5 25 26 27 28 33

	-5.5000 2.7000
	4 32 33 34 35
	0.0000 0.0000 1.8212
	1 7
	5 29 30 31 32 37

	5.5000 2.7000
	4 36 37 38 39
	0.0000 0.0000 1.8212
	1 8
	5 33 34 35 36 41

	-5.5000 3.4000
	4 40 41 42 43
	0.0000 0.0000 2.2933
	1 9
	5 37 38 39 40 45

	5.5000 3.4000
	4 44 45 46 47
	0.0000 0.0000 2.2933
	1 10
	5 41 42 43 44 49

	-5.5000 4.1000
	4 48 49 50 51
	0.0000 0.0000 2.7655
	1 11
	5 45 46 47 48 53

	5.5000 4.1000
	4 52 53 54 55
	0.0000 0.0000 2.7655
	1 12
	5 49 50 51 52 57

	-5.5000 4.8000
	4 56 57 58 59
	0.0000 0.0000 3.2376
	1 13
	5 53 54 55 56 61

	5.5000 4.8000
	4 60 61 62 63
	0.0000 0.0000 3.2376
	1 14
	5 57 58 59 60 65

	-5.5000 5.5000
	4 64 65 66 67
	0.0000 0.0000 3.7098
	1 15
	5 61 62 63 64 69

	5.5000 5.5000
	4 68 69 70 71
	0.0000 0.0000 3.7098
	1 16
	5 65 66 67 68 73

	-5.5000 6.2000
	4 72 73 74 75
	0.0000 0.0000 4.1820
	1 17
	5 69 70 71 72 77

	5.5000 6.2000
	4 76 77 78 79
	0.0000 0.0000 4.1820
	1 18
	5 73 74 75 76 81

	-5.5000 6.9000
	4 80 81 82 83
	0.0000 0.0000 4.6541
	1 19
	5 77 78 79 80 85

	5.5000 6.9000
	4 84 85 86 87
	0.0000 0.0000 4.6541
	1 20
	5 81 82 83 84 87
'''


class NavMeshTests(unittest.TestCase):
    
    def nav_mesh_equals(self, nm1, nm2):
        # Simple initial tests that counts are equal.
        self.assertEqual(len(nm1.vertices), len(nm2.vertices))
        self.assertEqual(len(nm1.groups), len(nm2.groups))
        self.assertEqual(len(nm1.nodes), len(nm2.nodes))
        self.assertEqual(len(nm1.edges), len(nm2.edges))
        self.assertEqual(len(nm1.obstacles), len(nm2.obstacles))

        # Confirm identical vertices
        for v in xrange(len(nm1.vertices)):
            v1 = nm1.vertices[v]
            v2 = nm2.vertices[v]
            self.assertTrue((v1 - v2).isZero())

        # The nodes must be in the same order.
        n1ToN2 = {}
        nodes2 = nm2.getNodeIterator()
        for g_name1, n1 in nm1.getNodeIterator():
            g_name2, n2 = nodes2.next()
            n1ToN2[n1] = n2
            self.assertEqual(g_name1, g_name2)
            self.assertEqual(n1.poly.verts, n2.poly.verts)
            self.assertEqual(n1.A, n2.A)
            self.assertEqual(n1.B, n2.B)
            self.assertEqual(n1.C, n2.C)
            self.assertTrue((n1.center - n2.center).isZero())
            self.assertEqual(n1.edges, n2.edges)
            self.assertEqual(n1.obstacles, n2.obstacles)
            self.assertEqual(n1.obstacles, n2.obstacles)

        for g_name1 in nm1.groups.keys():
            self.assertTrue(nm2.groups.has_key(g_name1))
            g1 = nm1.groups[g_name1]
            g2 = nm2.groups[g_name1]
            g1_mapped = [n1ToN2[n] for n in g1]
            self.assertEqual(g1_mapped, g2)

        for e in xrange(len(nm1.edges)):
            e1 = nm1.edges[e]
            e2 = nm2.edges[e]
            self.assertEqual(e1.v0, e2.v0)
            self.assertEqual(e1.v1, e2.v1)
            self.assertEqual(n1ToN2[e1.n0], e2.n0)
            self.assertEqual(n1ToN2[e1.n1], e2.n1)

        for o in xrange(len(nm1.obstacles)):
            o1 = nm1.obstacles[o]
            o2 = nm2.obstacles[o]
            self.assertEqual(o1.v0, o2.v0)
            self.assertEqual(o1.v1, o2.v1)
            self.assertEqual(n1ToN2[o1.n0], o2.n0)
            self.assertEqual(o1.next, o2.next)
        

    def create_two_meshes(self, mesh_string):
        in_file = StringIO.StringIO(mesh_string)
        nav_mesh = NavMesh()
        nav_mesh.readNavFileAscii(in_file)
        out_file = StringIO.StringIO()
        nav_mesh.writeNavFileAscii(out_file)
        out_file.seek(0)
        nav_mesh2 = NavMesh()
        nav_mesh2.readNavFileAscii(out_file)
        return nav_mesh, nav_mesh2
        
    def test_simple_read_ascii(self):
        nav_mesh, nav_mesh2 = self.create_two_meshes(SIMPLE_NAV_SPEC)
        self.nav_mesh_equals(nav_mesh, nav_mesh2)

    def test_complex_read(self):
        nav_mesh, nav_mesh2 = self.create_two_meshes(COMPLEX_NAV_SPEC)
        self.nav_mesh_equals(nav_mesh, nav_mesh2)

if __name__ == '__main__':
    unittest.main()