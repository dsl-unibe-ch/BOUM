<script lang="ts">
	import { authFetch } from '$lib/auth.svelte';
	import { API_BASE_URL } from '$lib/constants';
	import { Dialog, Portal } from '@skeletonlabs/skeleton-svelte';
	import { X } from '@lucide/svelte';

	let {
		experimentId,
		videoId,
		open = $bindable(false)
	}: {
		experimentId: number;
		videoId: number;
		open: boolean;
	} = $props();

	let videoSrc = $state<string | null>(null);
	let loading = $state(false);
	let error = $state('');

	async function loadVideo() {
		loading = true;
		error = '';
		try {
			const res = await authFetch(
				`${API_BASE_URL}/experiment/${experimentId}/videos/${videoId}/download`
			);
			if (!res.ok) {
				error = 'Failed to load video.';
				return;
			}
			const blob = await res.blob();
			videoSrc = URL.createObjectURL(blob);
		} catch {
			error = 'Could not reach the server.';
		} finally {
			loading = false;
		}
	}

	function cleanup() {
		if (videoSrc) {
			URL.revokeObjectURL(videoSrc);
			videoSrc = null;
		}
		error = '';
	}

	function handleOpenChange(details: { open: boolean }) {
		open = details.open;
		if (!details.open) cleanup();
	}

	$effect(() => {
		if (open && !videoSrc && !loading && !error) {
			loadVideo();
		}
	});
</script>

<Dialog {open} onOpenChange={handleOpenChange}>
	<Portal>
		<Dialog.Backdrop class="fixed inset-0 z-50 bg-black/80" />
		<Dialog.Positioner class="fixed inset-0 z-50 flex items-center justify-center p-4">
			<Dialog.Content class="relative max-h-[90vh] max-w-[90vw]">
				<Dialog.Title class="sr-only">Video Player</Dialog.Title>

				<Dialog.CloseTrigger class="absolute top-0 right-0 z-10 btn-icon preset-filled-surface-500">
					<X size={20} />
				</Dialog.CloseTrigger>

				{#if loading}
					<div class="flex flex-col items-center gap-3 text-white">
						<div
							class="h-10 w-10 animate-spin rounded-full border-4 border-white/30 border-t-white"
						></div>
						<Dialog.Description>Loading video…</Dialog.Description>
					</div>
				{:else if error}
					<div class="card preset-filled-error-500 p-6 text-center">
						<Dialog.Description>{error}</Dialog.Description>
						<Dialog.CloseTrigger class="mt-3 btn preset-filled-surface-500">
							Close
						</Dialog.CloseTrigger>
					</div>
				{:else if videoSrc}
					<video class="max-h-[85vh] max-w-[90vw] rounded-lg" src={videoSrc} controls autoplay>
						<track kind="captions" />
					</video>
				{/if}
			</Dialog.Content>
		</Dialog.Positioner>
	</Portal>
</Dialog>
