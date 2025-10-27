const AgentList = {
    template: `
        <div class="bg-slate-700 rounded-lg p-6">
            <h2 class="text-2xl font-bold mb-6 text-white">Agent List</h2>
            <div class="mb-6 flex gap-4">
                <input v-model="searchQuery" type="text" placeholder="Search agents..."
                    class="w-full px-4 py-2 bg-slate-600 text-white rounded-md" />
            </div>
            <div v-for="agent in agents" :key="agent.id" class="bg-slate-600 p-4 rounded-lg mb-2">
                <h3 class="text-lg font-bold text-white">{{ agent.name || agent.id.substring(0, 8) }}</h3>
                <p class="text-slate-400">Status: {{ agent.status }}</p>
                <p class="text-slate-400">Tasks: {{ agent.metrics?.processed_tasks || 0 }}</p>
            </div>
        </div>
    `,

    props: {
        agents: { type: Array, default: () => [] }
    },

    emits: ["select"],

    setup(props, { emit }) {
        const searchQuery = Vue.ref("");
        return { searchQuery, agents: props.agents };
    }
};

window.AgentList = AgentList;
console.log('✅ AgentList component loaded');
