import sqlite3, os
import MolDisplay

class Database:
    def __init__(self, reset=False):
        # checks if molecules.db exists
        if reset == True:
            os.remove("molecules.db")
        self.conn = sqlite3.connect("molecules.db")
        self.cursor = self.conn.cursor()

    # Generates the tables for the data base schema
    def create_tables(self):
        # Elements Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Elements (
                ELEMENT_NO INTEGER NOT NULL,
                ELEMENT_CODE VARCHAR(3) NOT NULL,
                ELEMENT_NAME VARCHAR(32) NOT NULL,
                COLOUR1 CHAR(6) NOT NULL,
                COLOUR2 CHAR(6) NOT NULL,
                COLOUR3 CHAR(6) NOT NULL,
                RADIUS DECIMAL(3) NOT NULL,
                PRIMARY KEY (ELEMENT_CODE)
            )
        """)
        # Atoms Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Atoms (
                ATOM_ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                ELEMENT_CODE VARCHAR(3) NOT NULL,
                X DECIMAL(7,4) NOT NULL,
                Y DECIMAL(7,4) NOT NULL,
                Z DECIMAL(7,4) NOT NULL,
                FOREIGN KEY (ELEMENT_CODE) REFERENCES Elements(ELEMENT_CODE)
            )
        """)
        # Bonds Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Bonds (
                BOND_ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                A1 INTEGER NOT NULL,
                A2 INTEGER NOT NULL,
                EPAIRS INTEGER NOT NULL
            )
        """)
        # Molecules Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Molecules (
                MOLECULE_ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                NAME TEXT UNIQUE NOT NULL
            )
        """)
        # MoleculeAtom Table
        self.cursor.execute("""    
            CREATE TABLE IF NOT EXISTS MoleculeAtom (
                MOLECULE_ID INTEGER NOT NULL,
                ATOM_ID INTEGER NOT NULL,
                PRIMARY KEY (MOLECULE_ID, ATOM_ID),
                FOREIGN KEY (MOLECULE_ID) REFERENCES Molecules(MOLECULE_ID),
                FOREIGN KEY (ATOM_ID) REFERENCES Atoms(ATOM_ID)
            )
        """)
        # MoleculeBond Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS MoleculeBond (
                MOLECULE_ID INTEGER NOT NULL,
                BOND_ID INTEGER NOT NULL,
                PRIMARY KEY (MOLECULE_ID, BOND_ID)
                FOREIGN KEY (MOLECULE_ID) REFERENCES Molecules(MOLECULE_ID),
                FOREIGN KEY (BOND_ID) REFERENCES Bonds(BOND_ID)
            )
        """)

        # commit changes to db connection after tables have been generated
        self.conn.commit()

    # Inserts information into an existing table within the data base
    def __setitem__(self, table, values):
        self.cursor.execute(f"""
            INSERT INTO {table} VALUES {values}
        """)
        
        self.conn.commit()

    # Adds the attributes of the atom object into the Atoms table
    def add_atom(self, molname, atom):
        self.cursor.execute(f"""
            INSERT INTO Atoms (ELEMENT_CODE, X, Y, Z) 
                VALUES ("{atom.element}", {atom.x}, {atom.y}, {atom.z})
        """)
        
        atom_id = self.cursor.lastrowid # receives atom id from the last row entry
        
        self.cursor.execute(f"""
            INSERT INTO MoleculeAtom (MOLECULE_ID, ATOM_ID) 
            VALUES ((SELECT MOLECULE_ID FROM Molecules WHERE NAME = "{molname}"), {atom_id})
        """)

        self.conn.commit()

    # Adds the attributes of the bond object into the Bonds table
    def add_bond(self, molname, bond):
        self.cursor.execute(f"""
            INSERT INTO Bonds (A1, A2, EPAIRS)
                VALUES({bond.a1}, {bond.a2}, {bond.epairs})
        """)

        bond_id = self.cursor.lastrowid # retrieves bond id from the last row entry
        
        self.cursor.execute(f"""
            INSERT INTO MoleculeBond (MOLECULE_ID, BOND_ID)
                VALUES ((SELECT MOLECULE_ID FROM Molecules WHERE NAME ="{molname}"), {bond_id})
        """)
        
        self.conn.commit()
    
    # Adds the molecule to the Molecules table and append it the corresponding
    # Atoms and Bonds to the respective Atoms/Bonds/MoleculeAtom/MoleculeBond tables
    def add_molecule(self, name, fp):  
        # create molecule and parse the file contents
        molecule = MolDisplay.Molecule()
        molecule.parse(fp)

        self.cursor.execute(f"""
            INSERT INTO Molecules (NAME)
                VALUES ("{name}")
        """)

        # add atoms to the Atoms table
        for i in range(molecule.atom_no):
            atom = molecule.get_atom(i)
            self.add_atom(name, atom)

        # add bonds to the Bonds table
        for j in range(molecule.bond_no):
            bond = molecule.get_bond(j)
            self.add_bond(name, bond)

        self.conn.commit()

    def load_mol(self, name):
        # Retrieves all Atom columns from the molecules associated with the corresponding IDs and names
        atoms_query = self.cursor.execute(f"""
            SELECT Atoms.*
            FROM Molecules
            JOIN MoleculeAtom ON Molecules.MOLECULE_ID = MoleculeAtom.MOLECULE_ID
            JOIN Atoms ON MoleculeAtom.ATOM_ID = Atoms.ATOM_ID
            WHERE Molecules.NAME = "{name}"
            ORDER BY Atoms.ATOM_ID ASC
        """).fetchall()

        # Retrieves all Bonds columns from the molecules associated with the corresponding IDs and names
        bonds_query = self.cursor.execute(f"""
            SELECT Bonds.*
            FROM Molecules
            JOIN MoleculeBond ON Molecules.MOLECULE_ID = MoleculeBond.MOLECULE_ID
            JOIN Bonds ON MoleculeBond.BOND_ID = Bonds.BOND_ID
            WHERE Molecules.NAME = "{name}"
            ORDER BY Bonds.BOND_ID ASC
        """).fetchall()

        molecule = MolDisplay.Molecule() # create a new molecule
        
        for atom in atoms_query:
            # Element, X, Y, Z
            molecule.append_atom(atom[1], atom[2], atom[3], atom[4]) # type cast element to string only, not required for others
            
        for bond in bonds_query:
            # A1, A2, Epairs
            molecule.append_bond(bond[1], bond[2], bond[3])
        
        self.conn.commit()

        return molecule

    # Queries ELEMENT_CODE and RADIUS from Elements table and returns the radius dictionary
    def radius(self):
        elements_code_query = self.cursor.execute("SELECT ELEMENT_CODE, RADIUS FROM Elements").fetchall()
        radius = {} # empty dictionary
        for element in elements_code_query:    
            # key:value matching
            radius[element[0]] = element[1]
        
        self.conn.commit()

        return radius
    
    # Queries ELEMENT_NAME and RADIUS from Elements table and returns the elements_name dictionary
    def element_name(self):
        element_names_query = self.cursor.execute("SELECT ELEMENT_CODE, ELEMENT_NAME FROM Elements").fetchall()
        element_name = {} # empty dictionary
        for name in element_names_query:    
            # key:value matching
            element_name[name[0]] = name[1]
        
        self.conn.commit()

        return element_name

    # Returns a formatted gradient SVG
    def radial_gradients(self):
        svgs = []
        radialGradientSVG = """ 
            <radialGradient id="%s" cx="-50%%" cy="-50%%" r="220%%" fx="20%%" fy="20%%"> 
                <stop offset="0%%" stop-color="#%s"/> 
                <stop offset="50%%" stop-color="#%s"/> 
                <stop offset="100%%" stop-color="#%s"/> 
            </radialGradient>"""
        
        # fetch all the information and store into elements
        elements = self.cursor.execute("""SELECT ELEMENT_NAME, COLOUR1, COLOUR2, COLOUR3 FROM ELEMENTS """).fetchall()
        for element in elements:
            temp_string = radialGradientSVG % (element[0], element[1], element[2], element[3]) # element_name, colour1, colour2, colour3
            svgs.append(temp_string)

        self.conn.commit()
        
        return ''.join(svgs)


    # Debugging - prints each table in the data base``
    def printDatabase(self):
        tables = ("Elements", "Molecules", "Atoms", "Bonds", "MoleculeAtom", "MoleculeBond")
        for table in tables:
            print(f"\n{table} Table")
            for row in self.cursor.execute(f"SELECT * FROM {table}").fetchall():
                print(row)

    # Debugging - prints the values for a table
    def printTable(self, table):
        for row in self.cursor.execute(f"SELECT * from {table}").fetchall():
            print(row)