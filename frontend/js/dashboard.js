/**
 * Agri-Grid Farmer Dashboard Controller (Increment 1)
 * Manages Auth Session Guard, Active Crop CRUD Operations, Metrics, and Zero-Trust Request Pipeline.
 */

const API_BASE_URL = 'http://127.0.0.1:5000/api';

// =========================================================================
// 1. AUTH GUARD & SESSION VALIDATION
// =========================================================================
const token = sessionStorage.getItem('agrigrid_token');
if (!token) {
  window.location.replace('index.html');
}

// User Profile Parsing
let currentUser = null;
try {
  const userJson = sessionStorage.getItem('agrigrid_user');
  if (userJson) {
    currentUser = JSON.parse(userJson);
  }
} catch (e) {
  console.error('Failed to parse agrigrid_user session data:', e);
}

const storedRole = (currentUser && currentUser.role) || null;
const urlParams = new URLSearchParams(window.location.search);
const requestedRole = urlParams.get('role') || storedRole || 'farmer';

// Global Dashboard State
let currentCropsList = [];
let currentPage = 1;
const pageSize = 20;
let totalPages = 1;
let currentFilterStatus = 'Active';
let cropToDeleteId = null;

// DOM Elements: Header
const headerUsername = document.getElementById('headerUsername');
const headerFarmNameDisplay = document.getElementById('headerFarmNameDisplay');
const userAvatar = document.getElementById('userAvatar');
const logoutBtn = document.getElementById('logoutBtn');

// DOM Elements: Metrics
const metricActiveFields = document.getElementById('metricActiveFields');
const metricTotalAcreage = document.getElementById('metricTotalAcreage');
const metricProjectedYield = document.getElementById('metricProjectedYield');

// DOM Elements: Table & Action Bar
const cropsTable = document.getElementById('cropsTable');
const cropsTableBody = document.getElementById('cropsTableBody');
const emptyState = document.getElementById('emptyState');
const tableLoadingState = document.getElementById('tableLoadingState');
const recordsBadge = document.getElementById('recordsBadge');
const statusFilter = document.getElementById('statusFilter');
const openAddCropModalBtn = document.getElementById('openAddCropModalBtn');
const emptyStateAddBtn = document.getElementById('emptyStateAddBtn');

// DOM Elements: Pagination
const prevPageBtn = document.getElementById('prevPageBtn');
const nextPageBtn = document.getElementById('nextPageBtn');
const pageIndicator = document.getElementById('pageIndicator');
const paginationInfo = document.getElementById('paginationInfo');

// DOM Elements: Add/Edit Crop Modal
const cropModal = document.getElementById('cropModal');
const cropForm = document.getElementById('cropForm');
const modalTitle = document.getElementById('modalTitle');
const modalAlertBox = document.getElementById('modalAlertBox');
const modalListingId = document.getElementById('modalListingId');
const modalCropName = document.getElementById('modalCropName');
const modalPlantingDate = document.getElementById('modalPlantingDate');
const modalHarvestDate = document.getElementById('modalHarvestDate');
const modalAcreage = document.getElementById('modalAcreage');
const modalQuantityKg = document.getElementById('modalQuantityKg');
const modalAskingPrice = document.getElementById('modalAskingPrice');
const modalGpsLat = document.getElementById('modalGpsLat');
const modalGpsLng = document.getElementById('modalGpsLng');
const closeCropModalBtn = document.getElementById('closeCropModalBtn');
const cancelCropModalBtn = document.getElementById('cancelCropModalBtn');
const saveCropSubmitBtn = document.getElementById('saveCropSubmitBtn');
const saveCropBtnText = document.getElementById('saveCropBtnText');
const saveCropSpinner = document.getElementById('saveCropSpinner');

// DOM Elements: Delete / Withdraw Modal
const deleteModal = document.getElementById('deleteModal');
const deleteModalMessage = document.getElementById('deleteModalMessage');
const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
const confirmDeleteBtnText = document.getElementById('confirmDeleteBtnText');
const confirmDeleteSpinner = document.getElementById('confirmDeleteSpinner');

// DOM Elements: Toast Notification
const toastContainer = document.getElementById('toastContainer');

