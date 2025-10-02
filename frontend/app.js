#!/usr/bin/env javascript
/**
 * AWS Cost SaaS - Frontend Application
 * Complete turnkey SaaS frontend with robust error handling
 */

// Configuration
const CONFIG = {
    API_URL: 'http://localhost:8000',
    STRIPE_PUBLISHABLE_KEY: 'pk_test_your_stripe_publishable_key_here'
};

// Initialize Stripe
const stripe = Stripe(CONFIG.STRIPE_PUBLISHABLE_KEY);

// Global state
let currentUser = null;
let authToken = localStorage.getItem('auth_token');

// DOM Elements
const elements = {
    // Navigation
    userMenu: document.getElementById('userMenu'),
    authButtons: document.getElementById('authButtons'),
    logoutBtn: document.getElementById('logoutBtn'),
    loginBtn: document.getElementById('loginBtn'),
    registerBtn: document.getElementById('registerBtn'),
    
    // Sections
    heroSection: document.getElementById('heroSection'),
    dashboardSection: document.getElementById('dashboardSection'),
    pricingSection: document.getElementById('pricingSection'),
    resultsSection: document.getElementById('resultsSection'),
    
    // Forms
    analysisForm: document.getElementById('analysisForm'),
    uploadForm: document.getElementById('uploadForm'),
    loginForm: document.getElementById('loginForm'),
    registerForm: document.getElementById('registerForm'),
    
    // Modals
    loginModal: document.getElementById('loginModal'),
    registerModal: document.getElementById('registerModal'),
    
    // Other
    loadingOverlay: document.getElementById('loadingOverlay'),
    toastContainer: document.getElementById('toastContainer'),
    resultsContent: document.getElementById('resultsContent')
};

// Utility Functions
const utils = {
    showLoading() {
        elements.loadingOverlay.classList.remove('hidden');
    },
    
    hideLoading() {
        elements.loadingOverlay.classList.add('hidden');
    },
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        const bgColor = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        }[type] || 'bg-blue-500';
        
        toast.className = `${bgColor} text-white px-6 py-3 rounded-lg shadow-lg fade-in`;
        toast.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        elements.toastContainer.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    },
    
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },
    
    async apiRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...(authToken && { 'Authorization': `Bearer ${authToken}` })
            }
        };
        
        const response = await fetch(`${CONFIG.API_URL}${url}`, {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            const errorMessage = data?.detail || data?.message || `HTTP ${response.status}`;
            throw new Error(errorMessage);
        }
        
        return data;
    }
};

// Authentication Functions
const auth = {
    async login(email, password) {
        try {
            const response = await utils.apiRequest('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email, password })
            });
            
            if (response?.token) {
                authToken = response.token;
                localStorage.setItem('auth_token', authToken);
                currentUser = response;
                this.updateUI();
                utils.showToast('Login successful!', 'success');
                return true;
            }
            throw new Error('Invalid response format');
        } catch (error) {
            const errorMessage = error?.message || 'Login failed';
            utils.showToast(errorMessage, 'error');
            throw error;
        }
    },
    
    async register(name, email, password) {
        try {
            const response = await utils.apiRequest('/auth/register', {
                method: 'POST',
                body: JSON.stringify({ name, email, password })
            });
            
            if (response?.token) {
                authToken = response.token;
                localStorage.setItem('auth_token', authToken);
                currentUser = response;
                this.updateUI();
                utils.showToast('Registration successful!', 'success');
                return true;
            }
            throw new Error('Invalid response format');
        } catch (error) {
            const errorMessage = error?.message || 'Registration failed';
            utils.showToast(errorMessage, 'error');
            throw error;
        }
    },
    
    logout() {
        authToken = null;
        currentUser = null;
        localStorage.removeItem('auth_token');
        this.updateUI();
        utils.showToast('Logged out successfully', 'info');
    },
    
    updateUI() {
        if (currentUser && authToken) {
            elements.userMenu.classList.remove('hidden');
            elements.authButtons.classList.add('hidden');
            elements.heroSection.classList.add('hidden');
            elements.dashboardSection.classList.remove('hidden');
            
            // Update user profile
            const userPlan = document.getElementById('userPlan');
            const memberSince = document.getElementById('memberSince');
            
            if (userPlan) userPlan.textContent = currentUser.subscription_plan || 'Starter';
            if (memberSince) memberSince.textContent = new Date().toLocaleDateString();
        } else {
            elements.userMenu.classList.add('hidden');
            elements.authButtons.classList.remove('hidden');
            elements.heroSection.classList.remove('hidden');
            elements.dashboardSection.classList.add('hidden');
            elements.pricingSection.classList.add('hidden');
        }
    }
};

