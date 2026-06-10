import { goto, invalidateAll } from '$app/navigation';
import { PUBLIC_API_BASE_URL } from '$env/static/public';

const TOKEN_KEY = 'auth-token';

export interface User {
	id: number;
	role: number;
	username: string;
}

let user = $state<User | null>(null);

export function getUser(): User | null {
	return user;
}

export function getToken(): string | null {
	return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
	localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
	localStorage.removeItem(TOKEN_KEY);
}

export async function authFetch(
	url: string,
	options: RequestInit = {},
	fetchFn: typeof fetch = fetch
): Promise<Response> {
	const token = getToken();
	const headers = new Headers(options.headers);
	if (token) {
		headers.set('Authorization', `Bearer ${token}`);
	}
	return fetchFn(url, { ...options, headers });
}

export async function loadUser(fetchFn: typeof fetch = fetch): Promise<User | null> {
	const token = getToken();
	if (!token) {
		user = null;
		return null;
	}

	try {
		const res = await authFetch(`${PUBLIC_API_BASE_URL}/user/me`, {}, fetchFn);
		if (!res.ok) {
			clearToken();
			user = null;
			return null;
		}
		user = await res.json();
		return user;
	} catch {
		clearToken();
		user = null;
		return null;
	}
}

export async function logout(): Promise<void> {
	clearToken();
	user = null;
	await goto('/login');
	await invalidateAll();
}
