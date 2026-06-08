<script lang="ts">
	import { Trash } from '@lucide/svelte';
	import type { PageProps } from './$types';
	import { Dialog, Portal } from '@skeletonlabs/skeleton-svelte';

	let { data }: PageProps = $props();

	let open = $state(false);
	let selectedUserId = $state<string | null>(null);

	async function resetPassword(userId: string) {
		// Implement reset password logic here
	}

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
				{user.name} ({user.email})
				<button
					onclick={() => {
						selectedUserId = user.id;
						open = true;
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

<Dialog {open}>
	<Portal>
		<div class="dialog-content">
			<h2>Reset Password</h2>
			<form onsubmit={resetPassword}>
				<label for="oldPassword">Old Password:</label>
				<input id="oldPassword" type="password" required />
				<label for="newPassword">New Password:</label>
				<input id="newPassword" type="password" required />
				<button type="submit" class="btn preset-filled">Submit</button>
			</form>
		</div>
	</Portal>
</Dialog>
