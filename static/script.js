const fileInput = document.getElementById('file-input');
const fileLabel = document.getElementById('file-label-span');

fileInput.addEventListener('change', () => {
  const filename = fileInput.value.split('\\').pop();
  if (filename==='') {
    fileLabel.textContent = 'Choose file...';
  }
  else{
    fileLabel.textContent = '';
  }
});

var input_ = document.querySelector('input[type="file"]');
var previewImg = document.getElementById('preview');

input_.addEventListener('change', function () {
    var file = this.files[0];
    var reader = new FileReader();

    reader.onload = function (e) {
        previewImg.style.display = 'inline-block';
        previewImg.src = e.target.result;
    };

    reader.readAsDataURL(file);
});