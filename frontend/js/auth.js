/**
 * Agri-Grid Authentication & Session Gateway (Increment 1)
 * Handles Farmer Registration, Authentication, JWT Token Persistence, and UI State Transitions.
 */

// Base API URL configuration
const API_BASE_URL = 'http://127.0.0.1:5000/api';

// DOM Element Selectors
const tabLoginBtn = document.getElementById('tabLoginBtn');
const tabRegisterBtn = document.getElementById('tabRegisterBtn');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const alertBox = document.getElementById('alertBox');

const authPortalHeading = document.getElementById('authPortalHeading');
const authPortalSubheading = document.getElementById('authPortalSubheading');
const bottomTogglePrompt = document.getElementById('bottomTogglePrompt');
const switchLinkToRegister = document.getElementById('switchLinkToRegister');

// Login Elements
const loginUsernameInput = document.getElementById('loginUsername');
const loginPasswordInput = document.getElementById('loginPassword');
const loginSubmitBtn = document.getElementById('loginSubmitBtn');
const loginBtnText = document.getElementById('loginBtnText');
const loginSpinner = document.getElementById('loginSpinner');
const toggleLoginPasswordBtn = document.getElementById('toggleLoginPasswordBtn');

// Register Elements
const regFarmNameInput = document.getElementById('regFarmName');
const regUsernameInput = document.getElementById('regUsername');
const regPasswordInput = document.getElementById('regPassword');
const registerSubmitBtn = document.getElementById('registerSubmitBtn');
const registerBtnText = document.getElementById('registerBtnText');
const registerSpinner = document.getElementById('registerSpinner');
const toggleRegPasswordBtn = document.getElementById('toggleRegPasswordBtn');
const pwdRuleLength = document.getElementById('pwdRuleLength');
const pwdRuleComplexity = document.getElementById('pwdRuleComplexity');

/**
 * Tab Switching Logic
 */
function switchTab(target) {
  clearAlert();
  clearInputErrors();

  if (target === 'login') {
    // Tab pill styling
    tabLoginBtn.classList.add('active');
    tabLoginBtn.setAttribute('aria-selected', 'true');
    tabRegisterBtn.classList.remove('active');
    tabRegisterBtn.setAttribute('aria-selected', 'false');

    // Display Form
    loginForm.classList.remove('hidden');
    registerForm.classList.add('hidden');

    // Text headings
    authPortalHeading.textContent = 'Welcome to Agri-Grid';
    authPortalSubheading.textContent = 'Access your decentralized farm telemetry and crop ledger';

    // Bottom toggle prompt
    bottomTogglePrompt.innerHTML = `Don't have a farmer account yet? 
      <button type="button" id="switchLinkToRegister" class="text-emerald font-semibold hover:underline ml-1">
        Register as Farmer
      </button>`;
    
    const newSwitchBtn = document.getElementById('switchLinkToRegister');
    if (newSwitchBtn) {
      newSwitchBtn.addEventListener('click', () => switchTab('register'));
    }

    loginUsernameInput.focus();
  } else {
    // Tab pill styling
    tabRegisterBtn.classList.add('active');
    tabRegisterBtn.setAttribute('aria-selected', 'true');
    tabLoginBtn.classList.remove('active');
    tabLoginBtn.setAttribute('aria-selected', 'false');

    // Display Form
    registerForm.classList.remove('hidden');
    loginForm.classList.add('hidden');

    // Text headings
    authPortalHeading.textContent = 'Join Agri-Grid Network';
    authPortalSubheading.textContent = 'Register your farm node to start logging crops and telemetry';

    // Bottom toggle prompt
    bottomTogglePrompt.innerHTML = `Already registered on Agri-Grid? 
      <button type="button" id="switchLinkToLogin" class="text-emerald font-semibold hover:underline ml-1">
        Sign in here
      </button>`;
    
    const switchLinkToLogin = document.getElementById('switchLinkToLogin');
    if (switchLinkToLogin) {
      switchLinkToLogin.addEventListener('click', () => switchTab('login'));
    }

    regFarmNameInput.focus();
  }
}

// Event Listeners for Tab Switching
if (tabLoginBtn) {
  tabLoginBtn.addEventListener('click', () => switchTab('login'));
}

if (tabRegisterBtn) {
  tabRegisterBtn.addEventListener('click', () => switchTab('register'));
}

if (switchLinkToRegister) {
  switchLinkToRegister.addEventListener('click', () => switchTab('register'));
}

/**
 * Toggle Password Visibility Helper
 */
