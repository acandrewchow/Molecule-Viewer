#include "mol.h"

// Sets the values of a given atom
void atomset(atom * atom, char element[3], double * x, double * y, double * z) {
    strcpy(atom->element, element);
    atom->x = *x;
    atom->y = *y;
    atom->z = *z;
}

// Retrieves an an atom by passing an atom pointer
void atomget(atom * atom, char element[3], double * x, double * y, double * z) {
    strcpy(element, atom->element);
    *x = atom->x;
    *y = atom->y;
    *z = atom->z;
}

// Sets the value for a bond between two atoms
void bondset(bond * bond, unsigned short * a1, unsigned short * a2, atom ** atoms, unsigned char * epairs ) {
    bond->a1 = *a1;
    bond->a2 = *a2;
    bond->atoms = *atoms;
    bond->epairs = *epairs;
    // Compute the values for the given bond
    compute_coords(bond);
}

// Retrieves a bond by passing a bond pointer
void bondget(bond * bond, unsigned short * a1, unsigned short * a2, atom ** atoms, unsigned char * epairs ) {
    *a1 = bond->a1;
    *a2 = bond->a2;
    *atoms = bond->atoms;
    *epairs = bond->epairs;
}

// Allocates memory for a new mocule based on the passed values of atom_max and bond_max
// The function checks each malloc, if the value is NULL the function prints to stderr and exits
molecule * molmalloc(unsigned short atom_max, unsigned short bond_max) {
    molecule * newMolecule = malloc(sizeof(molecule));
    if (newMolecule == NULL) {
        return NULL;
    }
    // Assign atom values
    newMolecule->atom_max = atom_max;
    newMolecule->atom_no = 0;
    
    newMolecule->atoms = malloc(sizeof(atom) * atom_max);
    if (newMolecule->atoms == NULL) {
        return NULL;
    }

    newMolecule->atom_ptrs = malloc(sizeof(atom*) * atom_max);
    if (newMolecule->atom_ptrs == NULL) {
       return NULL;
    }
    // Assign bond values
    newMolecule->bond_max = bond_max;
    newMolecule->bond_no = 0;

    newMolecule->bonds = malloc(sizeof(bond) * bond_max);
    if (newMolecule->bonds == NULL) {
        return NULL;
    }

    newMolecule->bond_ptrs = malloc(sizeof(bond*) * bond_max);
    if (newMolecule->bond_ptrs == NULL) {
        return NULL;
    }
    // Return the address for the new copied molecule if successful
    return newMolecule;
}

/* Creates a new molecule and assigns the values located in the src */
molecule * molcopy(molecule * src) {
    // Checks if memory is valid
    if (src == NULL) {
        return NULL;
    }
    // Allocating a new molecule with the src's sizes for both atoms and bonds maximum valiue
    molecule * destination = molmalloc(src->atom_max, src->bond_max);

    // Check if memory is valid
    if (destination == NULL) {
        return NULL;
    }
    
    // Copies values from src to destination
    destination->atom_max = src->atom_max;
    destination->bond_max = src->bond_max;

    // add atoms to the new molecule and updates the pointers
    for (int i = 0; i < src->atom_no; i++) {
        molappend_atom(destination, &src->atoms[i]);
    }
    // add bonds to the new molecule and updates the pointers
    for (int i = 0; i < src->bond_no; i++) {
        molappend_bond(destination, &src->bonds[i]);
    }
    // return the address with the new malloced memory
    return destination;
}

/*
Frees all of the atoms, atom ptrs, bonds, bond ptrs arrays within the structure, then free's
the structure itself
*/
void molfree(molecule * ptr) {
    if (ptr == NULL) {
        fprintf(stderr, "Error, cannot free the molecule");
        exit(1);
    }
    // Free's the arrays within the molecule
    free(ptr->atoms);
    free(ptr->atom_ptrs);
    free(ptr->bonds);
    free(ptr->bond_ptrs);
    // free the molecule structure
    free(ptr);
}