// =========================================================================
// 2. INITIALIZATION & HEADER POPULATION
// =========================================================================
document.addEventListener('DOMContentLoaded', () => {
  if (requestedRole !== 'farmer') {
    renderRolePlaceholder(requestedRole);
    return;
  }
  initUserProfile();
  initDateDefaults();
  setupEventListeners();
  loadMetrics();
  loadCrops(1);
});

function renderRolePlaceholder(role) {
  document.body.innerHTML = `
    <div class="min-h-screen flex flex-col items-center justify-center p-6 text-center">
      <div class="glass-card max-w-md p-8">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center text-2xl">🚧</div>
        <h1 class="text-xl font-bold text-gray-900 capitalize">${escapeHtml(role)} Console</h1>
        <p class="text-sm text-gray-600 mt-2">Dashboard under construction — available in a future increment.</p>
        <button onclick="handleLogout()" class="mt-6 px-4 py-2 rounded-lg text-sm font-semibold">Sign Out</button>
      </div>
    </div>`;
}

function initUserProfile() {
  if (currentUser) {
    const username = currentUser.username || 'Farmer';
    const farmName = currentUser.farm_name || currentUser.farm || (currentUser.farmer_id ? `Farm Node #${currentUser.farmer_id}` : 'Verified Farm Node');
    
    if (headerUsername) headerUsername.textContent = username;
    if (headerFarmNameDisplay) headerFarmNameDisplay.textContent = farmName;
    if (userAvatar) userAvatar.textContent = username.charAt(0).toUpperCase();
  } else {
    if (headerFarmNameDisplay) headerFarmNameDisplay.textContent = 'Active Farmer Terminal';
  }
}

function initDateDefaults() {
  const today = new Date();
  const todayFormatted = today.toISOString().split('T')[0];
  
  // Default estimated harvest in 90 days
  const future = new Date();
  future.setDate(today.getDate() + 90);
  const futureFormatted = future.toISOString().split('T')[0];

  if (modalPlantingDate) modalPlantingDate.value = todayFormatted;
  if (modalHarvestDate) modalHarvestDate.value = futureFormatted;
}

