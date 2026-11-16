/**
 * AgriGrid — Farmer Inbound Orders & Settlement Management
 * Handles inbound order tracking, cancellation/dispute actions, and wallet updates.
 */

const API_BASE_URL = 'http://127.0.0.1:5000/api';

// Auth Guard: Validate session exists and belongs to a farmer
const token = sessionStorage.getItem('agrigrid_token');
const userJson = sessionStorage.getItem('agrigrid_user');

if (!token || !userJson) {
  window.location.replace('index.html');
}

let currentUser = null;
try {
  currentUser = JSON.parse(userJson);
} catch (e) {
  sessionStorage.removeItem('agrigrid_token');
  sessionStorage.removeItem('agrigrid_user');
  window.location.replace('index.html');
}

if (currentUser && currentUser.role === 'buyer') {
  window.location.replace('buyer_dashboard.html');
} else if (currentUser && currentUser.role !== 'farmer') {
  window.location.replace('index.html');
}

function getAuthHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${sessionStorage.getItem('agrigrid_token')}`
  };
}

// DOM Elements: Navigation & Identity
const navFarmerConsole = document.getElementById('navFarmerConsole');
const navFarmerOrders = document.getElementById('navFarmerOrders');
const navMarketplaceLink = document.getElementById('navMarketplaceLink');
const farmerWalletPill = document.getElementById('farmerWalletPill');
const farmerWalletBalance = document.getElementById('farmerWalletBalance');
const headerFarmNameDisplay = document.getElementById('headerFarmNameDisplay');
const headerFarmLocation = document.getElementById('headerFarmLocation');
const headerUsername = document.getElementById('headerUsername');
const userAvatar = document.getElementById('userAvatar');
const logoutBtn = document.getElementById('logoutBtn');
const toastContainer = document.getElementById('toastContainer');

// DOM Elements: Farmer Inbound Orders Table & Controls
const incomingOrdersSection = document.getElementById('incomingOrdersSection');
const incomingOrdersHeading = document.getElementById('incomingOrdersHeading');
const farmerOrdersTable = document.getElementById('farmerOrdersTable');
const farmerOrdersTableBody = document.getElementById('farmerOrdersTableBody');
const farmerOrdersEmpty = document.getElementById('farmerOrdersEmpty');
const farmerOrdersLoading = document.getElementById('farmerOrdersLoading');
const farmerOrdersCountBadge = document.getElementById('farmerOrdersCountBadge');
const farmerOrdersPaginationInfo = document.getElementById('farmerOrdersPaginationInfo');
const farmerOrdersPageIndicator = document.getElementById('farmerOrdersPageIndicator');
const farmerOrdersPrevBtn = document.getElementById('farmerOrdersPrevBtn');
const farmerOrdersNextBtn = document.getElementById('farmerOrdersNextBtn');

// Status Filter Chips
const farmerChipAll = document.getElementById('farmerChipAll');
const farmerChipEscrowFunded = document.getElementById('farmerChipEscrowFunded');
const farmerChipInTransit = document.getElementById('farmerChipInTransit');
const farmerChipDelivered = document.getElementById('farmerChipDelivered');
const farmerChipCompleted = document.getElementById('farmerChipCompleted');
const farmerChipCancelled = document.getElementById('farmerChipCancelled');
const farmerChipDisputed = document.getElementById('farmerChipDisputed');

const farmerChips = [
  farmerChipAll,
  farmerChipEscrowFunded,
  farmerChipInTransit,
  farmerChipDelivered,
  farmerChipCompleted,
  farmerChipCancelled,
  farmerChipDisputed
];

// State Variables
let currentFarmerOrders = [];
let currentFarmerOrdersPage = 1;
const farmerOrdersPageSize = 20;
let totalFarmerOrders = 0;
let totalFarmerOrdersPages = 1;
let currentFarmerOrdersStatus = '';

// Helper Functions
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatPriceRs(val) {
  const num = parseFloat(val) || 0;
  return `Rs ${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function showToast(message, type = 'info') {
  if (!toastContainer) return;
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.setAttribute('role', 'alert');

  let icon = `
    <svg class="flex-shrink-0" width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
    </svg>`;
  if (type === 'success') {
    icon = `
      <svg class="flex-shrink-0" width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
      </svg>`;
  } else if (type === 'error') {
    icon = `
      <svg class="flex-shrink-0" width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
      </svg>`;
  }

  toast.innerHTML = `
    ${icon}
    <div class="toast-body">${escapeHtml(message)}</div>
    <button type="button" class="toast-close" aria-label="Close">&times;</button>
  `;

  toast.querySelector('.toast-close').addEventListener('click', () => toast.remove());
  toastContainer.appendChild(toast);
  setTimeout(() => {
    if (toast.parentElement) toast.remove();
  }, 4500);
}

function handleLogout() {
  sessionStorage.removeItem('agrigrid_token');
  sessionStorage.removeItem('agrigrid_user');
  window.location.replace('index.html');
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
    const farmName = currentUser.farm_name || currentUser.farm || (currentUser.farmer_id ? `Farm Node #${currentUser.farmer_id}` : 'Verified Farm Node');

    if (headerUsername) headerUsername.textContent = username;
    if (headerFarmNameDisplay) headerFarmNameDisplay.textContent = farmName;
    if (userAvatar) userAvatar.textContent = username.charAt(0).toUpperCase();
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
      const formatted = Number(data.data.balance_pkr).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });
      farmerWalletBalance.textContent = `Rs ${formatted}`;
    } else {
      farmerWalletBalance.textContent = 'Rs —';
    }
  } catch (e) {
    farmerWalletBalance.textContent = 'Rs —';
  }
}

