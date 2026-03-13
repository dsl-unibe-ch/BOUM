import type { PageLoad } from './$types';
import { authFetch } from '$lib/auth.svelte';
import { API_BASE_URL } from '$lib/constants';

export const load: PageLoad = async ({ parent, fetch }) => {
	const { user } = await parent();
	if (!user) return { experiments: [] };

	const endpoint = user.role === 0 ? '/experiment/' : '/experiment/me';
	const res = await authFetch(`${API_BASE_URL}${endpoint}`, {}, fetch);
	if (!res.ok) {
		return { experiments: [], error: 'Failed to load experiments.' };
	}
	const experiments = await res.json();
	return { experiments };
};
