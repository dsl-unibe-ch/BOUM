import type { PageLoad } from './$types';
import { authFetch } from '$lib/auth.svelte';
import { PUBLIC_API_BASE_URL } from '$env/static/public';

export const load: PageLoad = async ({ fetch }) => {
	const res = await authFetch(`${PUBLIC_API_BASE_URL}/user`, {}, fetch);
	if (!res.ok) {
		return { error: 'Failed to load users.' };
	}

	const users = await res.json();
	return { users };
};
