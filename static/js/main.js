// Main JavaScript file for AI Chatbot Platform

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeTooltips();
    initializeAnimations();
    initializeFormValidation();
    
    // Auto-hide flash messages after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize animations
function initializeAnimations() {
    // Fade in cards on page load
    const cards = document.querySelectorAll('.card');
    cards.forEach(function(card, index) {
        setTimeout(function() {
            card.classList.add('fade-in');
        }, index * 100);
    });
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// Utility functions
const Utils = {
    // Show loading spinner
    showLoading: function(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Yuklanmoqda...</span></div></div>';
        }
    },
    
    // Hide loading spinner
    hideLoading: function(elementId, content) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = content || '';
        }
    },
    
    // Show toast notification
    showToast: function(message, type = 'info') {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = toastContainer.lastElementChild;
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    },
    
    // Format date
    formatDate: function(dateString) {
        const options = { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return new Date(dateString).toLocaleDateString('uz-UZ', options);
    },
    
    // Copy text to clipboard
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(function() {
            Utils.showToast('Matn nusxalandi!', 'success');
        }).catch(function() {
            Utils.showToast('Nusxalashda xatolik!', 'danger');
        });
    }
};

// Chat functionality (if on chat page)
if (window.location.pathname === '/chat') {
    // Chat will be handled by the chat.html template script
    console.log('Chat page loaded');
}

// Admin dashboard functionality
if (window.location.pathname.includes('/admin')) {
    document.addEventListener('DOMContentLoaded', function() {
        // Add confirmation dialogs for admin actions
        const deleteButtons = document.querySelectorAll('[data-action="delete"]');
        deleteButtons.forEach(function(button) {
            button.addEventListener('click', function(e) {
                if (!confirm('Bu amalni bajarishga ishonchingiz komilmi?')) {
                    e.preventDefault();
                }
            });
        });
        
        // Add success messages for admin actions
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('success')) {
            Utils.showToast('Amal muvaffaqiyatli bajarildi!', 'success');
        }
    });
}

// Knowledge base functionality
if (window.location.pathname === '/knowledge') {
    document.addEventListener('DOMContentLoaded', function() {
        const fileInput = document.getElementById('file');
        const textArea = document.getElementById('text');
        
        // Clear text when file is selected
        if (fileInput) {
            fileInput.addEventListener('change', function() {
                if (this.files.length > 0) {
                    textArea.value = '';
                }
            });
        }
        
        // Clear file when text is entered
        if (textArea) {
            textArea.addEventListener('input', function() {
                if (this.value.trim()) {
                    fileInput.value = '';
                }
            });
        }
    });
}

// Language switching
function switchLanguage(lang) {
    window.location.href = `/set_language/${lang}`;
}

// Global error handler
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
    Utils.showToast('Xatolik yuz berdi. Sahifani yangilang.', 'danger');
});

// Service worker registration (for future PWA features)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Future implementation for offline support
    });
}