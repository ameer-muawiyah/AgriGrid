/**
 * Agri-Grid — B2B Wholesale Marketplace & Buyer Controller
 * Increment 2, Phase 2 (Contracts Endpoints 1–4, 13)
 */

const API_BASE_URL = 'http://127.0.0.1:5000/api';

// =========================================================================
// 1. AUTH GUARD & SESSION VALIDATION
// =========================================================================
const token = sessionStorage.getItem('agrigrid_token');
if (!token) {
  window.location.replace('index.html');
}

let currentUser = null;
try {
  const userJson = sessionStorage.getItem('agrigrid_user');
  if (userJson) {
    currentUser = JSON.parse(userJson);
  }
} catch (e) {
  console.error('Failed to parse agrigrid_user session data:', e);
}

// Global Headers Helper
function getAuthHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${sessionStorage.getItem('agrigrid_token')}`
  };
}

// DOM Elements
const headerCompanyNameDisplay = document.getElementById('headerCompanyNameDisplay');
const headerLocationDisplay = document.getElementById('headerLocationDisplay');
const headerRoleBadge = document.getElementById('headerRoleBadge');
const headerWalletBalance = document.getElementById('headerWalletBalance');
const headerWalletPill = document.getElementById('headerWalletPill');
const buyerAvatar = document.getElementById('buyerAvatar');
const buyerLogoutBtn = document.getElementById('buyerLogoutBtn');
const farmerConsoleLink = document.getElementById('farmerConsoleLink');

// Catalog & Filter Elements
const filterCropName = document.getElementById('filterCropName');
const filterMaxPrice = document.getElementById('filterMaxPrice');
const filterSort = document.getElementById('filterSort');
const applyFiltersBtn = document.getElementById('applyFiltersBtn');
const resetFiltersBtn = document.getElementById('resetFiltersBtn');
const clearFiltersBtn = document.getElementById('clearFiltersBtn');
const catalogCountBadge = document.getElementById('catalogCountBadge');
const catalogGrid = document.getElementById('catalogGrid');
const catalogLoading = document.getElementById('catalogLoading');
const catalogEmpty = document.getElementById('catalogEmpty');

// Pagination Elements
const catalogPaginationInfo = document.getElementById('catalogPaginationInfo');
const catalogPageIndicator = document.getElementById('catalogPageIndicator');
const catalogPrevBtn = document.getElementById('catalogPrevBtn');
const catalogNextBtn = document.getElementById('catalogNextBtn');

// Modal Elements
const listingDetailModal = document.getElementById('listingDetailModal');
const closeDetailModalBtn = document.getElementById('closeDetailModalBtn');
const detailModalAlert = document.getElementById('detailModalAlert');
const detailModalContent = document.getElementById('detailModalContent');
const modalCropIcon = document.getElementById('modalCropIcon');
const modalCropNameHeading = document.getElementById('modalCropNameHeading');
const modalFarmOrigin = document.getElementById('modalFarmOrigin');
const modalBatchIdBadge = document.getElementById('modalBatchIdBadge');
const modalAskingPriceVal = document.getElementById('modalAskingPriceVal');
const modalTotalPriceVal = document.getElementById('modalTotalPriceVal');
const modalQuantityVal = document.getElementById('modalQuantityVal');
const modalAcreageVal = document.getElementById('modalAcreageVal');
const modalPlantingDateVal = document.getElementById('modalPlantingDateVal');
const modalHarvestDateVal = document.getElementById('modalHarvestDateVal');
const modalGpsVal = document.getElementById('modalGpsVal');
const modalStatusBadge = document.getElementById('modalStatusBadge');
const modalListingMeta = document.getElementById('modalListingMeta');

// Checkout Elements (Increment 2 Phase 3)
const checkoutSection = document.getElementById('checkoutSection');
const checkoutAlert = document.getElementById('checkoutAlert');
const checkoutForm = document.getElementById('checkoutForm');
const checkoutLockedQuantity = document.getElementById('checkoutLockedQuantity');
const checkoutDestination = document.getElementById('checkoutDestination');
const checkoutMaxTemp = document.getElementById('checkoutMaxTemp');
const checkoutTotalCommitment = document.getElementById('checkoutTotalCommitment');
const checkoutSubmitBtn = document.getElementById('checkoutSubmitBtn');
const checkoutSubmitBtnText = document.getElementById('checkoutSubmitBtnText');
const checkoutSpinner = document.getElementById('checkoutSpinner');
const checkoutSuccessState = document.getElementById('checkoutSuccessState');
const successOrderNumber = document.getElementById('successOrderNumber');
const successOrderTotal = document.getElementById('successOrderTotal');
const successRemainingBalance = document.getElementById('successRemainingBalance');
const closeSuccessModalBtn = document.getElementById('closeSuccessModalBtn');

// Buyer Orders Elements (Increment 2 Phase 3)
const buyerOrdersTable = document.getElementById('buyerOrdersTable');
const buyerOrdersTableBody = document.getElementById('buyerOrdersTableBody');
const buyerOrdersEmpty = document.getElementById('buyerOrdersEmpty');
const buyerOrdersLoading = document.getElementById('buyerOrdersLoading');
const buyerOrdersCountBadge = document.getElementById('buyerOrdersCountBadge');
const buyerOrdersPaginationInfo = document.getElementById('buyerOrdersPaginationInfo');
const buyerOrdersPageIndicator = document.getElementById('buyerOrdersPageIndicator');
const buyerOrdersPrevBtn = document.getElementById('buyerOrdersPrevBtn');
const buyerOrdersNextBtn = document.getElementById('buyerOrdersNextBtn');
const buyerChipAll = document.getElementById('buyerChipAll');
const buyerChipEscrowFunded = document.getElementById('buyerChipEscrowFunded');
const buyerChipInTransit = document.getElementById('buyerChipInTransit');
const buyerChipDelivered = document.getElementById('buyerChipDelivered');
const buyerChipCompleted = document.getElementById('buyerChipCompleted');
const buyerChipCancelled = document.getElementById('buyerChipCancelled');
const buyerChipDisputed = document.getElementById('buyerChipDisputed');

// State
let currentDetailListing = null;
let currentListings = [];
let currentPage = 1;
const pageSize = 12;
let totalListings = 0;
let totalPages = 1;

let currentBuyerOrders = [];
let currentBuyerOrdersPage = 1;
const buyerOrdersPageSize = 20;
let totalBuyerOrders = 0;
let totalBuyerOrdersPages = 1;
let currentBuyerOrdersStatus = '';

// Crop Emoji Taxonomy Mapping
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

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatPriceRs(val) {
  const num = parseFloat(val) || 0;
  return `Rs ${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatTotalRs(val) {
  const num = parseFloat(val) || 0;
  return `Rs ${Math.round(num).toLocaleString('en-US')}`;
}

// =========================================================================
// 2. HEADER & PROFILE INITIALIZATION
// =========================================================================
function initHeaderProfile() {
  if (!currentUser) return;

  const role = currentUser.role || 'buyer';

  if (role === 'farmer') {
    // Farmer viewing marketplace
    if (farmerConsoleLink) farmerConsoleLink.classList.remove('hidden');
    if (headerCompanyNameDisplay) {
      headerCompanyNameDisplay.textContent = currentUser.farm_name || currentUser.username || 'Farmer Terminal';
    }
    if (headerLocationDisplay) headerLocationDisplay.textContent = 'Producer Node · Verified';
    if (headerRoleBadge) headerRoleBadge.textContent = 'Farmer (Market View)';
    if (headerWalletPill) {
      headerWalletPill.title = 'Marketplace read-only transparency mode';
      headerWalletBalance.textContent = 'Transparency View';
    }
    if (buyerAvatar) buyerAvatar.textContent = (currentUser.username || 'F').charAt(0).toUpperCase();
  } else {
    // Buyer account
    const company = currentUser.company_name || currentUser.username || 'B2B Wholesale Terminal';
    if (headerCompanyNameDisplay) headerCompanyNameDisplay.textContent = company;
    if (headerLocationDisplay) headerLocationDisplay.textContent = 'Wholesale Terminal · Verified';
    if (headerRoleBadge) headerRoleBadge.textContent = 'B2B Buyer';

    // Balance rendered as Rs 500,000 (Rs + thousands separators - zero $)
    const rawBalance = currentUser.wallet_balance_pkr !== undefined ? currentUser.wallet_balance_pkr : 500000.0;
    const formattedBalance = `Rs ${Math.round(parseFloat(rawBalance)).toLocaleString('en-US')}`;
    if (headerWalletBalance) headerWalletBalance.textContent = formattedBalance;

    if (buyerAvatar) {
      buyerAvatar.textContent = company.charAt(0).toUpperCase();
    }
  }
}

// Logout Action
if (buyerLogoutBtn) {
  buyerLogoutBtn.addEventListener('click', async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: getAuthHeaders()
      }).catch(() => {});
    } finally {
      sessionStorage.removeItem('agrigrid_token');
      sessionStorage.removeItem('agrigrid_user');
      window.location.replace('index.html');
    }
  });
}