function setupEventListeners() {
  if (logoutBtn) {
    logoutBtn.addEventListener('click', handleLogout);
  }

  // Farmer Inbound Order Status Filter Chips
  farmerChips.forEach(chip => {
    if (chip) {
      chip.addEventListener('click', () => {
        farmerChips.forEach(c => c && c.classList.remove('active'));
        chip.classList.add('active');
        currentFarmerOrdersStatus = chip.getAttribute('data-status') || '';
        loadFarmerOrders(1);
      });
    }
  });

  // Farmer Inbound Orders Pagination
  if (farmerOrdersPrevBtn) {
    farmerOrdersPrevBtn.addEventListener('click', () => {
      if (currentFarmerOrdersPage > 1) loadFarmerOrders(currentFarmerOrdersPage - 1);
    });
  }
  if (farmerOrdersNextBtn) {
    farmerOrdersNextBtn.addEventListener('click', () => {
      if (currentFarmerOrdersPage < totalFarmerOrdersPages) loadFarmerOrders(currentFarmerOrdersPage + 1);
    });
  }
}

function getOrderStatusClass(status) {
  const norm = (status || '').toLowerCase().trim();
  if (norm === 'escrow_funded') return 'escrow-funded';
  if (norm === 'in_transit') return 'in-transit';
  if (norm === 'delivered') return 'delivered';
  if (norm === 'completed') return 'completed';
  if (norm === 'cancelled') return 'cancelled';
  if (norm === 'disputed') return 'disputed';
  return 'active';
}

