<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { API_BASE_URL } from '$lib/constants';
	import { onMount } from 'svelte';

	let username = $state('');
	let password = $state('');
	let error = $state('');
	let submitting = $state(false);

	onMount(() => {
		if (page.data.user) {
			goto('/');
		}
	});

	async function handleLogin(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		submitting = true;

		try {
			const response = await fetch(`${API_BASE_URL}/auth/login`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ username, password })
			});

			if (!response.ok) {
				if (response.status === 401) {
					error = 'Invalid username or password';
				} else {
					error = 'Something went wrong. Please try again later.';
				}
				return;
			}

			const { bearer } = await response.json();
			const expires = new Date(Date.now() + 30 * 60 * 1000).toUTCString();
			document.cookie = `auth-session=${bearer}; expires=${expires}; path=/; SameSite=Strict`;

			await goto('/');
		} catch {
			error = 'Could not reach the server. Please try again later.';
		} finally {
			submitting = false;
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center">
	<div class="w-full max-w-md space-y-6 card preset-outlined-surface-200-800 p-8">
		<header class="text-center">
			<h1 class="h2 font-bold">Login</h1>
			<p class="preset-typo-muted mt-1">Sign in to your account</p>
		</header>

		{#if error}
			<aside class="alert preset-filled-error-500">
				<p>{error}</p>
			</aside>
		{/if}

		<form onsubmit={handleLogin} class="space-y-4">
			<label class="label">
				<span class="label-text">Username</span>
				<input
					class="input"
					type="text"
					bind:value={username}
					placeholder="Enter your username"
					required
					minlength={3}
					maxlength={31}
				/>
			</label>

			<label class="label">
				<span class="label-text">Password</span>
				<input
					class="input"
					type="password"
					bind:value={password}
					placeholder="Enter your password"
					required
					minlength={6}
					maxlength={255}
				/>
			</label>

			<button type="submit" class="btn w-full preset-filled-primary-500" disabled={submitting}>
				{#if submitting}
					Signing in...
				{:else}
					Sign in
				{/if}
			</button>
		</form>
	</div>
</div>
