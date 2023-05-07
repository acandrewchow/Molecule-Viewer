from http.server import HTTPServer, BaseHTTPRequestHandler
import sys, io, json, cgi
import MolDisplay, molsql, molecule

# Create DB
db = molsql.Database(reset=True)
db.create_tables()

# Set our default element values 
db['Elements'] = (1, 'H', 'Hydrogen', 'FFFFFF', '050505', '020202', 25)
db['Elements'] = (6, 'C', 'Carbon', '808080', '010101', '000000', 40)
db['Elements'] = (7, 'N', 'Nitrogen', '0000FF', '000005', '000002', 40)
db['Elements'] = (8, 'O', 'Oxygen', 'FF0000', '050000', '020000', 40)

# Add 3 molecules to the web page by default
fp = open('molecules/water-3D-structure.sdf')
db.add_molecule("Water", fp)

fp = open('molecules/caffeine-3D-structure-C.sdf')
db.add_molecule('Caffeine', fp)

fp = open('molecules/CID_31260.sdf')
db.add_molecule('Isopentanol', fp)

class myHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            with open("index.html", "rb") as f: # main page
                html = f.read()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html)
        
        elif self.path.endswith('.css'): # css
            with open("./public/css/styles.css", "rb") as f:
                css = f.read()
            # send CSS content
            self.send_response(200)
            self.send_header('Content-type', 'text/css')
            self.end_headers()
            self.wfile.write(css)

        elif self.path.endswith('.js'): # javascript 
            with open("./public/js/scripts.js", "rb") as f:
                js = f.read()
            # send JS content
            self.send_response(200)
            self.send_header('Content-type', 'text/javascript')
            self.end_headers()
            self.wfile.write(js)

        elif self.path.endswith('.jpg'): # header pic
            with open("./public/images/header.jpg", 'rb') as f:
                content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                self.wfile.write(content)

        # retrieves all molecules stored in the db
        elif self.path == "/retrieve-molecules":
            molecules_query = db.cursor.execute(f"""
                SELECT Molecules.NAME, COUNT(DISTINCT MoleculeAtom.ATOM_ID) AS numAtoms, COUNT(DISTINCT MoleculeBond.BOND_ID) AS numBonds
                FROM Molecules
                JOIN MoleculeAtom ON MoleculeAtom.MOLECULE_ID = Molecules.MOLECULE_ID
                JOIN Atoms ON MoleculeAtom.ATOM_ID = Atoms.ATOM_ID
                JOIN MoleculeBond ON MoleculeBond.MOLECULE_ID = Molecules.MOLECULE_ID
                JOIN Bonds ON MoleculeBond.BOND_ID = Bonds.BOND_ID
                GROUP BY Molecules.NAME;
            """).fetchall()

            molecules_list = []
            for molecule in molecules_query:
                molecule_values = {"name": molecule[0], "numAtoms": molecule[1], "numBonds": molecule[2]}
                molecules_list.append(molecule_values)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(molecules_list).encode())
        
        # retrieves all elements stored in the db
        elif self.path == "/retrieve-elements":
            elements_query = db.cursor.execute("""SELECT ELEMENT_NO, ELEMENT_CODE, ELEMENT_NAME, COLOUR1, COLOUR2, COLOUR3, RADIUS FROM ELEMENTS""").fetchall()
            elements_list = []

            for element in elements_query:
                element_values = {"Element No": element[0], "Element Code": element[1], "Element Name": element[2], "Colour 1": element[3], "Colour 2": element[4], "Colour 3": element[5], "Radius": element[6]}
                elements_list.append(element_values)
        
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(elements_list).encode())
        else:
            self.send_error(404, "Error Found")
            self.end_headers()
            self.wfile.write(bytes("404: Error Not found", "utf-8"))
        
    def do_POST(self):
        # request to display a molecule
        if self.path == '/molecule':
            content_length = int(self.headers.get('Content-Length'))
            molecule_data = self.rfile.read(content_length)
            data = json.loads(molecule_data)
            molecule_name = data.get('molecule') # receive the molecule name

            # Build our default dictionaries
            MolDisplay.radius = db.radius()
            MolDisplay.element_name = db.element_name()
            MolDisplay.header += db.radial_gradients()
            
            print(MolDisplay.element_name)

            # load the molecule and generate svg
            mol = db.load_mol(molecule_name)
            mol.sort()
            svg = mol.svg() # create the svg
            
            print(svg)
  
            # send the svg back to the client
            self.send_response(200)
            self.send_header('Content-type', 'image/svg+xml')
            self.end_headers()
            self.wfile.write(bytes(svg, "utf-8"))

        # request to upload a new molecule
        elif self.path == "/upload-file":
            cgi.parse_header(self.headers['Content-Type'])
            # Parse the form data to get the file and molecule name
            form = cgi.FieldStorage(
                fp = self.rfile,
                headers = self.headers,
                environ = {'REQUEST_METHOD': 'POST'}
            )

            # receive the file object
            file_item = form['file']
            molecule_name = form.getvalue('moleculeName')

            # read the file contents
            file_contents = file_item.file.read()

            # convert to bytes in order to parse
            bytes_io = io.BytesIO(file_contents)
            data = io.TextIOWrapper(bytes_io)

            # add the molecule to the database
            db.add_molecule(molecule_name, data)
            self.send_response(200)
            self.end_headers()
        
        # request to add an element to the database
        elif self.path == "/add-element":
            # Read the request body as JSON data
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            element_data = json.loads(body)

            # Insert the element into the Elements table
            db["Elements"] = (
                element_data["elementNum"],
                element_data["elementCode"],
                element_data["elementName"],
                element_data["colourOne"],
                element_data["colourTwo"],
                element_data["colourThree"],
                element_data["elementRadius"],
            )

            new_element = {
                "elementNum": element_data["elementNum"],
                "elementCode": element_data["elementCode"],
                "elementName": element_data["elementName"],
                "colourOne": element_data["colourOne"],
                "colourTwo": element_data["colourTwo"],
                "colourThree": element_data["colourThree"],
                "elementRadius": element_data["elementRadius"],
            }

        
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(new_element).encode())

        # request to remove an element from the database
        elif self.path == "/remove-element":
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            element_data = json.loads(body)
            # print(element_data)
            element_code = element_data['elementCode']

            # deletes the row in the Elements table matching the element code
            db.cursor.execute(f"""
                DELETE FROM Elements WHERE ELEMENT_CODE = "{element_code}";
            """)

            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))

        elif self.path == "/rotate-molecule":
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            rotate_data = json.loads(body)
            
            molecule_to_rotate = rotate_data['molecule'] # receive the molecule name

            try:
                x = int(rotate_data['x'])
            except:
                x = 0
            try:
                y = int(rotate_data['y'])
            except:
                y = 0 
            try:
                z = int(rotate_data['z'])
            except:
                z = 0
    
            # receive the molecule to rotate
            mol = db.load_mol(molecule_to_rotate)

            # rotate the molecule
            mx = molecule.mx_wrapper(x, y, z)
            mol.xform(mx.xform_matrix)

            # receive the new SVG after rotation and send to client
            svg = mol.svg()

            self.send_response(200)
            self.send_header('Content-type', 'image/svg+xml')
            self.end_headers()
            self.wfile.write(bytes(svg, "utf-8"))
        else:
            self.send_error(404, "Error Found")
            self.end_headers()
            self.wfile.write(bytes("404: Error Not found", "utf-8"))

httpd = HTTPServer(('localhost', int(sys.argv[1])), myHandler)
httpd.serve_forever()