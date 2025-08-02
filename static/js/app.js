/**
 * CourtLens JavaScript Application
 * Handles UI interactions, CAPTCHA management, and form submissions
 */

// Global application object
const CourtLens = {
    config: {
        captchaRefreshInterval: 300000, // 5 minutes
        apiEndpoints: {
            captcha: '/api/captcha',
            caseTypes: '/api/case-types',
            years: '/api/years',
            validateCaptcha: '/api/validate-captcha'
        }
    },
    
    init: function() {
        console.log('CourtLens application initialized');
        this.setupEventListeners();
        this.initializeComponents();
    },
    
    setupEventListeners: function() {
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey) {
                switch(e.key) {
                    case 'Enter':
                        const searchBtn = document.getElementById('searchBtn');
                        if (searchBtn) searchBtn.click();
                        break;
                    case 'r':
                        e.preventDefault();
                        this.refreshCaptcha();
                        break;
                }
            }
        });
        
        // Close alerts automatically
        setTimeout(() => {
            const alerts = document.querySelectorAll('.alert');
            alerts.forEach(alert => {
                if (alert.classList.contains('alert-success')) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            });
        }, 5000);
    },
    
    initializeComponents: function() {
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Initialize popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
        
        // Auto-hide success messages
        this.autoHideAlerts();
        
        // Setup CAPTCHA refresh if element exists
        const refreshBtn = document.getElementById('refresh-captcha');
        if (refreshBtn) {
            this.setupCaptchaHandlers();
        }
    },
    
    setupCaptchaHandlers: function() {
        const refreshBtn = document.getElementById('refresh-captcha');
        const audioBtn = document.getElementById('play-audio');
        const captchaImg = document.getElementById('captcha-image');
        
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshCaptcha());
        }
        
        if (audioBtn) {
            audioBtn.addEventListener('click', () => this.playCaptchaAudio());
        }
        
        // Auto-refresh CAPTCHA periodically
        setInterval(() => {
            if (document.getElementById('captcha-image')) {
                this.refreshCaptcha();
            }
        }, this.config.captchaRefreshInterval);
    },
    
    refreshCaptcha: function() {
        const captchaImg = document.getElementById('captcha-image');
        const captchaInput = document.getElementById('captcha_code');
        const refreshBtn = document.getElementById('refresh-captcha');
        
        if (!captchaImg) return;
        
        // Show loading state
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            refreshBtn.disabled = true;
        }
        
        // Fetch new CAPTCHA
        fetch(this.config.apiEndpoints.captcha + '?' + new Date().getTime())
            .then(response => response.json())
            .then(data => {
                if (data.success && data.captcha) {
                    captchaImg.src = data.captcha.image_url;
                    if (captchaInput) captchaInput.value = '';
                    this.showToast('CAPTCHA refreshed', 'success');
                } else {
                    // Fallback to simple image refresh
                    captchaImg.src = '/api/captcha?' + new Date().getTime();
                }
            })
            .catch(error => {
                console.error('Error refreshing CAPTCHA:', error);
                // Fallback to simple image refresh
                captchaImg.src = '/api/captcha?' + new Date().getTime();
            })
            .finally(() => {
                // Reset button state
                if (refreshBtn) {
                    refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
                    refreshBtn.disabled = false;
                }
            });
    },
    
    playCaptchaAudio: function() {
        const audioBtn = document.getElementById('play-audio');
        const audio = document.getElementById('captcha-audio');
        
        if (audioBtn) {
            audioBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            audioBtn.disabled = true;
        }
        
        fetch(this.config.apiEndpoints.captcha)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.captcha && data.captcha.audio_url) {
                    if (audio) {
                        audio.src = data.captcha.audio_url;
                        audio.play().catch(e => {
                            console.error('Error playing audio:', e);
                            this.showToast('Audio playback failed', 'error');
                        });
                    }
                } else {
                    this.showToast('Audio CAPTCHA not available', 'warning');
                }
            })
            .catch(error => {
                console.error('Error getting audio CAPTCHA:', error);
                this.showToast('Failed to get audio CAPTCHA', 'error');
            })
            .finally(() => {
                if (audioBtn) {
                    audioBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
                    audioBtn.disabled = false;
                }
            });
    },
    
    showToast: function(message, type = 'info', duration = 3000) {
        const toastContainer = this.getOrCreateToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${this.getToastIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();
        
        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toastContainer.removeChild(toast);
        });
    },
    
    getToastIcon: function(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    },
    
    getOrCreateToastContainer: function() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    },
    
    autoHideAlerts: function() {
        const alerts = document.querySelectorAll('.alert-success, .alert-info');
        alerts.forEach(alert => {
            setTimeout(() => {
                if (alert.parentNode) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 5000);
        });
    },
    
    // Form validation utilities
    validateForm: function(formId) {
        const form = document.getElementById(formId);
        if (!form) return false;
        
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
                field.classList.add('is-valid');
            }
        });
        
        return isValid;
    },
    
    // Loading state management
    setLoadingState: function(element, loading = true) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        
        if (!element) return;
        
        if (loading) {
            element.classList.add('btn-loading');
            element.disabled = true;
            element.dataset.originalText = element.textContent;
            element.innerHTML = '<span class="loading-spinner"></span> Loading...';
        } else {
            element.classList.remove('btn-loading');
            element.disabled = false;
            element.textContent = element.dataset.originalText || 'Submit';
        }
    },
    
    // Utility functions
    formatDate: function(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },
    
    copyToClipboard: function(text, successMessage = 'Copied to clipboard!') {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                this.showToast(successMessage, 'success');
            }).catch(err => {
                console.error('Failed to copy: ', err);
                this.fallbackCopyToClipboard(text, successMessage);
            });
        } else {
            this.fallbackCopyToClipboard(text, successMessage);
        }
    },
    
    fallbackCopyToClipboard: function(text, successMessage) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            this.showToast(successMessage, 'success');
        } catch (err) {
            console.error('Fallback copy failed: ', err);
            this.showToast('Copy failed. Please copy manually.', 'error');
        }
        
        document.body.removeChild(textArea);
    },
    
    // Animation utilities
    animateCounter: function(element, target, duration = 2000) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        
        if (!element) return;
        
        const start = parseInt(element.textContent) || 0;
        const increment = (target - start) / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            element.textContent = Math.floor(current);
            
            if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
                element.textContent = target;
                clearInterval(timer);
            }
        }, 16);
    }
};

