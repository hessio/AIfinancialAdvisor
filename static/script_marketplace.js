// Get all the modal buttons
var modalBtns = document.querySelectorAll('.item');

// Add a click event listener to each modal button
modalBtns.forEach(function(btn) {
  btn.addEventListener('click', function() {
    // Get the modal ID from the data-modal attribute
    var modalId = btn.getAttribute('data-modal');

    // Get the modal element
    var modal = document.querySelector(modalId);
    
    // Display the modal
    modal.style.display = 'block';

    // Add a click event listener to the close button
    var closeBtn = modal.querySelector('.close-btn');
    closeBtn.addEventListener('click', function() {
      // Hide the modal
      modal.style.display = 'none';
    });
  });
});