// =========================================================================
// 3. API SERVICE LAYER (WITH ZERO-TRUST & JWT HEADERS)
// =========================================================================
function getAuthHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${sessionStorage.getItem('agrigrid_token')}`
  };
}

/**
 * Robust error extractor matching Agri-Grid contract Section 5
 */
function extractErrorMessage(data, fallback = 'Server operation failed.') {
  if (!data) return fallback;
  if (typeof data.error === 'string') return data.error;
  if (data.error && typeof data.error.message === 'string') return data.error.message;
  if (typeof data.message === 'string') return data.message;
  return fallback;
}

/**
 * Logout Handler
 */
async function handleLogout() {
  try {
    // Attempt graceful server-side logout
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({})
    }).catch(() => {});
  } finally {
    sessionStorage.removeItem('agrigrid_token');
    sessionStorage.removeItem('agrigrid_user');
    window.location.replace('index.html');
  }
}

// =========================================================================
// 4. CROP DATA FETCH & METRICS CALCULATION
// =========================================================================
async function loadCrops(page = 1) {
  showTableLoading(true);
  currentPage = page;

  try {
    let url = `${API_BASE_URL}/crops?page=${page}&limit=${pageSize}`;
    if (currentFilterStatus && currentFilterStatus !== 'ALL') {
      url += `&status=${encodeURIComponent(currentFilterStatus)}`;
    }
    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders()
    });

    if (response.status === 401) {
      showToast('Session expired. Please log in again.', 'error');
      sessionStorage.removeItem('agrigrid_token');
      setTimeout(() => window.location.replace('index.html'), 1000);
      return;
    }

    const data = await response.json();

    if (response.ok && data) {
      // Backend contract: { success: true, data: [...], page: 1, limit: 20, total: 1 }
      const crops = Array.isArray(data.data) ? data.data : (Array.isArray(data) ? data : []);
      const totalCount = typeof data.total === 'number' ? data.total : crops.length;
      
      currentCropsList = crops;
      totalPages = Math.max(1, Math.ceil(totalCount / pageSize));

      renderCropsTable(crops, totalCount);
      updatePaginationControls(totalCount);
    } else {
      const errorMsg = extractErrorMessage(data, 'Could not retrieve crop listings.');
      showToast(errorMsg, 'error');
      renderCropsTable([], 0);
    }
  } catch (error) {
    console.error('Failed to load crop listings:', error);
    showToast(`Network error reaching Agri-Grid API at ${API_BASE_URL}. Ensure backend is running.`, 'error');
    renderCropsTable([], 0);
  } finally {
    showTableLoading(false);
  }
}

async function loadMetrics() {
  try {
    const response = await fetch(`${API_BASE_URL}/crops/stats`, { headers: getAuthHeaders() });
    const data = await response.json().catch(() => null);
    if (response.ok && data && data.data) {
      const m = data.data;
      if (metricActiveFields) metricActiveFields.textContent = m.active_fields;
      if (metricTotalAcreage) metricTotalAcreage.textContent = Number(m.total_acreage).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
      if (metricProjectedYield) metricProjectedYield.textContent = Math.round(m.projected_yield_kg).toLocaleString('en-US');
    }
  } catch (err) {
    console.error('Failed to load metrics:', err);
  }
}

// =========================================================================
// 5. TABLE RENDERING & FILTERING
// =========================================================================
function renderCropsTable(crops, totalCount) {
  cropsTableBody.innerHTML = '';

  if (recordsBadge) {
    recordsBadge.textContent = `${crops.length} of ${totalCount} Records`;
  }

  if (crops.length === 0) {
    cropsTable.classList.add('hidden');
    emptyState.classList.remove('hidden');
    return;
  }

  cropsTable.classList.remove('hidden');
  emptyState.classList.add('hidden');

  crops.forEach(crop => {
    const listingId = crop.listing_id || crop.id;
    const cropName = crop.crop_name || crop.crop_type || 'Crop';
    const plantingDate = crop.planting_date || 'N/A';
    const harvestDate = crop.estimated_harvest_date || 'N/A';
    const acreage = parseFloat(crop.acreage) || 0;
    const quantityKg = parseFloat(crop.quantity_kg || crop.estimated_yield_kg) || 0;
    const askingPrice = crop.asking_price_per_kg || crop.asking_price || crop.price_per_kg;
    const priceDisplay = askingPrice ? `$${parseFloat(askingPrice).toFixed(2)} / kg` : '<span class="text-gray-400">—</span>';
    const status = crop.status || 'Active';

    let badgeClass = 'badge-active';
    if (status.toLowerCase() === 'withdrawn') badgeClass = 'badge-withdrawn';
    if (status.toLowerCase() === 'sold') badgeClass = 'badge-sold';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="font-mono text-xs text-gray-500 font-semibold">#${listingId}</td>
      <td>
        <div class="flex items-center space-x-2">
          <span class="inline-flex items-center justify-center w-7 h-7 rounded-md bg-emerald-50 text-emerald-800 text-xs font-bold border border-mint">
            ${getCropEmoji(cropName)}
          </span>
          <span class="font-semibold text-gray-900">${escapeHtml(cropName)}</span>
        </div>
      </td>
      <td class="text-gray-600 text-xs">${escapeHtml(plantingDate)}</td>
      <td class="text-gray-600 text-xs">${escapeHtml(harvestDate)}</td>
      <td class="font-medium text-gray-800">${acreage.toFixed(1)} <span class="text-xs text-gray-400">ac</span></td>
      <td class="font-semibold text-gray-900">${Math.round(quantityKg).toLocaleString()} <span class="text-xs text-gray-400">kg</span></td>
      <td class="text-xs font-medium text-gray-700">${priceDisplay}</td>
      <td>
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${badgeClass}">
          ${escapeHtml(status)}
        </span>
      </td>
      <td class="text-right pr-4">
        <div class="inline-flex items-center space-x-1.5">
          <button 
            type="button" 
            onclick="openEditModal(${listingId})"
            class="p-1.5 text-gray-600 hover:text-emerald hover:bg-emerald-50 rounded transition-colors"
            title="Edit crop details">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
          </button>
          ${status.toLowerCase() !== 'withdrawn' ? `
            <button 
              type="button" 
              onclick="openWithdrawModal(${listingId})"
              class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
              title="Withdraw / soft-delete listing">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
            </button>
          ` : `
            <span class="p-1.5 text-gray-300 cursor-not-allowed" title="Withdrawn records are archived">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"></path>
              </svg>
            </span>
          `}
        </div>
      </td>
    `;
    cropsTableBody.appendChild(tr);
  });
}

