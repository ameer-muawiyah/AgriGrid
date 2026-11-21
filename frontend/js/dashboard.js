/**
 * AgriGrid Farmer Dashboard Controller (Increment 1)
 * Manages Auth Session Guard, Active Crop CRUD Operations, Metrics, and Request Pipeline.
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

// DOM Elements: Location Picker (PD-M3, PD-M4)
const cropLocationMap = document.getElementById('cropLocationMap');
const useMyLocationBtn = document.getElementById('useMyLocationBtn');
const locationPickerStatus = document.getElementById('locationPickerStatus');

// DOM Elements: Delete / Withdraw Modal
const deleteModal = document.getElementById('deleteModal');
const deleteModalMessage = document.getElementById('deleteModalMessage');
const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
const confirmDeleteBtnText = document.getElementById('confirmDeleteBtnText');
const confirmDeleteSpinner = document.getElementById('confirmDeleteSpinner');

// DOM Elements: Predictive Yield Forecast Modal (Increment 2 Phase 4)
const forecastModal = document.getElementById('forecastModal');
const forecastModalCropName = document.getElementById('forecastModalCropName');
const forecastModalAcreage = document.getElementById('forecastModalAcreage');
const closeForecastModalBtn = document.getElementById('closeForecastModalBtn');
const closeForecastModalFooterBtn = document.getElementById('closeForecastModalFooterBtn');
const forecastEstimatedYield = document.getElementById('forecastEstimatedYield');
const forecastConfidenceBadge = document.getElementById('forecastConfidenceBadge');
const forecastConfidenceTier = document.getElementById('forecastConfidenceTier');
const forecastHarvestDate = document.getElementById('forecastHarvestDate');
const forecastEnvIndex = document.getElementById('forecastEnvIndex');
const forecastIrrigationAdvice = document.getElementById('forecastIrrigationAdvice');
const forecastGpsCoords = document.getElementById('forecastGpsCoords');
const forecastTelemetryContainer = document.getElementById('forecastTelemetryContainer');

// DOM Elements: Toast Notification
const toastContainer = document.getElementById('toastContainer');

// Navigation & Wallet (Increment 2 Phase 4 Refactor)
const navFarmerConsole = document.getElementById('navFarmerConsole');
const navFarmerOrders = document.getElementById('navFarmerOrders');
const navMarketplaceLink = document.getElementById('navMarketplaceLink');
const farmerWalletBalance = document.getElementById('farmerWalletBalance');

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
  fetchFarmerWallet();
});

function renderRolePlaceholder(role) {
  document.body.innerHTML = `
    <div class="role-placeholder">
      <div class="role-placeholder-card">
        <div class="role-placeholder-icon" aria-hidden="true">🚧</div>
        <h1>${escapeHtml(role)} Console</h1>
        <p>Dashboard under construction — available in a future increment.</p>
        <button onclick="handleLogout()" class="btn small">Sign Out</button>
      </div>
    </div>`;
}

function initUserProfile() {
  if (currentUser) {
    const role = currentUser.role || 'farmer';
    if (role === 'farmer') {
      if (navFarmerConsole) navFarmerConsole.classList.remove('hidden');
      if (navFarmerOrders) navFarmerOrders.classList.remove('hidden');
      if (navMarketplaceLink) navMarketplaceLink.classList.remove('hidden');
    }

    const username = currentUser.username || 'Farmer';
    const farmName = currentUser.farm_name || currentUser.farm || (currentUser.farmer_id ? `My Farm #${currentUser.farmer_id}` : 'My Farm');
    
    if (headerUsername) headerUsername.textContent = username;
    if (headerFarmNameDisplay) headerFarmNameDisplay.textContent = farmName;
    if (userAvatar) userAvatar.textContent = username.charAt(0).toUpperCase();
  } else {
    if (headerFarmNameDisplay) headerFarmNameDisplay.textContent = 'My Farm';
  }
}

async function fetchFarmerWallet() {
  if (!farmerWalletBalance) return;
  try {
    const res = await fetch(`${API_BASE_URL}/farmer/wallet`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) {
      farmerWalletBalance.textContent = 'Rs —';
      return;
    }
    const data = await res.json().catch(() => null);
    if (data && data.success && data.data && typeof data.data.balance_pkr === 'number') {
      farmerWalletBalance.textContent = `Rs ${data.data.balance_pkr.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    } else {
      farmerWalletBalance.textContent = 'Rs —';
    }
  } catch (e) {
    farmerWalletBalance.textContent = 'Rs —';
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
// 3. API SERVICE LAYER (WITH AUTH & JWT HEADERS)
// =========================================================================
function getAuthHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${sessionStorage.getItem('agrigrid_token')}`
  };
}

/**
 * Robust error extractor matching AgriGrid contract Section 5
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
    showToast(`Network error reaching AgriGrid API at ${API_BASE_URL}. Ensure backend is running.`, 'error');
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
    const batchId = crop.batch_id;
    const batchDisplay = batchId 
      ? `<span class="cell-batch mono">${escapeHtml(batchId)}</span>` 
      : '<span class="cell-price-na">—</span>';

    const cropName = crop.crop_name || crop.crop_type || 'Crop';
    const plantingDate = crop.planting_date || 'N/A';
    const harvestDate = crop.estimated_harvest_date || 'N/A';
    const acreage = parseFloat(crop.acreage) || 0;
    const quantityKg = parseFloat(crop.quantity_kg || crop.estimated_yield_kg) || 0;
    const askingPrice = crop.asking_price_per_kg || crop.asking_price || crop.price_per_kg;
    const priceDisplay = (askingPrice && parseFloat(askingPrice) > 0)
      ? `Rs ${parseFloat(askingPrice).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / kg`
      : '<span class="cell-price-na">—</span>';
    const status = crop.status || 'Active';

    let badgeClass = 'growing';
    if (status.toLowerCase() === 'withdrawn') badgeClass = 'withdrawn';
    if (status.toLowerCase() === 'sold') badgeClass = 'sold';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="cell-id">#${listingId}</td>
      <td>${batchDisplay}</td>
      <td>
        <div class="cell-crop">
          <span class="crop-icon">
            ${getCropEmoji(cropName)}
          </span>
          <span class="crop-name">${escapeHtml(cropName)}</span>
        </div>
      </td>
      <td class="cell-date">${escapeHtml(plantingDate)}</td>
      <td class="cell-date">${escapeHtml(harvestDate)}</td>
      <td class="cell-value">${acreage.toFixed(1)} <span class="cell-unit">ac</span></td>
      <td class="cell-value">${Math.round(quantityKg).toLocaleString()} <span class="cell-unit">kg</span></td>
      <td class="cell-price">${priceDisplay}</td>
      <td>
        <span class="status ${badgeClass}">
          ${escapeHtml(status)}
        </span>
      </td>
      <td class="cell-actions">
        <div class="action-group">
          ${status.toLowerCase() === 'active' ? `
            <button 
              type="button" 
              onclick="handleForecastYield(event, ${listingId})"
              class="btn-forecast"
              title="Forecast Yield">
              ⚡ Forecast Yield
            </button>
          ` : ''}
          <button 
            type="button" 
            onclick="openEditModal(${listingId})"
            class="action-btn"
            title="Edit crop details">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
          </button>
          ${status.toLowerCase() !== 'withdrawn' ? `
            <button 
              type="button" 
              onclick="openWithdrawModal(${listingId})"
              class="action-btn delete-btn"
              title="Withdraw / soft-delete listing">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
            </button>
          ` : `
            <span class="action-btn disabled-btn" title="Withdrawn records are archived">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
    'sugarcane': '🎋'
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
// 5.5 FIELD LOCATION PICKER (LEAFLET PIN-DROP) (PD-M4, PD-M5)
// =========================================================================
let cropLocationMapInstance = null;
let cropLocationMarker = null;
let locationPickerInitialized = false;

function updateGpsInputs(lat, lng) {
  if (modalGpsLat) modalGpsLat.value = lat.toFixed(6);
  if (modalGpsLng) modalGpsLng.value = lng.toFixed(6);
  if (locationPickerStatus) locationPickerStatus.textContent = '';
}

function handleGpsInputChange() {
  const latVal = parseFloat(modalGpsLat?.value);
  const lngVal = parseFloat(modalGpsLng?.value);
  if (!isNaN(latVal) && !isNaN(lngVal) && latVal >= -90 && latVal <= 90 && lngVal >= -180 && lngVal <= 180) {
    if (cropLocationMarker) {
      cropLocationMarker.setLatLng([latVal, lngVal]);
    }
    if (cropLocationMapInstance) {
      cropLocationMapInstance.setView([latVal, lngVal]);
      if (locationPickerStatus) locationPickerStatus.textContent = '';
    }
  }
}

function handleUseMyLocation() {
  if (!window.L) {
    if (locationPickerStatus) {
      locationPickerStatus.textContent = 'Map unavailable — type the coordinates instead.';
    }
    if (useMyLocationBtn) {
      useMyLocationBtn.disabled = true;
    }
    return;
  }

  if (!navigator.geolocation || !navigator.geolocation.getCurrentPosition) {
    if (locationPickerStatus) {
      locationPickerStatus.textContent = 'Location unavailable — drop the pin on the map instead.';
    }
    return;
  }

  navigator.geolocation.getCurrentPosition(
    function(pos) {
      const lat = pos.coords.latitude;
      const lng = pos.coords.longitude;
      updateGpsInputs(lat, lng);
      if (cropLocationMarker) {
        cropLocationMarker.setLatLng([lat, lng]);
      }
      if (cropLocationMapInstance) {
        cropLocationMapInstance.setView([lat, lng], 15);
      }
      if (locationPickerStatus) {
        locationPickerStatus.textContent = '';
      }
    },
    function(err) {
      if (locationPickerStatus) {
        locationPickerStatus.textContent = 'Location unavailable — drop the pin on the map instead.';
      }
    },
    { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
  );
}

function initLocationPicker() {
  if (locationPickerInitialized) return;
  locationPickerInitialized = true;

  if (useMyLocationBtn) {
    useMyLocationBtn.addEventListener('click', handleUseMyLocation);
  }

  if (modalGpsLat) modalGpsLat.addEventListener('change', handleGpsInputChange);
  if (modalGpsLng) modalGpsLng.addEventListener('change', handleGpsInputChange);

  if (!window.L) {
    if (locationPickerStatus) {
      locationPickerStatus.textContent = 'Map unavailable — type the coordinates instead.';
    }
    if (useMyLocationBtn) {
      useMyLocationBtn.disabled = true;
    }
    return;
  }

  if (!cropLocationMap) return;

  const initialLat = parseFloat(modalGpsLat?.value) || 34.0151;
  const initialLng = parseFloat(modalGpsLng?.value) || 71.5249;

  // Base layers: Satellite (default, Esri) and Street (OSM) (PD-M2)
  const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri',
    maxZoom: 18
  });

  const streetLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  });

  const baseLayers = {
    'Satellite': satelliteLayer,
    'Street': streetLayer
  };

  cropLocationMapInstance = L.map(cropLocationMap, {
    center: [initialLat, initialLng],
    zoom: 13,
    layers: [satelliteLayer]
  });

  L.control.layers(baseLayers).addTo(cropLocationMapInstance);

  // Draggable marker (PD-M4)
  cropLocationMarker = L.marker([initialLat, initialLng], {
    draggable: true
  }).addTo(cropLocationMapInstance);

  cropLocationMarker.on('dragend', function(e) {
    const pos = e.target.getLatLng();
    updateGpsInputs(pos.lat, pos.lng);
  });

  cropLocationMapInstance.on('click', function(e) {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;
    cropLocationMarker.setLatLng([lat, lng]);
    updateGpsInputs(lat, lng);
  });
}

function syncLocationPicker(lat, lng, zoom = 13) {
  if (!locationPickerInitialized) {
    initLocationPicker();
  }

  if (!window.L) {
    if (locationPickerStatus) {
      locationPickerStatus.textContent = 'Map unavailable — type the coordinates instead.';
    }
    if (useMyLocationBtn) {
      useMyLocationBtn.disabled = true;
    }
    return;
  }

  if (locationPickerStatus) {
    locationPickerStatus.textContent = '';
  }

  const validLat = typeof lat === 'number' && !isNaN(lat) ? lat : (parseFloat(modalGpsLat?.value) || 34.0151);
  const validLng = typeof lng === 'number' && !isNaN(lng) ? lng : (parseFloat(modalGpsLng?.value) || 71.5249);

  if (cropLocationMarker) {
    cropLocationMarker.setLatLng([validLat, validLng]);
  }
  if (cropLocationMapInstance) {
    cropLocationMapInstance.setView([validLat, validLng], zoom);
    cropLocationMapInstance.invalidateSize();
    requestAnimationFrame(() => {
      if (cropLocationMapInstance) {
        cropLocationMapInstance.invalidateSize();
        cropLocationMapInstance.setView([validLat, validLng], zoom);
      }
    });
    setTimeout(() => {
      if (cropLocationMapInstance) {
        cropLocationMapInstance.invalidateSize();
        cropLocationMapInstance.setView([validLat, validLng], zoom);
      }
    }, 300);
  }
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

  if (modalGpsLat) modalGpsLat.value = '34.0151';
  if (modalGpsLng) modalGpsLng.value = '71.5249';

  cropModal.classList.remove('hidden');
  syncLocationPicker(34.0151, 71.5249, 12);
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

  const latVal = parseFloat(crop.gps_latitude || '34.0151');
  const lngVal = parseFloat(crop.gps_longitude || '71.5249');

  if (modalGpsLat) modalGpsLat.value = crop.gps_latitude || '34.0151';
  if (modalGpsLng) modalGpsLng.value = crop.gps_longitude || '71.5249';

  cropModal.classList.remove('hidden');
  syncLocationPicker(latVal, lngVal, 13);
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
    const gpsLat = parseFloat(modalGpsLat.value || 34.0151);
    const gpsLng = parseFloat(modalGpsLng.value || 71.5249);

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

    // Payload Construction:
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

    const rawPrice = modalAskingPrice ? modalAskingPrice.value.trim() : '';
    if (rawPrice !== '') {
      const priceVal = parseFloat(rawPrice);
      if (isNaN(priceVal) || priceVal <= 0) {
        showModalError('Asking price per kg must be greater than 0.');
        setModalButtonLoading(false);
        return;
      }
      payload.asking_price_per_kg = Math.round(priceVal * 100) / 100;
    }

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
  deleteModalMessage.textContent = `Are you sure you want to withdraw crop listing #${listingId}? It will be marked as Withdrawn and removed from the marketplace.`;
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
      showToast(`Network error communicating with AgriGrid Gateway.`, 'error');
      closeDeleteModal();
    }
  });
}

// =========================================================================
// 7B. PREDICTIVE YIELD FORECAST & TELEMETRY ENGINE (Increment 2 Phase 4)
// =========================================================================

function closeForecastModal() {
  if (forecastModal) {
    forecastModal.classList.add('hidden');
  }
}

if (closeForecastModalBtn) {
  closeForecastModalBtn.addEventListener('click', closeForecastModal);
}
if (closeForecastModalFooterBtn) {
  closeForecastModalFooterBtn.addEventListener('click', closeForecastModal);
}
if (forecastModal) {
  forecastModal.addEventListener('click', (e) => {
    if (e.target === forecastModal) {
      closeForecastModal();
    }
  });
}

/**
 * Handle Forecast Yield click on active crop rows (FR-YLD-007)
 */
