import { sequence } from '@sveltejs/kit/hooks';
import type { Handle } from '@sveltejs/kit';
import { API_BASE_URL } from '$lib/constants';

const sessionCookieName = 'auth-session';

const handleAuth: Handle = async ({ event, resolve }) => {
	const sessionToken = event.cookies.get(sessionCookieName);
	if (!sessionToken) {
		event.locals.user = null;
		return resolve(event);
	}

	const user = await fetch(`${API_BASE_URL}/user/me`, {
		headers: {
			Authorization: `Bearer ${sessionToken}`
		}
	})
		.then((res) => {
			if (!res.ok) {
				throw new Error('Failed to fetch user data');
			}
			return res.json();
		})
		.catch(() => null);

	if (user) {
		event.cookies.set(sessionCookieName, sessionToken, {
			expires: new Date(Date.now() + 30 * 60 * 1000), // 30 minutes
			path: '/',
			httpOnly: true,
			sameSite: 'strict'
		});
	} else {
		event.cookies.delete(sessionCookieName, {
			path: '/'
		});
	}

	event.locals.user = user;

	return resolve(event);
};

export const handle: Handle = sequence(handleAuth);
