import type { PageLoad } from './$types';
import { authFetch } from '$lib/auth.svelte';
import { PUBLIC_API_BASE_URL } from '$env/static/public';
import type { ExperimentListItem } from '$lib/types';

export const load: PageLoad = async ({ parent, fetch }) => {
	const { user } = await parent();
	if (!user) return { experiments: [] as ExperimentListItem[] };

	const endpoint = user.role === 0 ? '/experiment/' : '/experiment/me';
	const res = await authFetch(`${PUBLIC_API_BASE_URL}${endpoint}`, {}, fetch);
	if (!res.ok) {
		return { experiments: [] as ExperimentListItem[], error: 'Failed to load experiments.' };
	}
	const experiments: ExperimentListItem[] = await res.json();
	return { experiments };
};