window.handleForecastYield = async function(event, listingId) {
  const btn = event ? event.currentTarget : null;
  const originalHtml = btn ? btn.innerHTML : '⚡ Forecast Yield';

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="forecast-spinner"></span> Forecasting...';
  }

  try {
    const response = await fetch(`${API_BASE_URL}/yield/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ listing_id: Number(listingId) })
    });

    const data = await response.json().catch(() => null);

    if (response.ok && data && data.success && data.data) {
      await openForecastModal(data.data, listingId);
    } else {
      const errorMsg = (data && data.error) ? data.error : extractErrorMessage(data, 'Failed to generate yield forecast.');
      showToast(errorMsg, 'error');
    }
  } catch (err) {
    console.error('Yield prediction error:', err);
    showToast(`Network error reaching AgriGrid API at ${API_BASE_URL}. Ensure backend is running.`, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalHtml;
    }
  }
};

/**
 * Populate and display the forecast modal
 */
async function openForecastModal(forecast, listingId) {
  if (!forecastModal) return;

  const cropName = forecast.crop_name || 'Crop';
  const acreage = Number(forecast.acreage || 0);

  if (forecastModalCropName) {
    forecastModalCropName.textContent = `${cropName} Yield Projection`;
  }
  if (forecastModalAcreage) {
    forecastModalAcreage.textContent = `${acreage.toFixed(1)} Acres`;
  }

  // Estimated yield: formatted kg + tonnes in parentheses (2 decimals)
  const yieldKg = Number(forecast.predicted_yield_kg) || 0;
  const tonnes = (yieldKg / 1000).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const kgFormatted = yieldKg.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (forecastEstimatedYield) {
    forecastEstimatedYield.textContent = `${kgFormatted} kg (${tonnes} t)`;
  }

  // Confidence badge: color tiers: >= 85 high (Terra green), 70-84 medium (clay accent), < 70 low (muted red)
  const confidence = Number(forecast.confidence_score_pct) || 0;
  let tierClass = 'conf-low';
  let tierText = 'Low Confidence (<70%)';
  if (confidence >= 85) {
    tierClass = 'conf-high';
    tierText = 'High Agronomic Certainty (≥85%)';
  } else if (confidence >= 70) {
    tierClass = 'conf-medium';
    tierText = 'Moderate Certainty (70–84%)';
  }

  if (forecastConfidenceBadge) {
    forecastConfidenceBadge.className = `confidence-badge ${tierClass}`;
    forecastConfidenceBadge.textContent = `${confidence}% Confidence`;
  }
  if (forecastConfidenceTier) {
    forecastConfidenceTier.textContent = tierText;
  }

  // Predicted harvest date
  if (forecastHarvestDate) {
    forecastHarvestDate.textContent = forecast.predicted_harvest_date || 'N/A';
  }

  // Environmental index (2 decimals)
  const envIndex = Number(forecast.environmental_index);
  if (forecastEnvIndex) {
    forecastEnvIndex.textContent = !isNaN(envIndex) ? envIndex.toFixed(2) : '—';
  }

  // Irrigation advice
  if (forecastIrrigationAdvice) {
    forecastIrrigationAdvice.textContent = forecast.irrigation_advice || 'Maintain standard irrigation schedule.';
  }

  // Telemetry context (Weather & Soil)
  const crop = currentCropsList.find(c => Number(c.listing_id || c.id) === Number(listingId));
  const lat = crop ? crop.gps_latitude : null;
  const lon = crop ? crop.gps_longitude : null;

  if (forecastGpsCoords) {
    if (lat !== null && lat !== undefined && lon !== null && lon !== undefined && !isNaN(Number(lat)) && !isNaN(Number(lon))) {
      forecastGpsCoords.textContent = `GPS: ${Number(lat).toFixed(4)}, ${Number(lon).toFixed(4)}`;
    } else {
      forecastGpsCoords.textContent = 'GPS: Not specified';
    }
  }

  await loadTelemetryContext(lat, lon);

  forecastModal.classList.remove('hidden');
}

/**
 * Load telemetry context (Weather + Soil)
 */
async function loadTelemetryContext(lat, lon) {
  if (!forecastTelemetryContainer) return;

  if (lat === null || lat === undefined || lon === null || lon === undefined || isNaN(Number(lat)) || isNaN(Number(lon))) {
    forecastTelemetryContainer.innerHTML = '<div class="telemetry-unavailable">Weather and soil data unavailable</div>';
    return;
  }

  try {
    const latNum = Number(lat);
    const lonNum = Number(lon);

    const [weatherRes, soilRes] = await Promise.allSettled([
      fetch(`${API_BASE_URL}/telemetry/weather?lat=${latNum}&lon=${lonNum}`, { headers: getAuthHeaders() }),
      fetch(`${API_BASE_URL}/telemetry/soil?lat=${latNum}&lon=${lonNum}`, { headers: getAuthHeaders() })
    ]);

    let weatherData = null;
    let weatherSource = null;
    let soilData = null;
    let soilSource = null;

    if (weatherRes.status === 'fulfilled' && weatherRes.value && weatherRes.value.ok) {
      const wJson = await weatherRes.value.json().catch(() => null);
      if (wJson && wJson.success && wJson.data) {
        weatherData = wJson.data;
        weatherSource = wJson.source || 'cache';
      }
    }

    if (soilRes.status === 'fulfilled' && soilRes.value && soilRes.value.ok) {
      const sJson = await soilRes.value.json().catch(() => null);
      if (sJson && sJson.success && sJson.data) {
        soilData = sJson.data;
        soilSource = sJson.source || 'live_api';
      }
    }

    if (!weatherData || !soilData) {
      forecastTelemetryContainer.innerHTML = '<div class="telemetry-unavailable">Weather and soil data unavailable</div>';
      return;
    }

    let html = `
      <div class="telemetry-card">
        <span class="telemetry-label">Temperature</span>
        <span class="telemetry-value">${escapeHtml(String(weatherData.temperature_c))} °C</span>
        <span class="telemetry-source">source: ${escapeHtml(String(weatherSource))}</span>
      </div>
      <div class="telemetry-card">
        <span class="telemetry-label">Relative Humidity</span>
        <span class="telemetry-value">${escapeHtml(String(weatherData.relative_humidity_pct))}%</span>
        <span class="telemetry-source">source: ${escapeHtml(String(weatherSource))}</span>
      </div>
      <div class="telemetry-card">
        <span class="telemetry-label">Topsoil Moisture</span>
        <span class="telemetry-value">${escapeHtml(String(soilData.topsoil_moisture_vol_pct))} vol %</span>
        <span class="telemetry-source">source: ${escapeHtml(String(soilSource))}</span>
      </div>
      <div class="telemetry-card">
        <span class="telemetry-label">Soil pH</span>
        <span class="telemetry-value">${escapeHtml(String(soilData.soil_ph))}</span>
        <span class="telemetry-source">source: ${escapeHtml(String(soilSource))}</span>
      </div>
    `;

    forecastTelemetryContainer.innerHTML = html;
  } catch (err) {
    console.error('Telemetry fetch error:', err);
    forecastTelemetryContainer.innerHTML = '<div class="telemetry-unavailable">Weather and soil data unavailable</div>';
  }
}

// =========================================================================
// 8. TOAST NOTIFICATION ENGINE
// =========================================================================
function showToast(message, type = 'info') {
  if (!toastContainer) return;

  const isSuccess = type === 'success';
  const isError = type === 'error';

  let toastTypeClass = '';
  let iconSvg = '';

  if (isSuccess) {
    toastTypeClass = 'toast-success';
    iconSvg = `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
    </svg>`;
  } else if (isError) {
    toastTypeClass = 'toast-error';
    iconSvg = `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
    </svg>`;
  } else {
    iconSvg = `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
    </svg>`;
  }

  const toast = document.createElement('div');
  toast.className = `toast-banner ${toastTypeClass}`;
  toast.innerHTML = `
    <div class="toast-content">
      ${iconSvg}
      <div class="toast-text">${escapeHtml(message)}</div>
    </div>
    <button type="button" class="toast-dismiss" onclick="this.parentElement.remove()">
      <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
