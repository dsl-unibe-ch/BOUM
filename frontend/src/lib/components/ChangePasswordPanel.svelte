<script lang="ts">
	import { XIcon } from '@lucide/svelte';
	import { Dialog, Portal } from '@skeletonlabs/skeleton-svelte';
	import { authFetch } from '$lib/auth.svelte';
	import { PUBLIC_API_BASE_URL } from '$env/static/public';

	let {
		selectedUserId,
		open,
		onOpenChange
	}: {
		selectedUserId: string | null;
		open: boolean;
		onOpenChange: (open: boolean) => void;
	} = $props();

	function handleOpenChange(details: { open: boolean }) {
		onOpenChange(details.open);
	}

	let saving = $state(false);
	let error = $state('');
	let success = $state('');
	let oldPassword = $state('');
	let newPassword = $state('');

	$effect(() => {
		if (!open) {
			oldPassword = '';
			newPassword = '';
			error = '';
			success = '';
		}
	});

	async function handleResetPassword(e: SubmitEvent) {
		e.preventDefault();
		if (!selectedUserId) return;
		saving = true;
		error = '';
		success = '';

		try {
			const res = await authFetch(`${PUBLIC_API_BASE_URL}/user/${selectedUserId}/password`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					old_password: oldPassword,
					new_password: newPassword
				})
			});
			if (!res.ok) {
				const data = await res.json().catch(() => null);
				throw new Error(data?.msg ?? 'Failed to update password');
			}
			success = 'Password updated successfully';
			oldPassword = '';
			newPassword = '';
			// close the dialog after a short delay to show the success message
			setTimeout(() => onOpenChange(false), 800);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error updating password';
		} finally {
			saving = false;
		}
	}
</script>

<Dialog {open} onOpenChange={handleOpenChange}>
	<Portal>
		<Dialog.Backdrop class="fixed inset-0 z-50 bg-surface-50-950/50" />
		<Dialog.Positioner class="fixed inset-0 z-50 flex items-center justify-center p-4">
			<Dialog.Content
				class="flex w-full max-w-md flex-col space-y-4 card bg-surface-100-900 p-4 shadow-xl"
			>
				<header class="flex items-center justify-between">
					<Dialog.Title class="text-lg font-bold">Change Password</Dialog.Title>
					<Dialog.CloseTrigger class="btn-icon hover:preset-tonal">
						<XIcon class="size-4" />
					</Dialog.CloseTrigger>
				</header>

				<form onsubmit={handleResetPassword} class="space-y-4">
					{#if error}
						<aside class="alert preset-filled-error-500">
							<p>{error}</p>
						</aside>
					{/if}

					{#if success}
						<aside class="alert preset-filled-success-500">
							<p>{success}</p>
						</aside>
					{/if}

					<div class="space-y-2">
						<label for="oldPassword" class="block text-sm font-medium">Old Password:</label>
						<input
							id="oldPassword"
							type="password"
							bind:value={oldPassword}
							class="input w-full"
							required
							disabled={saving}
						/>
					</div>

					<div class="space-y-2">
						<label for="newPassword" class="block text-sm font-medium">New Password:</label>
						<input
							id="newPassword"
							type="password"
							bind:value={newPassword}
							class="input w-full"
							required
							disabled={saving}
						/>
					</div>

					<div class="flex gap-2 pt-4">
						<button type="submit" class="btn preset-filled-primary-500 flex-1" disabled={saving}>
							{#if saving}
								Updating...
							{:else}
								Update Password
							{/if}
						</button>
						<button
							type="button"
							class="btn preset-outlined-surface-200-800"
							onclick={() => onOpenChange(false)}
							disabled={saving}
						>
							Cancel
						</button>
					</div>
				</form>
			</Dialog.Content>
		</Dialog.Positioner>
	</Portal>
</Dialog>