// Appends an atom to a molecule
void molappend_atom(molecule * molecule, atom * atom) {
    // Check if its empty, increase atom max for space for a single atom
    if (molecule->atom_max == 0) {
        molecule->atom_max = 1;
    }   
    // Check if its full, double for sufficient space
    else if (molecule->atom_max == molecule->atom_no) {
        molecule->atom_max *= 2;
    }
    // Otherwise append since there is space available
    // Reallocate memory to the atoms and atom ptrs array based on the array's size
    molecule->atoms = realloc(molecule->atoms, sizeof(*atom) * molecule->atom_max);
    molecule->atom_ptrs = realloc(molecule->atom_ptrs, sizeof(*atom) * molecule->atom_max);

    // Check if reallocation is valid
    if ((molecule->atoms == NULL) || (molecule->atom_ptrs == NULL)) {
        fprintf(stderr, "NULL");
        exit(1);
    }

    // updates the atom pointers to the new corresponding atoms in the atoms array
    for (int i = 0; i < molecule->atom_no; i++) {
        molecule->atom_ptrs[i] = &(molecule->atoms[i]);
    }
    
    // Copy the values from the atom (src) to the first atom in the atoms array (destination)
    atomset(&(molecule->atoms[molecule->atom_no]), atom->element, &(atom->x), &(atom->y), &(atom->z));

    // Point our atom ptrs to the atoms array
    molecule->atom_ptrs[molecule->atom_no] = &(molecule->atoms[molecule->atom_no]);

    // increment after adding
    molecule->atom_no++;
}

// Appends a bond to a molecule
void molappend_bond(molecule * molecule, bond * bond) {
    // Check if its empty, increase atom max for space for a single bond
    if (molecule->bond_max == 0) {
        molecule->bond_max = 1;
    }
    // Check if its full, double for sufficient space
    else if (molecule->bond_max == molecule->bond_no) {
        molecule->bond_max *=2;
    }
    // Otherwise append since there is space available
    // Reallocate memory to the bonds and bond ptrs array based on the array's size
    molecule->bonds = realloc(molecule->bonds, sizeof(*bond) * molecule->bond_max);
    molecule->bond_ptrs = realloc(molecule->bond_ptrs, sizeof(*bond) * molecule->bond_max);

    // Check if reallocaiton is valid
    if ((molecule->bonds == NULL) || (molecule->bond_ptrs == NULL)) {
        fprintf(stderr, "NULL");
        exit(1);
    }
    
    // updates the bond pointers to the new corresponding bonds in the bonds array
    for (int i = 0; i < molecule->bond_no; i++) {
        molecule->bond_ptrs[i] = &(molecule->bonds[i]);
    }
    // Set the values for the bonds
    bondset(&(molecule->bonds[molecule->bond_no]), &(bond->a1), &(bond->a2), &(bond->atoms), &(bond->epairs));

    // Create our array of bond_ptrs
    molecule->bond_ptrs[molecule->bond_no] = &(molecule->bonds[molecule->bond_no]);

    // Increment the number of bonds after appending
    molecule->bond_no++;
}

// Sorts the bonds and atoms in the molecule based on the Z value in increasing order
void molsort(molecule * molecule) {
    if (molecule == NULL) {
        fprintf(stderr, "NULL");
        exit(1);
    }
    // Sorting Atom ptrs
    qsort(molecule->atom_ptrs, molecule->atom_no, sizeof(atom*), atom_comp);
    // Sorting Bond ptrs
    qsort(molecule->bond_ptrs, molecule->bond_no, sizeof(bond*), bond_comp);
}

// Sets the matrix's values to perform x rotation
void xrotation(xform_matrix xform_matrix, unsigned short deg) {
    /* 
        Rotation around X-axis
        [1][0][0]
        [0][cos(theta)][-sin(theta)]
        [0][sin(theta)][cos(theta)]
    */
    double rad = deg * M_PI / 180.0;
    xform_matrix[0][0] = 1;
    xform_matrix[0][1] = 0;
    xform_matrix[0][2] = 0;
    xform_matrix[1][0] = 0;
    xform_matrix[1][1] = cos(rad);
    xform_matrix[1][2] = -sin(rad);
    xform_matrix[2][0] = 0;
    xform_matrix[2][1] = sin(rad);
    xform_matrix[2][2] = cos(rad);
}
// Sets the matrix's values to perform y rotation
void yrotation(xform_matrix xform_matrix, unsigned short deg) {
    /*
        Rotation around Y-axis
        [cos(theta)][0][sin(theta)]
        [0][1][0]
        [-sin(theta)][0][cos(theta)]
    */
    double rad = deg * M_PI / 180.0;
    xform_matrix[0][0] = cos(rad);
    xform_matrix[0][1] = 0;
    xform_matrix[0][2] = sin(rad);
    xform_matrix[1][0] = 0;
    xform_matrix[1][1] = 1;
    xform_matrix[1][2] = 0;
    xform_matrix[2][0] = -sin(rad);
    xform_matrix[2][1] = 0;
    xform_matrix[2][2] = cos(rad);
}

