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
</script>

{#if data.error}
	<p class="error">{data.error}</p>
{:else if data.users}
	<h1>Users</h1>
	<ul>
		{#each data.users as user}
			<li>
				{user.username} ({user.role === 0 ? 'Admin' : 'User'})
				<button
					onclick={() => {
						selectedUserId = user.id;
						passwordPanelOpen = true;
					}}
					class="btn preset-filled">reset password</button
				>
				<button onclick={() => deleteUser(user.id)} class="btn-icon preset-filled"><Trash /></button
				>
			</li>
		{/each}
	</ul>
{:else}
	<p>Loading...</p>
{/if}

<ChangePasswordPanel
	{selectedUserId}
	open={passwordPanelOpen}
	onOpenChange={(isOpen) => {
		passwordPanelOpen = isOpen;
		if (!isOpen) selectedUserId = null;
	}}
/>
