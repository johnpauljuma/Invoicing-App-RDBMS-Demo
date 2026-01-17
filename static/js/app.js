// static/js/app.js
console.log('Invoicing App JavaScript loaded');

// Global app state
window.AppState = {
    currentUser: null,
    customers: [],
    invoices: []
};

// Initialize tooltips
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Format currency
function formatCurrency(amount, currency = 'KES') {
    return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-KE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Calculate days until due
function getDaysUntilDue(dueDate) {
    const today = new Date();
    const due = new Date(dueDate);
    const diffTime = due - today;
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('main .container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                const bsAlert = new bootstrap.Alert(alertDiv);
                bsAlert.close();
            }
        }, 5000);
    }
}

// Handle form submissions with AJAX
function initAjaxForms() {
    document.addEventListener('submit', async function(e) {
        const form = e.target;
        
        // Only handle forms with data-ajax attribute
        if (!form.hasAttribute('data-ajax')) return;
        
        e.preventDefault();
        
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn ? submitBtn.innerHTML : '';
        
        // Show loading
        if (submitBtn) {
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Processing...';
            submitBtn.disabled = true;
        }
        
        try {
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            const response = await fetch(form.action, {
                method: form.method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Handle redirect
                if (form.dataset.redirect) {
                    window.location.href = form.dataset.redirect;
                } else if (result.redirect) {
                    window.location.href = result.redirect;
                } else if (form.dataset.reload) {
                    location.reload();
                } else {
                    showAlert(result.message || 'Operation successful', 'success');
                    form.reset();
                }
            } else {
                showAlert(result.error || 'Operation failed', 'danger');
            }
        } catch (error) {
            showAlert('Network error. Please try again.', 'danger');
            console.error('Form submission error:', error);
        } finally {
            // Reset button state
            if (submitBtn) {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        }
    });
}

// Handle logout
function initLogout() {
    const logoutLinks = document.querySelectorAll('[data-logout]');
    logoutLinks.forEach(link => {
        link.addEventListener('click', async function(e) {
            e.preventDefault();
            
            try {
                const response = await fetch('/logout');
                if (response.ok) {
                    window.location.href = '/login';
                }
            } catch (error) {
                console.error('Logout error:', error);
            }
        });
    });
}

// Load customers for dropdowns
async function loadCustomers() {
    try {
        const response = await fetch('/api/customers');
        const data = await response.json();
        
        if (data.data) {
            AppState.customers = data.data;
            
            // Update any customer dropdowns
            document.querySelectorAll('[data-customer-dropdown]').forEach(select => {
                const currentValue = select.value;
                select.innerHTML = '<option value="">Select Customer</option>';
                
                AppState.customers.forEach(customer => {
                    const option = document.createElement('option');
                    option.value = customer.id;
                    option.textContent = customer.name;
                    option.selected = customer.id == currentValue;
                    select.appendChild(option);
                });
            });
        }
    } catch (error) {
        console.error('Error loading customers:', error);
    }
}

// Generate PDF for invoice
async function generateInvoicePDF(invoiceId) {
    try {
        const response = await fetch(`/api/invoices/${invoiceId}/pdf`);
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `invoice-${invoiceId}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }
    } catch (error) {
        console.error('Error generating PDF:', error);
        showAlert('Failed to generate PDF', 'warning');
    }
}

// Send invoice via email
async function sendInvoiceEmail(invoiceId, email) {
    if (!email) {
        email = prompt('Enter customer email address:');
        if (!email) return;
    }
    
    try {
        const response = await fetch(`/api/invoices/${invoiceId}/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ email: email })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('Invoice sent successfully!', 'success');
        } else {
            showAlert(result.error || 'Failed to send invoice', 'danger');
        }
    } catch (error) {
        console.error('Error sending email:', error);
        showAlert('Network error. Please try again.', 'danger');
    }
}

// Update invoice status
async function updateInvoiceStatus(invoiceId, status) {
    try {
        const response = await fetch(`/api/invoices/${invoiceId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ status: status })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert(`Invoice status updated to ${status}`, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert(result.error || 'Failed to update status', 'danger');
        }
    } catch (error) {
        console.error('Error updating status:', error);
        showAlert('Network error. Please try again.', 'danger');
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Invoicing App...');
    
    // Initialize Bootstrap components
    initTooltips();
    
    // Initialize form handlers
    initAjaxForms();
    
    // Initialize logout
    initLogout();
    
    // Load customers if needed
    if (document.querySelector('[data-customer-dropdown]')) {
        loadCustomers();
    }
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + N for new invoice
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            const newInvoiceBtn = document.querySelector('[data-new-invoice]');
            if (newInvoiceBtn) newInvoiceBtn.click();
        }
        
        // Ctrl/Cmd + F for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="search"]');
            if (searchInput) searchInput.focus();
        }
    });
    
    // Update copyright year
    const yearSpan = document.querySelector('[data-current-year]');
    if (yearSpan) {
        yearSpan.textContent = new Date().getFullYear();
    }
    
    console.log('Invoicing App initialized successfully');
});

// Export functions for use in templates
window.invoicingApp = {
    formatCurrency,
    formatDate,
    getDaysUntilDue,
    showAlert,
    generateInvoicePDF,
    sendInvoiceEmail,
    updateInvoiceStatus,
    loadCustomers
};