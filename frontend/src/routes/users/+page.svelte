<script lang="ts">
	import { Trash } from '@lucide/svelte';
	import type { PageProps } from './$types';
	import ChangePasswordPanel from '$lib/components/ChangePasswordPanel.svelte';
	import { authFetch } from '$lib/auth.svelte';
	import { PUBLIC_API_BASE_URL } from '$env/static/public';
	import { invalidateAll } from '$app/navigation';

	let { data }: PageProps = $props();

	let passwordPanelOpen = $state(false);
	let selectedUserId = $state<string | null>(null);

	async function deleteUser(userId: string) {
		if (!confirm('Are you sure you want to delete this user?')) return;
		try {
			const res = await authFetch(`${PUBLIC_API_BASE_URL}/user/${userId}`, {
				method: 'DELETE'
			});
			if (!res.ok) throw new Error('Failed to delete user');
			invalidateAll(); // Invalidate the users data to refetch the list
		} catch (err) {
			console.error(err);
			alert('Error deleting user');
		}
	}

	let newUsername = $state('');
	let newPassword = $state('');
	let isAdmin = $state(false);
	let creatingUser = $state(false);

	async function createUser(e: SubmitEvent) {
		e.preventDefault();
		if (!newUsername || !newPassword) return;
		creatingUser = true;
		try {
			authFetch(`${PUBLIC_API_BASE_URL}/user`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					username: newUsername,
					password: newPassword,
					role: isAdmin ? 0 : 1
				})
			})
				.then((res) => {
					if (!res.ok) throw new Error('Failed to create user');
					return res.json();
				})
				.then((newUser) => {
					newUsername = '';
					newPassword = '';
					isAdmin = false;
					invalidateAll(); // Invalidate the users data to refetch the list
				})
				.catch((err) => {
					console.error(err);
					alert('Error creating user');
				});
		} finally {
			creatingUser = false;
		}
	}
</script>

<div class="p-4">
	<h1 class="mb-4 h2 font-bold">Users</h1>
	{#if data.error}
		<p class="error">{data.error}</p>
	{:else if data.users}
		<ul class="mb-6 card preset-outlined-surface-200-800">
			{#each data.users as user, index (user.id)}
				{#if index !== 0}
					<hr class="hr" />
				{/if}
				<li class="flex items-center justify-between gap-4 px-4 py-3">
					<span class="font-medium">
						{user.username}
						<span class="text-sm opacity-60">({user.role === 0 ? 'Admin' : 'User'})</span>
					</span>
					<div class="flex shrink-0 items-center gap-2">
						<button
							onclick={() => {
								selectedUserId = user.id;
								passwordPanelOpen = true;
							}}
							class="btn preset-filled-primary-500">reset password</button
						>
						<button
							onclick={() => deleteUser(user.id)}
							class="btn-icon preset-filled-error-500"
							aria-label="Delete user"><Trash size={18} /></button
						>
					</div>
				</li>
			{/each}
		</ul>
	{:else}
		<p>Loading...</p>
	{/if}
	<form onsubmit={createUser} class="my-6 flex max-w-lg gap-2">
		<input
			class="input flex-1"
			type="text"
			bind:value={newUsername}
			placeholder="username"
			required
			minlength={1}
			maxlength={100}
		/>
		<input
			class="input flex-1"
			type="password"
			bind:value={newPassword}
			placeholder="password"
			required
			minlength={6}
			maxlength={100}
		/>
		<label class="flex items-center space-x-2">
			<input class="checkbox" type="checkbox" bind:checked={isAdmin} />
			<p>admin</p>
		</label>
		<button type="submit" class="btn preset-filled-primary-500" disabled={creatingUser}>
			{#if creatingUser}
				Creating...
			{:else}
				Create
			{/if}
		</button>
	</form>
</div>

<ChangePasswordPanel
	{selectedUserId}
	open={passwordPanelOpen}
	onOpenChange={(isOpen: boolean) => {
		passwordPanelOpen = isOpen;
		if (!isOpen) selectedUserId = null;
	}}
/>
