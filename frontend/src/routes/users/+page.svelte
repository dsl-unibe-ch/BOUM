<script lang="ts">
	import { Trash } from '@lucide/svelte';
	import type { PageProps } from './$types';
	import ChangePasswordPanel from '$lib/components/ChangePasswordPanel.svelte';

	let { data }: PageProps = $props();

	let passwordPanelOpen = $state(false);
	let selectedUserId = $state<string | null>(null);

	async function deleteUser(userId: string) {
		// Implement delete user logic here
	}

	let newUsername = $state('');
	let creatingUser = $state(false);

	async function createUser(e: SubmitEvent) {
		e.preventDefault();
		if (!newUsername) return;
		creatingUser = true;
		try {
			// Implement create user logic here
		} finally {
			creatingUser = false;
		}
	}
</script>

{#if data.error}
	<p class="error">{data.error}</p>
{:else if data.users}
	<h1>Users</h1>
	<ul>
		{#each data.users as user}
			<li class="flex items-center gap-4">
				{user.username} ({user.role === 0 ? 'Admin' : 'User'})
				<button
					onclick={() => {
						selectedUserId = user.id;
						passwordPanelOpen = true;
					}}
					class="btn preset-filled-primary-500">reset password</button
				>
				<button onclick={() => deleteUser(user.id)} class="btn-icon preset-filled-primary-500"
					><Trash /></button
				>
			</li>
		{/each}
	</ul>
{:else}
	<p>Loading...</p>
{/if}
<form onsubmit={createUser} class="my-6 flex max-w-md gap-2">
	<input
		class="input flex-1"
		type="text"
		bind:value={newUsername}
		placeholder="New username"
		required
		minlength={1}
		maxlength={100}
	/>
	<button type="submit" class="btn preset-filled-primary-500" disabled={creatingUser}>
		{#if creatingUser}
			Creating...
		{:else}
			Create
		{/if}
	</button>
</form>

<ChangePasswordPanel
	{selectedUserId}
	open={passwordPanelOpen}
	onOpenChange={(isOpen: boolean) => {
		passwordPanelOpen = isOpen;
		if (!isOpen) selectedUserId = null;
	}}
/>
