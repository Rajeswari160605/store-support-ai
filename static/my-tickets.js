// 🔥 COMPLETE FIXED my-tickets.js - Store2 Works 100%
document.addEventListener('DOMContentLoaded', function() {
    // Kill loaders instantly
    const style = document.createElement('style');
    style.id = 'kill-loaders';
    style.textContent = `
        * { animation-duration: 0s !important; animation-iteration-count: 1 !important; }
        .animate-spin, .animate-pulse, .loading, .spinner, [class*="animate-"] { 
            animation: none !important; animation-duration: 0s !important; background: transparent !important;
        }
        .skeleton, .loading-skeleton, .skeleton-row { display: none !important; }
    `;
    document.head.appendChild(style);
    
    document.querySelectorAll('.skeleton-row, .loading, .spinner').forEach(el => el.remove());
    
    initMyTickets();
});

let allTickets = [];

// 🔥 UNIVERSAL TOKEN FETCH - ALL API CALLS
async function apiFetch(endpoint) {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/'; // Relogin
        throw new Error('No token');
    }
    
    const res = await fetch(endpoint, {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });
    
    if (!res.ok) {
        if (res.status === 401) window.location.href = '/';
        throw new Error(`API ${res.status}`);
    }
    return res.json();
}

function initMyTickets() {
    const searchInput = document.getElementById('searchInput');
    let currentFilter = 'All';

    // 🔥 TOKENIZED LOAD - Store2 Fixed
    apiFetch('/api/my-tickets')
        .then(data => {
            document.getElementById('storeName').textContent = data.store_name;
            allTickets = data.tickets || [];
            updateCounts();
            displayTickets(allTickets);
        })
        .catch(err => {
            console.error('Load failed:', err);
            document.getElementById('ticketsList').innerHTML = `
                <div class="py-16 text-center text-red-500">
                    <i class="fas fa-exclamation-triangle text-4xl mb-4"></i>
                    <p>Session expired - <a href="/" class="underline font-bold">Login Again</a></p>
                </div>
            `;
        });

    // Tab filters
    document.querySelectorAll('.tab').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.tab').forEach(b => b.classList.remove('bg-indigo-600', 'text-white'));
            e.target.classList.add('bg-indigo-600', 'text-white');
            currentFilter = e.target.dataset.status;
            applyFilters();
        });
    });

    // Search debounce
    searchInput.addEventListener('input', (e) => {
        clearTimeout(window.searchTimeout);
        window.searchTimeout = setTimeout(applyFilters, 300);
    });

    function applyFilters() {
        let filtered = allTickets.filter(t => t.status === currentFilter || currentFilter === 'All');
        const search = searchInput.value.toLowerCase();
        filtered = filtered.filter(t => 
            (t.ticket_number || '').toLowerCase().includes(search) ||
            (t.description || '').toLowerCase().includes(search)
        );
        displayTickets(filtered);
    }

    function updateCounts() {
        const counts = { All: 0, Open: 0, 'In Progress': 0, Closed: 0, Resolved: 0 };
        allTickets.forEach(t => {
            const status = t.status?.trim();
            if (status) counts[status] = (counts[status] || 0) + 1;
            counts.All += 1;
        });
        document.getElementById('allCount').textContent = `(${counts.All})`;
        document.getElementById('openCount').textContent = `(${counts.Open})`;
        document.getElementById('progressCount').textContent = `(${counts['In Progress']})`;
        document.getElementById('closedCount').textContent = `(${counts.Closed + counts.Resolved})`;
    }

    function displayTickets(tickets) {
        const container = document.getElementById('ticketsList');
        container.innerHTML = tickets.length ? `
            <div class="overflow-x-auto border border-gray-200 rounded-xl shadow-sm">
                <table class="w-full">
                    <thead>
                        <tr class="bg-gradient-to-r from-[#667eea] via-[#764ba2] to-[#f093fb]">
                            <th class="px-6 py-4 text-left text-white font-bold text-sm uppercase tracking-wider w-20">TICKET #</th>
                            <th class="px-6 py-4 text-left text-white font-bold text-sm uppercase tracking-wider flex-1 min-w-[250px]">DESCRIPTION</th>
                            <th class="px-6 py-4 text-center text-white font-bold text-sm uppercase tracking-wider w-28">STATUS</th>
                            <th class="px-6 py-4 text-left text-white font-bold text-sm uppercase tracking-wider w-24">DEPT</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
                        ${tickets.map(ticket => `
                            <tr class="hover:bg-gray-50/50 h-16 ${getStatusRowClass(ticket.status)}">
                                <td class="px-6 py-4 font-bold text-lg">${ticket.ticket_number}</td>
                                <td class="px-6 py-4 text-gray-800">${ticket.description}</td>
                                <td class="px-6 py-4 text-center">
                                    <span class="${getStatusBadgeClass(ticket.status)} px-4 py-2 rounded-lg font-bold text-xs uppercase mx-auto block w-fit">
                                        ${ticket.status}
                                    </span>
                                </td>
                                <td class="px-6 py-4 font-semibold flex items-center">
                                    <div class="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                                    ${ticket.department}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        ` : '<div class="py-16 text-center text-gray-500 text-lg">No tickets for this store</div>';
    }

    function getStatusBadgeClass(status) {
        return {
            'Open': 'bg-emerald-500 text-white', 
            'In Progress': 'bg-amber-400 text-gray-900', 
            'Resolved': 'bg-emerald-500 text-white', 
            'Closed': 'bg-gray-400 text-white'
        }[status] || 'bg-gray-400 text-white';
    }

    function getStatusRowClass(status) {
        return {
            'Open': 'border-l-4 border-emerald-400 bg-emerald-50/30', 
            'In Progress': 'border-l-4 border-amber-400 bg-amber-50/30',
            'Resolved': 'border-l-4 border-emerald-400 bg-emerald-50/30',
            'Closed': 'border-l-4 border-gray-400 bg-gray-50'
        }[status] || '';
    }
}
