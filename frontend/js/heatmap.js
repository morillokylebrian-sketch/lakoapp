// Heatmap Layer for OSM Maps
class HeatmapLayer {
    constructor(map) {
        this.map = map;
        this.layer = null;
        this.active = false;
    }

    async toggle() {
        if (this.active) {
            this.hide();
        } else {
            await this.show();
        }
    }

    async show() {
        try {
            const data = await api.getHeatmap();
            const points = data.points.map(p => [p.latitude, p.longitude, p.weight]);
            
            if (typeof L !== 'undefined' && L.heatLayer) {
                this.layer = L.heatLayer(points, {
                    radius: 25,
                    blur: 15,
                    maxZoom: 17,
                    gradient: {
                        0.2: '#10b981',
                        0.4: '#84cc16',
                        0.6: '#eab308',
                        0.8: '#f97316',
                        1.0: '#dc2626'
                    }
                }).addTo(this.map);
                this.active = true;
            }
        } catch (error) {
            console.error('Error loading heatmap:', error);
        }
    }

    hide() {
        if (this.layer) {
            this.map.removeLayer(this.layer);
            this.layer = null;
            this.active = false;
        }
    }
}

// Note: Heatmap layer is typically instantiated per map instance
// For usage: const heatmap = new HeatmapLayer(mapManager.map);