// Cost Analysis Functions
const costAnalysis = {
    async analyzeCosts(monthlyBill, services, region, workloadType) {
        try {
            utils.showLoading();
            
            const response = await utils.apiRequest('/api/analyze', {
                method: 'POST',
                body: JSON.stringify({
                    monthly_bill: parseFloat(monthlyBill),
                    services: services.split(',').map(s => s.trim()),
                    region,
                    workload_type: workloadType
                })
            });
            
            this.displayResults(response);
            utils.showToast('Analysis completed successfully!', 'success');
            
        } catch (error) {
            const errorMessage = error?.message || 'Analysis failed';
            utils.showToast(errorMessage, 'error');
            console.error('Analysis error:', error);
        } finally {
            utils.hideLoading();
        }
    },
    
    async uploadFile(file) {
        try {
            utils.showLoading();
            
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${CONFIG.API_URL}/api/upload-billing`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                },
                body: formData
            });
            
            const data = await response.json();
            console.log('Upload response:', data); // 🔍 Debugging aid
            
            if (data?.analysis) {
                this.displayResults(data.analysis);
                utils.showToast('File uploaded and analyzed successfully!', 'success');
            } else {
                const errorMessage = data?.detail || data?.message || 'Upload failed';
                utils.showToast(errorMessage, 'error');
            }
            
        } catch (error) {
            const errorMessage = error?.message || 'File upload failed';
            utils.showToast(errorMessage, 'error');
            console.error('Upload error:', error);
        } finally {
            utils.hideLoading();
        }
    },
    
    displayResults(analysis) {
        if (!analysis) {
            utils.showToast('No analysis data received', 'error');
            return;
        }
        
        const {
            current_bill = 0,
            potential_savings = 0,
            optimized_bill = 0,
            wasted_spend = 0,
            recommendations = [],
            service_breakdown = {},
            confidence_score = 0
        } = analysis;
        
        const html = `
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <div class="bg-blue-50 p-4 rounded-lg">
                    <div class="text-2xl font-bold text-blue-600">${utils.formatCurrency(current_bill)}</div>
                    <div class="text-sm text-gray-600">Current Monthly Bill</div>
                </div>
                <div class="bg-green-50 p-4 rounded-lg">
                    <div class="text-2xl font-bold text-green-600">${utils.formatCurrency(potential_savings)}</div>
                    <div class="text-sm text-gray-600">Potential Savings</div>
                </div>
                <div class="bg-purple-50 p-4 rounded-lg">
                    <div class="text-2xl font-bold text-purple-600">${utils.formatCurrency(optimized_bill)}</div>
                    <div class="text-sm text-gray-600">Optimized Bill</div>
                </div>
                <div class="bg-red-50 p-4 rounded-lg">
                    <div class="text-2xl font-bold text-red-600">${utils.formatCurrency(wasted_spend)}</div>
                    <div class="text-sm text-gray-600">Wasted Spend</div>
                </div>
            </div>
            
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-4">Service Breakdown</h3>
                    <div class="space-y-2">
                        ${Object.entries(service_breakdown).map(([service, cost]) => `
                            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                                <span class="font-medium">${service}</span>
                                <span class="text-blue-600 font-semibold">${utils.formatCurrency(cost)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-4">Optimization Recommendations</h3>
                    <div class="space-y-3">
                        ${recommendations.map(rec => `
                            <div class="p-4 border border-gray-200 rounded-lg">
                                <div class="flex justify-between items-start mb-2">
                                    <h4 class="font-semibold text-gray-900">${rec.title || 'Recommendation'}</h4>
                                    <span class="px-2 py-1 text-xs rounded-full ${
                                        rec.priority === 'High' ? 'bg-red-100 text-red-800' :
                                        rec.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                                        'bg-green-100 text-green-800'
                                    }">${rec.priority || 'Medium'}</span>
                                </div>
                                <p class="text-gray-600 text-sm mb-2">${rec.description || 'No description available'}</p>
                                <div class="flex justify-between items-center">
                                    <span class="text-green-600 font-semibold">${utils.formatCurrency(rec.potential_savings || 0)} savings</span>
                                    <span class="text-xs text-gray-500">${rec.implementation_effort || 'Medium'} effort</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
            
            <div class="mt-6 p-4 bg-blue-50 rounded-lg">
                <div class="flex items-center">
                    <i class="fas fa-info-circle text-blue-600 mr-2"></i>
                    <span class="text-blue-800">Confidence Score: ${Math.round((confidence_score || 0) * 100)}%</span>
                </div>
            </div>
        `;
        
        elements.resultsContent.innerHTML = html;
        elements.resultsSection.classList.remove('hidden');
        elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
};

// Payment Functions
const payment = {
    async createPaymentIntent(planId) {
        try {
            utils.showLoading();
            
            const response = await utils.apiRequest('/api/subscription/create-payment-intent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `plan_id=${planId}`
            });
            
            if (response?.client_secret) {
                await this.confirmPayment(response.client_secret);
            } else {
                throw new Error('No client secret received');
            }
            
        } catch (error) {
            const errorMessage = error?.message || 'Payment setup failed';
            utils.showToast(errorMessage, 'error');
        } finally {
            utils.hideLoading();
        }
    },
    
    async confirmPayment(clientSecret) {
        try {
            const { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret);
            
            if (error) {
                utils.showToast(error.message || 'Payment failed', 'error');
            } else if (paymentIntent?.status === 'succeeded') {
                utils.showToast('Payment successful! Welcome to your new plan!', 'success');
                // Refresh user data
                await this.refreshUserData();
            }
        } catch (error) {
            utils.showToast('Payment confirmation failed', 'error');
        }
    },
    
    async refreshUserData() {
        try {
            const response = await utils.apiRequest('/api/user/profile');
            if (response) {
                currentUser = { ...currentUser, ...response };
                auth.updateUI();
            }
        } catch (error) {
            console.error('Failed to refresh user data:', error);
        }
    }
};

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize app
    if (authToken) {
        // Verify token and load user data
        auth.updateUI();
    }
    
    // Navigation events
    elements.loginBtn?.addEventListener('click', () => {
        elements.loginModal.classList.remove('hidden');
    });
    
    elements.registerBtn?.addEventListener('click', () => {
        elements.registerModal.classList.remove('hidden');
    });
    
    elements.logoutBtn?.addEventListener('click', () => {
        auth.logout();
    });
    
    elements.getStartedBtn?.addEventListener('click', () => {
        if (currentUser) {
            elements.dashboardSection.classList.remove('hidden');
        } else {
            elements.registerModal.classList.remove('hidden');
        }
    });
    
    // Modal events
    elements.closeLoginModal?.addEventListener('click', () => {
        elements.loginModal.classList.add('hidden');
    });
    
    elements.closeRegisterModal?.addEventListener('click', () => {
        elements.registerModal.classList.add('hidden');
    });
    
    elements.showRegisterModal?.addEventListener('click', () => {
        elements.loginModal.classList.add('hidden');
        elements.registerModal.classList.remove('hidden');
    });
    
    elements.showLoginModal?.addEventListener('click', () => {
        elements.registerModal.classList.add('hidden');
        elements.loginModal.classList.remove('hidden');
    });
    
    // Form submissions
    elements.loginForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        
        try {
            await auth.login(email, password);
            elements.loginModal.classList.add('hidden');
            elements.loginForm.reset();
        } catch (error) {
            // Error already handled in auth.login
        }
    });
    
    elements.registerForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('registerName').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        
        try {
            await auth.register(name, email, password);
            elements.registerModal.classList.add('hidden');
            elements.registerForm.reset();
        } catch (error) {
            // Error already handled in auth.register
        }
    });
    
    elements.analysisForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const monthlyBill = document.getElementById('monthlyBill').value;
        const services = document.getElementById('services').value;
        const region = document.getElementById('region').value;
        const workloadType = document.getElementById('workloadType').value;
        
        if (!monthlyBill || !services) {
            utils.showToast('Please fill in all required fields', 'warning');
            return;
        }
        
        await costAnalysis.analyzeCosts(monthlyBill, services, region, workloadType);
    });
    
    elements.uploadForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];
        
        if (!file) {
            utils.showToast('Please select a file', 'warning');
            return;
        }
        
        await costAnalysis.uploadFile(file);
    });
    
    // Plan selection
    document.querySelectorAll('.plan-select').forEach(button => {
        button.addEventListener('click', (e) => {
            const planId = e.target.dataset.plan;
            if (currentUser) {
                payment.createPaymentIntent(planId);
            } else {
                utils.showToast('Please login to select a plan', 'warning');
                elements.loginModal.classList.remove('hidden');
            }
        });
    });
    
    elements.upgradeBtn?.addEventListener('click', () => {
        elements.pricingSection.classList.remove('hidden');
        elements.pricingSection.scrollIntoView({ behavior: 'smooth' });
    });
    
    // Close modals on outside click
    [elements.loginModal, elements.registerModal].forEach(modal => {
        modal?.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        });
    });
});

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { auth, costAnalysis, payment, utils };
}