function setupPasswordToggle(button, input) {
  if (!button || !input) return;
  button.addEventListener('click', () => {
    const isPassword = input.getAttribute('type') === 'password';
    input.setAttribute('type', isPassword ? 'text' : 'password');
    button.classList.toggle('text-emerald', isPassword);
  });
}

setupPasswordToggle(toggleLoginPasswordBtn, loginPasswordInput);
setupPasswordToggle(toggleRegPasswordBtn, regPasswordInput);

/**
 * Real-time Password Validation Hints on Registration
 */
if (regPasswordInput) {
  regPasswordInput.addEventListener('input', () => {
    const val = regPasswordInput.value;
    const hasMinLength = val.length >= 8;
    const hasComplexity = /[A-Z]/.test(val) && /[a-z]/.test(val) && /[0-9]/.test(val);

    // Update length indicator
    if (pwdRuleLength) {
      pwdRuleLength.className = hasMinLength 
        ? 'inline-flex items-center text-emerald font-medium' 
        : 'inline-flex items-center text-gray-500';
    }

    // Update complexity indicator
    if (pwdRuleComplexity) {
      pwdRuleComplexity.className = hasComplexity 
        ? 'inline-flex items-center text-emerald font-medium' 
        : 'inline-flex items-center text-gray-500';
    }
  });
}

/**
 * In-Card Animated Alert Feedback
 */
function showAlert(message, type = 'error') {
  if (!alertBox) return;

  const isSuccess = type === 'success';
  const bgColor = isSuccess ? 'bg-mint/80 border-emerald/40 text-emerald-950' : 'bg-red-50 border-red-200 text-red-900';
  const iconColor = isSuccess ? 'text-emerald-700' : 'text-red-600';

  const iconSvg = isSuccess
    ? `<svg class="w-5 h-5 ${iconColor} flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
         <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
       </svg>`
    : `<svg class="w-5 h-5 ${iconColor} flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
         <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
       </svg>`;

  alertBox.className = `alert-banner p-3.5 rounded-lg border text-xs sm:text-sm flex items-start justify-between shadow-sm ${bgColor} mb-5`;
  alertBox.innerHTML = `
    <div class="flex items-start space-x-2.5">
      ${iconSvg}
      <div class="font-medium leading-relaxed">${escapeHtml(message)}</div>
    </div>
    <button type="button" class="ml-2 text-gray-400 hover:text-gray-700 focus:outline-none" onclick="document.getElementById('alertBox').classList.add('hidden')">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
      </svg>
    </button>
  `;
  alertBox.classList.remove('hidden');
}

function clearAlert() {
  if (alertBox) {
    alertBox.classList.add('hidden');
    alertBox.innerHTML = '';
  }
}

function clearInputErrors() {
  document.querySelectorAll('.auth-input').forEach(input => {
    input.classList.remove('has-error');
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Standard Error Envelope Parser
 * Robust extraction of error message from backend envelope or network error
 */
function extractErrorMessage(data, fallback = 'An unexpected response was received from the server.') {
  if (!data) return fallback;
  if (typeof data.error === 'string') return data.error;
  if (data.error && typeof data.error.message === 'string') return data.error.message;
  if (typeof data.message === 'string') return data.message;
  return fallback;
}

/**
 * Button Loading State Helpers
 */
function setButtonLoading(button, textSpan, spinner, isLoading, loadingText, defaultText) {
  if (!button) return;
  button.disabled = isLoading;
  if (isLoading) {
    if (textSpan) textSpan.textContent = loadingText;
    if (spinner) spinner.classList.remove('hidden');
  } else {
    if (textSpan) textSpan.textContent = defaultText;
    if (spinner) spinner.classList.add('hidden');
  }
}

/**
 * =========================================================================
 * Form Submission: LOGIN (POST /api/auth/login)
 * =========================================================================
 */
if (loginForm) {
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAlert();
    clearInputErrors();

    const username = loginUsernameInput.value.trim();
    const password = loginPasswordInput.value;

    // Client-side quick checks
    if (!username) {
      showAlert('Please enter your username.', 'error');
      loginUsernameInput.classList.add('has-error');
      loginUsernameInput.focus();
      return;
    }

    if (!password) {
      showAlert('Please enter your password.', 'error');
      loginPasswordInput.classList.add('has-error');
      loginPasswordInput.focus();
      return;
    }

    setButtonLoading(loginSubmitBtn, loginBtnText, loginSpinner, true, 'Authenticating...', 'Sign In to Farm Node');

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: username,
          password: password
        })
      });

      let responseData = null;
      try {
        responseData = await response.json();
      } catch (err) {
        responseData = null;
      }

      if (response.ok && responseData && responseData.token) {
        // Contract Success Rule:
        // Store token in sessionStorage under key 'agrigrid_token'
        // Store user in sessionStorage under key 'agrigrid_user'
        sessionStorage.setItem('agrigrid_token', responseData.token);
        if (responseData.user) {
          sessionStorage.setItem('agrigrid_user', JSON.stringify(responseData.user));
        }

        showAlert('Authentication verified. Loading Farmer Dashboard...', 'success');

        // Redirect to dashboard.html
        setTimeout(() => {
          window.location.href = 'dashboard.html';
        }, 500);
      } else {
        const errorMsg = extractErrorMessage(responseData, 'Authentication failed. Please verify your credentials.');
        showAlert(errorMsg, 'error');
        loginPasswordInput.classList.add('has-error');
        loginPasswordInput.focus();
      }
    } catch (networkError) {
      console.error('Login network error:', networkError);
      showAlert(
        `Unable to reach Agri-Grid Gateway at ${API_BASE_URL}. Ensure the backend server is active.`,
        'error'
      );
    } finally {
      setButtonLoading(loginSubmitBtn, loginBtnText, loginSpinner, false, 'Authenticating...', 'Sign In to Farm Node');
    }
  });
}

