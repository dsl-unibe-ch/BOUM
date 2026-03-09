import { redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';
import { getToken, getUser, loadUser } from '$lib/auth.svelte';

export const ssr = false;

export const load: LayoutLoad = async ({ url }) => {
	const token = getToken();

	if (!token) {
		if (url.pathname !== '/login') {
			throw redirect(302, '/login');
		}
		return { user: null };
	}

	let user = getUser();
	if (!user) {
		user = await loadUser();
		if (url.pathname !== '/login') {
			throw redirect(302, '/login');
		}
	}

	return { user };
};
