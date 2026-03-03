<script lang="ts">
	import { enhance } from '$app/forms';
	import type { ActionData } from './$types';

	let { form }: { form: ActionData } = $props();
	let submitting = $state(false);
</script>

<div class="flex min-h-screen items-center justify-center">
	<div class="w-full max-w-md space-y-6 card preset-outlined-surface-200-800 p-8">
		<header class="text-center">
			<h1 class="h2 font-bold">Login</h1>
			<p class="preset-typo-muted mt-1">Sign in to your account</p>
		</header>

		{#if form?.message}
			<aside class="alert preset-filled-error-500">
				<p>{form.message}</p>
			</aside>
		{/if}

		<form
			method="POST"
			action="?/login"
			use:enhance={() => {
				submitting = true;
				return async ({ update }) => {
					submitting = false;
					await update();
				};
			}}
			class="space-y-4"
		>
			<label class="label">
				<span class="label-text">Username</span>
				<input
					class="input"
					type="text"
					name="username"
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
					name="password"
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