// =========================================================================
// 3. FETCH & RENDER MARKETPLACE CATALOG
// =========================================================================
async function fetchCatalog(page = 1) {
  currentPage = page;
  showCatalogLoading(true);

  try {
    let url = `${API_BASE_URL}/marketplace/listings?page=${page}&limit=${pageSize}`;

    const cropVal = filterCropName ? filterCropName.value.trim() : '';
    const maxPriceVal = filterMaxPrice ? filterMaxPrice.value.trim() : '';
    const sortVal = filterSort ? filterSort.value.trim() : 'date_desc';

    if (cropVal) {
      url += `&crop_name=${encodeURIComponent(cropVal)}`;
    }
    if (maxPriceVal) {
      const p = parseFloat(maxPriceVal);
      if (!isNaN(p) && p > 0) {
        url += `&max_price=${encodeURIComponent(p)}`;
      }
    }
    if (sortVal) {
      url += `&sort=${encodeURIComponent(sortVal)}`;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders()
    });

    if (response.status === 401) {
      showToast('Session expired. Please log in again.', 'error');
      sessionStorage.removeItem('agrigrid_token');
      setTimeout(() => window.location.replace('index.html'), 1200);
      return;
    }

    if (response.status === 403) {
      showToast('Access denied to marketplace catalog.', 'error');
      return;
    }

    const resData = await response.json().catch(() => null);

    if (response.ok && resData && resData.success) {
      currentListings = resData.data || [];
      totalListings = resData.total || 0;
      totalPages = Math.max(1, Math.ceil(totalListings / pageSize));

      renderCatalogCards(currentListings);
      updatePaginationControls();
    } else {
      const err = resData?.error || 'Failed to load catalog produce listings.';
      showToast(err, 'error');
      renderCatalogCards([]);
    }
  } catch (err) {
    console.error('Fetch catalog network error:', err);
    showToast(`Network error reaching ${API_BASE_URL}. Ensure backend is active.`, 'error');
    renderCatalogCards([]);
  } finally {
    showCatalogLoading(false);
  }
}

