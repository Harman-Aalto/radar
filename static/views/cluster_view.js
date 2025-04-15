// Import
import {connectSliderValueDisplay} from "./helper_functions.js";


// Variables
var buildControl = {};
var buttonsControl = {};
var checkboxesControl = {};

// List of exercise names
var student_names = [];

// Functions

// Get exercise names from context
function getStudentNames() {
  $('.student_name').each(function() {
    student_names.push($(this).text().trim());
  });
}


// Initialize the UI
function initializeUI() {
  // Build control UI
  buildControl.filterButton = $("#filter-cluster-button");
  buildControl.minSimilaritySlider = $(".build-args-ui .slider-container input.similarity-slider");
  buildControl.minSimilaritySliderValue = $(".build-args-ui .slider-container p.similarity-slider-value");
  buildControl.filterButton.on("click", filterCells);

  // Connect the slider value display to the slider
  connectSliderValueDisplay(
    buildControl.minSimilaritySlider,
    buildControl.minSimilaritySliderValue,
    parseFloat
  );

  //Buttons
  buttonsControl.showALL = $('#show_all_students');
  buttonsControl.hideALL = $('#hide_all_students');
  buttonsControl.showALL.click(showAllStudents);
  buttonsControl.hideALL.click(hideAllStudents);

  // Show students
  for (var i = 0; i < student_names.length; i++) {
    checkboxesControl[student_names[i]] = $('#show_' + student_names[i]);
    checkboxesControl[student_names[i]].change(showStudent);
    if (checkboxesControl[student_names[i]].is(':checked')) {
      $(`.${student_names[i]}_column`).show();
    }
    else {
      $(`.${student_names[i]}_column`).hide();
    }
  }
}


// Show all exercises
function showAllStudents() {
  // Check all the checkboxes
  student_names.forEach(function(student) {
    $('#show_' + student).prop('checked', true);
    $(`.${student}_column`).show();
  });
}


// Hide all exercises
function hideAllStudents() {
  // Uncheck all the checkboxes
  student_names.forEach(function(student) {
    $('#show_' + student).prop('checked', false);
    $(`.${student}_column`).hide();
  });
}


// Filter cells based on the slider value
function filterCells() {
  // Get the slider value
  var sliderValue = parseFloat(buildControl.minSimilaritySlider.val()) * 100;

  // Get all the table cells
  var cells = $('#clustersdatatable td').filter(function() {
    return !this.className.includes('natural-sort')
  });

  // Loop through each cell and check its value
  cells.each(function() {
    var cellValue = parseFloat($(this).text().replace('%', ''));
    if (cellValue < sliderValue) {
      $(this).css('visibility', 'hidden'); // Hide the cell if it doesn't meet the criteria
    } else {
      $(this).css('visibility', 'visible'); // Show the cell if it meets the criteria
    }
  });

  hideEmptyCells();
}


// Hide empty cells
function hideEmptyCells() {
  // Get all the rows
  var rows = $('#clustersdatatable tr');

  // Loop through each row
  rows.each(function() {
    var row = $(this);
    var emptyCells = row.find('td').filter(function() {

      var hide = $(this).css('visibility') === 'hidden' || $(this).text() === '';

      if(!hide) {
        // Check if the cell is empty
        console.log("Value:", $(this).text());
      }

      return hide;
    });

    console.log(emptyCells.length, row.find('td').length - 1, row);
    // If all cells in the row are hidden, hide the row
    if (emptyCells.length === row.find('td').length - 1) {
      row.css('visibility', 'collapse');
    } else {
      row.css('visibility', 'visible');
    }
  });
}


// Initialize the table
function initializeTable() {
  var emptyString = DataTable.absoluteOrder( {
		value: "", position: 'bottom'
	});

	$('#clustersdatatable').DataTable( {
		lengthMenu: [
			[-1, 10, 25, 100],
			["All", 10, 25, 100]
    ],
		columnDefs: [
			{ type: 'natural', target: 0 },
			{ type: emptyString, targets: '_all' },
			{ className: 'dt-center', targets: '_all' },
		],
    order: [],
    fixedColumns: {
      start: 1,
    },
    scrollX: true,
    scrollY: '85vh',
    scrollCollapse: true,
	});

  // Highlight cells based on their percentage value
  highlightCells();

  // Add event listeners to the table cells
  $('#clustersdatatable td').on('mouseenter', handleMouseEnter);
  $('#clustersdatatable td').on('mouseleave', handleMouseLeave);
}


// Highlight cells based on their percentage value
function highlightCells() {
	// Get every table cell that has a percentage value
	var cells = $('#clustersdatatable td').filter(function() {
		return this.innerText.includes('%');
	});

	// Loop through each cell and change the background color
	for (var i = 0; i < cells.length; i++) {
		var cell = cells[i];
		// Get the value of the cell and remove % sign
		var value = cell.innerText.replace('%', '');

		// Convert the value to a number
		value = parseInt(value);
		// Set the background color based on the value
		if (100 >= value && value >= 80) {
			cell.style.backgroundColor = '#e96e5c';
		} else if (80 > value && value >= 60) {
			cell.style.backgroundColor = '#fdbb83';
		} else if (60 > value && value >= 40) {
			cell.style.backgroundColor = '#fee8c8';
		}
	};
}


// Handle mouse enter event
function handleMouseEnter() {
  var table = $('#clustersdatatable').DataTable();

  // Get the index of the cell
  let colIdx = table.cell(this).index().column;
  let rowIdx = table.cell(this).index().row;

  //Get head of the column
  let colHead = table.column(colIdx).header();

  // Change the header color
  colHead.classList.add('highlight');

  // Get the first cell of the row
  let rowHead = table.rows(rowIdx).nodes()[0].cells[0];

  // Change the header color
  rowHead.classList.add('highlight');

  // Change the background color of the cell
  this.classList.add('highlight');
}


// Handle mouse leave event
function handleMouseLeave() {
  var table = $('#clustersdatatable').DataTable();

  // Get the index of the cell
  let colIdx = table.cell(this).index().column;
  let rowIdx = table.cell(this).index().row;

  //Get head of the column
  let colHead = table.column(colIdx).header();

  // Change the header color
  colHead.classList.remove('highlight');

  // Get the first cell of the row
  let rowHead = table.rows(rowIdx).nodes()[0].cells[0];

  // Change the header color
  rowHead.classList.remove('highlight');

  // Change the background color of the cell
  this.classList.remove('highlight');
}


// Show student
function showStudent() {
  var student = this.id.split('_')[1];
  if (this.checked) {
    $(`.${student}_column`).show();
  } else {
    $(`.${student}_column`).hide();
  }
}


$(getStudentNames);
$(initializeUI);
$(initializeTable);
