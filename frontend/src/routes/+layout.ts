import { redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';
import { getToken, getUser, loadUser } from '$lib/auth.svelte';

export const ssr = false;

export const load: LayoutLoad = async ({ url, fetch }) => {
	const token = getToken();

	if (!token) {
		if (url.pathname !== '/login') {
			throw redirect(302, '/login');
		}
		return { user: null };
	}

	let user = getUser();
	if (!user) {
		user = await loadUser(fetch);
		if (url.pathname !== '/login') {
			throw redirect(302, '/login');
		}
	}

	return { user };
};