function showCatalogLoading(isLoading) {
  if (isLoading) {
    if (catalogLoading) catalogLoading.classList.remove('hidden');
    if (catalogEmpty) catalogEmpty.classList.add('hidden');
    if (catalogGrid) catalogGrid.classList.add('hidden');
  } else {
    if (catalogLoading) catalogLoading.classList.add('hidden');
  }
}

function renderCatalogCards(listings) {
  if (!catalogGrid) return;
  catalogGrid.innerHTML = '';

  if (catalogCountBadge) {
    catalogCountBadge.textContent = `${totalListings} Listings`;
  }

  if (!listings || listings.length === 0) {
    if (catalogEmpty) catalogEmpty.classList.remove('hidden');
    catalogGrid.classList.add('hidden');
    return;
  }

  if (catalogEmpty) catalogEmpty.classList.add('hidden');
  catalogGrid.classList.remove('hidden');

  listings.forEach(listing => {
    const listingId = listing.listing_id || listing.id;
    const cropName = listing.crop_name || 'Produce';
    const batchId = listing.batch_id || 'BATCH-PROV';
    const farmName = listing.farm_name || 'Verified Farm Node';
    const farmLoc = listing.farm_location || 'Pakistan';
    const quantityKg = parseFloat(listing.quantity_kg) || 0;
    const pricePerKg = parseFloat(listing.asking_price_per_kg) || 0;
    const totalPricePkr = parseFloat(listing.total_price_pkr) || (quantityKg * pricePerKg);
    const estHarvest = listing.estimated_harvest_date || 'N/A';

    const card = document.createElement('div');
    card.className = 'produce-card';
    card.innerHTML = `
      <div class="produce-card-head">
        <div class="crop-profile">
          <div class="crop-profile-icon" aria-hidden="true">${getCropEmoji(cropName)}</div>
          <div class="crop-profile-info">
            <h3>${escapeHtml(cropName)}</h3>
            <div class="farm-origin">${escapeHtml(farmName)} • ${escapeHtml(farmLoc)}</div>
          </div>
        </div>
        <span class="badge-batch">${escapeHtml(batchId)}</span>
      </div>

      <div class="card-metrics">
        <div class="metric-row">
          <span class="m-lbl">Available Lot</span>
          <span class="m-val">${Math.round(quantityKg).toLocaleString('en-US')} kg</span>
        </div>
        <div class="metric-row">
          <span class="m-lbl">Asking Price</span>
          <span class="m-val">${formatPriceRs(pricePerKg)} / kg</span>
        </div>
        <div class="metric-row">
          <span class="m-lbl">Est. Harvest</span>
          <span class="m-val mono">${escapeHtml(estHarvest)}</span>
        </div>
        <div class="metric-row highlight">
          <span class="m-lbl">Total Lot Price</span>
          <span class="m-val">${formatTotalRs(totalPricePkr)}</span>
        </div>
      </div>

      <div class="produce-card-foot">
        <button 
          type="button" 
          class="btn-view-detail" 
          onclick="openListingDetail(${listingId})"
          title="Inspect full commercial and agronomic telemetry">
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
          </svg>
          <span>View Listing Details</span>
        </button>
      </div>
    `;
    catalogGrid.appendChild(card);
  });
}

function updatePaginationControls() {
  if (catalogPaginationInfo) {
    const start = totalListings === 0 ? 0 : (currentPage - 1) * pageSize + 1;
    const end = Math.min(currentPage * pageSize, totalListings);
    catalogPaginationInfo.textContent = `Showing ${start} to ${end} of ${totalListings} listings`;
  }

  if (catalogPageIndicator) {
    catalogPageIndicator.textContent = `Page ${currentPage} of ${totalPages}`;
  }

  if (catalogPrevBtn) catalogPrevBtn.disabled = currentPage <= 1;
  if (catalogNextBtn) catalogNextBtn.disabled = currentPage >= totalPages;
}

