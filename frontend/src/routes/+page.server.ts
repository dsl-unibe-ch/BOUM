import { redirect } from '@sveltejs/kit';
import type { Actions } from './$types';

export const actions: Actions = {
	logout: async (event) => {
		event.cookies.delete('auth-session', { path: '/' });
		return redirect(302, '/login');
	}
};