function getCropEmoji(cropName) {
  const map = {
    'wheat': '🌾',
    'rice': '🌾',
    'tomato': '🍅',
    'potato': '🥔',
    'cotton': '🌱',
    'maize': '🌽',
    'corn': '🌽',
    'sugarcane': '🎋',
    'barley': '🌾'
  };
  return map[(cropName || '').toLowerCase()] || '🌱';
}

function showTableLoading(isLoading) {
  if (isLoading) {
    cropsTable.classList.add('hidden');
    emptyState.classList.add('hidden');
    tableLoadingState.classList.remove('hidden');
  } else {
    tableLoadingState.classList.add('hidden');
  }
}

function updatePaginationControls(total) {
  if (paginationInfo) {
    const start = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
    const end = Math.min(currentPage * pageSize, total);
    paginationInfo.textContent = `Showing ${start} to ${end} of ${total} crops`;
  }

  if (pageIndicator) {
    pageIndicator.textContent = `Page ${currentPage} of ${totalPages}`;
  }

  if (prevPageBtn) prevPageBtn.disabled = currentPage <= 1;
  if (nextPageBtn) nextPageBtn.disabled = currentPage >= totalPages;
}

// =========================================================================
// 6. ADD / EDIT CROP MODAL WORKFLOW
// =========================================================================
function openAddCropModal() {
  modalAlertBox.classList.add('hidden');
  modalAlertBox.innerHTML = '';
  modalTitle.textContent = 'Register New Crop Listing';
  saveCropBtnText.textContent = 'Create Listing';
  modalListingId.value = '';
  cropForm.reset();
  initDateDefaults();

  if (modalGpsLat) modalGpsLat.value = '30.3753';
  if (modalGpsLng) modalGpsLng.value = '69.3451';

  cropModal.classList.remove('hidden');
  modalCropName.focus();
}

