const dropZone = document.getElementById('dropZone');
const status = document.getElementById('status');
const fileInput = document.getElementById('fileInput');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    
    const file = e.dataTransfer.files[0];
    handleFile(file);
});

// Add click handler for the drop zone
dropZone.addEventListener('click', () => {
    fileInput.click();
});

// Add change handler for the file input
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    handleFile(file);
});

function handleFile(file) {
    if (file && file.type.startsWith('image/')) {
        uploadFile(file);
    } else {
        status.textContent = 'Please select an image file';
    }
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('image', file);
    
    status.textContent = 'Converting...';
    status.className = 'converting';
    
    fetch('/convert', {
        method: 'POST',
        body: formData
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'converted.dxf';
        a.click();
        status.textContent = 'Conversion complete!';
        status.className = 'success';
    })
    .catch(error => {
        status.textContent = 'Error during conversion';
        status.className = 'error';
        console.error(error);
    });
} 