async function loadFarmerOrders(page = 1) {
  if (!farmerOrdersTableBody) return;
  currentFarmerOrdersPage = page;
  showFarmerOrdersLoading(true);

  try {
    let url = `${API_BASE_URL}/orders/farmer?page=${page}&limit=${farmerOrdersPageSize}`;
    if (currentFarmerOrdersStatus) {
      url += `&status=${encodeURIComponent(currentFarmerOrdersStatus)}`;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    const resData = await response.json().catch(() => null);

    if (response.ok && resData && resData.success) {
      currentFarmerOrders = resData.data || [];
      totalFarmerOrders = resData.total !== undefined ? resData.total : currentFarmerOrders.length;
      totalFarmerOrdersPages = Math.max(1, Math.ceil(totalFarmerOrders / farmerOrdersPageSize));

      renderFarmerOrdersTable(currentFarmerOrders);
      updateFarmerOrdersPagination();
    } else {
      const err = resData?.error || 'Failed to retrieve inbound orders.';
      showToast(err, 'error');
      renderFarmerOrdersTable([]);
    }
  } catch (err) {
    console.error('Load farmer orders error:', err);
    showToast(`Network error reaching ${API_BASE_URL}. Ensure backend is active.`, 'error');
    renderFarmerOrdersTable([]);
  } finally {
    showFarmerOrdersLoading(false);
    fetchFarmerWallet();
  }
}

function showFarmerOrdersLoading(isLoading) {
  if (isLoading) {
    if (farmerOrdersLoading) farmerOrdersLoading.classList.remove('hidden');
    if (farmerOrdersEmpty) farmerOrdersEmpty.classList.add('hidden');
  } else {
    if (farmerOrdersLoading) farmerOrdersLoading.classList.add('hidden');
  }
}

function renderFarmerOrdersTable(orders) {
  if (!farmerOrdersTableBody) return;
  farmerOrdersTableBody.innerHTML = '';

  if (farmerOrdersCountBadge) {
    farmerOrdersCountBadge.textContent = `${totalFarmerOrders} Orders`;
  }

  if (!orders || orders.length === 0) {
    if (farmerOrdersEmpty) farmerOrdersEmpty.classList.remove('hidden');
    return;
  }

  if (farmerOrdersEmpty) farmerOrdersEmpty.classList.add('hidden');

  orders.forEach(order => {
    const orderId = order.order_id || order.id;
    const orderNumber = order.order_number || `#ORD-${orderId}`;
    const buyerName = order.buyer_name || order.buyer_company || `Buyer #${order.buyer_id}`;
    const cropName = order.crop_name || order.crop_type || 'Crop';
    const batchId = order.batch_id || `BATCH-${order.listing_id || '0'}`;
    const qtyKg = parseFloat(order.quantity_kg || 0).toLocaleString();
    const unitPrice = formatPriceRs(order.unit_price_pkr);
    const totalPrice = formatPriceRs(order.total_price_pkr);
    const dest = order.delivery_address || order.destination || 'Mandi Terminal';
    const maxTemp = order.max_temp_celsius !== undefined && order.max_temp_celsius !== null
      ? `${order.max_temp_celsius}°C`
      : 'Standard';
    const status = order.status || 'Escrow_Funded';
    const statusClass = getOrderStatusClass(status);
    const createdDate = order.created_at ? order.created_at.split('T')[0] : 'Today';

    const canCancel = (status === 'Escrow_Funded');
    const canDispute = (status === 'Delivered' || status === 'In_Transit');

    let actionsHtml = '';
    if (canCancel) {
      actionsHtml += `<button type="button" class="btn small btn-cancel-order" onclick="handleFarmerCancelOrder(${orderId}, '${escapeHtml(orderNumber)}')">Cancel</button>`;
    }
    if (canDispute) {
      actionsHtml += `<button type="button" class="btn small btn-dispute-order" onclick="handleFarmerDisputeOrder(${orderId}, '${escapeHtml(orderNumber)}')">Dispute</button>`;
    }
    if (!actionsHtml) {
      actionsHtml = '<span class="cell-price-na">—</span>';
    }

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="cell-mono" style="font-weight: 600;">${escapeHtml(orderNumber)}</td>
      <td style="font-weight: 500;">${escapeHtml(buyerName)}</td>
      <td>
        <div style="font-weight: 600; color: var(--clay);">${escapeHtml(cropName)}</div>
        <div class="cell-mono" style="font-size: 11px; color: var(--ink-soft);">${escapeHtml(batchId)}</div>
      </td>
      <td>${qtyKg} kg</td>
      <td class="cell-mono">${unitPrice}</td>
      <td class="cell-mono" style="font-weight: 600;">${totalPrice}</td>
      <td style="max-width: 140px; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(dest)}">${escapeHtml(dest)}</td>
      <td><span class="cell-mono badge-temp">${escapeHtml(maxTemp)}</span></td>
      <td><span class="status-badge status-${statusClass}">${escapeHtml(status)}</span></td>
      <td class="cell-mono" style="font-size: 12px;">${escapeHtml(createdDate)}</td>
      <td class="cell-actions">${actionsHtml}</td>
    `;

    farmerOrdersTableBody.appendChild(tr);
  });
}

function updateFarmerOrdersPagination() {
  if (farmerOrdersPaginationInfo) {
    const start = totalFarmerOrders === 0 ? 0 : (currentFarmerOrdersPage - 1) * farmerOrdersPageSize + 1;
    const end = Math.min(currentFarmerOrdersPage * farmerOrdersPageSize, totalFarmerOrders);
    farmerOrdersPaginationInfo.textContent = `Showing ${start} to ${end} of ${totalFarmerOrders} orders`;
  }

  if (farmerOrdersPageIndicator) {
    farmerOrdersPageIndicator.textContent = `Page ${currentFarmerOrdersPage} of ${totalFarmerOrdersPages}`;
  }

  if (farmerOrdersPrevBtn) farmerOrdersPrevBtn.disabled = currentFarmerOrdersPage <= 1;
  if (farmerOrdersNextBtn) farmerOrdersNextBtn.disabled = currentFarmerOrdersPage >= totalFarmerOrdersPages;
}

window.handleFarmerCancelOrder = async function(orderId, orderNumber) {
  if (!confirm(`Are you sure you want to cancel inbound order ${orderNumber}?\nEscrow funds will be refunded to the buyer and the listing inventory restored.`)) {
    return;
  }

  try {
    const resp = await fetch(`${API_BASE_URL}/orders/${orderId}/cancel`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ reason: 'Farmer rejected or unable to fulfill order' })
    });
    const resData = await resp.json().catch(() => null);
    if (resp.ok && resData && resData.success) {
      showToast(resData.message || 'Order cancelled successfully. Funds refunded and crop restored to catalog.', 'success');
      loadFarmerOrders(currentFarmerOrdersPage);
      fetchFarmerWallet();
    } else {
      const err = resData?.error || resData?.message || 'Failed to cancel order.';
      showToast(err, 'error');
      loadFarmerOrders(currentFarmerOrdersPage);
    }
  } catch (e) {
    console.error('Cancel order error:', e);
    showToast('Network error while cancelling order.', 'error');
    loadFarmerOrders(currentFarmerOrdersPage);
  }
};

window.handleFarmerDisputeOrder = async function(orderId, orderNumber) {
  const reason = prompt(`Dispute Order ${orderNumber}:\nPlease describe the reason for disputing this delivery:`);
  if (!reason || !reason.trim()) return;

  try {
    const resp = await fetch(`${API_BASE_URL}/orders/${orderId}/dispute`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ reason: reason.trim() })
    });
    const resData = await resp.json().catch(() => null);
    if (resp.ok && resData && resData.success) {
      showToast(resData.message || 'Dispute registered. Escrow funds have been frozen.', 'success');
      loadFarmerOrders(currentFarmerOrdersPage);
      fetchFarmerWallet();
    } else {
      const err = resData?.error || resData?.message || 'Failed to dispute order.';
      showToast(err, 'error');
      loadFarmerOrders(currentFarmerOrdersPage);
    }
  } catch (e) {
    console.error('Dispute order error:', e);
    showToast('Network error while disputing order.', 'error');
    loadFarmerOrders(currentFarmerOrdersPage);
  }
};

// Lifecycle Initialization
document.addEventListener('DOMContentLoaded', () => {
  initUserProfile();
  setupEventListeners();
  fetchFarmerWallet();
  loadFarmerOrders(1);
});