// Search form specific functionality
const SearchForm = {
    init: function() {
        const form = document.getElementById('searchForm');
        if (!form) return;
        
        this.setupFormValidation(form);
        this.setupLoadingModal();
        this.loadFormOptions();
    },
    
    setupFormValidation: function(form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            if (form.checkValidity()) {
                this.submitForm(form);
            }
            
            form.classList.add('was-validated');
        });
    },
    
    setupLoadingModal: function() {
        this.loadingModal = document.getElementById('loadingModal');
        this.loadingStep = document.getElementById('loadingStep');
        this.progressBar = document.querySelector('.progress-bar');
        
        if (this.loadingModal) {
            this.bsLoadingModal = new bootstrap.Modal(this.loadingModal);
        }
    },
    
    submitForm: function(form) {
        if (!this.bsLoadingModal) {
            form.submit();
            return;
        }
        
        this.bsLoadingModal.show();
        
        const steps = [
            { text: 'Connecting to Delhi High Court...', progress: 20 },
            { text: 'Extracting security tokens...', progress: 40 },
            { text: 'Solving CAPTCHA automatically...', progress: 60 },
            { text: 'Submitting search query...', progress: 80 },
            { text: 'Processing results...', progress: 95 }
        ];
        
        let currentStep = 0;
        const stepInterval = setInterval(() => {
            if (currentStep < steps.length) {
                if (this.loadingStep) {
                    this.loadingStep.textContent = steps[currentStep].text;
                }
                if (this.progressBar) {
                    this.progressBar.style.width = steps[currentStep].progress + '%';
                }
                currentStep++;
            } else {
                clearInterval(stepInterval);
                setTimeout(() => {
                    form.submit();
                }, 1000);
            }
        }, 800);
    },
    
    loadFormOptions: function() {
        // Load case types
        fetch(CourtLens.config.apiEndpoints.caseTypes)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.populateSelect('case_type', data.case_types);
                }
            })
            .catch(error => console.error('Error loading case types:', error));
        
        // Load years
        fetch(CourtLens.config.apiEndpoints.years)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.populateSelect('case_year', data.years);
                }
            })
            .catch(error => console.error('Error loading years:', error));
    },
    
    populateSelect: function(selectId, options) {
        const select = document.getElementById(selectId);
        if (!select || !options) return;
        
        // Clear existing options except the first one
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }
        
        // Add new options
        Object.entries(options).forEach(([display, value]) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = display;
            select.appendChild(option);
        });
    },
    
    resetForm: function() {
        const form = document.getElementById('searchForm');
        if (form) {
            form.reset();
            form.classList.remove('was-validated');
            CourtLens.refreshCaptcha();
        }
    }
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    CourtLens.init();
    SearchForm.init();
    
    // Add fade-in animation to main content
    const main = document.querySelector('main');
    if (main) {
        main.classList.add('fade-in');
    }
});

// Global utility functions for backward compatibility
window.resetForm = SearchForm.resetForm.bind(SearchForm);
window.copyToClipboard = function(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        CourtLens.copyToClipboard(element.value || element.textContent);
    }
};

// Export for use in other scripts
window.CourtLens = CourtLens;
window.SearchForm = SearchForm;