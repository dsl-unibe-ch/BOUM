import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';

export const load = (async (event) => {
	if (!event.locals.user && event.route.id !== '/login') {
		console.log('User not logged in, redirecting to login page');
		return redirect(302, '/login');
	}
	return { user: event.locals.user ?? null };
}) satisfies LayoutServerLoad;