/**
 * =========================================================================
 * Form Submission: REGISTRATION (POST /api/auth/register)
 * =========================================================================
 */
if (registerForm) {
  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAlert();
    clearInputErrors();

    const farmName = regFarmNameInput.value.trim();
    const username = regUsernameInput.value.trim();
    const password = regPasswordInput.value;

    // 1. Validate farm_name
    if (!farmName) {
      showAlert('Farm / Facility Name is required for farmer accounts.', 'error');
      regFarmNameInput.classList.add('has-error');
      regFarmNameInput.focus();
      return;
    }

    // 2. Validate username
    if (!username) {
      showAlert('Username is required.', 'error');
      regUsernameInput.classList.add('has-error');
      regUsernameInput.focus();
      return;
    }

    if (username.length < 3 || username.length > 50) {
      showAlert('Username must be between 3 and 50 characters.', 'error');
      regUsernameInput.classList.add('has-error');
      regUsernameInput.focus();
      return;
    }

    // 3. Validate password (Must be at least 8 characters)
    if (!password || password.length < 8) {
      showAlert('Password must be at least 8 characters long.', 'error');
      regPasswordInput.classList.add('has-error');
      regPasswordInput.focus();
      return;
    }

    setButtonLoading(registerSubmitBtn, registerBtnText, registerSpinner, true, 'Registering Farm...', 'Register & Initialize Farm');

    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: username,
          password: password,
          role: 'farmer',
          farm_name: farmName
        })
      });

      let responseData = null;
      try {
        responseData = await response.json();
      } catch (err) {
        responseData = null;
      }

      if (response.status === 201 || (response.ok && responseData && responseData.success)) {
        const successMessage = responseData?.message || 'Registration successful. Please log in.';
        
        // Clear registration form
        registerForm.reset();

        // Switch to login tab and show green success message
        switchTab('login');
        showAlert(successMessage, 'success');

        // Prefill login username
        if (loginUsernameInput) {
          loginUsernameInput.value = username;
          if (loginPasswordInput) {
            loginPasswordInput.focus();
          }
        }
      } else {
        const errorMsg = extractErrorMessage(responseData, 'Registration failed. Please check your details and try again.');
        showAlert(errorMsg, 'error');
      }
    } catch (networkError) {
      console.error('Registration network error:', networkError);
      showAlert(
        `Unable to reach Agri-Grid Gateway at ${API_BASE_URL}. Ensure the backend server is active.`,
        'error'
      );
    } finally {
      setButtonLoading(registerSubmitBtn, registerBtnText, registerSpinner, false, 'Registering Farm...', 'Register & Initialize Farm');
    }
  });
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
  // Check if user is already logged in with valid token
  const existingToken = sessionStorage.getItem('agrigrid_token');
  if (existingToken) {
    // Session token detected notice (soft prompt)
    const existingUser = sessionStorage.getItem('agrigrid_user');
    let username = '';
    if (existingUser) {
      try {
        username = JSON.parse(existingUser).username;
      } catch (e) {}
    }
    if (username && loginUsernameInput) {
      loginUsernameInput.value = username;
    }
  }
});
