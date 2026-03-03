import type { PageServerLoad, Actions } from './$types';
import { fail, redirect } from '@sveltejs/kit';
import { API_BASE_URL } from '$lib/constants';

const sessionCookieName = 'auth-session';

export const load = (async (event) => {
	if (event.locals.user) {
		return redirect(302, '/');
	}
	return {};
}) satisfies PageServerLoad;

export const actions: Actions = {
	login: async (event) => {
		const formData = await event.request.formData();
		const username = formData.get('username');
		const password = formData.get('password');

		if (!validateUsername(username)) {
			return fail(400, {
				message: 'Invalid username (min 3, max 31 characters, alphanumeric only)'
			});
		}
		if (!validatePassword(password)) {
			return fail(400, { message: 'Invalid password (min 6, max 255 characters)' });
		}

		let response: Response;
		try {
			response = await fetch(`${API_BASE_URL}/auth/login`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ username, password })
			});
		} catch {
			return fail(500, { message: 'Could not reach the server. Please try again later.' });
		}

		if (!response.ok) {
			if (response.status === 401) {
				return fail(401, { message: 'Invalid username or password' });
			}
			return fail(500, { message: 'Something went wrong. Please try again later.' });
		}

		const { bearer } = await response.json();

		event.cookies.set(sessionCookieName, bearer, {
			expires: new Date(Date.now() + 30 * 60 * 1000), // 30 minutes
			path: '/',
			httpOnly: true,
			sameSite: 'strict'
		});

		return redirect(302, '/');
	}
};

function validateUsername(username: unknown): username is string {
	return (
		typeof username === 'string' &&
		username.length >= 3 &&
		username.length <= 31 &&
		/^[a-zöäüéàèë0-9_-]+$/.test(username)
	);
}

function validatePassword(password: unknown): password is string {
	return typeof password === 'string' && password.length >= 6 && password.length <= 255;
}