window.openEditModal = async function(listingId) {
  const cachedCrop = currentCropsList.find(c => (c.listing_id || c.id) == listingId);
  if (!cachedCrop) {
    showToast('Crop listing record not found in cache.', 'error');
    return;
  }

  let crop = cachedCrop;
  try {
    const response = await fetch(`${API_BASE_URL}/crops/${listingId}`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    const data = await response.json().catch(() => null);

    if (response.status === 401) {
      showToast('Session expired. Please log in again.', 'error');
      sessionStorage.removeItem('agrigrid_token');
      setTimeout(() => window.location.replace('index.html'), 1000);
      return;
    }

    if (!response.ok || !data?.data) {
      showToast(extractErrorMessage(data, 'Could not load crop listing details.'), 'error');
      return;
    }

    crop = data.data;
  } catch (err) {
    console.error('Load crop detail error:', err);
    showToast(`Network error reaching ${API_BASE_URL}. Ensure backend is active.`, 'error');
    return;
  }

  modalAlertBox.classList.add('hidden');
  modalAlertBox.innerHTML = '';
  modalTitle.textContent = `Update Crop Listing #${listingId}`;
  saveCropBtnText.textContent = 'Update Listing';
  modalListingId.value = listingId;

  // Pre-fill form fields
  modalCropName.value = crop.crop_name || crop.crop_type || 'Wheat';
  modalPlantingDate.value = crop.planting_date || '';
  modalHarvestDate.value = crop.estimated_harvest_date || '';
  modalAcreage.value = crop.acreage || '';
  modalQuantityKg.value = crop.quantity_kg || crop.estimated_yield_kg || '';
  
  const price = crop.asking_price_per_kg || crop.asking_price || crop.price_per_kg || '';
  modalAskingPrice.value = price;

  if (modalGpsLat) modalGpsLat.value = crop.gps_latitude || '30.3753';
  if (modalGpsLng) modalGpsLng.value = crop.gps_longitude || '69.3451';

  cropModal.classList.remove('hidden');
  modalAcreage.focus();
};

function closeCropModal() {
  cropModal.classList.add('hidden');
  modalAlertBox.classList.add('hidden');
  cropForm.reset();
}

// Form Submission (Add or Update)
if (cropForm) {
  cropForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    modalAlertBox.classList.add('hidden');

    const listingId = modalListingId.value;
    const isEdit = Boolean(listingId);

    const cropName = modalCropName.value;
    const plantingDate = modalPlantingDate.value;
    const harvestDate = modalHarvestDate.value;
    const acreage = parseFloat(modalAcreage.value);
    const quantityKg = parseFloat(modalQuantityKg.value);
    const gpsLat = parseFloat(modalGpsLat.value || 30.3753);
    const gpsLng = parseFloat(modalGpsLng.value || 69.3451);

    // Client-side validations matching contract constraints
    if (!cropName) {
      showModalError('Please select a valid crop variety.');
      return;
    }

    if (!plantingDate) {
      showModalError('Planting date is required.');
      return;
    }

    if (!harvestDate) {
      showModalError('Estimated harvest date is required.');
      return;
    }

    if (new Date(harvestDate) <= new Date(plantingDate)) {
      showModalError('Estimated harvest date must be after planting date.');
      return;
    }

    if (isNaN(acreage) || acreage <= 0) {
      showModalError('Acreage must be a positive number.');
      return;
    }

    if (isNaN(quantityKg) || quantityKg <= 0) {
      showModalError('Estimated yield (kg) must be a positive number.');
      return;
    }

    // Zero-Trust Payload Construction:
    // STRICT RULE: Never include farmer_id or user_id in the payload!
    const payload = {
      crop_name: cropName,
      planting_date: plantingDate,
      estimated_harvest_date: harvestDate,
      acreage: acreage,
      quantity_kg: quantityKg,
      gps_latitude: gpsLat,
      gps_longitude: gpsLng
    };

    setModalButtonLoading(true);

    try {
      const url = isEdit ? `${API_BASE_URL}/crops/${listingId}` : `${API_BASE_URL}/crops`;
      const method = isEdit ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method: method,
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
      });

      const data = await response.json().catch(() => null);

      if (response.ok) {
        closeCropModal();
        const successMessage = isEdit 
          ? (data?.message || 'Crop listing updated successfully.') 
          : (data?.message || 'Crop listing created successfully.');
        showToast(successMessage, 'success');
        loadMetrics();
        loadCrops(currentPage);
      } else {
        const errorMsg = extractErrorMessage(data, 'Could not save crop listing.');
        showModalError(errorMsg);
      }
    } catch (err) {
      console.error('Save crop error:', err);
      showModalError(`Network error reaching ${API_BASE_URL}. Ensure backend is active.`);
    } finally {
      setModalButtonLoading(false);
    }
  });
}

function showModalError(msg) {
  modalAlertBox.textContent = msg;
  modalAlertBox.classList.remove('hidden');
}

function setModalButtonLoading(isLoading) {
  saveCropSubmitBtn.disabled = isLoading;
  if (isLoading) {
    saveCropBtnText.textContent = 'Saving...';
    saveCropSpinner.classList.remove('hidden');
  } else {
    saveCropBtnText.textContent = modalListingId.value ? 'Update Listing' : 'Save Listing';
    saveCropSpinner.classList.add('hidden');
  }
}

// =========================================================================
// 7. SOFT-DELETE / WITHDRAWAL WORKFLOW
// =========================================================================
window.openWithdrawModal = function(listingId) {
  cropToDeleteId = listingId;
  deleteModalMessage.textContent = `Are you sure you want to withdraw crop listing #${listingId}? It will be marked as Withdrawn in the provenance ledger.`;
  deleteModal.classList.remove('hidden');
};

function closeDeleteModal() {
  cropToDeleteId = null;
  deleteModal.classList.add('hidden');
  confirmDeleteBtn.disabled = false;
  confirmDeleteBtnText.textContent = 'Withdraw';
  confirmDeleteSpinner.classList.add('hidden');
}