// =========================================================================
// 4. LISTING DETAIL MODAL (Contracts Endpoint 4)
// =========================================================================
window.openListingDetail = async function(listingId) {
  if (!listingDetailModal) return;

  // Clear modal states
  if (detailModalAlert) {
    detailModalAlert.classList.add('hidden');
    detailModalAlert.innerHTML = '';
  }
  if (detailModalContent) detailModalContent.classList.remove('hidden');

  listingDetailModal.classList.remove('hidden');

  try {
    const response = await fetch(`${API_BASE_URL}/marketplace/listings/${listingId}`, {
      method: 'GET',
      headers: getAuthHeaders()
    });

    const resData = await response.json().catch(() => null);

    if (response.status === 404 || !response.ok || !resData || !resData.data) {
      // Contracts Endpoint 4 requirement: 404 response shows server's "Listing not found." message
      const errMsg = resData?.error || 'Listing not found.';
      if (detailModalAlert) {
        detailModalAlert.innerHTML = `
          <div style="padding: 12px 14px; background: var(--danger-soft); border: 1px solid var(--danger); border-radius: 10px; color: var(--danger); font-size: 13.5px; font-weight: 500;">
            ${escapeHtml(errMsg)}
          </div>
        `;
        detailModalAlert.classList.remove('hidden');
      }
      if (detailModalContent) detailModalContent.classList.add('hidden');
      return;
    }

    const item = resData.data;

    // Populate Modal Content
    if (modalCropIcon) modalCropIcon.textContent = getCropEmoji(item.crop_name);
    if (modalCropNameHeading) modalCropNameHeading.textContent = item.crop_name || 'Produce';
    if (modalFarmOrigin) {
      modalFarmOrigin.textContent = `${item.farm_name || 'Farm Node'} • ${item.farm_location || 'Pakistan'}`;
    }
    if (modalBatchIdBadge) modalBatchIdBadge.textContent = item.batch_id || 'BATCH-PROV';
    if (modalAskingPriceVal) modalAskingPriceVal.textContent = `${formatPriceRs(item.asking_price_per_kg)} / kg`;
    if (modalTotalPriceVal) modalTotalPriceVal.textContent = formatTotalRs(item.total_price_pkr);
    if (modalQuantityVal) modalQuantityVal.textContent = `${Math.round(item.quantity_kg || 0).toLocaleString('en-US')} kg`;
    if (modalAcreageVal) modalAcreageVal.textContent = `${parseFloat(item.acreage || 0).toFixed(1)} ac`;
    if (modalPlantingDateVal) modalPlantingDateVal.textContent = item.planting_date || 'N/A';
    if (modalHarvestDateVal) modalHarvestDateVal.textContent = item.estimated_harvest_date || 'N/A';
    
    if (modalGpsVal) {
      const lat = item.gps_latitude !== null && item.gps_latitude !== undefined ? item.gps_latitude : 'N/A';
      const lng = item.gps_longitude !== null && item.gps_longitude !== undefined ? item.gps_longitude : 'N/A';
      modalGpsVal.textContent = `${lat}° N, ${lng}° E`;
    }

    if (modalStatusBadge) {
      modalStatusBadge.textContent = item.status || 'Active';
    }

    if (modalListingMeta) {
      const dateStr = item.created_at ? item.created_at.split('T')[0] : 'N/A';
      modalListingMeta.textContent = `Listing #${item.listing_id} • Registered ${dateStr}`;
    }

    currentDetailListing = item;

    // Populate Checkout Section (Increment 2 Phase 3)
    if (checkoutSection) {
      if (currentUser && currentUser.role === 'farmer') {
        checkoutSection.innerHTML = `
          <div style="padding: 14px; background: var(--surface-2); border: 1px solid var(--line); border-radius: 12px; font-size: 13px; color: var(--ink-soft); text-align: center; margin-top: 16px;">
            Marketplace Transparency Mode: Procurement ordering is reserved for verified B2B Buyer accounts.
          </div>
        `;
      } else {
        if (checkoutLockedQuantity) {
          checkoutLockedQuantity.value = `${Math.round(item.quantity_kg || 0).toLocaleString('en-US')} kg`;
        }
        if (checkoutTotalCommitment) {
          checkoutTotalCommitment.textContent = formatTotalRs(item.total_price_pkr);
        }
        if (checkoutDestination && !checkoutDestination.value) {
          checkoutDestination.value = (currentUser && (currentUser.warehouse_address || currentUser.company_name)) || '';
        }
        if (checkoutMaxTemp && !checkoutMaxTemp.value) {
          checkoutMaxTemp.value = '6.0';
        }
        if (checkoutAlert) {
          checkoutAlert.classList.add('hidden');
          checkoutAlert.innerHTML = '';
        }
        if (checkoutSuccessState) checkoutSuccessState.classList.add('hidden');
        if (checkoutForm) checkoutForm.classList.remove('hidden');
      }
    }

  } catch (err) {
    console.error('Fetch listing detail error:', err);
    if (detailModalAlert) {
      detailModalAlert.innerHTML = `
        <div style="padding: 12px 14px; background: var(--danger-soft); border: 1px solid var(--danger); border-radius: 10px; color: var(--danger); font-size: 13.5px;">
          Network error retrieving listing details. Please try again.
        </div>
      `;
      detailModalAlert.classList.remove('hidden');
    }
    if (detailModalContent) detailModalContent.classList.add('hidden');
  }
};

