$(document).ready(function () {
  // Scroll reveal library
  ScrollReveal().reveal(
    "#upload-section, #select-molecule, #add-element, #elements-section, #rotate-container, #svg-display",
    {
      delay: 100,
      duration: 1000,
      easing: "cubic-bezier(0.5, 0, 0, 1)",
      origin: "bottom",
      distance: "50px",
      threshhold: 0.5,
    }
  );

  // Typing library'
  const typed = new Typed(".auto-type", {
    strings: ["Atoms", "Bonds", "Molecules"],
    typeSpeed: 150,
    backSpeed: 100,
    loop: true,
  });

  // Validates the input for Add Element
  function validateInput() {
    const elementNum = $("#element-number").val();
    const elementCode = $("#element-code").val();
    const elementName = $("#element-name").val();
    const colourOne = $("#color-value-1").val();
    const colourTwo = $("#color-value-2").val();
    const colourThree = $("#color-value-3").val();
    const elementRadius = $("#element-radius").val();

    // 118 represents last element on periodic table
    if (!/^\d+$/.test(elementNum) || elementNum > 118) {
      $(".success-element")
        .text("Element number should be a number and less than 119")
        .addClass("error");
      return false;
    }

    if (!/^[A-Za-z]+$/.test(elementCode) || elementCode.length > 2) {
      $(".success-element")
        .text(
          "Element code must be 2 characters or less and only contain letters"
        )
        .addClass("error");
      return false;
    }

    if (!/^[A-Za-z]+$/.test(elementName)) {
      $(".success-element")
        .text("Element name should be a letter")
        .addClass("error");
      return false;
    }

    if (!colourOne || colourOne.length !== 6) {
      $(".success-element").text("Invalid Colour 1!").addClass("error");
      return false;
    }

    if (!colourTwo || colourTwo.length !== 6) {
      $(".success-element").text("Invalid Colour 2!").addClass("error");
      return false;
    }

    if (!colourThree || colourThree.length !== 6) {
      $(".success-element").text("Invalid Colour 3!").addClass("error");
      return false;
    }

    if (!/^\d*\.?\d+$/.test(elementRadius) || elementRadius <= 0) {
      $(".success-element")
        .text("Element radius should be a number greater than 0!")
        .addClass("error");
      return false;
    }

    return true;
  }

  // Returns a promise with the number of atoms and bonds
  function readSDFFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsText(file);

      reader.onload = function (e) {
        // Extract the atoms and bonds values on the 4th line
        const fileContent = e.target.result;
        const lines = fileContent.split("\n");
        const atomsLine = lines[3];
        const atoms = atomsLine.slice(0, 3).trim();
        const bonds = atomsLine.slice(3, 6).trim();

        resolve({ atoms, bonds });
      };
      reader.onerror = reject;
    });
  }


  let originalSVG; // used to reset molecule during rotation

  // Changes the Molecule displayed when selected
  $("#molecules").change(function (e) {
    e.preventDefault();
    const selectedMolecule = $(this).val();

    if (selectedMolecule === "") {
      // If it is empty, clear the SVG area and return
      $(".svg-area").empty();
      return;
    }

    $.ajax({
      url: "/molecule",
      type: "POST",
      data: JSON.stringify({ molecule: selectedMolecule }),
      contentType: "application/json",
      success: function (svg) {
        console.log(svg);

        const svgString = new XMLSerializer().serializeToString(svg);
        originalSVG = svgString;
        // console.log(svgString)
        $(".svg-area").empty();
        $(".svg-area").html(svgString);
      },
      error: function () {
        console.log("Error trying to fetch SVG for " + selectedMolecule);
        $(".svg-area").html("Cannot Display Molecule!");
      },
    });
  });

  // Retrieves all elements in the DB when the server loads
  $.ajax({
    url: "/retrieve-elements",
    type: "GET",
    success: function (elementData) {
      const tableBody = $(".elements-table tbody");
      tableBody.empty();

      if (elementData.length === 0) {
        // If there are no elements, display a message
        const noElementsMessage = $("<h2>", {
          class: "title",
          text: "No Elements Found",
        });

        $(".elements-container").html(noElementsMessage);
        return;
      } else {
        // Otherwise, update the table with the element data
        $.each(elementData, function (index, value) {
          const tr = $("<tr>");
          tr.append(
            $("<td>", { class: "element-number", text: value["Element No"] })
          );
          tr.append(
            $("<td>", { class: "element-code", text: value["Element Code"] })
          );
          tr.append(
            $("<td>", { class: "element-name", text: value["Element Name"] })
          );
          tr.append($("<td>", { class: "colour-1", text: value["Colour 1"] }));
          tr.append($("<td>", { class: "colour-2", text: value["Colour 2"] }));
          tr.append($("<td>", { class: "colour-3", text: value["Colour 3"] }));
          tr.append($("<td>", { class: "radius", text: value["Radius"] }));
          tr.append(
            $("<td>").append(
              $("<button>", { class: "remove-button", text: "×" })
            )
          );
          tableBody.append(tr);
        });
      }
    },
    error: function (xhr, status, error) {
      console.log("Error retrieving element data: " + error);
    },
  });

  // Retrieves all molecules in the DB when the server loads
  $.ajax({
    url: "/retrieve-molecules",
    type: "GET",
    success: function (moleculeData) {
      const selectOption = $("#molecules");
      selectOption.empty();
      selectOption.append(
        $("<option>", {
          value: "",
          text: "Choose Molecule",
        })
      );
      $.each(moleculeData, function (index, value) {
        selectOption.append(
          $("<option>", {
            value: value.name,
            text:
              value["name"] +
              " (Atoms: " +
              value["numAtoms"] +
              ", Bonds: " +
              value["numBonds"] +
              ")",
          })
        );
      });
    },
    error: function (xhr, status, error) {
      console.log("Error: " + status);
    },
  });

  // Adds a molecule to the drop-down menu after successful upload
  $("#upload-form").submit(async function (e) {
    e.preventDefault();

    // receive the file name
    const file = $("#sdf_file")[0].files[0];
    console.log(file);
    // Check if the selected file is a valid .sdf file
    if (file && file.name.endsWith(".sdf")) {
      // prompt user to input a name for the file
      const moleculeName = prompt("Enter a name for molecule: ", file.name);

      // FormData object to hold information
      const formData = new FormData();

      formData.append("file", file);
      formData.append("moleculeName", moleculeName);

      const { atoms, bonds } = await readSDFFile(file);

      if (atoms > 0 && bonds > 0) {
        // POST request to the server
        $.ajax({
          url: "/upload-file",
          type: "POST",
          data: formData,
          processData: false,
          contentType: false,
          success: function (response) {
            // Handle the response from the server
            alert("Successfully uploaded file!");
            const newMolecule = $("<option>")
              .val(moleculeName)
              .text(`${moleculeName} (Atoms: ${atoms}, Bonds: ${bonds})`);
            $("#molecules").append(newMolecule);
            $(".file-chosen").text("").removeClass("default"); // reset field after the file has been uploaded
          },
          error: function (xhr, status, error) {
            console.error(error);
            alert(
              "Upload Failed! Please enter a valid SDF file with a unique molecule name!"
            );
          },
        });
      }
    } else {
      $(".file-chosen")
        .text("Invalid File! You must upload a valid .SDF file")
        .addClass("error");
    }
  });

  $("#sdf_file").change(function () {
    const fileName = $(this).val().split("\\").pop();
    if (fileName.endsWith(".sdf")) {
      $(".file-chosen")
        .text("File Selected: " + fileName)
        .addClass("default");
    } else {
      $(".file-chosen")
        .text("Invalid File! You must upload a .SDF file")
        .addClass("error");
    }
  });

  // Add an element to the table
  $(".add-element-button").click(function (e) {
    e.preventDefault();

    if (validateInput()) {
      const elementNum = $("#element-number").val();
      const elementCode = $("#element-code").val();
      const elementName = $("#element-name").val();
      const colourOne = $("#color-value-1").val();
      const colourTwo = $("#color-value-2").val();
      const colourThree = $("#color-value-3").val();
      const elementRadius = $("#element-radius").val();

      const elementData = {
        elementNum: elementNum,
        elementCode: elementCode,
        elementName: elementName,
        colourOne: colourOne,
        colourTwo: colourTwo,
        colourThree: colourThree,
        elementRadius: elementRadius,
      };
      $.ajax({
        type: "POST",
        url: "/add-element",
        data: JSON.stringify(elementData),
        contentType: "application/json; charset=utf-8",
        dataType: "json", // return value must be json
        success: function (newElement) {
          const newRow = `<tr>
          <td class="element-no">${newElement.elementNum}</td>
          <td class="element-code">${newElement.elementCode}</td>
          <td class="element-name">${newElement.elementName}</td>
          <td class="colour-1">${newElement.colourOne}</td>
          <td class="colour-2">${newElement.colourTwo}</td>
          <td class="colour-3">${newElement.colourThree}</td>
          <td class="radius">${newElement.elementRadius}</td>
          <td><button class="remove-button">X</button></td>
        </tr>`;

          // Adds a new row to the table with new element values
          $("tbody").append(newRow);
          $(".success-element").text("");
          $(".success-element")
            .text("Element " + elementName + " has been added")
            .addClass("success");

          // Reset form fields
          $("#element-number").val("");
          $("#element-code").val("");
          $("#element-name").val("");
          $("#color-value-1").val("");
          $("#color-value-2").val("");
          $("#color-value-3").val("");
          $("#element-radius").val("");
        },
        error: function (xhr, status, error) {
          $(".success-element")
            .text("Element " + elementName + " cannot be added!")
            .addClass("error");
          console.log(error);
        },
      });
    }
  });

  // Remove an element from the table
  $("table").on("click", ".remove-button", function () {
    const row = $(this).closest("tr");
    const elementNum = row.find(".element-no").text();
    const elementCode = row.find(".element-code").text();
    const elementName = row.find(".element-name").text();
    const colour1 = row.find(".colour-1").text();
    const colour2 = row.find(".colour-2").text();
    const colour3 = row.find(".colour-3").text();
    const radius = row.find(".radius").text();
    row.remove();

    const elementData = {
      elementNum: elementNum,
      elementCode: elementCode,
      elementName: elementName,
      colourOne: colour1,
      colourTwo: colour2,
      colourThree: colour3,
      elementRadius: radius,
    };
    $.ajax({
      type: "POST",
      url: "/remove-element",
      data: JSON.stringify(elementData),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        $(".success-element")
          .text("Element " + elementName + " has been removed")
          .addClass("success");
        console.log(response);
      },
      error: function (xhr, status, error) {
        $(".success-element")
          .text("Element " + elementName + " cannot be removed!")
          .addClass("error");
        console.log(xhr, status, error);
      },
    });

    $("#element-number").val("");
    $("#element-code").val("");
    $("#element-name").val("");
    $("#color-value-1").val("");
    $("#color-value-2").val("");
    $("#color-value-3").val("");
    $("#element-radius").val("");
  });

  // Rotates molecule along the x, y or z-axis
  $(".rotate-molecule-button").click(function (e) {
    e.preventDefault();
    const x = $("#rotate-x").val();
    const y = $("#rotate-y").val();
    const z = $("#rotate-z").val();

    const selectedMolecule = $("#molecules").val();

    rotateData = {
      molecule: selectedMolecule,
      x: x,
      y: y,
      z: z,
    };

    if (isNaN(x) || isNaN(y) || isNaN(z)) {
      $(".rotate-message")
        .text("Invalid Data! Please enter a number")
        .addClass("error");
    } else if (x === "" && y === "" && z === "") {
      $(".rotate-message")
        .text("Blank Data! Please enter a number")
        .addClass("error");
    } else if ($("#molecules").val() === "") {
      $(".rotate-message")
        .text("Cannot Rotate! No Molecule Selected")
        .addClass("error");
    } else {
      $.ajax({
        url: "/rotate-molecule",
        type: "POST",
        data: JSON.stringify(rotateData),
        contentType: "application/json",
        success: function (svg) {
          const svgString = new XMLSerializer().serializeToString(svg);
          $(".svg-area").empty();
          $(".svg-area").html(svgString);
          $(".rotate-message")
            .text("Successfully Rotated Molecule!")
            .addClass("success");
        },
        error: function () {
          console.log("Error trying to fetch SVG for " + selectedMolecule);
          $(".svg-area").html("Cannot Display Molecule!");
        },
      });
    }
  });

  // Resets the molecule to its original orientation
  $(".reset-molecule-button").click(function (e) {
    e.preventDefault();
    $(".rotate-message").text("Molecule Reset!!").addClass("success");
    $(".svg-area").html(originalSVG); // reset the rotation when button is clicked
  });

  // Received selected molecule
  $("#select-molecule").change(function () {
    const selectedMolecule = $("#molecules").val();
    if ($(".svg-molecule-name") === "") {
      $(".svg-molecule-name").text("No Molecule Selected");
    }
    $(".svg-molecule-name").text(selectedMolecule);
  });
});
