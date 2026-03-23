<script lang="ts">
	import { goto } from '$app/navigation';
	import { PUBLIC_API_BASE_URL } from '$env/static/public';
	import { setToken } from '$lib/auth.svelte';

	let username = $state('');
	let password = $state('');
	let error = $state('');
	let submitting = $state(false);

	async function handleLogin(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		submitting = true;

		try {
			const response = await fetch(`${PUBLIC_API_BASE_URL}/auth/login`, {
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
			setToken(bearer);

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
