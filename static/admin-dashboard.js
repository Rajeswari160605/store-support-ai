// static/admin-dashboard.js - FULL WORKING VERSION
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Health & Glow Admin Dashboard - LIVE');
    
    // Load Overview Stats
    await loadStats();
    
    // Load Tickets Table (Overview)
    await loadTickets();
    
    // Load Support Groups (when tab clicked)
    setupNavigation();
    
    // Search & Filter
    setupSearchFilter();
});

async function loadStats() {
    try {
        const response = await fetch('/api/admin/stats');
        const stats = await response.json();
        
        // FIXED - Multiple ID formats (camelCase OR kebab-case)
        updateElementText('totalTickets', stats.totalTickets);
        updateElementText('openTickets', stats.openTickets);
        updateElementText('resolvedTickets', stats.resolvedTickets);
        updateElementText('totalStores', stats.totalStores);
        
        console.log('✅ Stats LIVE:', stats);
    } catch (error) {
        console.error('❌ Stats failed:', error);
    }
}

function updateElementText(id, value) {
    // Try multiple ID formats
    const selectors = [`#${id}`, `#${id.replace(/([A-Z])/g, '-$1').toLowerCase()}`, `[id*="${id}"]`];
    for (let selector of selectors) {
        const el = document.querySelector(selector);
        if (el) {
            el.textContent = value;
            return;
        }
    }
    console.warn(`⚠️ Element not found: ${id}`);
}

async function loadTickets(search = '', status = 'All') {
    try {
        const url = `/api/admin/tickets?search=${encodeURIComponent(search)}&status_filter=${status}`;
        const response = await fetch(url);
        const tickets = await response.json();
        
        updateTicketsTable(tickets);
        console.log('✅ Tickets loaded:', tickets.length);
    } catch (error) {
        console.error('❌ Tickets error:', error);
    }
}

function updateTicketsTable(tickets) {
    const tbody = document.getElementById('ticketsTableBody') || 
                  document.querySelector('tbody') ||
                  document.querySelector('#tickets-table-body');
    
    if (!tbody) {
        console.error('❌ Table body not found');
        return;
    }
    
    if (tickets.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center p-4"><em>No tickets found</em></td></tr>';
        return;
    }
    
    tbody.innerHTML = tickets.map(ticket => `
        <tr>
            <td><strong>#${ticket.ticket_number || ticket.id}</strong></td>
            <td>${ticket.store_id || 'N/A'}</td>
            <td>${ticket.city || 'Bengaluru'}</td>
            <td>
                <strong>${ticket.title || ticket.category}</strong>
                <br><small>${ticket.description}</small>
            </td>
            <td><span class="badge priority-${ticket.priority?.toLowerCase()}">${ticket.priority}</span></td>
            <td><span class="badge status-${ticket.status?.toLowerCase().replace(/\s+/g, '-')}">${ticket.status}</span></td>
            <td>${ticket.department || 'Operations'}</td>
            <td>
                <button class="btn btn-sm btn-success assign-btn" data-ticket-id="${ticket.id}">
                    <i class="fas fa-user-plus"></i> Assign
                </button>
            </td>
        </tr>
    `).join('');
}

function setupSearchFilter() {
    const searchInput = document.querySelector('.search-input');
    const filterSelect = document.querySelector('.filter-select');
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => loadTickets(searchInput.value), 300));
    }
    if (filterSelect) {
        filterSelect.addEventListener('change', () => loadTickets('', filterSelect.value));
    }
}

function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', async function(e) {
            e.preventDefault();
            
            // Update active nav
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // Show section
            const section = this.dataset.section;
            document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
            document.getElementById(section)?.classList.add('active');
            
            // Load Support Groups
            if (section === 'support-groups') {
                await loadSupportGroups();
            }
        });
    });
}

async function loadSupportGroups() {
    try {
        const response = await fetch('/api/admin/groups');
        const groups = await response.json();
        
        const list = document.getElementById('groupsList');
        const count = document.getElementById('groupsCount');
        
        if (!list) return console.error('❌ groupsList not found');
        
        if (groups.length === 0) {
            list.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users-slash"></i>
                    <p>No support groups yet. Create your first group!</p>
                </div>
            `;
        } else {
            list.innerHTML = groups.map(g => `
                <div class="group-card">
                    <div class="group-header">
                        <h4>${g.group_name}</h4>
                        <span class="group-badge">${g.category}</span>
                    </div>
                    <div>Store: <strong>${g.store_id}</strong></div>
                    <div>Members: <strong>${g.member_count || JSON.parse(g.members).length}</strong></div>
                </div>
            `).join('');
        }
        
        if (count) count.textContent = groups.length;
        console.log('✅ Groups loaded:', groups.length);
    } catch (error) {
        console.error('❌ Groups error:', error);
    }
}

function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}
