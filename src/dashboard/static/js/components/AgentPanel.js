const AgentPanel = {
    template: `
        <div class="space-y-6 p-6 bg-slate-800 min-h-screen">
            <h1 class="text-4xl font-bold text-white mb-6">Agent Management</h1>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div v-for="agent in agentStore.agents" :key="agent.id" class="bg-slate-700 rounded-lg p-4">
                    <h3 class="font-bold text-white">{{ agent.name || agent.id.substring(0, 8) }}</h3>
                    <p class="text-slate-400">Status: {{ agent.status }}</p>
                </div>
            </div>
        </div>
    `,

    setup() {
        const agentStore = Vue.inject("agentStore") || window.App?.useAgentStore();
        return { agentStore };
    }
};

window.AgentPanel = AgentPanel;
console.log('✅ AgentPanel component loaded');

// ============================================================================
// Additional Component Methods
// ============================================================================

AgentPanel.methods = {
    selectAgent(agent) {
        this.selectedAgent = agent;
        console.log('Selected agent:', agent.id);
    },
    
    handleAgentAction(action) {
        if (!this.selectedAgent) return;
        console.log('Action:', action, 'for agent:', this.selectedAgent.id);
        // TODO: Implement actual agent control
    }
};

// Make it reactive
AgentPanel.setup = function() {
    const selectedAgent = Vue.ref(null);
    
    const methods = {
        selectAgent(agent) {
            selectedAgent.value = agent;
            console.log('Selected agent:', agent.id);
        },
        
        handleAgentAction(action) {
            if (!selectedAgent.value) return;
            console.log('Action:', action, 'for agent:', selectedAgent.value.id);
        }
    };
    
    return {
        selectedAgent,
        ...methods
    };
};

