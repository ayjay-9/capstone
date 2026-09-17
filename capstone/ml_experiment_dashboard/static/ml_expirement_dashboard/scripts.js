// Handle dataset upload, including drag-and-drop onto the drop zone
document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("drop-zone");
    const datasetInput = document.getElementById("dataset");
    const dropZoneText = document.getElementById("drop-zone-text");

    if (!dropZone || !datasetInput || !dropZoneText) {
        return;
    }

    const showSelectedFileName = () => {
        if (datasetInput.files.length > 0) {
            dropZoneText.textContent = datasetInput.files[0].name;
        }
    };

    datasetInput.addEventListener("change", showSelectedFileName);

    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.add("drag-over");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.remove("drag-over");
        });
    });

    dropZone.addEventListener("drop", (event) => {
        const droppedFiles = event.dataTransfer.files;
        if (droppedFiles.length > 0) {
            datasetInput.files = droppedFiles;
            showSelectedFileName();
        }
    });
});