function closeDetailModal() {
  if (listingDetailModal) listingDetailModal.classList.add('hidden');
}

if (closeDetailModalBtn) {
  closeDetailModalBtn.addEventListener('click', closeDetailModal);
}

if (closeSuccessModalBtn) {
  closeSuccessModalBtn.addEventListener('click', closeDetailModal);
}

if (listingDetailModal) {
  listingDetailModal.addEventListener('click', (e) => {
    if (e.target === listingDetailModal) closeDetailModal();
  });
}

// =========================================================================
// 5. CHECKOUT CONTROLLER (Contracts Endpoint 5)
// =========================================================================
if (checkoutForm) {
  checkoutForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentDetailListing) return;

    if (checkoutAlert) {
      checkoutAlert.classList.add('hidden');
      checkoutAlert.innerHTML = '';
    }

    const destination = checkoutDestination ? checkoutDestination.value.trim() : '';
    const tempRaw = checkoutMaxTemp ? checkoutMaxTemp.value.trim() : '';
    const tempVal = parseFloat(tempRaw);

    if (!destination || tempRaw === '' || isNaN(tempVal)) {
      showCheckoutAlert('All checkout fields are required.', 'error');
      return;
    }

    if (destination.length < 5) {
      showCheckoutAlert('Destination warehouse must be at least 5 characters.', 'error');
      return;
    }

    if (tempVal < -25.0 || tempVal > 30.0) {
      showCheckoutAlert('Max temperature must be between -25.0°C and 30.0°C.', 'error');
      return;
    }

    setCheckoutBtnLoading(true);

    try {
      const payload = {
        listing_id: currentDetailListing.listing_id || currentDetailListing.id,
        ordered_quantity_kg: parseFloat(currentDetailListing.quantity_kg),
        destination_warehouse: destination,
        max_temperature_celsius: tempVal
      };

      const response = await fetch(`${API_BASE_URL}/orders`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
      });

      const resData = await response.json().catch(() => null);

      if (response.status === 201 && resData && resData.success && resData.data) {
        const order = resData.data;
        const remainingPkr = order.remaining_wallet_balance_pkr !== undefined ? order.remaining_wallet_balance_pkr : 0;

        // Update Header Wallet Display and Session
        if (currentUser) {
          currentUser.wallet_balance_pkr = remainingPkr;
          sessionStorage.setItem('agrigrid_user', JSON.stringify(currentUser));
        }
        if (headerWalletBalance) {
          headerWalletBalance.textContent = formatTotalRs(remainingPkr);
        }

        // Show Success View in Modal
        if (checkoutForm) checkoutForm.classList.add('hidden');
        if (successOrderNumber) successOrderNumber.textContent = order.order_number || `ORD-${order.order_id}`;
        if (successOrderTotal) successOrderTotal.textContent = formatTotalRs(order.total_amount_pkr);
        if (successRemainingBalance) successRemainingBalance.textContent = formatTotalRs(remainingPkr);
        if (checkoutSuccessState) checkoutSuccessState.classList.remove('hidden');

        showToast(resData.message || 'Order created successfully. Escrow funds locked.', 'success');

        // Refresh Catalog (purchased lot is now Sold) and My Orders list
        fetchCatalog(currentPage);
        fetchBuyerOrders(1);

      } else {
        // Contract requirement: Server errors render inline, verbatim
        const errMsg = resData?.error || resData?.message || 'Failed to complete escrow checkout.';
        showCheckoutAlert(errMsg, 'error');
      }
    } catch (err) {
      console.error('Escrow checkout error:', err);
      showCheckoutAlert('Network error connecting to escrow checkout service.', 'error');
    } finally {
      setCheckoutBtnLoading(false);
    }
  });
}

function showCheckoutAlert(message, type = 'error') {
  if (!checkoutAlert) return;
  checkoutAlert.textContent = message;
  checkoutAlert.className = `checkout-alert ${type}`;
  checkoutAlert.classList.remove('hidden');
}

