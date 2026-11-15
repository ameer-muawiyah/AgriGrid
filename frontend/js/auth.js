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
const regRoleSelect = document.getElementById('regRole');
const farmerFields = document.getElementById('farmerFields');
const buyerFields = document.getElementById('buyerFields');
const regCompanyNameInput = document.getElementById('regCompanyName');
const regContactPhoneInput = document.getElementById('regContactPhone');
const regWarehouseAddressInput = document.getElementById('regWarehouseAddress');
const regWarehouseGpsLatInput = document.getElementById('regWarehouseGpsLat');
const regWarehouseGpsLngInput = document.getElementById('regWarehouseGpsLng');
const regRoleIndicator = document.getElementById('regRoleIndicator');
const regRoleBadgeText = document.getElementById('regRoleBadgeText');
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
      <button type="button" id="switchLinkToRegister" class="toggle-link">
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
      <button type="button" id="switchLinkToLogin" class="toggle-link">
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
    button.classList.toggle('pwd-visible', isPassword);
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
        ? 'pwd-rule valid' 
        : 'pwd-rule';
    }

    // Update complexity indicator
    if (pwdRuleComplexity) {
      pwdRuleComplexity.className = hasComplexity 
        ? 'pwd-rule valid' 
        : 'pwd-rule';
    }
  });
}

/**
 * In-Card Animated Alert Feedback
 */
