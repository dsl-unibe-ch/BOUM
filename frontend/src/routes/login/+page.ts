import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import { getToken } from '$lib/auth.svelte';

export const load: PageLoad = async () => {
	if (getToken()) {
		throw redirect(302, '/');
	}
	return {};
};
