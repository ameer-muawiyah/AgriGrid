/**
 * AgriGrid — Buyer Orders Controller
 * Dedicated orders management page for buyers.
 */

const API_BASE_URL = 'http://127.0.0.1:5000/api';

// =========================================================================
// 1. AUTH GUARD & SESSION VALIDATION (PD-R2)
// =========================================================================
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

if (currentUser && currentUser.role === 'farmer') {
  window.location.replace('dashboard.html');
} else if (currentUser && currentUser.role !== 'buyer') {
  window.location.replace('index.html');
}

function getAuthHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${sessionStorage.getItem('agrigrid_token')}`
  };
}

// DOM Elements: Identity & Navigation
const headerCompanyNameDisplay = document.getElementById('headerCompanyNameDisplay');
const headerLocationDisplay = document.getElementById('headerLocationDisplay');
const headerRoleBadge = document.getElementById('headerRoleBadge');
const headerWalletBalance = document.getElementById('headerWalletBalance');
const headerWalletPill = document.getElementById('headerWalletPill');
const buyerAvatar = document.getElementById('buyerAvatar');
const buyerLogoutBtn = document.getElementById('buyerLogoutBtn');

const buyerNavMarketplace = document.getElementById('buyerNavMarketplace');
const buyerNavOrders = document.getElementById('buyerNavOrders');
const toastContainer = document.getElementById('toastContainer');

// DOM Elements: Buyer Orders Table & Controls
const buyerOrdersTable = document.getElementById('buyerOrdersTable');
const buyerOrdersTableBody = document.getElementById('buyerOrdersTableBody');
const buyerOrdersEmpty = document.getElementById('buyerOrdersEmpty');
const buyerOrdersLoading = document.getElementById('buyerOrdersLoading');
const buyerOrdersCountBadge = document.getElementById('buyerOrdersCountBadge');
const buyerOrdersPaginationInfo = document.getElementById('buyerOrdersPaginationInfo');
const buyerOrdersPageIndicator = document.getElementById('buyerOrdersPageIndicator');
const buyerOrdersPrevBtn = document.getElementById('buyerOrdersPrevBtn');
const buyerOrdersNextBtn = document.getElementById('buyerOrdersNextBtn');

// Status Filter Chips
const buyerChipAll = document.getElementById('buyerChipAll');
const buyerChipEscrowFunded = document.getElementById('buyerChipEscrowFunded');
const buyerChipInTransit = document.getElementById('buyerChipInTransit');
const buyerChipDelivered = document.getElementById('buyerChipDelivered');
const buyerChipCompleted = document.getElementById('buyerChipCompleted');
const buyerChipCancelled = document.getElementById('buyerChipCancelled');
const buyerChipDisputed = document.getElementById('buyerChipDisputed');

const buyerChips = [
  buyerChipAll,
  buyerChipEscrowFunded,
  buyerChipInTransit,
  buyerChipDelivered,
  buyerChipCompleted,
  buyerChipCancelled,
  buyerChipDisputed
];

// State Variables
let currentBuyerOrders = [];
let currentBuyerOrdersPage = 1;
const buyerOrdersPageSize = 20;
let totalBuyerOrders = 0;
let totalBuyerOrdersPages = 1;
let currentBuyerOrdersStatus = '';

// Crop Taxonomy & Emojis
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

function initHeaderProfile() {
  if (!currentUser) return;

  const role = currentUser.role || 'buyer';
  if (role === 'buyer') {
    if (buyerNavMarketplace) buyerNavMarketplace.classList.remove('hidden');
    if (buyerNavOrders) buyerNavOrders.classList.remove('hidden');

    const company = currentUser.company_name || currentUser.username || 'My Company';
    if (headerCompanyNameDisplay) headerCompanyNameDisplay.textContent = company;
    if (headerLocationDisplay) headerLocationDisplay.textContent = '';
    if (headerRoleBadge) headerRoleBadge.textContent = 'Buyer';

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
    const farmName = order.farm_name || (order.farmer_id ? `Farm #${order.farmer_id}` : 'Farm');
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

// Initialization
document.addEventListener('DOMContentLoaded', () => {
  initHeaderProfile();
  fetchBuyerOrders(1);

  // Status Filter Chips for Buyer Orders
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