function showAlert(message, type = 'error') {
  if (!alertBox) return;

  const isSuccess = type === 'success';
  const alertClass = isSuccess ? 'alert-banner alert-success' : 'alert-banner alert-error';

  const iconSvg = isSuccess
    ? `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
         <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
       </svg>`
    : `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
         <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
       </svg>`;

  alertBox.className = alertClass;
  alertBox.innerHTML = `
    <div class="alert-content">
      ${iconSvg}
      <div class="alert-text">${escapeHtml(message)}</div>
    </div>
    <button type="button" class="alert-dismiss" onclick="document.getElementById('alertBox').classList.add('hidden')">
      <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
  document.querySelectorAll('.field input').forEach(input => {
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

        const role = responseData.role || (responseData.user && responseData.user.role) || 'farmer';
        if (role === 'farmer') {
          showAlert('Authentication verified. Loading Farmer Dashboard...', 'success');
          setTimeout(() => { window.location.href = 'dashboard.html'; }, 500);
        } else if (role === 'buyer') {
          showAlert('Authentication verified. Loading Marketplace Catalog...', 'success');
          setTimeout(() => { window.location.href = 'buyer_dashboard.html'; }, 500);
        } else {
          showAlert(`Authenticated as ${role}. Redirecting to console...`, 'success');
          setTimeout(() => { window.location.href = `dashboard.html?role=${encodeURIComponent(role)}`; }, 500);
        }
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
 * Role Switcher in Registration Form
 */
if (regRoleSelect) {
  regRoleSelect.addEventListener('change', () => {
    const role = regRoleSelect.value;
    clearAlert();
    clearInputErrors();
    if (role === 'buyer') {
      if (farmerFields) farmerFields.classList.add('hidden');
      if (buyerFields) buyerFields.classList.remove('hidden');
      if (registerBtnText) registerBtnText.textContent = 'Register as B2B Buyer';
      if (regRoleBadgeText) regRoleBadgeText.textContent = 'Role: B2B Wholesale Buyer';
    } else {
      if (farmerFields) farmerFields.classList.remove('hidden');
      if (buyerFields) buyerFields.classList.add('hidden');
      if (registerBtnText) registerBtnText.textContent = 'Register & Initialize Farm';
      if (regRoleBadgeText) regRoleBadgeText.textContent = 'Role: Verified Farmer (Producer)';
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

    const selectedRole = regRoleSelect ? regRoleSelect.value : 'farmer';
    const username = regUsernameInput.value.trim();
    const password = regPasswordInput.value;

    let payload = {
      username: username,
      password: password,
      role: selectedRole
    };

    if (selectedRole === 'farmer') {
      const farmName = regFarmNameInput ? regFarmNameInput.value.trim() : '';
      if (!farmName) {
        showAlert('Farm / Facility Name is required for farmer accounts.', 'error');
        if (regFarmNameInput) {
          regFarmNameInput.classList.add('has-error');
          regFarmNameInput.focus();
        }
        return;
      }
      payload.farm_name = farmName;
    } else if (selectedRole === 'buyer') {
      const companyName = regCompanyNameInput ? regCompanyNameInput.value.trim() : '';
      const contactPhone = regContactPhoneInput ? regContactPhoneInput.value.trim() : '';
      const warehouseAddress = regWarehouseAddressInput ? regWarehouseAddressInput.value.trim() : '';

      if (!companyName || !contactPhone || !warehouseAddress) {
        showAlert('Company name, phone, and warehouse address are required.', 'error');
        if (!companyName && regCompanyNameInput) regCompanyNameInput.classList.add('has-error');
        if (!contactPhone && regContactPhoneInput) regContactPhoneInput.classList.add('has-error');
        if (!warehouseAddress && regWarehouseAddressInput) regWarehouseAddressInput.classList.add('has-error');
        return;
      }

      payload.company_name = companyName;
      payload.contact_phone = contactPhone;
      payload.warehouse_address = warehouseAddress;

      const latVal = regWarehouseGpsLatInput ? regWarehouseGpsLatInput.value.trim() : '';
      const lngVal = regWarehouseGpsLngInput ? regWarehouseGpsLngInput.value.trim() : '';

      if (latVal !== '') {
        const parsedLat = parseFloat(latVal);
        if (isNaN(parsedLat) || parsedLat < -90 || parsedLat > 90) {
          showAlert('Warehouse GPS Latitude must be between -90 and 90.', 'error');
          if (regWarehouseGpsLatInput) regWarehouseGpsLatInput.classList.add('has-error');
          return;
        }
        payload.warehouse_gps_latitude = parsedLat;
      }

      if (lngVal !== '') {
        const parsedLng = parseFloat(lngVal);
        if (isNaN(parsedLng) || parsedLng < -180 || parsedLng > 180) {
          showAlert('Warehouse GPS Longitude must be between -180 and 180.', 'error');
          if (regWarehouseGpsLngInput) regWarehouseGpsLngInput.classList.add('has-error');
          return;
        }
        payload.warehouse_gps_longitude = parsedLng;
      }
    }

    // Common validations: username
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

    // Common validations: password
    if (!password || password.length < 8) {
      showAlert('Password must be at least 8 characters long.', 'error');
      regPasswordInput.classList.add('has-error');
      regPasswordInput.focus();
      return;
    }

    const loadingLabel = selectedRole === 'buyer' ? 'Registering Buyer...' : 'Registering Farm...';
    const defaultLabel = selectedRole === 'buyer' ? 'Register as B2B Buyer' : 'Register & Initialize Farm';
    setButtonLoading(registerSubmitBtn, registerBtnText, registerSpinner, true, loadingLabel, defaultLabel);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      let responseData = null;
      try {
        responseData = await response.json();
      } catch (err) {
        responseData = null;
      }

      if (response.status === 201 || (response.ok && responseData && responseData.success)) {
        const successMessage = responseData?.message || 'Registration successful. Please log in.';
        registerForm.reset();
        if (farmerFields) farmerFields.classList.remove('hidden');
        if (buyerFields) buyerFields.classList.add('hidden');
        if (regRoleSelect) regRoleSelect.value = 'farmer';
        if (registerBtnText) registerBtnText.textContent = 'Register & Initialize Farm';
        if (regRoleBadgeText) regRoleBadgeText.textContent = 'Role: Verified Farmer (Producer)';
        switchTab('login');
        showAlert(successMessage, 'success');
        if (loginUsernameInput) {
          loginUsernameInput.value = username;
          if (loginPasswordInput) loginPasswordInput.focus();
        }
      } else {
        const errorMsg = extractErrorMessage(responseData, 'Registration failed. Please check your details and try again.');
        showAlert(errorMsg, 'error');
        if (errorMsg.toLowerCase().includes('username')) {
          regUsernameInput.classList.add('has-error');
          regUsernameInput.focus();
        }
      }
    } catch (networkError) {
      console.error('Registration network error:', networkError);
      showAlert(
        `Unable to reach Agri-Grid Gateway at ${API_BASE_URL}. Ensure the backend server is active.`,
        'error'
      );
    } finally {
      setButtonLoading(registerSubmitBtn, registerBtnText, registerSpinner, false, loadingLabel, defaultLabel);
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
