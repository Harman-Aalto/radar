// Functions

// Initialize the UI
function initializeUI() {
  // Build control UI
  buildControl = {};
  buildControl.buildButton = $("#build-graph-button");
  buildControl.invalidateCacheButton = $("#invalidate-graph-button");
  buildControl.minSimilaritySlider = $(".build-args-ui .slider-container input.similarity-slider");
  buildControl.minSimilaritySliderValue = $(".build-args-ui .slider-container p.similarity-slider-value");
  buildControl.minMatchCountSlider = $(".build-args-ui .slider-container input.match-count-slider");
  buildControl.minMatchCountSliderValue = $(".build-args-ui .slider-container p.match-count-slider-value");
  buildControl.uniqueCheckbox = $("#use-unique-checkbox");
  buildControl.buildButton.on("click", buildTable);
  connectSliderValueDisplay(
      buildControl.minMatchCountSlider,
      buildControl.minMatchCountSliderValue,
      parseInt
  );
  connectSliderValueDisplay(
      buildControl.minSimilaritySlider,
      buildControl.minSimilaritySliderValue,
      parseFloat
  );

  // Send request to invalidate the cache
  buildControl.invalidateCacheButton.on("click", _ => {
    startLoader("Invalidating server table cache");
    $.ajax({
        url: "invalidate",
        type: "POST",
        dataType: "text",
        success: _ => stopLoader(),
        error: console.error,
        beforeSend: CSRFpreRequestCallback,
    });
  });

  progressBarContainer = $("#load-progress");
}


// Build the table
function buildTable() {
  startLoader("Building table");

  clearTable();

  // Data to be sent to the server for the request
  let taskState = {
    task_id: '',
    ready: false,
    min_similarity: buildControl.minSimilaritySlider.val(),
    min_matches: buildControl.minMatchCountSlider.val(),
    unique_exercises: buildControl.uniqueCheckbox.is(":checked"),
  };

  // Poll timeouts
  let pollIndex = 0;
  const pollSeconds = [1, 1, 1, 2, 2, 4, 4, 10, 30];

  // On request success
  function pollSuccess(newTaskState) {
    if (taskState.ready) {
      return;
    }
    taskState = newTaskState;
    if (taskState.ready) {
      pollIndex = 0;
      let tableDefinition = taskState.graph_data;
      if (tableDefinition.nodes && tableDefinition.edges) {
        // Update the table
        updateTable(tableDefinition);

        // Stop the loader
        stopLoader();
      } else {
        console.error("Server completed the data retrieval but returned an invalid table definition object.");
      }
    } else {
      setTimeout(pollTableData, 1000 * pollSeconds[pollIndex]);
      pollIndex = Math.min(pollSeconds.length - 1, pollIndex + 1);
    }
  }

  // On request error
  function pollError(response) {
    console.error("Failed to poll for API read task state:", response.responseText);
  }

  // Poll the server for the table data
  function pollTableData() {
    if (taskState.ready) {
      return;
    }

    $.ajax({
      beforeSend: CSRFpreRequestCallback,
      url: "../graph/build", // /course_instance/graph/build
      method: "POST",
      dataType: "json",
      contentType: "application/json",
      data: JSON.stringify(taskState),
      success: pollSuccess,
      error: pollError,
    });
  }

  // Trigger table build and poll for completion
  pollTableData();
}


// Add a X-CSRFToken header containing the Django generated CSRF token before sending requests
function CSRFpreRequestCallback(xhr) {
  const csrfToken = $("input[name=csrfmiddlewaretoken]").val();
  xhr.setRequestHeader("X-CSRFToken", csrfToken);
}


// Show loading bar
function startLoader(message) {
  progressBarContainer.children(".progress-bar").children("span.loader-message").text(message);
  progressBarContainer.show();
}


// Hide loading bar
function stopLoader() {
  progressBarContainer.children(".progress-bar").children("span.loader-message").text('');
  progressBarContainer.hide();
}


// Update the table
function updateTable(tableDefinition) {
  // Get the clusters from the data
  let clusters = getClusters(tableDefinition.edges);

  // Get the data table
  let table = $('#clustersdatatable').DataTable();

  // Add the clusters to the table
  clusters.forEach(function(cluster, index) {
    table.row.add([
      `<a href="${index + 1}">Cluster${index + 1}</a>`,
      cluster['students'].join(", "),
      (cluster['similarity'] * 100).toFixed(0) + "%",
      cluster['students'].length
    ]);
  });

  table.draw();
}


// Helper function for getting the clusters from data
function getClusters(students) {
  var clusters = [];

  students.forEach(function(student) {
    // Check if the student source or target is already in a group
    var found = false;

    // Loop through the clusters
    clusters.forEach(function(cluster) {
      if (cluster['students'].has(student['source']) || cluster['students'].has(student['target'])) {

        cluster['students'].add(student['source']);
        cluster['students'].add(student['target']);

        student['matches_in_exercises'].forEach(function(exercise) {
          cluster['similarity'].push(exercise['max_similarity']);
        });

        found = true;
        return;
      }
    });

    // If the student is not in any cluster, create a new one
    if (!found) {
      var similarity = [];

      student['matches_in_exercises'].forEach(function(exercise) {
        similarity.push(exercise['max_similarity'])
      });

      clusters.push({
        'students': new Set([student['source'], student['target']]),
        'similarity': similarity
      });
    }
  });

  if (buildControl.uniqueCheckbox.is(":checked")) {
    // Merge the linked groups if they share a student
    clusters.forEach(function(cluster) {
      clusters.forEach(function(otherCluster) {

        // Skip if same cluster
        if (cluster['students'] !== otherCluster['students']) {

          cluster['students'].forEach(function(student) {

            // Check if other cluster has the student
            if (otherCluster['students'].has(student)) {
              // Merge the clusters
              cluster['students'] = new Set([...cluster['students'], ...otherCluster['students']]);
              cluster['similarity'] = cluster['similarity'].concat(otherCluster['similarity']);

              // Get index of the other cluster
              var index = clusters.indexOf(otherCluster);

              // Remove the other cluster
              if (index > 0){
                clusters.splice(index, 1);
              }

              return;
            }
          });
        }
      });
    });
  }

  // Sort the students in each cluster
  var collator = new Intl.Collator(undefined, {numeric: true, sensitivity: 'base'})

  // Sort the clusters and get average similarity
  for (let index = 0; index < clusters.length; index++) {
    clusters[index]['students'] = Array.from(clusters[index]['students']).sort(collator.compare);
    clusters[index]['similarity'] = clusters[index]['similarity'].reduce((a, b) => a + b, 0) / clusters[index]['similarity'].length;
  }

  return clusters;
}


// Clear the table
function clearTable() {
  $('#clustersdatatable').DataTable().clear().draw();
}


// Connect the slider value to the display
function connectSliderValueDisplay(slider, display, parser) {
  slider.on("input", _ => display.text(parser(slider.val())));
}


// Initialize the table
function initializeTable() {
  $('#clustersdatatable').DataTable( {
    lengthMenu: [
      [-1, 10, 25, 100],
      ["All", 10, 25, 100] ],
    columnDefs: [
      { type: 'natural', target: 0 },
      { className: 'dt-left', targets: '_all' },
    ]
  });
}


$(initializeUI);
$(initializeTable);
