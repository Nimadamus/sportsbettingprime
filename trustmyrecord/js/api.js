// TrustMyRecord API Handler
const TMR_API = {
    baseUrl: '/trustmyrecord/api',

    // Fetch all handicappers
    async getHandicappers() {
        try {
            const response = await fetch(`${this.baseUrl}/handicappers.json`);
            if (!response.ok) throw new Error('Failed to fetch handicappers');
            return await response.json();
        } catch (error) {
            console.error('Error fetching handicappers:', error);
            return { handicappers: [], lastUpdated: null };
        }
    },

    // Fetch selections for a specific handicapper
    async getSelections(handicapperId) {
        try {
            const response = await fetch(`${this.baseUrl}/selections/${handicapperId}.json`);
            if (!response.ok) throw new Error(`Failed to fetch selections for ${handicapperId}`);
            return await response.json();
        } catch (error) {
            console.error(`Error fetching selections for ${handicapperId}:`, error);
            return { handicapperId, selections: [], summary: null, lastUpdated: null };
        }
    },

    // Get leaderboard data (sorted by rank)
    async getLeaderboard() {
        const data = await this.getHandicappers();
        const sorted = data.handicappers.sort((a, b) => a.rank - b.rank);
        return { handicappers: sorted, lastUpdated: data.lastUpdated };
    },

    // Get specific handicapper by slug
    async getHandicapper(slug) {
        const data = await this.getHandicappers();
        return data.handicappers.find(h => h.slug === slug) || null;
    }
};

// Utility functions
const TMR_Utils = {
    // Format win rate as percentage
    formatWinRate(winRate) {
        return `${winRate.toFixed(1)}%`;
    },

    // Format ROI as percentage
    formatROI(roi) {
        const sign = roi >= 0 ? '+' : '';
        return `${sign}${roi.toFixed(1)}%`;
    },

    // Format units
    formatUnits(units) {
        const sign = units >= 0 ? '+' : '';
        return `${sign}${units.toFixed(1)}u`;
    },

    // Format date
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    },

    // Get result badge HTML
    getResultBadge(result) {
        const badges = {
            'win': '<span class="badge badge-win">WIN</span>',
            'loss': '<span class="badge badge-loss">LOSS</span>',
            'push': '<span class="badge badge-push">PUSH</span>',
            'pending': '<span class="badge badge-pending">PENDING</span>'
        };
        return badges[result] || badges['pending'];
    },

    // Get confidence badge HTML
    getConfidenceBadge(confidence) {
        const badges = {
            'high': '<span class="confidence-badge confidence-high">HIGH</span>',
            'medium': '<span class="confidence-badge confidence-medium">MED</span>',
            'low': '<span class="confidence-badge confidence-low">LOW</span>'
        };
        return badges[confidence] || '';
    },

    // Calculate record string (W-L-P)
    getRecordString(wins, losses, pushes) {
        return pushes > 0 ? `${wins}-${losses}-${pushes}` : `${wins}-${losses}`;
    },

    // Get ROI color class
    getROIClass(roi) {
        if (roi >= 10) return 'roi-excellent';
        if (roi >= 5) return 'roi-good';
        if (roi >= 0) return 'roi-positive';
        return 'roi-negative';
    },

    // Get win rate color class
    getWinRateClass(winRate) {
        if (winRate >= 60) return 'winrate-excellent';
        if (winRate >= 55) return 'winrate-good';
        if (winRate >= 52.4) return 'winrate-profitable';
        return 'winrate-below';
    }
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TMR_API, TMR_Utils };
}