if (confirmDeleteBtn) {
  confirmDeleteBtn.addEventListener('click', async () => {
    if (!cropToDeleteId) return;

    confirmDeleteBtn.disabled = true;
    confirmDeleteBtnText.textContent = 'Withdrawing...';
    confirmDeleteSpinner.classList.remove('hidden');

    try {
      const response = await fetch(`${API_BASE_URL}/crops/${cropToDeleteId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });

      const data = await response.json().catch(() => null);

      if (response.ok) {
        closeDeleteModal();
        showToast(data?.message || 'Listing withdrawn successfully.', 'success');
        loadMetrics();
        loadCrops(currentPage);
      } else {
        const errorMsg = extractErrorMessage(data, 'Failed to withdraw listing.');
        showToast(errorMsg, 'error');
        closeDeleteModal();
      }
    } catch (err) {
      console.error('Delete crop error:', err);
      showToast(`Network error communicating with Agri-Grid Gateway.`, 'error');
      closeDeleteModal();
    }
  });
}

// =========================================================================
// 8. TOAST NOTIFICATION ENGINE
// =========================================================================
function showToast(message, type = 'info') {
  if (!toastContainer) return;

  const isSuccess = type === 'success';
  const isError = type === 'error';

  let bgClass = 'bg-white border-gray-200 text-gray-800';
  let iconSvg = '';

  if (isSuccess) {
    bgClass = 'bg-mint-light border-emerald/30 text-emerald-950';
    iconSvg = `<svg class="w-5 h-5 text-emerald flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
    </svg>`;
  } else if (isError) {
    bgClass = 'bg-red-50 border-red-200 text-red-950';
    iconSvg = `<svg class="w-5 h-5 text-red-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
    </svg>`;
  } else {
    iconSvg = `<svg class="w-5 h-5 text-gray-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
    </svg>`;
  }

  const toast = document.createElement('div');
  toast.className = `toast-banner pointer-events-auto p-3.5 rounded-lg border text-xs sm:text-sm flex items-start justify-between shadow-lg ${bgClass}`;
  toast.innerHTML = `
    <div class="flex items-start space-x-2.5">
      ${iconSvg}
      <div class="font-medium leading-relaxed">${escapeHtml(message)}</div>
    </div>
    <button type="button" class="ml-2 text-gray-400 hover:text-gray-700 focus:outline-none" onclick="this.parentElement.remove()">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
      </svg>
    </button>
  `;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// =========================================================================
// 9. EVENT LISTENERS & WIRING
// =========================================================================
function setupEventListeners() {
  // Logout
  if (logoutBtn) logoutBtn.addEventListener('click', handleLogout);

  // Status Filter Change
  if (statusFilter) {
    statusFilter.addEventListener('change', (e) => {
      currentFilterStatus = e.target.value;
      loadCrops(1);
    });
  }

  // Modal Open / Close
  if (openAddCropModalBtn) openAddCropModalBtn.addEventListener('click', openAddCropModal);
  if (emptyStateAddBtn) emptyStateAddBtn.addEventListener('click', openAddCropModal);
  if (closeCropModalBtn) closeCropModalBtn.addEventListener('click', closeCropModal);
  if (cancelCropModalBtn) cancelCropModalBtn.addEventListener('click', closeCropModal);

  // Delete Modal Close
  if (cancelDeleteBtn) cancelDeleteBtn.addEventListener('click', closeDeleteModal);

  // Pagination Clicks
  if (prevPageBtn) {
    prevPageBtn.addEventListener('click', () => {
      if (currentPage > 1) loadCrops(currentPage - 1);
    });
  }

  if (nextPageBtn) {
    nextPageBtn.addEventListener('click', () => {
      if (currentPage < totalPages) loadCrops(currentPage + 1);
    });
  }

  // Close modals on backdrop click or ESC key
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeCropModal();
      closeDeleteModal();
    }
  });

  [cropModal, deleteModal].forEach(modal => {
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          closeCropModal();
          closeDeleteModal();
        }
      });
    }
  });
}

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
