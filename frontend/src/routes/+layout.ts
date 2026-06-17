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
	}

	// If the token was invalid (e.g., expired), the user will be null after attempting to load it. In that case, redirect to the login page.
	if (!user && url.pathname !== '/login') {
		throw redirect(302, '/login');
	}

	return { user };
};