function setCheckoutBtnLoading(isLoading) {
  if (!checkoutSubmitBtn) return;
  checkoutSubmitBtn.disabled = isLoading;
  if (checkoutSpinner) {
    if (isLoading) checkoutSpinner.classList.remove('hidden');
    else checkoutSpinner.classList.add('hidden');
  }
  if (checkoutSubmitBtnText) {
    checkoutSubmitBtnText.textContent = isLoading ? 'Processing...' : 'Lock Escrow & Place Order';
  }
}

// =========================================================================
// 6. BUYER ORDERS SECTION (Contracts Endpoints 6–9)
// =========================================================================
function getBuyerOrderStatusClass(status) {
  const s = (status || '').toLowerCase().replace(/_/g, '-');
  if (s.includes('escrow')) return 'escrow-funded';
  if (s.includes('transit')) return 'in-transit';
  if (s.includes('deliver')) return 'delivered';
  if (s.includes('complet')) return 'completed';
  if (s.includes('cancel')) return 'cancelled';
  if (s.includes('disput')) return 'disputed';
  return 'active';
}

async function fetchBuyerOrders(page = 1) {
  if (!buyerOrdersTableBody) return;
  currentBuyerOrdersPage = page;
  showBuyerOrdersLoading(true);

  try {
    let url = `${API_BASE_URL}/orders/buyer?page=${page}&limit=${buyerOrdersPageSize}`;
    if (currentBuyerOrdersStatus) {
      url += `&status=${encodeURIComponent(currentBuyerOrdersStatus)}`;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders()
    });

    if (response.status === 401) {
      showToast('Session expired. Please log in again.', 'error');
      sessionStorage.removeItem('agrigrid_token');
      setTimeout(() => window.location.replace('index.html'), 1200);
      return;
    }

    if (response.status === 403) {
      showToast('Access denied to procurement orders.', 'error');
      return;
    }

    const resData = await response.json().catch(() => null);

    if (response.ok && resData && resData.success) {
      currentBuyerOrders = resData.data || [];
      totalBuyerOrders = resData.total !== undefined ? resData.total : currentBuyerOrders.length;
      totalBuyerOrdersPages = Math.max(1, Math.ceil(totalBuyerOrders / buyerOrdersPageSize));

      renderBuyerOrdersTable(currentBuyerOrders);
      updateBuyerOrdersPagination();
    } else {
      const err = resData?.error || 'Failed to retrieve procurement orders.';
      showToast(err, 'error');
      renderBuyerOrdersTable([]);
    }
  } catch (err) {
    console.error('Fetch buyer orders error:', err);
    showToast(`Network error reaching ${API_BASE_URL}. Ensure backend is active.`, 'error');
    renderBuyerOrdersTable([]);
  } finally {
    showBuyerOrdersLoading(false);
  }
}

function showBuyerOrdersLoading(isLoading) {
  if (isLoading) {
    if (buyerOrdersLoading) buyerOrdersLoading.classList.remove('hidden');
    if (buyerOrdersEmpty) buyerOrdersEmpty.classList.add('hidden');
  } else {
    if (buyerOrdersLoading) buyerOrdersLoading.classList.add('hidden');
  }
}

function renderBuyerOrdersTable(orders) {
  if (!buyerOrdersTableBody) return;
  buyerOrdersTableBody.innerHTML = '';

  if (buyerOrdersCountBadge) {
    buyerOrdersCountBadge.textContent = `${totalBuyerOrders} Orders`;
  }

  if (!orders || orders.length === 0) {
    if (buyerOrdersEmpty) buyerOrdersEmpty.classList.remove('hidden');
    return;
  }

  if (buyerOrdersEmpty) buyerOrdersEmpty.classList.add('hidden');

  orders.forEach(order => {
    const orderId = order.order_id || order.id;
    const orderNumber = order.order_number || `ORD-${orderId}`;
    const cropName = order.crop_name || 'Produce';
    const batchId = order.batch_id || '—';
    const farmName = order.farm_name || (order.farmer_id ? `Farm #${order.farmer_id}` : 'Verified Farm');
    const qty = parseFloat(order.ordered_quantity_kg) || 0;
    const pricePerKg = parseFloat(order.agreed_price_per_kg) || 0;
    const totalPkr = parseFloat(order.total_amount_pkr) || (qty * pricePerKg);
    const destination = order.destination_warehouse || '—';
    const maxTemp = order.max_temperature_celsius !== undefined && order.max_temperature_celsius !== null 
      ? `${parseFloat(order.max_temperature_celsius).toFixed(1)}°C` 
      : '—';
    const status = order.order_status || 'Escrow_Funded';
    const dateStr = order.created_at ? order.created_at.replace('T', ' ').substring(0, 16) : '—';

    const tr = document.createElement('tr');

    let actionsHtml = '<span class="cell-price-na">—</span>';
    if (status === 'Escrow_Funded') {
      actionsHtml = `
        <div class="action-group">
          <button type="button" class="btn-order-action confirm" onclick="handleBuyerConfirmDelivery(${orderId}, '${escapeHtml(orderNumber)}')">Confirm</button>
          <button type="button" class="btn-order-action cancel" onclick="handleBuyerCancelOrder(${orderId}, '${escapeHtml(orderNumber)}')">Cancel</button>
          <button type="button" class="btn-order-action dispute" onclick="handleBuyerDisputeOrder(${orderId}, '${escapeHtml(orderNumber)}')">Dispute</button>
        </div>
      `;
    }

    tr.innerHTML = `
      <td class="cell-id mono">${escapeHtml(orderNumber)}</td>
      <td>
        <div class="cell-crop">
          <span class="crop-icon">${getCropEmoji(cropName)}</span>
          <div>
            <div class="crop-name">${escapeHtml(cropName)}</div>
            <div class="cell-batch">${escapeHtml(batchId)}</div>
          </div>
        </div>
      </td>
      <td class="crop-name">${escapeHtml(farmName)}</td>
      <td>
        <span class="cell-value">${Math.round(qty).toLocaleString('en-US')}</span>
        <span class="cell-unit">kg</span>
      </td>
      <td class="cell-price">${formatPriceRs(pricePerKg)} / kg</td>
      <td class="cell-price" style="font-weight: 700;">${formatPriceRs(totalPkr)}</td>
      <td class="cell-date" style="max-width: 170px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(destination)}">${escapeHtml(destination)}</td>
      <td class="mono cell-date">${escapeHtml(maxTemp)}</td>
      <td>
        <span class="status ${getBuyerOrderStatusClass(status)}">${escapeHtml(status)}</span>
      </td>
      <td class="cell-date mono">${escapeHtml(dateStr)}</td>
      <td class="cell-actions">${actionsHtml}</td>
    `;

    buyerOrdersTableBody.appendChild(tr);
  });
}

