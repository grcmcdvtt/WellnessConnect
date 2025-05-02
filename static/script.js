// -------------------- DOM READY HANDLER --------------------
document.addEventListener("DOMContentLoaded", function () {
    setupSidebarToggle();
    initializeFlashMessages();
    initializeLogSectionToggles();
});

// -------------------- SIDEBAR TOGGLE --------------------
function setupSidebarToggle() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.toggle-btn');
    if (sidebar && toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('expanded');
        });
    }
}

// -------------------- MODAL HANDLERS --------------------
function openModal() {
    document.getElementById("uploadModal").style.display = "block";
}

function closeModal() {
    const modal = document.getElementById("uploadModal");
    if (!modal) return;

    modal.style.display = "none";

    const imagePreview = document.getElementById("imagePreview");
    if (imagePreview) {
        imagePreview.style.display = "none";
        imagePreview.src = "#";
    }

    const flashContainer = modal.querySelector(".flash-messages");
    if (flashContainer) flashContainer.remove();

    window.hasFlashMessage = false;
    window.flashMessages = [];

    pendingForm = null;
}

function openProofModal(imageUrl) {
    const modal = document.getElementById('proofModal');
    const img = document.getElementById('proofImagePreview');
    if (modal && img) {
        img.src = imageUrl;
        modal.style.display = 'block';
    }
}

function closeProofModal() {
    const modal = document.getElementById('proofModal');
    const img = document.getElementById('proofImagePreview');
    if (modal && img) {
        modal.style.display = 'none';
        img.src = '#';
    }
}

window.onclick = function(event) {
    const uploadModal = document.getElementById("uploadModal");
    const proofModal = document.getElementById("proofModal");

    if (event.target === uploadModal) {
        closeModal();
    } else if (event.target === proofModal) {
        closeProofModal();
    }
};

// -------------------- IMAGE PREVIEW --------------------
function previewImageAndOpenModal(event) {
    previewImage(event);
    openModal();
}

function previewImage(event) {
    const preview = document.getElementById("imagePreview");
    const file = event.target.files[0];

    const flashContainer = document.querySelector("#uploadModal .flash-messages");
    if (flashContainer) flashContainer.remove();

    if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function (e) {
            preview.src = e.target.result;
            preview.style.display = "block";
        };
        reader.readAsDataURL(file);
    } else {
        preview.style.display = "none";
    }
}

// -------------------- FILE INPUT + LABEL --------------------
function handleFileSelect(event, labelId) {
    const fileInput = event.target;
    const label = document.getElementById(labelId);
    const fileName = fileInput.files.length > 0 ? fileInput.files[0].name : 'No file selected';
    label.textContent = fileName;

    previewImageAndOpenModal(event);
}

// -------------------- CONFIRMATION MODAL --------------------
let pendingForm = null;

function openConfirmModal(message, form) {
    pendingForm = form || null;
    document.getElementById("confirmMessage").innerText = message;
    document.getElementById("uploadModal").style.display = "block";

    const buttons = document.getElementById("confirmButtons");
    buttons.style.display = form ? "block" : "none";

    if (!form) {
        setTimeout(closeModal, 2500);
    }
}

function confirmAction() {
    if (pendingForm) {
        pendingForm.submit();
        pendingForm = null;
    }
    closeModal();
}

// -------------------- FLASH MESSAGES --------------------
function initializeFlashMessages() {
    if (window.hasFlashMessage && Array.isArray(window.flashMessages)) {
        const [category, message] = window.flashMessages[0] || [];
        const modalCategories = [
            "profile", "activity", "company_profile", "admin_profile",
            "company_voucher", "company_voucher_deletion"
        ];

        if (modalCategories.includes(category)) {
            const modal = document.getElementById("uploadModal");
            const content = modal.querySelector(".modal-content");

            const oldMessages = content.querySelector(".flash-messages");
            if (oldMessages) oldMessages.remove();

            const container = document.createElement("div");
            container.className = "flash-messages";

            window.flashMessages.forEach(([cat, msg]) => {
                const p = document.createElement("p");
                p.className = `flash ${cat}`;
                p.innerHTML = msg.replace(/\n/g, "<br>");
                container.appendChild(p);
            });

            content.prepend(container);
            const buttons = document.getElementById("confirmButtons");
            if (buttons) buttons.style.display = "none";

            modal.style.display = "block";
        } else {
            openConfirmModal(message || "Success!", null);
        }
    }
}

// -------------------- LOG SECTION TOGGLE --------------------
function toggleLogSection(rowClass, button) {
    const rows = document.querySelectorAll(`.${rowClass}`);
    const isExpanded = localStorage.getItem(rowClass) === 'expanded';

    if (isExpanded) {
        rows.forEach((row, index) => {
            if (index !== 0) row.classList.add('hidden-row');
        });
        button.textContent = `Show All (${rows.length})`;
        localStorage.setItem(rowClass, 'collapsed');
    } else {
        rows.forEach(row => row.classList.remove('hidden-row'));
        button.textContent = "Hide";
        localStorage.setItem(rowClass, 'expanded');
    }
}

function initializeLogSectionToggles() {
    const toggleButtons = document.querySelectorAll('button.toggle-btn[onclick^="toggleLogSection"]');

    toggleButtons.forEach(button => {
        const onclickAttr = button.getAttribute('onclick');
        const rowClassMatch = onclickAttr.match(/'([^']+)'/);

        if (!rowClassMatch) return;

        const rowClass = rowClassMatch[1];
        const rows = document.querySelectorAll(`.${rowClass}`);
        const isExpanded = localStorage.getItem(rowClass) === 'expanded';

        if (isExpanded) {
            rows.forEach(row => row.classList.remove('hidden-row'));
            button.textContent = "Hide";
        } else {
            rows.forEach((row, index) => {
                if (index !== 0) row.classList.add('hidden-row');
            });
            button.textContent = `Show All (${rows.length})`;
        }
    });
}
