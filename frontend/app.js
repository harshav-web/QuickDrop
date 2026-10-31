const fileInput = document.getElementById("fileInput");
const browseButton = document.getElementById("browseButton");
const dropZone = document.getElementById("dropZone");
const selectedFile = document.getElementById("selectedFile");
const fileName = document.getElementById("fileName");
const fileSize = document.getElementById("fileSize");
const removeFile = document.getElementById("removeFile");
const uploadButton = document.getElementById("uploadButton");
const expirySelect = document.getElementById("expirySelect");
const statusBox = document.getElementById("status");
const progressWrap = document.getElementById("progressWrap");
const progressBar = document.getElementById("progressBar");
const resultCard = document.getElementById("resultCard");
const shareLink = document.getElementById("shareLink");
const copyButton = document.getElementById("copyButton");

let selected = null;

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function showStatus(message, isError = false) {
  statusBox.textContent = message;
  statusBox.classList.toggle("error", isError);
}

function chooseFile(file) {
  if (!file) return;
  if (file.size > 50 * 1024 * 1024) {
    showStatus("This file is larger than 50 MB.", true);
    return;
  }

  selected = file;
  fileName.textContent = file.name;
  fileSize.textContent = formatSize(file.size);
  selectedFile.classList.remove("hidden");
  uploadButton.disabled = false;
  resultCard.classList.add("hidden");
  showStatus("");
}

browseButton.addEventListener("click", () => fileInput.click());
dropZone.addEventListener("click", (event) => {
  if (event.target !== browseButton) fileInput.click();
});
dropZone.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") fileInput.click();
});
fileInput.addEventListener("change", () => chooseFile(fileInput.files[0]));

removeFile.addEventListener("click", () => {
  selected = null;
  fileInput.value = "";
  selectedFile.classList.add("hidden");
  uploadButton.disabled = true;
  showStatus("");
});

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragging");
  });
});

dropZone.addEventListener("drop", (event) => {
  chooseFile(event.dataTransfer.files[0]);
});

uploadButton.addEventListener("click", () => {
  if (!selected) return;

  const formData = new FormData();
  formData.append("file", selected);
  formData.append("expires_in_hours", expirySelect.value);

  uploadButton.disabled = true;
  progressWrap.classList.remove("hidden");
  progressBar.style.width = "0%";
  showStatus("Uploading your file...");

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/api/upload");

  xhr.upload.addEventListener("progress", (event) => {
    if (event.lengthComputable) {
      const percent = Math.round((event.loaded / event.total) * 100);
      progressBar.style.width = `${percent}%`;
    }
  });

  xhr.addEventListener("load", () => {
    progressWrap.classList.add("hidden");
    uploadButton.disabled = false;

    let data;
    try {
      data = JSON.parse(xhr.responseText);
    } catch {
      showStatus("The server returned an unexpected response.", true);
      return;
    }

    if (xhr.status < 200 || xhr.status >= 300) {
      showStatus(data.detail || "Upload failed. Please try again.", true);
      return;
    }

    shareLink.value = data.download_url;
    document.getElementById("resultFileName").textContent = data.filename;
    document.getElementById("expiryText").textContent =
      `Link expires at ${new Date(data.expires_at).toLocaleString()}`;
    document.getElementById("openLink").href = data.download_url;
    resultCard.classList.remove("hidden");
    showStatus("Upload complete!");
  });

  xhr.addEventListener("error", () => {
    progressWrap.classList.add("hidden");
    uploadButton.disabled = false;
    showStatus("Could not connect to the server. Please try again.", true);
  });

  xhr.send(formData);
});

copyButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(shareLink.value);
    copyButton.textContent = "Copied!";
    setTimeout(() => { copyButton.textContent = "Copy link"; }, 1800);
  } catch {
    shareLink.select();
    document.execCommand("copy");
    copyButton.textContent = "Copied!";
  }
});