function updateBuyerOrdersPagination() {
  if (buyerOrdersPaginationInfo) {
    const start = totalBuyerOrders === 0 ? 0 : (currentBuyerOrdersPage - 1) * buyerOrdersPageSize + 1;
    const end = Math.min(currentBuyerOrdersPage * buyerOrdersPageSize, totalBuyerOrders);
    buyerOrdersPaginationInfo.textContent = `Showing ${start} to ${end} of ${totalBuyerOrders} orders`;
  }

  if (buyerOrdersPageIndicator) {
    buyerOrdersPageIndicator.textContent = `Page ${currentBuyerOrdersPage} of ${totalBuyerOrdersPages}`;
  }

  if (buyerOrdersPrevBtn) buyerOrdersPrevBtn.disabled = currentBuyerOrdersPage <= 1;
  if (buyerOrdersNextBtn) buyerOrdersNextBtn.disabled = currentBuyerOrdersPage >= totalBuyerOrdersPages;
}

window.handleBuyerConfirmDelivery = async function(orderId, orderNumber) {
  try {
    const resp = await fetch(`${API_BASE_URL}/orders/${orderId}/confirm-delivery`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    const resData = await resp.json().catch(() => null);
    if (resp.ok && resData && resData.success) {
      showToast(resData.message || 'Delivery confirmed and escrow funds released to farmer.', 'success');
      fetchBuyerOrders(currentBuyerOrdersPage);
    } else {
      const err = resData?.error || resData?.message || 'Failed to confirm delivery.';
      showToast(err, 'error');
      fetchBuyerOrders(currentBuyerOrdersPage);
    }
  } catch (e) {
    console.error('Confirm delivery error:', e);
    showToast('Network error while confirming delivery.', 'error');
    fetchBuyerOrders(currentBuyerOrdersPage);
  }
};

window.handleBuyerCancelOrder = async function(orderId, orderNumber) {
  if (!window.confirm(`Are you sure you want to cancel order ${orderNumber}? Escrow funds will be refunded to your wallet.`)) {
    return;
  }
  try {
    const resp = await fetch(`${API_BASE_URL}/orders/${orderId}/cancel`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    const resData = await resp.json().catch(() => null);
    if (resp.ok && resData && resData.success) {
      const refunded = resData.data?.refunded_amount_pkr || 0;
      if (currentUser) {
        currentUser.wallet_balance_pkr = (currentUser.wallet_balance_pkr || 0) + refunded;
        sessionStorage.setItem('agrigrid_user', JSON.stringify(currentUser));
      }
      if (headerWalletBalance) {
        const cur = currentUser ? currentUser.wallet_balance_pkr : (parseFloat(headerWalletBalance.textContent.replace(/[^\d.]/g, '')) || 0);
        headerWalletBalance.textContent = formatTotalRs(cur);
      }
      showToast(resData.message || 'Order cancelled successfully. Funds refunded and crop restored to catalog.', 'success');
      fetchBuyerOrders(currentBuyerOrdersPage);
      fetchCatalog(currentPage);
    } else {
      const err = resData?.error || resData?.message || 'Failed to cancel order.';
      showToast(err, 'error');
      fetchBuyerOrders(currentBuyerOrdersPage);
    }
  } catch (e) {
    console.error('Cancel order error:', e);
    showToast('Network error while cancelling order.', 'error');
    fetchBuyerOrders(currentBuyerOrdersPage);
  }
};

window.handleBuyerDisputeOrder = async function(orderId, orderNumber) {
  if (!window.confirm(`Are you sure you want to flag a formal dispute on order ${orderNumber}? Escrow funds will be frozen.`)) {
    return;
  }
  try {
    const resp = await fetch(`${API_BASE_URL}/orders/${orderId}/dispute`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    const resData = await resp.json().catch(() => null);
    if (resp.ok && resData && resData.success) {
      showToast(resData.message || 'Dispute registered. Escrow funds have been frozen.', 'success');
      fetchBuyerOrders(currentBuyerOrdersPage);
    } else {
      const err = resData?.error || resData?.message || 'Failed to dispute order.';
      showToast(err, 'error');
      fetchBuyerOrders(currentBuyerOrdersPage);
    }
  } catch (e) {
    console.error('Dispute order error:', e);
    showToast('Network error while disputing order.', 'error');
    fetchBuyerOrders(currentBuyerOrdersPage);
  }
};

// =========================================================================
// 5. TOAST NOTIFICATION UTILITY
// =========================================================================
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  const toastClass = type === 'error' ? 'toast-banner toast-error' : 'toast-banner toast-success';
  toast.className = toastClass;

  const iconSvg = type === 'error'
    ? `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24" class="flex-shrink-0">
         <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
       </svg>`
    : `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24" class="flex-shrink-0">
         <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
       </svg>`;

  toast.innerHTML = `
    <div class="toast-content">
      ${iconSvg}
      <div class="toast-text">${escapeHtml(message)}</div>
    </div>
    <button type="button" class="toast-dismiss" aria-label="Dismiss notification">
      <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
      </svg>
    </button>
  `;

  const dismissBtn = toast.querySelector('.toast-dismiss');
  if (dismissBtn) {
    dismissBtn.addEventListener('click', () => toast.remove());
  }

  container.appendChild(toast);
  setTimeout(() => {
    if (toast.parentElement) toast.remove();
  }, 4000);
}

// =========================================================================
// 6. EVENT LISTENERS & INITIALIZATION
// =========================================================================
document.addEventListener('DOMContentLoaded', () => {
  initHeaderProfile();
  fetchCatalog(1);

  if (applyFiltersBtn) {
    applyFiltersBtn.addEventListener('click', () => fetchCatalog(1));
  }

  if (filterCropName) {
    filterCropName.addEventListener('change', () => fetchCatalog(1));
  }

  if (filterSort) {
    filterSort.addEventListener('change', () => fetchCatalog(1));
  }

  if (filterMaxPrice) {
    filterMaxPrice.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') fetchCatalog(1);
    });
  }

  if (resetFiltersBtn) {
    resetFiltersBtn.addEventListener('click', () => {
      if (filterCropName) filterCropName.value = '';
      if (filterMaxPrice) filterMaxPrice.value = '';
      if (filterSort) filterSort.value = 'date_desc';
      fetchCatalog(1);
    });
  }

  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener('click', () => {
      if (filterCropName) filterCropName.value = '';
      if (filterMaxPrice) filterMaxPrice.value = '';
      if (filterSort) filterSort.value = 'date_desc';
      fetchCatalog(1);
    });
  }

  if (catalogPrevBtn) {
    catalogPrevBtn.addEventListener('click', () => {
      if (currentPage > 1) fetchCatalog(currentPage - 1);
    });
  }

  if (catalogNextBtn) {
    catalogNextBtn.addEventListener('click', () => {
      if (currentPage < totalPages) fetchCatalog(currentPage + 1);
    });
  }

  // Fetch Buyer Orders (Increment 2 Phase 3)
  fetchBuyerOrders(1);

  // Status Filter Chips for Buyer Orders
  const buyerChips = [
    buyerChipAll,
    buyerChipEscrowFunded,
    buyerChipInTransit,
    buyerChipDelivered,
    buyerChipCompleted,
    buyerChipCancelled,
    buyerChipDisputed
  ];

  buyerChips.forEach(chip => {
    if (chip) {
      chip.addEventListener('click', () => {
        buyerChips.forEach(c => c && c.classList.remove('active'));
        chip.classList.add('active');
        currentBuyerOrdersStatus = chip.getAttribute('data-status') || '';
        fetchBuyerOrders(1);
      });
    }
  });

  // Pagination for Buyer Orders
  if (buyerOrdersPrevBtn) {
    buyerOrdersPrevBtn.addEventListener('click', () => {
      if (currentBuyerOrdersPage > 1) fetchBuyerOrders(currentBuyerOrdersPage - 1);
    });
  }

  if (buyerOrdersNextBtn) {
    buyerOrdersNextBtn.addEventListener('click', () => {
      if (currentBuyerOrdersPage < totalBuyerOrdersPages) fetchBuyerOrders(currentBuyerOrdersPage + 1);
    });
  }
});
