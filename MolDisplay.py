import molecule;
 
radius = {}
element_name = {}

header = """<svg version="1.1" width="1000" height="1000" xmlns="http://www.w3.org/2000/svg">"""
footer = """</svg>"""

offsetx = 500
offsety = 500
scale = 100

class Atom:
    def __init__(self, c_atom):
        self.c_atom = c_atom
        self.z = c_atom.z
    def __str__(self):
        return f"Element: {self.c_atom.element}, X: {self.c_atom.x}, Y: {self.c_atom.y}, Z: {self.z}"
    # returns the svg for a given atom
    def svg(self):
        return '  <circle cx="%.2f" cy="%.2f" r="%d" fill="url(#%s)"/>\n' % (self.c_atom.x * scale + offsetx, self.c_atom.y * scale + offsety, radius.get(self.c_atom.element), element_name.get(self.c_atom.element))
class Bond:
    def __init__(self, c_bond):
        self.c_bond = c_bond
        self.z = c_bond.z
    def __str__(self):
        return f"Atom: {self.c_bond.a1 + 1}, Atom: {self.c_bond.a2 + + 1}, ePairs: {self.c_bond.epairs} x1: {self.c_bond.x1}, y1: {self.c_bond.y1}, x2: {self.c_bond.x2}, y2: {self.c_bond.y2}, z: {self.c_bond.z} bond_len: {self.c_bond.len}, dx: {self.c_bond.dx}, dy: {self.c_bond.dy}"
    # returns the svg for a given bond; a rectangle which contains 8 points
    def svg(self):
        return '  <polygon points="%.2f,%.2f %.2f,%.2f %.2f,%.2f %.2f,%.2f" fill="green"/>\n'%(
            self.c_bond.x1 * scale - self.c_bond.dy * 10.0 + offsetx, self.c_bond.y1 * scale + self.c_bond.dx * 10.0 + offsety, 
            self.c_bond.x1 * scale + self.c_bond.dy * 10.0 + offsetx, self.c_bond.y1 * scale - self.c_bond.dx * 10.0 + offsety, 
            self.c_bond.x2 * scale + self.c_bond.dy * 10.0 + offsetx, self.c_bond.y2 * scale - self.c_bond.dx * 10.0 + offsety, 
            self.c_bond.x2 * scale - self.c_bond.dy * 10.0 + offsetx, self.c_bond.y2 * scale + self.c_bond.dx * 10.0 + offsety)

class Molecule(molecule.molecule):
    # prints all atoms and bonds in a molecule
    def print_molecule(self):
        for i in range(self.atom_no):
            temp_atom = self.get_atom(i)
            atom = Atom(temp_atom)
            print(atom)
        for j in range(self.bond_no):
            temp_bond = self.get_bond(j)
            bond = Bond(temp_bond)
            print(bond)

    # Parses a .CIF (.SDF Extension) file
    def parse(self, file):
        # read the file information into lines
        lines = file.readlines()
        # atom and bond information is located on line 4 of an SDF file
        num_atoms = int(lines[3].split()[0])
        num_bonds = int(lines[3].split()[1])
        atom_lines = lines[4:4+num_atoms]
        bond_lines = lines[4+num_atoms:4+num_atoms+num_bonds]

        # appending atom to molecule
        for line in atom_lines:
            info = line.split()
            x, y, z, element = info[0], info[1], info[2], info[3]
            self.append_atom(str(element), float(x), float(y), float(z))
        # appending bond to molecule
        for line in bond_lines:
            info = line.split()
            atom_one, atom_two, e_pairs = info[0], info[1], info[2]
            self.append_bond(int(atom_one) - 1, int(atom_two) - 1, int(e_pairs)) # removed from molecule.i to accomodate SQL table indices

    # Returns an SVG for a given molecule
    def svg(self):
        # receive each Atom and Bond in the molecule
        atoms = [Atom(self.get_atom(i)) for i in range(self.atom_no)]
        bonds = [Bond(self.get_bond(j)) for j in range(self.bond_no)]

        # sort atoms and bonds by z value
        atoms.sort(key=lambda x: x.z) 
        bonds.sort(key=lambda x: x.z)
        svgs = []

        while atoms or bonds:
            if atoms and bonds:
                a1 = atoms[0]
                b1 = bonds[0]
                if a1.z < b1.z:
                    element = atoms.pop(0)
                else:
                    element = bonds.pop(0)
            elif atoms:
                element = atoms.pop(0)
            elif bonds:
                element = bonds.pop(0)

            # Append the element to svgs
            svgs.append(element.svg())

        # Return the SVG for a molecule
        return header + ''.join(svgs) + footer
    
    