// Sets the matrix's values to perform z rotation
void zrotation(xform_matrix xform_matrix, unsigned short deg) {
    /*
        Rotation around Z-axis
        [cos(theta)][-sin(theta)][0]
        [sin(theta)][cos(theta)][0]
        [0][0][1]
    */
    double rad = deg * M_PI / 180.0;
    xform_matrix[0][0] = cos(rad);
    xform_matrix[0][1] = -sin(rad);
    xform_matrix[0][2] = 0;
    xform_matrix[1][0] = sin(rad);
    xform_matrix[1][1] = cos(rad);
    xform_matrix[1][2] = 0;
    xform_matrix[2][0] = 0;
    xform_matrix[2][1] = 0;
    xform_matrix[2][2] = 1;
}

// Iterates through all the bonds and atoms in th molecule and performs
// matrix multiplication with each x y and z value in the 3x3 matrix passed in
void mol_xform(molecule * molecule, xform_matrix matrix) {

    double x, y, z = 0;

    // Check if the molecule passed in is valid
    if (molecule == NULL) {
        fprintf(stderr, "NULL");
        exit(1);
    }
    // Iterate over the atoms in the molecule
    for (int i = 0; i < molecule->atom_no; i++) {
        // Store temp values to ensure the values are not overwriting one another
        x = molecule->atoms[i].x;
        y = molecule->atoms[i].y;
        z = molecule->atoms[i].z;
        // Computes matrix multiplication with the x, y, z value in each atom to a 3x3 matrix
        molecule->atoms[i].x = (matrix[0][0] * x) + (matrix[0][1] * y) + (matrix[0][2] * z);
        molecule->atoms[i].y = (matrix[1][0] * x) + (matrix[1][1] * y) + (matrix[1][2] * z);
        molecule->atoms[i].z = (matrix[2][0] * x) + (matrix[2][1] * y) + (matrix[2][2] * z);
    }
    // Iterate over all the bonds in the molecule and set the values
    for (int i = 0; i < molecule->bond_no; i++) {
        compute_coords(&(molecule->bonds[i]));
    }
}
// Compares the Z value of two given atoms
int atom_comp(const void * atomOne, const void * atomTwo) {
    // cast to an atom struct
    const atom *a1 = *(const atom**)atomOne;
    const atom *a2 = *(const atom**)atomTwo;

    // Returns an integer depending on the result of a1 and a2
    if (a1->z > a2->z) {
        return 1;
    }
    else if (a1->z < a2->z) {
        return -1;
    }
    return 0;
}
// Compares the Z value of two given bonds by finding the average
int bond_comp(const void * bondOne, const void * bondTwo) {
    // cast to a bond struct
    const bond *b1 = *(const bond**)bondOne;
    const bond *b2 = *(const bond**)bondTwo;

    // Returns an integer depending on the result of b1 and b2
    if (b1->z > b2->z) {
        return 1;
    }
    else if (b1->z < b2->z) {
        return -1;
    }
    return 0;
}

// Calculates the values for the bonds
void compute_coords(bond * bond) {
    // retrieve our addresses for our atoms at index a1 and a2
    atom * a1 = &(bond->atoms[bond->a1]);
    atom * a2 = &(bond->atoms[bond->a2]);

    // Assign the coordinates for a1 (x1, y1)
    bond->x1 = a1->x;
    bond->y1 = a1->y;
    
    // assign the coordinates for a2 (x2, y2)
    bond->x2 = a2->x;
    bond->y2 = a2->y;

    // average z value between the values a1 and a2
    bond->z = (a1->z + a2->z) / 2.0;

    // Calculate the distance from a1 -> a2 in 2-D space
    bond->len = sqrt(fabs(pow(bond->x2 - bond->x1, 2)) + fabs(pow(bond->y2 - bond->y1, 2)));

    // differences between x and y values of a2 and a1
    bond->dx = (bond->x2 - bond->x1) / (bond->len);
    bond->dy = (bond->y2 - bond->y1) / (bond->len);
}
